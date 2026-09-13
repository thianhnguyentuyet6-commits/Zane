# -*- coding: utf-8 -*-
"""
遗忘机制 v0914 - 低价值自动遗忘 + 4层遗忘曲线 + DREAMS.md
- 4层遗忘曲线：conversational 7天/episodic 30天/semantic 90天/procedural 180天
- 单元测试：tests/test_forgetting.py 时间流逝模拟
- DREAMS.md：人类可读日记，记录遗忘记忆
"""
import time
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class ForgettingCurveV0914:
    """遗忘机制 v0914 - 4层遗忘曲线"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or __file__).parent.parent.parent
        self.dreams_path = self.base_dir / "data" / "DREAMS.md"
        
        # 4层遗忘曲线 - 不同类型不同遗忘时间
        self.forgetting_curves = {
            "conversational": 7,   # 会话7天
            "episodic": 30,        # 情景30天
            "semantic": 90,        # 语义90天
            "procedural": 180      # 程序180天
        }
        
        self.threshold_access = 3
        self.threshold_importance = 0.3
        self.threshold_days = 30
        self.high_value_access = 10
        self.high_value_importance = 0.8
    
    def should_forget(self, memory) -> bool:
        """是否应该遗忘 - 支持Dict和对象"""
        # 兼容Dict和对象
        if isinstance(memory, dict):
            access_count = memory.get("access_count", 0)
            importance = memory.get("importance", memory.get("importance_score", 0.5))
            created_at = memory.get("created_at", time.time())
            last_accessed = memory.get("last_accessed", created_at)
            mem_type = memory.get("type", "episodic")
        else:
            access_count = getattr(memory, "access_count", 0)
            importance = getattr(memory, "importance", 0.5)
            created_at = getattr(memory, "created_at", time.time())
            last_accessed = getattr(memory, "last_accessed", created_at)
            mem_type = getattr(memory, "type", "episodic")
        
        days_since_created = (time.time() - created_at) / 86400
        days_since_access = (time.time() - last_accessed) / 86400
        
        # 高价值保留：访问>10重要性>0.8保留，不遗忘
        if access_count > self.high_value_access and importance > self.high_value_importance:
            return False
        
        # 4层遗忘曲线
        curve_days = self.forgetting_curves.get(mem_type, self.threshold_days)
        
        # 低访问+低重要性+超过曲线时间 → 遗忘
        if access_count < self.threshold_access and importance < self.threshold_threshold_importance() and days_since_created > curve_days:
            return True
        
        # 通用阈值
        if access_count < self.threshold_access and importance < self.threshold_importance and days_since_created > self.threshold_days:
            return True
        
        # 长期未访问>60天且重要性<0.5
        if days_since_access > 60 and importance < 0.5:
            return True
        
        # 超过类型曲线2倍时间，即使中等重要性也遗忘
        if days_since_created > curve_days * 2 and importance < 0.6:
            return True
        
        return False
    
    def threshold_threshold_importance(self):
        # 兼容旧命名
        return self.threshold_importance
    
    def get_forget_candidates(self, memories: List) -> List:
        """获取遗忘候选"""
        to_forget = []
        for mem in memories:
            if self.should_forget(mem):
                to_forget.append(mem)
        return to_forget
    
    def forget_batch(self, memories: List) -> Dict[str, Any]:
        """批量遗忘"""
        to_forget = []
        retained = []
        
        for mem in memories:
            if self.should_forget(mem):
                to_forget.append(mem)
            else:
                retained.append(mem)
        
        # 生成DREAMS.md - 人类可读日记
        self._write_dreams(to_forget, retained)
        
        return {
            "total": len(memories),
            "to_forget": len(to_forget),
            "retained": len(retained),
            "forgotten_ids": [getattr(m, "id", m.get("id", "")) if not isinstance(m, dict) else m.get("id", "") for m in to_forget],
            "by_type": self._count_by_type(to_forget),
            "note": f"遗忘阈值：访问<{self.threshold_access} + 重要性<{self.threshold_importance} + 4层曲线 conversational 7天/episodic 30天/semantic 90天/procedural 180天",
            "dreams_path": str(self.dreams_path),
            "curves": self.forgetting_curves
        }
    
    def _count_by_type(self, memories: List) -> Dict:
        by_type = {}
        for mem in memories:
            t = getattr(mem, "type", mem.get("type", "unknown")) if not isinstance(mem, dict) else mem.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        return by_type
    
    def _write_dreams(self, forgotten: List, retained: List):
        """生成DREAMS.md人类可读日记"""
        try:
            self.dreams_path.parent.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now()
            content = f"# Zane DREAMS - {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += f"> 人类可读日记，记录遗忘的记忆，{now.strftime('%Y-%m-%d')} 梦境整理\n\n"
            content += f"## 统计\n\n"
            content += f"- 总记忆：{len(forgotten) + len(retained)}\n"
            content += f"- 遗忘：{len(forgotten)}条\n"
            content += f"- 保留：{len(retained)}条\n"
            content += f"- 遗忘曲线：conversational 7天/episodic 30天/semantic 90天/procedural 180天\n"
            content += f"- 阈值：访问<{self.threshold_access} 重要性<{self.threshold_importance}\n\n"
            
            if forgotten:
                content += f"## 遗忘的记忆 ({len(forgotten)}条)\n\n"
                by_type = self._count_by_type(forgotten)
                content += f"按类型：{by_type}\n\n"
                
                for mem in forgotten[:20]:  # 最多20条
                    mem_id = getattr(mem, "id", mem.get("id", "")) if not isinstance(mem, dict) else mem.get("id", "")
                    mem_type = getattr(mem, "type", mem.get("type", "")) if not isinstance(mem, dict) else mem.get("type", "")
                    mem_content = getattr(mem, "content", mem.get("content", "")) if not isinstance(mem, dict) else mem.get("content", "")
                    mem_importance = getattr(mem, "importance", mem.get("importance", 0)) if not isinstance(mem, dict) else mem.get("importance", 0)
                    mem_access = getattr(mem, "access_count", mem.get("access_count", 0)) if not isinstance(mem, dict) else mem.get("access_count", 0)
                    created = getattr(mem, "created_at", 0) if not isinstance(mem, dict) else mem.get("created_at", 0)
                    age_days = (time.time() - created) / 86400 if created else 0
                    
                    content += f"- **{mem_type}** [{mem_id[:20]}...] 重要性{mem_importance:.2f} 访问{mem_access}次 {age_days:.1f}天前\n"
                    content += f"  内容：{str(mem_content)[:100]}...\n\n"
            else:
                content += f"## 遗忘的记忆\n\n暂无遗忘，全部保留\n\n"
            
            content += f"## 保留的高价值记忆 ({len(retained)}条)\n\n"
            # 按重要性排序显示保留的
            sorted_retained = sorted(
                retained, 
                key=lambda m: getattr(m, "importance", m.get("importance", 0)) if not isinstance(m, dict) else m.get("importance", 0),
                reverse=True
            )
            for mem in sorted_retained[:10]:
                mem_type = getattr(mem, "type", mem.get("type", "")) if not isinstance(mem, dict) else mem.get("type", "")
                mem_content = getattr(mem, "content", mem.get("content", "")) if not isinstance(mem, dict) else mem.get("content", "")
                mem_importance = getattr(mem, "importance", mem.get("importance", 0)) if not isinstance(mem, dict) else mem.get("importance", 0)
                mem_access = getattr(mem, "access_count", mem.get("access_count", 0)) if not isinstance(mem, dict) else mem.get("access_count", 0)
                
                content += f"- **{mem_type}** 重要性{mem_importance:.2f} 访问{mem_access}次\n"
                content += f"  {str(mem_content)[:100]}...\n\n"
            
            content += f"\n---\n\n*自动生成于 {now.strftime('%Y-%m-%d %H:%M:%S')}，遗忘机制最容易埋雷，需单元测试验证*\n"
            
            with open(self.dreams_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"生成DREAMS.md失败: {e}")


class ForgettingMechanism(ForgettingCurveV0914):
    """兼容旧命名"""
    pass


# 为了兼容测试
ForgettingCurve = ForgettingCurveV0914

# 全局 v0914
forgetting_curve = ForgettingCurveV0914()
forgetting_mechanism = forgetting_curve
forgetting_curve_v0914 = forgetting_curve
