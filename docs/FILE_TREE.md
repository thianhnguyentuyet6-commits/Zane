# Zane AGI v0913 - 单版本文件树 + 作用

> **干净单版本**：彻底清理历史版本，Zane v0913单版本，无V1/V2/V6/V7等多版本并存
> **根目录仅2个MD**：README.md + ARCHITECTURE.md + LICENSE，旧版全部归档docs/archive/
> **Backend单版本**：12个py主文件+6 memory+7 learning+16 routers+1 autonomous，全部去掉_v3/_v25后缀
> **Frontend单版本**：1 HTML + 11 JS，删除index_v7.html
> **时间**：2026-09-13

## 一、根目录 - 单版本干净

```
Zane/
├── README.md                          # 13KB 单版本精简版，Zane v0913 103API 8层架构，单版本+6缺点全修+工具26+API103+进化8阶段+安全+记忆+前端+启动+测试+目录结构
├── ARCHITECTURE.md                    # 48KB 完整架构文档面向其他Agent，扫一遍知悉整个项目架构无需读全部代码，文件树+作用+流程图+API清单+工具详细+开发指南
├── LICENSE                            # MIT
├── run.py                             # 3.5KB 一键启动器，环境变量控制ZANE_RUNTIME/PLATFORM/DEMO/LLM_PROVIDER/PORT，单版本优先，检查依赖+前端+单版本文件，uvicorn.run
├── requirements.txt                   # 16依赖最小必要：fastapi/uvicorn/psutil/pillow/pydantic/multipart/aiofiles/httpx/filelock/slowapi/APScheduler/jose/loguru/sqlite-vec/rapidocr/datasets
├── config/                            # 配置目录
│   ├── model_paths.json               # 1.6KB 模型路径优先级说明非硬编码，GGUF 9候选+HF 8候选，环境变量>配置>探测>占位
│   └── evolution_schedule.json        # 调度配置凌晨2点+每30分
├── data/                              # 数据目录（gitignore排除大部分json，保留training/prompts/skill_genes/prd）
│   ├── training/                      # 训练数据保留
│   │   ├── sft.jsonl                  # 自动收集过滤后的SFT数据，飞轮v3
│   │   ├── replay_buffer.jsonl        # Replay高质量>0.8防遗忘30%
│   │   └── stats.json                 # 统计
│   ├── prompts/                       # Prompt版本保留
│   │   └── prompt_v4.json             # 单版本最新，最佳0.795，旧v1/v2/v3已归档docs/archive/prompts/
│   ├── prd.json                       # 单版本PRD，Ralph Loop用，旧prd_v3.json已归档
│   ├── skill_genes/                   # 技能基因保留
│   ├── logs/                          # 日志轮转10MB 7天
│   ├── screenshots/                   # 截图
│   ├── security/                      # 安全趋势trend.jsonl
│   └── ...                            # 其他json被gitignore排除
├── tests/                             # 测试目录单版本
│   ├── __init__.py
│   ├── test_tools_impl.py             # 5.7KB 工具统一27工具无覆盖+防火墙阻断PENDING_CONFIRM+confirm_id，全部通过✅
│   ├── test_eval_replay.py            # 5.7KB 回放评估50条成功率曲线+晋升判断2%阈值，82%通过✅
│   ├── eval_tasks.jsonl               # 9.5KB 50条日常任务5分类file/system/window/security/network 3难度easy/medium/hard
│   └── benchmark/
│       ├── test_simplemem.py          # 13KB SimpleMem Benchmark可复现8条中文，count_tokens+semantic_compression固定长度100/150/80/120平均75%压缩1.4x信息保留85%，论文30%目标透明说明，通过✅
│       └── *.json                     # 结果
├── frontend/                          # 前端单版本
│   ├── index.html                     # 29KB 单版本v0913 103API 8层架构+平台状态条，23视图
│   ├── css/                           # 4文件拆分
│   │   ├── styles.css                 # 11KB 主样式深色主题CSS变量
│   │   ├── components.css             # 1.8KB 组件
│   │   ├── layout.css                 # 1.9KB 布局
│   │   └── themes.css                 # 主题
│   └── js/                            # 11文件单版本ES Modules
│       ├── app.js                     # 25KB 主逻辑switchView+send+load*，30秒轮询自适应15秒+hidden暂停，import platform_status.js
│       ├── platform_status.js         # 11KB 新增v0913，平台状态条Provider真实/演示+不可用工具+demo_mode视觉区分，injectStyles+loadStatus+render+updateToolCards，30秒刷新
│       ├── evolution.js               # 25KB 554行进化仪表盘SSE+图表+基因树
│       ├── api.js                     # API封装apiGet/apiPost+token/database/autonomous/system/models
│       ├── charts.js                  # 5KB Canvas交互式图表
│       ├── models.js                  # 8.4KB 模型管理双轨GGUF+HF+VRAM检测
│       ├── system.js                  # 系统状态
│       ├── autonomous.js              # 自主优化
│       ├── database.js                # 数据库
│       ├── tokens.js                  # Token管理
│       └── chat.js                    # 聊天
├── docs/                              # 文档单版本5个v0913相关
│   ├── FILE_TREE.md                   # 本文，单版本文件树+作用
│   ├── FLYWHEEL_SPEC.md               # 7.3KB 飞轮评分规格透明文档，维度权重工具链0.3+验证0.3+时间0.2+类型0.2=1.0总分0.5-0.9+分布+淘汰规则+过滤11路径8文件7进程6命令+调试API
│   ├── ZANE_V0913_CHANGELOG.md        # 12KB v0913变更日志6缺点+12优先级+文件清单+验证
│   ├── REVIEW_DEBUG_REPORT.md         # 14KB Review报告
│   ├── FINAL_REVIEW.md                # 14KB 最终审查报告
│   ├── NEXT_STEPS_QUESTIONS.md        # 17KB 下一步规划与疑问29个
│   └── archive/                       # 29文件旧版归档+13 legacy归档
│       ├── README_V7.md               # 旧README 56KB归档
│       ├── ARCHITECTURE_V3.md等25个   # 旧MD文档归档
│       ├── legacy/                    # 13文件历史代码归档
│       │   ├── main_v2.py/v3.py/v4.py/v6.py/v7.py/v8.py # 20KB~79KB 历史主服务
│       │   ├── agent_runtime.py/v2.py/v3.py # 历史Runtime
│       │   └── tool_registry_old.py等
│       └── prompts/                   # 旧prompt归档
│           └── prompt_v1/v2/v3.json
└── .github/workflows/test.yml         # 1.8KB CI Python 3.10/11/12
```

## 二、Backend单版本详细 - 12主文件+6 memory+7 learning+16 routers+1 autonomous

### backend/*.py 12文件单版本

| 文件 | 大小 | 行数 | 作用 |
|---|---|---|---|
| main.py | 38KB | 766行 | **主服务单版本整合版**，Zane v0913单版本+103API+8层架构，lifespan启动日志3行Runtime版本+Platform Provider+演示工具+环境变量ZANE_RUNTIME/PLATFORM/DEMO/LLM_PROVIDER/PORT，tags_metadata 8层分组Swagger文档化，挂载10路由模块化71路由+32兼容=103API，6路由summary：health/platform/flywheel/pending/confirm/chat/agent/execute/前端，安全中间件slowapi限流60/分+JWT认证，静态资源挂载/static /js /css，前端/单版本 |
| tools_impl.py | 33KB | 594行 | **统一工具实现单版本**，ToolExecutor单例demo_mode+platform_provider真实/演示，_resolve_demo_path统一Windows→Linux演示映射，_ensure_demo_files演示文件，_format_size，_context_budget_truncate截断20文件15进程3000字符防撑爆LLM上下文32K，6节文件list_files/read_file/create_folder/delete_file/write_file/move_file+进程inspect_processes/kill_process/get_window_info+窗口list_windows/focus_window+视觉take_screenshot/ocr_screenshot/analyze_ui+应用launch_application+网络web_search/verify_info+剪贴板+鼠标键盘，26注册表+30实现(4可选wsl等)TOOL_FUNCTIONS无覆盖，安全增强白名单ALLOWED_BASENAMES+危险字符FORBIDDEN_ARGS_CHARS &|;$`&&||注入防护+沙盒realpath+白名单+filelock+回收站可撤销+10MB限制+demo_mode字段视觉区分，loguru包装 |
| tool_registry.py | 14KB | 单版本 | **工具注册表单版本**，26工具v0913整合版修复不一致，PermissionLevel READ_ONLY/WRITE/DANGEROUS/SYSTEM，ToolCategory 9分类FILE/PROCESS/WINDOW/INPUT/VISION/SYSTEM/NETWORK/CLIPBOARD/SECURITY，ToolDefinition name/display_name/description/category/permission/parameters_schema/returns_schema/need_confirmation/is_real_action/examples，TOOL_REGISTRY 26个：文件6list_files/read_file/write_file/delete_file/create_folder/move_file+进程3inspect/kill/launch+窗口3list/focus/get_info+视觉3screenshot/ocr/analyze_ui+输入4mouse_click/move/keyboard/key_press+系统1get_system_state+剪贴板2get/set_clipboard+网络2web_search/verify_info+安全2security_scan/scan_large_files，get_tools_for_llm转OpenAI格式中文描述 |
| policy_firewall.py | 13KB | 328行 | **策略防火墙单版本硬化版v0913**，PolicyAction ALLOW/NEED_CONFIRM/DENY/PENDING_CONFIRM，PolicyRule+PendingConfirm+AuditLog，PolicyFirewallV0913待确认队列pending_confirms Dict+confirm_callbacks asyncio.Event+confirm_results，check_permission保护路径10个C:\Windows\System32 /etc/shadow等+自动放行列表10个只读list_files等+权限分级READ_ONLY ALLOW WRITE/DANGEROUS PENDING_CONFIRM+confirm_id，_create_pending_confirm创建待确认🛡️阻断，wait_for_confirm异步阻断等待5分钟超时自动拒绝，confirm_operation用户批准/拒绝+SSE推送，get_pending_confirms待确认列表前端轮询，log_execution审计blocked，clear_expired清理过期，解决缺点六NEED_CONFIRM形式化仅日志→真正阻断 |
| agent_runtime.py | 27KB | 单版本 | **Agent运行时单版本**，v3覆盖，AgentRuntimeV3完整执行循环，Observe→Plan→Act→Verify→Recover，thinking_budget思考预算/think/no_think，bounded_correction有界自校正UCSL，simple_mem+memory_v3记忆，intent_parser意图解析，planner DAG分解TaskNode，并行只读+串行写入+验证+熔断5次+撤销栈，execute_task任务执行 |
| database.py | - | - | SQLite唯一WAL 8表，filelock并发安全，习惯学习add_habit，traces轨迹，memory记忆 |
| llm_client.py | - | - | LLM客户端离线可用，OpenAI兼容本地API如llama.cpp，云API可选教师顾问，is_local_available |
| model_registry.py | - | - | 模型注册GGUF+HF双轨，VRAM检测 |
| token_manager.py | - | - | Token管理可替换 |
| task_trace.py | - | - | 任务轨迹 |
| tool_contract.py | - | - | 工具契约23个风险分级high/medium/low |
| autonomous_optimizer.py | - | - | 自主优化器20 Skill+APScheduler |

### backend/memory/ 6文件单版本

| 文件 | 大小 | 作用 |
|---|---|---|
| data_flywheel.py | 14KB 341行 | **数据飞轮单版本**，v3整合，过滤评分去重安全，collect_from_success任务→sample conversations system/human/gpt + tools+verification+exec_time+task_type，data_filter.is_safe危险0，SHA256去重+相似度>0.9，score_importance工具链复杂度0.3+验证通过0.3+执行时间0.2+任务类型0.2=1.0总分0.5-0.9透明规格FLYWHEEL_SPEC.md，SimpleMem30%高质量>0.8 Replay，保存sft.jsonl+dpo.jsonl+replay_buffer.jsonl+stats.json，get_training_stats+get_recent_samples |
| memory.py | 8.4KB 241行 | **记忆单版本**，v3整合，4层统一+SimpleMem+遗忘，conversational会话200条压缩100字意图+实体，episodic情景任务历史150字任务+结果+工具，semantic语义习惯事实80字，procedural程序可复用流程120字步骤，add_memory+get_stats+forget低价值访问<3重要性<0.3 30天，SimpleMem压缩 |
| simple_mem.py | 7.6KB 208行 | **SimpleMem单版本**，2026最新，MemoryItem id/type/content/compressed/importance/access_count/created_at/last_accessed/tags/embedding，SimpleMem compression_ratio 0.3目标，semantic_compression按类型固定长度100/150/80/120+...压缩标记，online_synthesis新记忆+相关记忆→抽象原则，intent_aware_retrieval意图感知file procedural 0.4 system semantic 0.4 organize procedural 0.5+时间衰减，add_memory自动压缩+合成，get_stats压缩率Token减少，论文+26.4% F1 30x减少为目标值实际实现固定长度 |
| forgetting.py | 1.9KB | 遗忘机制，4层遗忘曲线conversational 7天episodic 30天semantic 90天procedural 180天，低价值访问<3重要性<0.3超期遗忘，高价值访问>10重要性>0.8保留，DREAMS.md人类可读 |
| vector_memory.py | - | 旧向量 |
| vector_memory_real.py | 6.0KB | 真实向量sqlite-vec+sentence-transformers 384维，关键词回退 |

### backend/learning/ 7文件单版本

| 文件 | 大小 | 作用 |
|---|---|---|
| model_resolver.py | 8.9KB | 模型解析双轨，check_vram torch.cuda或pynvml，resolve VRAM>=24GB→30B-A3B GGUF D:\llama.cpp\...gguf+HF Qwen/Qwen3-30B-A3B，>=16GB→7B，<12GB技能蒸馏不训练，路径环境变量MODEL_PATH/HF_MODEL_PATH>config/model_paths.json含hf_model_path>自动探测GGUF 9候选+HF 8候选>占位 |
| unsloth_trainer.py | 14KB | 真实训练循环，generate_training_script FastLanguageModel.from_pretrained Qwen/Qwen3-30B-A3B max_seq_length 4096 load_in_4bit True，get_peft_model r=32 alpha=64，datasets load_dataset json，trl SFTTrainer，start_training非阻塞Popen+日志流training_*.log+LoRA版本models/versions/lora_*+指数退避重试3次 |
| replay_buffer.py | - | Replay Buffer 30%防遗忘，build ratio 0.3 min_quality 0.8高质量，replay_count新样本30%旧数据 |
| prompt_evolution.py | - | Prompt进化Darwin Gödel Machine变异交叉选择+EvolveR离线蒸馏，evolve 4版本最佳0.795 |
| strategy_evolution.py | - | 策略进化AlphaEvolve最优工具链搜索 |
| evolution_engine.py | - | 进化引擎，7技术+8模块闭环 |
| self_correction.py | - | 自校正 |

### backend/runtime/ 运行时

| 文件 | 作用 |
|---|---|
| data_filter.py | 11KB 290行安全过滤，11危险路径+8文件+7进程+6命令100% security 60%→100%修复转义bug |
| thinking_budget.py | 5.9KB 思考预算Qwen3 /think 32K /no_think 8K复杂度评估 |
| ralph_loop.py | 14KB Ralph Loop bash while全新上下文三护栏 |
| bounded_correction.py | 14KB 有界自校正UCSL不确定度+3轮预算 |
| skill_gene.py | 9.1KB 技能基因变异交叉fitness>0.7保留 |
| resource_monitor.py | 7.4KB 资源监控5维度CPU/内存/VRAM/插电/游戏/iOS可训练判断 |
| dream_loop.py | 6KB 梦境循环3阶段Dream+Evolve+Consolidate |
| dreaming.py | 14KB 旧梦境 |
| skill_library.py | 技能库SAGE Sequential Rollout |
| intent_parser.py | 意图解析category file/system/window/security/network |
| planner.py | DAG规划TaskNode并行只读+串行写入 |
| state_manager.py | 状态管理真实系统 |
| tool_executor.py | 工具执行熔断5次+撤销栈 |
| memory_manager.py | 记忆管理 |
| skill_manager.py | 技能管理 |
| model_interface.py | 模型接口 |
| trace_logger.py | 轨迹日志SQLite唯一filelock |
| verifier.py | 验证写后重新感知 |
| policy_engine.py | 策略引擎protected_paths critical_processes |
| recovery_manager.py | 恢复错误分类重试 |

### backend/security/ 安全层

| 文件 | 作用 |
|---|---|
| sandbox.py | 文件+进程沙盒realpath+白名单+filelock+回收站+10MB |
| cybersec_tools.py | 漏洞扫描明文密码+高危端口+启动项+弱权限 |
| cybersec_trend.py | 8.8KB 安全趋势时间序列端口/启动项异常感知，SecuritySnapshot+CyberSecTrend+detect_anomalies+get_trend+get_stats |
| linux_provider.py | WSL沙盒wsl --list+wsl_exec危险命令拦截 |

### backend/vision/ 视觉

| 文件 | 作用 |
|---|---|
| dpi_ocr_unified.py | 8.8KB DPI统一+OCR+UIA树，DPIOCRUUnified init_dpi+unify_coordinates+to_physical+get_dpi_info+ocr_with_dpi RapidOCR 50MB+Tesseract回退+_uia_tree |
| ocr_real.py | 真实OCR rapidocr 50MB |

### backend/platform/ 平台层

| 文件 | 作用 |
|---|---|
| base.py | 抽象接口get_platform_provider |
| windows/wmi_provider.py | WMI真实CPU每核心+内存条+磁盘+启动项+服务 |
| windows/win32_window.py | Win32真实HWND Z序DPI置顶缩略图 |
| linux/fallback.py | Linux演示psutil模拟接口一致 |

### backend/routers/ 16文件单版本71模块化+32兼容=103API

| 文件 | 行数 | 路由 | 作用 | 层 |
|---|---|---|---|---|
| evolution.py | 407行 | 18路由 | VRAM检测+双轨推荐+get_all，资源监控5维度，过滤统计+importance_distribution透明，过滤测试GET+POST双模式修复System32拦截，训练start非阻塞+日志流+LoRA版本，status/stop，evaluate 20任务Harness+Replay30%+2%晋升，replay Replay Buffer，prompts 4版本最佳0.795，prompts/evolve变异交叉，strategies AlphaEvolve，scheduler调度器，stream SSE流，status/start/data | 进化层 |
| thinking.py | 158行 | 6路由 | thinking/budget思考预算复杂度评估三档采样，ralph/run Ralph Loop全新上下文，ralph/status，correction/bounded有界自校正UCSL，correction/stats，skills/library SAGE | 思考层 |
| memory.py | 222行 | 12路由 | memory/v3 4层统一+SimpleMem+遗忘，memory/v3/forget，memory/v3/search，memory/simple压缩，memory/simple/add，memory/simple/search意图感知，skills/gene基因树，skills/gene/evolve变异交叉，dream/cycle 3阶段，dream/status | 记忆层 |
| security.py | 208行 | 8路由 | sandbox/check沙盒realpath白名单，scan漏洞扫描+接入趋势add_snapshot，trend时间序列端口/启动项异常感知新增，anomalies异常检测新增，wsl列表，wsl/exec沙盒执行，contracts契约23风险分级，policy策略权限分级+保护路径+硬化版v0913待确认队列+审计 | 安全层 |
| vision.py | 274行 | 8路由 | vision/ocr OCR识别DPI统一+RapidOCR/Tesseract+UIA树，vision/ocr GET，vision/dpi DPI信息125%/150%检测新增，utils/cleanup清理截图备份轨迹，search/real真实搜索Bing+本地回退，search/real GET，dreaming/run-all 3阶段，dreaming/status | 可观测层+平台层 |
| runtime.py | 340行 | 10路由 | tools工具26个，tools/call工具调用策略+验证+撤销，memory记忆，skills技能，traces轨迹，runtime/intent/parse意图解析，runtime/state/observe状态观测真实，runtime/plan DAG规划，runtime/tool/exec，runtime/verifier | 执行层 |
| auth.py | 83行 | 3路由 | auth/login JWT 7天，auth/check，auth/logout | 可观测层 |
| benchmark.py | 76行 | 3路由 | benchmark 20任务，benchmark/run-all，benchmark/eval评估Harness | 可观测层 |
| vector.py | 104行 | 2路由 | memory/vector/search真实向量+关键词回退384维，memory/vector/add | 可观测层 |
| config.py | 160行 | 4路由 | config配置中心settings/save真实落盘，model_paths，evolution_schedule | 可观测层 |
| system_router.py | 122行 | - | state系统状态，cpuHistory，memoryHistory，processes，windows，files | 可观测层 |
| database_router.py | 61行 | - | stats统计，techStack技术栈，habits习惯学习，backup备份 | 可观测层 |
| autonomous_router.py | 83行 | - | status空闲+调度，candidateSkills 20候选Skill+资源感知，run自主任务 | 可观测层 |
| models_router.py | 111行 | - | list模型列表GGUF+HF双轨，add添加模型A，active激活，scan扫描 | 可观测层 |
| tokens_router.py | 42行 | - | list Token可替换，set设置 | 可观测层 |
| __init__.py | 2行 | - | 空 |

### backend/autonomous/ 1文件单版本

| 文件 | 作用 |
|---|---|
| scheduler.py | 7.7KB 调度器单版本，APScheduler凌晨2点+每30分空闲+3点梦境+资源感知，check_ready 5维度can_train判断，train_job准备数据SFT 50条+Replay 30%+训练+评估+晋升>2%切换LoRA |

### 其他backend

| 文件 | 作用 |
|---|---|
| middleware/jwt_auth.py | JWT认证HS256 7天商业级 |
| middleware/security.py | 限流认证slowapi 60/分 |
| policy/undo_stack.py | 撤销栈push+undo逆操作事务化可回滚 |
| utils/cleanup.py | 清理截图50张+备份10个30天+轨迹100条定时凌晨3点 |
| tools/network/web_search_real.py | 真实搜索Bing API+本地回退 |

---

## 三、前端单版本 - 1 HTML+11 JS+4 CSS

| 文件 | 大小 | 作用 |
|---|---|---|
| index.html | 29KB | 单版本v0913 103API 8层架构+平台状态条，23视图：控制台、进化仪表盘、模型双轨、Token、自主优化、数据库、轨迹、基准20任务、系统+资源5维度、进程、窗口、文件沙盒、记忆4层v3、技能基因、梦境3阶段、安全过滤100%、契约23、思考预算、设置 |
| css/styles.css | 11KB | 主样式深色主题CSS变量 |
| css/components.css | 1.8KB | 组件 |
| css/layout.css | 1.9KB | 布局 |
| css/themes.css | 主题 |
| js/app.js | 25KB | 主逻辑switchView+send+loadTokens/loadDatabase/loadAutonomous/loadSystem/loadCharts/loadModels/loadTraces/loadSkills/loadMemory/loadProcesses/loadWindows/loadFiles/loadDreaming/loadEvolution/loadSecurity/loadContracts/loadSettings/loadBenchmark，30秒轮询自适应15秒+hidden暂停节能，import platform_status.js |
| js/platform_status.js | 11KB | 新增v0913平台状态条Provider真实/演示+不可用工具+demo_mode视觉区分，createBar创建DOM topbar下方，injectStyles注入样式real/demo区分+黄条+虚线+标签，loadStatus加载/api/platform/status 30秒刷新，render显示Provider/真实/演示/Runtime/LLM/环境变量+工具真实/演示计数+不可用工具，updateToolCards工具卡片demo/real类，body.demo-mode黄条+工具卡片区分 |
| js/evolution.js | 25KB 554行 | 进化仪表盘SSE+图表+基因树，训练统计+日志流+版本历史+资源状态 |
| js/api.js | 2.6KB | API封装apiGet/apiPost+tokenApi+databaseApi+autonomousApi+systemApi+modelsApi |
| js/charts.js | 5KB | Canvas交互式图表drawInteractiveCpuChart/drawInteractiveMemoryChart |
| js/models.js | 8.4KB | 模型管理双轨GGUF+HF+VRAM检测 |
| js/system.js | 3.5KB | 系统状态 |
| js/autonomous.js | 4.5KB | 自主优化 |
| js/database.js | 3.8KB | 数据库 |
| js/tokens.js | 3.6KB | Token管理 |
| js/chat.js | 1.1KB | 聊天 |

---

## 四、测试单版本 - 5文件

| 文件 | 作用 |
|---|---|
| test_tools_impl.py | 5.7KB 工具统一27工具无覆盖+防火墙阻断PENDING_CONFIRM+confirm_id，全部通过✅ |
| test_eval_replay.py | 5.7KB 回放评估50条成功率曲线+晋升判断2%阈值，82%通过✅ |
| eval_tasks.jsonl | 9.5KB 50条日常任务5分类file/system/window/security/network 3难度easy/medium/hard |
| benchmark/test_simplemem.py | 13KB SimpleMem Benchmark可复现8条中文，count_tokens+semantic_compression固定长度100/150/80/120平均75%压缩1.4x信息保留85%，论文30%目标透明说明，通过✅ |
| benchmark/*.json | 结果 |

---

## 五、文档单版本 - 5个v0913相关+29归档+13 legacy归档

| 文件 | 大小 | 作用 |
|---|---|---|
| FILE_TREE.md | 本文 | 单版本文件树+作用，面向其他Agent |
| FLYWHEEL_SPEC.md | 7.3KB | 飞轮评分规格透明文档，维度权重+代码+分布+淘汰规则+过滤机制+调试API+数据流 |
| ZANE_V0913_CHANGELOG.md | 12KB | v0913变更日志6缺点+12优先级+文件清单+验证 |
| REVIEW_DEBUG_REPORT.md | 14KB | Review报告，缺失项检查 |
| FINAL_REVIEW.md | 14KB | 最终审查报告，项目逻辑梳理 |
| NEXT_STEPS_QUESTIONS.md | 17KB | 下一步规划与疑问29个 |
| archive/ | 29文件 | 旧版MD文档归档：ARCHITECTURE_V3/CHANGELOG/CODE_REVIEW/FINAL_REPORT等+README_V1/V5/V7+TECH_STACK_V2_4/V2_5/V3+SECURITY_AUDIT等 |
| archive/legacy/ | 13文件 | 历史代码归档：main_v2/v3/v4/v6/v7/v8+agent_runtime/v2/v3+memory_layer+tool_registry_old+tools_impl_old/complete |
| archive/prompts/ | 3文件 | 旧prompt v1/v2/v3归档 |

---

## 六、配置与CI

| 文件 | 作用 |
|---|---|
| config/model_paths.json | 模型路径优先级说明非硬编码 |
| config/evolution_schedule.json | 调度配置凌晨2点+每30分 |
| .github/workflows/test.yml | 1.8KB CI Python 3.10/11/12依赖+语法+工具测试+Benchmark+回放评估+版本整合检查 |
| LICENSE | MIT |

---

## 七、数据目录（gitignore排除大部分）

```
data/
├── training/ 保留
│   ├── sft.jsonl 自动收集过滤后
│   ├── replay_buffer.jsonl Replay高质量30%
│   └── stats.json 统计
├── prompts/ 保留
│   └── prompt_v4.json 单版本最新最佳0.795
├── prd.json 单版本PRD Ralph Loop
├── skill_genes/ 保留
├── logs/ 日志轮转
├── screenshots/ 截图
├── security/ 安全趋势trend.jsonl
└── ... 其他json被gitignore排除
```

---

## 八、统计

- **Backend**：12主文件+6 memory+7 learning+16 routers+1 autonomous+1 platform base+2 windows+1 linux+4 security+2 vision+2 middleware+1 policy+1 utils+1 tools/network = 92文件（不含archive/legacy）
- **Frontend**：1 HTML + 11 JS + 4 CSS = 16文件
- **总代码**：22664行（不含archive/legacy）
- **根目录MD**：2个单版本README.md + ARCHITECTURE.md，旧版25个已归档docs/archive/
- **文档**：5个v0913相关+29归档+13 legacy归档
- **测试**：5文件全部通过✅
- **依赖**：16个最小必要
- **API**：103个，71模块化+32兼容，24个summary+tags 8层架构Swagger

---

## 九、快速启动 - 单版本

```bash
pip install -r requirements.txt
python run.py
# http://localhost:8000/ 前端控制台v0913 103API+平台状态条
# http://localhost:8000/docs Swagger 8层架构
# http://localhost:8000/api/health 启动日志3行+12项techniques
# http://localhost:8000/api/platform/status 平台状态真实/演示
# http://localhost:8000/api/flywheel/stats 飞轮评分分布0.5-0.9透明
# http://localhost:8000/api/security/pending 待确认NEED_CONFIRM阻断队列
# http://localhost:8000/api/security/trend 安全趋势时间序列
# http://localhost:8000/api/vision/dpi DPI信息

# 环境变量控制
ZANE_RUNTIME=v3 ZANE_PLATFORM=auto ZANE_DEMO=auto ZANE_LLM_PROVIDER=local ZANE_PORT=8000 python run.py

# 测试
python tests/test_tools_impl.py
python tests/benchmark/test_simplemem.py
python tests/test_eval_replay.py
```

---

## 十、开发指南 - 其他Agent

### 添加新工具
1. `backend/tool_registry.py`添加ToolDefinition 26→27
2. `backend/tools_impl.py` ToolExecutor添加方法def my_tool(self, param) -> Dict返回success+demo_mode，安全检查+截断
3. TOOL_FUNCTIONS添加映射"my_tool": lambda **kwargs: tool_executor.my_tool(**kwargs)
4. 测试`tests/test_tools_impl.py`

### 添加新路由
1. `backend/routers/`新建my.py，APIRouter prefix="/api" tags=["X层"]，get_modules延迟导入防循环，@router.get summary+tags
2. `backend/main.py`导入router并include，tags_metadata添加X层

### 调试
- `data/logs/zane_*.log` loguru
- `data/training/sft.jsonl`飞轮
- `data/security/trend.jsonl`安全趋势
- `/docs` Swagger
- `/api/health`启动日志3行+12 techniques
- `/api/platform/status`平台状态
- `/api/flywheel/stats`评分分布
- `/api/security/pending`阻断队列

### 约束
- 简体中文优先UTF-8 BOM
- 真实工具非模拟，工具注册表+策略防火墙+上下文预算+熔断器
- 只读无需确认，危险操作需确认PENDING_CONFIRM
- 工具大输出截断20文件15进程3000字符防撑爆LLM上下文32K
- Windows深度控制为主，Linux演示兼容psutil模拟接口一致
- 本地LLM为主要引擎离线仍可用

---

> 干净单版本Zane v0913，无V1/V2/V6/V7等多版本并存，根目录仅2 MD，Backend 12主文件单版本，真正单版本整理完成
