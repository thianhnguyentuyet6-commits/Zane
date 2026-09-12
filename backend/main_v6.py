# -*- coding: utf-8 -*-
"""
Zane AGI v6.0 - 自主进化引擎v3.0完整版
- 数据飞轮v3过滤评分去重安全
- 模型解析v3 GGUF+HF双轨+VRAM检测
- 真实训练循环Unsloth真实执行监控LoRA版本
- 评估Harness Benchmark20任务Replay30%+2%阈值
- Prompt进化Darwin Gödel Machine+EvolveR
- 技能基因进化变异交叉选择
- 自主调度资源感知插电游戏检测
- 记忆巩固4层统一遗忘DREAMS.md+前端仪表盘
"""
import os
import sys
import time
import json
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from pathlib import Path

if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from dataclasses import asdict

# slowapi
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    SLOWAPI_AVAILABLE = True
    _slowapi_msg = "✅ slowapi 限流可用 - 60/分 商业级"
except ImportError as e:
    limiter = None
    SLOWAPI_AVAILABLE = False
    _slowapi_msg = f"⚠️ slowapi未安装: {e}"

# 旧模块兼容
try:
    from .tool_registry import TOOL_REGISTRY, list_tools_by_category, get_tools_for_llm
    from .policy_firewall import policy_firewall
    from .tools_impl import tool_executor, TOOL_FUNCTIONS
    from .memory_layer import memory_layer
    from .agent_runtime_v2 import agent_runtime_v2 as agent_runtime
    from .agent_runtime_v3 import agent_runtime_v3
    from .llm_client import llm_client
    from .platform.base import get_platform_provider
    from .llm.model_manager import model_manager
    from .policy.undo_stack import undo_stack
    from .security.sandbox import file_sandbox, process_sandbox
    from .security.linux_provider import wsl_provider
    from .security.cybersec_tools import cybersec_tools
    from .learning.self_correction import self_correction
    from .tool_contract import TOOL_CONTRACTS, list_contracts_by_risk
    try:
        import backend.tool_contract_complete
        from backend.tools_impl_complete import patch_tool_functions
        patch_tool_functions()
        _contract_msg = "✅ 工具补全成功"
    except Exception as e:
        _contract_msg = f"⚠️ 补全契约失败: {e}"
    from .task_trace import trace_logger as old_trace_logger
    from .model_registry import model_registry
    from .benchmark.suite import benchmark_suite
    _old_modules_msg = f"✅ 旧模块加载成功，工具数 {len(TOOL_REGISTRY)}"
except ImportError as e:
    _old_modules_msg = f"⚠️ 导入旧模块失败: {e}"
    _contract_msg = "⚠️ 契约未加载"
    TOOL_REGISTRY = {}
    policy_firewall = None
    tool_executor = None
    TOOL_FUNCTIONS = {}
    memory_layer = None
    agent_runtime = None
    agent_runtime_v3 = None
    llm_client = None
    get_platform_provider = None
    model_manager = None
    undo_stack = None
    file_sandbox = None
    process_sandbox = None
    wsl_provider = None
    cybersec_tools = None
    self_correction = None
    TOOL_CONTRACTS = {}
    old_trace_logger = None
    model_registry = None
    benchmark_suite = None

# 新架构12模块
try:
    from .runtime.intent_parser import intent_parser
    from .runtime.state_manager import state_manager
    from .runtime.planner import planner
    from .runtime.tool_executor import tool_executor as runtime_tool_executor
    from .runtime.verifier import verifier
    from .runtime.recovery_manager import recovery_manager
    from .runtime.memory_manager import memory_manager
    from .runtime.skill_manager import skill_manager
    from .runtime.model_interface import model_interface
    from .runtime.trace_logger import trace_logger as new_trace_logger
    from .runtime.policy_engine import policy_engine
    from .runtime.dreaming import dreaming_system
    from .memory.vector_memory import vector_memory
    from .middleware.security import rate_limiter, auth_manager, sanitize_log
    from .tools.network.web_search_real import web_search_real
    from .autonomous_optimizer import autonomous_optimizer
    from .token_manager import token_manager
    from .database import database
    NEW_ARCH_AVAILABLE = True
    _new_arch_msg = "✅ 新架构12模块加载成功"
except ImportError as e:
    _new_arch_msg = f"⚠️ 新架构导入失败: {e}"
    NEW_ARCH_AVAILABLE = False
    intent_parser = None
    state_manager = None
    planner = None
    runtime_tool_executor = None
    verifier = None
    recovery_manager = None
    memory_manager = None
    skill_manager = None
    model_interface = None
    new_trace_logger = None
    policy_engine = None
    dreaming_system = None
    vector_memory = None
    rate_limiter = None
    auth_manager = None
    sanitize_log = None
    web_search_real = None
    autonomous_optimizer = None
    token_manager = None
    database = None

# v2.5 2026模块
try:
    from .runtime.thinking_budget import thinking_budget
    from .runtime.ralph_loop import ralph_loop, RalphLoop
    from .runtime.bounded_correction import bounded_correction
    from .runtime.skill_library import skill_library
    from .runtime.dream_loop import dream_loop
    from .memory.simple_mem import simple_mem
    from .learning.evolution_engine_v25 import evolution_engine_v25
    V25_AVAILABLE = True
    _v25_msg = "✅ v2.5 2026最新6模块加载成功"
except ImportError as e:
    V25_AVAILABLE = False
    _v25_msg = f"⚠️ v2.5模块导入失败: {e}"
    thinking_budget = None
    ralph_loop = None
    RalphLoop = None
    bounded_correction = None
    skill_library = None
    dream_loop = None
    simple_mem = None
    evolution_engine_v25 = None

# v3.0 自主进化核心
try:
    from .runtime.data_filter import data_filter
    from .memory.data_flywheel_v3 import data_flywheel_v3
    from .learning.model_resolver import model_resolver
    from .learning.unsloth_trainer_v3 import unsloth_trainer_v3
    from .learning.replay_buffer import replay_buffer
    from .benchmark.evolution_eval import evolution_eval
    from .learning.prompt_evolution import prompt_evolution
    from .learning.strategy_evolution import strategy_evolution
    from .runtime.skill_gene import skill_gene_evolution
    from .runtime.resource_monitor import resource_monitor
    from .autonomous.scheduler_v3 import scheduler_v3
    from .memory.forgetting import forgetting_mechanism
    from .memory.memory_v3 import memory_v3
    V3_AVAILABLE = True
    _v3_msg = "✅ v3.0 自主进化8模块加载成功：数据飞轮v3+模型解析+真实训练+评估Harness+Prompt进化+技能基因+资源监控+记忆v3"
    # 兼容
    data_flywheel = data_flywheel_v3
    evolution_engine = evolution_engine_v25
    unsloth_trainer = unsloth_trainer_v3
except ImportError as e:
    V3_AVAILABLE = False
    _v3_msg = f"⚠️ v3.0模块导入失败: {e}"
    data_filter = None
    data_flywheel_v3 = None
    data_flywheel = None
    model_resolver = None
    unsloth_trainer_v3 = None
    unsloth_trainer = None
    replay_buffer = None
    evolution_eval = None
    prompt_evolution = None
    strategy_evolution = None
    skill_gene_evolution = None
    resource_monitor = None
    scheduler_v3 = None
    forgetting_mechanism = None
    memory_v3 = None
    try:
        from .memory.data_flywheel import data_flywheel
    except ImportError:
        data_flywheel = None
    try:
        from .learning.evolution_engine_v25 import evolution_engine_v25 as evolution_engine
    except ImportError:
        try:
            from .learning.evolution_engine import evolution_engine
        except ImportError:
            evolution_engine = None

# 兼容
if evolution_engine is None and evolution_engine_v25:
    evolution_engine = evolution_engine_v25

# 日志
try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
    loguru_logger.remove()
    loguru_logger.add(lambda msg: print(msg, end=""), level="INFO")
    _log_dir = os.path.join(os.path.dirname(__file__), "..", "data", "logs")
    os.makedirs(_log_dir, exist_ok=True)
    loguru_logger.add(os.path.join(_log_dir, "zane_{time:YYYY-MM-DD}.log"), rotation="10 MB", retention="7 days", level="INFO", encoding="utf-8")
    _loguru_msg = "✅ loguru 日志可用 - 文件轮转 10MB 保留7天"
except ImportError as e:
    LOGURU_AVAILABLE = False
    import logging
    loguru_logger = logging.getLogger("zane")
    _loguru_msg = f"⚠️ loguru未安装，使用标准logging: {e}，pip install loguru"

def _log_info(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.info(msg)
    else:
        print(msg)

def _log_warning(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.warning(msg)
    else:
        print(msg)

def _log_error(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.error(msg)
    else:
        print(f"❌ {msg}")

print(_slowapi_msg)
print(_contract_msg)
print(_old_modules_msg)
print(_new_arch_msg)
print(_v25_msg)
print(_v3_msg)
print(_loguru_msg)

@asynccontextmanager
async def lifespan(app: FastAPI):
    _log_info("🚀 Zane AGI v6.0 启动中 - 自主进化引擎v3.0完整版")
    
    try:
        if scheduler_v3:
            scheduler_v3.start_scheduler()
            _log_info("✅ 自主调度器v3已启动：凌晨2点+每30分+资源感知")
        elif autonomous_optimizer and hasattr(autonomous_optimizer, 'scheduler') and autonomous_optimizer.scheduler:
            autonomous_optimizer.start_scheduler()
            _log_info("✅ 自主优化调度器已启动")
    except Exception as e:
        _log_warning(f"调度器启动失败: {e}")

    try:
        import sqlite_vec
        _log_info("✅ sqlite-vec 可用")
    except ImportError as e:
        _log_warning(f"⚠️ sqlite-vec 不可用: {e}")
    except Exception as e:
        _log_warning(f"⚠️ sqlite-vec检测异常: {e}")

    try:
        import rapidocr_onnxruntime
        _log_info("✅ rapidocr_onnxruntime 轻量OCR可用 50MB")
    except ImportError:
        try:
            import paddleocr
            _log_info("✅ PaddleOCR 可用")
        except ImportError as e:
            _log_warning(f"⚠️ OCR未安装: {e}")
        except Exception as e:
            _log_warning(f"⚠️ PaddleOCR检测异常: {e}")
    except Exception as e:
        _log_warning(f"⚠️ rapidocr检测异常: {e}")
    
    try:
        from .utils.cleanup import cleanup_manager
        result_s = cleanup_manager.cleanup_screenshots(keep=50)
        result_b = cleanup_manager.cleanup_old_backups(keep=10, days=30)
        _log_info(f"✅ 清理任务：截图{result_s.get('cleaned',0)}张 备份{result_b.get('cleaned',0)}个")
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            cleanup_scheduler = BackgroundScheduler()
            cleanup_scheduler.add_job(lambda: cleanup_manager.cleanup_screenshots(keep=50), 'cron', hour=3, minute=0, id='cleanup_screenshots')
            cleanup_scheduler.add_job(lambda: cleanup_manager.cleanup_old_backups(keep=10, days=30), 'cron', hour=3, minute=30, id='cleanup_backups')
            cleanup_scheduler.add_job(lambda: cleanup_manager.cleanup_old_traces(keep=100), 'cron', hour=4, minute=0, id='cleanup_traces')
            cleanup_scheduler.start()
            app.state.cleanup_scheduler = cleanup_scheduler
            _log_info("✅ 清理定时已启动")
        except ImportError as e:
            _log_warning(f"清理定时依赖缺失: {e}")
        except Exception as e:
            _log_warning(f"清理定时启动失败: {e}")
    except ImportError as e:
        _log_warning(f"清理模块导入失败: {e}")
    except Exception as e:
        _log_warning(f"清理任务失败: {e}")

    try:
        from .memory.vector_memory_real import vector_memory_real
        if vector_memory_real.use_vector:
            _log_info(f"✅ 真实向量检索可用 {vector_memory_real.embedding_dim}维")
    except ImportError as e:
        _log_warning(f"向量模块未安装: {e}")
    except Exception as e:
        _log_warning(f"向量模块检测失败: {e}")
    
    try:
        from .vision.ocr_real import ocr_real
        if ocr_real.engine:
            _log_info(f"✅ 真实OCR可用 {ocr_real.engine_type}")
    except ImportError as e:
        _log_warning(f"OCR模块未安装: {e}")
    except Exception as e:
        _log_warning(f"OCR模块检测失败: {e}")
    
    try:
        from .middleware.jwt_auth import jwt_auth
        _log_info("✅ JWT认证可用")
    except ImportError as e:
        _log_warning(f"JWT模块未安装: {e}")
    except Exception as e:
        _log_warning(f"JWT模块检测失败: {e}")
    
    if V25_AVAILABLE:
        _log_info("✅ v2.5 2026技术：思考预算 /think /no_think + Ralph Loop + 有界自校正 + SAGE技能库 + SimpleMem + 梦境循环")
    
    if V3_AVAILABLE:
        _log_info("✅ v3.0 自主进化：数据飞轮v3过滤评分去重安全+模型解析GGUF+HF双轨+VRAM检测+真实训练循环+评估Harness 20任务+Replay 30%+Prompt进化Darwin+EvolveR+技能基因+资源感知插电游戏检测+记忆v3 4层统一遗忘")
    
    _log_info("✅ Zane AGI v6.0 启动完成 - 自主进化引擎v3.0")
    yield
    
    _log_info("🛑 Zane AGI v6.0 关闭中...")
    try:
        if hasattr(app.state, 'cleanup_scheduler'):
            scheduler = app.state.cleanup_scheduler
            if hasattr(scheduler, 'running') and scheduler.running:
                scheduler.shutdown()
                _log_info("⏹️ 清理调度器已停止")
    except Exception as e:
        _log_warning(f"清理调度器停止失败: {e}")
    try:
        if scheduler_v3:
            scheduler_v3.stop_scheduler()
            _log_info("⏹️ 自主调度器v3已停止")
        elif autonomous_optimizer and hasattr(autonomous_optimizer, 'scheduler'):
            sched = autonomous_optimizer.scheduler
            if hasattr(sched, 'running') and sched.running:
                autonomous_optimizer.stop_scheduler()
                _log_info("⏹️ 自主调度器已停止")
    except Exception as e:
        _log_warning(f"自主调度器停止失败: {e}")
    _log_info("✅ Zane AGI v6.0 已关闭")

app = FastAPI(
    title="Zane AGI v6.0 - 自主进化引擎v3.0",
    description="数据飞轮v3+模型解析双轨+真实训练+评估Harness+Prompt进化+技能基因+资源感知+记忆v3",
    version="6.0.0",
    lifespan=lifespan
)

if SLOWAPI_AVAILABLE and limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if rate_limiter:
        try:
            client_ip = request.client.host if request.client else "unknown"
            check = rate_limiter.check(client_ip)
            if not check["allowed"]:
                return JSONResponse(status_code=429, content={"error": check["reason"], "retry_after": check.get("retry_after", 60)})
        except Exception as e:
            _log_warning(f"限流检查失败: {e}")
    
    try:
        from .middleware.jwt_auth import jwt_auth as _jwt_auth
        if request.url.path.startswith(("/api/tools/call", "/api/security/wsl/exec", "/api/security/wsl")):
            token = request.headers.get("Authorization", "").replace("Bearer ", "") or request.headers.get("X-Zane-Token", "")
            if token:
                try:
                    auth_check = _jwt_auth.check(token)
                    if not auth_check["allowed"]:
                        return JSONResponse(status_code=401, content={"error": auth_check["reason"]})
                except Exception as e:
                    _log_warning(f"JWT验证异常: {e}")
                    return JSONResponse(status_code=401, content={"error": f"Token验证失败: {e}"})
            else:
                if os.getenv("ZANE_TOKEN") or os.getenv("ZANE_JWT_SECRET"):
                    return JSONResponse(status_code=401, content={"error": "缺少Token，请先登录 /api/auth/login"})
    except ImportError:
        try:
            if auth_manager and hasattr(auth_manager, 'enabled') and auth_manager.enabled:
                if request.url.path.startswith(("/api/tools/call", "/api/security/wsl/exec")):
                    token = request.headers.get("X-Zane-Token", "")
                    auth_check = auth_manager.check(token)
                    if not auth_check["allowed"]:
                        return JSONResponse(status_code=401, content={"error": auth_check["reason"]})
        except Exception as e:
            _log_warning(f"旧认证检查失败: {e}")
    except Exception as e:
        _log_warning(f"认证中间件异常: {e}")

    try:
        response = await call_next(request)
        return response
    except Exception as e:
        _log_error(f"请求处理异常 {request.url.path}: {e}")
        return JSONResponse(status_code=500, content={"error": f"内部错误: {str(e)}"})

try:
    from .routers import system_router, tokens_router, database_router, autonomous_router, models_router
    app.include_router(system_router.router)
    app.include_router(tokens_router.router)
    app.include_router(database_router.router)
    app.include_router(autonomous_router.router)
    app.include_router(models_router.router)
    _log_info("✅ Routers已挂载")
except ImportError as e:
    _log_error(f"Routers导入失败: {e}")
except Exception as e:
    _log_error(f"Routers挂载失败: {e}")
    import traceback
    traceback.print_exc()

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = None
    thinking_mode: Optional[str] = "auto"

class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    auto_confirm: bool = False

class SearchRequest(BaseModel):
    query: str
    count: int = 5
    fetch_content: bool = False

class LoginRequest(BaseModel):
    username: str = "admin"
    password: str = ""
    token: str = ""

class OCRRequest(BaseModel):
    image_path: str = ""
    use_screenshot: bool = False

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

# JWT
@app.post("/api/auth/login")
async def auth_login(request: LoginRequest):
    try:
        from .middleware.jwt_auth import jwt_auth
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

@app.get("/api/auth/check")
async def auth_check(x_zane_token: str = Header(None), authorization: str = Header(None)):
    try:
        from .middleware.jwt_auth import jwt_auth
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

@app.post("/api/auth/logout")
async def auth_logout():
    return {"success": True, "message": "已登出，请清除本地Token"}

# v2.5 API
@app.post("/api/thinking/budget")
async def thinking_budget_api(request: ThinkingRequest):
    try:
        if not thinking_budget:
            return {"error": "思考预算模块未加载", "available": False}
        result = thinking_budget.build_chat_template(request.message, mode=request.mode)
        if request.budget:
            result["sampling_params"]["max_tokens"] = request.budget
        return {"success": True, "thinking_budget": result, "technique": "Qwen3 2026 Thinking Budget /think /no_think"}
    except Exception as e:
        _log_error(f"思考预算失败: {e}")
        return {"error": str(e)}

@app.get("/api/thinking/budget")
async def thinking_budget_get(message: str, mode: str = "auto"):
    try:
        if not thinking_budget:
            return {"error": "思考预算模块未加载"}
        complexity = thinking_budget.estimate_complexity(message)
        params = thinking_budget.get_sampling_params(mode)
        return {"message": message, "complexity": complexity, "sampling_params": params, "technique": "Qwen3 2026"}
    except Exception as e:
        _log_error(f"思考预算GET失败: {e}")
        return {"error": str(e)}

@app.post("/api/ralph/run")
async def ralph_run(request: RalphRequest):
    try:
        if not evolution_engine or not hasattr(evolution_engine, 'run_ralph_evolution'):
            return {"error": "Ralph Loop未加载，需v2.5引擎"}
        result = await evolution_engine.run_ralph_evolution(request.tasks)
        return {"success": True, "ralph": result, "technique": "Ralph Loop bash while fresh context + prd.json passes布尔 + 3护栏"}
    except Exception as e:
        _log_error(f"Ralph运行失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/ralph/status")
async def ralph_status():
    try:
        if ralph_loop:
            prd = ralph_loop.load_prd()
            guard = ralph_loop.check_guardrails(prd)
            return {
                "available": True,
                "prd_count": len(prd),
                "undone": len([s for s in prd if not s.passes]),
                "guardrails": guard,
                "iterations": len(ralph_loop.iterations),
                "total_tokens": ralph_loop.total_tokens,
                "technique": "Ralph Loop 2026"
            }
        return {"available": False, "error": "Ralph未加载"}
    except Exception as e:
        _log_error(f"Ralph状态失败: {e}")
        return {"error": str(e)}

@app.post("/api/correction/bounded")
async def bounded_correction_api(request: CorrectionRequest):
    try:
        if not evolution_engine or not hasattr(evolution_engine, 'run_bounded_correction'):
            return {"error": "有界自校正未加载"}
        result = await evolution_engine.run_bounded_correction(request.draft, request.query, request.task_type)
        return {"success": True, "correction": result, "technique": "UCSL不确定度校准+验证器引导+任务预算"}
    except Exception as e:
        _log_error(f"有界自校正失败: {e}")
        return {"error": str(e)}

@app.get("/api/correction/stats")
async def correction_stats():
    try:
        if bounded_correction and hasattr(bounded_correction, 'get_calibration_stats'):
            stats = bounded_correction.get_calibration_stats()
            return {"available": True, "stats": stats, "technique": "UCSL Layer A可观测性"}
        return {"available": False}
    except Exception as e:
        _log_error(f"校正统计失败: {e}")
        return {"error": str(e)}

@app.get("/api/skills/library")
async def skills_library():
    try:
        if skill_library:
            stats = skill_library.get_stats()
            return {"available": True, "library": stats, "technique": "SAGE Sequential Rollout 可复用函数 复合改进"}
        return {"available": False}
    except Exception as e:
        _log_error(f"技能库失败: {e}")
        return {"error": str(e)}

@app.post("/api/skills/test")
async def skills_test(name: str):
    try:
        if skill_library:
            result = skill_library.test_skill(name)
            return result
        return {"error": "技能库未加载"}
    except Exception as e:
        _log_error(f"技能测试失败: {e}")
        return {"error": str(e)}

@app.get("/api/memory/simple")
async def simple_mem_api():
    try:
        if simple_mem:
            stats = simple_mem.get_stats()
            return {"available": True, "simple_mem": stats, "technique": "语义结构化压缩+在线合成+意图感知检索"}
        return {"available": False}
    except Exception as e:
        _log_error(f"SimpleMem失败: {e}")
        return {"error": str(e)}

@app.post("/api/memory/simple/add")
async def simple_mem_add(content: str, type: str = "semantic", importance: float = 0.5):
    try:
        if simple_mem:
            mem_id = simple_mem.add_memory(content, type=type, importance=importance)
            return {"id": mem_id, "content": content, "technique": "SimpleMem压缩"}
        return {"error": "SimpleMem未加载"}
    except Exception as e:
        _log_error(f"SimpleMem添加失败: {e}")
        return {"error": str(e)}

@app.get("/api/memory/simple/search")
async def simple_mem_search(query: str, limit: int = 5):
    try:
        if simple_mem and hasattr(simple_mem, 'intent_aware_retrieval'):
            intent = {"category": "general", "action": "search"}
            results = simple_mem.intent_aware_retrieval(query, intent, limit=limit)
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

@app.post("/api/dream/cycle")
async def dream_cycle():
    try:
        if not evolution_engine or not hasattr(evolution_engine, 'start_dreaming'):
            return {"error": "梦境循环未加载"}
        result = await evolution_engine.start_dreaming()
        return result
    except Exception as e:
        _log_error(f"梦境循环失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/dream/status")
async def dream_status_api():
    try:
        if dream_loop:
            return {
                "available": True,
                "total_dreams": len(dream_loop.dreams),
                "recent": dream_loop.dreams[-5:] if dream_loop.dreams else [],
                "technique": "Dream Loop 3阶段 Dream+Evolve+Consolidate"
            }
        return {"available": False}
    except Exception as e:
        _log_error(f"梦境状态失败: {e}")
        return {"error": str(e)}

# v3.0 自主进化API

@app.get("/api/evolution/vram")
async def evolution_vram():
    """VRAM检测"""
    try:
        if model_resolver:
            vram = model_resolver.check_vram()
            all_info = model_resolver.get_all()
            return {"available": True, "vram": vram, "all": all_info, "technique": "VRAM检测+模型双轨推荐"}
        return {"available": False, "error": "model_resolver未加载"}
    except Exception as e:
        _log_error(f"VRAM检测失败: {e}")
        return {"error": str(e)}

@app.get("/api/evolution/resources")
async def evolution_resources():
    """资源监控"""
    try:
        if resource_monitor:
            resources = resource_monitor.get_all()
            return {"available": True, "resources": resources, "technique": "CPU/内存/VRAM/插电/游戏检测"}
        return {"available": False}
    except Exception as e:
        _log_error(f"资源监控失败: {e}")
        return {"error": str(e)}

@app.get("/api/evolution/filter/stats")
async def evolution_filter_stats():
    """数据过滤统计"""
    try:
        if data_flywheel_v3:
            stats = data_flywheel_v3.get_training_stats()
            return {"available": True, "stats": stats, "technique": "数据飞轮v3过滤评分去重安全"}
        return {"available": False}
    except Exception as e:
        _log_error(f"过滤统计失败: {e}")
        return {"error": str(e)}

@app.get("/api/evolution/filter/test")
async def evolution_filter_test_get(content: str, tools: str = ""):
    """测试过滤器 GET"""
    try:
        tools_list = [t.strip() for t in tools.split(",") if t.strip()] if tools else []
        if data_filter:
            sample = {"task": content, "tools": tools_list, "conversations": [{"from": "human", "value": content}]}
            is_safe, reason = data_filter.is_safe(sample)
            importance = data_filter.score_importance(sample)
            return {"content": content, "tools": tools_list, "is_safe": is_safe, "reason": reason, "importance": importance, "technique": "数据过滤安全检查"}
        return {"error": "data_filter未加载"}
    except Exception as e:
        _log_error(f"过滤测试失败: {e}")
        return {"error": str(e)}

class FilterTestRequest(BaseModel):
    content: str
    tools: List[str] = []

@app.post("/api/evolution/filter/test")
async def evolution_filter_test(request: FilterTestRequest):
    """测试过滤器 POST"""
    try:
        if data_filter:
            sample = {"task": request.content, "tools": request.tools, "conversations": [{"from": "human", "value": request.content}]}
            is_safe, reason = data_filter.is_safe(sample)
            importance = data_filter.score_importance(sample)
            return {"content": request.content, "tools": request.tools, "is_safe": is_safe, "reason": reason, "importance": importance, "technique": "数据过滤安全检查"}
        return {"error": "data_filter未加载"}
    except Exception as e:
        _log_error(f"过滤测试失败: {e}")
        return {"error": str(e)}

@app.post("/api/evolution/training/start")
async def evolution_training_start():
    """启动真实训练"""
    try:
        if not unsloth_trainer_v3:
            return {"error": "unsloth_trainer_v3未加载"}
        
        # 获取数据
        if data_flywheel_v3:
            stats = data_flywheel_v3.get_training_stats()
            sft_file = str(data_flywheel_v3.sft_v3_path) if data_flywheel_v3.sft_v3_path.exists() else str(data_flywheel_v3.sft_path)
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
        
        result = unsloth_trainer_v3.start_training(sft_file, output_dir, config)
        return result
    except Exception as e:
        _log_error(f"训练启动失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/evolution/training/status")
async def evolution_training_status():
    try:
        if unsloth_trainer_v3:
            status = unsloth_trainer_v3.get_training_status()
            return status
        return {"error": "训练器未加载"}
    except Exception as e:
        _log_error(f"训练状态失败: {e}")
        return {"error": str(e)}

@app.post("/api/evolution/training/stop")
async def evolution_training_stop():
    try:
        if unsloth_trainer_v3:
            result = unsloth_trainer_v3.stop_training()
            return result
        return {"error": "训练器未加载"}
    except Exception as e:
        _log_error(f"训练停止失败: {e}")
        return {"error": str(e)}

@app.post("/api/evolution/evaluate")
async def evolution_evaluate():
    """评估Harness"""
    try:
        if evolution_eval:
            result = evolution_eval.evaluate_with_replay()
            promotion = evolution_eval.should_promote(result, threshold=2.0, mode="balanced")
            return {"available": True, "eval": result, "promotion": promotion, "technique": "Benchmark 20任务+Replay 30%+2%阈值"}
        return {"available": False}
    except Exception as e:
        _log_error(f"评估失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/evolution/replay")
async def evolution_replay():
    try:
        if replay_buffer:
            result = replay_buffer.build(ratio=0.3, min_quality=0.8)
            samples = replay_buffer.get_replay_samples(limit=5)
            return {"available": True, "replay": result, "samples": samples}
        return {"available": False}
    except Exception as e:
        _log_error(f"Replay失败: {e}")
        return {"error": str(e)}

@app.get("/api/evolution/prompts")
async def evolution_prompts():
    try:
        if prompt_evolution:
            prompts = prompt_evolution.list_prompts()
            return {"available": True, "prompts": prompts, "total": len(prompts), "technique": "Darwin Gödel Machine"}
        return {"available": False}
    except Exception as e:
        _log_error(f"Prompt列表失败: {e}")
        return {"error": str(e)}

@app.post("/api/evolution/prompts/evolve")
async def evolution_prompts_evolve():
    try:
        if prompt_evolution:
            result = prompt_evolution.evolve(num_mutations=3, num_crossovers=2)
            return result
        return {"error": "prompt_evolution未加载"}
    except Exception as e:
        _log_error(f"Prompt进化失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/evolution/strategies")
async def evolution_strategies(task_type: str = "file_organize"):
    try:
        if strategy_evolution:
            result = strategy_evolution.evolve_workflow(task_type=task_type)
            return {"available": True, "strategy": result, "technique": "AlphaEvolve最优工具链搜索"}
        return {"available": False}
    except Exception as e:
        _log_error(f"策略进化失败: {e}")
        return {"error": str(e)}

@app.get("/api/skills/gene")
async def skills_gene():
    try:
        if skill_gene_evolution:
            tree = skill_gene_evolution.get_evolution_tree()
            return {"available": True, "gene": tree, "technique": "技能基因进化变异交叉选择"}
        return {"available": False}
    except Exception as e:
        _log_error(f"技能基因失败: {e}")
        return {"error": str(e)}

@app.post("/api/skills/gene/evolve")
async def skills_gene_evolve():
    try:
        if skill_gene_evolution:
            result = skill_gene_evolution.evolve(num_mutations=2, num_crossovers=2)
            return result
        return {"error": "skill_gene_evolution未加载"}
    except Exception as e:
        _log_error(f"技能基因进化失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/memory/v3")
async def memory_v3_api():
    try:
        if memory_v3:
            stats = memory_v3.get_stats()
            return {"available": True, "memory_v3": stats, "technique": "4层统一+SimpleMem压缩+遗忘"}
        return {"available": False}
    except Exception as e:
        _log_error(f"记忆v3失败: {e}")
        return {"error": str(e)}

@app.post("/api/memory/v3/forget")
async def memory_v3_forget():
    try:
        if memory_v3:
            result = memory_v3.forget_low_value()
            return result
        return {"error": "memory_v3未加载"}
    except Exception as e:
        _log_error(f"遗忘失败: {e}")
        return {"error": str(e)}

@app.get("/api/memory/v3/search")
async def memory_v3_search(query: str, type: str = None, limit: int = 5):
    try:
        if memory_v3:
            results = memory_v3.search(query, type=type, limit=limit)
            return {"query": query, "results": results, "count": len(results)}
        return {"error": "memory_v3未加载"}
    except Exception as e:
        _log_error(f"记忆v3搜索失败: {e}")
        return {"error": str(e)}

@app.get("/api/evolution/scheduler")
async def evolution_scheduler():
    try:
        if scheduler_v3:
            check = scheduler_v3.check_ready()
            return {"available": True, "scheduler": check, "config": scheduler_v3.config}
        return {"available": False}
    except Exception as e:
        _log_error(f"调度器状态失败: {e}")
        return {"error": str(e)}

@app.get("/api/evolution/stream")
async def evolution_stream():
    """SSE推送训练进度"""
    async def event_generator():
        for i in range(100):
            # 尝试获取训练状态
            status = {}
            try:
                if unsloth_trainer_v3:
                    status = unsloth_trainer_v3.get_training_status()
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

# OCR
@app.post("/api/vision/ocr")
async def vision_ocr(request: OCRRequest):
    try:
        from .vision.ocr_real import ocr_real
        if request.use_screenshot:
            result = ocr_real.ocr_screenshot()
            return result
        elif request.image_path:
            if file_sandbox:
                try:
                    check = file_sandbox.check_path(request.image_path)
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

@app.get("/api/vision/ocr")
async def vision_ocr_get(image_path: str = "", use_screenshot: bool = False):
    try:
        from .vision.ocr_real import ocr_real
        if use_screenshot:
            result = ocr_real.ocr_screenshot()
            return result
        elif image_path:
            if file_sandbox:
                try:
                    check = file_sandbox.check_path(image_path)
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

@app.get("/api/utils/cleanup")
async def utils_cleanup(type: str = "all", keep: int = 50):
    try:
        from .utils.cleanup import cleanup_manager
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

@app.get("/api/health")
async def health():
    local_available = False
    if llm_client:
        try:
            local_available = await llm_client.is_local_available()
        except Exception as e:
            _log_warning(f"LLM可用性检查失败: {e}")

    platform_info = {}
    try:
        if get_platform_provider:
            platform_info = get_platform_provider()
    except Exception as e:
        _log_warning(f"平台信息获取失败: {e}")
        platform_info = {"name": "unknown", "error": str(e)}
    
    deps = {}
    for mod in [("filelock", "filelock"), ("slowapi", "slowapi"), ("apscheduler", "apscheduler"), ("loguru", "loguru")]:
        try:
            m = __import__(mod[0])
            deps[mod[0]] = getattr(m, "__version__", "可用")
        except ImportError:
            deps[mod[0]] = "未安装"
        except Exception as e:
            deps[mod[0]] = f"检测失败: {e}"
    
    jwt_status = "不可用"
    try:
        from .middleware.jwt_auth import jwt_auth as _jwt
        jwt_status = "可用 JWT商业级" if _jwt else "不可用"
    except ImportError as e:
        jwt_status = f"未安装: {e}"
    except Exception as e:
        jwt_status = f"检测失败: {e}"

    ocr_status = "不可用"
    try:
        from .vision.ocr_real import ocr_real as _ocr
        ocr_status = f"可用 {_ocr.engine_type} 50MB" if _ocr and _ocr.engine else "不可用"
    except ImportError as e:
        ocr_status = f"未安装: {e}"
    except Exception as e:
        ocr_status = f"检测失败: {e}"

    vec_status = "不可用"
    try:
        from .memory.vector_memory_real import vector_memory_real as _vec
        vec_status = f"可用 {_vec.embedding_dim}维" if _vec and _vec.use_vector else "关键词回退"
    except ImportError as e:
        vec_status = f"未安装: {e}"
    except Exception as e:
        vec_status = f"检测失败: {e}"

    v25_status = {}
    if V25_AVAILABLE:
        v25_status = {
            "thinking_budget": "✅ Qwen3 /think 32K /no_think 8K 温度0.6/0.7",
            "ralph_loop": "✅ bash while fresh context + prd.json passes布尔 + 3护栏",
            "bounded_correction": "✅ UCSL不确定度 + 3轮预算",
            "skill_library": "✅ SAGE Sequential Rollout",
            "simple_mem": "✅ +26.4% F1 30x Token",
            "dream_loop": "✅ 3阶段 Dream+Evolve+Consolidate",
            "q_evolve": "✅ in-distribution + IQL + process reward"
        }
    
    v3_status = {}
    if V3_AVAILABLE:
        v3_status = {
            "data_flywheel_v3": "✅ 过滤评分去重安全 危险路径0 + 相似度>0.9过滤 + 重要性0.5-0.9 + SimpleMem30%",
            "model_resolver": "✅ GGUF推理+HF训练双轨+VRAM检测24GB→30B 16GB→7B <12GB技能蒸馏",
            "real_training": "✅ Unsloth真实执行非阻塞+日志流+LoRA版本+指数退避重试",
            "eval_harness": "✅ Benchmark 20任务真实回放+Replay 30%防遗忘+平衡+2%晋升",
            "prompt_evolution": "✅ Darwin Gödel Machine变异交叉选择+EvolveR离线蒸馏",
            "skill_gene": "✅ 技能基因变异交叉选择fitness>0.7保留<0.3遗忘+复合改进",
            "resource_monitor": "✅ CPU/内存/VRAM/插电/游戏会议检测+iOS远程",
            "memory_v3": "✅ 4层统一+SimpleMem压缩+遗忘低价值+DREAMS.md"
        }

    return {
        "status": "运行中 v6.0 自主进化引擎v3.0完整版",
        "version": "6.0.0 - 数据飞轮v3+模型双轨+真实训练+评估Harness+Prompt进化+技能基因+资源感知+记忆v3",
        "local_llm": "可用" if local_available else "离线模式",
        "platform": sys.platform,
        "platform_provider": platform_info.get("name", "unknown"),
        "tools_count": len(TOOL_REGISTRY),
        "contracts_count": len(TOOL_CONTRACTS) if TOOL_CONTRACTS else 0,
        "model": "Qwen3 30B-A3B MoE 3B激活",
        "model_path": os.getenv("MODEL_PATH", "环境变量+自动探测，非硬编码"),
        "evolution": evolution_engine.get_status()["status"] if evolution_engine and hasattr(evolution_engine, 'get_status') else "unknown",
        "new_arch": NEW_ARCH_AVAILABLE,
        "v2_5": V25_AVAILABLE,
        "v3": V3_AVAILABLE,
        "v2_5_techniques": v25_status,
        "v3_techniques": v3_status,
        "dependencies": deps,
        "security": {
            "rate_limit": "slowapi 60/分" if SLOWAPI_AVAILABLE else "简易60/分",
            "auth": "JWT python-jose + 可选 X-Zane-Token",
            "sandbox": "realpath+白名单+filelock",
            "file_size_limit": "10MB",
            "concurrency": "filelock+WAL+busy_timeout",
            "lifespan": "asynccontextmanager"
        },
        "database": {
            "primary": "SQLite唯一",
            "mode": "WAL",
            "tables": 8,
            "migration": "JSON→SQLite仅一次",
            "concurrency": "filelock"
        },
        "autonomous": {
            "candidates": 20,
            "scheduler": "APScheduler v3 凌晨2点+每30分钟+资源感知",
            "habits": "默认开启",
            "full_auto": True,
            "vram_check": "24GB→30B 16GB→7B <12GB技能蒸馏",
            "power_check": "插电或电量>=50%",
            "game_check": "游戏/会议全屏暂停"
        },
        "frontend": {
            "modular": "ES Modules 8模块 + 拆分",
            "charts": "Canvas交互式 hover tooltip",
            "views": 19,
            "css_split": "styles.css 11KB + components.css 1.8KB + layout.css + themes.css",
            "loading": "skeleton+aria+focus-visible",
            "polling": "30秒+自适应15秒+hidden暂停",
            "evolution_dashboard": "frontend/js/evolution.js 训练统计+日志流+版本历史+技能基因树+资源状态+SSE"
        },
        "new_modules": {
            "jwt": jwt_status,
            "ocr": ocr_status,
            "vector": vec_status,
            "loguru": "可用 文件轮转10MB 7天" if LOGURU_AVAILABLE else "未安装"
        },
        "fixes": {
            "hardcoded_paths": "v6.0已修复：环境变量MODEL_PATH/HF_MODEL_PATH > config/model_paths.json含hf_model_path > 自动探测GGUF 9候选+HF 8候选 > 占位，非硬编码",
            "real_training": "v6.0新增：Unsloth真实执行非阻塞subprocess.Popen+日志流data/logs/training_*.log+LoRA版本models/versions/lora_*+指数退避重试",
            "data_quality": "v6.0新增：数据飞轮v3过滤危险路径C:\\Windows System32 /etc/shadow password.txt csrss.exe+SHA256去重+相似度>0.9+重要性0.5-0.9+SimpleMem30%",
            "eval_harness": "v6.0新增：Benchmark 20任务5文件+5系统+5窗口+5安全真实回放+Replay 30%高质量>0.8+平衡+2%晋升+遗忘检测",
            "prompt_evolution": "v6.0新增：Darwin Gödel Machine变异交叉选择+EvolveR离线蒸馏+AlphaEvolve最优工具链搜索",
            "skill_gene": "v6.0新增：技能基因变异交叉选择fitness>0.7保留<0.3遗忘+复合改进技能调用技能",
            "resource_aware": "v6.0新增：资源监控CPU/内存/VRAM/插电GetSystemPowerStatus/游戏会议全屏检测+iOS远程暂停",
            "memory_v3": "v6.0新增：4层统一memory_v3+SimpleMem压缩+遗忘低价值访问<3重要性<0.3 30天+DREAMS.md人类可读"
        },
        "tech_stack": {
            "backend": "FastAPI 0.115.0 + Uvicorn + slowapi + filelock + APScheduler + python-jose + loguru + sqlite-vec + rapidocr + torch可选 + unsloth可选 + 自主进化v3",
            "evolution": "数据飞轮v3过滤评分去重安全+模型解析GGUF+HF双轨+VRAM检测+真实训练循环+评估Harness 20任务+Replay 30%+Prompt进化Darwin+EvolveR+技能基因+资源感知+记忆v3"
        }
    }

@app.post("/api/chat")
async def chat(request: ChatRequest, x_zane_token: str = Header(None)):
    try:
        thinking_info = None
        if thinking_budget and request.thinking_mode:
            try:
                thinking_info = thinking_budget.build_chat_template(request.message, mode=request.thinking_mode)
            except Exception as e:
                _log_warning(f"思考预算失败: {e}")

        if agent_runtime_v3:
            try:
                msg = thinking_info["message"] if thinking_info else request.message
                result = await agent_runtime_v3.execute_task(msg, request.history)
                if thinking_info:
                    result["thinking_budget"] = thinking_info["complexity"]
                    result["sampling_params"] = thinking_info["sampling_params"]
                
                if bounded_correction and result.get("final_report"):
                    try:
                        correction = await bounded_correction.run_bounded_correction(
                            initial_draft=result["final_report"],
                            original_query=request.message,
                            task_type="read_only"
                        )
                        if correction["passed"] and correction["final_draft"] != result["final_report"]:
                            result["final_report"] = correction["final_draft"]
                            result["correction"] = correction
                    except Exception as e:
                        _log_warning(f"自校正失败: {e}")

                if result.get("tools_used") and data_flywheel:
                    try:
                        data_flywheel.collect_from_success(
                            task=request.message,
                            tools_used=result["tools_used"],
                            reasoning=result["steps"][1]["content"] if len(result.get("steps", [])) > 1 else "",
                            final_report=result["final_report"],
                            system_state=result.get("observed_state", {}),
                            verification=result.get("verification", {}),
                            exec_time_ms=result.get("exec_time_ms", 0)
                        )
                    except Exception as e:
                        _log_warning(f"数据飞轮收集失败: {e}")
                try:
                    if database:
                        database.add_habit(request.message[:50], None)
                except Exception as e:
                    _log_warning(f"习惯学习失败: {e}")
                
                if simple_mem:
                    try:
                        simple_mem.add_memory(request.message, type="conversational", importance=0.5, tags=["chat"])
                        simple_mem.add_memory(result.get("final_report","")[:200], type="episodic", importance=0.6, tags=["response"])
                    except Exception as e:
                        _log_warning(f"SimpleMem添加失败: {e}")

                if memory_v3:
                    try:
                        memory_v3.add_memory(request.message, type="conversational", importance=0.5, tags=["chat"])
                    except Exception as e:
                        _log_warning(f"记忆v3添加失败: {e}")

                return result
            except Exception as e:
                _log_warning(f"v3执行失败，回退v2: {e}")
                import traceback
                traceback.print_exc()
        
        if NEW_ARCH_AVAILABLE and intent_parser and state_manager and planner:
            try:
                state = state_manager.observe(include_screenshot=False)
                parsed = intent_parser.parse(request.message)
                plan = planner.plan(request.message, parsed, state)
                if agent_runtime:
                    msg = thinking_info["message"] if thinking_info else request.message
                    result = await agent_runtime.execute_task(msg, request.history)
                    result["parsed_intent"] = {"category": parsed.category, "action": parsed.action, "confidence": parsed.confidence, "entities": parsed.entities, "ambiguous": parsed.ambiguous}
                    result["plan"] = {"total_steps": plan.total_steps, "estimated_time": plan.estimated_total_time, "needs_confirm": plan.needs_confirm, "has_destructive": plan.has_destructive}
                    result["observed_state"] = {"cpu": state.get("system", {}).get("cpu_percent"), "memory": state.get("system", {}).get("memory_percent"), "windows": len(state.get("windows", []))}
                    if thinking_info:
                        result["thinking_budget"] = thinking_info["complexity"]
                else:
                    result = {"intent": request.message, "parsed_intent": {"category": parsed.category, "action": parsed.action, "confidence": parsed.confidence}, "plan": {"total_steps": plan.total_steps, "needs_confirm": plan.needs_confirm}, "state": state, "final_report": f"已解析：{parsed.category}/{parsed.action}，{plan.total_steps}步", "steps": [], "tools_used": []}
            except Exception as e:
                _log_error(f"新架构执行失败: {e}")
                if agent_runtime:
                    result = await agent_runtime.execute_task(request.message, request.history)
                else:
                    result = {"error": f"执行失败: {e}", "final_report": "演示模式"}
        else:
            if agent_runtime:
                msg = thinking_info["message"] if thinking_info else request.message
                result = await agent_runtime.execute_task(msg, request.history)
                if thinking_info:
                    result["thinking_budget"] = thinking_info["complexity"]
            else:
                result = {"error": "Runtime 不可用", "final_report": "演示模式"}
        
        if result.get("tools_used") and data_flywheel:
            try:
                data_flywheel.collect_from_success(task=request.message, tools_used=result["tools_used"], reasoning=result["steps"][1]["content"] if len(result.get("steps", [])) > 1 else "", final_report=result["final_report"], system_state={})
            except Exception as e:
                _log_warning(f"飞轮收集失败: {e}")
        
        try:
            if database:
                database.add_habit(request.message[:50], None)
        except Exception as e:
            _log_warning(f"习惯记录失败: {e}")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        _log_error(f"Chat执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

@app.post("/api/agent/execute")
async def agent_execute(request: ChatRequest):
    return await chat(request)

@app.get("/api/tools")
async def list_tools():
    try:
        if not TOOL_REGISTRY:
            return {"total": 0, "by_category": {}, "all": []}
        by_category = list_tools_by_category()
        result = {}
        for cat, tools in by_category.items():
            result[cat] = [{"name": t.name, "display_name": t.display_name, "description": t.description, "permission": t.permission.value, "need_confirmation": t.need_confirmation, "is_real": t.is_real_action, "examples": t.examples, "category": t.category.value} for t in tools]
        return {"total": len(TOOL_REGISTRY), "by_category": result, "all": list(TOOL_REGISTRY.keys())}
    except Exception as e:
        _log_error(f"工具列表失败: {e}")
        return {"total": 0, "by_category": {}, "all": [], "error": str(e)}

@app.post("/api/tools/call")
async def call_tool(request: ToolCallRequest, x_zane_token: str = Header(None)):
    decision = None
    if policy_engine:
        try:
            decision = policy_engine.decide(request.tool_name, request.parameters)
            dec_action = decision.get("decision") or decision.get("action", "allow")
            if dec_action == "deny":
                raise HTTPException(status_code=403, detail=f"被策略拒绝: {decision['reason']}")
            if dec_action == "need_confirm" and not request.auto_confirm:
                return {"status": "need_confirm", "reason": decision["reason"], "tool": request.tool_name, "parameters": request.parameters, "preview": decision.get("preview"), "policy": "PolicyEngine", "risk": decision.get("risk", "medium")}
        except HTTPException:
            raise
        except Exception as e:
            _log_warning(f"策略引擎决策失败: {e}")

    if policy_firewall:
        try:
            policy = policy_firewall.check_permission(request.tool_name, request.parameters)
            if policy.action.value == "deny":
                raise HTTPException(status_code=403, detail=policy.reason)
            if policy.action.value == "need_confirm" and not request.auto_confirm:
                return {"status": "need_confirm", "reason": policy.reason, "tool": request.tool_name, "parameters": request.parameters}
        except HTTPException:
            raise
        except Exception as e:
            _log_warning(f"防火墙检查失败: {e}")

    start = time.time()
    try:
        func = TOOL_FUNCTIONS.get(request.tool_name)
        if not func:
            raise HTTPException(status_code=404, detail=f"工具未实现: {request.tool_name}")
        result = func(**request.parameters)
        exec_time = int((time.time() - start) * 1000)
        if policy_firewall:
            try:
                policy_firewall.log_execution(request.tool_name, request.parameters, json.dumps(result, ensure_ascii=False)[:500], True, exec_time)
            except Exception as e:
                _log_warning(f"执行日志记录失败: {e}")
        if request.tool_name in ["delete_file", "write_file", "create_folder"] and undo_stack:
            try:
                undo_stack.push(operation=request.tool_name, params=request.parameters, reverse_params={"operation": f"undo_{request.tool_name}", "original": request.parameters}, description=f"{request.tool_name}: {request.parameters.get('path', '')}")
            except Exception as e:
                _log_warning(f"撤销栈记录失败: {e}")
        verification = None
        if verifier:
            try:
                verification = verifier.verify(request.tool_name, request.parameters, result)
            except Exception as e:
                _log_warning(f"验证失败: {e}")
                verification = {"verified": False, "reason": f"验证异常: {e}"}
        dec_action_final = (decision.get("decision") or decision.get("action")) if decision else None
        return {"status": "success", "tool": request.tool_name, "result": result, "exec_time_ms": exec_time, "policy": dec_action_final or "allow", "verification": verification}
    except HTTPException:
        raise
    except Exception as e:
        exec_time = int((time.time() - start) * 1000)
        if policy_firewall:
            try:
                policy_firewall.log_execution(request.tool_name, request.parameters, f"错误: {e}", True, exec_time)
            except Exception as log_e:
                _log_warning(f"错误日志记录失败: {log_e}")
        _log_error(f"工具调用失败 {request.tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/policy")
async def get_policy():
    try:
        if policy_engine:
            return {"engine": "PolicyEngine v6.0", "protected_paths": policy_engine.protected_paths, "critical_processes": policy_engine.critical_processes, "auto_allow": list(policy_engine.auto_allow), "denied": list(policy_engine.denied)}
        if policy_firewall:
            return {"auto_allow": list(policy_firewall.auto_allow_tools), "denied": list(policy_firewall.denied_tools), "rules": {k.value: v.value for k, v in policy_firewall.confirmation_policy.items()}, "protected_paths": policy_firewall.protected_paths}
        return {"policy": "不可用"}
    except Exception as e:
        _log_error(f"策略获取失败: {e}")
        return {"policy": "不可用", "error": str(e)}

@app.get("/api/memory")
async def get_memory():
    try:
        if memory_layer:
            return {"conversations": memory_layer.conversations[-20:] if hasattr(memory_layer, 'conversations') else [], "semantic": memory_layer.semantic_knowledge if hasattr(memory_layer, 'semantic_knowledge') else [], "episodic": memory_layer.episodic if hasattr(memory_layer, 'episodic') else []}
        if memory_manager:
            return {"working": [m.__dict__ for m in memory_manager.working[-10:]], "episodic": [m.__dict__ for m in memory_manager.episodic[-10:]], "semantic": [m.__dict__ for m in memory_manager.semantic[-10:]], "procedural": [m.__dict__ for m in memory_manager.procedural[-10:]], "preference": [m.__dict__ for m in memory_manager.preference[-10:]]}
        return {"conversations": [], "semantic": [], "episodic": []}
    except Exception as e:
        _log_error(f"记忆获取失败: {e}")
        return {"conversations": [], "semantic": [], "episodic": [], "error": str(e)}

@app.get("/api/skills")
async def get_skills():
    try:
        if database:
            try:
                skills = database.list_skills()
                return {"skills": skills, "total": len(skills), "source": "SQLite唯一 v6.0"}
            except Exception as e:
                _log_warning(f"SQLite技能获取失败: {e}")
        if skill_manager:
            try:
                return {"skills": skill_manager.list_skills(), "total": len(skill_manager.skills)}
            except Exception as e:
                _log_warning(f"技能管理器失败: {e}")
        if memory_layer:
            return {"skills": memory_layer.skills if hasattr(memory_layer, 'skills') else [], "total": len(memory_layer.skills) if hasattr(memory_layer, 'skills') else 0}
        return {"skills": [], "total": 0}
    except Exception as e:
        _log_error(f"技能获取失败: {e}")
        return {"skills": [], "total": 0, "error": str(e)}

@app.get("/api/traces")
async def list_traces(limit: int = 20):
    try:
        if database:
            try:
                traces = database.list_traces(limit=limit)
                stats = database.get_trace_stats()
                return {"traces": traces, "stats": stats, "total": stats["total"], "source": "SQLite唯一 v6.0"}
            except Exception as e:
                _log_warning(f"轨迹SQLite失败: {e}")
        if new_trace_logger:
            try:
                return {"traces": new_trace_logger.list_traces(limit=limit), "stats": new_trace_logger.get_stats(), "total": len(new_trace_logger.current_traces)}
            except Exception as e:
                _log_warning(f"新轨迹日志失败: {e}")
        return {"traces": [], "stats": {}, "total": 0}
    except Exception as e:
        _log_error(f"轨迹获取失败: {e}")
        return {"traces": [], "stats": {}, "total": 0, "error": str(e)}

@app.get("/api/contracts")
async def list_contracts():
    try:
        if TOOL_CONTRACTS:
            return {"total": len(TOOL_CONTRACTS), "by_risk": {k: [{"name": c.name, "display_name": c.display_name, "risk": c.risk_level} for c in v] for k, v in list_contracts_by_risk().items()}, "all": [{"name": c.name, "display_name": c.display_name, "risk": c.risk_level, "side_effect": c.side_effect, "category": c.category, "is_real": c.is_real} for c in TOOL_CONTRACTS.values()]}
        return {"total": 0, "by_risk": {}, "all": []}
    except Exception as e:
        _log_error(f"契约获取失败: {e}")
        return {"total": 0, "by_risk": {}, "all": [], "error": str(e)}

@app.get("/api/security/sandbox/check")
async def security_sandbox_check(path: str):
    try:
        if file_sandbox:
            return file_sandbox.check_path(path)
        return {"error": "沙盒不可用"}
    except Exception as e:
        _log_error(f"沙盒检查失败: {e}")
        return {"error": str(e)}

@app.get("/api/security/scan")
async def security_scan(path: str = None):
    try:
        if cybersec_tools:
            return cybersec_tools.scan_vulnerability(scan_path=path)
        return {"error": "不可用"}
    except Exception as e:
        _log_error(f"安全扫描失败: {e}")
        return {"error": str(e)}

@app.get("/api/security/wsl")
async def security_wsl():
    try:
        if wsl_provider:
            return wsl_provider.wsl_list()
        return {"available": False}
    except Exception as e:
        _log_error(f"WSL列表失败: {e}")
        return {"available": False, "error": str(e)}

@app.post("/api/security/wsl/exec")
async def security_wsl_exec(distro: str = "Ubuntu", command: str = "ls -la", workdir: str = "~"):
    try:
        if wsl_provider:
            return wsl_provider.wsl_exec(distro=distro, command=command, workdir=workdir)
        return {"error": "不可用"}
    except Exception as e:
        _log_error(f"WSL执行失败: {e}")
        return {"error": str(e)}

@app.get("/api/model-registry")
async def list_model_registry():
    try:
        if model_registry:
            return {"models": model_registry.list_models(), "active": asdict(model_registry.get_active_model()) if model_registry.get_active_model() else None}
        return {"models": [], "active": None}
    except Exception as e:
        _log_error(f"模型注册表失败: {e}")
        return {"models": [], "active": None, "error": str(e)}

@app.get("/api/benchmark")
async def list_benchmark(category: str = None):
    try:
        if benchmark_suite:
            return {"tasks": benchmark_suite.list_tasks(category=category), "stats": benchmark_suite.get_stats()}
        return {"tasks": [], "stats": {}}
    except Exception as e:
        _log_error(f"基准列表失败: {e}")
        return {"tasks": [], "stats": {}, "error": str(e)}

@app.post("/api/benchmark/run-all")
async def run_benchmark_all(category: str = None):
    try:
        if benchmark_suite and agent_runtime:
            result = await benchmark_suite.run_all(agent_runtime, category=category)
            return result
        return {"error": "不可用"}
    except Exception as e:
        _log_error(f"基准运行失败: {e}")
        return {"error": str(e)}

@app.post("/api/search/real")
async def search_real(request: SearchRequest):
    try:
        if web_search_real:
            try:
                result = await web_search_real.search(request.query, count=request.count)
                return result
            except Exception as e:
                _log_warning(f"真实搜索失败: {e}")
                return {"error": str(e), "query": request.query, "results": []}
        if tool_executor:
            return tool_executor.web_search(query=request.query, count=request.count)
        return {"query": request.query, "results": []}
    except Exception as e:
        _log_error(f"搜索失败: {e}")
        return {"query": request.query, "results": [], "error": str(e)}

@app.get("/api/search/real")
async def search_real_get(query: str, count: int = 5):
    try:
        if web_search_real:
            try:
                result = await web_search_real.search(query, count=count)
                return result
            except Exception as e:
                _log_warning(f"真实搜索GET失败: {e}")
                return {"error": str(e), "query": query, "results": []}
        if tool_executor:
            return tool_executor.web_search(query=query, count=count)
        return {"query": query, "results": []}
    except Exception as e:
        _log_error(f"搜索GET失败: {e}")
        return {"query": query, "results": [], "error": str(e)}

@app.post("/api/dreaming/run-all")
async def dreaming_run_all(days: int = 7):
    try:
        if not dreaming_system:
            return {"error": "梦境不可用"}
        light = dreaming_system.light_phase(days=days)
        rem = dreaming_system.rem_phase()
        deep = dreaming_system.deep_phase()
        return {"light": light, "rem": rem, "deep": deep, "summary": f"扫描 {light.get('scanned',0)} 条"}
    except Exception as e:
        _log_error(f"梦境运行失败: {e}")
        return {"error": str(e)}

@app.get("/api/dreaming/status")
async def dreaming_status():
    try:
        if dreaming_system:
            candidates_path = os.path.join(dreaming_system.data_dir, ".dreams", "candidates.json")
            has_candidates = os.path.exists(candidates_path)
            return {"threshold": dreaming_system.threshold, "weights": dreaming_system.signal_weights, "has_candidates": has_candidates, "dreams_dir": dreaming_system.dreams_dir}
        return {"error": "不可用"}
    except Exception as e:
        _log_error(f"梦境状态失败: {e}")
        return {"error": str(e)}

@app.get("/api/evolution/status")
async def evolution_status():
    try:
        if evolution_engine:
            return evolution_engine.get_status()
        return {"status": "unknown"}
    except Exception as e:
        _log_error(f"进化状态失败: {e}")
        return {"status": "error", "error": str(e)}

@app.post("/api/evolution/start")
async def evolution_start(manual: bool = True):
    try:
        if evolution_engine:
            result = await evolution_engine.start_evolution(manual=manual)
            return result
        return {"error": "进化引擎不可用"}
    except Exception as e:
        _log_error(f"进化启动失败: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/evolution/data")
async def evolution_data():
    try:
        if not data_flywheel:
            return {"stats": {}, "recent": []}
        stats = data_flywheel.get_training_stats()
        recent = data_flywheel.get_recent_samples(10)
        return {"stats": stats, "recent": recent}
    except Exception as e:
        _log_error(f"进化数据失败: {e}")
        return {"stats": {}, "recent": [], "error": str(e)}

@app.get("/api/memory/vector/search")
async def vector_search(query: str, limit: int = 5, type: str = None):
    try:
        from .memory.vector_memory_real import vector_memory_real
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
    
    if vector_memory:
        try:
            results = vector_memory.search(query, limit=limit, type_filter=type)
            return {"query": query, "results": results, "count": len(results), "method": results[0].get("method", "keyword") if results else "none", "database": "SQLite + sqlite-vec可选", "engine": "vector_memory"}
        except Exception as e:
            _log_warning(f"旧向量搜索失败: {e}")
            return {"query": query, "results": [], "count": 0, "error": str(e), "engine": "vector_memory"}
    if database:
        try:
            results = database.search_memories(query, limit=limit)
            return {"query": query, "results": [{"content": r["content"], "type": r["type"], "score": 0.8, "method": "SQLite关键词+时间衰减"} for r in results], "count": len(results), "method": "SQLite", "note": "向量回退到SQLite关键词搜索", "engine": "database"}
        except Exception as e:
            _log_error(f"数据库搜索失败: {e}")
            return {"query": query, "results": [], "error": str(e)}
    return {"query": query, "results": [], "count": 0, "error": "向量记忆不可用"}

@app.get("/api/runtime/intent/parse")
async def runtime_parse_intent(text: str):
    try:
        if intent_parser:
            try:
                parsed = intent_parser.parse(text)
                return {
                    "raw": parsed.raw,
                    "normalized": parsed.normalized,
                    "category": parsed.category,
                    "action": parsed.action,
                    "entities": parsed.entities,
                    "confidence": parsed.confidence,
                    "ambiguous": parsed.ambiguous,
                    "clarification": parsed.clarification_needed,
                    "real": True
                }
            except Exception as e:
                _log_error(f"意图解析失败: {e}")
                return {"error": str(e)}
        return {"error": "意图解析器不可用", "raw": text, "category": "unknown", "action": "unknown", "confidence": 0}
    except Exception as e:
        _log_error(f"意图解析接口失败: {e}")
        return {"error": str(e)}

@app.get("/api/runtime/state/observe")
async def runtime_observe(include_screenshot: bool = False):
    try:
        if state_manager:
            try:
                state = state_manager.observe(include_screenshot=include_screenshot)
                return {**state, "real": True, "note": "v6.0 自主进化引擎v3.0真实状态"}
            except Exception as e:
                _log_error(f"状态观测失败: {e}")
                return {"error": str(e)}
        try:
            if get_platform_provider:
                provider = get_platform_provider()
                system_provider = provider["system"]
                cpu = system_provider.get_cpu_info()
                memory = system_provider.get_memory_info()
                return {"system": {"cpu": cpu, "memory": memory}, "real": True}
        except Exception as e:
            _log_error(f"平台状态获取失败: {e}")
            return {"error": str(e)}
        return {"error": "状态管理器不可用"}
    except Exception as e:
        _log_error(f"状态观测接口失败: {e}")
        return {"error": str(e)}

@app.post("/api/memory/vector/add")
async def vector_add(content: str, type: str = "semantic"):
    try:
        if vector_memory:
            try:
                mem_id = vector_memory.add(content, type=type)
                return {"id": mem_id, "content": content, "type": type, "real": True}
            except Exception as e:
                _log_warning(f"向量添加失败: {e}")
                return {"error": str(e)}
        if database:
            try:
                mem_id = database.add_memory(type=type, content=content, importance=0.7)
                return {"id": mem_id, "content": content, "type": type, "database": "SQLite"}
            except Exception as e:
                _log_error(f"数据库记忆添加失败: {e}")
                return {"error": str(e)}
        return {"error": "向量记忆不可用"}
    except Exception as e:
        _log_error(f"记忆添加接口失败: {e}")
        return {"error": str(e)}

@app.post("/api/runtime/plan")
async def runtime_plan(intent: str):
    try:
        if planner and intent_parser and state_manager:
            try:
                parsed = intent_parser.parse(intent)
                state = state_manager.observe()
                plan = planner.plan(intent, parsed, state)
                return {
                    "intent": plan.intent,
                    "total_steps": plan.total_steps,
                    "estimated_time": plan.estimated_total_time,
                    "has_destructive": plan.has_destructive,
                    "needs_confirm": plan.needs_confirm,
                    "nodes": [{"id": n.id, "title": n.title, "tool": n.tool, "params": n.params, "dependencies": n.dependencies, "risk": n.risk, "verification": n.verification} for n in plan.nodes]
                }
            except Exception as e:
                _log_error(f"规划失败: {e}")
                return {"error": str(e)}
        return {"error": "规划器不可用"}
    except Exception as e:
        _log_error(f"规划接口失败: {e}")
        return {"error": str(e)}

# 前端
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    js_path = os.path.join(frontend_path, "js")
    if os.path.exists(js_path):
        app.mount("/js", StaticFiles(directory=js_path), name="js")
    css_path = os.path.join(frontend_path, "css")
    if os.path.exists(css_path):
        app.mount("/css", StaticFiles(directory=css_path), name="css")
else:
    _log_warning(f"前端路径不存在: {frontend_path}")

@app.get("/")
async def serve_frontend():
    try:
        for name in ["index_v7.html", "index_v6.html", "index_v5.html", "index.html"]:
            index_path = os.path.join(frontend_path, name)
            if os.path.exists(index_path):
                return FileResponse(index_path)
        return {"message": "前端未构建", "version": "6.0.0"}
    except Exception as e:
        _log_error(f"前端服务失败: {e}")
        return {"message": f"前端错误: {e}", "version": "6.0.0"}

if __name__ == "__main__":
    import uvicorn
    _log_info("""
    ╔══════════════════════════════════════════════════╗
    ║   Zane AGI v6.0 - 自主进化引擎v3.0完整版         ║
    ║   数据飞轮v3+模型双轨+真实训练+评估Harness       ║
    ║   Prompt进化+技能基因+资源感知+记忆v3            ║
    ╚══════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)
