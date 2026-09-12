# -*- coding: utf-8 -*-
"""
模型路径解析器 v3 - GGUF推理+HF训练双轨
- 修复硬编码14处，环境变量+配置+自动探测
- VRAM检测，推荐模型
"""
import os
import json
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any

class ModelResolver:
    """模型路径解析器 v3"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.config_path = self.base_dir / "config" / "model_paths.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def resolve_gguf_path(self) -> Dict[str, Any]:
        """解析GGUF推理路径"""
        # 1. 环境变量
        env_vars = ["MODEL_PATH", "QWEN_MODEL_PATH", "LLM_MODEL_PATH"]
        for var in env_vars:
            path = os.getenv(var)
            if path and os.path.exists(path):
                return {
                    "path": path,
                    "source": f"环境变量 {var}",
                    "exists": True,
                    "type": "gguf"
                }
        
        # 2. 配置文件
        cfg_path = self.config.get("model_path") or self.config.get("qwen_path") or self.config.get("gguf_path")
        if cfg_path and os.path.exists(cfg_path):
            return {
                "path": cfg_path,
                "source": "config/model_paths.json",
                "exists": True,
                "type": "gguf"
            }
        
        # 3. 自动探测
        candidates = [
            "D:\\llama.cpp\\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf",
            "C:\\models\\qwen3.gguf",
            "D:\\models\\qwen3.gguf",
            os.path.expanduser("~/models/qwen3.gguf"),
            os.path.expanduser("~/.cache/qwen/model.gguf"),
            str(self.base_dir / "models" / "qwen3.gguf"),
            str(self.base_dir / "models" / "Qwen3.6-35B-A3B.gguf"),
            "/home/user/models/qwen3.gguf",
            "/models/qwen3.gguf"
        ]
        for cand in candidates:
            if os.path.exists(cand):
                return {
                    "path": cand,
                    "source": f"自动探测 {cand}",
                    "exists": True,
                    "type": "gguf"
                }
        
        # 4. 占位
        return {
            "path": candidates[0],
            "source": "占位，未找到",
            "exists": False,
            "type": "gguf",
            "candidates": candidates,
            "env_vars": env_vars,
            "note": "GGUF用于推理，需llama.cpp"
        }
    
    def resolve_hf_path(self) -> Dict[str, Any]:
        """解析HF训练路径"""
        # 1. 环境变量
        env_vars = ["HF_MODEL_PATH", "HF_PATH", "TRAIN_MODEL_PATH"]
        for var in env_vars:
            path = os.getenv(var)
            if path and os.path.exists(path):
                return {
                    "path": path,
                    "source": f"环境变量 {var}",
                    "exists": True,
                    "type": "hf"
                }
        
        # 2. 配置文件
        cfg_path = self.config.get("hf_model_path") or self.config.get("hf_path") or self.config.get("train_model_path")
        if cfg_path and os.path.exists(cfg_path):
            return {
                "path": cfg_path,
                "source": "config/model_paths.json",
                "exists": True,
                "type": "hf"
            }
        
        # 3. 自动探测 HF格式
        candidates = [
            "D:\\models\\Qwen3-30B-A3B",
            "C:\\models\\Qwen3-30B-A3B",
            os.path.expanduser("~/models/Qwen3-30B-A3B"),
            os.path.expanduser("~/.cache/huggingface/hub/models--Qwen--Qwen3-30B-A3B"),
            str(self.base_dir / "models" / "Qwen3-30B-A3B"),
            "/home/user/models/Qwen3-30B-A3B",
            "Qwen/Qwen3-30B-A3B",  # HF Hub ID
            "Qwen/Qwen2.5-7B-Instruct",  # 降级
        ]
        for cand in candidates:
            if os.path.exists(cand):
                return {
                    "path": cand,
                    "source": f"自动探测 {cand}",
                    "exists": True,
                    "type": "hf"
                }
            # HF Hub ID 不检查存在，允许
            if "/" in cand and not os.path.sep in cand:
                # 可能是HF ID
                if cand == "Qwen/Qwen3-30B-A3B":
                    return {
                        "path": cand,
                        "source": "HF Hub ID",
                        "exists": False,
                        "type": "hf",
                        "is_hub_id": True,
                        "note": "需 huggingface-cli download"
                    }
        
        return {
            "path": candidates[0],
            "source": "占位，未找到",
            "exists": False,
            "type": "hf",
            "candidates": candidates,
            "env_vars": env_vars,
            "note": "HF用于训练，需Unsloth+Transformers，执行 huggingface-cli download Qwen/Qwen3-30B-A3B"
        }
    
    def check_vram(self) -> Dict[str, Any]:
        """检测VRAM，推荐模型"""
        total_gb = 0
        available_gb = 0
        device = "cpu"
        
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                total_gb = round(props.total_memory / 1024**3, 1)
                # 可用显存
                free, total = torch.cuda.mem_get_info(0)
                available_gb = round(free / 1024**3, 1)
                device = props.name
            else:
                device = "cpu"
        except ImportError:
            device = "cpu - torch未安装"
        except Exception as e:
            device = f"检测失败: {e}"
        
        # 推荐
        if total_gb >= 24:
            recommended = {
                "model": "Qwen3-30B-A3B",
                "type": "30B MoE 3B激活",
                "quantization": "4bit QLoRA",
                "vram_required": "24GB",
                "can_train": True,
                "note": "可训练30B"
            }
        elif total_gb >= 16:
            recommended = {
                "model": "Qwen2.5-7B-Instruct",
                "type": "7B",
                "quantization": "4bit QLoRA",
                "vram_required": "16GB",
                "can_train": True,
                "note": "降级训练7B，30B需24GB"
            }
        elif total_gb >= 8:
            recommended = {
                "model": "Qwen2.5-3B-Instruct",
                "type": "3B",
                "quantization": "4bit QLoRA",
                "vram_required": "8GB",
                "can_train": True,
                "note": "训练3B小模型"
            }
        else:
            recommended = {
                "model": "技能蒸馏",
                "type": "无模型训练",
                "quantization": "无",
                "vram_required": "0GB",
                "can_train": False,
                "note": "显存不足，仅进化技能库+Prompt，不训练模型"
            }
        
        return {
            "total_gb": total_gb,
            "available_gb": available_gb,
            "device": device,
            "recommended": recommended,
            "cuda_available": total_gb > 0,
            "check_method": "torch.cuda.get_device_properties + mem_get_info"
        }
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有路径信息"""
        gguf = self.resolve_gguf_path()
        hf = self.resolve_hf_path()
        vram = self.check_vram()
        
        return {
            "gguf": gguf,
            "hf": hf,
            "vram": vram,
            "dual_track": {
                "inference": f"GGUF {gguf['path']} ({'存在' if gguf['exists'] else '不存在'})",
                "training": f"HF {hf['path']} ({'存在' if hf['exists'] else '不存在'})",
                "note": "GGUF用于llama.cpp推理，HF用于Unsloth训练，双轨非硬编码"
            },
            "env_vars": {
                "MODEL_PATH": os.getenv("MODEL_PATH", ""),
                "QWEN_MODEL_PATH": os.getenv("QWEN_MODEL_PATH", ""),
                "LLM_MODEL_PATH": os.getenv("LLM_MODEL_PATH", ""),
                "HF_MODEL_PATH": os.getenv("HF_MODEL_PATH", ""),
                "BASE_MODEL": os.getenv("BASE_MODEL", "Qwen3-30B-A3B"),
                "QUANTIZATION": os.getenv("QUANTIZATION", "IQ4_XS")
            },
            "config_file": str(self.config_path),
            "config_exists": self.config_path.exists()
        }

# 全局
model_resolver = ModelResolver()
