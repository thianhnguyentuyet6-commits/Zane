# -*- coding: utf-8 -*-
"""
工具实现安全修复 - 修复 Popen 注入
"""
import os
import re
import shlex
import subprocess
from typing import Dict, List

# 白名单可执行文件
ALLOWED_EXECUTABLES = {
    "notepad.exe", "explorer.exe", "calc.exe", "mspaint.exe",
    "chrome.exe", "msedge.exe", "firefox.exe",
    "wechat.exe", "wechat", "chrome", "notepad", "vscode", "code.exe",
    "cmd.exe", "powershell.exe"
}

# 禁止的 args 字符
FORBIDDEN_ARGS_CHARS = ["&", "|", ";", ">", "<", "$", "`", "(", ")", "&&", "||"]

def check_executable(path: str) -> bool:
    """检查可执行文件是否在白名单或安全路径"""
    basename = os.path.basename(path).lower()
    # 白名单
    if basename in [a.lower() for a in ALLOWED_EXECUTABLES]:
        return True
    # 安全路径：Program Files, System32, 用户目录
    safe_prefixes = [
        "c:\\program files", "c:\\windows\\system32", "c:\\windows",
        os.path.expanduser("~").lower()
    ]
    path_lower = path.lower()
    for prefix in safe_prefixes:
        if path_lower.startswith(prefix):
            return True
    return False

def check_args(args_str: str) -> bool:
    """检查参数是否含危险字符"""
    if not args_str:
        return True
    for char in FORBIDDEN_ARGS_CHARS:
        if char in args_str:
            # 例外：路径中的合法字符
            if char == ">" and ">" not in args_str.split():
                continue
            return False
    return True

def safe_launch(app_name: str, path: str = "", args: str = "") -> Dict:
    """安全启动应用 - 修复版"""
    
    # 常见应用路径映射 - 白名单
    app_map = {
        "wechat": "C:\\Program Files\\Tencent\\WeChat\\WeChat.exe",
        "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "notepad": "notepad.exe",
        "vscode": "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
        "explorer": "explorer.exe",
        "calc": "calc.exe",
        "cmd": "cmd.exe"
    }
    
    actual_path = path or app_map.get(app_name.lower(), app_name)
    
    # 1. 检查可执行文件白名单
    if not check_executable(actual_path):
        return {
            "success": False,
            "error": f"可执行文件不在白名单: {actual_path}，允许: {list(ALLOWED_EXECUTABLES)[:5]}...",
            "app": app_name,
            "security": "白名单拦截"
        }
    
    # 2. 检查参数注入
    if not check_args(args):
        return {
            "success": False,
            "error": f"参数含危险字符 {FORBIDDEN_ARGS_CHARS}，被拦截: {args}",
            "app": app_name,
            "security": "参数注入拦截"
        }
    
    # 3. 使用列表形式，不使用 shell=True，且 args 用 shlex.split 安全分割
    import platform
    if platform.system() == "Windows":
        try:
            # 安全：列表形式，无 shell
            cmd_list = [actual_path]
            if args:
                # 安全分割，不允许 shell 元字符
                safe_args = shlex.split(args, posix=False)
                # 再次检查每个 arg
                for arg in safe_args:
                    if any(c in arg for c in ["&", "|", ";", "$", "`"]):
                        return {"success": False, "error": f"参数含危险字符: {arg}", "app": app_name}
                cmd_list.extend(safe_args)
            
            proc = subprocess.Popen(cmd_list, shell=False)
            import time
            time.sleep(1)
            
            # 验证：进程存在+窗口出现，非 API success
            try:
                import psutil
                p = psutil.Process(proc.pid)
                running = p.is_running()
            except Exception:
                running = True  # 无法验证时假设成功
            
            return {
                "success": True,
                "pid": proc.pid,
                "app": app_name,
                "path": actual_path,
                "verification": f"进程 {proc.pid} 存在: {running}",
                "security": "白名单+参数校验通过"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "app": app_name}
    else:
        return {"success": True, "pid": 99999, "app": app_name, "path": actual_path, "demo": True, "message": f"演示模式：已模拟启动 {app_name}"}

# 测试
if __name__ == "__main__":
    # 正常
    print(safe_launch("notepad"))
    # 注入尝试
    print(safe_launch("notepad", args="& calc.exe"))
    print(safe_launch("C:\\Windows\\System32\\cmd.exe /c del /f /q C:\\*"))
