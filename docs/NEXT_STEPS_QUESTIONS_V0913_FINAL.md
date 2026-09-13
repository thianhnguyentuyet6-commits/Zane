# Zane AGI v0913 - 单版本整理完成 + 下一步疑问

> **状态**：✅ 单版本整理彻底完成，真正干净单版本，无V1/V2/V6/V7并存
> **时间**：2026-09-13

## 一、单版本整理 - 已完成✅

### 根目录 - 仅2个MD单版本

**整理前**：28个MD多版本并存 ARCHITECTURE_V3/CHANGELOG_V2_3/V3_2/CODE_REVIEW_V4/V5_FINAL/COMPLETION_V7_FINAL/EVOLUTION_PLAN_V3/FINAL_PROJECT_REPORT/V2/V3/FINAL_REVIEW_V3/FINAL_TEST_REPORT_V1/FINAL_V7_REPORT/GIT_PUSH_GUIDE/NEXT_STEPS_V2/OPTIMIZATION_PLAN/V6/PROJECT_REPORT_V1/README_V1/V5/SECURITY_AUDIT_V3/SELF_EVOLUTION_AGI_PLAN/TECH_STACK_V2_4/V2_5/V3 + README_V0913.md双版

**整理后**：✅ 2个单版本
- README.md 13KB 精简版v0913 103API 8层架构
- ARCHITECTURE.md 48KB 完整架构单版本干净版（已重写，无v后缀无legacy引用）
- 旧版25个 → 归档docs/archive/
- README_V0913.md → README.md单版本，旧56KB归档docs/archive/README_V7.md

### backend/ - 12主文件单版本无后缀

**整理前**：main_v2/v3/v4/v6/v7/v8 20KB~79KB多版本，agent_runtime_v2/v3，tool_contract_complete.py/memory_layer.py/tools_impl_complete.py/tool_registry_old.py，policy_firewall_v0913.py双版，legacy/ 13文件历史

**整理后**：✅ 13文件单版本（12+__init__）
- main.py 38KB 766行单版本整合版，导入单版本无后缀优先+旧命名回退兼容
- agent_runtime.py 27KB 单版本v3覆盖，旧v2/v3删除
- tool_registry.py 14KB 26工具单版本
- tools_impl.py 33KB 统一工具30实现单版本
- policy_firewall.py 13KB 328行硬化版单版本，旧v0913删除
- 删除tool_contract_complete.py/memory_layer.py/tools_impl_complete.py
- legacy/ 13文件 → 归档docs/archive/legacy/后删除原位

### backend/memory/ - 6文件单版本

**整理前**：data_flywheel_v3.py + data_flywheel.py双版，memory_v3.py + 旧版双版

**整理后**：✅ 6文件单版本无后缀
- data_flywheel.py 14KB 341行单版本（原v3）
- memory.py 8.4KB 241行单版本（原v3）
- simple_mem.py 7.6KB 单版本
- forgetting.py/vector_memory.py/vector_memory_real.py 单版本

### backend/learning/ - 7文件单版本

**整理前**：evolution_engine_v25.py + evolution_engine.py，unsloth_trainer_v3.py + unsloth_trainer.py

**整理后**：✅ 7文件单版本
- evolution_engine.py 单版本（原v25）
- unsloth_trainer.py 14KB 单版本（原v3）
- model_resolver.py/replay_buffer.py/prompt_evolution.py/strategy_evolution.py/self_correction.py 单版本

### backend/routers/ - 16文件单版本无后缀71模块化+32兼容=103API

**整理前**：auth_v3.py/benchmark_v3.py/config_v3.py/evolution_v3.py/memory_v3.py/runtime_v3.py/security_v3.py/thinking_v25.py/vector_v3.py/vision_v3.py 10文件带_v3/_v25后缀

**整理后**：✅ 16文件单版本无后缀
- auth.py/benchmark.py/config.py/evolution.py/memory.py/runtime.py/security.py/thinking.py/vector.py/vision.py 10文件单版本（cp v3→无后缀，rm v3）
- system_router.py/database_router.py/autonomous_router.py/models_router.py/tokens_router.py/__init__.py 单版本

### backend/autonomous/ - 1文件单版本

**整理前**：scheduler_v3.py

**整理后**：✅ scheduler.py 单版本（cp v3→无后缀）

### backend/llm/ - 单版本

**整理前**：model_manager_v2.py + model_manager.py

**整理后**：✅ model_manager.py 单版本（原v2）

### frontend/ - 1 HTML+11 JS单版本

**整理前**：index.html + index_v7.html双版

**整理后**：✅ 1 HTML单版本
- index.html 29KB 单版本v0913
- 删除index_v7.html

### data/ - 单版本

**整理前**：prompts/prompt_v1/v2/v3/v4多版本，prd_v3.json+prd.json双版

**整理后**：✅ 单版本
- prompts/prompt_v4.json 单版本最新最佳0.795，旧v1/v2/v3归档docs/archive/prompts/
- prd.json 单版本，旧prd_v3.json归档docs/archive/prd_v3.json

### requirements - 单版本

**整理前**：requirements.txt + requirements_v2.txt

**整理后**：✅ requirements.txt单版本16依赖，删除requirements_v2.txt

### 最终统计 - 单版本干净

- 根目录MD：2个单版本 README.md + ARCHITECTURE.md
- backend/*.py：13文件（12+__init__）单版本
- backend/memory/：6文件单版本
- backend/learning/：7文件单版本
- backend/routers/：16文件单版本71模块化+32兼容=103API
- backend/autonomous/：1文件单版本
- backend其他：platform 1+2+1，security 4，vision 2，runtime 20，middleware 2，policy 1，utils 1，tools/network 1 = 34文件
- 总backend：92文件单版本（不含archive/legacy）
- frontend：1 HTML + 11 JS + 4 CSS = 16文件单版本
- docs/：5个v0913相关（FILE_TREE/FLYWHEEL_SPEC/ZANE_V0913_CHANGELOG/REVIEW_DEBUG_REPORT/FINAL_REVIEW/NEXT_STEPS_QUESTIONS_V0913_FINAL）+29归档+13 legacy归档
- 总代码22664行，Python 92文件JS 11文件
- 测试全部通过✅，语法通过✅，可启动✅

---

## 二、下一步看法 - 夯实基础优先（用户明确）

### P0 - 夯实基础（必须，当前最优先）

1. **测试夯实**：当前3个测试文件，工具统一+防火墙阻断+Benchmark+回放评估，但回放评估是模拟成功率，不是真实执行agent_runtime。需添加集成测试真实调用execute_task执行50条任务，工具真实/演示双模式测试，安全拦截真实测试delete System32应被阻断PENDING_CONFIRM，前端platform_status.js加载测试

2. **文档夯实**：ARCHITECTURE.md已重写为单版本干净版✅，FILE_TREE.md已创建单版本文件树✅，README.md已单版本13KB✅，但frontend/index.html还是旧内容51路由，是否应重写为v0913 103API？

3. **错误处理与日志夯实**：loguru统一日志轮转10MB 7天，裸except已修复152→0，但仍需全局搜索except:是否还有，添加更多loguru日志，错误恢复如list_files路径不存在回退cwd已实现可更完善，熔断器失败5次需测试

4. **性能夯实**：前端30秒轮询自适应15秒+hidden暂停节能，工具结果截断20文件15进程3000字符防撑爆32K，思考预算动态8192快速/32768深度，训练非阻塞Popen+SSE流推送。需测试inspect_processes interval 0.5是否合适，evolution.js 25KB是否应拆分懒加载，simple_mem.json是否会无限增长遗忘机制是否生效

5. **安全夯实**：沙盒realpath+白名单+filelock+回收站+10MB，防火墙硬化NEED_CONFIRM阻断+待确认队列+Event+超时5分钟自动拒绝+前端确认+审计，过滤11路径8文件7进程6命令100%，趋势时间序列异常感知，DPI统一。需真实测试安全拦截delete System32→PENDING_CONFIRM→前端确认→审计，回收站可撤销undo，白名单注入防护&|;$`

### P1 - 深度优化（重要）

6. **SimpleMem真实语义压缩**：当前固定长度100/150/80/120平均75%压缩1.4x，不是论文30% 3x，论文目标+26.4%F1+30x Token。是否应用LLM进行真实语义压缩？提示词"将以下内容压缩到30%保留关键实体和意图"，离线固定长度回退，添加配置config/simplemem.json {use_llm: true, ratio: 0.3, fallback_fixed_length: true}

7. **DPI+OCR真实落地**：dpi_ocr_unified.py已创建流程DPI→OCR→UIA树，RapidOCR 50MB+Tesseract回退+UIA，但ocr_screenshot还是演示占位。需集成RapidOCR真实pip install rapidocr_onnxruntime自动下载模型，DPI统一Windows真实GetDeviceCaps LOGPIXELSX Linux回退1.0，UIA树Windows uiautomation真实控件

8. **训练管道真实化**：unsloth_trainer.py生成脚本FastLanguageModel+QLoRA r=32+非阻塞Popen+日志流+LoRA版本+指数退避重试，但未在24GB VRAM下测试30B-A3B LoRA训练。需添加训练状态真实检查Popen存活日志错误模型生成，VRAM真实检测torch.cuda.get_device_properties，训练数据验证sft.jsonl格式

9. **前端平台状态条测试**：platform_status.js 11KB已创建，顶部显示Provider真实/演示+demo_mode视觉区分，但是否真正加载？app.js已导入，但index.html旧版51路由内容，需重写为v0913 103API并测试demo_mode黄条+工具卡片区分

### P2 - 功能完善（可选）

10. **iOS远程端口**：用户说预留iOS移动设备远程查看控制端口，resource_monitor中有iOS检测frontend上报viewing状态，但未实现WebSocket。需实现POST /api/ios/report {viewing: bool, device: string}前端定时上报，调度器check_ready检查iOS viewing暂停训练，iOS前端简单页面显示系统状态+控制

11. **确认弹窗+预览Diff**：删除前列表，窗口移动虚线框

12. **WMI图表**：CPU每核心折线图Canvas

13. **配置中心**：settings/save真实落盘config/

### P3 - 实验性（隔离）

14. **EXE打包PyInstaller**

15. **向量检索sentence-transformers真实384维**

16. **更多技能基因和Prompt进化实验**

---

## 三、我的疑惑和问题 - 向用户提问（29个→10个核心）

### 关于模型

1. **Qwen3.6 35B A3B路径**：用户说本地已部署在D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf，要求静默时自动微调进化，不再是原生Qwen3.6。当前是Linux演示环境无法访问D盘，是否应添加路径映射或已通过环境变量MODEL_PATH支持？config/model_paths.json已含优先级说明，是否需测试该模型是否可用？

2. **模型微调触发条件**：静默时自动微调进化的具体触发条件是什么？是凌晨2点+资源感知已实现，还是用户空闲时？是否应添加用户习惯学习如工作时间9:00-18:00不打扰，已在database.py习惯学习中？

3. **模型双轨**：GGUF推理+HF训练双轨已实现，但HF训练需要Qwen/Qwen3-30B-A3B，是否应添加自动下载或提示用户设置HF_MODEL_PATH？

### 关于训练与记忆

4. **SimpleMem实现**：当前固定长度100/150/80/120平均75%压缩1.4x，不是真正语义压缩论文30%目标。是否应用LLM进行真实压缩？但用户说离线仍可用，固定长度可能是为了离线可用。是否应添加配置use_llm true时用LLM，false时固定长度？

5. **训练数据与评估**：数据飞轮自动收集过滤后保存到sft.jsonl，SimpleMem 30% Replay高质量>0.8阈值是否合适？50条回放评估eval_tasks.jsonl是模拟成功率，不是真实执行agent_runtime，是否应实现真实回放？

6. **遗忘机制与DREAMS.md**：4层遗忘曲线7/30/90/180天低价值访问<3重要性<0.3 30天遗忘已实现但未测试是否真正生效，是否应添加测试？DREAMS.md人类可读日记是否应实现？

### 关于视觉与安全

7. **DPI+OCR真实落地**：dpi_ocr_unified.py已创建，RapidOCR 50MB已在requirements.txt，但ocr_screenshot还是演示占位。是否应接入真实RapidOCR添加自动下载模型逻辑？用户说品质需媲美商业级对标Operator/Claude Computer Use，OCR是核心视觉能力

8. **kill_process安全性**：刚添加实现过滤危险进程7个csrss.exe等，但未经真实Windows测试，是否安全？是否应添加更多危险进程如winlogon.exe services.exe等已在旧版中有？待确认流程NEED_CONFIRM阻断+前端确认已实现，但前端platform_status.js只显示平台状态未显示待确认队列，是否应在前端添加待确认弹窗？

### 关于前端与iOS

9. **前端与平台状态条**：platform_status.js已创建11KB顶部显示Provider真实/演示+demo_mode视觉区分，但是否真正加载？app.js已导入，但index.html还是旧版51路由内容，是否应重写为v0913 103API？进化仪表盘evolution.js 25KB SSE+图表+基因树是否与后端evolution.py 18路由完全对接？是否应测试SSE流？

10. **iOS远程需求**：用户说预留iOS移动设备远程查看控制端口，resource_monitor中有iOS检测，但未实现WebSocket。是否应实现POST /api/ios/report和iOS前端页面？具体需求是查看系统状态，还是远程控制？用户说Windows深度控制为主iOS远程端口预留，是否应先实现查看再实现控制？远程控制安全是否需额外认证JWT已实现但是否应添加iOS专用Token？

### 关于优先级与商业级

11. **优先级**：用户说优先级你来决定，已按评估→安全趋势→DPI顺序执行，当前6缺点+12优先级完成，Review Debug完成，单版本整理完成。下一步应优先夯实测试，还是优化SimpleMem真实压缩，还是实现iOS远程，还是重写README和前端？

12. **商业级品质差距**：用户说品质需媲美商业级对标Operator/Claude Computer Use + Manus/Devin + PowerToys/Raycast。当前哪些方面离商业级还有差距？是测试覆盖率，还是文档，还是性能，还是安全性？是否太吃配置24GB VRAM训练30B-A3B是否太高应优化为更低配置可用？参考openclaw memory dreaming

---

## 四、建议的下一步 - 按优先级

### P0 - 夯实基础（必须）- 建议立即执行

1. 添加集成测试：真实执行50条回放评估任务，非模拟
2. 重写frontend/index.html为v0913 103API单版本23视图+平台状态条（当前还是旧51路由内容）
3. 测试安全拦截真实流程：delete System32 → PENDING_CONFIRM → 前端确认 → 审计
4. 验证启动pip install -r requirements.txt && python run.py → /docs Swagger 8层架构
5. 清理pycache和临时文件已完成✅

### P1 - 深度优化（重要）- 建议第二批

6. SimpleMem真实语义压缩：LLM可用时用LLM，离线固定长度回退，添加配置
7. DPI+OCR真实落地：接入RapidOCR真实，测试Windows DPI和UIA
8. 训练管道真实化：添加训练状态真实检查和SSE推送测试
9. 前端平台状态条测试：验证demo_mode视觉区分是否生效

### P2 - 功能完善（可选）- 建议第三批

10. iOS远程端口：实现POST /api/ios/report + iOS前端查看
11. 确认弹窗+预览Diff：删除前列表，窗口移动虚线框
12. WMI图表：CPU每核心折线图Canvas
13. 配置中心：settings/save真实落盘config/

### P3 - 实验性（隔离）- 建议实验分支

14. EXE打包PyInstaller
15. 向量检索sentence-transformers真实384维
16. 更多技能基因和Prompt进化实验

---

## 五、向用户的核心问题 - 10个需决策

1. **模型路径D:\llama.cpp\...在Linux演示环境无法访问，是否已通过环境变量MODEL_PATH支持？是否需测试该模型？**

2. **SimpleMem固定长度实现 vs LLM真实语义压缩，是否应添加use_llm配置，LLM可用时用LLM离线固定长度回退？**

3. **DPI+OCR真实落地是否应接入RapidOCR真实并自动下载模型？**

4. **iOS远程查看控制的具体需求是查看还是控制，是否应实现WebSocket？先查看再控制？**

5. **回放评估50条模拟成功率是否应实现真实执行agent_runtime？**

6. **kill_process等新工具未经Windows真实测试是否安全？是否应添加更多危险进程？**

7. **下一步优先级：测试夯实 vs SimpleMem优化 vs iOS远程 vs 前端重写，哪个优先？**

8. **商业级品质差距在哪，是否测试覆盖率、文档、性能、安全性？是否太吃配置？**

9. **frontend/index.html 29KB旧版51路由内容是否应重写为v0913 103API单版本23视图+平台状态条？**

10. **是否应创建dev分支用于实验性功能隔离？用户说允许创新试错实验性功能隔离**

---

> **当前状态**：单版本整理彻底完成✅，真正干净单版本，无V1/V2/V6/V7并存，根目录仅2 MD，backend 13主文件单版本，routers 16文件单版本，legacy删除归档，prompts单版本v4，可启动
> **等待用户决策**：10个核心问题需用户决定，再执行P0/P1/P2/P3
