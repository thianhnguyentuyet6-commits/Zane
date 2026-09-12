# Zane AGI - Git 推送脚本 - 需要Token
# 使用方法： .\scripts\push_with_token.ps1 -Token YOUR_GITHUB_TOKEN

param(
    [string]$Token = "",
    [string]$Message = "v1.0 成品 - 第一版成品达成"
)

Write-Host "=== Zane AGI Git 推送 ===" -ForegroundColor Cyan

if (-not $Token) {
    Write-Host "❌ 需要提供 GitHub Token" -ForegroundColor Red
    Write-Host @"
获取Token步骤：
1. 打开 https://github.com/settings/tokens
2. 点击 Generate new token → Tokens (classic)
3. 勾选：
   - repo (全部)
   - workflow
4. 生成，复制Token（ghp_开头）

然后执行：
.\scripts\push_with_token.ps1 -Token ghp_你的Token

或者设置环境变量：
`$env:GITHUB_TOKEN="ghp_..."`
.\scripts\push_with_token.ps1
"@
    exit 1
}

# 检查是否在git仓库
if (-not (Test-Path ".git")) {
    Write-Host "❌ 不在git仓库，请在项目根目录执行" -ForegroundColor Red
    exit 1
}

# 配置remote URL带Token
$remoteUrl = "https://$Token@github.com/thianhnguyentuyet6-commits/Zane.git"
Write-Host "🔧 配置远程URL..." -ForegroundColor Yellow
git remote set-url origin $remoteUrl

# 检查状态
Write-Host "📊 检查状态..." -ForegroundColor Yellow
git status --short

# 添加
Write-Host "📦 添加文件..." -ForegroundColor Yellow
git add .

# 提交
Write-Host "💾 提交: $Message" -ForegroundColor Yellow
git commit -m $Message

# 推送
Write-Host "🚀 推送到 origin main..." -ForegroundColor Yellow
try {
    git push origin main
    Write-Host "✅ 推送成功！" -ForegroundColor Green
    Write-Host "仓库: https://github.com/thianhnguyentuyet6-commits/Zane" -ForegroundColor Cyan
} catch {
    Write-Host "❌ 推送失败: $_" -ForegroundColor Red
    Write-Host "可能原因：Token权限不足，需勾选 repo + workflow" -ForegroundColor Yellow
}

# 恢复URL（移除Token，避免泄露）
Write-Host "🔒 清理Token..." -ForegroundColor Yellow
git remote set-url origin https://github.com/thianhnguyentuyet6-commits/Zane.git

Write-Host "完成" -ForegroundColor Green
