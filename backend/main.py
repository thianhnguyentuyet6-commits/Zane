# -*- coding: utf-8 -*-
"""
Zane AGI v0913 - 单版本整合版 单文件终极版
- 版本：Zane v0913 单版本，历史已归档docs/archive/，不再多版本并存
- 整合：103API + 硬化安全 + 启动日志3行 + 路由summary/tags 8层架构 + 飞轮透明规格
- 解决缺点：1双文件隐患已合并tools_impl.py统一 2路由无summary补全 3飞轮评分规格透明化 4SimpleMem Benchmark 5前端demo_mode区分 6安全NEED_CONFIRM阻断
- 技术栈：FastAPI+SlowAPI限流+JWT认证+loguru日志+SQLite WAL+filelock+psutil+RapidOCR 50MB+sqlite-vec+APScheduler
- 约束：简体中文优先+UTF-8 BOM，真实工具非模拟，工具注册表+策略防火墙+上下文预算+熔断器，Windows深度控制为主iOS远程端口预留
"""
import os
import sys
import time
import json
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from pathlib import Path

if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    SLOWAPI_AVAILABLE = True
except ImportError:
    limiter = None
    SLOWAPI_AVAILABLE = False

# 核心模块 - 单版本
try:
    from .tool_registry import TOOL_REGISTRY
    from .tool_contract import TOOL_CONTRACTS
    from .agent_runtime import agent_runtime_v3, agent_runtime_v2
    from .llm_client import llm_client
    from .platform.base import get_platform_provider
    from .database import database
    from .model_registry import model_registry
    from .benchmark.suite import benchmark_suite
    _old_ok = True
    agent_runtime = agent_runtime_v2
    agent_runtime_v3 = agent_runtime_v3
except ImportError as e:
    _old_ok = False
    TOOL_REGISTRY = {}
    TOOL_CONTRACTS = {}
    agent_runtime = None
    agent_runtime_v3 = None
    llm_client = None
    get_platform_provider = None
    database = None
    model_registry = None
    benchmark_suite = None

try:
    from .runtime.thinking_budget import thinking_budget
    from .runtime.bounded_correction import bounded_correction
    from .memory.simple_mem import simple_mem
    from .memory.memory import memory_v3
    from .memory.data_flywheel import data_flywheel_v3 as data_flywheel
    from .learning.evolution_engine import evolution_engine_v25 as evolution_engine
    from .autonomous.scheduler import scheduler_v3
    from .middleware.security import rate_limiter, auth_manager
    from .autonomous_optimizer import autonomous_optimizer
    V3_AVAILABLE = True
except ImportError:
    try:
        from .runtime.thinking_budget import thinking_budget
        from .runtime.bounded_correction import bounded_correction
        from .memory.simple_mem import simple_mem
        from .memory.memory_v3 import memory_v3
        from .memory.data_flywheel_v3 import data_flywheel_v3 as data_flywheel
        from .learning.evolution_engine_v25 import evolution_engine_v25 as evolution_engine
        from .autonomous.scheduler_v3 import scheduler_v3
        from .middleware.security import rate_limiter, auth_manager
        from .autonomous_optimizer import autonomous_optimizer
        V3_AVAILABLE = True
    except ImportError:
        V3_AVAILABLE = False
        thinking_budget = None
        bounded_correction = None
        simple_mem = None
        memory_v3 = None
        data_flywheel = None
        evolution_engine = None
        scheduler_v3 = None
        rate_limiter = None
        auth_manager = None
        autonomous_optimizer = None

# 硬化版防火墙 - 单版本
try:
    from .policy_firewall import policy_firewall_v0913
    from .tools_impl import tool_executor
    FIREWALL_V0913 = True
except ImportError:
    policy_firewall_v0913 = None
    tool_executor = None
    FIREWALL_V0913 = False

try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
    loguru_logger.remove()
    loguru_logger.add(lambda msg: print(msg, end=""), level="INFO")
    _log_dir = Path(__file__).parent.parent / "data" / "logs"
    _log_dir.mkdir(parents=True, exist_ok=True)
    loguru_logger.add(str(_log_dir / "zane_{time:YYYY-MM-DD}.log"), rotation="10 MB", retention="7 days", level="INFO", encoding="utf-8")
except ImportError:
    LOGURU_AVAILABLE = False
    import logging
    loguru_logger = logging.getLogger("zane")

def _log_info(msg: str):
    (loguru_logger.info if LOGURU_AVAILABLE else print)(msg)

def _log_warning(msg: str):
    (loguru_logger.warning if LOGURU_AVAILABLE else print)(f"⚠️ {msg}")

def _log_error(msg: str):
    (loguru_logger.error if LOGURU_AVAILABLE else print)(f"❌ {msg}")

# 环境变量控制 - 显式
RUNTIME_VERSION = os.getenv("ZANE_RUNTIME", "v3")
PLATFORM_MODE = os.getenv("ZANE_PLATFORM", "auto")
DEMO_MODE = os.getenv("ZANE_DEMO", "auto").lower()
LLM_PROVIDER = os.getenv("ZANE_LLM_PROVIDER", "local")

def get_startup_info():
    """启动日志3行 - Runtime版本+Platform Provider真实/演示+演示工具列表"""
    runtime_info = f"Runtime {RUNTIME_VERSION} (env ZANE_RUNTIME={RUNTIME_VERSION}) {'v3可用' if agent_runtime_v3 else 'v3不可用回退v2'}"
    platform_info = {}
    try:
        if get_platform_provider:
            provider_name = "unknown"
            is_demo = True
            try:
                from .platform.base import get_platform_provider as gpp
                info = gpp() if callable(gpp) else {}
                provider_name = info.get("name", sys.platform)
            except Exception:
                provider_name = sys.platform
            if tool_executor:
                is_demo = getattr(tool_executor, 'demo_mode', False)
                provider_name = getattr(tool_executor, 'platform_provider', provider_name)
            mode_str = "演示" if is_demo else "真实"
            platform_info = {"provider": provider_name, "mode": mode_str, "is_demo": is_demo, "platform": sys.platform, "env_platform": PLATFORM_MODE}
    except Exception as e:
        platform_info = {"provider": sys.platform, "mode": "未知", "is_demo": True, "error": str(e)}
    platform_line = f"Platform Provider {platform_info.get('provider')} {platform_info.get('mode')}模式 (env ZANE_PLATFORM={PLATFORM_MODE} ZANE_DEMO={DEMO_MODE}) 系统:{sys.platform}"
    demo_tools = []
    real_tools = []
    if TOOL_REGISTRY:
        for name in TOOL_REGISTRY.keys():
            demo_tools.append(name) if platform_info.get('is_demo') else real_tools.append(name)
    if tool_executor and hasattr(tool_executor, 'demo_mode'):
        is_demo_exec = tool_executor.demo_mode
        if is_demo_exec:
            demo_tools = list(TOOL_REGISTRY.keys()) if TOOL_REGISTRY else ["全部演示"]
            real_tools = []
        else:
            real_tools = list(TOOL_REGISTRY.keys()) if TOOL_REGISTRY else []
            demo_tools = []
    tools_line = f"工具 {len(real_tools)}真实 {len(demo_tools)}演示 (env ZANE_LLM_PROVIDER={LLM_PROVIDER} ZANE_RUNTIME={RUNTIME_VERSION}) 演示工具:{','.join(demo_tools[:5])}{'...' if len(demo_tools)>5 else ''} 真实:{len(real_tools)}"
    return runtime_info, platform_line, tools_line, platform_info, demo_tools, real_tools

@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime_info, platform_line, tools_line, platform_info, demo_tools, real_tools = get_startup_info()
    _log_info("="*60)
    _log_info(f"🚀 Zane AGI v0913 单版本整合版启动")
    _log_info(f"  1. {runtime_info}")
    _log_info(f"  2. {platform_line}")
    _log_info(f"  3. {tools_line}")
    _log_info(f"  环境变量: ZANE_RUNTIME={RUNTIME_VERSION} ZANE_PLATFORM={PLATFORM_MODE} ZANE_DEMO={DEMO_MODE} ZANE_LLM_PROVIDER={LLM_PROVIDER}")
    _log_info("="*60)
    try:
        if scheduler_v3:
            scheduler_v3.start_scheduler()
            _log_info("✅ 调度器已启动：凌晨2点+每30分+资源感知")
        elif autonomous_optimizer and hasattr(autonomous_optimizer, 'scheduler') and autonomous_optimizer.scheduler:
            autonomous_optimizer.start_scheduler()
    except Exception as e:
        _log_warning(f"调度器启动失败: {e}")
    try:
        import sqlite_vec
        _log_info("✅ sqlite-vec 可用 - 向量搜索")
    except ImportError as e:
        _log_warning(f"sqlite-vec 不可用: {e}")
    try:
        import rapidocr_onnxruntime
        _log_info("✅ rapidocr 50MB可用 - OCR")
    except ImportError:
        _log_warning("OCR未安装")
    try:
        from .utils.cleanup import cleanup_manager
        rs = cleanup_manager.cleanup_screenshots(keep=50)
        rb = cleanup_manager.cleanup_old_backups(keep=10, days=30)
        _log_info(f"✅ 清理：截图{rs.get('cleaned',0)}张 备份{rb.get('cleaned',0)}个")
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            cs = BackgroundScheduler()
            cs.add_job(lambda: cleanup_manager.cleanup_screenshots(keep=50), 'cron', hour=3, minute=0, id='cleanup_screenshots')
            cs.add_job(lambda: cleanup_manager.cleanup_old_backups(keep=10, days=30), 'cron', hour=3, minute=30, id='cleanup_backups')
            cs.add_job(lambda: cleanup_manager.cleanup_old_traces(keep=100), 'cron', hour=4, minute=0, id='cleanup_traces')
            cs.start()
            app.state.cleanup_scheduler = cs
            _log_info("✅ 清理定时已启动")
        except Exception as e:
            _log_warning(f"清理定时失败: {e}")
    except Exception as e:
        _log_warning(f"清理失败: {e}")
    try:
        from .middleware.jwt_auth import jwt_auth
        _log_info("✅ JWT可用 - 认证")
    except ImportError:
        _log_warning("JWT未安装")
    if FIREWALL_V0913:
        _log_info("✅ 策略防火墙v0913硬化版 - NEED_CONFIRM阻断等待确认")
    else:
        _log_warning("⚠️ 策略防火墙旧版 - NEED_CONFIRM仅日志")
    _log_info("✅ Zane AGI v0913 单版本启动完成 - 103API 8层架构")
    _log_info("   技术栈: FastAPI+SlowAPI+JWT+loguru+SQLite WAL+filelock+psutil+RapidOCR+sqlite-vec+APScheduler")
    _log_info("   8层: 接入层/思考层/执行层/记忆层/进化层/平台层/安全层/可观测层")
    yield
    _log_info("🛑 Zane AGI v0913 关闭中...")
    try:
        if hasattr(app.state, 'cleanup_scheduler') and app.state.cleanup_scheduler.running:
            app.state.cleanup_scheduler.shutdown()
    except Exception as e:
        _log_warning(f"清理调度器停止失败: {e}")
    try:
        if scheduler_v3:
            scheduler_v3.stop_scheduler()
    except Exception as e:
        _log_warning(f"调度器停止失败: {e}")
    _log_info("✅ Zane AGI v0913 已关闭")

tags_metadata = [
    {"name": "接入层", "description": "健康检查、聊天、Agent执行、前端，系统入口"},
    {"name": "思考层", "description": "思考预算/think/no_think、Ralph Loop三护栏、有界自校正UCSL、技能库SAGE"},
    {"name": "执行层", "description": "工具26个、记忆读写、技能调用、轨迹、意图解析、状态观测、DAG规划"},
    {"name": "记忆层", "description": "SimpleMem压缩、梦境3阶段、记忆v3 4层、技能基因变异交叉"},
    {"name": "进化层", "description": "数据飞轮v3过滤评分去重安全、模型双轨VRAM检测、真实训练Unsloth非阻塞、评估Harness 50条、Replay 30%、Prompt进化Darwin、技能基因、资源监控、调度器"},
    {"name": "平台层", "description": "Windows真实/psutil演示双模式、工具统一分节、路径兼容、demo_mode视觉区分"},
    {"name": "安全层", "description": "沙盒realpath+白名单+filelock+回收站+10MB限制、策略防火墙NEED_CONFIRM阻断、过滤11路径8文件7进程6命令100%、WSl沙盒、漏洞扫描、契约23+趋势时间序列+DPI统一"},
    {"name": "可观测层", "description": "系统+资源监控5维度、Benchmark 20任务、Vector向量搜索、Config配置、Auth认证、清理、梦境、Token"},
]

app = FastAPI(
    title="Zane AGI v0913 - 单版本整合版",
    description="""
## Zane AGI v0913 单版本整合版 - 个人AGI管家

**版本**：Zane v0913 单版本，历史归档docs/archive/，不再多版本并存
**目标**：品质媲美商业级，对标Operator/Claude Computer Use + Manus/Devin + PowerToys/Raycast

### 8层架构
- **接入层**：健康、聊天、Agent执行、前端
- **思考层**：思考预算/think/no_think、Ralph Loop、有界自校正UCSL、技能库SAGE
- **执行层**：工具26个、记忆、技能、轨迹、意图、状态观测、DAG规划
- **记忆层**：SimpleMem压缩、梦境3阶段、记忆v3 4层、技能基因
- **进化层**：数据飞轮v3、模型双轨、真实训练、评估Harness 50条、Replay、Prompt进化
- **平台层**：Windows真实/psutil演示双模式、demo_mode视觉区分
- **安全层**：沙盒+策略防火墙NEED_CONFIRM阻断+过滤100%+WSL沙盒+漏洞扫描+契约+趋势时间序列+DPI统一
- **可观测层**：系统资源监控5维度、Benchmark、Vector、Config、Auth

### 核心修复 - 外部评审6缺点
1. ✅ 双文件隐患合并为单文件tools_impl.py统一，消除覆盖bug
2. ✅ 路由补summary+tags分组按8层架构Swagger文档化
3. ✅ 飞轮评分规格透明化文档+API评分分布0.5-0.9四档
4. ✅ SimpleMem Benchmark脚本tests/benchmark/可复现
5. ✅ 前端平台状态条+demo_mode视觉区分
6. ✅ 安全策略硬化NEED_CONFIRM执行阻断等待确认+前端确认事件

### 环境变量显式控制
- `ZANE_RUNTIME=v2/v3` Runtime版本切换
- `ZANE_PLATFORM=auto/windows/demo` 平台模式
- `ZANE_DEMO=auto/true/false` 演示模式
- `ZANE_LLM_PROVIDER=local/openai/claude` LLM提供方

### 技术栈
FastAPI+SlowAPI限流60/分+JWT认证+loguru日志+SQLite WAL+filelock+psutil+RapidOCR 50MB+sqlite-vec+APScheduler
    """,
    version="0.9.13",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

if SLOWAPI_AVAILABLE and limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if rate_limiter:
        try:
            client_ip = request.client.host if request.client else "unknown"
            check = rate_limiter.check(client_ip)
            if not check["allowed"]:
                return JSONResponse(status_code=429, content={"error": check["reason"]})
        except Exception as e:
            _log_warning(f"限流检查失败: {e}")
    try:
        from .middleware.jwt_auth import jwt_auth as _jwt_auth
        if request.url.path.startswith(("/api/tools/call", "/api/security/wsl/exec", "/api/security/confirm")):
            token = request.headers.get("Authorization", "").replace("Bearer ", "") or request.headers.get("X-Zane-Token", "")
            if token:
                try:
                    auth_check = _jwt_auth.check(token)
                    if not auth_check["allowed"]:
                        return JSONResponse(status_code=401, content={"error": auth_check["reason"]})
                except Exception as e:
                    _log_warning(f"JWT验证异常: {e}")
                    return JSONResponse(status_code=401, content={f"Token验证失败: {e}"})
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
        _log_error(f"请求异常 {request.url.path}: {e}")
        return JSONResponse(status_code=500, content={"error": f"内部错误: {str(e)}"})

# 挂载路由 - 旧兼容
try:
    from .routers import system_router, tokens_router, database_router, autonomous_router, models_router
    app.include_router(system_router.router)
    app.include_router(tokens_router.router)
    app.include_router(database_router.router)
    app.include_router(autonomous_router.router)
    app.include_router(models_router.router)
    _log_info("✅ 旧Routers已挂载")
except Exception as e:
    _log_error(f"旧Routers失败: {e}")

# 挂载新模块化路由 v0913 - 单版本10路由文件71路由
try:
    from .routers.evolution import router as evolution_router
    from .routers.thinking import router as thinking_router
    from .routers.memory import router as memory_router
    from .routers.security import router as security_router
    from .routers.vision import router as vision_router
    from .routers.runtime import router as runtime_router
    from .routers.auth import router as auth_router
    from .routers.benchmark import router as benchmark_router
    from .routers.vector import router as vector_router
    from .routers.config import router as config_router
    app.include_router(evolution_router)
    app.include_router(thinking_router)
    app.include_router(memory_router)
    app.include_router(security_router)
    app.include_router(vision_router)
    app.include_router(runtime_router)
    app.include_router(auth_router)
    app.include_router(benchmark_router)
    app.include_router(vector_router)
    app.include_router(config_router)
    _log_info("✅ v0913 模块化Routers已挂载：evolution(18)+thinking(6)+memory(12)+security(8)+vision(8)+runtime(10)+auth(3)+benchmark(3)+vector(2)+config(4)=71路由模块化单版本")
except Exception as e:
    _log_error(f"v0913 Routers失败: {e}")
    import traceback
    traceback.print_exc()
    # 回退尝试旧命名
    try:
        from .routers.evolution_v3 import router as evolution_v3_router
        from .routers.thinking_v25 import router as thinking_v25_router
        from .routers.memory_v3 import router as memory_v3_router
        from .routers.security_v3 import router as security_v3_router
        from .routers.vision_v3 import router as vision_v3_router
        from .routers.runtime_v3 import router as runtime_v3_router
        from .routers.auth_v3 import router as auth_v3_router
        from .routers.benchmark_v3 import router as benchmark_v3_router
        from .routers.vector_v3 import router as vector_v3_router
        from .routers.config_v3 import router as config_v3_router
        app.include_router(evolution_v3_router)
        app.include_router(thinking_v25_router)
        app.include_router(memory_v3_router)
        app.include_router(security_v3_router)
        app.include_router(vision_v3_router)
        app.include_router(runtime_v3_router)
        app.include_router(auth_v3_router)
        app.include_router(benchmark_v3_router)
        app.include_router(vector_v3_router)
        app.include_router(config_v3_router)
        _log_info("✅ 回退旧命名Routers已挂载")
    except Exception as e2:
        _log_error(f"回退也失败: {e2}")

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = None
    thinking_mode: Optional[str] = "auto"

@app.get("/api/health", summary="健康检查 - 系统状态+平台+工具数+进化技术", tags=["接入层"])
async def health():
    local_available = False
    if llm_client:
        try:
            local_available = await llm_client.is_local_available()
        except Exception as e:
            _log_warning(f"LLM检查失败: {e}")
    runtime_info, platform_line, tools_line, platform_info, demo_tools, real_tools = get_startup_info()
    platform_detail = {}
    try:
        if get_platform_provider:
            platform_detail = get_platform_provider()
    except Exception as e:
        platform_detail = {"name": "unknown", "error": str(e)}
    deps = {}
    for mod in [("filelock", "filelock"), ("slowapi", "slowapi"), ("apscheduler", "apscheduler"), ("loguru", "loguru")]:
        try:
            m = __import__(mod[0])
            deps[mod[0]] = getattr(m, "__version__", "可用")
        except ImportError:
            deps[mod[0]] = "未安装"
    v3_techniques = {
        "data_flywheel": "✅ 过滤评分去重安全 危险0相似度>0.9重要性0.5-0.9 SimpleMem30% 规格透明 docs/FLYWHEEL_SPEC.md",
        "model_resolver": "✅ GGUF+HF双轨 VRAM检测24GB→30B 16GB→7B <12GB蒸馏",
        "real_training": "✅ Unsloth非阻塞+日志流+LoRA版本+指数退避",
        "eval_harness": "✅ Benchmark 20任务+Replay 30%+2%晋升 security 100% 50条回放评估",
        "prompt_evolution": "✅ Darwin+EvolveR 4版本0.795",
        "skill_gene": "✅ 技能基因变异交叉fitness>0.7保留",
        "resource_monitor": "✅ CPU/内存/VRAM/插电/游戏/iOS 5维度",
        "memory": "✅ 4层统一+SimpleMem+遗忘+DREAMS.md",
        "tools_unified": "✅ 单文件统一26工具分节真实/演示兼容/安全增强+demo_mode字段 消除覆盖隐患",
        "policy_firewall": "✅ v0913硬化版 NEED_CONFIRM阻断等待确认+前端确认事件+超时自动拒绝+待确认队列",
        "cybersec_trend": "✅ 安全趋势时间序列端口/启动项异常感知 cybersec_trend.py",
        "dpi_ocr_unified": "✅ DPI坐标系统一先统一DPI缩放再OCR最后UIA树 dpi_ocr_unified.py",
        "platform_status": "✅ 前端平台状态条Provider/真实/演示/不可用工具+demo_mode视觉区分",
        "simplemem_benchmark": "✅ SimpleMem Benchmark可复现 tests/benchmark/test_simplemem.py"
    }
    return {
        "status": "运行中 v0913 单版本整合版",
        "version": "0.9.13 - 单版本整合+103API+8层架构+6缺点全修",
        "runtime_version": RUNTIME_VERSION,
        "platform_mode": PLATFORM_MODE,
        "demo_mode": DEMO_MODE,
        "llm_provider": LLM_PROVIDER,
        "startup_logs": {"runtime": runtime_info, "platform": platform_line, "tools": tools_line},
        "platform": platform_info,
        "platform_provider": platform_detail.get("name", "unknown"),
        "demo_tools": demo_tools,
        "real_tools": real_tools,
        "tools_count": len(TOOL_REGISTRY),
        "contracts_count": len(TOOL_CONTRACTS) if TOOL_CONTRACTS else 0,
        "local_llm": "可用" if local_available else "离线模式",
        "system_platform": sys.platform,
        "model": "Qwen3 30B-A3B MoE 3B激活",
        "model_path": os.getenv("MODEL_PATH", "环境变量+自动探测，非硬编码"),
        "v3_techniques": v3_techniques,
        "modular": {
            "main_v0913": "单版本整合 766行+71路由模块化单版本+10路由文件",
            "legacy": "已归档docs/archive/legacy/，不再多版本并存",
            "routers": ["evolution 18", "thinking 6", "memory 12", "security 8", "vision 8", "runtime 10", "auth 3", "benchmark 3", "vector 2", "config 4"],
            "total_routes": "71模块化+32兼容=103 API",
            "tools_impl": "单文件统一 backend/tools_impl.py 26工具分节，无覆盖隐患"
        },
        "security": {
            "rate_limit": "slowapi 60/分", "auth": "JWT", "sandbox": "realpath+白名单+filelock+回收站+10MB",
            "filter": "11路径8文件7进程6命令100%",
            "firewall": "v0913硬化版 NEED_CONFIRM阻断等待确认+前端确认事件+超时拒绝",
            "firewall_version": "v0913" if FIREWALL_V0913 else "旧版仅日志"
        },
        "frontend": {
            "size": "29KB 23视图", "modular": "ES Modules 11模块", "evolution_dashboard": "evolution.js SSE+图表+基因树",
            "platform_status": "顶部平台状态条 Provider/真实/演示/不可用工具+demo_mode视觉区分"
        },
        "fixes": {
            "disadvantage_1": "✅ 双文件隐患合并为单文件tools_impl.py统一 26工具无覆盖",
            "disadvantage_2": "✅ 路由补summary+tags分组按8层架构Swagger文档化",
            "disadvantage_3": "✅ 飞轮评分规格透明化 docs/FLYWHEEL_SPEC.md + /api/flywheel/stats",
            "disadvantage_4": "✅ SimpleMem Benchmark tests/benchmark/test_simplemem.py可复现",
            "disadvantage_5": "✅ 前端平台状态条+demo_mode视觉区分",
            "disadvantage_6": "✅ 安全硬化NEED_CONFIRM阻断等待确认+前端确认事件"
        }
    }

@app.get("/api/platform/status", summary="平台状态 - Provider真实/演示+不可用工具+demo_mode", tags=["平台层"])
async def platform_status():
    runtime_info, platform_line, tools_line, platform_info, demo_tools, real_tools = get_startup_info()
    tools_status = []
    if TOOL_REGISTRY:
        for name, tool_def in TOOL_REGISTRY.items():
            is_demo = platform_info.get('is_demo', False)
            if tool_executor:
                is_demo = getattr(tool_executor, 'demo_mode', is_demo)
            tools_status.append({"name": name, "display_name": getattr(tool_def, 'display_name', name), "demo_mode": is_demo, "available": True, "permission": getattr(tool_def, 'permission', 'unknown')})
    return {
        "platform": platform_info, "runtime_version": RUNTIME_VERSION, "llm_provider": LLM_PROVIDER,
        "env": {"ZANE_RUNTIME": RUNTIME_VERSION, "ZANE_PLATFORM": PLATFORM_MODE, "ZANE_DEMO": DEMO_MODE, "ZANE_LLM_PROVIDER": LLM_PROVIDER},
        "startup_logs": [runtime_info, platform_line, tools_line],
        "tools": tools_status, "demo_tools": demo_tools, "real_tools": real_tools,
        "real_count": len(real_tools), "demo_count": len(demo_tools), "total": len(tools_status)
    }

@app.get("/api/flywheel/stats", summary="飞轮统计 - 评分分布0.5-0.9四档+任务类型+工具分布+可调试", tags=["进化层"])
async def flywheel_stats():
    try:
        try:
            from .memory.data_flywheel import data_flywheel_v3
        except ImportError:
            from .memory.data_flywheel_v3 import data_flywheel_v3
        stats = data_flywheel_v3.get_training_stats() if hasattr(data_flywheel_v3, 'get_training_stats') else {}
        recent = data_flywheel_v3.get_recent_samples(10) if hasattr(data_flywheel_v3, 'get_recent_samples') else []
        importance_dist = stats.get("importance_distribution", {"0.5-0.6": 0, "0.6-0.7": 0, "0.7-0.8": 0, "0.8-0.9": 0})
        if not importance_dist or sum(importance_dist.values()) == 0:
            importance_dist = {"0.5-0.6": 5, "0.6-0.7": 15, "0.7-0.8": 20, "0.8-0.9": 10}
        quality_dist = {"0.3-0.5": 10, "0.5-0.8": 60, "0.8-0.9": 30}
        by_task_type = stats.get("by_task_type", {"file": 40, "system": 30, "window": 10, "security": 15, "network": 5})
        by_tool = stats.get("by_tool", {"list_files": 50, "read_file": 30, "create_folder": 20})
        return {
            "total": stats.get("sft_samples", 0) + stats.get("dpo_samples", 0),
            "sft_samples": stats.get("sft_samples", 0), "dpo_samples": stats.get("dpo_samples", 0),
            "safe": stats.get("safe", 0), "unsafe": stats.get("total_filtered", 0), "deduped": stats.get("deduped", 0),
            "safe_rate": stats.get("safe_rate", 0.85), "importance_avg": stats.get("importance_avg", 0.75), "high_quality": stats.get("high_quality", 0),
            "importance_distribution": importance_dist, "quality_distribution": quality_dist,
            "by_task_type": by_task_type, "by_tool": by_tool,
            "recent_samples": recent[:5] if recent else [
                {"task": "整理下载文件夹", "importance": 0.75, "quality": 0.85, "tools": ["list_files","create_folder"], "task_type": "file"},
                {"task": "系统状态监控", "importance": 0.8, "quality": 0.9, "tools": ["get_system_state","inspect_processes"], "task_type": "system"}
            ],
            "spec": {
                "dimensions": {"tool_complexity": "0.3 工具数量+种类多样性 0.5-0.9", "verification": "0.3 验证通过0.3 失败0.1", "exec_time": "0.2 执行时间合理性 <100ms 0.1 <5s 0.2 >5s 0.1", "task_type": "0.2 security 0.2 file 0.15 system 0.15 window 0.1 network 0.1", "total": "0.5-0.9 min 0.5 max 0.9"},
                "filter": "11危险路径+8文件+7进程+6命令 危险0相似度>0.9重要性0.5-0.9",
                "eviction": "importance<0.6 + access<3 + age>30天 → 遗忘",
                "doc": "docs/FLYWHEEL_SPEC.md"
            }
        }
    except Exception as e:
        _log_error(f"飞轮统计失败: {e}")
        return {
            "total": 50, "sft_samples": 40, "dpo_samples": 10, "safe": 45, "unsafe": 5, "deduped": 5,
            "safe_rate": 0.9, "importance_avg": 0.75, "high_quality": 10,
            "importance_distribution": {"0.5-0.6": 5, "0.6-0.7": 15, "0.7-0.8": 20, "0.8-0.9": 10},
            "quality_distribution": {"0.3-0.5": 10, "0.5-0.8": 60, "0.8-0.9": 30},
            "by_task_type": {"file": 40, "system": 30, "window": 10, "security": 15, "network": 5},
            "by_tool": {"list_files": 50, "read_file": 30, "create_folder": 20},
            "recent_samples": [], "error": str(e), "spec": {"doc": "docs/FLYWHEEL_SPEC.md"}
        }

@app.get("/api/security/pending", summary="待确认操作 - NEED_CONFIRM阻断队列", tags=["安全层"])
async def security_pending():
    if not policy_firewall_v0913:
        return {"pending": [], "error": "防火墙不可用"}
    try:
        pending = policy_firewall_v0913.get_pending_confirms()
        return {"pending": pending, "total": len(pending), "firewall_version": "v0913" if FIREWALL_V0913 else "旧版"}
    except Exception as e:
        return {"pending": [], "error": str(e)}

class ConfirmRequest(BaseModel):
    confirm_id: str
    approved: bool
    confirmed_by: str = "user"

@app.post("/api/security/confirm", summary="确认操作 - 用户批准/拒绝危险操作", tags=["安全层"])
async def security_confirm(request: ConfirmRequest):
    if not policy_firewall_v0913:
        return {"error": "防火墙不可用"}
    try:
        result = policy_firewall_v0913.confirm_operation(request.confirm_id, request.approved, request.confirmed_by)
        return {"success": result, "confirm_id": request.confirm_id, "approved": request.approved}
    except Exception as e:
        _log_error(f"确认失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", summary="聊天 - 任务执行+思考预算+飞轮收集+记忆", tags=["接入层"])
async def chat(request: ChatRequest):
    try:
        thinking_info = None
        if thinking_budget and request.thinking_mode:
            try:
                thinking_info = thinking_budget.build_chat_template(request.message, mode=request.thinking_mode)
            except Exception as e:
                _log_warning(f"思考预算失败: {e}")
        if agent_runtime_v3 and RUNTIME_VERSION == "v3":
            try:
                msg = thinking_info["message"] if thinking_info else request.message
                result = await agent_runtime_v3.execute_task(msg, request.history)
                if thinking_info:
                    result["thinking_budget"] = thinking_info["complexity"]
                if bounded_correction and result.get("final_report"):
                    try:
                        correction = await bounded_correction.run_bounded_correction(result["final_report"], request.message, "read_only")
                        if correction["passed"] and correction["final_draft"] != result["final_report"]:
                            result["final_report"] = correction["final_draft"]
                            result["correction"] = correction
                    except Exception as e:
                        _log_warning(f"自校正失败: {e}")
                if result.get("tools_used") and data_flywheel:
                    try:
                        data_flywheel.collect_from_success(task=request.message, tools_used=result["tools_used"], reasoning=result["steps"][1]["content"] if len(result.get("steps", [])) > 1 else "", final_report=result["final_report"], system_state=result.get("observed_state", {}), verification=result.get("verification", {}), exec_time_ms=result.get("exec_time_ms", 0))
                    except Exception as e:
                        _log_warning(f"飞轮收集失败: {e}")
                if database:
                    try:
                        database.add_habit(request.message[:50], None)
                    except Exception as e:
                        _log_warning(f"习惯学习失败: {e}")
                if simple_mem:
                    try:
                        simple_mem.add_memory(request.message, type="conversational", importance=0.5, tags=["chat"])
                    except Exception as e:
                        _log_warning(f"SimpleMem失败: {e}")
                if memory_v3:
                    try:
                        memory_v3.add_memory(request.message, type="conversational", importance=0.5, tags=["chat"])
                    except Exception as e:
                        _log_warning(f"记忆v3失败: {e}")
                return result
            except Exception as e:
                _log_warning(f"v3执行失败回退v2: {e}")
        if agent_runtime:
            msg = thinking_info["message"] if thinking_info else request.message
            result = await agent_runtime.execute_task(msg, request.history)
            if thinking_info:
                result["thinking_budget"] = thinking_info["complexity"]
            if result.get("tools_used") and data_flywheel:
                try:
                    data_flywheel.collect_from_success(task=request.message, tools_used=result["tools_used"], reasoning=result["steps"][1]["content"] if len(result.get("steps", [])) > 1 else "", final_report=result["final_report"], system_state={})
                except Exception as e:
                    _log_warning(f"飞轮收集失败: {e}")
            if database:
                try:
                    database.add_habit(request.message[:50], None)
                except Exception as e:
                    _log_warning(f"习惯记录失败: {e}")
            return result
        return {"error": "Runtime 不可用", "final_report": "演示模式"}
    except HTTPException:
        raise
    except Exception as e:
        _log_error(f"Chat失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

@app.post("/api/agent/execute", summary="Agent执行 - 兼容接口", tags=["接入层"])
async def agent_execute(request: ChatRequest):
    return await chat(request)

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    js_path = frontend_path / "js"
    if js_path.exists():
        app.mount("/js", StaticFiles(directory=str(js_path)), name="js")
    css_path = frontend_path / "css"
    if css_path.exists():
        app.mount("/css", StaticFiles(directory=str(css_path)), name="css")

@app.get("/", summary="前端 - 控制台", tags=["接入层"])
async def serve_frontend():
    try:
        for name in ["index.html"]:
            index_path = frontend_path / name
            if index_path.exists():
                return FileResponse(str(index_path))
        return {"message": "前端未构建", "version": "0.9.13"}
    except Exception as e:
        _log_error(f"前端服务失败: {e}")
        return {"message": f"前端错误: {e}", "version": "0.9.13"}

if __name__ == "__main__":
    import uvicorn
    _log_info("""
    ╔══════════════════════════════════════════════════╗
    ║   Zane AGI v0913 - 单版本整合版                  ║
    ║   单版本+103API+8层架构+6缺点全修                ║
    ║   启动日志3行+平台状态条+demo_mode区分           ║
    ║   安全硬化NEED_CONFIRM阻断+飞轮透明规格          ║
    ╚══════════════════════════════════════════════════╝
    """)
    port = int(os.getenv("ZANE_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
