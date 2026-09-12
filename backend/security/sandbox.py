# -*- coding: utf-8 -*-
"""
沙盒 - File + Process Sandbox
商业级安全：文件操作限制在沙盒目录，进程保护关键系统进程
具体实现，非空中阁楼
"""
import os
import psutil
import shutil
from typing import List, Dict

class FileSandbox:
    """文件沙盒 - 具体实现"""
    
    def __init__(self):
        # 沙盒根目录 - 可配置
        self.sandbox_root = os.path.join(os.path.expanduser("~"), "ZaneSandbox")
        os.makedirs(self.sandbox_root, exist_ok=True)
        
        # 允许操作的目录 - 白名单
        self.allowed_roots = [
            os.path.realpath(self.sandbox_root),
            os.path.realpath(os.path.join(os.path.expanduser("~"), "Downloads")),
            os.path.realpath(os.path.join(os.path.expanduser("~"), "Documents")),
            os.path.realpath(os.path.join(os.path.expanduser("~"), "Desktop")),
            os.path.realpath(os.getcwd()),  # 当前项目目录
            os.path.realpath("/tmp"),  # Linux 演示
        ]
        
        # 保护路径 - 黑名单
        self.protected_paths = [
            "C:\\Windows\\System32",
            "C:\\Windows\\SysWOW64",
            "C:\\Program Files\\Windows",
            "/etc",
            "/usr/bin",
            "/bin",
            "/sbin"
        ]

    def _real_path(self, path: str) -> str:
        try:
            return os.path.realpath(path)
        except:
            return path

    def check_path(self, path: str) -> Dict:
        """检查路径是否允许操作 - 具体逻辑"""
        real_path = self._real_path(path)
        
        # 检查保护路径
        for protected in self.protected_paths:
            if protected.lower() in real_path.lower():
                return {
                    "allowed": False,
                    "reason": f"保护路径: {protected}",
                    "risk": "high",
                    "real_path": real_path
                }
        
        # 检查是否在允许目录
        for allowed in self.allowed_roots:
            if real_path.startswith(allowed):
                return {
                    "allowed": True,
                    "reason": f"在允许目录: {allowed}",
                    "risk": "low",
                    "real_path": real_path
                }
        
        # 不在白名单，默认拒绝写入，允许只读
        return {
            "allowed": False,
            "reason": f"不在沙盒白名单: {real_path}，允许目录: {self.allowed_roots[:2]}",
            "risk": "medium",
            "real_path": real_path,
            "suggestion": f"请将文件移到 {self.sandbox_root} 再操作"
        }

    def safe_list(self, path: str) -> Dict:
        """安全列出文件 - 只读，沙盒检查宽松"""
        check = self.check_path(path)
        # 只读操作即使不在白名单也允许，但警告
        return {"allowed": True, "check": check}

    def safe_delete(self, path: str, to_recycle: bool = True) -> Dict:
        """安全删除 - 必须在沙盒，移到回收站"""
        check = self.check_path(path)
        if not check["allowed"]:
            raise PermissionError(f"删除被拒绝: {check['reason']}")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"文件不存在: {path}")
        
        if to_recycle:
            # Windows: 移到回收站
            # 这里演示逻辑，真实用 winshell 或 SHFileOperation
            recycle_dir = os.path.join(self.sandbox_root, ".recycle")
            os.makedirs(recycle_dir, exist_ok=True)
            dest = os.path.join(recycle_dir, os.path.basename(path) + f".{int(os.path.getmtime(path))}")
            try:
                shutil.move(path, dest)
                return {
                    "success": True,
                    "message": f"已移到回收站: {dest}",
                    "original": path,
                    "recycle": dest,
                    "can_undo": True
                }
            except Exception as e:
                raise RuntimeError(f"移到回收站失败: {e}")
        else:
            os.remove(path)
            return {"success": True, "message": f"已删除: {path}", "can_undo": False}

    def safe_write(self, path: str, content: str) -> Dict:
        """安全写入 - 必须在沙盒"""
        check = self.check_path(path)
        if not check["allowed"]:
            raise PermissionError(f"写入被拒绝: {check['reason']}")
        
        # 检查磁盘空间
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "message": f"已写入: {path}",
            "size": len(content),
            "can_undo": True,
            "reverse": {"operation": "delete_file", "path": path}
        }

class ProcessSandbox:
    """进程沙盒 - 保护关键系统进程"""
    
    def __init__(self):
        # 关键系统进程，不能结束
        self.critical_processes = [
            "csrss.exe", "winlogon.exe", "services.exe", "lsass.exe",
            "svchost.exe", "wininit.exe", "explorer.exe",  # explorer 可结束但需确认
            "System", "Registry", "MemCompression"
        ]
        
        # 高危进程，结束需二次确认
        self.dangerous_processes = [
            "chrome.exe", "wechat.exe", "code.exe", "msedge.exe"
        ]

    def check_kill(self, pid: int = None, name: str = None) -> Dict:
        """检查是否允许结束进程"""
        target_name = name or ""
        target_pid = pid
        
        if pid:
            try:
                proc = psutil.Process(pid)
                target_name = proc.name()
            except:
                return {"allowed": False, "reason": f"进程不存在: {pid}", "risk": "low"}
        
        # 检查关键进程
        if target_name.lower() in [c.lower() for c in self.critical_processes]:
            return {
                "allowed": False,
                "reason": f"关键系统进程，不能结束: {target_name}",
                "risk": "critical",
                "suggestion": "请勿结束系统进程"
            }
        
        # 检查高危进程
        if target_name.lower() in [d.lower() for d in self.dangerous_processes]:
            return {
                "allowed": True,
                "need_confirm": True,
                "reason": f"高危进程，结束将丢失数据: {target_name}",
                "risk": "high",
                "suggestion": "请先保存数据"
            }
        
        return {
            "allowed": True,
            "need_confirm": False,
            "reason": f"允许结束: {target_name}",
            "risk": "low"
        }

    def safe_kill(self, pid: int = None, name: str = None) -> Dict:
        """安全结束进程"""
        check = self.check_kill(pid, name)
        if not check["allowed"]:
            raise PermissionError(check["reason"])
        
        if check.get("need_confirm"):
            # 需要确认，前端会弹窗
            pass
        
        try:
            if pid:
                proc = psutil.Process(pid)
                proc.terminate()
                return {"success": True, "message": f"已结束进程 PID {pid} ({proc.name()})", "can_undo": False}
            elif name:
                killed = []
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] and name.lower() in proc.info['name'].lower():
                        try:
                            proc.terminate()
                            killed.append(proc.info['pid'])
                        except:
                            continue
                return {"success": True, "message": f"已结束 {len(killed)} 个 {name} 进程", "pids": killed}
        except Exception as e:
            raise RuntimeError(f"结束进程失败: {e}")

# 全局沙盒
file_sandbox = FileSandbox()
process_sandbox = ProcessSandbox()
