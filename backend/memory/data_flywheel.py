# -*- coding: utf-8 -*-
"""
数据飞轮 - Data Flywheel
从日常使用自动收集 SFT/DPO 训练数据
核心：让模型越用越懂你
"""
import os
import json
import time
from typing import Dict, List, Any
from datetime import datetime

class DataFlywheel:
    """数据飞轮 - 自动将经验转化为训练数据"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "training")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.sft_path = os.path.join(self.data_dir, "sft.jsonl")
        self.dpo_path = os.path.join(self.data_dir, "dpo.jsonl")
        self.replay_path = os.path.join(self.data_dir, "replay_buffer.jsonl")
        self.stats_path = os.path.join(self.data_dir, "stats.json")
        
        self.stats = self._load_stats()

    def _load_stats(self) -> Dict:
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"total_sft": 0, "total_dpo": 0, "last_train": 0, "samples_today": 0}

    def _save_stats(self):
        with open(self.stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    def collect_from_success(self, task: str, tools_used: List[str], reasoning: str, final_report: str, system_state: Dict = None) -> Dict:
        """
        成功任务 → SFT 数据
        格式：ShareGPT
        """
        # 构建训练样本
        sample = {
            "id": f"sft_{int(time.time()*1000)}",
            "timestamp": time.time(),
            "type": "sft",
            "conversations": [
                {
                    "from": "system",
                    "value": "你是用户的个人AI管家，运行在Windows上。你了解用户的习惯：微信在 C:\\Program Files\\Tencent\\WeChat，常用文件夹是 Downloads/Documents，喜欢先截图再操作。"
                },
                {
                    "from": "human",
                    "value": f"任务：{task}\n当前系统：{json.dumps(system_state or {}, ensure_ascii=False)[:500]}"
                },
                {
                    "from": "gpt",
                    "value": f"<think>{reasoning}</think>\n\n我来帮你执行：\n使用的工具链：{' → '.join(tools_used)}\n\n执行步骤：\n{final_report[:1000]}\n\n验证：已检查真实系统状态，任务完成。"
                }
            ],
            "tools": tools_used,
            "task": task,
            "quality_score": 0.85,  # 可用小模型打分
            "source": "success_trajectory"
        }
        
        # 写入文件
        with open(self.sft_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        
        self.stats["total_sft"] += 1
        self.stats["samples_today"] += 1
        self._save_stats()
        
        return sample

    def collect_from_failure(self, task: str, failed_attempt: str, corrected: str, reflection: str) -> Dict:
        """
        失败+修正 → DPO 偏好数据
        Chosen: 正确做法
        Rejected: 失败做法
        """
        sample = {
            "id": f"dpo_{int(time.time()*1000)}",
            "timestamp": time.time(),
            "type": "dpo",
            "prompt": f"任务：{task}\n系统：Windows 10，中文环境",
            "chosen": corrected,
            "rejected": failed_attempt,
            "reflection": reflection,
            "quality_score": 0.9,
            "source": "failure_correction"
        }
        
        with open(self.dpo_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        
        self.stats["total_dpo"] += 1
        self._save_stats()
        
        return sample

    def collect_skill(self, skill_name: str, steps: List[Dict], parameters: Dict = None) -> Dict:
        """技能 → 参数化指令数据"""
        sample = {
            "id": f"skill_{int(time.time()*1000)}",
            "timestamp": time.time(),
            "type": "skill",
            "skill_name": skill_name,
            "instruction": f"执行技能：{skill_name}",
            "steps": steps,
            "parameters": parameters or {},
            "source": "skill_distillation"
        }
        
        # 技能也存入 SFT
        sft_sample = {
            "id": f"sft_skill_{int(time.time()*1000)}",
            "timestamp": time.time(),
            "type": "sft",
            "conversations": [
                {"from": "system", "value": "你是个人AI管家，拥有技能库。"},
                {"from": "human", "value": f"使用技能：{skill_name}，参数：{json.dumps(parameters or {}, ensure_ascii=False)}"},
                {"from": "gpt", "value": f"调用技能 {skill_name}，步骤：{json.dumps(steps, ensure_ascii=False)}"}
            ],
            "tools": [s.get("tool", "") for s in steps],
            "task": skill_name,
            "quality_score": 0.9,
            "source": "skill"
        }
        
        with open(self.sft_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(sft_sample, ensure_ascii=False) + "\n")
        
        return sft_sample

    def get_training_stats(self) -> Dict:
        """获取训练数据统计"""
        sft_count = 0
        dpo_count = 0
        replay_count = 0
        
        try:
            if os.path.exists(self.sft_path):
                with open(self.sft_path, 'r', encoding='utf-8') as f:
                    sft_count = sum(1 for _ in f)
            if os.path.exists(self.dpo_path):
                with open(self.dpo_path, 'r', encoding='utf-8') as f:
                    dpo_count = sum(1 for _ in f)
            if os.path.exists(self.replay_path):
                with open(self.replay_path, 'r', encoding='utf-8') as f:
                    replay_count = sum(1 for _ in f)
        except:
            pass
        
        return {
            "sft_samples": sft_count,
            "dpo_samples": dpo_count,
            "replay_samples": replay_count,
            "total": sft_count + dpo_count,
            "ready_for_training": sft_count >= 50,
            "samples_today": self.stats.get("samples_today", 0),
            "last_train": self.stats.get("last_train", 0),
            "next_train_in": max(0, 50 - sft_count),
            "data_dir": self.data_dir
        }

    def get_recent_samples(self, limit: int = 10) -> List[Dict]:
        """获取最近样本"""
        samples = []
        try:
            if os.path.exists(self.sft_path):
                with open(self.sft_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-limit:]
                    for line in lines:
                        try:
                            samples.append(json.loads(line))
                        except:
                            continue
        except:
            pass
        return list(reversed(samples))

    def build_replay_buffer(self):
        """构建 Replay Buffer - 防止灾难性遗忘"""
        # 保留高质量旧样本 + 通用样本
        # 这里演示逻辑
        replay_samples = [
            {
                "type": "replay",
                "conversations": [
                    {"from": "human", "value": "打开记事本"},
                    {"from": "gpt", "value": "调用 launch_application 工具启动 notepad.exe"}
                ],
                "source": "generic"
            }
        ]
        
        with open(self.replay_path, 'w', encoding='utf-8') as f:
            for s in replay_samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        
        return {"replay_count": len(replay_samples)}

data_flywheel = DataFlywheel()
