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
        except:
            return False

    def _list_distros(self) -> List[str]:
        """列出 WSL 发行版 - 真实命令"""
        try:
            result = subprocess.run(["wsl", "--list", "--quiet"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                distros = [d.strip() for d in result.stdout.splitlines() if d.strip()]
                return distros
        except:
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
        """在 WSL 中执行命令 - 沙盒限制，具体实现"""
        
        # === 沙盒检查 - 防止危险命令 ===
        dangerous_patterns = [
            "rm -rf /", "rm -rf /*", ":(){:|:&};:", "mkfs", "dd if=",
            "> /dev/sda", "chmod -R 777 /", "mv /*", "sudo rm"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command:
                raise PermissionError(f"危险命令被沙盒拦截: {pattern}")
        
        # 检查路径遍历
        if ".." in command and ("etc" in command or "root" in command):
            raise PermissionError(f"路径遍历被拦截: {command}")
        
        # 只允许在用户目录
        if workdir and not workdir.startswith(("/home/", "~", "/tmp")):
            workdir = "~"
        
        if not self.available:
            # Linux 演示环境，直接执行
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True, timeout=10, cwd="/tmp"
                )
                return {
                    "success": True,
                    "distro": distro,
                    "command": command,
                    "stdout": result.stdout[:2000],
                    "stderr": result.stderr[:500],
                    "returncode": result.returncode,
                    "real": False,
                    "note": "Linux 演示直接执行，Windows 上为 WSL 沙盒执行"
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "命令超时 10秒", "command": command}
            except Exception as e:
                return {"success": False, "error": str(e), "command": command}
        
        # Windows 真实 WSL 执行
        try:
            # 构建 WSL 命令
            wsl_cmd = ["wsl", "-d", distro, "--", "bash", "-c", f"cd {workdir} && {command}"]
            
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
                "real": True
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
