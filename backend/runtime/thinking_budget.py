# -*- coding: utf-8 -*-
"""
Thinking Budget - Qwen3 2026最新技术
- 思考预算机制，动态分配推理资源，平衡延迟与性能
- /think 和 /no_think 标志，控制推理模式
- 强到弱蒸馏，轻量模型继承推理能力
"""
import time
from typing import Dict, Any, Optional
from enum import Enum

class ThinkingMode(Enum):
    THINK = "think"  # 深度思考，32K输出，复杂任务
    NO_THINK = "no_think"  # 快速响应，通用任务
    AUTO = "auto"  # 自动根据任务复杂度选择

class ThinkingBudget:
    """思考预算 - Qwen3 2026最新"""
    
    # 任务复杂度评估关键词
    COMPLEX_KEYWORDS = [
        "分析", "推理", "规划", "设计", "优化", "调试", "复杂", "多步",
        "数学", "代码", "算法", "证明", "比较", "评估", "决策"
    ]
    SIMPLE_KEYWORDS = [
        "列出", "查看", "显示", "是什么", "简单", "快速", "帮我打开"
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
    
    def __init__(self):
        self.default_budget = 8192
        self.max_budget = 32768
        self.min_budget = 512
    
    def estimate_complexity(self, text: str) -> Dict[str, Any]:
        """评估任务复杂度，决定思考预算"""
        text_lower = text.lower()
        complex_score = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in text or kw.lower() in text_lower)
        simple_score = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in text or kw.lower() in text_lower)
        
        # 长度也影响复杂度
        length_score = min(2, len(text) / 100)
        
        total_complex = complex_score + length_score
        total_simple = simple_score
        
        if total_complex >= 2:
            mode = ThinkingMode.THINK
            budget = min(self.max_budget, 8192 + total_complex * 4096)
            confidence = min(0.95, 0.5 + total_complex * 0.15)
        elif total_simple >= 1 and total_complex == 0:
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
            "confidence": confidence,
            "reason": f"复杂关键词{complex_score}个，简单{simple_score}个，长度{len(text)}"
        }
    
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
        
        # 历史处理 - 思考内容不存入历史，Qwen3最佳实践
        cleaned_history = []
        if history:
            for msg in history[-10:]:  # 最近10条
                if isinstance(msg, dict):
                    # 移除思考内容，仅保留最终输出
                    content = msg.get("content", "")
                    # 如果有思考标签，移除
                    if "<think>" in content:
                        # 提取 </think> 后的内容
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
            "note": "Qwen3 2026思考预算机制，/think深度推理32K，/no_think快速8K，历史不含思考内容"
        }

# 全局
thinking_budget = ThinkingBudget()
