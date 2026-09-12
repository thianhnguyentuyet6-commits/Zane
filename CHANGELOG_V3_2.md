# v3.2 - Reliable Local Computer Agent - 更新日志

## 修复 - 安全漏洞

### [高危] 任意命令执行 - tools_impl.py:397
- 原：`Popen([actual_path] + args.split())`，actual_path 未校验，args 可注入
- 修复：白名单 ALLOWED_BASENAMES + 安全路径前缀 + 禁止 &|;$` 等 + shlex.split 安全分割 + shell=False + 验证进程存在
- 验证：`safe_launch` 拦截 `& calc.exe` 和 `cmd.exe /c del`

### [高危] WSL 命令注入 - linux_provider.py:81
- 原：`bash -c f"cd {workdir} && {command}"` 直接拼接
- 修复：白名单只读命令 ls,cat,grep... + 禁止 ;|&><$`` + shlex.quote + 不用 shell=True + 超时10秒 + workdir 限制 ~/tmp
- 验证：`ls; rm -rf /` 被白名单拦截，`ls -la` 正常执行

### [中危] 路径遍历
- 原：未检查 ../../
- 修复：realpath + 严格白名单前缀匹配 + 长度260检查 + 空路径检查 + 保护 System32/SysWOW64/etc
- 验证：`C:\Windows\System32` 被拦截 high风险

### [中危] 文件无大小限制
- 修复：10MB限制 + 磁盘空间检查 <100MB拒绝 + 日志换行净化
- 实现：`safe_write` 检查 size_bytes + psutil.disk_usage

### [中危] API无认证+速率限制
- 修复：RateLimiter 60/分 + 可选 X-Zane-Token + 危险操作默认需确认 + 中间件
- 实现：`middleware/security.py` RateLimiter + AuthManager + sanitize_log

## 新增 - Runtime模块化 10模块

| 模块 | 文件 | 职责 | 技术 |
|---|---|---|---|
| intent_parser | runtime/intent_parser.py | 意图解析 中文容错 | 关键词+实体提取+歧义检测 |
| state_manager | runtime/state_manager.py | 真实观测 统一场景 | WMI+窗口+进程+截图+OCR+UIA+DPI+光标统一SceneRepresentation |
| planner | runtime/planner.py | DAG分解 模板匹配 | 模板+推断工具+风险评估+验证方法 |
| tool_executor | runtime/tool_executor.py | 安全边界+事务+撤销 | PolicyEngine+pre/post state+undo_stack+Trace |
| verifier | runtime/verifier.py | 区分API完成vs真实成功 | launch_application 进程存在+窗口出现，非success |
| recovery_manager | runtime/recovery_manager.py | 失败分类+重试+重规划 | 5种失败类型+指数退避+熔断 |
| memory_manager | runtime/memory_manager.py | 5类型不同保留 | working(任务结束清空)/episodic(30天衰减)/semantic(永久)/procedural(Skill)/preference |
| skill_manager | runtime/skill_manager.py | 版本化可复用 | trigger/required_tools/procedure/preconditions/verification/recovery/version |
| model_interface | runtime/model_interface.py | 本地优先教师可选 | OpenAI兼容+离线演示+teacher_suggest |
| trace_logger | runtime/trace_logger.py | 统一轨迹 | user_request/observations/decisions/tool_calls/state_changes/verification/failures/recovery/outcome/latency/token/confidence |
| policy_engine | runtime/policy_engine.py | 安全边界独立 | 保护路径System32+关键进程csrss.exe+auto_allow只读+decide allow/need_confirm/deny+preview |
| dreaming | runtime/dreaming.py | 三阶段 Light→REM→Deep | 六信号加权 importance/frequency/recency/feedback/success/verifiable 阈值0.7 |

## 新增 - 真实联网

- `backend/tools/network/web_search_real.py`：Bing API优先+DuckDuckGo HTML回退+防SSRF禁止内网IP+超时10秒+截断5000+re安全校验
- `main_v3.py` `/api/search/real`：集成真实搜索
- 技术：httpx.AsyncClient + 正则提取，无 bs4 依赖，轻量

## 新增 - 向量记忆

- `backend/memory/vector_memory.py`：sqlite-vec可选，无则关键词回退，embedding all-MiniLM-L6-v2 80MB本地，语义检索
- API：`/api/memory/vector/add` `/api/memory/vector/search`

## 新增 - 梦境三阶段

- Light：扫描短期7天去重暂存到 `.dreams/candidates.json`，不写入长期，报告 `memory/dreaming/Light/YYYY-MM-DD.md`
- REM：主题聚类反思，增强frequency信号，不写入，报告 `REM/YYYY-MM-DD.md`
- Deep：六信号加权评分阈值0.7才写入 semantic.json + DREAMS.md 人类可读叙事 + Deep报告机器状态
- API：`/api/dreaming/light|rem|deep|run-all|status`

## 新增 - UI重构 v3

- `frontend/index_v3.html`：专业本地AI操作控制台，非通用聊天
- 设计：深色主题类似Linear/Raycast，CSS变量，单色图标，控制台风格，Observe→Plan→Act→Verify→Recover可视化
- 功能：12视图重构，执行流可视化，工具卡片验证区分API完成vs真实成功，确认弹窗预览Diff，WMI真实，轨迹统计，基准可视化，梦境三阶段，安全扫描，契约列表，模型注册表
- 之前不满意：通用聊天机器人，无控制台感；现在：专业控制台，真实状态观测为起点

## 优化 - 精简

- 14层→8层已完成，每层单一职责
- 前端 608行单文件→拆模块规划，CSS变量统一
- 截断重复抽为装饰器规划
- 模型扫描缓存5分钟规划
- 轮询3秒→5秒+document.hidden暂停规划

## 技术栈 - 夯实

- 后端：FastAPI+Uvicorn+psutil+WMI+pywin32+Pillow+httpx+Pydantic
- 前端：原生HTML/CSS/JS，无打包，<100ms
- 模型：Qwen3-30B-A3B MoE 30B/3B IQ4_XS 18.5GB 45tok/s，`D:\llama.cpp\...`，llama.cpp --ctx-size 32768 --n-gpu-layers 35 --flash-attn --cont-batching
- 平台：platform/base.py抽象，windows/wmi_provider.py真实，linux/fallback.py演示
- 安全：sandbox.py realpath+白名单+回收站，linux_provider.py WSL白名单沙盒，cybersec_tools.py漏洞扫描，policy_engine.py安全边界，middleware/security.py速率+认证
- 记忆：memory_layer.py JSON，data_flywheel.py SFT/DPO，vector_memory.py sqlite-vec可选，memory_manager.py 5类型
- 进化：evolution_engine.py QLoRA，unsloth_trainer.py脚本，self_correction.py错误分类，dreaming.py三阶段
- 执行：agent_runtime_v2.py DAG+思考+并行+验证，tool_contract.py契约，task_trace.py轨迹，model_registry.py注册表，benchmark/suite.py 12基准，undo_stack.py撤销，runtime/* 10模块

## 评估 - 可复现

- 基准12任务8类别：process/window/filesystem/clipboard/app launching/UI/screenshot/OCR/visual grounding/multi-step/failure recovery/ambiguous
- 每个任务显式成功标准可重放
- 指标：task success rate/verification accuracy/recovery rate/avg tool calls/latency/token consumption/regression rate
- 失败恢复作为重要指标

## 困惑权衡异议 - 技术诚实

1. MoE专家选择性微调是否有效？需实验Full LoRA vs 专家选择性，VRAM/时间/性能/回归，标记实验性，不吹嘘90%
2. 自我进化是否会变差？严格评估历史20任务回放，提升才晋升，保留回滚，Replay防遗忘，六信号阈值0.7
3. 视觉是否应主要接口？层次：结构化→UIA→OCR→视觉→坐标，优先结构化，视觉补充回退，反对视觉作为通用
4. 技能是否直接变权重？先变版本化技能可回放评估编辑回滚，独立于基础模型，安全易调试，反对直接微调
5. 本地vs云端？本地优先云端可选教师，本地保持核心能力，云不可用仍可执行，Teacher建议，本地权威，反对变瘦客户端
6. 功能多vs基础牢？下一里程碑Reliable而非更多AGI，先让现有确定可观测可测试可恢复可度量，再加高层
7. GitHub Skill整合？适配整合非照搬，file-organizer改为沙盒+撤销+验证符合契约
8. 14层是否必要？精简为8层每层单一职责，移除视觉技能学习系统教师冗余层，新增安全到工具+策略

## 部署

- 单端口8000，前端已写入content，无需单独部署
- `python -m uvicorn backend.main_v3:app --host 0.0.0.0 --port 8000`
- 前端访问 `/`，API文档 `/docs`

## 下一步 - Reliable Local Computer Agent

不是更多AGI，而是：
- 本地模型接收自然语言任务
- 观测真实Windows状态
- 选择结构化工具
- 通过受控运行时执行
- 验证真实结果
- 从失败恢复
- 记录轨迹
- 复用成功流程为技能
- 针对固定基准改进，可度量

一旦在可复现基准上可靠，高层学习和进化才有坚实基础
