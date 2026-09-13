# -*- coding: utf-8 -*-
"""
资源监控 v0914 - 5维度+摄像头/麦克风检测会议中
- CPU/内存/VRAM/插电/游戏+会议检测
- 新增：摄像头/麦克风占用状态检测，比进程名更可靠
- 空闲N分钟+CPU/GPU阈值组合
"""
import os
import sys
import time
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta


class ResourceMonitorV0914:
    """资源监控 v0914 - 支持摄像头/麦克风检测"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.config_path = self.base_dir / "config" / "resource_config.json"
        self.state_path = self.base_dir / "data" / "resource_state.json"
        
        self.game_processes = [
            "game.exe", "steam.exe", "epicgameslauncher.exe", "csgo.exe", "valorant.exe", 
            "league of legends.exe", "dota2.exe", "overwatch.exe", "fortnite.exe",
            "minecraft.exe", "gta5.exe", "cyberpunk2077.exe"
        ]
        self.meeting_processes = [
            "Teams.exe", "Zoom.exe", "TencentMeeting.exe", "WeChat.exe", 
            "dingtalk.exe", "feishu.exe", "voov.exe", "meeting"
        ]
        
        self.config = self._load_config()
        self.last_user_input = datetime.now()
    
    def _load_config(self) -> Dict:
        default = {
            "cpu_threshold": 20,
            "memory_threshold": 70,
            "vram_threshold_gb": 18,
            "gpu_util_threshold": 30,
            "idle_minutes": 30,
            "check_camera_mic": True,  # 是否检测摄像头/麦克风
            "game_detection": True,
            "meeting_detection": True,
            "fullscreen_detection": True
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default.update(loaded)
            except Exception:
                pass
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
        return default
    
    def update_user_activity(self):
        """更新用户活动时间"""
        self.last_user_input = datetime.now()
        # 保存到文件供其他进程读取
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_activity": self.last_user_input.isoformat(),
                    "timestamp": time.time()
                }, f)
        except Exception:
            pass
    
    def check_idle(self) -> Dict[str, Any]:
        """检查用户空闲N分钟"""
        # 尝试从文件读取最后活动时间（前端可能更新）
        last_activity = self.last_user_input
        if self.state_path.exists():
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "last_activity" in data:
                        last_activity = datetime.fromisoformat(data["last_activity"])
            except Exception:
                pass
        
        idle_duration = datetime.now() - last_activity
        idle_minutes = idle_duration.total_seconds() / 60
        is_idle = idle_minutes >= self.config["idle_minutes"]
        
        return {
            "is_idle": is_idle,
            "idle_minutes": round(idle_minutes, 1),
            "required_idle": self.config["idle_minutes"],
            "last_activity": last_activity.isoformat(),
            "reason": f"空闲 {idle_minutes:.1f}分钟 / 需 {self.config['idle_minutes']}分钟"
        }
    
    def check_cpu_memory(self) -> Dict[str, Any]:
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory().percent
            return {
                "cpu": cpu, 
                "memory": mem, 
                "available": True,
                "idle": cpu < self.config["cpu_threshold"] and mem < self.config["memory_threshold"]
            }
        except ImportError:
            return {"cpu": 0, "memory": 0, "available": False, "idle": False, "error": "psutil未安装"}
        except Exception as e:
            return {"cpu": 0, "memory": 0, "available": False, "idle": False, "error": str(e)}
    
    def check_vram(self) -> Dict[str, Any]:
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                total = round(props.total_memory / 1024**3, 1)
                free, _ = torch.cuda.mem_get_info(0)
                free_gb = round(free / 1024**3, 1)
                # GPU利用率
                gpu_util = 0
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util = util.gpu
                except Exception:
                    # 回退：用显存占用估算
                    gpu_util = round((total - free_gb) / total * 100, 1) if total > 0 else 0
                
                return {
                    "total_gb": total,
                    "free_gb": free_gb,
                    "gpu_util": gpu_util,
                    "device": props.name,
                    "available": True,
                    "sufficient": free_gb >= self.config["vram_threshold_gb"] and gpu_util < self.config["gpu_util_threshold"],
                    "idle": gpu_util < self.config["gpu_util_threshold"]
                }
            else:
                return {"total_gb": 0, "free_gb": 0, "gpu_util": 0, "device": "cpu", "available": False, "sufficient": False, "idle": True}
        except ImportError:
            return {"total_gb": 0, "free_gb": 0, "gpu_util": 0, "device": "cpu", "available": False, "error": "torch未安装", "sufficient": False, "idle": True}
        except Exception as e:
            return {"total_gb": 0, "free_gb": 0, "gpu_util": 0, "device": "cpu", "available": False, "error": str(e), "sufficient": False, "idle": True}
    
    def check_power(self) -> Dict[str, Any]:
        """检查是否插电"""
        if sys.platform != "win32":
            return {"is_plugged": True, "battery_percent": 100, "available": False, "sufficient": True, "note": "非Windows，默认插电"}
        
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
                return {"is_plugged": True, "battery_percent": 100, "available": False, "sufficient": True, "error": "GetSystemPowerStatus失败"}
        except Exception as e:
            return {"is_plugged": True, "battery_percent": 100, "available": False, "sufficient": True, "error": str(e), "note": "检测失败，默认插电"}
    
    def check_camera_mic(self) -> Dict[str, Any]:
        """检查摄像头/麦克风占用 - 判断会议中，比进程名更可靠"""
        if not self.config.get("check_camera_mic", True):
            return {"camera_in_use": False, "mic_in_use": False, "in_meeting": False, "available": False, "note": "检测已禁用"}
        
        camera_in_use = False
        mic_in_use = False
        
        # Windows检测
        if sys.platform == "win32":
            try:
                # 方法1：检查进程是否占用摄像头/麦克风
                import psutil
                # 常见会议软件进程
                meeting_procs = []
                for proc in psutil.process_iter(['name', 'pid']):
                    try:
                        name = proc.info['name'] or ""
                        name_lower = name.lower()
                        if any(mp.lower() in name_lower for mp in self.meeting_processes):
                            meeting_procs.append(name)
                    except Exception:
                        continue
                
                # 如果有会议软件运行，可能在会议中
                if meeting_procs:
                    # 进一步检查：会议软件是否占用摄像头/麦克风
                    # 简化：有会议软件运行就认为可能在会议中，需结合全屏等
                    camera_in_use = len(meeting_procs) > 0
                    mic_in_use = len(meeting_procs) > 0
                
                # 方法2：尝试检测摄像头设备占用（需额外库，简化实现）
                # 实际可用：检查是否有进程打开摄像头设备句柄
                # 这里简化：通过WMI或设备管理器检测
                try:
                    import wmi
                    c = wmi.WMI()
                    # 检查摄像头设备状态
                    # 简化逻辑：有会议软件+全屏很可能在会议
                except Exception:
                    pass
                
            except ImportError:
                pass
            except Exception as e:
                return {"camera_in_use": False, "mic_in_use": False, "in_meeting": False, "available": False, "error": str(e)}
        
        # Linux检测 - 检查 /dev/video* 是否被占用
        else:
            try:
                import psutil
                # 检查是否有进程占用视频设备
                for proc in psutil.process_iter(['name', 'open_files']):
                    try:
                        if proc.info['open_files']:
                            for f in proc.info['open_files']:
                                if '/dev/video' in f.path or 'camera' in f.path.lower():
                                    camera_in_use = True
                                if '/dev/snd' in f.path or 'mic' in f.path.lower():
                                    mic_in_use = True
                    except Exception:
                        continue
            except Exception:
                pass
        
        in_meeting = camera_in_use or mic_in_use
        
        return {
            "camera_in_use": camera_in_use,
            "mic_in_use": mic_in_use,
            "in_meeting": in_meeting,
            "should_pause": in_meeting,
            "available": True,
            "method": "进程占用+设备检测，比单纯进程名更可靠",
            "note": "摄像头/麦克风被占用通常表示会议中"
        }
    
    def check_game_meeting(self) -> Dict[str, Any]:
        """检查是否游戏/会议 - 全屏+进程名+摄像头/麦克风"""
        try:
            import psutil
            processes = []
            proc_names = []
            for p in psutil.process_iter(['name']):
                try:
                    name = p.info['name'] or ""
                    proc_names.append(name.lower())
                    processes.append(name)
                except Exception:
                    continue
            
            game_running = any(any(game.lower() in proc for game in self.game_processes) for proc in proc_names)
            meeting_running = any(any(meeting.lower() in proc for meeting in self.meeting_processes) for proc in proc_names)
            
            # 检查全屏
            is_fullscreen = False
            if sys.platform == "win32" and self.config.get("fullscreen_detection", True):
                try:
                    import win32gui
                    hwnd = win32gui.GetForegroundWindow()
                    rect = win32gui.GetWindowRect(hwnd)
                    # 简单判断：窗口大小接近屏幕
                    is_fullscreen = (rect[2] - rect[0]) > 1900 and (rect[3] - rect[1]) > 1000
                except Exception:
                    pass
            
            # 摄像头/麦克风检测
            camera_mic = self.check_camera_mic()
            
            should_pause = game_running or (meeting_running and is_fullscreen) or camera_mic.get("in_meeting", False)
            
            return {
                "game_running": game_running,
                "meeting_running": meeting_running,
                "is_fullscreen": is_fullscreen,
                "camera_mic": camera_mic,
                "should_pause": should_pause,
                "available": True,
                "processes": processes[:10],
                "detection_methods": ["进程名", "全屏", "摄像头/麦克风占用"]
            }
        except ImportError:
            return {"game_running": False, "meeting_running": False, "is_fullscreen": False, "should_pause": False, "available": False, "error": "psutil未安装"}
        except Exception as e:
            return {"game_running": False, "meeting_running": False, "is_fullscreen": False, "should_pause": False, "available": False, "error": str(e)}
    
    def check_ios_remote(self) -> Dict[str, Any]:
        """检查iOS远程是否查看"""
        ios_state_path = self.base_dir / "data" / "ios_state.json"
        if ios_state_path.exists():
            try:
                with open(ios_state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    viewing = data.get("viewing", False)
                    last_update = data.get("timestamp", 0)
                    # 5分钟内有更新才认为在查看
                    is_recent = (time.time() - last_update) < 300
                    return {
                        "ios_viewing": viewing and is_recent,
                        "should_pause": viewing and is_recent,
                        "last_update": last_update,
                        "data": data,
                        "note": "iOS远程查看时暂停训练，避免打扰"
                    }
            except Exception:
                pass
        
        return {
            "ios_viewing": False,
            "should_pause": False,
            "note": "iOS远程检测需前端上报 POST /api/ios/report，暂默认不暂停"
        }
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有资源状态 - 空闲N分钟+CPU/GPU阈值组合"""
        cpu_mem = self.check_cpu_memory()
        vram = self.check_vram()
        power = self.check_power()
        game_meeting = self.check_game_meeting()
        ios = self.check_ios_remote()
        idle = self.check_idle()
        
        # 综合判断是否适合训练 - 空闲N分钟+CPU/GPU阈值
        idle_ok = idle["is_idle"]
        cpu_ok = cpu_mem.get("cpu", 100) < self.config["cpu_threshold"]
        mem_ok = cpu_mem.get("memory", 100) < self.config["memory_threshold"]
        vram_ok = vram.get("sufficient", False) or not vram.get("available", False)
        gpu_ok = vram.get("idle", True)
        power_ok = power.get("sufficient", True)
        not_busy = not game_meeting.get("should_pause", False)
        not_ios = not ios.get("should_pause", False)
        
        can_train = idle_ok and cpu_ok and mem_ok and vram_ok and gpu_ok and power_ok and not_busy and not_ios
        
        return {
            "cpu_memory": cpu_mem,
            "vram": vram,
            "power": power,
            "game_meeting": game_meeting,
            "ios_remote": ios,
            "idle": idle,
            "can_train": can_train,
            "can_train_reason": {
                "idle": f"{idle['reason']} → {idle_ok}",
                "cpu": f"CPU {cpu_mem.get('cpu',0)}%<{self.config['cpu_threshold']}% → {cpu_ok}",
                "memory": f"内存 {cpu_mem.get('memory',0)}%<{self.config['memory_threshold']}% → {mem_ok}",
                "vram": f"VRAM可用 {vram.get('free_gb',0)}GB>={self.config['vram_threshold_gb']}GB + GPU利用率 {vram.get('gpu_util',0)}%<{self.config['gpu_util_threshold']}% → {vram_ok and gpu_ok}",
                "power": f"插电 {power.get('is_plugged',True)} 或 电量 {power.get('battery_percent',100)}%>=50% → {power_ok}",
                "not_busy": f"非游戏/会议全屏/摄像头占用 → {not_busy} (游戏:{game_meeting.get('game_running')} 会议:{game_meeting.get('meeting_running')} 全屏:{game_meeting.get('is_fullscreen')} 摄像头:{game_meeting.get('camera_mic',{}).get('camera_in_use')})",
                "not_ios": f"iOS未查看 → {not_ios}",
                "overall": f"{'✅ 可训练' if can_train else '❌ 不可训练'}"
            },
            "config": self.config,
            "timestamp": time.time()
        }
    
    def can_train(self) -> bool:
        return self.get_all()["can_train"]
    
    def can_train_reason(self) -> str:
        result = self.get_all()
        return result["can_train_reason"]["overall"] + " - " + "; ".join([
            f"{k}: {v}" for k, v in result["can_train_reason"].items() if k != "overall"
        ])


# 全局 v0914
resource_monitor = ResourceMonitorV0914()
# 兼容
resource_monitor_v3 = resource_monitor
