# -*- coding: utf-8 -*-
"""
Memory Manager - 记忆管理器
5种类型不同保留策略：working/episodic/semantic/procedural/preference
"""
import os
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class MemoryItem:
    id: str
    type: str  # working, episodic, semantic, procedural, preference
    content: str
    metadata: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    importance: float = 0.5  # 0-1

class MemoryManager:
    """记忆管理器 - 多类型不同保留"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data", "memory")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 5种记忆
        self.working: List[MemoryItem] = []      # 当前任务结束清空
        self.episodic: List[MemoryItem] = []     # 事件30天衰减
        self.semantic: List[MemoryItem] = []     # 稳定事实永久
        self.procedural: List[MemoryItem] = []   # 成功流程版本化Skill
        self.preference: List[MemoryItem] = []   # 用户行为偏好
        
        self.load()
    
    def add(self, type: str, content: str, metadata: Dict = None, importance: float = 0.5) -> MemoryItem:
        item = MemoryItem(
            id=f"{type}_{int(time.time()*1000)}",
            type=type,
            content=content,
            metadata=metadata or {},
            importance=importance
        )
        
        target = getattr(self, type, None)
        if target is not None:
            target.append(item)
            # 限制数量
            if type == "working" and len(target) > 20:
                target.pop(0)
            elif type == "episodic" and len(target) > 200:
                # 按重要性+时间衰减排序，保留重要
                target.sort(key=lambda x: (x.importance, x.created_at), reverse=True)
                target[:] = target[:200]
        
        self.save()
        return item
    
    def get_relevant(self, query: str, types: List[str] = None, limit: int = 5) -> List[MemoryItem]:
        """检索相关记忆 - 关键词匹配，未来向量"""
        types = types or ["semantic", "episodic", "preference"]
        candidates = []
        for t in types:
            candidates.extend(getattr(self, t, []))
        
        # 简单关键词匹配
        query_lower = query.lower()
        scored = []
        for item in candidates:
            score = 0
            if any(kw in item.content.lower() for kw in query_lower.split()):
                score += 1
            score += item.importance * 0.5
            # 时间衰减 - episodic
            if item.type == "episodic":
                days = (time.time() - item.created_at) / 86400
                decay = max(0.1, 1 - days / 30)  # 30天衰减
                score *= decay
            
            if score > 0:
                scored.append((score, item))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        result = [item for _, item in scored[:limit]]
        
        # 更新访问
        for item in result:
            item.last_accessed = time.time()
            item.access_count += 1
        
        return result
    
    def clear_working(self):
        """任务结束清空 working"""
        self.working.clear()
        self.save()
    
    def decay_episodic(self):
        """衰减过期 episodic"""
        now = time.time()
        self.episodic = [m for m in self.episodic if (now - m.created_at) < 30*86400 or m.importance > 0.8]
        self.save()
    
    def load(self):
        try:
            path = os.path.join(self.data_dir, "memory_manager.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for t in ["working", "episodic", "semantic", "procedural", "preference"]:
                        items = data.get(t, [])
                        setattr(self, t, [MemoryItem(**item) for item in items])
        except Exception as e:
            print(f"加载记忆失败: {e}")
    
    def save(self):
        try:
            path = os.path.join(self.data_dir, "memory_manager.json")
            data = {}
            for t in ["working", "episodic", "semantic", "procedural", "preference"]:
                data[t] = [item.__dict__ for item in getattr(self, t, [])]
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存记忆失败: {e}")

# 全局
memory_manager = MemoryManager()
