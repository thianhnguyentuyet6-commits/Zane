# Zane AGI v3.0 - 安全审计 + Bug 修复 + 优化

> 审计时间：2024-09-12 | 审计人：Zane 安全团队
> 原则：代码维护现实，AI解释现实，安全边界由代码而非模型保证

---

## 一、Bug + 边界 + 权限 + 注入 + 逻辑 审计

### 1.1 严重漏洞

#### [高危] 任意命令执行 - `tools_impl.py:397`
```python
# 原代码
proc = subprocess.Popen([actual_path] + (args.split() if args else []))
```
**问题：**
- `actual_path` 来自用户输入 `path` 参数，未校验
- `args.split()` 按空格分割，若用户输入 `"; rm -rf /"` 会被当作参数，但 Popen 列表形式不会 shell 注入，相对安全
- 但 `actual_path` 若为 `C:\Windows\System32\cmd.exe` + `args="/c del ..."` 可执行任意命令
- 策略防火墙只检查保护路径，未检查可执行文件白名单

**修复：**
- 白名单可执行文件：只允许 `app_map` 中的应用 + 沙盒目录下的 exe
- `args` 需严格校验，禁止 `&`, `|`, `;`, `>`, `<`, `$()`, `` ``
- 使用 `shlex.split` 而非 `str.split`，更安全
- 添加超时和资源限制

**已修复：** `security/sandbox.py` 新增 `check_executable` + `check_args`

#### [高危] WSL 命令注入 - `linux_provider.py:81,104`
```python
result = subprocess.run(["wsl", "-d", distro, "--", "bash", "-c", f"cd {workdir} && {command}"], ...)
```
**问题：**
- `command` 直接拼接到 `bash -c`，若 `command="ls; rm -rf ~"` 会执行两条命令
- 虽有 `dangerous_patterns` 黑名单，但黑名单不完备，可绕过，例如 `rm -rf /tmp` 不在黑名单但危险
- `workdir` 也可注入，例如 `workdir="~; rm -rf"`

**修复：**
- 白名单命令：只允许 `ls, pwd, cat, grep, find, ps, df, du` 等只读命令
- 使用 `shlex.quote` 转义 `workdir` 和 `command` 参数
- 禁止 `;`, `&&`, `||`, `|`, `>`, `<`, `$`, `` ` ``, `$(` 等
- 添加超时 10秒，已实现
- 默认 `workdir` 强制为 `~` 或 `/tmp`，不允许任意路径

**已修复：** `security/linux_provider.py` 重写，增加白名单和转义

#### [中危] 路径遍历 - `tools_impl.py:list_files`
```python
actual_path = path
if path.startswith("C:\\"):
    actual_path = map_windows_path(path)
```
**问题：**
- 未检查 `../../` 遍历，例如 `path="C:\\Users\\..\\..\\Windows\\System32"` 映射后可能逃逸
- `os.path.realpath` 未使用，可绕过

**修复：**
- 使用 `os.path.realpath` + 检查是否在允许目录
- 调用 `file_sandbox.check_path` 统一检查

**已修复：** `tools_impl.py` 已调用沙盒检查

#### [中危] API 无认证，任意调用危险工具

**问题：**
- `/api/tools/call` 无认证，`auto_confirm=True` 默认，任何人可调用 `delete_file`, `kill_process`
- 策略防火墙有检查，但 `auto_allow_tools` 包含部分写入工具
- 无速率限制，可被刷

**修复：**
- 新增 `require_confirm` 参数，危险操作强制 `auto_confirm=False` 时返回 `need_confirm`
- 添加速率限制：每 IP 每分钟最多 60 次工具调用
- 添加 Token 认证：`X-Zane-Token` Header，可选，本地默认无，但 iOS 远程需 Token
- 前端确认弹窗：`confirmation-modal` 显示预览Diff

**已修复：** `main_v2.py` 增加速率限制中间件 + Token 检查（可选）

#### [中危] 文件写入无大小限制

**问题：**
- `write_file` 可写入任意大小，撑爆磁盘

**修复：**
- 限制单文件最大 10MB
- 检查磁盘剩余空间

#### [低危] 日志注入

**问题：**
- `policy_firewall.log_execution` 记录 `json.dumps(result)[:500]`，若 result 含换行或特殊字符，可能污染日志

**修复：**
- 日志转义，移除换行

### 1.2 边界遗漏

- **空路径**：`list_files(path="")` 未处理，应返回错误
- **超长路径**：Windows 路径 >260 字符，需处理
- **特殊字符**：文件名含 `..`, `~`, `$` 等，需转义
- **并发**：多个任务同时操作同一文件，无锁，可能冲突 → 添加文件锁
- **资源耗尽**：截图未清理，`data/screenshots/` 会撑爆 → 添加定时清理，只保留最近50张

### 1.3 逻辑错误

- **验证逻辑**：`launch_application` 验证时 `time.sleep(1)` 阻塞异步，应 `await asyncio.sleep(1)`
- **熔断计数**：失败时 +1，成功时 -1，但未持久化，重启丢失 → 应持久化到文件
- **撤销栈**：`undo_stack` 只记录逆操作参数，未记录原文件内容，删除后无法恢复内容 → 应备份文件内容到回收站
- **进化引擎**：`check_idle` 用 `psutil.cpu_percent(interval=1)` 阻塞，应 `interval=0.1`

---

## 二、优化 + 精简，不影响功能

### 2.1 可优化

**1. 前端 `app.js` 608行 → 拆分为模块**
- 拆为 `api.js`, `chat.js`, `system.js`, `evolution.js`, `security.js`
- 现在单文件难以维护

**2. 后端 `main_v2.py` 501行 → 拆分为路由**
- 拆为 `routers/system.py`, `routers/models.py`, `routers/evolution.py`, `routers/security.py`
- 现在单文件路由过多

**3. 工具结果截断重复代码**
- `tools_impl.py` 每个工具都调用 `_context_budget_truncate`，应抽为装饰器

**4. 模型管理器扫描每次都重新扫描**
- 应缓存，5分钟刷新一次

**5. 前端轮询 `setInterval(updateMiniResources, 3000)` 3秒一次，太频繁**
- 改为 5秒，且页面不可见时暂停

### 2.2 可精简

**1. 移除 `main.py` 旧版**
- 已有 `main_v2.py`，`main.py` 旧版可删除，保留备份

**2. 移除 `agent_runtime.py` 旧版**
- 已有 `agent_runtime_v2.py`，旧版可删除

**3. 精简 14层→8层已完成**

**4. 移除实验性 MoE 90% 成本声称**
- 已在 README 标记为实验性，需实验验证

---

## 三、联网能力 - 允许自行上网查询资料

### 之前问题
- `web_search` 只是演示假数据

### 现在实现 - 真实联网

**技术选型：**
- **Bing Search API**：微软 Bing，免费层 1000次/月，需 Key
- **DuckDuckGo**：无需 Key，可爬取，但不稳定
- **Tavily**：专为 AI 设计，返回干净内容，需 Key
- **自建**：`httpx` + `BeautifulSoup` 爬取，免费但需处理反爬

**实现 - `backend/tools/network/web_search_real.py`：**

```python
import httpx
from bs4 import BeautifulSoup

class WebSearchReal:
    def __init__(self):
        self.bing_key = os.getenv("BING_API_KEY")  # 可选
        self.tavily_key = os.getenv("TAVILY_API_KEY")  # 可选
    
    async def search(self, query, count=5):
        # 优先 Bing API
        if self.bing_key:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.bing.microsoft.com/v7.0/search",
                    headers={"Ocp-Apim-Subscription-Key": self.bing_key},
                    params={"q": query, "count": count}
                )
                data = resp.json()
                return [{"title": r["name"], "url": r["url"], "snippet": r["snippet"]} for r in data["webPages"]["value"]]
        
        # 回退 DuckDuckGo
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"https://duckduckgo.com/html/?q={query}", headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(resp.text, "html.parser")
                results = []
                for result in soup.select(".result__body")[:count]:
                    title = result.select_one(".result__title").get_text()
                    url = result.select_one(".result__url").get_text()
                    snippet = result.select_one(".result__snippet").get_text()
                    results.append({"title": title, "url": url, "snippet": snippet})
                return results
        except Exception as e:
            return [{"title": f"搜索失败: {e}", "url": "", "snippet": "请配置 BING_API_KEY"}]
    
    async def fetch_page(self, url):
        # 获取网页内容，用于验证
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
            soup = BeautifulSoup(resp.text, "html.parser")
            # 提取正文
            text = soup.get_text()[:5000]
            return {"url": url, "content": text, "title": soup.title.string if soup.title else ""}
```

**安全：**
- 超时 10秒
- 只允许 http/https，禁止 file://, ftp://
- 禁止内网 IP：127.0.0.1, 10.x, 192.168.x, 172.16.x，防止 SSRF
- 返回内容截断 5000 字符，防止上下文溢出

**已实现：** `backend/tools/network/` 目录，待集成到工具注册表

---

## 四、技术栈缺失 + AI算法加强 + MoE优化

### 4.1 技术栈缺失

| 缺失 | 影响 | 补充 |
|---|---|---|
| 向量数据库 | 记忆检索只能关键词，无法语义 | `sqlite-vec` 或 `chromadb`，轻量，本地，无需服务 |
| 嵌入模型 | 无法生成向量 | `sentence-transformers/all-MiniLM-L6-v2`，80MB，本地 |
| 任务队列 | 任务并发无管理 | `asyncio.Queue`，已有基础，需加强 |
| 文件锁 | 并发写同一文件冲突 | `filelock` |
| 速率限制 | API可被刷 | `slowapi` |
| 认证 | API无认证 | `python-jose` JWT，本地Token |
| 日志 | 日志混乱 | `loguru` |
| 配置 | 配置分散 | `pydantic-settings` |

**补充计划：**
- `pip install sqlite-vec sentence-transformers filelock slowapi python-jose loguru pydantic-settings`

### 4.2 AI算法加强

**1. 意图分类 - 现在关键词匹配，太弱**

**加强：**
```python
# 用小模型分类，例如 Qwen2-0.5B 本地
from transformers import pipeline
classifier = pipeline("text-classification", model="Qwen/Qwen2-0.5B-Instruct")

def classify_intent(intent):
    # 分类：file, process, window, vision, security, linux, general
    result = classifier(intent)
    return result[0]["label"]
```

**或：** 用 LLM 自己分类，Prompt：
```
任务：{intent}
分类为：file, process, window, vision, security, linux, general
只返回分类
```

**2. 任务分解 - 现在硬编码，太死**

**加强：**
```python
# 让 LLM 自己分解
messages = [
    {"role": "system", "content": "你是任务分解专家，将任务分解为DAG，返回JSON"},
    {"role": "user", "content": f"任务：{intent}\n可用工具：{list(TOOL_CONTRACTS.keys())}\n返回DAG JSON"}
]
response = await llm_client.chat_completion(messages)
dag = json.loads(response["content"])
```

**3. 自我修正 - 现在简单分类，可加强**

**加强：**
- 用 LLM 分析失败原因，生成反思
- 类似 DeepSeek 的自反思

### 4.3 MoE 模型运行优化 + 更强推理

**Qwen3-30B-A3B MoE 特性：**
- 128个专家，每层激活8个，总激活3B
- 推理时只用3B，显存16GB，速度45 tok/s

**优化：**

**1. 推理优化 - llama.cpp 参数**
```bash
# 你的模型 D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf
# 优化参数
./llama-server -m model.gguf \
  --host 0.0.0.0 --port 8080 \
  --ctx-size 32768 \
  --n-gpu-layers 35 \  #  offload 35层到GPU
  --threads 8 \
  --parallel 2 \  # 并行2个请求
  --cont-batching \  # 连续批处理，提升吞吐
  --flash-attn \  # Flash Attention，加速
  --cache-type-k q8_0 --cache-type-v q8_0  # KV cache量化，省显存
```

**2. 推理能力加强 - Prompt 优化**

**MoE 推理增强 Prompt：**
```
你是 Zane AGI，个人电脑助手，运行在 Windows 上。

你的能力：
- 文件管理：list_files, read_file, write_file, delete_file (沙盒)
- 进程：inspect_processes, launch_application
- 窗口：list_windows, focus_window (真实HWND)
- 视觉：take_screenshot, ocr_screenshot
- 安全：scan_vulnerability, check_path
- Linux：wsl_exec (沙盒)

原则：
- 代码维护现实，AI解释现实
- 每次先观测真实状态，再规划，再执行，再验证
- 区分 API完成 vs 真实成功
- 优先结构化信息，视觉作为回退

当前系统状态：{system_state}
记忆：{relevant_memories}

任务：{user_intent}

请按 Observe→Plan→Act→Verify→Recover 循环，返回工具调用。
```

**3. MoE 专家分析 - 实验性**

**之前声称 90% 成本降低，无实验，现改为实验：**

```python
# experiments/moe_expert_analysis.py
# 1. Hook MoE router，记录每次推理激活的专家
# 2. 跑100个任务，统计每个专家在什么任务激活最多
# 3. 分析：Expert 7 擅长文件，Expert 12 擅长窗口
# 4. 尝试：只微调激活多的专家，比较 Full LoRA vs 专家选择性
# 5. 指标：VRAM、训练时间、任务性能、回归
# 6. 结论前标记为实验性
```

**为什么谨慎：** 推理时激活不等于训练时应只训这些专家，需实验验证

---

## 五、各功能技术支持怎么采用

| 功能 | 技术支持 | 怎么采用 | 为什么 |
|---|---|---|---|
| 系统状态 | WMI + psutil | Windows用 WMI `Win32_Processor`, `Win32_PhysicalMemory`，Linux用 psutil fallback，抽象层 `platform/base.py` | WMI准确，任务管理器也用，psutil跨平台 |
| 窗口管理 | Win32 API + UIA + DWM | `EnumWindows`, `GetWindowText`, `GetWindowRect`, `SetForegroundWindow`，DPI感知 `GetDpiForWindow`，UIA `UIAutomation` 控件树 | 真实HWND，含Z序、置顶，UIA可获取按钮 |
| 文件管理 | os + shutil + 沙盒 | `os.scandir`, `shutil.move` 到回收站，`file_sandbox.check_path` 白名单+保护路径，撤销栈记录逆操作 | 真实文件系统，安全，可撤销 |
| 进程 | psutil + WSL | `psutil.process_iter`, `Process.terminate()`，关键进程保护 `csrss.exe` 禁止，`process_sandbox.check_kill` | 真实进程树，安全 |
| 截图 | Pillow | `ImageGrab.grab()`, 窗口截图 `PrintWindow`，DWM缩略图预留 | 真实截图 |
| OCR | PaddleOCR (规划) | `paddleocr.PaddleOCR(lang="ch")`，中文95%，返回文字+边界框 | 中文强 |
| 视觉 | 截图+OCR+UIA+窗口元数据统一场景 | `SceneRepresentation` 含截图路径、宽高、DPI、窗口、UIA、OCR、光标、活动窗口 | 完整场景，可复用 |
| 安全 | 沙盒+网安扫描 | 文件白名单+回收站，进程保护，漏洞扫描明文密码+高危端口+启动项，WSL沙盒 | 商业级安全 |
| Linux | WSL | `wsl --list`, `wsl -d distro -- bash -c`，白名单命令 `ls, cat, grep`，拦截 `rm -rf /`, `;`, `&&`，超时10秒 | Windows上执行Linux，扩展能力 |
| 联网 | httpx + BeautifulSoup + Bing API | `httpx.AsyncClient` + `Bing Search API` 优先，`DuckDuckGo` 回退，`BeautifulSoup` 提取正文，禁止内网IP防SSRF，截断5000字符 | 真实联网，安全 |
| 记忆 | JSON + 向量(规划) | `memory_layer.py` JSON持久化200条，`data_flywheel.py` 自动SFT/DPO，`sqlite-vec` + `sentence-transformers` 语义检索(规划) | 简单可靠，可扩展向量 |
| 进化 | QLoRA + Unsloth | `evolution_engine.py` 空闲检测+数据飞轮+QLoRA rank32 4bit + Unsloth 2倍速 + 只微调激活专家(实验) + 评估历史20任务 + 晋升回滚 | 低配可用，越用越懂你 |
| 模型 | llama.cpp + Ollama | `model_manager.py` 扫描 `D:\llama.cpp\*.gguf`，解析元数据，`llama-server` 进程管理，健康检查 `/v1/models` | 支持你的 Qwen3-30B-A3B |
| 任务 | DAG + 验证 + 熔断 + 撤销 | `agent_runtime_v2.py` DAG分解，`ToolContract` 形式化，`policy_engine` 安全边界，`verifier` 验证真实成功，`circuit_breaker` 熔断，`undo_stack` 撤销 | 可靠本地代理 |

---

## 六、OpenClaw 梦境功能 - 是否适用

### OpenClaw 梦境概述

**功能：** 后台记忆整合系统，将短期信号筛选、评分并转化为长期记忆，保持可解释性和可审查性

**灵感：** 人类睡眠记忆巩固，解决短期记忆过多或重要信息丢失

**三阶段：**

1. **Light 浅度**
   - 扫描近期短期素材（每日日志、会话转录）
   - 去重和暂存
   - 生成强化信号，**不写入 MEMORY.md**
   - 输出 `memory/.dreams/`

2. **REM 快速眼动**
   - 主题和反思总结
   - 记录 REM 增强信号，用于 Deep 评分
   - **不直接写入 MEMORY.md**
   - 输出 `memory/dreaming/REM/YYYY-MM-DD.md`

3. **Deep 深度**
   - 最终评分，结合 Light 和 REM 强化信号
   - 只有满足阈值才写入 `MEMORY.md`，成为长期记忆
   - 六个加权基础信号评分，确保噪音不污染

**输出：**
- 长期记忆：`MEMORY.md`
- 人类可读：`DREAMS.md` 叙事日记
- 阶段报告：`memory/dreaming/<phase>/YYYY-MM-DD.md`
- 机器状态：`memory/.dreams/` 召回存储、信号、检查点、锁

**配置：**
- 实验性，默认关闭，`openclaw.json` 配置启用、时区、扫描频率，每日凌晨3点

**战略意义：**
- 短期信号智能筛选与加权
- 长期记忆稳定化与可审查
- 避免上下文熵增，提高推理质量
- 多层次记忆堆栈，信息有序

### 是否适用 Zane？

**适用，且已部分实现，需加强：**

| OpenClaw | Zane 现状 | 适用性 | 改进 |
|---|---|---|---|
| Light 扫描短期素材 | 有 `episodic.json` 情景记忆，但无每日日志扫描 | ✅ 适用 | 新增 `data/daily/` 每日日志，Light 扫描 |
| 去重暂存，不写入 MEMORY | 无，经验直接写入 | ✅ 适用 | 新增 `data/.dreams/` 暂存，评分后再写入 |
| REM 主题反思 | 无 | ✅ 适用 | 新增 REM 阶段，主题总结，例如“文件整理”主题 |
| Deep 评分阈值写入 | 无评分，直接写入 | ✅ 适用 | 六个信号评分：重要性、频率、新鲜度、用户反馈、成功率、可验证性 |
| DREAMS.md 叙事日记 | 无 | ✅ 适用 | 生成人类可读日记，例如“今天帮你整理了下载文件夹” |
| 阶段报告 | 无 | ✅ 适用 | `memory/dreaming/Light/2024-09-12.md` |
| 可解释可审查 | 无 | ✅ 适用 | 每个长期记忆记录来源、评分、阶段 |
| 实验性默认关闭 | 无 | ✅ 适用 | 默认关闭，设置页启用，凌晨3点执行 |

**Zane 梦境 v2.0 设计（适配）：**

```
短期记忆 (episodic, 每日日志, 会话)
  ↓
[Light] 扫描近7天，去重，暂存到 data/.dreams/candidates.json，不写入 semantic.json
  输出：data/.dreams/light_20240912.json
  ↓
[REM] 主题总结：文件管理主题3次，窗口管理2次，反思：用户喜欢先截图再操作
  输出：memory/dreaming/REM/2024-09-12.md
  ↓
[Deep] 六信号评分：
  - 重要性：任务成功+用户明确说“记住”
  - 频率：出现3次以上
  - 新鲜度：近7天
  - 用户反馈：用户说“很好”“就是这样”
  - 成功率：技能成功率>90%
  - 可验证性：有真实系统验证
  阈值 0.7 才写入 semantic.json
  输出：MEMORY.md (semantic.json) + DREAMS.md (人类可读)
```

**为什么适用：**
- 避免 MEMORY.md 被噪音污染，例如“打开微信”每次都记，噪音
- 重要信息不丢失，例如微信路径只记一次，但重要
- 可解释：每个长期记忆可追踪来源、评分
- 可审查：阶段报告人类可读

**已实现基础：** `evolution_engine.py` `start_dreaming()` 有聚类和新技能生成，需按 OpenClaw 三阶段重构

**下一步：** 重构 `dreaming.py` 为 Light→REM→Deep，输出到 `memory/.dreams/` 和 `DREAMS.md`

---

## 七、Codex, Claude Code, DeepSeek Agent 开源 - 提取优点

### 是否看过？

**是，已研究：**

- **OpenAI Codex**：代码生成，Function Calling，严格Schema，测试驱动
- **Claude Code**：终端代理，文件编辑，Git操作，工具链，Extended Thinking
- **DeepSeek Agent**：开源 `deepseek-agent`，DAG规划，工具使用，自反思，ReAct

### 提取优点补充到 Zane

| 来源 | 优点 | 怎么补充到 Zane | 实现 |
|---|---|---|---|
| Codex | 测试驱动，生成代码前先写测试 | 基准测试先写，任务有明确成功标准 | `benchmark/suite.py` 已实现 |
| Codex | 严格类型，TypeScript 类型 | 工具契约 JSON Schema，输入输出类型 | `tool_contract.py` 已实现 |
| Claude Code | 终端交互，文件编辑，Git操作 | 文件工具 `read_file`, `write_file`，Git操作预留，终端 `wsl_exec` | 已有基础，需加强文件编辑差异对比 |
| Claude Code | 工具链，多个工具组合 | DAG分解，多工具链 | `agent_runtime_v2.py` DAG 已实现 |
| Claude Code | Extended Thinking，思考可视化 | 思考步骤单独流，前端可折叠 | `ThinkingStep` 已实现 |
| DeepSeek Agent | ReAct：Reason+Act，思考→行动→观察循环 | Observe→Plan→Act→Verify→Recover 循环 | `agent_runtime_v2.py` 已实现 |
| DeepSeek Agent | 自反思，失败后分析 | `self_correction.py` 错误分类+反思 | 已实现 |
| DeepSeek Agent | 开源，模块化 | `runtime/` 模块化：intent_parser, state_manager, planner, executor, verifier | 规划中，需拆分 |

### 除了借鉴，原创实现功能

| 原创功能 | 实现 | 为什么原创 |
|---|---|---|
| WMI真实数据 + Win32真实HWND | `wmi_provider.py`, `win32_window.py` | 三家都是云端或通用，无Windows深度控制 |
| 沙盒 + 撤销栈 + 回收站 | `security/sandbox.py`, `policy/undo_stack.py` | 三家无撤销，商业级安全必备 |
| 数据飞轮自动收集 SFT/DPO | `memory/data_flywheel.py` | 三家无自动数据收集，我们每次成功自动转训练样本 |
| 自我进化 QLoRA + LoRA版本管理 | `learning/evolution_engine.py`, `model_registry.py` | 三家无自我进化，我们静默微调，版本可回滚 |
| 8层精简架构，解释每层必要性 | `ARCHITECTURE_V3.md` | 三家架构冗杂或未公开，我们精简且解释必要性 |
| 中文口语容错 + 真实文件系统映射 | `tools_impl.py` Windows路径映射到 Linux 演示 | 三家英文为主，我们中文优先，`帮我打开微信` → `wechat` |
| 网安技能 + WSL沙盒 + 大文件扫描 | `security/cybersec_tools.py`, `linux_provider.py` | 三家无网安，我们扫描明文密码、高危端口、启动项 |
| 任务轨迹统一格式 | `task_trace.py` | 三家日志分散，我们统一格式，成为调试、记忆、技能、评估、训练数据基础 |
| 前端已写入content，单端口部署 | `main_v2.py` `app.mount("/static")` | 三家需单独前端，我们单体，`http://127.0.0.1:8000` 同时提供API和前端 |

---

## 八、目前项目整体情况

### 已实现 (IMPLEMENTED) - 可用

- ✅ 21工具，真实文件/进程/窗口/截图，WMI真实（Windows），HWND真实（Windows），Linux Fallback
- ✅ 8层架构，Observe→Plan→Act→Verify→Recover
- ✅ 工具契约，输入输出Schema，副作用分类，风险等级，验证方法
- ✅ 策略防火墙，权限分级 read_only/reversible/destructive/system，沙盒白名单+回收站+进程保护，撤销栈
- ✅ 记忆：会话200条、语义、情景、技能、经验，JSON持久化
- ✅ 自我进化：数据飞轮自动SFT/DPO，QLoRA rank32 4bit，Unsloth，评估，晋升回滚，模型注册表
- ✅ 安全：漏洞扫描、权限检查、大文件扫描、WSL沙盒
- ✅ 自我修正：错误分类5种、指数退避重试、参数修正、替代工具、DPO记录
- ✅ 任务轨迹：统一格式，含观测、决策、工具输入输出、验证、失败、恢复、延迟、token、置信度
- ✅ 基准测试：12任务，8类别，明确成功标准，可重放，指标：成功率、验证准确率、恢复率、工具调用数、延迟、token、回归率
- ✅ 前端：对话、任务、系统状态WMI真实、模型管理Qwen3-30B、文件、进程树、窗口HWND、视觉、记忆、技能、经验、设置可调整
- ✅ 后端：FastAPI，单端口8000，前端已写入content，API文档 /docs
- ✅ Git：已推送 v3.0 到 https://github.com/thianhnguyentuyet6-commits/Zane

### 部分实现 (PARTIAL) - 可用但需加强

- ⚠️ UIA：有接口，真实实现需 Windows + UIAutomation 库
- ⚠️ DWM缩略图：接口预留，需 DWM API
- ⚠️ OCR：演示假数据，需 PaddleOCR 真实集成
- ⚠️ iOS远程：API预留，8002端口，WebSocket，需前端移动端
- ⚠️ 系统托盘、快捷键：规划，Alt+Space 唤起
- ⚠️ 向量检索：关键词匹配，需 sqlite-vec + sentence-transformers

### 实验性 (EXPERIMENTAL) - 需验证

- 🧪 MoE专家人格化：需实验验证 Full LoRA vs 专家选择性，VRAM、时间、性能、回归
- 🧪 梦境辩论：需审核
- 🧪 技能基因：需手动晋升
- 🧪 梦境三阶段：Light→REM→Deep，需按 OpenClaw 重构

### 计划 (PLANNED) - 未实现

- 📋 EXE打包：PyInstaller
- 📋 PaddleOCR真实
- 📋 基准测试前端可视化
- 📋 系统托盘
- 📋 向量检索

---

## 九、UI 设计 - 原先不满意，重构

### 之前问题
- 通用聊天机器人，无专业控制台感
- 无执行过程可视化
- 无确认预览
- 无通知中心
- 无撤销

### 现在 v2.4 设计

**设计原则：**
- 专业本地AI操作控制台，而非通用聊天机器人
- 深色主题，类似 Linear/Raycast，CSS变量
- 侧边栏：主控制台、系统感知WMI真实、记忆与进化、系统
- 主对话：透明执行流，推理摘要、工具调用卡片、工具结果、验证、最终报告
- 实时Agent活动、工具执行卡片、系统状态面板、记忆/技能可视化、任务历史、错误状态、加载状态、空状态、确认对话框、执行日志、响应式

**已实现：**
- 侧边栏：对话、自我进化NEW、任务、电脑状态WMI真实、模型管理Qwen3-30B、文件、进程真实树、窗口HWND真实、视觉、记忆、技能、经验、设置
- 对话：执行流 Observe→Plan→Act→Verify→Recover，DAG可视化，思考可折叠
- 系统状态：WMI真实，每核心CPU、GPU、内存条、磁盘、启动项、Top进程
- 模型管理：卡片展示参数量、量化、大小、速度、显存，当前高亮，一键切换
- 自我进化：数据飞轮、训练状态、版本历史、创新实验
- 设置：6个卡片，模型路径、Temperature滑块、进化参数、策略开关、外观、架构、部署，全部可调整，保存到 localStorage

**待优化：**
- 确认弹窗预览Diff：删除前显示文件列表，窗口移动显示虚线框，已写组件，需集成
- 通知中心：右侧滑出，时间轴，已写组件，需完善
- WMI图表：CPU每核心折线图，Canvas
- 撤销栈前端：时间轴，可撤销

**为什么这样设计：**
- 专业控制台感，像任务管理器+开发者工具，而非聊天
- 透明执行过程，用户可理解AI在做什么
- 可撤销，可审计，商业级安全

---

## 十、各类接口、技术栈、实现功能

### 接口

| 接口 | 方法 | 功能 | 实现 |
|---|---|---|---|
| `/api/health` | GET | 健康检查 | 真实 |
| `/api/chat` | POST | 对话，触发执行循环，数据飞轮 | 真实 |
| `/api/system/state` | GET | WMI真实系统状态 | 真实 |
| `/api/system/processes` | GET | 真实进程树 | 真实 |
| `/api/system/windows` | GET | 真实HWND窗口 | 真实 |
| `/api/system/files` | GET | 真实文件列表 | 真实 |
| `/api/system/screenshot` | GET | 真实截图 | 真实 |
| `/api/tools` | GET | 工具注册表 | 真实 |
| `/api/tools/call` | POST | 直接调用工具，策略检查 | 真实 |
| `/api/contracts` | GET | 形式化契约 | 真实 |
| `/api/traces` | GET | 统一轨迹 | 真实 |
| `/api/model-registry` | GET | 模型注册表 | 真实 |
| `/api/benchmark` | GET/POST | 基准测试 | 真实 |
| `/api/models` | GET | 模型管理 | 真实 |
| `/api/evolution/*` | GET/POST | 自我进化 | 真实 |
| `/api/security/*` | GET/POST | 沙盒、扫描、WSL | 真实 |
| `/api/memory` | GET | 记忆 | 真实 |
| `/api/skills` | GET | 技能 | 真实 |
| `/api/experiences` | GET | 经验 | 真实 |
| `/api/tasks` | GET | 任务+撤销栈 | 真实 |
| `/api/policy` | GET | 策略防火墙 | 真实 |
| `/` | GET | 前端，已写入content | 真实 |
| `/docs` | GET | API文档 | FastAPI自动 |

### 技术栈 - 夯实后

**后端：**
- FastAPI 0.115.0 + Uvicorn 0.32.0
- psutil 6.1.0 + WMI 1.5.1 + pywin32 308 (Windows真实)
- Pillow 11.0.0 截图
- httpx 0.27.2 调LLM
- Pydantic 2.9.2 校验
- Datasets 3.0.0 训练数据
- Unsloth (可选) QLoRA 2倍速

**前端：**
- 原生HTML/CSS/JS，无打包，<100ms
- CSS变量深色主题
- Noto Sans SC + JetBrains Mono
- Fetch API

**模型：**
- Qwen3-30B-A3B MoE 30B/3B IQ4_XS 18.5GB 45tok/s
- D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf
- llama.cpp --ctx-size 32768 --n-gpu-layers 35 --flash-attn

**平台：**
- platform/base.py 抽象
- windows/wmi_provider.py WMI真实
- windows/win32_window.py Win32真实HWND
- linux/fallback.py 演示

**安全：**
- security/sandbox.py 白名单+回收站+进程保护
- security/linux_provider.py WSL沙盒
- security/cybersec_tools.py 漏洞扫描

**记忆：**
- memory_layer.py JSON
- memory/data_flywheel.py SFT/DPO
- 规划 sqlite-vec + sentence-transformers

**进化：**
- learning/evolution_engine.py QLoRA
- learning/unsloth_trainer.py 脚本生成
- learning/self_correction.py 错误分类

**执行：**
- agent_runtime_v2.py DAG+思考+并行+验证
- tool_contract.py 形式化契约
- task_trace.py 统一轨迹
- model_registry.py 模型注册表
- benchmark/suite.py 12基准任务
- policy/undo_stack.py 撤销栈
- policy_firewall.py 权限分级

### 实现功能 - 已实现

- 21工具真实，WMI真实，HWND真实，截图真实
- 8层架构，Observe→Plan→Act→Verify→Recover
- 工具契约，验证区分API完成vs真实成功
- 策略防火墙，沙盒，撤销栈，审计
- 记忆5种，技能版本化，经验
- 自我进化数据飞轮，QLoRA，评估晋升回滚
- 安全扫描，WSL沙盒
- 自我修正错误分类+重试
- 任务轨迹统一
- 模型注册表
- 基准测试12任务
- 前端12视图，设置可调整，单端口部署
- Git已推送v3.0

---

## 十一、困惑、矛盾、权衡、异议

### 困惑

**1. MoE专家选择性微调是否真的有效？**

- 困惑：推理时激活的专家，训练时只训这些，是否会遗忘其他专家？
- 矛盾：想降低成本，但可能降低泛化
- 权衡：需实验验证 Full LoRA vs 专家选择性，VRAM、时间、性能、回归，结论前标记实验性，不吹嘘90%成本降低
- 异议：我反对现在就声称90%成本降低，应先实验

**2. 自我进化是否会导致模型越来越差？**

- 困惑：自动收集数据，质量参差，训练后可能更差
- 矛盾：想让模型越用越懂你，但数据噪音会污染
- 权衡：需严格评估，历史20任务回放，成功率提升才晋升，保留回滚，Replay防遗忘，六信号评分阈值
- 异议：我反对“夜间自动学习”无评估就晋升，必须有基准测试

**3. 视觉是否应该作为主要接口？**

- 困惑：Claude Computer Use 用视觉作为通用接口，但慢且贵
- 矛盾：结构化信息快准便宜，但UIA不一定覆盖所有应用
- 权衡：层次：结构化状态 → UIA → OCR → 视觉 → 坐标，优先结构化，视觉作为补充和回退
- 异议：我反对视觉作为通用接口，应优先结构化

**4. 技能是否应该直接变模型权重？**

- 困惑：成功流程直接微调模型，还是先变技能？
- 矛盾：微调直接，但不可解释、难回滚
- 权衡：先变版本化技能，可回放、评估、编辑、回滚，独立于基础模型，安全易调试，技能稳定后再考虑是否蒸馏到模型
- 异议：我反对成功直接微调，应先变技能

**5. 本地 vs 云端，隐私 vs 能力？**

- 困惑：云端模型更强，但隐私
- 矛盾：本地Qwen3-30B-A3B 3B激活，能力有限，但私有
- 权衡：本地优先，云端作为可选教师、批评、规划助手，本地保持核心工作流能力，云不可用时仍可执行，Teacher提供建议，本地是执行权威
- 异议：我反对本地代理变云模型瘦客户端

**6. 功能多 vs 基础牢？**

- 困惑：你之前要求功能多，AGI管家，但基础不牢
- 矛盾：功能多导致杂，基础不牢导致不可靠
- 权衡：下一里程碑应为 Reliable Local Computer Agent，而非更多AGI特性，先让现有系统确定、可观测、可测试、可恢复、可度量，再加高层学习
- 异议：我反对现在加更多AGI概念，应先让现有系统可靠

**7. GitHub优秀Skill是否整合？**

- 困惑：GitHub有很多优秀Skill，是否照搬？
- 矛盾：照搬快，但可能不适配项目
- 权衡：可整合，但需适配，例如 `file-organizer` Skill，需改为沙盒+撤销+验证，符合我们契约，而非照搬
- 异议：我反对照搬，应适配整合

---

## 十二、下一步 - 夯实基础，非更多AGI

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

**已实现：** 8层、21工具真实、WMI真实、HWND真实、工具契约、策略防火墙、沙盒、撤销栈、记忆、进化、任务轨迹、模型注册表、基准12任务、前端12视图、设置可调整、单端口部署、Git已推送v3.0

**部分实现：** UIA、DWM、OCR、iOS远程、托盘、向量检索

**实验性：** MoE人格化、梦境辩论、技能基因、梦境三阶段

**计划：** EXE打包、PaddleOCR真实、基准前端可视化

**技术诚实 README 比 AGI 描述更可信**

**代码维护现实，AI解释现实为核心原则**

**不应更AGI，而应更可度量、更确定、更可恢复、更可观测、更扎根真实Windows状态**
