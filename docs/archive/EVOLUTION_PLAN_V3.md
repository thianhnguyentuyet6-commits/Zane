# 自主进化引擎 v3.0 完整优化计划 - 适应性与自主进化性为核心

> 基于用户选择：都要，最重适应性与自主进化，凌晨2点+空闲30分自动，平衡安全，GGUF推理+HF训练双轨

## 一、现状诊断

### 已有 v2.5
- 思考预算 /think 32K /no_think 8K 动态
- Ralph Loop fresh context + prd.json passes布尔 + 3护栏
- 有界自校正 UCSL 3轮 + 不确定度校准
- 技能库 SAGE Sequential Rollout
- SimpleMem +26.4% F1 30x Token
- 梦境循环 3阶段
- Q-Evolve in-distribution critic + process reward 模拟

### 缺陷
1. **训练未真实闭环**：`unsloth_trainer.py` 仅生成脚本字符串，`evolution_engine.start_evolution()` 中 `await asyncio.sleep(1.5)` 模拟，未真实调用 torch/unsloth，未检测VRAM，未管理HF路径
2. **数据飞轮无质量**：`data_flywheel.py` 收集所有成功轨迹，无过滤、无去重、无重要性评分、无SimpleMem压缩、无安全过滤（危险操作可能污染）
3. **评估无真实回放**：eval_result 硬编码 `old 0.82 new 0.91`，未真实回放 benchmark_suite 20任务，未实现 Replay Buffer防遗忘，未实现+2%晋升阈值
4. **Prompt/策略未进化**：Darwin Gödel Machine、EvolveR、AlphaEvolve 未实现，prompt写死在代码
5. **技能基因未进化**：skill_library 仅保存，未实现基因交叉变异、优胜劣汰
6. **调度未资源感知**：check_idle 仅CPU/内存，未检测VRAM、未检测是否插电、未检测用户是否在游戏/会议
7. **记忆未真正巩固**：dream_loop 与 dreaming.py 双轨，4层记忆未与SimpleMem打通，遗忘机制未实现

## 二、目标：适应性与自主进化性

### 适应性定义
- 任务适应：根据用户习惯自动调整工具链，例如用户常整理下载→自动技能`organize_downloads`，思考预算自动/think→/no_think
- 环境适应：Windows/Linux自动切换，WMI→psutil，路径自动映射，资源不足自动降级
- 模型适应：GGUF推理，HF训练，VRAM 24GB训30B，16GB训7B或仅技能蒸馏

### 自主进化性定义
- 数据自主：成功/失败自动收集，无需人工标注，安全过滤
- 训练自主：凌晨2点+空闲30分自动触发，资源感知，失败自动重试3次指数退避
- 评估自主：基准任务自动回放，成功率+2%自动晋升，否则回滚，生成报告
- 策略自主：Prompt/工具链/验证规则自动进化，优胜劣汰
- 记忆自主：梦境循环自动整理，低价值自动遗忘，高价值晋升长期

## 三、v3.0 架构设计

```
用户交互 → Chat → 思考预算(动态) → Agent执行 → 工具调用
                                          ↓
                                    数据飞轮v3(过滤+评分+压缩+安全)
                                          ↓
                          ┌───────────────┴───────────────┐
                          ↓                               ↓
                  经验池 JSONL                  技能库 SAGE + 基因
                          ↓                               ↓
                  SimpleMem压缩                   技能基因进化
                          ↓                               ↓
                  训练就绪检查(50条+空闲+VRAM+插电+非游戏)
                          ↓
                  ┌───────┴────────┐
                  ↓                ↓
          真实训练循环        Prompt进化循环
          Unsloth QLoRA       Darwin Gödel Machine
          HF模型路径          AlphaEvolve搜索
                  ↓                ↓
                  └───────┬────────┘
                          ↓
                  评估Harness
                  Benchmark 20任务 + Replay 30% + 成功率+2%阈值
                          ↓
                  ┌───────┴────────┐
                  ↓                ↓
              晋升 LoRA        回滚 + 报告
                  ↓
          梦境循环 3阶段 + 4层记忆巩固 + 遗忘
                  ↓
          通知用户 + 日志 + iOS远程查看
```

## 四、8阶段实现计划

### 阶段A：数据飞轮 v3 - 质量与安全（核心）

**目标**：从收集→高质量训练数据

**文件**：
- `backend/memory/data_flywheel_v3.py` 新建，兼容旧
- `backend/runtime/data_filter.py` 新建

**实现**：
1. 安全过滤器：危险工具 `delete_file` 带 `C:\Windows`、隐私文件 `password.txt`、系统进程 `csrss.exe` 不进训练
2. 去重：SHA256 conversations去重，相似度>0.9跳过
3. 重要性评分：工具链长度>3 + 验证通过 + 用户未撤销 + 耗时<60s → 0.9，否则0.5
4. SimpleMem压缩：content >200字压缩到30%，Token减少3x
5. 平衡安全：允许 `write_file` `create_folder` 等写入任务，但需验证通过
6. DPO质量：失败+修正，reflection长度>20字才有效

**验证标准**（机器可验证）：
- `data/training/sft.jsonl` 每行JSON可解析
- 危险路径 `C:\Windows\System32` 样本数 ==0
- 去重后相似度>0.9数 ==0
- 重要性评分分布 0.5-0.9
- API `GET /api/evolution/data` 返回 sft_samples + 质量分布

**风险**：过滤过严导致样本不足 → 阈值可配置，默认平衡

### 阶段B：真实训练循环 - Unsloth真实闭环

**目标**：从模拟sleep→真实训练

**文件**：
- `backend/learning/unsloth_trainer_v3.py` 重构
- `backend/learning/model_resolver.py` 新建
- `config/model_paths.json` 已有，扩展HF路径

**实现**：
1. 模型路径解析 v3：
   - 推理：GGUF `D:\llama.cpp\Qwen3.6-35B-A3B...` 环境变量MODEL_PATH
   - 训练：HF `Qwen/Qwen3-30B-A3B` 环境变量HF_MODEL_PATH，自动探测 `~/models/Qwen3-30B-A3B` `D:\models\Qwen3-30B-A3B`
   - 回退：若无HF，提示 `huggingface-cli download Qwen/Qwen3-30B-A3B`
2. VRAM检测：`torch.cuda.get_device_properties(0).total_memory`，24GB→30B，16GB→7B `Qwen2.5-7B-Instruct`，<12GB→仅技能蒸馏不训练模型
3. 训练脚本生成→真实执行：`subprocess.Popen` 执行 `python training_script.py`，非阻塞，日志流到 `data/logs/training_{id}.log`
4. 监控：每30秒读取日志，解析 Loss，更新状态 TRAINING → EVALUATING
5. LoRA版本管理：`models/versions/lora_{timestamp}` 保存adapter，`adapter_config.json` + `adapter_model.safetensors`
6. 失败重试：3次指数退避 5s 10s 20s，记录到 `evolution_history.json`

**验证标准**：
- `model_resolver.py` 解析GGUF存在性 false但HF路径可配置
- VRAM检测API `GET /api/evolution/vram` 返回 total/available/推荐模型
- 训练脚本生成后 `py_compile` 通过
- 模拟训练：无GPU时生成LoRA空文件，状态流转正确

**风险**：Windows上unsloth安装困难 → 提供安装指南+CPU回退+技能蒸馏

### 阶段C：评估Harness - 防遗忘与晋升

**目标**：从硬编码0.82→0.91→真实回放

**文件**：
- `backend/benchmark/evolution_eval.py` 新建
- `backend/learning/replay_buffer.py` 新建

**实现**：
1. Benchmark 20任务：从 `benchmark/suite.py` 选取 5文件+5系统+5窗口+5安全，真实执行，非模拟
2. Replay Buffer 30%：从旧SFT中随机30%高质量样本（评分>0.8）混入新训练，防止灾难性遗忘
3. 评估流程：
   - 旧LoRA执行20任务→old_success_rate
   - 新LoRA执行20任务→new_success_rate
   - 通用任务（打开记事本）额外5任务→generic_rate防遗忘
4. 晋升阈值：平衡模式 +2%即晋升，严格+5%，激进+0%（只要不下降）
5. 回滚：若new < old，删除新LoRA，保留旧，记录失败原因

**验证标准**：
- `evolution_eval.py` 执行20任务返回 success_rate
- Replay Buffer 30%数量正确
- 晋升逻辑 +2%阈值可配置
- API `POST /api/evolution/evaluate` 返回 old/new/improvement/是否晋升

**风险**：评估任务执行真实系统操作→沙盒限制，只读任务为主

### 阶段D：Prompt/策略自进化 - Darwin Gödel Machine

**目标**：Prompt和执行策略自动进化

**文件**：
- `backend/learning/prompt_evolution.py` 新建
- `backend/learning/strategy_evolution.py` 新建
- `data/prompts/` 目录

**实现**：
1. Prompt基因：系统提示词、工具描述、验证规则作为基因，存储 `data/prompts/prompt_v{version}.json`
2. Darwin Gödel Machine：
   - 变异：随机改写prompt一句话，例如"先截图再操作"→"先感知再规划"
   - 交叉：两个高分prompt各取一半拼接
   - 选择：用benchmark评估，成功率高保留
3. EvolveR：离线蒸馏（从成功轨迹提炼原则）+在线原则（实时添加到系统提示）
4. AlphaEvolve：进化搜索最优工具链，例如文件整理最优链 `list_files→analyze→create_folder→move`

**验证标准**：
- `data/prompts/` 版本数增长
- Prompt进化后benchmark提升
- API `GET /api/evolution/prompts` 列出版本和评分

**风险**：Prompt进化可能变差→评估过滤，保留旧版本可回滚

### 阶段E：技能基因进化 - Skill Gene

**目标**：技能库从保存→进化

**文件**：
- `backend/runtime/skill_gene.py` 新建
- `experiments/skill_gene.py` 已有，整合

**实现**：
1. 技能基因：每个技能含 `code` + `tests` + `success_count` + `fitness`
2. 适应度：`success_count / (success_count+failure_count) * importance`
3. 进化：
   - 变异：随机改参数，例如整理下载→整理文档
   - 交叉：两个技能组合，例如 `list_files`+`create_folder`→`organize_files`
   - 选择：fitness>0.7保留，<0.3遗忘
4. 复合改进：技能调用技能，形成链

**验证标准**：
- 技能数增长，fitness分布
- 技能基因交叉产生新技能
- API `GET /api/skills/gene` 返回进化树

### 阶段F：自主调度 - 资源感知

**目标**：从定时→真正自主

**文件**：
- `backend/autonomous/scheduler_v3.py` 新建
- `backend/runtime/resource_monitor.py` 新建

**实现**：
1. APScheduler：凌晨2点+每30分钟检查
2. 资源感知：
   - CPU<20% + 内存<70% + 空闲30分（现有）
   - 新增：VRAM可用>18GB + 是否插电（Windows `GetSystemPowerStatus`）+ 是否游戏/会议（检测进程 `game.exe` `Teams.exe` 全屏）
   - iOS远程：若用户在iOS查看，暂停训练
3. 通知：训练开始/完成/失败推送到前端通知中心 + 日志
4. 配置：`config/evolution_schedule.json` 可调整阈值

**验证标准**：
- 调度器日志 `data/logs/scheduler.log`
- 资源检测API `GET /api/evolution/resources` 返回 CPU/内存/VRAM/插电/游戏
- 空闲时自动触发（可手动 `POST /api/evolution/start`）

### 阶段G：记忆巩固 - 4层+SimpleMem+遗忘

**目标**：从双轨→统一

**文件**：
- `backend/memory/memory_v3.py` 新建，整合 `memory_layer` + `simple_mem` + `dreaming.py` + `dream_loop.py`
- `backend/memory/forgetting.py` 新建

**实现**：
1. 统一4层：conversational（短期上下文）+ episodic（任务历史）+ semantic（事实）+ procedural（技能），全部走SimpleMem压缩
2. 遗忘机制：访问计数<3 + 重要性<0.3 + 超过30天 → 自动遗忘，释放空间
3. 梦境循环：每晚2点后执行Light→REM→Deep，提炼长期记忆，生成`DREAMS.md`人类可读
4. 意图感知：检索时根据任务类型调整权重

**验证标准**：
- 4层记忆统一API `GET /api/memory/v3`
- 遗忘数统计
- DREAMS.md生成

### 阶段H：可观测性 - 仪表盘与iOS

**目标**：进化过程可看可控

**文件**：
- `frontend/js/evolution.js` 新建
- `backend/routers/evolution_router.py` 新建

**实现**：
1. 前端进化页：训练数据统计+样本列表+训练日志流+版本历史+Prompt版本+技能基因树+资源状态
2. iOS远程：`http://ip:8000/` 已支持，新增进化进度SSE推送
3. 日志：loguru文件轮转，训练日志单独文件

**验证标准**：
- 前端进化页可访问
- SSE推送训练进度

## 五、实施顺序与Ralph Loop

### 用Ralph Loop执行

**PRD**：`data/prd_v3.json` 8个story，每个小到一上下文窗口

1. story_A：数据飞轮v3过滤+评分+去重+安全
2. story_B：模型路径解析v3 GGUF+HF双轨+VRAM检测
3. story_C：真实训练循环 unsloth真实执行+监控+LoRA版本
4. story_D：评估Harness benchmark 20任务+Replay 30%+2%阈值
5. story_E：Prompt进化 Darwin Gödel Machine+EvolveR
6. story_F：技能基因进化 变异交叉选择
7. story_G：自主调度 资源感知+插电+游戏检测
8. story_H：记忆巩固 4层统一+遗忘+DREAMS.md+前端仪表盘

每个story验收标准机器可验证，三护栏。

### 时间估算
- 阶段A+B+C：核心闭环，2-3天
- 阶段D+E+F+G：进化性，3-4天
- 阶段H：可观测性，1天
- 总计：6-8天，小步迭代

## 六、安全与平衡模式

- 安全过滤：危险路径`C:\Windows\System32` `/etc` `password.txt` `csrss.exe` 不进训练
- 允许：`write_file` `create_folder` `list_files` 等文件管理需验证通过
- 晋升：+2%阈值，平衡模式
- 回滚：失败自动回滚，保留旧LoRA
- 审计：所有训练样本记录来源，`data/training/` 可审查

## 七、验证清单（机器可验证）

- [ ] `data/training/sft.jsonl` 危险样本数==0
- [ ] `config/model_paths.json` 含HF路径字段
- [ ] `GET /api/evolution/vram` 返回VRAM
- [ ] `POST /api/evolution/start` 状态流转 IDLE→COLLECTING→TRAINING→EVALUATING→PROMOTING→IDLE
- [ ] Benchmark 20任务回放成功率计算
- [ ] Replay Buffer 30%数量正确
- [ ] Prompt版本数增长
- [ ] 技能fitness分布
- [ ] 调度器日志存在
- [ ] DREAMS.md生成
- [ ] 前端进化页可访问

## 八、下一步行动

1. 用户确认本计划
2. 创建 `data/prd_v3.json` 8个story，passes=false
3. 启动Ralph Loop，每次全新上下文执行一个story
4. 每story完成后验证验收标准，更新passes
5. 全部完成后，`main_v5.py` 升级为 `main_v6.py`，健康检查显示v3.0

---

**技术栈夯实**：无新重型依赖，复用现有 torch/unsloth（可选）、psutil、filelock、APScheduler，技术说明非标签，代码注释中文，UTF-8 BOM。

**适应性核心**：环境自动探测、资源自动降级、任务自动习惯、模型双轨、Prompt自进化、技能基因进化。

**自主进化性核心**：数据自主收集过滤、训练自主触发监控、评估自主回放晋升、记忆自主整理遗忘、策略自主变异选择。
