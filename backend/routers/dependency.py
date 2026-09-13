# -*- coding: utf-8 -*-
"""
依赖检测 + 自动补全API - 真实API
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/api/dependency", tags=["依赖检测"])

@router.get("/check", summary="依赖检测 - 所有依赖状态+API真实性")
async def check_dependencies():
    try:
        from ..utils.dependency_checker import dependency_checker
        status = dependency_checker.check_all()
        api_status = dependency_checker.get_api_real_status()
        
        return {
            "dependencies": status,
            "api_real": api_status,
            "summary": {
                "total_deps": status["total"],
                "available": status["available"],
                "missing": status["missing"],
                "missing_list": status["missing_list"],
                "required_missing": status["required_missing"],
                "api_real": api_status["real"],
                "api_total": api_status["total"],
                "all_real": api_status["all_real"]
            }
        }
    except Exception as e:
        return {"error": str(e), "dependencies": {"total": 0, "available": 0, "missing": 0}}

@router.post("/install", summary="自动安装缺失依赖")
async def auto_install_dependencies(only_required: bool = True):
    try:
        from ..utils.dependency_checker import dependency_checker
        result = dependency_checker.auto_install(only_required=only_required, interactive=False)
        status = dependency_checker.check_all()
        
        return {
            "install_result": result,
            "new_status": status,
            "message": f"尝试安装 {result['attempted']} 个，成功 {len(result['installed'])} 个，失败 {len(result['failed'])} 个"
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/api-real", summary="API真实性检查 - 必须真实")
async def check_api_real():
    try:
        from ..utils.dependency_checker import dependency_checker
        api_status = dependency_checker.get_api_real_status()
        return api_status
    except Exception as e:
        return {"error": str(e), "total": 0, "real": 0}
