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
    
    # v8.0 终极模块化版优先，目标500行+71路由模块化，失败回退v7/v6/v4/v3
    for version, desc in [
        ("backend.main_v8", "v8.0 终极模块化版 - 422行目标500行+71路由模块化10路由文件+自主进化v3.0 8模块闭环"),
        ("backend.main_v7", "v7.0 模块化重构优化版 - 6路由模块化 931行+51路由+自主进化v3.0 8模块闭环"),
        ("backend.main_v6", "v6.0 自主进化完整版 - 数据飞轮v3+模型双轨+真实训练+评估Harness+Prompt进化+技能基因"),
        ("backend.main_v4", "v4.0 A+C夯实 - SQLite唯一+20Skill+APScheduler+习惯学习+模块化+Canvas"),
        ("backend.main_v3", "v3.0 集成版"),
    ]:
        try:
            __import__(version)
            print(f"✅ 启动 {desc}")
            uvicorn.run(
                f"{version}:app",
                host="0.0.0.0",
                port=8000,
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
