# Windows桌面端 Tauri 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建Zane Windows桌面端v1.0，Tauri 2.x + Python FastAPI Sidecar + 混合LLM检测，MSI安装包，托盘常驻+Alt+Space全局快捷键，复用现有114API+26工具完整功能

**Architecture:** Tauri Rust主进程管理Webview(复用89KB前端)+Sidecar Python FastAPI(114API)+Sidecar llama.cpp(混合检测外置/内置)，通过localhost:8000通信，Tauri插件提供托盘/快捷键/自启/通知原生能力，PyInstaller打包后端，Tauri bundler生成MSI安装包80-120MB

**Tech Stack:** Tauri 2.2+ (Rust), Python 3.11+ FastAPI 114API, PyInstaller 6.x, WebView2, WMI+Win32 (platform/windows/), llama.cpp Qwen3 30B-A3B, tauri-plugin-shell/tray-icon/global-shortcut/autostart/notification/fs/dialog

**Spec:** docs/superpowers/specs/2026-09-13-windows-desktop-tauri-design.md

## Global Constraints

- 离线优先：本地LLM主引擎OpenAI兼容llama.cpp，云API仅可选教师，安装包不强制包含模型，用户自备或下载
- 安全：工具注册表+策略防火墙L0/L1/L2+待确认队列+undo端到端，桌面端额外Tauri fs scope限制
- 真实：WMI+Win32真实API，Windows真实环境测试，Linux演示结构真实
- 商业级：对标PowerToys/Raycast，安装包签名，崩溃报告，日志
- 中文优先：UI/日志/文档/回复简体中文，源码英文，UTF-8 BOM
- 版本：单版本v0914，历史归档docs/archive/，不再多版本并存
- 模型路径优先级：env MODEL_PATH/QWEN_MODEL_PATH/LLM_MODEL_PATH/ZANE_MODEL_PATH/HF_MODEL_PATH > config/model_paths.json > 默认探测，找不到报错退出，HF不自动下载检测缓存提示确认
- iOS默认禁用：ZANE_ENABLE_IOS=false，专注Windows，保留代码
- 测试：test_windows_foundation 4/4 + test_forgetting 2/2 + test_undo_e2e 3/3 必须保持通过
- 性能：启动<3s，内存<200MB空闲，包体积<120MB

---

## 7 Tasks - 已完成 22/22测试通过

### Task 1: Tauri项目初始化 ✅
Task 2: Python Sidecar打包 ✅
Task 3: LLM混合检测+Backend管理器 ✅
Task 4: 系统托盘+全局快捷键 ✅
Task 5: 开机自启+原生通知+窗口状态记忆 ✅
Task 6: MSI安装包生成 ✅
Task 7: 集成测试+文档 ✅

详见 docs/WINDOWS_DESKTOP_REPORT.md
