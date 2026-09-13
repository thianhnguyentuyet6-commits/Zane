# Zane Windows桌面端 v0914

> **Tauri 2.x + Python FastAPI Sidecar + 混合LLM检测**，Windows PC专注，离线优先，深度Windows控制

## 快速开始

### 安装
1. 下载 `Zane_0.9.14_x64_zh-CN.msi` (80-120MB)
2. 双击安装到 `C:\Program Files\Zane\`
3. 开始菜单启动 Zane，或桌面快捷方式
4. 托盘图标出现，Alt+Space 全局唤起

### 使用
- **聊天**: 自然语言说"整理下载文件夹"，真实文件操作+确认弹窗+回收站+undo
- **托盘**: 单击托盘图标显示/隐藏主窗口，右键菜单：显示主窗口/设置/退出
- **全局快捷键**: Alt+Space 唤起主窗口，聚焦聊天输入
- **关闭**: 关闭按钮最小化到托盘，不退出，托盘菜单退出才真正退出
- **开机自启**: 设置页开关，联动Tauri autostart插件
- **通知**: 原生Windows通知，任务完成/需要确认时推送

### LLM配置 (混合检测，符合v0914-14)

优先级：env > config > 默认探测，找不到报错退出，HF不自动下载

1. **环境变量** (最高优先级):
   ```
   MODEL_PATH / QWEN_MODEL_PATH / LLM_MODEL_PATH / ZANE_MODEL_PATH / HF_MODEL_PATH
   = D:\llama.cpp\qwen3-30b-a3b.gguf
   ```

2. **config/model_paths.json**:
   ```json
   {
     "qwen": "D:\\llama.cpp\\qwen3-30b-a3b.gguf",
     "default": "D:\\models\\qwen.gguf"
   }
   ```

3. **常见路径自动探测**:
   - `D:\llama.cpp\*.gguf`
   - `C:\llama.cpp\*.gguf`
   - `D:\llama\*.gguf`

4. **内置Sidecar** (最后回退):
   - 若安装包包含 `llama-server.exe`，自动使用

**找不到模型**: 报错退出，提示用户配置路径，不自动下载HF模型，检测缓存提示确认

### 系统要求
- Windows 10/11 64位
- WebView2 (Win11自带，Win10需安装)
- 8GB VRAM 3060ti + 32GB RAM 推荐 (CPU Offload支持8GB)
- 磁盘: 500MB (应用) + 模型大小 (Qwen3 30B-A3B ~18GB)

## 开发

### 环境
- Rust 1.77.2+ + Cargo
- Node.js 18+ (可选，Tauri CLI)
- Python 3.11+ + PyInstaller 6.x
- Windows 10/11 (真实测试WMI+Win32)

### 开发模式
```bash
# 后端单独
python -m uvicorn backend.main:app --port 8000

# Tauri开发 (需cargo)
cargo tauri dev

# 或
python scripts/build_tauri.py  # 验证配置
```

### 构建MSI
```bash
# Windows真实环境
pip install pyinstaller
python scripts/build_backend.py  # 生成zane-backend.exe到src-tauri/binaries/
cargo tauri build  # 生成MSI到src-tauri/target/release/bundle/msi/

# 一键构建
python scripts/build_tauri.py
```

产物: `src-tauri/target/release/bundle/msi/Zane_0.9.14_x64_zh-CN.msi` 80-120MB

### 项目结构
```
src-tauri/
├── Cargo.toml (tauri 2.2+ + 7插件)
├── tauri.conf.json (app id com.zane.windows + bundle msi+nsis + sidecars)
├── src/
│   ├── main.rs (setup sidecar+tray+shortcut+window_state)
│   ├── llm_detector.rs (混合检测env>config>默认)
│   ├── backend_manager.rs (sidecar生命周期+健康检查)
│   ├── tray.rs (托盘菜单显示/设置/退出+单击切换)
│   └── window_state.rs (窗口位置大小记忆)
├── icons/ (icon.ico+icon.png)
└── binaries/ (zane-backend.exe+llama-server.exe，gitignore)

frontend/index.html (isTauri检测+托盘最小化+通知统一+自启切换)
backend/main.py (--port参数+sidecar支持)
scripts/build_backend.py + build_tauri.py
```

## 架构

```
Zane.exe (Tauri Rust主进程)
├── Webview: frontend/index.html (89KB毛玻璃+渐变+知识图谱) + Tauri API
├── Sidecar: zane-backend.exe (Python FastAPI 114API) --port 8000
│   ├── platform/windows/wmi_provider.py (WMI真实 per-core+GPU+内存条+SMART)
│   ├── platform/windows/win32_window.py (Win32真实 HWND Z序DPI多显示器)
│   ├── tools/file_tools.py (深模块) + tools_impl.py (26工具)
│   ├── memory/ 4层+SimpleMem+forgetting+DREAMS.md
│   ├── policy_firewall+undo_stack+security
│   └── routers/ 18路由+knowledge-graph 4路由
├── Sidecar: llama-server.exe (可选，混合检测)
│   └── Qwen3 30B-A3B D:\llama.cpp\...gguf
└── Tauri插件: tray+globalShortcut Alt+Space+autostart+notification+fs+dialog+single-instance
```

## 测试

```bash
pytest tests/test_windows_foundation.py -v  # 4/4 WMI+Win32基础
pytest tests/test_forgetting.py -v          # 2/2 遗忘曲线
pytest tests/test_undo_e2e.py -v            # 3/3 撤销端到端
pytest tests/test_tauri_integration.py -v   # 5/5 Tauri集成
pytest tests/test_desktop_e2e.py -v         # 桌面端端到端
```

## 后续 (v1.1+)

- 右键菜单集成"用Zane整理"
- 文件关联+拖拽文件到窗口
- 多窗口(设置独立窗口)
- 自动更新检查+下载
- 性能: Rust重写热点(文件列表+进程监控)
- 分发: Microsoft Store + Winget

---

**Windows专注，PC做好，前端写好，后端打牢**，Tauri桌面端完整AGI管家，托盘常驻+全局快捷键，开箱即用
