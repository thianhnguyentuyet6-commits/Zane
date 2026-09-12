# -*- coding: utf-8 -*-
"""
数据过滤器 - v3.0 自主进化核心
- 安全过滤：危险路径不进训练
- 去重：SHA256 + 相似度
- 重要性评分
- SimpleMem压缩
"""
import os
import hashlib
import re
from typing import Dict, List, Any, Tuple

class DataFilter:
    """数据过滤器 v3"""
    
    # 危险路径/文件/进程，平衡模式：文件管理允许但需验证，系统路径禁止
    DANGEROUS_PATHS = [
        "C:\\Windows\\System32",
        "C:\\Windows\\SysWOW64",
        "/etc/shadow",
        "/etc/passwd",
        "/root/",
        "C:\\Windows\\System32\\drivers",
    ]
    
    DANGEROUS_FILES = [
        "password.txt",
        "passwd.txt",
        ".env",
        "id_rsa",
        "id_dsa",
        ".pem",
        "credentials.json",
        "shadow",
    ]
    
    DANGEROUS_PROCESSES = [
        "csrss.exe",
        "winlogon.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "wininit.exe",
        "systemd",
        "init",
    ]
    
    DANGEROUS_COMMANDS = [
        "rm -rf /",
        "rm -rf /*",
        ":(){:|:&};:",
        "mkfs",
        "dd if=",
        "shutdown -h now",
        "format C:",
    ]
    
    def __init__(self):
        self.seen_hashes = set()
    
    def is_safe(self, sample: Dict) -> Tuple[bool, str]:
        """安全检查，平衡模式：危险操作不进训练 - v3.0修复转义"""
        # 合并所有文本字段，处理转义
        task = sample.get("task", "") or sample.get("prompt", "") or ""
        tools = sample.get("tools", []) or []
        conversations = sample.get("conversations", [])
        
        # 构建检查文本，包含原始和转义还原
        raw_texts = [task, str(sample)]
        for convo in conversations:
            if isinstance(convo, dict):
                raw_texts.append(convo.get("value", ""))
        
        # 合并并处理双反斜杠
        content_combined = " ".join(raw_texts)
        # 还原转义：\\ → \，同时保留原始
        content_normalized = content_combined.replace("\\\\", "\\").replace("\\\\", "\\")
        content_lower = content_normalized.lower()
        content_raw_lower = content_combined.lower()
        
        # 检查路径 - 检查task和content
        for dangerous_path in self.DANGEROUS_PATHS:
            dp_lower = dangerous_path.lower()
            if dp_lower in content_lower or dp_lower in content_raw_lower or dp_lower in task.lower() or dangerous_path in task:
                # 平衡：如果是list_files等只读，允许；write/delete禁止
                if any(tool in ["delete_file", "write_file", "kill_process"] for tool in tools):
                    return False, f"危险路径 {dangerous_path} + 写入操作"
                # 只读任务，记录但允许
                if "list_files" in tools or "read_file" in tools:
                    # 但System32等核心路径即使只读也需二次确认，训练时过滤
                    if dangerous_path in ["C:\\Windows\\System32", "/etc/shadow", "/etc/passwd"]:
                        return False, f"核心系统路径 {dangerous_path} 即使只读也不进训练"
                    continue
                # 其他情况，禁止核心路径
                if dangerous_path in ["C:\\Windows\\System32", "/etc/shadow", "/etc/passwd"]:
                    return False, f"危险路径 {dangerous_path}"
        
        # 检查危险文件
        for dangerous_file in self.DANGEROUS_FILES:
            if dangerous_file.lower() in content_lower or dangerous_file.lower() in content_raw_lower:
                # 如果是读取密码文件，禁止
                if "read_file" in tools or "read_file" in content_lower:
                    return False, f"危险文件 {dangerous_file}"
        
        # 检查危险进程
        for dangerous_proc in self.DANGEROUS_PROCESSES:
            if (dangerous_proc.lower() in content_lower or dangerous_proc.lower() in content_raw_lower) and "kill_process" in tools:
                return False, f"危险进程 {dangerous_proc} + kill"
        
        # 检查危险命令
        for dangerous_cmd in self.DANGEROUS_COMMANDS:
            if dangerous_cmd in content_normalized or dangerous_cmd in content_combined:
                return False, f"危险命令 {dangerous_cmd}"
        
        # 检查隐私
        if re.search(r"(password|passwd|pwd)\s*[:=]\s*\S+", content_normalized, re.IGNORECASE) or re.search(r"(password|passwd|pwd)\s*[:=]\s*\S+", content_combined, re.IGNORECASE):
            if "read_file" in content_lower or "write_file" in content_lower:
                return False, "含明文密码"
        
        return True, "安全"
    
    def deduplicate(self, sample: Dict) -> Tuple[bool, str]:
        """去重：SHA256"""
        # 计算hash
        convo_str = str(sample.get("conversations", sample.get("task", "")))
        hash_val = hashlib.sha256(convo_str.encode('utf-8')).hexdigest()[:16]
        
        if hash_val in self.seen_hashes:
            return False, f"重复样本 hash {hash_val}"
        
        self.seen_hashes.add(hash_val)
        return True, f"唯一 hash {hash_val}"
    
    def similarity_check(self, sample: Dict, existing_samples: List[Dict], threshold: float = 0.9) -> Tuple[bool, float]:
        """相似度检查，简单版：关键词重叠"""
        content = str(sample.get("conversations", sample.get("task", "")))[:200]
        if not existing_samples:
            return True, 0.0
        
        max_sim = 0.0
        for existing in existing_samples[-50:]:  # 最近50条
            existing_content = str(existing.get("conversations", existing.get("task", "")))[:200]
            # 简单相似度：共同词数 / 总词数
            words1 = set(content.lower().split())
            words2 = set(existing_content.lower().split())
            if not words1 or not words2:
                continue
            sim = len(words1 & words2) / max(len(words1), len(words2))
            max_sim = max(max_sim, sim)
        
        if max_sim > threshold:
            return False, max_sim
        
        return True, max_sim
    
    def score_importance(self, sample: Dict) -> float:
        """重要性评分 0.5-0.9"""
        score = 0.5
        
        tools = sample.get("tools", [])
        task = sample.get("task", "")
        quality = sample.get("quality_score", 0.5)
        
        # 工具链长度>3 +0.2
        if len(tools) >= 3:
            score += 0.2
        elif len(tools) >= 2:
            score += 0.1
        
        # 验证通过 +0.1
        if sample.get("verification", {}).get("verified") or "验证" in str(sample):
            score += 0.1
        
        # 用户未撤销 +0.1 (无撤销记录)
        if "undo" not in str(sample).lower():
            score += 0.05
        
        # 耗时<60s +0.05
        if sample.get("exec_time_ms", 0) < 60000 or sample.get("duration", 100) < 60:
            score += 0.05
        
        # 质量分
        score += (quality - 0.5) * 0.2
        
        # 任务复杂度
        if any(kw in task for kw in ["整理", "分析", "多步", "复杂"]):
            score += 0.05
        
        return round(min(0.9, max(0.5, score)), 2)
    
    def compress_content(self, content: str, ratio: float = 0.3) -> str:
        """SimpleMem压缩 30%"""
        if len(content) <= 200:
            return content
        
        # 简单压缩：保留关键信息
        # 实际应调用SimpleMem
        try:
            from ..memory.simple_mem import simple_mem
            compressed = simple_mem.semantic_compression(content, "semantic")
            return compressed
        except Exception:
            # 回退：截断+标记
            target_len = int(len(content) * ratio)
            return content[:target_len] + f"... [压缩 {len(content)}→{target_len} {int(ratio*100)}%]"
    
    def check_dpo_quality(self, sample: Dict) -> Tuple[bool, str]:
        """DPO质量检查"""
        reflection = sample.get("reflection", "")
        if len(reflection) < 20:
            return False, f"reflection过短 {len(reflection)}<20"
        
        chosen = sample.get("chosen", "")
        rejected = sample.get("rejected", "")
        if not chosen or not rejected:
            return False, "chosen/rejected为空"
        
        if chosen == rejected:
            return False, "chosen==rejected"
        
        return True, "DPO质量合格"
    
    def filter_batch(self, samples: List[Dict]) -> Dict[str, Any]:
        """批量过滤"""
        safe = []
        filtered = []
        stats = {
            "total": len(samples),
            "safe": 0,
            "dangerous": 0,
            "duplicate": 0,
            "similar": 0,
            "low_quality": 0,
        }
        
        for sample in samples:
            # 安全
            is_safe, reason = self.is_safe(sample)
            if not is_safe:
                filtered.append({"sample": sample, "reason": f"安全过滤: {reason}"})
                stats["dangerous"] += 1
                continue
            
            # 去重
            is_unique, reason = self.deduplicate(sample)
            if not is_unique:
                filtered.append({"sample": sample, "reason": f"去重: {reason}"})
                stats["duplicate"] += 1
                continue
            
            # 相似度
            is_similar_ok, sim = self.similarity_check(sample, safe, threshold=0.9)
            if not is_similar_ok:
                filtered.append({"sample": sample, "reason": f"相似度 {sim:.2f}>0.9"})
                stats["similar"] += 1
                continue
            
            # DPO质量
            if sample.get("type") == "dpo":
                is_quality_ok, reason = self.check_dpo_quality(sample)
                if not is_quality_ok:
                    filtered.append({"sample": sample, "reason": f"DPO质量: {reason}"})
                    stats["low_quality"] += 1
                    continue
            
            # 评分
            importance = self.score_importance(sample)
            sample["importance_score"] = importance
            
            # 压缩
            if len(str(sample)) > 500:
                # 压缩conversations
                if "conversations" in sample:
                    for convo in sample["conversations"]:
                        if "value" in convo and len(convo["value"]) > 200:
                            convo["value"] = self.compress_content(convo["value"])
            
            safe.append(sample)
            stats["safe"] += 1
        
        return {
            "safe": safe,
            "filtered": filtered,
            "stats": stats,
            "safe_rate": round(stats["safe"] / stats["total"] * 100, 1) if stats["total"] else 0
        }

# 全局
data_filter = DataFilter()
