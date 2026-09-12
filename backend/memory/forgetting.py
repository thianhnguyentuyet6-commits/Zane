# -*- coding: utf-8 -*-
"""
遗忘机制 - 低价值自动遗忘
"""
import time
from typing import Dict, List, Any

class ForgettingMechanism:
    """遗忘机制"""
    
    def __init__(self):
        self.threshold_access = 3
        self.threshold_importance = 0.3
        self.threshold_days = 30
    
    def should_forget(self, memory: Dict) -> bool:
        """是否应该遗忘"""
        access_count = memory.get("access_count", 0)
        importance = memory.get("importance", memory.get("importance_score", 0.5))
        created_at = memory.get("created_at", time.time())
        last_accessed = memory.get("last_accessed", created_at)
        
        days_since_created = (time.time() - created_at) / 86400
        days_since_access = (time.time() - last_accessed) / 86400
        
        # 低访问+低重要性+超30天 → 遗忘
        if access_count < self.threshold_access and importance < self.threshold_importance and days_since_created > self.threshold_days:
            return True
        
        # 长期未访问>60天
        if days_since_access > 60 and importance < 0.5:
            return True
        
        return False
    
    def forget_batch(self, memories: List[Dict]) -> Dict[str, Any]:
        """批量遗忘"""
        to_forget = []
        retained = []
        
        for mem in memories:
            if self.should_forget(mem):
                to_forget.append(mem)
            else:
                retained.append(mem)
        
        return {
            "total": len(memories),
            "to_forget": len(to_forget),
            "retained": len(retained),
            "forgotten_ids": [m.get("id", "") for m in to_forget],
            "note": f"遗忘阈值：访问<{self.threshold_access} + 重要性<{self.threshold_importance} + {self.threshold_days}天"
        }

# 全局
forgetting_mechanism = ForgettingMechanism()
