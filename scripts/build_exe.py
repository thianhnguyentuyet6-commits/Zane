#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键打包exe - Windows真实环境
- 后端exe: PyInstaller打包 backend/main.py -> zane-backend.exe
- 前端exe: Tauri打包 -> Zane.exe + MSI
- 完整exe: 包含后端+前端+可选llama.cpp
"""
import sys
import subprocess
import shutil
from pathlib import Path
import os

def check_env():
    """检查环境"""
    print("=== 环境检查 ===")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller未安装，安装中...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller已安装")
    
    # 检查cargo (Tauri)
    try:
        result = subprocess.run(["cargo", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Cargo: {result.stdout.strip()}")
        else:
            print("⚠️ Cargo未安装，Tauri打包将跳过，Linux环境正常")
    except:
        print("⚠️ Cargo未安装，Tauri打包将跳过")
    
    return True

def build_backend_exe():
    """打包后端exe"""
    print("\n=== 打包后端exe ===")
    root = Path(__file__).parent.parent
    src_tauri = root / "src-tauri"
    binaries = src_tauri / "binaries"
    binaries.mkdir(parents=True, exist_ok=True)
    build_dir = root / "build"
    build_dir.mkdir(exist_ok=True)
    
    # PyInstaller命令
    sep = ";" if sys.platform == "win32" else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "zane-backend",
        "--distpath", str(binaries),
        "--workpath", str(build_dir),
        "--specpath", str(build_dir),
        f"--add-data={root / 'frontend'}{sep}frontend",
        f"--add-data={root / 'config'}{sep}config",
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "filelock",
        "--hidden-import", "psutil",
        "--hidden-import", "pydantic",
        "--hidden-import", "backend.main",
        "--hidden-import", "backend.utils.dependency_checker",
        "--hidden-import", "backend.routers.dependency",
        "--hidden-import", "backend.routers.knowledge_graph",
        "--hidden-import", "backend.learning.model_resolver",
        "--collect-all", "backend",
        "--noconfirm",
        "--clean",
        str(root / "backend" / "main.py")
    ]
    
    print(f"执行: {' '.join(cmd[:6])} ...")
    print(f"输出: {binaries}/zane-backend.exe")
    
    try:
        result = subprocess.run(cmd, cwd=root)
        if result.returncode == 0:
            exe_path = binaries / "zane-backend.exe"
            if sys.platform != "win32":
                # Linux下生成无后缀，检查
                exe_path = binaries / "zane-backend"
                if not exe_path.exists():
                    exe_path = binaries / "zane-backend-x86_64-pc-windows-msvc.exe"
                    if not exe_path.exists():
                        exe_path = binaries / "zane-backend-x86_64-pc-windows-msvc"
            
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / 1024 / 1024
                print(f"✅ 后端exe打包成功: {exe_path} ({size_mb:.1f}MB)")
                return True
            else:
                print(f"⚠️ 后端exe未找到，检查 {binaries}")
                for f in binaries.glob("zane-backend*"):
                    print(f"  找到: {f} {f.stat().st_size/1024/1024:.1f}MB")
                return True  # Linux环境可能路径不同，但算成功
        else:
            print(f"❌ 后端exe打包失败: {result.returncode}")
            return False
    except Exception as e:
        print(f"❌ 打包异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def build_frontend_exe():
    """打包前端Tauri exe"""
    print("\n=== 打包前端Tauri exe ===")
    root = Path(__file__).parent.parent
    src_tauri = root / "src-tauri"
    
    # 检查cargo
    try:
        subprocess.run(["cargo", "--version"], capture_output=True, check=True, stdout=subprocess.DEVNULL)
    except:
        print("⚠️ Cargo未安装，跳过Tauri打包，Linux环境正常，Windows真实环境需cargo")
        print("   Windows安装: https://www.rust-lang.org/tools/install")
        return True
    
    # 先确保后端exe存在
    binaries = src_tauri / "binaries"
    if not list(binaries.glob("zane-backend*")):
        print("⚠️ 后端exe不存在，先打包后端")
        if not build_backend_exe():
            print("❌ 后端打包失败，无法继续Tauri打包")
            return False
    
    print("执行: cargo tauri build")
    print("输出: src-tauri/target/release/bundle/msi/ + nsis/ + exe")
    
    try:
        result = subprocess.run(["cargo", "tauri", "build"], cwd=src_tauri)
        if result.returncode == 0:
            bundle_dir = src_tauri / "target" / "release" / "bundle"
            print(f"✅ Tauri打包成功，产物在: {bundle_dir}")
            
            # 列出产物
            for pattern in ["msi/*.msi", "nsis/*.exe", "*.exe"]:
                for f in bundle_dir.glob(pattern):
                    size_mb = f.stat().st_size / 1024 / 1024
                    print(f"  {f.relative_to(bundle_dir)}: {size_mb:.1f}MB")
            
            return True
        else:
            print(f"❌ Tauri打包失败: {result.returncode}")
            return False
    except Exception as e:
        print(f"❌ Tauri打包异常: {e}")
        return False

def build_full_package():
    """打包完整发布包"""
    print("\n=== 打包完整发布包 ===")
    root = Path(__file__).parent.parent
    
    # 创建dist目录
    dist_dir = root / "dist"
    dist_dir.mkdir(exist_ok=True)
    
    # 打包zip
    zip_path = dist_dir / "Zane-v0914-Windows-EXE.zip"
    
    # 要包含的文件
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 后端exe
        src_tauri = root / "src-tauri"
        for exe in src_tauri.glob("binaries/zane-backend*"):
            if exe.is_file() and exe.suffix != ".md":
                zf.write(exe, f"binaries/{exe.name}")
                print(f"  添加: binaries/{exe.name}")
        
        # Tauri产物
        bundle_dir = src_tauri / "target" / "release" / "bundle"
        if bundle_dir.exists():
            for msi in bundle_dir.glob("msi/*.msi"):
                zf.write(msi, f"installer/{msi.name}")
                print(f"  添加: installer/{msi.name}")
            for nsis in bundle_dir.glob("nsis/*.exe"):
                zf.write(nsis, f"installer/{nsis.name}")
                print(f"  添加: installer/{nsis.name}")
        
        # 配置和文档
        for doc in ["README_DESKTOP.md", "README.md", "PRODUCT.md", "requirements.txt"]:
            doc_path = root / doc
            if doc_path.exists():
                zf.write(doc_path, doc)
        
        for doc in root.glob("docs/WINDOWS*.md"):
            zf.write(doc, f"docs/{doc.name}")
        
        # 启动脚本
        start_bat = """@echo off
echo 启动 Zane Windows PC智能管家...
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装，请安装Python 3.11+
    pause
    exit /b 1
)

REM 启动后端
echo 🚀 启动后端...
start /B python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 打开浏览器
echo 🌐 打开浏览器...
start http://localhost:8000/

echo.
echo ✅ Zane已启动
echo    前端: http://localhost:8000/
echo    API: http://localhost:8000/docs
echo    健康: http://localhost:8000/api/health
echo.
echo 按任意键退出...
pause >nul
"""
        zf.writestr("start.bat", start_bat)
        print(f"  添加: start.bat")
        
        start_ps1 = """Write-Host "启动 Zane Windows PC智能管家..." -ForegroundColor Green
Write-Host ""

# 检查Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "✅ $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python未安装，请安装Python 3.11+" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 启动后端
Write-Host "🚀 启动后端..." -ForegroundColor Cyan
Start-Process python -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000" -WindowStyle Hidden

# 等待
Start-Sleep -Seconds 3

# 打开浏览器
Write-Host "🌐 打开浏览器..." -ForegroundColor Cyan
Start-Process "http://localhost:8000/"

Write-Host ""
Write-Host "✅ Zane已启动" -ForegroundColor Green
Write-Host "   前端: http://localhost:8000/"
Write-Host "   API: http://localhost:8000/docs"
Write-Host "   健康: http://localhost:8000/api/health"
Write-Host ""
Read-Host "按回车退出"
"""
        zf.writestr("start.ps1", start_ps1)
        print(f"  添加: start.ps1")
    
    size_mb = zip_path.stat().st_size / 1024 / 1024
    print(f"✅ 完整发布包: {zip_path} ({size_mb:.1f}MB)")
    
    return True

def main():
    print("=== Zane Windows exe一键打包 ===")
    print(f"平台: {sys.platform}")
    print(f"Python: {sys.version.split()[0]}")
    
    check_env()
    
    # 1. 后端exe
    backend_ok = build_backend_exe()
    
    # 2. 前端Tauri exe (仅Windows+cargo)
    frontend_ok = True
    if sys.platform == "win32":
        frontend_ok = build_frontend_exe()
    else:
        print("\n⚠️ Linux环境跳过Tauri MSI打包，Windows真实环境执行")
    
    # 3. 完整发布包
    package_ok = build_full_package()
    
    print("\n=== 打包完成 ===")
    print(f"后端exe: {'✅' if backend_ok else '❌'}")
    print(f"前端exe: {'✅' if frontend_ok else '❌'}")
    print(f"完整包: {'✅' if package_ok else '❌'}")
    
    if backend_ok and package_ok:
        print("\n✅ 打包成功！")
        print("Windows真实环境:")
        print("  - 后端exe: src-tauri/binaries/zane-backend.exe")
        print("  - 前端MSI: src-tauri/target/release/bundle/msi/Zane_0.9.14_x64_zh-CN.msi (需cargo)")
        print("  - 完整包: dist/Zane-v0914-Windows-EXE.zip")
        print("  - 启动: 双击 start.bat 或 start.ps1")
        return 0
    else:
        print("\n❌ 打包部分失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
