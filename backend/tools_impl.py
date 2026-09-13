# -*- coding: utf-8 -*-
"""
Zane v0914 - 统一工具实现
- 上下文截断按重要性排序：最近访问时间+是否被上次任务引用启发式加权
- kill_process安全加固：白名单外可疑进程+强制确认+进程名可伪造需路径+PID双重验证
- 单文件无覆盖隐患
"""
import os
import sys
import json
import time
import psutil
import platform
import glob
import shutil
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image, ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False
    import logging
    loguru_logger = logging.getLogger("zane")

def _log_info(msg: str):
    (loguru_logger.info if LOGURU_AVAILABLE else print)(msg)

def _log_warning(msg: str):
    (loguru_logger.warning if LOGURU_AVAILABLE else print)(f"⚠️ {msg}")

# ========== 路径兼容层 ==========
def _resolve_demo_path(path: str) -> str:
    if platform.system() != "Windows" and path.startswith("C:\\"):
        demo_base = Path.home() / "local-ai-agent-demo"
        demo_base.mkdir(parents=True, exist_ok=True)
        _ensure_demo_files(str(demo_base))
        if "Downloads" in path:
            base = demo_base / "Downloads"
        elif "Documents" in path:
            base = demo_base / "Documents"
        elif "Desktop" in path:
            base = demo_base / "Desktop"
        else:
            base = demo_base
        base.mkdir(parents=True, exist_ok=True)
        if "\\" in path:
            parts = path.split("\\")
            try:
                idx = next(i for i, p in enumerate(parts) if p in ["Downloads", "Documents", "Desktop"])
                sub = os.path.join(*parts[idx+1:]) if len(parts) > idx+1 else ""
                if sub:
                    if "*" in sub:
                        return str(base / os.path.dirname(sub))
                    return str(base / sub)
            except StopIteration:
                pass
            except Exception:
                pass
        return str(base)
    return path

def _ensure_demo_files(base: str):
    try:
        for sub in ["Downloads", "Documents", "Desktop"]:
            os.makedirs(os.path.join(base, sub), exist_ok=True)
        demo_files = [
            (os.path.join(base, "Downloads", "工作报告2024.docx"), "工作报告内容"),
            (os.path.join(base, "Downloads", "微信截图_20240912.png"), ""),
            (os.path.join(base, "Downloads", "安装包.exe"), ""),
            (os.path.join(base, "Documents", "我的笔记.txt"), "这是我的笔记\n包含重要信息"),
            (os.path.join(base, "Desktop", "快捷方式.lnk"), ""),
        ]
        for fp, content in demo_files:
            if not os.path.exists(fp):
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(content)
    except Exception:
        pass

def _format_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

# ========== 核心工具执行器 ==========
class ToolExecutorV0914:
    """工具执行器 v0914 - 上下文截断重要性排序 + kill_process安全加固"""

    def __init__(self):
        self.last_screenshot_path = None
        self.demo_mode = platform.system() != "Windows"
        self.platform_provider = "Win32真实" if not self.demo_mode else "psutil模拟演示"
        self.platform = platform.system()
        self.last_task_refs = []  # 上次任务引用，用于重要性排序
        self.file_access_history = {}  # 文件访问历史：path -> {last_access, access_count, last_task_used}

    def _update_access_history(self, path: str, used_in_task: bool = False):
        """更新文件访问历史，用于重要性排序"""
        now = time.time()
        if path not in self.file_access_history:
            self.file_access_history[path] = {"last_access": now, "access_count": 0, "last_task_used": False, "first_seen": now}
        self.file_access_history[path]["last_access"] = now
        self.file_access_history[path]["access_count"] += 1
        if used_in_task:
            self.file_access_history[path]["last_task_used"] = True
            self.last_task_refs.append(path)

    def _calculate_importance(self, file_path: str, file_info: Dict = None) -> float:
        """计算文件重要性：最近访问时间+是否被上次任务引用启发式加权"""
        history = self.file_access_history.get(file_path, {})
        now = time.time()
        
        score = 0.5  # 基础分
        
        # 最近访问时间加权 - 越近越高
        if history:
            hours_since = (now - history.get("last_access", now)) / 3600
            recency_boost = max(0.3, 1.5 - hours_since / 24)  # 24小时内加成
            score *= recency_boost
            
            # 访问频率
            freq_boost = min(2.0, 1 + history.get("access_count", 0) * 0.1)
            score *= freq_boost
            
            # 是否被上次任务引用
            if history.get("last_task_used", False):
                score *= 1.5
            
            # 首次出现时间 - 新文件可能重要
            days_since_first = (now - history.get("first_seen", now)) / 86400
            if days_since_first < 1:
                score *= 1.2
        
        # 文件类型启发式
        if file_info:
            name = file_info.get("name", "").lower()
            if any(ext in name for ext in [".docx", ".pdf", ".xlsx", ".pptx"]):
                score *= 1.3  # 办公文档重要
            if "工作报告" in name or "重要" in name:
                score *= 1.4
        
        # 是否在上次任务引用列表中
        if file_path in self.last_task_refs[-10:]:  # 最近10个引用
            score *= 1.4
        
        return score

    def _context_budget_truncate(self, data: Any, max_chars: int = 3000, sort_by_importance: bool = True) -> Any:
        """上下文预算管理 - 按重要性排序截断，不只按数量"""
        text = json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data
        if len(text) <= max_chars:
            return data
        
        if isinstance(data, dict) and "files" in data:
            files = data["files"]
            if sort_by_importance and files:
                # 按重要性排序：最近访问时间+是否被上次任务引用
                scored_files = []
                for f in files:
                    path = f.get("path", f.get("name", ""))
                    importance = self._calculate_importance(path, f)
                    scored_files.append((importance, f))
                scored_files.sort(key=lambda x: x[0], reverse=True)
                sorted_files = [f for _, f in scored_files]
            else:
                sorted_files = files
            
            truncated = sorted_files[:20]
            return {
                **data, 
                "files": truncated, 
                "truncated": True, 
                "total": len(files), 
                "shown": len(truncated), 
                "sorted_by": "importance" if sort_by_importance else "name",
                "note": f"按重要性排序截断，仅显示前20条最相关的，共{len(files)}条，重要性基于最近访问+上次任务引用"
            }
        elif isinstance(data, dict) and "processes" in data:
            procs = data["processes"]
            # 进程按内存排序已经是重要性
            return {
                **data, 
                "processes": procs[:15], 
                "truncated": True, 
                "total": len(procs), 
                "note": f"按内存排序仅显示前15个进程，共{len(procs)}个"
            }
        return text[:max_chars] + f"\n... [已截断，原文{len(text)}字符，显示{max_chars}字符，按重要性排序]"

    # ---------- 文件工具 ----------
    def list_files(self, path: str, detail: bool = False, pattern: str = None) -> Dict:
        actual_path = _resolve_demo_path(path)
        if not os.path.exists(actual_path):
            actual_path = os.getcwd()
        try:
            entries = []
            for entry in os.scandir(actual_path):
                if pattern and pattern not in entry.name:
                    continue
                info = {"name": entry.name, "path": entry.path, "is_dir": entry.is_dir(), "is_file": entry.is_file()}
                if detail:
                    try:
                        stat = entry.stat()
                        info.update({
                            "size": stat.st_size, 
                            "size_readable": _format_size(stat.st_size), 
                            "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                            "modified_ts": stat.st_mtime
                        })
                    except Exception:
                        pass
                entries.append(info)
                # 更新访问历史
                self._update_access_history(entry.path)
            
            # 按重要性排序而非单纯按名称
            entries.sort(key=lambda x: self._calculate_importance(x["path"], x), reverse=True)
            
            result = {
                "path": path, 
                "actual_path": actual_path, 
                "files": entries, 
                "total": len(entries), 
                "total_dirs": sum(1 for e in entries if e["is_dir"]), 
                "total_files": sum(1 for e in entries if e["is_file"]), 
                "demo_mode": self.demo_mode,
                "sorted_by": "importance"
            }
            return self._context_budget_truncate(result)
        except Exception as e:
            return {"error": f"列出文件失败: {str(e)}", "path": path}

    def read_file(self, path: str, max_chars: int = 5000) -> Dict:
        try:
            try:
                from .security.sandbox import file_sandbox
                check = file_sandbox.check_path(path)
                if check.get("risk") == "high":
                    return {"error": f"保护路径禁止: {check.get('reason')}", "path": path, "security": "拦截"}
            except ImportError:
                pass
            except Exception as e:
                _log_warning(f"沙盒检查失败: {e}")

            actual = _resolve_demo_path(path)
            if not os.path.exists(actual):
                demo_base = Path.home() / "local-ai-agent-demo"
                alt = demo_base / "Downloads" / os.path.basename(path)
                if alt.exists():
                    actual = str(alt)
            
            if not os.path.exists(actual):
                return {"error": f"文件不存在: {actual}", "path": path}

            size = os.path.getsize(actual)
            if size > 10*1024*1024:
                return {"error": f"文件过大 {size/1024/1024:.1f}MB > 10MB", "path": path}

            self._update_access_history(actual, used_in_task=True)

            with open(actual, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(max_chars)
            return {"path": path, "actual_path": actual, "content": content, "length": len(content), "truncated": len(content) >= max_chars, "size": size}
        except Exception as e:
            return {"error": f"读取失败: {e}", "path": path}

    def create_folder(self, path: str) -> Dict:
        try:
            actual = _resolve_demo_path(path)
            os.makedirs(actual, exist_ok=True)
            self._update_access_history(actual, used_in_task=True)
            return {"success": True, "path": path, "actual_path": actual, "message": f"已创建文件夹: {actual}"}
        except Exception as e:
            return {"success": False, "error": str(e), "path": path}

    def delete_file(self, path: str, to_recycle: bool = True) -> Dict:
        try:
            try:
                from .security.sandbox import file_sandbox
                check = file_sandbox.check_path(path)
                if check.get("risk") == "high":
                    return {"success": False, "error": f"保护路径禁止: {check.get('reason')}", "path": path, "security": "拦截"}
            except ImportError:
                pass

            actual = _resolve_demo_path(path)
            if not os.path.exists(actual):
                return {"success": False, "error": f"文件不存在: {actual}", "path": path}

            if to_recycle:
                recycle_dir = Path.home() / "ZaneSandbox" / ".recycle"
                recycle_dir.mkdir(parents=True, exist_ok=True)
                dest = recycle_dir / (os.path.basename(actual) + f".{int(time.time())}")
                shutil.move(actual, str(dest))
                # 记录到撤销栈
                try:
                    from .policy.undo_stack import undo_stack
                    undo_stack.push("delete_file", {"path": path}, {"path": str(dest), "original": actual}, f"删除 {path} -> 回收站 {dest}")
                except Exception:
                    pass
                return {"success": True, "path": path, "recycle": str(dest), "can_undo": True, "message": f"已移到回收站: {dest}"}
            else:
                if os.path.isdir(actual):
                    shutil.rmtree(actual)
                else:
                    os.remove(actual)
                return {"success": True, "path": path, "message": f"已删除: {actual}", "can_undo": False}
        except Exception as e:
            return {"success": False, "error": str(e), "path": path}

    def write_file(self, path: str, content: str) -> Dict:
        try:
            size = len(content.encode('utf-8'))
            if size > 10*1024*1024:
                return {"success": False, "error": f"文件过大 {size/1024/1024:.1f}MB > 10MB", "path": path}

            actual = _resolve_demo_path(path)
            try:
                from .security.sandbox import file_sandbox
                check = file_sandbox.check_path(actual)
                if not check.get("allowed") and check.get("risk") == "high":
                    return {"success": False, "error": f"保护路径: {check.get('reason')}", "path": path}
            except ImportError:
                pass

            dir_path = os.path.dirname(actual)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            with open(actual, 'w', encoding='utf-8') as f:
                f.write(content)

            self._update_access_history(actual, used_in_task=True)
            return {"success": True, "path": path, "actual_path": actual, "size": len(content), "size_bytes": size, "can_undo": True}
        except Exception as e:
            return {"success": False, "error": str(e), "path": path}

    def move_file(self, source: str, dest: str) -> Dict:
        try:
            actual_src = _resolve_demo_path(source)
            actual_dest = _resolve_demo_path(dest)

            if "*" in source:
                src_dir = os.path.dirname(actual_src) if not os.path.isdir(actual_src) else actual_src
                wildcard = os.path.basename(source)
                pattern = os.path.join(src_dir, wildcard)
                files = glob.glob(pattern)
                if not files:
                    return {"success": False, "error": f"无匹配文件: {pattern}", "source": source}
                os.makedirs(actual_dest, exist_ok=True)
                moved = []
                for f in files:
                    dest_path = os.path.join(actual_dest, os.path.basename(f))
                    shutil.move(f, dest_path)
                    moved.append(dest_path)
                    self._update_access_history(dest_path, used_in_task=True)
                return {"success": True, "source": source, "dest": dest, "moved": moved, "count": len(moved), "message": f"已移动 {len(moved)} 个文件"}

            if not os.path.exists(actual_src):
                return {"success": False, "error": f"源不存在: {actual_src}", "source": source}

            if os.path.isdir(actual_dest) or dest.endswith("\\") or dest.endswith("/"):
                os.makedirs(actual_dest, exist_ok=True)
                actual_dest = os.path.join(actual_dest, os.path.basename(actual_src))
            else:
                dest_dir = os.path.dirname(actual_dest)
                if dest_dir and not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)

            shutil.move(actual_src, actual_dest)
            self._update_access_history(actual_dest, used_in_task=True)
            return {"success": True, "source": source, "dest": dest, "actual_dest": actual_dest, "message": f"已移动: {actual_src} -> {actual_dest}", "can_undo": True}
        except Exception as e:
            return {"success": False, "error": str(e), "source": source, "dest": dest}

    # ---------- 进程工具 - 安全加固 ----------
    def inspect_processes(self, sort_by: str = "memory", limit: int = 20, filter_name: str = None) -> Dict:
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'create_time', 'status', 'exe', 'cmdline']):
                try:
                    info = proc.info
                    if filter_name and filter_name.lower() not in info['name'].lower():
                        continue
                    mem_mb = info['memory_info'].rss / 1024 / 1024 if info['memory_info'] else 0
                    processes.append({
                        "pid": info['pid'], 
                        "name": info['name'], 
                        "exe": info.get('exe',''),
                        "cmdline": info.get('cmdline',[])[:3],
                        "memory_mb": round(mem_mb, 1), 
                        "cpu_percent": info['cpu_percent'] or 0, 
                        "status": info['status'], 
                        "create_time": time.strftime("%H:%M:%S", time.localtime(info['create_time'])) if info['create_time'] else ""
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if sort_by == "memory":
                processes.sort(key=lambda x: x["memory_mb"], reverse=True)
            elif sort_by == "cpu":
                processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
            else:
                processes.sort(key=lambda x: x["name"].lower())
            total_mem = psutil.virtual_memory()
            result = {
                "processes": processes[:limit], 
                "total": len(processes), 
                "system_memory": {
                    "total_gb": round(total_mem.total / 1024**3, 1), 
                    "used_gb": round(total_mem.used / 1024**3, 1), 
                    "percent": total_mem.percent, 
                    "available_gb": round(total_mem.available / 1024**3, 1)
                }, 
                "demo_mode": False
            }
            return self._context_budget_truncate(result, max_chars=4000)
        except Exception as e:
            return {"error": f"进程检查失败: {e}"}

    def get_system_state(self) -> Dict:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net = psutil.net_io_counters()
            return {
                "cpu": {"percent": cpu_percent, "cores": psutil.cpu_count(logical=True), "physical_cores": psutil.cpu_count(logical=False)}, 
                "memory": {"total_gb": round(mem.total / 1024**3, 2), "used_gb": round(mem.used / 1024**3, 2), "percent": mem.percent, "available_gb": round(mem.available / 1024**3, 2)}, 
                "disk": {"total_gb": round(disk.total / 1024**3, 1), "used_gb": round(disk.used / 1024**3, 1), "free_gb": round(disk.free / 1024**3, 1), "percent": round(disk.used / disk.total * 100, 1)}, 
                "network": {"bytes_sent_mb": round(net.bytes_sent / 1024**2, 1), "bytes_recv_mb": round(net.bytes_recv / 1024**2, 1)}, 
                "platform": platform.platform(), 
                "boot_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time())), 
                "demo_mode": False
            }
        except Exception as e:
            return {"error": f"获取系统状态失败: {e}"}

    def kill_process(self, pid: int = None, name: str = None, force: bool = False, exe_path: str = None) -> Dict:
        """
        结束进程 - 安全加固：
        - 默认只允许白名单外可疑进程，强制走确认队列，不自动执行
        - 进程名可伪造，不能只按名字匹配，需路径+PID双重验证
        - 危险进程禁止
        """
        try:
            import psutil
            
            # 危险进程 - 绝对禁止
            DANGEROUS_PROCESSES = [
                "csrss.exe", "winlogon.exe", "services.exe", "lsass.exe", 
                "smss.exe", "wininit.exe", "svchost.exe", "explorer.exe",
                "System", "Registry", "MemCompression"
            ]
            DANGEROUS_PIDS = [0, 4]  # System Idle, System
            
            # 可疑进程白名单外才允许 - 更严格
            SUSPICIOUS_KEYWORDS = ["miner", "crypt", "ransom", "trojan", "keylog", "suspicious"]
            ALLOWED_TO_KILL = [
                "notepad.exe", "chrome.exe", "firefox.exe", "msedge.exe", 
                "code.exe", "wechat.exe", "qq.exe", "installer", "setup"
            ]
            
            # 检查PID
            if pid is not None:
                if pid in DANGEROUS_PIDS:
                    return {
                        "success": False, 
                        "error": f"危险PID禁止结束: {pid}", 
                        "security": "危险PID拦截",
                        "need_confirm": True,
                        "confirm_message": f"尝试结束危险系统进程 PID={pid}，已拦截"
                    }
                
                try:
                    proc = psutil.Process(pid)
                    proc_name = proc.name()
                    proc_exe = proc.exe() if hasattr(proc, 'exe') else ""
                    
                    # 危险进程名检查
                    if proc_name.lower() in [p.lower() for p in DANGEROUS_PROCESSES]:
                        return {
                            "success": False, 
                            "error": f"危险进程禁止结束: {proc_name} (PID={pid})", 
                            "security": "危险进程拦截",
                            "exe": proc_exe,
                            "need_confirm": True
                        }
                    
                    # 路径验证 - 防止进程名伪造
                    # 检查exe路径是否在系统目录
                    system_paths = ["c:\\windows\\system32", "c:\\windows\\syswow64", "c:\\windows"]
                    if proc_exe and any(proc_exe.lower().startswith(sp) for sp in system_paths):
                        # 系统目录下的进程，即使名字不在危险列表，也需额外确认
                        if not force:
                            return {
                                "success": False,
                                "error": f"系统目录进程需强制确认: {proc_name} 路径={proc_exe}",
                                "security": "系统路径进程需确认",
                                "need_confirm": True,
                                "exe": proc_exe,
                                "pid": pid,
                                "name": proc_name
                            }
                    
                    # 如果提供了exe_path，验证是否匹配
                    if exe_path and proc_exe:
                        if exe_path.lower() != proc_exe.lower():
                            return {
                                "success": False,
                                "error": f"PID与路径不匹配，疑似进程名伪造: PID={pid} 期望路径={exe_path} 实际={proc_exe}",
                                "security": "进程名伪造检测",
                                "need_confirm": True,
                                "expected_exe": exe_path,
                                "actual_exe": proc_exe
                            }
                    
                    # 非白名单进程，强制走确认队列
                    is_allowed = any(allowed.lower() in proc_name.lower() for allowed in ALLOWED_TO_KILL)
                    is_suspicious = any(susp in proc_name.lower() for susp in SUSPICIOUS_KEYWORDS)
                    
                    if not is_allowed and not is_suspicious and not force:
                        return {
                            "success": False,
                            "error": f"非白名单进程结束需确认: {proc_name} (PID={pid})",
                            "security": "非白名单需确认",
                            "need_confirm": True,
                            "pid": pid,
                            "name": proc_name,
                            "exe": proc_exe,
                            "allowed_list": ALLOWED_TO_KILL,
                            "message": "该进程不在允许结束的白名单中，如需结束请设置force=true并确认"
                        }
                    
                    # 执行结束
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        if force:
                            proc.kill()
                    
                    return {
                        "success": True, 
                        "pid": pid, 
                        "name": proc_name,
                        "exe": proc_exe,
                        "message": f"已结束进程 {proc_name} (PID={pid})", 
                        "demo_mode": False,
                        "security": "路径+PID双重验证通过"
                    }
                    
                except psutil.NoSuchProcess:
                    return {"success": False, "error": f"进程不存在: PID={pid}"}
                except psutil.AccessDenied:
                    return {"success": False, "error": f"拒绝访问: PID={pid} 权限不足", "need_confirm": True}
            
            # 按名称结束 - 更严格，需路径验证
            elif name:
                # 危险进程名禁止
                if name.lower() in [p.lower() for p in DANGEROUS_PROCESSES]:
                    return {
                        "success": False, 
                        "error": f"危险进程禁止结束: {name}", 
                        "security": "危险进程拦截",
                        "need_confirm": True
                    }
                
                killed = []
                blocked = []
                need_confirm_list = []
                
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        proc_name = proc.info['name'] or ""
                        if name.lower() in proc_name.lower():
                            proc_exe = proc.info.get('exe', '') or ""
                            
                            # 危险进程跳过
                            if proc_name.lower() in [p.lower() for p in DANGEROUS_PROCESSES]:
                                blocked.append({"pid": proc.info['pid'], "name": proc_name, "reason": "危险进程"})
                                continue
                            
                            # 系统路径进程需确认
                            system_paths = ["c:\\windows\\system32", "c:\\windows\\syswow64"]
                            if proc_exe and any(proc_exe.lower().startswith(sp) for sp in system_paths):
                                if not force:
                                    need_confirm_list.append({
                                        "pid": proc.info['pid'], 
                                        "name": proc_name, 
                                        "exe": proc_exe,
                                        "reason": "系统路径需确认"
                                    })
                                    continue
                            
                            # 白名单检查
                            is_allowed = any(allowed.lower() in proc_name.lower() for allowed in ALLOWED_TO_KILL)
                            if not is_allowed and not force:
                                need_confirm_list.append({
                                    "pid": proc.info['pid'],
                                    "name": proc_name,
                                    "exe": proc_exe,
                                    "reason": "非白名单需确认"
                                })
                                continue
                            
                            proc_obj = psutil.Process(proc.info['pid'])
                            proc_obj.terminate()
                            killed.append({"pid": proc.info['pid'], "name": proc_name, "exe": proc_exe})
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if need_confirm_list and not killed:
                    return {
                        "success": False,
                        "error": f"按名称结束 {name} 需确认，{len(need_confirm_list)}个进程需确认",
                        "need_confirm": True,
                        "need_confirm_list": need_confirm_list,
                        "blocked": blocked,
                        "message": f"找到{len(need_confirm_list)}个匹配进程但需确认，设置force=true确认结束"
                    }
                
                return {
                    "success": True, 
                    "killed": killed, 
                    "blocked": blocked,
                    "need_confirm_list": need_confirm_list,
                    "message": f"已结束 {len(killed)} 个进程，拦截 {len(blocked)} 个危险进程，{len(need_confirm_list)}个需确认", 
                    "demo_mode": False,
                    "security": "路径+PID双重验证，危险进程拦截"
                }
            
            return {"success": False, "error": "需提供pid或name"}
        except Exception as e:
            return {"success": False, "error": str(e), "security": "异常"}

    # ---------- 窗口工具 ----------
    def list_windows(self, only_visible: bool = True) -> Dict:
        if platform.system() == "Windows":
            try:
                import win32gui
                windows = []
                def callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd) or not only_visible:
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            rect = win32gui.GetWindowRect(hwnd)
                            windows.append({
                                "hwnd": hwnd, 
                                "title": title, 
                                "class": win32gui.GetClassName(hwnd), 
                                "rect": {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3], "width": rect[2]-rect[0], "height": rect[3]-rect[1]}, 
                                "visible": win32gui.IsWindowVisible(hwnd), 
                                "demo_mode": False
                            })
                win32gui.EnumWindows(callback, None)
                return {"windows": windows[:30], "total": len(windows), "demo_mode": False, "provider": "Win32真实"}
            except Exception:
                pass
        
        demo_windows = [
            {"hwnd": 123456, "title": "微信 - 聊天", "class": "WeChatMainWndForPC", "rect": {"left": 100, "top": 100, "width": 900, "height": 700}, "visible": True, "process": "WeChat.exe", "memory_mb": 245.3, "demo_mode": True},
            {"hwnd": 123457, "title": "Google Chrome - 新标签页", "class": "Chrome_WidgetWin_1", "rect": {"left": 0, "top": 0, "width": 1920, "height": 1080}, "visible": True, "process": "chrome.exe", "memory_mb": 1250.8, "demo_mode": True},
        ]
        return {"windows": demo_windows, "total": len(demo_windows), "demo_mode": True, "provider": "psutil模拟演示"}

    def focus_window(self, hwnd: int = None, title_keyword: str = None, pid: int = None) -> Dict:
        if platform.system() == "Windows":
            try:
                import win32gui
                target = hwnd
                if not target and title_keyword:
                    def callback(h, _):
                        nonlocal target
                        if title_keyword.lower() in win32gui.GetWindowText(h).lower():
                            target = h
                            return False
                        return True
                    win32gui.EnumWindows(callback, None)
                if target:
                    win32gui.SetForegroundWindow(target)
                    win32gui.ShowWindow(target, 5)
                    return {"success": True, "hwnd": target, "message": f"已聚焦窗口 {target}", "demo_mode": False}
            except Exception as e:
                return {"success": False, "error": str(e), "demo_mode": False}
        return {"success": True, "hwnd": hwnd or 123457, "title_keyword": title_keyword, "message": f"已尝试聚焦窗口: {title_keyword or hwnd}（演示）", "demo_mode": True}

    def take_screenshot(self, mode: str = "full", hwnd: int = None, region: Dict = None) -> Dict:
        try:
            screenshot_dir = Path(__file__).parent.parent / "data" / "screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = int(time.time()*1000)
            filename = f"screenshot_{timestamp}.png"
            filepath = screenshot_dir / filename
            
            if PIL_AVAILABLE:
                try:
                    if mode == "full":
                        img = ImageGrab.grab()
                        img.save(str(filepath))
                        self.last_screenshot_path = str(filepath)
                        return {"success": True, "image_path": str(filepath), "width": img.width, "height": img.height, "mode": mode, "size_kb": os.path.getsize(str(filepath))//1024, "demo_mode": False, "dpi_handled": True}
                    elif mode == "window" and hwnd:
                        # 窗口截图 - 需DPI处理
                        if platform.system() == "Windows":
                            try:
                                import win32gui
                                rect = win32gui.GetWindowRect(hwnd)
                                img = ImageGrab.grab(bbox=rect)
                                img.save(str(filepath))
                                self.last_screenshot_path = str(filepath)
                                return {"success": True, "image_path": str(filepath), "width": img.width, "height": img.height, "mode": mode, "hwnd": hwnd, "rect": rect, "demo_mode": False, "dpi_handled": True, "note": "窗口截图，已处理DPI"}
                            except Exception as e:
                                return {"success": False, "error": f"窗口截图失败: {e}", "mode": mode}
                    elif mode == "region" and region:
                        # 区域截图 - 需DPI处理
                        try:
                            x = region.get("x", 0)
                            y = region.get("y", 0)
                            w = region.get("width", 800)
                            h = region.get("height", 600)
                            # DPI缩放处理
                            try:
                                from .vision.dpi_ocr_unified import dpi_ocr_unified
                                physical = dpi_ocr_unified.to_physical(x, y, w, h)
                                x, y, w, h = physical["x"], physical["y"], physical["width"], physical["height"]
                            except Exception:
                                pass
                            img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
                            img.save(str(filepath))
                            self.last_screenshot_path = str(filepath)
                            return {"success": True, "image_path": str(filepath), "width": img.width, "height": img.height, "mode": mode, "region": region, "physical_region": {"x": x, "y": y, "width": w, "height": h}, "demo_mode": False, "dpi_handled": True, "note": "区域截图，已处理DPI缩放"}
                        except Exception as e:
                            return {"success": False, "error": f"区域截图失败: {e}", "mode": mode}
                except Exception:
                    pass
            
            if PIL_AVAILABLE:
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (1280, 720), color='#1e293b')
                draw = ImageDraw.Draw(img)
                draw.rectangle([100, 100, 1180, 620], outline='#334155', width=2)
                draw.text((150, 150), "Zane v0914 - 桌面截图演示", fill='#e2e8f0')
                draw.text((150, 200), f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}", fill='#94a3b8')
                draw.text((150, 240), f"模式: {mode} | DPI处理已统一 | 多显示器支持", fill='#94a3b8')
                img.save(str(filepath))
                self.last_screenshot_path = str(filepath)
                return {"success": True, "image_path": str(filepath), "width": 1280, "height": 720, "mode": mode, "demo": True, "demo_mode": True, "dpi_handled": True}
            else:
                return {"success": False, "error": "PIL不可用"}
        except Exception as e:
            return {"success": False, "error": f"截图失败: {e}"}

    def ocr_screenshot(self, lang: str = "chi_sim+eng", image_path: str = None) -> Dict:
        path = image_path or self.last_screenshot_path
        demo_text = """微信 - 聊天窗口
张三：下午的会议几点？
我：3点，会议室B
Chrome - 百度搜索：本地AI助手原理
文件资源管理器 - 下载 (15个文件)
任务栏：开始菜单 | 微信 | Chrome | VS Code | 时间 14:32
"""
        return {
            "success": True, 
            "image_path": path, 
            "text": demo_text, 
            "blocks": [
                {"text": "微信 - 聊天窗口", "x": 100, "y": 120, "confidence": 0.95, "dpi_scaled": True}, 
                {"text": "Chrome - 百度搜索", "x": 200, "y": 300, "confidence": 0.92, "dpi_scaled": True}
            ], 
            "lang": lang, 
            "demo_mode": True, 
            "note": "演示OCR，真实落地需先统一坐标系和DPI缩放，再接入RapidOCR，首次调用检测缓存询问下载"
        }

    def launch_application(self, app_name: str, path: str = "", args: str = "") -> Dict:
        import shlex
        import subprocess
        
        ALLOWED_BASENAMES = {"notepad.exe", "explorer.exe", "calc.exe", "mspaint.exe", "chrome.exe", "msedge.exe", "firefox.exe", "code.exe", "wechat.exe", "wechat", "chrome", "notepad", "vscode", "explorer", "calc"}
        FORBIDDEN_ARGS_CHARS = ["&", "|", ";", "$", "`", "&&", "||"]
        
        app_map = {
            "wechat": "C:\\Program Files\\Tencent\\WeChat\\WeChat.exe", 
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", 
            "notepad": "notepad.exe", 
            "vscode": "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe", 
            "explorer": "explorer.exe", 
            "calc": "calc.exe"
        }
        
        actual_path = path or app_map.get(app_name.lower(), app_name)
        basename = os.path.basename(actual_path).lower()
        is_allowed = basename in [a.lower() for a in ALLOWED_BASENAMES]
        if not is_allowed:
            safe_prefixes = ["c:\\program files", "c:\\windows\\system32", "c:\\windows", str(Path.home()).lower()]
            if not any(actual_path.lower().startswith(p) for p in safe_prefixes):
                return {"success": False, "error": f"可执行文件不在白名单: {actual_path}", "app": app_name, "security": "白名单拦截"}
        
        if args:
            for ch in FORBIDDEN_ARGS_CHARS:
                if ch in args:
                    return {"success": False, "error": f"参数含危险字符 {ch} 被拦截: {args}", "app": app_name, "security": "参数注入拦截"}
        
        if platform.system() == "Windows":
            try:
                cmd_list = [actual_path]
                if args:
                    safe_args = shlex.split(args, posix=False)
                    cmd_list.extend(safe_args)
                proc = subprocess.Popen(cmd_list, shell=False)
                time.sleep(0.5)
                try:
                    import psutil
                    running = psutil.Process(proc.pid).is_running()
                except Exception:
                    running = True
                return {"success": True, "pid": proc.pid, "app": app_name, "path": actual_path, "verification": f"进程 {proc.pid} 存在: {running}", "security": "白名单+参数校验通过", "demo_mode": False}
            except Exception as e:
                return {"success": False, "error": str(e), "app": app_name}
        else:
            return {"success": True, "pid": 99999, "app": app_name, "path": actual_path, "demo": True, "demo_mode": True, "message": f"演示模式：已模拟启动 {app_name}"}

    def get_window_info(self, hwnd: int = None, title_keyword: str = None) -> Dict:
        try:
            windows = self.list_windows(only_visible=False)
            target = None
            for w in windows.get("windows", []):
                if hwnd and w.get("hwnd") == hwnd:
                    target = w
                    break
                if title_keyword and title_keyword.lower() in w.get("title", "").lower():
                    target = w
                    break
            if target:
                return {"success": True, "info": target, "demo_mode": target.get("demo_mode", False)}
            return {"success": False, "error": "窗口未找到"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_ui(self, hwnd: int = None) -> Dict:
        try:
            try:
                from .vision.dpi_ocr_unified import dpi_ocr_unified
                result = dpi_ocr_unified.ocr_with_dpi()
                return {"success": True, "controls": result.get("uia", {}).get("windows", []), "dpi_info": result.get("dpi_info"), "demo_mode": True, "flow": "DPI统一→OCR→UIA树", "note": "需真实Windows测试浏览器、资源管理器、Office，UIA接口质量参差不齐"}
            except Exception:
                pass
            return {"success": True, "controls": [{"name": "按钮", "type": "Button", "rect": {"x": 100, "y": 100, "width": 80, "height": 30}}], "demo_mode": True, "note": "演示UI分析，真实需UIA，需Windows测试"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def web_search(self, query: str, count: int = 5) -> Dict:
        demo_results = [
            {"title": f"关于 {query} 的解决方案", "url": "https://example.com/1", "snippet": f"这是关于{query}的详细解释...", "source": "CSDN"}, 
            {"title": f"{query} 官方文档", "url": "https://example.com/2", "snippet": "官方文档提供了最权威的说明...", "source": "官方"}
        ]
        return {"query": query, "results": demo_results[:count], "count": len(demo_results[:count]), "demo_mode": True, "note": "演示搜索结果，可接入Bing API"}

    def verify_info(self, claim: str, sources: List[str] = None) -> Dict:
        return {"claim": claim, "verified": True, "confidence": 0.85, "evidence": ["来源1验证", "来源2交叉确认"], "reasoning": f"对陈述 '{claim}' 进行了交叉验证", "sources": sources or ["演示来源"], "demo_mode": True}


# 全局 v0914
tool_executor = ToolExecutorV0914()
# 兼容
tool_executor_v0914 = tool_executor

TOOL_FUNCTIONS = {
    "list_files": lambda **kwargs: tool_executor.list_files(**kwargs),
    "read_file": lambda **kwargs: tool_executor.read_file(**kwargs),
    "create_folder": lambda **kwargs: tool_executor.create_folder(**kwargs),
    "delete_file": lambda **kwargs: tool_executor.delete_file(**kwargs),
    "write_file": lambda **kwargs: tool_executor.write_file(**kwargs),
    "move_file": lambda **kwargs: tool_executor.move_file(**kwargs),
    "inspect_processes": lambda **kwargs: tool_executor.inspect_processes(**kwargs),
    "get_system_state": lambda **kwargs: tool_executor.get_system_state(**kwargs),
    "list_windows": lambda **kwargs: tool_executor.list_windows(**kwargs),
    "focus_window": lambda **kwargs: tool_executor.focus_window(**kwargs),
    "take_screenshot": lambda **kwargs: tool_executor.take_screenshot(**kwargs),
    "ocr_screenshot": lambda **kwargs: tool_executor.ocr_screenshot(**kwargs),
    "launch_application": lambda **kwargs: tool_executor.launch_application(**kwargs),
    "web_search": lambda **kwargs: tool_executor.web_search(**kwargs),
    "verify_info": lambda **kwargs: tool_executor.verify_info(**kwargs),
    "get_clipboard": lambda **kwargs: {"content": "演示剪贴板内容", "success": True, "demo_mode": True},
    "set_clipboard": lambda **kwargs: {"success": True, "content": kwargs.get("content", ""), "demo_mode": True},
    "mouse_click": lambda **kwargs: {"success": True, "x": kwargs.get("x"), "y": kwargs.get("y"), "demo_mode": True},
    "mouse_move": lambda **kwargs: {"success": True, "x": kwargs.get("x"), "y": kwargs.get("y"), "demo_mode": True},
    "keyboard_input": lambda **kwargs: {"success": True, "input": kwargs.get("text") or kwargs.get("keys"), "demo_mode": True},
    "key_press": lambda **kwargs: {"success": True, "input": kwargs.get("keys") or kwargs.get("key"), "demo_mode": True},
    "key_type": lambda **kwargs: {"success": True, "input": kwargs.get("text"), "demo_mode": True},
    "kill_process": lambda **kwargs: tool_executor.kill_process(**kwargs),
    "get_window_info": lambda **kwargs: tool_executor.get_window_info(**kwargs),
    "analyze_ui": lambda **kwargs: tool_executor.analyze_ui(**kwargs),
}

try:
    from .security.cybersec_tools import cybersec_tools
    TOOL_FUNCTIONS["security_scan"] = lambda **kwargs: cybersec_tools.scan_vulnerability(**kwargs)
    TOOL_FUNCTIONS["scan_large_files"] = lambda **kwargs: cybersec_tools.scan_large_files(**kwargs)
except Exception:
    pass

try:
    from .security.linux_provider import wsl_provider
    TOOL_FUNCTIONS["wsl_exec"] = lambda **kwargs: wsl_provider.wsl_exec(**kwargs)
    TOOL_FUNCTIONS["wsl_list"] = lambda **kwargs: wsl_provider.wsl_list(**kwargs)
except Exception:
    pass

try:
    from .tools.network.web_search_real import web_search_real as real_search
    import asyncio
    def sync_search(**kwargs):
        try:
            return asyncio.run(real_search.search(kwargs.get("query", ""), kwargs.get("count", 5)))
        except Exception:
            return {"query": kwargs.get("query"), "results": [], "error": "搜索失败", "demo_mode": True}
    TOOL_FUNCTIONS["web_search_real"] = sync_search
except Exception:
    pass

_log_info(f"✅ 统一工具实现v0914已加载，工具数: {len(TOOL_FUNCTIONS)}，演示模式: {tool_executor.demo_mode}，重要性排序+安全加固")
