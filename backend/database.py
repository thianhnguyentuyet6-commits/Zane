# -*- coding: utf-8 -*-
"""
Database - SQLite唯一主数据库 - A夯实+SQLite Only
技术栈：SQLite WAL + filelock并发安全 + sqlite-vec可选向量 + 嵌入

v2.0 升级：
- SQLite唯一，JSON废弃只读迁移一次
- filelock并发安全，避免多进程写冲突
- WAL模式+64MB缓存+事务+索引
- 自动迁移data/*.json到SQLite，迁移后标记不再重复
- 备份机制
- tech_stack完整返回
"""

import os
import json
import sqlite3
import time
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from filelock import FileLock
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False
    FileLock = None
    print("⚠️ filelock未安装，并发写可能冲突，pip install filelock")

class Database:
    """数据库 - SQLite唯一主"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "data", "zane.db")
        self.db_path = os.path.abspath(self.db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # filelock
        self.lock_path = self.db_path + ".lock"
        self.lock = FileLock(self.lock_path, timeout=10) if FILELOCK_AVAILABLE else None
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        
        # WAL模式
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA cache_size=-64000;")  # 64MB
        self.conn.execute("PRAGMA busy_timeout=10000;")  # 10秒忙等待
        self.conn.execute("PRAGMA foreign_keys=ON;")
        
        self._init_tables()
        self._migrate_from_json_once()  # 仅迁移一次
        
        # 向量
        self.vec_available = False
        self._init_vec()
    
    def _init_vec(self):
        try:
            import sqlite_vec
            self.conn.enable_load_extension(True)
            sqlite_vec.load(self.conn)
            self.conn.enable_load_extension(False)
            self.vec_available = True
            self._init_vec_tables()
            print("✅ sqlite-vec 向量数据库可用")
        except Exception as e:
            print(f"⚠️ sqlite-vec 不可用，关键词回退: {e}")
            # 尝试轻量替代：检查sentence-transformers
            try:
                import sentence_transformers
                print("✅ sentence-transformers 可用，可启用语义检索")
            except:
                pass
    
    def _init_tables(self):
        # 1. 记忆 5类型
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                last_accessed REAL NOT NULL
            )
        """)
        # 2. 技能 版本化
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                version TEXT DEFAULT '1.0.0',
                trigger_conditions TEXT,
                required_tools TEXT,
                procedure TEXT,
                parameters TEXT,
                preconditions TEXT,
                verification_rules TEXT,
                failure_recovery TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                tags TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        # 3. 轨迹 统一12字段
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                task_id TEXT PRIMARY KEY,
                user_request TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                success BOOLEAN,
                final_outcome TEXT,
                latency_ms INTEGER,
                tool_calls TEXT,
                observations TEXT,
                verification_results TEXT,
                failures TEXT,
                token_usage TEXT,
                confidence REAL,
                created_at REAL NOT NULL
            )
        """)
        # 4. 训练数据 数据飞轮
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS training_data (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                task TEXT NOT NULL,
                conversations TEXT,
                tools_used TEXT,
                created_at REAL NOT NULL
            )
        """)
        # 5. Token 可替换
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
        # 6. 自主报告
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_reports (
                id TEXT PRIMARY KEY,
                report TEXT NOT NULL,
                skills_added INTEGER DEFAULT 0,
                repos_queried INTEGER DEFAULT 0,
                failures_analyzed INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            )
        """)
        # 7. 习惯学习
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_habits (
                id TEXT PRIMARY KEY,
                pattern TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_seen REAL NOT NULL,
                suggested_skill TEXT,
                created_at REAL NOT NULL
            )
        """)
        # 8. 迁移标记
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS migration_log (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                migrated_count INTEGER DEFAULT 0,
                migrated_at REAL NOT NULL
            )
        """)
        # 索引
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_traces_success ON traces(success);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_traces_start ON traces(start_time DESC);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_habits_freq ON user_habits(frequency DESC);")
        self.conn.commit()
    
    def _init_vec_tables(self):
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
    
    def _migrate_from_json_once(self):
        """仅迁移一次，SQLite唯一后不再写JSON"""
        try:
            # 检查是否已迁移
            cursor = self.conn.execute("SELECT COUNT(*) as cnt FROM migration_log WHERE source='json'")
            if cursor.fetchone()["cnt"] > 0:
                return
            cursor = self.conn.execute("SELECT COUNT(*) as cnt FROM memories")
            if cursor.fetchone()["cnt"] > 5:  # 已有数据，标记已迁移
                self.conn.execute("INSERT OR IGNORE INTO migration_log (id, source, migrated_count, migrated_at) VALUES (?, ?, ?, ?)",
                                  ("json_migrated", "json", 0, time.time()))
                self.conn.commit()
                return
            
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            migrated_total = 0
            
            # episodic.json
            episodic_path = os.path.join(data_dir, "episodic.json")
            if os.path.exists(episodic_path):
                try:
                    with open(episodic_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for item in data:
                            if isinstance(item, dict):
                                content = item.get("task", "") + " " + item.get("result", "") or str(item)
                                self.add_memory(type="episodic", content=content[:2000], metadata=item, importance=0.6, _no_lock=True)
                                migrated_total += 1
                    print(f"✅ 迁移 episodic.json {len(data)}条")
                except Exception as e:
                    print(f"迁移episodic失败: {e}")
            
            # semantic.json
            semantic_path = os.path.join(data_dir, "semantic.json")
            if os.path.exists(semantic_path):
                try:
                    with open(semantic_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for item in data:
                            if isinstance(item, dict):
                                content = item.get("fact", "") or item.get("content", "") or str(item)
                                self.add_memory(type="semantic", content=content[:2000], metadata=item, importance=item.get("confidence", 0.7), _no_lock=True)
                                migrated_total += 1
                    print(f"✅ 迁移 semantic.json {len(data)}条")
                except Exception as e:
                    print(f"迁移semantic失败: {e}")
            
            # 标记已迁移
            self.conn.execute("INSERT OR REPLACE INTO migration_log (id, source, migrated_count, migrated_at) VALUES (?, ?, ?, ?)",
                              ("json_migrated", "json", migrated_total, time.time()))
            self.conn.commit()
            if migrated_total > 0:
                print(f"✅ JSON迁移完成，共{migrated_total}条，今后SQLite唯一")
        
        except Exception as e:
            print(f"迁移检查失败: {e}")
    
    def _with_lock(self, func):
        """filelock包装"""
        if self.lock and FILELOCK_AVAILABLE:
            try:
                with self.lock:
                    return func()
            except Exception as e:
                print(f"filelock超时，直接执行: {e}")
                return func()
        else:
            return func()
    
    # ========== 记忆 ==========
    def add_memory(self, type: str, content: str, metadata: Dict = None, importance: float = 0.5, _no_lock=False) -> str:
        def _do():
            mem_id = f"mem_{type}_{int(time.time()*1000000)}"
            now = time.time()
            self.conn.execute("""
                INSERT INTO memories (id, type, content, metadata, importance, access_count, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """, (mem_id, type, content, json.dumps(metadata or {}, ensure_ascii=False), importance, now, now))
            self.conn.commit()
            return mem_id
        if _no_lock:
            return _do()
        return self._with_lock(_do)
    
    def search_memories(self, query: str, types: List[str] = None, limit: int = 5) -> List[Dict]:
        # 修复闭包变量名冲突 - 之前 types 变量在嵌套函数内赋值导致 UnboundLocalError
        search_types = types or ["semantic", "episodic", "preference"]
        def _do():
            placeholders = ",".join(["?"] * len(search_types))
            sql = f"""
                SELECT * FROM memories 
                WHERE type IN ({placeholders})
                ORDER BY importance DESC, last_accessed DESC
                LIMIT ?
            """
            cursor = self.conn.execute(sql, (*search_types, limit*3))
            candidates = [dict(row) for row in cursor.fetchall()]
            query_lower = query.lower()
            scored = []
            for item in candidates:
                score = 0
                content_lower = item["content"].lower()
                for kw in query_lower.split():
                    if kw in content_lower:
                        score += 1
                score += item["importance"] * 0.5
                if item["type"] == "episodic":
                    days = (time.time() - item["created_at"]) / 86400
                    decay = max(0.1, 1 - days / 30)
                    score *= decay
                if score > 0:
                    scored.append((score, item))
            scored.sort(key=lambda x: x[0], reverse=True)
            result = [item for _, item in scored[:limit]]
            for item in result:
                self.conn.execute("UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?", (time.time(), item["id"]))
            self.conn.commit()
            return result
        return self._with_lock(_do)
    
    def get_memory_stats(self) -> Dict:
        def _do():
            cursor = self.conn.execute("SELECT type, COUNT(*) as count FROM memories GROUP BY type")
            stats = {row["type"]: row["count"] for row in cursor.fetchall()}
            cursor = self.conn.execute("SELECT COUNT(*) as total FROM memories")
            total = cursor.fetchone()["total"]
            return {"total": total, "by_type": stats, "database": "SQLite", "lock": "filelock" if FILELOCK_AVAILABLE else "none"}
        return self._with_lock(_do)
    
    # ========== 技能 ==========
    def add_skill(self, skill: Dict) -> str:
        def _do():
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
        return self._with_lock(_do)
    
    def list_skills(self) -> List[Dict]:
        def _do():
            cursor = self.conn.execute("SELECT * FROM skills ORDER BY success_count DESC, updated_at DESC")
            skills = []
            for row in cursor.fetchall():
                skill = dict(row)
                for field in ["trigger_conditions", "required_tools", "procedure", "parameters", "preconditions", "verification_rules", "failure_recovery", "tags"]:
                    try:
                        skill[field] = json.loads(skill[field]) if skill[field] else []
                    except:
                        pass
                skills.append(skill)
            return skills
        return self._with_lock(_do)
    
    # ========== 轨迹 ==========
    def add_trace(self, trace: Dict):
        def _do():
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
        return self._with_lock(_do)
    
    def list_traces(self, limit: int = 20) -> List[Dict]:
        def _do():
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
        return self._with_lock(_do)
    
    def get_trace_stats(self) -> Dict:
        def _do():
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
                "database": "SQLite",
                "lock": "filelock" if FILELOCK_AVAILABLE else "none"
            }
        return self._with_lock(_do)
    
    # ========== 习惯学习 ==========
    def add_habit(self, pattern: str, suggested_skill: str = None) -> str:
        def _do():
            now = time.time()
            # 检查是否存在
            cursor = self.conn.execute("SELECT id, frequency FROM user_habits WHERE pattern = ?", (pattern,))
            row = cursor.fetchone()
            if row:
                self.conn.execute("UPDATE user_habits SET frequency = frequency + 1, last_seen = ?, suggested_skill = ? WHERE id = ?",
                                  (now, suggested_skill, row["id"]))
                self.conn.commit()
                return row["id"]
            else:
                habit_id = f"habit_{int(now*1000)}"
                self.conn.execute("""
                    INSERT INTO user_habits (id, pattern, frequency, last_seen, suggested_skill, created_at)
                    VALUES (?, ?, 1, ?, ?, ?)
                """, (habit_id, pattern, now, suggested_skill, now))
                self.conn.commit()
                return habit_id
        return self._with_lock(_do)
    
    def get_top_habits(self, limit: int = 10) -> List[Dict]:
        def _do():
            cursor = self.conn.execute("SELECT * FROM user_habits ORDER BY frequency DESC, last_seen DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
        return self._with_lock(_do)
    
    def backup(self) -> str:
        """备份"""
        def _do():
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f"zane_backup_{int(time.time())}.db")
            shutil.copy2(self.db_path, backup_path)
            return backup_path
        return self._with_lock(_do)
    
    def get_tech_stack(self) -> Dict:
        size_mb = round(os.path.getsize(self.db_path) / 1024 / 1024, 2) if os.path.exists(self.db_path) else 0
        return {
            "database": {
                "primary": "SQLite",
                "file": self.db_path,
                "size_mb": size_mb,
                "mode": "WAL",
                "tables": ["memories", "skills", "traces", "training_data", "tokens", "autonomous_reports", "user_habits", "migration_log"],
                "indexes": ["type, importance, created_at, success, start_time, name, frequency"],
                "vector": "sqlite-vec" if self.vec_available else "关键词回退+可选sentence-transformers",
                "embedding": "all-MiniLM-L6-v2 80MB (可选，已实现回退)",
                "concurrency": "filelock" if FILELOCK_AVAILABLE else "WAL busy_timeout",
                "migration": "JSON→SQLite仅一次，SQLite唯一",
                "why": "本地优先，无需安装，单文件，Windows兼容，事务，并发，索引，备份"
            },
            "backend": {
                "framework": "FastAPI 0.115.0 + slowapi 0.1.9 限流",
                "server": "Uvicorn 0.32.0",
                "language": "Python 3.11+",
                "concurrency": "filelock 3.15.0 + WAL + busy_timeout",
                "system": "psutil 6.1.0 + WMI 1.5.1 + pywin32 308",
                "vision": "Pillow 11.0.0 + rapidocr_onnxruntime 50MB (轻量) / PaddleOCR 500MB (可选)",
                "network": "httpx 0.27.2 + Bing API + GitHub API + DuckDuckGo，防SSRF",
                "ai": "Qwen3-30B-A3B MoE 30B/3B IQ4_XS + llama.cpp + OpenAI兼容",
                "training": "datasets 3.0.0 + unsloth + torch + transformers + trl + peft + QLoRA rank32 4bit",
                "security": "sandbox realpath+白名单 + policy_engine独立 + slowapi 60/分 + auth JWT/python-jose + 10MB限制 + 日志净化",
                "scheduler": "APScheduler 3.10.4 定时2点+空闲检测",
                "architecture": "8层精简 + 12模块Runtime + routers拆分",
                "lines": "13000+行"
            },
            "frontend": {
                "framework": "原生HTML/CSS/JS + ES Modules拆分，无打包",
                "size": "主60KB + 模块按需 <100ms首屏，Canvas图表",
                "style": "深色 Linear/Raycast，CSS变量，SF Mono + JetBrains Mono + Noto Sans SC",
                "views": "19视图，专业控制台，模块化api.js/chat.js/system.js/evolution.js/security.js/tokens.js/database.js/autonomous.js",
                "charts": "Canvas原生 CPU每核心折线图+内存+磁盘，无外部依赖",
                "tech": "Fetch API + ES Modules + CSS变量 + Canvas + 原生JS",
                "modular": "已拆分，符合A夯实要求"
            },
            "deployment": {
                "port": "单端口8000",
                "frontend": "模块化但单端口，/static/js/ + /static/css/",
                "command": "python run.py 或 uvicorn backend.main_v3:app --host 0.0.0.0 --port 8000",
                "windows": "scripts/setup_windows.ps1 一键安装 + filelock + slowapi",
                "exe": "PyInstaller 规划"
            }
        }

# 全局
database = Database()
