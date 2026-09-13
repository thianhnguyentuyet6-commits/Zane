# -*- coding: utf-8 -*-
"""
记忆 v3 - 4层统一+SimpleMem压缩+遗忘+DREAMS.md
整合 memory_layer + simple_mem + dreaming + dream_loop
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

class MemoryV3:
    """记忆 v3 统一"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.data_dir = self.base_dir / "data" / "memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 4层
        self.layers = {
            "conversational": [],  # 会话
            "episodic": [],  # 情景
            "semantic": [],  # 语义
            "procedural": []  # 程序
        }
        
        # 导入
        try:
            from .simple_mem import simple_mem
            self.simple_mem = simple_mem
        except Exception:
            try:
                from ..runtime.simple_mem import simple_mem
                self.simple_mem = simple_mem
            except Exception:
                self.simple_mem = None
        
        try:
            from .forgetting import forgetting_mechanism
            self.forgetting = forgetting_mechanism
        except Exception:
            self.forgetting = None
        
        self.load()
    
    def load(self):
        # 尝试加载现有
        for layer in self.layers:
            path = self.data_dir / f"{layer}.json"
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.layers[layer] = json.load(f)
                except Exception:
                    self.layers[layer] = []
        
        # 从simple_mem加载
        if self.simple_mem and hasattr(self.simple_mem, 'memories'):
            for mem in self.simple_mem.memories:
                layer = mem.type if mem.type in self.layers else "semantic"
                if not any(m.get("id") == mem.id for m in self.layers[layer]):
                    self.layers[layer].append({
                        "id": mem.id,
                        "content": mem.content,
                        "compressed": mem.compressed,
                        "importance": mem.importance,
                        "access_count": mem.access_count,
                        "created_at": mem.created_at,
                        "last_accessed": mem.last_accessed,
                        "tags": mem.tags
                    })
    
    def save(self):
        for layer, memories in self.layers.items():
            path = self.data_dir / f"{layer}.json"
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(memories, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存{layer}失败: {e}")
    
    def add_memory(self, content: str, type: str = "semantic", importance: float = 0.5, tags: List[str] = None) -> str:
        """添加记忆，自动压缩"""
        if type not in self.layers:
            type = "semantic"
        
        # SimpleMem压缩
        compressed = content
        if self.simple_mem:
            try:
                compressed = self.simple_mem.semantic_compression(content, type)
            except Exception:
                pass
        
        mem_id = f"mem_v3_{type}_{int(time.time()*1000000)}"
        now = time.time()
        
        memory = {
            "id": mem_id,
            "content": content,
            "compressed": compressed,
            "importance": importance,
            "access_count": 0,
            "created_at": now,
            "last_accessed": now,
            "tags": tags or [],
            "type": type
        }
        
        self.layers[type].append(memory)
        self.save()
        
        # 同步到SimpleMem
        if self.simple_mem:
            try:
                self.simple_mem.add_memory(content, type=type, importance=importance, tags=tags)
            except Exception:
                pass
        
        return mem_id
    
    def search(self, query: str, type: str = None, limit: int = 5) -> List[Dict]:
        """搜索，意图感知"""
        # 尝试SimpleMem意图感知
        if self.simple_mem and hasattr(self.simple_mem, 'intent_aware_retrieval'):
            try:
                intent = {"category": type or "general", "action": "search"}
                results = self.simple_mem.intent_aware_retrieval(query, intent, limit=limit)
                return [{"id": r.id, "content": r.content, "compressed": r.compressed, "importance": r.importance, "type": r.type} for r in results]
            except Exception:
                pass
        
        # 回退关键词
        query_lower = query.lower()
        all_mems = []
        layers_to_search = [type] if type and type in self.layers else list(self.layers.keys())
        
        for layer in layers_to_search:
            for mem in self.layers[layer]:
                if query_lower in mem.get("content", "").lower() or query_lower in mem.get("compressed", "").lower():
                    all_mems.append(mem)
        
        # 按重要性+时间排序
        all_mems.sort(key=lambda x: (x.get("importance", 0), x.get("last_accessed", 0)), reverse=True)
        
        # 更新访问
        for mem in all_mems[:limit]:
            mem["access_count"] = mem.get("access_count", 0) + 1
            mem["last_accessed"] = time.time()
        self.save()
        
        return all_mems[:limit]
    
    def forget_low_value(self) -> Dict[str, Any]:
        """遗忘低价值"""
        if not self.forgetting:
            return {"total": 0, "forgotten": 0, "error": "遗忘机制未加载"}
        
        all_mems = []
        for layer in self.layers:
            all_mems.extend(self.layers[layer])
        
        result = self.forgetting.forget_batch(all_mems)
        
        # 删除遗忘的
        forgotten_ids = set(result["forgotten_ids"])
        for layer in self.layers:
            self.layers[layer] = [m for m in self.layers[layer] if m.get("id") not in forgotten_ids]
        
        self.save()
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """统计"""
        total = sum(len(mems) for mems in self.layers.values())
        by_type = {k: len(v) for k, v in self.layers.items()}
        
        total_original = 0
        total_compressed = 0
        for layer in self.layers.values():
            for mem in layer:
                total_original += len(mem.get("content", ""))
                total_compressed += len(mem.get("compressed", mem.get("content", "")))
        
        ratio = total_compressed / total_original if total_original else 1
        
        return {
            "total": total,
            "by_type": by_type,
            "total_original_chars": total_original,
            "total_compressed_chars": total_compressed,
            "compression_ratio": round(ratio, 3),
            "token_reduction": round(1/ratio, 1) if ratio else 1,
            "layers": list(self.layers.keys()),
            "note": "4层统一+SimpleMem压缩+遗忘"
        }
    
    def generate_dreams_md(self) -> str:
        """生成DREAMS.md"""
        dreams_path = self.base_dir / "memory" / "DREAMS.md"
        dreams_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 统计
        stats = self.get_stats()
        
        content = f"""
# DREAMS.md - {time.strftime('%Y-%m-%d')}

> 梦境整理，人类可读叙事

今天帮你整理了记忆：

- 总记忆数：{stats['total']}
- 按类型：{stats['by_type']}
- 压缩比：{stats['compression_ratio']*100:.1f}% → Token减少 {stats['token_reduction']}x

## 高价值记忆

"""
        # 高价值
        all_mems = []
        for layer in self.layers.values():
            all_mems.extend(layer)
        all_mems.sort(key=lambda x: x.get("importance", 0), reverse=True)
        
        for mem in all_mems[:5]:
            content += f"- [{mem.get('type','')}] {mem.get('content','')[:100]} (重要性 {mem.get('importance',0)})\n"
        
        content += f"\n> 阈值访问<3 + 重要性<0.3 + 30天自动遗忘\n"
        
        try:
            with open(dreams_path, 'a', encoding='utf-8') as f:
                f.write(content)
            return str(dreams_path)
        except Exception as e:
            return f"生成失败: {e}"

# 全局
memory_v3 = MemoryV3()
