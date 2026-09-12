# -*- coding: utf-8 -*-
"""Tokens Router - Token可替换管理 - A夯实"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/tokens", tags=["tokens"])

@router.get("")
async def list_tokens(mask: bool = True):
    try:
        from ..token_manager import token_manager
        return {
            "tokens": token_manager.list_tokens(mask=mask),
            "real_search_config": token_manager.get_real_search_config(),
            "count": len(token_manager.token_definitions)
        }
    except Exception as e:
        return {"tokens": {}, "count": 0, "error": str(e)}

@router.get("/{token_id}")
async def get_token(token_id: str, mask: bool = True):
    try:
        from ..token_manager import token_manager
        return token_manager.get_token(token_id, mask=mask)
    except Exception as e:
        return {"error": str(e)}

@router.post("/{token_id}")
async def set_token(token_id: str, value: str):
    try:
        from ..token_manager import token_manager
        result = token_manager.set_token(token_id, value)
        return result
    except Exception as e:
        return {"error": str(e)}

@router.get("/real-search/config")
async def real_search_config():
    try:
        from ..token_manager import token_manager
        return token_manager.get_real_search_config()
    except Exception as e:
        return {"error": str(e)}
