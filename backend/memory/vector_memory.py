# -*- coding: utf-8 -*-
"""
Vector Memory - 向量记忆
sqlite-vec 或 chromadb，轻量本地，语义检索
可选依赖，无则回退关键词
"""
import os
import json
import time
from typing import Dict, List, Any, Optional

class VectorMemory:
    """向量记忆 - 可选 sqlite-vec，无则关键词"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data", "memory")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.embedding_model = None
        self.vector_db = None
        self.use_vector = False
        
        # 尝试加载嵌入模型
        self._init_embedding()
    
    def _init_embedding(self):
        try:
            # 尝试 sentence-transformers
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB
            self.use_vector = True
            print("向量记忆：sentence-transformers 加载成功")
        except Exception as e:
            print(f"向量记忆：未安装 sentence-transformers，使用关键词回退: {e}")
            self.use_vector = False
        
        # 尝试 sqlite-vec
        if self.use_vector:
            try:
                import sqlite_vec
                import sqlite3
                db_path = os.path.join(self.data_dir, "vector.db")
                self.conn = sqlite3.connect(db_path)
                self.conn.enable_load_extension(True)
                sqlite_vec.load(self.conn)
                self.conn.enable_load_extension(False)
                
                # 创建表
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        content TEXT,
                        type TEXT,
                        embedding BLOB,
                        created_at REAL
                    )
                """)
                self.conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(
                        id TEXT PRIMARY KEY,
                        embedding FLOAT[384]
                    )
                """)
                print("向量记忆：sqlite-vec 初始化成功")
            except Exception as e:
                print(f"向量记忆：sqlite-vec 失败，使用内存: {e}")
                self.conn = None
    
    def add(self, content: str, type: str = "semantic", metadata: Dict = None) -> str:
        mem_id = f"vec_{int(time.time()*1000)}"
        
        if self.use_vector and self.embedding_model:
            try:
                embedding = self.embedding_model.encode(content).tolist()
                if hasattr(self, 'conn') and self.conn:
                    # 存入 sqlite-vec
                    import json as js
                    self.conn.execute("INSERT INTO memories VALUES (?, ?, ?, ?, ?)",
                                      (mem_id, content, type, js.dumps(embedding), time.time()))
                    self.conn.execute("INSERT INTO memories_vec VALUES (?, ?)",
                                      (mem_id, str(embedding)))
                    self.conn.commit()
                return mem_id
            except Exception as e:
                print(f"向量添加失败: {e}")
        
        # 回退：JSON
        path = os.path.join(self.data_dir, "vector_fallback.json")
        data = []
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = []
        data.append({"id": mem_id, "content": content, "type": type, "created_at": time.time(), "metadata": metadata or {}})
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data[-500:], f, ensure_ascii=False, indent=2)
        
        return mem_id
    
    def search(self, query: str, limit: int = 5, type_filter: str = None) -> List[Dict]:
        if self.use_vector and self.embedding_model:
            try:
                query_emb = self.embedding_model.encode(query).tolist()
                if hasattr(self, 'conn') and self.conn:
                    # 向量搜索
                    results = self.conn.execute("""
                        SELECT m.id, m.content, m.type, distance
                        FROM memories_vec
                        JOIN memories m ON m.id = memories_vec.id
                        ORDER BY distance
                        LIMIT ?
                    """, (limit,)).fetchall()
                    return [{"id": r[0], "content": r[1], "type": r[2], "score": 1 - r[3], "method": "vector"} for r in results]
            except Exception as e:
                print(f"向量搜索失败: {e}")
        
        # 回退：关键词
        path = os.path.join(self.data_dir, "vector_fallback.json")
        if not os.path.exists(path):
            return []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            query_lower = query.lower()
            scored = []
            for item in data:
                if type_filter and item.get("type") != type_filter:
                    continue
                content_lower = item["content"].lower()
                score = sum(1 for kw in query_lower.split() if kw in content_lower)
                if score > 0:
                    scored.append((score, item))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            return [{"id": item["id"], "content": item["content"], "type": item["type"], "score": score, "method": "keyword"} for score, item in scored[:limit]]
        except Exception:
            return []

# 全局
vector_memory = VectorMemory()
