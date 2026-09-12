# -*- coding: utf-8 -*-
"""Models Router - 本地模型载入功能 - 真实扫描+自定义模型A"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/models", tags=["models"])

class AddModelRequest(BaseModel):
    path: str
    name: Optional[str] = None

@router.get("")
async def list_models():
    """列出所有本地模型 - 真实扫描文件系统+自定义模型A"""
    try:
        from ..llm.model_manager_v2 import model_manager_v2
        models = model_manager_v2.scan_models()
        return {
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "path": m.path,
                    "size_gb": m.size_gb,
                    "quantization": m.quantization,
                    "context_length": m.context_length,
                    "parameters": m.parameters,
                    "type": m.type,
                    "is_active": m.is_active,
                    "is_custom": m.is_custom,
                    "exists": m.exists,
                    "performance": m.performance
                } for m in models
            ],
            "total": len(models),
            "custom_count": len([m for m in models if m.is_custom]),
            "real_scan": True,
            "note": "真实扫描文件系统 GGUF + 用户自定义模型A，支持模型A选择"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"models": [], "total": 0, "error": str(e)}

@router.get("/status")
async def model_status():
    """llama.cpp server 状态 - 真实检测"""
    try:
        from ..llm.model_manager_v2 import model_manager_v2
        status = model_manager_v2.get_server_status()
        return status
    except Exception as e:
        return {"running": False, "error": str(e)}

@router.post("/switch")
async def switch_model(model_id: str):
    """切换模型 - 真实重启 llama.cpp server"""
    try:
        from ..llm.model_manager_v2 import model_manager_v2
        result = model_manager_v2.switch_model(model_id)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@router.post("/add")
async def add_custom_model(request: AddModelRequest):
    """添加用户自定义模型A - 例如本地有模型A，选择该模型"""
    try:
        from ..llm.model_manager_v2 import model_manager_v2
        result = model_manager_v2.add_custom_model(request.path, request.name)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@router.delete("/{model_id}")
async def remove_custom_model(model_id: str):
    """移除自定义模型"""
    try:
        from ..llm.model_manager_v2 import model_manager_v2
        result = model_manager_v2.remove_custom_model(model_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/versions")
async def model_versions():
    """模型版本 - LoRA版本"""
    try:
        from ..llm.model_manager_v2 import model_manager_v2
        versions = model_manager_v2.get_model_versions()
        return {"versions": versions, "total": len(versions)}
    except Exception as e:
        return {"versions": [], "error": str(e)}

@router.get("/scan/dirs")
async def scan_dirs():
    """扫描目录配置"""
    try:
        from ..llm.model_manager_v2 import model_manager_v2
        return {
            "scan_dirs": model_manager_v2.model_dirs,
            "custom_file": model_manager_v2.custom_models_file,
            "note": "可添加自定义路径到 model_dirs 或使用 /api/models/add 添加模型A"
        }
    except Exception as e:
        return {"error": str(e)}
