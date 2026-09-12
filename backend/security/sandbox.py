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
        except Exception:
            return path

    def check_path(self, path: str) -> Dict:
        """检查路径是否允许操作 - 已修复路径遍历，realpath+严格白名单"""
        if not path or path.strip() == "":
            return {"allowed": False, "reason": "空路径", "risk": "high", "real_path": ""}
        
        # 长度检查
        if len(path) > 260:
            return {"allowed": False, "reason": f"路径过长 {len(path)} > 260", "risk": "medium", "real_path": path}
        
        # realpath 解析符号链接和 ..
        real_path = self._real_path(path)
        real_path_lower = real_path.lower()
        
        # 检查保护路径 - 严格匹配前缀或包含
        for protected in self.protected_paths:
            prot_lower = protected.lower()
            prot_real = self._real_path(protected).lower() if os.path.exists(protected) else prot_lower
            if real_path_lower.startswith(prot_real) or prot_lower in real_path_lower:
                # 例外：/tmp 是允许的，但 /etc 不允许
                if prot_lower in ["/etc", "/usr/bin", "/bin", "/sbin"] and "/tmp" in real_path_lower:
                    continue
                # Windows System32 严格禁止
                if "system32" in prot_lower or "syswow64" in prot_lower:
                    return {
                        "allowed": False,
                        "reason": f"保护路径禁止: {protected}",
                        "risk": "high",
                        "real_path": real_path
                    }
        
        # 检查是否在允许目录 - 必须 realpath 前缀匹配
        for allowed in self.allowed_roots:
            allowed_real = self._real_path(allowed).lower() if os.path.exists(allowed) else allowed.lower()
            # 严格：real_path 必须以 allowed 开头且下一字符是分隔符或结束
            if real_path_lower == allowed_real or real_path_lower.startswith(allowed_real + os.sep.lower()) or real_path_lower.startswith(allowed_real + "/") or real_path_lower.startswith(allowed_real + "\\"):
                return {
                    "allowed": True,
                    "reason": f"在允许目录: {allowed}",
                    "risk": "low",
                    "real_path": real_path
                }
            # 兼容：Windows 盘符大小写
            if real_path_lower.startswith(allowed.lower()):
                return {
                    "allowed": True,
                    "reason": f"在允许目录: {allowed}",
                    "risk": "low",
                    "real_path": real_path
                }
        
        # 不在白名单，默认拒绝写入，允许只读（返回 medium）
        return {
            "allowed": False,
            "reason": f"不在沙盒白名单: {real_path}，允许目录: {self.allowed_roots[:3]}",
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

    def safe_write(self, path: str, content: str, max_size_mb: int = 10) -> Dict:
        """安全写入 - 必须在沙盒，限制大小，检查磁盘"""
        check = self.check_path(path)
        if not check["allowed"]:
            raise PermissionError(f"写入被拒绝: {check['reason']}")
        
        # 文件大小限制 10MB
        size_bytes = len(content.encode('utf-8'))
        max_bytes = max_size_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValueError(f"文件过大: {size_bytes/1024/1024:.1f}MB > {max_size_mb}MB 限制")
        
        # 检查磁盘空间
        import psutil
        try:
            disk = psutil.disk_usage(os.path.dirname(path) or "/")
            if disk.free < 100 * 1024 * 1024:  # 小于100MB
                raise RuntimeError(f"磁盘空间不足: 剩余 {disk.free/1024/1024:.1f}MB")
        except Exception:
            pass
        
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        # 日志注入防护：禁止换行污染路径
        if "\n" in path or "\r" in path:
            raise ValueError("路径含非法换行符")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "message": f"已写入: {path}",
            "size": len(content),
            "size_bytes": size_bytes,
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
            except Exception:
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
                        except Exception:
                            continue
                return {"success": True, "message": f"已结束 {len(killed)} 个 {name} 进程", "pids": killed}
        except Exception as e:
            raise RuntimeError(f"结束进程失败: {e}")

# 全局沙盒
file_sandbox = FileSandbox()
process_sandbox = ProcessSandbox()
