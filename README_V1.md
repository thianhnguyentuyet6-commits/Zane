# Zane AGI v1.0 - 可靠本地计算机代理

> **核心原则：代码维护现实，AI解释现实**  
> **目标：Reliable Local Computer Agent，非更多AGI概念**

---

## 一句话介绍

私有、自主、自我进化的 Windows 桌面助手，本地 Qwen3-30B-A3B MoE 为主，真实工具控制，工具契约+策略防火墙+验证+事务+可观测可测试可恢复可度量，单端口部署。

---

## 技术诚实 - 实现状态

### IMPLEMENTED 已实现

**8层精简架构，每层单一职责：**
1. 感知层 - WMI真实 + Win32 HWND真实 + psutil + Pillow截图
2. 推理层 - Qwen3-30B-A3B MoE 30B/3B IQ4_XS + 意图解析中文容错
3. 规划层 - DAG分解 + 技能匹配 + 模板
4. 工具层 - 23工具真实 + 形式化契约 + 沙盒
5. 策略层 - PolicyEngine独立，LLM只提议，Policy决定allow/need_confirm/deny
6. 执行层 - 事务化+撤销栈+熔断+超时
7. 验证层 - 区分API完成vs真实成功，进程存在+窗口出现
8. 记忆层 - 5类型不同保留 + 向量检索可选 + 技能版本化

**21工具真实（+2新增）：**
- 文件：list_files, read_file, write_file, create_folder, move_file, delete_file - 真实FS + 沙盒realpath+白名单+回收站+10MB限制
- 进程：inspect_processes, kill_process - 真实进程树 + 保护csrss.exe等关键进程
- 窗口：list_windows, focus_window - 真实HWND + Z序+DPI+置顶
- 视觉：take_screenshot, ocr_screenshot - 真实截图
- 系统：get_system_state - WMI真实CPU每核心+内存条+磁盘+启动项
- 安全：security_scan, scan_large_files - 漏洞扫描明文密码高危端口大文件
- Linux：wsl_exec - WSL白名单ls/cat/grep+shlex.quote+禁止;|&+超时10秒
- 网络：web_search_real - Bing API优先+DuckDuckGo回退+防SSRF禁止内网IP+超时10秒
- 输入：get_clipboard, set_clipboard, mouse_click, keyboard_input
- 验证：verify_info

**安全加固 v3.2：**
- 修复 Popen注入：白名单+参数校验禁止&|;$ + shlex.split + shell=False
- 修复 WSL注入：白名单只读+shlex.quote+禁止拼接
- 修复路径遍历：realpath+严格白名单+保护System32/etc
- 文件10MB+磁盘检查+日志换行净化
- 速率60/分+可选X-Zane-Token+危险操作默认需确认+预览Diff

**Runtime模块化10模块：**
- intent_parser：中文口语容错，分类file/process/window/vision/security/linux/network/system，实体提取path/pid/app_name，歧义检测
- state_manager：真实观测，统一SceneRepresentation 截图+宽高+DPI+窗口+UIA+OCR+光标+应用上下文
- planner：DAG分解，模板匹配organize_downloads/clean_large_files，风险评估，验证方法
- tool_executor：安全边界+事务pre/post+撤销栈+Trace，支持同步异步
- verifier：区分API完成vs真实成功，launch_application进程存在+窗口出现，非success
- recovery_manager：失败5分类permission/not_found/timeout/network/invalid_param，指数退避重试，熔断
- memory_manager：5类型 working任务结束清空/episodic30天衰减/semantic永久/procedural Skill/preference
- skill_manager：版本化可复用，trigger/required_tools/procedure/parameters/preconditions/verification/recovery/version
- model_interface：本地优先教师可选，OpenAI兼容，离线演示
- trace_logger：统一轨迹 user_request/observations/decisions/tool_calls/state_changes/verification/failures/recovery/outcome/latency/token/confidence
- policy_engine：安全边界独立，保护路径System32/SysWOW64/etc+关键进程csrss.exe+auto_allow只读+decide+preview可撤销
- dreaming：三阶段 Light扫描去重暂存不写入→REM主题反思增强信号不写入→Deep六信号加权阈值0.7才写入

**记忆与进化：**
- 记忆5种不同保留策略，JSON持久化
- 技能版本化，可回放评估编辑回滚独立于基础模型
- 数据飞轮自动收集成功任务为SFT/DPO，data_flywheel.py
- 自我进化QLoRA rank32 4bit + Unsloth 2倍速，评估20任务回放，提升才晋升，保留回滚
- 梦境三阶段：Light 7天扫描→REM主题→Deep六信号评分阈值0.7写入长期+DREAMS.md叙事
- 向量记忆：sqlite-vec可选，无则关键词回退，all-MiniLM-L6-v2 80MB本地语义检索

**任务轨迹与基准：**
- 统一Task Trace：data/traces/task_*.json，含12字段，成为调试/记忆/Skill/评估/训练基础
- 可复现基准12任务8类别：process/window/filesystem/clipboard/app launching/UI/screenshot/OCR/visual grounding/multi-step/failure recovery/ambiguous，每个显式成功标准可重放，指标success rate/verification accuracy/recovery rate/avg tool calls/latency/token/regression rate

**前端 v3.2：**
- 专业本地AI操作控制台，非通用聊天，深色Linear/Raycast风格
- 16视图：控制台/轨迹/基准/系统/WMI真实/进程树/窗口HWND/文件/视觉/记忆向量/技能/梦境三阶段/进化/安全/契约/模型注册表/设置
- 执行流Observe→Plan→Act→Verify→Recover可视化，工具卡片验证区分真实成功，确认弹窗预览Diff，撤销栈，通知中心
- 单端口8000，前端已写入content，无需单独部署

**部署：**
- `python -m uvicorn backend.main_v3:app --host 0.0.0.0 --port 8000`
- 单端口，前端 `/`，API `/docs`
- Windows：`.\scripts\setup_windows.ps1` + `python run.py`

### PARTIAL 部分实现

- UIA：接口预留，真实需Windows+UIAutomation库
- DWM缩略图：接口预留
- OCR：演示，真实需PaddleOCR
- iOS远程：API预留8002端口
- 托盘、快捷键：规划
- 向量检索：关键词匹配为主，sqlite-vec可选需安装sentence-transformers

### EXPERIMENTAL 实验性

- MoE专家人格化：分析128专家激活，标记实验性，需实验对比Full LoRA/常规PEFT/专家选择性在VRAM/训练时间/性能/回归，未实验前不声称90%成本降低
- 梦境辩论、技能基因：需审核，Light→REM→Deep已实现基础

### PLANNED 计划

- EXE打包 PyInstaller
- PaddleOCR真实集成
- 基准前端可视化图表
- WMI图表Canvas折线图
- 文件锁filelock+slowapi限流+jwt认证+loguru日志

---

## 快速开始

### Windows本地部署（推荐）

```powershell
# 1. 克隆
git clone https://github.com/thianhnguyentuyet6-commits/Zane.git
cd Zane

# 2. 一键安装
.\scripts\setup_windows.ps1

# 3. 配置模型（你的Qwen3路径）
# 编辑 .env 或设置环境变量
# LLM_MODEL_PATH=D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf

# 4. 启动 llama.cpp server（另开终端）
.\llama.cpp\llama-server.exe -m D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf --host 0.0.0.0 --port 8080 --ctx-size 32768 --n-gpu-layers 35 --flash-attn --cont-batching

# 5. 启动 Zane AGI
python run.py
# 或
python -m uvicorn backend.main_v3:app --host 0.0.0.0 --port 8000

# 6. 打开浏览器
# http://localhost:8000
```

### Linux演示环境

```bash
git clone https://github.com/thianhnguyentuyet6-commits/Zane.git
cd Zane
pip install -r requirements.txt
python -m uvicorn backend.main_v3:app --host 0.0.0.0 --port 8000
# http://localhost:8000
```

### 环境变量

```bash
# .env
BING_API_KEY=your_bing_key  # 可选，真实搜索，1000次/月免费
ZANE_TOKEN=your_secret_token  # 可选，API认证 X-Zane-Token头
LLM_API_BASE=http://localhost:8080/v1
LLM_MODEL=qwen3-30b-a3b
```

---

## API - 已实现23工具+安全+契约+轨迹+模型+基准+联网+梦境+向量+Runtime

| 接口 | 功能 | 验证 |
|---|---|---|
| `/api/health` | 健康+版本+安全信息 | ✅ |
| `/api/chat` | 对话+完整循环Observe→Plan→Act→Verify→Recover | ✅ |
| `/api/system/state` | WMI真实系统状态 | ✅ |
| `/api/system/processes` | 真实进程树 | ✅ |
| `/api/system/windows` | 真实HWND | ✅ |
| `/api/system/files` | 真实文件+沙盒检查 | ✅ |
| `/api/system/screenshot` | 真实截图 | ✅ |
| `/api/tools` | 工具注册表21工具 | ✅ |
| `/api/tools/call` | 工具调用+PolicyEngine+验证 | ✅ |
| `/api/contracts` | 形式化契约23个 | ✅ |
| `/api/contracts/{tool}` | 单个契约 | ✅ |
| `/api/traces` | 统一轨迹列表+统计 | ✅ |
| `/api/traces/{id}` | 单个轨迹 | ✅ |
| `/api/model-registry` | 模型注册表推理训练分离 | ✅ |
| `/api/benchmark` | 基准12任务 | ✅ |
| `/api/benchmark/run/{id}` | 运行单个基准 | ✅ |
| `/api/benchmark/run-all` | 运行全部基准 | ✅ |
| `/api/search/real` | 真实联网Bing优先+DuckDuckGo回退+防SSRF | ✅ |
| `/api/dreaming/light|rem|deep|run-all|status` | 梦境三阶段 | ✅ |
| `/api/memory/vector/add|search` | 向量记忆语义检索 | ✅ |
| `/api/runtime/intent/parse` | 意图解析 | ✅ |
| `/api/runtime/state/observe` | 真实观测 | ✅ |
| `/api/runtime/plan` | DAG规划 | ✅ |
| `/api/runtime/skills/match` | 技能匹配 | ✅ |
| `/api/security/sandbox/check` | 沙盒检查 | ✅ |
| `/api/security/scan` | 漏洞扫描 | ✅ |
| `/api/security/wsl` | WSL列表 | ✅ |
| `/api/security/wsl/exec` | WSL白名单执行 | ✅ |
| `/api/policy` | PolicyEngine安全边界 | ✅ |
| `/` | 前端v3专业控制台 | ✅ |
| `/docs` | API文档 | FastAPI自动 |

---

## 架构 - 8层精简

```
用户自然语言
    ↓
[Observe] state_manager 真实WMI+窗口+进程+统一场景
    ↓
[Parse] intent_parser 中文容错+实体+歧义
    ↓
[Skill Match] skill_manager 版本化技能匹配
    ↓
[Plan] planner DAG分解+模板+风险评估
    ↓
[Policy] policy_engine 安全边界独立，LLM只提议，Policy决定
    ↓
[Act] tool_executor 事务pre-state+执行+post-state+撤销栈+Trace
    ↓
[Verify] verifier 区分API完成vs真实成功，进程存在+窗口出现
    ↓
[Recover] recovery_manager 失败分类+重试+替代+重规划+熔断
    ↓
[Memory] memory_manager 5类型+vector+skill+trace+benchmark
    ↓
最终报告 + 轨迹 + 记忆 + 技能 + 飞轮
```

**每层单一职责，必要性已在ARCHITECTURE_V3.md解释**

---

## 安全 - 商业级

- 文件沙盒：realpath+白名单+保护System32/SysWOW64/etc+回收站+10MB限制+磁盘检查
- 进程沙盒：保护csrss.exe/winlogon.exe等关键进程，高危进程二次确认
- WSL沙盒：白名单ls/cat/grep...15个只读+shlex.quote+禁止;|&><$``+超时10秒+workdir限制
- 联网安全：防SSRF禁止内网IP 127.0.0.1/10.x/192.168.x/172.16.x+超时10秒+截断5000+查询清理
- API安全：速率60/分+可选X-Zane-Token+危险操作强制确认+预览Diff+日志换行净化
- 策略引擎：LLM只提议，PolicyEngine决定allow/need_confirm/deny，永不依赖模型判断安全
- 破坏性事务：记录pre-state+可逆机制(删除→回收站/移动→映射回滚/配置→备份/进程→PID)+验证post-state+提交或回滚

---

## 记忆与进化 - 证据驱动

- **多类型不同保留：** working当前任务结束清空/episodic事件30天衰减/semantic稳定事实永久/procedural成功流程版本化Skill/preference用户行为
- **技能版本化：** trigger conditions/required tools/procedure/parameters/preconditions/verification rules/failure recovery/version，可回放评估编辑回滚独立于基础模型
- **自我改进基于证据：** collect traces→识别成功失败→分类失败→生成候选→创建训练/Skill数据→训练candidate adapter→跑固定benchmark→对比当前版本→提升才晋升→保留回滚，回答什么变了/为什么/什么提升/什么回归/是否晋升
- **MoE实验性：** 需实验对比Full LoRA/常规PEFT/专家选择性在VRAM/训练时间/性能/回归，未实验前不声称90%成本降低
- **硬件分离：** Model Registry跟踪base model/quantization/runtime backend/context length/GPU offload/adapter versions/benchmark/promotion status
- **梦境三阶段：** Light扫描短期去重暂存不写入→REM主题反思增强信号不写入→Deep六加权信号阈值0.7才写入长期+DREAMS.md叙事+机器状态

---

## 对比商业产品 - 技术诚实

| 能力 | Operator/Manus | PowerToys/Raycast | Zane AGI v1.0 |
|---|---|---|---|
| Windows深度 | 云端通用 | 本地工具 | WMI真实+HWND真实+UIA预留+DWM预留，任务管理器同级准确 |
| 安全 | 无撤销 | 无 | 沙盒+撤销栈+回收站+PolicyEngine独立+保护路径 |
| 记忆 | 会话 | 无 | 5类型+向量可选+技能版本化+经验+飞轮+梦境三阶段 |
| 进化 | 无 | 无 | 数据飞轮自动SFT/DPO+QLoRA+评估晋升回滚+模型注册表 |
| 可观测 | 日志分散 | 无 | 统一Task Trace 12字段+基准12任务可重放+指标 |
| 验证 | API success | 无 | 区分API完成vs真实成功，进程存在+窗口出现 |
| 中文 | 英文为主 | 英文 | 简体中文优先，口语容错，路径映射 |
| 部署 | 云端 | 本地 | 单端口8000，前端写入content，离线可用，本地LLM为主 |
| 开源 | 闭源 | 部分 | 完全开源，可审计 |

**品质目标：媲美商业级完善产品，对标Operator/Claude Computer Use + Manus/Devin + PowerToys/Raycast，不是滥竽充数**

---

## 困惑权衡异议 - 技术诚实

1. **MoE专家选择性微调是否有效？** 推理激活专家，训练只训这些，是否遗忘其他？想降成本但可能降泛化。权衡：需实验Full LoRA vs 专家选择性，VRAM/时间/性能/回归，标记实验性，不吹嘘90%。异议：反对现在声称90%成本降低，应先实验。

2. **自我进化是否会变差？** 自动收集数据质量参差，训练后可能更差。想越用越懂你，但噪音污染。权衡：严格评估历史20任务回放，提升才晋升，保留回滚，Replay防遗忘，六信号阈值0.7。异议：反对夜间自动学习无评估就晋升，必须基准测试。

3. **视觉是否应主要接口？** Claude用视觉通用但慢贵。结构化快准便宜但UIA不一定覆盖。权衡：层次结构化→UIA→OCR→视觉→坐标，优先结构化，视觉补充回退。异议：反对视觉作为通用接口。

4. **技能是否直接变权重？** 成功流程直接微调还是先变技能？微调直接但不可解释难回滚。权衡：先变版本化技能可回放评估编辑回滚独立于基础模型，安全易调试，稳定后再蒸馏。异议：反对成功直接微调。

5. **本地vs云端隐私vs能力？** 云端更强但隐私，本地3B激活能力有限但私有。权衡：本地优先云端可选教师，本地保持核心能力，云不可用仍可执行，Teacher建议，本地权威。异议：反对变云瘦客户端。

6. **功能多vs基础牢？** 要求功能多AGI管家但基础不牢，功能多导致杂。权衡：下一里程碑Reliable Local Computer Agent而非更多AGI，先让现有确定可观测可测试可恢复可度量，再加高层。异议：反对现在加更多AGI概念。

7. **GitHub Skill整合？** 很多优秀Skill是否照搬？照搬快但可能不适配。权衡：可整合但需适配，例如file-organizer改为沙盒+撤销+验证符合契约，非照搬。异议：反对照搬，应适配整合。

8. **14层是否必要？** 14层是否冗杂？想分层清晰但职责重叠。权衡：精简为8层每层单一职责，必要性已解释，移除视觉技能学习系统教师冗余层，新增安全到工具+策略。异议：反对14层，应精简为8层。

---

## 下一步 - Reliable Local Computer Agent

**不是更多AGI，而是：**

- 本地模型接收自然语言任务
- 观测真实Windows状态
- 选择结构化工具
- 通过受控运行时执行
- 验证真实结果
- 从失败恢复
- 记录轨迹
- 复用成功流程为技能
- 针对固定基准改进，可度量

**一旦在可复现基准上可靠，高层学习和进化才有坚实基础**

---

## 许可证

MIT - 私有、自主、本地优先
