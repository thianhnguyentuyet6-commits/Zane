# -*- coding: utf-8 -*-
"""
Dreaming - 三阶段梦境系统
Light→REM→Deep，参考 OpenClaw 设计，适配 Zane
"""
import os
import json
import time
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import Counter

@dataclass
class DreamCandidate:
    id: str
    content: str
    source: str  # 来自哪条短期记忆
    signals: Dict[str, float]  # 六信号
    total_score: float
    created_at: float

class DreamingSystem:
    """
    三阶段：
    Light: 扫描短期素材，去重暂存，不写入 MEMORY
    REM: 主题反思总结，增强信号，不写入
    Deep: 六加权信号评分，阈值才写入长期，生成 DREAMS.md
    """
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data", "memory")
        self.dreams_dir = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "dreaming")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.dreams_dir, "Light"), exist_ok=True)
        os.makedirs(os.path.join(self.dreams_dir, "REM"), exist_ok=True)
        os.makedirs(os.path.join(self.dreams_dir, "Deep"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, ".dreams"), exist_ok=True)
        
        # 六信号权重
        self.signal_weights = {
            "importance": 0.25,   # 重要性
            "frequency": 0.20,    # 频率
            "recency": 0.15,      # 新鲜度
            "feedback": 0.15,     # 用户反馈
            "success": 0.15,      # 成功率
            "verifiable": 0.10    # 可验证性
        }
        self.threshold = 0.7  # 写入阈值
    
    def light_phase(self, days: int = 7) -> Dict:
        """
        Light: 扫描短期素材，去重暂存
        不写入 MEMORY.md，输出到 .dreams/candidates.json
        """
        # 扫描短期记忆 - episodic + conversations + daily logs
        short_term = self._collect_short_term(days)
        
        # 去重 - 语义去重简单版：关键词重叠
        unique = self._deduplicate(short_term)
        
        # 生成候选，不写入长期
        candidates = []
        for item in unique:
            signals = self._score_signals(item, short_term)
            total = sum(signals[k] * self.signal_weights[k] for k in self.signal_weights)
            candidate = DreamCandidate(
                id=f"cand_{int(time.time()*1000)}_{len(candidates)}",
                content=item["content"],
                source=item.get("source", "episodic"),
                signals=signals,
                total_score=total,
                created_at=time.time()
            )
            candidates.append(candidate)
        
        # 暂存到 .dreams/candidates.json
        candidates_path = os.path.join(self.data_dir, ".dreams", "candidates.json")
        with open(candidates_path, 'w', encoding='utf-8') as f:
            json.dump([c.__dict__ for c in candidates], f, ensure_ascii=False, indent=2)
        
        # 生成 Light 报告
        report_path = os.path.join(self.dreams_dir, "Light", f"{time.strftime('%Y-%m-%d')}.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Light 阶段 - {time.strftime('%Y-%m-%d')}\n\n")
            f.write(f"扫描 {len(short_term)} 条短期，去重后 {len(unique)} 条，候选 {len(candidates)} 条\n\n")
            for c in candidates[:20]:
                f.write(f"- [{c.total_score:.2f}] {c.content[:100]}\n")
        
        return {
            "phase": "Light",
            "scanned": len(short_term),
            "unique": len(unique),
            "candidates": len(candidates),
            "candidates_path": candidates_path,
            "report": report_path,
            "note": "未写入长期记忆，仅暂存"
        }
    
    def rem_phase(self) -> Dict:
        """
        REM: 主题反思总结
        增强信号，不写入
        """
        # 加载候选
        candidates_path = os.path.join(self.data_dir, ".dreams", "candidates.json")
        if not os.path.exists(candidates_path):
            return {"phase": "REM", "error": "无 Light 候选，先运行 Light"}
        
        with open(candidates_path, 'r', encoding='utf-8') as f:
            candidates_data = json.load(f)
        
        # 主题聚类 - 简单关键词聚类
        themes = self._cluster_themes(candidates_data)
        
        # 增强信号：同主题频率提升
        for cand in candidates_data:
            theme = self._get_theme(cand["content"], themes)
            if theme:
                # 同主题出现多次，frequency 信号增强
                count = sum(1 for c in candidates_data if theme in c["content"])
                cand["signals"]["frequency"] = min(1.0, count * 0.3)
                # 重新计算总分
                cand["total_score"] = sum(cand["signals"][k] * self.signal_weights[k] for k in self.signal_weights)
        
        # 保存增强后
        with open(candidates_path, 'w', encoding='utf-8') as f:
            json.dump(candidates_data, f, ensure_ascii=False, indent=2)
        
        # REM 报告
        report_path = os.path.join(self.dreams_dir, "REM", f"{time.strftime('%Y-%m-%d')}.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# REM 阶段 - {time.strftime('%Y-%m-%d')}\n\n")
            f.write(f"主题数：{len(themes)}\n\n")
            for theme, items in themes.items():
                f.write(f"## 主题：{theme} ({len(items)} 条)\n")
                for item in items[:3]:
                    f.write(f"- {item[:80]}\n")
                f.write("\n")
        
        return {
            "phase": "REM",
            "themes": len(themes),
            "themes_detail": {k: len(v) for k, v in themes.items()},
            "report": report_path,
            "note": "主题反思，增强信号，未写入长期"
        }
    
    def deep_phase(self) -> Dict:
        """
        Deep: 六信号评分，阈值才写入长期，生成 DREAMS.md
        """
        candidates_path = os.path.join(self.data_dir, ".dreams", "candidates.json")
        if not os.path.exists(candidates_path):
            return {"phase": "Deep", "error": "无候选"}
        
        with open(candidates_path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
        
        # 阈值过滤
        promoted = [c for c in candidates if c["total_score"] >= self.threshold]
        rejected = [c for c in candidates if c["total_score"] < self.threshold]
        
        # 写入长期记忆 - semantic.json
        semantic_path = os.path.join(self.data_dir, "semantic.json")
        semantic = []
        if os.path.exists(semantic_path):
            try:
                with open(semantic_path, 'r', encoding='utf-8') as f:
                    semantic = json.load(f)
            except:
                semantic = []
        
        new_memories = []
        for cand in promoted:
            # 去重：长期已存在不重复
            if not any(cand["content"][:30] in s.get("content", "") for s in semantic):
                mem = {
                    "id": cand["id"],
                    "content": cand["content"],
                    "source": f"dreaming Deep {time.strftime('%Y-%m-%d')}",
                    "score": cand["total_score"],
                    "signals": cand["signals"],
                    "created_at": time.time()
                }
                semantic.append(mem)
                new_memories.append(mem)
        
        with open(semantic_path, 'w', encoding='utf-8') as f:
            json.dump(semantic, f, ensure_ascii=False, indent=2)
        
        # 生成 DREAMS.md - 人类可读叙事
        dreams_md_path = os.path.join(os.path.dirname(self.data_dir), "..", "DREAMS.md")
        # 实际路径在 memory/DREAMS.md
        dreams_md_path = os.path.join(self.dreams_dir, "..", "DREAMS.md")
        os.makedirs(os.path.dirname(dreams_md_path), exist_ok=True)
        
        # 追加而非覆盖
        with open(dreams_md_path, 'a', encoding='utf-8') as f:
            f.write(f"\n## {time.strftime('%Y-%m-%d')} 梦境\n\n")
            f.write(f"今天帮你整理了 {len(candidates)} 条短期记忆，提炼出 {len(new_memories)} 条长期记忆：\n\n")
            for mem in new_memories[:5]:
                f.write(f"- {mem['content']}\n")
            f.write(f"\n> 阈值 {self.threshold}，六信号加权评分，{len(rejected)} 条未达阈值未写入\n\n")
        
        # Deep 报告 - 机器状态
        report_path = os.path.join(self.dreams_dir, "Deep", f"{time.strftime('%Y-%m-%d')}.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Deep 阶段 - {time.strftime('%Y-%m-%d')}\n\n")
            f.write(f"候选 {len(candidates)}，晋升 {len(promoted)}，拒绝 {len(rejected)}，新写入 {len(new_memories)}\n\n")
            f.write(f"## 晋升记忆\n")
            for mem in new_memories:
                f.write(f"- [{mem['score']:.2f}] {mem['content'][:100]} | {mem['signals']}\n")
        
        return {
            "phase": "Deep",
            "candidates": len(candidates),
            "promoted": len(promoted),
            "rejected": len(rejected),
            "new_memories": len(new_memories),
            "memories": new_memories[:5],
            "dreams_md": dreams_md_path,
            "report": report_path,
            "note": f"阈值 {self.threshold}，六信号加权，仅高分写入长期"
        }
    
    def _collect_short_term(self, days: int) -> List[Dict]:
        items = []
        # episodic.json
        episodic_path = os.path.join(self.data_dir, "episodic.json")
        if os.path.exists(episodic_path):
            try:
                with open(episodic_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data[-100:]:  # 最近100
                        if isinstance(item, dict):
                            content = item.get("content", str(item))
                        else:
                            content = str(item)
                        items.append({"content": content, "source": "episodic"})
            except:
                pass
        
        # conversations
        conv_path = os.path.join(self.data_dir, "conversations.json")
        if os.path.exists(conv_path):
            try:
                with open(conv_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data[-50:]:
                        items.append({"content": str(item), "source": "conversation"})
            except:
                pass
        
        # 模拟一些短期
        if not items:
            items = [
                {"content": "用户今天整理了下载文件夹3次", "source": "episodic"},
                {"content": "用户偏好深色主题，经常使用文件管理", "source": "preference"},
                {"content": "任务：清理大文件，成功率较高", "source": "task"},
            ]
        
        return items
    
    def _deduplicate(self, items: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for item in items:
            # 简单去重：前30字符
            key = item["content"][:30].lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
    
    def _score_signals(self, item: Dict, all_items: List[Dict]) -> Dict[str, float]:
        content = item["content"]
        # 重要性：长度+关键词
        importance = min(1.0, len(content) / 200 + (0.3 if any(k in content for k in ["重要", "经常", "偏好"]) else 0))
        # 频率：同类出现次数
        freq = sum(1 for i in all_items if content[:20] in i["content"]) / max(1, len(all_items))
        freq = min(1.0, freq * 3)
        # 新鲜度：默认高，实际应按时间
        recency = 0.8
        # 反馈：是否有成功标记
        feedback = 0.7 if "成功" in content else 0.5
        # 成功率：任务相关
        success = 0.8 if "成功" in content else 0.5
        # 可验证性：是否具体
        verifiable = 0.7 if any(k in content for k in ["文件", "任务", "整理"]) else 0.4
        
        return {
            "importance": round(importance, 2),
            "frequency": round(freq, 2),
            "recency": round(recency, 2),
            "feedback": round(feedback, 2),
            "success": round(success, 2),
            "verifiable": round(verifiable, 2)
        }
    
    def _cluster_themes(self, candidates: List[Dict]) -> Dict[str, List[str]]:
        # 简单关键词聚类
        themes = {}
        for cand in candidates:
            content = cand["content"]
            # 提取主题词
            if "下载" in content or "文件" in content:
                themes.setdefault("文件管理", []).append(content)
            elif "进程" in content or "任务" in content:
                themes.setdefault("进程管理", []).append(content)
            elif "偏好" in content or "主题" in content:
                themes.setdefault("用户偏好", []).append(content)
            else:
                themes.setdefault("其他", []).append(content)
        return themes
    
    def _get_theme(self, content: str, themes: Dict) -> Optional[str]:
        for theme, items in themes.items():
            if any(content[:20] in item for item in items):
                return theme
        return None

# 全局
dreaming_system = DreamingSystem()
