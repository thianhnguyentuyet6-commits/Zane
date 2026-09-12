# -*- coding: utf-8 -*-
"""
工具契约 - 形式化定义
每个工具完整契约：输入输出Schema、副作用、风险、验证方法
区分 API调用完成 vs 真实动作成功
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import json

@dataclass
class ToolContract:
    name: str
    display_name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    side_effect: str  # none, reversible, destructive, system
    risk_level: str  # low, medium, high, critical
    timeout: int
    required_permissions: List[str]
    preconditions: List[str]
    postconditions: List[str]
    verification_method: str
    category: str
    is_real: bool
    examples: List[str]

# 形式化工具契约 - 21个工具完整定义
TOOL_CONTRACTS: Dict[str, ToolContract] = {
    "list_files": ToolContract(
        name="list_files",
        display_name="列出文件",
        description="列出指定路径文件，真实文件系统",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件夹路径"},
                "detail": {"type": "boolean", "description": "详细信息"},
                "pattern": {"type": "string", "description": "过滤模式，可选"}
            },
            "required": ["path"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "files": {"type": "array", "items": {"type": "object"}},
                "total": {"type": "integer"},
                "total_dirs": {"type": "integer"},
                "total_files": {"type": "integer"}
            }
        },
        side_effect="none",
        risk_level="low",
        timeout=5,
        required_permissions=["file_read"],
        preconditions=["路径存在"],
        postconditions=["返回文件列表"],
        verification_method="检查返回 total 与 files 长度一致",
        category="文件管理",
        is_real=True,
        examples=["列出下载文件夹"]
    ),
    "inspect_processes": ToolContract(
        name="inspect_processes",
        display_name="检查进程",
        description="获取真实进程列表，含进程树",
        input_schema={
            "type": "object",
            "properties": {
                "sort_by": {"type": "string", "enum": ["memory", "cpu", "name"], "default": "memory"},
                "limit": {"type": "integer", "default": 20},
                "filter_name": {"type": "string", "description": "按名称过滤，可选"}
            }
        },
        output_schema={
            "type": "object",
            "properties": {
                "processes": {"type": "array"},
                "total": {"type": "integer"},
                "system_memory": {"type": "object"}
            }
        },
        side_effect="none",
        risk_level="low",
        timeout=5,
        required_permissions=["process_read"],
        preconditions=[],
        postconditions=["返回进程列表"],
        verification_method="检查进程 PID 唯一，总数合理",
        category="进程控制",
        is_real=True,
        examples=["看看什么程序占内存最多"]
    ),
    "launch_application": ToolContract(
        name="launch_application",
        display_name="启动应用",
        description="启动应用程序，验证进程和窗口",
        input_schema={
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "应用名"},
                "path": {"type": "string", "description": "exe路径，可选"},
                "args": {"type": "string", "description": "启动参数，可选"}
            },
            "required": ["app_name"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "pid": {"type": "integer"},
                "process_name": {"type": "string"},
                "window_hwnd": {"type": "integer"},
                "verification": {"type": "object"}
            }
        },
        side_effect="reversible",
        risk_level="medium",
        timeout=10,
        required_permissions=["process_launch"],
        preconditions=["检查应用是否已运行，避免重复"],
        postconditions=["进程存在", "PID有效", "可选：窗口出现"],
        verification_method="进程存在检查 + 窗口枚举 + 可选 UIA 验证，区分 API完成 vs 真实成功",
        category="进程控制",
        is_real=True,
        examples=["帮我打开微信"]
    ),
    "list_windows": ToolContract(
        name="list_windows",
        display_name="枚举窗口",
        description="获取真实窗口列表，含 HWND、Z序、DPI",
        input_schema={
            "type": "object",
            "properties": {
                "only_visible": {"type": "boolean", "default": True}
            }
        },
        output_schema={
            "type": "object",
            "properties": {
                "windows": {"type": "array"},
                "total": {"type": "integer"}
            }
        },
        side_effect="none",
        risk_level="low",
        timeout=5,
        required_permissions=["window_read"],
        preconditions=[],
        postconditions=["返回窗口列表"],
        verification_method="检查 HWND 唯一，标题非空",
        category="窗口管理",
        is_real=True,
        examples=["看看开了哪些窗口"]
    ),
    "focus_window": ToolContract(
        name="focus_window",
        display_name="聚焦窗口",
        description="将窗口切换到前台，DPI感知",
        input_schema={
            "type": "object",
            "properties": {
                "hwnd": {"type": "integer", "description": "窗口句柄，可选"},
                "title_keyword": {"type": "string", "description": "标题关键词，可选"}
            }
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "hwnd": {"type": "integer"},
                "verification": {"type": "object"}
            }
        },
        side_effect="reversible",
        risk_level="medium",
        timeout=5,
        required_permissions=["window_control"],
        preconditions=["窗口存在"],
        postconditions=["窗口在前台", "IsWindowVisible true"],
        verification_method="检查前台窗口是否为目标，GetForegroundWindow",
        category="窗口管理",
        is_real=True,
        examples=["把Chrome切到前台"]
    ),
    "take_screenshot": ToolContract(
        name="take_screenshot",
        display_name="屏幕截图",
        description="真实截图，支持全屏、窗口、区域",
        input_schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["full", "window", "region"], "default": "full"},
                "hwnd": {"type": "integer", "description": "窗口模式时需要"}
            }
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "image_path": {"type": "string"},
                "width": {"type": "integer"},
                "height": {"type": "integer"}
            }
        },
        side_effect="none",
        risk_level="low",
        timeout=5,
        required_permissions=["screen_capture"],
        preconditions=[],
        postconditions=["图片文件存在", "宽高有效"],
        verification_method="检查文件存在，宽高>0",
        category="视觉感知",
        is_real=True,
        examples=["截图看看桌面"]
    ),
    "delete_file": ToolContract(
        name="delete_file",
        display_name="删除文件",
        description="删除文件，移到回收站，可撤销",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "to_recycle": {"type": "boolean", "default": True}
            },
            "required": ["path"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "recycle_path": {"type": "string"},
                "can_undo": {"type": "boolean"}
            }
        },
        side_effect="destructive",
        risk_level="high",
        timeout=10,
        required_permissions=["file_delete"],
        preconditions=["路径在沙盒白名单", "非保护路径"],
        postconditions=["文件不存在或在回收站", "可撤销"],
        verification_method="检查原路径不存在，回收站存在",
        category="文件管理",
        is_real=True,
        examples=["删除临时文件"]
    ),
    "kill_process": ToolContract(
        name="kill_process",
        display_name="结束进程",
        description="结束进程，保护关键系统进程",
        input_schema={
            "type": "object",
            "properties": {
                "pid": {"type": "integer", "description": "进程ID"},
                "name": {"type": "string", "description": "进程名，二选一"}
            }
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "killed_pids": {"type": "array"}
            }
        },
        side_effect="destructive",
        risk_level="high",
        timeout=5,
        required_permissions=["process_kill"],
        preconditions=["非关键系统进程", "非保护进程"],
        postconditions=["进程不存在"],
        verification_method="检查进程 PID 不存在",
        category="进程控制",
        is_real=True,
        examples=["结束卡死进程"]
    ),
}

def get_contract(name: str) -> Optional[ToolContract]:
    return TOOL_CONTRACTS.get(name)

def list_contracts_by_risk():
    result = {"low": [], "medium": [], "high": [], "critical": []}
    for contract in TOOL_CONTRACTS.values():
        result[contract.risk_level].append(contract)
    return result
