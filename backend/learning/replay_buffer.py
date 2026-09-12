# -*- coding: utf-8 -*-
"""
Replay Buffer - 防灾难性遗忘
- 高质量旧样本>0.8随机30%混入新训练
"""
import os
import json
import random
from pathlib import Path
from typing import Dict, List, Any

class ReplayBuffer:
    """Replay Buffer防遗忘"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.data_dir = self.base_dir / "data" / "training"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.sft_path = self.data_dir / "sft.jsonl"
        self.sft_v3_path = self.data_dir / "sft_v3.jsonl"
        self.replay_path = self.data_dir / "replay_buffer.jsonl"
    
    def build(self, ratio: float = 0.3, min_quality: float = 0.8) -> Dict[str, Any]:
        """构建Replay Buffer"""
        all_high_quality = []
        
        # 从SFT v3选高质量
        sft_file = self.sft_v3_path if self.sft_v3_path.exists() else self.sft_path
        
        if sft_file.exists():
            try:
                with open(sft_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if data.get("importance_score", 0.5) >= min_quality or data.get("quality_score", 0.5) >= min_quality:
                                all_high_quality.append(data)
                        except Exception:
                            continue
            except Exception as e:
                return {"replay_count": 0, "error": str(e)}
        
        if not all_high_quality:
            # 通用保底
            all_high_quality = [
                {
                    "type": "replay",
                    "conversations": [
                        {"from": "human", "value": "打开记事本"},
                        {"from": "gpt", "value": "调用 launch_application 工具启动 notepad.exe"}
                    ],
                    "source": "generic",
                    "importance_score": 0.9,
                    "quality_score": 0.9
                },
                {
                    "type": "replay",
                    "conversations": [
                        {"from": "human", "value": "列出下载文件夹"},
                        {"from": "gpt", "value": "调用 list_files 工具列出 Downloads"}
                    ],
                    "source": "generic",
                    "importance_score": 0.9
                }
            ]
        
        # 随机30%
        random.shuffle(all_high_quality)
        num_replay = max(1, int(len(all_high_quality) * ratio))
        replay_samples = all_high_quality[:num_replay]
        
        # 保存
        try:
            with open(self.replay_path, 'w', encoding='utf-8') as f:
                for s in replay_samples:
                    f.write(json.dumps(s, ensure_ascii=False) + "\n")
        except Exception as e:
            return {"replay_count": 0, "error": str(e)}
        
        return {
            "replay_count": len(replay_samples),
            "total_high_quality": len(all_high_quality),
            "ratio": ratio,
            "min_quality": min_quality,
            "replay_path": str(self.replay_path),
            "note": f"Replay Buffer {ratio*100}% 高质量>{min_quality}，防灾难性遗忘"
        }
    
    def get_replay_samples(self, limit: int = None) -> List[Dict]:
        samples = []
        if not self.replay_path.exists():
            return samples
        
        try:
            with open(self.replay_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        samples.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            pass
        
        if limit:
            return samples[:limit]
        return samples

# 全局
replay_buffer = ReplayBuffer()
