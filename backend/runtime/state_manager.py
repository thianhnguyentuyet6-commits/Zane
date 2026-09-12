# -*- coding: utf-8 -*-
"""
State Manager - 状态管理器
任务始于真实状态观测而非假设，统一 Scene 表示
"""
import os
import time
import platform
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class SceneRepresentation:
    """统一场景表示 - Vision 子系统核心"""
    timestamp: float
    screenshot_path: Optional[str] = None
    width: int = 0
    height: int = 0
    dpi: float = 1.0
    scaling: float = 1.0
    windows: List[Dict] = field(default_factory=list)
    uia_elements: List[Dict] = field(default_factory=list)  # UIA 控件树
    ocr_blocks: List[Dict] = field(default_factory=list)    # OCR 文字+边界框
    cursor_pos: Dict = field(default_factory=dict)
    active_window: Optional[Dict] = None
    app_context: str = ""  # 当前应用上下文
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "screenshot": self.screenshot_path,
            "resolution": f"{self.width}x{self.height}",
            "dpi": self.dpi,
            "windows_count": len(self.windows),
            "uia_count": len(self.uia_elements),
            "ocr_count": len(self.ocr_blocks),
            "cursor": self.cursor_pos,
            "active": self.active_window.get("title", "") if self.active_window else "",
            "app_context": self.app_context
        }

class StateManager:
    """状态管理器 - 真实观测"""
    
    def __init__(self):
        self.last_scene: Optional[SceneRepresentation] = None
        self.is_windows = platform.system() == "Windows"
    
    def observe(self, include_screenshot: bool = False) -> Dict[str, Any]:
        """观测真实状态 - Observe 阶段"""
        state = {}
        
        # 1. 系统基础
        state["system"] = self._get_system_state()
        
        # 2. 窗口 - 真实 HWND
        state["windows"] = self._get_windows()
        
        # 3. 进程 Top5
        state["processes"] = self._get_top_processes()
        
        # 4. 统一场景（可选截图）
        if include_screenshot:
            state["scene"] = self._build_scene().to_dict()
        
        state["timestamp"] = time.time()
        state["platform"] = platform.system()
        
        return state
    
    def _get_system_state(self) -> Dict:
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return {
                "cpu_percent": cpu,
                "memory_percent": mem.percent,
                "memory_available_gb": round(mem.available / 1024**3, 2),
                "disk_percent": round(disk.used / disk.total * 100, 1),
                "disk_free_gb": round(disk.free / 1024**3, 1),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_windows(self) -> List[Dict]:
        try:
            from ..platform.base import get_platform_provider
            provider = get_platform_provider()
            return provider["window"].enum_windows()[:10]
        except:
            return []
    
    def _get_top_processes(self) -> List[Dict]:
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    mem = p.info['memory_info'].rss / 1024 / 1024 if p.info['memory_info'] else 0
                    procs.append({"pid": p.info['pid'], "name": p.info['name'], "memory_mb": round(mem, 1)})
                except:
                    continue
            procs.sort(key=lambda x: x["memory_mb"], reverse=True)
            return procs[:5]
        except:
            return []
    
    def _build_scene(self) -> SceneRepresentation:
        """构建统一场景 - 截图+OCR+UIA+窗口+DPI+光标+应用上下文"""
        scene = SceneRepresentation(timestamp=time.time())
        
        # 截图
        try:
            from ..tools_impl import tool_executor
            result = tool_executor.take_screenshot(mode="full")
            if result.get("success"):
                scene.screenshot_path = result.get("image_path")
                scene.width = result.get("width", 1920)
                scene.height = result.get("height", 1080)
        except:
            pass
        
        # 窗口
        scene.windows = self._get_windows()
        if scene.windows:
            scene.active_window = scene.windows[0]
            scene.app_context = scene.active_window.get("process", "")
        
        # DPI
        if self.is_windows:
            try:
                import ctypes
                hdc = ctypes.windll.user32.GetDC(0)
                dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
                ctypes.windll.user32.ReleaseDC(0, hdc)
                scene.dpi = dpi / 96.0
            except:
                scene.dpi = 1.0
        
        # 光标
        if self.is_windows:
            try:
                import win32gui
                x, y = win32gui.GetCursorPos()
                scene.cursor_pos = {"x": x, "y": y}
            except:
                scene.cursor_pos = {"x": 0, "y": 0}
        
        # UIA 预留
        scene.uia_elements = []  # 需 UIAutomation 库
        
        # OCR 预留
        scene.ocr_blocks = []
        
        self.last_scene = scene
        return scene

# 全局
state_manager = StateManager()
