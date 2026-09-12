# 个人AGI管家 - 自我进化架构
## 从 Qwen3-30B-A3B 到“你的模型”

> 目标：让助手在日常运行中，静默时自动微调自己，一步步不再是 Qwen3.6
> 核心思想：OpenClaw Dreaming + 持续学习 + LoRA进化 + 技能蒸馏

---

### 一、为什么 Qwen3-30B-A3B 非常适合做自我进化

**Qwen3-30B-A3B 的特性：**
- MoE 架构：总参数 30B，激活 3B，推理时只用 3B，显存需求低（Q4下 ~16GB 可跑）
- A3B：3B Active，意味着微调时可以只微调激活的专家 + 共享专家，成本低
- Qwen3 原生支持 Function Calling、长上下文、中文极强

**为什么适合自我进化：**
- MoE 的专家可以被“个性化”：让某些专家专门处理你的习惯（例如 Expert 12 专门处理你的文件整理习惯）
- 激活参数小，QLoRA 微调可行：4bit量化 + LoRA rank 32，24GB 显存可训练
- 推理快，适合日常使用，不会因为进化而变慢

---

### 二、自我进化飞轮 - 数据从哪里来？

```
日常使用
  ├─ 成功任务 → SFT 数据 (Instruction, Input, Output)
  ├─ 失败+修正 → DPO 偏好数据 (Chosen vs Rejected)
  ├─ 技能 → 参数化指令数据
  ├─ 记忆 → 知识数据 (你的习惯、环境、偏好)
  └─ 验证失败 → 反思数据 (为什么错，下次怎么做)
       ↓
  [数据清洗层] 去重、脱敏、格式化为 ShareGPT/Alpaca
       ↓
  [经验池] Replay Buffer，防止灾难性遗忘
       ↓
  [静默微调] 凌晨2点，CPU<20%，自动触发
       ↓
  [评估层] 历史任务回放，成功率是否提升
       ↓
  [模型晋升] 新 LoRA 合并，旧版本保留，可回滚
       ↓
  [你] 第二天醒来，助手更懂你了
```

#### 2.1 数据自动收集（已实现 70%）

**现在已有的：**
- `experiences.json`：问题→解法→验证
- `skills.json`：可复用流程
- `episodic.json`：情景记忆

**需要增强的：**
- **成功轨迹**：每次任务成功的完整 Tool Calls + 推理，转为 SFT
  - 格式：`{"instruction": "帮我打开微信", "input": "当前窗口...", "output": "调用 list_windows → launch_application → 验证"}`
- **失败修正**：失败后用户纠正或AI自反思，转为 DPO
  - `Chosen`: 正确做法
  - `Rejected`: 失败做法
- **偏好**：你总是让它“先截图再操作”→ 学习你的偏好
- **知识**：`C:\Users\...` 路径、微信安装位置、你常用的3个文件夹

**实现：** `backend/memory/data_flywheel.py`
- 监听 `agent_runtime` 每次执行
- 自动生成训练样本，存入 `data/training/sft.jsonl` + `dpo.jsonl`
- 每天去重，质量过滤（用小模型打分）

#### 2.2 静默微调 - 如何不影响日常使用

**触发条件（可配置）：**
- 空闲 30 分钟 + CPU < 20% + 内存 < 70%
- 或 定时凌晨 2:00-5:00
- 或 手动：设置页“立即梦境学习”

**技术栈（低配可用）：**
- **QLoRA**：4bit 量化 + LoRA，rank=32, alpha=64, target_modules=`["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]`
- **Unsloth**：2倍速微调，显存减半，支持 Qwen3
- **Axolotl** 或 **LLaMA-Factory**：配置文件驱动，适合自动化
- **CPU Offload**：若显存不足，自动切 CPU 训练（慢但可行）
- **专家微调**：只微调 MoE 中被频繁激活的 2-3 个专家，其余冻结，极大降低成本

**训练参数（针对 30B-A3B）：**
```yaml
model: Qwen/Qwen3-30B-A3B
quantization: q4_k_m (推理) + nf4 (训练)
lora_rank: 32
lora_alpha: 64
batch_size: 1
gradient_accumulation: 8
learning_rate: 2e-4
epochs: 1-3 (每次增量)
max_seq_length: 4096
replay_ratio: 0.3 (30%旧数据防止遗忘)
```

**流程：**
1. 检查 `data/training/` 是否有 >50 条新样本
2. 合并 Replay Buffer（旧的 100 条高质量样本）
3. 启动 `unsloth` 训练，生成 `lora_adapter_YYYYMMDD`
4. 合并测试：用新 LoRA 跑历史 20 个任务，成功率是否提升
5. 若提升 >5%，晋升为当前模型，旧版本备份
6. 若下降，回滚，记录失败原因到经验

**实现：** `backend/learning/evolution_engine.py` + `backend/learning/unsloth_trainer.py`

#### 2.3 避免灾难性遗忘 - 关键

- **Replay Buffer**：保留 20% 通用数据 + 30% 你的历史高质量数据
- **技能 LoRA 分离**：每个技能一个小 LoRA（例如 `file_organize_lora`），按需加载，不污染主模型
- **模型版本管理**：`models/versions/` 保留最近5版，可一键回滚
- **评估集**：`data/eval/` 包含 100 个你的常用任务，训练后自动评估

#### 2.4 从 Qwen3.6 到“你的模型”

**阶段1：习惯学习（1-2周）**
- 数据：你的文件路径、常用应用、口语习惯
- 效果：它不再问“微信在哪”，直接知道 `C:\Program Files\...`

**阶段2：技能内化（1个月）**
- 数据：成功的工具链
- 效果：它学会“先枚举窗口再启动”，不需要每次都推理

**阶段3：偏好对齐（2个月）**
- 数据：DPO 偏好
- 效果：它知道你喜欢“先截图预览再删除”，自动遵守

**阶段4：专家特化（3个月+）**
- 数据：MoE 专家路由分析
- 效果：Expert 7 专门处理你的文件任务，Expert 12 专门处理窗口，推理更快更准

**最终：** 模型权重还是 Qwen3，但 LoRA + 专家路由 + 记忆，已经是你的专属模型，不再是通用 Qwen。

---

### 三、Windows API 真实化 - Git 仓库联动方案

**你提到的：** Linux容器无法真实测试 Windows API

**我的方案：**

#### 3.1 项目结构优化（为什么这样做）

```
local-ai-agent/
├── backend/
│   ├── platform/
│   │   ├── base.py (抽象接口)
│   │   ├── windows/ (真实实现)
│   │   │   ├── wmi_provider.py (WMI真实数据)
│   │   │   ├── win32_window.py (EnumWindows真实)
│   │   │   ├── uia_provider.py (UI Automation)
│   │   │   ├── dwm_thumbnail.py (缩略图)
│   │   │   └── registry.py (注册表)
│   │   ├── linux/ (Linux fallback，演示用)
│   │   └── darwin/ (macOS)
│   ├── tools/ (调用 platform 抽象，不直接调 win32)
│   └── ...
├── frontend/
├── scripts/
│   ├── setup_windows.ps1 (一键安装依赖，UTF-8 BOM)
│   ├── install_paddleocr.ps1
│   └── dev.ps1
├── tests/
│   ├── test_windows_real.py (需在真实Windows跑)
│   └── test_linux_mock.py
└── .github/
    └── workflows/
        └── windows-test.yml (GitHub Actions Windows Runner)
```

**为什么这样做：**
- **抽象层**：`platform/base.py` 定义接口，Windows/Linux 实现不同，Agent 不关心平台，商业级跨平台标准做法（类似 VS Code）
- **真实/模拟分离**：Linux 上用 `linux/` 模拟，Windows 上用 `windows/` 真实，测试可分别跑
- **GitHub Actions**：免费 Windows Runner，每次 push 自动在真实 Windows 上跑 `test_windows_real.py`，保证准确性

#### 3.2 Git 仓库联动

**你提供仓库后，我可以：**
1. **初始化 Git**：`git init` + `.gitignore` + `README` 商业级
2. **推送**：你给我仓库 URL + Token（或你先建空仓库），我推送完整重构版
3. **Actions**：自动配置 Windows 测试，每次提交验证 WMI、窗口、截图真实性
4. **协作**：你本地 Windows 跑 `python -m pytest tests/test_windows_real.py -v`，失败日志自动提 Issue

**请提供：**
- Git 仓库 URL（GitHub/Gitee/GitLab）
- 是否公开/私有
- 你希望的分支策略

---

### 四、创新与试错 - 允许失败的实验

你提到“AI可能无法接受新事物，甚至在创造这一块不擅长，但现在就是要你学会创造，创新，并加以实验，允许进行试错。”

**我提议的 3 个创新实验（高风险高回报）：**

#### 实验1：MoE 专家人格化
- **想法**：给每个 MoE 专家起名字、人格，Expert 3 是“文件管家”、Expert 12 是“窗口管家”
- **实现**：分析专家激活路由，统计每个专家在什么任务激活最多，自动命名
- **价值**：可视化、可解释，未来可手动分配任务给特定专家
- **风险**：可能不准，需要大量数据
- **试错**：先做分析工具，不影响主流程

#### 实验2：梦境对话
- **想法**：凌晨 Dreaming 时，让两个 LoRA 互相辩论，一个扮演“谨慎派”、一个扮演“激进派”，辩论出最佳经验
- **实现**：用当前模型生成正反观点，DPO 训练
- **价值**：类似人类做梦时整理记忆，可能产生新技能
- **风险**：可能产生幻觉
- **试错**：辩论结果需人工审核（设置页显示“梦境辩论”）

#### 实验3：技能基因进化
- **想法**：技能像基因一样变异、交叉、选择
- **实现**：两个技能 `文件整理` + `窗口切换` 交叉，产生 `整理时自动聚焦文件管理器`
- **价值**：自动发明新技能
- **风险**：可能产生无用技能
- **试错**：新技能标记为“实验”，需手动晋升

**我会为每个实验写 `experiments/` 目录，独立运行，不影响主程序，允许失败。**

---

### 五、完整执行计划（融合版）

#### Phase 1: 地基 + 模型管理（2天）- 立即执行
- [ ] 重写 `platform/windows/` 真实 WMI、窗口、截图
- [ ] 模型管理器：支持 Qwen3-30B-A3B，自动发现，切换，健康检查
- [ ] Git 结构重构 + Windows Actions
- [ ] 通知中心 + 分级确认 + 撤销栈

#### Phase 2: Harness 融合 + 数据飞轮（2天）
- [ ] OpenAI 严格Schema + Claude Set-of-Mark + DeepSeek DAG + 验证闭环
- [ ] 数据飞轮：自动收集 SFT/DPO 数据
- [ ] Replay Buffer + 评估集

#### Phase 3: 自我进化引擎（3天）- 核心创新
- [ ] QLoRA + Unsloth 训练器
- [ ] 静默触发 + 版本管理 + 回滚
- [ ] Dreaming 定时任务
- [ ] 3个创新实验

#### Phase 4: 商业级打磨 + iOS预留（1.5天）
- [ ] 商业级UI重设计
- [ ] iOS 远程 API 预留（8002端口）
- [ ] 系统托盘 + 快捷键 + 性能监控
- [ ] 低配优化

#### Phase 5: 文档 + 测试（0.5天）
- [ ] Windows 真实测试指南
- [ ] 自我进化手册

**总计：约 9 天，分阶段交付，每阶段可独立验证**

---

### 六、需要你现在决定的

1. **Git 仓库**：请提供 URL，我立即重构并推送
2. **是否同意自我进化架构**：允许它在静默时微调自己，生成 LoRA
3. **Qwen3-30B-A3B 路径**：你的模型在 `C:\models\` 还是 Ollama？
4. **是否允许实验**：3个创新实验是否都要尝试？

---

**我的思考：**
- 传统 Agent 是工具调用，你要的是**会进化的生命体**
- Qwen3-30B-A3B 的 MoE 特性非常适合个性化，3B激活让微调可行
- 关键不是一次微调，而是**数据飞轮**：用得越多，数据越多，模型越懂你
- 商业级不是功能多，而是**每个功能都准确、可回滚、可解释**
- 允许试错意味着**实验隔离**，不影响主流程

请提供 Git 仓库，我立即开始 Phase 1 + 自我进化地基。
