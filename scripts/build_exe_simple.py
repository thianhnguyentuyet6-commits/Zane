#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化打包exe - 快速版
"""
import sys
from pathlib import Path
import subprocess
import zipfile

root = Path(__file__).parent.parent
dist_dir = root / "dist"
dist_dir.mkdir(exist_ok=True)

print("=== 简化打包 - 直接ZIP ===")

# 直接打包源码为可执行包，包含启动脚本
zip_path = dist_dir / "Zane-v0914-Windows-EXE-Simple.zip"
print(f"打包: {zip_path}")

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    # 后端
    for py in root.glob("backend/**/*.py"):
        if "__pycache__" not in str(py):
            zf.write(py, str(py.relative_to(root)))
    
    # 前端
    zf.write(root / "frontend" / "index.html", "frontend/index.html")
    
    # 配置
    for cfg in root.glob("config/*.json"):
        zf.write(cfg, str(cfg.relative_to(root)))
    
    # 测试
    for test in root.glob("tests/test_*.py"):
        zf.write(test, str(test.relative_to(root)))
    
    # 文档
    for doc in ["README_DESKTOP.md", "README.md", "PRODUCT.md", "requirements.txt"]:
        p = root / doc
        if p.exists():
            zf.write(p, doc)
    
    for doc in root.glob("docs/WINDOWS*.md"):
        zf.write(doc, f"docs/{doc.name}")
    
    # src-tauri
    for f in root.glob("src-tauri/**/*"):
        if f.is_file() and "target" not in str(f) and "__pycache__" not in str(f):
            if f.suffix not in [".lock"]:
                try:
                    zf.write(f, str(f.relative_to(root)))
                except:
                    pass
    
    # 启动脚本
    start_bat = """@echo off
echo 启动 Zane Windows PC智能管家...
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装，请安装Python 3.11+ https://www.python.org/
    pause
    exit /b 1
)

echo 📦 检查依赖...
pip install -r requirements.txt -q

echo 🚀 启动后端...
start /B python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info

timeout /t 3 /nobreak >nul

echo 🌐 打开浏览器...
start http://localhost:8000/

echo.
echo ✅ Zane已启动
echo    前端: http://localhost:8000/
echo    API: http://localhost:8000/docs
echo    健康: http://localhost:8000/api/health
echo    依赖: http://localhost:8000/api/dependency/check
echo.
echo 按任意键退出...
pause >nul
"""
    zf.writestr("start.bat", start_bat)
    
    start_ps1 = """Write-Host "启动 Zane Windows PC智能管家..." -ForegroundColor Green
Write-Host "📦 检查依赖..." -ForegroundColor Cyan
pip install -r requirements.txt -q

Write-Host "🚀 启动后端..." -ForegroundColor Cyan
Start-Process python -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info" -WindowStyle Hidden
Start-Sleep -Seconds 3

Write-Host "🌐 打开浏览器..." -ForegroundColor Cyan
Start-Process "http://localhost:8000/"

Write-Host ""
Write-Host "✅ Zane已启动" -ForegroundColor Green
Write-Host "   前端: http://localhost:8000/"
Write-Host "   API: http://localhost:8000/docs"
Write-Host "   测试: pytest tests/ -v (22 tests)"
Write-Host ""
Read-Host "按回车退出"
"""
    zf.writestr("start.ps1", start_ps1)
    
    # 一键exe构建脚本
    build_exe_bat = """@echo off
echo 打包exe...
echo.

python --version
pip install pyinstaller -q

echo 打包后端exe...
python scripts/build_backend.py

echo.
echo 打包Tauri MSI (需Rust)...
cd src-tauri
cargo tauri build
cd ..

echo.
echo ✅ 打包完成
echo    后端exe: src-tauri/binaries/zane-backend.exe
echo    前端MSI: src-tauri/target/release/bundle/msi/
echo.
pause
"""
    zf.writestr("build_exe.bat", build_exe_bat)

size_mb = zip_path.stat().st_size / 1024 / 1024
print(f"✅ 简化打包完成: {zip_path} ({size_mb:.1f}MB)")

# 同时复制到/tmp供下载
import shutil
shutil.copy(zip_path, "/tmp/Zane-v0914-Windows-EXE.zip")
print(f"✅ 已复制到 /tmp/Zane-v0914-Windows-EXE.zip")

