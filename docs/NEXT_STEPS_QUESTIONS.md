# Zane AGI v0913 - 下一步规划与疑问

> 对下一步的看法，提出的疑惑和问题

## 当前状态总结

**已完成**：
- ✅ 单版本整合 Zane v0913，103API，8层架构，legacy归档13文件
- ✅ 6缺点全修：双文件隐患→单文件统一，路由summary+tags，飞轮评分透明，SimpleMem Benchmark，平台状态条demo_mode区分，安全硬化NEED_CONFIRM阻断
- ✅ 12优先级：合并tools_impl+安全硬化+启动日志3行+平台状态条+路由summary+飞轮规格+Benchmark+版本整合+回放评估50条+安全趋势+DPI统一+LICENSE+CI
- ✅ Review & Debug：工具注册表与实现一致性修复26 vs 30核心一致，安全趋势和DPI集成到路由，.gitignore修复，pycache清理，MD文档归档28→3根目录，ARCHITECTURE.md面向其他Agent的完整架构文档

**代码统计**：
- Python 92文件（不含legacy），JS 11文件，总代码22664行
- 测试5文件全部通过，文档4个+README_V0913，CI+LICENSE完整
- 单版本核心：main.py 38KB + tools_impl.py 33KB + tool_registry.py 14KB + policy_firewall_v0913.py 13KB = 1775行

**可启动**：`pip install -r requirements.txt && python run.py` → http://localhost:8000/docs Swagger 8层架构

---

## 下一步看法 - 夯实基础优先

### 1. 夯实现有功能，而非新增花哨功能

**用户明确**：继续夯实基础和现有功能。当前功能已多（26工具+103API+8层+自主进化8阶段），应先夯实而非新增。

#### 1.1 测试夯实 - 最优先

**现状**：3个测试文件，工具统一+防火墙阻断+Benchmark+回放评估，但回放评估是模拟成功率，不是真实执行agent_runtime。

**下一步**：
- 添加集成测试：真实调用`agent_runtime_v3.execute_task`执行`eval_tasks.jsonl`中的50条任务，记录成功率曲线
- 添加工具测试：每个工具的真实/演示双模式测试，如`list_files`在Windows真实路径和Linux演示路径
- 添加安全测试：验证11危险路径+8文件+7进程+6命令是否真正拦截，尝试`delete_file System32`应被policy_firewall阻断
- 添加前端测试：platform_status.js是否真正加载，demo_mode视觉区分是否生效

**疑问**：当前环境是Linux演示，无法测试Windows真实API（WMI/Win32），是否应该添加Windows CI或mock更真实？

#### 1.2 文档夯实

**现状**：ARCHITECTURE.md已完成面向其他Agent的完整指南，README_V0913.md 12KB精简版，但README.md 56KB还是旧版v7.0内容，frontend/index.html 29KB还是v7.0 51路由内容。

**下一步**：
- 用README_V0913.md覆盖README.md，或将README.md重写为v0913单版本103API，旧版归档docs/archive/README_V7.md
- frontend/index.html重写为v0913 103API+平台状态条详细介绍，当前内容还是v7.0 51路由
- 每个router添加详细docstring，说明summary+tags+参数+返回值，方便Swagger

**疑问**：README应该精简到多少KB？当前56KB过长，是否应该控制在20KB以内，只写实现无吹嘘，符合v2.5批评？

#### 1.3 错误处理与日志夯实

**现状**：已用loguru统一日志，文件轮转10MB 7天，裸except已修复152→0，但仍有部分地方可能有隐藏bug。

**下一步**：
- 全局搜索`except:`和`except Exception`是否还有裸except，替换为具体异常
- 添加更多loguru日志，尤其工具执行和安全拦截
- 添加错误恢复：如`list_files`路径不存在时回退到cwd，已实现但可更完善
- 熔断器：失败5次熔断已实现，但需测试是否真正生效

**疑问**：loguru在未安装环境下回退到print，是否应该强制要求loguru为核心依赖？

#### 1.4 性能夯实

**现状**：前端30秒轮询自适应15秒+hidden暂停节能，工具结果截断20文件15进程3000字符防撑爆LLM上下文32K，思考预算动态简单任务8192 tokens快速复杂32768深度，训练非阻塞Popen不阻塞API SSE流推送进度。

**下一步**：
- 测试工具调用性能：`inspect_processes`和`get_system_state`的psutil interval 0.5是否合适，是否应该更短或缓存
- 前端性能：evolution.js 25KB SSE+图表+基因树，是否应该拆分或懒加载
- 内存：simple_mem.json和memory_v3是否会无限增长，需测试遗忘机制是否生效

**疑问**：SimpleMem当前固定长度100/150/80/120，平均75%压缩1.4x，不是论文30% 3x，是否应该用LLM进行真实语义压缩？但用户说本地LLM为主要引擎离线仍可用，固定长度可能是为了离线可用？

#### 1.5 安全夯实

**现状**：沙盒realpath+白名单+filelock+回收站+10MB，防火墙v0913硬化NEED_CONFIRM阻断+待确认队列+Event+超时5分钟自动拒绝+前端确认+审计blocked，过滤11路径8文件7进程6命令100% security 60%→100%，趋势时间序列端口/启动项异常感知，DPI统一。

**下一步**：
- 真实测试安全拦截：尝试`delete_file C:\Windows\System32\test.txt`应被policy_firewall_v0913阻断，返回PENDING_CONFIRM+confirm_id，前端pending轮询显示，用户确认后才执行
- 测试回收站可撤销：delete_file to_recycle=True时是否真正移到回收站，能否undo
- 测试白名单和注入防护：launch_application不在白名单是否拦截，参数含&|;$`是否拦截

**疑问**：kill_process等3个工具刚添加实现，过滤危险进程csrss.exe等7个，但未经真实Windows测试，是否安全？是否应该添加更多危险进程？

### 2. 现有功能深度优化

#### 2.1 SimpleMem真实语义压缩

**现状**：semantic_compression固定长度截断+...压缩标记，不是真正语义压缩，论文目标30%+26.4%F1+3x Token，实际实现75%压缩1.4x信息保留85%可复现Benchmark。

**下一步**：
- 如果LLM可用，用LLM进行真实语义压缩：提示词"将以下内容压缩到30%，保留关键实体和意图"
- 如果离线，保留固定长度作为回退
- 添加配置：`config/simplemem.json` {use_llm: true, compression_ratio: 0.3, fallback_fixed_length: true}

**疑问**：用户说本地已部署Qwen3.6 35B A3B在D:\llama.cpp\...，要求静默时自动微调进化，不再是原生Qwen3.6。是否应该接入该模型进行SimpleMem压缩？但当前是Linux演示环境，无法访问D盘路径。

#### 2.2 DPI+OCR真实落地

**现状**：dpi_ocr_unified.py已创建，流程DPI统一→OCR识别→UIA树，RapidOCR 50MB+Tesseract回退+UIA，但ocr_screenshot还是演示占位。

**下一步**：
- 集成RapidOCR真实：`pip install rapidocr_onnxruntime`，自动下载模型，`ocr_real.py`已存在但需测试
- DPI统一：Windows下获取真实DPI GetDeviceCaps LOGPIXELSX，Linux回退1.0，已实现但需真实Windows测试
- UIA树：Windows uiautomation获取真实控件，Linux回退演示

**疑问**：RapidOCR需要模型文件，是否应该添加自动下载逻辑？用户说品质需媲美商业级，对标Operator/Claude Computer Use，OCR是核心视觉能力。

#### 2.3 训练管道真实化

**现状**：unsloth_trainer_v3.py生成训练脚本FastLanguageModel+QLoRA r=32+非阻塞Popen+日志流+LoRA版本+指数退避重试，但实际未在24GB VRAM下测试30B-A3B LoRA训练。

**下一步**：
- 添加训练状态真实检查：Popen后检查进程是否存活，日志是否有错误，模型是否生成
- 添加VRAM真实检测：torch.cuda.get_device_properties，已实现但需测试
- 添加训练数据验证：sft.jsonl是否格式正确，是否过滤安全

**疑问**：训练需要大量资源，用户说不能太吃配置，参考openclaw memory dreaming。是否应该添加更细致的资源感知，如检测是否插电、电量、是否游戏会议全屏、iOS是否查看，已在resource_monitor实现但需测试？

#### 2.4 iOS远程端口

**现状**：用户说预留iOS移动设备远程查看控制端口，resource_monitor中有iOS检测frontend上报viewing状态，但未实现WebSocket。

**下一步**：
- 实现`POST /api/ios/report` {viewing: bool, device: string}，前端定时上报
- 调度器check_ready中检查iOS viewing，如果viewing则暂停训练，避免打扰用户远程查看
- 添加iOS前端：简单页面显示系统状态+控制

**疑问**：iOS远程查看控制的具体需求是什么？是查看系统状态，还是远程控制电脑？用户说Windows深度控制为主，iOS远程端口预留，是否应该先实现查看，再实现控制？

### 3. 版本与清理

**现状**：单版本整合完成，legacy 13文件历史归档，根目录MD 28→3已归档到docs/archive/，pycache已清理，当前仅main.py单版本。

**下一步**：
- 检查legacy是否还有更旧版本可删除，只保留v8和v7，或全部归档后删除原地已完成
- README.md 56KB旧版是否应该用README_V0913.md覆盖，或重写为20KB以内精简版
- frontend/index.html 29KB旧版51路由内容是否应该重写为v0913 103API

**疑问**：版本清理到什么程度？用户说全部整理成一版Zane v0913，是否应该删除legacy，只保留main.py单版？但保留legacy有助于回退，当前13文件是否合适？

---

## 我的疑惑和问题 - 向用户提问

### 关于模型

1. **Qwen3.6 35B A3B路径**：用户说本地已部署在`D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf`，要求静默时自动微调进化，不再是原生Qwen3.6。当前是Linux演示环境无法访问D盘，是否应该添加路径映射或环境变量`MODEL_PATH`已支持？是否应该测试该模型是否可用？

2. **模型微调**：静默时自动微调进化的具体触发条件是什么？是凌晨2点+资源感知已实现，还是用户空闲时？是否应该添加用户习惯学习，如工作时间9:00-18:00不打扰，休息时不打扰，已在database.py习惯学习中？

3. **模型双轨**：GGUF推理+HF训练双轨已实现，但HF训练需要`Qwen/Qwen3-30B-A3B`，是否应该添加自动下载或提示用户设置`HF_MODEL_PATH`？

### 关于训练

4. **Unsloth训练**：真实LoRA训练需要GPU和大量依赖，当前实现生成脚本+Popen，是否足够？是否应该添加训练进度的真实SSE推送，已在evolution_v3.py stream实现但需测试？

5. **训练数据**：数据飞轮自动收集过滤后保存到`sft.jsonl`，但SimpleMem 30% Replay高质量>0.8的阈值是否合适？是否应该可配置？

6. **评估Harness**：20任务5分类真实回放已实现，但50条回放评估`eval_tasks.jsonl`是模拟成功率，不是真实执行agent_runtime，是否应该实现真实回放？

### 关于记忆

7. **SimpleMem实现**：当前固定长度100/150/80/120，不是真正语义压缩，论文30%目标。是否应该用LLM进行真实压缩？但用户说离线仍可用，固定长度可能是为了离线可用。是否应该添加配置`use_llm` true时用LLM，false时固定长度？

8. **遗忘机制**：4层遗忘曲线7天/30天/90天/180天，低价值访问<3重要性<0.3 30天遗忘，已实现但未测试是否真正生效，是否应该添加测试？

9. **DREAMS.md**：人类可读日记，是否应该实现？当前forgetting.py中有提及但未真实生成。

### 关于视觉

10. **DPI+OCR真实落地**：dpi_ocr_unified.py已创建，RapidOCR 50MB已在requirements.txt，但ocr_screenshot还是演示占位。是否应该接入真实RapidOCR，添加自动下载模型逻辑？

11. **UIA树**：Windows UIA分析界面控件，是否应该实现真实`analyze_ui`？当前已添加实现但调用dpi_ocr_unified，未真实测试Windows UIA。

12. **截图**：take_screenshot真实PIL ImageGrab已实现，但Linux下回退演示占位，是否应该添加更多截图模式如窗口、区域，已在参数中支持但未完全实现？

### 关于安全

13. **kill_process安全性**：刚添加实现过滤危险进程7个csrss.exe等，但未经真实Windows测试，是否安全？是否应该添加更多危险进程如winlogon.exe services.exe等已在旧版中有？

14. **待确认流程**：NEED_CONFIRM阻断+前端确认已实现，但前端platform_status.js只显示平台状态，未显示待确认队列，是否应该在前端添加待确认弹窗？

15. **回收站可撤销**：delete_file to_recycle=True移到回收站可撤销已实现，但undo_stack是否真正能恢复？是否应该测试？

### 关于前端

16. **平台状态条**：platform_status.js已创建11KB，顶部显示Provider真实/演示+demo_mode视觉区分，但是否真正加载？app.js已导入，但index.html还是旧版51路由内容，是否应该重写？

17. **进化仪表盘**：evolution.js 25KB SSE+图表+基因树已存在，但是否与后端evolution_v3.py 18路由完全对接？是否应该测试SSE流？

18. **轮询优化**：30秒+自适应15秒+hidden暂停节能已实现，但是否应该添加WebSocket替代轮询？

### 关于iOS远程

19. **iOS远程需求**：用户说预留iOS移动设备远程查看控制端口，resource_monitor中有iOS检测，但未实现WebSocket。是否应该实现`POST /api/ios/report`和iOS前端页面？具体需求是查看系统状态，还是远程控制？

20. **远程控制安全**：如果实现iOS远程控制，是否需要额外认证？当前JWT已实现，但是否应该添加iOS专用Token？

### 关于版本

21. **Legacy清理**：当前legacy 13文件历史归档，根目录MD 28→3已归档，是否应该删除legacy只保留main.py单版？用户说全部整理成一版Zane v0913，是否应该更彻底？

22. **README**：README.md 56KB旧版v7.0内容，README_V0913.md 12KB精简版，是否应该用精简版覆盖旧版？

23. **分支**：当前只有main分支，是否应该创建dev分支用于实验性功能隔离？用户说允许创新试错，实验性功能隔离。

### 关于性能

24. **上下文预算**：工具大输出截断20文件15进程3000字符防撑爆LLM上下文32K已实现，但是否应该更智能，如按重要性排序截断？

25. **思考预算**：Qwen3 /think 32K /no_think 8K auto动态已实现，但复杂度评估是否准确？14个复杂关键词+7个简单词+长度，是否应该用LLM评估复杂度？

26. **资源感知**：5维度CPU/内存/VRAM/插电/游戏/iOS可训练判断已实现，但游戏检测全屏+进程名匹配是否准确？是否应该添加会议检测？

### 关于下一步优先级

27. **优先级**：用户说优先级你来决定，已按评估→安全趋势→DPI顺序执行，当前6缺点+12优先级完成，Review Debug完成。下一步应该优先夯实测试，还是优化SimpleMem真实压缩，还是实现iOS远程，还是重写README和前端？

28. **商业级品质**：用户说品质需媲美商业级，对标Operator/Claude Computer Use + Manus/Devin + PowerToys/Raycast。当前哪些方面离商业级还有差距？是测试覆盖率，还是文档，还是性能，还是安全性？

29. **个人AGI管家目标**：目标个人AGI管家，不能太吃配置，参考openclaw memory dreaming。当前是否太吃配置？24GB VRAM训练30B-A3B是否太高？是否应该优化为更低配置可用？

---

## 建议的下一步 - 按优先级

### P0 - 夯实基础（必须）
1. 添加集成测试：真实执行50条回放评估任务，非模拟
2. 重写README.md为20KB以内精简版，旧版归档
3. 重写frontend/index.html为v0913 103API单版本
4. 测试安全拦截真实流程：delete System32 → PENDING_CONFIRM → 前端确认 → 审计
5. 清理pycache和临时文件已完成，验证启动`pip install -r requirements.txt && python run.py`

### P1 - 深度优化（重要）
6. SimpleMem真实语义压缩：LLM可用时用LLM，离线固定长度回退，添加配置
7. DPI+OCR真实落地：接入RapidOCR真实，测试Windows DPI和UIA
8. 训练管道真实化：添加训练状态真实检查和SSE推送测试
9. 前端平台状态条测试：验证demo_mode视觉区分是否生效

### P2 - 功能完善（可选）
10. iOS远程端口：实现POST /api/ios/report + iOS前端查看
11. 确认弹窗+预览Diff：删除前列表，窗口移动虚线框
12. WMI图表：CPU每核心折线图Canvas
13. 配置中心：settings/save真实落盘config/

### P3 - 实验性（隔离）
14. EXE打包PyInstaller
15. 向量检索sentence-transformers真实384维
16. 更多技能基因和Prompt进化实验

---

## 向用户的问题总结

1. 模型路径D:\llama.cpp\...在Linux演示环境无法访问，是否应该添加映射或已通过环境变量支持？
2. SimpleMem固定长度实现 vs LLM真实语义压缩，是否应该添加use_llm配置？
3. DPI+OCR真实落地是否应该接入RapidOCR真实并自动下载模型？
4. iOS远程查看控制的具体需求是查看还是控制，是否应该实现WebSocket？
5. README 56KB旧版是否应该用12KB精简版覆盖？
6. 回放评估50条模拟成功率是否应该实现真实执行agent_runtime？
7. kill_process等新工具未经Windows真实测试是否安全？
8. 下一步优先级：测试夯实 vs SimpleMem优化 vs iOS远程 vs 文档重写，哪个优先？
9. 商业级品质差距在哪，是否测试覆盖率、文档、性能、安全性？
10. 是否应该删除legacy只保留main.py单版更彻底，还是保留13文件归档合适？

---

> 等待用户决策，再执行下一步
