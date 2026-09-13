# -*- coding: utf-8 -*-
"""
记忆层 - Memory Layer
持久化长期记忆：会话记忆、语义知识、情景体验、技能、任务经验
"""
import json
import os
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

@dataclass
class ConversationMemory:
    id: str
    timestamp: float
    role: str
    content: str
    tool_calls: List[Dict] = None
    importance: int = 1

@dataclass
class SemanticKnowledge:
    id: str
    timestamp: float
    topic: str
    fact: str
    source: str
    confidence: float
    tags: List[str]

@dataclass
class EpisodicExperience:
    id: str
    timestamp: float
    task: str
    context: str
    actions: List[str]
    result: str
    success: bool
    lessons: List[str]

@dataclass
class Skill:
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    created_at: float
    usage_count: int
    success_rate: float
    tags: List[str]

@dataclass
class TaskExperience:
    id: str
    task_type: str
    problem: str
    solution: str
    tools_used: List[str]
    verification: str
    created_at: float
    reusable: bool

class MemoryLayer:
    """记忆层 - 负责所有持久化记忆"""
    
    def __init__(self):
        ensure_data_dir()
        self.conversations: List[ConversationMemory] = []
        self.semantic_knowledge: List[SemanticKnowledge] = []
        self.episodic: List[EpisodicExperience] = []
        self.skills: List[Skill] = []
        self.experiences: List[TaskExperience] = []
        self.load_all()

    def load_all(self):
        """加载所有记忆"""
        try:
            # 加载示例数据
            for fname, attr in [
                ("memories.json", "conversations"),
                ("semantic.json", "semantic_knowledge"),
                ("episodic.json", "episodic"),
                ("skills.json", "skills"),
                ("experiences.json", "experiences")
            ]:
                path = os.path.join(DATA_DIR, fname)
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        setattr(self, attr, data)
        except Exception as e:
            print(f"[Memory] 加载失败: {e}")
            self._seed_demo_data()

        if not self.conversations:
            self._seed_demo_data()

    def _seed_demo_data(self):
        """播种演示数据，让仪表盘首次启动就鲜活"""
        now = time.time()
        
        # 技能
        self.skills = [
            {
                "id": "skill_001",
                "name": "微信自动启动与登录检查",
                "description": "自动启动微信并验证是否成功登录，包含窗口检测和异常重试",
                "steps": [
                    {"tool": "list_windows", "desc": "检查微信是否已运行"},
                    {"tool": "launch_application", "desc": "启动微信"},
                    {"tool": "take_screenshot", "desc": "截图验证登录界面"},
                    {"tool": "ocr_screenshot", "desc": "识别登录状态"}
                ],
                "created_at": now - 86400*3,
                "usage_count": 12,
                "success_rate": 0.92,
                "tags": ["微信", "启动", "自动化"]
            },
            {
                "id": "skill_002",
                "name": "系统内存清理流程",
                "description": "分析内存占用，找出大户，安全清理临时文件",
                "steps": [
                    {"tool": "inspect_processes", "desc": "按内存排序进程"},
                    {"tool": "get_system_state", "desc": "获取整体内存状态"},
                    {"tool": "list_files", "desc": "检查临时文件夹"},
                    {"tool": "delete_file", "desc": "清理临时文件（需确认）"}
                ],
                "created_at": now - 86400*5,
                "usage_count": 8,
                "success_rate": 0.88,
                "tags": ["内存", "清理", "性能"]
            },
            {
                "id": "skill_003",
                "name": "文件整理与归档",
                "description": "将下载文件夹按类型自动分类整理",
                "steps": [
                    {"tool": "list_files", "desc": "扫描下载文件夹"},
                    {"tool": "create_folder", "desc": "创建分类文件夹"},
                    {"tool": "write_file", "desc": "移动并记录日志"}
                ],
                "created_at": now - 86400*2,
                "usage_count": 15,
                "success_rate": 0.95,
                "tags": ["文件", "整理", "自动化"]
            },
            {
                "id": "skill_004",
                "name": "窗口智能切换",
                "description": "根据标题关键词快速切换窗口，支持模糊匹配",
                "steps": [
                    {"tool": "list_windows", "desc": "枚举所有窗口"},
                    {"tool": "focus_window", "desc": "聚焦目标窗口"},
                    {"tool": "get_window_info", "desc": "验证窗口状态"}
                ],
                "created_at": now - 86400*1,
                "usage_count": 23,
                "success_rate": 0.97,
                "tags": ["窗口", "切换", "效率"]
            }
        ]

        # 语义知识
        self.semantic_knowledge = [
            {
                "id": "sem_001",
                "timestamp": now - 3600*5,
                "topic": "用户习惯",
                "fact": "用户通常在上午9-11点使用微信和Chrome，下午处理文档文件",
                "source": "行为观察",
                "confidence": 0.85,
                "tags": ["习惯", "时间"]
            },
            {
                "id": "sem_002",
                "timestamp": now - 3600*10,
                "topic": "系统环境",
                "fact": "微信安装在 C:\\Program Files\\Tencent\\WeChat\\WeChat.exe，版本 3.9.8",
                "source": "文件扫描",
                "confidence": 0.95,
                "tags": ["微信", "路径"]
            },
            {
                "id": "sem_003",
                "timestamp": now - 3600*2,
                "topic": "性能基准",
                "fact": "正常情况下内存占用约 65%，Chrome通常占用最多，约 2.5GB",
                "source": "系统监控",
                "confidence": 0.9,
                "tags": ["内存", "Chrome"]
            }
        ]

        # 情景体验
        self.episodic = [
            {
                "id": "epi_001",
                "timestamp": now - 86400,
                "task": "帮我打开微信",
                "context": "用户首次要求打开微信",
                "actions": ["检查窗口", "启动应用", "验证成功"],
                "result": "成功启动微信，窗口句柄 123456",
                "success": True,
                "lessons": ["微信启动需要2-3秒", "需要检查是否已运行避免重复启动"]
            },
            {
                "id": "epi_002",
                "timestamp": now - 3600*6,
                "task": "清理C盘空间",
                "context": "C盘空间不足警告",
                "actions": ["扫描大文件", "清理临时文件", "验证空间"],
                "result": "清理了3.2GB临时文件，但未能完全解决问题",
                "success": False,
                "lessons": ["需要更深入分析大文件来源", "下载文件夹占用了8GB"]
            }
        ]

        # 任务经验
        self.experiences = [
            {
                "id": "exp_001",
                "task_type": "应用启动",
                "problem": "如何可靠地启动Windows应用并验证成功",
                "solution": "先枚举窗口避免重复启动，使用launch_application后等待2秒，再用list_windows验证，最后截图OCR确认界面",
                "tools_used": ["list_windows", "launch_application", "take_screenshot", "ocr_screenshot"],
                "verification": "窗口存在且标题匹配，截图包含应用界面特征",
                "created_at": now - 86400*2,
                "reusable": True
            },
            {
                "id": "exp_002",
                "task_type": "内存分析",
                "problem": "找出内存占用最高的程序",
                "solution": "使用inspect_processes按memory排序，取前10，结合get_system_state获取总览，生成可视化报告",
                "tools_used": ["inspect_processes", "get_system_state"],
                "verification": "对比任务管理器数据，误差<5%",
                "created_at": now - 86400,
                "reusable": True
            },
            {
                "id": "exp_003",
                "task_type": "文件管理",
                "problem": "安全地批量整理文件",
                "solution": "先list_files扫描，创建分类文件夹，逐个移动并记录日志，任何失败都回滚并报告",
                "tools_used": ["list_files", "create_folder", "write_file"],
                "verification": "目标文件夹文件数匹配，源文件夹已清空对应类型",
                "created_at": now - 3600*12,
                "reusable": True
            }
        ]

        self.save_all()

    def save_all(self):
        ensure_data_dir()
        try:
            with open(os.path.join(DATA_DIR, "skills.json"), 'w', encoding='utf-8') as f:
                json.dump(self.skills, f, ensure_ascii=False, indent=2)
            with open(os.path.join(DATA_DIR, "semantic.json"), 'w', encoding='utf-8') as f:
                json.dump(self.semantic_knowledge, f, ensure_ascii=False, indent=2)
            with open(os.path.join(DATA_DIR, "episodic.json"), 'w', encoding='utf-8') as f:
                json.dump(self.episodic, f, ensure_ascii=False, indent=2)
            with open(os.path.join(DATA_DIR, "experiences.json"), 'w', encoding='utf-8') as f:
                json.dump(self.experiences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Memory] 保存失败: {e}")

    def add_conversation(self, role: str, content: str, tool_calls: List[Dict] = None):
        mem = {
            "id": f"conv_{int(time.time()*1000)}",
            "timestamp": time.time(),
            "role": role,
            "content": content,
            "tool_calls": tool_calls or [],
            "importance": 1
        }
        self.conversations.append(mem)
        # 保持最近200条
        if len(self.conversations) > 200:
            self.conversations = self.conversations[-200:]

    def retrieve_relevant(self, query: str, limit: int = 5) -> Dict[str, List]:
        """检索相关记忆"""
        query_lower = query.lower()
        relevant = {
            "skills": [],
            "knowledge": [],
            "episodic": [],
            "experiences": []
        }
        
        # 简单关键词匹配（实际可用向量检索）
        for skill in self.skills:
            if any(k in query_lower for k in [t.lower() for t in skill.get("tags", [])]) or query_lower in skill.get("name", "").lower():
                relevant["skills"].append(skill)
        
        for know in self.semantic_knowledge:
            if any(k in query_lower for k in [t.lower() for t in know.get("tags", [])]) or query_lower in know.get("fact", "").lower():
                relevant["knowledge"].append(know)
                
        for epi in self.episodic:
            if query_lower in epi.get("task", "").lower():
                relevant["episodic"].append(epi)
                
        for exp in self.experiences:
            if query_lower in exp.get("task_type", "").lower() or query_lower in exp.get("problem", "").lower():
                relevant["experiences"].append(exp)
        
        # 限制数量
        for k in relevant:
            relevant[k] = relevant[k][:limit]
            
        return relevant

    def add_experience(self, task_type: str, problem: str, solution: str, tools_used: List[str], verification: str):
        exp = {
            "id": f"exp_{int(time.time()*1000)}",
            "task_type": task_type,
            "problem": problem,
            "solution": solution,
            "tools_used": tools_used,
            "verification": verification,
            "created_at": time.time(),
            "reusable": True
        }
        self.experiences.append(exp)
        self.save_all()
        return exp

    def add_skill(self, name: str, description: str, steps: List[Dict], tags: List[str]):
        skill = {
            "id": f"skill_{int(time.time()*1000)}",
            "name": name,
            "description": description,
            "steps": steps,
            "created_at": time.time(),
            "usage_count": 0,
            "success_rate": 0.0,
            "tags": tags
        }
        self.skills.append(skill)
        self.save_all()
        return skill

memory_layer = MemoryLayer()
