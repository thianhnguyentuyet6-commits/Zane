# -*- coding: utf-8 -*-
"""
Zane AGI v1.0 - 一键启动
可靠本地计算机代理
"""
import os
import sys
import time

if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def main():
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   Zane AGI v1.0 - 可靠本地计算机代理             ║
    ║   Reliable Local Computer Agent                  ║
    ║   代码维护现实，AI解释现实                       ║
    ║   8层精简 + 10模块Runtime + 安全加固             ║
    ║   Qwen3-30B-A3B MoE + 自我进化                   ║
    ╚══════════════════════════════════════════════════╝
    
    启动中...
    """)
    
    # 检查依赖
    try:
        import fastapi, uvicorn, psutil
        print("✅ 核心依赖已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 检查前端
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend_path):
        print(f"✅ 前端已就绪: {frontend_path}")
    else:
        print(f"⚠️ 前端未找到: {frontend_path}")
    
    # 启动
    import uvicorn
    print("""
    🚀 启动 Zane AGI v1.0
    📍 前端: http://localhost:8000
    📚 API文档: http://localhost:8000/docs
    🔧 健康检查: http://localhost:8000/api/health
    
    按 Ctrl+C 停止
    """)
    
    # 优先v4 A+C夯实，失败回退v3
    try:
        import backend.main_v4
        print("✅ 启动 v4.0 A+C夯实 - SQLite唯一+20Skill+APScheduler+习惯学习+模块化+Canvas")
        uvicorn.run(
            "backend.main_v4:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"v4启动失败，回退v3: {e}")
        uvicorn.run(
            "backend.main_v3:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )

if __name__ == "__main__":
    main()
