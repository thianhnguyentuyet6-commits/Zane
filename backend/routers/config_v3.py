# -*- coding: utf-8 -*-
"""
配置中心 + 设置保存 路由 v7.0新增
- 真实落盘 config/ + data/
- 前端localStorage同步
"""
import os
import json
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False
    import logging
    loguru_logger = logging.getLogger("zane")

def _log_info(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.info(msg)
    else:
        print(msg)

def _log_error(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.error(msg)
    else:
        print(f"❌ {msg}")

router = APIRouter(prefix="/api", tags=["配置中心"])

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
DATA_DIR = Path(__file__).parent.parent.parent / "data"

class SettingsRequest(BaseModel):
    category: str  # model, evolution, policy, appearance
    settings: Dict[str, Any]

@router.get("/settings")
async def get_settings():
    """获取所有配置"""
    try:
        settings = {}
        # 模型路径
        model_paths_file = CONFIG_DIR / "model_paths.json"
        if model_paths_file.exists():
            with open(model_paths_file, 'r', encoding='utf-8') as f:
                settings['model'] = json.load(f)
        
        # 进化调度
        evo_schedule_file = CONFIG_DIR / "evolution_schedule.json"
        if evo_schedule_file.exists():
            with open(evo_schedule_file, 'r', encoding='utf-8') as f:
                settings['evolution'] = json.load(f)
        
        # 环境变量
        settings['env'] = {
            "MODEL_PATH": os.getenv("MODEL_PATH", ""),
            "HF_MODEL_PATH": os.getenv("HF_MODEL_PATH", ""),
            "ZANE_TOKEN": "***" if os.getenv("ZANE_TOKEN") else "",
            "ZANE_PASSWORD": "***" if os.getenv("ZANE_PASSWORD") else "",
        }
        
        return {"success": True, "settings": settings}
    except Exception as e:
        _log_error(f"获取配置失败: {e}")
        return {"success": False, "error": str(e)}

@router.post("/settings/save")
async def save_settings(request: SettingsRequest):
    """保存配置 - 真实落盘"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        if request.category == "model":
            # 保存模型路径
            file_path = CONFIG_DIR / "model_paths.json"
            existing = {}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            existing.update(request.settings)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            _log_info(f"✅ 模型配置已保存: {file_path}")
            return {"success": True, "message": f"模型配置已保存到 {file_path}", "path": str(file_path)}
        
        elif request.category == "evolution":
            file_path = CONFIG_DIR / "evolution_schedule.json"
            existing = {}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            existing.update(request.settings)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            _log_info(f"✅ 进化配置已保存: {file_path}")
            return {"success": True, "message": f"进化配置已保存", "path": str(file_path)}
        
        elif request.category == "policy":
            file_path = CONFIG_DIR / "policy.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(request.settings, f, ensure_ascii=False, indent=2)
            _log_info(f"✅ 策略配置已保存: {file_path}")
            return {"success": True, "message": "策略配置已保存", "path": str(file_path)}
        
        elif request.category == "appearance":
            file_path = CONFIG_DIR / "appearance.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(request.settings, f, ensure_ascii=False, indent=2)
            _log_info(f"✅ 外观配置已保存: {file_path}")
            return {"success": True, "message": "外观配置已保存", "path": str(file_path)}
        
        else:
            # 通用
            file_path = CONFIG_DIR / f"{request.category}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(request.settings, f, ensure_ascii=False, indent=2)
            return {"success": True, "message": f"{request.category}配置已保存", "path": str(file_path)}
    
    except Exception as e:
        _log_error(f"保存配置失败: {e}")
        return {"success": False, "error": str(e)}

@router.get("/settings/model-paths")
async def get_model_paths():
    """获取模型路径 - 非硬编码，环境变量>配置>探测"""
    try:
        from ..learning.model_resolver import model_resolver
        if model_resolver:
            all_info = model_resolver.get_all()
            return {"success": True, "model_paths": all_info, "technique": "环境变量>配置>探测9+8候选>占位 非硬编码"}
        return {"success": False, "error": "model_resolver未加载"}
    except Exception as e:
        _log_error(f"模型路径获取失败: {e}")
        return {"success": False, "error": str(e)}

@router.post("/settings/model-paths/test")
async def test_model_path(path: str):
    """测试模型路径是否可用"""
    try:
        p = Path(path)
        exists = p.exists()
        size = p.stat().st_size if exists else 0
        size_gb = round(size / 1024**3, 2) if exists else 0
        return {
            "path": path,
            "exists": exists,
            "size_bytes": size,
            "size_gb": size_gb,
            "readable": os.access(path, os.R_OK) if exists else False,
            "message": f"{'✅ 存在' if exists else '❌ 不存在'} {size_gb}GB" if exists else "路径不存在"
        }
    except Exception as e:
        _log_error(f"模型路径测试失败: {e}")
        return {"path": path, "exists": False, "error": str(e)}
