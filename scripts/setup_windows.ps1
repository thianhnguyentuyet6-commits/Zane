# -*- coding: utf-8 -*-
# Windows 一键安装脚本 - UTF-8 with BOM for Windows compatibility
# 本地AI电脑助手 - Windows 深度控制版

Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   本地AI电脑助手 - Windows 安装        ║" -ForegroundColor Cyan
Write-Host "║   私有 · 自主 · 自我进化              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan

# 检查 Python
Write-Host "`n[1/5] 检查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    exit 1
}

# 检查模型
Write-Host "`n[2/5] 检查模型..." -ForegroundColor Yellow
$modelPath = "D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf"
if (Test-Path $modelPath) {
    $size = (Get-Item $modelPath).Length / 1GB
    Write-Host "✅ 找到模型: $modelPath ($([math]::Round($size,1)) GB)" -ForegroundColor Green
} else {
    Write-Host "⚠️  未找到模型: $modelPath" -ForegroundColor Yellow
    Write-Host "   请确保模型在 D:\llama.cpp\ 目录" -ForegroundColor Yellow
}

# 安装依赖
Write-Host "`n[3/5] 安装依赖..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install wmi pywin32
Write-Host "✅ 基础依赖安装完成" -ForegroundColor Green

# 可选：Unsloth 用于自我进化
Write-Host "`n[4/5] 是否安装自我进化组件 (Unsloth)？需要 24GB VRAM (y/n)" -ForegroundColor Yellow
$installUnsloth = Read-Host
if ($installUnsloth -eq "y") {
    pip install unsloth torch --index-url https://download.pytorch.org/whl/cu121
    pip install trl transformers datasets accelerate
    Write-Host "✅ Unsloth 安装完成" -ForegroundColor Green
}

# 启动
Write-Host "`n[5/5] 启动服务..." -ForegroundColor Yellow
Write-Host "   后端: http://127.0.0.1:8001" -ForegroundColor Cyan
Write-Host "   前端: http://127.0.0.1:8001/" -ForegroundColor Cyan
Write-Host "   模型: $modelPath" -ForegroundColor Cyan
Write-Host "`n按 Ctrl+C 停止`n" -ForegroundColor Gray

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
