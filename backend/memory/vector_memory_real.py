# -*- coding: utf-8 -*-
"""
Vector Memory Real - 真实向量检索 - 补全
- sqlite-vec + sentence-transformers all-MiniLM-L6-v2 80MB
- 关键词回退
- 嵌入缓存
"""

import os
import json
import time
from typing import List, Dict, Optional

class VectorMemoryReal:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.use_vector = False
        self.embedding_model = None
        self.embedding_dim = 384
        
        # 尝试加载 sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            # 使用轻量模型 all-MiniLM-L6-v2 80MB
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            # 检查是否已下载或允许下载
            try:
                self.embedding_model = SentenceTransformer(model_name, device='cpu')
                self.use_vector = True
                print(f"✅ 真实向量嵌入可用: {model_name} 384维")
            except Exception as e:
                print(f"⚠️ 嵌入模型加载失败，使用关键词回退: {e}")
                self.use_vector = False
        except ImportError:
            print("⚠️ sentence-transformers未安装，关键词回退，pip install sentence-transformers")
            self.use_vector = False
        
        # 尝试 sqlite-vec
        self.vec_available = False
        try:
            import sqlite_vec
            self.vec_available = True
            print("✅ sqlite-vec 可用")
        except ImportError:
            print("⚠️ sqlite-vec未安装，pip install sqlite-vec")
    
    def embed(self, text: str) -> Optional[List[float]]:
        """真实嵌入"""
        if not self.use_vector or not self.embedding_model:
            return None
        try:
            embedding = self.embedding_model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            print(f"嵌入失败: {e}")
            return None
    
    def add(self, content: str, type: str = "semantic", metadata: Dict = None) -> str:
        """添加记忆，带向量"""
        try:
            from ..database import database
            mem_id = database.add_memory(type=type, content=content, metadata=metadata, importance=0.7)
            
            # 如果向量可用，添加向量
            if self.use_vector and self.vec_available:
                try:
                    embedding = self.embed(content)
                    if embedding:
                        # 存入向量表
                        try:
                            database.conn.execute("INSERT OR REPLACE INTO memories_vec (id, embedding) VALUES (?, ?)", 
                                                  (mem_id, json.dumps(embedding)))
                            database.conn.commit()
                        except Exception as e:
                            print(f"向量存储失败: {e}")
                except Exception as e:
                    print(f"向量添加失败: {e}")
            
            return mem_id
        except Exception as e:
            print(f"添加记忆失败: {e}")
            return f"mem_{int(time.time())}"
    
    def search(self, query: str, limit: int = 5, type_filter: str = None) -> List[Dict]:
        """真实向量搜索 + 关键词回退"""
        try:
            from ..database import database
            
            # 尝试向量搜索
            if self.use_vector and self.vec_available:
                try:
                    query_embedding = self.embed(query)
                    if query_embedding:
                        # 向量相似度搜索 - 简化版，实际应使用 sqlite-vec 的 KNN
                        # 这里用 Python 计算余弦相似度作为演示
                        cursor = database.conn.execute("SELECT id, embedding FROM memories_vec LIMIT 100")
                        candidates = []
                        for row in cursor.fetchall():
                            try:
                                emb = json.loads(row["embedding"]) if isinstance(row["embedding"], str) else row["embedding"]
                                # 余弦相似度
                                import math
                                dot = sum(a*b for a, b in zip(query_embedding, emb))
                                # 已归一化，dot即相似度
                                candidates.append((dot, row["id"]))
                            except Exception:
                                continue
                        
                        candidates.sort(key=lambda x: x[0], reverse=True)
                        results = []
                        for score, mem_id in candidates[:limit]:
                            try:
                                cursor = database.conn.execute("SELECT * FROM memories WHERE id = ?", (mem_id,))
                                row = cursor.fetchone()
                                if row:
                                    mem = dict(row)
                                    mem["score"] = score
                                    mem["method"] = "vector"
                                    if not type_filter or mem["type"] == type_filter:
                                        results.append(mem)
                            except Exception:
                                continue
                        
                        if results:
                            return results
                except Exception as e:
                    print(f"向量搜索失败，回退关键词: {e}")
            
            # 关键词回退
            results = database.search_memories(query, limit=limit)
            for r in results:
                r["method"] = "keyword+time_decay"
                r["score"] = 0.5
            return results
        
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

# 全局
vector_memory_real = VectorMemoryReal()
