#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键构建Tauri MSI安装包
Windows真实环境执行，Linux下验证配置
"""
import subprocess
import sys
from pathlib import Path

def build_backend_sidecar():
    """构建backend sidecar"""
    root = Path(__file__).parent.parent
    script = root / "scripts" / "build_backend.py"
    print(f"=== 构建backend sidecar: {script} ===")
    result = subprocess.run([sys.executable, str(script)], cwd=root)
    return result.returncode == 0

def build_tauri():
    """构建Tauri"""
    root = Path(__file__).parent.parent
    src_tauri = root / "src-tauri"
    
    # 检查cargo
    try:
        subprocess.run(["cargo", "--version"], capture_output=True, check=True)
    except:
        print("⚠️ cargo未安装，Linux环境跳过实际Tauri构建，仅验证配置")
        print("   Windows执行: cargo tauri build")
        # 验证配置
        import json
        config = json.loads((src_tauri / "tauri.conf.json").read_text())
        assert config["productName"] == "Zane"
        assert "msi" in config["bundle"]["targets"]
        print("✅ Tauri配置验证通过")
        return True
    
    # 1. 先构建backend sidecar
    if not build_backend_sidecar():
        print("❌ backend构建失败")
        return False
    
    # 2. 构建Tauri
    print("=== 构建Tauri MSI ===")
    result = subprocess.run(["cargo", "tauri", "build"], cwd=src_tauri)
    if result.returncode != 0:
        print("❌ Tauri构建失败")
        return False
    
    # 3. 列出产物
    bundle_dir = src_tauri / "target" / "release" / "bundle"
    print(f"✅ 构建产物在: {bundle_dir}")
    for msi in bundle_dir.rglob("*.msi"):
        size_mb = msi.stat().st_size / 1024 / 1024
        print(f"  MSI: {msi} ({size_mb:.1f}MB)")
        if size_mb > 150:
            print(f"  ⚠️ 体积偏大>{150}MB，考虑UPX压缩+排除大库")
    
    return True

def check_config():
    """验证配置"""
    root = Path(__file__).parent.parent
    src_tauri = root / "src-tauri"
    import json
    config = json.loads((src_tauri / "tauri.conf.json").read_text())
    
    checks = [
        (config["productName"] == "Zane", "productName=Zane"),
        (config["identifier"] == "com.zane.windows", "identifier=com.zane.windows"),
        ("msi" in config["bundle"]["targets"], "bundle包含msi"),
        (len(config["bundle"]["externalBin"]) >= 1, "externalBin包含sidecar"),
    ]
    
    for ok, desc in checks:
        print(f"  {'✅' if ok else '❌'} {desc}")
    
    return all(ok for ok, _ in checks)

if __name__ == "__main__":
    print("=== Zane Windows桌面端构建 ===")
    print(f"平台: {sys.platform}")
    
    if not check_config():
        print("❌ 配置检查失败")
        sys.exit(1)
    
    success = build_tauri()
    if success:
        print("✅ 构建成功或配置验证通过")
    sys.exit(0 if success else 1)
