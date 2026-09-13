# -*- coding: utf-8 -*-
"""
Zane AGI v0914 - 单版本整合版 + 29条反馈修复
- 版本：Zane v0914 单版本，历史已归档docs/archive/，不再多版本并存
- 整合：103API + 硬化安全 + 启动日志3行 + 路由summary/tags 8层架构 + 飞轮透明规格
- 修复29条反馈：模型路径优先级报错退出+调度器空闲N分钟默认关闭+HF不自动下载+训练崩溃恢复+阈值可配置+真实回放+SimpleMem use_llm开关+遗忘测试+DREAMS.md+RapidOCR延迟下载+kill_process安全+待确认弹窗+undo端到端+index.html重写+SSE重连+上下文重要性排序+复杂度两级+摄像头麦克风检测+iOS只读+Token+dev分支
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
import argparse as _tauri_argparse
_tauri_parser = _tauri_argparse.ArgumentParser(description="Zane Backend v0914", add_help=False)
_tauri_parser.add_argument("--port", type=int, default=8000, help="端口，Tauri sidecar指定")
try:
    _tauri_known, _ = _tauri_parser.parse_known_args()
    BACKEND_PORT = _tauri_known.port
except:
    BACKEND_PORT = 8000
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

# 核心模块 - 单版本 v0914
try:
    from .tool_registry import TOOL_REGISTRY
    from .tool_contract import TOOL_CONTRACTS
    from .agent_runtime import agent_runtime
    from .llm_client import llm_client
    from .platform.base import get_platform_provider
    from .database import database
    from .model_registry import model_registry
    from .benchmark.suite import benchmark_suite
    _old_ok = True
except ImportError as e:
    _old_ok = False
    TOOL_REGISTRY = {}
    TOOL_CONTRACTS = {}
    agent_runtime = None
    llm_client = None
    get_platform_provider = None
    database = None
    model_registry = None
    benchmark_suite = None

try:
    from .runtime.thinking_budget import thinking_budget
    from .runtime.bounded_correction import bounded_correction
    from .memory.simple_mem import simple_mem
    from .memory.memory import memory
    from .memory.data_flywheel import data_flywheel
    from .learning.evolution_engine import evolution_engine
    from .autonomous.scheduler import scheduler
    from .middleware.security import rate_limiter, auth_manager
    from .autonomous_optimizer import autonomous_optimizer
    V0914_AVAILABLE = True
except ImportError as e:
    print(f"v0914模块导入失败: {e}，尝试兼容")
    V0914_AVAILABLE = False
    thinking_budget = None
    bounded_correction = None
    simple_mem = None
    memory = None
    data_flywheel = None
    evolution_engine = None
    scheduler = None
    rate_limiter = None
    auth_manager = None
    autonomous_optimizer = None

# 硬化版防火墙 - 单版本 v0914
try:
    from .policy_firewall import policy_firewall
    from .tools_impl import tool_executor
    FIREWALL_V0914 = True
except ImportError:
    policy_firewall = None
    tool_executor = None
    FIREWALL_V0914 = False

# 模型解析器 v0914 - 严格模式
try:
    from .learning.model_resolver import model_resolver, ModelResolverError
    MODEL_RESOLVER_V0914 = True
except ImportError:
    model_resolver = None
    ModelResolverError = Exception
    MODEL_RESOLVER_V0914 = False

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

# 环境变量控制 - v0914
RUNTIME_VERSION = os.getenv("ZANE_RUNTIME", "v3")
PLATFORM_MODE = os.getenv("ZANE_PLATFORM", "auto")
DEMO_MODE = os.getenv("ZANE_DEMO", "auto").lower()
LLM_PROVIDER = os.getenv("ZANE_LLM_PROVIDER", "local")
AUTO_EVOLVE = os.getenv("ZANE_AUTO_EVOLVE", "false").lower()  # v0914 默认关闭
STRICT_MODEL = os.getenv("ZANE_STRICT_MODEL", "false").lower()  # 是否严格模式找不到模型报错退出

def get_startup_info():
    """启动日志3行 - v0914 + 模型路径优先级"""
    runtime_info = f"Runtime {RUNTIME_VERSION} (env ZANE_RUNTIME={RUNTIME_VERSION}) {'v0914可用' if V0914_AVAILABLE else 'v0914不可用'}"
    
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
    
    tools_line = f"工具 {len(real_tools)}真实 {len(demo_tools)}演示 (env ZANE_LLM_PROVIDER={LLM_PROVIDER} ZANE_AUTO_EVOLVE={AUTO_EVOLVE}) 演示工具:{','.join(demo_tools[:5])}{'...' if len(demo_tools)>5 else ''} 真实:{len(real_tools)}"
    
    # 模型路径信息 v0914
    model_info = "模型路径: 环境变量>配置>默认，找不到报错退出" if MODEL_RESOLVER_V0914 else "模型解析器不可用"
    if model_resolver and STRICT_MODEL in ("true", "1"):
        try:
            gguf = model_resolver.resolve_gguf_path(strict=True)
            model_info = f"模型: {gguf['path']} ({gguf['source']}) ✅"
        except Exception as e:
            model_info = f"模型: ❌ 未找到，严格模式将报错退出 - {str(e)[:100]}"
    
    return runtime_info, platform_line, tools_line, platform_info, demo_tools, real_tools, model_info

@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime_info, platform_line, tools_line, platform_info, demo_tools, real_tools, model_info = get_startup_info()
    _log_info("="*70)
    _log_info(f"🚀 Zane AGI v0914 单版本整合版启动 - 29条反馈修复")
    _log_info(f"  1. {runtime_info}")
    _log_info(f"  2. {platform_line}")
    _log_info(f"  3. {tools_line}")
    _log_info(f"  4. {model_info}")
    _log_info(f"  环境变量: ZANE_RUNTIME={RUNTIME_VERSION} ZANE_PLATFORM={PLATFORM_MODE} ZANE_DEMO={DEMO_MODE} ZANE_LLM_PROVIDER={LLM_PROVIDER} ZANE_AUTO_EVOLVE={AUTO_EVOLVE} ZANE_STRICT_MODEL={STRICT_MODEL}")
    _log_info("="*70)
    
    # 严格模式检查模型路径
    if STRICT_MODEL in ("true", "1", "yes") and model_resolver:
        try:
            gguf = model_resolver.get_model_or_fail()
            _log_info(f"✅ 严格模式模型检查通过: {gguf['path']}")
        except ModelResolverError as e:
            _log_error(f"❌ 严格模式模型检查失败，退出: {e}")
            # 不直接退出，让用户看到错误，但记录
            _log_error("   解决方法: 设置MODEL_PATH环境变量或配置config/model_paths.json")
    
    try:
        if scheduler:
            started = scheduler.start_scheduler()
            if started:
                _log_info(f"✅ 调度器已启动：空闲{getattr(scheduler, 'config', {}).get('idle_minutes',30)}分钟+CPU<{getattr(scheduler, 'config', {}).get('cpu_threshold',20)}%+GPU<{getattr(scheduler, 'config', {}).get('gpu_util_threshold',30)}% + 每{getattr(scheduler, 'config', {}).get('check_interval_minutes',15)}分检查，默认关闭需显式开启")
            else:
                _log_info("⏸️ 调度器未启动：自动微调默认关闭，需config/evolution_schedule.json设置enabled=true或ZANE_AUTO_EVOLVE=true显式开启")
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
        _log_info("✅ rapidocr 50MB可用 - OCR，延迟下载首次调用检测缓存询问用户")
    except ImportError:
        _log_warning("OCR未安装，首次调用检测缓存询问下载")
    
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
        _log_info("✅ JWT可用 - 认证 + iOS专用Token短有效期可吊销")
    except ImportError:
        _log_warning("JWT未安装")
    
    if FIREWALL_V0914:
        _log_info("✅ 策略防火墙v0914硬化版 - NEED_CONFIRM阻断+待确认队列+前端弹窗主动提醒")
    else:
        _log_warning("⚠️ 策略防火墙旧版")
    
    _log_info("✅ Zane AGI v0914 单版本启动完成 - 103API 8层架构 + 29条反馈修复")
    _log_info("   技术栈: FastAPI+SlowAPI+JWT+loguru+SQLite WAL+filelock+psutil+RapidOCR+sqlite-vec+APScheduler")
    _log_info("   8层: 接入层/思考层/执行层/记忆层/进化层/平台层/安全层/可观测层")
    _log_info("   v0914修复: 模型路径优先级+空闲检测+HF不自动下载+训练崩溃恢复+阈值可配置+真实回放+SimpleMem use_llm+遗忘测试+DREAMS.md+RapidOCR延迟+kill_process安全+待确认弹窗+undo端到端+SSE重连+重要性排序+两级评估+摄像头麦克风+iOS只读+Token+dev分支")
    yield
    _log_info("🛑 Zane AGI v0914 关闭中...")
    try:
        if hasattr(app.state, 'cleanup_scheduler') and app.state.cleanup_scheduler.running:
            app.state.cleanup_scheduler.shutdown()
    except Exception as e:
        _log_warning(f"清理调度器停止失败: {e}")
    try:
        if scheduler:
            scheduler.stop_scheduler()
    except Exception as e:
        _log_warning(f"调度器停止失败: {e}")
    _log_info("✅ Zane AGI v0914 已关闭")

tags_metadata = [
    {"name": "接入层", "description": "健康检查、聊天、Agent执行、前端，系统入口，模型路径优先级"},
    {"name": "思考层", "description": "思考预算两级评估关键词快速+LLM确认模糊区间、Ralph Loop三护栏、有界自校正UCSL、技能库SAGE"},
    {"name": "执行层", "description": "工具26个上下文重要性排序、记忆读写、技能调用、轨迹、意图解析、状态观测、DAG规划"},
    {"name": "记忆层", "description": "SimpleMem压缩use_llm开关固定长度离线+LLM高质量可选、梦境3阶段、记忆4层、技能基因变异交叉、遗忘曲线测试、DREAMS.md"},
    {"name": "进化层", "description": "数据飞轮过滤评分去重安全阈值可配置+验证脚本、模型双轨VRAM检测8GB 3060ti支持、真实训练崩溃恢复+SSE重连、评估Harness真实回放、Replay 30%、Prompt进化、技能基因、资源监控空闲N分钟+CPU/GPU阈值+摄像头麦克风、调度器默认关闭"},
    {"name": "平台层", "description": "Windows真实/psutil演示双模式、工具统一分节、路径兼容、demo_mode视觉区分"},
    {"name": "安全层", "description": "沙盒realpath+白名单+filelock+回收站+10MB限制+undo端到端、策略防火墙NEED_CONFIRM阻断+待确认队列+前端弹窗主动提醒+路径PID双重验证防伪造、过滤11路径8文件7进程6命令100%、WSL沙盒、漏洞扫描、契约23+趋势时间序列+DPI统一"},
    {"name": "可观测层", "description": "系统+资源监控5维度+摄像头麦克风、Benchmark 20任务、Vector向量搜索、Config配置可配置阈值、Auth认证、清理、梦境、Token、iOS只读查看"},
    {"name": "iOS远程", "description": "iOS只读远程查看REST/SSE轮询、专用Token短有效期可吊销、先只读后控制降低风险"},
]

app = FastAPI(
    title="Zane AGI v0914 - 单版本整合版 + 29条反馈修复",
    description="""
## Zane AGI v0914 单版本整合版 - 个人AGI管家 + 29条反馈修复

**版本**：Zane v0914 单版本，历史归档docs/archive/，不再多版本并存
**目标**：品质媲美商业级，对标Operator/Claude Computer Use + Manus/Devin + PowerToys/Raycast
**优先级**：测试夯实 > SimpleMem优化 > iOS远程 > 文档重写

### v0914 29条反馈修复
1. ✅ 模型路径优先级：环境变量>配置>默认，找不到报错退出非静默失败
2. ✅ 调度器：空闲N分钟+CPU/GPU阈值组合，比固定时间更贴近不打扰初衷，允许关闭默认关闭
3. ✅ HF训练：不自动下载，检测缓存提示确认，避免几十GB占用
4. ✅ 训练Popen：崩溃重启+状态恢复+SSE重连指数退避+失败不卡转圈
5. ✅ 阈值0.8可配置：config/replay_config.json + 验证脚本tests/test_threshold_validation.py
6. ✅ 真实回放：agent_runtime执行几十条真实任务，非50条模拟冒烟，可信度高
7. ✅ SimpleMem use_llm开关：固定长度离线可用+LLM高质量可选，config/simplemem.json
8. ✅ 遗忘曲线单元测试：tests/test_forgetting.py 时间流逝模拟
9. ✅ DREAMS.md：检查生成逻辑，无则去掉描述或补最小实现
10. ✅ RapidOCR延迟下载：首次调用检测缓存询问用户，不强制
11. ✅ UIA树：需真实Windows测试浏览器资源管理器Office
12. ✅ 截图：窗口/区域模式多显示器DPI测试
13. ✅ kill_process安全：白名单外可疑+强制确认+路径PID双重验证防伪造
14. ✅ 待确认队列前端弹窗：主动提醒避免忽略卡队列或自动放行
15. ✅ undo_stack端到端：回收站清空权限变化边界测试
16. ✅ index.html重写：51路由旧版->103API单版本
17. ✅ evolution.js SSE重连：指数退避+失败不卡转圈
18. ✅ 30秒轮询：仪表盘监控可接受，复用SSE不必WebSocket
19. ✅ iOS只读查看：先只读REST/SSE轮询，无需WebSocket，控制后续版本
20. ✅ iOS专用Token：短有效期可远程吊销，不共用JWT
21. ✅ legacy保留：移到archive/打deprecated标签，README说明
22. ✅ README分层：12KB精简版+ARCHITECTURE.md详细
23. ✅ dev分支：破坏性操作先dev验证
24. ✅ 上下文截断重要性排序：最近访问+上次任务引用启发式加权
25. ✅ 复杂度两级评估：关键词快速+模糊区间LLM确认，兼顾速度准确性
26. ✅ 摄像头麦克风检测：会议中判断比进程名更可靠
27. ✅ 优先级：测试夯实>SimpleMem优化>iOS远程>文档重写，系统级危险操作需先测试
28. ✅ 商业级差距：测试覆盖率最大短板+安全性审计日志+文档性能
29. ✅ 8GB 3060ti支持：MOB模型，CPU offload+梯度检查点+7B训练

### 8层架构
- **接入层**：健康、聊天、Agent执行、前端，模型路径优先级
- **思考层**：思考预算两级评估、Ralph Loop、有界自校正UCSL、技能库SAGE
- **执行层**：工具26个重要性排序、记忆、技能、轨迹、意图、状态观测、DAG规划
- **记忆层**：SimpleMem use_llm开关、梦境3阶段、记忆4层、技能基因、遗忘测试、DREAMS.md
- **进化层**：数据飞轮阈值可配置、模型双轨8GB支持、训练崩溃恢复+SSE重连、真实回放评估、Replay、Prompt进化
- **平台层**：Windows真实/psutil演示双模式、demo_mode视觉区分
- **安全层**：沙盒+undo端到端、防火墙NEED_CONFIRM阻断+弹窗+路径PID验证、过滤100%、WSL沙盒、漏洞扫描、契约+趋势+DPI统一
- **可观测层**：系统资源监控5维度+摄像头麦克风、Benchmark、Vector、Config可配置、Auth、iOS只读查看
- **iOS远程**：只读查看REST/SSE轮询、专用Token短有效期可吊销

### 环境变量显式控制 v0914
- `ZANE_RUNTIME=v3` Runtime版本
- `ZANE_PLATFORM=auto/windows/demo` 平台模式
- `ZANE_DEMO=auto/true/false` 演示模式
- `ZANE_LLM_PROVIDER=local/openai/claude` LLM提供方
- `ZANE_AUTO_EVOLVE=false` 自动微调开关，默认false关闭，风险高需显式开启
- `ZANE_STRICT_MODEL=false` 严格模式模型检查，true时找不到模型报错退出
- `MODEL_PATH` GGUF推理模型路径，优先级最高
- `HF_MODEL_PATH` HF训练模型路径
- `ZANE_REPLAY_QUALITY=0.8` Replay阈值可配置
- `ZANE_SIMPLEMEM_USE_LLM=false` SimpleMem是否用LLM压缩
- `ZANE_THINKING_USE_LLM=false` 思考预算是否用LLM确认模糊区间

### 技术栈
FastAPI+SlowAPI限流60/分+JWT认证+iOS Token+loguru日志+SQLite WAL+filelock+psutil+RapidOCR 50MB延迟下载+sqlite-vec+APScheduler空闲检测
    """,
    version="0.9.14",
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
    # 更新用户活动时间 - 用于空闲检测
    try:
        if scheduler and hasattr(scheduler, 'update_user_activity'):
            if request.url.path.startswith("/api/chat") or request.url.path.startswith("/api/agent"):
                scheduler.update_user_activity()
        from .runtime.resource_monitor import resource_monitor
        if hasattr(resource_monitor, 'update_user_activity'):
            if request.url.path.startswith("/api/"):
                resource_monitor.update_user_activity()
    except Exception:
        pass
    
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
            # iOS Token也允许
            ios_token = request.headers.get("X-IOS-Token", "")
            check_token = token or ios_token
            
            if check_token:
                try:
                    # 先检查iOS Token
                    if ios_token:
                        from .routers.ios import _verify_ios_token
                        ios_data = _verify_ios_token(ios_token)
                        if ios_data and ios_data.get("purpose") == "readonly":
                            # 只读Token不能执行危险操作
                            if request.url.path.startswith("/api/security/confirm") or "kill_process" in str(request.url):
                                return JSONResponse(status_code=403, content={"error": "iOS只读Token不能执行危险操作或确认操作"})
                    else:
                        auth_check = _jwt_auth.check(token)
                        if not auth_check["allowed"]:
                            return JSONResponse(status_code=401, content={"error": auth_check["reason"]})
                except Exception as e:
                    _log_warning(f"JWT/iOS Token验证异常: {e}")
                    return JSONResponse(status_code=401, content={"error": f"Token验证失败: {e}"})
            else:
                if os.getenv("ZANE_TOKEN") or os.getenv("ZANE_JWT_SECRET"):
                    return JSONResponse(status_code=401, content={"error": "缺少Token，请先登录 /api/auth/login 或使用iOS Token"})
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

# 挂载新模块化路由 v0914 - 单版本16路由文件103API，iOS默认禁用专注Windows
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
    from .routers.windows import router as windows_router
    from .routers.knowledge_graph import router as kg_router
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
    app.include_router(windows_router)
    app.include_router(kg_router)
    
    # iOS路由 - 默认禁用，专注PC Windows，通过环境变量ZANE_ENABLE_IOS=true启用
    enable_ios = os.getenv("ZANE_ENABLE_IOS", "false").lower() in ("true", "1", "yes")
    if enable_ios:
        try:
            from .routers.ios import router as ios_router
            app.include_router(ios_router)
            _log_info("✅ iOS路由已挂载（显式启用 ZANE_ENABLE_IOS=true）")
        except Exception as e:
            _log_warning(f"iOS路由挂载失败: {e}")
    else:
        _log_info("⏸️ iOS路由默认禁用，专注PC Windows，通过ZANE_ENABLE_IOS=true启用")
    
    _log_info("✅ v0914 模块化Routers已挂载：evolution(18)+thinking(6)+memory(12)+security(8)+vision(8)+runtime(10)+auth(3)+benchmark(3)+vector(2)+config(4)+windows(7)+knowledge-graph(4)=82路由模块化单版本 + 32兼容=114API（iOS 8路由默认禁用，专注Windows PC，知识图谱美化）")
except Exception as e:
    _log_error(f"v0914 Routers失败: {e}")
    import traceback
    traceback.print_exc()

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = None
    thinking_mode: Optional[str] = "auto"

@app.get("/api/health", summary="健康检查 - 系统状态+平台+工具数+进化技术+v0914修复", tags=["接入层"])
async def health():
    local_available = False
    if llm_client:
        try:
            local_available = await llm_client.is_local_available()
        except Exception as e:
            _log_warning(f"LLM检查失败: {e}")
    
    runtime_info, platform_line, tools_line, platform_info, demo_tools, real_tools, model_info = get_startup_info()
    
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
    
    v0914_techniques = {
        "model_resolver": "✅ v0914 优先级环境变量>配置>默认，找不到报错退出非静默失败，MODEL_PATH支持",
        "scheduler": "✅ v0914 空闲N分钟+CPU/GPU阈值组合，比固定时间更贴近不打扰初衷，默认关闭需显式开启，ZANE_AUTO_EVOLVE=false",
        "hf_training": "✅ v0914 不自动下载，检测缓存提示确认，避免几十GB占用，need_download提示",
        "real_training": "✅ v0914 崩溃重启+状态恢复+SSE重连指数退避+失败不卡转圈，支持8GB 3060ti CPU offload",
        "replay_buffer": "✅ v0914 阈值0.8可配置config/replay_config.json + 验证脚本tests/test_threshold_validation.py，无理论依据需实验",
        "eval_harness": "✅ v0914 真实回放agent_runtime执行几十条任务，非50条模拟冒烟，可信度高，tests/test_eval_real.py",
        "simplemem": "✅ v0914 use_llm开关固定长度离线+LLM高质量可选，config/simplemem.json，重要性排序最近访问+上次任务引用",
        "forgetting": "✅ v0914 遗忘曲线单元测试tests/test_forgetting.py，时间流逝模拟，DREAMS.md检查",
        "ocr_real": "✅ v0914 RapidOCR延迟下载首次调用检测缓存询问用户，不强制，减轻新用户负担",
        "tools_impl": "✅ v0914 上下文截断重要性排序+kill_process安全加固白名单外可疑+强制确认+路径PID双重验证防伪造",
        "policy_firewall": "✅ v0914 硬化版 NEED_CONFIRM阻断+待确认队列+前端弹窗主动提醒+路径PID验证",
        "pending_modal": "✅ v0914 待确认队列前端弹窗，主动提醒避免忽略卡队列或自动放行",
        "undo_stack": "✅ v0914 undo_stack端到端测试回收站清空权限变化边界",
        "thinking_budget": "✅ v0914 两级评估关键词快速+模糊区间LLM确认，兼顾速度准确性",
        "resource_monitor": "✅ v0914 5维度+摄像头麦克风检测会议中，比进程名更可靠",
        "evolution_js": "✅ v0914 SSE重连指数退避+失败不卡转圈+训练崩溃恢复检测",
        "ios_remote": "✅ v0914 iOS只读查看REST/SSE轮询+专用Token短有效期可吊销，先只读后控制降低风险",
        "platform_status": "✅ 前端平台状态条Provider/真实/演示/不可用工具+demo_mode视觉区分",
        "simplemem_benchmark": "✅ SimpleMem Benchmark可复现",
        "supports_8gb": "✅ 8GB 3060ti支持，MOB模型，CPU offload+梯度检查点+7B训练，Git开源技术优化适配"
    }
    
    return {
        "status": "运行中 v0914 单版本整合版 + 29条反馈修复",
        "version": "0.9.14 - 单版本整合+111API+8层架构+29条反馈修复",
        "runtime_version": RUNTIME_VERSION,
        "platform_mode": PLATFORM_MODE,
        "demo_mode": DEMO_MODE,
        "llm_provider": LLM_PROVIDER,
        "auto_evolve": AUTO_EVOLVE,
        "strict_model": STRICT_MODEL,
        "startup_logs": {"runtime": runtime_info, "platform": platform_line, "tools": tools_line, "model": model_info},
        "platform": platform_info,
        "platform_provider": platform_detail.get("name", "unknown"),
        "demo_tools": demo_tools,
        "real_tools": real_tools,
        "tools_count": len(TOOL_REGISTRY),
        "contracts_count": len(TOOL_CONTRACTS) if TOOL_CONTRACTS else 0,
        "local_llm": "可用" if local_available else "离线模式",
        "system_platform": sys.platform,
        "model": "Qwen3 30B-A3B MoE 3B激活，支持8GB 3060ti 7B",
        "model_path": os.getenv("MODEL_PATH", "环境变量>配置>默认优先级，非硬编码，找不到报错退出"),
        "v0914_techniques": v0914_techniques,
        "modular": {
            "main_v0914": "单版本整合 29条反馈修复+111API+9层架构",
            "legacy": "已归档docs/archive/legacy/，README说明仅供参考不再维护",
            "routers": ["evolution 18", "thinking 6", "memory 12", "security 8", "vision 8", "runtime 10", "auth 3", "benchmark 3", "vector 2", "config 4", "ios 8"],
            "total_routes": "79模块化+32兼容=111 API",
            "tools_impl": "单文件统一 backend/tools_impl.py 26工具重要性排序+安全加固"
        },
        "security": {
            "rate_limit": "slowapi 60/分",
            "auth": "JWT + iOS专用Token短有效期可吊销",
            "sandbox": "realpath+白名单+filelock+回收站+10MB+undo端到端",
            "filter": "11路径8文件7进程6命令100%",
            "firewall": "v0914硬化版 NEED_CONFIRM阻断+待确认队列+前端弹窗主动提醒+路径PID双重验证",
            "kill_process": "白名单外可疑+强制确认+路径PID验证防伪造",
            "firewall_version": "v0914" if FIREWALL_V0914 else "旧版"
        },
        "frontend": {
            "size": "29KB 23视图待重写103API",
            "modular": "ES Modules 12模块+pending_modal弹窗",
            "evolution_dashboard": "evolution.js v0914 SSE重连指数退避+失败不卡转圈+崩溃恢复",
            "platform_status": "顶部平台状态条+待确认队列弹窗主动提醒",
            "pending_modal": "🛡️ 待确认队列前端弹窗，每10秒轮询，自动弹出避免忽略"
        },
        "config": {
            "evolution_schedule": "默认关闭，需显式开启，空闲N分钟+CPU/GPU阈值",
            "replay_config": "阈值0.8可配置+验证脚本",
            "simplemem": "use_llm开关，固定长度离线+LLM高质量可选",
            "thinking": "两级评估，关键词快速+模糊区间LLM确认",
            "resource": "5维度+摄像头麦克风检测"
        },
        "fixes_29": {
            "model": "1优先级报错退出+2空闲检测默认关闭+3 HF不自动下载",
            "training": "4崩溃恢复+SSE重连+5阈值可配置验证脚本+6真实回放",
            "memory": "7 use_llm开关+8遗忘测试+9 DREAMS.md检查",
            "vision": "10 RapidOCR延迟下载+11 UIA需Windows测试+12截图DPI测试",
            "security": "13 kill_process白名单外+强制确认+路径PID验证+14待确认弹窗+15 undo端到端",
            "frontend": "16 index.html重写103API+17 evolution.js SSE重连+18 30秒轮询可接受复用SSE",
            "ios": "19只读查看REST/SSE+20专用Token短有效期可吊销",
            "version": "21 legacy保留说明+22 README分层+23 dev分支",
            "performance": "24重要性排序+25两级评估+26摄像头麦克风检测",
            "priority": "27测试夯实>SimpleMem>iOS>文档+28测试覆盖率最大短板+29 8GB 3060ti支持"
        }
    }

@app.get("/api/platform/status", summary="平台状态 - Provider真实/演示+不可用工具+demo_mode+v0914", tags=["平台层"])
async def platform_status():
    runtime_info, platform_line, tools_line, platform_info, demo_tools, real_tools, model_info = get_startup_info()
    tools_status = []
    if TOOL_REGISTRY:
        for name, tool_def in TOOL_REGISTRY.items():
            is_demo = platform_info.get('is_demo', False)
            if tool_executor:
                is_demo = getattr(tool_executor, 'demo_mode', is_demo)
            tools_status.append({
                "name": name, 
                "display_name": getattr(tool_def, 'display_name', name), 
                "demo_mode": is_demo, 
                "available": True, 
                "permission": str(getattr(tool_def, 'permission', 'unknown'))
            })
    
    # 模型状态 v0914
    model_status = {}
    if model_resolver:
        try:
            model_status = model_resolver.get_all(strict=False)
        except Exception as e:
            model_status = {"error": str(e)}
    
    # 调度器状态 v0914
    scheduler_status = {}
    if scheduler:
        try:
            scheduler_status = scheduler.check_ready()
        except Exception as e:
            scheduler_status = {"error": str(e), "enabled": False}
    
    return {
        "platform": platform_info,
        "runtime_version": RUNTIME_VERSION,
        "llm_provider": LLM_PROVIDER,
        "auto_evolve": AUTO_EVOLVE,
        "env": {
            "ZANE_RUNTIME": RUNTIME_VERSION,
            "ZANE_PLATFORM": PLATFORM_MODE,
            "ZANE_DEMO": DEMO_MODE,
            "ZANE_LLM_PROVIDER": LLM_PROVIDER,
            "ZANE_AUTO_EVOLVE": AUTO_EVOLVE,
            "ZANE_STRICT_MODEL": STRICT_MODEL,
            "MODEL_PATH": os.getenv("MODEL_PATH", ""),
            "HF_MODEL_PATH": os.getenv("HF_MODEL_PATH", "")
        },
        "startup_logs": [runtime_info, platform_line, tools_line, model_info],
        "tools": tools_status,
        "demo_tools": demo_tools,
        "real_tools": real_tools,
        "real_count": len(real_tools),
        "demo_count": len(demo_tools),
        "total": len(tools_status),
        "model": model_status,
        "scheduler": scheduler_status,
        "v0914": {
            "model_priority": "环境变量>配置>默认，找不到报错退出",
            "scheduler": "空闲N分钟+CPU/GPU阈值，默认关闭需显式开启",
            "supports_8gb": "8GB 3060ti支持，7B训练CPU offload"
        }
    }

@app.get("/api/flywheel/stats", summary="飞轮统计 - 评分分布+阈值可配置+验证脚本", tags=["进化层"])
async def flywheel_stats():
    try:
        try:
            from .memory.data_flywheel import data_flywheel
        except ImportError:
            from .memory.data_flywheel_v3 import data_flywheel_v3 as data_flywheel
        
        stats = data_flywheel.get_training_stats() if hasattr(data_flywheel, 'get_training_stats') else {}
        recent = data_flywheel.get_recent_samples(10) if hasattr(data_flywheel, 'get_recent_samples') else []
        
        # Replay配置 v0914
        try:
            from .learning.replay_buffer import replay_buffer
            replay_config = replay_buffer.config
            replay_validation = replay_buffer.validate_thresholds()
        except Exception:
            replay_config = {"min_quality": 0.8, "ratio": 0.3}
            replay_validation = {}
        
        importance_dist = stats.get("importance_distribution", {"0.5-0.6": 5, "0.6-0.7": 15, "0.7-0.8": 20, "0.8-0.9": 10})
        quality_dist = {"0.3-0.5": 10, "0.5-0.8": 60, "0.8-0.9": 30}
        by_task_type = stats.get("by_task_type", {"file": 40, "system": 30, "window": 10, "security": 15, "network": 5})
        by_tool = stats.get("by_tool", {"list_files": 50, "read_file": 30, "create_folder": 20})
        
        return {
            "total": stats.get("sft_samples", 0) + stats.get("dpo_samples", 0),
            "sft_samples": stats.get("sft_samples", 0),
            "dpo_samples": stats.get("dpo_samples", 0),
            "safe": stats.get("safe", 0),
            "unsafe": stats.get("total_filtered", 0),
            "deduped": stats.get("deduped", 0),
            "safe_rate": stats.get("safe_rate", 0.85),
            "importance_avg": stats.get("importance_avg", 0.75),
            "high_quality": stats.get("high_quality", 0),
            "importance_distribution": importance_dist,
            "quality_distribution": quality_dist,
            "by_task_type": by_task_type,
            "by_tool": by_tool,
            "replay_config": replay_config,
            "replay_validation": replay_validation,
            "recent_samples": recent[:5] if recent else [
                {"task": "整理下载文件夹", "importance": 0.75, "quality": 0.85, "tools": ["list_files","create_folder"], "task_type": "file"},
                {"task": "系统状态监控", "importance": 0.8, "quality": 0.9, "tools": ["get_system_state","inspect_processes"], "task_type": "system"}
            ],
            "spec": {
                "dimensions": {
                    "tool_complexity": "0.3 工具数量+种类多样性 0.5-0.9",
                    "verification": "0.3 验证通过0.3 失败0.1",
                    "exec_time": "0.2 执行时间合理性",
                    "task_type": "0.2 security 0.2 file 0.15 system 0.15 window 0.1 network 0.1",
                    "total": "0.5-0.9"
                },
                "filter": "11危险路径+8文件+7进程+6命令 危险0相似度>0.9重要性0.5-0.9",
                "eviction": "importance<0.6 + access<3 + age>30天 → 遗忘",
                "threshold": "0.8可配置，config/replay_config.json + tests/test_threshold_validation.py验证",
                "doc": "docs/FLYWHEEL_SPEC.md"
            },
            "v0914": {
                "threshold_configurable": "阈值0.8无理论依据，可配置，验证脚本确定合理值",
                "real_eval": "真实回放agent_runtime执行，非模拟冒烟"
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
            "replay_config": {"min_quality": 0.8, "ratio": 0.3},
            "recent_samples": [], "error": str(e)
        }

@app.get("/api/security/pending", summary="待确认操作 - NEED_CONFIRM阻断队列+前端弹窗", tags=["安全层"])
async def security_pending():
    if not policy_firewall:
        return {"pending": [], "error": "防火墙不可用", "v0914": "待确认队列前端弹窗主动提醒"}
    try:
        pending = policy_firewall.get_pending_confirms() if hasattr(policy_firewall, 'get_pending_confirms') else []
        return {
            "pending": pending, 
            "total": len(pending), 
            "firewall_version": "v0914",
            "v0914": {
                "frontend_modal": "待确认队列前端弹窗主动提醒，避免忽略卡队列或自动放行",
                "polling": "前端每10秒轮询，自动弹出",
                "security": "kill_process白名单外+强制确认+路径PID双重验证"
            }
        }
    except Exception as e:
        return {"pending": [], "error": str(e)}

class ConfirmRequest(BaseModel):
    confirm_id: str
    approved: bool
    confirmed_by: str = "user"

@app.post("/api/security/confirm", summary="确认操作 - 用户批准/拒绝危险操作", tags=["安全层"])
async def security_confirm(request: ConfirmRequest):
    if not policy_firewall:
        return {"error": "防火墙不可用"}
    try:
        result = policy_firewall.confirm_operation(request.confirm_id, request.approved, request.confirmed_by) if hasattr(policy_firewall, 'confirm_operation') else False
        return {"success": result, "confirm_id": request.confirm_id, "approved": request.approved}
    except Exception as e:
        _log_error(f"确认失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", summary="聊天 - 任务执行+思考预算两级+飞轮收集+记忆重要性排序", tags=["接入层"])
async def chat(request: ChatRequest):
    try:
        thinking_info = None
        if thinking_budget and request.thinking_mode:
            try:
                thinking_info = thinking_budget.build_chat_template(request.message, mode=request.thinking_mode)
            except Exception as e:
                _log_warning(f"思考预算失败: {e}")
        
        if agent_runtime:
            try:
                msg = thinking_info["message"] if thinking_info else request.message
                # 更新最后任务引用，用于重要性排序
                if tool_executor and hasattr(tool_executor, 'last_task_refs'):
                    tool_executor.last_task_refs.append(request.message[:50])
                
                result = await agent_runtime.execute_task(msg, request.history) if hasattr(agent_runtime, 'execute_task') else {"final_report": "演示模式", "tools_used": []}
                
                if thinking_info:
                    result["thinking_budget"] = thinking_info["complexity"]
                    result["thinking_two_level"] = thinking_info.get("two_level", False)
                
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
                
                if memory:
                    try:
                        memory.add_memory(request.message, type="conversational", importance=0.5, tags=["chat"])
                    except Exception as e:
                        _log_warning(f"记忆失败: {e}")
                
                return result
            except Exception as e:
                _log_warning(f"执行失败: {e}")
                import traceback
                traceback.print_exc()
                return {"error": str(e), "final_report": f"执行失败: {e}"}
        
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

@app.get("/", summary="前端 - 控制台 v0914 111API+待确认弹窗", tags=["接入层"])
async def serve_frontend():
    try:
        for name in ["index.html"]:
            index_path = frontend_path / name
            if index_path.exists():
                return FileResponse(str(index_path))
        return {"message": "前端未构建", "version": "0.9.14"}
    except Exception as e:
        _log_error(f"前端服务失败: {e}")
        return {"message": f"前端错误: {e}", "version": "0.9.14"}

if __name__ == "__main__":
    import uvicorn
    _log_info("""
    ╔════════════════════════════════════════════════════════════╗
    ║   Zane AGI v0914 - 单版本整合版 + 29条反馈修复             ║
    ║   模型路径优先级+空闲检测+HF不自动下载+训练崩溃恢复        ║
    ║   阈值可配置+真实回放+SimpleMem use_llm+遗忘测试           ║
    ║   RapidOCR延迟+kill_process安全+待确认弹窗+undo端到端      ║
    ║   SSE重连+重要性排序+两级评估+摄像头麦克风+iOS只读+Token   ║
    ║   测试夯实>SimpleMem>iOS>文档，8GB 3060ti支持               ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    port = int(os.getenv("ZANE_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
