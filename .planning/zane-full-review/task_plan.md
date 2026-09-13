# Zane Windows全项目整理+Debug+依赖自动补全+真实API

## 目标
整理项目，Debug，检测缺失项，增加内置检测模块，检查依赖自动下载补全，API必须真实，优化前端PRO，代码审查，自动化测试

## 约束
- Windows专注，PC做好，前端写好，后端打牢
- 离线优先，本地LLM主引擎，云API仅可选教师
- 真实计算机控制非模拟，受控类型化接口
- 工具注册表+策略防火墙显式权限审计
- 简体中文优先，源码英文，UTF-8
- 单版本v0914干净，历史归档

## 阶段

### Phase 1: 项目整理 + 持久化规划 (planning-with-files)
- [x] 初始化.planning目录
- [ ] 创建task_plan.md, findings.md, progress.md
- [ ] 扫描项目结构，记录到findings.md
- [ ] 避免上下文限制，所有重要信息写磁盘

### Phase 2: 全项目Debug (systematic-debugging)
- [ ] 探索项目上下文
- [ ] 识别问题：VRAM 0GB, 422错误, 前端内部备注, 滚动条, 知识图谱无用, 系统检测失败, 模型未加载
- [ ] 修复已完成部分，验证
- [ ] 深度Debug剩余问题

### Phase 3: 依赖检测 + 自动补全 + 真实API
- [ ] 扫描所有依赖：requirements.txt vs 实际import
- [ ] 检测缺失：sqlite-vec, apscheduler, python-jose, rapidocr, torch, GPUtil, wmi, etc
- [ ] 增加内置检测模块 backend/utils/dependency_checker.py
- [ ] 自动下载补全：程序启动时检测，缺失则pip install或提示
- [ ] API必须真实：所有/api/*返回真实数据，非演示

### Phase 4: 前端PRO优化 (ui-ux-pro-max)
- [ ] 搜索设计系统：dashboard productivity tool
- [ ] 优化布局：滚动条、响应式、空状态、加载状态
- [ ] 优化交互：知识图谱可点击、系统检测真实、模型加载状态
- [ ] 移除所有内部备注，用户友好文案
- [ ] 可访问性：对比度4.5:1、键盘导航、ARIA

### Phase 5: 代码审查 (code-review)
- [ ] 审查自上次commit以来的变更
- [ ] Standards: 是否符合项目编码规范
- [ ] Spec: 是否符合用户需求（Windows专注、真实API、商业级）

### Phase 6: 自动化测试 (webapp-testing)
- [ ] 编写Playwright自动化测试脚本
- [ ] 测试前端功能：聊天、工具、系统状态、知识图谱、设置
- [ ] 测试后端API真实性
- [ ] 生成测试报告

## 文件
- task_plan.md: 本文件
- findings.md: 发现的问题和解决方案
- progress.md: 进度

## 成功标准
- 22/22 P0测试通过 + 新增依赖检测测试
- 所有API返回真实数据，非演示
- 前端无内部备注，滚动条正常，知识图谱可交互，系统检测真实
- 依赖缺失自动检测+下载补全
- 前端PRO级优化
- 代码审查通过
- 自动化测试通过
