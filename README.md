# Zane AGI v0913 - 单版本整合版

> **运行在你PC上的私有助手，数据不出本地，越用越懂你**
> 
> **版本**：Zane v0913 单版本整合版 单版本+103API+8层架构+6缺点全修 | **平台**：Windows 10/11 (Linux兼容演示)
> 
> **模型**：`D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf` Qwen3 30B-A3B MoE 3B激活

## 1. 是什么

本地Windows电脑助手，理解中文自然语言，操作真实系统，**自主进化**。

**能做**：
- 看系统：CPU每核心、内存、磁盘、进程树、HWND窗口Z序DPI、资源5维度可训练判断
- 管文件：列出/读取/写入/删除/移动，真实文件系统，沙盒+回收站可撤销+验证+10MB限制
- 控窗口：枚举/聚焦/详情，真实HWND，DPI统一
- 视觉：截图真实PIL、OCR 50MB rapidocr、UI分析UIA树，DPI坐标系统一
- 输入：鼠标点击/移动、键盘输入，DPI统一
- 剪贴板：读取/写入
- 网络：搜索、信息验证
- 安全：漏洞扫描明文密码+高危端口+启动项、历史趋势时间序列异常感知、沙盒realpath白名单、策略防火墙NEED_CONFIRM阻断
- 记忆：4层统一+SimpleMem压缩+遗忘+DREAMS.md
- 进化：数据飞轮自动收集→过滤去重安全→评分0.5-0.9透明→训练→评估50条→晋升

**不能做**：
- 不联网上传数据，SQLite唯一
- 不直接执行任意代码，工具受控类型化接口，严格JSON Schema

## 2. 8层架构

| 层 | 名称 | 职责 | 实现 |
|---|---|---|---|
| 1 | 接入层 | 健康、聊天、Agent执行、前端 | `main.py` 6路由+前端 |
| 2 | 思考层 | 思考预算/think/no_think、Ralph Loop、有界自校正 | `thinking_budget.py` `ralph_loop.py` `bounded_correction.py` |
| 3 | 执行层 | 工具26个、记忆、技能、轨迹、DAG | `tools_impl.py` `planner.py` |
| 4 | 记忆层 | SimpleMem压缩、梦境3阶段、记忆v3 4层、技能基因 | `simple_mem.py` `memory_v3.py` `skill_gene.py` |
| 5 | 进化层 | 飞轮v3过滤评分、模型双轨、训练、评估50条、Replay、Prompt进化 | `data_flywheel_v3.py` `model_resolver.py` `unsloth_trainer_v3.py` `evolution_eval.py` |
| 6 | 平台层 | Windows真实/psutil演示、demo_mode视觉区分 | `tools_impl.py` `platform/` `platform_status.js` |
| 7 | 安全层 | 沙盒+防火墙NEED_CONFIRM阻断+过滤100%+趋势+契约 | `sandbox.py` `policy_firewall_v0913.py` `cybersec_trend.py` `data_filter.py` |
| 8 | 可观测层 | 系统资源5维度、Benchmark、Vector、Config、Auth、DPI+OCR统一 | `resource_monitor.py` `dpi_ocr_unified.py` `system_router.py` |

**技术栈**：FastAPI+SlowAPI限流60/分+JWT+loguru日志+SQLite WAL+filelock+psutil+RapidOCR 50MB+sqlite-vec+APScheduler

## 3. 单版本整合

**Zane v0913**：单版本，不再多版本并存，历史归档`backend/legacy/`

- `backend/main.py` 37KB 762行 单版本整合 103API
- `backend/tools_impl.py` 30KB 统一工具实现 26注册表+30实现(4可选)
- `backend/tool_registry.py` 26工具 修复不一致
- `backend/policy_firewall_v0913.py` 13KB 硬化版
- `backend/legacy/` 13文件历史归档 main_v2/v3/v4/v6/v7/v8 + agent_runtime + tool_registry_old + tools_impl_old

**启动日志3行**：
1. Runtime v2/v3 (env ZANE_RUNTIME=v3) v3可用/回退v2
2. Platform Provider Windows真实/psutil演示 (env ZANE_PLATFORM/DEMO) 系统:linux
3. 工具 0真实 26演示 (env ZANE_LLM_PROVIDER) 演示工具列表

**环境变量显式控制**：
- `ZANE_RUNTIME=v2/v3` Runtime版本切换
- `ZANE_PLATFORM=auto/windows/demo` 平台模式
- `ZANE_DEMO=auto/true/false` 演示模式
- `ZANE_LLM_PROVIDER=local/openai/claude` LLM提供方
- `ZANE_PORT=8000` 端口

## 4. 6缺点全修

1. **双文件隐患** → 单文件`tools_impl.py`统一，消除TOOL_FUNCTIONS覆盖bug
2. **路由无summary** → 补summary+tags按8层架构Swagger文档化
3. **飞轮评分不透明** → `docs/FLYWHEEL_SPEC.md`透明规格+`/api/flywheel/stats`评分分布
4. **SimpleMem无Benchmark** → `tests/benchmark/test_simplemem.py`可复现
5. **前端无真实/演示区分** → `platform_status.js`平台状态条+demo_mode视觉区分
6. **安全策略形式化** → `policy_firewall_v0913.py`硬化版NEED_CONFIRM阻断等待确认

## 5. 工具26个

**文件6**：list_files/read_file/write_file/delete_file/create_folder/move_file
**进程3**：inspect_processes/kill_process/launch_application
**窗口3**：list_windows/focus_window/get_window_info
**视觉3**：take_screenshot/ocr_screenshot/analyze_ui
**输入4**：mouse_click/mouse_move/keyboard_input/key_press
**系统1**：get_system_state
**剪贴板2**：get_clipboard/set_clipboard
**网络2**：web_search/verify_info
**安全2**：security_scan/scan_large_files

**安全增强**：白名单+参数注入防护&|;$`+沙盒realpath+回收站+10MB限制+上下文预算截断20文件15进程+demo_mode字段

## 6. API 103个

**接入层**：/api/health /api/chat /api/agent/execute / (前端)
**平台层**：/api/platform/status 真实/演示+demo_mode+不可用工具
**进化层**：/api/flywheel/stats 评分分布0.5-0.9四档 + /api/evolution/* 18路由
**安全层**：/api/security/pending 待确认队列 + /api/security/confirm 确认操作 + /api/security/scan + /api/security/trend 时间序列 + /api/security/anomalies 异常感知 + /api/security/sandbox/check + /api/security/wsl + /contracts + /policy
**可观测层**：/api/vision/ocr + /api/vision/dpi DPI统一 + /api/utils/cleanup + /api/search/real + /api/dreaming/* + /api/system/* + /api/benchmark + /api/memory/* + /api/tokens + /api/database + /api/models + /api/autonomous

**模块化**：evolution_v3 18 + thinking_v25 6 + memory_v3 12 + security_v3 8 + vision_v3 8 + runtime_v3 10 + auth_v3 3 + benchmark_v3 3 + vector_v3 2 + config_v3 4 = 71模块化+32兼容=103API

## 7. 自主进化8阶段

1. **收集**：聊天成功自动collect_from_success → sft.jsonl
2. **过滤**：data_filter 11危险路径+8文件+7进程+6命令 危险0相似度>0.9重要性0.5-0.9 SimpleMem30%
3. **解析**：model_resolver GGUF+HF双轨 VRAM检测24GB→30B 16GB→7B
4. **训练**：unsloth_trainer_v3 Unsloth非阻塞+日志流+LoRA版本+指数退避
5. **Replay**：30%高质量>0.8防遗忘
6. **评估**：evolution_eval 20任务5分类+50条回放评估 tests/eval_tasks.jsonl 成功率82%
7. **进化**：Prompt Darwin+EvolveR 4版本0.795 + 技能基因变异交叉fitness>0.7保留
8. **晋升**：2%阈值且security不下降，切换LoRA旧版本保留可回滚

**调度**：APScheduler凌晨2点+每30分空闲+资源感知5维度CPU/内存/VRAM/插电/游戏/iOS

**飞轮透明**：`docs/FLYWHEEL_SPEC.md` 维度权重工具链0.3+验证0.3+时间0.2+类型0.2=1.0，总分0.5-0.9，分布API `/api/flywheel/stats`

## 8. 安全

**沙盒**：realpath+白名单+filelock+回收站+10MB限制
**防火墙v0913硬化**：NEED_CONFIRM阻断PENDING_CONFIRM+confirm_id+待确认队列+Event+超时5分钟自动拒绝+前端确认+审计blocked
**过滤100%**：11危险路径C:\Windows\System32 /etc/shadow等+8文件+7进程+6命令，核心路径只读也过滤，去重SHA256+相似度>0.9
**趋势**：cybersec_trend.py 时间序列端口/启动项异常感知，new_ports/closed_ports/new_startup/risk_spike/plaintext_passwords
**DPI统一**：dpi_ocr_unified.py 先统一DPI缩放再OCR最后UIA树，unify_coordinates + to_physical + RapidOCR 50MB + Tesseract回退 + UIA

## 9. 记忆

**4层统一v3**：conversational会话200条压缩100字意图+实体，episodic情景任务历史150字任务+结果+工具，semantic语义习惯事实80字，procedural程序可复用流程120字步骤

**SimpleMem**：语义结构化压缩，论文目标30%压缩+26.4%F1+3x Token，实际实现固定长度100/150/80/120平均75%压缩1.4x，信息保留85%，可复现Benchmark `tests/benchmark/test_simplemem.py`

**遗忘**：访问<3重要性<0.3 30天低价值遗忘，DREAMS.md人类可读

**梦境**：3阶段Dream梦境生成+噪声变体+技能组合+反事实，Evolve进化价值0.3-0.9>0.6生成原则，Consolidate巩固原则到语义

## 10. 前端

**v0913**：29KB，原生HTML/CSS/JS ES Modules 8模块，Canvas交互式图表，CSS变量深色主题4文件，skeleton loading+aria

**平台状态条**：`platform_status.js` 11KB，顶部显示Provider/真实/演示/Runtime/LLM/环境变量+工具真实/演示计数+不可用工具，body.demo-mode黄条+工具卡片demo/real标签视觉区分

**视图**：控制台、进化仪表盘、模型双轨、Token、自主优化、数据库、轨迹、基准20任务、系统+资源5维度、进程、窗口、文件沙盒、记忆4层v3、技能基因、梦境3阶段、安全过滤100%、契约23、思考预算、设置

**轮询**：30秒+自适应15秒+hidden暂停节能

## 11. 快速启动

```bash
# Windows
git clone https://github.com/thianhnguyentuyentuyet6-commits/Zane.git
cd Zane
pip install -r requirements.txt
# Windows真实数据
pip install wmi pywin32 -U
# 可选
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install unsloth sentence-transformers rapidocr_onnxruntime loguru slowapi python-jose filelock apscheduler -U

# 环境变量
set MODEL_PATH=D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf
set HF_MODEL_PATH=Qwen/Qwen3-30B-A3B

# llama.cpp推理可选
llama-server.exe -m Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf --host 0.0.0.0 --port 8080 --ctx-size 32768

# 启动Zane v0913
python run.py
# 或
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 打开
# http://localhost:8000/ 前端控制台
# http://localhost:8000/docs API文档8层架构
# http://localhost:8000/api/health 健康检查启动日志3行
# http://localhost:8000/api/platform/status 平台状态真实/演示
# http://localhost:8000/api/flywheel/stats 飞轮评分分布
# http://localhost:8000/api/security/pending 待确认NEED_CONFIRM

# 环境变量控制
ZANE_RUNTIME=v3 ZANE_PLATFORM=windows ZANE_DEMO=false ZANE_LLM_PROVIDER=local ZANE_PORT=8000 python run.py

# Linux演示
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
# 自动演示模式psutil模拟接口一致
```

## 12. 测试

```bash
python tests/test_tools_impl.py # 工具统一+防火墙阻断
python tests/benchmark/test_simplemem.py # Benchmark可复现
python tests/test_eval_replay.py # 回放评估50条成功率82%

# 结果
# tests/benchmark/simplemem_benchmark_result.json
# tests/eval_replay_result.json
```

**回放评估50条**：`tests/eval_tasks.jsonl` 5分类file/system/window/security/network 3难度easy/medium/hard，成功率82%，历史v6 75%→v7 85%→v8 90%→v0913 82%，晋升判断2%阈值且security不下降

## 13. 目录结构 v0913单版本

```
Zane/
├── backend/
│   ├── main.py 37KB v0913单版本整合103API
│   ├── tools_impl.py 30KB 统一工具26+30实现
│   ├── tool_registry.py 26工具修复不一致
│   ├── policy_firewall_v0913.py 13KB 硬化版
│   ├── legacy/ 13文件历史归档
│   ├── routers/ 71路由模块化 10文件
│   ├── memory/ 飞轮v3+记忆v3+SimpleMem+向量
│   ├── runtime/ 过滤+思考预算+Ralph+有界校正+技能基因+资源监控
│   ├── security/ 沙盒+网安+趋势+WSL
│   ├── vision/ DPI统一+OCR
│   ├── platform/ Windows WMI+Win32真实+Linux演示
│   └── ...
├── frontend/
│   ├── index.html 29KB v0913 103API+平台状态条
│   ├── js/ 11文件 app+platform_status+evolution+charts等
│   └── css/ 4文件 styles+components+layout+themes
├── tests/
│   ├── test_tools_impl.py
│   ├── test_eval_replay.py
│   ├── eval_tasks.jsonl 50条
│   └── benchmark/test_simplemem.py
├── docs/
│   ├── FLYWHEEL_SPEC.md 评分规格透明
│   ├── ZANE_V0913_CHANGELOG.md 变更日志
│   └── REVIEW_DEBUG_REPORT.md Review报告
├── .github/workflows/test.yml CI
├── requirements.txt 16依赖
├── run.py v0913单版本优先+环境变量
├── LICENSE MIT
└── README_V0913.md 本文
```

## 14. 许可证

MIT

## 作者

Zane - 个人AGI管家 单版本整合版

**GitHub**: https://github.com/thianhnguyentuyet6-commits/Zane

> 代码维护现实，AI解释现实 | 数据不出本地，越用越懂你 | 单版本整合+103API+8层架构+6缺点全修+启动日志3行+平台状态条+安全硬化+飞轮透明
