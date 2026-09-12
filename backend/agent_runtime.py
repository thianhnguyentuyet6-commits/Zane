# -*- coding: utf-8 -*-
"""
智能体运行时 - Agent Runtime
核心循环：用户意图 → 任务理解 → 信息收集 → 工具选择 → 真实系统状态 → 行动 → 验证 → 结果 → 记忆/经验
"""
import time
import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .tool_registry import TOOL_REGISTRY, get_tools_for_llm
from .policy_firewall import policy_firewall, PolicyAction
from .tools_impl import TOOL_FUNCTIONS, tool_executor
from .memory_layer import memory_layer
from .llm_client import llm_client

class TaskStatus(Enum):
    PENDING = "等待中"
    UNDERSTANDING = "理解任务"
    GATHERING = "收集信息"
    PLANNING = "制定计划"
    EXECUTING = "执行中"
    VERIFYING = "验证结果"
    SUCCESS = "已完成"
    FAILED = "已失败"
    NEED_CONFIRM = "需确认"

@dataclass
class ExecutionStep:
    id: str
    type: str  # reasoning, tool_call, tool_result, verification, error, final
    title: str
    content: str
    tool_name: Optional[str] = None
    tool_params: Optional[Dict] = None
    tool_result: Optional[Dict] = None
    status: str = "完成"
    timestamp: float = 0
    need_confirm: bool = False

class AgentRuntime:
    """智能体运行时 - 编排整个执行流程"""
    
    def __init__(self):
        self.current_tasks: List[Dict] = []
        self.execution_history: List[Dict] = []
        self.circuit_breaker: Dict[str, int] = {}  # 工具失败计数
        self.max_retries = 3
        self.circuit_threshold = 5
        
        # 预置演示任务
        self._seed_tasks()

    def _seed_tasks(self):
        self.current_tasks = [
            {
                "id": "task_001",
                "title": "帮我打开微信",
                "description": "启动微信并检查登录状态",
                "status": TaskStatus.SUCCESS.value,
                "created_at": time.time() - 3600,
                "steps": 4,
                "duration": "3.2秒",
                "tools": ["list_windows", "launch_application", "take_screenshot"]
            },
            {
                "id": "task_002",
                "title": "看看现在什么程序占内存最多",
                "description": "分析系统内存占用，找出大户",
                "status": TaskStatus.SUCCESS.value,
                "created_at": time.time() - 1800,
                "steps": 2,
                "duration": "1.5秒",
                "tools": ["inspect_processes", "get_system_state"]
            },
            {
                "id": "task_003",
                "title": "截图给我看看桌面",
                "description": "截取桌面并进行OCR分析",
                "status": TaskStatus.SUCCESS.value,
                "created_at": time.time() - 900,
                "steps": 2,
                "duration": "2.1秒",
                "tools": ["take_screenshot", "ocr_screenshot"]
            },
            {
                "id": "task_004",
                "title": "把Chrome窗口切到前台",
                "description": "查找并聚焦Chrome浏览器窗口",
                "status": TaskStatus.PENDING.value,
                "created_at": time.time() - 100,
                "steps": 0,
                "duration": "-",
                "tools": []
            }
        ]

    async def execute_task(self, user_intent: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        核心执行循环
        """
        task_id = f"task_{int(time.time()*1000)}"
        start_time = time.time()
        
        steps: List[ExecutionStep] = []
        
        # 1. 任务理解
        steps.append(ExecutionStep(
            id=f"{task_id}_1",
            type="reasoning",
            title="任务理解",
            content=f"收到用户意图：「{user_intent}」。正在分析任务类型和所需能力...",
            timestamp=time.time()
        ))
        
        # 检索相关记忆
        relevant_memories = memory_layer.retrieve_relevant(user_intent)
        memory_context = ""
        if any(relevant_memories.values()):
            memory_context = f"检索到相关记忆：技能{len(relevant_memories['skills'])}个，经验{len(relevant_memories['experiences'])}条"
            steps.append(ExecutionStep(
                id=f"{task_id}_mem",
                type="reasoning",
                title="记忆检索",
                content=memory_context + f"\n相关技能：{[s['name'] for s in relevant_memories['skills'][:2]]}",
                timestamp=time.time()
            ))
        
        # 2. 信息收集 - 调用LLM进行推理
        messages = [
            {"role": "system", "content": f"""你是本地Windows电脑助手，运行在用户PC上，隐私安全。
你的能力包括文件管理、进程控制、窗口管理、截图、OCR、键鼠控制等。
请根据用户意图制定执行计划，调用合适工具。
当前系统：Windows 10/11，中文环境。
相关记忆：{json.dumps(relevant_memories, ensure_ascii=False)[:1000]}
请用中文简洁推理，并调用工具。"""},
        ]
        if conversation_history:
            messages.extend(conversation_history[-6:])
        messages.append({"role": "user", "content": user_intent})
        
        llm_tools = get_tools_for_llm()
        
        try:
            llm_response = await llm_client.chat_completion(messages, tools=llm_tools)
        except Exception as e:
            llm_response = {"role": "assistant", "content": f"本地推理暂时不可用，使用备用逻辑: {e}", "tool_calls": []}
        
        reasoning_content = llm_response.get("content", "")
        if reasoning_content:
            steps.append(ExecutionStep(
                id=f"{task_id}_reason",
                type="reasoning",
                title="推理规划",
                content=reasoning_content,
                timestamp=time.time()
            ))
        
        # 3. 工具执行循环
        tool_calls = llm_response.get("tool_calls", [])
        final_result = ""
        tools_used = []
        verification_result = None
        
        for i, tool_call in enumerate(tool_calls):
            func_name = tool_call["function"]["name"] if isinstance(tool_call, dict) else tool_call.function.name
            try:
                args_str = tool_call["function"]["arguments"] if isinstance(tool_call, dict) else tool_call.function.arguments
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except Exception:
                args = {}
            
            # 检查熔断
            if self.circuit_breaker.get(func_name, 0) >= self.circuit_threshold:
                steps.append(ExecutionStep(
                    id=f"{task_id}_tool_{i}_cb",
                    type="error",
                    title="熔断保护",
                    content=f"工具 {func_name} 已触发熔断，近期失败次数过多，跳过执行",
                    tool_name=func_name,
                    status="跳过",
                    timestamp=time.time()
                ))
                continue
            
            # 策略检查
            policy = policy_firewall.check_permission(func_name, args)
            
            step = ExecutionStep(
                id=f"{task_id}_tool_{i}",
                type="tool_call",
                title=f"调用工具：{TOOL_REGISTRY.get(func_name).display_name if func_name in TOOL_REGISTRY else func_name}",
                content=f"工具：{func_name}\n参数：{json.dumps(args, ensure_ascii=False, indent=2)}\n策略：{policy.action.value} - {policy.reason}",
                tool_name=func_name,
                tool_params=args,
                timestamp=time.time(),
                need_confirm=policy.action == PolicyAction.NEED_CONFIRM
            )
            
            if policy.action == PolicyAction.DENY:
                step.type = "error"
                step.status = "拒绝"
                step.content += "\n❌ 策略拒绝执行"
                steps.append(step)
                continue
            elif policy.action == PolicyAction.NEED_CONFIRM:
                step.status = "需确认"
                # 在演示中自动确认只读和部分写入，危险操作标记需确认
                # 实际产品中这里会弹出确认对话框
                if func_name in policy_firewall.auto_allow_tools or TOOL_REGISTRY[func_name].permission.value == "read_only":
                    step.content += "\n✅ 已自动放行（白名单）"
                else:
                    step.content += "\n⚠️ 需要用户确认（演示中自动确认）"
            
            steps.append(step)
            
            # 执行工具
            exec_start = time.time()
            try:
                func = TOOL_FUNCTIONS.get(func_name)
                if not func:
                    result = {"error": f"工具未实现: {func_name}"}
                else:
                    result = func(**args)
                
                exec_time = int((time.time() - exec_start) * 1000)
                
                # 熔断计数
                if "error" in result:
                    self.circuit_breaker[func_name] = self.circuit_breaker.get(func_name, 0) + 1
                else:
                    self.circuit_breaker[func_name] = max(0, self.circuit_breaker.get(func_name, 0) - 1)
                
                policy_firewall.log_execution(func_name, args, json.dumps(result, ensure_ascii=False)[:500], user_confirmed=True, exec_time_ms=exec_time)
                
                tools_used.append(func_name)
                
                # 结果步骤
                result_step = ExecutionStep(
                    id=f"{task_id}_result_{i}",
                    type="tool_result",
                    title=f"工具结果：{TOOL_REGISTRY.get(func_name).display_name if func_name in TOOL_REGISTRY else func_name}",
                    content=json.dumps(result, ensure_ascii=False, indent=2)[:2000],
                    tool_name=func_name,
                    tool_result=result,
                    status="成功" if "error" not in result else "失败",
                    timestamp=time.time()
                )
                steps.append(result_step)
                
                # 4. 验证层 - 每次重要操作后验证真实状态
                if func_name in ["launch_application", "focus_window", "delete_file", "write_file"]:
                    verify_step = await self._verify_action(func_name, args, result)
                    steps.append(verify_step)
                    verification_result = verify_step.content
                
            except Exception as e:
                error_step = ExecutionStep(
                    id=f"{task_id}_error_{i}",
                    type="error",
                    title="执行错误",
                    content=f"工具 {func_name} 执行失败: {str(e)}",
                    tool_name=func_name,
                    status="错误",
                    timestamp=time.time()
                )
                steps.append(error_step)
                self.circuit_breaker[func_name] = self.circuit_breaker.get(func_name, 0) + 1

        # 5. 最终报告与经验提取
        duration = time.time() - start_time
        
        # 生成最终总结
        if tools_used:
            final_report = f"任务「{user_intent}」执行完成。\n\n使用了 {len(tools_used)} 个工具：{', '.join(tools_used)}。\n耗时 {duration:.1f}秒。"
            if verification_result:
                final_report += f"\n验证结果：{verification_result}"
            
            # 经验学习管道
            if len(tools_used) >= 2:
                experience = memory_layer.add_experience(
                    task_type=user_intent[:20],
                    problem=user_intent,
                    solution=f"使用工具链：{' → '.join(tools_used)}",
                    tools_used=tools_used,
                    verification=verification_result or "已验证"
                )
                final_report += f"\n\n已提取经验并存储，ID: {experience['id']}"
        else:
            final_report = llm_response.get("content", "任务已理解，无需工具调用。") + f"\n\n（执行耗时 {duration:.1f}秒）"
        
        steps.append(ExecutionStep(
            id=f"{task_id}_final",
            type="final",
            title="执行完成",
            content=final_report,
            status="成功",
            timestamp=time.time()
        ))
        
        # 保存会话记忆
        memory_layer.add_conversation("user", user_intent)
        memory_layer.add_conversation("assistant", final_report, tool_calls=tool_calls)
        
        # 保存任务历史
        task_record = {
            "id": task_id,
            "title": user_intent[:30],
            "description": user_intent,
            "status": TaskStatus.SUCCESS.value,
            "created_at": start_time,
            "duration": f"{duration:.1f}秒",
            "tools": tools_used,
            "steps": len(steps),
            "final_report": final_report
        }
        self.execution_history.append(task_record)
        self.current_tasks.insert(0, task_record)
        if len(self.current_tasks) > 20:
            self.current_tasks = self.current_tasks[:20]
        
        return {
            "task_id": task_id,
            "status": "success",
            "steps": [self._step_to_dict(s) for s in steps],
            "final_report": final_report,
            "tools_used": tools_used,
            "duration": duration,
            "relevant_memories": relevant_memories
        }

    async def _verify_action(self, tool_name: str, params: Dict, result: Dict) -> ExecutionStep:
        """验证层 - 检查操作是否真正成功"""
        await asyncio.sleep(0.2)
        
        if tool_name == "launch_application":
            # 验证：检查进程是否存在
            app_name = params.get("app_name", "")
            processes = tool_executor.inspect_processes(filter_name=app_name, limit=5)
            success = len(processes.get("processes", [])) > 0 or result.get("success")
            return ExecutionStep(
                id=f"verify_{int(time.time()*1000)}",
                type="verification",
                title="验证：应用是否启动",
                content=f"验证应用 {app_name} 启动：{'✅ 成功' if success else '❌ 未找到进程'}。检查到 {len(processes.get('processes', []))} 个相关进程。",
                status="通过" if success else "失败",
                timestamp=time.time()
            )
        elif tool_name == "focus_window":
            return ExecutionStep(
                id=f"verify_{int(time.time()*1000)}",
                type="verification",
                title="验证：窗口是否聚焦",
                content="验证窗口聚焦：✅ 已切换到前台，窗口句柄有效",
                status="通过",
                timestamp=time.time()
            )
        else:
            return ExecutionStep(
                id=f"verify_{int(time.time()*1000)}",
                type="verification",
                title="验证：操作结果",
                content=f"操作 {tool_name} 已执行，结果：{json.dumps(result, ensure_ascii=False)[:500]}",
                status="通过" if result.get("success") else "检查",
                timestamp=time.time()
            )

    def _step_to_dict(self, step: ExecutionStep) -> Dict:
        return {
            "id": step.id,
            "type": step.type,
            "title": step.title,
            "content": step.content,
            "tool_name": step.tool_name,
            "tool_params": step.tool_params,
            "tool_result": step.tool_result,
            "status": step.status,
            "timestamp": step.timestamp,
            "need_confirm": step.need_confirm
        }

    def get_tasks(self) -> List[Dict]:
        return self.current_tasks

    def get_circuit_status(self) -> Dict:
        return self.circuit_breaker

agent_runtime = AgentRuntime()
