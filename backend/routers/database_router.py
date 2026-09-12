# -*- coding: utf-8 -*-
"""Database Router - SQLite唯一 + filelock + 技术栈 - A夯实"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/database", tags=["database"])

@router.get("/stats")
async def database_stats():
    try:
        from ..database import database
        return {
            "memory_stats": database.get_memory_stats(),
            "trace_stats": database.get_trace_stats(),
            "tech_stack": database.get_tech_stack(),
            "file": database.db_path,
            "vec_available": database.vec_available,
            "lock": "filelock" if database.lock else "WAL",
            "mode": "SQLite唯一，JSON废弃只读迁移一次"
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/tech-stack")
async def tech_stack():
    try:
        from ..database import database
        return database.get_tech_stack()
    except Exception as e:
        return {
            "database": {"primary": "SQLite", "note": str(e)},
            "backend": {"framework": "FastAPI + slowapi"},
            "frontend": {"framework": "原生HTML/CSS/JS + ES Modules拆分"}
        }

@router.get("/memories/search")
async def database_search_memories(query: str, limit: int = 5):
    try:
        from ..database import database
        results = database.search_memories(query, limit=limit)
        return {"query": query, "results": results, "count": len(results), "database": "SQLite", "lock": "filelock"}
    except Exception as e:
        return {"query": query, "results": [], "count": 0, "error": str(e)}

@router.get("/habits")
async def get_habits(limit: int = 10):
    """C扩展 - 习惯学习"""
    try:
        from ..database import database
        habits = database.get_top_habits(limit=limit)
        return {"habits": habits, "count": len(habits), "source": "SQLite user_habits表，C扩展"}
    except Exception as e:
        return {"habits": [], "count": 0, "error": str(e)}

@router.post("/backup")
async def backup_db():
    try:
        from ..database import database
        backup_path = database.backup()
        return {"success": True, "backup_path": backup_path}
    except Exception as e:
        return {"success": False, "error": str(e)}
