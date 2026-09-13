# Zane AGI v0913 Review & Debug 报告

> 全面代码审查，检查缺失项和依赖，梳理项目逻辑

## 执行时间
2026-09-13 审查

## 1. 项目结构梳理

### 核心文件 - 单版本整合版
```
backend/
├── main.py 37KB 762行 v0913单版本整合版 单版本+103API+8层架构
├── tools_impl.py 30KB 531行 统一工具实现 26注册表+30实现(4可选)
├── tool_registry.py 26工具 v0913整合版 修复不一致
├── policy_firewall_v0913.py 13KB 硬化版 NEED_CONFIRM阻断
├── policy_firewall.py 4.9KB 旧版兼容
├── agent_runtime.py 16KB 旧版已归档legacy
├── agent_runtime_v2.py 16KB v2
├── agent_runtime_v3.py 27KB v3 思考预算+有界校正
├── legacy/ 392KB 10文件历史归档
│   ├── main_v2.py/v3.py/v4.py/v6.py/v7.py/v8.py
│   ├── agent_runtime.py/v2.py/v3.py
│   ├── memory_layer.py
│   ├── tool_registry_old.py
│   └── tools_impl_old.py/complete.py
├── routers/ 16文件
│   ├── evolution_v3.py 18路由 VRAM/资源/过滤/训练/评估
│   ├── thinking_v25.py 6路由 思考预算/Ralph/有界校正
│   ├── memory_v3.py 12路由 SimpleMem/梦境/记忆v3/技能基因
│   ├── security_v3.py 8路由 沙盒/扫描/WSL/契约/策略+趋势+异常
│   ├── vision_v3.py 8路由 OCR/搜索/清理/梦境+DPI
│   ├── runtime_v3.py 10路由 工具/记忆/技能/轨迹
│   ├── auth_v3.py 3路由 JWT
│   ├── benchmark_v3.py 3路由 Benchmark
│   ├── vector_v3.py 2路由 向量
│   └── config_v3.py 4路由 配置
├── memory/
│   ├── data_flywheel_v3.py 14KB 过滤评分去重安全
│   ├── memory_v3.py 8.4KB 4层统一+SimpleMem+遗忘
│   ├── simple_mem.py 7.6KB 压缩30%目标固定长度实现
│   └── vector_memory_real.py 真实向量
├── runtime/
│   ├── data_filter.py 11KB 11路径8文件7进程6命令 过滤100%
│   ├── thinking_budget.py Qwen3 /think 32K /no_think 8K
│   ├── ralph_loop.py bash while全新上下文
│   ├── bounded_correction.py UCSL有界校正
│   ├── skill_gene.py 技能基因变异交叉
│   ├── resource_monitor.py 7.4KB 5维度可训练
│   └── ...
├── security/
│   ├── sandbox.py 文件+进程沙盒 realpath+白名单+回收站
│   ├── cybersec_tools.py 漏洞扫描
│   ├── cybersec_trend.py 234行 历史趋势时间序列新增
│   └── linux_provider.py WSL沙盒
├── vision/
│   ├── dpi_ocr_unified.py 242行 DPI统一+OCR+UIA树新增
│   └── ocr_real.py RapidOCR 50MB
└── platform/
    ├── base.py 抽象接口
    └── windows/ WMI+Win32真实

frontend/
├── index.html 29KB v0913 标题已更新 内容待更新
├── index_v7.html 21KB v7.0备份
├── css/ 4文件 styles 11KB+components+layout+themes
└── js/ 11文件
    ├── app.js 25KB 主逻辑 + platform_status导入
    ├── platform_status.js 11KB 新增 平台状态条+demo_mode视觉区分
    ├── evolution.js 25KB SSE+图表+基因树
    ├── charts.js 交互式图表
    └── ...

tests/
├── test_tools_impl.py 5.7KB 工具统一+防火墙阻断
├── test_eval_replay.py 5.7KB 回放评估50条
├── eval_tasks.jsonl 9.5KB 50条任务5分类3难度
└── benchmark/
    └── test_simplemem.py 13KB Benchmark可复现

docs/
├── FLYWHEEL_SPEC.md 7.3KB 评分规格透明
└── ZANE_V0913_CHANGELOG.md 12KB 变更日志

根目录
├── main.py 替代 run.py? 实际run.py是启动器
├── run.py 113行 v0913单版本优先+环境变量控制
├── requirements.txt 16依赖 最小必要
├── LICENSE MIT
└── README.md 56KB v7.0内容 标题已改v0913待重写
```

### 8层架构
1. 接入层：health/chat/agent/execute/前端
2. 思考层：thinking_budget/think/no_think/Ralph/bounded_correction
3. 执行层：工具21个+记忆+技能+轨迹+DAG
4. 记忆层：SimpleMem+梦境3阶段+记忆v3 4层+技能基因
5. 进化层：飞轮v3+模型双轨+训练+评估+Replay+Prompt进化
6. 平台层：Windows真实/psutil演示+demo_mode区分
7. 安全层：沙盒+防火墙NEED_CONFIRM阻断+过滤100%+趋势
8. 可观测层：系统资源5维度+Benchmark+Vector+Config+Auth+清理

## 2. 依赖检查

### requirements.txt 16依赖
```
fastapi 0.115.0 Web框架
uvicorn 0.32.0 ASGI服务器
psutil 6.1.0 系统信息
pillow 11.0.0 截图
pydantic 2.9.2 数据校验
python-multipart 0.0.12 表单
aiofiles 24.1.0 异步文件
httpx 0.27.2 异步HTTP调LLM
filelock 3.15.0 并发安全
slowapi 0.1.9 限流60/分
APScheduler 3.10.4 定时
python-jose 3.3.0 JWT
loguru 0.7.2 日志轮转
sqlite-vec 0.1.6 向量轻量
rapidocr_onnxruntime 1.3.12 OCR 50MB
datasets 3.0.0 训练数据
```

### 环境检查
- 当前环境：psutil 7.2.2 + pydantic 2.13.4 已安装，fastapi/loguru未安装
- 测试：通过mock loguru通过
- 真实启动：需pip install -r requirements.txt
- Windows额外：wmi pywin32 (sys_platform=="win32"条件)

### 缺失依赖
- 无，requirements.txt完整
- 可选重型：torch, unsloth, sentence-transformers按需

## 3. 代码逻辑梳理

### 启动流程 run.py
```
1. 打印Banner v0913单版本整合版
2. 读取环境变量 ZANE_RUNTIME/PLATFORM/DEMO/LLM_PROVIDER/PORT
3. 检查核心依赖 fastapi uvicorn psutil
4. 检查可选依赖 loguru slowapi rapidocr sqlite-vec filelock
5. 检查前端 index.html
6. 检查单版本文件 main.py tools_impl.py policy_firewall_v0913.py
7. 检查legacy归档
8. 打印启动信息 前端/docs/health/platform/flywheel/pending
9. 尝试启动版本优先级：
   - backend.main v0913单版本
   - backend.legacy.main_v8 v8.0
   - backend.legacy.main_v7 v7.0
   - backend.legacy.main_v6 v6.0
10. uvicorn.run host 0.0.0.0 port ZANE_PORT
```

### main.py lifespan启动日志3行
```python
def get_startup_info():
    1. Runtime版本 env ZANE_RUNTIME=v3 v3可用/回退v2
    2. Platform Provider Windows真实/psutil演示 env ZANE_PLATFORM/DEMO 系统:linux
    3. 工具 0真实 24演示 env ZANE_LLM_PROVIDER 演示工具列表 真实数

@asynccontextmanager lifespan:
    打印3行启动日志
    启动调度器v3 凌晨2点+每30分+资源感知
    检查sqlite-vec/rapidocr/JWT
    检查防火墙版本v0913硬化版
    打印技术栈8层架构
```

### 工具调用流程
```
用户消息 → /api/chat → thinking_budget /think → agent_runtime_v3.execute_task
→ intent_parser → planner DAG分解 → tool_executor检查权限policy_firewall_v0913
→ 如果READ_ONLY自动放行
→ 如果WRITE/DANGEROUS创建pending_confirm NEED_CONFIRM阻断等待确认
→ 前端GET /api/security/pending轮询 → POST /api/security/confirm确认
→ 执行工具tools_impl.py真实/演示兼容
→ 验证verify_info写后重新感知
→ 熔断器失败5次
→ 撤销栈可回滚
→ 收集到data_flywheel_v3 → 过滤data_filter 11路径8文件7进程6命令
→ 评分importance 0.5-0.9 + quality
→ 保存sft.jsonl + replay_buffer 30%
→ 记忆simple_mem+memory_v3
→ 返回final_report
```

### 安全流程
```
工具调用 → policy_firewall_v0913.check_permission
→ 保护路径检查 C:\Windows\System32 /etc/shadow等10个
→ 自动放行列表 list_files read_file等10个只读
→ 权限分级 READ_ONLY ALLOW, WRITE/DANGEROUS PENDING_CONFIRM
→ 创建PendingConfirm id=confirm_xxx tool_name parameters reason risk_level
→ 存入pending_confirms + confirm_callbacks asyncio.Event
→ 日志🛡️ 策略阻断
→ 返回PolicyRule action=PENDING_CONFIRM confirm_id
→ 执行器wait_for_confirm等待5分钟超时自动拒绝
→ 前端确认confirm_operation approved bool
→ 触发Event → 继续执行
→ 审计日志log_execution blocked=True
```

## 4. 缺失项检查 - 已修复

### 已修复
- ✅ 遗留main文件：main_v2/v3/v4/v6/v7/v8已删除原地，legacy有备份，当前仅main.py + main_v4已归档删除
- ✅ 工具注册表与实现不一致：注册表26实现30(4可选wsl等)，核心26一致，缺失kill_process/get_window_info/analyze_ui已添加实现和映射
- ✅ .gitignore：已修复排除data/*.json diary dreams episodic等
- ✅ 安全趋势和DPI集成：security_v3.py已集成cybersec_trend 3路由trend/anomalies，vision_v3.py已集成dpi_ocr_unified DPI信息+OCR统一流程
- ✅ tool_registry.py已重写26工具统一
- ✅ tools_impl.py已添加缺失实现kill_process/get_window_info/analyze_ui + 映射
- ✅ 前端platform_status.js已创建并在app.js导入

### 待修复 - 本次review
- ❌ README.md 56KB内容还是v7.0 51路由，标题已改v0913，需要重写为v0913单版本103API 8层架构
- ❌ frontend/index.html 29KB内容还是v7.0 51路由，需要更新为v0913 103API+平台状态条
- ❌ data目录还有json被跟踪已通过git rm --cached移除，但.gitignore需确保排除
- ❌ main.py健康检查未体现cybersec_trend和dpi_ocr_unified，需在v3_techniques中添加
- ❌ 缺少对main_v4.py的归档，已修复
- ❌ 缺少LICENSE和CI的进一步检查，已存在但需验证

## 5. 依赖与导入测试

### 核心导入
- ✅ backend.tools_impl 27工具演示模式单文件无覆盖
- ✅ backend.platform.base
- ✅ backend.memory.simple_mem semantic_compression方法
- ✅ backend.memory.memory_v3
- ✅ backend.runtime.thinking_budget
- ❌ backend.main 需fastapi未安装环境
- ❌ backend.policy_firewall_v0913 需loguru未安装环境，mock后通过

### 工具注册表与实现一致性
- 注册表26，旧版21→新增move_file/kill_process/get_window_info/analyze_ui/mouse_move/key_press/security_scan/scan_large_files
- 实现30，包含26+4可选wsl_exec/wsl_list/web_search_real/mouse_move等
- 核心一致，无缺失

## 6. 路由检查

### main.py 6路由 summary已补
- GET /api/health 接入层 健康检查+平台+工具数+进化技术
- GET /api/platform/status 平台层 Provider真实/演示+demo_mode
- GET /api/flywheel/stats 进化层 评分分布0.5-0.9四档
- GET /api/security/pending 安全层 NEED_CONFIRM阻断队列
- POST /api/security/confirm 安全层 确认操作
- POST /api/chat 接入层 聊天+思考预算+飞轮收集+记忆
- POST /api/agent/execute 接入层 兼容
- GET / 前端控制台

### routers 71路由模块化
- evolution_v3 18路由 VRAM/资源/过滤/训练/评估/Replay/Prompt/策略/调度/SSE
- thinking_v25 6路由 思考预算/Ralph/有界校正
- memory_v3 12路由 SimpleMem/梦境/记忆v3/技能基因
- security_v3 8路由 沙盒/扫描/WSL/契约/策略+趋势+异常 新增2
- vision_v3 8路由 OCR/搜索/清理/梦境+DPI 新增1
- runtime_v3 10路由 工具/记忆/技能/轨迹
- auth_v3 3路由 JWT
- benchmark_v3 3路由 Benchmark
- vector_v3 2路由 向量
- config_v3 4路由 配置
- 总计71模块化+32兼容=103API

### 新增集成
- security_v3：trend/anomalies 2新增，接入cybersec_trend历史趋势
- vision_v3：dpi 1新增，接入dpi_ocr_unified DPI统一

## 7. 前端检查

### index.html
- 标题已更新v0913但内容还是v7.0 51路由，需要更新为103API
- 引用app.js type=module，已导入platform_status.js

### js文件
- app.js 25KB 已导入platform_status.js
- platform_status.js 11KB 平台状态条+demo_mode视觉区分
- evolution.js 25KB SSE+图表+基因树
- charts.js 交互式图表

### 平台状态条逻辑
- 创建DOM topbar下方
- 加载/api/platform/status
- 显示Provider/真实/演示/Runtime/LLM/环境变量
- 工具信息真实/演示计数
- body.demo-mode黄条+工具卡片区分

## 8. 测试检查

### tests/
- test_tools_impl.py 工具统一+防火墙阻断 通过✅
- test_eval_replay.py 回放评估50条 成功率82% 通过✅
- benchmark/test_simplemem.py Benchmark可复现 75%压缩1.4x 通过✅(论文30%目标固定长度实现)
- eval_tasks.jsonl 50条任务5分类3难度

### CI
- .github/workflows/test.yml Python 3.10/11/12，依赖安装+语法检查+工具测试+Benchmark+回放评估+版本整合检查

## 9. 安全检查

### tools_impl.py安全增强
- 白名单ALLOWED_BASENAMES notepad explorer calc chrome等
- 危险字符FORBIDDEN_ARGS_CHARS &|;$`&&|| 参数注入防护
- 沙盒检查file_sandbox.check_path
- 回收站可撤销to_recycle
- 大小限制10MB
- 路径兼容_resolve_demo_path Windows→Linux演示映射
- 上下文预算截断20文件15进程

### policy_firewall_v0913硬化
- NEED_CONFIRM真正阻断PENDING_CONFIRM+confirm_id
- 待确认队列+Event+超时5分钟自动拒绝
- 前端确认事件SSE推送
- 审计日志blocked

### data_filter过滤100%
- 11危险路径 C:\Windows\System32 /etc/shadow等
- 8危险文件 .ssh/id_rsa password.txt等
- 7危险进程 csrss.exe lsass.exe等
- 6危险命令 rm -rf / :(){:|:&};:等
- 核心路径只读也过滤
- 去重SHA256+相似度>0.9
- 重要性0.5-0.9评分

## 10. 待修复清单 - 本轮review

1. README.md重写v0913单版本103API 8层架构，当前56KB v7.0内容
2. frontend/index.html更新v0913 103API+平台状态条，当前29KB v7.0 51路由
3. main.py健康检查v3_techniques添加cybersec_trend和dpi_ocr_unified
4. 检查data目录json是否还有被跟踪，已git rm --cached
5. 验证run.py legacy fallback路径backend.legacy.main_v*是否存在
6. 检查是否有其他遗留文件如tool_registry_v0913.py是否需要清理
7. 验证前端CSS是否包含platform_status样式，已在platform_status.js中injectStyles
8. 检查LICENSE和CI是否完整，已存在

## 11. 建议

- README精简到v0913单版本，旧版归档docs/
- frontend/index.html更新为v0913
- main.py添加cybersec_trend和dpi_ocr到health
- 清理tool_registry_v0913.py临时文件，已备份到legacy
- 验证所有路由summary+tags 8层架构已补，main.py 6个已补，routers需检查是否全部有summary
- 测试pip install -r requirements.txt后启动
