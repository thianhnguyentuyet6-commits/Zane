# -*- coding: utf-8 -*-
"""
认证路由 v3.0 - JWT商业级
拆分自 main_v7.py
"""
import os
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

router = APIRouter(prefix="/api/auth", tags=["认证JWT"])

class LoginRequest(BaseModel):
    username: str = "admin"
    password: str = ""
    token: str = ""

@router.post("/login")
async def auth_login(request: LoginRequest):
    try:
        from ..middleware.jwt_auth import jwt_auth
        expected_token = os.getenv("ZANE_TOKEN", "")
        expected_pwd = os.getenv("ZANE_PASSWORD", expected_token or "zane123")
        if expected_token and request.token == expected_token:
            jwt_token = jwt_auth.create_token({"sub": request.username or "admin", "method": "token"})
            return {"success": True, "token": jwt_token, "method": "token", "expires_days": 7}
        elif expected_pwd and request.password == expected_pwd:
            jwt_token = jwt_auth.create_token({"sub": request.username, "method": "password"})
            return {"success": True, "token": jwt_token, "method": "password", "expires_days": 7}
        elif not expected_token and not os.getenv("ZANE_JWT_SECRET"):
            jwt_token = jwt_auth.create_token({"sub": request.username or "admin", "method": "no_auth"})
            return {"success": True, "token": jwt_token, "method": "no_auth", "note": "未配置认证，开发模式", "expires_days": 7}
        else:
            raise HTTPException(status_code=401, detail="用户名/密码/Token错误")
    except HTTPException:
        raise
    except ImportError as e:
        _log_error(f"JWT模块未安装: {e}")
        return {"success": False, "error": f"JWT未安装: {e}"}
    except Exception as e:
        _log_error(f"登录失败: {e}")
        return {"success": False, "error": str(e)}

@router.get("/check")
async def auth_check(x_zane_token: str = Header(None), authorization: str = Header(None)):
    try:
        from ..middleware.jwt_auth import jwt_auth
        token = (authorization or "").replace("Bearer ", "") or (x_zane_token or "")
        if not token:
            return {"authenticated": False, "reason": "无Token", "need_login": bool(os.getenv("ZANE_TOKEN") or os.getenv("ZANE_JWT_SECRET"))}
        result = jwt_auth.check(token)
        if result["allowed"]:
            return {"authenticated": True, "payload": result.get("payload"), "method": result.get("method", "jwt")}
        else:
            return {"authenticated": False, "reason": result.get("reason")}
    except ImportError as e:
        return {"authenticated": False, "error": f"JWT未安装: {e}"}
    except Exception as e:
        _log_warning(f"认证检查失败: {e}")
        return {"authenticated": False, "error": str(e)}

@router.post("/logout")
async def auth_logout():
    return {"success": True, "message": "已登出，请清除本地Token"}
