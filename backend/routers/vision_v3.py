# -*- coding: utf-8 -*-
"""
视觉 + 搜索 + 清理 + 系统 路由
拆分自 main_v6.py
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Header
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

router = APIRouter(prefix="/api", tags=["视觉与系统"])

def get_modules():
    mods = {}
    try:
        from ..security.sandbox import file_sandbox
        mods['file_sandbox'] = file_sandbox
    except ImportError:
        mods['file_sandbox'] = None
    try:
        from ..tools.network.web_search_real import web_search_real
        mods['web_search_real'] = web_search_real
    except ImportError:
        mods['web_search_real'] = None
    try:
        from ..tools_impl import tool_executor
        mods['tool_executor'] = tool_executor
    except ImportError:
        mods['tool_executor'] = None
    try:
        from ..runtime.dreaming import dreaming_system
        mods['dreaming_system'] = dreaming_system
    except ImportError:
        mods['dreaming_system'] = None
    return mods

class SearchRequest(BaseModel):
    query: str
    count: int = 5
    fetch_content: bool = False

class OCRRequest(BaseModel):
    image_path: str = ""
    use_screenshot: bool = False

@router.post("/vision/ocr")
async def vision_ocr(request: OCRRequest):
    mods = get_modules()
    try:
        from ..vision.ocr_real import ocr_real
        if request.use_screenshot:
            result = ocr_real.ocr_screenshot()
            return result
        elif request.image_path:
            if mods['file_sandbox']:
                try:
                    check = mods['file_sandbox'].check_path(request.image_path)
                    if not check.get("allowed", True):
                        raise HTTPException(status_code=403, detail="路径不允许")
                except HTTPException:
                    raise
                except Exception as e:
                    _log_warning(f"沙盒检查失败: {e}")
            result = ocr_real.ocr_image(request.image_path)
            return result
        else:
            return {"error": "需提供 image_path 或 use_screenshot=true"}
    except HTTPException:
        raise
    except ImportError as e:
        return {"error": f"OCR未安装: {e}", "text": ""}
    except Exception as e:
        _log_error(f"OCR失败: {e}")
        return {"error": str(e), "text": ""}

@router.get("/vision/ocr")
async def vision_ocr_get(image_path: str = "", use_screenshot: bool = False):
    mods = get_modules()
    try:
        from ..vision.ocr_real import ocr_real
        if use_screenshot:
            result = ocr_real.ocr_screenshot()
            return result
        elif image_path:
            if mods['file_sandbox']:
                try:
                    check = mods['file_sandbox'].check_path(image_path)
                    if not check.get("allowed", True):
                        raise HTTPException(status_code=403, detail="路径不允许")
                except HTTPException:
                    raise
                except Exception as e:
                    _log_warning(f"沙盒检查失败: {e}")
            result = ocr_real.ocr_image(image_path)
            return result
        else:
            return {"error": "需提供 image_path 或 use_screenshot=true"}
    except ImportError as e:
        return {"error": f"OCR未安装: {e}"}
    except Exception as e:
        _log_error(f"OCR GET失败: {e}")
        return {"error": str(e)}

@router.get("/utils/cleanup")
async def utils_cleanup(type: str = "all", keep: int = 50):
    try:
        from ..utils.cleanup import cleanup_manager
        if type == "screenshots":
            result = cleanup_manager.cleanup_screenshots(keep=keep)
            return result
        elif type == "backups":
            result = cleanup_manager.cleanup_old_backups(keep=10, days=30)
            return result
        elif type == "traces":
            result = cleanup_manager.cleanup_old_traces(keep=keep)
            return result
        else:
            s = cleanup_manager.cleanup_screenshots(keep=50)
            b = cleanup_manager.cleanup_old_backups(keep=10, days=30)
            t = cleanup_manager.cleanup_old_traces(keep=100)
            return {"screenshots": s, "backups": b, "traces": t}
    except ImportError as e:
        return {"error": f"清理模块未安装: {e}"}
    except Exception as e:
        _log_error(f"清理失败: {e}")
        return {"error": str(e)}

@router.post("/search/real")
async def search_real(request: SearchRequest):
    mods = get_modules()
    try:
        if mods['web_search_real']:
            try:
                result = await mods['web_search_real'].search(request.query, count=request.count)
                return result
            except Exception as e:
                _log_warning(f"真实搜索失败: {e}")
                return {"error": str(e), "query": request.query, "results": []}
        if mods['tool_executor']:
            return mods['tool_executor'].web_search(query=request.query, count=request.count)
        return {"query": request.query, "results": []}
    except Exception as e:
        _log_error(f"搜索失败: {e}")
        return {"query": request.query, "results": [], "error": str(e)}

@router.get("/search/real")
async def search_real_get(query: str, count: int = 5):
    mods = get_modules()
    try:
        if mods['web_search_real']:
            try:
                result = await mods['web_search_real'].search(query, count=count)
                return result
            except Exception as e:
                _log_warning(f"真实搜索GET失败: {e}")
                return {"error": str(e), "query": query, "results": []}
        if mods['tool_executor']:
            return mods['tool_executor'].web_search(query=query, count=count)
        return {"query": query, "results": []}
    except Exception as e:
        _log_error(f"搜索GET失败: {e}")
        return {"query": query, "results": [], "error": str(e)}

@router.post("/dreaming/run-all")
async def dreaming_run_all(days: int = 7):
    mods = get_modules()
    try:
        if not mods['dreaming_system']:
            return {"error": "梦境不可用"}
        light = mods['dreaming_system'].light_phase(days=days)
        rem = mods['dreaming_system'].rem_phase()
        deep = mods['dreaming_system'].deep_phase()
        return {"light": light, "rem": rem, "deep": deep, "summary": f"扫描 {light.get('scanned',0)} 条"}
    except Exception as e:
        _log_error(f"梦境运行失败: {e}")
        return {"error": str(e)}

@router.get("/dreaming/status")
async def dreaming_status():
    mods = get_modules()
    try:
        if mods['dreaming_system']:
            import os
            candidates_path = os.path.join(mods['dreaming_system'].data_dir, ".dreams", "candidates.json")
            has_candidates = os.path.exists(candidates_path)
            return {"threshold": mods['dreaming_system'].threshold, "weights": mods['dreaming_system'].signal_weights, "has_candidates": has_candidates, "dreams_dir": mods['dreaming_system'].dreams_dir}
        return {"error": "不可用"}
    except Exception as e:
        _log_error(f"梦境状态失败: {e}")
        return {"error": str(e)}
