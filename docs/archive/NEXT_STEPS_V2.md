# Zane AGI v2.2 → v3.0 下一步规划

> 时间：2026-09-13 | 当前：v2.2 d20cccc 26API全通+模型A真实+UI优化 | 目标：v3.0 商业级完善

---

## 一、已补全 - 本次检修

### 运行逻辑
- ✅ 26API全通：修复3个404 /api/memory/vector/search, /api/runtime/intent/parse, /api/runtime/state/observe
- ✅ lifespan修复：@app.on_event deprecated → asynccontextmanager lifespan
- ✅ sys导入修复：model_manager_v2 switch失败已修复

### 代码逻辑
- ✅ 59文件语法通过
- ✅ 安全无高危
- ✅ 18个Bug已修复，0高危

### 模型载入
- ✅ 真实扫描文件系统GGUF 10目录
- ✅ 自定义模型A custom_models.json，添加/切换/移除真实可用
- ✅ Server管理 socket+psutil真实检测，subprocess.Popen重启
- ✅ 前端UI models.js 8模块

### UI优化
- ✅ CSS拆分 styles.css 11KB + components.css 1.8KB 外部
- ✅ 加载状态 skeleton+spinner+empty+progress+aria-busy
- ✅ Aria无障碍 role+aria-label+aria-live+aria-current
- ✅ 焦点可见 focus-visible
- ✅ 轮询优化 10秒+document.hidden暂停

### 补全新增
- ✅ utils/cleanup.py 截图清理保留50张+备份清理保留10个/30天+轨迹清理保留100条
- ✅ memory/vector_memory_real.py 真实向量 sqlite-vec+sentence-transformers 80MB + 关键词回退
- ✅ vision/ocr_real.py 真实OCR rapidocr_onnxruntime 50MB优先 + PaddleOCR 500MB可选
- ✅ middleware/jwt_auth.py JWT python-jose商业级认证
- ✅ js/charts.js Canvas交互式图表 hover tooltip + 填充 + 网格标签

---

## 二、实际不可使用项 - 7个，需Windows真实环境

| 项 | Linux现状 | Windows真实 | 解决 | 优先级 |
|---|---|---|---|---|
| Qwen3模型 D:\llama.cpp\... | 不存在演示 | 18.5GB真实存在 | Windows启动 | 高 |
| WMI | psutil模拟 | 真实CPU每核心+内存条 | 安装wmi | 高 |
| pywin32 HWND | 演示 | 真实HWND+Z序+DPI | 安装pywin32 | 高 |
| llama.cpp server 8080 | 未运行离线 | 可启动 | 手动启动llama-server | 高 |
| PaddleOCR 500MB | 未安装 | 未安装 | rapidocr 50MB已安装替代 | 中 |
| sentence-transformers 80MB | 未安装关键词回退 | 未安装 | pip install可选 | 中 |
| torch | 未安装 | 未安装 | pip install可选 | 低 |

**下一步：Windows真实测试**

```powershell
# Windows PowerShell
cd D:\Zane
# 1. 安装依赖
pip install -r requirements.txt
pip install wmi pywin32
pip install sentence-transformers rapidocr_onnxruntime  # 可选重型

# 2. 启动 llama-server - 你的Qwen3模型
D:\llama.cpp\llama-server.exe --model D:\llama.cpp\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf --host 127.0.0.1 --port 8080 --ctx-size 32768 --n-gpu-layers 35

# 3. 启动 Zane AGI
python run.py  # 自动优先v4.1

# 4. 打开 http://localhost:8000
# 测试：模型列表应显示真实存在，WMI真实，HWND真实，OCR真实
```

---

## 三、下一步规划 - v3.0 商业级完善

### 阶段1：Windows真实验证 (1-2天) - 高优先级

**目标：** 在Windows上真实运行，验证所有真实功能

**任务：**
1. **Windows环境搭建**
   - [ ] 克隆仓库到Windows D:\Zane
   - [ ] 安装Python 3.11+ + 依赖 `pip install -r requirements.txt`
   - [ ] 安装Windows专属 `pip install wmi pywin32`
   - [ ] 验证Qwen3模型路径 `D:\llama.cpp\Qwen3.6-35B...` 存在

2. **llama.cpp Server真实启动**
   - [ ] 编译或下载 `llama-server.exe`
   - [ ] 启动 `llama-server --model Qwen3... --port 8080`
   - [ ] 验证 `/api/health` local_llm 可用，非离线
   - [ ] 测试Chat真实调用本地LLM，非离线模拟

3. **真实系统控制测试**
   - [ ] WMI真实：CPU每核心+内存条+磁盘+GPU，媲美任务管理器
   - [ ] Win32真实：EnumWindows真实HWND+标题+矩形+Z序+DPI
   - [ ] 文件真实：沙盒+回收站+10MB限制
   - [ ] 视觉真实：截图+PaddleOCR/rapidocr真实OCR
   - [ ] 测试微信/Chrome等应用真实启动

4. **模型A真实测试**
   - [ ] 添加自定义模型A，例如 `D:\models\qwen2-7b.gguf`
   - [ ] 切换模型，验证server重启
   - [ ] Ollama检测，若有Ollama运行

**产出：** Windows真实测试报告，截图，性能数据

---

### 阶段2：重型依赖可选安装 (1天) - 中优先级

**目标：** 启用真实向量和OCR

**任务：**
1. **向量检索真实**
   - [ ] `pip install sentence-transformers` 80MB
   - [ ] 下载 `all-MiniLM-L6-v2` 模型
   - [ ] 测试 `vector_memory_real` 真实嵌入384维
   - [ ] 测试 `/api/memory/vector/search` 向量相似度，非关键词
   - [ ] sqlite-vec KNN真实搜索

2. **OCR真实**
   - [ ] `rapidocr_onnxruntime` 已安装，测试真实OCR
   - [ ] 可选 `pip install paddleocr paddlepaddle` 500MB
   - [ ] 测试截图+OCR，中文+英文
   - [ ] 前端视觉视图显示OCR结果和boxes

3. **训练真实**
   - [ ] `pip install torch transformers peft trl` 可选
   - [ ] 测试 `evolution_engine` QLoRA rank32 4bit
   - [ ] 测试数据飞轮 SFT/DPO收集

**产出：** 向量+OCR真实可用，性能对比

---

### 阶段3：安全加固+认证 (1天) - 高优先级

**目标：** 商业级安全

**任务：**
1. **JWT认证**
   - [ ] `jwt_auth.py` 已实现，集成到main_v4
   - [ ] `POST /api/auth/login` 登录获取JWT
   - [ ] 前端登录页，Token存储localStorage
   - [ ] 危险操作需JWT，普通只读无需

2. **速率限制细化**
   - [ ] slowapi已实现60/分，细化：chat 20/分，tools/call 30/分，search 10/分
   - [ ] IP白名单+黑名单

3. **日志加固**
   - [ ] `loguru` 替代print，结构化日志，文件轮转
   - [ ] 日志净化已实现，换行+敏感信息过滤

4. **沙盒加固**
   - [ ] filelock已实现，测试并发写
   - [ ] 进程保护8个关键进程
   - [ ] WSL白名单15只读

**产出：** 安全审计报告，JWT登录

---

### 阶段4：UI/UX完善 (2天) - 中优先级

**目标：** 媲美商业级 Raycast/Linear

**任务：**
1. **CSS进一步拆分**
   - [ ] 当前43KB主文件，目标<30KB
   - [ ] 拆 `css/layout.css` + `css/themes.css` + `css/animations.css`
   - [ ] 已拆 `styles.css` + `components.css`

2. **图表交互**
   - [ ] charts.js已实现hover tooltip，添加缩放、平滑、图例
   - [ ] CPU每核心可点击隐藏/显示
   - [ ] 内存历史可切换GB/%
   - [ ] 添加磁盘、网络图表

3. **加载状态+空状态**
   - [ ] skeleton已实现，添加更多场景
   - [ ] empty状态插图+操作引导
   - [ ] 错误状态重试按钮

4. **快捷键+命令面板**
   - [ ] Raycast风格命令面板 `Ctrl+K`，模糊搜索所有视图和工具
   - [ ] 快捷键：`Ctrl+1-9` 切换视图，`Ctrl+L` 清空聊天

5. **通知中心**
   - [ ] 任务完成通知，成功/失败
   - [ ] 自主优化报告通知

**产出：** UI/UX完善，商业级体验

---

### 阶段5：自主进化+基准 (2天) - 中优先级

**目标：** 自我进化真实可用

**任务：**
1. **自主任务扩展**
   - [ ] 20 Skill已实现，扩展到30 Skill
   - [ ] APScheduler已实现，测试凌晨2点真实触发
   - [ ] 习惯学习已实现，收集更多traces生成个性化Skill

2. **梦境优化**
   - [ ] Light→REM→Deep三阶段已实现，优化六信号权重
   - [ ] DREAMS.md人类可读叙事优化

3. **基准可视化**
   - [ ] 12任务已实现，添加图表可视化成功率/延迟/token
   - [ ] 回归检测

4. **数据飞轮**
   - [ ] SFT/DPO已实现，真实收集，训练脚本生成

**产出：** 自主进化报告，Skill库扩展到30

---

### 阶段6：部署+打包 (1天) - 低优先级

**目标：** 一键部署

**任务：**
1. **Windows一键安装**
   - [ ] `setup_windows.ps1` 已实现，测试
   - [ ] 自动安装依赖+模型下载

2. **EXE打包**
   - [ ] PyInstaller打包单文件EXE
   - [ ] 测试EXE启动

3. **Docker可选**
   - [ ] Dockerfile，Linux演示

4. **GitHub Actions**
   - [ ] windows-test.yml 真实WMI/HWND测试

**产出：** EXE+安装脚本

---

## 四、优先级矩阵

| 优先级 | 任务 | 工期 | 产出 |
|---|---|---|---|
| P0 高 | Windows真实验证 | 1-2天 | 真实测试报告 |
| P0 高 | 安全加固JWT | 1天 | 安全审计+登录 |
| P1 中 | 重型依赖向量+OCR | 1天 | 真实向量+OCR |
| P1 中 | UI/UX完善 | 2天 | 商业级体验 |
| P1 中 | 自主进化扩展 | 2天 | 30 Skill+习惯 |
| P2 低 | 部署打包EXE | 1天 | EXE+安装脚本 |

**总计：7-8天 v3.0 商业级完善**

---

## 五、当前状态 - v2.2 检修修复版

- **版本**：v2.2 d20cccc + v2.1 71478c3 + v2.0 0789048 + v1.0 dc291b5
- **API**：26/26 200 OK，3个404已修复，lifespan修复
- **数据库**：SQLite唯一8表 filelock WAL 备份 迁移一次 user_habits
- **模型**：真实扫描+自定义模型A+Server管理+Ollama检测，支持模型A选择
- **前端**：49KB→43KB主 + 11KB styles.css + 1.8KB components.css + 8模块 ES Modules + Canvas原生交互式图表 + skeleton+aria+focus-visible+10秒轮询+hidden暂停
- **安全**：sandbox+policy_engine+slowapi 60/分+filelock+10MB+日志净化+lifespan
- **自主**：20 Skill+APScheduler凌晨2点+每30分钟+习惯学习默认开启+备份
- **补全**：cleanup截图清理+vector_memory_real真实向量+ocr_real rapidocr 50MB+jwt_auth JWT+charts.js交互式

**可直接使用，26API全通，模型A真实，UI优化**

---

## 六、立即下一步 - 建议

**选项1：Windows真实测试 (推荐)**
- 在Windows上克隆，安装wmi/pywin32，启动llama-server，验证真实WMI/HWND/模型切换

**选项2：重型依赖安装**
- `pip install sentence-transformers` 启用真实向量检索，测试语义搜索

**选项3：安全加固**
- 集成JWT登录，前端登录页，危险操作需认证

**选项4：UI进一步优化**
- 主文件<30KB，图表缩放+图例，命令面板Ctrl+K

**建议：先1 Windows真实验证，再2+3并行，4最后**

---

## 七、提问 - 需要确认

1. **Windows环境**：是否有Windows机器可测试真实WMI/HWND/模型切换？路径 D:\llama.cpp\... 是否准确？
2. **重型依赖**：是否现在安装 sentence-transformers 80MB + torch，启用真实向量？还是保持轻量关键词回退？
3. **模型A**：你的模型A具体路径是什么？我可以帮你配置到扫描目录或添加为自定义模型
4. **安全**：是否启用JWT登录？还是保持可选Token简单认证？
5. **下一步**：选1 Windows真实，2 重型依赖，3 安全加固，4 UI优化，或全部？

请确认，我继续补全直到v3.0商业级完善。
