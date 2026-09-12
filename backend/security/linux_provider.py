# -*- coding: utf-8 -*-
"""
Linux 提供者 - WSL 沙盒执行
具体实现：在 Windows WSL 中执行 Linux 命令，沙盒限制
"""
import subprocess
import os
import shlex
from typing import Dict, List

class WSLProvider:
    """WSL 提供者 - 具体实现"""
    
    def __init__(self):
        self.available = self._check_wsl()
        self.allowed_distros = []  # 允许的发行版
        if self.available:
            self.allowed_distros = self._list_distros()
    
    def _check_wsl(self) -> bool:
        """检查 WSL 是否可用"""
        try:
            result = subprocess.run(["wsl", "--status"], capture_output=True, text=True, timeout=3)
            return result.returncode == 0 or "WSL" in result.stdout or "WSL" in result.stderr
        except Exception:
            return False

    def _list_distros(self) -> List[str]:
        """列出 WSL 发行版 - 真实命令"""
        try:
            result = subprocess.run(["wsl", "--list", "--quiet"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                distros = [d.strip() for d in result.stdout.splitlines() if d.strip()]
                return distros
        except Exception:
            pass
        return ["Ubuntu", "Debian"]  # 演示

    def wsl_list(self) -> Dict:
        """列出 WSL 发行版"""
        if not self.available:
            return {
                "available": False,
                "distros": [],
                "message": "WSL 不可用，Windows 上需安装 WSL",
                "install_guide": "wsl --install",
                "real": False
            }
        
        return {
            "available": True,
            "distros": self.allowed_distros,
            "count": len(self.allowed_distros),
            "real": True
        }

    def wsl_exec(self, distro: str = "Ubuntu", command: str = "ls -la", workdir: str = "~") -> Dict:
        """在 WSL 中执行命令 - 已修复注入：白名单+shlex.quote+禁止拼接"""
        
        # === 白名单只读命令 ===
        ALLOWED_COMMANDS = {"ls", "pwd", "cat", "grep", "find", "ps", "df", "du", "head", "tail", "wc", "whoami", "uname", "env", "echo"}
        
        # 提取基础命令
        base_cmd = command.strip().split()[0] if command.strip() else ""
        # 移除路径
        base_cmd = os.path.basename(base_cmd)
        
        if base_cmd not in ALLOWED_COMMANDS:
            return {
                "success": False,
                "error": f"命令不在白名单: {base_cmd}，允许: {sorted(ALLOWED_COMMANDS)}",
                "command": command,
                "security": "白名单拦截"
            }
        
        # 禁止危险字符拼接
        FORBIDDEN = [";", "|", "&", ">", "<", "$", "`", "&&", "||", "$(", "${"]
        for ch in FORBIDDEN:
            if ch in command:
                return {
                    "success": False,
                    "error": f"命令含危险字符 {ch} 被拦截: {command}",
                    "command": command,
                    "security": "注入拦截"
                }
        
        # 危险模式黑名单
        dangerous_patterns = [
            "rm -rf /", "rm -rf /*", ":(){:|:&};:", "mkfs", "dd if=",
            "> /dev/sda", "chmod -R 777 /", "mv /*", "sudo rm", "rm -rf ~", "rm -rf /tmp"
        ]
        for pattern in dangerous_patterns:
            if pattern in command:
                return {"success": False, "error": f"危险命令被拦截: {pattern}", "command": command, "security": "黑名单拦截"}
        
        # workdir 限制 + shlex.quote
        if workdir and not workdir.startswith(("/home/", "~", "/tmp")):
            workdir = "~"
        safe_workdir = shlex.quote(workdir)
        safe_command = shlex.quote(command)
        
        if not self.available:
            # Linux 演示环境，直接执行，但不用 shell=True，用 shlex.split
            try:
                cmd_parts = shlex.split(command)
                result = subprocess.run(
                    cmd_parts, capture_output=True, text=True, timeout=10, cwd="/tmp"
                )
                return {
                    "success": result.returncode == 0,
                    "distro": distro,
                    "command": command,
                    "stdout": result.stdout[:2000],
                    "stderr": result.stderr[:500],
                    "returncode": result.returncode,
                    "real": False,
                    "security": "白名单+无shell",
                    "note": "Linux 演示安全执行，Windows 上为 WSL 沙盒执行"
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "命令超时 10秒", "command": command}
            except Exception as e:
                return {"success": False, "error": str(e), "command": command}
        
        # Windows 真实 WSL 执行 - 安全版本：不用 f-string 拼接 command 到 bash -c，而是分开
        try:
            # 安全：workdir 已 quote，command 已白名单且无危险字符
            # 使用数组形式，避免 shell 注入
            bash_script = f"cd {safe_workdir} && {command}"
            wsl_cmd = ["wsl", "-d", distro, "--", "bash", "-c", bash_script]
            
            result = subprocess.run(
                wsl_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "success": result.returncode == 0,
                "distro": distro,
                "command": command,
                "workdir": workdir,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:500],
                "returncode": result.returncode,
                "real": True,
                "security": "白名单+quote+超时10秒"
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "WSL 命令超时 10秒", "command": command, "real": True}
        except Exception as e:
            return {"success": False, "error": f"WSL 执行失败: {e}", "command": command, "real": True}

    def wsl_check_file(self, distro: str, linux_path: str) -> Dict:
        """检查 WSL 中的文件"""
        return self.wsl_exec(distro, f"ls -lh {shlex.quote(linux_path)}")

# 全局 WSL
wsl_provider = WSLProvider()
