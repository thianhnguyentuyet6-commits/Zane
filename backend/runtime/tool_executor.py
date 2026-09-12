# -*- coding: utf-8 -*-
"""
Tool Executor - 工具执行器
通过 PolicyEngine 安全边界，记录 Trace，支持事务
"""
import time
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    tool: str
    params: Dict
    success: bool
    result: Any
    exec_time_ms: int
    policy_decision: str
    pre_state: Optional[Dict] = None
    post_state: Optional[Dict] = None
    can_undo: bool = False
    error: str = ""

class ToolExecutor:
    """工具执行器 - 安全边界+事务+验证"""
    
    def __init__(self):
        self.policy_engine = None
        self.trace_logger = None
        self.undo_stack = None
    
    def set_dependencies(self, policy_engine, trace_logger, undo_stack, tool_functions):
        self.policy_engine = policy_engine
        self.trace_logger = trace_logger
        self.undo_stack = undo_stack
        self.tool_functions = tool_functions
    
    async def execute(self, tool_name: str, params: Dict, task_id: str = "", auto_confirm: bool = True) -> ExecutionResult:
        start = time.time()
        
        # 1. Policy 检查 - 兼容 action/decision
        if self.policy_engine:
            decision = self.policy_engine.decide(tool_name, params)
            dec_action = decision.get("decision") or decision.get("action", "allow")
            if dec_action == "deny":
                return ExecutionResult(
                    tool=tool_name, params=params, success=False,
                    result=None, exec_time_ms=0,
                    policy_decision="deny",
                    error=f"被策略拒绝: {decision['reason']}"
                )
            if dec_action == "need_confirm" and not auto_confirm:
                return ExecutionResult(
                    tool=tool_name, params=params, success=False,
                    result={"need_confirm": True, "preview": decision.get("preview")},
                    exec_time_ms=0,
                    policy_decision="need_confirm",
                    error=f"需确认: {decision['reason']}"
                )
        else:
            decision = {"decision": "allow"}
            dec_action = "allow"
        
        # 2. 记录 pre-state（事务）
        pre_state = self._capture_pre_state(tool_name, params)
        
        # 3. 执行
        try:
            func = self.tool_functions.get(tool_name)
            if not func:
                raise ValueError(f"工具未实现: {tool_name}")
            
            # 支持同步和异步
            if asyncio.iscoroutinefunction(func):
                result = await func(**params)
            else:
                result = func(**params)
            
            exec_time = int((time.time() - start) * 1000)
            
            # 4. 记录 post-state
            post_state = self._capture_post_state(tool_name, params, result)
            
            # 5. 记录 Trace
            if self.trace_logger and task_id:
                dec_action_log = decision.get("decision") or decision.get("action", "allow")
                self.trace_logger.log_tool_call(task_id, tool_name, params, result, exec_time, dec_action_log)
            
            # 6. 加入撤销栈（如果是写操作）
            can_undo = False
            if self.undo_stack and tool_name in ["delete_file", "write_file", "move_file", "create_folder"]:
                reverse = self._generate_reverse(tool_name, params, result)
                if reverse:
                    self.undo_stack.push(
                        operation=tool_name,
                        params=params,
                        reverse_params=reverse,
                        description=f"{tool_name}: {params.get('path', params.get('source', ''))}"
                    )
                    can_undo = True
            
            dec_action_final = decision.get("decision") or decision.get("action", "allow")
            return ExecutionResult(
                tool=tool_name, params=params, success=True,
                result=result, exec_time_ms=exec_time,
                policy_decision=dec_action_final,
                pre_state=pre_state, post_state=post_state,
                can_undo=can_undo
            )
        
        except Exception as e:
            exec_time = int((time.time() - start) * 1000)
            if self.trace_logger and task_id:
                self.trace_logger.log_failure(task_id, tool_name, str(e), {"params": params})
            
            dec_err = decision.get("decision") or decision.get("action", "allow") if 'decision' in locals() else "allow"
            return ExecutionResult(
                tool=tool_name, params=params, success=False,
                result=None, exec_time_ms=exec_time,
                policy_decision=dec_err,
                error=str(e)
            )
    
    def _capture_pre_state(self, tool: str, params: Dict) -> Optional[Dict]:
        """事务 pre-state"""
        try:
            if tool == "delete_file":
                import os
                path = params.get("path", "")
                if os.path.exists(path):
                    return {"exists": True, "size": os.path.getsize(path), "mtime": os.path.getmtime(path)}
            elif tool == "move_file":
                import os
                src = params.get("source", "")
                return {"src_exists": os.path.exists(src)}
        except Exception:
            pass
        return None
    
    def _capture_post_state(self, tool: str, params: Dict, result: Any) -> Optional[Dict]:
        try:
            if tool == "launch_application":
                # 验证：进程存在+窗口出现，非 API success
                return {"api_success": result.get("success"), "pid": result.get("pid"), "verification": "需检查进程存在+窗口"}
        except Exception:
            pass
        return None
    
    def _generate_reverse(self, tool: str, params: Dict, result: Any) -> Optional[Dict]:
        if tool == "delete_file":
            recycle = result.get("recycle") if isinstance(result, dict) else None
            if recycle:
                return {"operation": "restore_file", "recycle_path": recycle, "original": params.get("path")}
        elif tool == "move_file":
            return {"operation": "move_file", "source": params.get("dest"), "dest": params.get("source")}
        elif tool == "write_file":
            return {"operation": "delete_file", "path": params.get("path")}
        return None

# 全局
tool_executor = ToolExecutor()
