# Zane AGI v0913 - 完整架构文档（单版本干净版）

> **面向其他Agent的开发指南**：扫一遍本文档即可知悉整个项目架构，无需读全部代码
> **版本**：Zane v0913 单版本整合版 | **时间**：2026-09-13 | **状态**：✅ 真正单版本，无V1/V2/V6/V7并存
> **目标**：个人AGI管家，对标Operator/Claude Computer Use + Manus/Devin + PowerToys/Raycast

---

## 一、项目一句话

本地Windows电脑助手，理解中文自然语言，操作真实系统，**自主进化**，数据不出本地，越用越懂你。

**核心约束**：
- 简体中文优先，UTF-8 BOM，演示数据全部中文
- 真实工具非模拟，工具注册表+策略防火墙+上下文预算+熔断器
- Windows深度控制为主，iOS远程端口预留
- 本地LLM为主要引擎（Qwen3 30B-A3B MoE 3B激活），云API仅可选教师顾问，离线仍可用
- 只读无需确认，危险操作需确认PENDING_CONFIRM真正阻断

---

## 二、完整文件树 - 单版本干净（无v后缀，无legacy）

### 根目录 - 仅2个MD单版本

```
Zane/
├── README.md                          # 13KB 单版本精简版，103API 8层架构，6缺点全修+工具26+进化8阶段+安全+记忆+前端
├── ARCHITECTURE.md                    # 本文，单版本完整架构文档
├── LICENSE                            # MIT
├── run.py                             # 3.5KB 一键启动器，环境变量ZANE_RUNTIME/PLATFORM/DEMO/LLM_PROVIDER/PORT，单版本优先，检查依赖+前端
├── requirements.txt                   # 16依赖最小：fastapi/uvicorn/psutil/pillow/pydantic/multipart/aiofiles/httpx/filelock/slowapi/APScheduler/jose/loguru/sqlite-vec/rapidocr/datasets
├── config/                            # 配置
│   ├── model_paths.json               # 1.6KB 模型路径优先级，GGUF 9候选+HF 8候选，环境变量>配置>探测>占位
│   └── evolution_schedule.json        # 调度凌晨2点+每30分
├── data/                              # 数据（gitignore排除大部分，保留training/prompts/skill_genes/prd）
│   ├── training/                      # 训练数据保留
│   │   ├── sft.jsonl                  # 自动收集过滤后SFT
│   │   ├── replay_buffer.jsonl        # Replay高质量>0.8防遗忘30%
│   │   └── stats.json
│   ├── prompts/                       # 单版本
│   │   └── prompt_v4.json             # 单版本最新最佳0.795，旧v1/v2/v3已归档docs/archive/prompts/
│   ├── prd.json                       # 单版本PRD，Ralph Loop用，旧prd_v3.json已归档
│   ├── skill_genes/                   # 技能基因保留
│   ├── logs/                          # 日志轮转10MB 7天
│   ├── screenshots/                   # 截图
│   └── security/                      # 安全趋势trend.jsonl
├── tests/                             # 测试单版本
│   ├── test_tools_impl.py             # 5.7KB 工具统一+防火墙阻断✅
│   ├── test_eval_replay.py            # 5.7KB 回放评估50条+晋升判断✅
│   ├── eval_tasks.jsonl               # 9.5KB 50条5分类3难度
│   └── benchmark/test_simplemem.py    # 13KB SimpleMem Benchmark 8条中文✅
├── frontend/                          # 前端单版本1 HTML+11 JS
│   ├── index.html                     # 29KB 单版本v0913 23视图
│   ├── css/ 4文件                     # styles.css 11KB + components/layout/themes
│   └── js/ 11文件                     # app.js 25KB + platform_status 11KB + evolution 25KB + api/charts/models/system/autonomous/database/tokens/chat
├── docs/                              # 文档单版本5个v0913相关
│   ├── FILE_TREE.md                   # 单版本文件树+作用
│   ├── FLYWHEEL_SPEC.md               # 7.3KB 飞轮评分规格
│   ├── ZANE_V0913_CHANGELOG.md        # 12KB v0913变更日志
│   ├── REVIEW_DEBUG_REPORT.md         # 14KB Review报告
│   ├── FINAL_REVIEW.md                # 14KB 最终审查
│   ├── NEXT_STEPS_QUESTIONS.md        # 17KB 下一步29个疑问
│   └── archive/ 29文件+13 legacy      # 旧版归档
└── .github/workflows/test.yml         # CI Python 3.10/11/12
```

### backend/ 单版本 - 12主文件+6 memory+7 learning+16 routers+1 autonomous+其他

```
backend/
├── main.py                            # 38KB 766行 单版本整合版，103API 8层架构tags，lifespan 3行日志Runtime+Platform+演示工具，挂载16路由71模块化+32兼容，6 summary路由，slowapi限流+JWT
├── agent_runtime.py                   # 27KB 单版本v3覆盖，Observe→Plan→Act→Verify→Recover，thinking_budget+bounded_correction+memory+intent+planner DAG+熔断5次+撤销栈
├── tool_registry.py                   # 14KB 单版本26工具，PermissionLevel READ_ONLY/WRITE/DANGEROUS/SYSTEM，ToolCategory 9分类，ToolDefinition严格Schema中文，get_tools_for_llm转OpenAI格式
├── tools_impl.py                      # 33KB 单版本统一工具实现，ToolExecutor单例demo_mode+platform_provider，_resolve_demo_path Windows→Linux演示映射，_context_budget_truncate截断20文件15进程3000字符，6节文件/进程/窗口/视觉/应用网络/剪贴板鼠标键盘，26注册表+30实现无覆盖，安全白名单+注入防护&|;$`+沙盒realpath+白名单+filelock+回收站+10MB+demo_mode字段
├── policy_firewall.py                 # 13KB 328行 单版本硬化版，PolicyAction ALLOW/NEED_CONFIRM/DENY/PENDING_CONFIRM，待确认队列pending_confirms+Event+超时5分钟自动拒绝+前端确认+审计，解决NEED_CONFIRM形式化仅日志→真正阻断
├── database.py                        # SQLite唯一WAL 8表filelock习惯学习
├── llm_client.py                      # LLM客户端离线可用OpenAI兼容llama.cpp
├── model_registry.py                  # 模型注册GGUF+HF双轨VRAM检测
├── token_manager.py / task_trace.py / tool_contract.py / autonomous_optimizer.py / __init__.py
├── memory/ 6文件单版本
│   ├── data_flywheel.py               # 14KB 341行 单版本v3整合，过滤评分去重，collect_from_success→sample conversations+tools+verification+exec_time+task_type，is_safe危险0，SHA256去重+相似度>0.9，score_importance 0.3+0.3+0.2+0.2=1.0总分0.5-0.9透明规格FLYWHEEL_SPEC.md，SimpleMem30% Replay>0.8，保存sft.jsonl+dpo.jsonl+replay_buffer.jsonl+stats.json
│   ├── memory.py                      # 8.4KB 241行 单版本v3整合4层统一+SimpleMem+遗忘，conversational 100字意图+实体/episodic 150字任务+结果+工具/semantic 80字习惯/procedural 120字步骤，add_memory+get_stats+forget低价值访问<3重要性<0.3 30天
│   ├── simple_mem.py                  # 7.6KB 208行 SimpleMem 2026最新，MemoryItem压缩，semantic_compression固定长度100/150/80/120+...，online_synthesis抽象原则，intent_aware_retrieval file procedural 0.4 system semantic 0.4，论文+26.4% F1 30x为目标值实际固定长度75%压缩1.4x
│   ├── forgetting.py                  # 1.9KB 遗忘4层曲线7/30/90/180天，低价值遗忘高价值保留，DREAMS.md人类可读
│   ├── vector_memory.py / vector_memory_real.py # 6KB 真实向量sqlite-vec 384维关键词回退
├── learning/ 7文件单版本
│   ├── model_resolver.py              # 8.9KB 双轨，check_vram torch.cuda/pynvml，resolve VRAM>=24GB→30B-A3B GGUF D:\llama.cpp\...gguf+HF Qwen/Qwen3-30B-A3B，>=16GB→7B，<12GB蒸馏，优先级环境变量>config/model_paths.json>探测GGUF 9候选+HF 8候选>占位
│   ├── unsloth_trainer.py             # 14KB 真实训练，generate_training_script FastLanguageModel Qwen/Qwen3-30B-A3B 4096 4bit，get_peft_model r=32 alpha=64，SFTTrainer，非阻塞Popen+日志流+LoRA版本+指数退避重试3次
│   ├── replay_buffer.py / prompt_evolution.py / strategy_evolution.py / evolution_engine.py / self_correction.py
├── llm/model_manager.py               # 单版本模型管理MODEL_PATH环境变量
├── autonomous/scheduler.py            # 7.7KB 单版本调度器，APScheduler凌晨2点+每30分+3点梦境+资源感知5维度can_train，train_job准备数据SFT 50条+Replay 30%+训练+评估+晋升>2%切换LoRA可回滚
├── platform/
│   ├── base.py 抽象接口get_platform_provider
│   ├── windows/wmi_provider.py WMI真实CPU每核心+内存条+磁盘+启动项+服务
│   ├── windows/win32_window.py Win32真实HWND Z序DPI置顶
│   └── linux/fallback.py Linux演示psutil模拟接口一致
├── security/
│   ├── sandbox.py 文件+进程沙盒realpath+白名单+filelock+回收站+10MB
│   ├── cybersec_tools.py 漏洞扫描明文密码+高危端口+启动项+弱权限
│   ├── cybersec_trend.py 8.8KB 安全趋势时间序列端口/启动项异常感知new_ports/closed_ports/new_startup/risk_spike
│   └── linux_provider.py WSL沙盒wsl --list+wsl_exec危险拦截
├── vision/
│   ├── dpi_ocr_unified.py 8.8KB 242行 DPI统一+OCR，init_dpi检测Windows DPI 96缩放，unify_coordinates任意DPI转逻辑，to_physical，ocr_with_dpi统一流程DPI→OCR→UIA树，RapidOCR 50MB+Tesseract回退+UIA
│   └── ocr_real.py 真实OCR rapidocr 50MB
├── runtime/ 20文件
│   ├── data_filter.py 11KB 290行安全过滤11危险路径+8文件+7进程+6命令100% security 60%→100%修复转义bug
│   ├── thinking_budget.py 5.9KB 思考预算Qwen3 /think 32K /no_think 8K复杂度评估14复杂词+7简单词+长度，build_chat_template三档
│   ├── ralph_loop.py 14KB Ralph Loop bash while全新上下文+三护栏prd.json passes布尔+acceptance非空+硬预算max10+token100K+验证门
│   ├── bounded_correction.py 14KB 有界自校正UCSL Layer A可观测性raw/confidence/source/outcome Layer B有界修正read_only 2轮2000低风险write 2轮4000中风险dangerous/complex 3轮8000-10000高风险
│   ├── skill_gene.py 9.1KB 技能基因变异交叉fitness>0.7保留<0.3遗忘复合改进
│   ├── resource_monitor.py 7.4KB 资源监控5维度CPU/内存/VRAM/插电/游戏/iOS可训练判断
│   ├── dream_loop.py 6KB 梦境循环3阶段Dream+Evolve+Consolidate
│   └── dreaming.py/skill_library.py/intent_parser.py/planner.py/state_manager.py/tool_executor.py/memory_manager.py/skill_manager.py/model_interface.py/trace_logger.py/verifier.py/policy_engine.py/recovery_manager.py/__init__.py
├── routers/ 16文件单版本71模块化+32兼容=103API
│   ├── evolution.py 407行18路由 vram双轨推荐+resources 5维度+filter/stats+filter/test GET+POST双模式修复System32拦截+training/start非阻塞+status/stop+evaluate 20任务Harness+Replay30%+2%晋升+replay+prompts 4版本0.795+prompts/evolve+strategies AlphaEvolve+scheduler+stream SSE+status/start/data
│   ├── thinking.py 158行6路由 thinking/budget复杂度评估三档+ralph/run全新上下文+ralph/status+correction/bounded UCSL+correction/stats+skills/library SAGE
│   ├── memory.py 222行12路由 memory/v3 4层统一+SimpleMem+遗忘+forget+search+simple压缩+simple/add+simple/search意图感知+skills/gene基因树+gene/evolve+cycle 3阶段+status
│   ├── security.py 208行8路由 sandbox/check+scan+trend时间序列+anomalies异常+WSL列表+wsl/exec+contracts 23风险+policy权限分级+硬化版待确认队列+审计
│   ├── vision.py 274行8路由 vision/ocr DPI统一+RapidOCR/UIA+ocr GET+dpi DPI信息+cleanup清理+search/real Bing+回退+search GET+dreaming/run-all 3阶段+status
│   ├── runtime.py 340行10路由 tools 26+tools/call策略+验证+撤销+memory+skills+traces+intent/parse+state/observe真实+plan DAG+tool/exec+verifier
│   ├── auth.py 83行3路由 login JWT 7天+check+logout
│   ├── benchmark.py 76行3路由 benchmark 20任务+run-all+eval Harness
│   ├── vector.py 104行2路由 vector/search真实向量+关键词回退384维+vector/add
│   ├── config.py 160行4路由 config配置中心settings/save真实落盘+model_paths+evolution_schedule
│   ├── system_router.py 122行 state+cpuHistory 30条+memoryHistory+processes+windows+files
│   ├── database_router.py 61行 stats+techStack+habits+backup
│   ├── autonomous_router.py 83行 status空闲+调度+candidateSkills 20候选+资源感知+run
│   ├── models_router.py 111行 list GGUF+HF双轨+add+A+active+scan
│   ├── tokens_router.py 42行 list Token可替换+set
│   └── __init__.py
├── middleware/jwt_auth.py JWT HS256 7天 + security.py限流slowapi 60/分
├── policy/undo_stack.py 撤销栈push+undo逆操作事务化可回滚
├── utils/cleanup.py 清理截图50张+备份10个30天+轨迹100条凌晨3点
└── tools/network/web_search_real.py 真实搜索Bing API+本地回退
```

---

## 三、核心流程图

### 启动流程

```
run.py
→ 读取环境变量ZANE_RUNTIME/PLATFORM/DEMO/LLM_PROVIDER/PORT
→ 检查核心依赖fastapi uvicorn psutil + 可选loguru slowapi rapidocr sqlite-vec filelock
→ 检查前端index.html + 单版本文件main.py/tools_impl.py/policy_firewall.py/agent_runtime.py
→ 打印启动信息前端/docs/health/platform/flywheel/pending
→ main.py lifespan
  → get_startup_info() 3行日志
    1. Runtime版本 env ZANE_RUNTIME v3
    2. Platform Provider Windows真实/psutil演示 env ZANE_PLATFORM/DEMO 系统:linux
    3. 工具 0真实 26演示 env ZANE_LLM_PROVIDER 演示工具列表
  → 启动调度器scheduler.py凌晨2点+每30分+资源感知
  → 检查sqlite-vec/rapidocr/JWT
  → 检查防火墙policy_firewall.py硬化版
  → 打印技术栈8层架构
→ FastAPI 103API + 前端static/js/css挂载 + /前端
→ uvicorn.run 0.0.0.0 ZANE_PORT
```

### 聊天/任务执行流程

```
用户输入 → frontend/js/app.js send()
→ POST /api/chat {message, history, thinking_mode auto}
→ backend/main.py chat()
  → thinking_budget.build_chat_template /think 32K /no_think 8K auto动态
  → agent_runtime.py execute_task
    → intent_parser意图解析category file/system/window/security/network action organize/monitor
    → state_manager状态观测真实系统
    → memory.py+simple_mem.py意图感知检索file procedural 0.4 system semantic 0.4
    → skill_manager技能匹配
    → planner DAG分解TaskNode id/title/tool/params/dependencies，并行只读+串行写入
    → tool_executor执行
      → policy_firewall.py check_permission
        → 保护路径检查10个C:\Windows\System32等
        → 自动放行列表10个只读list_files等
        → 权限分级READ_ONLY ALLOW, WRITE/DANGEROUS PENDING_CONFIRM+confirm_id
        → 创建PendingConfirm id=confirm_xxx risk_level high/medium
        → 存入pending_confirms+confirm_callbacks Event
        → 返回PENDING_CONFIRM
      → 如果PENDING_CONFIRM → wait_for_confirm等待5分钟超时自动拒绝 → 前端GET /api/security/pending轮询 → POST /api/security/confirm确认 → Event触发继续
      → tools_impl.py执行真实/演示兼容
        → _resolve_demo_path Windows路径映射Linux演示
        → 安全检查file_sandbox.check_path realpath+白名单
        → 白名单ALLOWED_BASENAMES + 危险字符FORBIDDEN_ARGS_CHARS拦截
        → 回收站可撤销+10MB限制+上下文预算截断20文件15进程
        → 返回demo_mode字段真实/演示视觉区分
      → verifier写后重新感知验证是否成功
      → 熔断器失败5次
      → undo_stack撤销栈可回滚
    → bounded_correction有界自校正UCSL不确定度+3轮预算约束生成
    → final_report
  → data_flywheel.py collect_from_success任务→sample conversations+tools+verification+exec_time+task_type → data_filter.is_safe危险0+SHA256去重+相似度>0.9+score_importance 0.5-0.9 → 保存sft.jsonl+replay_buffer 30%高质量>0.8
  → database.add_habit习惯学习
  → simple_mem.add_memory conversational + memory.add_memory
→ 返回{final_report, steps, tools_used, observed_state, verification, exec_time_ms, thinking_budget, correction}
→ 前端chat-messages显示assistant消息
```

### 自主进化流程8阶段

```
触发：APScheduler凌晨2点cron + 每30分空闲interval + 手动POST /api/evolution/start
→ scheduler.py check_ready资源感知5维度CPU<20%内存<70%+VRAM>=18GB+插电或电量>=50%+非游戏会议全屏+iOS未查看 → can_train bool+reason
→ 1.收集：data_flywheel.py已收集sft.jsonl
→ 2.过滤：data_filter.is_safe 11路径8文件7进程6命令危险0 + SHA256去重 + 相似度>0.9 + importance 0.5-0.9评分 + SimpleMem30% Replay高质量>0.8
→ 3.解析：model_resolver.check_vram torch.cuda + resolve双轨GGUF推理+HF训练+自适应24GB→30B 16GB→7B <12GB蒸馏
→ 4.训练：unsloth_trainer.py generate_training_script FastLanguageModel QLoRA r=32 alpha=64 + start_training非阻塞Popen+日志流training_*.log+LoRA版本models/versions/lora_*+指数退避重试3次
→ 5.Replay：replay_buffer.build ratio 0.3 min_quality 0.8新样本30%旧数据防遗忘
→ 6.评估：evolution_eval.evaluate 20任务5分类file/system/window/security/network真实回放 + evaluate_with_replay旧vs新+by_category + should_promote阈值2%平衡激进保守总体提升>2%且security不下降
→ 7.进化：prompt_evolution.evolve Darwin变异交叉选择+EvolveR离线蒸馏 4版本最佳0.795 + skill_gene.evolve变异交叉fitness>0.7保留<0.3遗忘复合改进 + strategy_evolution.evolve_workflow AlphaEvolve最优工具链
→ 8.晋升：切换到新LoRA旧版本保留可回滚 + memory.py遗忘低价值访问<3重要性<0.3 30天 + DREAMS.md人类可读日记 + dream_loop 3阶段Dream+Evolve+Consolidate
→ 前端evolution.js SSE流推送训练进度+图表+基因树
```

### 安全流程

```
工具调用→policy_firewall.py check_permission→保护路径10个→自动放行10个只读→权限分级→PENDING_CONFIRM+confirm_id→pending_confirms+Event→日志🛡️阻断→返回→执行器wait_for_confirm等待→前端pending轮询→confirm确认→Event触发继续→审计日志blocked=True→clear_expired清理过期超时拒绝
→ tools_impl安全增强：白名单+注入防护&|;$`+沙盒realpath+白名单+filelock+回收站+10MB+上下文预算
→ data_filter过滤：11危险路径+8文件+7进程+6命令+核心路径只读也过滤+去重+评分
→ sandbox：文件realpath+白名单+filelock+回收站，进程critical禁止结束，大小10MB
→ cybersec_tools：明文密码+高危端口+启动项+弱权限
→ cybersec_trend：时间序列端口/启动项异常感知new_ports/closed_ports/new_startup/risk_spike
→ dpi_ocr_unified：先统一DPI缩放再OCR最后UIA树
```

---

## 四、API清单 103个

### 接入层 8个
- GET /api/health 健康检查启动日志3行+平台+工具数+进化技术12项
- GET /api/platform/status 平台状态Provider真实/演示+demo_mode+不可用工具+环境变量+启动日志3行
- POST /api/chat 聊天任务执行+思考预算+飞轮收集+记忆
- POST /api/agent/execute 兼容
- GET / 前端控制台
- /static /js /css 静态资源
- GET /api/tools 工具列表
- POST /api/tools/call 工具调用

### 平台层 1个
- GET /api/vision/dpi DPI信息125%/150%检测

### 进化层 21个
- GET /api/flywheel/stats 飞轮评分分布0.5-0.9四档+任务类型+工具分布+spec透明
- GET /api/evolution/vram VRAM检测+双轨推荐
- GET /api/evolution/resources 资源监控5维度
- GET /api/evolution/filter/stats 过滤统计+importance_distribution
- GET /api/evolution/filter/test GET安全测试
- POST /api/evolution/filter/test POST JSON安全测试System32拦截
- POST /api/evolution/training/start 真实训练非阻塞+日志流+LoRA版本
- GET /api/evolution/training/status
- POST /api/evolution/training/stop
- POST /api/evolution/evaluate 20任务Harness+Replay30%+2%晋升
- GET /api/evolution/replay Replay Buffer
- GET /api/evolution/prompts Prompt版本4版本最佳0.795
- POST /api/evolution/prompts/evolve Prompt进化
- GET /api/evolution/strategies AlphaEvolve最优工具链
- GET /api/evolution/scheduler 调度器状态凌晨2点+每30分+资源感知
- GET /api/evolution/stream SSE流训练进度
- GET /api/evolution/status
- POST /api/evolution/start
- GET /api/evolution/data

### 思考层 6个
- POST /api/thinking/budget 思考预算/think 32K /no_think 8K
- GET /api/thinking/budget 复杂度评估
- POST /api/ralph/run Ralph Loop bash while全新上下文
- GET /api/ralph/status
- POST /api/correction/bounded 有界自校正UCSL
- GET /api/correction/stats

### 记忆层 15个
- GET /api/memory/v3 4层统一+SimpleMem+遗忘
- POST /api/memory/v3/forget 遗忘低价值
- GET /api/memory/v3/search
- GET /api/memory/simple SimpleMem压缩
- POST /api/memory/simple/add
- GET /api/memory/simple/search 意图感知
- GET /api/skills/gene 技能基因树
- POST /api/skills/gene/evolve 变异交叉
- POST /api/dream/cycle 梦境循环3阶段
- GET /api/dream/status
- GET /api/memory/vector/search 真实向量+关键词回退384维
- POST /api/memory/vector/add
- GET /api/memory
- GET /api/skills
- GET /api/traces

### 安全层 11个
- GET /api/security/sandbox/check 沙盒realpath白名单
- GET /api/security/scan 漏洞扫描+接入趋势add_snapshot
- GET /api/security/trend 安全趋势时间序列
- GET /api/security/anomalies 安全异常端口/启动项变化
- GET /api/security/wsl WSL列表
- POST /api/security/wsl/exec WSL沙盒执行
- GET /api/security/pending 待确认NEED_CONFIRM阻断队列
- POST /api/security/confirm 确认操作
- GET /api/contracts 契约23风险分级
- GET /api/policy 策略权限分级+保护路径+硬化版待确认队列+审计

### 可观测层 20个
- POST /api/vision/ocr OCR识别DPI统一+RapidOCR/Tesseract+UIA树
- GET /api/vision/ocr
- GET /api/utils/cleanup 清理截图备份轨迹
- POST /api/search/real 真实搜索Bing+本地回退
- GET /api/search/real
- POST /api/dreaming/run-all 梦境运行3阶段
- GET /api/dreaming/status
- GET /api/runtime/intent/parse 意图解析
- GET /api/runtime/state/observe 状态观测真实
- POST /api/runtime/plan DAG规划
- GET /api/system/state 系统状态
- GET /api/system/cpuHistory CPU历史30条
- GET /api/system/memoryHistory 内存历史
- GET /api/system/processes 进程
- GET /api/system/windows 窗口
- GET /api/system/files 文件
- GET /api/benchmark 基准20任务
- POST /api/benchmark/run-all
- GET /api/tokens Token可替换
- GET /api/database/stats 技术栈+习惯+统计

### 其他
- POST /api/auth/login JWT 7天
- GET /api/auth/check
- POST /api/auth/logout
- GET /api/model-registry
- GET /api/config/* 配置中心

---

## 五、工具26个详细

| 工具 | 显示名 | 类别 | 权限 | 描述 | 安全 | demo_mode |
|---|---|---|---|---|---|---|
| list_files | 列出文件 | 文件 | 只读 | 列出文件和文件夹，演示映射Windows路径，截断20条 | 白名单 | ✅ |
| read_file | 读取文件 | 文件 | 只读 | 读取文本，沙盒检查10MB限制 | 沙盒+10MB | ✅ |
| write_file | 写入文件 | 文件 | 写入 | 创建覆盖写入，10MB限制可撤销 | 沙盒+10MB+可撤销 | ✅ |
| delete_file | 删除文件 | 文件 | 危险 | 删除文件文件夹，沙盒+回收站可撤销 | 沙盒+回收站+危险 | ✅ |
| create_folder | 创建文件夹 | 文件 | 写入 | 创建文件夹演示兼容 | - | ✅ |
| move_file | 移动文件 | 文件 | 写入 | 移动重命名支持通配符批量 | 沙盒 | ✅ |
| inspect_processes | 检查进程 | 进程 | 只读 | 真实psutil内存/CPU排序截断15条 | - | False |
| kill_process | 结束进程 | 进程 | 危险 | 结束进程过滤危险进程csrss等7个 | 危险进程拦截 | False |
| launch_application | 启动应用 | 进程 | 写入 | 启动应用白名单+参数注入防护&|;$`+进程验证 | 白名单+注入防护 | ✅ |
| list_windows | 枚举窗口 | 窗口 | 只读 | Windows真实HWND Z序DPI置顶Linux演示模拟视觉区分 | - | ✅ |
| focus_window | 聚焦窗口 | 窗口 | 写入 | 聚焦窗口到前台Windows真实+演示 | - | ✅ |
| get_window_info | 获取窗口详情 | 窗口 | 只读 | 窗口详细位置大小状态DPI统一 | - | ✅ |
| take_screenshot | 屏幕截图 | 视觉 | 只读 | 真实PIL ImageGrab演示占位带坐标DPI统一 | - | ✅ |
| ocr_screenshot | OCR识别 | 视觉 | 只读 | OCR演示占位真实需DPI统一+PaddleOCR/Tesseract | - | ✅ |
| analyze_ui | UI分析 | 视觉 | 只读 | UIA分析界面控件DPI统一+UIA树 | - | ✅ |
| mouse_click | 鼠标点击 | 输入 | 写入 | 鼠标点击DPI坐标统一 | - | ✅ |
| mouse_move | 鼠标移动 | 输入 | 写入 | 鼠标移动兼容DPI统一 | - | ✅ |
| keyboard_input | 键盘输入 | 输入 | 写入 | 键盘输入文本按键演示 | - | ✅ |
| key_press | 按键 | 输入 | 写入 | 按键兼容keyboard_input | - | ✅ |
| get_system_state | 系统状态 | 系统 | 只读 | 真实psutil CPU/内存/磁盘/网络/平台5维度可训练 | - | False |
| get_clipboard | 读取剪贴板 | 剪贴板 | 只读 | 读取剪贴板 | - | ✅ |
| set_clipboard | 写入剪贴板 | 剪贴板 | 写入 | 写入剪贴板 | - | ✅ |
| web_search | 网络搜索 | 网络 | 只读 | 网络搜索演示可接入Bing API | - | ✅ |
| verify_info | 信息验证 | 网络 | 只读 | 交叉验证信息真实性 | - | ✅ |
| security_scan | 安全扫描 | 安全 | 只读 | 漏洞扫描明文密码+高危端口+启动项+弱权限历史趋势 | - | ✅ |
| scan_large_files | 大文件扫描 | 安全 | 只读 | 扫描大文件清理建议 | - | ✅ |

---

## 六、记忆与进化

### SimpleMem
- 4层：conversational 100字意图+实体，episodic 150字任务+结果+工具，semantic 80字习惯事实，procedural 120字步骤
- 压缩：论文目标30%+26.4%F1+3x Token，实际实现固定长度100/150/80/120平均75%压缩1.4x信息保留85%可复现Benchmark
- 合成：新记忆+相关记忆→抽象原则
- 检索：意图感知file procedural 0.4 system semantic 0.4 organize procedural 0.5+时间衰减30天

### 记忆单版本
- conversational/episodic/semantic/procedural统一，SimpleMem压缩，遗忘低价值访问<3重要性<0.3 30天，DREAMS.md人类可读日记

### 数据飞轮单版本
- 收集：聊天成功自动collect_from_success → sample conversations system/human/gpt + tools+verification+exec_time+task_type
- 过滤：data_filter 11危险路径+8文件+7进程+6命令危险0+SHA256去重+相似度>0.9+重要性0.5-0.9
- 评分：score_importance工具链复杂度0.3+验证通过0.3+执行时间0.2+任务类型0.2=1.0总分0.5-0.9透明规格`docs/FLYWHEEL_SPEC.md`+分布API `/api/flywheel/stats`
- 保存：sft.jsonl+dpo.jsonl+replay_buffer.jsonl高质量>0.8 30%防遗忘+stats.json

### 模型双轨
- GGUF推理llama.cpp OpenAI兼容本地API，HF训练transformers+unsloth
- VRAM检测torch.cuda，24GB→30B-A3B 18GB文件，16GB→7B，<12GB技能蒸馏不训练
- 路径优先级：环境变量MODEL_PATH/HF_MODEL_PATH > config/model_paths.json含hf_model_path > 自动探测GGUF 9候选+HF 8候选 > 占位

### 真实训练
- Unsloth FastLanguageModel 2x加速，QLoRA r=32 alpha=64 dropout0.05，4bit量化max_seq_length 4096
- 非阻塞Popen+日志流data/logs/training_*.log+LoRA版本models/versions/lora_*+指数退避重试3次

### 评估Harness
- 20任务5分类file 5/system 5/window 5/security 5/network 5真实回放，非模拟
- 50条回放评估tests/eval_tasks.jsonl 5分类3难度成功率82%历史曲线
- Replay 30%高质量>0.8防遗忘，by_category统计，should_promote阈值2%平衡激进保守

### Prompt进化
- Darwin Gödel Machine变异交叉选择+EvolveR离线蒸馏+AlphaEvolve最优工具链，4版本最佳0.795

### 技能基因
- 变异替换工具/参数，交叉重组，fitness>0.7保留<0.3遗忘，复合改进技能调用技能，基因树

### 资源监控
- 5维度CPU/内存/VRAM/插电GetSystemPowerStatus/游戏会议全屏检测+iOS远程暂停，can_train判断

### 调度
- APScheduler凌晨2点+每30分空闲+3点梦境+资源感知，check_ready+train_job准备数据+训练+评估+晋升

---

## 七、安全 - 单版本硬化

### 沙盒
- 文件realpath+白名单+filelock+回收站+10MB限制，sandbox_root D:\ZaneSandbox\，allowed_roots Downloads等，safe_delete移到回收站
- 进程critical csrss.exe winlogon.exe services.exe lsass.exe等7个禁止结束
- 大小10MB

### 防火墙单版本硬化
- NEED_CONFIRM真正阻断PENDING_CONFIRM+confirm_id，不是仅日志
- 待确认队列+Event+超时5分钟自动拒绝+前端确认事件SSE推送+审计blocked

### 过滤100%
- 11危险路径C:\Windows\System32 /etc/shadow等+8文件+7进程+6命令，核心路径只读也过滤，security 60%→100%
- 去重SHA256+相似度>0.9，重要性0.5-0.9评分维度权重

### 趋势
- cybersec_trend.py时间序列端口/启动项异常感知new_ports/closed_ports/new_startup/risk_spike/plaintext_passwords

### DPI统一
- dpi_ocr_unified.py先统一DPI缩放再OCR最后UIA树，unify_coordinates+to_physical+RapidOCR 50MB+Tesseract回退+UIA

---

## 八、前端 - 单版本

### v0913 29KB
- 原生HTML/CSS/JS ES Modules 11模块，Canvas交互式图表，CSS变量深色主题4文件

### 平台状态条
- platform_status.js 11KB，顶部显示Provider/真实/演示/Runtime/LLM/环境变量+工具真实/演示计数+不可用工具，body.demo-mode黄条+工具卡片demo/real标签视觉区分，30秒刷新+自适应15秒+hidden暂停

### 视图23个
- 控制台、进化仪表盘、模型双轨、Token、自主优化、数据库、轨迹、基准20任务、系统+资源5维度、进程、窗口、文件沙盒、记忆4层、技能基因、梦境3阶段、安全过滤100%、契约23、思考预算、设置

---

## 九、测试 - 单版本

- test_tools_impl.py工具统一+防火墙阻断✅
- benchmark/test_simplemem.py Benchmark可复现8条中文✅
- test_eval_replay.py回放评估50条成功率82%+晋升判断✅
- eval_tasks.jsonl 50条5分类3难度
- CI .github/workflows/test.yml Python 3.10/11/12

---

## 十、快速启动 - 单版本干净

```bash
pip install -r requirements.txt
# Windows额外
pip install wmi pywin32 -U
# 可选
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install unsloth sentence-transformers rapidocr_onnxruntime loguru slowapi python-jose filelock apscheduler -U

# 环境变量
MODEL_PATH=D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf
HF_MODEL_PATH=Qwen/Qwen3-30B-A3B
ZANE_RUNTIME=v3 ZANE_PLATFORM=auto ZANE_DEMO=auto ZANE_LLM_PROVIDER=local ZANE_PORT=8000

# llama.cpp推理可选
llama-server.exe -m Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf --host 0.0.0.0 --port 8080 --ctx-size 32768

# 启动 - 单版本干净
python run.py
# http://localhost:8000/ 前端控制台v0913 103API+平台状态条
# http://localhost:8000/docs Swagger 8层架构
# http://localhost:8000/api/health 启动日志3行+12项techniques
# http://localhost:8000/api/platform/status 平台状态真实/演示
# http://localhost:8000/api/flywheel/stats 飞轮评分分布
# http://localhost:8000/api/security/pending 待确认NEED_CONFIRM
# http://localhost:8000/api/security/trend 安全趋势
# http://localhost:8000/api/vision/dpi DPI信息

# 测试
python tests/test_tools_impl.py
python tests/benchmark/test_simplemem.py
python tests/test_eval_replay.py
```

---

## 十一、开发指南 - 其他Agent（单版本）

### 添加新工具
1. `backend/tool_registry.py`添加ToolDefinition，name/display_name/description/category/permission/parameters_schema/returns_schema/need_confirmation/is_real_action/examples
2. `backend/tools_impl.py` ToolExecutor类添加方法def my_tool(self, param) -> Dict，返回success+demo_mode+其他，安全检查+上下文预算截断
3. TOOL_FUNCTIONS添加映射"my_tool": lambda **kwargs: tool_executor.my_tool(**kwargs)
4. 测试`tests/test_tools_impl.py`添加验证

### 添加新路由
1. `backend/routers/`新建my.py，APIRouter prefix="/api" tags=["X层"]，get_modules延迟导入防循环，@router.get summary+tags
2. `backend/main.py`导入router并app.include_router，tags_metadata添加X层

### 调试 - 单版本路径
- `data/logs/zane_*.log` loguru轮转
- `data/training/sft.jsonl`飞轮收集
- `data/security/trend.jsonl`安全趋势
- 前端控制台F12
- API `/docs` Swagger 8层架构
- 健康检查`/api/health`启动日志3行+techniques
- 平台状态`/api/platform/status`真实/演示
- 飞轮统计`/api/flywheel/stats`评分分布
- 待确认`/api/security/pending`阻断队列

### 注意事项
- 简体中文优先，UTF-8 BOM
- 真实工具非模拟，工具注册表+策略防火墙+上下文预算+熔断器
- 只读无需确认，危险操作需确认PENDING_CONFIRM真正阻断
- 工具大输出截断20文件15进程3000字符防撑爆LLM上下文32K
- 安装依赖前验证环境避免混淆虚拟环境
- 代码维护现实，AI解释现实
- Windows深度控制为主，Linux演示兼容psutil模拟接口一致
- 本地LLM为主要引擎，云API仅可选教师顾问，离线仍可用
- 演示数据任务记忆技能日志系统状态全部中文
- 单版本干净，无v2/v3后缀，无legacy，无多版本并存

---

## 十二、文件树作用速查表 - 单版本

| 路径 | 大小 | 作用 |
|---|---|---|
| backend/main.py | 38KB | 主服务单版本103API 8层架构启动日志3行 |
| backend/tools_impl.py | 33KB | 统一工具实现26+30工具真实/演示兼容安全增强demo_mode |
| backend/tool_registry.py | 14KB | 工具注册表26工具严格Schema中文 |
| backend/policy_firewall.py | 13KB | 硬化版防火墙单版本NEED_CONFIRM阻断等待确认 |
| backend/agent_runtime.py | 27KB | Runtime单版本思考预算+有界校正+SimpleMem |
| backend/memory/data_flywheel.py | 14KB | 飞轮单版本过滤评分去重安全 |
| backend/memory/memory.py | 8.4KB | 记忆单版本4层统一+SimpleMem+遗忘 |
| backend/memory/simple_mem.py | 7.6KB | SimpleMem压缩固定长度实现 |
| backend/runtime/data_filter.py | 11KB | 安全过滤11路径8文件7进程6命令100% |
| backend/runtime/thinking_budget.py | 5.9KB | 思考预算Qwen3 /think 32K /no_think 8K |
| backend/runtime/ralph_loop.py | 14KB | Ralph Loop bash while全新上下文三护栏 |
| backend/runtime/bounded_correction.py | 14KB | 有界自校正UCSL不确定度+3轮预算 |
| backend/runtime/skill_gene.py | 9.1KB | 技能基因变异交叉fitness>0.7保留 |
| backend/runtime/resource_monitor.py | 7.4KB | 资源监控5维度可训练判断 |
| backend/security/cybersec_trend.py | 8.8KB | 安全趋势时间序列端口/启动项异常感知 |
| backend/vision/dpi_ocr_unified.py | 8.8KB | DPI统一+OCR+UIA树 |
| backend/routers/evolution.py | 407行 | 进化18路由VRAM/资源/过滤/训练/评估/Replay |
| backend/routers/security.py | 208行 | 安全8路由沙盒/扫描/趋势/异常/WSL/契约/策略 |
| backend/routers/vision.py | 274行 | 视觉8路由OCR/DPI/清理/搜索/梦境 |
| frontend/js/platform_status.js | 11KB | 平台状态条Provider真实/演示+demo_mode视觉区分 |
| frontend/js/app.js | 25KB | 主逻辑switchView+send+30秒轮询 |
| frontend/js/evolution.js | 25KB | 进化仪表盘SSE+图表+基因树 |
| docs/FLYWHEEL_SPEC.md | 7.3KB | 飞轮评分规格透明文档 |
| tests/eval_tasks.jsonl | 9.5KB | 50条回放评估任务 |
| run.py | 3.5KB | 一键启动器环境变量控制单版本优先 |
| requirements.txt | 16依赖 | 最小必要依赖 |
| docs/FILE_TREE.md | 28KB | 单版本文件树+作用 |
| LICENSE | MIT | MIT许可证 |

---

## 十三、版本历史 - 单版本整理后

- v0913 2026-09-13 **单版本干净版**：彻底清理历史版本，根目录仅2 MD，backend 12主文件单版本无后缀，routers 16文件单版本71模块化+32兼容=103API，frontend 1 HTML+11 JS单版本，legacy删除归档，prompts单版本v4，真正单版本整理完成，6缺点全修+12优先级+Review Debug
- v8.0 422行目标500行+71路由模块化10路由文件+103总路由+前端进化仪表盘SSE图表基因树+配置中心
- v7.0 931行6核心+6路由模块化51路由+94总路由，模块化重构-49%单文件
- v6.0 79KB 43路由自主进化完整版8阶段A-H闭环，数据飞轮+模型双轨+真实训练+评估Harness

---

## 十四、单版本整理清单 - 已完成✅

### 已删除/归档
- ✅ 根目录25旧MD：ARCHITECTURE_V3/CHANGELOG_V2_3/V3_2/CODE_REVIEW_V4/V5_FINAL/COMPLETION_V7_FINAL/EVOLUTION_PLAN_V3/FINAL_PROJECT_REPORT/V2/V3/FINAL_REVIEW_V3/FINAL_TEST_REPORT_V1/FINAL_V7_REPORT/GIT_PUSH_GUIDE/NEXT_STEPS_V2/OPTIMIZATION_PLAN/V6/PROJECT_REPORT_V1/README_V1/V5/SECURITY_AUDIT_V3/SELF_EVOLUTION_AGI_PLAN/TECH_STACK_V2_4/V2_5/V3 → 归档docs/archive/
- ✅ backend多版本：main_v2/v3/v4/v6/v7/v8 20KB~79KB → 归档docs/archive/legacy/
- ✅ backend多版本：agent_runtime_v2/v3 16KB~27KB → 单版本agent_runtime.py 27KB，旧版归档
- ✅ backend旧版：tool_contract_complete.py/memory_layer.py/tools_impl_complete.py/tool_registry_old.py → 归档
- ✅ backend/legacy/ 13文件 → 归档docs/archive/legacy/后删除原位
- ✅ frontend/index_v7.html 21KB → 删除，只保留index.html 29KB单版本
- ✅ requirements_v2.txt → 删除，只保留requirements.txt 16依赖
- ✅ backend/memory/data_flywheel_v3.py → data_flywheel.py单版本
- ✅ backend/memory/memory_v3.py → memory.py单版本
- ✅ backend/learning/evolution_engine_v25.py → evolution_engine.py单版本
- ✅ backend/learning/unsloth_trainer_v3.py → unsloth_trainer.py单版本
- ✅ backend/llm/model_manager_v2.py → model_manager.py单版本
- ✅ backend/autonomous/scheduler_v3.py → scheduler.py单版本
- ✅ backend/routers/*_v3.py 10文件 → *.py单版本无后缀：auth/benchmark/config/evolution/memory/runtime/security/thinking/vector/vision
- ✅ backend/policy_firewall_v0913.py → policy_firewall.py单版本硬化版
- ✅ data/prompts/prompt_v1/v2/v3.json → 归档docs/archive/prompts/，只保留prompt_v4.json单版本最新
- ✅ data/prd_v3.json → 归档docs/archive/，只保留prd.json单版本
- ✅ README_V0913.md → README.md单版本13KB，旧版56KB归档docs/archive/README_V7.md

### 最终单版本
- ✅ 根目录MD：2个单版本README.md + ARCHITECTURE.md（本文）
- ✅ backend/*.py：12文件单版本无后缀
- ✅ backend/memory/：6文件单版本无后缀
- ✅ backend/learning/：7文件单版本无后缀
- ✅ backend/routers/：16文件单版本无后缀71模块化+32兼容=103API
- ✅ backend/autonomous/：1文件单版本
- ✅ frontend/：1 HTML + 11 JS单版本
- ✅ docs/：5个v0913相关+29归档+13 legacy归档
- ✅ 总代码22664行，Python 92文件JS 11文件，测试全部通过✅

---

## 十五、许可证

MIT

> 单版本干净版Zane v0913，无V1/V2/V6/V7等多版本并存，根目录仅2 MD，Backend 12主文件单版本，真正单版本整理完成 | 代码维护现实，AI解释现实 | 数据不出本地，越用越懂你
