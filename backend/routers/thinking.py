# -*- coding: utf-8 -*-
"""
思考预算 + Ralph Loop + 有界自校正 路由 v2.5
拆分自 main_v6.py
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel

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

def _log_warning(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.warning(msg)
    else:
        print(f"⚠️ {msg}")

router = APIRouter(prefix="/api", tags=["思考与进化v2.5"])

def get_modules():
    mods = {}
    try:
        from ..runtime.thinking_budget import thinking_budget
        mods['thinking_budget'] = thinking_budget
    except ImportError:
        mods['thinking_budget'] = None
    try:
        from ..runtime.ralph_loop import ralph_loop
        mods['ralph_loop'] = ralph_loop
    except ImportError:
        mods['ralph_loop'] = None
    try:
        from ..runtime.bounded_correction import bounded_correction
        mods['bounded_correction'] = bounded_correction
    except ImportError:
        mods['bounded_correction'] = None
    try:
        from ..learning.evolution_engine_v25 import evolution_engine_v25 as evolution_engine
        mods['evolution_engine'] = evolution_engine
    except ImportError:
        try:
            from ..learning.evolution_engine import evolution_engine
            mods['evolution_engine'] = evolution_engine
        except ImportError:
            mods['evolution_engine'] = None
    return mods

class ThinkingRequest(BaseModel):
    message: str
    mode: str = "auto"
    budget: Optional[int] = None

class RalphRequest(BaseModel):
    tasks: List[Dict[str, Any]]
    max_iterations: int = 10
    token_budget: int = 100000

class CorrectionRequest(BaseModel):
    draft: str
    query: str
    task_type: str = "read_only"

@router.post("/thinking/budget")
async def thinking_budget_api(request: ThinkingRequest):
    mods = get_modules()
    try:
        if not mods['thinking_budget']:
            return {"error": "思考预算模块未加载", "available": False}
        result = mods['thinking_budget'].build_chat_template(request.message, mode=request.mode)
        if request.budget:
            result["sampling_params"]["max_tokens"] = request.budget
        return {"success": True, "thinking_budget": result, "technique": "Qwen3 2026 Thinking Budget /think /no_think"}
    except Exception as e:
        _log_error(f"思考预算失败: {e}")
        return {"error": str(e)}

@router.get("/thinking/budget")
async def thinking_budget_get(message: str, mode: str = "auto"):
    mods = get_modules()
    try:
        if not mods['thinking_budget']:
            return {"error": "思考预算模块未加载"}
        complexity = mods['thinking_budget'].estimate_complexity(message)
        params = mods['thinking_budget'].get_sampling_params(mode)
        return {"message": message, "complexity": complexity, "sampling_params": params, "technique": "Qwen3 2026"}
    except Exception as e:
        _log_error(f"思考预算GET失败: {e}")
        return {"error": str(e)}

@router.post("/ralph/run")
async def ralph_run(request: RalphRequest):
    mods = get_modules()
    try:
        if not mods['evolution_engine'] or not hasattr(mods['evolution_engine'], 'run_ralph_evolution'):
            return {"error": "Ralph Loop未加载，需v2.5引擎"}
        result = await mods['evolution_engine'].run_ralph_evolution(request.tasks)
        return {"success": True, "ralph": result, "technique": "Ralph Loop bash while fresh context + prd.json passes布尔 + 3护栏"}
    except Exception as e:
        _log_error(f"Ralph运行失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/ralph/status")
async def ralph_status():
    mods = get_modules()
    try:
        if mods['ralph_loop']:
            prd = mods['ralph_loop'].load_prd()
            guard = mods['ralph_loop'].check_guardrails(prd)
            return {
                "available": True,
                "prd_count": len(prd),
                "undone": len([s for s in prd if not s.passes]),
                "guardrails": guard,
                "iterations": len(mods['ralph_loop'].iterations),
                "total_tokens": mods['ralph_loop'].total_tokens,
                "technique": "Ralph Loop 2026"
            }
        return {"available": False, "error": "Ralph未加载"}
    except Exception as e:
        _log_error(f"Ralph状态失败: {e}")
        return {"error": str(e)}

@router.post("/correction/bounded")
async def bounded_correction_api(request: CorrectionRequest):
    mods = get_modules()
    try:
        if not mods['evolution_engine'] or not hasattr(mods['evolution_engine'], 'run_bounded_correction'):
            return {"error": "有界自校正未加载"}
        result = await mods['evolution_engine'].run_bounded_correction(request.draft, request.query, request.task_type)
        return {"success": True, "correction": result, "technique": "UCSL不确定度校准+验证器引导+任务预算"}
    except Exception as e:
        _log_error(f"有界自校正失败: {e}")
        return {"error": str(e)}

@router.get("/correction/stats")
async def correction_stats():
    mods = get_modules()
    try:
        if mods['bounded_correction'] and hasattr(mods['bounded_correction'], 'get_calibration_stats'):
            stats = mods['bounded_correction'].get_calibration_stats()
            return {"available": True, "stats": stats, "technique": "UCSL Layer A可观测性"}
        return {"available": False}
    except Exception as e:
        _log_error(f"校正统计失败: {e}")
        return {"error": str(e)}
