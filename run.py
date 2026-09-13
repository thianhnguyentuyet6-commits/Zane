# -*- coding: utf-8 -*-
"""
Zane AGI v0913 - 单版本整合版 一键启动
- 单版本：不再多版本并存，历史归档legacy/
- 启动日志3行：Runtime版本+Platform Provider真实/演示+演示工具列表+环境变量控制
- 环境变量显式控制：ZANE_RUNTIME=v2/v3 ZANE_PLATFORM=auto/windows/demo ZANE_DEMO=auto/true/false ZANE_LLM_PROVIDER=local/openai/claude ZANE_PORT=8000
"""
import os
import sys
import time

if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def main():
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   Zane AGI v0913 - 单版本整合版                  ║
    ║   单版本+103API+8层架构+6缺点全修                ║
    ║   启动日志3行+平台状态条+demo_mode区分           ║
    ║   安全硬化NEED_CONFIRM阻断+飞轮透明规格          ║
    ║   代码维护现实，AI解释现实                       ║
    ╚══════════════════════════════════════════════════╝
    
    启动中...
    """)
    
    # 环境变量
    runtime = os.getenv("ZANE_RUNTIME", "v3")
    platform_mode = os.getenv("ZANE_PLATFORM", "auto")
    demo_mode = os.getenv("ZANE_DEMO", "auto")
    llm_provider = os.getenv("ZANE_LLM_PROVIDER", "local")
    port = os.getenv("ZANE_PORT", "8000")
    
    print(f"环境变量: ZANE_RUNTIME={runtime} ZANE_PLATFORM={platform_mode} ZANE_DEMO={demo_mode} ZANE_LLM_PROVIDER={llm_provider} ZANE_PORT={port}")
    print(f"  Runtime: {runtime} - v2/v3切换")
    print(f"  Platform: {platform_mode} - auto/windows/demo")
    print(f"  Demo: {demo_mode} - auto/true/false")
    print(f"  LLM Provider: {llm_provider} - local/openai/claude")
    print(f"  Port: {port}")
    print()
    
    # 检查依赖
    try:
        import fastapi, uvicorn, psutil
        print("✅ 核心依赖已安装: fastapi uvicorn psutil")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 检查可选依赖
    optional_deps = []
    try:
        import loguru
        optional_deps.append("loguru")
    except ImportError:
        print("⚠️ loguru未安装，日志为print")
    
    try:
        import slowapi
        optional_deps.append("slowapi")
    except ImportError:
        print("⚠️ slowapi未安装，限流不可用")
    
    try:
        import rapidocr_onnxruntime
        optional_deps.append("rapidocr 50MB")
    except ImportError:
        print("⚠️ rapidocr未安装，OCR不可用")
    
    try:
        import sqlite_vec
        optional_deps.append("sqlite-vec")
    except ImportError:
        print("⚠️ sqlite-vec未安装，向量搜索不可用")
    
    try:
        import filelock
        optional_deps.append("filelock")
    except ImportError:
        print("⚠️ filelock未安装，文件锁不可用")
    
    if optional_deps:
        print(f"✅ 可选依赖: {', '.join(optional_deps)}")
    
    # 检查前端
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend_path):
        print(f"✅ 前端已就绪: {frontend_path}")
    else:
        print(f"⚠️ 前端未找到: {frontend_path}")
    
    # 检查单版本
    main_path = os.path.join(os.path.dirname(__file__), "backend", "main.py")
    tools_path = os.path.join(os.path.dirname(__file__), "backend", "tools_impl.py")
    firewall_path = os.path.join(os.path.dirname(__file__), "backend", "policy_firewall_v0913.py")
    
    print()
    print("单版本检查:")
    print(f"  {'✅' if os.path.exists(main_path) else '❌'} backend/main.py - Zane v0913单版本整合版")
    print(f"  {'✅' if os.path.exists(tools_path) else '❌'} backend/tools_impl.py - 统一工具实现21工具")
    print(f"  {'✅' if os.path.exists(firewall_path) else '❌'} backend/policy_firewall_v0913.py - 硬化版防火墙")
    
    legacy_path = os.path.join(os.path.dirname(__file__), "backend", "legacy")
    if os.path.exists(legacy_path):
        legacy_files = os.listdir(legacy_path)
        print(f"  ✅ backend/legacy/ - 历史版本归档 {len(legacy_files)}个文件")
    
    # 启动
    import uvicorn
    print(f"""
    🚀 启动 Zane AGI v0913 单版本整合版
    📍 前端: http://localhost:{port}
    📚 API文档: http://localhost:{port}/docs (8层架构tags分组)
    🔧 健康检查: http://localhost:{port}/api/health (启动日志3行)
    🛡️ 平台状态: http://localhost:{port}/api/platform/status (真实/演示区分)
    📊 飞轮统计: http://localhost:{port}/api/flywheel/stats (评分分布透明)
    🔒 待确认: http://localhost:{port}/api/security/pending (NEED_CONFIRM阻断)
    
    环境变量控制:
      ZANE_RUNTIME=v3 uvicorn run.py (Runtime v2/v3切换)
      ZANE_PLATFORM=windows ZANE_DEMO=false python run.py (真实模式)
      ZANE_LLM_PROVIDER=local python run.py (本地LLM)
    
    按 Ctrl+C 停止
    """)
    
    # v0913 单版本优先，失败回退legacy
    for version, desc in [
        ("backend.main", "v0913 单版本整合版 - 单版本+103API+8层架构+6缺点全修+启动日志3行+平台状态条+安全硬化+飞轮透明"),
        ("backend.legacy.main_v8", "v8.0 终极模块化版 - 422行+71路由模块化"),
        ("backend.legacy.main_v7", "v7.0 模块化重构 - 6路由模块化51路由"),
        ("backend.legacy.main_v6", "v6.0 自主进化完整版 - 8模块闭环"),
    ]:
        try:
            __import__(version)
            print(f"✅ 启动 {desc}")
            uvicorn.run(
                f"{version}:app",
                host="0.0.0.0",
                port=int(port),
                reload=False,
                log_level="info"
            )
            return
        except Exception as e:
            print(f"⚠️ {version}启动失败: {e}，尝试下一版本...")
            import traceback
            traceback.print_exc()
            continue
    
    print("❌ 所有版本启动失败")
    print("请检查依赖: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
