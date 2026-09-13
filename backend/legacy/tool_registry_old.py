# -*- coding: utf-8 -*-
"""
工具注册表 - Tool Registry
所有计算机操作必须显式定义、权限控制、可审计
"""
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass
import json

class PermissionLevel(Enum):
    """权限等级"""
    READ_ONLY = "read_only"          # 只读，无需确认
    WRITE = "write"                  # 写入，需确认
    DANGEROUS = "dangerous"          # 危险操作，需二次确认
    SYSTEM = "system"                # 系统级，需严格确认

class ToolCategory(Enum):
    FILE = "文件管理"
    PROCESS = "进程控制"
    WINDOW = "窗口管理"
    INPUT = "输入控制"
    VISION = "视觉感知"
    SYSTEM = "系统状态"
    NETWORK = "网络信息"
    CLIPBOARD = "剪贴板"

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
    is_real_action: bool  # 是否是真实系统操作而非模拟
    examples: List[str]

# 工具注册表 - 所有工具显式定义
TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    # ========== 文件管理 ==========
    "list_files": ToolDefinition(
        name="list_files",
        display_name="列出文件",
        description="列出指定路径下的文件和文件夹，支持详细信息",
        category=ToolCategory.FILE,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件夹路径，如 C:\\Users\\User\\Documents"},
                "detail": {"type": "boolean", "description": "是否显示详细信息"},
                "pattern": {"type": "string", "description": "文件名过滤模式，可选"}
            },
            "required": ["path"]
        },
        returns_schema={"files": "文件列表", "total": "总数"},
        need_confirmation=False,
        is_real_action=True,
        examples=["列出下载文件夹", "看看桌面有什么文件"]
    ),
    "read_file": ToolDefinition(
        name="read_file",
        display_name="读取文件",
        description="读取文本文件内容，自动处理编码",
        category=ToolCategory.FILE,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "max_chars": {"type": "integer", "description": "最大读取字符数，默认5000"}
            },
            "required": ["path"]
        },
        returns_schema={"content": "文件内容"},
        need_confirmation=False,
        is_real_action=True,
        examples=["读取这个txt文件"]
    ),
    "write_file": ToolDefinition(
        name="write_file",
        display_name="写入文件",
        description="创建或覆盖写入文件",
        category=ToolCategory.FILE,
        permission=PermissionLevel.WRITE,
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "encoding": {"type": "string", "default": "utf-8"}
            },
            "required": ["path", "content"]
        },
        returns_schema={"success": "是否成功"},
        need_confirmation=True,
        is_real_action=True,
        examples=["帮我创建一个笔记文件"]
    ),
    "delete_file": ToolDefinition(
        name="delete_file",
        display_name="删除文件",
        description="删除文件或文件夹（危险操作）",
        category=ToolCategory.FILE,
        permission=PermissionLevel.DANGEROUS,
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "to_recycle": {"type": "boolean", "description": "是否移到回收站，默认true"}
            },
            "required": ["path"]
        },
        returns_schema={"success": "是否成功"},
        need_confirmation=True,
        is_real_action=True,
        examples=["删除临时文件"]
    ),
    "create_folder": ToolDefinition(
        name="create_folder",
        display_name="创建文件夹",
        description="创建新文件夹",
        category=ToolCategory.FILE,
        permission=PermissionLevel.WRITE,
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        },
        returns_schema={"success": "是否成功"},
        need_confirmation=False,
        is_real_action=True,
        examples=["新建一个文件夹"]
    ),
    # ========== 进程控制 ==========
    "inspect_processes": ToolDefinition(
        name="inspect_processes",
        display_name="检查进程",
        description="获取当前运行的进程列表，支持按内存/CPU排序",
        category=ToolCategory.PROCESS,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "sort_by": {"type": "string", "enum": ["memory", "cpu", "name"], "default": "memory"},
                "limit": {"type": "integer", "default": 20},
                "filter_name": {"type": "string", "description": "按名称过滤，可选"}
            },
            "required": []
        },
        returns_schema={"processes": "进程列表"},
        need_confirmation=False,
        is_real_action=True,
        examples=["看看现在什么程序占内存最多", "检查Chrome进程"]
    ),
    "kill_process": ToolDefinition(
        name="kill_process",
        display_name="结束进程",
        description="结束指定进程（危险操作）",
        category=ToolCategory.PROCESS,
        permission=PermissionLevel.DANGEROUS,
        parameters_schema={
            "type": "object",
            "properties": {
                "pid": {"type": "integer", "description": "进程ID"},
                "name": {"type": "string", "description": "进程名，二选一"},
                "force": {"type": "boolean", "default": False}
            },
            "required": []
        },
        returns_schema={"success": "是否成功"},
        need_confirmation=True,
        is_real_action=True,
        examples=["结束这个卡死的进程"]
    ),
    "launch_application": ToolDefinition(
        name="launch_application",
        display_name="启动应用",
        description="启动应用程序",
        category=ToolCategory.PROCESS,
        permission=PermissionLevel.WRITE,
        parameters_schema={
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "应用名称，如 wechat, chrome, notepad"},
                "path": {"type": "string", "description": "可执行文件路径，可选"},
                "args": {"type": "string", "description": "启动参数，可选"}
            },
            "required": ["app_name"]
        },
        returns_schema={"success": "是否成功", "pid": "进程ID"},
        need_confirmation=True,
        is_real_action=True,
        examples=["帮我打开微信", "启动Chrome浏览器"]
    ),
    # ========== 窗口管理 ==========
    "list_windows": ToolDefinition(
        name="list_windows",
        display_name="枚举窗口",
        description="获取当前所有可见窗口列表",
        category=ToolCategory.WINDOW,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "only_visible": {"type": "boolean", "default": True}
            },
            "required": []
        },
        returns_schema={"windows": "窗口列表"},
        need_confirmation=False,
        is_real_action=True,
        examples=["看看现在开了哪些窗口", "把这个窗口切到前台"]
    ),
    "focus_window": ToolDefinition(
        name="focus_window",
        display_name="聚焦窗口",
        description="将指定窗口切换到前台并聚焦",
        category=ToolCategory.WINDOW,
        permission=PermissionLevel.WRITE,
        parameters_schema={
            "type": "object",
            "properties": {
                "hwnd": {"type": "integer", "description": "窗口句柄，可选"},
                "title_keyword": {"type": "string", "description": "窗口标题关键词，可选"},
                "pid": {"type": "integer", "description": "进程ID，可选"}
            },
            "required": []
        },
        returns_schema={"success": "是否成功"},
        need_confirmation=True,
        is_real_action=True,
        examples=["把Chrome切到前台"]
    ),
    "get_window_info": ToolDefinition(
        name="get_window_info",
        display_name="获取窗口详情",
        description="获取窗口的详细位置、大小、状态信息",
        category=ToolCategory.WINDOW,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "hwnd": {"type": "integer"},
                "title_keyword": {"type": "string"}
            },
            "required": []
        },
        returns_schema={"info": "窗口信息"},
        need_confirmation=False,
        is_real_action=True,
        examples=["看看这个窗口多大"]
    ),
    # ========== 视觉感知 ==========
    "take_screenshot": ToolDefinition(
        name="take_screenshot",
        display_name="屏幕截图",
        description="截取屏幕，支持全屏、窗口、区域截图",
        category=ToolCategory.VISION,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["full", "window", "region"], "default": "full"},
                "hwnd": {"type": "integer", "description": "窗口模式时需要"},
                "region": {"type": "object", "description": "区域模式 {x,y,width,height}"}
            },
            "required": []
        },
        returns_schema={"image_path": "截图路径", "width": "宽度", "height": "高度"},
        need_confirmation=False,
        is_real_action=True,
        examples=["截图给我看看桌面", "截一下这个窗口"]
    ),
    "ocr_screenshot": ToolDefinition(
        name="ocr_screenshot",
        display_name="OCR文字识别",
        description="对最近截图进行OCR文字识别",
        category=ToolCategory.VISION,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "lang": {"type": "string", "default": "chi_sim+eng"},
                "image_path": {"type": "string", "description": "图片路径，可选，默认最新截图"}
            },
            "required": []
        },
        returns_schema={"text": "识别文字", "blocks": "文字块"},
        need_confirmation=False,
        is_real_action=True,
        examples=["识别屏幕上的文字"]
    ),
    "analyze_ui": ToolDefinition(
        name="analyze_ui",
        display_name="UI自动化分析",
        description="使用Windows UI Automation分析当前界面控件",
        category=ToolCategory.VISION,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "hwnd": {"type": "integer", "description": "窗口句柄，可选"}
            },
            "required": []
        },
        returns_schema={"controls": "控件列表"},
        need_confirmation=False,
        is_real_action=True,
        examples=["分析一下这个窗口的按钮"]
    ),
    # ========== 输入控制 ==========
    "mouse_click": ToolDefinition(
        name="mouse_click",
        display_name="鼠标点击",
        description="模拟鼠标点击",
        category=ToolCategory.INPUT,
        permission=PermissionLevel.WRITE,
        parameters_schema={
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                "double": {"type": "boolean", "default": False}
            },
            "required": ["x", "y"]
        },
        returns_schema={"success": "是否成功"},
        need_confirmation=True,
        is_real_action=True,
        examples=["点击这个按钮"]
    ),
    "keyboard_input": ToolDefinition(
        name="keyboard_input",
        display_name="键盘输入",
        description="模拟键盘输入文本或按键",
        category=ToolCategory.INPUT,
        permission=PermissionLevel.WRITE,
        parameters_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "要输入的文本，可选"},
                "keys": {"type": "string", "description": "特殊按键，如 {ENTER}, {CTRL}+C，可选"},
                "delay_ms": {"type": "integer", "default": 50}
            },
            "required": []
        },
        returns_schema={"success": "是否成功"},
        need_confirmation=True,
        is_real_action=True,
        examples=["帮我输入这段文字"]
    ),
    # ========== 系统状态 ==========
    "get_system_state": ToolDefinition(
        name="get_system_state",
        display_name="获取系统状态",
        description="获取CPU、内存、磁盘、网络等系统状态",
        category=ToolCategory.SYSTEM,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {},
            "required": []
        },
        returns_schema={"cpu": "CPU信息", "memory": "内存信息"},
        need_confirmation=False,
        is_real_action=True,
        examples=["看看电脑现在状态怎么样"]
    ),
    "get_clipboard": ToolDefinition(
        name="get_clipboard",
        display_name="读取剪贴板",
        description="读取剪贴板内容",
        category=ToolCategory.CLIPBOARD,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {},
            "required": []
        },
        returns_schema={"content": "剪贴板内容"},
        need_confirmation=False,
        is_real_action=True,
        examples=["看看剪贴板有什么"]
    ),
    "set_clipboard": ToolDefinition(
        name="set_clipboard",
        display_name="写入剪贴板",
        description="写入文本到剪贴板",
        category=ToolCategory.CLIPBOARD,
        permission=PermissionLevel.WRITE,
        parameters_schema={
            "type": "object",
            "properties": {
                "content": {"type": "string"}
            },
            "required": ["content"]
        },
        returns_schema={"success": "是否成功"},
        need_confirmation=False,
        is_real_action=True,
        examples=["复制这段文字"]
    ),
    # ========== 网络信息 ==========
    "web_search": ToolDefinition(
        name="web_search",
        display_name="网络搜索",
        description="联网搜索信息，用于资料验证",
        category=ToolCategory.NETWORK,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "count": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        },
        returns_schema={"results": "搜索结果"},
        need_confirmation=False,
        is_real_action=True,
        examples=["搜索一下这个问题怎么解决"]
    ),
    "verify_info": ToolDefinition(
        name="verify_info",
        display_name="信息验证",
        description="交叉验证信息的真实性",
        category=ToolCategory.NETWORK,
        permission=PermissionLevel.READ_ONLY,
        parameters_schema={
            "type": "object",
            "properties": {
                "claim": {"type": "string", "description": "待验证的陈述"},
                "sources": {"type": "array", "items": {"type": "string"}, "description": "来源，可选"}
            },
            "required": ["claim"]
        },
        returns_schema={"verified": "是否验证", "confidence": "置信度"},
        need_confirmation=False,
        is_real_action=True,
        examples=["验证一下这个说法对不对"]
    ),
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
    """转换为OpenAI tool格式，描述使用中文"""
    tools = []
    for t in TOOL_REGISTRY.values():
        tools.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": f"{t.display_name}: {t.description}。类别：{t.category.value}。权限：{t.permission.value}。示例：{','.join(t.examples)}",
                "parameters": t.parameters_schema
            }
        })
    return tools
