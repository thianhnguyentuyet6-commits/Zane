# -*- coding: utf-8 -*-
"""
Trace Logger - 统一任务轨迹
成为调试/记忆/Skill/评估/训练数据基础
"""
import os
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class TraceEvent:
    type: str  # observation, decision, tool_call, verification, failure, recovery, final
    timestamp: float
    data: Dict

@dataclass
class TaskTrace:
    task_id: str
    user_request: str
    start_time: float
    end_time: Optional[float] = None
    observations: List[Dict] = field(default_factory=list)
    model_decisions: List[Dict] = field(default_factory=list)
    tool_calls: List[Dict] = field(default_factory=list)
    state_changes: List[Dict] = field(default_factory=list)
    verification_results: List[Dict] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)
    recoveries: List[Dict] = field(default_factory=list)
    final_outcome: Optional[str] = None
    success: bool = False
    latency_ms: int = 0
    token_usage: Dict = field(default_factory=dict)
    confidence: float = 0.0
    events: List[TraceEvent] = field(default_factory=list)

class TraceLogger:
    """轨迹记录器 - 统一"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data", "traces")
        os.makedirs(self.data_dir, exist_ok=True)
        self.current_traces: Dict[str, TaskTrace] = {}
    
    def create_trace(self, user_request: str) -> str:
        task_id = f"task_{int(time.time()*1000)}"
        trace = TaskTrace(
            task_id=task_id,
            user_request=user_request,
            start_time=time.time()
        )
        self.current_traces[task_id] = trace
        return task_id
    
    def log_observation(self, task_id: str, observation: Dict):
        if task_id in self.current_traces:
            self.current_traces[task_id].observations.append(observation)
            self.current_traces[task_id].events.append(TraceEvent("observation", time.time(), observation))
    
    def log_decision(self, task_id: str, decision: Dict):
        if task_id in self.current_traces:
            self.current_traces[task_id].model_decisions.append(decision)
            self.current_traces[task_id].events.append(TraceEvent("decision", time.time(), decision))
    
    def log_tool_call(self, task_id: str, tool: str, params: Dict, result: Any, exec_time: int, policy: str):
        if task_id in self.current_traces:
            entry = {
                "tool": tool,
                "params": params,
                "result": str(result)[:1000] if result else None,
                "exec_time_ms": exec_time,
                "policy": policy,
                "timestamp": time.time()
            }
            self.current_traces[task_id].tool_calls.append(entry)
            self.current_traces[task_id].events.append(TraceEvent("tool_call", time.time(), entry))
    
    def log_verification(self, task_id: str, tool: str, verification: Dict):
        if task_id in self.current_traces:
            entry = {"tool": tool, **verification, "timestamp": time.time()}
            self.current_traces[task_id].verification_results.append(entry)
            self.current_traces[task_id].events.append(TraceEvent("verification", time.time(), entry))
    
    def log_failure(self, task_id: str, tool: str, error: str, context: Dict = None):
        if task_id in self.current_traces:
            entry = {"tool": tool, "error": error, "context": context or {}, "timestamp": time.time()}
            self.current_traces[task_id].failures.append(entry)
            self.current_traces[task_id].events.append(TraceEvent("failure", time.time(), entry))
    
    def log_recovery(self, task_id: str, failure: str, recovery_action: Dict):
        if task_id in self.current_traces:
            entry = {"failure": failure, "recovery": recovery_action, "timestamp": time.time()}
            self.current_traces[task_id].recoveries.append(entry)
            self.current_traces[task_id].events.append(TraceEvent("recovery", time.time(), entry))
    
    def finalize(self, task_id: str, outcome: str, success: bool, token_usage: Dict = None, confidence: float = 0.0):
        if task_id in self.current_traces:
            trace = self.current_traces[task_id]
            trace.end_time = time.time()
            trace.final_outcome = outcome
            trace.success = success
            trace.latency_ms = int((trace.end_time - trace.start_time) * 1000)
            trace.token_usage = token_usage or {}
            trace.confidence = confidence
            trace.events.append(TraceEvent("final", time.time(), {"outcome": outcome, "success": success}))
            
            # 保存到文件
            self._save_trace(trace)
            return trace
        return None
    
    def _save_trace(self, trace: TaskTrace):
        try:
            path = os.path.join(self.data_dir, f"{trace.task_id}.json")
            # 转换 events
            data = asdict(trace)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存轨迹失败: {e}")
    
    def get_trace(self, task_id: str) -> Optional[Dict]:
        if task_id in self.current_traces:
            return asdict(self.current_traces[task_id])
        # 从文件加载
        try:
            path = os.path.join(self.data_dir, f"{task_id}.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return None
    
    def list_traces(self, limit: int = 20) -> List[Dict]:
        traces = []
        try:
            files = sorted([f for f in os.listdir(self.data_dir) if f.endswith('.json')], reverse=True)[:limit]
            for file in files:
                path = os.path.join(self.data_dir, file)
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    traces.append({
                        "task_id": data.get("task_id"),
                        "user_request": data.get("user_request", "")[:100],
                        "success": data.get("success"),
                        "latency_ms": data.get("latency_ms"),
                        "tool_calls": len(data.get("tool_calls", [])),
                        "failures": len(data.get("failures", [])),
                        "start_time": data.get("start_time")
                    })
        except Exception as e:
            print(f"列出轨迹失败: {e}")
        
        # 加上内存中的
        for task_id, trace in self.current_traces.items():
            if not any(t["task_id"] == task_id for t in traces):
                traces.append({
                    "task_id": task_id,
                    "user_request": trace.user_request[:100],
                    "success": trace.success,
                    "latency_ms": trace.latency_ms,
                    "tool_calls": len(trace.tool_calls),
                    "failures": len(trace.failures),
                    "start_time": trace.start_time
                })
        
        return traces[:limit]
    
    def get_stats(self) -> Dict:
        traces = self.list_traces(limit=100)
        if not traces:
            return {"total": 0, "success_rate": 0, "avg_latency": 0, "avg_tool_calls": 0}
        
        total = len(traces)
        success = sum(1 for t in traces if t.get("success"))
        avg_latency = sum(t.get("latency_ms", 0) for t in traces) / total if total else 0
        avg_tools = sum(t.get("tool_calls", 0) for t in traces) / total if total else 0
        
        return {
            "total": total,
            "success": success,
            "success_rate": round(success / total * 100, 1) if total else 0,
            "avg_latency_ms": int(avg_latency),
            "avg_tool_calls": round(avg_tools, 1)
        }

# 全局
trace_logger = TraceLogger()
