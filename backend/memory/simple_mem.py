# -*- coding: utf-8 -*-
"""
SimpleMem v0914 - 记忆压缩，支持use_llm开关
- 固定长度压缩保证离线可用，有算力用户可选LLM高质量压缩
- 配置：config/simplemem.json {use_llm: false, compression_ratio: 0.3, fallback_fixed_length: true}
- 论文目标30% +26.4% F1 + 30x Token，实际固定长度75%压缩1.4x，可配置LLM压缩
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class MemoryItem:
    id: str
    type: str  # conversational, episodic, semantic, procedural
    content: str
    compressed: str  # 压缩后
    importance: float
    access_count: int
    created_at: float
    last_accessed: float
    tags: List[str] = field(default_factory=list)
    embedding: List[float] = None
    compression_method: str = "fixed_length"  # fixed_length 或 llm


class SimpleMemV0914:
    """SimpleMem v0914 - 支持use_llm开关"""
    
    def __init__(self, db_path: str = None, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.db_path = db_path or str(self.base_dir / "data" / "simple_mem.json")
        self.config_path = self.base_dir / "config" / "simplemem.json"
        self.config = self._load_config()
        
        self.memories: List[MemoryItem] = []
        self.compression_ratio = self.config.get("compression_ratio", 0.3)
        self.load()
    
    def _load_config(self) -> Dict:
        default = {
            "use_llm": False,  # 默认False，固定长度离线可用，有算力用户True用LLM高质量压缩
            "compression_ratio": 0.3,  # 压缩到30%目标
            "fallback_fixed_length": True,  # LLM失败回退固定长度
            "fixed_lengths": {
                "conversational": 100,  # 会话100字意图+实体
                "episodic": 150,  # 情景150字任务+结果+工具
                "semantic": 80,   # 语义80字习惯事实
                "procedural": 120  # 程序120字步骤
            },
            "llm_config": {
                "model": "local",  # local或cloud
                "prompt": "将以下内容压缩到30%，保留关键实体和意图，去除冗余：\n{content}\n压缩后：",
                "max_tokens": 200
            },
            "note": "use_llm=False默认固定长度离线可用，True时用LLM高质量压缩，兼顾两类用户"
        }
        
        # 环境变量覆盖
        env_use_llm = os.getenv("ZANE_SIMPLEMEM_USE_LLM", "").lower()
        if env_use_llm in ("true", "1", "yes"):
            default["use_llm"] = True
        elif env_use_llm in ("false", "0", "no"):
            default["use_llm"] = False
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default.update(loaded)
                    if "fixed_lengths" in loaded:
                        default["fixed_lengths"].update(loaded["fixed_lengths"])
                    if "llm_config" in loaded:
                        default["llm_config"].update(loaded["llm_config"])
            except Exception:
                pass
        
        # 保存
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
        return default
    
    def load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.memories = []
                for item in data:
                    try:
                        # 兼容旧数据
                        if "tags" not in item:
                            item["tags"] = []
                        if "compression_method" not in item:
                            item["compression_method"] = "fixed_length"
                        self.memories.append(MemoryItem(**item))
                    except Exception:
                        continue
            except Exception:
                self.memories = []
    
    def save(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(m) for m in self.memories], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"SimpleMem保存失败: {e}")
    
    def _fixed_length_compression(self, content: str, type: str) -> str:
        """固定长度压缩 - 离线可用兜底"""
        fixed_lengths = self.config.get("fixed_lengths", {})
        target_len = fixed_lengths.get(type, 100)
        
        if len(content) <= target_len:
            return content
        
        # 按类型压缩
        if type == "conversational":
            compressed = content[:target_len] + f"... [压缩 {len(content)}→{target_len} {int(target_len/len(content)*100)}% 固定长度离线]"
        elif type == "episodic":
            compressed = content[:target_len] + f"... [情景压缩 {len(content)}→{target_len} 固定长度]"
        elif type == "semantic":
            compressed = content[:target_len] + f"... [语义压缩 固定长度]"
        elif type == "procedural":
            compressed = content[:target_len] + f"... [程序压缩 固定长度]"
        else:
            target = int(len(content) * self.compression_ratio)
            compressed = content[:target] + f"... [压缩 {len(content)}→{target}]"
        
        return compressed
    
    def _llm_compression(self, content: str, type: str) -> Optional[str]:
        """LLM高质量压缩 - 有算力用户可选"""
        try:
            # 尝试使用本地LLM客户端
            from ..llm_client import llm_client
            
            prompt_template = self.config.get("llm_config", {}).get("prompt", "压缩到30%保留关键：\n{content}\n压缩后：")
            prompt = prompt_template.format(content=content, type=type)
            
            # 检查LLM是否可用
            if hasattr(llm_client, 'is_local_available'):
                if not llm_client.is_local_available():
                    return None
            
            # 调用LLM压缩
            if hasattr(llm_client, 'generate'):
                result = llm_client.generate(prompt, max_tokens=self.config.get("llm_config", {}).get("max_tokens", 200))
                if result and len(result) < len(content):
                    return result.strip() + f" [LLM压缩 {len(content)}→{len(result)}]"
            
            return None
        except Exception as e:
            # LLM失败，回退
            if self.config.get("fallback_fixed_length", True):
                return None
            else:
                raise e
    
    def semantic_compression(self, content: str, type: str) -> str:
        """语义结构化压缩 - 支持use_llm开关"""
        # 如果配置use_llm=True，尝试LLM压缩
        if self.config.get("use_llm", False):
            llm_result = self._llm_compression(content, type)
            if llm_result:
                return llm_result
            # LLM失败且允许回退，则用固定长度
            if not self.config.get("fallback_fixed_length", True):
                return content  # 不压缩
        
        # 默认固定长度压缩 - 离线可用
        return self._fixed_length_compression(content, type)
    
    def online_synthesis(self, new_memory: str, related: List[MemoryItem]) -> str:
        """在线语义合成 - 合并相关记忆"""
        if not related:
            return new_memory
        
        # 合成：新记忆 + 相关记忆 → 更抽象的原则
        synthesis = f"基于{len(related)}条相关记忆合成：\n新：{new_memory[:100]}\n相关："
        for mem in related[:3]:
            synthesis += f"{mem.compressed[:50]}；"
        synthesis += f"\n→ 抽象原则：{new_memory[:80]} 的通用模式"
        
        # 如果use_llm，尝试LLM合成
        if self.config.get("use_llm", False):
            try:
                from ..llm_client import llm_client
                if hasattr(llm_client, 'generate'):
                    prompt = f"基于以下记忆提炼通用原则：\n新记忆：{new_memory}\n相关：{'; '.join([m.compressed for m in related[:3]])}\n原则："
                    llm_synthesis = llm_client.generate(prompt, max_tokens=150)
                    if llm_synthesis:
                        return llm_synthesis.strip()
            except Exception:
                pass
        
        return synthesis
    
    def intent_aware_retrieval(self, query: str, intent: Dict, limit: int = 5) -> List[MemoryItem]:
        """意图感知检索 - 按重要性排序：最近访问时间+是否被上次任务引用"""
        category = intent.get("category", "general")
        action = intent.get("action", "general")
        
        # 根据意图决定检索权重
        type_weights = {
            "conversational": 0.2,
            "episodic": 0.3,
            "semantic": 0.3,
            "procedural": 0.2
        }
        
        if category == "file":
            type_weights["procedural"] = 0.4
            type_weights["episodic"] = 0.3
        elif category == "system":
            type_weights["semantic"] = 0.4
        elif action == "organize":
            type_weights["procedural"] = 0.5
        
        # 检索 - 按重要性排序：最近访问+是否被上次任务引用启发式
        query_lower = query.lower()
        scored = []
        
        # 获取上次任务引用（如果有）
        last_task_refs = intent.get("last_task_tools", []) + intent.get("last_task_keywords", [])
        
        for mem in self.memories:
            score = 0
            
            # 关键词匹配
            if query_lower in mem.content.lower() or query_lower in mem.compressed.lower():
                score += 1
            
            # 重要性
            score += mem.importance * 0.5
            
            # 类型权重
            score *= type_weights.get(mem.type, 0.2)
            
            # 时间衰减 + 最近访问加权
            days = (time.time() - mem.created_at) / 86400
            decay = max(0.1, 1 - days / 30)
            score *= decay
            
            # 最近访问时间加权 - 越近越高
            hours_since_access = (time.time() - mem.last_accessed) / 3600
            recency_boost = max(0.5, 1.5 - hours_since_access / 24)  # 24小时内有加成
            score *= recency_boost
            
            # 是否被上次任务引用 - 启发式重要性
            if last_task_refs:
                for ref in last_task_refs:
                    if ref.lower() in mem.content.lower() or ref.lower() in mem.compressed.lower():
                        score *= 1.3  # 被上次任务引用，加权
                        break
            
            # 访问频率
            freq_boost = min(2.0, 1 + mem.access_count * 0.1)
            score *= freq_boost
            
            if score > 0:
                scored.append((score, mem))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        result = [mem for _, mem in scored[:limit]]
        
        # 更新访问
        for mem in result:
            mem.access_count += 1
            mem.last_accessed = time.time()
        self.save()
        
        return result
    
    def add_memory(self, content: str, type: str = "semantic", importance: float = 0.5, tags: List[str] = None) -> str:
        """添加记忆，自动压缩"""
        related = [m for m in self.memories if m.type == type and any(tag in m.content for tag in (tags or []))]
        
        compressed = self.semantic_compression(content, type)
        method = "llm" if self.config.get("use_llm") and "LLM压缩" in compressed else "fixed_length"
        
        if related:
            synthesized = self.online_synthesis(content, related)
            if "抽象原则" in synthesized or "原则" in synthesized:
                compressed = synthesized
        
        mem_id = f"sm_{type}_{int(time.time()*1000000)}"
        now = time.time()
        
        item = MemoryItem(
            id=mem_id,
            type=type,
            content=content,
            compressed=compressed,
            importance=importance,
            access_count=0,
            created_at=now,
            last_accessed=now,
            tags=tags or [],
            compression_method=method
        )
        
        self.memories.append(item)
        self.save()
        
        return mem_id
    
    def get_stats(self) -> Dict[str, Any]:
        """统计，展示压缩效果"""
        if not self.memories:
            return {"total": 0, "compression": "无", "config": self.config}
        
        by_type = {}
        by_method = {}
        total_original = 0
        total_compressed = 0
        
        for mem in self.memories:
            t = mem.type
            m = mem.compression_method
            by_type[t] = by_type.get(t, 0) + 1
            by_method[m] = by_method.get(m, 0) + 1
            total_original += len(mem.content)
            total_compressed += len(mem.compressed)
        
        ratio = total_compressed / total_original if total_original else 1
        token_reduction = 1 / ratio if ratio else 1
        
        return {
            "total": len(self.memories),
            "by_type": by_type,
            "by_method": by_method,
            "total_original_chars": total_original,
            "total_compressed_chars": total_compressed,
            "compression_ratio": round(ratio, 3),
            "token_reduction": round(token_reduction, 1),
            "config": self.config,
            "config_path": str(self.config_path),
            "note": f"SimpleMem压缩 {ratio*100:.1f}% → Token减少 {token_reduction:.1f}x，use_llm={self.config.get('use_llm')}，固定长度离线可用，LLM高质量可选",
            "improvement": "+26.4% F1, 30x Token减少 (论文目标，实际固定长度75%压缩1.4x，LLM可接近目标)"
        }


# 全局 v0914
simple_mem = SimpleMemV0914()
# 兼容
simple_mem_v0914 = simple_mem
