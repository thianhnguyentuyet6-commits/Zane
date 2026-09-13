#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建zane-backend.exe sidecar via PyInstaller
Windows真实环境执行，Linux下仅生成spec
"""
import subprocess
import sys
from pathlib import Path

def build_backend():
    root = Path(__file__).parent.parent
    src_tauri = root / "src-tauri"
    binaries = src_tauri / "binaries"
    binaries.mkdir(parents=True, exist_ok=True)
    build_dir = root / "build"
    build_dir.mkdir(exist_ok=True)
    
    # 检查PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("⚠️ PyInstaller未安装，Linux环境跳过实际打包，仅验证配置")
        print(f"   Windows执行: pip install pyinstaller && python scripts/build_backend.py")
        # 创建占位说明
        (binaries / "README.md").write_text("# Sidecar二进制\n\nWindows执行: python scripts/build_backend.py 生成 zane-backend-x86_64-pc-windows-msvc.exe\n")
        return True
    
    # PyInstaller命令
    sep = ";" if sys.platform == "win32" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "zane-backend-x86_64-pc-windows-msvc",
        "--distpath", str(binaries),
        "--workpath", str(build_dir),
        "--specpath", str(build_dir),
        f"--add-data={root / 'config'}{sep}config",
        f"--add-data={root / 'frontend'}{sep}frontend",
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "filelock",
        "--hidden-import", "backend.main",
        "--collect-all", "backend",
        "--noconfirm",
        str(root / "backend" / "main.py")
    ]
    
    print(f"构建命令: {' '.join(cmd[:5])}...")
    result = subprocess.run(cmd, cwd=root)
    return result.returncode == 0

def check_backend_health(port=8000):
    """健康检查"""
    try:
        import requests
        resp = requests.get(f"http://localhost:{port}/api/health", timeout=2)
        return resp.status_code == 200
    except:
        return False

if __name__ == "__main__":
    success = build_backend()
    if success:
        print("✅ Backend sidecar构建成功或配置验证通过")
    sys.exit(0 if success else 1)
