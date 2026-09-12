# -*- coding: utf-8 -*-
"""
本地AI电脑助手 - 后端主服务 v2.0
商业级 + 自我进化 + Windows深度控制 + Qwen3-30B-A3B
"""
import os
import sys
import time
import json
import asyncio
from typing import List, Dict, Any, Optional

if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 导入本地模块
from .tool_registry import TOOL_REGISTRY, list_tools_by_category, get_tools_for_llm
from .policy_firewall import policy_firewall
from .tools_impl import tool_executor, TOOL_FUNCTIONS
from .memory_layer import memory_layer
from .agent_runtime import agent_runtime
from .llm_client import llm_client

# 新架构
from .platform.base import get_platform_provider
from .llm.model_manager import model_manager
from .memory.data_flywheel import data_flywheel
from .learning.evolution_engine import evolution_engine
from .learning.unsloth_trainer import unsloth_trainer
from .policy.undo_stack import undo_stack

app = FastAPI(
    title="本地AI电脑助手 - Zane AGI",
    description="私有、自主、自我进化的桌面AGI管家 - Qwen3-30B-A3B",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 数据模型 ==========
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = None

class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    auto_confirm: bool = True

class PolicyUpdateRequest(BaseModel):
    tool_name: str
    auto_allow: bool

# ========== 核心API v2 ==========
@app.get("/api/health")
async def health():
    local_available = await llm_client.is_local_available()
    platform_info = get_platform_provider()
    return {
        "status": "运行中",
        "version": "2.0.0 - Zane AGI",
        "local_llm": "可用" if local_available else "离线模式（演示）",
        "platform": sys.platform,
        "platform_provider": platform_info["name"],
        "uptime": f"{int(time.time()) % 86400 // 3600}小时",
        "tools_count": len(TOOL_REGISTRY),
        "memories_count": len(memory_layer.skills) + len(memory_layer.experiences),
        "model": "Qwen3 30B-A3B MoE - D:\\llama.cpp\\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf",
        "evolution": evolution_engine.get_status()["status"]
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        result = await agent_runtime.execute_task(request.message, request.history)
        
        # 自动收集训练数据（数据飞轮）
        if result.get("tools_used"):
            try:
                data_flywheel.collect_from_success(
                    task=request.message,
                    tools_used=result["tools_used"],
                    reasoning=result["steps"][1]["content"] if len(result.get("steps", [])) > 1 else "",
                    final_report=result["final_report"],
                    system_state={}
                )
            except Exception as e:
                print(f"数据飞轮收集失败: {e}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

@app.post("/api/agent/execute")
async def agent_execute(request: ChatRequest):
    return await chat(request)

# ========== 真实系统状态 - Windows深度控制 ==========
@app.get("/api/system/state")
async def system_state():
    """真实系统状态 - WMI + 真实数据"""
    try:
        provider = get_platform_provider()
        system_provider = provider["system"]
        
        cpu = system_provider.get_cpu_info()
        memory = system_provider.get_memory_info()
        disks = system_provider.get_disk_info()
        processes = system_provider.get_processes(limit=5)
        startup = system_provider.get_startup_items()
        
        # 兼容旧接口
        legacy_state = tool_executor.get_system_state()
        
        return {
            "cpu": cpu,
            "memory": memory,
            "disks": disks,
            "top_processes": processes.get("processes", [])[:5],
            "startup_items": startup[:10],
            "platform": platform_info(),
            "real": cpu.get("real", False),
            "legacy": legacy_state,
            "note": "v2.0 真实WMI数据，Windows上 100% 准确"
        }
    except Exception as e:
        # Fallback
        state = tool_executor.get_system_state()
        processes = tool_executor.inspect_processes(limit=5)
        return {**state, "top_processes": processes.get("processes", [])[:5], "error": str(e)}

def platform_info():
    import platform
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }

@app.get("/api/system/processes")
async def system_processes(sort_by: str = "memory", limit: int = 20, filter_name: str = None):
    try:
        provider = get_platform_provider()
        return provider["system"].get_processes(sort_by=sort_by, limit=limit)
    except:
        return tool_executor.inspect_processes(sort_by=sort_by, limit=limit, filter_name=filter_name)

@app.get("/api/system/windows")
async def system_windows():
    try:
        provider = get_platform_provider()
        windows = provider["window"].enum_windows()
        return {"windows": windows, "total": len(windows), "real": windows[0].get("real", False) if windows else False}
    except Exception as e:
        return tool_executor.list_windows()

@app.get("/api/system/files")
async def system_files(path: str = "C:\\Users\\User\\Downloads", detail: bool = True):
    return tool_executor.list_files(path=path, detail=detail)

@app.get("/api/system/screenshot")
async def system_screenshot(mode: str = "full"):
    result = tool_executor.take_screenshot(mode=mode)
    return result

# ========== 模型管理 - Qwen3-30B-A3B ==========
@app.get("/api/models")
async def list_models():
    models = model_manager.scan_models()
    status = model_manager.get_server_status()
    versions = model_manager.get_model_versions()
    return {
        "models": [{"id": m.id, "name": m.name, "path": m.path, "size_gb": m.size_gb, "quantization": m.quantization, "parameters": m.parameters, "type": m.type, "is_active": m.is_active, "performance": m.performance} for m in models],
        "server": status,
        "versions": versions,
        "current": "D:\\llama.cpp\\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf"
    }

@app.post("/api/models/switch")
async def switch_model(model_id: str):
    return model_manager.switch_model(model_id)

@app.get("/api/models/status")
async def model_status():
    return model_manager.get_server_status()

# ========== 自我进化 - 核心创新 ==========
@app.get("/api/evolution/status")
async def evolution_status():
    return evolution_engine.get_status()

@app.post("/api/evolution/start")
async def evolution_start(manual: bool = True):
    result = await evolution_engine.start_evolution(manual=manual)
    return result

@app.post("/api/evolution/dreaming")
async def evolution_dreaming():
    result = await evolution_engine.start_dreaming()
    return result

@app.get("/api/evolution/data")
async def evolution_data():
    stats = data_flywheel.get_training_stats()
    recent = data_flywheel.get_recent_samples(10)
    return {
        "stats": stats,
        "recent": recent,
        "unsloth": unsloth_trainer.get_install_guide()
    }

@app.get("/api/evolution/training-script")
async def evolution_training_script():
    stats = data_flywheel.get_training_stats()
    script = unsloth_trainer.generate_training_script(
        sft_file=data_flywheel.sft_path,
        output_dir=os.path.join(os.path.dirname(__file__), "..", "models", "versions", f"lora_{int(time.time())}"),
        config={
            "model_path": evolution_engine.config["model_path"],
            "samples": stats["sft_samples"],
            "lora_rank": evolution_engine.config["lora_rank"],
            "lora_alpha": 64,
            "learning_rate": evolution_engine.config["learning_rate"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    return {"script": script, "path": "scripts/train_lora.py"}

# ========== 记忆与技能 ==========
@app.get("/api/memory")
async def get_memory():
    return {
        "conversations": memory_layer.conversations[-20:],
        "semantic": memory_layer.semantic_knowledge,
        "episodic": memory_layer.episodic,
        "stats": {
            "conversations": len(memory_layer.conversations),
            "knowledge": len(memory_layer.semantic_knowledge),
            "episodic": len(memory_layer.episodic)
        }
    }

@app.get("/api/skills")
async def get_skills():
    return {"skills": memory_layer.skills, "total": len(memory_layer.skills)}

@app.get("/api/experiences")
async def get_experiences():
    return {"experiences": memory_layer.experiences, "total": len(memory_layer.experiences)}

@app.get("/api/tasks")
async def get_tasks():
    return {
        "tasks": agent_runtime.get_tasks(),
        "circuit_breaker": agent_runtime.get_circuit_status(),
        "audit_logs": policy_firewall.get_audit_logs(20),
        "undo_stack": undo_stack.get_history(10)
    }

@app.post("/api/tasks/undo")
async def undo_task():
    result = undo_stack.undo()
    if not result:
        raise HTTPException(status_code=404, detail="无可撤销操作")
    return result

@app.post("/api/tasks/redo")
async def redo_task():
    result = undo_stack.redo()
    if not result:
        raise HTTPException(status_code=404, detail="无可重做操作")
    return result

# ========== 工具 ==========
@app.get("/api/tools")
async def list_tools():
    by_category = list_tools_by_category()
    result = {}
    for cat, tools in by_category.items():
        result[cat] = [{"name": t.name, "display_name": t.display_name, "description": t.description, "permission": t.permission.value, "need_confirmation": t.need_confirmation, "is_real": t.is_real_action, "examples": t.examples, "category": t.category.value} for t in tools]
    return {"total": len(TOOL_REGISTRY), "by_category": result, "all": list(TOOL_REGISTRY.keys())}

@app.post("/api/tools/call")
async def call_tool(request: ToolCallRequest):
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
        policy_firewall.log_execution(request.tool_name, request.parameters, json.dumps(result, ensure_ascii=False)[:500], True, exec_time)
        
        # 记录到撤销栈（如果是写操作）
        if request.tool_name in ["delete_file", "write_file", "create_folder"]:
            undo_stack.push(
                operation=request.tool_name,
                params=request.parameters,
                reverse_params={"operation": f"undo_{request.tool_name}", "original": request.parameters},
                description=f"{request.tool_name}: {request.parameters.get('path', '')}"
            )
        
        return {"status": "success", "tool": request.tool_name, "result": result, "exec_time_ms": exec_time, "policy": policy.action.value}
    except Exception as e:
        exec_time = int((time.time() - start) * 1000)
        policy_firewall.log_execution(request.tool_name, request.parameters, f"错误: {e}", True, exec_time)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/policy")
async def get_policy():
    return {
        "auto_allow": list(policy_firewall.auto_allow_tools),
        "denied": list(policy_firewall.denied_tools),
        "rules": {k.value: v.value for k, v in policy_firewall.confirmation_policy.items()},
        "protected_paths": policy_firewall.protected_paths,
        "audit_logs": policy_firewall.get_audit_logs(30),
        "undo_history": undo_stack.get_history(10)
    }

@app.post("/api/policy/update")
async def update_policy(req: PolicyUpdateRequest):
    policy_firewall.update_policy(req.tool_name, req.auto_allow)
    return {"success": True, "auto_allow": list(policy_firewall.auto_allow_tools)}

@app.get("/api/settings")
async def get_settings():
    local_available = await llm_client.is_local_available()
    platform_provider = get_platform_provider()
    return {
        "local_llm": {"api_base": llm_client.config["api_base"], "model": llm_client.config["model"], "available": local_available, "offline_mode": llm_client._offline_mode},
        "model_manager": model_manager.get_server_status(),
        "evolution": evolution_engine.get_status(),
        "platform": {"name": platform_provider["name"], "real": sys.platform == "Windows"},
        "policy": {"auto_allow_count": len(policy_firewall.auto_allow_tools), "protected_paths": policy_firewall.protected_paths},
        "memory": {"skills": len(memory_layer.skills), "experiences": len(memory_layer.experiences), "knowledge": len(memory_layer.semantic_knowledge)},
        "version": "2.0.0 - Zane AGI",
        "model_path": "D:\\llama.cpp\\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf"
    }

# ========== 前端 ==========
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def serve_frontend():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "前端未构建，请访问 /docs"}

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   Zane AGI - 个人AGI管家 v2.0                    ║
    ║   Qwen3-30B-A3B + 自我进化 + Windows深度控制     ║
    ║   私有 · 自主 · 会进化的模型                     ║
    ╚══════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8001)
