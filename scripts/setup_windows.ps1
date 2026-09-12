# Zane AGI v1.0 - Windows 一键安装脚本
# 商业级 + 自我进化 + Windows深度控制

Write-Host @"
╔══════════════════════════════════════════════════╗
║   Zane AGI v1.0 - Windows 一键安装              ║
║   Reliable Local Computer Agent                  ║
║   Qwen3-30B-A3B MoE + 自我进化                   ║
╚══════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 未安装，请安装 Python 3.10+" -ForegroundColor Red
    exit 1
}

# 创建虚拟环境
if (-not (Test-Path "venv")) {
    Write-Host "📦 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
}

# 激活虚拟环境
Write-Host "🔧 激活虚拟环境..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# 安装依赖
Write-Host "📥 安装依赖..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

# 检查 llama.cpp
$llamaPath = "D:\llama.cpp"
if (Test-Path $llamaPath) {
    Write-Host "✅ 发现 llama.cpp: $llamaPath" -ForegroundColor Green
    $modelPath = "D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf"
    if (Test-Path $modelPath) {
        Write-Host "✅ 发现模型: $modelPath" -ForegroundColor Green
        $size = (Get-Item $modelPath).Length / 1GB
        Write-Host "   大小: $([math]::Round($size,1)) GB" -ForegroundColor Gray
    } else {
        Write-Host "⚠️ 模型未找到: $modelPath" -ForegroundColor Yellow
        Write-Host "   请下载 Qwen3-30B-A3B IQ4_XS 到该路径" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️ 未发现 llama.cpp: $llamaPath" -ForegroundColor Yellow
    Write-Host "   将使用演示模式，功能受限" -ForegroundColor Yellow
}

# 创建数据目录
Write-Host "📁 创建数据目录..." -ForegroundColor Yellow
@("data", "data/memory", "data/traces", "data/screenshots", "models", "memory/dreaming/Light", "memory/dreaming/REM", "memory/dreaming/Deep") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

# 创建 .env
if (-not (Test-Path ".env")) {
    Write-Host "📝 创建 .env 配置..." -ForegroundColor Yellow
    @"
# Zane AGI v1.0 配置
LLM_API_BASE=http://localhost:8080/v1
LLM_MODEL=qwen3-30b-a3b
BING_API_KEY=
ZANE_TOKEN=
"@ | Out-File -FilePath ".env" -Encoding utf8
}

Write-Host @"
✅ 安装完成！

下一步：

1. 启动 llama.cpp server（另开终端）：
   D:\llama.cpp\llama-server.exe -m D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf --host 0.0.0.0 --port 8080 --ctx-size 32768 --n-gpu-layers 35 --flash-attn --cont-batching

2. 启动 Zane AGI：
   python run.py
   或
   .\venv\Scripts\python.exe -m uvicorn backend.main_v3:app --host 0.0.0.0 --port 8000

3. 打开浏览器：
   http://localhost:8000

4. API文档：
   http://localhost:8000/docs

技术诚实，无吹嘘，代码维护现实，AI解释现实
"@ -ForegroundColor Green
