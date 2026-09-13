# Windows桌面端 Tauri 设计文档

> **状态**: Draft → 待用户确认
> **日期**: 2026-09-13
> **技能**: brainstorming (Architectural Path) + writing-plans后续
> **目标**: Windows桌面端完整AGI管家，Tauri + Python Sidecar，安装包分发

## 1. 背景与目标

### 1.1 现状评估 (Superpowers项目体检)
- **后端**: 86文件，114API (82模块化+32兼容)，26工具Windows真实但Linux演示，WMI per-core+GPU+内存条+SMART+启动项+服务+Win32 HWND Z序DPI多显示器+截图DPI统一+UIA树+OCR延迟+5维度资源监控+摄像头/麦克风会议检测，4层记忆+SimpleMem use_llm开关+遗忘4曲线+DREAMS.md+undo端到端+策略防火墙L0/L1/L2+路径PID双验证，测试P0 6项全过，基础已打牢
- **前端**: 89KB单文件，毛玻璃blur 24px saturate 180%+渐变135deg #6366f1→#8b5cf6→#d946ef+mesh+知识图谱Canvas发光+渐变边+设置27可交互，10视图Windows专注，111→114API对齐，错误处理+skeleton+SSE重连+重要性排序
- **约束**: 离线优先本地LLM主引擎OpenAI兼容llama.cpp Qwen3 30B-A3B D:\llama.cpp\...gguf，云API仅可选教师，8GB VRAM 3060ti+32G适配，简体中文优先，源码英文，真实计算机控制非模拟，受控类型化接口，工具注册表+策略防火墙显式权限审计，商业级对标Operator/Claude Computer Use+Manus/Devin+PowerToys/Raycast
- **缺口**: 无桌面端，Web版需浏览器+手动启动后端+手动启动llama.cpp，无系统托盘+全局快捷键+开机自启+原生窗口控制+文件关联+原生通知，Windows真实环境未测试(WMI温度GPU进程树窗口移动DPI虚拟桌面)

### 1.2 目标
- **产品**: Zane Windows桌面端 v1.0，Tauri安装包，单exe安装，开箱即用，托盘常驻，Alt+Space全局唤起，聊天+26工具+记忆+进化+监控完整功能
- **用户**: Windows 10/11 Power用户，开发者，离线优先，本地LLM，已有llama.cpp或愿一键安装
- **成功标准**: 用户双击MSI安装→桌面快捷方式+开始菜单→启动→托盘图标→Alt+Space唤起主窗口→说"整理下载文件夹"→真实文件操作+确认弹窗+回收站+undo，全程离线，8GB VRAM可用

### 1.3 非目标
- iOS默认禁用保留代码ZANE_ENABLE_IOS=true才启用，降低风险专注Windows
- 不重写后端Python，复用现有基础
- 不引入Electron(体积大)，Tauri体积小10MB级前端+Rust轻量
- v1.0不做自动更新，手动更新

## 2. 方案对比 (已与用户确认方向)

### 2.1 Approach A: Tauri + Python Sidecar (推荐，2-3天)
- **前端**: 现有89KB index.html直接作为Tauri webview，少量适配Tauri API (window.__TAURI__)
- **后端**: backend/main.py打包zane-backend.exe via PyInstaller，Tauri sidecar配置，启动时自动启动，localhost:8000通信，健康检查/api/health
- **LLM**: 混合检测 - 启动时检测 D:\llama.cpp\llama-server.exe / C:\llama.cpp\ / 注册表 / PATH / config/model_paths.json，存在则用外置，回退内置sidecar llama-server.exe，Qwen3 30B-A3B
- **系统集成**: Tauri插件 tray+globalShortcut+autostart+notification+fs+dialog+shell
- **打包**: MSI via Tauri bundler WiX，包含zane-backend.exe+可选llama-server.exe+模型路径配置，~80-120MB，安装包签名可选
- **优势**: 复用100%现有代码，开发最快，Python WMI/Win32真实，测试已过
- **劣势**: 体积稍大，Python启动1-2s
- **风险**: 低，Tauri sidecar成熟

### 2.2 Approach B: Tauri + Rust重写 (不推荐，2-4周)
- Rust重写后端，wmi-rs+windows-rs，llama-cpp-rs
- 优势体积小15MB性能最好，劣势重写成本极高与现有基础脱节，WMI Rust生态不成熟

### 2.3 Approach C: Tauri + PyTauri嵌入 (备选，1-2周)
- PyTauri Python嵌入Rust，无sidecar进程
- 优势无进程通信开销体积40MB，劣势pytauri 0.3.x实验性文档少稳定性未知

**决策**: Approach A，符合"先把PC Windows做好，后端基础打牢"原则，现有基础已打牢复用最快验证桌面端，后续渐进式迁移热点Rust

## 3. 架构设计 (Approach A)

### 3.1 整体架构
```
Zane.exe (Tauri Rust主进程)
├── Webview: frontend/index.html (89KB毛玻璃+渐变+知识图谱) + Tauri API适配
├── Sidecar: zane-backend.exe (Python FastAPI 114API) --port 8000
│   ├── platform/windows/wmi_provider.py (WMI真实)
│   ├── platform/windows/win32_window.py (Win32真实)
│   ├── tools/file_tools.py (深模块) + tools_impl.py (兼容)
│   ├── memory/ 4层 + SimpleMem + forgetting + DREAMS.md
│   ├── policy_firewall + undo_stack + security
│   └── routers/ 18路由 + knowledge-graph 4路由
├── Sidecar: llama-server.exe (可选，混合检测)
│   └── Qwen3 30B-A3B D:\llama.cpp\...gguf
└── Tauri插件: tray + globalShortcut Alt+Space + autostart + notification + fs + dialog
```

### 3.2 目录结构
```
local-ai-agent/
├── src-tauri/ (新建)
│   ├── Cargo.toml (tauri 2.x + plugins)
│   ├── tauri.conf.json (app + bundle + sidecars + plugins)
│   ├── src/
│   │   ├── main.rs (setup sidecar + tray + shortcut + window)
│   │   ├── llm_detector.rs (混合检测外置/内置llama)
│   │   └── tray.rs (托盘菜单)
│   ├── icons/ (icon.ico + icon.png)
│   └── binaries/ (zane-backend-x86_64-pc-windows-msvc.exe + llama-server.exe)
├── frontend/ (现有，少量适配)
│   └── index.html (检测window.__TAURI__，用invoke替代部分fetch)
├── backend/ (现有，PyInstaller打包)
│   └── main.py (增加--port参数支持sidecar指定端口)
├── scripts/
│   ├── build_backend.py (PyInstaller打包zane-backend.exe)
│   └── build_tauri.py (cargo tauri build)
└── docs/superpowers/specs/ (本文件)
```

### 3.3 关键流程
1. **启动**: Tauri main.rs启动→检测llm_detector→启动zane-backend sidecar→健康检查/api/health轮询→启动llama sidecar(若需要)→显示主窗口
2. **托盘**: 最小化到托盘，托盘菜单: 显示主窗口/设置/退出，单击显示/隐藏
3. **全局快捷键**: Alt+Space注册，唤起主窗口聚焦聊天输入框
4. **通信**: 前端fetch http://localhost:8000/api/* (sidecar)，Tauri invoke用于原生操作(tray/autostart/notification)
5. **LLM混合**: 检测顺序 env MODEL_PATH > config/model_paths.json > D:\llama.cpp\ > C:\llama.cpp\ > 注册表 > PATH > 内置sidecar，找不到报错退出符合v0914-14
6. **安装包**: Tauri bundler生成MSI，包含sidecars，安装到Program Files，开始菜单快捷方式+桌面可选+开机自启选项

### 3.4 Tauri配置要点
- tauri.conf.json: app identifier com.zane.windows, productName Zane, version 0.9.14, bundle active, icon, resources, externalBin ["binaries/zane-backend", "binaries/llama-server"]
- Cargo.toml: tauri 2.2+, tauri-plugin-shell (sidecar), tray-icon, global-shortcut, autostart, notification, fs, dialog
- main.rs: tauri::Builder::default().plugin(tauri_plugin_shell::init()).plugin(tauri_plugin_global_shortcut::Builder::new().build()).plugin(tauri_plugin_autostart::init()).setup(|app| { 启动sidecar + tray + shortcut })

### 3.5 前端适配
- 检测window.__TAURI__存在则为桌面端
- isTauri = !!window.__TAURI__
- 托盘最小化: window.__TAURI__.window.getCurrentWindow().hide()替代window.close()
- 通知: window.__TAURI__.notification.sendNotification()替代浏览器Notification
- 文件对话框: window.__TAURI__.dialog.open()替代input file
- 后端地址: 桌面端固定http://localhost:8000，Web版可配置

### 3.6 后端适配
- main.py增加argparse --port支持sidecar指定端口
- tools_impl.py Windows真实API需在真实Windows测试，Linux演示结构真实
- 打包: pyinstaller --onefile --add-data "config;config" --add-data "frontend;frontend" backend/main.py --name zane-backend

## 4. 功能清单 (v1.0)

### 4.1 P0 必须 (桌面基础)
- [ ] Tauri项目初始化 src-tauri/ Cargo.toml tauri.conf.json
- [ ] Python sidecar打包 zane-backend.exe PyInstaller + 测试
- [ ] 主窗口显示现有前端 index.html
- [ ] Sidecar自动启动+健康检查+日志
- [ ] 系统托盘+菜单(显示/设置/退出)+单击切换
- [ ] 全局快捷键Alt+Space唤起+聚焦输入
- [ ] MSI安装包生成+安装测试
- [ ] LLM混合检测+启动

### 4.2 P1 重要 (体验增强)
- [ ] 开机自启选项+设置页联动
- [ ] 原生通知+前端通知统一
- [ ] 窗口状态记忆(位置/大小/最大化)
- [ ] 文件关联+拖拽文件到窗口
- [ ] 自动更新检查(仅检查，手动下载)
- [ ] 崩溃恢复+SSE重连+sidecar重启

### 4.3 P2 可选 (后续)
- [ ] 自动更新下载安装
- [ ] 多窗口(设置独立窗口)
- [ ] 原生菜单+上下文菜单
- [ ] 深度Windows集成(右键菜单"用Zane整理")

## 5. 技术约束

- **离线优先**: 本地LLM主引擎，云API仅可选教师，安装包不强制包含模型，用户自备或下载
- **安全**: 工具注册表+策略防火墙+待确认队列+undo端到端，桌面端额外文件系统权限Tauri fs scope限制
- **真实**: WMI+Win32真实API，Windows真实环境测试，Linux演示结构真实
- **商业级**: 对标PowerToys/Raycast，安装包签名，崩溃报告，日志
- **中文优先**: UI/日志/文档/回复中文，源码英文，UTF-8 BOM
- **版本**: 单版本v0914，历史归档docs/archive/，不再多版本并存

## 6. 风险与缓解

- **R1 Python打包体积大**: 缓解 - PyInstaller --onefile+UPX压缩，排除torch/transformers等大库(延迟加载)，目标80MB以内
- **R2 Sidecar启动慢**: 缓解 - 启动画面+skeleton，健康检查轮询，异步启动LLM，1-2s可接受
- **R3 Tauri Windows兼容**: 缓解 - Tauri 2.x Windows支持成熟，测试Win10/11，WebView2依赖检测
- **R4 WMI/Win32权限**: 缓解 - manifest请求管理员权限可选，普通权限+UAC提升，文档说明
- **R5 LLM模型路径**: 缓解 - 复用v0914-14优先级 env>config>默认探测，找不到报错退出，HF不自动下载检测缓存提示确认

## 7. 测试计划

- **单元**: test_windows_foundation 4/4 + test_forgetting 2/2 + test_undo_e2e 3/3 保持通过
- **集成**: Tauri启动→sidecar健康→LLM检测→聊天→工具调用→托盘→快捷键→安装包安装卸载
- **真实环境**: Windows 10/11真实机器测试WMI温度GPU进程树窗口移动DPI多显示器截图UIA
- **性能**: 启动时间<3s，内存<200MB空闲，包体积<120MB

## 8. 后续开发 (v1.1+)

- 性能优化: Rust重写热点(文件列表+进程监控)
- 功能: 右键菜单集成+文件关联+多窗口+自动更新
- 生态: 插件系统+技能市场
- 分发: Microsoft Store + Winget

---

**待用户确认后，进入writing-plans生成详细实现计划**
