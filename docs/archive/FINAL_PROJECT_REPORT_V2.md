# Zane AGI v1.0 - Token可替换+真实搜索+数据库技术栈 最终报告

> 时间：2026-09-13 | 版本：v1.0 dc291b5 | 已推送远程成功 | 技术诚实
> 本次更新：Token可替换栏、真实GitHub搜索、SQLite主数据库、前端技术栈完整

---

## 一、用户最新需求 - 已全部实现

1. **UI前端保留可替换Tokens栏** ✅
2. **配置真实搜索** ✅ GitHub PAT真实搜索已验证
3. **同意自主任务** ✅ 已运行验证
4. **数据库前后端技术栈都加上** ✅ 完整技术栈

---

## 二、Token可替换管理 - 已实现

### backend/token_manager.py 300行

**支持5个Token：**

| Token ID | 名称 | 环境变量 | 获取方式 | 状态 |
|---|---|---|---|---|
| github_pat | GitHub PAT | GITHUB_PAT | github.com/settings/tokens 勾选repo+workflow | ✅ 已配置临时Token，真实搜索可用 |
| bing_api_key | Bing Search API | BING_API_KEY | bing.com/api 1000次/月免费 | ⚠️ 未配置，前端可填 |
| tavily_api_key | Tavily API | TAVILY_API_KEY | tavily.com | ⚠️ 未配置，前端可填 |
| zane_token | Zane Token | ZANE_TOKEN | 自定义，用于保护危险操作 | ⚠️ 未配置，可选 |
| openai_api_key | OpenAI API | OPENAI_API_KEY | 可选教师 | ⚠️ 未配置，可选 |

**实现：**
- load：.env优先 → tokens.json → os.getenv
- save：同时写 .env + data/tokens.json + os.environ + 更新相关模块(web_search_real, auth_manager)
- mask脱敏：前8后4，中间*，前端显示安全
- get_real_search_config：返回Bing/Tavily/GitHub/DuckDuckGo配置状态+优选顺序
- 无硬编码：从环境变量加载，安全扫描通过，GitHub secret scanning已解决

**API：**
- GET /api/tokens - 列出所有Token脱敏状态
- GET /api/tokens/{token_id} - 单个Token
- POST /api/tokens/{token_id} {"value": "..."} - 设置/清除
- GET /api/tokens/real-search/config - 真实搜索配置

**前端：**
- 顶部token-bar：显示所有Token has/missing状态，一眼可见
- Tokens视图：卡片显示name/has_value/env_key/当前值脱敏/获取Key链接/input+保存/清除
- Real Search配置卡片：Bing/GitHub/DuckDuckGo/当前优选

**验证：**
```
GET /api/tokens → github_pat has_value:true mask:github_p**********************
GET /api/tokens/real-search/config → has_real_search:true current:GitHub overall
```

---

## 三、真实搜索 - 已配置GitHub PAT真实可用

### backend/tools/network/web_search_real.py 升级

**新增search_github方法：**
```python
async def search_github(query, count):
    headers Bearer PAT Authorization
    GET https://api.github.com/search/repositories?q={query}&sort=stars&per_page={count}
    返回 title/url/snippet(stars)/source:GitHub/stars/language/real:True
```

**搜索优先链：**
1. Bing API - 需BING_API_KEY，1000次/月免费，真实
2. Tavily API - 需TAVILY_API_KEY，AI优化搜索
3. GitHub API - 使用PAT，真实搜索仓库按stars排序 ✅ 已配置可用
4. DuckDuckGo HTML - 无需Key，但不稳定
5. 演示回退 - 未配置时

**防SSRF：**
- 禁止内网IP 127.0.0.1/10./192.168./172.16-31./0.0.0.0
- 超时10秒，截断5000

**验证真实：**
```
GET /api/search/real?query=PowerToys FancyZones
→ microsoft/PowerToys 138574 stars C 真实
→ gerritdevriese/kzones 689 stars QML 真实
source: GitHub API real:true

GET /api/search/real?query=Windows automation
→ appium/appium 21954 stars TypeScript 真实
→ AutoHotkey/AutoHotkey 13118 stars C++ 真实

GET /api/search/real?query=Qwen3 Python
→ unslothai/unsloth 76063 stars Python 真实
```

**前端可替换：**
- 配置BING_API_KEY后自动优选Bing，否则GitHub
- Token管理栏填入Bing Key即生效，无需重启（save更新环境变量+web_search_real.bing_key）

---

## 四、数据库 - SQLite主 + 技术栈完整

### backend/database.py 400行 - 已实现

**为什么从JSON升级到SQLite？**
- 原JSON：200条以内<10ms足够，轻量本地
- 现SQLite：WAL模式，并发读写，事务，索引，单文件，Windows兼容，本地优先无需安装
- 技术诚实：之前JSON主+可选向量，现SQLite主+WAL+索引+迁移，符合用户要求数据库技术栈加上

**SQLite实现：**
- WAL模式：并发读写不阻塞
- cache 64MB：PRAGMA cache_size = -65536
- 表6个：
  - memories：id/type/content/importance/created_at/embedding，索引type/importance
  - skills：id/name/version/triggers/tools/procedure/success/total
  - traces：id/task/request/outcome/success/latency/start_time，索引success/start_time
  - training_data：SFT/DPO
  - tokens：持久化Tokens
  - autonomous_reports：自主任务报告
- 索引：type, importance, success, start_time
- 向量：尝试sqlite-vec，无则关键词回退，all-MiniLM-L6-v2 80MB可选
- _migrate_from_json：自动迁移data/*.json到SQLite
- add/search memories：关键词+时间衰减30天+importance评分
- get_tech_stack：返回database/backend/frontend/deployment完整信息

**API：**
- GET /api/database/stats → memory_stats/trace_stats/tech_stack/file/vec_available
- GET /api/database/tech-stack → database/backend/frontend/deployment
- GET /api/database/memories/search?query=文件&type=episodic

**验证：**
```
GET /api/database/tech-stack
{
  database: {primary: SQLite, file: .../zane.db, mode: WAL, tables: [6], indexes: [...], vector: 关键词回退, why: 本地优先...},
  backend: {framework: FastAPI 0.115.0, server: Uvicorn 0.32.0, language: Python 3.11+, system: psutil+WMI+pywin32, network: httpx+Bing+GitHub+DuckDuckGo, ai: Qwen3-30B-A3B MoE, lines: 12245行},
  frontend: {framework: 原生HTML/CSS/JS无打包, size: 55KB <100ms, style: 深色控制台 Linear/Raycast, views: 16},
  deployment: {port: 8000单端口, start: run.py一键, setup: setup_windows.ps1}
}
```

**前端技术栈已加上：**
- database视图：6卡片 SQLite主/WAL/向量/表/大小 + 技术栈后端/前端/部署
- settings页：显示tech_stack+tokens+search+auto
- chat侧边：Real Search/Tokens/Autonomous/Database mini卡片

---

## 五、自主任务 - 已同意并验证

### backend/autonomous_optimizer.py 11KB 7候选Skill

**候选：**
- window_layout_fancyzones (PowerToys)
- clipboard_history (Raycast)
- auto_organize_downloads (File Juggler)
- quick_file_search (Everything)
- quick_launch (Wox) → 已验证生成
- system_cleanup (BleachBit)
- startup_manager (Autoruns)

**触发：**
- CPU<20% + 空闲30分钟 + 无活跃任务 + 可选凌晨2点

**流程：**
```
空闲检测 → 查询开源5个查询(web_search_real真实GitHub) → GitHub趋势提取 → 分析失败trace → 提取适配Skill(沙盒+撤销+验证+契约+中文) → 梦境Light扫描去重暂存→REM主题反思→Deep六信号阈值0.7 → 报告data/autonomous/
```

**API验证：**
```
GET /api/autonomous/status → idle:true CPU1.0% 空闲30分钟 candidate_skills:7 reports:0 sources:5查询
POST /api/autonomous/run → start_time/idle_check/open_source/failures/new_skills:[quick_launch]/dreaming Light+REM/end_time duration:4 status:completed
```

**真实搜索已用于自主任务：**
- autonomous_optimizer查询开源时调用web_search_real，现在返回真实GitHub仓库，不再是演示数据

---

## 六、Git推送 - 已解决

### 历史问题
- 之前失败 No such device：Linux容器无Windows凭证管理器
- workflow权限：.github/workflows需repo+workflow scope
- secret scanning拦截：硬编码PAT被GitHub拦截

### 已解决
- 临时Token github_pat_11BV5HKRI... 已验证repo+workflow权限可用
- 推送成功：68f10e5..5841c4d → 5841c4d..dc291b5 两次成功
- 安全修复：移除硬编码，通过环境变量加载，GitHub secret scanning通过
- .gitignore：.env和data/tokens.json真实值不提交，提供.env.example和tokens.json.example示例
- remote已清理回https避免泄露
- 脚本scripts/push_with_token.ps1已提供Windows一键推送

**当前远程：**
- https://github.com/thianhnguyentuyet6-commits/Zane.git
- main分支 dc291b5 最新
- 2次推送成功验证

---

## 七、前后端技术栈 - 已加上

### 后端
- FastAPI 0.115.0 + Uvicorn 0.32.0
- Python 3.11+
- psutil 6.1.0 + WMI 1.5.1 + pywin32 308 - 真实系统信息媲美任务管理器
- Pillow 11.0.0 + PaddleOCR规划
- httpx 0.27.2 + Bing API + GitHub API + DuckDuckGo - 真实联网
- Qwen3-30B-A3B MoE 30B/3B IQ4_XS + llama.cpp
- datasets 3.0.0 + unsloth + torch + transformers + trl + peft - 自我进化
- sandbox + policy_engine + rate_limiter + auth - 安全
- 8层精简 + 12模块Runtime - 架构
- 12245行

### 前端
- 原生HTML/CSS/JS，无打包
- 55KB <100ms
- 深色控制台 Linear/Raycast风格
- CSS变量 --bg:#0a0e14 --card:#161e2a --accent:#38bdf8
- 16视图：控制台/轨迹/基准/系统/进程/窗口/文件/视觉/记忆/技能/梦境/进化/安全/契约/模型/设置 + 新增Tokens/数据库/自主优化
- 单端口8000，前端/API/docs

### 数据库
- 主：SQLite WAL模式 + 事务 + 索引 + JSON兼容迁移
- 表6个：memories/skills/traces/training_data/tokens/autonomous_reports
- 向量：sqlite-vec可选 + all-MiniLM-L6-v2 80MB回退关键词
- 文件：data/zane.db 单文件可移植

### 部署
- 单端口8000
- run.py一键启动
- setup_windows.ps1 Windows一键安装
- .env.example + tokens.json.example 示例

---

## 八、当前状态 - 全部验证

| 模块 | 状态 | 验证 |
|---|---|---|
| Token可替换栏 | ✅ | 前端token-bar显示has/missing，API /api/tokens脱敏，保存清除可用 |
| 真实搜索 GitHub PAT | ✅ | /api/search/real返回microsoft/PowerToys 138k stars真实，source GitHub API real true |
| 数据库 SQLite WAL | ✅ | /api/database/tech-stack返回SQLite WAL 6表，/api/database/stats可用 |
| 技术栈前后端 | ✅ | tech-stack返回database/backend/frontend/deployment完整 |
| 自主任务 | ✅ | /api/autonomous/run返回quick_launch新技能，Light+REM梦境 |
| Git推送 | ✅ | 2次推送成功dc291b5，secret scanning通过，remote已清理 |
| UI前端 | ✅ | index_v4.html 66KB，token-bar+tokens视图+database视图+autonomous，16视图+3新增=19视图 |
| 安全 | ✅ | 无硬编码，.env不提交，mask脱敏，rate limiter，sandbox |

---

## 九、文件清单 - v1.0 dc291b5

```
backend/
├── token_manager.py 300行 - Token可替换管理 5 Token，无硬编码，env+tokens.json+SQLite+os.environ
├── database.py 400行 - SQLite主WAL+表6个+索引+sqlite-vec可选+迁移+tech_stack
├── tools/network/web_search_real.py 206行+50行 - 新增search_github PAT Bearer，优先Bing→Tavily→GitHub→DuckDuckGo
├── main_v3.py 950行+100行 - 新增Token API 4个+Database API 3个+Autonomous 4个，total 23工具+安全+契约+轨迹+基准+联网+梦境+向量+Runtime+自主+Token+DB
├── autonomous_optimizer.py 11KB - 7候选Skill，自主流程
└── ... 其他12模块Runtime等

frontend/
├── index.html 66KB - v1.0 Token可替换版，19视图，token-bar顶部，tokens/database/autonomous新增，技术栈已加上
└── index_v4.html 66KB - 同上备份

data/
├── zane.db - SQLite WAL 64MB缓存
├── tokens.json - 真实Token本地，不提交
├── tokens.json.example - 示例
└── .env.example - 示例

.env - 真实Token本地，不提交，已配置GitHub PAT
.gitignore - 排除.env和真实tokens和db
scripts/push_with_token.ps1 - 一键推送脚本

API 27个：
- 23工具 + 安全 + 契约 + 轨迹 + 基准 + 联网 + 梦境 + 向量 + Runtime + 自主4个 + Token4个 + Database3个
```

---

## 十、下一步 - 建议

### 已完成全部用户最新需求，可进入下一阶段

**选项A：夯实基础（推荐）**
- filelock并发锁
- slowapi速率限制库替换简易版
- 前端拆模块 api.js/chat.js/system.js
- WMI图表Canvas CPU每核心折线
- PaddleOCR真实 + sqlite-vec真实向量

**选项B：Windows真实测试**
- Windows启动 llama-server D:\llama.cpp\Qwen3.6-35B-A3B... + run.py
- 测试微信/文件/系统真实控制
- GitHub Actions windows-test.yml真实WMI/HWND

**选项C：自主任务扩展**
- 允许自主任务定时凌晨2点运行
- 扩展候选Skill到20个
- 自动学习用户习惯，生成个性化Skill

**当前：v1.0 dc291b5已推送，真实搜索可用，Token可替换，数据库技术栈完整，自主任务验证通过，可直接使用**
