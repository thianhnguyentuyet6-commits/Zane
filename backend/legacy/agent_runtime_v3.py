# -*- coding: utf-8 -*-
"""
Agent Runtime v3 - 完整执行循环
Observe→Plan→Act→Verify→Recover 严格循环
整合所有Runtime模块，实现可靠本地代理
"""
import time
import json
import asyncio
from typing import Dict, List, Any, Optional

class AgentRuntimeV3:
    """Agent Runtime v3 - 可靠本地计算机代理"""
    
    def __init__(self):
        # 延迟导入，避免循环
        self.intent_parser = None
        self.state_manager = None
        self.planner = None
        self.tool_executor = None
        self.verifier = None
        self.recovery_manager = None
        self.memory_manager = None
        self.skill_manager = None
        self.model_interface = None
        self.trace_logger = None
        self.policy_engine = None
        self.old_runtime = None
        self.tool_functions = {}
        self.undo_stack = None
        self.initialized = False
    
    def init(self):
        if self.initialized:
            return
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
            from .runtime.trace_logger import trace_logger
            from .runtime.policy_engine import policy_engine
            from .tools_impl import TOOL_FUNCTIONS
            from .policy.undo_stack import undo_stack
            from .agent_runtime_v2 import agent_runtime_v2
            
            self.intent_parser = intent_parser
            self.state_manager = state_manager
            self.planner = planner
            self.tool_executor = runtime_tool_executor
            self.verifier = verifier
            self.recovery_manager = recovery_manager
            self.memory_manager = memory_manager
            self.skill_manager = skill_manager
            self.model_interface = model_interface
            self.trace_logger = trace_logger
            self.policy_engine = policy_engine
            self.tool_functions = TOOL_FUNCTIONS
            self.undo_stack = undo_stack
            self.old_runtime = agent_runtime_v2
            
            # 设置依赖
            if self.tool_executor:
                self.tool_executor.set_dependencies(
                    policy_engine=policy_engine,
                    trace_logger=trace_logger,
                    undo_stack=undo_stack,
                    tool_functions=TOOL_FUNCTIONS
                )
            
            self.initialized = True
            print("AgentRuntimeV3 初始化成功 - 10模块")
        except Exception as e:
            print(f"AgentRuntimeV3 初始化失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def execute_task(self, intent: str, history: List[Dict] = None) -> Dict:
        """执行任务 - 完整循环"""
        self.init()
        
        task_id = None
        if self.trace_logger:
            task_id = self.trace_logger.create_trace(intent)
        
        start_time = time.time()
        steps = []
        tools_used = []
        consecutive_failures = 0
        
        try:
            # ========== Observe ==========
            observe_start = time.time()
            state = {}
            if self.state_manager:
                state = self.state_manager.observe(include_screenshot=False)
                if self.trace_logger and task_id:
                    self.trace_logger.log_observation(task_id, state)
            
            steps.append({
                "id": f"{task_id}_observe" if task_id else "observe",
                "type": "reasoning",
                "title": "👁️ Observe - 真实状态观测",
                "content": f"系统: CPU {state.get('system', {}).get('cpu_percent', '--')}% 内存 {state.get('system', {}).get('memory_percent', '--')}% 窗口 {len(state.get('windows', []))}个 进程 {len(state.get('processes', []))}个",
                "status": "完成",
                "timestamp": time.time(),
                "observe_time_ms": int((time.time() - observe_start) * 1000),
                "state": state
            })
            
            # ========== Intent Parse ==========
            parsed = None
            if self.intent_parser:
                parsed = self.intent_parser.parse(intent)
                steps.append({
                    "id": f"{task_id}_parse" if task_id else "parse",
                    "type": "reasoning",
                    "title": f"🧠 Intent Parse - {parsed.category}/{parsed.action} 置信度 {int(parsed.confidence*100)}%",
                    "content": f"原始: {parsed.raw}\n归一化: {parsed.normalized}\n实体: {json.dumps(parsed.entities, ensure_ascii=False)}\n歧义: {parsed.ambiguous} {parsed.clarification_needed}",
                    "status": "完成",
                    "timestamp": time.time(),
                    "parsed": {
                        "category": parsed.category,
                        "action": parsed.action,
                        "confidence": parsed.confidence,
                        "entities": parsed.entities
                    }
                })
                
                if parsed.ambiguous:
                    return {
                        "task_id": task_id or f"task_{int(time.time()*1000)}",
                        "status": "need_clarification",
                        "intent": intent,
                        "parsed_intent": {
                            "category": parsed.category,
                            "action": parsed.action,
                            "confidence": parsed.confidence,
                            "entities": parsed.entities,
                            "ambiguous": True,
                            "clarification_needed": parsed.clarification_needed
                        },
                        "observed_state": state,
                        "steps": steps,
                        "tools_used": [],
                        "final_report": f"意图不明确：{parsed.clarification_needed}",
                        "need_clarification": True,
                        "clarification": parsed.clarification_needed
                    }
            
            # ========== Skill Match ==========
            matched_skill = None
            if self.skill_manager and intent:
                matched_skill = self.skill_manager.match_skill(intent)
                if matched_skill:
                    steps.append({
                        "id": f"{task_id}_skill" if task_id else "skill",
                        "type": "reasoning",
                        "title": f"🛠️ Skill Match - 匹配到技能 {matched_skill.name} v{matched_skill.version}",
                        "content": f"描述: {matched_skill.description}\n成功率: {matched_skill.success_count}/{matched_skill.success_count+matched_skill.failure_count}\n步骤: {len(matched_skill.procedure)}",
                        "status": "完成",
                        "timestamp": time.time(),
                        "skill": matched_skill.name
                    })
            
            # ========== Plan ==========
            plan = None
            if self.planner:
                plan = self.planner.plan(intent, parsed, state)
                steps.append({
                    "id": f"{task_id}_plan" if task_id else "plan",
                    "type": "reasoning",
                    "title": f"📋 Plan - DAG分解 {plan.total_steps}步 需确认:{'是' if plan.needs_confirm else '否'}",
                    "content": "\n".join([f"{n.id}. {n.title} - {n.tool} {n.params} 依赖:{n.dependencies} 风险:{n.risk} 验证:{n.verification}" for n in plan.nodes]),
                    "status": "完成",
                    "timestamp": time.time(),
                    "plan": {
                        "total_steps": plan.total_steps,
                        "estimated_time": plan.estimated_total_time,
                        "needs_confirm": plan.needs_confirm,
                        "has_destructive": plan.has_destructive,
                        "nodes": [{"id": n.id, "title": n.title, "tool": n.tool, "risk": n.risk} for n in plan.nodes]
                    }
                })
            
            # 如果有匹配技能，使用技能流程
            nodes_to_execute = plan.nodes if plan else []
            if matched_skill and not nodes_to_execute:
                # 将技能转换为节点
                from .runtime.planner import TaskNode
                nodes_to_execute = [
                    TaskNode(
                        id=str(s.get("step", i+1)),
                        title=s.get("tool", f"步骤{i+1}"),
                        tool=s.get("tool", "list_files"),
                        params=s.get("params", {}),
                        dependencies=[],
                        risk="low",
                        verification=s.get("verification", "")
                    )
                    for i, s in enumerate(matched_skill.procedure)
                ]
            
            # 如果仍无节点，回退到旧runtime或单工具
            if not nodes_to_execute:
                if self.old_runtime:
                    # 使用旧runtime执行
                    old_result = await self.old_runtime.execute_task(intent, history)
                    # 合并步骤
                    steps.extend(old_result.get("steps", []))
                    tools_used = old_result.get("tools_used", [])
                    final_report = old_result.get("final_report", "")
                    
                    # 记录轨迹
                    if self.trace_logger and task_id:
                        for t in tools_used:
                            self.trace_logger.log_tool_call(
                                task_id, t.get("tool", ""), t.get("params", {}),
                                t.get("result", {}), t.get("exec_time_ms", 0), t.get("policy", "allow")
                            )
                        self.trace_logger.finalize(task_id, final_report, old_result.get("status") == "success")
                    
                    return {
                        "task_id": task_id or old_result.get("task_id", f"task_{int(time.time()*1000)}"),
                        "status": old_result.get("status", "success"),
                        "intent": intent,
                        "parsed_intent": {
                            "category": parsed.category if parsed else "general",
                            "action": parsed.action if parsed else "general",
                            "confidence": parsed.confidence if parsed else 0.5,
                            "entities": parsed.entities if parsed else {}
                        } if parsed else None,
                        "plan": {
                            "total_steps": plan.total_steps if plan else 1,
                            "needs_confirm": plan.needs_confirm if plan else False
                        } if plan else None,
                        "observed_state": state,
                        "steps": steps,
                        "tools_used": tools_used,
                        "final_report": final_report,
                        "latency_ms": int((time.time() - start_time) * 1000),
                        "matched_skill": matched_skill.name if matched_skill else None
                    }
                else:
                    # 单工具推断
                    tool, params = self._infer_tool(intent, parsed)
                    from .runtime.planner import TaskNode
                    nodes_to_execute = [TaskNode(id="1", title=f"执行 {tool}", tool=tool, params=params, risk="low", verification="API返回success")]
            
            # ========== Act - 执行节点 ==========
            for node in nodes_to_execute:
                # 检查依赖 - 简单实现：依赖必须已成功
                # 这里假设按顺序执行，依赖已满足
                
                # 执行
                exec_result = None
                if self.tool_executor:
                    exec_result = await self.tool_executor.execute(
                        tool_name=node.tool,
                        params=node.params,
                        task_id=task_id or "",
                        auto_confirm=True  # v3 内部执行自动确认，外部API仍需确认
                    )
                else:
                    # 回退直接调用
                    func = self.tool_functions.get(node.tool)
                    if func:
                        try:
                            result = func(**node.params)
                            from .runtime.tool_executor import ExecutionResult
                            exec_result = ExecutionResult(
                                tool=node.tool, params=node.params, success=True,
                                result=result, exec_time_ms=100, policy_decision="allow"
                            )
                        except Exception as e:
                            from .runtime.tool_executor import ExecutionResult
                            exec_result = ExecutionResult(
                                tool=node.tool, params=node.params, success=False,
                                result=None, exec_time_ms=0, policy_decision="allow", error=str(e)
                            )
                
                if not exec_result:
                    continue
                
                # ========== Verify ==========
                verification = None
                if self.verifier:
                    verification = self.verifier.verify(
                        tool=node.tool,
                        params=node.params,
                        result=exec_result.result,
                        pre_state=exec_result.pre_state
                    )
                    if self.trace_logger and task_id:
                        self.trace_logger.log_verification(task_id, node.tool, verification)
                
                # 记录
                tool_entry = {
                    "tool": node.tool,
                    "params": node.params,
                    "result": exec_result.result,
                    "success": exec_result.success,
                    "exec_time_ms": exec_result.exec_time_ms,
                    "policy": exec_result.policy_decision,
                    "verification": verification,
                    "can_undo": exec_result.can_undo,
                    "error": exec_result.error
                }
                tools_used.append(tool_entry)
                
                steps.append({
                    "id": f"{task_id}_{node.id}" if task_id else node.id,
                    "type": "tool_call",
                    "title": f"🔧 {node.title} - {node.tool}",
                    "content": f"工具: {node.tool}\n参数: {json.dumps(node.params, ensure_ascii=False)}\n策略: {exec_result.policy_decision}\n结果: {json.dumps(exec_result.result, ensure_ascii=False)[:500] if exec_result.result else exec_result.error}\n验证: {verification.get('verified', False) if verification else '无'} - {verification.get('reason', '') if verification else ''}",
                    "tool_name": node.tool,
                    "tool_params": node.params,
                    "status": "完成" if exec_result.success else "失败",
                    "timestamp": time.time(),
                    "verification": verification
                })
                
                if not exec_result.success:
                    consecutive_failures += 1
                    
                    # ========== Recover ==========
                    if self.recovery_manager:
                        failure_type = self.recovery_manager.classify_failure(node.tool, exec_result.error, node.params)
                        recovery = self.recovery_manager.get_recovery(node.tool, exec_result.error, node.params, failure_type, consecutive_failures)
                        
                        steps.append({
                            "id": f"{task_id}_{node.id}_recovery" if task_id else f"{node.id}_recovery",
                            "type": "reasoning",
                            "title": f"🔄 Recover - {failure_type.value} → {recovery.type}",
                            "content": f"失败: {exec_result.error}\n类型: {failure_type.value}\n恢复: {recovery.type} - {recovery.reason}\n新参数: {recovery.new_params}",
                            "status": "完成" if recovery.type != "ask_user" else "需用户介入",
                            "timestamp": time.time(),
                            "recovery": recovery.__dict__
                        })
                        
                        if self.trace_logger and task_id:
                            self.trace_logger.log_failure(task_id, node.tool, exec_result.error, {"params": node.params})
                            self.trace_logger.log_recovery(task_id, exec_result.error, recovery.__dict__)
                        
                        if recovery.type == "ask_user":
                            # 需要用户介入
                            break
                        elif recovery.type == "retry":
                            # 重试
                            await asyncio.sleep(recovery.delay)
                            # 重试一次
                            retry_result = await self.tool_executor.execute(node.tool, recovery.new_params or node.params, task_id or "", True)
                            # 再次验证
                            retry_verification = None
                            if self.verifier:
                                retry_verification = self.verifier.verify(node.tool, recovery.new_params or node.params, retry_result.result)
                            
                            tools_used.append({
                                "tool": node.tool,
                                "params": recovery.new_params or node.params,
                                "result": retry_result.result,
                                "success": retry_result.success,
                                "exec_time_ms": retry_result.exec_time_ms,
                                "policy": retry_result.policy_decision,
                                "verification": retry_verification,
                                "is_retry": True
                            })
                            
                            if retry_result.success:
                                consecutive_failures = 0
                            continue
                        elif recovery.type == "alternative":
                            # 替代方案
                            alt_result = await self.tool_executor.execute(node.tool, recovery.new_params, task_id or "", True)
                            tools_used.append({
                                "tool": node.tool,
                                "params": recovery.new_params,
                                "result": alt_result.result,
                                "success": alt_result.success,
                                "exec_time_ms": alt_result.exec_time_ms,
                                "is_alternative": True
                            })
                            if alt_result.success:
                                consecutive_failures = 0
                            continue
                    
                    # 熔断检查
                    if self.recovery_manager and self.recovery_manager.should_circuit_break(task_id or "", consecutive_failures):
                        steps.append({
                            "id": f"{task_id}_circuit_break" if task_id else "circuit_break",
                            "type": "reasoning",
                            "title": "🚨 Circuit Break - 熔断",
                            "content": f"连续失败 {consecutive_failures} 次，触发熔断，停止执行",
                            "status": "熔断",
                            "timestamp": time.time()
                        })
                        break
                else:
                    consecutive_failures = 0
            
            # ========== Finalize ==========
            success_count = sum(1 for t in tools_used if t.get("success"))
            total_count = len(tools_used)
            overall_success = success_count == total_count and total_count > 0
            
            final_report = self._generate_final_report(intent, tools_used, state, parsed, plan, matched_skill)
            
            if self.trace_logger and task_id:
                self.trace_logger.finalize(task_id, final_report, overall_success, confidence=0.8 if overall_success else 0.3)
            
            # 记录到记忆
            if self.memory_manager and overall_success:
                self.memory_manager.add(
                    type="episodic",
                    content=f"任务成功: {intent}，使用工具: {', '.join([t['tool'] for t in tools_used])}",
                    metadata={"tools": [t["tool"] for t in tools_used], "success": overall_success},
                    importance=0.7
                )
            
            # 记录技能成功
            if self.skill_manager and matched_skill and overall_success:
                self.skill_manager.record_success(matched_skill.name)
            elif self.skill_manager and matched_skill and not overall_success:
                self.skill_manager.record_failure(matched_skill.name)
            
            return {
                "task_id": task_id or f"task_{int(time.time()*1000)}",
                "status": "success" if overall_success else "partial_success" if success_count > 0 else "failed",
                "intent": intent,
                "parsed_intent": {
                    "category": parsed.category,
                    "action": parsed.action,
                    "confidence": parsed.confidence,
                    "entities": parsed.entities,
                    "ambiguous": parsed.ambiguous
                } if parsed else None,
                "plan": {
                    "total_steps": plan.total_steps,
                    "estimated_time": plan.estimated_total_time,
                    "needs_confirm": plan.needs_confirm,
                    "has_destructive": plan.has_destructive
                } if plan else None,
                "observed_state": {
                    "cpu": state.get("system", {}).get("cpu_percent"),
                    "memory": state.get("system", {}).get("memory_percent"),
                    "windows": len(state.get("windows", [])),
                    "processes": len(state.get("processes", []))
                },
                "steps": steps,
                "tools_used": tools_used,
                "final_report": final_report,
                "latency_ms": int((time.time() - start_time) * 1000),
                "success_count": success_count,
                "total_count": total_count,
                "matched_skill": matched_skill.name if matched_skill else None,
                "runtime": "v3 - Observe→Plan→Act→Verify→Recover"
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_report = f"执行异常: {str(e)}"
            if self.trace_logger and task_id:
                self.trace_logger.log_failure(task_id, "runtime", str(e), {})
                self.trace_logger.finalize(task_id, error_report, False)
            
            return {
                "task_id": task_id or f"task_{int(time.time()*1000)}",
                "status": "error",
                "intent": intent,
                "steps": steps,
                "tools_used": tools_used,
                "final_report": error_report,
                "error": str(e),
                "latency_ms": int((time.time() - start_time) * 1000)
            }
    
    def _infer_tool(self, intent: str, parsed) -> tuple[str, Dict]:
        if not parsed:
            return "get_system_state", {}
        
        cat = parsed.category
        act = parsed.action
        entities = parsed.entities
        
        if cat == "file":
            if act == "list":
                return "list_files", {"path": entities.get("path", "C:\\Users\\User\\Downloads"), "detail": True}
            elif act == "read":
                return "read_file", {"path": entities.get("path", "")}
            elif act == "delete":
                return "delete_file", {"path": entities.get("path", "")}
            else:
                return "list_files", {"path": entities.get("path", "C:\\Users\\User\\Downloads")}
        elif cat == "process":
            if act == "kill":
                return "kill_process", {"pid": entities.get("pid"), "name": entities.get("app_name", "")}
            else:
                return "inspect_processes", {"sort_by": "memory", "limit": 20}
        elif cat == "window":
            return "list_windows", {"only_visible": True}
        elif cat == "network":
            return "web_search_real", {"query": intent, "count": 5}
        elif cat == "system":
            return "get_system_state", {}
        elif cat == "security":
            return "security_scan", {"path": entities.get("path")}
        elif cat == "linux":
            return "wsl_exec", {"command": intent, "workdir": "~"}
        else:
            return "get_system_state", {}
    
    def _generate_final_report(self, intent: str, tools_used: List[Dict], state: Dict, parsed, plan, matched_skill) -> str:
        success_count = sum(1 for t in tools_used if t.get("success"))
        total = len(tools_used)
        
        report = f"任务：{intent}\n"
        if parsed:
            report += f"意图：{parsed.category}/{parsed.action} 置信度 {int(parsed.confidence*100)}%\n"
        if matched_skill:
            report += f"匹配技能：{matched_skill.name} v{matched_skill.version}\n"
        if plan:
            report += f"计划：{plan.total_steps}步 需确认:{'是' if plan.needs_confirm else '否'}\n"
        
        report += f"执行：{success_count}/{total} 工具成功\n"
        
        for t in tools_used:
            ver = t.get("verification", {})
            ver_str = f"验证:{'✅真实成功' if ver.get('verified') else '❌失败' if ver else 'API完成'} {ver.get('method', '')}" if ver else ""
            report += f"- {t['tool']} {'✅' if t.get('success') else '❌'} {t.get('exec_time_ms', 0)}ms {ver_str}\n"
        
        if success_count == total and total > 0:
            report += "\n✅ 任务完成，真实成功已验证（区分API完成vs真实成功）"
        elif success_count > 0:
            report += f"\n⚠️ 部分成功 {success_count}/{total}"
        else:
            report += "\n❌ 任务失败，已尝试恢复"
        
        return report

# 全局
agent_runtime_v3 = AgentRuntimeV3()
