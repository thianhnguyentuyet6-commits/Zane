# -*- coding: utf-8 -*-
"""
工具注册表 v0913 - 单版本整合版
- 修复：注册表与实现不一致 21→26统一
- 添加move_file，同步security_scan等，补全kill_process/get_window_info/analyze_ui
- 兼容旧版TOOL_REGISTRY
"""
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

class PermissionLevel(Enum):
    READ_ONLY = "read_only"
    WRITE = "write"
    DANGEROUS = "dangerous"
    SYSTEM = "system"

class ToolCategory(Enum):
    FILE = "文件管理"
    PROCESS = "进程控制"
    WINDOW = "窗口管理"
    INPUT = "输入控制"
    VISION = "视觉感知"
    SYSTEM = "系统状态"
    NETWORK = "网络信息"
    CLIPBOARD = "剪贴板"
    SECURITY = "安全扫描"

@dataclass
class ToolDefinition:
    name: str
    display_name: str
    description: str
    category: ToolCategory
    permission: PermissionLevel
    parameters_schema: Dict[str, Any]
    returns_schema: Dict[str, Any]
    need_confirmation: bool
    is_real_action: bool
    examples: List[str]

TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    "list_files": ToolDefinition(name="list_files", display_name="列出文件", description="列出文件和文件夹，演示环境映射Windows路径", category=ToolCategory.FILE, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"path": {"type": "string"}, "detail": {"type": "boolean"}, "pattern": {"type": "string"}}, "required": ["path"]}, returns_schema={"files": "文件列表", "demo_mode": "演示标志"}, need_confirmation=False, is_real_action=True, examples=["列出下载文件夹"]),
    "read_file": ToolDefinition(name="read_file", display_name="读取文件", description="读取文本文件，沙盒检查10MB限制", category=ToolCategory.FILE, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"path": {"type": "string"}, "max_chars": {"type": "integer", "default": 5000}}, "required": ["path"]}, returns_schema={"content": "文件内容"}, need_confirmation=False, is_real_action=True, examples=["读取笔记"]),
    "write_file": ToolDefinition(name="write_file", display_name="写入文件", description="创建或覆盖写入文件，10MB限制可撤销", category=ToolCategory.FILE, permission=PermissionLevel.WRITE, parameters_schema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}, returns_schema={"success": "是否成功"}, need_confirmation=True, is_real_action=True, examples=["创建笔记"]),
    "delete_file": ToolDefinition(name="delete_file", display_name="删除文件", description="删除文件或文件夹，沙盒+回收站可撤销", category=ToolCategory.FILE, permission=PermissionLevel.DANGEROUS, parameters_schema={"type": "object", "properties": {"path": {"type": "string"}, "to_recycle": {"type": "boolean", "default": True}}, "required": ["path"]}, returns_schema={"success": "是否成功"}, need_confirmation=True, is_real_action=True, examples=["删除临时文件"]),
    "create_folder": ToolDefinition(name="create_folder", display_name="创建文件夹", description="创建新文件夹", category=ToolCategory.FILE, permission=PermissionLevel.WRITE, parameters_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, returns_schema={"success": "是否成功"}, need_confirmation=False, is_real_action=True, examples=["新建文件夹"]),
    "move_file": ToolDefinition(name="move_file", display_name="移动文件", description="移动或重命名文件，支持通配符批量移动", category=ToolCategory.FILE, permission=PermissionLevel.WRITE, parameters_schema={"type": "object", "properties": {"source": {"type": "string", "description": "源路径支持通配符"}, "dest": {"type": "string"}}, "required": ["source", "dest"]}, returns_schema={"success": "是否成功", "moved": "已移动列表"}, need_confirmation=True, is_real_action=True, examples=["移动图片"]),
    "inspect_processes": ToolDefinition(name="inspect_processes", display_name="检查进程", description="真实进程检查psutil，内存/CPU排序", category=ToolCategory.PROCESS, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"sort_by": {"type": "string", "enum": ["memory", "cpu", "name"], "default": "memory"}, "limit": {"type": "integer", "default": 20}, "filter_name": {"type": "string"}}, "required": []}, returns_schema={"processes": "进程列表"}, need_confirmation=False, is_real_action=True, examples=["检查内存占用"]),
    "kill_process": ToolDefinition(name="kill_process", display_name="结束进程", description="结束指定进程，过滤危险进程", category=ToolCategory.PROCESS, permission=PermissionLevel.DANGEROUS, parameters_schema={"type": "object", "properties": {"pid": {"type": "integer"}, "name": {"type": "string"}, "force": {"type": "boolean", "default": False}}, "required": []}, returns_schema={"success": "是否成功"}, need_confirmation=True, is_real_action=True, examples=["结束卡死进程"]),
    "launch_application": ToolDefinition(name="launch_application", display_name="启动应用", description="启动应用程序，白名单+参数注入防护", category=ToolCategory.PROCESS, permission=PermissionLevel.WRITE, parameters_schema={"type": "object", "properties": {"app_name": {"type": "string"}, "path": {"type": "string"}, "args": {"type": "string"}}, "required": ["app_name"]}, returns_schema={"success": "是否成功", "pid": "进程ID"}, need_confirmation=True, is_real_action=True, examples=["打开微信"]),
    "list_windows": ToolDefinition(name="list_windows", display_name="枚举窗口", description="枚举窗口Windows真实HWND+Z序DPI，Linux演示模拟", category=ToolCategory.WINDOW, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"only_visible": {"type": "boolean", "default": True}}, "required": []}, returns_schema={"windows": "窗口列表", "demo_mode": "演示标志"}, need_confirmation=False, is_real_action=True, examples=["枚举窗口"]),
    "focus_window": ToolDefinition(name="focus_window", display_name="聚焦窗口", description="聚焦窗口到前台", category=ToolCategory.WINDOW, permission=PermissionLevel.WRITE, parameters_schema={"type": "object", "properties": {"hwnd": {"type": "integer"}, "title_keyword": {"type": "string"}, "pid": {"type": "integer"}}, "required": []}, returns_schema={"success": "是否成功"}, need_confirmation=True, is_real_action=True, examples=["聚焦Chrome"]),
    "get_window_info": ToolDefinition(name="get_window_info", display_name="获取窗口详情", description="获取窗口详细位置大小状态，DPI统一", category=ToolCategory.WINDOW, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"hwnd": {"type": "integer"}, "title_keyword": {"type": "string"}}, "required": []}, returns_schema={"info": "窗口信息"}, need_confirmation=False, is_real_action=True, examples=["窗口多大"]),
    "take_screenshot": ToolDefinition(name="take_screenshot", display_name="屏幕截图", description="截图真实PIL ImageGrab，DPI统一", category=ToolCategory.VISION, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"mode": {"type": "string", "enum": ["full", "window", "region"], "default": "full"}, "hwnd": {"type": "integer"}, "region": {"type": "object"}}, "required": []}, returns_schema={"image_path": "截图路径"}, need_confirmation=False, is_real_action=True, examples=["截图桌面"]),
    "ocr_screenshot": ToolDefinition(name="ocr_screenshot", display_name="OCR识别", description="OCR识别演示，真实需DPI统一+PaddleOCR", category=ToolCategory.VISION, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"lang": {"type": "string", "default": "chi_sim+eng"}, "image_path": {"type": "string"}}, "required": []}, returns_schema={"text": "识别文字"}, need_confirmation=False, is_real_action=True, examples=["识别文字"]),
    "analyze_ui": ToolDefinition(name="analyze_ui", display_name="UI分析", description="UI Automation分析界面控件，DPI统一+UIA树", category=ToolCategory.VISION, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"hwnd": {"type": "integer"}}, "required": []}, returns_schema={"controls": "控件列表"}, need_confirmation=False, is_real_action=True, examples=["分析按钮"]),
    "mouse_click": ToolDefinition(name="mouse_click", display_name="鼠标点击", description="鼠标点击，DPI坐标统一", category=ToolCategory.INPUT, permission=PermissionLevel.WRITE, parameters_schema={"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "button": {"type": "string", "default": "left"}, "double": {"type": "boolean", "default": False}}, "required": ["x", "y"]}, returns_schema={"success": "是否成功"}, need_confirmation=True, is_real_action=True, examples=["点击按钮"]),
    "mouse_move": ToolDefinition(name="mouse_move", display_name="鼠标移动", description="鼠标移动兼容mouse_click，DPI统一", category=ToolCategory.INPUT, permission=PermissionLevel.WRITE, parameters_schema={"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]}, returns_schema={"success": "是否成功"}, need_confirmation=True, is_real_action=True, examples=["移动鼠标"]),
    "keyboard_input": ToolDefinition(name="keyboard_input", display_name="键盘输入", description="键盘输入文本或按键", category=ToolCategory.INPUT, permission=PermissionLevel.WRITE, parameters_schema={"type": "object", "properties": {"text": {"type": "string"}, "keys": {"type": "string"}, "delay_ms": {"type": "integer", "default": 50}}, "required": []}, returns_schema={"success": "是否成功"}, need_confirmation=True, is_real_action=True, examples=["输入文字"]),
    "key_press": ToolDefinition(name="key_press", display_name="按键", description="按键兼容keyboard_input", category=ToolCategory.INPUT, permission=PermissionLevel.WRITE, parameters_schema={"type": "object", "properties": {"keys": {"type": "string"}, "key": {"type": "string"}}, "required": []}, returns_schema={"success": "是否成功"}, need_confirmation=True, is_real_action=True, examples=["按回车"]),
    "get_system_state": ToolDefinition(name="get_system_state", display_name="系统状态", description="真实系统状态psutil，5维度可训练判断", category=ToolCategory.SYSTEM, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {}, "required": []}, returns_schema={"cpu": "CPU", "memory": "内存"}, need_confirmation=False, is_real_action=True, examples=["系统状态"]),
    "get_clipboard": ToolDefinition(name="get_clipboard", display_name="读取剪贴板", description="读取剪贴板内容", category=ToolCategory.CLIPBOARD, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {}, "required": []}, returns_schema={"content": "内容"}, need_confirmation=False, is_real_action=True, examples=["剪贴板"]),
    "set_clipboard": ToolDefinition(name="set_clipboard", display_name="写入剪贴板", description="写入剪贴板", category=ToolCategory.CLIPBOARD, permission=PermissionLevel.WRITE, parameters_schema={"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]}, returns_schema={"success": "是否成功"}, need_confirmation=False, is_real_action=True, examples=["复制文字"]),
    "web_search": ToolDefinition(name="web_search", display_name="网络搜索", description="网络搜索演示，可接入Bing API", category=ToolCategory.NETWORK, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"query": {"type": "string"}, "count": {"type": "integer", "default": 5}}, "required": ["query"]}, returns_schema={"results": "搜索结果"}, need_confirmation=False, is_real_action=True, examples=["搜索"]),
    "verify_info": ToolDefinition(name="verify_info", display_name="信息验证", description="交叉验证信息真实性", category=ToolCategory.NETWORK, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"claim": {"type": "string"}, "sources": {"type": "array", "items": {"type": "string"}}}, "required": ["claim"]}, returns_schema={"verified": "是否验证"}, need_confirmation=False, is_real_action=True, examples=["验证说法"]),
    "security_scan": ToolDefinition(name="security_scan", display_name="安全扫描", description="漏洞扫描明文密码+高危端口+启动项+弱权限，历史趋势", category=ToolCategory.SECURITY, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": []}, returns_schema={"issues": "问题列表", "risk_level": "风险等级"}, need_confirmation=False, is_real_action=True, examples=["安全扫描"]),
    "scan_large_files": ToolDefinition(name="scan_large_files", display_name="大文件扫描", description="扫描大文件清理建议", category=ToolCategory.SECURITY, permission=PermissionLevel.READ_ONLY, parameters_schema={"type": "object", "properties": {"path": {"type": "string"}, "min_size_mb": {"type": "integer", "default": 100}}, "required": []}, returns_schema={"files": "大文件列表"}, need_confirmation=False, is_real_action=True, examples=["扫描大文件"]),
}

def get_tool(name: str) -> Optional[ToolDefinition]:
    return TOOL_REGISTRY.get(name)

def list_tools_by_category() -> Dict[str, List[ToolDefinition]]:
    result = {}
    for tool in TOOL_REGISTRY.values():
        cat = tool.category.value
        if cat not in result:
            result[cat] = []
        result[cat].append(tool)
    return result

def get_tools_for_llm() -> List[Dict]:
    tools = []
    for t in TOOL_REGISTRY.values():
        tools.append({"type": "function", "function": {"name": t.name, "description": f"{t.display_name}: {t.description}。类别：{t.category.value}。权限：{t.permission.value}。示例：{','.join(t.examples)}", "parameters": t.parameters_schema}})
    return tools
