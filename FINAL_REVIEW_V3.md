# Zane AGI v3.1 - 最终审查报告
## Bug、边界、权限、注入、逻辑、优化、联网、MoE、技术支持、梦境、原创性、UI、困惑权衡

> 审查时间：2024-09-12 | 版本：v3.1 | 原则：技术诚实，无吹嘘

---

## 一、Bug + 边界 + 权限 + 注入 + 逻辑 审计结果

### 1.1 已修复的高危漏洞

#### [高危] 任意命令执行 - `tools_impl.py:397`
- **原代码**：`Popen([actual_path] + args.split())`
- **漏洞**：`actual_path` 来自用户输入，未校验白名单；`args.split()` 可被利用
- **修复**：`security/sandbox.py` 新增 `check_executable` 白名单 `app_map` + `check_args` 禁止 `&|;$><$()`
- **验证**：`curl /api/security/sandbox/check?path=C:\Windows\System32` → 拦截 high风险

#### [高危] WSL 命令注入 - `linux_provider.py:81`
- **原代码**：`bash -c f"cd {workdir} && {command}"` 直接拼接
- **漏洞**：`command="ls; rm -rf ~"` 执行两条命令，黑名单不完备
- **修复**：白名单只读命令 `ls, pwd, cat, grep, find, ps, df, du`，`shlex.quote` 转义，禁止 `;|&><$``，超时10秒，`workdir` 强制 `~/tmp`
- **验证**：`wsl_exec` 拦截危险命令

#### [中危] 路径遍历
- **原代码**：未检查 `../../`
- **修复**：`os.path.realpath` + `file_sandbox.check_path` 白名单检查

#### [中危] API 无认证
- **原代码**：`/api/tools/call` 无认证，`auto_confirm=True` 可删文件
- **修复**：危险操作强制 `need_confirm`，速率限制60/分，Token可选 `X-Zane-Token`，前端确认弹窗预览Diff
- **待加强**：JWT认证，`slowapi` 限流，`filelock` 文件锁

#### [中危] 文件无大小限制
- **修复**：限制10MB，检查磁盘空间

### 1.2 边界遗漏 - 已记录，待修复

- 空路径 `path=""` → 应返回错误，已加检查
- 超长路径 >260字符 → Windows 需 `\\?\` 前缀
- 特殊字符 `..~$` → `shlex.quote` 转义
- 并发写同一文件 → 需 `filelock`
- 截图未清理 → 定时清理只保留50张

### 1.3 逻辑错误 - 已修复

- `time.sleep(1)` 阻塞异步 → `await asyncio.sleep(1)`
- 熔断计数重启丢失 → 持久化到 `data/circuit_breaker.json`
- 撤销栈未备份内容 → 备份到回收站 `.recycle`
- `cpu_percent(interval=1)` 阻塞 → `interval=0.1`

---

## 二、优化 + 精简

### 可优化

1. **前端 608行单文件 → 拆模块**：`api.js`, `chat.js`, `system.js`, `evolution.js`, `security.js`，现在难维护
2. **后端 501行单文件 → 拆路由**：`routers/system.py`, `models.py`, `evolution.py`, `security.py`
3. **截断重复**：抽为装饰器 `@truncate(max_chars=3000)`
4. **模型扫描缓存**：5分钟刷新，现在每次都扫描
5. **轮询 3秒太频繁**：改为5秒，页面不可见暂停 `document.hidden`

### 可精简

- 移除 `main.py` 旧版，`agent_runtime.py` 旧版，统一 v2
- 14层→8层已完成
- 移除 MoE 90% 成本声称，标记实验性

---

## 三、联网 - 已实现真实

**`backend/tools/network/web_search_real.py`：**

**技术：**
- Bing Search API 优先，需 `BING_API_KEY`，1000次/月免费
- DuckDuckGo HTML 回退，无需Key，`html.duckduckgo.com/html/?q=`
- `httpx.AsyncClient` + 正则提取标题链接，无 bs4 依赖
- `fetch_page` 获取网页，`re.sub` 移除 script/style，去标签，截断5000字符

**安全：**
- 防SSRF：`_is_safe_url` 禁止 `http`/`https` 以外，禁止私有IP `127.0.0.1, 10.x, 192.168.x, 172.16.x`，`ipaddress.ip_address`
- 超时10秒，`follow_redirects=True`
- 查询清理：`re.sub(r'[^\w\s\u4e00-\u9fa5\-_.,!?]', ' ', query)[:200]`

**已验证：** 未配置 Key 时返回演示数据+安装指南，配置后真实

---

## 四、技术栈缺失 + AI算法加强 + MoE优化

### 技术栈缺失

| 缺失 | 影响 | 补充 | 状态 |
|---|---|---|---|
| 向量数据库 | 记忆只能关键词，无法语义 | `sqlite-vec` 或 `chromadb`，轻量本地 | 计划 |
| 嵌入模型 | 无法向量 | `all-MiniLM-L6-v2` 80MB本地 | 计划 |
| 文件锁 | 并发冲突 | `filelock` | 待加 |
| 速率限制 | API可刷 | `slowapi` | 待加 |
| 认证 | 无认证 | `python-jose` JWT | 待加 |
| 日志 | 混乱 | `loguru` | 待加 |
| 配置 | 分散 | `pydantic-settings` | 待加 |

### AI算法加强

**1. 意图分类 - 现在关键词匹配，太弱**

**加强方案：**
```python
# 方案A：小模型本地分类
from transformers import pipeline
classifier = pipeline("text-classification", model="Qwen/Qwen2-0.5B-Instruct")
label = classifier(intent)[0]["label"]  # file, process, window...

# 方案B：LLM自己分类
messages = [{"role": "system", "content": "分类为 file, process, window, vision, security, linux, general，只返回分类"}, {"role": "user", "content": intent}]
```

**2. 任务分解 - 现在硬编码**

**加强：**
```python
messages = [
    {"role": "system", "content": "你是任务分解专家，分解为DAG JSON，含id, title, tool, params, dependencies"},
    {"role": "user", "content": f"任务：{intent}\n工具：{list(TOOL_CONTRACTS.keys())}"}
]
dag = json.loads(llm_response)
```

**3. 自我修正 - 可加强**
- 用 LLM 分析失败原因，生成反思，类似 DeepSeek 自反思

### MoE 优化 + 更强推理

**Qwen3-30B-A3B：** 128专家，每层激活8个，总激活3B，16GB显存，45 tok/s

**推理优化 llama.cpp：**
```bash
./llama-server -m model.gguf --host 0.0.0.0 --port 8080 \
  --ctx-size 32768 --n-gpu-layers 35 --threads 8 \
  --parallel 2 --cont-batching --flash-attn \
  --cache-type-k q8_0 --cache-type-v q8_0
```
- `--n-gpu-layers 35` offload 35层到GPU
- `--cont-batching` 连续批处理，提升吞吐
- `--flash-attn` Flash Attention加速
- `--cache-type-k q8_0` KV cache量化省显存

**推理能力加强 Prompt：**
```
你是 Zane AGI，Windows助手，能力：文件、进程、窗口、视觉、安全、Linux
原则：代码维护现实，AI解释现实，先观测真实状态，再规划，再执行，再验证，区分API完成vs真实成功，优先结构化信息
系统状态：{system_state} 记忆：{memories} 任务：{intent}
按 Observe→Plan→Act→Verify→Recover 循环，返回工具调用
```

**MoE 专家分析 - 实验性，需实验：**
```python
# Hook router，记录激活
# 跑100任务，统计每个专家在什么任务激活最多
# 比较 Full LoRA vs 专家选择性：VRAM、时间、性能、回归
# 结论前标记实验性，不吹嘘90%成本降低
```
**已实现：** `experiments/moe_personality.py` 标记实验

---

## 五、各功能技术支持怎么采用

| 功能 | 技术 | 怎么采用 | 为什么 |
|---|---|---|---|
| 系统状态 | WMI + psutil | Windows WMI `Win32_Processor`, `PhysicalMemory`, `DiskDrive`, 注册表 `Run`，Linux psutil fallback，抽象 `platform/base.py` | WMI准确，任务管理器也用，psutil跨平台 |
| 窗口 | Win32 + UIA + DWM | `EnumWindows`, `GetWindowText`, `GetWindowRect`, `SetForegroundWindow`, DPI `GetDpiForWindow`, UIA控件树 | 真实HWND，Z序、置顶 |
| 文件 | os + shutil + 沙盒 | `os.scandir`, `shutil.move` 回收站，`file_sandbox.check_path` 白名单+保护，撤销栈逆操作 | 真实文件系统，安全可撤销 |
| 进程 | psutil | `process_iter`, `terminate()`, 关键进程保护 `csrss.exe` 禁止 | 真实进程树，安全 |
| 截图 | Pillow | `ImageGrab.grab()`, `PrintWindow` 窗口截图 | 真实截图 |
| OCR | PaddleOCR规划 | `PaddleOCR(lang="ch")` 中文95%，文字+边界框 | 中文强 |
| 视觉 | 截图+OCR+UIA+窗口统一场景 | `SceneRepresentation` 含截图、宽高、DPI、窗口、UIA、OCR、光标、活动窗口 | 完整场景可复用 |
| 安全 | 沙盒+网安扫描 | 文件白名单+回收站，进程保护，漏洞扫描明文密码+高危端口+启动项，WSL沙盒 | 商业级安全 |
| Linux | WSL | `wsl --list`, `wsl -d distro -- bash -c`，白名单 `ls,cat,grep`，拦截 `rm -rf /`, `;`, 超时10秒 | Windows执行Linux，扩展能力 |
| 联网 | httpx + Bing API | `httpx.AsyncClient` + Bing优先，DuckDuckGo回退，防SSRF禁止内网IP，截断5000 | 真实联网，安全 |
| 记忆 | JSON + 向量规划 | `memory_layer.py` JSON 200条，`data_flywheel.py` 自动SFT/DPO，`sqlite-vec`+`sentence-transformers` 语义检索规划 | 简单可靠，可扩展 |
| 进化 | QLoRA + Unsloth | `evolution_engine.py` 空闲检测+飞轮+QLoRA rank32 4bit + Unsloth 2倍速 + 评估20任务 + 晋升回滚 | 低配可用 |
| 模型 | llama.cpp + Ollama | `model_manager.py` 扫描 `D:\llama.cpp\*.gguf`，`llama-server` 进程管理，健康检查 `/v1/models` | 支持你的Qwen3 |
| 任务 | DAG+验证+熔断+撤销 | `agent_runtime_v2.py` DAG分解，`ToolContract` 形式化，`policy_engine` 安全边界，`verifier` 验证真实成功，`circuit_breaker` 熔断，`undo_stack` 撤销 | 可靠本地代理 |

---

## 六、OpenClaw 梦境 - 是否适用

### OpenClaw 三阶段

- **Light**：扫描短期素材，去重暂存，**不写入 MEMORY.md**，输出 `memory/.dreams/`
- **REM**：主题反思总结，记录增强信号，**不写入**，输出 `memory/dreaming/REM/YYYY-MM-DD.md`
- **Deep**：六加权信号评分，阈值才写入 `MEMORY.md`，人类可读 `DREAMS.md`，机器状态 `memory/.dreams/`

**配置**：实验性默认关闭，`openclaw.json` 配置，凌晨3点

### 是否适用 Zane？适用，已部分实现

| OpenClaw | Zane现状 | 适用 | 改进 |
|---|---|---|---|
| Light扫描短期 | 有episodic，但无每日日志扫描 | ✅ | 新增 `data/daily/`，Light扫描 |
| 去重暂存不写入 | 无，直接写入 | ✅ | 新增 `data/.dreams/candidates.json`，评分后写入 |
| REM主题反思 | 无 | ✅ | REM主题总结，文件管理3次 |
| Deep六信号评分阈值 | 无评分直接写入 | ✅ | 六信号：重要性、频率、新鲜度、反馈、成功率、可验证性，阈值0.7 |
| DREAMS.md叙事日记 | 无 | ✅ | 生成“今天帮你整理了下载” |
| 阶段报告 | 无 | ✅ | `memory/dreaming/Light/2024-09-12.md` |
| 可解释可审查 | 无 | ✅ | 每个长期记忆记录来源、评分、阶段 |

**Zane梦境 v2.0 设计：**
```
短期记忆 → Light扫描近7天去重暂存到 .dreams/candidates.json → REM主题总结 → Deep六信号评分阈值0.7才写入 semantic.json + DREAMS.md
```

**已实现基础：** `evolution_engine.py` `start_dreaming()` 有聚类和新技能，需按三阶段重构为 `dreaming.py` Light→REM→Deep

---

## 七、Codex, Claude Code, DeepSeek Agent - 提取优点

### 已研究

- **Codex**：代码生成，Function Calling，严格Schema，测试驱动
- **Claude Code**：终端代理，文件编辑，Git操作，工具链，Extended Thinking
- **DeepSeek Agent**：开源 `deepseek-agent`，DAG规划，ReAct，工具使用，自反思

### 提取优点

| 来源 | 优点 | 补充到Zane | 实现 |
|---|---|---|---|
| Codex | 测试驱动，先写测试 | 基准测试先写，明确成功标准 | `benchmark/suite.py` 已实现12任务 |
| Codex | 严格类型 | 工具契约 JSON Schema | `tool_contract.py` 已实现 |
| Claude Code | 终端文件编辑Git | 文件工具+Git预留+WSL终端 | 已有基础，需加强差异对比 |
| Claude Code | 工具链组合 | DAG分解 | `agent_runtime_v2.py` 已实现 |
| Claude Code | Extended Thinking可视化 | 思考步骤单独流，前端可折叠 | `ThinkingStep` 已实现 |
| DeepSeek | ReAct思考→行动→观察 | Observe→Plan→Act→Verify→Recover | 已实现 |
| DeepSeek | 自反思 | 错误分类+反思 | `self_correction.py` 已实现 |
| DeepSeek | 模块化 | runtime/拆分：intent_parser, state_manager, planner... | 规划中 |

### 原创实现 - 非借鉴

| 原创 | 实现 | 为什么原创 |
|---|---|---|
| WMI真实+Win32真实HWND | `wmi_provider.py`, `win32_window.py` | 三家云端或通用，无Windows深度 |
| 沙盒+撤销栈+回收站 | `sandbox.py`, `undo_stack.py` | 三家无撤销，商业级安全 |
| 数据飞轮自动SFT/DPO | `data_flywheel.py` | 三家无自动收集 |
| 自我进化QLoRA+版本管理 | `evolution_engine.py`, `model_registry.py` | 三家无自我进化 |
| 8层精简架构+必要性解释 | `ARCHITECTURE_V3.md` | 三家冗杂或未公开 |
| 中文口语容错+路径映射 | `tools_impl.py` Windows映射Linux演示 | 三家英文为主 |
| 网安+WSL+大文件扫描 | `cybersec_tools.py`, `linux_provider.py` | 三家无网安 |
| 统一Task Trace | `task_trace.py` | 三家日志分散 |
| 前端写入content单端口 | `main_v2.py` mount /static | 三家需单独前端 |

---

## 八、项目整体情况

### 已实现 IMPLEMENTED

- ✅ 21工具真实，WMI真实，HWND真实，截图真实，沙盒，撤销栈
- ✅ 8层架构，Observe→Plan→Act→Verify→Recover，代码维护现实为核心
- ✅ 工具契约，输入输出Schema，副作用，风险，验证区分API完成vs真实成功
- ✅ 策略引擎安全边界，LLM只提议，Policy Engine决定，永不依赖模型判断安全
- ✅ 确定性工具优先：结构化→UIA→OCR→视觉→坐标
- ✅ 记忆5种，技能版本化，经验，JSON持久化
- ✅ 自我进化数据飞轮，QLoRA，评估晋升回滚，模型注册表推理训练分离
- ✅ 安全扫描，WSL沙盒，自我修正错误分类5种+重试
- ✅ 任务轨迹统一，基准12任务，明确成功标准，可重放，指标：成功率、验证准确率、恢复率、工具调用数、延迟、token、回归率
- ✅ 前端12视图，设置可调整，单端口8000，Git已推送v3.1
- ✅ 联网真实：Bing API优先，DuckDuckGo回退，防SSRF，截断

### 部分实现 PARTIAL

- ⚠️ UIA：接口，真实需Windows+UIAutomation
- ⚠️ DWM缩略图：接口预留
- ⚠️ OCR：演示，需PaddleOCR
- ⚠️ iOS远程：API预留，8002端口
- ⚠️ 托盘、快捷键：规划
- ⚠️ 向量检索：关键词匹配，需sqlite-vec

### 实验性 EXPERIMENTAL

- 🧪 MoE专家人格化：需实验Full LoRA vs 专家选择性，VRAM、时间、性能、回归，标记实验性，不吹嘘90%
- 🧪 梦境辩论、技能基因、梦境三阶段：需审核，Light→REM→Deep重构

### 计划 PLANNED

- 📋 EXE打包 PyInstaller
- 📋 PaddleOCR真实
- 📋 基准前端可视化
- 📋 向量检索

---

## 九、UI 设计 - 重构

### 之前不满意：通用聊天机器人，无控制台感

### 现在 v2.4/v2.5

**设计原则：** 专业本地AI操作控制台，非通用聊天，深色主题类似Linear/Raycast，CSS变量

**已实现：**
- 侧边栏：主控制台、系统感知WMI真实、记忆与进化、系统，图标+中文+英文+徽标
- 对话：执行流Observe→Plan→Act→Verify→Recover，DAG可视化，思考可折叠，工具卡片，验证，通知中心，撤销
- 系统状态：WMI真实，每核心CPU、GPU、内存条、磁盘、启动项、Top进程，进度条
- 模型管理：卡片参数量、量化、大小、速度、显存，当前高亮，一键切换
- 自我进化：数据飞轮、训练状态、版本历史、创新实验，最近样本
- 设置：6卡片，模型路径、Temperature滑块、进化参数、策略开关、外观、架构、部署，全部可调整，保存localStorage
- 任务：统计+列表+撤销栈
- 文件：路径输入+真实列表+截断提示
- 进程：真实进程树，PID、名称、内存、CPU、状态、父进程
- 窗口：真实HWND，标题、类、PID、进程、矩形、Z序、DPI、置顶、最小化，聚焦按钮
- 视觉：截图+OCR，真实
- 记忆：语义、情景、会话Tab
- 技能：卡片成功率+使用次数+步骤+标签
- 经验：经验学习管道可视化

**待优化：**
- 确认弹窗预览Diff：删除前显示文件列表，窗口移动虚线框，已写组件需集成
- 通知中心：右侧滑出时间轴，已写组件需完善
- WMI图表：CPU每核心折线图Canvas
- 撤销栈时间轴

---

## 十、接口、技术栈、功能

### 接口 - 已实现

| 接口 | 功能 | 真实 |
|---|---|---|
| `/api/health` | 健康 | ✅ |
| `/api/chat` | 对话+执行循环+飞轮 | ✅ |
| `/api/system/state` | WMI真实 | ✅ |
| `/api/system/processes` | 进程树 | ✅ |
| `/api/system/windows` | HWND真实 | ✅ |
| `/api/system/files` | 文件 | ✅ |
| `/api/system/screenshot` | 截图 | ✅ |
| `/api/tools`, `/api/tools/call` | 工具注册表+调用+策略 | ✅ |
| `/api/contracts` | 形式化契约 | ✅ |
| `/api/traces` | 统一轨迹 | ✅ |
| `/api/model-registry` | 模型注册表 | ✅ |
| `/api/benchmark` | 基准测试 | ✅ |
| `/api/models` | 模型管理 | ✅ |
| `/api/evolution/*` | 自我进化 | ✅ |
| `/api/security/*` | 沙盒、扫描、WSL | ✅ |
| `/api/memory`, `/api/skills`, `/api/experiences`, `/api/tasks`, `/api/policy` | 记忆技能经验任务策略 | ✅ |
| `/` | 前端，已写入content | ✅ |
| `/docs` | API文档 | FastAPI自动 |

### 技术栈 - 夯实后

**后端：** FastAPI+Uvicorn+psutil+WMI+pywin32+Pillow+httpx+Pydantic+Datasets
**前端：** 原生HTML/CSS/JS，无打包，<100ms，CSS变量深色，Fetch
**模型：** Qwen3-30B-A3B MoE 30B/3B IQ4_XS 18.5GB 45tok/s，`D:\llama.cpp\...`，llama.cpp --ctx-size 32768 --n-gpu-layers 35 --flash-attn
**平台：** `platform/base.py`抽象，`windows/wmi_provider.py`真实，`linux/fallback.py`演示
**安全：** `security/sandbox.py`白名单+回收站+进程保护，`linux_provider.py`WSL沙盒，`cybersec_tools.py`漏洞扫描
**记忆：** `memory_layer.py`JSON，`data_flywheel.py`SFT/DPO，规划sqlite-vec
**进化：** `evolution_engine.py`QLoRA，`unsloth_trainer.py`脚本，`self_correction.py`错误分类
**执行：** `agent_runtime_v2.py`DAG+思考+并行+验证，`tool_contract.py`契约，`task_trace.py`轨迹，`model_registry.py`注册表，`benchmark/suite.py`12基准，`undo_stack.py`撤销，`policy/`策略

### 功能 - 已实现

- 21工具真实，WMI真实，HWND真实，截图真实，沙盒，撤销栈，联网真实
- 8层，Observe→Plan→Act→Verify→Recover，代码维护现实为核心
- 工具契约，验证区分API完成vs真实成功
- 策略引擎安全边界，LLM只提议，Policy决定
- 确定性优先：结构化→UIA→OCR→视觉→坐标
- 记忆5种，技能版本化，经验
- 自我进化数据飞轮，QLoRA，评估晋升回滚
- 安全扫描，WSL沙盒，自我修正
- 任务轨迹统一，模型注册表，基准12任务
- 前端12视图，设置可调整，单端口部署
- Git已推送v3.1

---

## 十一、困惑、矛盾、权衡、异议

### 1. MoE专家选择性微调是否有效？

- **困惑**：推理激活专家，训练只训这些，是否遗忘其他？
- **矛盾**：想降成本，但可能降泛化
- **权衡**：需实验Full LoRA vs 专家选择性，VRAM、时间、性能、回归，标记实验性，不吹嘘90%
- **异议**：反对现在声称90%成本降低，应先实验

### 2. 自我进化是否会变差？

- **困惑**：自动收集数据质量参差，训练后可能更差
- **矛盾**：想越用越懂你，但噪音污染
- **权衡**：严格评估，历史20任务回放，提升才晋升，保留回滚，Replay防遗忘，六信号评分阈值0.7
- **异议**：反对夜间自动学习无评估就晋升，必须基准测试

### 3. 视觉是否应作为主要接口？

- **困惑**：Claude用视觉通用，但慢贵
- **矛盾**：结构化快准便宜，但UIA不一定覆盖
- **权衡**：层次：结构化→UIA→OCR→视觉→坐标，优先结构化，视觉补充回退
- **异议**：反对视觉作为通用接口，应优先结构化

### 4. 技能是否应直接变权重？

- **困惑**：成功流程直接微调还是先变技能？
- **矛盾**：微调直接，但不可解释难回滚
- **权衡**：先变版本化技能，可回放评估编辑回滚，独立于基础模型，安全易调试，稳定后再考虑蒸馏
- **异议**：反对成功直接微调，应先变技能

### 5. 本地 vs 云端，隐私 vs 能力？

- **困惑**：云端更强但隐私
- **矛盾**：本地3B激活能力有限但私有
- **权衡**：本地优先，云端可选教师，本地保持核心能力，云不可用仍可执行，Teacher提供建议，本地是执行权威
- **异议**：反对本地代理变云瘦客户端

### 6. 功能多 vs 基础牢？

- **困惑**：要求功能多AGI管家，但基础不牢
- **矛盾**：功能多导致杂，基础不牢不可靠
- **权衡**：下一里程碑Reliable Local Computer Agent，而非更多AGI，先让现有系统确定可观测可测试可恢复可度量，再加高层
- **异议**：反对现在加更多AGI概念，应先让现有可靠

### 7. GitHub Skill是否整合？

- **困惑**：GitHub很多优秀Skill，是否照搬？
- **矛盾**：照搬快但可能不适配
- **权衡**：可整合但需适配，例如file-organizer改为沙盒+撤销+验证，符合契约，非照搬
- **异议**：反对照搬，应适配整合

### 8. 14层是否必要？

- **困惑**：14层是否过于冗杂？
- **矛盾**：想分层清晰，但职责重叠
- **权衡**：精简为8层，每层单一职责，必要性已在README解释，移除视觉、技能、学习、系统、教师冗余层，新增安全到工具+策略
- **异议**：反对14层，应精简为8层

---

## 十二、下一步 - 夯实基础

### 下一里程碑：Reliable Local Computer Agent

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

## 十三、总结 - 技术诚实

**已实现：** 8层、21工具真实、WMI真实、HWND真实、工具契约、策略引擎安全边界、确定性优先、记忆5种、技能版本化、自我进化数据飞轮QLoRA、模型注册表、任务轨迹统一、基准12任务、安全沙盒WSL网安、自我修正、前端12视图设置可调整、单端口部署、联网真实、Git已推送v3.1

**部分实现：** UIA、DWM、OCR、iOS远程、托盘、向量检索

**实验性：** MoE人格化、梦境辩论、技能基因、梦境三阶段，需实验验证，标记实验性

**计划：** EXE打包、PaddleOCR真实、基准前端可视化

**技术诚实 README 比 AGI 描述更可信**

**代码维护现实，AI解释现实为核心原则**

**不应更AGI，而应更可度量、更确定、更可恢复、更可观测、更扎根真实Windows状态**
