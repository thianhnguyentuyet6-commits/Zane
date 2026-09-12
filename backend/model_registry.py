# -*- coding: utf-8 -*-
"""
模型注册表 - 推理与训练分离
跟踪基础模型、量化、后端、上下文、GPU offload、adapter版本、基准结果、晋升状态
"""
import os
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class ModelArtifact:
    id: str
    base_model: str  # Qwen3-30B-A3B
    quantization: str  # IQ4_XS, Q4_K_M
    runtime_backend: str  # llama.cpp, ollama
    context_length: int
    gpu_offload: str  # 35层 offload
    model_path: str  # D:\llama.cpp\...
    adapter_versions: List[str]
    active_adapter: Optional[str]
    benchmark_results: Dict
    promotion_status: str  # active, candidate, rollback
    created_at: float
    vram_required: str
    tokens_per_sec: float

class ModelRegistry:
    """模型注册表 - 分离推理和训练"""
    
    def __init__(self):
        self.registry_path = os.path.join(os.path.dirname(__file__), "..", "data", "model_registry.json")
        self.models: List[ModelArtifact] = self._load()
    
    def _load(self) -> List[ModelArtifact]:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [ModelArtifact(**m) for m in data]
            except Exception:
                pass
        
        # 默认模型 - 你的 Qwen3
        return [
            ModelArtifact(
                id="qwen3-30b-a3b-iq4xs",
                base_model="Qwen3-30B-A3B",
                quantization="IQ4_XS",
                runtime_backend="llama.cpp",
                context_length=32768,
                gpu_offload="35 layers",
                model_path="D:\\llama.cpp\\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf",
                adapter_versions=["lora_20240910", "lora_20240912"],
                active_adapter="lora_20240912",
                benchmark_results={
                    "file_ops": 0.95,
                    "window_ops": 0.88,
                    "process_ops": 0.92,
                    "overall": 0.91
                },
                promotion_status="active",
                created_at=time.time() - 86400*2,
                vram_required="16GB",
                tokens_per_sec=45.0
            ),
            ModelArtifact(
                id="qwen2-7b-q4km",
                base_model="Qwen2-7B",
                quantization="Q4_K_M",
                runtime_backend="llama.cpp",
                context_length=8192,
                gpu_offload="33 layers",
                model_path="D:\\models\\qwen2-7b-instruct-q4_k_m.gguf",
                adapter_versions=[],
                active_adapter=None,
                benchmark_results={},
                promotion_status="inactive",
                created_at=time.time() - 86400*5,
                vram_required="5GB",
                tokens_per_sec=85.0
            )
        ]

    def _save(self):
        try:
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(m) for m in self.models], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存模型注册表失败: {e}")

    def list_models(self) -> List[Dict]:
        return [asdict(m) for m in self.models]

    def get_active_model(self) -> Optional[ModelArtifact]:
        for m in self.models:
            if m.promotion_status == "active":
                return m
        return self.models[0] if self.models else None

    def add_adapter(self, base_model_id: str, adapter_id: str, benchmark: Dict):
        """添加 adapter 版本"""
        for model in self.models:
            if model.id == base_model_id:
                if adapter_id not in model.adapter_versions:
                    model.adapter_versions.append(adapter_id)
                model.benchmark_results[adapter_id] = benchmark
                self._save()
                return model
        return None

    def promote_adapter(self, base_model_id: str, adapter_id: str) -> Dict:
        """晋升 adapter - 需基准测试提升"""
        for model in self.models:
            if model.id == base_model_id:
                old_adapter = model.active_adapter
                old_benchmark = model.benchmark_results.get("overall", 0)
                new_benchmark = model.benchmark_results.get(adapter_id, {}).get("overall", 0) if isinstance(model.benchmark_results.get(adapter_id), dict) else model.benchmark_results.get(adapter_id, 0)
                
                # 检查是否提升
                if isinstance(new_benchmark, dict):
                    new_overall = new_benchmark.get("overall", 0)
                else:
                    new_overall = new_benchmark
                
                if new_overall > old_benchmark:
                    model.active_adapter = adapter_id
                    model.promotion_status = "active"
                    self._save()
                    return {
                        "success": True,
                        "message": f"晋升成功: {old_adapter} -> {adapter_id}, {old_benchmark} -> {new_overall}",
                        "old": old_adapter,
                        "new": adapter_id,
                        "improvement": new_overall - old_benchmark
                    }
                else:
                    return {
                        "success": False,
                        "message": f"未提升，不晋升: {old_benchmark} -> {new_overall}",
                        "old": old_adapter,
                        "new": adapter_id
                    }
        return {"success": False, "message": "模型未找到"}

    def rollback(self, base_model_id: str) -> Dict:
        """回滚到上一版本"""
        for model in self.models:
            if model.id == base_model_id:
                if len(model.adapter_versions) >= 2:
                    # 回滚到倒数第二个
                    prev_adapter = model.adapter_versions[-2]
                    model.active_adapter = prev_adapter
                    self._save()
                    return {"success": True, "message": f"已回滚到 {prev_adapter}", "adapter": prev_adapter}
        return {"success": False, "message": "无可回滚版本"}

model_registry = ModelRegistry()
