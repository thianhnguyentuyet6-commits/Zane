# Windows PC 专注计划 - v0914后

> 用户明确：先不做iOS，先把PC Windows做好，前端功能写好，后端基础打牢
> 优先级：测试夯实 > SimpleMem优化 > iOS远程 > 文档重写，iOS延后

## 一、iOS处理 - 默认禁用，保留代码

- `backend/routers/ios.py` 保留，但默认不挂载
- 环境变量 `ZANE_ENABLE_IOS=false` 默认false
- 前端iOS视图保留但隐藏或标注"暂未开放"
- 降低第一版风险，专注Windows

## 二、Windows PC 基础打牢

### 后端基础

#### 1. Windows平台层 - 真实实现加强
- `backend/platform/windows/wmi_provider.py` 已有真实WMI，但需：
  - 添加更多信息：CPU温度、GPU温度、风扇转速
  - 添加进程树：父进程、命令行、签名验证
  - 添加启动项管理：启用/禁用
  - 添加服务管理：启动/停止

- `backend/platform/windows/win32_window.py` 已有真实Win32，但需：
  - 添加窗口操作：移动、缩放、最小化、最大化、关闭
  - 添加DPI感知：GetDpiForWindow，多显示器
  - 添加虚拟桌面支持
  - 添加窗口截图：DWM缩略图

- `backend/tools_impl.py` Windows真实：
  - 文件操作：真实路径，非演示映射
  - 进程操作：真实psutil，路径PID双重验证已做
  - 窗口操作：真实Win32 EnumWindows
  - 截图：真实PIL ImageGrab，多显示器DPI已处理
  - OCR：RapidOCR延迟下载，需测试
  - UIA：需真实Windows测试浏览器、资源管理器、Office

#### 2. 工具注册表 - 26工具全部Windows真实
- 文件6个：list_files/read_file/write_file/delete_file/create_folder/move_file
  - 沙盒realpath+白名单+filelock+回收站+10MB+可撤销+undo端到端
  - 重要性排序最近访问+上次任务引用

- 进程3个：inspect_processes/kill_process/launch_application
  - kill_process安全加固：白名单外可疑+强制确认+路径PID双重验证
  - launch_application白名单+参数注入防护&|;$`

- 窗口3个：list_windows/focus_window/get_window_info
  - 真实HWND Z序DPI置顶缩略图

- 视觉3个：take_screenshot/ocr_screenshot/analyze_ui
  - 截图多显示器DPI统一+窗口/区域模式
  - OCR RapidOCR 50MB延迟下载
  - UIA树分析需Windows测试

- 输入4个：mouse_click/mouse_move/keyboard_input/key_press
  - DPI坐标统一

- 系统1个：get_system_state
  - 真实psutil CPU/内存/磁盘/网络+WMI详细信息

- 剪贴板2个：get_clipboard/set_clipboard

- 网络2个：web_search/verify_info

- 安全2个：security_scan/scan_large_files
  - 漏洞扫描明文密码+高危端口+启动项+弱权限
  - 安全趋势时间序列

#### 3. 记忆层 - 4层统一+SimpleMem+遗忘
- `backend/memory/memory.py` 4层：conversational 100字/episodic 150字/semantic 80字/procedural 120字
- `backend/memory/simple_mem.py` use_llm开关，固定长度离线+LLM高质量可选，重要性排序
- `backend/memory/forgetting.py` 4层曲线7/30/90/180天+阈值+单元测试+DREAMS.md人类可读
- `backend/memory/data_flywheel.py` 过滤评分去重安全，阈值可配置+验证脚本

#### 4. 运行时 - 20文件
- `backend/runtime/resource_monitor.py` 5维度+摄像头麦克风检测会议中+空闲N分钟+CPU/GPU阈值
- `backend/runtime/thinking_budget.py` 两级评估关键词快速+模糊区间LLM确认
- `backend/runtime/data_filter.py` 11危险路径+8文件+7进程+6命令100%安全
- `backend/runtime/skill_gene.py` 变异交叉fitness>0.7保留
- `backend/runtime/planner.py` DAG规划并行只读串行写入
- `backend/runtime/tool_executor.py` 熔断5次+撤销栈
- `backend/runtime/verifier.py` 写后重新感知验证
- `backend/runtime/ralph_loop.py` bash while全新上下文三护栏
- `backend/runtime/bounded_correction.py` 有界自校正UCSL

#### 5. 安全层
- `backend/security/sandbox.py` 文件+进程沙盒realpath+白名单+filelock+回收站+10MB+undo端到端
- `backend/policy_firewall.py` 硬化版NEED_CONFIRM阻断+待确认队列+前端弹窗主动提醒+路径PID验证防伪造
- `backend/security/cybersec_trend.py` 时间序列端口启动项异常感知
- `backend/security/linux_provider.py` WSL沙盒

#### 6. 视觉层
- `backend/vision/dpi_ocr_unified.py` DPI统一+OCR+UIA树，先统一DPI缩放再OCR最后UIA
- `backend/vision/ocr_real.py` RapidOCR延迟下载，首次调用检测缓存询问用户

#### 7. 自主调度器
- `backend/autonomous/scheduler.py` 默认关闭，空闲N分钟+CPU/GPU阈值组合，允许用户关闭，ZANE_AUTO_EVOLVE=false默认

### 前端功能 - 12 JS文件完善

#### 1. 主页面 `frontend/index.html` v0914 111API
- 23视图：控制台、进化仪表盘、模型双轨+8GB、Token+iOS、自主优化、数据库、轨迹、基准真实回放、系统+资源+摄像头、进程安全加固、窗口、文件重要性+undo、记忆use_llm、技能基因、梦境DREAMS、安全过滤+弹窗、契约undo、思考两级、iOS只读（暂隐藏）、设置技术栈
- 已重写为v0914 111API，但需确保所有API调用对齐后端

#### 2. JS模块 12文件
- `app.js` 主逻辑switchView+send+load*，30秒轮询自适应15秒+hidden暂停，import platform_status+pending_modal
- `platform_status.js` 平台状态条Provider真实/演示+不可用工具+demo_mode视觉区分
- `pending_modal.js` 待确认队列前端弹窗，每10秒轮询，自动弹出避免忽略
- `evolution.js` 进化仪表盘SSE重连指数退避+失败不卡转圈+崩溃恢复+8GB支持，18路由对接
- `api.js` API封装
- `charts.js` Canvas交互式图表
- `models.js` 模型管理双轨GGUF+HF+VRAM检测+优先级报错退出+8GB支持
- `system.js` 系统状态+资源监控5维度+摄像头麦克风
- `autonomous.js` 自主优化+空闲检测+默认关闭
- `database.js` 数据库+习惯学习+空闲检测
- `tokens.js` Token管理+iOS专用Token
- `chat.js` 聊天+思考预算两级

#### 3. 前端需要完善的
- 所有视图的load*函数需对齐后端103API（现111API含iOS 8个，禁用后103API）
- API调用错误处理+重试
- 加载状态skeleton+aria
- 空状态empty提示
- 表单验证
- 确认弹窗（删除、kill_process等危险操作）
- 预览Diff（文件操作前）
- WMI图表：CPU每核心折线图Canvas交互式
- 平台状态条：真实/演示区分+黄条+虚线+标签
- 待确认弹窗：主动提醒+批准拒绝

## 三、后端基础打牢 - 具体任务

### P0 - 必须（Windows核心路径测试）

1. **工具真实Windows测试**
   - list_files/read_file/write_file/delete_file/move_file 真实文件系统
   - inspect_processes 真实psutil+WMI详细信息
   - kill_process 安全加固测试：危险进程拦截+路径PID验证+白名单外需确认
   - launch_application 白名单+参数注入防护
   - list_windows/focus_window 真实Win32
   - take_screenshot 多显示器DPI测试
   - get_system_state 真实psutil+WMI

2. **安全拦截真实流程测试**
   - delete_file System32 → PENDING_CONFIRM → 前端弹窗 → 确认 → 审计
   - kill_process csrss.exe → 拦截
   - launch_application 非白名单 → 拦截
   - 参数注入 &|;$` → 拦截

3. **撤销栈端到端测试**
   - delete_file to_recycle=True → 回收站 → undo → 恢复
   - 回收站被清空 → undo失败明确错误
   - 路径权限变化 → undo处理

4. **遗忘曲线单元测试**
   - 构造不同时间戳访问频率记忆
   - 模拟时间流逝检查衰减清除
   - DREAMS.md生成验证

5. **阈值验证**
   - 跑不同阈值0.5-0.9看回放效果
   - 确定合理默认值

6. **真实回放评估**
   - 真实调用agent_runtime执行任务
   - 统计成功率，非模拟冒烟

### P1 - 重要（Windows深度优化）

7. **WMI提供者加强**
   - CPU温度、GPU温度、风扇
   - 进程树父进程命令行签名
   - 启动项启用禁用
   - 服务启动停止

8. **Win32窗口加强**
   - 窗口移动缩放最小化最大化关闭
   - DPI感知多显示器
   - 虚拟桌面
   - DWM缩略图

9. **SimpleMem use_llm开关测试**
   - 固定长度离线可用
   - LLM高质量可选
   - 重要性排序验证

10. **上下文重要性排序验证**
    - 最近访问时间+上次任务引用加权
    - 跑实际任务看效果

11. **复杂度两级评估验证**
    - 关键词快速+模糊区间LLM确认
    - 测试准确度

12. **摄像头麦克风检测验证**
    - 会议中判断
    - 比进程名更可靠

13. **RapidOCR延迟下载测试**
    - 首次调用检测缓存
    - 询问用户是否下载

14. **前端功能完善**
    - 所有视图load*对齐后端
    - 错误处理重试
    - 确认弹窗+预览Diff
    - WMI图表Canvas交互式
    - 平台状态条+待确认弹窗

### P2 - 可选（Windows体验优化）

15. **配置中心**
    - settings/save真实落盘
    - 可配置阈值开关

16. **前端轮询优化**
    - 30秒轮询可接受
    - 复用SSE不必WebSocket

17. **文档**
    - README 12KB精简版快速上手
    - ARCHITECTURE.md 48KB详细架构
    - FILE_TREE.md 28KB文件树

## 四、当前进度

- ✅ 单版本整理完成，真正干净单版本
- ✅ 29条反馈修复，测试夯实优先
- ✅ dev分支+main分支
- ✅ 111API（103+8 iOS），前端12 JS，配置6个，测试7个
- ✅ 核心安全加固：kill_process路径PID验证+待确认弹窗+undo端到端
- ✅ 核心优化：重要性排序+两级评估+摄像头麦克风+8GB支持+崩溃恢复+SSE重连

- ⏳ iOS默认禁用，专注Windows
- ⏳ 前端功能需完善所有视图API对齐
- ⏳ Windows真实测试需在真实Windows环境
- ⏳ 后端基础需打牢WMI+Win32深度

## 五、下一步

1. 禁用iOS路由，默认不挂载
2. 完善Windows平台层WMI+Win32
3. 完善前端所有视图load*函数API对齐
4. 加强后端基础工具真实实现
5. 测试夯实：安全拦截+撤销+遗忘+阈值+真实回放
6. 配置中心可配置阈值开关
7. 前端确认弹窗+预览Diff+WMI图表
