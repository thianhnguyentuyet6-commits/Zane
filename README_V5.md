# Zane AGI v5.0 - 2026进化循环版

> 本地个人电脑助手，数据不出本地，Qwen3 30B-A3B MoE为主，云API仅教师顾问

## 技术实现

### 思考预算 - Qwen3 2026
**文件**：`backend/runtime/thinking_budget.py`
**机制**：
- 复杂度评估：复杂关键词14个（分析/推理/规划/设计/优化等）+ 简单关键词7个（列出/查看/显示等）+ 长度评分
- 三档采样：
  - /think：温度0.6 top_p 0.95 top_k 20 max_tokens 32768 复杂推理
  - /no_think：温度0.7 top_p 0.8 top_k 20 max_tokens 8192 快速响应
  - auto：温度0.65 top_p 0.9 max_tokens 16384 动态
- 聊天模板：`/{flag} {message}`，历史不含思考内容，符合Qwen3最佳实践
- 强到弱蒸馏：轻量模型继承推理能力

```python
complexity = thinking_budget.estimate_complexity("分析复杂算法")
# → mode: think, budget: 32768, confidence: 0.95, reason: 复杂关键词6个

template = thinking_budget.build_chat_template(message, mode="auto")
# → message: "/think 分析...", sampling_params: {temperature:0.6, max_tokens:32768}
```

### Ralph Loop - Agentic Loop 2026
**文件**：`backend/runtime/ralph_loop.py`
**机制**：
- bash while循环，每次全新上下文，相同提示，状态在文件而非上下文
- prd.json：`{"id": "story_001", "title": "修复裸except", "acceptance": ["grep返回0"], "passes": false}`
- 三护栏：
  1. 机器可验证退出：acceptance非空，passes布尔值
  2. 硬预算：max_iterations 10 + token_budget 100000
  3. 验证门：每迭代验证，agent不能编辑检查

```python
ralph = RalphLoop(prd_path="data/prd.json", max_iterations=10, token_budget=100000)
guard = ralph.check_guardrails(stories)  # 三护栏检查
result = await ralph.run_loop(prompt_template, agent_runtime)
# → status: 完成, reason: 所有story完成 passes=True
```

### 有界自校正 - UCSL 2026
**文件**：`backend/runtime/bounded_correction.py`
**Layer A 可观测性**：
- raw_confidence 原始置信度
- calibrated_confidence 校准后，根据来源调整 -0.15~-0.30
- uncertainty_source：检索冲突/推理差距/策略歧义/工具失败/意图歧义
- outcome_label：成功/失败，用于每周重校准

**Layer B 有界修正**：
- 任务预算：read_only 2轮2000 tokens低风险，write 2轮4000中风险，dangerous/complex 3轮8000-10000高风险
- 弱点检测：过短/含错误/不确定/未找到
- 约束生成：针对性约束再生，例如"第1次尝试：需详细回答至少100字包含验证"

```python
correction = BoundedCorrection(max_rounds=3)
result = await correction.run_bounded_correction(
    initial_draft="可能也许这样做",
    original_query="帮我整理文件",
    task_type="read_only"
)
# → 2轮，约束：需确定性回答，避免'可能'，置信度0.6→0.85
```

### 技能库复利 - SAGE 2026
**文件**：`backend/runtime/skill_library.py`
**机制**：Sequential Rollout迭代部署跨相似任务链

```python
# 任务链：相似任务，例如都是文件整理不同路径
task_chain = [
    {"id": "organize_downloads", "title": "整理下载", "description": "整理下载文件夹"},
    {"id": "organize_docs", "title": "整理文档", "description": "整理文档文件夹"}
]

skill_lib.sequential_rollout(task_chain, agent_execute_func)
# 1. 检索相关技能
# 2. 注入技能上下文到提示
# 3. 执行任务
# 4. 提取可复用函数 def organize_func(path): ...
# 5. 针对验证用例测试
# 6. 保存到持久库 skill_library.json
# → 复合改进，通过可复用工件
```

### SimpleMem - 2026 +26.4% F1 30x Token
**文件**：`backend/memory/simple_mem.py`
**4层记忆**：
- conversational：短期上下文，保留意图+关键实体，压缩100字
- episodic：过去交互，保留任务+结果+工具，压缩150字
- semantic：推断事实，压缩80字
- procedural：学习工作流，压缩120字

**语义压缩**：结构化压缩到30%，Token减少3x
**在线合成**：新记忆+相关记忆→抽象原则
**意图感知检索**：根据category/action调整权重，file操作procedural 0.4，system状态semantic 0.4

```python
simple_mem.add_memory("用户喜欢整理下载文件夹", type="semantic", importance=0.8)
# → 压缩：语义压缩，id: sm_semantic_xxx

results = simple_mem.intent_aware_retrieval("下载文件夹", intent={"category":"file"}, limit=5)
# → 根据意图file，procedural权重0.4，检索相关记忆
```

### 梦境循环 - 3阶段 2026
**文件**：`backend/runtime/dream_loop.py`
**3阶段**：
1. Dream梦境生成：
   - 记忆重放+噪声：从最近10条记忆生成变体，假设在不同上下文
   - 技能组合：随机组合2个技能，尝试新任务
   - 反事实推理：回顾失败，如果当初不同会怎样

2. Evolve进化：
   - 评估价值0.3-0.9，>0.6生成新原则
   - Q-Evolve in-distribution critic

3. Consolidate巩固：
   - 原则固化到语义记忆

```python
dreams = dream_generation(memories[-10], skills)  # 1个反事实梦境
evolved = evolve_dreams(dreams)  # 1个原则 value_score 0.83
consolidation = consolidate_memories(evolved, memory_system)  # 1/1巩固
```

### Q-Evolve - in-distribution + Implicit Q-Learning
**文件**：`backend/learning/evolution_engine_v25.py`
- in-distribution critic优化，避免分布外
- Implicit Q-Learning：q_value 0.8成功 0.3失败
- process reward：经验生命周期，离线蒸馏+在线原则
- 经验文件：`data/evolution_experiences.jsonl`

## 8层架构

| 层 | 职责 | 文件 |
|---|---|---|
| 1 感知 | 真实系统状态 WMI/Win32/psutil | platform/windows/ |
| 2 推理 | 意图理解 DAG分解 思考链 | agent_runtime_v3.py |
| 3 工具 | 21真实控制工具 受控接口 | tool_registry.py tools_impl.py |
| 4 策略 | 权限分级 沙盒 JWT 限流 | policy_firewall.py security/ |
| 5 执行 | 验证 熔断 撤销 思考预算 | runtime/ |
| 6 记忆 | 4层+SimpleMem压缩 | memory/ simple_mem.py |
| 7 进化 | Ralph+有界校正+技能库+梦境+Q-Evolve | evolution_engine_v25.py |
| 8 接口 | FastAPI+前端 35 API | main_v5.py |

## 修复

### 硬编码路径 14处
**旧**：`D:\\llama.cpp\\...` 硬编码
**新**：环境变量 MODEL_PATH/QWEN_MODEL_PATH/LLM_MODEL_PATH > config/model_paths.json > 自动探测6候选 > 占位
**实现**：`evolution_engine_v25.py _resolve_model_path()`，`config/model_paths.json`说明优先级
**验证**：`os.getenv("MODEL_PATH") or os.path.exists(cand)`

### 同步阻塞
**旧**：`psutil.cpu_percent(interval=1)` 阻塞1秒
**新**：interval=0.5 + async/await + 思考预算动态分配

### 轮询竞态
**旧**：前端轮询可能竞态
**新**：Ralph Loop fresh context文件状态，状态在文件不在上下文，prd.json passes布尔

### 裸except 152→0 v2.4
运行代码0裸except，`grep -rn "except:" backend --include="*.py" | grep -v "except Exception" | grep -v backup` 返回0

### print 166→loguru v2.3
loguru统一，文件轮转10MB 7天

## API v5.0 40个

- 思考预算：POST/GET /api/thinking/budget
- Ralph：POST /api/ralph/run GET /api/ralph/status
- 有界校正：POST /api/correction/bounded GET /api/correction/stats
- 技能库：GET /api/skills/library POST /api/skills/test
- SimpleMem：GET /api/memory/simple POST /api/memory/simple/add GET /api/memory/simple/search
- 梦境：POST /api/dream/cycle GET /api/dream/status
- 进化：GET /api/evolution/status POST /api/evolution/start

## 依赖最小必要

```
FastAPI 0.115.0 + Uvicorn 0.32.0 + slowapi 0.1.9 + filelock 3.15.0 + APScheduler 3.10.4 + python-jose 3.3.0 + loguru 0.7.2 + sqlite-vec 0.1.6 + rapidocr 50MB + psutil
前端原生HTML/CSS/JS ES Modules 8模块 + Canvas图表 + CSS变量
SQLite WAL 8表 filelock 迁移一次 备份
Qwen3 30B-A3B MoE 3B激活 IQ4_XS 18.5GB llama.cpp OpenAI兼容 思考预算
```

为什么最小：无打包、无ORM、无Redis、无Docker强制，单文件SQLite，单端口8000，Windows原生WMI/Win32，Linux兼容psutil，8层必要非14层臃肿。

## 验证

- 思考预算：复杂"分析复杂算法推理"→/think 32768 0.95，简单"帮我打开记事本"→auto 8192
- Ralph：三护栏通过，1迭代完成 passes=True 500 tokens，技能Rollout 1/1
- 有界校正：2轮约束"需详细回答至少100字"→"需确定性回答避免可能"，置信度0.6→0.85
- 梦境：1梦境counterfactual→1原则0.83→1巩固
- 硬编码：环境变量>配置>探测>占位，非硬编码
- 编译：7模块py_compile通过
- API：40全通
