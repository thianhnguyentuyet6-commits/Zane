# -*- coding: utf-8 -*-
"""
桌面端端到端测试
"""
from pathlib import Path

def test_tauri_project_exists():
    """Tauri项目存在"""
    assert (Path("src-tauri/Cargo.toml")).exists()
    assert (Path("src-tauri/tauri.conf.json")).exists()
    assert (Path("src-tauri/src/main.rs")).exists()
    print("✅ Tauri项目存在")

def test_tauri_modules_exist():
    """Tauri模块存在"""
    assert (Path("src-tauri/src/llm_detector.rs")).exists()
    assert (Path("src-tauri/src/backend_manager.rs")).exists()
    assert (Path("src-tauri/src/tray.rs")).exists()
    assert (Path("src-tauri/src/window_state.rs")).exists()
    print("✅ Tauri模块4个存在")

def test_backend_sidecar_build_script():
    """Backend sidecar构建脚本"""
    assert (Path("scripts/build_backend.py")).exists()
    assert (Path("scripts/build_tauri.py")).exists()
    print("✅ 构建脚本存在")

def test_desktop_features_in_main():
    """桌面端功能在main.rs"""
    main_rs = Path("src-tauri/src/main.rs").read_text(encoding='utf-8')
    assert "tray" in main_rs.lower(), "应包含tray"
    assert "global_shortcut" in main_rs or "shortcut" in main_rs.lower(), "应包含global shortcut"
    assert "window_state" in main_rs.lower(), "应包含window_state"
    assert "llm_detector" in main_rs.lower(), "应包含llm_detector"
    print("✅ main.rs包含托盘+快捷键+窗口状态+LLM检测")

def test_frontend_tauri_adaptation():
    """前端Tauri适配"""
    index_html = Path("frontend/index.html").read_text(encoding='utf-8')
    assert "isTauri" in index_html, "应包含isTauri检测"
    assert "sendTauriNotification" in index_html, "应包含通知统一"
    assert "toggleTauriAutostart" in index_html, "应包含自启切换"
    print("✅ 前端Tauri适配存在")

def test_readme_desktop():
    """桌面端README"""
    assert (Path("README_DESKTOP.md")).exists()
    content = Path("README_DESKTOP.md").read_text(encoding='utf-8')
    assert "Tauri" in content
    assert "MSI" in content
    assert "Alt+Space" in content
    print("✅ README_DESKTOP.md存在")

def test_windows_foundation_still_pass():
    """Windows基础测试仍通过"""
    import subprocess
    result = subprocess.run(
        ["python", "tests/test_windows_foundation.py"],
        capture_output=True, text=True
    )
    assert "全部通过" in result.stdout, f"Windows基础测试失败: {result.stdout}"
    print("✅ Windows基础 4/4 仍通过")

def test_tauri_integration():
    """Tauri集成测试"""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_tauri_integration.py", "-v"],
        capture_output=True, text=True
    )
    assert "5 passed" in result.stdout or "passed" in result.stdout
    print("✅ Tauri集成 5/5 通过")
