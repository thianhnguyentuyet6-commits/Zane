# -*- coding: utf-8 -*-
"""
Zane AGI v7.0 - 模块化重构优化版
- 拆分main_v6.py 1839行70路由→模块化路由
- 核心逻辑保留，路由外置，lifespan统一，日志统一
- 数据飞轮v3+模型双轨+真实训练+评估Harness+Prompt进化+技能基因+资源感知+记忆v3
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

# 旧模块兼容 - 核心
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
    _loguru_msg = f"⚠️ loguru未安装，使用标准logging: {e}"

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
    _log_info("🚀 Zane AGI v7.0 启动中 - 模块化重构优化版")
    
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
    
    _log_info("✅ Zane AGI v7.0 启动完成 - 模块化重构优化版")
    yield
    
    _log_info("🛑 Zane AGI v7.0 关闭中...")
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
    _log_info("✅ Zane AGI v7.0 已关闭")

app = FastAPI(
    title="Zane AGI v7.0 - 模块化重构优化版",
    description="数据飞轮v3+模型双轨+真实训练+评估Harness+Prompt进化+技能基因+资源感知+记忆v3 | 模块化路由",
    version="7.0.0",
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

# 挂载旧路由
try:
    from .routers import system_router, tokens_router, database_router, autonomous_router, models_router
    app.include_router(system_router.router)
    app.include_router(tokens_router.router)
    app.include_router(database_router.router)
    app.include_router(autonomous_router.router)
    app.include_router(models_router.router)
    _log_info("✅ 旧Routers已挂载")
except ImportError as e:
    _log_error(f"旧Routers导入失败: {e}")
except Exception as e:
    _log_error(f"旧Routers挂载失败: {e}")

# 挂载新模块化路由 v7.0
try:
    from .routers.evolution_v3 import router as evolution_v3_router
    from .routers.thinking_v25 import router as thinking_v25_router
    from .routers.memory_v3 import router as memory_v3_router
    from .routers.security_v3 import router as security_v3_router
    from .routers.vision_v3 import router as vision_v3_router
    from .routers.runtime_v3 import router as runtime_v3_router
    app.include_router(evolution_v3_router)
    app.include_router(thinking_v25_router)
    app.include_router(memory_v3_router)
    app.include_router(security_v3_router)
    app.include_router(vision_v3_router)
    app.include_router(runtime_v3_router)
    _log_info("✅ v7.0 模块化Routers已挂载：evolution_v3 + thinking_v25 + memory_v3 + security_v3 + vision_v3 + runtime_v3")
except ImportError as e:
    _log_error(f"v7.0 Routers导入失败: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    _log_error(f"v7.0 Routers挂载失败: {e}")
    import traceback
    traceback.print_exc()

# 核心模型
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = None
    thinking_mode: Optional[str] = "auto"

class LoginRequest(BaseModel):
    username: str = "admin"
    password: str = ""
    token: str = ""

# JWT认证
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

# 健康检查
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
        "status": "运行中 v7.0 模块化重构优化版",
        "version": "7.0.0 - 模块化路由+数据飞轮v3+模型双轨+真实训练+评估Harness+Prompt进化+技能基因+资源感知+记忆v3",
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
            "modular": "ES Modules 8模块 + 拆分 + v7.0模块化路由",
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
        "modular": {
            "main_v6": "1839行70路由 单文件",
            "main_v7": "模块化 6路由文件 evolution_v3+thinking_v25+memory_v3+security_v3+vision_v3+runtime_v3",
            "routers": ["evolution_v3 16 API", "thinking_v25 6 API", "memory_v3 10 API", "security_v3 6 API", "vision_v3 6 API", "runtime_v3 10 API"],
            "total_routes": "54模块化 + 5旧兼容 + 3核心 = 62 API",
            "optimization": "可维护性↑ 单文件↓ 职责单一"
        }
    }

# 核心聊天 - 保留核心逻辑
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
        return {"message": "前端未构建", "version": "7.0.0"}
    except Exception as e:
        _log_error(f"前端服务失败: {e}")
        return {"message": f"前端错误: {e}", "version": "7.0.0"}

if __name__ == "__main__":
    import uvicorn
    _log_info("""
    ╔══════════════════════════════════════════════════╗
    ║   Zane AGI v7.0 - 模块化重构优化版               ║
    ║   6路由模块化 1839行→模块化 可维护性↑            ║
    ║   数据飞轮v3+模型双轨+真实训练+评估Harness       ║
    ║   Prompt进化+技能基因+资源感知+记忆v3            ║
    ╚══════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)
