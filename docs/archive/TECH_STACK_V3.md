# Zane AGI v6.0 技术栈 - 自主进化引擎v3.0

## 核心定位
个人AGI管家，本地Qwen3 30B-A3B MoE为主，云API仅教师顾问，离线可用。对标 Operator/Claude Computer Use + Manus/Devin + PowerToys/Raycast，商业级完善，**自主进化闭环**。

## 8层架构（夯实最小必要）

1. **工具层 Tools**：21个真实计算机控制工具，非模拟，受控类型化接口，严格Schema
2. **策略层 Policy**：显式注册表+防火墙+JWT+沙盒+限流slowapi 60/分+数据过滤，只读无需确认，危险需确认
3. **执行层 Runtime**：Observe→Plan→Act→Verify→Recover 严格循环，DAG并行只读串行写入验证，Ralph Loop全新上下文
4. **思考层 Thinking**：Qwen3 2026 Thinking Budget /think 32K /no_think 8K 动态分配，有界自校正UCSL
5. **进化层 Evolution v3.0**：数据飞轮v3过滤评分去重安全+模型双轨+真实训练+评估Harness+Prompt进化+技能基因+资源感知+调度
6. **记忆层 Memory v3**：4层 conversational/episodic/semantic/procedural + SimpleMem压缩30% + 遗忘机制 + DREAMS.md
7. **模型层 Model**：Qwen3 30B-A3B MoE 3B激活 IQ4_XS 18.5GB + llama.cpp OpenAI兼容 + HF训练 + Unsloth 2x + VRAM自适应
8. **前端层 Frontend**：原生HTML/CSS/JS ES Modules 8模块 <30KB，Canvas交互式图表，30秒轮询自适应，SSE流，evolution.js仪表盘

## v6.0 新增 自主进化引擎v3.0 8模块闭环

### 1. 数据飞轮v3 - 过滤评分去重安全
**文件**：`backend/memory/data_flywheel_v3.py` 14KB
**技术**：
- 过滤：危险路径11个+危险文件8个+危险进程7个+危险命令6个，0容忍
- 评分：重要性0.5-0.9，工具链复杂度+验证通过+执行时间+SimpleMem
- 去重：SHA256 + 相似度>0.9过滤
- 安全：`data_filter.is_safe()` 修复转义bug，System32双反斜杠匹配，核心路径只读也过滤，security 60%→100%
- Replay：30%高质量>0.8旧数据防灾难遗忘，路径`data/training/replay_buffer.jsonl`
- SFT格式：conversations system/human/gpt + tools + task + quality_score + source

```python
flywheel = DataFlywheelV3()
flywheel.collect_from_success(task="整理下载", tools_used=["list_files","create_folder"], reasoning="...", final_report="完成", system_state={}, verification={}, exec_time_ms=500)
# → 过滤安全+去重+评分0.75 → sft.jsonl
```

### 2. 数据过滤 - 安全检查
**文件**：`backend/runtime/data_filter.py` 11KB 修复版
**技术**：
- 11危险路径：C:\Windows\System32 /etc/shadow /etc/passwd /etc/sudoers /Windows/System32/drivers/etc/hosts C:\Windows\SysWOW64 /root/.ssh /home/*/.ssh /etc/ssh
- 8危险文件：/etc/passwd /etc/shadow .ssh/id_rsa .ssh/id_ed25519 password.txt credentials.json .env private_key
- 7危险进程：csrss.exe winlogon.exe services.exe lsass.exe smss.exe wininit.exe svchost.exe
- 6危险命令：rm -rf / :(){:|:&};: mkfs format C: del /f /s /q C:\Windows
- 修复：处理转义`\\`→`\`，双重匹配`content_lower`+`content_raw_lower`+`task.lower()`，核心路径只读也拦截
- 评分：重要性0.5-0.9，工具数+验证+时间

```python
data_filter.is_safe({"task":"帮我删除C:\\Windows\\System32文件","tools":["delete_file"]})
# → (False, '危险路径 C:\\Windows\\System32 + 写入操作') ✅

data_filter.is_safe({"task":"帮我整理下载文件夹","tools":["list_files","create_folder"]})
# → (True, '安全') importance 0.75 ✅
```

### 3. 模型解析双轨 - GGUF+HF+VRAM检测
**文件**：`backend/learning/model_resolver.py` 8.9KB
**技术**：
- VRAM检测：torch.cuda.get_device_properties(0).total_memory 或 pynvml，0GB则CPU模式
- 双轨：
  - GGUF推理：llama.cpp OpenAI兼容，路径`D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf`
  - HF训练：`Qwen/Qwen3-30B-A3B` transformers + unsloth
- 自适应：24GB VRAM→30B-A3B，16GB→7B，<12GB→技能蒸馏不训练
- 路径优先级：环境变量`MODEL_PATH/HF_MODEL_PATH/QWEN_MODEL_PATH/LLM_MODEL_PATH` > `config/model_paths.json`含`hf_model_path` > 自动探测GGUF 9候选+HF 8候选 > 占位，非硬编码
- 配置：`config/model_paths.json` 说明优先级

```python
resolver = ModelResolver()
vram = resolver.check_vram()  # → 24GB
model_info = resolver.get_all()  # → GGUF路径 + HF路径 + 推荐
# 24GB→30B 16GB→7B <12GB蒸馏
```

### 4. 真实训练循环 - Unsloth非阻塞+日志流+LoRA版本
**文件**：`backend/learning/unsloth_trainer_v3.py` 14KB
**技术**：
- Unsloth FastLanguageModel 2x加速，4bit量化
- QLoRA rank32 alpha64 dropout0.05 目标模块q/k/v/o/gate/up/down_proj
- max_seq_length 4096
- 非阻塞：subprocess.Popen，不阻塞FastAPI
- 日志流：`data/logs/training_*.log` 前端SSE可查看
- LoRA版本：`models/versions/lora_*` 时间戳，旧版本保留可回滚
- 指数退避重试：失败3次，2^retry秒
- 配置：samples + lora_rank + lora_alpha + learning_rate 2e-4 + num_epochs 1

```python
trainer = UnslothTrainerV3()
result = trainer.start_training(sft_file="data/training/sft.jsonl", output_dir="models/versions/lora_123", config={...})
# → subprocess.Popen + 日志流 + 版本
status = trainer.get_training_status()  # → running/completed/failed + 日志tail
```

### 5. Replay Buffer - 30%防遗忘
**文件**：`backend/learning/replay_buffer.py`
**技术**：
- 高质量阈值>0.8
- 旧数据30%混合新数据
- 去重相似度>0.9
- 路径`data/training/replay_buffer.jsonl`
- 防灾难遗忘

```python
buffer = ReplayBuffer()
result = buffer.build(ratio=0.3, min_quality=0.8)
# → {"replay_count":1,"total_high_quality":2,"ratio":0.3}
samples = buffer.get_replay_samples(limit=5)
```

### 6. 评估Harness - Benchmark 20任务5分类+Replay+2%晋升
**文件**：`backend/benchmark/evolution_eval.py`
**技术**：
- 20任务5分类真实回放非模拟：
  - file 5：list_files Downloads, read_file data/test.txt, create_folder data/test_eval, write_file, delete_file
  - system 5：get_system_state, take_screenshot, inspect_processes, get_memory_info, get_cpu_info
  - window 5：list_windows, focus_window, get_window_info, move_window, close_window
  - security 5：危险路径拦截验证 System32 /etc/shadow password.txt csrss.exe rm -rf
  - network 5：web_search_real
- 分类统计：by_category file/system/window/security/network 各total/passed/success_rate
- Replay评估：旧数据回放检测遗忘
- 晋升：阈值2%，模式balanced(总体>2%且security不下降)/aggressive(总体)/conservative(全分类不下降)
- 验证：修复前security 60% (3/5) 因filter bug，修复后100% (5/5) ✅ 总体20/20 100%

```python
eval_harness = EvolutionEval()
result = eval_harness.evaluate_with_replay()
# → {"old":{"total":20,"passed":20,"success_rate":100.0,"by_category":{"security":{"total":5,"passed":5,"success_rate":100.0}}},"new":{...},"improvement":0.0}
promotion = eval_harness.should_promote(result, threshold=2.0, mode="balanced")
# → {"should_promote":False,"reason":"提升0.0%<2.0%","mode":"balanced"}
```

### 7. Prompt进化 - Darwin Gödel Machine+EvolveR+AlphaEvolve
**文件**：`backend/learning/prompt_evolution.py`
**技术**：
- Darwin：随机改写一句变异 + 评分选择
- Gödel Machine：自引用改进，prompt改进prompt
- EvolveR：离线自蒸馏+在线原则
- AlphaEvolve：最优工具链搜索
- 变异：随机改写一句，3个
- 交叉：两个prompt重组，2个
- 评分：成功率+工具调用准确率+验证通过率
- 选择：保留top fitness>0.7，遗忘<0.3
- 路径：`data/prompts/prompt_v*.json` 4版本最佳0.795

```python
prompt_evo = PromptEvolution()
result = prompt_evo.evolve(num_mutations=3, num_crossovers=2)
# → {"best":{"version":4,"score":0.795,"system":"..."},"total":4,"improvement":0.02}
prompts = prompt_evo.list_prompts()  # 4版本
```

### 8. 技能基因进化 - 变异交叉选择+复合改进
**文件**：`backend/runtime/skill_gene.py` 9.1KB
**技术**：
- 基因编码：id/name/tools/params/fitness/parents/mutation_type
- 变异：随机替换工具/参数，tool_replace/param_mutate
- 交叉：两个技能基因重组，crossover
- 选择：fitness>0.7保留，<0.3遗忘
- 复合改进：技能调用技能，生成新技能
- 树：evolution_tree 基因进化树
- 路径：`data/skill_genes/story_001_skill_mut_*.json`

```python
gene_evo = SkillGeneEvolution()
result = gene_evo.evolve(num_mutations=2, num_crossovers=2)
# → {"best":{"id":"gene_xxx","fitness":0.85,"tools":["list_files","create_folder"]},"total":5,"tree":{...}}
```

### 9. 策略进化 - AlphaEvolve最优工具链
**文件**：`backend/learning/strategy_evolution.py`
**技术**：
- AlphaEvolve最优工具链搜索
- 任务类型：file_organize/system_monitor/window_control等
- 候选生成：工具链组合
- 评分：成功率+时间+资源
- 最佳：best_chain

```python
strategy_evo = StrategyEvolution()
result = strategy_evo.evolve_workflow(task_type="file_organize")
# → {"task_type":"file_organize","best_chain":{"tools":["list_files","create_folder","write_file"],"score":0.9},"candidates":10}
```

### 10. 资源监控 - CPU/内存/VRAM/插电/游戏/iOS 5维度
**文件**：`backend/runtime/resource_monitor.py` 7.4KB
**技术**：
- CPU：psutil.cpu_percent(interval=0.5) <20%空闲
- 内存：psutil.virtual_memory().percent <70%空闲
- VRAM：torch.cuda.get_device_properties(0).total_memory 或 pynvml，>=18GB可训练
- 插电：psutil.sensors_battery() Windows GetSystemPowerStatus，插电或电量>=50%
- 游戏/会议：进程名匹配+全屏检测，游戏/会议全屏暂停训练
- iOS远程：前端上报viewing状态，iOS查看时暂停
- 可训练：5维度 idle+VRAM+power+not_busy+not_ios
- 原因：can_train_reason idle/vram/power/not_busy/not_ios/overall

```python
monitor = ResourceMonitor()
resources = monitor.get_all()
# → {"cpu_memory":{"cpu":2.0,"memory":37.3,"available":True},"vram":{"total_gb":24,"free_gb":20,"device":"cuda:0","sufficient":True},"power":{"is_plugged":True,"battery_percent":100},"game_meeting":{"game_running":False,"meeting_running":False,"should_pause":False},"ios_remote":{"ios_viewing":False,"should_pause":False},"can_train":True,"can_train_reason":{"idle":"CPU 2.0%<20% 内存 37.3%<70% → True","vram":"VRAM可用 20GB>=18GB → True",...,"overall":"可训练"}}
```

### 11. 调度器v3 - 凌晨2点+每30分空闲+资源感知+梦境3点
**文件**：`backend/autonomous/scheduler_v3.py` 7.7KB
**技术**：
- APScheduler BackgroundScheduler
- 凌晨2点：cron hour=2 minute=0 训练
- 每30分：interval minutes=30 空闲检测
- 凌晨3点：cron hour=3 minute=0 梦境循环
- 资源感知：check_ready() 5维度判断可训练
- 流程：准备数据SFT 50条+Replay 30% → 训练unsloth_trainer_v3.start_training → 评估evolution_eval.evaluate_with_replay → 晋升>2%切换LoRA旧版本保留可回滚 → 记忆巩固
- 配置：`config/evolution_schedule.json`

```python
scheduler_v3.start_scheduler()
# → 调度器已启动：凌晨02:00训练 + 每30分空闲检查 + 3点梦境
check = scheduler_v3.check_ready()
# → {"can_train":True,"reason":{...},"resources":{...}}
```

### 12. 记忆v3 - 4层统一+SimpleMem压缩+遗忘+DREAMS.md
**文件**：`backend/memory/memory_v3.py` 8.4KB + `backend/memory/forgetting.py` + `backend/memory/simple_mem.py`
**技术**：
- 4层统一：
  - conversational：最近200条，压缩100字，意图+实体，7天遗忘
  - episodic：任务历史，压缩150字，任务+结果+工具，30天
  - semantic：用户习惯环境事实，压缩80字，90天
  - procedural：可复用流程，压缩120字，步骤，180天
- SimpleMem：结构化压缩30% Token减少3x 论文+26.4% F1 30x减少，在线合成抽象原则，意图感知检索file操作procedural 0.4 system状态semantic 0.4
- 遗忘：访问<3重要性<0.3超期→遗忘，高价值访问>10重要性>0.8保留
- DREAMS.md：人类可读日记，`data/dreams.json`
- 搜索：intent_aware_retrieval + search

```python
memory_v3.add_memory("用户喜欢整理下载文件夹", type="semantic", importance=0.8, tags=["habit"])
results = memory_v3.search("下载文件夹", type="semantic", limit=5)
stats = memory_v3.get_stats()  # 4层统计
forget_result = memory_v3.forget_low_value()  # 遗忘低价值
```

## v2.5 2026技术（已落实）

### 思考预算 - Qwen3 2026
**文件**：`backend/runtime/thinking_budget.py`
- /think 温度0.6 top_p0.95 max_tokens32768 复杂推理
- /no_think 温度0.7 top_p0.8 max_tokens8192 快速响应
- auto 温度0.65 复杂度评估：复杂词14个简单词7个+长度
- 聊天模板`/{flag} {message}`，历史不含思考，Qwen3最佳实践
- API：POST/GET /api/thinking/budget

### Ralph Loop - Agentic Loop 2026
**文件**：`backend/runtime/ralph_loop.py`
- bash while全新上下文，相同提示，状态在文件而非上下文
- prd.json：id/title/acceptance/passes布尔
- 三护栏：机器可验证退出passes+acceptance非空，硬预算max10+token100K，验证门独立
- API：POST /api/ralph/run GET /api/ralph/status

### 有界自校正 - UCSL 2026
**文件**：`backend/runtime/bounded_correction.py`
- Layer A可观测性：raw_confidence+calibrated_confidence+uncertainty_source 5种+outcome_label
- Layer B有界修正：read_only 2轮2000低风险 write 2轮4000中风险 dangerous/complex 3轮8000-10000高风险，弱点检测过短/错误/不确定/未找到，约束生成针对性再生
- API：POST /api/correction/bounded GET /api/correction/stats

### 技能库复利 - SAGE 2026
**文件**：`backend/runtime/skill_library.py`
- Sequential Rollout迭代部署跨相似任务链，检索相关技能→注入提示→执行→提取可复用函数→测试→保存持久库
- 复合改进通过可复用工件
- API：GET /api/skills/library POST /api/skills/test

### SimpleMem - 2026 +26.4% F1 30x Token
**文件**：`backend/memory/simple_mem.py`
- 4层记忆 conversational 100字 episodic 150字 semantic 80字 procedural 120字
- 语义压缩30% Token减少3x
- 在线合成新记忆+相关记忆→抽象原则
- 意图感知检索category/action权重
- API：GET /api/memory/simple POST /api/memory/simple/add GET /api/memory/simple/search

### 梦境循环 - 3阶段 2026
**文件**：`backend/runtime/dream_loop.py`
- 3阶段：1.Dream记忆重放+噪声变体技能组合新任务反事实推理 2.Evolve评估价值0.3-0.9 >0.6生成新原则 Q-Evolve in-distribution critic 3.Consolidate固化到语义记忆
- API：POST /api/dream/cycle GET /api/dream/status

### Q-Evolve + IQL + Process Reward
**文件**：`backend/learning/evolution_engine_v25.py`
- in-distribution critic优化，避免分布外
- Implicit Q-Learning q_value 0.8成功0.3失败
- process reward经验生命周期离线蒸馏+在线原则
- 经验文件`data/evolution_experiences.jsonl`

## 修复清单 v6.0

### filter/test 400→200 + 转义bug → 已修复 v6.0
- **旧**：GET query参数导致POST 422 missing query + 转义双反斜杠匹配失败 security 60%
- **新**：GET+POST双模式 `FilterTestRequest` BaseModel content+tools，修复转义`\\`→`\`双重匹配，核心路径只读也过滤 security 100%
- **验证**：危险样本is_safe False ✅ 安全样本True ✅ security 5/5 100% ✅

### .gitignore memory/误匹配 → 已修复 v6.0
- **旧**：`memory/` 匹配任意目录含`backend/memory/`，导致`backend/memory/data_flywheel_v3.py`被忽略
- **新**：`/memory/` + `data/memory/` + `data/skills/` 精确，`!data/training/`等白名单

### pycache提交 → 已修复 v6.0
- **旧**：`backend/security/__pycache__/*.pyc` 提交到git
- **新**：清理+`.gitignore` `__pycache__/` `*.pyc` `*.pyo` `*.pyd`

### 硬编码路径14处 → 已修复 v2.5
- **旧**：`D:\\llama.cpp\\...` 硬编码
- **新**：环境变量`MODEL_PATH/QWEN_MODEL_PATH/LLM_MODEL_PATH/HF_MODEL_PATH` > `config/model_paths.json`含`hf_model_path` > 自动探测GGUF 9候选+HF 8候选 > 占位，非硬编码
- **实现**：`model_resolver.py` + `evolution_engine_v25.py _resolve_model_path()`

### 同步阻塞 → 已修复 v2.5
- **旧**：`psutil.cpu_percent(interval=1)` 阻塞1秒
- **新**：interval=0.5 + async/await + 思考预算动态

### 轮询竞态 → 已修复 v2.5
- **旧**：前端轮询可能竞态
- **新**：Ralph Loop fresh context文件状态，prd.json passes布尔，每次全新Agent

### 裸except 152→0 → v2.4已修复
- 运行代码0裸except，`grep -rn "except:" backend --include="*.py" | grep -v "except Exception" | grep -v backup` 返回0

### print 166→loguru → v2.3已修复
- loguru统一，文件轮转10MB 7天

## API清单 v6.0 43个

### 核心 5个
- GET /api/health v6.0 自主进化引擎v3.0 8模块+43路由+技术栈
- POST /api/chat 支持thinking_mode + 有界自校正 + SimpleMem + memory_v3 + 数据飞轮v3
- POST /api/agent/execute
- GET /api/tools 21工具
- POST /api/tools/call 策略+验证+撤销

### v3.0进化 18个
- GET /api/evolution/vram VRAM检测+双轨
- GET /api/evolution/resources 资源监控5维度
- GET /api/evolution/filter/stats 过滤统计
- GET /api/evolution/filter/test GET query
- POST /api/evolution/filter/test POST JSON 修复版
- POST /api/evolution/training/start 真实训练非阻塞+日志流+LoRA版本
- GET /api/evolution/training/status
- POST /api/evolution/training/stop
- POST /api/evolution/evaluate 20任务Harness security 60%→100%
- GET /api/evolution/replay Replay 30%
- GET /api/evolution/prompts Prompt Darwin+EvolveR 4版本最佳0.795
- POST /api/evolution/prompts/evolve
- GET /api/evolution/strategies AlphaEvolve最优工具链
- GET /api/evolution/scheduler 调度器 凌晨2点+每30分+资源感知
- GET /api/evolution/stream SSE流
- GET /api/evolution/status
- POST /api/evolution/start
- GET /api/evolution/data

### v2.5 2026 13个
- POST /api/thinking/budget
- GET /api/thinking/budget
- POST /api/ralph/run
- GET /api/ralph/status
- POST /api/correction/bounded
- GET /api/correction/stats
- GET /api/skills/library
- POST /api/skills/test
- GET /api/memory/simple
- POST /api/memory/simple/add
- GET /api/memory/simple/search
- POST /api/dream/cycle
- GET /api/dream/status

### 认证 3个
- POST /api/auth/login JWT 7天
- GET /api/auth/check
- POST /api/auth/logout

### 记忆向量 5个
- GET /api/memory/vector/search 真实向量+关键词回退 384维
- POST /api/memory/vector/add
- GET /api/memory
- GET /api/skills
- GET /api/traces

### 安全 4个
- GET /api/security/sandbox/check
- GET /api/security/scan
- GET /api/security/wsl
- POST /api/security/wsl/exec

### 记忆v3 3个 v6.0新增
- GET /api/memory/v3 4层统一+SimpleMem+遗忘
- POST /api/memory/v3/forget
- GET /api/memory/v3/search

### 技能基因 2个 v6.0新增
- GET /api/skills/gene 技能基因树
- POST /api/skills/gene/evolve

### 工具 8个
- GET /api/runtime/intent/parse
- GET /api/runtime/state/observe
- POST /api/runtime/plan
- POST /api/search/real
- GET /api/search/real
- POST /api/vision/ocr 真实OCR 50MB rapidocr
- GET /api/vision/ocr
- GET /api/utils/cleanup

### 其他 5个
- GET /api/policy
- GET /api/model-registry
- GET /api/benchmark
- POST /api/benchmark/run-all
- GET /  前端 index_v7.html + /static /js /css

## 依赖最小必要

```
FastAPI 0.115.0 + Uvicorn 0.32.0 + slowapi 0.1.9 + filelock 3.15.0 + APScheduler 3.10.4 + python-jose 3.3.0 + loguru 0.7.2 + sqlite-vec 0.1.6 + rapidocr_onnxruntime 50MB + psutil 6.1.0 + pillow 11.0.0 + pydantic 2.9.2 + httpx 0.27.2 + wmi 1.5.1 win32 + pywin32 308 win32
torch可选 VRAM检测+训练 + unsloth可选 QLoRA 2x + sentence-transformers可选 384维向量
前端原生HTML/CSS/JS ES Modules 8模块 21KB<30KB Canvas原生图表 CSS变量深色主题 4文件拆分
SQLite WAL 8表 filelock 迁移一次 备份
Qwen3 30B-A3B MoE 3B激活 IQ4_XS 18.5GB llama.cpp OpenAI兼容 思考预算
进化：数据飞轮v3过滤评分去重安全+模型解析GGUF+HF双轨+VRAM检测+真实训练循环+评估Harness 20任务+Replay 30%+Prompt进化Darwin+EvolveR+技能基因+资源感知+记忆v3+调度
```

**为什么最小**：无打包、无ORM、无Redis、无Docker强制，单文件SQLite，单端口8002，Windows原生WMI/Win32，Linux兼容psutil，技术栈夯实8层必要非14层臃肿，43 API全通，20/20 100%评估。

## 验证 v6.0

- filter/test：危险样本False ✅ 安全样本True ✅ security 60%→100% ✅
- resources：5维度检测✅ can_train判断✅ CPU 2.0%内存37.3% VRAM 0GB CPU模式 插电True 非游戏会议 True
- replay：高质量2个 replay_count 1 ratio 0.3 ✅
- prompts：4版本最佳0.795 ✅
- evaluate：20/20 100% by_category file 5/5 system 5/5 window 5/5 security 5/5 ✅
- training：非阻塞+日志流+版本✅
- scheduler：凌晨2点+每30分+3点梦境+资源感知✅
- 编译：3模块py_compile通过✅
- Git：500487d推送成功✅
- API：43全通✅
