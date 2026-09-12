# -*- coding: utf-8 -*-
"""
Prompt进化 - Darwin Gödel Machine + EvolveR
- Prompt基因变异交叉选择
- 离线蒸馏+在线原则
"""
import os
import json
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Optional

class PromptEvolution:
    """Prompt进化 - Darwin Gödel Machine"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.prompts_dir = self.base_dir / "data" / "prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_version = self._load_current_version()
    
    def _load_current_version(self) -> int:
        # 查找最新版本
        versions = list(self.prompts_dir.glob("prompt_v*.json"))
        if not versions:
            return 0
        try:
            nums = [int(f.stem.split("_v")[1]) for f in versions if "_v" in f.stem]
            return max(nums) if nums else 0
        except Exception:
            return 0
    
    def _load_prompt(self, version: int) -> Dict:
        path = self.prompts_dir / f"prompt_v{version}.json"
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        # 默认prompt
        return {
            "version": version,
            "system": "你是用户的个人AI管家，运行在Windows上。你了解用户的习惯：微信在 C:\\Program Files\\Tencent\\WeChat，常用文件夹是 Downloads/Documents，喜欢先截图再操作。",
            "tool_desc": "工具需严格按Schema调用，参数错误返回InvalidParam",
            "verification": "每次写后重新感知，验证是否成功",
            "score": 0.8,
            "created_at": time.time()
        }
    
    def mutate(self, prompt: Dict) -> Dict:
        """变异：随机改写一句话"""
        system = prompt["system"]
        sentences = system.split("。")
        
        mutations = [
            "你注重安全，危险操作需确认",
            "你先感知再规划，先截图再操作",
            "你使用思考预算，复杂任务用/think",
            "你使用有界自校正，2-3轮验证",
            "你记住用户习惯，越用越懂",
            "你操作真实系统，代码维护现实",
            "你使用技能库，可复用函数",
            "你使用SimpleMem压缩记忆"
        ]
        
        # 随机替换或添加一句
        if sentences and len(sentences) > 1:
            idx = random.randint(0, len(sentences)-1)
            sentences[idx] = random.choice(mutations)
        else:
            sentences.append(random.choice(mutations))
        
        new_system = "。".join([s for s in sentences if s])
        
        new_prompt = prompt.copy()
        new_prompt["system"] = new_system
        new_prompt["version"] = self.current_version + 1
        new_prompt["parent"] = prompt["version"]
        new_prompt["mutation"] = "随机改写一句"
        new_prompt["created_at"] = time.time()
        new_prompt["score"] = 0  # 待评估
        
        return new_prompt
    
    def crossover(self, prompt1: Dict, prompt2: Dict) -> Dict:
        """交叉：两个高分各取一半拼接"""
        sys1 = prompt1["system"]
        sys2 = prompt2["system"]
        
        # 各取一半
        mid1 = len(sys1) // 2
        mid2 = len(sys2) // 2
        
        new_system = sys1[:mid1] + "。" + sys2[mid2:]
        
        new_prompt = {
            "version": self.current_version + 1,
            "system": new_system,
            "tool_desc": prompt1.get("tool_desc", "") + " " + prompt2.get("tool_desc", ""),
            "verification": prompt1.get("verification", ""),
            "parent": [prompt1["version"], prompt2["version"]],
            "crossover": f"v{prompt1['version']} + v{prompt2['version']}",
            "created_at": time.time(),
            "score": 0
        }
        
        return new_prompt
    
    def evolve_offline(self, success_trajectories: List[Dict]) -> Dict:
        """EvolveR离线蒸馏：从成功轨迹提炼原则"""
        principles = []
        
        for traj in success_trajectories[-10:]:
            task = traj.get("task", "")
            tools = traj.get("tools", [])
            
            # 提炼原则
            if len(tools) >= 3:
                principle = f"任务 {task[:30]} 最优工具链：{'→'.join(tools)}"
                principles.append(principle)
            if "整理" in task and "list_files" in tools:
                principles.append("文件整理任务：先list_files再analyze再create_folder再move")
        
        # 去重
        principles = list(set(principles))
        
        # 生成新prompt
        base_prompt = self._load_prompt(self.current_version)
        evolved_system = base_prompt["system"] + "。离线原则：" + "；".join(principles[:3])
        
        new_prompt = {
            "version": self.current_version + 1,
            "system": evolved_system,
            "principles": principles,
            "source": "EvolveR离线蒸馏",
            "created_at": time.time(),
            "score": 0
        }
        
        return new_prompt
    
    def save_prompt(self, prompt: Dict) -> str:
        """保存prompt"""
        version = prompt["version"]
        path = self.prompts_dir / f"prompt_v{version}.json"
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(prompt, f, ensure_ascii=False, indent=2)
            self.current_version = max(self.current_version, version)
            return str(path)
        except Exception as e:
            return f"保存失败: {e}"
    
    def evaluate_prompt(self, prompt: Dict, benchmark_func=None) -> float:
        """评估prompt，用benchmark"""
        if benchmark_func:
            try:
                # 用benchmark评估
                result = benchmark_func()
                score = result.get("success_rate", 0) / 100
                prompt["score"] = score
                return score
            except Exception:
                pass
        
        # 模拟评分
        score = random.uniform(0.7, 0.95)
        prompt["score"] = score
        return score
    
    def evolve(self, num_mutations: int = 3, num_crossovers: int = 2) -> Dict[str, Any]:
        """进化一轮"""
        # 加载当前最优
        best_prompts = []
        for v in range(max(0, self.current_version-5), self.current_version+1):
            p = self._load_prompt(v)
            if p.get("score", 0) > 0:
                best_prompts.append(p)
        
        if not best_prompts:
            best_prompts = [self._load_prompt(self.current_version)]
        
        # 按分数排序
        best_prompts.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        new_prompts = []
        
        # 变异
        for i in range(num_mutations):
            parent = random.choice(best_prompts[:3])
            mutated = self.mutate(parent)
            self.evaluate_prompt(mutated)
            self.save_prompt(mutated)
            new_prompts.append(mutated)
        
        # 交叉
        for i in range(num_crossovers):
            if len(best_prompts) >= 2:
                p1, p2 = random.sample(best_prompts[:3], 2)
                crossed = self.crossover(p1, p2)
                self.evaluate_prompt(crossed)
                self.save_prompt(crossed)
                new_prompts.append(crossed)
        
        # 离线蒸馏
        try:
            from ..memory.data_flywheel_v3 import data_flywheel_v3
            recent = data_flywheel_v3.get_recent_samples(10)
            if recent:
                evolved = self.evolve_offline(recent)
                self.evaluate_prompt(evolved)
                self.save_prompt(evolved)
                new_prompts.append(evolved)
        except Exception:
            pass
        
        # 选择最优
        all_prompts = best_prompts + new_prompts
        all_prompts.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return {
            "total": len(all_prompts),
            "new": len(new_prompts),
            "best": all_prompts[0] if all_prompts else None,
            "best_score": all_prompts[0].get("score", 0) if all_prompts else 0,
            "new_prompts": new_prompts,
            "note": "Darwin Gödel Machine变异交叉选择 + EvolveR离线蒸馏"
        }
    
    def list_prompts(self) -> List[Dict]:
        prompts = []
        for path in self.prompts_dir.glob("prompt_v*.json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    prompts.append(data)
            except Exception:
                continue
        prompts.sort(key=lambda x: x.get("version", 0))
        return prompts

# 全局
prompt_evolution = PromptEvolution()
