# -*- coding: utf-8 -*-
"""
本地AI电脑助手 - 后端主服务
FastAPI 提供所有API，支持真实系统操作
"""
import os
import sys
import time
import json
import asyncio
from typing import List, Dict, Any, Optional

# 确保中文编码
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

app = FastAPI(
    title="本地AI电脑助手",
    description="私有、自主的桌面助手，运行在你的PC上",
    version="1.0.0"
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

# ========== 核心API ==========
@app.get("/api/health")
async def health():
    local_available = await llm_client.is_local_available()
    return {
        "status": "运行中",
        "local_llm": "可用" if local_available else "离线模式（演示）",
        "platform": sys.platform,
        "version": "1.0.0",
        "uptime": f"{int(time.time()) % 86400 // 3600}小时",
        "tools_count": len(TOOL_REGISTRY),
        "memories_count": len(memory_layer.skills) + len(memory_layer.experiences)
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """核心对话接口 - 触发智能体执行循环"""
    try:
        result = await agent_runtime.execute_task(request.message, request.history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

@app.post("/api/agent/execute")
async def agent_execute(request: ChatRequest):
    """智能体执行接口"""
    return await chat(request)

@app.get("/api/tools")
async def list_tools():
    """工具注册表"""
    by_category = list_tools_by_category()
    result = {}
    for cat, tools in by_category.items():
        result[cat] = [
            {
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "permission": t.permission.value,
                "need_confirmation": t.need_confirmation,
                "is_real": t.is_real_action,
                "examples": t.examples,
                "category": t.category.value
            }
            for t in tools
        ]
    return {
        "total": len(TOOL_REGISTRY),
        "by_category": result,
        "all": list(TOOL_REGISTRY.keys())
    }

@app.post("/api/tools/call")
async def call_tool(request: ToolCallRequest):
    """直接调用工具（受策略防火墙保护）"""
    # 检查权限
    policy = policy_firewall.check_permission(request.tool_name, request.parameters)
    
    if policy.action.value == "deny":
        raise HTTPException(status_code=403, detail=policy.reason)
    
    if policy.action.value == "need_confirm" and not request.auto_confirm:
        return {
            "status": "need_confirm",
            "reason": policy.reason,
            "tool": request.tool_name,
            "parameters": request.parameters
        }
    
    # 执行
    start = time.time()
    try:
        func = TOOL_FUNCTIONS.get(request.tool_name)
        if not func:
            raise HTTPException(status_code=404, detail=f"工具未实现: {request.tool_name}")
        
        result = func(**request.parameters)
        exec_time = int((time.time() - start) * 1000)
        
        policy_firewall.log_execution(
            request.tool_name,
            request.parameters,
            json.dumps(result, ensure_ascii=False)[:500],
            user_confirmed=True,
            exec_time_ms=exec_time
        )
        
        return {
            "status": "success",
            "tool": request.tool_name,
            "result": result,
            "exec_time_ms": exec_time,
            "policy": policy.action.value
        }
    except Exception as e:
        exec_time = int((time.time() - start) * 1000)
        policy_firewall.log_execution(request.tool_name, request.parameters, f"错误: {e}", True, exec_time)
        raise HTTPException(status_code=500, detail=str(e))

# ========== 系统状态 ==========
@app.get("/api/system/state")
async def system_state():
    """真实系统状态"""
    state = tool_executor.get_system_state()
    processes = tool_executor.inspect_processes(limit=5)
    return {
        **state,
        "top_processes": processes.get("processes", [])[:5]
    }

@app.get("/api/system/processes")
async def system_processes(sort_by: str = "memory", limit: int = 20, filter_name: str = None):
    return tool_executor.inspect_processes(sort_by=sort_by, limit=limit, filter_name=filter_name)

@app.get("/api/system/windows")
async def system_windows():
    return tool_executor.list_windows()

@app.get("/api/system/files")
async def system_files(path: str = "C:\\Users\\User\\Downloads", detail: bool = True):
    return tool_executor.list_files(path=path, detail=detail)

@app.get("/api/system/screenshot")
async def system_screenshot(mode: str = "full"):
    result = tool_executor.take_screenshot(mode=mode)
    # 如果有图片，返回base64（简化）
    return result

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
    return {
        "skills": memory_layer.skills,
        "total": len(memory_layer.skills)
    }

@app.get("/api/experiences")
async def get_experiences():
    return {
        "experiences": memory_layer.experiences,
        "total": len(memory_layer.experiences)
    }

@app.get("/api/tasks")
async def get_tasks():
    return {
        "tasks": agent_runtime.get_tasks(),
        "circuit_breaker": agent_runtime.get_circuit_status(),
        "audit_logs": policy_firewall.get_audit_logs(20)
    }

@app.get("/api/policy")
async def get_policy():
    return {
        "auto_allow": list(policy_firewall.auto_allow_tools),
        "denied": list(policy_firewall.denied_tools),
        "rules": {k.value: v.value for k, v in policy_firewall.confirmation_policy.items()},
        "protected_paths": policy_firewall.protected_paths,
        "audit_logs": policy_firewall.get_audit_logs(30)
    }

@app.post("/api/policy/update")
async def update_policy(req: PolicyUpdateRequest):
    policy_firewall.update_policy(req.tool_name, req.auto_allow)
    return {"success": True, "auto_allow": list(policy_firewall.auto_allow_tools)}

@app.get("/api/settings")
async def get_settings():
    local_available = await llm_client.is_local_available()
    return {
        "local_llm": {
            "api_base": llm_client.config["api_base"],
            "model": llm_client.config["model"],
            "available": local_available,
            "offline_mode": llm_client._offline_mode
        },
        "teacher": {
            "enabled": llm_client.teacher_config["enabled"],
            "model": llm_client.teacher_config["model"]
        },
        "policy": {
            "auto_allow_count": len(policy_firewall.auto_allow_tools),
            "protected_paths": policy_firewall.protected_paths
        },
        "memory": {
            "skills": len(memory_layer.skills),
            "experiences": len(memory_layer.experiences),
            "knowledge": len(memory_layer.semantic_knowledge)
        },
        "version": "1.0.0",
        "platform": sys.platform
    }

# ========== 前端静态文件 ==========
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def serve_frontend():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "前端未构建，请访问 /docs 查看API"}

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════╗
    ║   本地AI电脑助手 - Local AI Computer Agent   ║
    ║   私有 · 自主 · 运行在你的PC上              ║
    ╚══════════════════════════════════════════════╝
    
    启动中...
    - 本地LLM: http://127.0.0.1:8080/v1 (llama.cpp)
    - 后端API: http://127.0.0.1:8000
    - 前端控制台: http://127.0.0.1:8000/
    - API文档: http://127.0.0.1:8000/docs
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)
