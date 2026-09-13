# -*- coding: utf-8 -*-
"""
视觉 + 搜索 + 清理 + 系统 路由 v0913整合版
- 集成dpi_ocr_unified DPI坐标系统一
- 8层架构：可观测层+平台层
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
    (loguru_logger.error if LOGURU_AVAILABLE else print)(f"❌ {msg}")

def _log_warning(msg: str):
    (loguru_logger.warning if LOGURU_AVAILABLE else print)(f"⚠️ {msg}")

def _log_info(msg: str):
    (loguru_logger.info if LOGURU_AVAILABLE else print)(msg)

router = APIRouter(prefix="/api", tags=["可观测层"])

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
    try:
        from ..vision.dpi_ocr_unified import dpi_ocr_unified
        mods['dpi_ocr_unified'] = dpi_ocr_unified
    except ImportError:
        mods['dpi_ocr_unified'] = None
    return mods

class SearchRequest(BaseModel):
    query: str
    count: int = 5
    fetch_content: bool = False

class OCRRequest(BaseModel):
    image_path: str = ""
    use_screenshot: bool = False

@router.post("/vision/ocr", summary="OCR识别 - DPI统一+RapidOCR/Tesseract+UIA树", tags=["可观测层"])
async def vision_ocr(request: OCRRequest):
    mods = get_modules()
    try:
        # 优先DPI统一版
        if mods['dpi_ocr_unified']:
            try:
                if request.use_screenshot and mods['tool_executor']:
                    # 先截图再DPI统一OCR
                    screenshot = mods['tool_executor'].take_screenshot(mode="full")
                    if screenshot.get("success"):
                        result = mods['dpi_ocr_unified'].ocr_with_dpi(image_path=screenshot.get("image_path"))
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
                    result = mods['dpi_ocr_unified'].ocr_with_dpi(image_path=request.image_path)
                    return result
            except Exception as e:
                _log_warning(f"DPI统一OCR失败，回退旧版: {e}")
        
        # 回退旧版
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

@router.get("/vision/ocr", summary="OCR识别GET - DPI统一", tags=["可观测层"])
async def vision_ocr_get(image_path: str = "", use_screenshot: bool = False):
    mods = get_modules()
    try:
        if mods['dpi_ocr_unified']:
            try:
                if use_screenshot and mods['tool_executor']:
                    screenshot = mods['tool_executor'].take_screenshot(mode="full")
                    if screenshot.get("success"):
                        result = mods['dpi_ocr_unified'].ocr_with_dpi(image_path=screenshot.get("image_path"))
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
                    result = mods['dpi_ocr_unified'].ocr_with_dpi(image_path=image_path)
                    return result
            except Exception as e:
                _log_warning(f"DPI统一OCR GET失败，回退: {e}")
        
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

@router.get("/vision/dpi", summary="DPI信息 - 坐标系统一125%/150%检测", tags=["平台层"])
async def vision_dpi():
    """DPI坐标系统一信息"""
    mods = get_modules()
    try:
        if mods['dpi_ocr_unified']:
            return mods['dpi_ocr_unified'].get_dpi_info()
        # 回退
        import sys
        import platform
        return {"detected_dpi": 96, "dpi_scale": 1.0, "platform": sys.platform, "system": platform.system(), "note": "DPI统一模块不可用"}
    except Exception as e:
        _log_error(f"DPI信息失败: {e}")
        return {"error": str(e)}

@router.get("/utils/cleanup", summary="清理 - 截图/备份/轨迹", tags=["可观测层"])
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

@router.post("/search/real", summary="真实搜索 - Bing API+本地回退", tags=["可观测层"])
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

@router.get("/search/real", summary="真实搜索GET", tags=["可观测层"])
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

@router.post("/dreaming/run-all", summary="梦境运行 - 3阶段Dream+Evolve+Consolidate", tags=["记忆层"])
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

@router.get("/dreaming/status", summary="梦境状态 - 阈值+候选", tags=["记忆层"])
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
