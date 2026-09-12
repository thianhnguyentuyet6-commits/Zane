# -*- coding: utf-8 -*-
"""
资源监控 - v3 资源感知
- CPU/内存/VRAM/插电/游戏检测
"""
import os
import sys
import time
from typing import Dict, Any, List
from pathlib import Path

class ResourceMonitor:
    """资源监控 v3"""
    
    def __init__(self):
        self.game_processes = ["game.exe", "steam.exe", "epicgameslauncher.exe", "csgo.exe", "valorant.exe", "league of legends.exe"]
        self.meeting_processes = ["Teams.exe", "Zoom.exe", "TencentMeeting.exe", "WeChat.exe"]
    
    def check_cpu_memory(self) -> Dict[str, Any]:
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory().percent
            return {"cpu": cpu, "memory": mem, "available": True}
        except ImportError:
            return {"cpu": 0, "memory": 0, "available": False, "error": "psutil未安装"}
        except Exception as e:
            return {"cpu": 0, "memory": 0, "available": False, "error": str(e)}
    
    def check_vram(self) -> Dict[str, Any]:
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                total = round(props.total_memory / 1024**3, 1)
                free, _ = torch.cuda.mem_get_info(0)
                free_gb = round(free / 1024**3, 1)
                return {
                    "total_gb": total,
                    "free_gb": free_gb,
                    "device": props.name,
                    "available": True,
                    "sufficient": free_gb >= 18
                }
            else:
                return {"total_gb": 0, "free_gb": 0, "device": "cpu", "available": False, "sufficient": False}
        except ImportError:
            return {"total_gb": 0, "free_gb": 0, "device": "cpu", "available": False, "error": "torch未安装", "sufficient": False}
        except Exception as e:
            return {"total_gb": 0, "free_gb": 0, "device": "cpu", "available": False, "error": str(e), "sufficient": False}
    
    def check_power(self) -> Dict[str, Any]:
        """检查是否插电，Windows"""
        if sys.platform != "win32":
            return {"is_plugged": True, "battery_percent": 100, "available": False, "note": "非Windows，默认插电"}
        
        try:
            import ctypes
            from ctypes import wintypes
            
            class SYSTEM_POWER_STATUS(ctypes.Structure):
                _fields_ = [
                    ('ACLineStatus', wintypes.BYTE),
                    ('BatteryFlag', wintypes.BYTE),
                    ('BatteryLifePercent', wintypes.BYTE),
                    ('Reserved1', wintypes.BYTE),
                    ('BatteryLifeTime', wintypes.DWORD),
                    ('BatteryFullLifeTime', wintypes.DWORD),
                ]
            
            status = SYSTEM_POWER_STATUS()
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
                is_plugged = status.ACLineStatus == 1
                battery = status.BatteryLifePercent
                if battery == 255:
                    battery = 100
                
                return {
                    "is_plugged": is_plugged,
                    "battery_percent": battery,
                    "ac_status": status.ACLineStatus,
                    "available": True,
                    "sufficient": is_plugged or battery >= 50
                }
            else:
                return {"is_plugged": True, "battery_percent": 100, "available": False, "error": "GetSystemPowerStatus失败"}
        except Exception as e:
            return {"is_plugged": True, "battery_percent": 100, "available": False, "error": str(e), "note": "检测失败，默认插电"}
    
    def check_game_meeting(self) -> Dict[str, Any]:
        """检查是否游戏/会议"""
        try:
            import psutil
            processes = [p.name().lower() for p in psutil.process_iter(['name'])]
            
            game_running = any(any(game.lower() in proc for game in self.game_processes) for proc in processes)
            meeting_running = any(any(meeting.lower() in proc for meeting in self.meeting_processes) for proc in processes)
            
            # 检查全屏
            is_fullscreen = False
            if sys.platform == "win32":
                try:
                    import win32gui
                    hwnd = win32gui.GetForegroundWindow()
                    rect = win32gui.GetWindowRect(hwnd)
                    # 简单判断：窗口大小接近屏幕
                    is_fullscreen = (rect[2] - rect[0]) > 1900 and (rect[3] - rect[1]) > 1000
                except Exception:
                    pass
            
            return {
                "game_running": game_running,
                "meeting_running": meeting_running,
                "is_fullscreen": is_fullscreen,
                "should_pause": game_running or (meeting_running and is_fullscreen),
                "available": True,
                "processes": processes[:10]
            }
        except ImportError:
            return {"game_running": False, "meeting_running": False, "is_fullscreen": False, "should_pause": False, "available": False, "error": "psutil未安装"}
        except Exception as e:
            return {"game_running": False, "meeting_running": False, "is_fullscreen": False, "should_pause": False, "available": False, "error": str(e)}
    
    def check_ios_remote(self) -> Dict[str, Any]:
        """检查iOS远程是否查看"""
        # 简单：检查是否有最近的前端访问
        # 实际可通过文件或数据库记录
        return {
            "ios_viewing": False,
            "should_pause": False,
            "note": "iOS远程检测需前端上报，暂默认不暂停"
        }
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有资源状态"""
        cpu_mem = self.check_cpu_memory()
        vram = self.check_vram()
        power = self.check_power()
        game_meeting = self.check_game_meeting()
        ios = self.check_ios_remote()
        
        # 综合判断是否适合训练
        idle = cpu_mem.get("cpu", 100) < 20 and cpu_mem.get("memory", 100) < 70
        vram_ok = vram.get("sufficient", False) or not vram.get("available", False)  # 无GPU也允许技能进化
        power_ok = power.get("sufficient", True)
        not_busy = not game_meeting.get("should_pause", False)
        not_ios = not ios.get("should_pause", False)
        
        can_train = idle and vram_ok and power_ok and not_busy and not_ios
        
        return {
            "cpu_memory": cpu_mem,
            "vram": vram,
            "power": power,
            "game_meeting": game_meeting,
            "ios_remote": ios,
            "can_train": can_train,
            "can_train_reason": {
                "idle": f"CPU {cpu_mem.get('cpu',0)}%<20% 内存 {cpu_mem.get('memory',0)}%<70% → {idle}",
                "vram": f"VRAM可用 {vram.get('free_gb',0)}GB>=18GB → {vram_ok}",
                "power": f"插电 {power.get('is_plugged',True)} 或 电量 {power.get('battery_percent',100)}%>=50% → {power_ok}",
                "not_busy": f"非游戏/会议全屏 → {not_busy}",
                "not_ios": f"iOS未查看 → {not_ios}",
                "overall": f"{'可训练' if can_train else '不可训练'}"
            },
            "timestamp": time.time()
        }

# 全局
resource_monitor = ResourceMonitor()
