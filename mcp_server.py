#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zane Windows PC智能管家 - MCP Server
MCP Builder skill - 为26工具构建MCP服务器，支持LLM通过MCP协议调用

26工具 Windows真实：
- 文件：list_files, read_file, write_file, delete_file, create_folder, move_file
- 进程：inspect_processes, kill_process, get_system_state
- 窗口：list_windows, focus_window, get_window_info
- 视觉：take_screenshot, ocr_screenshot, analyze_ui
- 系统：launch_application, web_search, verify_info
- 安全：policy_check, pending_queue, undo
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp.server.fastmcp import FastMCP
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    print("⚠️ MCP SDK未安装，运行: pip install mcp")
    # 创建模拟
    class FastMCP:
        def __init__(self, name): self.name = name
        def tool(self, *args, **kwargs): return lambda f: f

# 初始化MCP服务器
mcp = FastMCP("Zane Windows PC智能管家 - 26工具真实")

# 导入工具执行器
try:
    from backend.tools_impl import tool_executor
    from backend.policy.undo_stack import undo_stack
    from backend.policy_firewall import policy_firewall
    TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 工具导入失败: {e}，使用演示模式")
    TOOLS_AVAILABLE = False
    tool_executor = None
    undo_stack = None
    policy_firewall = None

# ========== 文件工具 ==========
@mcp.tool()
async def list_files(path: str = "/tmp", detail: bool = True, pattern: str = None) -> Dict[str, Any]:
    """
    列出文件 - 支持重要性排序+安全沙盒+filelock
    
    Args:
        path: 路径，支持 /tmp, ~/ 等
        detail: 是否详细，含大小时间重要性
        pattern: 过滤模式，如 *.py
    """
    if not TOOLS_AVAILABLE:
        return {"files": [{"name": "demo.txt", "path": "/tmp/demo.txt", "is_dir": False, "size": 100}], "total": 1, "demo": True}
    
    try:
        result = tool_executor.list_files(path, detail=detail, pattern=pattern)
        return result
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def read_file(path: str, max_chars: int = 5000) -> Dict[str, Any]:
    """
    读取文件 - 支持截断+重要性更新
    
    Args:
        path: 文件路径
        max_chars: 最大字符数，默认5000，上下文预算截断
    """
    if not TOOLS_AVAILABLE:
        return {"content": "演示内容", "path": path, "demo": True}
    
    try:
        result = tool_executor.read_file(path, max_chars=max_chars)
        return result
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def write_file(path: str, content: str) -> Dict[str, Any]:
    """
    写入文件 - 支持filelock+可撤销+安全检查
    
    Args:
        path: 文件路径
        content: 内容
    """
    if not TOOLS_AVAILABLE:
        return {"success": True, "path": path, "demo": True}
    
    try:
        result = tool_executor.write_file(path, content)
        return result
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def delete_file(path: str, to_recycle: bool = True) -> Dict[str, Any]:
    """
    删除文件 - 回收站+可撤销+保护路径检查+待确认队列
    
    Args:
        path: 文件路径
        to_recycle: 是否到回收站，默认True可撤销
    """
    if not TOOLS_AVAILABLE:
        return {"success": True, "path": path, "recycle": "/tmp/recycle", "can_undo": True, "demo": True}
    
    try:
        result = tool_executor.delete_file(path, to_recycle=to_recycle)
        return result
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def create_folder(path: str) -> Dict[str, Any]:
    """创建文件夹"""
    if not TOOLS_AVAILABLE:
        return {"success": True, "path": path, "demo": True}
    try:
        return tool_executor.create_folder(path)
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def move_file(source: str, dest: str) -> Dict[str, Any]:
    """移动文件"""
    if not TOOLS_AVAILABLE:
        return {"success": True, "source": source, "dest": dest, "demo": True}
    try:
        return tool_executor.move_file(source, dest)
    except Exception as e:
        return {"error": str(e), "success": False}

# ========== 进程工具 ==========
@mcp.tool()
async def inspect_processes(sort_by: str = "memory", limit: int = 20, filter_name: str = None) -> Dict[str, Any]:
    """
    检查进程 - 真实psutil+进程树+安全
    
    Args:
        sort_by: 排序 memory/cpu/name
        limit: 限制数量
        filter_name: 过滤名称
    """
    if not TOOLS_AVAILABLE:
        return {"processes": [{"pid": 1234, "name": "demo.exe", "memory_mb": 100}], "total": 1, "demo": True}
    try:
        return tool_executor.inspect_processes(sort_by=sort_by, limit=limit, filter_name=filter_name)
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def kill_process(pid: int = None, name: str = None, force: bool = False, exe_path: str = None) -> Dict[str, Any]:
    """
    结束进程 - 白名单外可疑+强制确认+路径PID双重验证防伪造+危险进程拦截
    
    Args:
        pid: PID
        name: 进程名
        force: 是否强制
        exe_path: 可执行路径，用于双重验证防伪造
    """
    if not TOOLS_AVAILABLE:
        return {"success": False, "error": "演示模式，禁止结束进程", "security": "演示", "demo": True}
    try:
        return tool_executor.kill_process(pid=pid, name=name, force=force, exe_path=exe_path)
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def get_system_state() -> Dict[str, Any]:
    """获取系统状态 - 真实psutil+WMI"""
    if not TOOLS_AVAILABLE:
        return {"cpu": {"percent": 25}, "memory": {"percent": 50}, "platform": "linux_demo", "demo": True}
    try:
        return tool_executor.get_system_state()
    except Exception as e:
        return {"error": str(e), "success": False}

# ========== 窗口工具 ==========
@mcp.tool()
async def list_windows(only_visible: bool = True) -> Dict[str, Any]:
    """
    列出窗口 - Win32真实HWND Z序DPI置顶+多显示器
    
    Args:
        only_visible: 仅可见窗口
    """
    if not TOOLS_AVAILABLE:
        return {"windows": [{"hwnd": 123456, "title": "Demo Window", "process": "demo.exe"}], "total": 1, "demo": True}
    try:
        return tool_executor.list_windows(only_visible=only_visible)
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def focus_window(hwnd: int = None, title_keyword: str = None, pid: int = None) -> Dict[str, Any]:
    """聚焦窗口"""
    if not TOOLS_AVAILABLE:
        return {"success": True, "hwnd": hwnd, "demo": True}
    try:
        return tool_executor.focus_window(hwnd=hwnd, title_keyword=title_keyword, pid=pid)
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def get_window_info(hwnd: int = None, title_keyword: str = None) -> Dict[str, Any]:
    """获取窗口信息"""
    if not TOOLS_AVAILABLE:
        return {"hwnd": hwnd, "title": "Demo", "rect": {"left": 0, "top": 0, "width": 800, "height": 600}, "demo": True}
    try:
        return tool_executor.get_window_info(hwnd=hwnd, title_keyword=title_keyword)
    except Exception as e:
        return {"error": str(e), "success": False}

# ========== 视觉工具 ==========
@mcp.tool()
async def take_screenshot(mode: str = "full", hwnd: int = None, region: Dict = None) -> Dict[str, Any]:
    """
    截图 - DPI统一+多显示器+窗口/区域模式
    
    Args:
        mode: full/window/region
        hwnd: 窗口句柄，mode=window时
        region: 区域 {x,y,width,height}，mode=region时，DPI已处理
    """
    if not TOOLS_AVAILABLE:
        return {"success": True, "image_path": "/tmp/screenshot.png", "width": 1920, "height": 1080, "dpi_handled": True, "demo": True}
    try:
        return tool_executor.take_screenshot(mode=mode, hwnd=hwnd, region=region)
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def ocr_screenshot(lang: str = "chi_sim+eng", image_path: str = None) -> Dict[str, Any]:
    """
    OCR截图 - RapidOCR 50MB延迟下载
    
    Args:
        lang: 语言 chi_sim+eng
        image_path: 图片路径，None则自动截图
    """
    if not TOOLS_AVAILABLE:
        return {"text": "演示OCR文本", "success": True, "demo": True}
    try:
        return tool_executor.ocr_screenshot(lang=lang, image_path=image_path)
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def analyze_ui(hwnd: int = None) -> Dict[str, Any]:
    """
    分析UI - UIA树，需Windows真实环境测试浏览器/资源管理器/Office
    
    Args:
        hwnd: 窗口句柄
    """
    if not TOOLS_AVAILABLE:
        return {"elements": [{"name": "Button", "type": "Button", "rect": {"x": 0, "y": 0}}], "total": 1, "demo": True}
    try:
        return tool_executor.analyze_ui(hwnd=hwnd)
    except Exception as e:
        return {"error": str(e), "success": False}

# ========== 系统工具 ==========
@mcp.tool()
async def launch_application(app_name: str, path: str = "", args: str = "") -> Dict[str, Any]:
    """
    启动应用
    
    Args:
        app_name: 应用名，如 notepad, chrome
        path: 路径，可选
        args: 参数，可选
    """
    if not TOOLS_AVAILABLE:
        return {"success": True, "app": app_name, "demo": True}
    try:
        return tool_executor.launch_application(app_name, path=path, args=args)
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def web_search(query: str, count: int = 5) -> Dict[str, Any]:
    """网络搜索"""
    if not TOOLS_AVAILABLE:
        return {"results": [{"title": "Demo", "url": "https://example.com", "snippet": "Demo"}], "demo": True}
    try:
        return tool_executor.web_search(query, count=count)
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def verify_info(claim: str, sources: List[str] = None) -> Dict[str, Any]:
    """验证信息"""
    if not TOOLS_AVAILABLE:
        return {"verified": True, "confidence": 0.8, "demo": True}
    try:
        return tool_executor.verify_info(claim, sources=sources)
    except Exception as e:
        return {"error": str(e), "success": False}

# ========== 安全工具 ==========
@mcp.tool()
async def policy_check(tool: str, params: Dict) -> Dict[str, Any]:
    """策略检查 - 权限分级L0只读L1写入L2危险"""
    if not TOOLS_AVAILABLE:
        return {"allowed": True, "risk": "low", "need_confirm": False, "demo": True}
    try:
        if policy_firewall:
            result = policy_firewall.check(tool, params)
            return result
        return {"allowed": True, "risk": "low"}
    except Exception as e:
        return {"error": str(e), "allowed": False}

@mcp.tool()
async def pending_queue() -> Dict[str, Any]:
    """待确认队列 - 前端弹窗主动提醒"""
    if not TOOLS_AVAILABLE:
        return {"pending": [], "total": 0, "demo": True}
    try:
        if policy_firewall and hasattr(policy_firewall, 'get_pending'):
            return policy_firewall.get_pending()
        return {"pending": [], "total": 0}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def undo_last() -> Dict[str, Any]:
    """撤销最后操作 - 端到端验证，回收站清空权限变化边界"""
    if not TOOLS_AVAILABLE:
        return {"success": True, "message": "已撤销", "demo": True}
    try:
        if undo_stack:
            return undo_stack.undo()
        return {"success": False, "error": "撤销栈不可用"}
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
async def get_memory_stats() -> Dict[str, Any]:
    """获取记忆统计 - 4层+SimpleMem+遗忘"""
    try:
        from backend.memory.memory import memory_v3
        return memory_v3.get_stats()
    except Exception as e:
        try:
            from backend.memory.simple_mem import simple_mem
            return simple_mem.get_stats()
        except Exception as e2:
            return {"error": str(e2), "total": 0, "demo": True}

@mcp.tool()
async def search_memory(query: str, limit: int = 5) -> Dict[str, Any]:
    """搜索记忆 - 重要性排序+意图感知"""
    try:
        from backend.memory.memory import memory_v3
        results = memory_v3.search(query, limit=limit)
        return {"results": results, "total": len(results)}
    except Exception as e:
        return {"error": str(e), "results": []}

# ========== Windows增强 ==========
@mcp.tool()
async def windows_overview() -> Dict[str, Any]:
    """Windows系统概览 - WMI+Win32真实"""
    try:
        from backend.platform.windows.enhanced import windows_enhanced
        return windows_enhanced.get_system_overview()
    except Exception as e:
        try:
            from backend.platform.windows.wmi_provider import WindowsSystemProvider
            provider = WindowsSystemProvider()
            return {
                "cpu": provider.get_cpu_info(),
                "memory": provider.get_memory_info(),
                "real": False,
                "note": "Linux演示，Windows真实"
            }
        except Exception as e2:
            return {"error": str(e2)}

@mcp.tool()
async def windows_process_tree() -> Dict[str, Any]:
    """Windows进程树 - 父进程+命令行+真实"""
    try:
        from backend.platform.windows.enhanced import windows_enhanced
        return windows_enhanced.get_process_tree()
    except Exception as e:
        return {"error": str(e), "processes": []}

@mcp.tool()
async def windows_startup() -> Dict[str, Any]:
    """Windows启动项 - 注册表+启动文件夹"""
    try:
        from backend.platform.windows.enhanced import windows_enhanced
        return windows_enhanced.get_startup_items_enhanced()
    except Exception as e:
        return {"error": str(e), "items": []}

if __name__ == "__main__":
    if HAS_MCP:
        print("🚀 Zane MCP Server启动 - 26工具 Windows真实")
        print("   文件: list_files, read_file, write_file, delete_file, create_folder, move_file")
        print("   进程: inspect_processes, kill_process, get_system_state")
        print("   窗口: list_windows, focus_window, get_window_info")
        print("   视觉: take_screenshot, ocr_screenshot, analyze_ui")
        print("   系统: launch_application, web_search, verify_info")
        print("   安全: policy_check, pending_queue, undo_last")
        print("   记忆: get_memory_stats, search_memory")
        print("   Windows: windows_overview, windows_process_tree, windows_startup")
        print("")
        print("   运行: python mcp_server.py")
        print("   或: mcp dev mcp_server.py")
        mcp.run()
    else:
        print("❌ MCP SDK未安装")
        print("   pip install mcp")
        print("")
        print("   演示模式工具列表:")
        print("   - list_files, read_file, write_file, delete_file")
        print("   - inspect_processes, kill_process, get_system_state")
        print("   - list_windows, focus_window")
        print("   - take_screenshot, ocr_screenshot")
        print("   - 26工具全部支持，Windows真实")
