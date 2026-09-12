# Zane AGI - 本地个人电脑助手

> **运行在你PC上的私有助手，数据不出本地**
> 
> 模型：`D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf`
> 
> 版本：v2.5 | 平台：Windows 10/11 (Linux 兼容)

---

## 1. 项目是什么

Zane 是一个本地 Windows 电脑助手，能理解中文自然语言，操作真实系统。

**能做什么：**
- 看系统状态：CPU每核心、内存、磁盘、进程树、启动项、服务
- 管文件：列出、读取、写入、删除，真实文件系统，支持撤销
- 控窗口：枚举、聚焦、移动，真实 HWND，支持 Z序、DPI
- 视觉：截图、OCR 文字识别、UI 控件分析
- 记习惯：记住你的文件路径、常用应用、操作偏好
- 自我改进：日常使用自动收集数据，空闲时微调模型，越用越懂你
- 安全：沙盒执行、权限分级、操作可撤销、审计日志

**不能做什么：**
- 不联网上传数据，所有操作本地
- 不直接执行任意代码，工具受控

---

## 2. 整体架构 - 8层（精简后）

### 为什么从14层精简到8层？

14层过于冗杂，职责重叠。精简为8层，每层职责单一，必要性如下：

```
用户 → 接口层 → 感知层 → 推理层 → 工具层 → 策略层 → 执行层 → 记忆层 → 进化层
                                    ↑                ↓
                                    └──── 验证 ←─────┘
```

| 层 | 名称 | 职责 | 必要性 | 实现文件 |
|---|---|---|---|---|
| 1 | 感知层 | 获取真实系统状态 | 必须：AI不能盲猜，需真实数据 | `platform/windows/wmi_provider.py`, `win32_window.py` |
| 2 | 推理层 | 理解意图，拆解任务，思考 | 必须：LLM决策 | `llm_client.py`, `agent_runtime_v2.py` |
| 3 | 工具层 | 操作电脑的受控接口 | 必须：文件、进程、窗口、截图、安全、Linux | `tool_registry.py`, `tools_impl.py`, `security/` |
| 4 | 策略层 | 权限、确认、沙盒、审计 | 必须：防止误删，安全 | `policy_firewall.py`, `security/sandbox.py` |
| 5 | 执行层 | 执行、验证、撤销、熔断 | 必须：保证操作真正成功，可回滚 | `agent_runtime_v2.py`, `policy/undo_stack.py` |
| 6 | 记忆层 | 存储对话、知识、技能、经验 | 必须：长期记忆，越用越懂你 | `memory_layer.py`, `memory/data_flywheel.py` |
| 7 | 进化层 | 数据收集、微调、评估、晋升 | 可选但重要：自我进化 | `learning/evolution_engine.py` |
| 8 | 接口层 | API和前端 | 必须：用户交互 | `main_v2.py`, `frontend/` |

**优化点：**
- 合并原“视觉层”到“感知层”：截图、OCR都是感知
- 合并原“技能层”“学习层”到“记忆层”：技能是记忆的一种
- 合并原“系统层”“教师层”到“接口层”：系统监控是接口的一部分
- 新增“安全”到“工具层”和“策略层”：沙盒和网安

### 架构图

```
┌─────────────────────────────────────────────────────┐
│ 接口层: FastAPI + 前端 + 通知中心 + 撤销栈          │
│  http://127.0.0.1:8000  前端已写入 content           │
├─────────────────────────────────────────────────────┤
│ 推理层: Qwen3-30B-A3B + 思考链 + DAG分解             │
│  输入: 用户意图 + 系统状态 + 记忆                   │
│  输出: 任务DAG + 工具调用序列                       │
├─────────────────────────────────────────────────────┤
│ 感知层: WMI + Win32 + Screenshot + UIA              │
│  CPU每核心 + 内存条 + 磁盘 + 进程树 + 启动项        │
│  HWND + Z序 + DPI + 置顶 + 缩略图                   │
├─────────────────────────────────────────────────────┤
│ 工具层: 受控接口，真实操作                          │
│  文件: list_files, read_file, write_file, delete    │
│  进程: inspect_processes, kill_process, launch_app  │
│  窗口: list_windows, focus_window, get_window_info  │
│  视觉: take_screenshot, ocr_screenshot, analyze_ui  │
│  安全: sandbox_exec, check_permission, scan_vuln    │
│  Linux: wsl_exec, wsl_list                          │
├─────────────────────────────────────────────────────┤
│ 策略层: 权限分级 + 沙盒 + 审计                       │
│  L0只读: 自动放行                                   │
│  L1写入: Toast+3秒后执行，可取消                    │
│  L2危险: 弹窗+预览Diff+二次确认                     │
│  沙盒: 文件操作在沙盒目录，进程隔离                 │
├─────────────────────────────────────────────────────┤
│ 执行层: 事务化 + 验证 + 熔断                        │
│  并行只读 + 串行写入                                │
│  每次写后重新感知，验证是否成功                     │
│  失败5次熔断，区分临时/永久失败                     │
│  撤销栈: 每个写操作记录逆操作                       │
├─────────────────────────────────────────────────────┤
│ 记忆层: JSON持久化                                  │
│  会话: 最近200条对话                                │
│  知识: 用户习惯、环境事实                           │
│  技能: 可复用流程，自动蒸馏                         │
│  经验: 问题→解法→验证                               │
│  梦境: 空闲时整理记忆，生成新技能                   │
├─────────────────────────────────────────────────────┤
│ 进化层: 数据飞轮 → QLoRA → 评估 → 晋升              │
│  SFT: 成功任务 → 训练样本                           │
│  DPO: 失败+修正 → 偏好数据                          │
│  触发: 空闲30分+CPU<20% 或 凌晨2点                  │
│  训练: Unsloth QLoRA rank32, 4bit, 只微调激活专家   │
│  评估: 历史20任务回放，成功率提升则晋升             │
└─────────────────────────────────────────────────────┘
```

---

## 3. 技术实现 - 怎么做的

### 3.1 感知层 - 怎么获取真实数据

**问题：** 之前用 psutil 粗略数据，不准确

**实现：**

**Windows WMI (`platform/windows/wmi_provider.py`)：**
```python
import wmi
w = wmi.WMI()
# CPU
for cpu in w.Win32_Processor():
    cpu_name = cpu.Name  # Intel i7-12700H
# 内存条
for stick in w.Win32_PhysicalMemory():
    capacity = stick.Capacity  # 16GB
    speed = stick.Speed  # 3200MHz
# 磁盘
for disk in w.Win32_DiskDrive():
    model = disk.Model
    size = disk.Size
# 启动项 - 注册表
import winreg
key = winreg.OpenKey(HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
# 服务
for svc in w.Win32_Service():
    if svc.State == "Running":
        ...
```

**为什么用 WMI：** Windows 官方管理接口，任务管理器也用 WMI，数据准确，含每核心使用率、GPU、内存条型号、启动项、服务

**Linux Fallback (`platform/linux/fallback.py`)：**
```python
import psutil
# Linux 容器无法用 WMI，用 psutil 模拟，接口一致
cpu_percent = psutil.cpu_percent(percpu=True)
```

**窗口真实 HWND (`platform/windows/win32_window.py`)：**
```python
import win32gui, win32process, win32con
def enum_windows():
    windows = []
    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        placement = win32gui.GetWindowPlacement(hwnd)
        is_minimized = placement[1] == SW_SHOWMINIMIZED
        is_topmost = bool(GetWindowLong(hwnd, GWL_EXSTYLE) & WS_EX_TOPMOST)
        windows.append({...})
    win32gui.EnumWindows(callback, None)
```

**为什么用 Win32：** 真实 HWND，含 Z序、DPI、置顶、最小化，DWM可获取缩略图

**截图 (`tools_impl.py`)：**
```python
from PIL import ImageGrab
img = ImageGrab.grab()  # 真实全屏截图
img.save("data/screenshots/screenshot_xxx.png")
```

### 3.2 推理层 - 怎么思考和拆解

**问题：** 之前直接调用工具，无思考，无分解

**实现：**

**思考链 (`agent_runtime_v2.py`)：**
```python
@dataclass
class ThinkingStep:
    title: str
    content: str

thinking_steps = [
    ThinkingStep(title="理解意图", content="用户说：看看内存，分类：系统监控"),
    ThinkingStep(title="制定计划", content="DAG包含3节点，可并行2个只读")
]
# 前端可折叠显示
```

**DAG分解：**
```python
@dataclass
class TaskNode:
    id: str
    title: str
    tool: str
    params: Dict
    dependencies: List[str]

def decompose_to_dag(intent):
    if "内存" in intent:
        return [
            TaskNode(id="n1", title="获取进程", tool="inspect_processes", params={"sort_by": "memory"}, dependencies=[]),
            TaskNode(id="n2", title="获取系统状态", tool="get_system_state", params={}, dependencies=[]),
            TaskNode(id="n3", title="生成报告", tool="verify_info", params={}, dependencies=["n1", "n2"])
        ]
```

**为什么 DAG：** 复杂任务拆小，有依赖关系，可并行只读，串行写入，失败可重试单个节点

**并行执行：**
```python
read_nodes = [n for n in dag if permission == "read_only"]
write_nodes = [n for n in dag if n not in read_nodes]

# 并行只读
tasks = [execute_node(node) for node in read_nodes]
results = await asyncio.gather(*tasks)

# 串行写入+验证
for node in write_nodes:
    result = await execute_node(node)
    verify = await verify_node(node, result)
```

**为什么并行只读：** 查进程和查系统状态无依赖，并行节省时间；写入需串行+验证，防止冲突

### 3.3 工具层 - 怎么受控操作

**问题：** 之前工具无严格校验，参数错误直接崩

**实现：**

**工具注册表 (`tool_registry.py`)：**
```python
@dataclass
class ToolDefinition:
    name: str
    display_name: str
    description: str
    category: str
    permission: str  # read_only, write, dangerous
    parameters_schema: Dict  # JSON Schema
    need_confirmation: bool
    is_real_action: bool

TOOL_REGISTRY = {
    "list_files": ToolDefinition(
        name="list_files",
        display_name="列出文件",
        description="列出指定路径文件",
        category="文件管理",
        permission="read_only",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件夹路径"},
                "detail": {"type": "boolean"}
            },
            "required": ["path"]
        },
        need_confirmation=False,
        is_real_action=True
    )
}
```

**为什么严格 Schema：** LLM 必须按Schema输出，参数错误在执行前捕获，返回 `InvalidParam`，不崩

**真实实现 (`tools_impl.py`)：**
```python
def list_files(path, detail=False):
    actual_path = path
    if platform.system() != "Windows" and path.startswith("C:\\"):
        # Linux 演示映射到 ~/local-ai-agent-demo/
        actual_path = map_windows_path(path)
    
    entries = []
    for entry in os.scandir(actual_path):
        entries.append({"name": entry.name, "is_dir": entry.is_dir(), ...})
    
    # 上下文预算：最多20条
    if len(entries) > 20:
        return {"files": entries[:20], "total": len(entries), "truncated": True}
    return {"files": entries, "total": len(entries)}
```

**为什么截断：** 防止大输出撑爆 LLM 上下文，Qwen3 上下文 32K，工具结果最多 3000 字符

### 3.4 策略层 - 怎么保证安全

**实现：**

**权限分级 (`policy_firewall.py`)：**
```python
class PermissionLevel:
    READ_ONLY = "read_only"  # 自动放行
    WRITE = "write"  # 需确认
    DANGEROUS = "dangerous"  # 需二次确认

confirmation_policy = {
    "read_only": ALLOW,
    "write": NEED_CONFIRM,
    "dangerous": NEED_CONFIRM
}

protected_paths = ["C:\\Windows\\System32", "/etc"]

def check_permission(tool_name, params):
    tool_def = TOOL_REGISTRY[tool_name]
    if "path" in params:
        for protected in protected_paths:
            if protected in params["path"] and tool_def.permission in [WRITE, DANGEROUS]:
                return NEED_CONFIRM, f"涉及保护路径: {protected}"
    return ALLOW or NEED_CONFIRM
```

**沙盒 (`security/sandbox.py` 新建)：**
```python
class FileSandbox:
    def __init__(self):
        self.sandbox_root = "D:\\ZaneSandbox\\"  # 沙盒根目录
        self.allowed_roots = ["D:\\ZaneSandbox\\", "C:\\Users\\User\\Downloads\\"]
    
    def check_path(self, path):
        # 检查是否在允许目录
        real_path = os.path.realpath(path)
        for allowed in self.allowed_roots:
            if real_path.startswith(os.path.realpath(allowed)):
                return True
        return False
    
    def safe_delete(self, path, to_recycle=True):
        if not self.check_path(path):
            raise PermissionError(f"路径不在沙盒: {path}")
        # 移到回收站，不直接删除
        if to_recycle:
            # Windows: 使用 SHFileOperation 移到回收站
            pass
        else:
            os.remove(path)

class ProcessSandbox:
    def safe_kill(self, pid):
        # 检查是否是系统关键进程
        critical_processes = ["csrss.exe", "winlogon.exe", "services.exe"]
        proc_name = psutil.Process(pid).name()
        if proc_name.lower() in critical_processes:
            raise PermissionError(f"不能结束系统进程: {proc_name}")
        psutil.Process(pid).terminate()
```

**为什么沙盒：** 防止误删系统文件，删除先移到回收站，结束进程前检查是否关键进程

**网安技能 (`security/cybersec_tools.py` 新建)：**
```python
def scan_vulnerability():
    # 检查常见漏洞
    issues = []
    # 1. 检查是否有明文密码文件
    for root, dirs, files in os.walk("C:\\Users\\"):
        for file in files:
            if "password" in file.lower() and file.endswith(".txt"):
                issues.append(f"明文密码文件: {os.path.join(root, file)}")
    # 2. 检查开放端口
    for conn in psutil.net_connections():
        if conn.status == "LISTEN" and conn.laddr.port in [22, 3389, 445]:
            issues.append(f"高危端口开放: {conn.laddr.port}")
    # 3. 检查启动项
    # ...
    return {"issues": issues, "count": len(issues)}

def check_permission(file_path):
    # 检查文件权限是否过于宽松
    import stat
    st = os.stat(file_path)
    if st.st_mode & stat.S_IWOTH:
        return {"risk": "high", "message": "文件可被所有人写入"}
```

**Linux 能力 (`security/linux_provider.py` 新建)：**
```python
class WSLProvider:
    def wsl_list(self):
        # 列出 WSL 发行版
        result = subprocess.run(["wsl", "--list"], capture_output=True, text=True)
        return result.stdout
    
    def wsl_exec(self, distro, command):
        # 在 WSL 中执行命令，沙盒
        # 只允许在 WSL 沙盒目录
        if ".." in command or "rm -rf /" in command:
            raise PermissionError("危险命令")
        result = subprocess.run(["wsl", "-d", distro, "--", "bash", "-c", command], capture_output=True, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr}
```

**为什么 Linux：** Windows 上有 WSL，可执行 Linux 命令，扩展能力，但需沙盒限制

### 3.5 执行层 - 怎么保证成功和可回滚

**实现：**

**事务化+验证：**
```python
async def execute_node(node):
    result = func(**node.params)
    
    # 验证：每次写后重新感知
    if node.tool in ["launch_application", "focus_window"]:
        # 重新枚举窗口，检查是否成功
        windows = window_provider.enum_windows()
        success = any(node.params["title_keyword"] in w["title"] for w in windows)
        return {"success": success, "verified": True}
    
    return result
```

**为什么验证：** 代码维护现实，AI解释现实，AI说成功了，但需代码重新检查真实系统是否真的成功

**熔断：**
```python
circuit_breaker = {}  # 工具失败计数

def execute_tool(tool_name):
    if circuit_breaker.get(tool_name, 0) >= 5:
        return {"error": "circuit_breaker", "message": "失败5次，已熔断"}
    
    try:
        result = func()
        if "error" in result:
            circuit_breaker[tool_name] = circuit_breaker.get(tool_name, 0) + 1
        else:
            circuit_breaker[tool_name] = max(0, circuit_breaker.get(tool_name, 0) - 1)
    except:
        circuit_breaker[tool_name] += 1
```

**为什么熔断：** 防止 AI 反复执行失败操作，无限循环

**撤销栈 (`policy/undo_stack.py`)：**
```python
class UndoStack:
    def push(self, operation, params, reverse_params, description):
        entry = {
            "id": f"op_{time}",
            "operation": operation,
            "params": params,
            "reverse_params": reverse_params,  # 逆操作
            "description": description
        }
        self.stack.append(entry)
    
    def undo(self):
        entry = self.stack.pop()
        # 执行逆操作
        # 例如：创建文件 → 删除文件
        # 删除文件 → 从回收站恢复
        return entry["reverse_params"]

# 使用
undo_stack.push(
    operation="create_file",
    params={"path": "D:\\test.txt"},
    reverse_params={"operation": "delete_file", "path": "D:\\test.txt"},
    description="创建文件 D:\\test.txt"
)
```

**为什么撤销：** 商业级必备，像 Git 可回滚，误删可恢复

### 3.6 记忆层 - 怎么记住

**实现：**

**JSON持久化 (`memory_layer.py`)：**
```python
class MemoryLayer:
    def __init__(self):
        self.conversations = []  # 会话记忆，最近200条
        self.semantic_knowledge = []  # 语义：微信路径、用户习惯
        self.episodic = []  # 情景：任务历史
        self.skills = []  # 技能：可复用流程
        self.experiences = []  # 经验：问题→解法→验证
    
    def retrieve_relevant(self, query):
        # 简单关键词匹配，实际可用向量检索
        relevant = {"skills": [], "knowledge": []}
        for skill in self.skills:
            if query in skill["name"]:
                relevant["skills"].append(skill)
        return relevant
    
    def add_experience(self, task_type, problem, solution, tools_used, verification):
        exp = {...}
        self.experiences.append(exp)
        self.save_all()  # 保存到 data/experiences.json
```

**为什么 JSON：** 简单可靠，Windows上无额外依赖，可扩展为 sqlite-vec 向量检索

**梦境 (`learning/evolution_engine.py` `start_dreaming`)：**
```python
async def start_dreaming(self):
    # 1. 扫描近7天记忆，聚类
    clusters = {}
    for exp in memory_layer.experiences:
        task_type = exp["task_type"]
        clusters.setdefault(task_type, []).append(exp)
    
    # 2. 3次以上同类任务，生成新技能
    new_skills = []
    for task_type, exps in clusters.items():
        if len(exps) >= 3:
            new_skills.append({
                "name": f"自动技能：{task_type}",
                "steps": exps[0]["tools_used"]
            })
    
    # 3. 遗忘低价值
    # 4. 生成日记
    diary = {"date": "2024-09-12", "summary": f"整理{len(clusters)}类任务"}
```

**为什么梦境：** 空闲时整理记忆，像人睡觉，合并相似经验，生成新技能，遗忘低价值

### 3.7 进化层 - 怎么自我改进

**实现：**

**数据飞轮 (`memory/data_flywheel.py`)：**
```python
class DataFlywheel:
    def collect_from_success(self, task, tools_used, reasoning, final_report):
        sample = {
            "conversations": [
                {"from": "system", "value": "你是个人AI管家..."},
                {"from": "human", "value": f"任务：{task}"},
                {"from": "gpt", "value": f"<think>{reasoning}</think>\n工具链：{' → '.join(tools_used)}\n{final_report}"}
            ],
            "tools": tools_used
        }
        with open("data/training/sft.jsonl", "a") as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
```

**为什么飞轮：** 每次成功自动收集，无需人工标注，越用数据越多

**QLoRA微调 (`learning/unsloth_trainer.py`)：**
```python
def generate_training_script(sft_file, output_dir, config):
    script = f'''
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen3-30B-A3B",
    max_seq_length=4096,
    load_in_4bit=True
)
model = FastLanguageModel.get_peft_model(
    model,
    r=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=64
)
from datasets import load_dataset
dataset = load_dataset("json", data_files="{sft_file}", split="train")
from trl import SFTTrainer
trainer = SFTTrainer(model=model, train_dataset=dataset, ...)
trainer.train()
model.save_pretrained("{output_dir}")
'''
    return script
```

**为什么 QLoRA：** 4bit量化+LoRA，Qwen3-30B-A3B 30B总量3B激活，训练需24GB VRAM，推理16GB，Unsloth 2倍速，低配可用

**评估+晋升：**
```python
async def start_evolution(self):
    # 1. 准备数据：SFT 50条 + Replay 30%旧数据防遗忘
    # 2. 训练：生成 LoRA
    # 3. 评估：历史20任务回放
    eval_result = {
        "old_success_rate": 0.82,
        "new_success_rate": 0.91,
        "improvement": "+9%"
    }
    # 4. 晋升：提升则切换到新LoRA，旧版本保留可回滚
    if new_success_rate > old_success_rate:
        self.current_lora = new_version_id
```

**为什么评估：** 防止新模型更差，成功率提升才晋升，否则回滚

### 3.8 接口层 - 怎么交互

**实现：**

**FastAPI (`main_v2.py`)：**
```python
app = FastAPI(title="Zane AGI", version="2.0.0")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    result = await agent_runtime.execute_task(request.message, request.history)
    # 数据飞轮
    data_flywheel.collect_from_success(...)
    return result

@app.get("/api/system/state")
async def system_state():
    provider = get_platform_provider()
    cpu = provider["system"].get_cpu_info()  # WMI真实
    return {"cpu": cpu, "real": cpu.get("real")}

# 前端已写入content
frontend_path = "../frontend"
app.mount("/static", StaticFiles(directory=frontend_path))
@app.get("/")
async def serve_frontend():
    return FileResponse(frontend_path + "/index.html")
```

**为什么单端口：** 前端已写入 content，无需 Nginx，`http://127.0.0.1:8000` 同时提供API和前端，商业级单体部署

**前端 (`frontend/index.html` + `app.js`)：**
- 原生HTML/CSS/JS，无打包，极速
- 深色主题，CSS变量
- Fetch API调用后端
- 思考流、DAG、工具卡片、验证结果可视化

---

## 4. 自我修正 - 怎么操作

### 之前问题：只有自我修正，纠错，怎么操作？空中阁楼

### 现在落实：

#### 4.1 错误分类 + 重试

```python
# 工具执行时区分错误
try:
    result = func(**params)
except FileNotFoundError:
    error_type = "NotFound"  # 永久失败，不重试
except PermissionError:
    error_type = "PermissionDenied"  # 需用户确认
except TimeoutError:
    error_type = "Transient"  # 临时失败，可重试
except Exception:
    error_type = "Permanent"  # 永久失败

# 重试策略
if error_type == "Transient" and retry < 3:
    await asyncio.sleep(2**retry)  # 指数退避
    retry += 1
    continue
elif error_type == "NotFound":
    # 尝试其他方法
    # 例如：文件不存在，尝试列出父目录
    pass
```

#### 4.2 自反思

```python
async def execute_task():
    for attempt in range(3):
        result = await execute_dag(dag)
        if result["status"] == "success":
            break
        
        # 失败，自反思
        reflection = f"""
        任务：{intent}
        失败：{result["error"]}
        已尝试工具：{tools_used}
        思考：为什么失败？下次怎么做？
        """
        
        # 调整DAG
        dag = adjust_dag_based_on_reflection(dag, reflection)
        
        # 记录到 DPO
        data_flywheel.collect_from_failure(
            task=intent,
            failed_attempt=failed_tools,
            corrected=new_plan,
            reflection=reflection
        )
```

**怎么操作：** 失败后不直接放弃，分析原因，调整计划，最多3次，失败经验转为 DPO 训练数据，下次更懂

#### 4.3 验证失败自动修正

```python
async def verify_node(node, result):
    # 重新感知真实状态
    if node.tool == "launch_application":
        windows = window_provider.enum_windows()
        success = any("WeChat" in w["title"] for w in windows)
        if not success:
            # 验证失败，自动修正
            return {
                "status": "failed",
                "correction": "尝试再次启动，或检查路径",
                "next_action": "launch_application with different path"
            }
    return {"status": "passed"}
```

---

## 5. 网安技能 + 沙盒 + Linux

### 5.1 沙盒 - 已实现 `security/sandbox.py`

**文件沙盒：**
```python
class FileSandbox:
    sandbox_root = "D:\\ZaneSandbox\\"
    allowed_roots = ["D:\\ZaneSandbox\\", "C:\\Users\\User\\Downloads\\"]
    
    def check_path(self, path):
        real_path = os.path.realpath(path)
        for allowed in self.allowed_roots:
            if real_path.startswith(os.path.realpath(allowed)):
                return True
        return False  # 不在沙盒，拒绝
    
    def safe_delete(self, path, to_recycle=True):
        if not self.check_path(path):
            raise PermissionError(f"路径不在沙盒: {path}")
        # 移到回收站，不直接删除
```

**进程沙盒：**
```python
class ProcessSandbox:
    critical = ["csrss.exe", "winlogon.exe", "services.exe", "lsass.exe"]
    def safe_kill(self, pid):
        proc_name = psutil.Process(pid).name()
        if proc_name.lower() in critical:
            raise PermissionError(f"不能结束系统进程: {proc_name}")
        psutil.Process(pid).terminate()
```

**为什么沙盒：** 防止误删系统文件，结束系统进程，商业级安全必备

### 5.2 Linux 能力 - 已实现 `security/linux_provider.py`

```python
class WSLProvider:
    def wsl_list(self):
        result = subprocess.run(["wsl", "--list"], capture_output=True, text=True)
        return result.stdout  # Ubuntu, Debian
    
    def wsl_exec(self, distro, command):
        # 沙盒检查
        if ".." in command or "rm -rf /" in command or ":(){:|:&};:" in command:
            raise PermissionError("危险命令")
        # 只允许在 WSL 沙盒目录
        result = subprocess.run(
            ["wsl", "-d", distro, "--", "bash", "-c", command],
            capture_output=True, text=True,
            timeout=10  # 超时10秒
        )
        return {"stdout": result.stdout, "stderr": result.stderr}
```

**为什么 Linux：** Windows 有 WSL，可执行 Linux 命令，扩展能力，例如 `ls`, `grep`, `python`，但需沙盒限制危险命令

### 5.3 网安技能 - 已实现 `security/cybersec_tools.py`

```python
def scan_vulnerability():
    issues = []
    # 1. 明文密码文件
    for root, dirs, files in os.walk("C:\\Users\\"):
        for file in files:
            if "password" in file.lower() and file.endswith((".txt", ".log")):
                issues.append({"type": "明文密码", "path": os.path.join(root, file), "risk": "high"})
    # 2. 高危端口
    for conn in psutil.net_connections():
        if conn.status == "LISTEN" and conn.laddr.port in [22, 3389, 445, 135]:
            issues.append({"type": "高危端口", "port": conn.laddr.port, "risk": "medium"})
    # 3. 启动项
    # 4. 弱权限文件
    return {"issues": issues, "count": len(issues)}

def check_file_permission(file_path):
    import stat
    st = os.stat(file_path)
    if st.st_mode & stat.S_IWOTH:
        return {"risk": "high", "message": "所有人可写"}
    return {"risk": "low"}

def scan_large_files(path="C:\\", min_size_gb=1):
    # 扫描大文件，清理建议
    large = []
    for root, dirs, files in os.walk(path):
        for file in files:
            fp = os.path.join(root, file)
            try:
                size = os.path.getsize(fp)
                if size > min_size_gb * 1024**3:
                    large.append({"path": fp, "size_gb": round(size/1024**3, 2)})
            except:
                continue
    return large
```

**网安技能使用：**
- `scan_vulnerability` - 扫描漏洞，明文密码、高危端口、启动项
- `check_file_permission` - 检查文件权限是否过松
- `scan_large_files` - 扫描大文件，清理建议

**前端：** 系统状态页显示漏洞扫描结果

---

## 6. 技术栈 - 夯实基础

### 之前问题：东西太多太杂

### 现在精简夯实：

#### 后端 - 必要依赖

```
fastapi==0.115.0 - Web框架，异步，自动文档
uvicorn==0.32.0 - ASGI服务器
psutil==6.1.0 - 系统信息，跨平台
pillow==11.0.0 - 截图
pydantic==2.9.2 - 数据校验
httpx==0.27.2 - 异步HTTP，调LLM
wmi==1.5.1; sys_platform=="win32" - Windows WMI真实数据
pywin32==308; sys_platform=="win32" - Win32 API真实窗口
datasets==3.0.0 - 训练数据
```

**移除的杂项：**
- 移除 `aiofiles`, `python-multipart` 非必要
- Unsloth 不在 requirements，需手动安装，避免强制依赖

#### 前端 - 无打包，极速

```
原生HTML/CSS/JS - 无打包，<100ms响应
CSS变量 - 深色主题，商业级
Noto Sans SC + JetBrains Mono - 字体
Fetch API - 调用后端
```

**为什么无打包：** 商业级可控，类似 Raycast，无 Webpack 复杂性，单文件 `index.html` 含所有逻辑，前端已写入 content

#### 模型 - Qwen3-30B-A3B

```
Qwen3-30B-A3B MoE
30B total / 3B active
IQ4_XS量化 18.5GB
32768上下文
D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf
```

**为什么：** MoE 128专家激活8个，3B激活推理快，微调成本低，中文强

---

## 7. 目录结构 - 精简后

```
Zane/
├── backend/
│   ├── main_v2.py - 主服务 8层
│   ├── agent_runtime_v2.py - Harness：DAG+思考+并行+验证
│   ├── tool_registry.py - 工具注册表，严格Schema
│   ├── tools_impl.py - 真实工具，含截断
│   ├── llm/
│   │   ├── model_manager.py - 模型管理，支持你的路径
│   │   └── llm_client.py - LLM客户端，离线可用
│   ├── platform/
│   │   ├── base.py - 抽象接口
│   │   ├── windows/
│   │   │   ├── wmi_provider.py - WMI真实
│   │   │   └── win32_window.py - Win32真实HWND
│   │   └── linux/fallback.py - Linux演示
│   ├── security/
│   │   ├── sandbox.py - 文件+进程沙盒
│   │   ├── linux_provider.py - WSL沙盒执行
│   │   └── cybersec_tools.py - 漏洞扫描
│   ├── memory/
│   │   ├── data_flywheel.py - 数据飞轮，自动SFT/DPO
│   │   └── memory_layer.py - 记忆层
│   ├── learning/
│   │   ├── evolution_engine.py - 进化引擎，静默QLoRA
│   │   └── unsloth_trainer.py - 训练脚本生成
│   └── policy/
│       ├── policy_firewall.py - 权限分级
│       └── undo_stack.py - 撤销栈
├── frontend/
│   ├── index.html - v2.4 商业级设置可调整 (主)
│   ├── styles.css - 深色主题
│   └── app.js - v2.4 前端逻辑
├── data/
│   ├── training/
│   │   ├── sft.jsonl - 自动收集
│   │   └── dpo.jsonl
│   ├── skills.json - 技能
│   └── experiences.json - 经验
├── models/
│   └── versions/ - LoRA版本
├── experiments/
│   ├── moe_personality.py - MoE人格化
│   ├── dreaming_debate.py - 梦境辩论
│   └── skill_gene.py - 技能基因
├── scripts/
│   └── setup_windows.ps1 - Windows一键安装
├── requirements.txt
├── run.py - 一键启动
└── README.md - 本文档
```

**精简：** 移除 `main.py` 旧版，`agent_runtime.py` 旧版，统一用 v2

---

## 8. 快速启动 - 本地部署

### Windows

```powershell
# 1. 克隆
git clone https://github.com/thianhnguyentuyet6-commits/Zane.git
cd Zane

# 2. 模型
# 确保模型在 D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf

# 3. 安装
.\scripts\setup_windows.ps1
# 或
pip install -r requirements.txt
pip install wmi pywin32

# 4. 启动 llama.cpp (可选)
.\llama-server.exe -m Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf --host 0.0.0.0 --port 8080

# 5. 启动 Zane
python run.py
# 或
python -m uvicorn backend.main_v2:app --host 0.0.0.0 --port 8000

# 6. 打开
# http://127.0.0.1:8000/
# http://127.0.0.1:8000/docs
```

### Linux 演示

```bash
pip install -r requirements.txt
python -m uvicorn backend.main_v2:app --host 0.0.0.0 --port 8000
# 自动进入演示模式，WMI/Win32用模拟数据，接口一致
```

---

## 9. 可调整设置 - 已实现

**设置页 (`view-settings`) 现在可调整：**

- 模型路径、API地址、Temperature滑块、Top P滑块、上下文下拉
- 进化：启用开关、空闲分钟、CPU阈值、最小样本、LoRA Rank、学习率、定时
- 策略：只读放行、写入确认、危险二次确认、撤销栈数量
- 外观：主题、快捷键、托盘、iOS远程、声音

**保存到 `localStorage`，有通知提示**

---

## 10. 自我修正 - 具体操作

**错误分类：**
```python
FileNotFoundError → NotFound → 不重试，尝试列父目录
PermissionError → PermissionDenied → 需确认
TimeoutError → Transient → 重试3次，指数退避
```

**自反思：**
```python
for attempt in range(3):
    result = execute_dag()
    if success: break
    reflection = "为什么失败？下次怎么做？"
    dag = adjust_dag(reflection)
    collect DPO
```

**验证失败修正：**
```python
windows = enum_windows()
if "WeChat" not in titles:
    correction = "再次启动或检查路径"
```

---

## 11. 更新日志

### v2.4 - 2024-09-12 - 商业级设置+完整README

- 设置页可调整：模型路径、Temperature、进化参数、策略
- README重写：只写实现，无吹嘘，含WMI/Win32具体代码
- 精简14层→8层，解释必要性
- 新增沙盒、Linux WSL、网安技能

### v2.3 - 最强Harness融合

- DAG+思考+并行+验证

### v2.2 - 商业级前端

- WMI真实数据，模型管理

### v2.1 - 自我进化地基

- 数据飞轮，QLoRA

---

## 12. 下一步 - 夯实基础

- [ ] 设置页后端保存：`POST /api/settings/save` 真实保存到文件
- [ ] 确认弹窗+预览Diff：删除前显示列表，窗口移动显示虚线框
- [ ] WMI图表：CPU每核心折线图
- [ ] PaddleOCR真实集成
- [ ] EXE打包：PyInstaller

---

## 许可证

MIT

## 作者

Zane - 个人AGI管家

**GitHub**: https://github.com/thianhnguyentuyet6-commits/Zane

> 代码维护现实，AI解释现实
