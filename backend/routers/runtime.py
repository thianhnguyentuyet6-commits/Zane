# -*- coding: utf-8 -*-
"""
运行时 + 工具 + 记忆 + 轨迹 路由
拆分自 main_v6.py
"""
import time
import json
import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

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

def _log_info(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.info(msg)
    else:
        print(msg)

router = APIRouter(prefix="/api", tags=["运行时"])

def get_modules():
    mods = {}
    try:
        from ..tool_registry import TOOL_REGISTRY, list_tools_by_category
        mods['TOOL_REGISTRY'] = TOOL_REGISTRY
        mods['list_tools_by_category'] = list_tools_by_category
    except ImportError:
        mods['TOOL_REGISTRY'] = {}
        mods['list_tools_by_category'] = lambda: {}
    try:
        from ..tools_impl import TOOL_FUNCTIONS
        mods['TOOL_FUNCTIONS'] = TOOL_FUNCTIONS
    except ImportError:
        mods['TOOL_FUNCTIONS'] = {}
    try:
        from ..policy_firewall import policy_firewall
        mods['policy_firewall'] = policy_firewall
    except ImportError:
        mods['policy_firewall'] = None
    try:
        from ..runtime.policy_engine import policy_engine
        mods['policy_engine'] = policy_engine
    except ImportError:
        mods['policy_engine'] = None
    try:
        from ..runtime.verifier import verifier
        mods['verifier'] = verifier
    except ImportError:
        mods['verifier'] = None
    try:
        from ..policy.undo_stack import undo_stack
        mods['undo_stack'] = undo_stack
    except ImportError:
        mods['undo_stack'] = None
    try:
        from ..memory_layer import memory_layer
        mods['memory_layer'] = memory_layer
    except ImportError:
        mods['memory_layer'] = None
    try:
        from ..runtime.memory_manager import memory_manager
        mods['memory_manager'] = memory_manager
    except ImportError:
        mods['memory_manager'] = None
    try:
        from ..runtime.skill_manager import skill_manager
        mods['skill_manager'] = skill_manager
    except ImportError:
        mods['skill_manager'] = None
    try:
        from ..runtime.trace_logger import trace_logger as new_trace_logger
        mods['new_trace_logger'] = new_trace_logger
    except ImportError:
        mods['new_trace_logger'] = None
    try:
        from ..database import database
        mods['database'] = database
    except ImportError:
        mods['database'] = None
    try:
        from ..runtime.intent_parser import intent_parser
        mods['intent_parser'] = intent_parser
    except ImportError:
        mods['intent_parser'] = None
    try:
        from ..runtime.state_manager import state_manager
        mods['state_manager'] = state_manager
    except ImportError:
        mods['state_manager'] = None
    try:
        from ..runtime.planner import planner
        mods['planner'] = planner
    except ImportError:
        mods['planner'] = None
    try:
        from ..platform.base import get_platform_provider
        mods['get_platform_provider'] = get_platform_provider
    except ImportError:
        mods['get_platform_provider'] = None
    return mods

class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}
    auto_confirm: bool = False
    # 兼容前端可能传的额外字段
    args: Dict[str, Any] = {}
    params: Dict[str, Any] = {}
    
    def get_params(self) -> Dict[str, Any]:
        # 合并parameters, args, params，兼容不同前端
        merged = {}
        merged.update(self.args or {})
        merged.update(self.params or {})
        merged.update(self.parameters or {})
        return merged

@router.get("/tools")
async def list_tools():
    mods = get_modules()
    try:
        if not mods['TOOL_REGISTRY']:
            return {"total": 0, "by_category": {}, "all": []}
        by_category = mods['list_tools_by_category']()
        result = {}
        for cat, tools in by_category.items():
            result[cat] = [{"name": t.name, "display_name": t.display_name, "description": t.description, "permission": t.permission.value, "need_confirmation": t.need_confirmation, "is_real": t.is_real_action, "examples": t.examples, "category": t.category.value} for t in tools]
        return {"total": len(mods['TOOL_REGISTRY']), "by_category": result, "all": list(mods['TOOL_REGISTRY'].keys())}
    except Exception as e:
        _log_error(f"工具列表失败: {e}")
        return {"total": 0, "by_category": {}, "all": [], "error": str(e)}

@router.post("/tools/call")
async def call_tool(request: ToolCallRequest, x_zane_token: str = Header(None)):
    mods = get_modules()
    decision = None
    if mods['policy_engine']:
        try:
            params = request.get_params() if hasattr(request, 'get_params') else request.parameters
            decision = mods['policy_engine'].decide(request.tool_name, params)
            dec_action = decision.get("decision") or decision.get("action", "allow")
            if dec_action == "deny":
                raise HTTPException(status_code=403, detail=f"被策略拒绝: {decision['reason']}")
            if dec_action == "need_confirm" and not request.auto_confirm:
                return {"status": "need_confirm", "reason": decision["reason"], "tool": request.tool_name, "parameters": request.parameters, "preview": decision.get("preview"), "policy": "PolicyEngine", "risk": decision.get("risk", "medium")}
        except HTTPException:
            raise
        except Exception as e:
            _log_warning(f"策略引擎决策失败: {e}")

    if mods['policy_firewall']:
        try:
            params = request.get_params() if hasattr(request, 'get_params') else request.parameters
            policy = mods['policy_firewall'].check_permission(request.tool_name, params)
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
        params = request.get_params() if hasattr(request, 'get_params') else request.parameters
        func = mods['TOOL_FUNCTIONS'].get(request.tool_name)
        if not func:
            raise HTTPException(status_code=404, detail=f"工具未实现: {request.tool_name}")
        result = func(**params)
        exec_time = int((time.time() - start) * 1000)
        if mods['policy_firewall']:
            try:
                mods['policy_firewall'].log_execution(request.tool_name, request.parameters, json.dumps(result, ensure_ascii=False)[:500], True, exec_time)
            except Exception as e:
                _log_warning(f"执行日志记录失败: {e}")
        if request.tool_name in ["delete_file", "write_file", "create_folder"] and mods['undo_stack']:
            try:
                mods['undo_stack'].push(operation=request.tool_name, params=request.parameters, reverse_params={"operation": f"undo_{request.tool_name}", "original": request.parameters}, description=f"{request.tool_name}: {request.parameters.get('path', '')}")
            except Exception as e:
                _log_warning(f"撤销栈记录失败: {e}")
        verification = None
        if mods['verifier']:
            try:
                verification = mods['verifier'].verify(request.tool_name, request.parameters, result)
            except Exception as e:
                _log_warning(f"验证失败: {e}")
                verification = {"verified": False, "reason": f"验证异常: {e}"}
        dec_action_final = (decision.get("decision") or decision.get("action")) if decision else None
        return {"status": "success", "tool": request.tool_name, "result": result, "exec_time_ms": exec_time, "policy": dec_action_final or "allow", "verification": verification}
    except HTTPException:
        raise
    except Exception as e:
        exec_time = int((time.time() - start) * 1000)
        if mods['policy_firewall']:
            try:
                mods['policy_firewall'].log_execution(request.tool_name, request.parameters, f"错误: {e}", True, exec_time)
            except Exception as log_e:
                _log_warning(f"错误日志记录失败: {log_e}")
        _log_error(f"工具调用失败 {request.tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory")
async def get_memory():
    mods = get_modules()
    try:
        if mods['memory_layer']:
            return {"conversations": mods['memory_layer'].conversations[-20:] if hasattr(mods['memory_layer'], 'conversations') else [], "semantic": mods['memory_layer'].semantic_knowledge if hasattr(mods['memory_layer'], 'semantic_knowledge') else [], "episodic": mods['memory_layer'].episodic if hasattr(mods['memory_layer'], 'episodic') else []}
        if mods['memory_manager']:
            return {"working": [m.__dict__ for m in mods['memory_manager'].working[-10:]], "episodic": [m.__dict__ for m in mods['memory_manager'].episodic[-10:]], "semantic": [m.__dict__ for m in mods['memory_manager'].semantic[-10:]], "procedural": [m.__dict__ for m in mods['memory_manager'].procedural[-10:]], "preference": [m.__dict__ for m in mods['memory_manager'].preference[-10:]]}
        return {"conversations": [], "semantic": [], "episodic": []}
    except Exception as e:
        _log_error(f"记忆获取失败: {e}")
        return {"conversations": [], "semantic": [], "episodic": [], "error": str(e)}

@router.get("/skills")
async def get_skills():
    mods = get_modules()
    try:
        if mods['database']:
            try:
                skills = mods['database'].list_skills()
                return {"skills": skills, "total": len(skills), "source": "SQLite唯一 v6.0"}
            except Exception as e:
                _log_warning(f"SQLite技能获取失败: {e}")
        if mods['skill_manager']:
            try:
                return {"skills": mods['skill_manager'].list_skills(), "total": len(mods['skill_manager'].skills)}
            except Exception as e:
                _log_warning(f"技能管理器失败: {e}")
        if mods['memory_layer']:
            return {"skills": mods['memory_layer'].skills if hasattr(mods['memory_layer'], 'skills') else [], "total": len(mods['memory_layer'].skills) if hasattr(mods['memory_layer'], 'skills') else 0}
        return {"skills": [], "total": 0}
    except Exception as e:
        _log_error(f"技能获取失败: {e}")
        return {"skills": [], "total": 0, "error": str(e)}

@router.get("/traces")
async def list_traces(limit: int = 20):
    mods = get_modules()
    try:
        if mods['database']:
            try:
                traces = mods['database'].list_traces(limit=limit)
                stats = mods['database'].get_trace_stats()
                return {"traces": traces, "stats": stats, "total": stats["total"], "source": "SQLite唯一 v6.0"}
            except Exception as e:
                _log_warning(f"轨迹SQLite失败: {e}")
        if mods['new_trace_logger']:
            try:
                return {"traces": mods['new_trace_logger'].list_traces(limit=limit), "stats": mods['new_trace_logger'].get_stats(), "total": len(mods['new_trace_logger'].current_traces)}
            except Exception as e:
                _log_warning(f"新轨迹日志失败: {e}")
        return {"traces": [], "stats": {}, "total": 0}
    except Exception as e:
        _log_error(f"轨迹获取失败: {e}")
        return {"traces": [], "stats": {}, "total": 0, "error": str(e)}

@router.get("/runtime/intent/parse")
async def runtime_parse_intent(text: str):
    mods = get_modules()
    try:
        if mods['intent_parser']:
            try:
                parsed = mods['intent_parser'].parse(text)
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

@router.get("/runtime/state/observe")
async def runtime_observe(include_screenshot: bool = False):
    mods = get_modules()
    try:
        if mods['state_manager']:
            try:
                state = mods['state_manager'].observe(include_screenshot=include_screenshot)
                return {**state, "real": True, "note": "v6.0 自主进化引擎v3.0真实状态"}
            except Exception as e:
                _log_error(f"状态观测失败: {e}")
                return {"error": str(e)}
        try:
            if mods['get_platform_provider']:
                provider = mods['get_platform_provider']()
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

@router.post("/runtime/plan")
async def runtime_plan(intent: str):
    mods = get_modules()
    try:
        if mods['planner'] and mods['intent_parser'] and mods['state_manager']:
            try:
                parsed = mods['intent_parser'].parse(intent)
                state = mods['state_manager'].observe()
                plan = mods['planner'].plan(intent, parsed, state)
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
