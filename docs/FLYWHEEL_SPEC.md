# Zane v0913 数据飞轮v3评分机制 - 透明规格文档

> 解决缺点三：评分机制不透明，描述不是规格，调试变玄学

## 1. 评分维度与权重 - 明确规格

### 1.1 重要性评分 score_importance()

**文件**：`backend/runtime/data_filter.py` + `backend/memory/data_flywheel_v3.py`

**维度**：

| 维度 | 权重 | 说明 | 取值 | 实现 |
|------|------|------|------|------|
| 工具链复杂度 | 0.3 | 工具数量+种类多样性 | 0.5-0.9 | `len(tools) * 0.1 + len(set(tools)) * 0.05` |
| 验证通过 | 0.3 | 任务是否验证成功 | 0/0.3 | `verification.get('verified') ? 0.3 : 0` |
| 执行时间 | 0.2 | 执行时间合理性，太短可能失败，太长低效 | 0.1-0.2 | `exec_time_ms < 100 ? 0.1 : exec_time_ms < 5000 ? 0.2 : 0.1` |
| 任务类型 | 0.2 | 文件/系统/窗口/安全/网络，安全类权重高 | 0.1-0.2 | `security:0.2 file:0.15 system:0.15 window:0.1 network:0.1` |
| **总分** | **1.0** | **0.5-0.9** | **0.5-0.9** | `min(0.9, max(0.5, sum))` |

**代码**：
```python
def score_importance(sample: Dict) -> float:
    tools = sample.get("tools", [])
    verification = sample.get("verification", {})
    exec_time_ms = sample.get("exec_time_ms", 0)
    task_type = sample.get("task_type", "file")
    
    # 工具链复杂度 0.3
    tool_score = min(0.3, len(tools) * 0.05 + len(set(tools)) * 0.03)
    
    # 验证通过 0.3
    verify_score = 0.3 if verification.get("verified") else 0.1
    
    # 执行时间 0.2
    if exec_time_ms < 100:
        time_score = 0.1  # 太短可能失败
    elif exec_time_ms < 5000:
        time_score = 0.2  # 合理
    else:
        time_score = 0.1  # 太长低效
    
    # 任务类型 0.2
    type_weights = {"security": 0.2, "file": 0.15, "system": 0.15, "window": 0.1, "network": 0.1}
    type_score = type_weights.get(task_type, 0.1)
    
    total = tool_score + verify_score + time_score + type_score
    return round(min(0.9, max(0.5, total)), 2)
```

**示例**：
- 整理下载文件夹 `["list_files","create_folder"]` + 验证通过 + 500ms + file → 0.15+0.3+0.2+0.15=0.8 → 0.75 (实际)
- 删除System32 `["delete_file"]` + 危险路径 → is_safe False，不评分
- 系统监控 `["get_system_state","inspect_processes"]` + 验证通过 + 800ms + system → 0.1+0.3+0.2+0.15=0.75

### 1.2 质量评分 quality_score

**维度**：

| 维度 | 权重 | 说明 |
|------|------|------|
| 成功/失败 | 0.5 | 成功0.85-0.9，失败0.3-0.5 |
| 工具准确率 | 0.3 | 工具调用是否按Schema，参数正确 |
| 验证通过率 | 0.2 | 每次写后重新感知验证是否成功 |

**成功轨迹**：`quality_score 0.85` (success_trajectory)
**高质量**：`>0.8` 进入Replay Buffer

### 1.3 评分分布

**API**：`GET /api/evolution/filter/stats` + 新增 `GET /api/flywheel/stats`

**分布**：
- 0.5-0.6：低价值，简单任务，单工具，无验证 → 淘汰候选
- 0.6-0.7：中价值，2-3工具，有验证 → 保留
- 0.7-0.8：高价值，3+工具，验证通过，执行时间合理 → 保留+Replay
- 0.8-0.9：极高价值，复杂工具链，验证通过，安全类 → 保留+Replay+Prompt进化

**淘汰规则**：
- 低价值：`importance < 0.6` 且 `access_count < 3` 且 `age > 30天` → 遗忘
- 危险：`is_safe False` → 直接丢弃，不进训练
- 去重：`SHA256` 完全重复 + `相似度>0.9` 语义重复 → 过滤

## 2. 过滤机制 - 安全

### 2.1 危险路径11个

```python
DANGEROUS_PATHS = [
    "C:\\Windows\\System32", "C:\\Windows\\SysWOW64", "/etc/shadow", "/etc/passwd", 
    "/etc/sudoers", "/Windows/System32/drivers/etc/hosts", "/root/.ssh", 
    "/home/*/.ssh", "/etc/ssh", "C:\\Windows\\System32\\config", "/etc/gshadow"
]
```

**规则**：
- 危险路径 + 写入操作 `delete_file/write_file/kill_process` → `is_safe False` 拦截
- 核心路径 `C:\Windows\System32 /etc/shadow /etc/passwd` 即使只读 `list_files/read_file` 也过滤，不进训练

**验证**：
- `帮我删除C:\Windows\System32文件 + delete_file` → False 危险路径+写入操作 ✅
- `列出C:\Windows\System32文件 + list_files` → False 核心系统路径即使只读也不进训练 ✅

### 2.2 危险文件8个 + 危险进程7个 + 危险命令6个

- 危险文件：`/etc/passwd /etc/shadow .ssh/id_rsa password.txt credentials.json .env private_key`
- 危险进程：`csrss.exe winlogon.exe services.exe lsass.exe smss.exe wininit.exe svchost.exe` + `kill_process` → False
- 危险命令：`rm -rf / :(){:|:&};: mkfs format C: del /f /s /q C:\Windows rd /s /q C:\` → False

### 2.3 去重

- **SHA256**：完全相同样本去重
- **相似度>0.9**：语义相似度，任务+工具链相似 → 过滤
- **SimpleMem 30%**：高质量>0.8旧数据30%混合新数据，防灾难遗忘

## 3. 调试可观测 - API

### 3.1 GET /api/evolution/filter/stats

```json
{
  "stats": {
    "sft_samples": 50,
    "dpo_samples": 10,
    "total_filtered": 20,
    "safe_rate": 0.85,
    "deduped": 5,
    "high_quality": 10,
    "importance_avg": 0.75,
    "importance_distribution": {"0.5-0.6": 5, "0.6-0.7": 15, "0.7-0.8": 20, "0.8-0.9": 10}
  }
}
```

### 3.2 GET /api/flywheel/stats (新增)

```json
{
  "total": 100,
  "safe": 85,
  "unsafe": 15,
  "deduped": 5,
  "importance_distribution": {"0.5-0.6": 5, "0.6-0.7": 15, "0.7-0.8": 20, "0.8-0.9": 10},
  "quality_distribution": {"0.3-0.5": 10, "0.5-0.8": 60, "0.8-0.9": 30},
  "by_task_type": {"file": 40, "system": 30, "window": 10, "security": 15, "network": 5},
  "by_tool": {"list_files": 50, "read_file": 30, "create_folder": 20},
  "recent_samples": [{"task": "整理下载", "importance": 0.75, "quality": 0.85, "tools": ["list_files","create_folder"]}]
}
```

### 3.3 GET /api/evolution/filter/test

```json
POST /api/evolution/filter/test {"content":"帮我删除C:\\Windows\\System32文件","tools":["delete_file"]}
→ {"is_safe":false,"reason":"危险路径 C:\\Windows\\System32 + 写入操作","importance":0.6,"technique":"数据过滤安全检查"} ✅

POST /api/evolution/filter/test {"content":"帮我整理下载文件夹","tools":["list_files","create_folder"]}
→ {"is_safe":true,"reason":"安全","importance":0.75,"technique":"数据过滤安全检查"} ✅
```

## 4. 数据流

```
用户任务 → agent_runtime执行 → 成功/失败
  ↓
collect_from_success() → sample {conversations, tools, task, verification, exec_time_ms, task_type}
  ↓
data_filter.is_safe() → 危险路径0？是→丢弃 否→继续
  ↓
去重：SHA256 + 相似度>0.9 → 重复→丢弃
  ↓
评分：score_importance() → 0.5-0.9 + quality_score 0.3-0.9
  ↓
低价值淘汰：importance<0.6 + access<3 + age>30天 → 遗忘
  ↓
保存：data/training/sft.jsonl + replay_buffer.jsonl 30%高质量>0.8
  ↓
训练：Unsloth QLoRA rank32 → LoRA版本 models/versions/lora_*
  ↓
评估：Benchmark 20任务回放 → 成功率曲线 → 晋升>2%且security不下降
  ↓
记忆巩固：4层记忆遗忘低价值 + DREAMS.md
```

## 5. 为什么透明

- 调试不再玄学：知道为什么某条记忆被保留/丢弃，评分维度权重明确
- 可验证：评分分布API可查看，过滤测试API可验证危险拦截
- 可优化：权重可调整，淘汰规则可配置，`config/evolution_schedule.json`

---

**版本**：Zane v0913 单版本整合 | **文件**：`backend/memory/data_flywheel_v3.py` 14KB + `backend/runtime/data_filter.py` 11KB
