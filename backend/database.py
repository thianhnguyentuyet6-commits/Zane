# -*- coding: utf-8 -*-
"""
Database - 数据库层
技术栈：SQLite主 + JSON兼容 + sqlite-vec可选向量 + 嵌入

为什么这样设计：
- 本地优先，无需安装，单文件，Windows兼容
- SQLite：事务，WAL，并发，索引，5000条以上仍快
- JSON兼容：原有data/*.json自动迁移到SQLite
- 向量：sqlite-vec可选，80MB嵌入模型，无则关键词回退
- 备份：定时备份到 .backup/
"""

import os
import json
import sqlite3
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

class Database:
    """数据库 - SQLite + JSON兼容"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "data", "zane.db")
        self.db_path = os.path.abspath(self.db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # 启用WAL模式，提升并发
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA cache_size=-64000;")  # 64MB缓存
        
        self._init_tables()
        self._migrate_from_json()
        
        # 尝试加载sqlite-vec
        self.vec_available = False
        try:
            import sqlite_vec
            self.conn.enable_load_extension(True)
            sqlite_vec.load(self.conn)
            self.conn.enable_load_extension(False)
            self.vec_available = True
            self._init_vec_tables()
            print("✅ sqlite-vec 向量数据库可用")
        except Exception as e:
            print(f"⚠️ sqlite-vec 不可用，使用关键词回退: {e}")
    
    def _init_tables(self):
        """初始化表"""
        
        # 1. 记忆表 - 5类型
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,  -- working, episodic, semantic, procedural, preference
                content TEXT NOT NULL,
                metadata TEXT,  -- JSON
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                last_accessed REAL NOT NULL
            )
        """)
        
        # 2. 技能表 - 版本化
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                version TEXT DEFAULT '1.0.0',
                trigger_conditions TEXT,  -- JSON array
                required_tools TEXT,  -- JSON array
                procedure TEXT,  -- JSON array
                parameters TEXT,  -- JSON
                preconditions TEXT,  -- JSON array
                verification_rules TEXT,  -- JSON array
                failure_recovery TEXT,  -- JSON
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                tags TEXT,  -- JSON array
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        
        # 3. 任务轨迹表 - 统一
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                task_id TEXT PRIMARY KEY,
                user_request TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                success BOOLEAN,
                final_outcome TEXT,
                latency_ms INTEGER,
                tool_calls TEXT,  -- JSON array
                observations TEXT,  -- JSON
                verification_results TEXT,  -- JSON
                failures TEXT,  -- JSON
                token_usage TEXT,  -- JSON
                confidence REAL,
                created_at REAL NOT NULL
            )
        """)
        
        # 4. 训练数据表 - 数据飞轮
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS training_data (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,  -- sft, dpo
                task TEXT NOT NULL,
                conversations TEXT,  -- JSON
                tools_used TEXT,  -- JSON
                created_at REAL NOT NULL
            )
        """)
        
        # 5. Token表 - 可替换Tokens
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                token_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                env_key TEXT NOT NULL,
                has_value BOOLEAN DEFAULT 0,
                updated_at REAL NOT NULL
            )
        """)
        
        # 6. 自主优化报告表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_reports (
                id TEXT PRIMARY KEY,
                report TEXT NOT NULL,  -- JSON
                skills_added INTEGER DEFAULT 0,
                repos_queried INTEGER DEFAULT 0,
                failures_analyzed INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            )
        """)
        
        # 创建索引
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_traces_success ON traces(success);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_traces_start_time ON traces(start_time DESC);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_training_type ON training_data(type);")
        
        self.conn.commit()
    
    def _init_vec_tables(self):
        """初始化向量表"""
        if not self.vec_available:
            return
        
        try:
            self.conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding FLOAT[384]
                )
            """)
            self.conn.commit()
        except Exception as e:
            print(f"向量表初始化失败: {e}")
            self.vec_available = False
    
    def _migrate_from_json(self):
        """从JSON迁移到SQLite - 兼容旧数据"""
        try:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            
            # 检查是否已迁移
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM memories")
            if cursor.fetchone()["count"] > 0:
                return  # 已有数据，跳过迁移
            
            # 迁移 episodic.json
            episodic_path = os.path.join(data_dir, "episodic.json")
            if os.path.exists(episodic_path):
                try:
                    with open(episodic_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for item in data:
                            if isinstance(item, dict):
                                content = item.get("task", "") + " " + item.get("result", "")
                                self.add_memory(
                                    type="episodic",
                                    content=content,
                                    metadata=item,
                                    importance=0.6
                                )
                    print(f"✅ 迁移 episodic.json {len(data)}条")
                except Exception as e:
                    print(f"迁移episodic失败: {e}")
            
            # 迁移 semantic.json
            semantic_path = os.path.join(data_dir, "semantic.json")
            if os.path.exists(semantic_path):
                try:
                    with open(semantic_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for item in data:
                            if isinstance(item, dict):
                                content = item.get("fact", "") or item.get("content", "") or str(item)
                                self.add_memory(
                                    type="semantic",
                                    content=content,
                                    metadata=item,
                                    importance=item.get("confidence", 0.7)
                                )
                    print(f"✅ 迁移 semantic.json {len(data)}条")
                except Exception as e:
                    print(f"迁移semantic失败: {e}")
        
        except Exception as e:
            print(f"迁移失败: {e}")
    
    # ========== 记忆操作 ==========
    def add_memory(self, type: str, content: str, metadata: Dict = None, importance: float = 0.5) -> str:
        mem_id = f"mem_{type}_{int(time.time()*1000)}"
        now = time.time()
        
        self.conn.execute("""
            INSERT INTO memories (id, type, content, metadata, importance, access_count, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
        """, (mem_id, type, content, json.dumps(metadata or {}, ensure_ascii=False), importance, now, now))
        self.conn.commit()
        
        return mem_id
    
    def search_memories(self, query: str, types: List[str] = None, limit: int = 5) -> List[Dict]:
        """搜索记忆 - 关键词，未来向量"""
        types = types or ["semantic", "episodic", "preference"]
        
        # 关键词搜索
        placeholders = ",".join(["?"] * len(types))
        sql = f"""
            SELECT * FROM memories 
            WHERE type IN ({placeholders})
            ORDER BY importance DESC, last_accessed DESC
            LIMIT ?
        """
        
        cursor = self.conn.execute(sql, (*types, limit*3))
        candidates = [dict(row) for row in cursor.fetchall()]
        
        # 简单评分
        query_lower = query.lower()
        scored = []
        for item in candidates:
            score = 0
            content_lower = item["content"].lower()
            for kw in query_lower.split():
                if kw in content_lower:
                    score += 1
            score += item["importance"] * 0.5
            
            # 时间衰减 episodic
            if item["type"] == "episodic":
                days = (time.time() - item["created_at"]) / 86400
                decay = max(0.1, 1 - days / 30)
                score *= decay
            
            if score > 0:
                scored.append((score, item))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        result = [item for _, item in scored[:limit]]
        
        # 更新访问计数
        for item in result:
            self.conn.execute("UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?", (time.time(), item["id"]))
        self.conn.commit()
        
        return result
    
    def get_memory_stats(self) -> Dict:
        cursor = self.conn.execute("SELECT type, COUNT(*) as count FROM memories GROUP BY type")
        stats = {row["type"]: row["count"] for row in cursor.fetchall()}
        
        cursor = self.conn.execute("SELECT COUNT(*) as total FROM memories")
        total = cursor.fetchone()["total"]
        
        return {"total": total, "by_type": stats}
    
    # ========== 技能操作 ==========
    def add_skill(self, skill: Dict) -> str:
        now = time.time()
        self.conn.execute("""
            INSERT OR REPLACE INTO skills 
            (id, name, description, version, trigger_conditions, required_tools, procedure, parameters, preconditions, verification_rules, failure_recovery, success_count, failure_count, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            skill.get("id", f"skill_{int(now*1000)}"),
            skill["name"],
            skill.get("description", ""),
            skill.get("version", "1.0.0"),
            json.dumps(skill.get("trigger_conditions", []), ensure_ascii=False),
            json.dumps(skill.get("required_tools", []), ensure_ascii=False),
            json.dumps(skill.get("procedure", []), ensure_ascii=False),
            json.dumps(skill.get("parameters", {}), ensure_ascii=False),
            json.dumps(skill.get("preconditions", []), ensure_ascii=False),
            json.dumps(skill.get("verification_rules", []), ensure_ascii=False),
            json.dumps(skill.get("failure_recovery", {}), ensure_ascii=False),
            skill.get("success_count", 0),
            skill.get("failure_count", 0),
            json.dumps(skill.get("tags", []), ensure_ascii=False),
            skill.get("created_at", now),
            now
        ))
        self.conn.commit()
        return skill["name"]
    
    def list_skills(self) -> List[Dict]:
        cursor = self.conn.execute("SELECT * FROM skills ORDER BY success_count DESC, updated_at DESC")
        skills = []
        for row in cursor.fetchall():
            skill = dict(row)
            # 解析JSON
            for field in ["trigger_conditions", "required_tools", "procedure", "parameters", "preconditions", "verification_rules", "failure_recovery", "tags"]:
                try:
                    skill[field] = json.loads(skill[field]) if skill[field] else []
                except:
                    pass
            skills.append(skill)
        return skills
    
    # ========== 轨迹操作 ==========
    def add_trace(self, trace: Dict):
        now = time.time()
        self.conn.execute("""
            INSERT OR REPLACE INTO traces 
            (task_id, user_request, start_time, end_time, success, final_outcome, latency_ms, tool_calls, observations, verification_results, failures, token_usage, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trace.get("task_id", f"task_{int(now*1000)}"),
            trace.get("user_request", ""),
            trace.get("start_time", now),
            trace.get("end_time", now),
            trace.get("success", False),
            trace.get("final_outcome", ""),
            trace.get("latency_ms", 0),
            json.dumps(trace.get("tool_calls", []), ensure_ascii=False),
            json.dumps(trace.get("observations", []), ensure_ascii=False),
            json.dumps(trace.get("verification_results", []), ensure_ascii=False),
            json.dumps(trace.get("failures", []), ensure_ascii=False),
            json.dumps(trace.get("token_usage", {}), ensure_ascii=False),
            trace.get("confidence", 0.0),
            now
        ))
        self.conn.commit()
    
    def list_traces(self, limit: int = 20) -> List[Dict]:
        cursor = self.conn.execute("SELECT task_id, user_request, success, latency_ms, tool_calls, start_time FROM traces ORDER BY start_time DESC LIMIT ?", (limit,))
        result = []
        for row in cursor.fetchall():
            tool_calls = json.loads(row["tool_calls"]) if row["tool_calls"] else []
            result.append({
                "task_id": row["task_id"],
                "user_request": row["user_request"][:100],
                "success": bool(row["success"]),
                "latency_ms": row["latency_ms"],
                "tool_calls": len(tool_calls),
                "start_time": row["start_time"]
            })
        return result
    
    def get_trace_stats(self) -> Dict:
        cursor = self.conn.execute("SELECT COUNT(*) as total, SUM(CASE WHEN success THEN 1 ELSE 0 END) as success FROM traces")
        row = cursor.fetchone()
        total = row["total"] or 0
        success = row["success"] or 0
        
        cursor = self.conn.execute("SELECT AVG(latency_ms) as avg_lat FROM traces")
        avg_lat = cursor.fetchone()["avg_lat"] or 0
        
        return {
            "total": total,
            "success": success,
            "success_rate": round(success / total * 100, 1) if total else 0,
            "avg_latency_ms": int(avg_lat),
            "database": "SQLite"
        }
    
    def get_tech_stack(self) -> Dict:
        """技术栈信息"""
        return {
            "database": {
                "primary": "SQLite",
                "file": self.db_path,
                "size_mb": round(os.path.getsize(self.db_path) / 1024 / 1024, 2) if os.path.exists(self.db_path) else 0,
                "mode": "WAL",
                "tables": ["memories", "skills", "traces", "training_data", "tokens", "autonomous_reports"],
                "indexes": ["type, importance, success, start_time"],
                "vector": "sqlite-vec" if self.vec_available else "关键词回退",
                "embedding": "all-MiniLM-L6-v2 80MB (可选)",
                "why": "本地优先，无需安装，单文件，Windows兼容，事务，并发，索引"
            },
            "backend": {
                "framework": "FastAPI 0.115.0",
                "server": "Uvicorn 0.32.0",
                "language": "Python 3.11+",
                "system": "psutil 6.1.0 + WMI 1.5.1 + pywin32 308",
                "vision": "Pillow 11.0.0 + PaddleOCR (规划)",
                "network": "httpx 0.27.2 + Bing API + GitHub API + DuckDuckGo",
                "ai": "Qwen3-30B-A3B MoE 30B/3B IQ4_XS + llama.cpp",
                "training": "datasets 3.0.0 + unsloth + torch + transformers + trl + peft",
                "security": "sandbox + policy_engine + rate_limiter + auth",
                "architecture": "8层精简 + 12模块Runtime",
                "lines": "12245行"
            },
            "frontend": {
                "framework": "原生HTML/CSS/JS，无打包",
                "size": "55KB <100ms",
                "style": "深色 Linear/Raycast，CSS变量，SF Mono + JetBrains Mono + Noto Sans SC",
                "views": "16视图，专业控制台",
                "tech": "Fetch API + CSS变量 + 原生JS",
                "lines": "app.js 707行 + index.html 55KB"
            },
            "deployment": {
                "port": "单端口8000",
                "frontend": "已写入content，无需单独部署",
                "command": "python run.py 或 uvicorn backend.main_v3:app --host 0.0.0.0 --port 8000",
                "windows": "scripts/setup_windows.ps1 一键安装",
                "exe": "PyInstaller 规划"
            }
        }

# 全局
database = Database()
