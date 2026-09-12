# Zane AGI v3.0 - 工程化重构
## 从 AGI 概念到可靠本地计算机代理

> 核心原则：代码维护现实，AI解释现实
> 下一里程碑：Reliable Local Computer Agent，而非更多 AGI 特性

---

## 1. 核心循环 - Observe → Plan → Act → Verify → Recover

### 之前问题
- 任务直接调用工具，无真实状态观测
- 模型直接控制 OS，无验证
- 成功定义为 API 调用完成，而非真实世界动作成功

### 现在实现

```
用户请求
  ↓
[Observe] 获取真实系统状态，而非假设
  - WMI: CPU每核心、内存条、磁盘、进程树、启动项
  - Win32: HWND、Z序、DPI、置顶、矩形
  - UIA: 控件树、按钮、输入框
  - 文件: 真实文件列表
  ↓
[Plan] 模型生成计划，但不直接控制 OS
  - 输入：用户意图 + 真实状态 + 记忆
  - 输出：结构化工具请求 (ToolRequest)
  - 包含：工具名、参数、预期后置条件、验证方法
  ↓
[Act] 运行时验证+执行
  - Policy Engine: 检查权限、风险等级、是否需确认
  - Tool Executor: 执行工具，记录前置状态
  - 返回：工具输出 + 执行时间 + 副作用
  ↓
[Verify] 验证真实结果
  - 重新观测真实状态
  - 对比预期后置条件 vs 观测状态
  - 区分：API调用完成 vs 真实动作成功
  - 例如：launch_application 不仅检查 API 返回 success，还检查进程是否存在、窗口是否出现、窗口是否属于目标 exe
  ↓
[Recover] 失败则恢复/重规划
  - 分类失败：NotFound, PermissionDenied, Transient, Permanent
  - 恢复策略：重试、替代工具、重新观测、重规划
  - 最多3次，记录到 Task Trace
  ↓
[Commit] 验证通过则提交，记录 Trace，更新记忆
```

**代码位置：** `backend/runtime/` 模块化实现

---

## 2. 工具契约 - 形式化

### 之前问题
- 工具只有 name, description, 简单参数
- 无输入输出 Schema，无副作用分类，无验证方法
- launch_application 返回 success，但未定义 success 含义

### 现在实现 - 每个工具完整契约

```python
@dataclass
class ToolContract:
    name: str
    display_name: str
    description: str
    input_schema: Dict  # JSON Schema
    output_schema: Dict  # JSON Schema
    side_effect: str  # none, reversible, destructive, system
    risk_level: str  # low, medium, high, critical
    timeout: int  # 秒
    required_permissions: List[str]
    preconditions: List[str]  # 执行前需满足
    postconditions: List[str]  # 执行后预期
    verification_method: str  # 如何验证
    category: str
    is_real: bool
```

**例子：launch_application**

```python
ToolContract(
    name="launch_application",
    display_name="启动应用",
    description="启动应用程序",
    input_schema={
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "应用名，如 wechat, chrome"},
            "path": {"type": "string", "description": "exe路径，可选"},
            "args": {"type": "string", "description": "启动参数，可选"}
        },
        "required": ["app_name"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "pid": {"type": "integer"},
            "process_name": {"type": "string"},
            "window_hwnd": {"type": "integer"},
            "verification": {"type": "object"}
        }
    },
    side_effect="reversible",  # 可逆：可结束进程
    risk_level="medium",
    timeout=10,
    required_permissions=["process_launch"],
    preconditions=["检查应用是否已运行，避免重复"],
    postconditions=["进程存在", "PID有效", "可选：窗口出现"],
    verification_method="进程存在检查 + 窗口枚举 + 可选 UIA 验证",
    category="进程控制",
    is_real=True
)
```

**验证方法实现：**
```python
def verify_launch_application(params, result):
    # 1. API 调用完成？
    if not result.get("success"):
        return {"verified": False, "reason": "API调用失败"}
    
    # 2. 进程是否存在？（真实世界成功）
    pid = result.get("pid")
    try:
        proc = psutil.Process(pid)
        if not proc.is_running():
            return {"verified": False, "reason": f"进程 {pid} 不存在"}
    except:
        return {"verified": False, "reason": f"进程 {pid} 未找到"}
    
    # 3. 窗口是否出现？（可选，更强验证）
    time.sleep(1)  # 等待窗口出现
    windows = window_provider.enum_windows()
    app_windows = [w for w in windows if params["app_name"].lower() in w["process"].lower()]
    if not app_windows:
        return {"verified": True, "reason": "进程存在，窗口未出现（可能后台运行）", "level": "partial"}
    
    return {
        "verified": True,
        "reason": f"进程 {pid} 存在，窗口 {app_windows[0]['hwnd']} 出现",
        "level": "full",
        "process": True,
        "window": True
    }
```

**区分：** API调用完成 vs 真实动作成功，这是可靠代理的基础

**代码位置：** `backend/tool_contract.py`

---

## 3. Tool Registry 作为安全边界

### 之前问题
- Tool Registry 只是函数集合，无安全边界
- 依赖模型判断操作是否安全

### 现在实现

**Policy Engine 独立：**

```python
class PolicyLevel:
    READ_ONLY = "read_only"  # 只读，自动放行
    REVERSIBLE_WRITE = "reversible_write"  # 可逆写入，需确认
    DESTRUCTIVE = "destructive"  # 破坏性，需二次确认
    SYSTEM = "system"  # 系统级，拒绝或需密码

class PolicyEngine:
    def decide(self, tool_request):
        contract = TOOL_CONTRACTS[tool_request.name]
        
        # 1. 检查权限
        if contract.risk_level == "critical":
            return {"action": "deny", "reason": "关键操作，拒绝"}
        
        # 2. 检查保护路径
        if "path" in tool_request.params:
            if "System32" in tool_request.params["path"]:
                return {"action": "need_confirm", "level": "critical", "reason": "保护路径"}
        
        # 3. 根据 side_effect 决定
        if contract.side_effect == "none":
            return {"action": "allow"}
        elif contract.side_effect == "reversible":
            return {"action": "need_confirm", "level": "low"}
        elif contract.side_effect == "destructive":
            return {"action": "need_confirm", "level": "high", "need_reason": True}
        elif contract.side_effect == "system":
            return {"action": "deny", "reason": "系统级操作"}
```

**原则：** LLM 只提议，Policy Engine 决定是否允许、需确认、拒绝，永不依赖模型判断安全

**代码位置：** `backend/runtime/policy_engine.py`

---

## 4. 确定性工具 vs 模型工具分离

### 之前问题
- 所有工具同等，无优先级
- 视觉作为通用接口，慢且贵

### 现在实现 - 层次

```
结构化状态 (最优先，快、准、便宜)
  ↓ 若不可用
UI Automation (控件树，按钮、输入框)
  ↓ 若不可用
OCR (文字识别，边界框)
  ↓ 若不可用
视觉定位 (截图分析)
  ↓ 最后
坐标交互 (x,y 点击)
```

**例子：点击保存按钮**

```python
# 优先 UIA
uia_elements = uia_provider.find_elements(name="保存")
if uia_elements:
    # 直接调用 UIA InvokePattern，无需坐标
    uia_elements[0].invoke()
    return {"method": "uia", "confidence": 0.95}

# 回退 OCR
ocr_result = ocr_screenshot()
for block in ocr_result["blocks"]:
    if "保存" in block["text"]:
        # OCR 边界框
        x, y = block["x"] + block["width"]//2, block["y"] + block["height"]//2
        mouse_click(x, y)
        return {"method": "ocr", "confidence": 0.8}

# 回退视觉
# 截图 + 视觉模型定位
```

**为什么：** 结构化信息快、准、便宜，视觉作为补充和回退

**代码位置：** `backend/platform/` + `backend/tools/`

---

## 5. 视觉子系统 - 完整

### 之前问题
- 视觉只是截图+问模型看到什么

### 现在实现 - 统一场景表示

```python
@dataclass
class SceneRepresentation:
    screenshot_path: str
    width: int
    height: int
    dpi: int
    windows: List[Dict]  # 窗口元数据
    uia_elements: List[Dict]  # UIA控件树
    ocr_blocks: List[Dict]  # OCR文字+边界框
    cursor_position: Dict
    active_window: Dict
    timestamp: float

def build_scene():
    # 1. 截图
    screenshot = screenshot_provider.capture_full()
    # 2. OCR
    ocr = ocr_provider.recognize(screenshot["path"])
    # 3. UIA
    uia = uia_provider.get_tree()
    # 4. 窗口
    windows = window_provider.enum_windows()
    # 5. 统一表示
    scene = SceneRepresentation(
        screenshot_path=screenshot["path"],
        width=screenshot["width"],
        height=screenshot["height"],
        dpi=get_dpi(),
        windows=windows,
        uia_elements=uia,
        ocr_blocks=ocr["blocks"],
        cursor_position=get_cursor(),
        active_window=get_active_window(),
        timestamp=time.time()
    )
    return scene
```

**Agent 可说：** “这是当前应用窗口的保存按钮，边界框 x=500,y=300,w=80,h=30，置信度0.95，属于窗口 HWND 12345”

**可复用：** 规划、执行、验证、记忆都用同一场景表示

**代码位置：** `backend/vision/scene.py` (规划)

---

## 6. 记忆 - 多类型，不同保留策略

### 之前问题
- 单一向量数据库作为全部记忆

### 现在实现

| 记忆类型 | 内容 | 保留策略 | 检索 | 实现 |
|---|---|---|---|---|
| 工作记忆 | 当前任务上下文 | 任务结束清空 | 直接 | 内存变量 |
| 情景记忆 | 之前事件，任务历史 | 30天，重要性衰减 | 时间+相似度 | `episodic.json` |
| 语义记忆 | 稳定事实，微信路径 | 永久，除非用户修改 | 精确匹配 | `semantic.json` |
| 程序记忆 | 成功流程 | 版本化，可回滚 | 任务类型匹配 | `skills.json` |
| 偏好记忆 | 用户行为偏好 | 永久，学习 | 频率统计 | `preferences.json` |

**为什么：** 成功流程不应直接变模型权重，应先变版本化 Skill，安全易调试

**代码位置：** `backend/memory/`

---

## 7. 技能 - 版本化可复用

### 之前问题
- 成功直接微调模型

### 现在实现 - 技能契约

```python
@dataclass
class Skill:
    id: str
    name: str
    description: str
    trigger_conditions: List[str]  # 触发条件
    required_tools: List[str]
    procedure: List[Dict]  # 步骤
    parameters: Dict  # 参数化
    preconditions: List[str]
    verification_rules: List[str]
    failure_recovery: Dict  # 失败恢复策略
    version: str
    created_at: float
    usage_count: int
    success_rate: float
```

**例子：organize_downloads**

```python
Skill(
    id="skill_003",
    name="文件整理与归档",
    description="将下载文件夹按类型分类",
    trigger_conditions=["下载文件夹文件数>20", "用户说整理下载"],
    required_tools=["list_files", "create_folder", "write_file"],
    procedure=[
        {"tool": "list_files", "params": {"path": "C:\\Users\\User\\Downloads"}},
        {"tool": "create_folder", "params": {"path": "C:\\Users\\User\\Downloads\\Images"}},
        {"tool": "write_file", "params": {"path": "..."}}
    ],
    parameters={"source": "C:\\Users\\User\\Downloads", "rules": {"Images": [".png", ".jpg"]}},
    preconditions=["下载文件夹存在"],
    verification_rules=["目标文件夹文件数匹配", "源文件夹已清空对应类型"],
    failure_recovery={"on_failure": "回滚已移动文件", "retry": "跳过失败文件"},
    version="1.2",
    usage_count=15,
    success_rate=0.95
)
```

**可回放、评估、编辑、回滚，独立于基础模型**

**代码位置：** `backend/memory/skill_manager.py` (规划)

---

## 8. 自我改进 - 基于证据，非自主进化

### 之前问题
- “模型夜间学习” 无科学依据

### 现在实现 - 证据驱动

```
收集任务轨迹 → 识别成功/失败 → 分类失败 → 生成候选改进 → 创建训练/Skill数据 → 训练候选adapter → 跑固定基准 → 对比当前版本 → 提升才晋升 → 保留回滚
```

**具体：**
1. **收集**：每次任务生成 Task Trace
2. **识别**：成功/失败，失败分类
3. **生成**：候选改进，Skill 或训练数据
4. **训练**：候选 LoRA
5. **基准**：固定 benchmark 100任务
6. **对比**：成功率、验证准确率、恢复率、工具调用数、延迟、token消耗、回归率
7. **晋升**：提升才晋升，保留回滚
8. **回答**：什么变了、为什么、什么任务提升、什么回归、是否晋升

**科学可辩护**

**代码位置：** `backend/learning/evolution_engine.py` 已有基础，需加强评估

---

## 9. MoE 专家微调 - 实验性，需实验

### 之前问题
- 声称选择性微调专家降低90%成本，无实验

### 现在实现 - 实验性

**不应声称 90% 成本降低，除非有实验：**

**实验设计：**
```python
# 比较
# 1. Full LoRA: 所有参数
# 2. 常规 PEFT: q_proj, v_proj
# 3. 专家选择性: 只微调激活的2-3个专家

# 指标
# - VRAM使用
# - 训练时间
# - 任务性能
# - 回归行为

# 结论前标记为实验性
```

**代码位置：** `experiments/moe_personality.py` 标记为实验

---

## 10. 模型注册表 - 推理与训练分离

### 之前问题
- GGUF模型、训练checkpoint、LoRA、参数、评估结果耦合

### 现在实现

```python
@dataclass
class ModelArtifact:
    base_model: str  # Qwen3-30B-A3B
    quantization: str  # IQ4_XS
    runtime_backend: str  # llama.cpp
    context_length: int  # 32768
    gpu_offload: str  # 35层 offload
    adapter_versions: List[str]  # LoRA版本
    benchmark_results: Dict
    promotion_status: str  # active, candidate, rollback
```

**推理架构 vs 训练架构分离：**
- 推理：llama.cpp + GGUF + 量化 + 消费级GPU
- 训练：Unsloth + QLoRA + 训练checkpoint

**代码位置：** `backend/model_registry.py` (规划)

---

## 11. Task Trace - 统一

### 实现

```python
@dataclass
class TaskTrace:
    task_id: str
    user_request: str
    observations: List[Dict]  # 真实状态
    model_decision: Dict  # 模型决策
    selected_tools: List[str]
    tool_inputs: List[Dict]
    tool_outputs: List[Dict]
    state_changes: List[Dict]
    verification_results: List[Dict]
    failures: List[Dict]
    recovery_attempts: List[Dict]
    final_outcome: str
    latency: float
    token_usage: Dict
    confidence: float
    timestamp: float
```

**单一格式，成为调试、记忆、技能、评估、训练数据的基础**

**代码位置：** `backend/task_trace.py`

---

## 12. 可复现评估 - 基准套件

### 实现

**基准类别：**
- 进程管理：列出、结束、启动
- 窗口管理：枚举、聚焦、移动
- 文件操作：列出、读取、写入、删除、移动
- 剪贴板：读写
- 应用启动：启动、验证
- UI交互：点击、输入
- 截图、OCR、视觉定位
- 多步任务：3-5步
- 失败恢复：应用未安装、窗口消失、权限变化、网络失败、UI移动、进程挂起
- 模糊指令：歧义指令

**每个任务有明确成功标准，可重放**

**指标：**
- 任务成功率
- 验证准确率
- 恢复率
- 平均工具调用数
- 延迟
- Token消耗
- 回归率

**代码位置：** `backend/benchmark/`

---

## 13. 破坏性操作作为事务

### 实现

```python
def destructive_operation():
    # 1. 记录前置状态
    pre_state = observe()
    
    # 2. 可逆机制
    # 文件删除 → 移到回收站
    # 批量移动 → 记录映射，可回滚
    # 配置更改 → 备份原配置
    # 进程结束 → 记录PID，可重启
    
    # 3. 执行
    result = execute()
    
    # 4. 验证后置状态
    post_state = observe()
    verified = verify(post_state, expected)
    
    # 5. 提交或回滚
    if verified:
        commit()
    else:
        rollback(pre_state)
```

**文件删除、批量移动、配置更改、进程结束都有回滚策略**

**代码位置：** `backend/policy/undo_stack.py` 已有基础

---

## 14. 模块化代码库

### 之前问题
- main Agent Runtime 成为巨型编排模块

### 现在实现

```
backend/runtime/
├── intent_parser.py - 意图解析
├── state_manager.py - 状态管理
├── planner.py - 规划，DAG分解
├── tool_executor.py - 工具执行
├── policy_engine.py - 策略引擎，安全边界
├── verifier.py - 验证器
├── recovery_manager.py - 恢复管理
├── memory_manager.py - 记忆管理
├── skill_manager.py - 技能管理
├── model_interface.py - 模型接口
└── trace_logger.py - 轨迹日志
```

**Runtime 编排这些组件，而非实现所有内部逻辑，易于替换模型、Vision后端、Windows工具、云端教师**

**代码位置：** `backend/runtime/` (重构中)

---

## 15. 本地优先原则

**架构：**
- 云模型作为可选教师、批评、规划助手
- 本地模型保持核心工作流能力，云不可用时仍可执行
- Teacher 提供建议、修正、训练数据，本地 Runtime 是执行权威
- 隐私友好，避免本地代理变云模型瘦客户端

**代码位置：** `backend/llm_client.py` teacher 可选

---

## 16. README - 已实现/部分/实验/计划分离

### 之前问题
- 吹嘘，AGI描述，20工具说成60+

### 现在实现

**README 分区：**

```
## 已实现 (IMPLEMENTED)
- 21工具，真实文件/进程/窗口/截图，WMI真实，HWND真实
- 8层架构，Observe→Plan→Act→Verify→Recover
- 工具契约，输入输出Schema，验证方法
- 策略防火墙，权限分级，沙盒，撤销栈
- 记忆：会话、语义、情景、技能、经验
- 自我进化：数据飞轮，QLoRA，评估，晋升回滚
- 前端：对话、任务、系统状态、文件、进程、窗口、视觉、记忆、技能、经验、设置可调整

## 部分实现 (PARTIAL)
- UIA：有接口，真实实现需Windows
- DWM缩略图：接口预留
- OCR：演示，需PaddleOCR
- iOS远程：API预留，8002端口
- 系统托盘、快捷键：规划

## 实验性 (EXPERIMENTAL)
- MoE专家人格化：需实验验证
- 梦境辩论：需审核
- 技能基因：需手动晋升

## 计划 (PLANNED)
- EXE打包
- PaddleOCR真实集成
- 基准套件
- 向量检索
```

**技术诚实 README 比 AGI 描述更可信**

---

## 17. 下一里程碑 - Reliable Local Computer Agent

**不是更多 AGI 特性，而是：**

- 本地模型接收自然语言任务
- 观测真实 Windows 状态
- 选择结构化工具
- 通过受控运行时执行
- 验证真实结果
- 从失败恢复
- 记录轨迹
- 复用成功流程为技能

**一旦在可复现基准上可靠工作，高层学习和进化系统才有坚实基础**

**此时添加微调、自主技能生成、教师模型、多代理协作、更高级规划才有意义，而非架构装饰**

---

## 总结

**不应让 Zane 更 AGI，而应更可度量、更确定、更可恢复、更可观测、更扎根真实 Windows 状态**

**如果 Zane 能证明小本地模型可可靠操作真实 Windows 机器，验证自己动作，从失败恢复，记住有用流程，转为可复用技能，针对固定基准改进，那将是比添加更多层、工具、AGI术语更强的本地代理演示**

**架构已指向正确方向，下一步是将其变为严格工程系统**
