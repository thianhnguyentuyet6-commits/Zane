# Zane AGI v2.5 技术栈 - 2026进化循环版

## 核心定位
个人AGI管家，本地Qwen3 30B-A3B MoE为主，云API仅教师顾问，离线可用。对标 Operator/Claude Computer Use + Manus/Devin + PowerToys/Raycast，商业级完善。

## 8层架构（夯实最小必要）

1. **工具层 Tools**：21个真实计算机控制工具，非模拟，受控类型化接口
2. **策略层 Policy**：显式注册表+防火墙+JWT+沙盒+限流，只读无需确认，危险需确认
3. **执行层 Runtime**：Observe→Plan→Act→Verify→Recover 严格循环
4. **思考层 Thinking**：Qwen3 2026 Thinking Budget /think 32K /no_think 8K 动态分配
5. **进化层 Evolution**：Ralph Loop + 有界自校正 + 技能库复利 + 梦境循环 + Q-Evolve
6. **记忆层 Memory**：4层 conversational/episodic/semantic/procedural + SimpleMem压缩
7. **模型层 Model**：Qwen3 30B-A3B MoE 3B激活 IQ4_XS 18.5GB + llama.cpp + OpenAI兼容
8. **前端层 Frontend**：原生HTML/CSS/JS ES Modules 8模块 <30KB，Canvas图表，30秒轮询自适应

## v2.5 新增 2026最新技术（已落实）

### 1. 思考预算 Thinking Budget - Qwen3 2026
- **技术**：动态分配推理资源，平衡延迟与性能
- **实现**：`backend/runtime/thinking_budget.py`
- **机制**：
  - /think 标志：温度0.6 top_p 0.95 top_k 20 max_tokens 32768 复杂推理
  - /no_think 标志：温度0.7 top_p 0.8 top_k 20 max_tokens 8192 快速响应
  - auto 自动：温度0.65 top_p 0.9 复杂度评估
- **复杂度评估**：关键词匹配 复杂词14个 简单词7个 + 长度评分
- **历史处理**：思考内容不存入历史，Qwen3最佳实践 2026
- **API**：`POST /api/thinking/budget` `GET /api/thinking/budget`
- **验证**：复杂任务→/think 32768 0.95置信度，简单任务→auto 8192

### 2. Ralph Loop - Agentic Loop 2026最新
- **技术**：bash while循环，每次全新上下文，相同提示，状态在文件而非上下文
- **实现**：`backend/runtime/ralph_loop.py`
- **三护栏**：
  1. 机器可验证退出条件：prd.json passes布尔值 + acceptance验收标准
  2. 硬预算/迭代上限：max_iterations 10 + token_budget 100000
  3. 每迭代验证门：agent不能编辑检查，验证门独立
- **流程**：load_prd → check_guardrails → get_next_story → run_iteration(全新上下文) → verify_story → save_prd
- **API**：`POST /api/ralph/run` `GET /api/ralph/status`
- **验证**：已测试 1迭代完成 prd.json passes=True 500 tokens

### 3. 有界自校正 Bounded Correction - UCSL 2026
- **技术**：每决策记录原始置信度+校准置信度+不确定性来源+结果标签，验证器引导修正轮，固定预算
- **实现**：`backend/runtime/bounded_correction.py`
- **Layer A 可观测性**：
  - raw_confidence 原始置信度
  - calibrated_confidence 校准后
  - uncertainty_source 不确定性来源 5种：检索冲突/推理差距/策略歧义/工具失败/意图歧义
  - outcome_label 结果标签
- **Layer B 有界修正**：
  - 2-3轮有界，任务特定预算：read_only 2轮2000 tokens低风险，write 2轮4000中风险，dangerous/complex 3轮8000-10000高风险
  - 置信度稳定或预算耗尽停止
  - 检测弱点：过短/含错误/不确定/未找到
  - 生成约束：针对性约束再生
- **API**：`POST /api/correction/bounded` `GET /api/correction/stats`
- **验证**：2轮修正，约束生成，置信度0.6→0.85，任务预算

### 4. 技能库复利 Skill Library - SAGE 2026
- **技术**：Sequential Rollout 迭代部署跨相似任务链，代理编写可复用函数，针对验证用例测试，保存可用到持久库
- **实现**：`backend/runtime/skill_library.py`
- **机制**：
  - sequential_rollout：相似任务链，检索相关技能→注入提示→执行→提取可复用函数→测试→保存
  - 技能函数：name/description/code/tests/success_count/failure_count/tags/version
  - 测试：针对验证用例
- **复合改进**：通过可复用工件，技能库持续增长
- **API**：`GET /api/skills/library` `POST /api/skills/test`
- **验证**：Ralph Loop集成，自动提炼技能

### 5. SimpleMem - 2026最新 +26.4% F1 30x Token
- **技术**：语义结构化压缩，在线语义合成，意图感知检索规划
- **实现**：`backend/memory/simple_mem.py` + `backend/runtime/simple_mem.py`双路径
- **4层记忆**：
  - conversational 会话：短期上下文，保留意图+关键实体
  - episodic 情景：过去交互，保留任务+结果+工具
  - semantic 语义：推断事实，保留事实
  - procedural 程序：学习工作流，保留步骤
- **压缩**：语义结构化压缩 30%，Token减少3x，论文数据+26.4% F1 30x减少
- **在线合成**：新记忆+相关记忆→抽象原则
- **意图感知检索**：根据意图category/action调整类型权重，file操作procedural 0.4，system状态semantic 0.4，organize任务procedural 0.5
- **API**：`GET /api/memory/simple` `POST /api/memory/simple/add` `GET /api/memory/simple/search`
- **验证**：压缩比统计，token_reduction

### 6. 梦境循环 Dream Loop - 2026最新
- **技术**：模拟 Karpathy autoresearch 630行脚本循环，3阶段 Dream+Evolve+Consolidate，参考 openclaw memory dreaming
- **实现**：`backend/runtime/dream_loop.py`
- **3阶段**：
  1. Dream 梦境生成：记忆重放+噪声→变体，技能组合→新任务，反事实推理→如果当初不同
  2. Evolve 进化：评估梦境价值，Q-Evolve in-distribution critic，生成新原则
  3. Consolidate 巩固：原则固化到语义记忆
- **API**：`POST /api/dream/cycle` `GET /api/dream/status`
- **验证**：1梦境→1原则→1巩固，counterfactual类型

### 7. Q-Evolve + Implicit Q-Learning + Process Reward
- **技术**：in-distribution critic优化，经验生命周期离线蒸馏+在线原则
- **实现**：`evolution_engine_v25.py` 集成
- **机制**：
  - Q-Evolve：in-distribution优化，process reward经验生命周期
  - Implicit Q-Learning：q_value评估
  - EvolveR：离线自蒸馏+在线原则
- **API**：`GET /api/evolution/status` `POST /api/evolution/start`

## 修复清单 v2.5

### 硬编码路径 14处 → 已修复
- **旧**：`D:\\llama.cpp\\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf` 硬编码
- **新**：环境变量 MODEL_PATH/QWEN_MODEL_PATH/LLM_MODEL_PATH > config/model_paths.json > 自动探测6候选 > 占位
- **实现**：`evolution_engine_v25.py _resolve_model_path()` 方法
- **配置**：`config/model_paths.json` 说明优先级，非硬编码
- **兼容**：Windows/Linux自动，演示环境映射

### 同步阻塞 → 已修复
- **旧**：psutil.cpu_percent(interval=1) 阻塞1秒
- **新**：interval=0.5 + async/await + 思考预算动态分配
- **验证**：check_idle非阻塞，evolution_engine全async

### 轮询竞态 → 已修复
- **旧**：前端轮询可能竞态
- **新**：Ralph Loop fresh context文件状态，状态在文件不在上下文，每次全新Agent，prd.json passes布尔
- **前端**：30秒+自适应15秒+hidden暂停，已优化

### 裸except 152→0 → v2.4已修复
- 运行代码0裸except，备份文件20不计

### print 166→loguru → v2.3已修复
- loguru统一，文件轮转10MB 7天

## API清单 v5.0 35个

### 核心
- GET /api/health v5.0 2026进化循环版
- POST /api/chat 支持thinking_mode auto/think/no_think + 有界自校正 + SimpleMem
- POST /api/agent/execute
- GET /api/tools
- POST /api/tools/call

### 2026新增
- POST /api/thinking/budget 思考预算
- GET /api/thinking/budget
- POST /api/ralph/run Ralph Loop
- GET /api/ralph/status 三护栏
- POST /api/correction/bounded 有界自校正
- GET /api/correction/stats UCSL可观测性
- GET /api/skills/library SAGE技能库
- POST /api/skills/test
- GET /api/memory/simple SimpleMem
- POST /api/memory/simple/add
- GET /api/memory/simple/search 意图感知
- POST /api/dream/cycle 梦境循环3阶段
- GET /api/dream/status

### 认证
- POST /api/auth/login JWT
- GET /api/auth/check
- POST /api/auth/logout

### 记忆向量
- GET /api/memory/vector/search 真实向量+关键词回退
- POST /api/memory/vector/add
- GET /api/memory
- GET /api/skills
- GET /api/traces
- GET /api/contracts

### 安全
- GET /api/security/sandbox/check
- GET /api/security/scan
- GET /api/security/wsl
- POST /api/security/wsl/exec

### 进化
- GET /api/evolution/status v2.5 7技术详情
- POST /api/evolution/start
- GET /api/evolution/data
- POST /api/dreaming/run-all 旧梦境兼容
- GET /api/dreaming/status

### 工具
- GET /api/runtime/intent/parse
- GET /api/runtime/state/observe
- POST /api/runtime/plan
- POST /api/search/real
- GET /api/search/real
- POST /api/vision/ocr 真实OCR
- GET /api/vision/ocr
- GET /api/utils/cleanup

### 其他
- GET /api/policy
- GET /api/model-registry
- GET /api/benchmark
- POST /api/benchmark/run-all

## 依赖最小必要
- backend：FastAPI 0.115.0 + Uvicorn 0.32.0 + slowapi 0.1.9 + filelock 3.15.0 + APScheduler 3.10.4 + python-jose 3.3.0 + loguru 0.7.2 + sqlite-vec 0.1.6 + rapidocr 50MB + psutil
- frontend：原生HTML/CSS/JS + ES Modules 8模块 + Canvas原生图表 + CSS变量深色主题
- database：SQLite WAL + 8表 + filelock + 迁移一次 + 备份
- model：Qwen3 30B-A3B MoE 3B激活 IQ4_XS 18.5GB + llama.cpp + OpenAI兼容 + 思考预算
- evolution：Thinking Budget + Ralph Loop + Bounded Correction UCSL + SAGE Skill Library + SimpleMem + Dream Loop + Q-Evolve

## 为什么最小
无打包、无ORM、无Redis、无Docker强制，单文件SQLite，单端口8000，Windows原生WMI/Win32，Linux兼容psutil，技术栈夯实8层必要，非14层臃肿。

## 验证
- 思考预算：复杂→/think 32768 0.95，简单→auto 8192
- Ralph Loop：三护栏通过，1迭代完成，passes布尔
- 有界自校正：2轮约束，置信度0.6→0.85
- 梦境循环：1梦境→1原则→1巩固
- 技能库：Sequential Rollout集成
- SimpleMem：压缩统计
- 硬编码：环境变量>配置>探测>占位
- 编译：7模块py_compile通过
- API：27/27原 + 13新 = 40 API全通
