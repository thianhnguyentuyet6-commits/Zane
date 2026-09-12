# -*- coding: utf-8 -*-
"""
Zane AGI v6.0 - 进化路由 v3.0
- 拆分自 main_v6.py 16个进化API，优化可维护性
- 数据飞轮v3过滤评分去重安全+模型双轨+真实训练+评估Harness+Prompt进化+技能基因+资源感知
"""
import time
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 日志
try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False
    import logging
    loguru_logger = logging.getLogger("zane")

def _log_info(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.info(msg)
    else:
        print(msg)

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

router = APIRouter(prefix="/api/evolution", tags=["进化引擎v3.0"])

# 延迟导入，避免循环依赖
def get_modules():
    modules = {}
    try:
        from ..runtime.data_filter import data_filter
        modules['data_filter'] = data_filter
    except ImportError:
        modules['data_filter'] = None
    try:
        from ..memory.data_flywheel_v3 import data_flywheel_v3
        modules['data_flywheel_v3'] = data_flywheel_v3
        modules['data_flywheel'] = data_flywheel_v3
    except ImportError:
        try:
            from ..memory.data_flywheel import data_flywheel
            modules['data_flywheel'] = data_flywheel
            modules['data_flywheel_v3'] = None
        except ImportError:
            modules['data_flywheel'] = None
            modules['data_flywheel_v3'] = None
    try:
        from ..learning.model_resolver import model_resolver
        modules['model_resolver'] = model_resolver
    except ImportError:
        modules['model_resolver'] = None
    try:
        from ..learning.unsloth_trainer_v3 import unsloth_trainer_v3
        modules['unsloth_trainer_v3'] = unsloth_trainer_v3
        modules['unsloth_trainer'] = unsloth_trainer_v3
    except ImportError:
        try:
            from ..learning.unsloth_trainer import unsloth_trainer
            modules['unsloth_trainer'] = unsloth_trainer
            modules['unsloth_trainer_v3'] = None
        except ImportError:
            modules['unsloth_trainer'] = None
            modules['unsloth_trainer_v3'] = None
    try:
        from ..learning.replay_buffer import replay_buffer
        modules['replay_buffer'] = replay_buffer
    except ImportError:
        modules['replay_buffer'] = None
    try:
        from ..benchmark.evolution_eval import evolution_eval
        modules['evolution_eval'] = evolution_eval
    except ImportError:
        modules['evolution_eval'] = None
    try:
        from ..learning.prompt_evolution import prompt_evolution
        modules['prompt_evolution'] = prompt_evolution
    except ImportError:
        modules['prompt_evolution'] = None
    try:
        from ..learning.strategy_evolution import strategy_evolution
        modules['strategy_evolution'] = strategy_evolution
    except ImportError:
        modules['strategy_evolution'] = None
    try:
        from ..runtime.skill_gene import skill_gene_evolution
        modules['skill_gene_evolution'] = skill_gene_evolution
    except ImportError:
        modules['skill_gene_evolution'] = None
    try:
        from ..runtime.resource_monitor import resource_monitor
        modules['resource_monitor'] = resource_monitor
    except ImportError:
        modules['resource_monitor'] = None
    try:
        from ..autonomous.scheduler_v3 import scheduler_v3
        modules['scheduler_v3'] = scheduler_v3
    except ImportError:
        modules['scheduler_v3'] = None
    try:
        from ..learning.evolution_engine_v25 import evolution_engine_v25 as evolution_engine
        modules['evolution_engine'] = evolution_engine
    except ImportError:
        try:
            from ..learning.evolution_engine import evolution_engine
            modules['evolution_engine'] = evolution_engine
        except ImportError:
            modules['evolution_engine'] = None
    return modules

class FilterTestRequest(BaseModel):
    content: str
    tools: List[str] = []

@router.get("/vram")
async def evolution_vram():
    """VRAM检测 - 模型双轨推荐"""
    mods = get_modules()
    try:
        if mods['model_resolver']:
            vram = mods['model_resolver'].check_vram()
            all_info = mods['model_resolver'].get_all()
            return {"available": True, "vram": vram, "all": all_info, "technique": "VRAM检测+模型双轨推荐"}
        return {"available": False, "error": "model_resolver未加载"}
    except Exception as e:
        _log_error(f"VRAM检测失败: {e}")
        return {"error": str(e)}

@router.get("/resources")
async def evolution_resources():
    """资源监控 - CPU/内存/VRAM/插电/游戏/iOS 5维度"""
    mods = get_modules()
    try:
        if mods['resource_monitor']:
            resources = mods['resource_monitor'].get_all()
            return {"available": True, "resources": resources, "technique": "CPU/内存/VRAM/插电/游戏检测"}
        return {"available": False}
    except Exception as e:
        _log_error(f"资源监控失败: {e}")
        return {"error": str(e)}

@router.get("/filter/stats")
async def evolution_filter_stats():
    """数据过滤统计 - 飞轮v3"""
    mods = get_modules()
    try:
        if mods['data_flywheel_v3']:
            stats = mods['data_flywheel_v3'].get_training_stats()
            return {"available": True, "stats": stats, "technique": "数据飞轮v3过滤评分去重安全"}
        return {"available": False}
    except Exception as e:
        _log_error(f"过滤统计失败: {e}")
        return {"error": str(e)}

@router.get("/filter/test")
async def evolution_filter_test_get(content: str, tools: str = ""):
    """测试过滤器 GET - 安全检查"""
    mods = get_modules()
    try:
        tools_list = [t.strip() for t in tools.split(",") if t.strip()] if tools else []
        if mods['data_filter']:
            sample = {"task": content, "tools": tools_list, "conversations": [{"from": "human", "value": content}]}
            is_safe, reason = mods['data_filter'].is_safe(sample)
            importance = mods['data_filter'].score_importance(sample)
            return {"content": content, "tools": tools_list, "is_safe": is_safe, "reason": reason, "importance": importance, "technique": "数据过滤安全检查"}
        return {"error": "data_filter未加载"}
    except Exception as e:
        _log_error(f"过滤测试失败: {e}")
        return {"error": str(e)}

@router.post("/filter/test")
async def evolution_filter_test(request: FilterTestRequest):
    """测试过滤器 POST - 安全检查 JSON模式"""
    mods = get_modules()
    try:
        if mods['data_filter']:
            sample = {"task": request.content, "tools": request.tools, "conversations": [{"from": "human", "value": request.content}]}
            is_safe, reason = mods['data_filter'].is_safe(sample)
            importance = mods['data_filter'].score_importance(sample)
            return {"content": request.content, "tools": request.tools, "is_safe": is_safe, "reason": reason, "importance": importance, "technique": "数据过滤安全检查"}
        return {"error": "data_filter未加载"}
    except Exception as e:
        _log_error(f"过滤测试失败: {e}")
        return {"error": str(e)}

@router.post("/training/start")
async def evolution_training_start():
    """启动真实训练 - Unsloth非阻塞+日志流+LoRA版本"""
    mods = get_modules()
    try:
        if not mods['unsloth_trainer_v3']:
            return {"error": "unsloth_trainer_v3未加载"}
        
        if mods['data_flywheel_v3']:
            stats = mods['data_flywheel_v3'].get_training_stats()
            sft_file = str(mods['data_flywheel_v3'].sft_v3_path) if mods['data_flywheel_v3'].sft_v3_path.exists() else str(mods['data_flywheel_v3'].sft_path)
        elif mods['data_flywheel']:
            stats = mods['data_flywheel'].get_training_stats() if hasattr(mods['data_flywheel'], 'get_training_stats') else {"sft_samples": 0}
            sft_file = "data/training/sft.jsonl"
        else:
            stats = {"sft_samples": 0}
            sft_file = "data/training/sft.jsonl"
        
        output_dir = f"models/versions/lora_{int(time.time())}"
        config = {
            "samples": stats.get("sft_samples", 0),
            "lora_rank": 32,
            "lora_alpha": 64,
            "learning_rate": 2e-4,
            "num_epochs": 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        result = mods['unsloth_trainer_v3'].start_training(sft_file, output_dir, config)
        return result
    except Exception as e:
        _log_error(f"训练启动失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/training/status")
async def evolution_training_status():
    mods = get_modules()
    try:
        if mods['unsloth_trainer_v3']:
            status = mods['unsloth_trainer_v3'].get_training_status()
            return status
        return {"error": "训练器未加载"}
    except Exception as e:
        _log_error(f"训练状态失败: {e}")
        return {"error": str(e)}

@router.post("/training/stop")
async def evolution_training_stop():
    mods = get_modules()
    try:
        if mods['unsloth_trainer_v3']:
            result = mods['unsloth_trainer_v3'].stop_training()
            return result
        return {"error": "训练器未加载"}
    except Exception as e:
        _log_error(f"训练停止失败: {e}")
        return {"error": str(e)}

@router.post("/evaluate")
async def evolution_evaluate():
    """评估Harness - Benchmark 20任务+Replay 30%+2%阈值"""
    mods = get_modules()
    try:
        if mods['evolution_eval']:
            result = mods['evolution_eval'].evaluate_with_replay()
            promotion = mods['evolution_eval'].should_promote(result, threshold=2.0, mode="balanced")
            return {"available": True, "eval": result, "promotion": promotion, "technique": "Benchmark 20任务+Replay 30%+2%阈值"}
        return {"available": False}
    except Exception as e:
        _log_error(f"评估失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/replay")
async def evolution_replay():
    """Replay Buffer - 30%防遗忘"""
    mods = get_modules()
    try:
        if mods['replay_buffer']:
            result = mods['replay_buffer'].build(ratio=0.3, min_quality=0.8)
            samples = mods['replay_buffer'].get_replay_samples(limit=5)
            return {"available": True, "replay": result, "samples": samples}
        return {"available": False}
    except Exception as e:
        _log_error(f"Replay失败: {e}")
        return {"error": str(e)}

@router.get("/prompts")
async def evolution_prompts():
    """Prompt版本 - Darwin Gödel Machine"""
    mods = get_modules()
    try:
        if mods['prompt_evolution']:
            prompts = mods['prompt_evolution'].list_prompts()
            return {"available": True, "prompts": prompts, "total": len(prompts), "technique": "Darwin Gödel Machine"}
        return {"available": False}
    except Exception as e:
        _log_error(f"Prompt列表失败: {e}")
        return {"error": str(e)}

@router.post("/prompts/evolve")
async def evolution_prompts_evolve():
    """Prompt进化 - 变异交叉选择"""
    mods = get_modules()
    try:
        if mods['prompt_evolution']:
            result = mods['prompt_evolution'].evolve(num_mutations=3, num_crossovers=2)
            return result
        return {"error": "prompt_evolution未加载"}
    except Exception as e:
        _log_error(f"Prompt进化失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/strategies")
async def evolution_strategies(task_type: str = "file_organize"):
    """策略进化 - AlphaEvolve最优工具链"""
    mods = get_modules()
    try:
        if mods['strategy_evolution']:
            result = mods['strategy_evolution'].evolve_workflow(task_type=task_type)
            return {"available": True, "strategy": result, "technique": "AlphaEvolve最优工具链搜索"}
        return {"available": False}
    except Exception as e:
        _log_error(f"策略进化失败: {e}")
        return {"error": str(e)}

@router.get("/scheduler")
async def evolution_scheduler():
    """调度器状态 - 凌晨2点+每30分+资源感知"""
    mods = get_modules()
    try:
        if mods['scheduler_v3']:
            check = mods['scheduler_v3'].check_ready()
            return {"available": True, "scheduler": check, "config": mods['scheduler_v3'].config}
        return {"available": False}
    except Exception as e:
        _log_error(f"调度器状态失败: {e}")
        return {"error": str(e)}

@router.get("/stream")
async def evolution_stream():
    """SSE推送训练进度"""
    mods = get_modules()
    async def event_generator():
        for i in range(100):
            status = {}
            try:
                if mods['unsloth_trainer_v3']:
                    status = mods['unsloth_trainer_v3'].get_training_status()
            except Exception:
                status = {"status": "idle"}
            
            data = {
                "timestamp": time.time(),
                "iteration": i,
                "status": status,
                "message": f"进化进度 {i}%"
            }
            
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(2)
            
            if status.get("status") in ["completed", "failed"]:
                break
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/status")
async def evolution_status():
    mods = get_modules()
    try:
        if mods['evolution_engine']:
            return mods['evolution_engine'].get_status()
        return {"status": "unknown"}
    except Exception as e:
        _log_error(f"进化状态失败: {e}")
        return {"status": "error", "error": str(e)}

@router.post("/start")
async def evolution_start(manual: bool = True):
    mods = get_modules()
    try:
        if mods['evolution_engine']:
            result = await mods['evolution_engine'].start_evolution(manual=manual)
            return result
        return {"error": "进化引擎不可用"}
    except Exception as e:
        _log_error(f"进化启动失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/data")
async def evolution_data():
    mods = get_modules()
    try:
        flywheel = mods.get('data_flywheel_v3') or mods.get('data_flywheel')
        if not flywheel:
            return {"stats": {}, "recent": []}
        stats = flywheel.get_training_stats()
        recent = flywheel.get_recent_samples(10)
        return {"stats": stats, "recent": recent}
    except Exception as e:
        _log_error(f"进化数据失败: {e}")
        return {"stats": {}, "recent": [], "error": str(e)}
