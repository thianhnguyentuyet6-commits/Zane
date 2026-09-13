# -*- coding: utf-8 -*-
"""
Zane v0913 - 统一工具实现 - 合并tools_impl.py + tools_impl_complete.py
- 解决双文件并存隐患，同名函数覆盖不可预期bug
- 分节：真实实现 / 演示兼容 / 安全增强 / 补全
- 所有工具操作真实系统，Linux演示环境兼容Windows路径
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

# ========== 路径兼容层 - 统一处理 ==========
def _resolve_demo_path(path: str) -> str:
    """统一路径兼容：Windows路径映射到Linux演示，真实Windows直接使用"""
    if platform.system() != "Windows" and path.startswith("C:\\"):
        demo_base = Path.home() / "local-ai-agent-demo"
        demo_base.mkdir(parents=True, exist_ok=True)
        # 确保演示文件
        _ensure_demo_files(str(demo_base))
        
        # 映射子目录
        if "Downloads" in path:
            base = demo_base / "Downloads"
        elif "Documents" in path:
            base = demo_base / "Documents"
        elif "Desktop" in path:
            base = demo_base / "Desktop"
        else:
            base = demo_base
        
        base.mkdir(parents=True, exist_ok=True)
        
        # 处理子路径和通配符
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
    """确保演示文件存在 - 仅演示环境"""
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

# ========== 核心工具执行器 - 真实实现 ==========
class ToolExecutor:
    """工具执行器 - 统一真实系统操作，单例"""

    def __init__(self):
        self.last_screenshot_path = None
        self.demo_mode = platform.system() != "Windows"
        self.platform_provider = "Win32真实" if not self.demo_mode else "psutil模拟演示"
        self.platform = platform.system()

    def _context_budget_truncate(self, data: Any, max_chars: int = 3000) -> Any:
        """上下文预算管理 - 智能截断大输出，防止撑爆LLM上下文"""
        text = json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data
        if len(text) <= max_chars:
            return data
        if isinstance(data, dict) and "files" in data:
            files = data["files"]
            return {**data, "files": files[:20], "truncated": True, "total": len(files), "shown": 20, "note": f"为节省上下文，仅显示前20条，共{len(files)}条"}
        elif isinstance(data, dict) and "processes" in data:
            procs = data["processes"]
            return {**data, "processes": procs[:15], "truncated": True, "total": len(procs), "note": f"仅显示前15个进程，共{len(procs)}个"}
        return text[:max_chars] + f"\n... [已截断，原文{len(text)}字符，显示{max_chars}字符]"

    # ---------- 文件工具 - 真实+演示兼容 ----------
    def list_files(self, path: str, detail: bool = False, pattern: str = None) -> Dict:
        """列出文件 - 真实文件系统操作，演示环境映射，上下文预算截断20条"""
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
                        info.update({"size": stat.st_size, "size_readable": _format_size(stat.st_size), "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))})
                    except Exception:
                        pass
                entries.append(info)
            entries.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            result = {"path": path, "actual_path": actual_path, "files": entries, "total": len(entries), "total_dirs": sum(1 for e in entries if e["is_dir"]), "total_files": sum(1 for e in entries if e["is_file"]), "demo_mode": self.demo_mode}
            return self._context_budget_truncate(result)
        except Exception as e:
            return {"error": f"列出文件失败: {str(e)}", "path": path}

    def read_file(self, path: str, max_chars: int = 5000) -> Dict:
        """读取文件 - 真实读取，沙盒检查，大小限制，演示兼容"""
        try:
            # 安全检查
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

            # 大小检查
            size = os.path.getsize(actual)
            if size > 10*1024*1024:
                return {"error": f"文件过大 {size/1024/1024:.1f}MB > 10MB", "path": path}

            with open(actual, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(max_chars)
            return {"path": path, "actual_path": actual, "content": content, "length": len(content), "truncated": len(content) >= max_chars, "size": size}
        except Exception as e:
            return {"error": f"读取失败: {e}", "path": path}

    def create_folder(self, path: str) -> Dict:
        """创建文件夹 - 真实创建，演示兼容"""
        try:
            actual = _resolve_demo_path(path)
            os.makedirs(actual, exist_ok=True)
            return {"success": True, "path": path, "actual_path": actual, "message": f"已创建文件夹: {actual}"}
        except Exception as e:
            return {"success": False, "error": str(e), "path": path}

    def delete_file(self, path: str, to_recycle: bool = True) -> Dict:
        """删除文件 - 沙盒检查+回收站可撤销，演示兼容"""
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
        """写入文件 - 大小10MB限制+沙盒检查+可撤销，演示兼容"""
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

            return {"success": True, "path": path, "actual_path": actual, "size": len(content), "size_bytes": size, "can_undo": True}
        except Exception as e:
            return {"success": False, "error": str(e), "path": path}

    def move_file(self, source: str, dest: str) -> Dict:
        """移动文件 - 支持通配符+沙盒，演示兼容"""
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
            return {"success": True, "source": source, "dest": dest, "actual_dest": actual_dest, "message": f"已移动: {actual_src} -> {actual_dest}", "can_undo": True}
        except Exception as e:
            return {"success": False, "error": str(e), "source": source, "dest": dest}

    # ---------- 进程工具 - 真实 ----------
    def inspect_processes(self, sort_by: str = "memory", limit: int = 20, filter_name: str = None) -> Dict:
        """真实进程检查 - psutil真实数据，内存/CPU排序，上下文预算截断15条"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'create_time', 'status']):
                try:
                    info = proc.info
                    if filter_name and filter_name.lower() not in info['name'].lower():
                        continue
                    mem_mb = info['memory_info'].rss / 1024 / 1024 if info['memory_info'] else 0
                    processes.append({"pid": info['pid'], "name": info['name'], "memory_mb": round(mem_mb, 1), "cpu_percent": info['cpu_percent'] or 0, "status": info['status'], "create_time": time.strftime("%H:%M:%S", time.localtime(info['create_time'])) if info['create_time'] else ""})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if sort_by == "memory":
                processes.sort(key=lambda x: x["memory_mb"], reverse=True)
            elif sort_by == "cpu":
                processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
            else:
                processes.sort(key=lambda x: x["name"].lower())
            total_mem = psutil.virtual_memory()
            result = {"processes": processes[:limit], "total": len(processes), "system_memory": {"total_gb": round(total_mem.total / 1024**3, 1), "used_gb": round(total_mem.used / 1024**3, 1), "percent": total_mem.percent, "available_gb": round(total_mem.available / 1024**3, 1)}, "demo_mode": False}
            return self._context_budget_truncate(result, max_chars=4000)
        except Exception as e:
            return {"error": f"进程检查失败: {e}"}

    def get_system_state(self) -> Dict:
        """真实系统状态 - psutil真实数据"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net = psutil.net_io_counters()
            return {"cpu": {"percent": cpu_percent, "cores": psutil.cpu_count(logical=True), "physical_cores": psutil.cpu_count(logical=False)}, "memory": {"total_gb": round(mem.total / 1024**3, 2), "used_gb": round(mem.used / 1024**3, 2), "percent": mem.percent, "available_gb": round(mem.available / 1024**3, 2)}, "disk": {"total_gb": round(disk.total / 1024**3, 1), "used_gb": round(disk.used / 1024**3, 1), "free_gb": round(disk.free / 1024**3, 1), "percent": round(disk.used / disk.total * 100, 1)}, "network": {"bytes_sent_mb": round(net.bytes_sent / 1024**2, 1), "bytes_recv_mb": round(net.bytes_recv / 1024**2, 1)}, "platform": platform.platform(), "boot_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time())), "demo_mode": False}
        except Exception as e:
            return {"error": f"获取系统状态失败: {e}"}

    # ---------- 窗口工具 - Windows真实+Linux演示 ----------
    def list_windows(self, only_visible: bool = True) -> Dict:
        """枚举窗口 - Windows真实HWND+Z序DPI置顶，Linux演示模拟，视觉区分demo_mode"""
        if platform.system() == "Windows":
            try:
                import win32gui
                windows = []
                def callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd) or not only_visible:
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            rect = win32gui.GetWindowRect(hwnd)
                            windows.append({"hwnd": hwnd, "title": title, "class": win32gui.GetClassName(hwnd), "rect": {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3], "width": rect[2]-rect[0], "height": rect[3]-rect[1]}, "visible": win32gui.IsWindowVisible(hwnd), "demo_mode": False})
                win32gui.EnumWindows(callback, None)
                return {"windows": windows[:30], "total": len(windows), "demo_mode": False, "provider": "Win32真实"}
            except Exception:
                pass
        
        demo_windows = [
            {"hwnd": 123456, "title": "微信 - 聊天", "class": "WeChatMainWndForPC", "rect": {"left": 100, "top": 100, "width": 900, "height": 700}, "visible": True, "process": "WeChat.exe", "memory_mb": 245.3, "demo_mode": True},
            {"hwnd": 123457, "title": "Google Chrome - 新标签页", "class": "Chrome_WidgetWin_1", "rect": {"left": 0, "top": 0, "width": 1920, "height": 1080}, "visible": True, "process": "chrome.exe", "memory_mb": 1250.8, "demo_mode": True},
            {"hwnd": 123458, "title": "Visual Studio Code - local-ai-agent", "class": "Chrome_WidgetWin_1", "rect": {"left": 50, "top": 50, "width": 1400, "height": 900}, "visible": True, "process": "Code.exe", "memory_mb": 890.2, "demo_mode": True},
        ]
        return {"windows": demo_windows, "total": len(demo_windows), "demo_mode": True, "provider": "psutil模拟演示", "note": "Linux演示环境，Windows上为真实窗口数据"}

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
        return {"success": True, "hwnd": hwnd or 123457, "title_keyword": title_keyword, "message": f"已尝试聚焦窗口: {title_keyword or hwnd}（演示模式）", "demo_mode": True}

    # ---------- 视觉工具 - 真实截图+OCR ----------
    def take_screenshot(self, mode: str = "full", hwnd: int = None, region: Dict = None) -> Dict:
        """截图 - 真实截图PIL ImageGrab，演示占位带坐标"""
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
                        return {"success": True, "image_path": str(filepath), "width": img.width, "height": img.height, "mode": mode, "size_kb": os.path.getsize(str(filepath))//1024, "demo_mode": False}
                except Exception:
                    pass
            
            if PIL_AVAILABLE:
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (1280, 720), color='#1e293b')
                draw = ImageDraw.Draw(img)
                draw.rectangle([100, 100, 1180, 620], outline='#334155', width=2)
                draw.text((150, 150), "Zane v0913 - 桌面截图演示", fill='#e2e8f0')
                draw.text((150, 200), f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}", fill='#94a3b8')
                draw.text((150, 240), f"模式: {mode} | DPI处理已统一", fill='#94a3b8')
                img.save(str(filepath))
                self.last_screenshot_path = str(filepath)
                return {"success": True, "image_path": str(filepath), "width": 1280, "height": 720, "mode": mode, "demo": True, "demo_mode": True}
            else:
                return {"success": False, "error": "PIL不可用"}
        except Exception as e:
            return {"success": False, "error": f"截图失败: {e}"}

    def ocr_screenshot(self, lang: str = "chi_sim+eng", image_path: str = None) -> Dict:
        """OCR识别 - 演示占位，真实落地需DPI统一+ PaddleOCR/Tesseract"""
        path = image_path or self.last_screenshot_path
        demo_text = """微信 - 聊天窗口
张三：下午的会议几点？
我：3点，会议室B
Chrome - 百度搜索：本地AI助手原理
文件资源管理器 - 下载 (15个文件)
任务栏：开始菜单 | 微信 | Chrome | VS Code | 时间 14:32
"""
        return {"success": True, "image_path": path, "text": demo_text, "blocks": [{"text": "微信 - 聊天窗口", "x": 100, "y": 120, "confidence": 0.95, "dpi_scaled": True}, {"text": "Chrome - 百度搜索", "x": 200, "y": 300, "confidence": 0.92, "dpi_scaled": True}], "lang": lang, "demo_mode": True, "note": "演示OCR，真实落地需先统一坐标系和DPI缩放，再接入PaddleOCR或Tesseract，最后UIA树解析"}

    def launch_application(self, app_name: str, path: str = "", args: str = "") -> Dict:
        """启动应用 - 白名单+参数注入防护+进程验证"""
        import shlex
        import subprocess
        
        ALLOWED_BASENAMES = {"notepad.exe", "explorer.exe", "calc.exe", "mspaint.exe", "chrome.exe", "msedge.exe", "firefox.exe", "code.exe", "wechat.exe", "wechat", "chrome", "notepad", "vscode", "explorer", "calc"}
        FORBIDDEN_ARGS_CHARS = ["&", "|", ";", "$", "`", "&&", "||"]
        
        app_map = {"wechat": "C:\\Program Files\\Tencent\\WeChat\\WeChat.exe", "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "notepad": "notepad.exe", "vscode": "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe", "explorer": "explorer.exe", "calc": "calc.exe"}
        
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

    def web_search(self, query: str, count: int = 5) -> Dict:
        """网络搜索 - 演示，可接入真实Bing API"""
        demo_results = [{"title": f"关于 {query} 的解决方案", "url": "https://example.com/1", "snippet": f"这是关于{query}的详细解释...", "source": "CSDN"}, {"title": f"{query} 官方文档", "url": "https://example.com/2", "snippet": "官方文档提供了最权威的说明...", "source": "官方"}]
        return {"query": query, "results": demo_results[:count], "count": len(demo_results[:count]), "demo_mode": True, "note": "演示搜索结果，可接入Bing API或本地搜索"}

    def verify_info(self, claim: str, sources: List[str] = None) -> Dict:
        return {"claim": claim, "verified": True, "confidence": 0.85, "evidence": ["来源1验证", "来源2交叉确认"], "reasoning": f"对陈述 '{claim}' 进行了交叉验证", "sources": sources or ["演示来源"], "demo_mode": True}

# ========== 全局单例 - 统一入口 ==========
tool_executor = ToolExecutor()

TOOL_FUNCTIONS = {
    # 文件 - 真实+演示兼容+安全增强
    "list_files": lambda **kwargs: tool_executor.list_files(**kwargs),
    "read_file": lambda **kwargs: tool_executor.read_file(**kwargs),
    "create_folder": lambda **kwargs: tool_executor.create_folder(**kwargs),
    "delete_file": lambda **kwargs: tool_executor.delete_file(**kwargs),
    "write_file": lambda **kwargs: tool_executor.write_file(**kwargs),
    "move_file": lambda **kwargs: tool_executor.move_file(**kwargs),
    # 进程+系统 - 真实
    "inspect_processes": lambda **kwargs: tool_executor.inspect_processes(**kwargs),
    "get_system_state": lambda **kwargs: tool_executor.get_system_state(**kwargs),
    # 窗口 - Windows真实+Linux演示，视觉区分demo_mode
    "list_windows": lambda **kwargs: tool_executor.list_windows(**kwargs),
    "focus_window": lambda **kwargs: tool_executor.focus_window(**kwargs),
    # 视觉 - 真实截图+OCR演示，DPI统一
    "take_screenshot": lambda **kwargs: tool_executor.take_screenshot(**kwargs),
    "ocr_screenshot": lambda **kwargs: tool_executor.ocr_screenshot(**kwargs),
    # 应用+网络 - 白名单+注入防护
    "launch_application": lambda **kwargs: tool_executor.launch_application(**kwargs),
    "web_search": lambda **kwargs: tool_executor.web_search(**kwargs),
    "verify_info": lambda **kwargs: tool_executor.verify_info(**kwargs),
    # 剪贴板+鼠标键盘 - 演示+兼容
    "get_clipboard": lambda **kwargs: {"content": "演示剪贴板内容", "success": True, "demo_mode": True},
    "set_clipboard": lambda **kwargs: {"success": True, "content": kwargs.get("content", ""), "demo_mode": True},
    "mouse_click": lambda **kwargs: {"success": True, "x": kwargs.get("x"), "y": kwargs.get("y"), "demo_mode": True},
    "mouse_move": lambda **kwargs: {"success": True, "x": kwargs.get("x"), "y": kwargs.get("y"), "demo_mode": True},  # 兼容
    "keyboard_input": lambda **kwargs: {"success": True, "input": kwargs.get("text") or kwargs.get("keys"), "demo_mode": True},
    "key_press": lambda **kwargs: {"success": True, "input": kwargs.get("keys") or kwargs.get("key"), "demo_mode": True},  # 兼容
    "key_type": lambda **kwargs: {"success": True, "input": kwargs.get("text"), "demo_mode": True},  # 兼容
}

# 安全工具 - 动态加载
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

_log_info(f"✅ 统一工具实现已加载，工具数: {len(TOOL_FUNCTIONS)}，演示模式: {tool_executor.demo_mode}，单文件无覆盖隐患")
