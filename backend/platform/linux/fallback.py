# -*- coding: utf-8 -*-
"""
Linux Fallback - 演示环境
结构与 Windows 一致，但数据模拟，保证商业级接口一致性
"""
import psutil, time, platform
from typing import Dict, List

class LinuxSystemProvider:
    def get_cpu_info(self):
        cpu_percent = psutil.cpu_percent(interval=0.3, percpu=True)
        return {
            "name": platform.processor() or "Linux CPU",
            "total_percent": sum(cpu_percent)/len(cpu_percent) if cpu_percent else 0,
            "per_core": [{"core": i, "percent": p} for i, p in enumerate(cpu_percent)],
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "gpus": [],
            "real": False,
            "note": "Linux 演示，Windows上为真实 WMI 数据"
        }
    
    def get_memory_info(self):
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "physical": {"total_gb": round(mem.total/1024**3,2), "used_gb": round(mem.used/1024**3,2), "available_gb": round(mem.available/1024**3,2), "percent": mem.percent, "sticks": []},
            "swap": {"total_gb": round(swap.total/1024**3,2), "used_gb": round(swap.used/1024**3,2), "percent": swap.percent},
            "real": False
        }
    
    def get_disk_info(self):
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({"device": part.device, "mountpoint": part.mountpoint, "fstype": part.fstype, "total_gb": round(usage.total/1024**3,1), "used_gb": round(usage.used/1024**3,1), "free_gb": round(usage.free/1024**3,1), "percent": round(usage.used/usage.total*100,1), "type": "SSD"})
            except:
                continue
        return disks
    
    def get_processes(self, sort_by="memory", limit=50):
        processes = []
        for proc in psutil.process_iter(['pid','ppid','name','memory_info','cpu_percent','create_time','status']):
            try:
                info = proc.info
                mem_mb = info['memory_info'].rss/1024/1024 if info['memory_info'] else 0
                processes.append({"pid": info['pid'], "ppid": info['ppid'], "parent_name": "", "name": info['name'], "exe": "", "cmdline": "", "memory_mb": round(mem_mb,1), "memory_percent": 0, "cpu_percent": info['cpu_percent'] or 0, "username": "", "status": info['status'], "threads": 0, "handles": 0, "create_time": "", "uptime": 0})
            except:
                continue
        if sort_by=="memory":
            processes.sort(key=lambda x: x["memory_mb"], reverse=True)
        return {"processes": processes[:limit], "total": len(processes), "real": False}
    
    def get_startup_items(self):
        return [{"name": "演示启动项", "path": "/tmp/demo", "location": "演示", "enabled": True, "real": False}]
    
    def get_services(self):
        return []

class LinuxWindowProvider:
    def enum_windows(self, only_visible=True):
        return [
            {"hwnd": 1001, "title": "Chrome - Zane", "class": "Chrome", "pid": 100, "process": "chrome", "rect": {"left":0,"top":0,"width":1920,"height":1080,"right":1920,"bottom":1080}, "visible": True, "is_minimized": False, "is_maximized": True, "is_topmost": False, "z_order":0, "dpi":96, "real": False},
        ]
    
    def get_window_info(self, hwnd):
        return {"hwnd": hwnd, "title": "Linux演示窗口", "real": False}
    
    def focus_window(self, hwnd=None, title_keyword=None):
        return {"success": True, "hwnd": hwnd, "real": False}
    
    def get_window_thumbnail(self, hwnd):
        return None
