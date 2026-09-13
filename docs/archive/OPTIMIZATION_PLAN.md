# 本地AI电脑助手 - 商业级重构优化完整计划
## 从演示版到个人AGI管家

> 版本：v2.0 重构计划 | 目标：媲美 Operator / Claude Computer Use / Manus / PowerToys | 2026-09-12

---

### 一、现状诊断 - 为什么现在像“滥竽充数”

#### 1.1 你提到的痛点（已确认）
- **电脑状态不准确**：现在用 `psutil` 粗略数据，Linux容器演示，Windows上无 WMI、GPU、启动项、服务、真实性能计数器
- **窗口管理不完善**：演示假数据，无真实 HWND、Z序、DPI感知、虚拟桌面、DWM缩略图、UIA 树
- **设置不完善**：模型切换藏在代码里，无模型市场、无健康检查、无参数调节、无本地模型进程管理
- **行动无提示**：执行时无预览、无分级确认、无通知中心、无回滚、无审计时间轴
- **模型切换**：写死 `http://127.0.0.1:8080/v1`，无 llama.cpp 管理，无 gguf 元数据解析

#### 1.2 深层架构缺陷（我补充）
- **工具层**：无严格 JSON Schema 校验，参数错误直接崩，无 OpenAI 的 structured output
- **视觉层**：截图占位图，无真实坐标映射，无 Set-of-Mark，无 Claude 的视觉定位
- **推理层**：无显式思考链，无 DeepSeek 的任务DAG分解，无自反思
- **记忆层**：简单 JSON，无向量检索，无 OpenClaw 的 Memory Dreaming，无遗忘曲线
- **验证层**：只有简单检查，无 Manus 的多轮验证闭环
- **资源占用**：无上下文预算动态调节，无 prompt caching，无量化感知
- **远程能力**：无 iOS 远程查看/控制端口
- **商业级体验**：无键盘驱动(Raycast)、无插件生态、无性能监控、无崩溃恢复

---

### 二、愿景重定义

> **不是聊天机器人，是你的个人AGI管家**
> - **本地私有**：所有数据不出PC，离线可用
> - **持续进化**：像人一样睡觉时整理记忆（Dreaming），越用越懂你
> - **低配可用**：8GB显存/16GB内存流畅跑 7B 模型，自动优化
> - **全感官**：看屏幕、懂窗口、控鼠标键盘、读文件、记习惯
> - **可远程**：iOS 随时查看家里电脑在做什么，一键接管

**对标矩阵：**
- **OpenAI Operator** 的自主操作 + 严格工具规范
- **Claude Computer Use** 的视觉定位 + 长思考 + 缓存
- **DeepSeek R1** 的推理链 + 任务分解 + 成本意识
- **Manus/Devin** 的规划-执行-验证闭环 + 经验复用
- **PowerToys/Raycast** 的极速 + 键盘驱动 + 系统级集成
- **OpenClaw** 的 Memory Dreaming + 自我修正

---

### 三、集大成架构设计 - v2.0

#### 3.1 总体架构（10层 → 14层商业级）

```
[用户层] iOS远程 + 桌面控制台 + 键盘快捷键 + 系统托盘
   ↓
[交互层] 通知中心 + 确认弹窗 + 预览Diff + 撤销栈
   ↓
[Agent Harness 融合层] ← 核心重构
  ├─ OpenAI: 严格Schema + 并行工具调用 + Structured Output + 错误分类
  ├─ Claude: 视觉Set-of-Mark + 坐标归一化 + Extended Thinking可视化 + Prompt Caching
  ├─ DeepSeek: 推理链 + 任务DAG分解 + 自反思 + Token预算
  └─ 自研: 验证闭环 + 记忆梦境 + 技能蒸馏 + 低配优化
   ↓
[14层执行引擎]
1. 感知层: WMI + UIA + DWM + 真实截图 + OCR(PaddleOCR)
2. 推理层: 本地LLM + 思考链 + 计划
3. 规划层: DAG任务分解 + 依赖分析
4. 工具层: 21→60+工具，严格Schema，真实Windows API
5. 策略层: 分级确认 + 白名单学习 + 保护路径
6. 执行层: 事务化 + 可回滚 + 熔断 + 重试
7. 验证层: 多轮验证 + 视觉验证 + 状态对比
8. 记忆层: 向量+KV + Dreaming + 遗忘曲线
9. 技能层: 自动蒸馏 + 参数化 + 版本管理
10. 学习层: 经验提取 + 失败分析 + 自我修正
11. 模型层: llama.cpp管理 + 模型市场 + 自动切换
12. 远程层: iOS API + WebSocket + 鉴权
13. 系统层: 性能监控 + 崩溃恢复 + 低配优化
14. 教师层: 可选云端顾问
```

#### 3.2 借鉴精华（融合方案）

**从 OpenAI 提取：**
- 每个工具严格 JSON Schema，`required` + `enum` + `description` 中文
- 并行工具调用（一次推理调用3-5个只读工具）
- Structured Output：任务结果强制 JSON，便于验证
- 错误分类：`InvalidParam` / `PermissionDenied` / `NotFound` / `Transient` / `Permanent`
- Function calling v2：支持 `tool_choice: required`

**从 Claude 提取：**
- Computer Use：截图 + 坐标(0-1000归一化) + 鼠标键盘 + Set-of-Mark（给截图打标）
- Extended Thinking：思考过程单独流，UI可折叠，不污染上下文
- Prompt Caching：系统提示+工具定义缓存，节省 80% token
- Vision Grounding：OCR + UIA 控件树 + 视觉匹配，定位按钮
- 长上下文：200K 上下文管理，自动摘要

**从 DeepSeek 提取：**
- 显式推理链：`<think>` 标签，计划→执行→反思
- 任务DAG：复杂任务自动分解为有依赖的子任务，可并行
- 自反思：失败后分析原因，调整策略重试，最多3次
- Token预算：每个任务预算，超预算自动摘要
- 成本意识：优先只读工具，危险操作最后执行

**自研增强（超越）：**
- **验证闭环**：每个写操作后，重新感知真实状态，对比预期，Manus式
- **记忆梦境**：OpenClaw启发，空闲时自动整理记忆，合并相似经验，生成新技能，遗忘低价值记忆
- **技能蒸馏**：成功任务自动提取为参数化技能，支持变量
- **低配优化**：量化感知（自动选 Q4/Q5/Q8）、上下文动态裁剪、工具结果摘要、LoRA微调接口预留
- **拟人化**：模拟人类操作节奏（移动鼠标轨迹、打字间隔），避免被检测

---

### 四、核心模块重构详细计划

#### 4.1 电脑状态 - 从假数据到WMI商业级

**现在：** `psutil` 粗略
**重构后：**
- **CPU**：WMI `Win32_Processor` 每核心使用率 + 温度 + 频率 + GPU (NVIDIA/AMD/Intel)
- **内存**：物理/虚拟/页面文件，进程工作集、提交大小、句柄数
- **磁盘**：每盘符 SMART、IO、类型(SSD/HDD)、剩余时间预估
- **进程**：完整进程树、父子关系、命令行、启动时间、用户、完整路径、签名验证
- **系统**：启动项(`Run`注册表+启动文件夹)、服务状态、计划任务、环境变量
- **网络**：每进程流量、TCP连接、防火墙状态
- **实现**：`backend/tools/system/wmi_provider.py` + `performance_counter.py` + `platform/windows.py` + `platform/linux_fallback.py`

#### 4.2 窗口管理 - 从假数据到真实HWND

**现在：** 假数据
**重构后：**
- **枚举**：`EnumWindows` + `EnumChildWindows`，过滤不可见、工具窗口，支持 Z序
- **信息**：标题、类名、进程、PID、HWND、矩形、DPI、是否置顶、是否最小化、虚拟桌面ID
- **控制**：`SetForegroundWindow` + `ShowWindow` + `MoveWindow` + `SetWindowPos`，DPI感知
- **截图**：窗口截图（`PrintWindow` + DWM缩略图），支持被遮挡窗口
- **UIA**：`UIAutomation` 控件树，获取按钮、输入框、文本，支持 `InvokePattern`
- **预览**：窗口列表显示真实缩略图（DWM）
- **实现**：`backend/tools/window/win32_window.py` + `uia_provider.py` + `dwm_thumbnail.py`

#### 4.3 设置 - 从隐藏到商业级

**现在：** 写死配置
**重构后：**
- **模型管理页**：
  - 自动发现：扫描 `C:\models\*.gguf`，解析元数据（参数量、量化、上下文）
  - llama.cpp 控制：启动/停止/重启 server，日志查看，端口检测
  - 一键切换：Qwen2-7B / Llama3-8B / DeepSeek-R1-7B，下拉选择
  - 参数调节：temperature、top_p、repeat_penalty，实时生效
  - 健康检查：`/v1/models` 检测，延迟、token速度显示
  - 性能：显存占用、推理速度、上下文使用率
  - 支持 Ollama：`http://localhost:11434/v1` 自动识别
- **策略设置**：分级确认开关、白名单管理、保护路径编辑
- **远程设置**：iOS 远程开关、端口、鉴权Token、二维码
- **外观**：主题、语言、通知声音
- **实现**：`frontend/views/settings/model-manager.js` + `backend/llm/model_manager.py`

#### 4.4 行动提示 - 从无到通知中心

**现在：** 无提示
**重构后（你要求的 融合版）：**
- **分级策略**：
  - L0只读：自动执行，通知中心静默日志
  - L1写入：Toast + 预览（例如：将在 `Downloads` 创建文件夹），3秒后自动执行，可取消
  - L2危险：弹窗 + 截图Diff + 需输入原因 + 二次确认，支持“信任此操作30分钟”
  - L3系统：需密码/指纹（预留）
- **通知中心**：右侧滑出面板，时间轴，显示所有操作，可点击回滚
- **预览Diff**：删除文件前显示文件列表，移动窗口前显示目标位置虚线框
- **撤销栈**：每个写操作记录逆操作，支持一键撤销（类似 Git）
- **执行时**：鼠标轨迹可视化（可选）、当前操作高亮、进度条、预估剩余时间
- **实现**：`frontend/components/confirmation/` + `notification-center/` + `backend/policy/undo_stack.py`

#### 4.5 模型切换 - llama.cpp 商业级

**重构：**
- **后端** `backend/llm/llama_cpp_manager.py`：
  - 进程管理：`subprocess.Popen` 启动 server，监控日志，自动重启
  - 模型发现：扫描目录，`gguf` 解析（用 `gguf` 库读元数据）
  - API：`/api/models/list` `/api/models/switch` `/api/models/status` `/api/models/start` `/api/models/stop`
  - 健康：每5秒心跳，失败自动切离线模式
- **前端**：模型市场卡片，显示参数量、量化、大小、速度、显存，当前模型高亮，一键切换动画

#### 4.6 iOS 远程 - 预留端口

**新增：**
- **后端** `backend/remote/ios_api.py`：
  - 独立端口 8002（可配置），`FastAPI` + `WebSocket`
  - 鉴权：Token + 可选 FaceID（预留）
  - API：`/remote/state`（系统状态）、`/remote/screenshot`（实时截图流）、`/remote/tasks`、`/remote/chat`
  - WebSocket：实时推送执行步骤、通知
- **前端** `frontend/mobile/`：响应式移动端页面，适配 iOS，PWA 支持，可添加到主屏幕
- **安全**：仅局域网默认，公网需手动开启 + 强密码

#### 4.7 记忆梦境 - OpenClaw 启发

**新增 `backend/memory/dreaming.py`：**
- 触发：空闲30分钟或凌晨2点，CPU<20%
- 流程：
  1. 扫描近7天情景记忆，聚类相似任务
  2. 合并经验，生成新技能（例如：3次“整理下载文件夹”→生成“下载整理技能”）
  3. 遗忘：低重要性、久未使用记忆衰减
  4. 关联：建立知识图谱（微信→腾讯→聊天）
  5. 日记：生成每日总结，写入 episodic
- UI：记忆页显示“梦境日志”，可查看AI夜里学到了什么

#### 4.8 低配优化 - 不能太吃配置

- **量化感知**：自动检测显存，推荐 Q4_K_M / Q5 / Q8，8GB显存跑7B Q4
- **上下文**：Prompt Caching（系统+工具定义缓存）、工具结果摘要（LLM自动摘要长输出）、历史自动归档
- **推理**：流式输出、并行只读工具、写操作串行
- **后台**：Dreaming 低优先级、截图压缩、OCR 异步

---

### 五、商业级品质标准（对标你说的1,2,3）

#### 5.1 对标 Operator/Claude Computer Use
- 真实视觉操作：截图→Set-of-Mark→坐标→点击，误差<5px
- 跨应用：微信→Chrome→文件管理器，数据传递
- 人类节奏：鼠标贝塞尔曲线、打字间隔50-150ms
- 失败恢复：找不到按钮→滚动→OCR→UIA→搜索

#### 5.2 对标 Manus/Devin
- DAG分解：复杂任务自动拆3-7步，显示依赖图
- 验证闭环：每步验证，失败自反思，最多3次重试
- 经验复用：相似任务自动推荐技能
- 长任务：支持1小时+任务，可暂停/继续

#### 5.3 对标 PowerToys/Raycast
- 极速：快捷键 `Alt+Space` 唤起，<100ms 响应
- 键盘驱动：所有操作可键盘完成
- 系统托盘：常驻，右键菜单，性能悬浮窗
- 插件：工具可插件化，JS/Python 插件API预留

#### 5.4 额外商业级
- **性能**：前端虚拟滚动、后端异步、WebSocket 推送
- **稳定**：崩溃自动恢复、操作事务化、数据备份
- **可观测**：执行时间、token消耗、成功率统计
- **空状态**：每个页面精美空状态+引导
- **无障碍**：快捷键、屏幕阅读器预留

---

### 六、分阶段执行计划（预计总工时）

#### Phase 1: 地基重构（核心准确性）- 2天
- [ ] 重写 `system/wmi_provider.py` + `window/win32_window.py` + `vision/screenshot_real.py`
- [ ] 实现真实 PaddleOCR + UIA
- [ ] 模型管理器 `llm/model_manager.py` + 前端模型市场
- [ ] 策略分级 + 通知中心 + 撤销栈

#### Phase 2: Harness 融合（智能度）- 2天
- [ ] OpenAI: 严格Schema校验 + 并行工具调用 + Structured Output
- [ ] Claude: Set-of-Mark + 坐标归一化 + Extended Thinking UI + Prompt Caching
- [ ] DeepSeek: 推理链 + DAG分解 + 自反思 + Token预算
- [ ] 验证闭环 + 错误分类

#### Phase 3: 记忆与进化（AGI管家）- 1.5天
- [ ] 向量记忆（sqlite-vec）+ 语义检索
- [ ] Dreaming 定时任务 + 技能蒸馏
- [ ] 经验图谱 + 遗忘曲线

#### Phase 4: 远程与商业级打磨 - 1.5天
- [ ] iOS 远程 API + WebSocket + 移动端UI
- [ ] 系统托盘 + 快捷键 + 性能监控
- [ ] 商业级UI重设计：空状态、加载、错误、动画
- [ ] 低配优化 + 崩溃恢复

#### Phase 5: 测试与文档 - 1天
- [ ] Windows 真实环境测试清单
- [ ] 性能基准测试
- [ ] 用户手册 + 开发者文档

**总计：约 8 天工作量，分5个PRD交付**

---

### 七、风险与取舍

- **Windows API**：Linux容器无法真实测试，需你本地Windows验证，我会写好 fallback
- **llama.cpp**：需要你本地有模型，我会提供模型下载脚本
- **PaddleOCR**：体积大，默认用轻量，Windows上可选完整版
- **iOS远程**：局域网优先，公网需你配置内网穿透

---

### 八、需要你确认的问题

1. **是否同意此重构计划？** 若同意，我将从 Phase 1 开始执行
2. **模型路径**：你的 gguf 模型放在哪里？`C:\models\` 还是其他？
3. **iOS远程**：是否需要现在就开启 8002 端口？鉴权方式？
4. **优先级**：Phase 1-4 中，你最想先看到哪个？（我建议 Phase 1 电脑状态准确性）

---

**此计划旨在从“演示”升级为“可日常使用的个人AGI管家”，品质对标商业产品，同时保持低配可用和本地私有。**

请确认是否执行，或指出需要调整的地方。
