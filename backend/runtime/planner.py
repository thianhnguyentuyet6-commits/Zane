# -*- coding: utf-8 -*-
"""
Planner - 规划器
将意图分解为 DAG，支持多步任务
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class TaskNode:
    id: str
    title: str
    tool: str
    params: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    risk: str = "low"
    estimated_time: int = 2  # 秒
    verification: str = ""

@dataclass
class TaskPlan:
    intent: str
    nodes: List[TaskNode]
    total_steps: int
    estimated_total_time: int
    has_destructive: bool
    needs_confirm: bool

class Planner:
    """规划器 - 任务分解"""
    
    # 预定义模板 - 确定性
    TEMPLATES = {
        "organize_downloads": [
            TaskNode("1", "列出下载文件夹", "list_files", {"path": "C:\\Users\\User\\Downloads", "detail": True}, [], "low", 1, "文件列表非空"),
            TaskNode("2", "创建分类文件夹", "create_folder", {"path": "C:\\Users\\User\\Downloads\\分类"}, [], "low", 1, "文件夹存在"),
            TaskNode("3", "移动文档", "move_file", {"source": "C:\\Users\\User\\Downloads\\*.docx", "dest": "C:\\Users\\User\\Downloads\\分类\\文档"}, ["1", "2"], "medium", 2, "目标存在文件"),
        ],
        "clean_large_files": [
            TaskNode("1", "扫描大文件", "scan_large_files", {"min_gb": 1.0}, [], "low", 5, "返回大文件列表"),
            TaskNode("2", "确认删除", "confirm", {"message": "确认删除大文件"}, ["1"], "high", 1, "用户确认"),
        ]
    }
    
    def __init__(self):
        self.tool_contracts = None
    
    def plan(self, intent: str, parsed_intent: Optional[Any] = None, system_state: Optional[Dict] = None) -> TaskPlan:
        """规划 - 模板匹配优先，LLM补充"""
        
        # 1. 模板匹配
        template_key = self._match_template(intent)
        if template_key:
            nodes = self.TEMPLATES[template_key]
            return TaskPlan(
                intent=intent,
                nodes=nodes,
                total_steps=len(nodes),
                estimated_total_time=sum(n.estimated_time for n in nodes),
                has_destructive=any(n.risk in ["high", "critical"] for n in nodes),
                needs_confirm=any(n.risk in ["high", "critical"] for n in nodes)
            )
        
        # 2. 简单单步
        tool, params = self._infer_tool(intent, parsed_intent)
        node = TaskNode(
            id="1",
            title=f"执行 {tool}",
            tool=tool,
            params=params,
            dependencies=[],
            risk=self._estimate_risk(tool, params),
            estimated_time=2,
            verification=self._get_verification(tool)
        )
        
        return TaskPlan(
            intent=intent,
            nodes=[node],
            total_steps=1,
            estimated_total_time=2,
            has_destructive=node.risk in ["high", "critical"],
            needs_confirm=node.risk in ["high", "critical"]
        )
    
    def _match_template(self, intent: str) -> Optional[str]:
        if any(k in intent for k in ["整理", "归类", "下载"]):
            return "organize_downloads"
        if any(k in intent for k in ["大文件", "清理", "磁盘"]):
            return "clean_large_files"
        return None
    
    def _infer_tool(self, intent: str, parsed: Optional[Any]) -> tuple[str, Dict]:
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
    
    def _estimate_risk(self, tool: str, params: Dict) -> str:
        destructive = ["delete_file", "kill_process", "move_file", "wsl_exec"]
        if tool in destructive:
            return "high" if "System32" in str(params) or "csrss" in str(params) else "medium"
        return "low"
    
    def _get_verification(self, tool: str) -> str:
        verifications = {
            "list_files": "返回文件列表非空",
            "launch_application": "进程存在+窗口出现",
            "delete_file": "文件不存在",
            "move_file": "源不存在+目标存在",
            "kill_process": "进程不存在",
            "focus_window": "窗口在前台",
        }
        return verifications.get(tool, "API返回success且无error")

# 全局
planner = Planner()
