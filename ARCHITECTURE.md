# Zane AGI v0913 - 完整架构文档

> **面向其他Agent的开发指南**：扫一遍本文档即可知悉整个项目架构，无需读全部代码
> **版本**：Zane v0913 单版本整合版 | **时间**：2026-09-13 | **目标**：个人AGI管家，对标Operator/Claude Computer Use + Manus/Devin + PowerToys/Raycast

---

## 一、项目一句话

本地Windows电脑助手，理解中文自然语言，操作真实系统，**自主进化**，数据不出本地，越用越懂你。

**核心约束**：
- 简体中文优先，UTF-8 BOM
- 真实工具非模拟，工具注册表+策略防火墙+上下文预算+熔断器
- Windows深度控制为主，iOS远程端口预留
- 本地LLM为主要引擎（Qwen3 30B-A3B MoE 3B激活），云API仅可选教师顾问，离线仍可用

---

## 二、完整文件树 + 作用

### 根目录
```
Zane/
├── backend/main.py                    # 38KB 766行 v0913单版本整合版，FastAPI主服务，103API，8层架构tags，启动日志3行，lifespan生命周期
├── run.py                             # 3.5KB 一键启动器，环境变量控制ZANE_RUNTIME/PLATFORM/DEMO/LLM_PROVIDER/PORT，单版本优先legacy回退，检查依赖+前端+单版本文件
├── requirements.txt                   # 16依赖最小必要：fastapi/uvicorn/psutil/pillow/pydantic/multipart/aiofiles/httpx/filelock/slowapi/APScheduler/jose/loguru/sqlite-vec/rapidocr/datasets
├── LICENSE                            # MIT
├── README_V0913.md                    # 12KB 精简版单版本103API 8层架构
├── README.md                          # 56KB 旧版v7.0详细文档（待精简）
├── ARCHITECTURE.md                    # 本文，面向其他Agent的架构指南
├── docs/                              # 文档目录
│   ├── FLYWHEEL_SPEC.md               # 7.3KB 飞轮评分规格透明文档，维度权重+代码示例+分布+淘汰规则
│   ├── ZANE_V0913_CHANGELOG.md        # 12KB v0913变更日志6缺点+12优先级
│   ├── REVIEW_DEBUG_REPORT.md         # 14KB Review报告
│   ├── FINAL_REVIEW.md                # 14KB 最终审查报告
│   └── FINAL_REVIEW.md                # 同上
├── .github/workflows/test.yml         # 1.8KB CI，Python 3.10/11/12，依赖+语法+工具测试+Benchmark+回放评估
├── config/                            # 配置目录
│   ├── model_paths.json               # 1.6KB 模型路径优先级说明，非硬编码，GGUF 9候选+HF 8候选
│   └── evolution_schedule.json        # 313B 调度配置凌晨2点+每30分
├── data/                              # 数据目录（gitignore排除大部分json）
│   ├── training/                      # 训练数据（保留）
│   │   ├── sft.jsonl                  # 自动收集过滤后的SFT数据
│   │   ├── replay_buffer.jsonl        # Replay高质量>0.8防遗忘30%
│   │   └── stats.json                 # 统计
│   ├── prompts/                       # Prompt版本（保留）
│   │   ├── prompt_v1.json ~ v4.json   # 4版本，最佳0.795，Darwin+EvolveR
│   ├── skill_genes/                   # 技能基因（保留）
│   │   └── *.json                     # 技能基因变异交叉
│   ├── logs/                          # 日志轮转10MB 7天
│   ├── screenshots/                   # 截图
│   ├── security/                      # 安全趋势trend.jsonl
│   ├── memory/                        # 记忆
│   ├── skills/                        # 技能
│   ├── simple_mem.json                # SimpleMem
│   └── ...                            # 其他json被gitignore排除
├── tests/                             # 测试目录
│   ├── __init__.py
│   ├── test_tools_impl.py             # 5.7KB 工具统一27工具无覆盖+防火墙阻断PENDING_CONFIRM
│   ├── test_eval_replay.py            # 5.7KB 回放评估50条成功率曲线+晋升判断
│   ├── eval_tasks.jsonl               # 9.5KB 50条日常任务5分类file/system/window/security/network 3难度
│   └── benchmark/
│       ├── test_simplemem.py          # 13KB SimpleMem Benchmark可复现8条中文
│       └── simplemem_benchmark_result.json # 结果
└── frontend/                          # 前端
    ├── index.html                     # 29KB v0913主页面，23视图，ES Modules
    ├── index_v7.html                  # 21KB v7.0备份
    ├── css/                           # 4文件拆分
    │   ├── styles.css                 # 11KB 主样式深色主题CSS变量
    │   ├── components.css             # 1.8KB 组件
    │   ├── layout.css                 # 1.9KB 布局
    │   └── themes.css                 # 882B 主题
    └── js/                            # 11文件 ES Modules 8模块
        ├── app.js                     # 25KB 主逻辑，switchView+send+load*，30秒轮询自适应15秒+hidden暂停，导入platform_status
        ├── platform_status.js         # 11KB 新增v0913，平台状态条Provider/真实/演示/不可用工具+demo_mode视觉区分，injectStyles+loadStatus+render
        ├── evolution.js               # 25KB 554行，进化仪表盘SSE+图表+基因树，训练统计+日志流+版本历史+资源状态
        ├── api.js                     # 2.6KB API封装apiGet/apiPost+tokenApi+databaseApi+autonomousApi+systemApi+modelsApi
        ├── charts.js                  # 5.0KB Canvas交互式图表drawInteractiveCpuChart/drawInteractiveMemoryChart
        ├── models.js                  # 8.4KB 模型管理双轨GGUF+HF+VRAM检测
        ├── system.js                  # 3.5KB 系统状态
        ├── autonomous.js              # 4.5KB 自主优化
        ├── database.js                # 3.8KB 数据库
        ├── tokens.js                  # 3.6KB Token管理
        └── chat.js                    # 1.1KB 聊天
```

### 后端详细

```
backend/
├── __init__.py
├── main.py                            # 38KB 主服务，见根目录说明
├── tool_registry.py                   # 14KB 26工具注册表v0913整合版，修复不一致，PermissionLevel READ_ONLY/WRITE/DANGEROUS/SYSTEM，ToolCategory 9分类，ToolDefinition严格Schema中文描述，get_tools_for_llm转OpenAI格式
├── tools_impl.py                      # 33KB 统一工具实现，ToolExecutor单例，demo_mode+platform_provider，_resolve_demo_path统一Windows→Linux演示映射，_ensure_demo_files演示文件，_format_size，_context_budget_truncate截断20文件15进程，6节文件/进程/窗口/视觉/应用网络/剪贴板鼠标键盘，21+9工具TOOL_FUNCTIONS，安全增强白名单+注入防护+沙盒+回收站+10MB+demo_mode字段
├── tool_contract.py                   # 工具契约23个，风险分级high/medium/low，side_effect，category，is_real
├── tool_contract_complete.py          # 契约补全
├── policy_firewall.py                 # 4.9KB 旧版防火墙，NEED_CONFIRM仅日志
├── policy_firewall_v0913.py           # 13KB 328行硬化版，PolicyAction ALLOW/NEED_CONFIRM/DENY/PENDING_CONFIRM，PolicyRule+PendingConfirm+AuditLog，PolicyFirewallV0913待确认队列+Event+超时5分钟自动拒绝+前端确认+审计，get_pending_confirms+confirm_operation+wait_for_confirm+clear_expired，解决缺点六
├── agent_runtime.py                   # 16KB 旧版已归档
├── agent_runtime_v2.py                # 16KB v2 Harness DAG+思考+并行+验证
├── agent_runtime_v3.py                # 27KB v3 思考预算+有界校正+SimpleMem+memory_v3，execute_task
├── llm_client.py                      # LLM客户端，离线可用，OpenAI兼容本地API如llama.cpp，云API可选教师顾问
├── llm/
│   ├── model_manager.py               # 模型管理，支持MODEL_PATH环境变量
│   └── model_manager_v2.py            # v2
├── database.py                        # SQLite唯一WAL 8表，filelock并发安全，习惯学习add_habit
├── model_registry.py                  # 模型注册，GGUF+HF双轨
├── token_manager.py                   # Token管理可替换
├── task_trace.py                      # 任务轨迹
├── autonomous_optimizer.py            # 自主优化器，20 Skill+APScheduler
├── legacy/                            # 13文件历史归档
│   ├── main_v2.py/v3.py/v4.py/v6.py/v7.py/v8.py # 20KB~79KB 历史主服务
│   ├── agent_runtime.py/v2.py/v3.py   # 16KB~27KB 历史Runtime
│   ├── memory_layer.py                # 14KB 旧记忆层
│   ├── tool_registry_old.py           # 18KB 旧注册表
│   └── tools_impl_old.py/complete.py  # 24KB/949B 旧工具实现
├── platform/                          # 平台层
│   ├── base.py                        # 抽象接口get_platform_provider
│   ├── windows/
│   │   ├── wmi_provider.py            # WMI真实CPU每核心+内存条+磁盘+启动项+服务，Windows官方任务管理器也用
│   │   └── win32_window.py            # Win32真实HWND Z序DPI置顶缩略图，EnumWindows+GetWindowRect+SetForegroundWindow
│   └── linux/
│       └── fallback.py                # Linux演示psutil模拟接口一致，演示环境
├── security/                          # 安全层
│   ├── sandbox.py                     # 文件+进程沙盒，realpath+白名单+filelock+回收站，sandbox_root D:\ZaneSandbox\，allowed_roots Downloads等，safe_delete移到回收站，critical进程csrss.exe等禁止结束，10MB限制
│   ├── cybersec_tools.py              # 漏洞扫描，明文密码文件password.txt+高危端口22/3389/445/135+启动项+弱权限stat.S_IWOTH
│   ├── cybersec_trend.py              # 8.8KB 新增v0913，安全趋势时间序列，SecuritySnapshot时间戳+开放端口+启动项+弱权限+明文密码+风险分数+问题数，CyberSecTrend add_snapshot+detect_anomalies new_ports/closed_ports/new_startup/risk_spike/plaintext_passwords+get_trend按天聚合+get_stats统计端口启动项频率，接入飞轮
│   ├── linux_provider.py              # WSL沙盒，wsl --list列发行版，wsl -d distro -- bash -c command执行，危险命令.. rm -rf / :(){:|:&};:拦截，超时10秒
│   └── fix_tools_impl.py              # 临时修复脚本已清理
├── memory/                            # 记忆层
│   ├── data_flywheel_v3.py            # 14KB 341行 v3飞轮，过滤评分去重安全，collect_from_success任务→sample conversations+tools+verification+exec_time+task_type，data_filter.is_safe危险0，SHA256去重+相似度>0.9，score_importance工具链0.3+验证0.3+时间0.2+类型0.2=1.0总分0.5-0.9，SimpleMem30%高质量>0.8 Replay，保存sft.jsonl+dpo.jsonl+replay_buffer.jsonl+stats.json
│   ├── data_flywheel.py               # 7.8KB 旧飞轮
│   ├── memory_v3.py                   # 8.4KB 241行 v3 4层统一+SimpleMem+遗忘，conversational会话200条压缩100字意图+实体，episodic情景任务历史150字任务+结果+工具，semantic语义习惯事实80字，procedural程序可复用流程120字步骤，add_memory+get_stats+forget低价值访问<3重要性<0.3 30天
│   ├── simple_mem.py                  # 7.6KB 208行 SimpleMem 2026最新，MemoryItem id/type/content/compressed/importance/access_count/created_at/last_accessed/tags/embedding，SimpleMem compression_ratio 0.3目标，semantic_compression按类型固定长度100/150/80/120+...压缩标记，online_synthesis新记忆+相关记忆→抽象原则，intent_aware_retrieval意图感知file操作procedural 0.4 system semantic 0.4 organize procedural 0.5+时间衰减，add_memory自动压缩+合成，get_stats统计压缩率Token减少，论文+26.4% F1 30x减少为目标值实际实现固定长度
│   ├── forgetting.py                  # 1.9KB 遗忘机制，4层遗忘曲线conversational 7天episodic 30天semantic 90天procedural 180天，低价值访问<3重要性<0.3超期遗忘，高价值访问>10重要性>0.8保留，DREAMS.md人类可读日记
│   ├── vector_memory.py               # 旧向量
│   └── vector_memory_real.py          # 6.0KB 真实向量sqlite-vec+sentence-transformers 384维，关键词回退
├── learning/                          # 进化层
│   ├── model_resolver.py              # 8.9KB 模型解析双轨，check_vram torch.cuda或pynvml，resolve VRAM>=24GB→30B-A3B GGUF D:\llama.cpp\...gguf+HF Qwen/Qwen3-30B-A3B，>=16GB→7B，<12GB技能蒸馏不训练，路径环境变量MODEL_PATH/HF_MODEL_PATH>config/model_paths.json含hf_model_path>自动探测GGUF 9候选+HF 8候选>占位，GGUF推理llama.cpp OpenAI兼容，HF训练transformers+unsloth
│   ├── unsloth_trainer_v3.py          # 14KB 真实训练循环，generate_training_script生成训练脚本FastLanguageModel.from_pretrained model_name Qwen/Qwen3-30B-A3B max_seq_length 4096 load_in_4bit True，get_peft_model r=32 alpha=64 dropout 0.05 target_modules q/k/v/o/gate/up/down_proj，datasets load_dataset json，trl SFTTrainer，start_training非阻塞subprocess.Popen+日志流data/logs/training_*.log+LoRA版本models/versions/lora_*+指数退避重试3次
│   ├── unsloth_trainer.py             # 旧训练
│   ├── replay_buffer.py               # Replay Buffer 30%防遗忘，build ratio 0.3 min_quality 0.8高质量，replay_count新样本30%旧数据，get_replay_samples
│   ├── prompt_evolution.py            # Prompt进化Darwin Gödel Machine变异交叉选择+EvolveR离线蒸馏，evolve num_mutations 3 num_crossovers 2，mutate_random_sentence变异，crossover重组，score_prompt成功率+工具准确率+验证通过率，list_prompts 4版本最佳0.795
│   ├── strategy_evolution.py          # 策略进化AlphaEvolve最优工具链搜索，evolve_workflow task_type file_organize，generate_tool_chain_candidates，evaluate_chain
│   ├── evolution_engine.py            # 旧进化
│   ├── evolution_engine_v25.py        # v2.5 7技术
│   └── self_correction.py             # 自校正
├── runtime/                           # 运行时
│   ├── data_filter.py                 # 11KB 290行 安全过滤，DANGEROUS_PATHS 11个C:\Windows\System32 /etc/shadow等，DANGEROUS_FILES 8个，DANGEROUS_PROCESSES 7个，DANGEROUS_COMMANDS 6个rm -rf / :(){:|:&};:，修复转义bug content_combined.replace("\\\\","\\")双重匹配，is_safe危险路径+写入操作→False，核心路径只读也过滤，score_importance工具链复杂度+验证+时间+类型0.5-0.9，验证删除System32+delete_file→False✅整理下载+list/create→True 0.75✅ security 60%→100%
│   ├── thinking_budget.py             # 5.9KB 161行 思考预算Qwen3 2026 /think 32K /no_think 8K，estimate_complexity复杂关键词14个分析/推理/规划等+简单词7个列出/查看+长度，build_chat_template /think复杂推理温度0.6 top_p0.95 max_tokens32768 /no_think快速0.7 0.8 8192 auto动态0.65，动态分配推理资源
│   ├── ralph_loop.py                  # 14KB 329行 Ralph Loop bash while全新上下文+三护栏，prd.json id/title/acceptance/passes布尔，check_guardrails机器可验证退出passes布尔+acceptance非空+硬预算max10+token100K+验证门独立，run_loop全新上下文每次文件状态防污染
│   ├── bounded_correction.py          # 14KB 362行 有界自校正UCSL，Layer A可观测性raw_confidence+calibrated_confidence+uncertainty_source+outcome_label，Layer B有界修正read_only 2轮2000 tokens低风险write 2轮4000中风险dangerous/complex 3轮8000-10000高风险，弱点检测过短/含错误/不确定/未找到→约束生成针对性再生
│   ├── skill_gene.py                  # 9.1KB 267行 技能基因变异交叉选择fitness>0.7保留<0.3遗忘，SkillGene id/name/tools/params/fitness/parents/mutation_type，mutate随机替换工具/参数，crossover重组，evolve变异交叉，evolution_tree基因树，复合改进技能调用技能
│   ├── resource_monitor.py            # 7.4KB 170行 资源监控5维度可训练判断，get_all cpu psutil.cpu_percent+memory virtual_memory+VRAM torch.cuda+power sensors_battery Windows GetSystemPowerStatus+game全屏+进程名匹配+iOS frontend上报viewing，can_train idle+VRAM+power+not_busy+not_ios，can_train_reason
│   ├── dream_loop.py                  # 6.0KB 206行 梦境循环3阶段，dream_generation记忆重放+噪声变体+技能组合新任务+反事实推理如果当初不同，evolve_dreams评估价值0.3-0.9>0.6生成新原则Q-Evolve in-distribution critic，consolidate_memories原则固化到语义记忆
│   ├── dreaming.py                    # 14KB 324行 旧梦境
│   ├── skill_library.py               # 7.1KB 207行 技能库SAGE Sequential Rollout
│   ├── intent_parser.py               # 6.5KB 166行 意图解析，category file/system/window/security/network，action organize/monitor等
│   ├── planner.py                     # 5.5KB 147行 DAG规划，TaskNode id/title/tool/params/dependencies，decompose_to_dag意图→DAG，并行只读+串行写入+验证，失败重试单节点
│   ├── state_manager.py               # 5.5KB 161行 状态管理，真实系统状态
│   ├── tool_executor.py               # 6.5KB 161行 工具执行，并行只读+串行写入+验证+熔断5次+撤销栈
│   ├── memory_manager.py              # 4.8KB 131行 记忆管理
│   ├── skill_manager.py               # 5.7KB 149行 技能管理
│   ├── model_interface.py             # 7.1KB 159行 模型接口
│   ├── trace_logger.py                # 6.0KB 190行 轨迹日志，SQLite唯一filelock
│   ├── verifier.py                    # 5.9KB 154行 验证，写后重新感知验证是否成功
│   ├── policy_engine.py               # 6.7KB 164行 策略引擎，protected_paths critical_processes auto_allow denied
│   ├── recovery_manager.py            # 4.1KB 109行 恢复，错误分类重试NotFound/PermissionDenied/Transient/Permanent
│   └── __init__.py
├── autonomous/
│   ├── scheduler_v3.py                # 7.7KB 调度器v3，APScheduler凌晨2点+每30分空闲+3点梦境+资源感知，check_ready资源感知5维度can_train判断，train_job准备数据SFT 50条+Replay 30%+训练+评估+晋升>2%切换LoRA旧版本保留可回滚
│   └── ...
├── benchmark/
│   ├── evolution_eval.py              # 评估Harness 20任务5分类file 5/system 5/window 5/security 5/network 5真实回放，evaluate旧模型vs新模型by_category，should_promote阈值2%平衡激进保守，security 60%→100%修复后，总计20/20 100%
│   └── suite.py                       # 基准套件
├── vision/
│   ├── dpi_ocr_unified.py             # 8.8KB 242行 新增v0913，DPI坐标系统一+OCR，DPIOCRUUnified init_dpi检测Windows DPI 96缩放1.0 125% 1.25，unify_coordinates任意DPI转逻辑，to_physical逻辑转物理，get_dpi_info，ocr_with_dpi统一流程DPI统一→OCR识别→UIA树，_ocr_recognize RapidOCR 50MB+Tesseract回退，_uia_tree Windows UIA uiautomation，解决优先级11
│   └── ocr_real.py                    # 真实OCR rapidocr 50MB轻量替代PaddleOCR 500MB
├── tools/
│   └── network/
│       └── web_search_real.py         # 真实搜索Bing API+本地回退
├── middleware/
│   ├── jwt_auth.py                    # JWT认证HS256 7天商业级
│   └── security.py                    # 限流认证slowapi 60/分
├── policy/
│   └── undo_stack.py                  # 撤销栈，push operation+params+reverse_params+description，undo弹出逆操作，事务化+可回滚
├── utils/
│   └── cleanup.py                     # 清理截图50张+备份10个30天+轨迹100条，定时凌晨3点
└── routers/                           # 16文件71模块化+32兼容=103API
    ├── __init__.py
    ├── evolution_v3.py                # 407行18路由，get_modules延迟导入防循环，vram VRAM检测+双轨推荐+get_all，resources资源监控5维度，filter/stats过滤统计+importance_distribution透明，filter/test安全测试GET+POST双模式修复System32拦截，training/start真实训练非阻塞+日志流+LoRA版本，training/status，training/stop，evaluate 20任务Harness+Replay30%+2%晋升，replay Replay Buffer，prompts Prompt版本Darwin 4版本最佳0.795，prompts/evolve变异交叉，strategies AlphaEvolve最优工具链，scheduler调度器状态，stream SSE流训练进度，status，start，data
    ├── thinking_v25.py                # 158行6路由，thinking/budget思考预算复杂度评估三档采样，ralph/run Ralph Loop bash while全新上下文prc.json passes布尔三护栏，ralph/status，correction/bounded有界自校正UCSL不确定度+3轮预算，correction/stats，skills/library SAGE技能库
    ├── memory_v3.py                   # 222行12路由，memory/v3 4层统一+SimpleMem+遗忘，memory/v3/forget遗忘低价值，memory/v3/search，memory/simple SimpleMem压缩，memory/simple/add，memory/simple/search意图感知，skills/gene技能基因树，skills/gene/evolve变异交叉，dream/cycle梦境循环3阶段，dream/status
    ├── security_v3.py                 # 208行8路由，security/sandbox/check沙盒realpath白名单，security/scan漏洞扫描+接入趋势add_snapshot，security/trend时间序列端口/启动项异常感知新增，security/anomalies异常检测新增，security/wsl WSL列表，security/wsl/exec WSL沙盒执行，contracts契约23风险分级，policy策略权限分级+保护路径+硬化版v0913待确认队列+审计
    ├── vision_v3.py                   # 274行8路由，vision/ocr OCR识别DPI统一+RapidOCR/Tesseract+UIA树，vision/ocr GET，vision/dpi DPI信息125%/150%检测新增，utils/cleanup清理截图备份轨迹，search/real真实搜索Bing+本地回退，search/real GET，dreaming/run-all梦境运行3阶段，dreaming/status
    ├── runtime_v3.py                  # 340行10路由，tools工具26个，tools/call工具调用策略+验证+撤销，memory记忆，skills技能，traces轨迹，runtime/intent/parse意图解析，runtime/state/observe状态观测真实，runtime/plan DAG规划，runtime/tool/exec工具执行，runtime/verifier验证
    ├── auth_v3.py                     # 83行3路由，auth/login JWT 7天，auth/check，auth/logout
    ├── benchmark_v3.py                # 76行3路由，benchmark基准20任务，benchmark/run-all运行，benchmark/eval评估Harness
    ├── vector_v3.py                   # 104行2路由，memory/vector/search真实向量+关键词回退384维，memory/vector/add
    ├── config_v3.py                   # 160行4路由，config配置中心，settings/save真实落盘config/，model_paths，evolution_schedule
    ├── system_router.py               # 122行系统路由，state系统状态，cpuHistory 30条，memoryHistory，processes进程，windows窗口，files文件
    ├── database_router.py             # 61行数据库路由，stats统计，techStack技术栈，habits习惯学习，backup备份
    ├── autonomous_router.py           # 83行自主路由，status空闲+调度，candidateSkills 20候选Skill+资源感知，run运行自主任务
    ├── models_router.py               # 111行模型路由，list模型列表GGUF+HF双轨，add添加模型A，active激活，scan扫描
    └── tokens_router.py               # 42行Token路由，list Token可替换，set设置
```

---

## 三、核心流程图

### 启动流程
```
run.py
→ 读取环境变量ZANE_RUNTIME/PLATFORM/DEMO/LLM_PROVIDER/PORT
→ 检查核心依赖fastapi uvicorn psutil + 可选loguru slowapi rapidocr sqlite-vec filelock
→ 检查前端index.html + 单版本文件main.py/tools_impl.py/policy_firewall_v0913.py + legacy 13文件
→ 打印启动信息前端/docs/health/platform/flywheel/pending
→ 尝试启动优先级backend.main v0913 → legacy.main_v8 → v7 → v6
→ main.py lifespan
  → get_startup_info() 3行日志
    1. Runtime v2/v3 env ZANE_RUNTIME v3可用/回退v2
    2. Platform Provider Windows真实/psutil演示 env ZANE_PLATFORM/DEMO 系统:linux
    3. 工具 0真实 26演示 env ZANE_LLM_PROVIDER 演示工具列表
  → 启动调度器v3凌晨2点+每30分+资源感知
  → 检查sqlite-vec/rapidocr/JWT
  → 检查防火墙v0913硬化版
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
  → agent_runtime_v3.execute_task (RUNTIME_VERSION=v3) 或回退v2
    → intent_parser意图解析category file/system/window/security/network action organize/monitor
    → state_manager状态观测真实系统
    → memory_v3+simple_mem意图感知检索file procedural 0.4 system semantic 0.4
    → skill_manager技能匹配
    → planner DAG分解TaskNode id/title/tool/params/dependencies，并行只读+串行写入
    → tool_executor执行
      → policy_firewall_v0913.check_permission
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
  → data_flywheel_v3.collect_from_success任务→sample conversations+tools+verification+exec_time+task_type → data_filter.is_safe危险0+SHA256去重+相似度>0.9+score_importance 0.5-0.9 → 保存sft.jsonl+replay_buffer 30%高质量>0.8
  → database.add_habit习惯学习
  → simple_mem.add_memory conversational + memory_v3.add_memory
→ 返回{final_report, steps, tools_used, observed_state, verification, exec_time_ms, thinking_budget, correction}
→ 前端chat-messages显示assistant消息
```

### 自主进化流程8阶段
```
触发：APScheduler凌晨2点cron + 每30分空闲interval + 手动POST /api/evolution/start
→ scheduler_v3.check_ready资源感知5维度CPU<20%内存<70%+VRAM>=18GB+插电或电量>=50%+非游戏会议全屏+iOS未查看 → can_train bool+reason
→ 1.收集：data_flywheel_v3已收集sft.jsonl
→ 2.过滤：data_filter.is_safe 11路径8文件7进程6命令危险0 + SHA256去重 + 相似度>0.9 + importance 0.5-0.9评分 + SimpleMem30% Replay高质量>0.8
→ 3.解析：model_resolver.check_vram torch.cuda + resolve双轨GGUF推理+HF训练+自适应24GB→30B 16GB→7B <12GB蒸馏
→ 4.训练：unsloth_trainer_v3.generate_training_script FastLanguageModel QLoRA r=32 alpha=64 + start_training非阻塞Popen+日志流training_*.log+LoRA版本models/versions/lora_*+指数退避重试3次
→ 5.Replay：replay_buffer.build ratio 0.3 min_quality 0.8新样本30%旧数据防遗忘
→ 6.评估：evolution_eval.evaluate 20任务5分类file/system/window/security/network真实回放 + evaluate_with_replay旧vs新+by_category + should_promote阈值2%平衡激进保守总体提升>2%且security不下降
→ 7.进化：prompt_evolution.evolve Darwin变异交叉选择+EvolveR离线蒸馏 4版本最佳0.795 + skill_gene.evolve变异交叉fitness>0.7保留<0.3遗忘复合改进 + strategy_evolution.evolve_workflow AlphaEvolve最优工具链
→ 8.晋升：切换到新LoRA旧版本保留可回滚 + memory_v3遗忘低价值访问<3重要性<0.3 30天 + DREAMS.md人类可读日记 + dream_loop 3阶段Dream+Evolve+Consolidate
→ 前端evolution.js SSE流推送训练进度+图表+基因树
```

### 安全流程
```
工具调用→policy_firewall_v0913.check_permission→保护路径10个→自动放行10个只读→权限分级→PENDING_CONFIRM+confirm_id→pending_confirms+Event→日志🛡️阻断→返回→执行器wait_for_confirm等待→前端pending轮询→confirm确认→Event触发继续→审计日志blocked=True→clear_expired清理过期超时拒绝
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
- GET /api/security/scan 漏洞扫描+接入趋势
- GET /api/security/trend 安全趋势时间序列
- GET /api/security/anomalies 安全异常端口/启动项变化
- GET /api/security/wsl WSL列表
- POST /api/security/wsl/exec WSL沙盒执行
- GET /api/security/pending 待确认NEED_CONFIRM阻断队列
- POST /api/security/confirm 确认操作
- GET /api/contracts 契约23风险分级
- GET /api/policy 策略权限分级+保护路径+硬化版v0913
- GET /api/security/sandbox/check

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

**额外实现4个可选**：wsl_exec/wsl_list/web_search_real/mouse_move等

---

## 六、记忆与进化

### SimpleMem
- 4层：conversational 100字意图+实体，episodic 150字任务+结果+工具，semantic 80字习惯事实，procedural 120字步骤
- 压缩：论文目标30%+26.4%F1+3x Token，实际实现固定长度100/150/80/120平均75%压缩1.4x信息保留85%可复现Benchmark
- 合成：新记忆+相关记忆→抽象原则
- 检索：意图感知file procedural 0.4 system semantic 0.4 organize procedural 0.5+时间衰减30天

### 记忆v3 4层统一
- conversational/episodic/semantic/procedural统一，SimpleMem压缩，遗忘低价值访问<3重要性<0.3 30天，DREAMS.md人类可读日记

### 数据飞轮v3
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
- 50条回放评估tests/eval_tasks.jsonl 5分类3难度成功率82%历史曲线v6 75%→v7 85%→v8 90%→v0913 82%
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

## 七、安全

### 沙盒
- 文件realpath+白名单+filelock+回收站+10MB限制，sandbox_root D:\ZaneSandbox\，allowed_roots Downloads等，safe_delete移到回收站
- 进程critical csrss.exe winlogon.exe services.exe lsass.exe等7个禁止结束
- 大小10MB

### 防火墙v0913硬化
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

## 八、前端

### v0913 29KB
- 原生HTML/CSS/JS ES Modules 8模块，Canvas交互式图表，CSS变量深色主题4文件，skeleton loading+aria

### 平台状态条
- platform_status.js 11KB，顶部显示Provider/真实/演示/Runtime/LLM/环境变量+工具真实/演示计数+不可用工具，body.demo-mode黄条+工具卡片demo/real标签视觉区分，30秒刷新+自适应15秒+hidden暂停

### 视图23个
- 控制台、进化仪表盘、模型双轨、Token、自主优化、数据库、轨迹、基准20任务、系统+资源5维度、进程、窗口、文件沙盒、记忆4层v3、技能基因、梦境3阶段、安全过滤100%、契约23、思考预算、设置

---

## 九、测试

- test_tools_impl.py工具统一+防火墙阻断✅
- benchmark/test_simplemem.py Benchmark可复现8条中文✅
- test_eval_replay.py回放评估50条成功率82%+晋升判断✅
- eval_tasks.jsonl 50条5分类3难度
- CI .github/workflows/test.yml Python 3.10/11/12

---

## 十、快速启动

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

# 启动
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

## 十一、开发指南 - 其他Agent

### 添加新工具
1. `backend/tool_registry.py`添加ToolDefinition，name/display_name/description/category/permission/parameters_schema/returns_schema/need_confirmation/is_real_action/examples
2. `backend/tools_impl.py` ToolExecutor类添加方法def my_tool(self, param) -> Dict，返回success+demo_mode+其他，安全检查+上下文预算截断
3. TOOL_FUNCTIONS添加映射"my_tool": lambda **kwargs: tool_executor.my_tool(**kwargs)
4. 测试`tests/test_tools_impl.py`添加验证
5. 前端如需，`frontend/js/`添加视图

### 添加新路由
1. `backend/routers/`新建my_v3.py，APIRouter prefix="/api" tags=["X层"]，get_modules延迟导入防循环，@router.get summary+tags
2. `backend/main.py`导入router并app.include_router，tags_metadata添加X层
3. 测试

### 添加新记忆类型
1. `backend/memory/memory_v3.py`添加类型和压缩长度
2. `backend/memory/simple_mem.py` semantic_compression添加分支
3. 测试

### 调试
- 查看`data/logs/zane_*.log` loguru轮转
- 查看`data/training/sft.jsonl`飞轮收集
- 查看`data/security/trend.jsonl`安全趋势
- 前端控制台F12
- API `/docs` Swagger
- 健康检查`/api/health`启动日志3行+techniques
- 平台状态`/api/platform/status`真实/演示
- 飞轮统计`/api/flywheel/stats`评分分布
- 待确认`/api/security/pending`阻断队列

### 注意事项
- 简体中文优先，UTF-8 BOM
- 真实工具非模拟，工具注册表+策略防火墙+上下文预算+熔断器
- 只读无需确认，危险操作需确认PENDING_CONFIRM
- 工具大输出截断20文件15进程3000字符防撑爆LLM上下文32K
- 安装依赖前验证环境避免混淆虚拟环境
- 代码维护现实，AI解释现实
- Windows深度控制为主，Linux演示兼容psutil模拟接口一致
- 本地LLM为主要引擎，云API仅可选教师顾问，离线仍可用
- 演示数据任务记忆技能日志系统状态全部中文

---

## 十二、文件树作用速查表

| 路径 | 大小 | 作用 |
|---|---|---|
| backend/main.py | 38KB | 主服务单版本整合103API 8层架构启动日志3行 |
| backend/tools_impl.py | 33KB | 统一工具实现26+30工具真实/演示兼容安全增强demo_mode |
| backend/tool_registry.py | 14KB | 工具注册表26工具严格Schema中文 |
| backend/policy_firewall_v0913.py | 13KB | 硬化版防火墙NEED_CONFIRM阻断等待确认 |
| backend/agent_runtime_v3.py | 27KB | Runtime v3思考预算+有界校正+SimpleMem |
| backend/agent_runtime_v2.py | 16KB | Runtime v2 DAG+思考+并行+验证 |
| backend/memory/data_flywheel_v3.py | 14KB | 飞轮v3过滤评分去重安全 |
| backend/memory/memory_v3.py | 8.4KB | 记忆v3 4层统一+SimpleMem+遗忘 |
| backend/memory/simple_mem.py | 7.6KB | SimpleMem压缩固定长度实现 |
| backend/runtime/data_filter.py | 11KB | 安全过滤11路径8文件7进程6命令100% |
| backend/runtime/thinking_budget.py | 5.9KB | 思考预算Qwen3 /think 32K /no_think 8K |
| backend/runtime/ralph_loop.py | 14KB | Ralph Loop bash while全新上下文三护栏 |
| backend/runtime/bounded_correction.py | 14KB | 有界自校正UCSL不确定度+3轮预算 |
| backend/runtime/skill_gene.py | 9.1KB | 技能基因变异交叉fitness>0.7保留 |
| backend/runtime/resource_monitor.py | 7.4KB | 资源监控5维度可训练判断 |
| backend/security/cybersec_trend.py | 8.8KB | 安全趋势时间序列端口/启动项异常感知 |
| backend/vision/dpi_ocr_unified.py | 8.8KB | DPI统一+OCR+UIA树 |
| backend/routers/evolution_v3.py | 407行 | 进化18路由VRAM/资源/过滤/训练/评估/Replay |
| backend/routers/security_v3.py | 208行 | 安全8路由沙盒/扫描/趋势/异常/WSL/契约/策略 |
| backend/routers/vision_v3.py | 274行 | 视觉8路由OCR/DPI/清理/搜索/梦境 |
| frontend/js/platform_status.js | 11KB | 平台状态条Provider真实/演示+demo_mode视觉区分 |
| frontend/js/app.js | 25KB | 主逻辑switchView+send+30秒轮询 |
| frontend/js/evolution.js | 25KB | 进化仪表盘SSE+图表+基因树 |
| docs/FLYWHEEL_SPEC.md | 7.3KB | 飞轮评分规格透明文档 |
| tests/eval_tasks.jsonl | 9.5KB | 50条回放评估任务 |
| run.py | 3.5KB | 一键启动器环境变量控制单版本优先 |
| requirements.txt | 16依赖 | 最小必要依赖 |
| LICENSE | MIT | MIT许可证 |

---

## 十三、版本历史

- v0913 2026-09-13 单版本整合版6缺点全修+12优先级+Review Debug，单版本+103API+8层架构+启动日志3行+平台状态条+安全硬化+飞轮透明+Benchmark+回放评估50条+趋势+DPI统一+LICENSE+CI
- v8.0 422行目标500行+71路由模块化10路由文件+103总路由+前端进化仪表盘SSE图表基因树+配置中心
- v7.0 931行6核心+6路由模块化51路由+94总路由，模块化重构-49%单文件
- v6.0 79KB 43路由自主进化完整版8阶段A-H闭环，数据飞轮v3+模型双轨+真实训练+评估Harness
- v5.0 2026进化循环版思考预算+Ralph+有界校正+技能库+SimpleMem+梦境循环
- v2.4 商业级设置+完整README 14层→8层
- v2.3 集成版JWT+真实向量+OCR+交互图表
- v2.2 检修修复版26API全通+模型A真实+UI优化

---

## 十四、许可证

MIT

> 代码维护现实，AI解释现实 | 数据不出本地，越用越懂你 | 单版本整合+103API+8层架构+6缺点全修+Review Debug
