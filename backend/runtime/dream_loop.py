# -*- coding: utf-8 -*-
"""
Dream Loop - 2026最新 梦境循环 + 自进化 + 记忆巩固
- 模拟 Karpathy autoresearch 630行脚本循环
- 3阶段：Dream(梦境生成) + Evolve(进化) + Consolidate(巩固)
- 参考：openclaw memory dreaming, Q-Evolve, AlphaEvolve
"""
import os
import time
import json
import random
from typing import Dict, List, Any, Optional
from enum import Enum

class DreamPhase(Enum):
    DREAM = "梦境"
    EVOLVE = "进化"
    CONSOLIDATE = "巩固"

class DreamLoop:
    """梦境循环 - 2026最新"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data")
        self.dream_path = os.path.join(self.data_dir, "dreams.json")
        self.dreams: List[Dict] = []
        self.load_dreams()
    
    def load_dreams(self):
        if os.path.exists(self.dream_path):
            try:
                with open(self.dream_path, 'r', encoding='utf-8') as f:
                    self.dreams = json.load(f)
            except Exception:
                self.dreams = []
    
    def save_dreams(self):
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.dream_path, 'w', encoding='utf-8') as f:
                json.dump(self.dreams[-100:], f, ensure_ascii=False, indent=2)  # 保留最近100个
        except Exception as e:
            print(f"梦境保存失败: {e}")
    
    def dream_generation(self, memories: List[Dict], skills: List[Dict]) -> List[Dict]:
        """阶段1：梦境生成 - 从记忆和技能生成假设"""
        dreams = []
        
        # 1. 记忆重放 + 噪声
        for mem in memories[-10:]:  # 最近10条记忆
            # 添加噪声，生成变体
            dream = {
                "id": f"dream_{int(time.time()*1000)}_{random.randint(1000,9999)}",
                "type": "memory_replay",
                "source": mem.get("id", "unknown"),
                "content": mem.get("content", "")[:200],
                "variation": f"假设 {mem.get('content', '')[:50]} 在不同上下文 {random.choice(['工作', '家庭', '学习'])} 会如何",
                "timestamp": time.time(),
                "phase": DreamPhase.DREAM.value
            }
            dreams.append(dream)
        
        # 2. 技能组合 - 尝试组合技能生成新任务
        if len(skills) >= 2:
            for i in range(min(3, len(skills))):
                s1 = random.choice(skills)
                s2 = random.choice(skills)
                if s1 != s2:
                    dream = {
                        "id": f"dream_combine_{int(time.time()*1000)}_{i}",
                        "type": "skill_combination",
                        "source": f"{s1.get('name','')} + {s2.get('name','')}",
                        "content": f"组合技能 {s1.get('name','')} 和 {s2.get('name','')} 完成新任务",
                        "variation": f"如果用 {s1.get('description','')} 加上 {s2.get('description','')} 能否更快",
                        "timestamp": time.time(),
                        "phase": DreamPhase.DREAM.value
                    }
                    dreams.append(dream)
        
        # 3. 反事实推理 - 如果当初不同会怎样
        counterfactual = {
            "id": f"dream_counter_{int(time.time()*1000)}",
            "type": "counterfactual",
            "source": "failure_analysis",
            "content": "回顾失败任务，如果当初使用不同工具或策略会怎样",
            "variation": "假设任务失败是因为工具选择错误，改用其他工具是否成功",
            "timestamp": time.time(),
            "phase": DreamPhase.DREAM.value
        }
        dreams.append(counterfactual)
        
        return dreams
    
    def evolve_dreams(self, dreams: List[Dict], evolution_engine=None) -> List[Dict]:
        """阶段2：进化 - 评估梦境，生成新原则"""
        evolved = []
        
        for dream in dreams:
            # 评估梦境是否有价值
            # 演示：随机评估，实际应用Q-Evolve in-distribution critic
            value_score = random.uniform(0.3, 0.9)
            
            if value_score > 0.6:
                # 有价值，生成新原则
                principle = {
                    "id": f"principle_{dream['id']}",
                    "type": "evolved_principle",
                    "source_dream": dream["id"],
                    "content": f"从梦境 {dream['type']} 提炼原则：{dream['variation']}",
                    "value_score": value_score,
                    "timestamp": time.time(),
                    "phase": DreamPhase.EVOLVE.value
                }
                evolved.append(principle)
                
                # 如果有进化引擎，添加经验
                if evolution_engine and hasattr(evolution_engine, 'add_experience'):
                    try:
                        evolution_engine.add_experience(
                            task=f"梦境进化 {dream['type']}",
                            success=value_score > 0.7,
                            feedback=f"梦境价值 {value_score:.2f}，{dream['variation']}"
                        )
                    except Exception:
                        pass
        
        return evolved
    
    def consolidate_memories(self, evolved_principles: List[Dict], memory_system=None) -> Dict[str, Any]:
        """阶段3：巩固 - 将进化原则固化到记忆"""
        consolidated = []
        
        for principle in evolved_principles:
            if memory_system and hasattr(memory_system, 'add_memory'):
                try:
                    # 添加到语义记忆
                    mem_id = memory_system.add_memory(
                        content=principle["content"],
                        type="semantic",
                        importance=principle["value_score"],
                        tags=["dream", "evolved", principle["type"]]
                    )
                    consolidated.append({"principle": principle["id"], "memory_id": mem_id, "success": True})
                except Exception as e:
                    consolidated.append({"principle": principle["id"], "error": str(e), "success": False})
            else:
                consolidated.append({"principle": principle["id"], "note": "无记忆系统，演示", "success": True})
        
        return {
            "total": len(evolved_principles),
            "consolidated": len([c for c in consolidated if c["success"]]),
            "details": consolidated
        }
    
    async def run_dream_cycle(self, memory_system=None, skill_library=None, evolution_engine=None) -> Dict[str, Any]:
        """运行完整梦境循环 - 3阶段"""
        print("🌙 梦境循环启动 - 3阶段 Dream + Evolve + Consolidate")
        
        # 获取数据
        memories = []
        skills = []
        
        if memory_system and hasattr(memory_system, 'memories'):
            memories = [{"id": m.id, "content": m.content} for m in memory_system.memories[-20:]] if hasattr(memory_system, 'memories') else []
        elif memory_system and hasattr(memory_system, 'get_stats'):
            # 尝试获取
            memories = [{"id": "mem_demo", "content": "演示记忆"}]
        
        if skill_library and hasattr(skill_library, 'skills'):
            skills = [{"name": s.name, "description": s.description} for s in skill_library.skills] if hasattr(skill_library, 'skills') else []
        
        # 阶段1：梦境生成
        print("  阶段1: 梦境生成")
        dreams = self.dream_generation(memories, skills)
        print(f"    生成 {len(dreams)} 个梦境")
        
        # 阶段2：进化
        print("  阶段2: 进化")
        evolved = self.evolve_dreams(dreams, evolution_engine)
        print(f"    进化 {len(evolved)} 个原则，来自 {len(dreams)} 梦境")
        
        # 阶段3：巩固
        print("  阶段3: 巩固")
        consolidation = self.consolidate_memories(evolved, memory_system)
        print(f"    巩固 {consolidation['consolidated']}/{consolidation['total']}")
        
        # 保存梦境
        self.dreams.extend(dreams)
        self.dreams.extend(evolved)
        self.save_dreams()
        
        return {
            "timestamp": time.time(),
            "phase": "complete",
            "dreams_generated": len(dreams),
            "principles_evolved": len(evolved),
            "consolidated": consolidation["consolidated"],
            "total_memories": len(self.dreams),
            "dreams": dreams[:5],  # 返回前5个示例
            "evolved": evolved[:5],
            "consolidation": consolidation,
            "note": "梦境循环 3阶段，模拟 Karpathy autoresearch 630行，openclaw memory dreaming"
        }

# 全局
dream_loop = DreamLoop()
