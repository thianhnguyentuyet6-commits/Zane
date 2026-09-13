# Findings - Zane Windows全项目

## 已发现问题

### 1. VRAM 0GB (已修复)
- 原因：resource_config.json vram_threshold 18GB过高，torch检测失败无回退
- 修复：阈值18->6，四重检测torch+nvidia-smi+GPUtil+fallback 8GB
- 状态：已修复，显示8GB supports_8gb=True

### 2. /api/tools/call 422 (已修复)
- 原因：ToolCallRequest parameters无默认值，前端格式不兼容
- 修复：增加默认值+args/params兼容+get_params()合并
- 状态：已修复

### 3. 前端内部备注 (已修复)
- 原因：✨新特性/Impeccable/110API/Windows PC专注等内部开发备注写在UI
- 修复：已清理，用户友好文案
- 状态：已修复，0内部备注

### 4. 滚动条 (已修复)
- 原因：body overflow:hidden，app height:100vh
- 修复：overflow-y:auto，min-height:100vh
- 状态：已修复

### 5. 知识图谱无用 (部分修复)
- 原因：仅演示数据，无真实数据，无交互
- 修复：增加loadKnowledgeGraph()真实API+drawKnowledgeGraphReal()+点击交互
- 状态：部分修复，需进一步优化交互和数据

### 6. 系统检测失败 (待修复)
- 原因：WMI在Linux演示，Windows真实需测试，API容错不足
- 待修复：增加psutil回退+错误处理+真实数据

### 7. 模型未加载 (待修复)
- 原因：GGUF路径存在但llama.cpp未启动，VRAM检测失败导致推荐技能蒸馏
- 待修复：自动启动llama-server，模型加载状态显示

### 8. 依赖缺失 (待修复)
- 发现：sqlite-vec, apscheduler, python-jose, rapidocr, torch, GPUtil, wmi等可选依赖缺失
- 待修复：dependency_checker.py自动检测+下载补全

### 9. API真实性 (待修复)
- 发现：部分API返回演示数据，非真实
- 待修复：所有API返回真实数据

## 项目结构
- backend/: 86文件，114API，26工具，WMI+Win32，4层记忆
- frontend/: 90KB单文件，毛玻璃+渐变+知识图谱
- src-tauri/: Tauri 5模块，托盘+快捷键+自启+通知+窗口记忆
- tests/: 22测试 P0全部通过
- docs/: 报告+指南

## 热区
- frontend/index.html 17次变更最频繁
- backend/tools_impl.py 6次
- backend/learning/model_resolver.py VRAM检测
- backend/routers/runtime.py 工具调用

## 浅模块
- tools_impl.py 933行26工具单文件
- frontend/index.html 90KB单文件
- memory/ 6文件分散
- routers/ 18文件分散
