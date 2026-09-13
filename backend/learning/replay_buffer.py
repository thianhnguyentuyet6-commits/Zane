# -*- coding: utf-8 -*-
"""
Replay Buffer v0914 - 防灾难性遗忘，可配置阈值
- 阈值0.8改为可配置，config/replay_config.json
- 提供验证脚本，作者可跑不同阈值看效果
"""
import os
import json
import random
from pathlib import Path
from typing import Dict, List, Any


class ReplayBufferV0914:
    """Replay Buffer防遗忘 v0914 - 可配置阈值"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.data_dir = self.base_dir / "data" / "training"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.base_dir / "config" / "replay_config.json"
        
        self.sft_path = self.data_dir / "sft.jsonl"
        self.replay_path = self.data_dir / "replay_buffer.jsonl"
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        default = {
            "min_quality": 0.8,  # 默认0.8，但可配置，无理论依据需验证
            "ratio": 0.3,  # Replay比例30%
            "max_replay_samples": 100,
            "quality_field": "importance_score",  # 质量字段
            "fallback_field": "quality_score",
            "note": "min_quality 0.8无理论依据，可配置，建议跑验证脚本测试不同阈值效果，见tests/test_threshold_validation.py"
        }
        
        # 环境变量覆盖
        env_quality = os.getenv("ZANE_REPLAY_QUALITY")
        if env_quality:
            try:
                default["min_quality"] = float(env_quality)
            except:
                pass
        
        env_ratio = os.getenv("ZANE_REPLAY_RATIO")
        if env_ratio:
            try:
                default["ratio"] = float(env_ratio)
            except:
                pass
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default.update(loaded)
            except Exception:
                pass
        
        # 保存
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
        return default
    
    def build(self, ratio: float = None, min_quality: float = None) -> Dict[str, Any]:
        """构建Replay Buffer - 阈值可配置"""
        use_ratio = ratio if ratio is not None else self.config["ratio"]
        use_quality = min_quality if min_quality is not None else self.config["min_quality"]
        max_samples = self.config.get("max_replay_samples", 100)
        
        all_high_quality = []
        
        # 从SFT选高质量
        if self.sft_path.exists():
            try:
                with open(self.sft_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            quality_field = self.config.get("quality_field", "importance_score")
                            fallback_field = self.config.get("fallback_field", "quality_score")
                            quality = data.get(quality_field, 0.5)
                            if quality < use_quality:
                                quality = data.get(fallback_field, 0.5)
                            
                            if quality >= use_quality:
                                all_high_quality.append(data)
                        except Exception:
                            continue
            except Exception as e:
                return {"replay_count": 0, "error": str(e), "config": self.config}
        
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
        
        # 按质量排序，取高质量
        all_high_quality.sort(key=lambda x: x.get(self.config.get("quality_field", "importance_score"), 0), reverse=True)
        
        # 随机30%或按比例，但不超过max
        random.shuffle(all_high_quality)
        num_replay = max(1, int(len(all_high_quality) * use_ratio))
        num_replay = min(num_replay, max_samples)
        replay_samples = all_high_quality[:num_replay]
        
        # 保存
        try:
            with open(self.replay_path, 'w', encoding='utf-8') as f:
                for s in replay_samples:
                    f.write(json.dumps(s, ensure_ascii=False) + "\n")
        except Exception as e:
            return {"replay_count": 0, "error": str(e), "config": self.config}
        
        return {
            "replay_count": len(replay_samples),
            "total_high_quality": len(all_high_quality),
            "ratio": use_ratio,
            "min_quality": use_quality,
            "max_samples": max_samples,
            "replay_path": str(self.replay_path),
            "config": self.config,
            "config_path": str(self.config_path),
            "note": f"Replay Buffer {use_ratio*100}% 高质量>{use_quality}，防灾难性遗忘，可配置，见tests/test_threshold_validation.py验证不同阈值效果"
        }
    
    def validate_thresholds(self) -> Dict[str, Any]:
        """验证不同阈值效果 - 供作者跑几组数据看不同阈值影响"""
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
        results = {}
        
        # 读取所有样本
        all_samples = []
        if self.sft_path.exists():
            try:
                with open(self.sft_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            all_samples.append(data)
                        except:
                            continue
            except Exception:
                pass
        
        total = len(all_samples)
        
        for thresh in thresholds:
            high_quality = [
                s for s in all_samples 
                if s.get(self.config.get("quality_field", "importance_score"), 0.5) >= thresh
                or s.get(self.config.get("fallback_field", "quality_score"), 0.5) >= thresh
            ]
            replay_count = max(1, int(len(high_quality) * self.config["ratio"]))
            
            results[str(thresh)] = {
                "threshold": thresh,
                "high_quality_count": len(high_quality),
                "total": total,
                "high_quality_ratio": round(len(high_quality)/max(total,1), 3),
                "replay_count": replay_count,
                "replay_ratio": self.config["ratio"]
            }
        
        return {
            "total_samples": total,
            "thresholds": results,
            "current_config": self.config,
            "recommendation": "建议跑tests/test_threshold_validation.py看实际训练效果，选择平衡高质量数量和Replay多样性的阈值",
            "note": "0.8无理论依据，需实验确定，阈值越高高质量越少但质量越高，阈值越低数量越多但可能引入低质量"
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


# 全局 v0914
replay_buffer = ReplayBufferV0914()
# 兼容
replay_buffer_v0914 = replay_buffer
