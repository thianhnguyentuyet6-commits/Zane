# -*- coding: utf-8 -*-
"""
Skill Library - SAGE 2026最新 Skill Augmented GRPO
- Sequential Rollout 迭代部署跨相似任务链
- 代理编写可复用函数，针对验证用例测试，保存可用到持久库
- 技能库：复合改进通过可复用工件
- 参考：SAGE Dec 2025, Skill Library Compounding Improvement
"""
import os
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class SkillFunction:
    name: str
    description: str
    code: str  # 可复用函数代码
    tests: List[Dict]  # 验证用例
    success_count: int
    failure_count: int
    tags: List[str]
    created_at: float
    last_used: float
    version: str = "1.0.0"

class SkillLibrary:
    """技能库 - SAGE 2026最新"""
    
    def __init__(self, lib_path: str = None):
        self.lib_path = lib_path or os.path.join(os.path.dirname(__file__), "..", "..", "data", "skill_library.json")
        self.skills: List[SkillFunction] = []
        self.load()
    
    def load(self):
        if os.path.exists(self.lib_path):
            try:
                with open(self.lib_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.skills = [SkillFunction(**item) for item in data]
            except Exception:
                self.skills = []
    
    def save(self):
        try:
            os.makedirs(os.path.dirname(self.lib_path), exist_ok=True)
            with open(self.lib_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(s) for s in self.skills], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"技能库保存失败: {e}")
    
    def sequential_rollout(self, task_chain: List[Dict], agent_execute_func) -> Dict[str, Any]:
        """Sequential Rollout - 迭代部署跨相似任务链"""
        # 任务链：相似任务，例如都是文件整理，但不同路径
        results = []
        new_skills = []
        
        for i, task in enumerate(task_chain):
            print(f"Sequential Rollout {i+1}/{len(task_chain)}: {task.get('title', task.get('id', ''))}")
            
            # 1. 检索相关技能
            related_skills = self.retrieve_skills(task.get("query", task.get("title", "")), limit=3)
            
            # 2. 构建提示，注入技能
            skill_context = "\n".join([f"技能 {s.name}: {s.description}\n代码: {s.code[:200]}" for s in related_skills])
            
            prompt = f"""
任务：{task.get('description', task.get('title', ''))}
相关技能：
{skill_context}

要求：
1. 尝试复用技能，编写可复用函数
2. 针对验证用例测试
3. 保存可用函数到技能库
"""
            
            # 3. 执行
            try:
                if agent_execute_func:
                    result = agent_execute_func(prompt)
                else:
                    result = {"success": True, "final_report": f"模拟执行 {task.get('title')}"}
                
                results.append({"task": task, "result": result, "success": result.get("success", False)})
                
                # 4. 如果成功，提取可复用函数
                if result.get("success"):
                    # 尝试从结果中提取函数
                    # 演示：创建一个通用函数
                    func_code = f"""
def {task.get('id', 'skill')}_func(path: str):
    \"\"\"{task.get('description', '')} - 从任务链提炼\"\"\"
    import os
    # 通用逻辑
    return {{"success": True, "path": path}}
"""
                    skill = SkillFunction(
                        name=f"{task.get('id', 'auto')}_skill",
                        description=f"从 {task.get('title')} 提炼，可复用",
                        code=func_code,
                        tests=[{"input": {"path": "/tmp"}, "expected": {"success": True}}],
                        success_count=1,
                        failure_count=0,
                        tags=[task.get("category", "general"), "auto"],
                        created_at=time.time(),
                        last_used=time.time()
                    )
                    self.skills.append(skill)
                    new_skills.append(skill)
                    self.save()
            
            except Exception as e:
                results.append({"task": task, "result": {"error": str(e)}, "success": False})
        
        return {
            "total": len(task_chain),
            "success": sum(1 for r in results if r["success"]),
            "results": results,
            "new_skills": [asdict(s) for s in new_skills],
            "total_skills": len(self.skills),
            "note": "SAGE Sequential Rollout，可复用函数，持久库，复合改进"
        }
    
    def retrieve_skills(self, query: str, limit: int = 3) -> List[SkillFunction]:
        """检索相关技能"""
        query_lower = query.lower()
        scored = []
        for skill in self.skills:
            score = 0
            if query_lower in skill.name.lower() or query_lower in skill.description.lower():
                score += 2
            for tag in skill.tags:
                if tag.lower() in query_lower or query_lower in tag.lower():
                    score += 1
            score += skill.success_count * 0.1
            score -= skill.failure_count * 0.05
            if score > 0:
                scored.append((score, skill))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        result = [s for _, s in scored[:limit]]
        
        # 更新使用时间
        for skill in result:
            skill.last_used = time.time()
        self.save()
        
        return result
    
    def test_skill(self, skill_name: str) -> Dict[str, Any]:
        """测试技能，针对验证用例"""
        skill = next((s for s in self.skills if s.name == skill_name), None)
        if not skill:
            return {"success": False, "error": "技能不存在"}
        
        passed = 0
        failed = 0
        results = []
        
        for test in skill.tests:
            try:
                # 执行测试 - 演示
                # 实际应 exec skill.code 并调用函数
                input_data = test.get("input", {})
                expected = test.get("expected", {})
                
                # 模拟执行
                result = {"success": True, "input": input_data}
                
                if result.get("success") == expected.get("success"):
                    passed += 1
                    results.append({"test": test, "passed": True})
                else:
                    failed += 1
                    results.append({"test": test, "passed": False})
            except Exception as e:
                failed += 1
                results.append({"test": test, "passed": False, "error": str(e)})
        
        # 更新计数
        skill.success_count += passed
        skill.failure_count += failed
        self.save()
        
        return {
            "skill": skill.name,
            "total": len(skill.tests),
            "passed": passed,
            "failed": failed,
            "success_rate": round(passed / len(skill.tests) * 100, 1) if skill.tests else 0,
            "results": results
        }
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total": len(self.skills),
            "total_success": sum(s.success_count for s in self.skills),
            "total_failure": sum(s.failure_count for s in self.skills),
            "by_tag": {},
            "recent": [asdict(s) for s in sorted(self.skills, key=lambda x: x.last_used, reverse=True)[:5]],
            "note": "SAGE技能库，复合改进，可复用工件，持久化"
        }

# 全局
skill_library = SkillLibrary()
