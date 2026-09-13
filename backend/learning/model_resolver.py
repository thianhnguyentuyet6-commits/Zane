# -*- coding: utf-8 -*-
"""
模型路径解析器 v0914 - 优先级：环境变量 > 配置文件 > 默认路径，找不到报错退出
- 修复硬编码14处，支持MODEL_PATH环境变量
- VRAM检测，推荐模型，支持8GB 3060ti
- 双轨：GGUF推理+HF训练，不自动下载，检测缓存提示确认
"""
import os
import json
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any


class ModelResolverError(Exception):
    """模型解析错误，找不到模型时报错退出而非静默失败"""
    pass


class ModelResolver:
    """模型路径解析器 v0914 - 严格模式"""
    
    def __init__(self, base_dir: str = None, strict: bool = False):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.config_path = self.base_dir / "config" / "model_paths.json"
        self.config = self._load_config()
        self.strict = strict  # 严格模式：找不到报错退出
    
    def _load_config(self) -> Dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def resolve_gguf_path(self, strict: bool = None) -> Dict[str, Any]:
        """解析GGUF推理路径 - 优先级：环境变量 > 配置文件 > 默认路径"""
        is_strict = strict if strict is not None else self.strict
        
        # 1. 环境变量 - 最高优先级
        env_vars = ["MODEL_PATH", "QWEN_MODEL_PATH", "LLM_MODEL_PATH", "ZANE_MODEL_PATH"]
        for var in env_vars:
            path = os.getenv(var)
            if path:
                expanded = os.path.expanduser(path)
                if os.path.exists(expanded):
                    return {
                        "path": expanded,
                        "source": f"环境变量 {var}",
                        "exists": True,
                        "type": "gguf",
                        "priority": 1
                    }
                else:
                    # 环境变量指定但不存在，严格模式下报错
                    if is_strict:
                        raise ModelResolverError(
                            f"环境变量 {var}={path} 指定的模型文件不存在\n"
                            f"请检查路径是否正确，或取消该环境变量使用自动探测\n"
                            f"当前工作目录: {os.getcwd()}"
                        )
        
        # 2. 配置文件
        cfg_keys = ["model_path", "qwen_path", "gguf_path", "llm_model_path"]
        for key in cfg_keys:
            cfg_path = self.config.get(key)
            if cfg_path:
                expanded = os.path.expanduser(cfg_path)
                if os.path.exists(expanded):
                    return {
                        "path": expanded,
                        "source": f"config/model_paths.json:{key}",
                        "exists": True,
                        "type": "gguf",
                        "priority": 2
                    }
                else:
                    if is_strict:
                        raise ModelResolverError(
                            f"配置文件 {self.config_path} 中 {key}={cfg_path} 指定的模型不存在\n"
                            f"请检查配置或删除该配置项"
                        )
        
        # 3. 自动探测 - 默认路径
        candidates = [
            "D:\\llama.cpp\\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf",
            "D:\\llama.cpp\\Qwen3-30B-A3B.gguf",
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
                    "type": "gguf",
                    "priority": 3
                }
        
        # 4. 找不到 - 严格模式报错，非严格模式返回占位+提示
        result = {
            "path": candidates[0],
            "source": "未找到",
            "exists": False,
            "type": "gguf",
            "priority": 4,
            "candidates": candidates,
            "env_vars": env_vars,
            "config_keys": cfg_keys,
            "note": "GGUF用于推理，需llama.cpp，设置MODEL_PATH环境变量指定路径",
            "need_download": False,
            "error": f"未找到GGUF模型，已尝试 {len(candidates)} 个路径和 {len(env_vars)} 个环境变量"
        }
        
        if is_strict:
            raise ModelResolverError(
                f"❌ 未找到GGUF推理模型\n"
                f"已尝试环境变量: {env_vars}\n"
                f"已尝试配置文件: {self.config_path} -> {cfg_keys}\n"
                f"已尝试默认路径: {candidates[:3]}...\n"
                f"解决方法:\n"
                f"  1. 设置环境变量: export MODEL_PATH=/path/to/model.gguf\n"
                f"  2. 或在 config/model_paths.json 中配置 model_path\n"
                f"  3. 或将模型放到默认路径之一\n"
                f"当前为严格模式，找不到模型将退出，请配置后重试"
            )
        
        return result
    
    def resolve_hf_path(self, strict: bool = None) -> Dict[str, Any]:
        """解析HF训练路径 - 不自动下载，检测缓存，提示确认"""
        is_strict = strict if strict is not None else self.strict
        
        # 1. 环境变量
        env_vars = ["HF_MODEL_PATH", "HF_PATH", "TRAIN_MODEL_PATH", "ZANE_HF_PATH"]
        for var in env_vars:
            path = os.getenv(var)
            if path:
                expanded = os.path.expanduser(path)
                if os.path.exists(expanded):
                    return {
                        "path": expanded,
                        "source": f"环境变量 {var}",
                        "exists": True,
                        "type": "hf",
                        "priority": 1,
                        "need_download": False
                    }
                else:
                    if is_strict and not path.startswith("Qwen/"):
                        raise ModelResolverError(
                            f"环境变量 {var}={path} 指定的HF模型路径不存在"
                        )
        
        # 2. 配置文件
        cfg_keys = ["hf_model_path", "hf_path", "train_model_path"]
        for key in cfg_keys:
            cfg_path = self.config.get(key)
            if cfg_path:
                expanded = os.path.expanduser(cfg_path)
                if os.path.exists(expanded):
                    return {
                        "path": expanded,
                        "source": f"config/model_paths.json:{key}",
                        "exists": True,
                        "type": "hf",
                        "priority": 2,
                        "need_download": False
                    }
        
        # 3. 自动探测本地缓存
        candidates = [
            "D:\\models\\Qwen3-30B-A3B",
            "C:\\models\\Qwen3-30B-A3B",
            os.path.expanduser("~/models/Qwen3-30B-A3B"),
            os.path.expanduser("~/.cache/huggingface/hub/models--Qwen--Qwen3-30B-A3B"),
            str(self.base_dir / "models" / "Qwen3-30B-A3B"),
            "/home/user/models/Qwen3-30B-A3B",
        ]
        for cand in candidates:
            if os.path.exists(cand):
                return {
                    "path": cand,
                    "source": f"自动探测本地缓存 {cand}",
                    "exists": True,
                    "type": "hf",
                    "priority": 3,
                    "need_download": False
                }
        
        # 4. 未找到本地缓存 - 不自动下载，提示用户确认
        hub_id = "Qwen/Qwen3-30B-A3B"
        result = {
            "path": hub_id,
            "source": "HF Hub ID，未找到本地缓存",
            "exists": False,
            "type": "hf",
            "priority": 4,
            "candidates": candidates,
            "env_vars": env_vars,
            "config_keys": cfg_keys,
            "is_hub_id": True,
            "need_download": True,
            "download_size": "~60GB",
            "download_command": f"huggingface-cli download {hub_id} --local-dir ./models/Qwen3-30B-A3B",
            "note": f"未找到本地HF模型，需下载 {hub_id} 约60GB，请确认后手动下载，不自动下载以免占用带宽和硬盘",
            "error": f"未找到HF训练模型本地缓存，需手动下载 {hub_id}"
        }
        
        # 严格模式也不自动下载，只提示
        if is_strict:
            # 严格模式下也只是警告，不强制退出，因为训练可选
            result["strict_note"] = "严格模式下仍不自动下载HF模型，需用户手动确认下载"
        
        return result
    
    def check_vram(self) -> Dict[str, Any]:
        """检测VRAM，推荐模型，支持8GB 3060ti"""
        total_gb = 0
        available_gb = 0
        device = "cpu"
        
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                total_gb = round(props.total_memory / 1024**3, 1)
                try:
                    free, total = torch.cuda.mem_get_info(0)
                    available_gb = round(free / 1024**3, 1)
                except:
                    available_gb = total_gb
                device = props.name
            else:
                device = "cpu"
        except ImportError:
            device = "cpu - torch未安装"
        except Exception as e:
            device = f"检测失败: {e}"
        
        # 推荐 - 支持8GB 3060ti
        if total_gb >= 24:
            recommended = {
                "model": "Qwen3-30B-A3B",
                "type": "30B MoE 3B激活",
                "quantization": "4bit QLoRA r=32",
                "vram_required": "24GB",
                "can_train": True,
                "batch_size": 2,
                "note": "可训练30B-A3B，24GB显存"
            }
        elif total_gb >= 16:
            recommended = {
                "model": "Qwen2.5-14B-Instruct",
                "type": "14B",
                "quantization": "4bit QLoRA r=16",
                "vram_required": "16GB",
                "can_train": True,
                "batch_size": 2,
                "note": "降级训练14B，30B需24GB"
            }
        elif total_gb >= 8:
            # 3060ti 8GB + 32GB RAM 可训练
            recommended = {
                "model": "Qwen2.5-7B-Instruct",
                "type": "7B",
                "quantization": "4bit QLoRA r=8 + CPU offload",
                "vram_required": "8GB + 32GB RAM",
                "can_train": True,
                "batch_size": 1,
                "gradient_checkpointing": True,
                "cpu_offload": True,
                "note": "8GB显存可训练7B，需32GB内存配合CPU offload+梯度检查点，适合3060ti"
            }
        elif total_gb >= 6:
            recommended = {
                "model": "Qwen2.5-3B-Instruct",
                "type": "3B",
                "quantization": "4bit QLoRA r=8",
                "vram_required": "6GB",
                "can_train": True,
                "batch_size": 1,
                "note": "训练3B小模型，6GB可用"
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
            "check_method": "torch.cuda.get_device_properties + mem_get_info",
            "supports_8gb": total_gb >= 8
        }
    
    def get_model_or_fail(self) -> Dict[str, Any]:
        """严格模式获取模型，找不到报错退出 - 用于run.py启动时"""
        try:
            gguf = self.resolve_gguf_path(strict=True)
            return gguf
        except ModelResolverError as e:
            # 报错退出而非静默失败
            print(f"\n{str(e)}\n")
            raise
    
    def get_all(self, strict: bool = False) -> Dict[str, Any]:
        """获取所有路径信息"""
        try:
            gguf = self.resolve_gguf_path(strict=strict)
        except ModelResolverError as e:
            gguf = {"error": str(e), "exists": False, "type": "gguf", "strict_failed": True}
        
        hf = self.resolve_hf_path(strict=False)  # HF不严格，不自动下载
        vram = self.check_vram()
        
        return {
            "gguf": gguf,
            "hf": hf,
            "vram": vram,
            "dual_track": {
                "inference": f"GGUF {gguf.get('path','?')} ({'存在' if gguf.get('exists') else '不存在'})",
                "training": f"HF {hf['path']} ({'存在' if hf['exists'] else '需下载' if hf.get('need_download') else '不存在'})",
                "note": "GGUF用于llama.cpp推理，HF用于Unsloth训练，双轨，不自动下载HF"
            },
            "env_vars": {
                "MODEL_PATH": os.getenv("MODEL_PATH", ""),
                "QWEN_MODEL_PATH": os.getenv("QWEN_MODEL_PATH", ""),
                "LLM_MODEL_PATH": os.getenv("LLM_MODEL_PATH", ""),
                "HF_MODEL_PATH": os.getenv("HF_MODEL_PATH", ""),
                "ZANE_MODEL_PATH": os.getenv("ZANE_MODEL_PATH", ""),
                "BASE_MODEL": os.getenv("BASE_MODEL", "Qwen3-30B-A3B"),
            },
            "config_file": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "strict_mode": strict
        }


# 全局 - 默认非严格，启动时可严格
model_resolver = ModelResolver()
