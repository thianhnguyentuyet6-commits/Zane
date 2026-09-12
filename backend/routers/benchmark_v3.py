# -*- coding: utf-8 -*-
"""
基准 + 模型注册表 路由
拆分自 main_v7.py
"""
from fastapi import APIRouter
from dataclasses import asdict

try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False
    import logging
    loguru_logger = logging.getLogger("zane")

def _log_error(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.error(msg)
    else:
        print(f"❌ {msg}")

router = APIRouter(prefix="/api", tags=["基准与模型"])

def get_modules():
    mods = {}
    try:
        from ..model_registry import model_registry
        mods['model_registry'] = model_registry
    except ImportError:
        mods['model_registry'] = None
    try:
        from ..benchmark.suite import benchmark_suite
        mods['benchmark_suite'] = benchmark_suite
    except ImportError:
        mods['benchmark_suite'] = None
    try:
        from ..agent_runtime_v2 import agent_runtime_v2 as agent_runtime
        mods['agent_runtime'] = agent_runtime
    except ImportError:
        mods['agent_runtime'] = None
    return mods

@router.get("/model-registry")
async def list_model_registry():
    mods = get_modules()
    try:
        if mods['model_registry']:
            return {"models": mods['model_registry'].list_models(), "active": asdict(mods['model_registry'].get_active_model()) if mods['model_registry'].get_active_model() else None}
        return {"models": [], "active": None}
    except Exception as e:
        _log_error(f"模型注册表失败: {e}")
        return {"models": [], "active": None, "error": str(e)}

@router.get("/benchmark")
async def list_benchmark(category: str = None):
    mods = get_modules()
    try:
        if mods['benchmark_suite']:
            return {"tasks": mods['benchmark_suite'].list_tasks(category=category), "stats": mods['benchmark_suite'].get_stats()}
        return {"tasks": [], "stats": {}}
    except Exception as e:
        _log_error(f"基准列表失败: {e}")
        return {"tasks": [], "stats": {}, "error": str(e)}

@router.post("/benchmark/run-all")
async def run_benchmark_all(category: str = None):
    mods = get_modules()
    try:
        if mods['benchmark_suite'] and mods['agent_runtime']:
            result = await mods['benchmark_suite'].run_all(mods['agent_runtime'], category=category)
            return result
        return {"error": "不可用"}
    except Exception as e:
        _log_error(f"基准运行失败: {e}")
        return {"error": str(e)}
