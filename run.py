# -*- coding: utf-8 -*-
"""
启动脚本 - 一键启动本地AI电脑助手
"""
import os
import sys
import subprocess

def main():
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   本地AI电脑助手 - Local AI Computer Agent      ║
    ║   私有 · 自主 · 运行在你的PC上                  ║
    ║   代码维护现实 · AI解释现实                     ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # 检查依赖
    try:
        import fastapi, uvicorn, psutil, PIL
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("正在安装依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # 确保数据目录
    os.makedirs("data/screenshots", exist_ok=True)
    print("✅ 数据目录就绪")
    
    # 启动服务
    print("""
    启动服务...
    - 后端API: http://127.0.0.1:8000
    - 前端控制台: http://127.0.0.1:8000/
    - API文档: http://127.0.0.1:8000/docs
    - 本地LLM: http://127.0.0.1:8080/v1 (若已启动llama.cpp)
    
    提示：
    - 若无本地模型，系统自动进入离线演示模式，仍可体验完整流程
    - 支持中文口语指令：帮我打开微信、看看什么程序占内存最多等
    """)
    
    # 切换到backend目录并启动
    backend_path = os.path.join(os.path.dirname(__file__), "backend")
    sys.path.insert(0, os.path.dirname(__file__))
    
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()
