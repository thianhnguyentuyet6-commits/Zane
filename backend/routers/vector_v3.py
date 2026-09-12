# -*- coding: utf-8 -*-
"""
向量记忆 + 数据库 路由
拆分自 main_v7.py
"""
from fastapi import APIRouter

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

router = APIRouter(prefix="/api", tags=["向量记忆"])

def get_modules():
    mods = {}
    try:
        from ..memory.vector_memory import vector_memory
        mods['vector_memory'] = vector_memory
    except ImportError:
        mods['vector_memory'] = None
    try:
        from ..database import database
        mods['database'] = database
    except ImportError:
        mods['database'] = None
    return mods

@router.get("/memory/vector/search")
async def vector_search(query: str, limit: int = 5, type: str = None):
    mods = get_modules()
    try:
        from ..memory.vector_memory_real import vector_memory_real
        results = vector_memory_real.search(query, limit=limit, type_filter=type)
        if results:
            method = results[0].get("method", "keyword") if results else "none"
            return {
                "query": query, 
                "results": results, 
                "count": len(results), 
                "method": method,
                "real": vector_memory_real.use_vector,
                "embedding_dim": vector_memory_real.embedding_dim if vector_memory_real.use_vector else 0,
                "database": "SQLite + sqlite-vec + sentence-transformers" if vector_memory_real.use_vector else "SQLite关键词回退",
                "engine": "vector_memory_real"
            }
    except ImportError as e:
        _log_warning(f"vector_memory_real未安装: {e}")
    except Exception as e:
        _log_warning(f"vector_memory_real搜索失败: {e}")
    
    if mods['vector_memory']:
        try:
            results = mods['vector_memory'].search(query, limit=limit, type_filter=type)
            return {"query": query, "results": results, "count": len(results), "method": results[0].get("method", "keyword") if results else "none", "database": "SQLite + sqlite-vec可选", "engine": "vector_memory"}
        except Exception as e:
            _log_warning(f"旧向量搜索失败: {e}")
            return {"query": query, "results": [], "count": 0, "error": str(e), "engine": "vector_memory"}
    if mods['database']:
        try:
            results = mods['database'].search_memories(query, limit=limit)
            return {"query": query, "results": [{"content": r["content"], "type": r["type"], "score": 0.8, "method": "SQLite关键词+时间衰减"} for r in results], "count": len(results), "method": "SQLite", "note": "向量回退到SQLite关键词搜索", "engine": "database"}
        except Exception as e:
            _log_error(f"数据库搜索失败: {e}")
            return {"query": query, "results": [], "error": str(e)}
    return {"query": query, "results": [], "count": 0, "error": "向量记忆不可用"}

@router.post("/memory/vector/add")
async def vector_add(content: str, type: str = "semantic"):
    mods = get_modules()
    try:
        if mods['vector_memory']:
            try:
                mem_id = mods['vector_memory'].add(content, type=type)
                return {"id": mem_id, "content": content, "type": type, "real": True}
            except Exception as e:
                _log_warning(f"向量添加失败: {e}")
                return {"error": str(e)}
        if mods['database']:
            try:
                mem_id = mods['database'].add_memory(type=type, content=content, importance=0.7)
                return {"id": mem_id, "content": content, "type": type, "database": "SQLite"}
            except Exception as e:
                _log_error(f"数据库记忆添加失败: {e}")
                return {"error": str(e)}
        return {"error": "向量记忆不可用"}
    except Exception as e:
        _log_error(f"记忆添加接口失败: {e}")
        return {"error": str(e)}
