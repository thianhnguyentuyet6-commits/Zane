# -*- coding: utf-8 -*-
"""
记忆v3 + SimpleMem + 技能库 路由
拆分自 main_v6.py
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

router = APIRouter(prefix="/api", tags=["记忆v3"])

def get_modules():
    mods = {}
    try:
        from ..runtime.skill_library import skill_library
        mods['skill_library'] = skill_library
    except ImportError:
        mods['skill_library'] = None
    try:
        from ..memory.simple_mem import simple_mem
        mods['simple_mem'] = simple_mem
    except ImportError:
        mods['simple_mem'] = None
    try:
        from ..runtime.dream_loop import dream_loop
        mods['dream_loop'] = dream_loop
    except ImportError:
        mods['dream_loop'] = None
    try:
        from ..memory.memory_v3 import memory_v3
        mods['memory_v3'] = memory_v3
    except ImportError:
        mods['memory_v3'] = None
    try:
        from ..runtime.skill_gene import skill_gene_evolution
        mods['skill_gene_evolution'] = skill_gene_evolution
    except ImportError:
        mods['skill_gene_evolution'] = None
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

@router.get("/skills/library")
async def skills_library():
    mods = get_modules()
    try:
        if mods['skill_library']:
            stats = mods['skill_library'].get_stats()
            return {"available": True, "library": stats, "technique": "SAGE Sequential Rollout 可复用函数 复合改进"}
        return {"available": False}
    except Exception as e:
        _log_error(f"技能库失败: {e}")
        return {"error": str(e)}

@router.post("/skills/test")
async def skills_test(name: str):
    mods = get_modules()
    try:
        if mods['skill_library']:
            result = mods['skill_library'].test_skill(name)
            return result
        return {"error": "技能库未加载"}
    except Exception as e:
        _log_error(f"技能测试失败: {e}")
        return {"error": str(e)}

@router.get("/memory/simple")
async def simple_mem_api():
    mods = get_modules()
    try:
        if mods['simple_mem']:
            stats = mods['simple_mem'].get_stats()
            return {"available": True, "simple_mem": stats, "technique": "语义结构化压缩+在线合成+意图感知检索"}
        return {"available": False}
    except Exception as e:
        _log_error(f"SimpleMem失败: {e}")
        return {"error": str(e)}

@router.post("/memory/simple/add")
async def simple_mem_add(content: str, type: str = "semantic", importance: float = 0.5):
    mods = get_modules()
    try:
        if mods['simple_mem']:
            mem_id = mods['simple_mem'].add_memory(content, type=type, importance=importance)
            return {"id": mem_id, "content": content, "technique": "SimpleMem压缩"}
        return {"error": "SimpleMem未加载"}
    except Exception as e:
        _log_error(f"SimpleMem添加失败: {e}")
        return {"error": str(e)}

@router.get("/memory/simple/search")
async def simple_mem_search(query: str, limit: int = 5):
    mods = get_modules()
    try:
        if mods['simple_mem'] and hasattr(mods['simple_mem'], 'intent_aware_retrieval'):
            intent = {"category": "general", "action": "search"}
            results = mods['simple_mem'].intent_aware_retrieval(query, intent, limit=limit)
            return {
                "query": query,
                "results": [{"id": r.id, "type": r.type, "compressed": r.compressed, "importance": r.importance} for r in results],
                "count": len(results),
                "technique": "意图感知检索"
            }
        return {"error": "SimpleMem未加载"}
    except Exception as e:
        _log_error(f"SimpleMem搜索失败: {e}")
        return {"error": str(e)}

@router.post("/dream/cycle")
async def dream_cycle():
    mods = get_modules()
    try:
        if not mods['evolution_engine'] or not hasattr(mods['evolution_engine'], 'start_dreaming'):
            return {"error": "梦境循环未加载"}
        result = await mods['evolution_engine'].start_dreaming()
        return result
    except Exception as e:
        _log_error(f"梦境循环失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/dream/status")
async def dream_status_api():
    mods = get_modules()
    try:
        if mods['dream_loop']:
            return {
                "available": True,
                "total_dreams": len(mods['dream_loop'].dreams),
                "recent": mods['dream_loop'].dreams[-5:] if mods['dream_loop'].dreams else [],
                "technique": "Dream Loop 3阶段 Dream+Evolve+Consolidate"
            }
        return {"available": False}
    except Exception as e:
        _log_error(f"梦境状态失败: {e}")
        return {"error": str(e)}

@router.get("/memory/v3")
async def memory_v3_api():
    mods = get_modules()
    try:
        if mods['memory_v3']:
            stats = mods['memory_v3'].get_stats()
            return {"available": True, "memory_v3": stats, "technique": "4层统一+SimpleMem压缩+遗忘"}
        return {"available": False}
    except Exception as e:
        _log_error(f"记忆v3失败: {e}")
        return {"error": str(e)}

@router.post("/memory/v3/forget")
async def memory_v3_forget():
    mods = get_modules()
    try:
        if mods['memory_v3']:
            result = mods['memory_v3'].forget_low_value()
            return result
        return {"error": "memory_v3未加载"}
    except Exception as e:
        _log_error(f"遗忘失败: {e}")
        return {"error": str(e)}

@router.get("/memory/v3/search")
async def memory_v3_search(query: str, type: str = None, limit: int = 5):
    mods = get_modules()
    try:
        if mods['memory_v3']:
            results = mods['memory_v3'].search(query, type=type, limit=limit)
            return {"query": query, "results": results, "count": len(results)}
        return {"error": "memory_v3未加载"}
    except Exception as e:
        _log_error(f"记忆v3搜索失败: {e}")
        return {"error": str(e)}

@router.get("/skills/gene")
async def skills_gene():
    mods = get_modules()
    try:
        if mods['skill_gene_evolution']:
            tree = mods['skill_gene_evolution'].get_evolution_tree()
            return {"available": True, "gene": tree, "technique": "技能基因进化变异交叉选择"}
        return {"available": False}
    except Exception as e:
        _log_error(f"技能基因失败: {e}")
        return {"error": str(e)}

@router.post("/skills/gene/evolve")
async def skills_gene_evolve():
    mods = get_modules()
    try:
        if mods['skill_gene_evolution']:
            result = mods['skill_gene_evolution'].evolve(num_mutations=2, num_crossovers=2)
            return result
        return {"error": "skill_gene_evolution未加载"}
    except Exception as e:
        _log_error(f"技能基因进化失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}
