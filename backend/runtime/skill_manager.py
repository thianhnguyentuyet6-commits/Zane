# -*- coding: utf-8 -*-
"""
Skill Manager - 技能管理器
版本化可复用，含触发条件、所需工具、流程、参数、前置、验证、恢复、版本
"""
import os
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Skill:
    id: str
    name: str
    description: str
    version: str
    trigger_conditions: List[str]  # 触发关键词
    required_tools: List[str]
    procedure: List[Dict]  # 步骤
    parameters: Dict
    preconditions: List[str]
    verification_rules: List[str]
    failure_recovery: Dict
    success_count: int = 0
    failure_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)

class SkillManager:
    """技能管理器 - 版本化可复用"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data", "skills")
        os.makedirs(self.data_dir, exist_ok=True)
        self.skills: Dict[str, Skill] = {}
        self.load()
        
        # 预置技能
        self._ensure_builtin_skills()
    
    def _ensure_builtin_skills(self):
        if "organize_downloads" not in self.skills:
            self.create_skill(
                name="organize_downloads",
                description="整理下载文件夹，按类型分类到子文件夹",
                trigger_conditions=["整理下载", "下载太乱", "归类下载", "organize downloads"],
                required_tools=["list_files", "create_folder", "move_file"],
                procedure=[
                    {"step": 1, "tool": "list_files", "params": {"path": "C:\\Users\\User\\Downloads", "detail": True}, "verification": "文件列表非空"},
                    {"step": 2, "tool": "create_folder", "params": {"path": "C:\\Users\\User\\Downloads\\文档"}, "verification": "文件夹存在"},
                    {"step": 3, "tool": "move_file", "params": {"source": "*.pdf", "dest": "文档"}, "verification": "目标存在文件"},
                ],
                tags=["文件", "整理"]
            )
    
    def create_skill(self, name: str, description: str, trigger_conditions: List[str],
                     required_tools: List[str], procedure: List[Dict],
                     parameters: Dict = None, preconditions: List[str] = None,
                     verification_rules: List[str] = None, failure_recovery: Dict = None,
                     tags: List[str] = None) -> Skill:
        
        skill = Skill(
            id=f"skill_{name}_{int(time.time())}",
            name=name,
            description=description,
            version="1.0.0",
            trigger_conditions=trigger_conditions,
            required_tools=required_tools,
            procedure=procedure,
            parameters=parameters or {},
            preconditions=preconditions or [],
            verification_rules=verification_rules or [],
            failure_recovery=failure_recovery or {"retry": 2, "fallback": "ask_user"},
            tags=tags or []
        )
        
        self.skills[name] = skill
        self.save()
        return skill
    
    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)
    
    def match_skill(self, intent: str) -> Optional[Skill]:
        """根据意图匹配技能"""
        intent_lower = intent.lower()
        best_match = None
        best_score = 0
        
        for skill in self.skills.values():
            score = sum(1 for cond in skill.trigger_conditions if cond.lower() in intent_lower)
            if score > best_score:
                best_score = score
                best_match = skill
        
        return best_match if best_score > 0 else None
    
    def record_success(self, skill_name: str):
        if skill_name in self.skills:
            self.skills[skill_name].success_count += 1
            self.skills[skill_name].updated_at = time.time()
            self.save()
    
    def record_failure(self, skill_name: str):
        if skill_name in self.skills:
            self.skills[skill_name].failure_count += 1
            self.save()
    
    def list_skills(self) -> List[Dict]:
        return [
            {
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "triggers": s.trigger_conditions,
                "tools": s.required_tools,
                "steps": len(s.procedure),
                "success": s.success_count,
                "failure": s.failure_count,
                "success_rate": round(s.success_count / max(1, s.success_count + s.failure_count) * 100, 1),
                "tags": s.tags
            }
            for s in self.skills.values()
        ]
    
    def save(self):
        try:
            path = os.path.join(self.data_dir, "skills.json")
            data = {name: skill.__dict__ for name, skill in self.skills.items()}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存技能失败: {e}")
    
    def load(self):
        try:
            path = os.path.join(self.data_dir, "skills.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, s_data in data.items():
                        self.skills[name] = Skill(**s_data)
        except Exception as e:
            print(f"加载技能失败: {e}")

# 全局
skill_manager = SkillManager()
