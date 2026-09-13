# -*- coding: utf-8 -*-
"""
Thinking Budget v0914 - 两级评估：关键词快速 + LLM确认模糊区间
- 第一级：关键词快速判断，速度快
- 第二级：落在模糊区间时调用LLM二次确认，兼顾速度和准确性
- Qwen3 /think 32K /no_think 8K
"""
import time
import os
from typing import Dict, Any, Optional
from enum import Enum


class ThinkingMode(Enum):
    THINK = "think"  # 深度思考，32K输出，复杂任务
    NO_THINK = "no_think"  # 快速响应，通用任务
    AUTO = "auto"  # 自动根据任务复杂度选择


class ThinkingBudgetV0914:
    """思考预算 v0914 - 两级评估"""
    
    # 任务复杂度评估关键词
    COMPLEX_KEYWORDS = [
        "分析", "推理", "规划", "设计", "优化", "调试", "复杂", "多步",
        "数学", "代码", "算法", "证明", "比较", "评估", "决策", "架构",
        "重构", "性能", "安全", "并发", "分布式", "机器学习", "深度学习"
    ]
    SIMPLE_KEYWORDS = [
        "列出", "查看", "显示", "是什么", "简单", "快速", "帮我打开",
        "打开", "关闭", "删除", "复制", "移动", "重命名"
    ]
    
    # 模糊区间关键词 - 既不明显简单也不明显复杂
    FUZZY_KEYWORDS = [
        "整理", "清理", "搜索", "查找", "管理", "处理", "执行", "运行"
    ]
    
    # 采样参数 - Qwen3最佳实践 2026
    SAMPLING_PARAMS = {
        ThinkingMode.THINK: {
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "min_p": 0.0,
            "presence_penalty": 0.0,
            "max_tokens": 32768,
            "description": "思考模式 - 复杂推理，温度0.6，top_p 0.95，32K输出"
        },
        ThinkingMode.NO_THINK: {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 20,
            "min_p": 0.0,
            "presence_penalty": 1.5,
            "max_tokens": 8192,
            "description": "非思考模式 - 快速响应，温度0.7，top_p 0.8，8K输出"
        },
        ThinkingMode.AUTO: {
            "temperature": 0.65,
            "top_p": 0.9,
            "top_k": 20,
            "max_tokens": 16384,
            "description": "自动模式 - 根据复杂度动态"
        }
    }
    
    def __init__(self, base_dir: str = None):
        from pathlib import Path
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.config_path = self.base_dir / "config" / "thinking_config.json"
        self.config = self._load_config()
        
        self.default_budget = 8192
        self.max_budget = 32768
        self.min_budget = 512
    
    def _load_config(self) -> Dict:
        default = {
            "use_llm_for_fuzzy": False,  # 是否在模糊区间调用LLM确认，默认False速度快
            "fuzzy_threshold_low": 0.3,  # 模糊区间下界
            "fuzzy_threshold_high": 0.7,  # 模糊区间上界
            "enable_two_level": True,  # 启用两级评估
            "note": "两级评估：先关键词快速判断，模糊区间再LLM确认，兼顾速度准确性"
        }
        
        env_use_llm = os.getenv("ZANE_THINKING_USE_LLM", "").lower()
        if env_use_llm in ("true", "1", "yes"):
            default["use_llm_for_fuzzy"] = True
        elif env_use_llm in ("false", "0", "no"):
            default["use_llm_for_fuzzy"] = False
        
        if self.config_path.exists():
            try:
                import json
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default.update(loaded)
            except Exception:
                pass
        
        try:
            import json
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
        return default
    
    def estimate_complexity_fast(self, text: str) -> Dict[str, Any]:
        """第一级：关键词快速判断，速度快"""
        text_lower = text.lower()
        complex_score = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in text or kw.lower() in text_lower)
        simple_score = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in text or kw.lower() in text_lower)
        fuzzy_score = sum(1 for kw in self.FUZZY_KEYWORDS if kw in text or kw.lower() in text_lower)
        
        # 长度也影响复杂度
        length_score = min(2, len(text) / 100)
        
        total_complex = complex_score + length_score * 0.5
        total_simple = simple_score
        
        # 计算复杂度分数 0-1
        if total_complex + total_simple == 0:
            complexity_score = 0.5  # 中性，模糊
        else:
            complexity_score = total_complex / (total_complex + total_simple + 1)
        
        # 判断是否在模糊区间
        is_fuzzy = self.config["fuzzy_threshold_low"] <= complexity_score <= self.config["fuzzy_threshold_high"]
        
        if total_complex >= 2.5:
            mode = ThinkingMode.THINK
            budget = min(self.max_budget, 8192 + total_complex * 4096)
            confidence = min(0.95, 0.5 + total_complex * 0.15)
        elif total_simple >= 1.5 and total_complex <= 0.5:
            mode = ThinkingMode.NO_THINK
            budget = max(self.min_budget, 2048)
            confidence = 0.8
        else:
            mode = ThinkingMode.AUTO
            budget = 8192
            confidence = 0.6
        
        return {
            "mode": mode.value,
            "budget": int(budget),
            "complex_score": complex_score,
            "simple_score": simple_score,
            "fuzzy_score": fuzzy_score,
            "complexity_score": round(complexity_score, 3),
            "is_fuzzy": is_fuzzy,
            "confidence": confidence,
            "level": "fast",
            "reason": f"快速：复杂{complex_score}个，简单{simple_score}个，模糊{fuzzy_score}个，长度{len(text)}，分数{complexity_score:.2f} {'模糊区间' if is_fuzzy else '明确'}"
        }
    
    def estimate_complexity_llm(self, text: str, fast_result: Dict) -> Dict[str, Any]:
        """第二级：LLM确认模糊区间，准确性高"""
        try:
            from ..llm_client import llm_client
            
            if hasattr(llm_client, 'is_local_available'):
                if not llm_client.is_local_available():
                    return fast_result
            
            prompt = f"""判断以下任务的复杂度，返回think(复杂需深度推理)、no_think(简单快速)或auto(中等)：
任务：{text}
快速评估：{fast_result['reason']}
只返回一个词：think、no_think或auto
"""
            
            if hasattr(llm_client, 'generate'):
                llm_result = llm_client.generate(prompt, max_tokens=20)
                if llm_result:
                    llm_result = llm_result.strip().lower()
                    if "think" in llm_result and "no_think" not in llm_result:
                        mode = ThinkingMode.THINK
                        budget = 16384
                        confidence = 0.85
                    elif "no_think" in llm_result:
                        mode = ThinkingMode.NO_THINK
                        budget = 2048
                        confidence = 0.85
                    else:
                        mode = ThinkingMode.AUTO
                        budget = 8192
                        confidence = 0.7
                    
                    return {
                        "mode": mode.value,
                        "budget": budget,
                        "complex_score": fast_result["complex_score"],
                        "simple_score": fast_result["simple_score"],
                        "complexity_score": fast_result["complexity_score"],
                        "is_fuzzy": False,
                        "confidence": confidence,
                        "level": "llm",
                        "llm_raw": llm_result,
                        "reason": f"LLM确认：{llm_result} (快速评估{fast_result['mode']} 模糊，需LLM二次确认)"
                    }
            
            return fast_result
        except Exception as e:
            # LLM失败，回退快速结果
            return {
                **fast_result,
                "llm_error": str(e),
                "reason": fast_result["reason"] + f" (LLM确认失败: {e}，回退快速)"
            }
    
    def estimate_complexity(self, text: str) -> Dict[str, Any]:
        """评估任务复杂度 - 两级：先快速，模糊区间再LLM"""
        fast_result = self.estimate_complexity_fast(text)
        
        # 如果启用两级评估且在模糊区间且配置允许LLM，则调用LLM确认
        if (self.config.get("enable_two_level", True) 
            and fast_result["is_fuzzy"] 
            and self.config.get("use_llm_for_fuzzy", False)):
            return self.estimate_complexity_llm(text, fast_result)
        
        return fast_result
    
    def get_sampling_params(self, mode: str = "auto", custom_budget: int = None) -> Dict[str, Any]:
        """获取采样参数"""
        try:
            thinking_mode = ThinkingMode(mode)
        except ValueError:
            thinking_mode = ThinkingMode.AUTO
        
        params = self.SAMPLING_PARAMS[thinking_mode].copy()
        if custom_budget:
            params["max_tokens"] = max(self.min_budget, min(self.max_budget, custom_budget))
        
        return params
    
    def build_chat_template(self, message: str, mode: str = "auto", history: list = None) -> Dict[str, Any]:
        """构建聊天模板，支持 /think 和 /no_think 标志 - Qwen3 2026"""
        complexity = self.estimate_complexity(message)
        
        # 根据模式选择标志
        if mode == "think" or complexity["mode"] == "think":
            flag = "/think"
            final_mode = "think"
        elif mode == "no_think" or complexity["mode"] == "no_think":
            flag = "/no_think"
            final_mode = "no_think"
        else:
            flag = ""
            final_mode = "auto"
        
        # 构建消息
        if flag:
            formatted_message = f"{flag} {message}"
        else:
            formatted_message = message
        
        # 历史处理 - 思考内容不存入历史
        cleaned_history = []
        if history:
            for msg in history[-10:]:
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if "<think>" in content:
                        parts = content.split("</think>")
                        if len(parts) > 1:
                            content = parts[-1].strip()
                    cleaned_history.append({"role": msg.get("role", "user"), "content": content})
        
        params = self.get_sampling_params(final_mode, complexity["budget"])
        
        return {
            "message": formatted_message,
            "raw_message": message,
            "mode": final_mode,
            "flag": flag,
            "complexity": complexity,
            "sampling_params": params,
            "history": cleaned_history,
            "thinking_budget": complexity["budget"],
            "two_level": self.config.get("enable_two_level", True),
            "note": "Qwen3 2026思考预算，两级评估：关键词快速+LLM确认模糊区间，/think 32K /no_think 8K"
        }


# 全局 v0914
thinking_budget = ThinkingBudgetV0914()
# 兼容
thinking_budget_v0914 = thinking_budget
