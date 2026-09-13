# Zane v0914 实施计划 - 基于29条反馈

## 优先级：测试夯实 > SimpleMem优化 > iOS远程 > 文档重写

### 已完成
- ✅ dev分支创建
- ✅ 单版本整理彻底完成

### P0 - 测试夯实（必须）

#### 1. 模型路径优先级 - 环境变量>配置>默认，找不到报错退出
- 文件：backend/learning/model_resolver.py
- 现状：已有优先级，但占位不报错
- 修改：添加strict模式，找不到时抛出异常，run.py中捕获报错退出
- 添加：get_model_or_fail()方法

#### 2. 调度器 - 空闲N分钟+CPU/GPU阈值，默认关闭自动微调
- 文件：backend/autonomous/scheduler.py + config/evolution_schedule.json
- 现状：凌晨2点固定+30分检查，enabled默认True
- 修改：默认enabled=False，添加idle_minutes检测，CPU/GPU阈值，允许用户关闭，提供API开关
- 新增：idle检测逻辑，last_user_activity

#### 3. HF训练 - 不自动下载，检测缓存提示确认
- 文件：backend/learning/model_resolver.py + backend/learning/unsloth_trainer.py
- 修改：resolve_hf_path检测本地，不存在返回need_download=True，trainer中检查并提示，不自动下载

#### 4. 训练Popen - 崩溃重启+状态恢复+SSE重连
- 文件：backend/learning/unsloth_trainer.py + backend/routers/evolution.py + frontend/js/evolution.js
- 新增：训练状态持久化training_state.json，崩溃检测重启3次，SSE前端重连指数退避，失败状态推送

#### 5. 阈值0.8可配置+验证脚本
- 文件：config/replay_config.json + backend/learning/replay_buffer.py + tests/test_threshold_validation.py
- 新增：配置文件，验证脚本跑不同阈值0.5/0.6/0.7/0.8/0.9看回放效果

#### 6. 真实回放评估 - agent_runtime执行
- 文件：tests/test_eval_real.py + backend/benchmark/evolution_eval.py
- 新增：真实调用agent_runtime执行eval_tasks.jsonl，统计成功率，替换模拟

#### 7. 遗忘曲线单元测试
- 文件：tests/test_forgetting.py
- 新增：构造不同时间戳访问频率记忆，模拟时间流逝检查衰减清除

#### 8. 安全 - kill_process白名单外+强制确认+进程名伪造防护
- 文件：backend/tools_impl.py + backend/policy_firewall.py + backend/security/sandbox.py
- 修改：kill_process默认只允许白名单外可疑进程，强制走确认队列，添加进程路径+PID双重验证，不只按名字

#### 9. 待确认队列前端弹窗
- 文件：frontend/js/app.js + frontend/index.html + backend/routers/security.py
- 新增：前端弹窗提醒待确认队列，轮询pending，modal显示风险等级+操作详情，确认/拒绝按钮

#### 10. undo_stack端到端测试
- 文件：tests/test_undo_e2e.py + backend/policy/undo_stack.py
- 新增：测试回收站被清空、路径权限变化等边界

#### 11. index.html重写 - 103API单版本
- 文件：frontend/index.html
- 现状：旧版51路由内容
- 修改：重写为v0913 103API 23视图+平台状态条，路由数量对齐后端

#### 12. evolution.js SSE重连
- 文件：frontend/js/evolution.js
- 新增：SSE连接中断重连指数退避，训练进程异常退出前端正确收到失败状态，不卡转圈

### P1 - 深度优化

#### 13. SimpleMem use_llm开关
- 文件：backend/memory/simple_mem.py + config/simplemem.json
- 新增：use_llm开关，默认False固定长度，有算力用户True用LLM压缩，配置

#### 14. 上下文截断重要性排序
- 文件：backend/tools_impl.py + backend/runtime/state_manager.py
- 修改：_context_budget_truncate按最近访问时间+是否被上次任务引用加权排序，不只按数量

#### 15. 复杂度两级评估
- 文件：backend/runtime/thinking_budget.py
- 修改：关键词快速判断，模糊区间再LLM确认，兼顾速度准确性

#### 16. 摄像头/麦克风检测会议中
- 文件：backend/runtime/resource_monitor.py
- 新增：检测摄像头麦克风占用状态判断会议中，比进程名更可靠

#### 17. RapidOCR延迟下载
- 文件：backend/vision/ocr_real.py + backend/vision/dpi_ocr_unified.py
- 修改：首次调用检测本地缓存，没有询问用户是否下载，不放主安装脚本

#### 18. DREAMS.md检查
- 文件：backend/memory/forgetting.py + docs/
- 检查：是否实际生成逻辑，没有则README去掉描述或补最小实现

### P2 - 功能完善

#### 19. iOS只读远程查看
- 文件：backend/routers/system_router.py + config/ios_config.json
- 新增：POST /api/ios/report {viewing}，iOS前端只读页面，REST/SSE轮询订阅，不做控制

#### 20. iOS专用Token
- 文件：backend/middleware/jwt_auth.py + backend/routers/auth.py
- 新增：iOS专用Token短有效期可远程吊销，不与Web共用JWT

#### 21. 截图多显示器DPI测试
- 文件：tests/test_screenshot_dpi.py
- 新增：手动测试多显示器不同DPI缩放坐标计算

### P3 - 文档与分支

#### 22. legacy保留说明
- 已完成归档，添加README说明仅供参考不再维护

#### 23. README分层
- 已完成：12KB精简版 + ARCHITECTURE.md 48KB详细

#### 24. dev分支
- ✅ 已创建dev分支，破坏性操作先在dev验证

### 验证
- pip install -r requirements.txt && python run.py
- python tests/test_forgetting.py
- python tests/test_threshold_validation.py
- python tests/test_undo_e2e.py
- python tests/test_eval_real.py
- 前端：http://localhost:8000/ 检查103API + 平台状态条 + 待确认弹窗 + SSE重连
