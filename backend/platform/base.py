# -*- coding: utf-8 -*-
"""
平台抽象层 - Platform Abstraction
商业级跨平台设计，类似 VS Code 的抽象
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class SystemProvider(ABC):
    """系统信息提供者抽象"""
    @abstractmethod
    def get_cpu_info(self) -> Dict: pass
    @abstractmethod
    def get_memory_info(self) -> Dict: pass
    @abstractmethod
    def get_disk_info(self) -> List[Dict]: pass
    @abstractmethod
    def get_processes(self, sort_by: str = "memory", limit: int = 50) -> Dict: pass
    @abstractmethod
    def get_startup_items(self) -> List[Dict]: pass
    @abstractmethod
    def get_services(self) -> List[Dict]: pass

class WindowProvider(ABC):
    """窗口管理抽象"""
    @abstractmethod
    def enum_windows(self, only_visible: bool = True) -> List[Dict]: pass
    @abstractmethod
    def get_window_info(self, hwnd: int) -> Dict: pass
    @abstractmethod
    def focus_window(self, hwnd: int = None, title_keyword: str = None) -> Dict: pass
    @abstractmethod
    def get_window_thumbnail(self, hwnd: int) -> Optional[str]: pass

class ScreenshotProvider(ABC):
    @abstractmethod
    def capture_full(self) -> Dict: pass
    @abstractmethod
    def capture_window(self, hwnd: int) -> Dict: pass
    @abstractmethod
    def capture_region(self, x: int, y: int, w: int, h: int) -> Dict: pass

def get_platform_provider():
    """工厂：根据当前平台返回真实实现"""
    import platform
    system = platform.system()
    if system == "Windows":
        from .windows.wmi_provider import WindowsSystemProvider
        from .windows.win32_window import WindowsWindowProvider
        return {
            "system": WindowsSystemProvider(),
            "window": WindowsWindowProvider(),
            "name": "Windows"
        }
    else:
        from .linux.fallback import LinuxSystemProvider, LinuxWindowProvider
        return {
            "system": LinuxSystemProvider(),
            "window": LinuxWindowProvider(),
            "name": system + " (模拟)"
        }
