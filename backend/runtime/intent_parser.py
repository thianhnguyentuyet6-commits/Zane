# -*- coding: utf-8 -*-
"""
Intent Parser - 意图解析器
将自然语言转为结构化任务，支持中文口语容错
"""
import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ParsedIntent:
    raw: str
    normalized: str
    category: str  # file, process, window, vision, security, linux, network, system, general
    action: str    # list, read, write, delete, kill, focus, search...
    entities: Dict[str, Any]  # 提取实体：path, name, pid...
    confidence: float
    ambiguous: bool
    clarification_needed: str = ""

class IntentParser:
    """意图解析器 - 确定性优先，LLM补充"""
    
    # 分类关键词 - 中文优先
    CATEGORY_KEYWORDS = {
        "file": ["文件", "文件夹", "下载", "文档", "桌面", "整理", "删除", "复制", "移动", "重命名", "列出", "查看", "读取", "写入", "目录", "磁盘"],
        "process": ["进程", "任务", "程序", "结束", "杀死", "卡死", "占用", "内存", "CPU", "后台"],
        "window": ["窗口", "切换", "聚焦", "最小化", "最大化", "关闭", "微信", "浏览器", "Chrome", "置顶", "Z序"],
        "vision": ["截图", "看一下", "屏幕", "识别", "OCR", "文字", "图标", "找一下", "在哪"],
        "security": ["安全", "扫描", "漏洞", "密码", "明文", "启动项", "大文件", "沙盒", "风险"],
        "linux": ["Linux", "WSL", "Ubuntu", "执行", "bash", "ls", "cat", "grep", "终端"],
        "network": ["搜索", "联网", "查一下", "百度", "谷歌", "信息", "验证", "网页", "Bing"],
        "system": ["系统", "状态", "性能", "硬件", "CPU", "内存", "显卡", "磁盘", "温度", "电量"],
    }
    
    ACTION_KEYWORDS = {
        "list": ["列出", "查看", "显示", "有哪些", "列一下", "list", "ls"],
        "read": ["读取", "打开", "看", "内容", "read", "cat"],
        "write": ["写入", "创建", "新建", "写", "write", "保存"],
        "delete": ["删除", "移除", "清理", "删掉", "delete", "rm"],
        "kill": ["结束", "关闭", "杀死", "终止", "kill", "停止"],
        "focus": ["聚焦", "切换", "打开", "focus", "切换到"],
        "search": ["搜索", "查找", "搜一下", "search", "找"],
        "organize": ["整理", "归类", "分类", "organize"],
        "scan": ["扫描", "检查", "检测", "scan"],
    }
    
    def __init__(self):
        self.llm_classifier = None  # 可选：Qwen2-0.5B 本地分类
    
    def parse(self, text: str) -> ParsedIntent:
        """解析意图 - 确定性规则优先"""
        raw = text.strip()
        normalized = self._normalize(raw)
        
        # 1. 分类
        category, cat_conf = self._classify_category(normalized)
        
        # 2. 动作
        action, act_conf = self._classify_action(normalized)
        
        # 3. 实体提取
        entities = self._extract_entities(raw)
        
        # 4. 歧义检测
        ambiguous = cat_conf < 0.6 or act_conf < 0.5
        clarification = ""
        if ambiguous:
            clarification = self._generate_clarification(category, action, entities)
        
        confidence = (cat_conf + act_conf) / 2
        
        return ParsedIntent(
            raw=raw,
            normalized=normalized,
            category=category,
            action=action,
            entities=entities,
            confidence=confidence,
            ambiguous=ambiguous,
            clarification_needed=clarification
        )
    
    def _normalize(self, text: str) -> str:
        # 中文口语容错
        text = text.replace("帮我", "").replace("请", "").replace("一下", "").strip()
        text = re.sub(r"\s+", " ", text)
        return text
    
    def _classify_category(self, text: str) -> tuple[str, float]:
        scores = {}
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text or kw.lower() in text.lower())
            scores[cat] = score
        
        if not scores or max(scores.values()) == 0:
            return "general", 0.3
        
        best = max(scores, key=scores.get)
        total_kw = len(self.CATEGORY_KEYWORDS[best])
        conf = min(0.95, scores[best] / max(1, total_kw * 0.3) + 0.3)
        return best, conf
    
    def _classify_action(self, text: str) -> tuple[str, float]:
        scores = {}
        for act, keywords in self.ACTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text or kw.lower() in text.lower())
            scores[act] = score
        
        if not scores or max(scores.values()) == 0:
            return "general", 0.3
        
        best = max(scores, key=scores.get)
        conf = min(0.95, scores[best] * 0.4 + 0.4)
        return best, conf
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        entities = {}
        
        # 路径提取
        path_patterns = [
            r"[C-Z]:\\[^\s\"']+",
            r"/[^\s\"']+/[^\s\"']+",
            r"~\/[^\s\"']+",
            r"下载|文档|桌面|Downloads|Documents|Desktop"
        ]
        for pat in path_patterns:
            m = re.search(pat, text)
            if m:
                entities["path"] = m.group(0)
                break
        
        # PID
        m = re.search(r"PID\s*(\d+)", text, re.I)
        if m:
            entities["pid"] = int(m.group(1))
        
        # 应用名
        apps = ["微信", "Chrome", "VS Code", "Code", "Explorer", "Notepad", "WeChat"]
        for app in apps:
            if app in text:
                entities["app_name"] = app
                break
        
        # 关键词
        entities["keywords"] = re.findall(r"[\u4e00-\u9fa5]{2,}", text)[:5]
        
        return entities
    
    def _generate_clarification(self, category: str, action: str, entities: Dict) -> str:
        if category == "general":
            return "你的意图不太明确，能否具体说是要操作文件、进程、窗口还是搜索信息？"
        if not entities:
            return f"检测到想{action}{category}，但缺少具体对象，能否补充路径或名称？"
        return ""

# 全局
intent_parser = IntentParser()
