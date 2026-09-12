# -*- coding: utf-8 -*-
"""
统一 Task Trace - 结构化轨迹
每个任务生成结构化轨迹，包含所有信息，成为调试、记忆、技能、评估、训练数据的基础
"""
import time
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

@dataclass
class TaskTrace:
    task_id: str
    user_request: str
    observations: List[Dict]  # 真实状态观测
    model_decision: Dict  # 模型决策
    selected_tools: List[str]
    tool_inputs: List[Dict]
    tool_outputs: List[Dict]
    state_changes: List[Dict]
    verification_results: List[Dict]
    failures: List[Dict]
    recovery_attempts: List[Dict]
    final_outcome: str
    latency: float
    token_usage: Dict
    confidence: float
    timestamp: float
    version: str = "2.5"

class TraceLogger:
    """轨迹日志 - 统一格式"""
    
    def __init__(self):
        self.trace_dir = os.path.join(os.path.dirname(__file__), "..", "data", "traces")
        os.makedirs(self.trace_dir, exist_ok=True)
        self.current_traces: List[TaskTrace] = []

    def create_trace(self, task_id: str, user_request: str) -> TaskTrace:
        trace = TaskTrace(
            task_id=task_id,
            user_request=user_request,
            observations=[],
            model_decision={},
            selected_tools=[],
            tool_inputs=[],
            tool_outputs=[],
            state_changes=[],
            verification_results=[],
            failures=[],
            recovery_attempts=[],
            final_outcome="pending",
            latency=0,
            token_usage={"prompt": 0, "completion": 0, "total": 0},
            confidence=0.0,
            timestamp=time.time()
        )
        return trace

    def log_observation(self, trace: TaskTrace, observation: Dict):
        """记录观测 - 真实系统状态"""
        trace.observations.append({
            "timestamp": time.time(),
            "type": observation.get("type", "system_state"),
            "data": observation,
            "real": observation.get("real", False)
        })

    def log_tool_call(self, trace: TaskTrace, tool_name: str, tool_input: Dict, tool_output: Dict, exec_time_ms: int):
        """记录工具调用"""
        trace.selected_tools.append(tool_name)
        trace.tool_inputs.append({
            "tool": tool_name,
            "input": tool_input,
            "timestamp": time.time()
        })
        trace.tool_outputs.append({
            "tool": tool_name,
            "output": tool_output,
            "exec_time_ms": exec_time_ms,
            "timestamp": time.time()
        })

    def log_verification(self, trace: TaskTrace, verification: Dict):
        """记录验证结果"""
        trace.verification_results.append({
            "timestamp": time.time(),
            "verified": verification.get("verified", False),
            "reason": verification.get("reason", ""),
            "level": verification.get("level", "unknown"),
            "data": verification
        })

    def log_failure(self, trace: TaskTrace, failure: Dict):
        """记录失败"""
        trace.failures.append({
            "timestamp": time.time(),
            "error": failure.get("error", ""),
            "type": failure.get("type", "unknown"),
            "tool": failure.get("tool", ""),
            "recovery": failure.get("recovery", "")
        })

    def log_recovery(self, trace: TaskTrace, recovery: Dict):
        """记录恢复尝试"""
        trace.recovery_attempts.append({
            "timestamp": time.time(),
            "attempt": recovery.get("attempt", 0),
            "strategy": recovery.get("strategy", ""),
            "result": recovery.get("result", "")
        })

    def finalize_trace(self, trace: TaskTrace, outcome: str, latency: float, token_usage: Dict = None):
        """完成轨迹"""
        trace.final_outcome = outcome
        trace.latency = latency
        if token_usage:
            trace.token_usage = token_usage
        
        # 计算置信度：基于验证结果
        if trace.verification_results:
            verified_count = sum(1 for v in trace.verification_results if v["verified"])
            trace.confidence = verified_count / len(trace.verification_results)
        else:
            trace.confidence = 1.0 if outcome == "success" else 0.0
        
        # 保存到文件
        trace_path = os.path.join(self.trace_dir, f"{trace.task_id}.json")
        try:
            with open(trace_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(trace), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存轨迹失败: {e}")
        
        self.current_traces.append(trace)
        if len(self.current_traces) > 100:
            self.current_traces = self.current_traces[-100:]
        
        return trace

    def get_trace(self, task_id: str) -> Optional[Dict]:
        trace_path = os.path.join(self.trace_dir, f"{task_id}.json")
        if os.path.exists(trace_path):
            try:
                with open(trace_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return None

    def list_traces(self, limit: int = 20) -> List[Dict]:
        traces = []
        try:
            files = sorted(os.listdir(self.trace_dir), reverse=True)[:limit]
            for file in files:
                if file.endswith(".json"):
                    path = os.path.join(self.trace_dir, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            traces.append({
                                "task_id": data["task_id"],
                                "user_request": data["user_request"][:50],
                                "outcome": data["final_outcome"],
                                "latency": data["latency"],
                                "confidence": data["confidence"],
                                "tools": data["selected_tools"],
                                "timestamp": data["timestamp"]
                            })
                    except:
                        continue
        except:
            pass
        return traces

    def get_stats(self) -> Dict:
        """统计"""
        traces = self.current_traces
        if not traces:
            return {"total": 0}
        
        success = sum(1 for t in traces if t.final_outcome == "success")
        avg_latency = sum(t.latency for t in traces) / len(traces) if traces else 0
        avg_tools = sum(len(t.selected_tools) for t in traces) / len(traces) if traces else 0
        
        return {
            "total": len(traces),
            "success": success,
            "success_rate": success / len(traces) if traces else 0,
            "avg_latency": round(avg_latency, 2),
            "avg_tools": round(avg_tools, 1),
            "total_failures": sum(len(t.failures) for t in traces),
            "total_recoveries": sum(len(t.recovery_attempts) for t in traces)
        }

trace_logger = TraceLogger()
