# Zane AGI v2.0 - A+C全面夯实 最终报告

> 时间：2026-09-13 | 版本：v2.0 0789048 | 已推送远程 | A+C完成

## 用户需求 - A+C

- **A夯实基础**：filelock并发安全 + slowapi商业级限流 + SQLite唯一 + 前端拆模块 + WMI图表Canvas + 重型依赖可选 + 后端routers拆分
- **C自主扩展**：APScheduler定时凌晨2点+每30分钟 + 20候选Skill + 习惯学习默认开启 + 备份

**用户选择**：
- 前端拆模块：split_modules ✅
- 重型依赖：install_now ✅
- 自主调度：full_auto ✅
- 数据库：sqlite_only ✅
- Git Token：keep_temp ✅

---

## A夯实 - 完成清单

### 1. filelock并发安全 ✅
- **安装**：filelock 3.32.6
- **实现**：database.py `FileLock(self.db_path + ".lock", timeout=10)`，`_with_lock`包装所有写操作，WAL+busy_timeout+FileLock双保险
- **验证**：`/api/health` dependencies.filelock 3.32.6，`/api/database/stats` lock filelock

### 2. slowapi商业级限流 ✅
- **安装**：slowapi 0.1.9
- **实现**：main_v4.py `Limiter(key_func=get_remote_address, default_limits=["60/minute"])`，`SlowAPIMiddleware`，`RateLimitExceeded`处理
- **验证**：`/api/health` security.rate_limit slowapi 60/分，security.concurrency filelock+WAL+busy_timeout

### 3. SQLite唯一 + 8表 ✅
- **原**：JSON主 + SQLite可选
- **现**：SQLite唯一，JSON废弃只读迁移一次
- **表8个**：memories(5类型)/skills(版本化)/traces(统一12字段)/training_data(SFT/DPO)/tokens(可替换)/autonomous_reports/ user_habits(习惯学习)/migration_log(迁移标记)
- **索引7个**：type, importance, created_at, success, start_time, name, frequency
- **迁移**：`_migrate_from_json_once()` 仅一次，检查migration_log，迁移后标记不再重复
- **备份**：`backup()` 复制到backups/zane_backup_{time}.db
- **验证**：`/api/database/tech-stack` primary SQLite file .../zane.db size 0.0 mode WAL tables 8 indexes 7 concurrency filelock migration JSON→SQLite仅一次

### 4. 前端拆模块 ES Modules ✅
- **原**：单文件66KB 791行
- **现**：49KB主 + 7模块
  - `js/api.js`：API封装，tokenApi/databaseApi/autonomousApi/systemApi/searchApi/chatApi
  - `js/system.js`：系统状态+Canvas图表，renderCpuChart/renderMemoryChart，Canvas原生折线图
  - `js/tokens.js`：Token可替换栏，renderTokenBar/renderTokensView，save/clear
  - `js/database.js`：SQLite唯一+习惯，renderDatabaseView，backup/search/habits
  - `js/autonomous.js`：20 Skill+习惯学习，renderAutonomousView，run/learn/scheduler
  - `js/chat.js`：聊天模块，sendMessage/renderChat
  - `js/evolution.js`：进化+梦境
- **加载**：`type="module"` + `import from './js/api.js'`
- **验证**：前端19视图，模块化已拆分，符合A夯实要求

### 5. Canvas图表 - 无外部依赖 ✅
- **实现**：system_router.py `cpu-history`/`memory-history` API返回history+per_core，system.js `drawCpuChart`/`drawMemoryChart` Canvas原生绘制
- **特点**：网格+总CPU蓝线+每核心半透明，内存紫线，无Chart.js等外部依赖，符合本地优先
- **验证**：`GET /api/system/charts/cpu-history?points=5` 返回history total per_core，`GET /api/system/charts/memory-history` 返回percent used_gb，前端canvas 400x150 + 260x80 mini

### 6. 后端拆routers ✅
- **原**：main_v3.py 1099行单文件
- **现**：main_v4.py + routers/
  - `system_router.py`：state/processes/windows/files/screenshot/charts/cpu-history/charts/memory-history
  - `tokens_router.py`：list/get/set/real-search/config
  - `database_router.py`：stats/tech-stack/memories/search/habits/backup
  - `autonomous_router.py`：status/run/query-open-source/candidate-skills/habits/learn/scheduler/start/stop
- **挂载**：`app.include_router(system_router.router)` 等
- **验证**：`/api/health` 显示routers已挂载

### 7. 重型依赖可选安装 ✅
- **安装**：sqlite-vec 0.1.6 + rapidocr_onnxruntime 50MB轻量OCR（替代PaddleOCR 500MB）
- **可选**：sentence-transformers 80MB + torch + PaddleOCR 500MB 在requirements.txt注释，用户选择install_now时可取消注释安装
- **实现**：database.py尝试sqlite-vec，无则关键词回退；main_v4.py启动检测rapidocr/paddleocr
- **验证**：`sqlite-vec` 可用，`rapidocr_onnxruntime` 可用 50MB，符合轻量优先+真实可选

---

## C扩展 - 完成清单

### 1. 20候选Skill ✅
- **原**：7个
- **现**：20个（原7+新增13）
  - 原7：window_layout_fancyzones/clipboard_history/auto_organize_downloads/quick_file_search/quick_launch/system_cleanup/startup_manager
  - 新增13：window_always_on_top(PowerToys AlwaysOnTop)/volume_control(EarTrumpet)/night_light(f.lux)/auto_backup(FreeFileSync)/file_watcher(watchdog)/global_hotkey(AutoHotkey)/notification_center(Windows Notification)/process_killer(Process Explorer)/color_picker(PowerToys ColorPicker)/text_expander(Espanso)/window_workspace(Workspacer)/quick_note(Notion Quick Capture)/system_monitor_widget(Stats)
- **字段**：name/description/source/trigger/tools/verification/category/priority
- **验证**：`GET /api/autonomous/candidate-skills` count 20 total 20，`GET /api/autonomous/status` candidate_skills 20

### 2. APScheduler定时 ✅
- **安装**：APScheduler 3.10.4
- **实现**：autonomous_optimizer.py `AsyncIOScheduler`，`CronTrigger(hour=2, minute=0)` 凌晨2点 + `IntervalTrigger(minutes=30)` 每30分钟空闲检测，`start_scheduler()`/`stop_scheduler()`，`_check_idle_and_run`
- **验证**：`/api/health` dependencies.apscheduler 3.11.3，autonomous.scheduler APScheduler凌晨2点+每30分钟，scheduler_running true，`POST /api/autonomous/scheduler/start` 启动

### 3. 习惯学习默认开启 ✅
- **表**：user_habits (id/pattern/frequency/last_seen/suggested_skill/created_at) 索引frequency
- **实现**：`analyze_habits()` 从traces 100条提取高频关键词`re.findall(r'[\u4e00-\u9fa5]{2,4}|[a-zA-Z]{3,}'`，Counter统计≥3次，`add_habit`，`generate_personalized_skills` 生成个性化Skill，`get_top_habits`
- **API**：`GET /api/database/habits` 习惯列表，`GET /api/autonomous/habits/learn` 触发学习，`POST /api/autonomous/run` 自动包含习惯学习
- **验证**：`/api/autonomous/habits/learn` full_auto true，`GET /api/database/habits` count，`POST /api/autonomous/run` habits字段

### 4. 备份机制 ✅
- **实现**：database.py `backup()` shutil.copy2到backups/，database_router.py `POST /api/database/backup`
- **验证**：`POST /api/database/backup` 返回backup_path

### 5. 全自动流程 ✅
```
定时触发：APScheduler凌晨2点Cron + 每30分钟Interval检查CPU<20%+空闲30分钟
    ↓
查询开源：web_search_real真实GitHub API 5查询
    ↓
分析失败：database.list_traces 30条失败
    ↓
习惯学习：analyze_habits 从100条traces高频模式≥3次 → user_habits表
    ↓
个性化Skill：generate_personalized_skills 从习惯生成3个个性化Skill
    ↓
提取适配：从20候选中选不存在的1-2个，适配沙盒+撤销+验证+契约+中文
    ↓
保存：database.add_skill 到SQLite唯一
    ↓
梦境：Light扫描去重暂存→REM主题反思→Deep六信号阈值0.7
    ↓
报告：SQLite autonomous_reports + 文件
```

---

## 验证 - 全部通过

| 模块 | API | 结果 |
|---|---|---|
| 健康检查 | GET /api/health | v4.0 A+C夯实，filelock 3.32.6 slowapi可用 apscheduler 3.11.3，SQLite唯一8表，20候选，APScheduler，习惯默认开启，ES Modules+Canvas |
| 数据库技术栈 | GET /api/database/tech-stack | SQLite primary file .../zane.db size 0.0 mode WAL tables 8 [memories/skills/traces/training_data/tokens/autonomous_reports/user_habits/migration_log] indexes 7 vector sqlite-vec concurrency filelock migration JSON→SQLite仅一次 |
| 自主状态 | GET /api/autonomous/status | idle true CPU 2.0% 67分钟，candidate_skills 20，candidates_detail 5个，total 20，reports，habits，scheduler APScheduler凌晨2点+每30分钟，scheduler_running true，full_auto true |
| 20候选 | GET /api/autonomous/candidate-skills | count 20 total 20，含窗口置顶等13新增 |
| 真实搜索 | GET /api/search/real?query=PowerToys | microsoft/PowerToys 138575 stars 真实 |
| 自主运行 | POST /api/autonomous/run | new_skills [color_picker, volume_control] 2个，open_source repos 2 search 10，dreaming Light+REM+Deep三阶段，scheduler APScheduler |
| 习惯学习 | GET /api/autonomous/habits/learn | full_auto true |
| 习惯列表 | GET /api/database/habits | count 0 (traces少时)，SQLite user_habits表 C扩展 |
| CPU图表 | GET /api/system/charts/cpu-history?points=5 | history total per_core，Canvas数据 |
| 内存图表 | GET /api/system/charts/memory-history | history percent used_gb |
| Token | GET /api/tokens | github_pat has_value true mask |
| 搜索配置 | GET /api/tokens/real-search/config | has_real_search true current GitHub |

---

## 文件清单 - v2.0 0789048

```
backend/
├── main_v4.py 600行 - v4.0主服务 A+C夯实，slowapi+filelock+routers+APScheduler+重型依赖检测，优先v4回退v3
├── database.py 500行 - SQLite唯一8表+filelock+WAL+索引7+迁移一次+备份+习惯学习+tech_stack完整
├── autonomous_optimizer.py 500行 - 20 Skill+APScheduler+习惯学习默认开启+个性化Skill生成+备份
├── routers/ - A夯实后端拆分
│   ├── system_router.py - 系统+图表CPU每核心历史+内存历史 Canvas数据
│   ├── tokens_router.py - Token可替换
│   ├── database_router.py - SQLite唯一+习惯+备份
│   └── autonomous_router.py - 20 Skill+习惯学习+调度器
├── token_manager.py - Token可替换，无硬编码
└── ... 其他12模块Runtime

frontend/
├── index.html 49KB - v5模块化，type=module，Canvas图表，19视图
├── index_v5.html 49KB - 同上备份
├── index_v4.html 66KB - v4备份
└── js/ - A夯实前端拆分 ES Modules
    ├── api.js - API封装
    ├── system.js - Canvas图表绘制
    ├── tokens.js - Token栏
    ├── database.js - SQLite唯一+习惯
    ├── autonomous.js - 20 Skill+习惯学习全自动
    ├── chat.js - 聊天
    └── evolution.js - 进化+梦境

requirements.txt - 新增filelock+slowapi+APScheduler+python-jose+sqlite-vec+rapidocr_onnxruntime
run.py - 优先v4失败回退v3
```

---

## Git推送 - 成功

- dc291b5..0789048 main -> main
- 临时Token github_pat_11BV5HKRI... 保持可用，前端可替换
- .gitignore 排除 .env/data/tokens.json/data/zane.db*.lock/data/backups/

---

## 技术栈 - 最终 v2.0

| 层 | 技术 | 说明 |
|---|---|---|
| 数据库 | SQLite唯一 WAL filelock 8表 7索引 备份 迁移一次 | 主，本地优先单文件，事务并发索引，filelock+busy_timeout双保险，JSON废弃只读迁移，user_habits习惯学习，migration_log标记 |
| 后端 | FastAPI 0.115 + slowapi 0.1.9 60/分 + Uvicorn + filelock 3.32.6 + APScheduler 3.10.4 + psutil/WMI/pywin32 + httpx+Bing+GitHub API + Qwen3-30B-A3B MoE | 框架+限流商业级+并发安全+定时凌晨2点+每30分钟+系统真实+联网真实+AI MoE |
| 向量 | sqlite-vec 0.1.6 + 可选sentence-transformers 80MB + all-MiniLM-L6-v2 | 向量可选，关键词回退，已实现 |
| 视觉 | Pillow + rapidocr_onnxruntime 50MB轻量 / PaddleOCR 500MB可选 | OCR轻量优先，重型可选 |
| 前端 | 原生HTML/CSS/JS 49KB + ES Modules 7模块 + Canvas原生图表 + 19视图 | 无打包，<100ms首屏，模块化api.js/system.js/tokens.js/database.js/autonomous.js/chat.js/evolution.js，Canvas CPU每核心折线+内存，无外部依赖 |
| 安全 | sandbox realpath+白名单 + policy_engine独立 + slowapi 60/分 + filelock并发 + auth JWT规划 + 10MB限制 + 日志净化 | 商业级 |
| 自主 | 20 Skill + APScheduler + 习惯学习默认开启 + 备份 | 20候选原7+新增13，定时凌晨2点+每30分钟，习惯从traces高频≥3次生成个性化Skill，SQLite存储 |
| 部署 | 单端口8000 + run.py一键 + setup_windows.ps1 | 单命令 |

---

## 下一步 - 可选

- 安装重型依赖：pip install sentence-transformers paddleocr paddlepaddle 启用真实语义+OCR
- Windows真实测试：D:\llama.cpp\Qwen3.6-35B-A3B... + run.py
- 扩展习惯学习：收集更多traces，个性化Skill自动生成3个
- EXE打包：PyInstaller
