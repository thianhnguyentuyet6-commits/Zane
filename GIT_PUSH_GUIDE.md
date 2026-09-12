# Git 推送指南 - Zane AGI

你的仓库：https://github.com/thianhnguyentuyent6-commits/Zane

## 为什么无法自动推送？

Linux 容器无法读取 GitHub 凭证，需要你本地操作。

## 一键推送（Windows PowerShell）

在你的 Windows 电脑上，打开 PowerShell，执行：

```powershell
# 1. 克隆你的仓库（若已有则跳过）
git clone https://github.com/thianhnguyentuyet6-commits/Zane.git
cd Zane

# 2. 下载本项目的最新代码
# 方式A：从当前环境下载（我已打包）
# 下载链接：你需要从 Arena 下载 /home/user/local-ai-agent 整个文件夹

# 方式B：手动复制文件
# 将 local-ai-agent 下的所有文件复制到 Zane 文件夹

# 3. 推送
git add .
git commit -m "v2.0 Zane AGI - 自我进化 + Windows深度控制 + Qwen3-30B-A3B"
git push origin main
```

## 或者：直接在你本地创建

```powershell
# 在 D:\Zane 目录
git init
git remote add origin https://github.com/thianhnguyentuyet6-commits/Zane.git
# 复制所有文件到此目录
git add .
git commit -m "v2.0"
git branch -M main
git push -u origin main
```

## 配置 GitHub Actions - Windows 真实测试

创建 `.github/workflows/windows-test.yml`:

```yaml
name: Windows Real Test

on: [push]

jobs:
  test-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install wmi pywin32
      - run: python -m pytest tests/test_windows_real.py -v
      - run: python -m backend.main_v2 --help
```

这样每次推送，都会在真实 Windows 上测试 WMI、窗口、截图是否准确。

## 模型路径

你的模型：`D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf`

已在代码中写死，`backend/llm/model_manager.py` 会自动发现。

若要切换，在设置页或 API 调用：
```
POST /api/models/switch?model_id=qwen3-30b-a3b-iq4xs
```

## 自我进化如何工作？

1. **日常使用**：每次任务成功，自动收集到 `data/training/sft.jsonl`
2. **检查**：`GET /api/evolution/status` 查看是否准备好（需50条样本）
3. **触发**：`POST /api/evolution/start?manual=true` 手动触发，或等凌晨2点自动
4. **训练**：生成 `scripts/train_lora.py`，在 Windows 上执行：
   ```powershell
   pip install unsloth torch trl transformers datasets
   python scripts/train_lora.py
   ```
5. **晋升**：评估成功率提升，自动切换到新 LoRA

## 创新实验

在 `experiments/` 目录，3个实验独立运行，不影响主流程，允许失败。

- `moe_personality.py`: 分析 MoE 专家激活
- `dreaming_debate.py`: 梦境辩论
- `skill_gene.py`: 技能基因进化

---

**推送后，告诉我，我可以继续帮你配置 Actions 和测试。**
