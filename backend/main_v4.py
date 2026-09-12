# -*- coding: utf-8 -*-
"""
Zane AGI v4.0 - A+C全面夯实
- A夯实：filelock+slowapi+SQLite唯一+Canvas+模块化+后端routers拆分
- C扩展：20 Skill+APScheduler凌晨2点+习惯学习默认开启+备份
- 技术诚实，无吹嘘，代码维护现实
"""

import os
import sys
import time
import json
import asyncio
from typing import List, Dict, Any, Optional

if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dataclasses import asdict

# slowapi 限流 - A夯实
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    SLOWAPI_AVAILABLE = True
    print("✅ slowapi 限流可用 - 60/分 商业级")
except ImportError:
    limiter = None
    SLOWAPI_AVAILABLE = False
    print("⚠️ slowapi未安装，使用简易限流")

# 导入旧模块兼容
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
    from .memory.data_flywheel import data_flywheel
    from .learning.evolution_engine import evolution_engine
    from .learning.unsloth_trainer import unsloth_trainer
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
    except Exception as e:
        print(f"补全契约失败: {e}")
    from .task_trace import trace_logger as old_trace_logger
    from .model_registry import model_registry
    from .benchmark.suite import benchmark_suite
except ImportError as e:
    print(f"导入旧模块失败: {e}")
    TOOL_REGISTRY = {}
    policy_firewall = None
    tool_executor = None
    TOOL_FUNCTIONS = {}
    memory_layer = None
    agent_runtime = None
    agent_runtime_v3 = None
    llm_client = None

# 新架构
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
except ImportError as e:
    print(f"新架构导入失败: {e}")
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
    web_search_real = None
    autonomous_optimizer = None
    token_manager = None
    database = None

app = FastAPI(
    title="Zane AGI v4.0 - A+C全面夯实",
    description="SQLite唯一+filelock+slowapi+20Skill+APScheduler+习惯学习+模块化+Canvas图表",
    version="4.0.0"
)

# slowapi中间件
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

# 安全中间件
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if rate_limiter:
        client_ip = request.client.host if request.client else "unknown"
        check = rate_limiter.check(client_ip)
        if not check["allowed"]:
            return JSONResponse(status_code=429, content={"error": check["reason"], "retry_after": check.get("retry_after", 60)})
    if auth_manager and auth_manager.enabled:
        if request.url.path.startswith("/api/tools/call") or request.url.path.startswith("/api/security/wsl/exec"):
            token = request.headers.get("X-Zane-Token", "")
            auth_check = auth_manager.check(token)
            if not auth_check["allowed"]:
                return JSONResponse(status_code=401, content={"error": auth_check["reason"]})
    response = await call_next(request)
    return response

# 引入routers - A夯实后端拆分 + 模型管理
try:
    from .routers import system_router, tokens_router, database_router, autonomous_router, models_router
    app.include_router(system_router.router)
    app.include_router(tokens_router.router)
    app.include_router(database_router.router)
    app.include_router(autonomous_router.router)
    app.include_router(models_router.router)
    print("✅ Routers已挂载：system, tokens, database, autonomous, models - A夯实后端拆分+模型载入")
except Exception as e:
    print(f"Routers挂载失败: {e}")
    import traceback
    traceback.print_exc()

# 数据模型
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = None

class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    auto_confirm: bool = False

class PolicyUpdateRequest(BaseModel):
    tool_name: str
    auto_allow: bool

class SearchRequest(BaseModel):
    query: str
    count: int = 5
    fetch_content: bool = False

@app.get("/api/health")
async def health():
    local_available = False
    if llm_client:
        try:
            local_available = await llm_client.is_local_available()
        except:
            pass
    platform_info = {}
    try:
        if get_platform_provider:
            platform_info = get_platform_provider()
    except:
        platform_info = {"name": "unknown"}
    
    # 检查新依赖
    deps = {}
    try:
        import filelock
        deps["filelock"] = filelock.__version__
    except:
        deps["filelock"] = "未安装"
    try:
        import slowapi
        deps["slowapi"] = slowapi.__version__ if hasattr(slowapi, '__version__') else "可用"
    except:
        deps["slowapi"] = "未安装"
    try:
        import apscheduler
        deps["apscheduler"] = apscheduler.__version__
    except:
        deps["apscheduler"] = "未安装"
    
    return {
        "status": "运行中 v4.0 A+C夯实",
        "version": "4.0.0 - SQLite唯一+20Skill+APScheduler+习惯学习+模块化+Canvas",
        "local_llm": "可用" if local_available else "离线模式",
        "platform": sys.platform,
        "platform_provider": platform_info.get("name", "unknown"),
        "tools_count": len(TOOL_REGISTRY),
        "contracts_count": len(TOOL_CONTRACTS) if 'TOOL_CONTRACTS' in globals() else 0,
        "model": "Qwen3 30B-A3B MoE",
        "evolution": evolution_engine.get_status()["status"] if evolution_engine else "unknown",
        "new_arch": NEW_ARCH_AVAILABLE,
        "dependencies": deps,
        "security": {
            "rate_limit": "slowapi 60/分" if SLOWAPI_AVAILABLE else "简易60/分",
            "auth": "可选 X-Zane-Token + python-jose JWT规划",
            "sandbox": "realpath+白名单+filelock",
            "file_size_limit": "10MB",
            "concurrency": "filelock+WAL+busy_timeout"
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
            "scheduler": "APScheduler 凌晨2点+每30分钟",
            "habits": "默认开启",
            "full_auto": True
        },
        "frontend": {
            "modular": "ES Modules拆分",
            "charts": "Canvas原生",
            "views": 19
        }
    }

@app.post("/api/chat")
async def chat(request: ChatRequest, x_zane_token: str = Header(None)):
    try:
        if 'agent_runtime_v3' in globals() and agent_runtime_v3:
            try:
                result = await agent_runtime_v3.execute_task(request.message, request.history)
                if result.get("tools_used") and data_flywheel:
                    try:
                        data_flywheel.collect_from_success(
                            task=request.message,
                            tools_used=result["tools_used"],
                            reasoning=result["steps"][1]["content"] if len(result.get("steps", [])) > 1 else "",
                            final_report=result["final_report"],
                            system_state=result.get("observed_state", {})
                        )
                    except Exception as e:
                        print(f"数据飞轮失败: {e}")
                # 习惯学习 - C扩展
                try:
                    if database:
                        database.add_habit(request.message[:50], None)
                except:
                    pass
                return result
            except Exception as e:
                print(f"v3失败回退: {e}")
                import traceback
                traceback.print_exc()
        
        if NEW_ARCH_AVAILABLE and intent_parser and state_manager and planner:
            state = state_manager.observe(include_screenshot=False)
            parsed = intent_parser.parse(request.message)
            plan = planner.plan(request.message, parsed, state)
            if agent_runtime:
                result = await agent_runtime.execute_task(request.message, request.history)
                result["parsed_intent"] = {"category": parsed.category, "action": parsed.action, "confidence": parsed.confidence, "entities": parsed.entities, "ambiguous": parsed.ambiguous}
                result["plan"] = {"total_steps": plan.total_steps, "estimated_time": plan.estimated_total_time, "needs_confirm": plan.needs_confirm, "has_destructive": plan.has_destructive}
                result["observed_state"] = {"cpu": state.get("system", {}).get("cpu_percent"), "memory": state.get("system", {}).get("memory_percent"), "windows": len(state.get("windows", []))}
            else:
                result = {"intent": request.message, "parsed_intent": {"category": parsed.category, "action": parsed.action, "confidence": parsed.confidence}, "plan": {"total_steps": plan.total_steps, "needs_confirm": plan.needs_confirm}, "state": state, "final_report": f"已解析意图：{parsed.category}/{parsed.action}，计划 {plan.total_steps} 步", "steps": [], "tools_used": []}
        else:
            if agent_runtime:
                result = await agent_runtime.execute_task(request.message, request.history)
            else:
                result = {"error": "Runtime 不可用", "final_report": "演示模式"}
        
        if result.get("tools_used") and data_flywheel:
            try:
                data_flywheel.collect_from_success(task=request.message, tools_used=result["tools_used"], reasoning=result["steps"][1]["content"] if len(result.get("steps", [])) > 1 else "", final_report=result["final_report"], system_state={})
            except Exception as e:
                print(f"数据飞轮失败: {e}")
        
        # 习惯学习
        try:
            if database:
                database.add_habit(request.message[:50], None)
        except:
            pass
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

@app.post("/api/agent/execute")
async def agent_execute(request: ChatRequest):
    return await chat(request)

# 兼容旧API - 未被routers覆盖的
@app.get("/api/tools")
async def list_tools():
    if not TOOL_REGISTRY:
        return {"total": 0, "by_category": {}, "all": []}
    by_category = list_tools_by_category()
    result = {}
    for cat, tools in by_category.items():
        result[cat] = [{"name": t.name, "display_name": t.display_name, "description": t.description, "permission": t.permission.value, "need_confirmation": t.need_confirmation, "is_real": t.is_real_action, "examples": t.examples, "category": t.category.value} for t in tools]
    return {"total": len(TOOL_REGISTRY), "by_category": result, "all": list(TOOL_REGISTRY.keys())}

@app.post("/api/tools/call")
async def call_tool(request: ToolCallRequest, x_zane_token: str = Header(None)):
    decision = None
    if policy_engine:
        decision = policy_engine.decide(request.tool_name, request.parameters)
        dec_action = decision.get("decision") or decision.get("action", "allow")
        if dec_action == "deny":
            raise HTTPException(status_code=403, detail=f"被策略拒绝: {decision['reason']}")
        if dec_action == "need_confirm" and not request.auto_confirm:
            return {"status": "need_confirm", "reason": decision["reason"], "tool": request.tool_name, "parameters": request.parameters, "preview": decision.get("preview"), "policy": "PolicyEngine", "risk": decision.get("risk", "medium")}
    if policy_firewall:
        policy = policy_firewall.check_permission(request.tool_name, request.parameters)
        if policy.action.value == "deny":
            raise HTTPException(status_code=403, detail=policy.reason)
        if policy.action.value == "need_confirm" and not request.auto_confirm:
            return {"status": "need_confirm", "reason": policy.reason, "tool": request.tool_name, "parameters": request.parameters}
    start = time.time()
    try:
        func = TOOL_FUNCTIONS.get(request.tool_name)
        if not func:
            raise HTTPException(status_code=404, detail=f"工具未实现: {request.tool_name}")
        result = func(**request.parameters)
        exec_time = int((time.time() - start) * 1000)
        if policy_firewall:
            policy_firewall.log_execution(request.tool_name, request.parameters, json.dumps(result, ensure_ascii=False)[:500], True, exec_time)
        if request.tool_name in ["delete_file", "write_file", "create_folder"] and undo_stack:
            undo_stack.push(operation=request.tool_name, params=request.parameters, reverse_params={"operation": f"undo_{request.tool_name}", "original": request.parameters}, description=f"{request.tool_name}: {request.parameters.get('path', '')}")
        verification = None
        if verifier:
            verification = verifier.verify(request.tool_name, request.parameters, result)
        dec_action_final = (decision.get("decision") or decision.get("action")) if decision else None
        return {"status": "success", "tool": request.tool_name, "result": result, "exec_time_ms": exec_time, "policy": dec_action_final or "allow", "verification": verification}
    except Exception as e:
        exec_time = int((time.time() - start) * 1000)
        if policy_firewall:
            policy_firewall.log_execution(request.tool_name, request.parameters, f"错误: {e}", True, exec_time)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/policy")
async def get_policy():
    if policy_engine:
        return {"engine": "PolicyEngine v4.0 + filelock+slowapi", "protected_paths": policy_engine.protected_paths, "critical_processes": policy_engine.critical_processes, "auto_allow": list(policy_engine.auto_allow), "denied": list(policy_engine.denied), "note": "LLM只提议，Policy决定，filelock并发安全"}
    if policy_firewall:
        return {"auto_allow": list(policy_firewall.auto_allow_tools), "denied": list(policy_firewall.denied_tools), "rules": {k.value: v.value for k, v in policy_firewall.confirmation_policy.items()}, "protected_paths": policy_firewall.protected_paths, "audit_logs": policy_firewall.get_audit_logs(30), "undo_history": undo_stack.get_history(10) if undo_stack else []}
    return {"policy": "不可用"}

# 其他API保持兼容
@app.get("/api/memory")
async def get_memory():
    if memory_layer:
        return {"conversations": memory_layer.conversations[-20:] if hasattr(memory_layer, 'conversations') else [], "semantic": memory_layer.semantic_knowledge if hasattr(memory_layer, 'semantic_knowledge') else [], "episodic": memory_layer.episodic if hasattr(memory_layer, 'episodic') else [], "stats": {"conversations": len(memory_layer.conversations) if hasattr(memory_layer, 'conversations') else 0}}
    if memory_manager:
        return {"working": [m.__dict__ for m in memory_manager.working[-10:]], "episodic": [m.__dict__ for m in memory_manager.episodic[-10:]], "semantic": [m.__dict__ for m in memory_manager.semantic[-10:]], "procedural": [m.__dict__ for m in memory_manager.procedural[-10:]], "preference": [m.__dict__ for m in memory_manager.preference[-10:]]}
    return {"conversations": [], "semantic": [], "episodic": []}

@app.get("/api/skills")
async def get_skills():
    if database:
        try:
            skills = database.list_skills()
            return {"skills": skills, "total": len(skills), "source": "SQLite唯一 v4.0"}
        except:
            pass
    if skill_manager:
        return {"skills": skill_manager.list_skills(), "total": len(skill_manager.skills), "source": "SkillManager"}
    if memory_layer:
        return {"skills": memory_layer.skills if hasattr(memory_layer, 'skills') else [], "total": len(memory_layer.skills) if hasattr(memory_layer, 'skills') else 0}
    return {"skills": [], "total": 0}

@app.get("/api/traces")
async def list_traces(limit: int = 20):
    if database:
        try:
            traces = database.list_traces(limit=limit)
            stats = database.get_trace_stats()
            return {"traces": traces, "stats": stats, "total": stats["total"], "source": "SQLite唯一 v4.0 filelock"}
        except:
            pass
    if new_trace_logger:
        return {"traces": new_trace_logger.list_traces(limit=limit), "stats": new_trace_logger.get_stats(), "total": len(new_trace_logger.current_traces), "source": "TraceLogger"}
    return {"traces": [], "stats": {}, "total": 0}

@app.get("/api/contracts")
async def list_contracts():
    if 'TOOL_CONTRACTS' in globals() and TOOL_CONTRACTS:
        return {"total": len(TOOL_CONTRACTS), "by_risk": {k: [{"name": c.name, "display_name": c.display_name, "risk": c.risk_level} for c in v] for k, v in list_contracts_by_risk().items()}, "all": [{"name": c.name, "display_name": c.display_name, "risk": c.risk_level, "side_effect": c.side_effect, "category": c.category, "is_real": c.is_real} for c in TOOL_CONTRACTS.values()]}
    return {"total": 0, "by_risk": {}, "all": []}

@app.get("/api/security/sandbox/check")
async def security_sandbox_check(path: str):
    if file_sandbox:
        return file_sandbox.check_path(path)
    return {"error": "沙盒不可用"}

@app.get("/api/security/scan")
async def security_scan(path: str = None):
    if cybersec_tools:
        return cybersec_tools.scan_vulnerability(scan_path=path)
    return {"error": "不可用"}

@app.get("/api/security/wsl")
async def security_wsl():
    if wsl_provider:
        return wsl_provider.wsl_list()
    return {"available": False}

@app.post("/api/security/wsl/exec")
async def security_wsl_exec(distro: str = "Ubuntu", command: str = "ls -la", workdir: str = "~"):
    if wsl_provider:
        return wsl_provider.wsl_exec(distro=distro, command=command, workdir=workdir)
    return {"error": "不可用"}

@app.get("/api/model-registry")
async def list_model_registry():
    if model_registry:
        return {"models": model_registry.list_models(), "active": asdict(model_registry.get_active_model()) if model_registry.get_active_model() else None}
    return {"models": [], "active": None}

@app.get("/api/benchmark")
async def list_benchmark(category: str = None):
    if benchmark_suite:
        return {"tasks": benchmark_suite.list_tasks(category=category), "stats": benchmark_suite.get_stats()}
    return {"tasks": [], "stats": {}}

@app.post("/api/benchmark/run-all")
async def run_benchmark_all(category: str = None):
    if benchmark_suite and agent_runtime:
        result = await benchmark_suite.run_all(agent_runtime, category=category)
        return result
    return {"error": "不可用"}

@app.post("/api/search/real")
async def search_real(request: SearchRequest):
    if web_search_real:
        try:
            result = await web_search_real.search(request.query, count=request.count)
            return result
        except Exception as e:
            return {"error": str(e), "query": request.query, "results": []}
    if tool_executor:
        return tool_executor.web_search(query=request.query, count=request.count)
    return {"query": request.query, "results": []}

@app.get("/api/search/real")
async def search_real_get(query: str, count: int = 5):
    if web_search_real:
        try:
            result = await web_search_real.search(query, count=count)
            return result
        except Exception as e:
            return {"error": str(e), "query": query, "results": []}
    if tool_executor:
        return tool_executor.web_search(query=query, count=count)
    return {"query": query, "results": []}

@app.post("/api/dreaming/run-all")
async def dreaming_run_all(days: int = 7):
    if not dreaming_system:
        return {"error": "梦境不可用"}
    light = dreaming_system.light_phase(days=days)
    rem = dreaming_system.rem_phase()
    deep = dreaming_system.deep_phase()
    return {"light": light, "rem": rem, "deep": deep, "summary": f"扫描 {light.get('scanned',0)} 条"}

@app.get("/api/dreaming/status")
async def dreaming_status():
    if dreaming_system:
        import os
        candidates_path = os.path.join(dreaming_system.data_dir, ".dreams", "candidates.json")
        has_candidates = os.path.exists(candidates_path)
        return {"threshold": dreaming_system.threshold, "weights": dreaming_system.signal_weights, "has_candidates": has_candidates, "dreams_dir": dreaming_system.dreams_dir}
    return {"error": "不可用"}

@app.get("/api/evolution/status")
async def evolution_status():
    if evolution_engine:
        return evolution_engine.get_status()
    return {"status": "unknown"}

@app.get("/api/evolution/data")
async def evolution_data():
    if not data_flywheel:
        return {"stats": {}, "recent": []}
    stats = data_flywheel.get_training_stats()
    recent = data_flywheel.get_recent_samples(10)
    return {"stats": stats, "recent": recent}

# 前端
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    # 额外挂载js/css
    js_path = os.path.join(frontend_path, "js")
    if os.path.exists(js_path):
        app.mount("/js", StaticFiles(directory=js_path), name="js")
    css_path = os.path.join(frontend_path, "css")
    if os.path.exists(css_path):
        app.mount("/css", StaticFiles(directory=css_path), name="css")

@app.get("/")
async def serve_frontend():
    for name in ["index_v5.html", "index_v4.html", "index.html"]:
        index_path = os.path.join(frontend_path, name)
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return {"message": "前端未构建", "version": "4.0.0"}

# 启动时启动调度器
@app.on_event("startup")
async def startup_event():
    try:
        if autonomous_optimizer and autonomous_optimizer.scheduler:
            autonomous_optimizer.start_scheduler()
            print("✅ 自主优化调度器已启动 - A+C全自动")
    except Exception as e:
        print(f"调度器启动失败: {e}")
    
    # 检查重型依赖
    try:
        import sqlite_vec
        print("✅ sqlite-vec 可用")
    except:
        print("⚠️ sqlite-vec 不可用，关键词回退")
    
    try:
        import rapidocr_onnxruntime
        print("✅ rapidocr_onnxruntime 轻量OCR可用 50MB")
    except:
        try:
            import paddleocr
            print("✅ PaddleOCR 可用 500MB")
        except:
            print("⚠️ OCR未安装，截图无OCR")

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   Zane AGI v4.0 - A+C全面夯实                    ║
    ║   SQLite唯一+filelock+slowapi+20Skill+APScheduler║
    ║   习惯学习默认开启+模块化+Canvas图表              ║
    ║   代码维护现实，AI解释现实                       ║
    ╚══════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)
