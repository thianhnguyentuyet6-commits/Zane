# -*- coding: utf-8 -*-
"""
Bounded Self-Correction - 2026最新 不确定性校准自校正循环 UCSL
- 每决策记录原始置信度+校准置信度+不确定性来源+结果标签
- 验证器引导修正轮，固定预算，根据风险和延迟决定预算大小
- 2-3轮有界自校正，任务特定预算，置信度稳定或预算耗尽停止
- 参考：Uncertainty-Calibrated Self-Correction Loops 2026-03-02
"""
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class UncertaintySource(Enum):
    RETRIEVAL_CONFLICT = "检索冲突"
    REASONING_GAP = "推理差距"
    POLICY_AMBIGUITY = "策略歧义"
    TOOL_FAILURE = "工具失败"
    AMBIGUOUS_INTENT = "意图歧义"

@dataclass
class ConfidenceLog:
    timestamp: float
    decision: str
    raw_confidence: float  # 原始置信度
    calibrated_confidence: float  # 校准后
    uncertainty_source: str
    outcome_label: str = ""  # 事后标签：成功/失败
    feedback: str = ""

@dataclass
class CorrectionRound:
    round: int
    weakness: str  # 检测到的弱点
    constraint: str  # 针对性约束
    regenerated: str
    confidence_before: float
    confidence_after: float
    passed: bool
    tokens_used: int = 0

class BoundedCorrection:
    """有界自校正 - UCSL 2026最新"""
    
    def __init__(self, max_rounds: int = 3):
        self.max_rounds = max_rounds
        self.confidence_logs: List[ConfidenceLog] = []
        self.calibration_data: List[Dict] = []
        
        # 任务特定预算 - 根据风险和延迟
        self.task_budgets = {
            "read_only": {"rounds": 2, "tokens": 2000, "risk": "low", "description": "只读任务，低风险，2轮"},
            "write": {"rounds": 2, "tokens": 4000, "risk": "medium", "description": "写入任务，中风险，2轮"},
            "dangerous": {"rounds": 3, "tokens": 8000, "risk": "high", "description": "危险任务，高风险，3轮"},
            "complex": {"rounds": 3, "tokens": 10000, "risk": "high", "description": "复杂任务，高风险，3轮"}
        }
    
    def log_confidence(self, decision: str, raw_conf: float, calibrated_conf: float, source: str, outcome: str = "", feedback: str = ""):
        """每有意义决策记录置信度 - Layer A: 不确定性可观测性"""
        log = ConfidenceLog(
            timestamp=time.time(),
            decision=decision,
            raw_confidence=raw_conf,
            calibrated_confidence=calibrated_conf,
            uncertainty_source=source,
            outcome_label=outcome,
            feedback=feedback
        )
        self.confidence_logs.append(log)
        
        # 用于每周重校准
        if outcome:
            self.calibration_data.append({
                "raw": raw_conf,
                "calibrated": calibrated_conf,
                "source": source,
                "outcome": outcome,
                "timestamp": log.timestamp
            })
    
    def calibrate_confidence(self, raw_conf: float, source: str) -> float:
        """校准置信度 - 基于历史数据"""
        # 简单校准：根据来源调整
        # 实际应使用历史校准数据训练
        adjustments = {
            UncertaintySource.RETRIEVAL_CONFLICT.value: -0.15,
            UncertaintySource.REASONING_GAP.value: -0.10,
            UncertaintySource.POLICY_AMBIGUITY.value: -0.20,
            UncertaintySource.TOOL_FAILURE.value: -0.25,
            UncertaintySource.AMBIGUOUS_INTENT.value: -0.30
        }
        
        adjustment = adjustments.get(source, 0)
        calibrated = max(0.1, min(0.95, raw_conf + adjustment))
        
        # 如果历史数据显示该来源经常失败，进一步降低
        recent_failures = [d for d in self.calibration_data[-20:] if d["source"] == source and d["outcome"] == "失败"]
        if len(recent_failures) >= 3:
            calibrated = max(0.1, calibrated - 0.10)
        
        return calibrated
    
    def detect_weakness(self, draft: str, original_query: str) -> Dict[str, Any]:
        """检测答案弱点 - 验证器引导"""
        weaknesses = []
        
        # 1. 检查是否完全解决请求
        if len(draft) < 20:
            weaknesses.append({"type": "过短", "severity": "high", "description": "回答过短，可能未完全解决"})
        
        # 2. 检查是否有错误
        if "error" in draft.lower() or "失败" in draft:
            weaknesses.append({"type": "含错误", "severity": "high", "description": "回答含错误信息"})
        
        # 3. 检查是否有未验证信息
        if "可能" in draft or "也许" in draft or "不确定" in draft:
            weaknesses.append({"type": "不确定", "severity": "medium", "description": "含不确定表述，需验证"})
        
        # 4. 检查工具调用
        if "未找到" in draft or "不存在" in draft:
            weaknesses.append({"type": "未找到", "severity": "medium", "description": "资源未找到，需替代方案"})
        
        return {
            "has_weakness": len(weaknesses) > 0,
            "weaknesses": weaknesses,
            "count": len(weaknesses),
            "highest_severity": max([w["severity"] for w in weaknesses], default="low")
        }
    
    def generate_constraint(self, weakness: Dict, attempt: int) -> str:
        """生成针对性约束 - 用于再生"""
        w_type = weakness.get("type", "")
        
        constraints = {
            "过短": f"第{attempt+1}次尝试：需详细回答，至少100字，包含具体步骤和验证",
            "含错误": f"第{attempt+1}次尝试：之前失败，错误：{weakness.get('description')}，请修正错误，使用替代方案",
            "不确定": f"第{attempt+1}次尝试：需确定性回答，避免'可能'等模糊词，提供验证方法",
            "未找到": f"第{attempt+1}次尝试：资源未找到，尝试在沙盒搜索或列出父目录"
        }
        
        return constraints.get(w_type, f"第{attempt+1}次尝试：修正弱点 {weakness.get('description')}，提供更准确回答")
    
    async def run_bounded_correction(self, initial_draft: str, original_query: str, task_type: str = "read_only", llm_generate_func=None) -> Dict[str, Any]:
        """运行有界自校正循环 - Layer B"""
        budget = self.task_budgets.get(task_type, self.task_budgets["read_only"])
        max_rounds = budget["rounds"]
        token_budget = budget["tokens"]
        
        current_draft = initial_draft
        rounds: List[CorrectionRound] = []
        total_tokens = 0
        
        # 初始置信度
        raw_conf = 0.7
        source = UncertaintySource.REASONING_GAP.value
        calibrated_conf = self.calibrate_confidence(raw_conf, source)
        
        self.log_confidence(
            decision=f"初始回答: {original_query[:50]}",
            raw_conf=raw_conf,
            calibrated_conf=calibrated_conf,
            source=source
        )
        
        for round_num in range(max_rounds):
            # 1. 检测弱点
            weakness_check = self.detect_weakness(current_draft, original_query)
            
            if not weakness_check["has_weakness"]:
                # 无弱点，通过
                self.log_confidence(
                    decision=f"第{round_num+1}轮验证通过",
                    raw_conf=0.85,
                    calibrated_conf=self.calibrate_confidence(0.85, source),
                    source=source,
                    outcome="成功",
                    feedback="无弱点"
                )
                return {
                    "final_draft": current_draft,
                    "passed": True,
                    "rounds": [asdict(r) for r in rounds],
                    "total_rounds": len(rounds),
                    "total_tokens": total_tokens,
                    "confidence": calibrated_conf,
                    "budget": budget,
                    "reason": "无弱点，验证通过"
                }
            
            # 有弱点，需修正
            worst_weakness = weakness_check["weaknesses"][0] if weakness_check["weaknesses"] else {"type": "未知", "description": "未知弱点"}
            constraint = self.generate_constraint(worst_weakness, round_num)
            
            confidence_before = calibrated_conf
            
            # 2. 带约束再生
            if llm_generate_func:
                try:
                    # 调用LLM再生
                    regeneration_prompt = f"""
原请求：{original_query}
之前回答：{current_draft}
检测到弱点：{worst_weakness}
约束：{constraint}

请修正弱点，重新回答：
"""
                    regenerated = await llm_generate_func(regeneration_prompt) if callable(llm_generate_func) else f"修正后：{current_draft} - 已应用约束 {constraint}"
                    tokens_used = len(regenerated) // 4  # 粗略估算
                    total_tokens += tokens_used
                    
                    # 检查预算
                    if total_tokens >= token_budget:
                        return {
                            "final_draft": current_draft,
                            "passed": False,
                            "rounds": [asdict(r) for r in rounds],
                            "total_rounds": len(rounds),
                            "total_tokens": total_tokens,
                            "confidence": confidence_before,
                            "budget": budget,
                            "reason": f"Token预算耗尽 {total_tokens}/{token_budget}",
                            "budget_exceeded": True
                        }
                    
                    # 评估新置信度
                    new_raw_conf = min(0.95, raw_conf + 0.1 * (round_num + 1))
                    new_calibrated = self.calibrate_confidence(new_raw_conf, source)
                    
                    # 检查置信度是否稳定
                    if abs(new_calibrated - confidence_before) < 0.05 and round_num >= 1:
                        # 稳定，停止
                        rounds.append(CorrectionRound(
                            round=round_num + 1,
                            weakness=str(worst_weakness),
                            constraint=constraint,
                            regenerated=regenerated,
                            confidence_before=confidence_before,
                            confidence_after=new_calibrated,
                            passed=True,
                            tokens_used=tokens_used
                        ))
                        self.log_confidence(
                            decision=f"第{round_num+1}轮置信度稳定",
                            raw_conf=new_raw_conf,
                            calibrated_conf=new_calibrated,
                            source=source,
                            outcome="成功",
                            feedback=f"置信度稳定 {confidence_before:.2f}→{new_calibrated:.2f}"
                        )
                        return {
                            "final_draft": regenerated,
                            "passed": True,
                            "rounds": [asdict(r) for r in rounds],
                            "total_rounds": len(rounds),
                            "total_tokens": total_tokens,
                            "confidence": new_calibrated,
                            "budget": budget,
                            "reason": f"置信度稳定 {confidence_before:.2f}→{new_calibrated:.2f}，停止"
                        }
                    
                    rounds.append(CorrectionRound(
                        round=round_num + 1,
                        weakness=str(worst_weakness),
                        constraint=constraint,
                        regenerated=regenerated,
                        confidence_before=confidence_before,
                        confidence_after=new_calibrated,
                        passed=False,
                        tokens_used=tokens_used
                    ))
                    
                    current_draft = regenerated
                    calibrated_conf = new_calibrated
                    raw_conf = new_raw_conf
                    
                    self.log_confidence(
                        decision=f"第{round_num+1}轮修正",
                        raw_conf=new_raw_conf,
                        calibrated_conf=new_calibrated,
                        source=source,
                        feedback=f"弱点：{worst_weakness}，约束：{constraint}"
                    )
                
                except Exception as e:
                    rounds.append(CorrectionRound(
                        round=round_num + 1,
                        weakness=str(worst_weakness),
                        constraint=constraint,
                        regenerated=f"再生失败: {e}",
                        confidence_before=confidence_before,
                        confidence_after=confidence_before,
                        passed=False,
                        tokens_used=0
                    ))
                    break
            else:
                # 无LLM函数，模拟修正
                regenerated = f"{current_draft}\n\n[第{round_num+1}轮修正：已应用约束 {constraint}]"
                rounds.append(CorrectionRound(
                    round=round_num + 1,
                    weakness=str(worst_weakness),
                    constraint=constraint,
                    regenerated=regenerated,
                    confidence_before=confidence_before,
                    confidence_after=confidence_before + 0.05,
                    passed=round_num >= 1,
                    tokens_used=100
                ))
                current_draft = regenerated
                if round_num >= 1:
                    break
        
        # 达到最大轮数
        final_passed = len(rounds) > 0 and rounds[-1].passed
        return {
            "final_draft": current_draft,
            "passed": final_passed,
            "rounds": [asdict(r) for r in rounds],
            "total_rounds": len(rounds),
            "total_tokens": total_tokens,
            "confidence": calibrated_conf,
            "budget": budget,
            "reason": f"达到最大轮数{max_rounds}，{'通过' if final_passed else '未通过'}"
        }
    
    def get_calibration_stats(self) -> Dict[str, Any]:
        """获取校准统计，用于每周重校准"""
        if not self.confidence_logs:
            return {"total": 0}
        
        by_source = {}
        for log in self.confidence_logs:
            src = log.uncertainty_source
            if src not in by_source:
                by_source[src] = {"count": 0, "avg_raw": 0, "avg_calibrated": 0, "success": 0, "fail": 0}
            by_source[src]["count"] += 1
            by_source[src]["avg_raw"] += log.raw_confidence
            by_source[src]["avg_calibrated"] += log.calibrated_confidence
            if log.outcome_label == "成功":
                by_source[src]["success"] += 1
            elif log.outcome_label == "失败":
                by_source[src]["fail"] += 1
        
        for src in by_source:
            cnt = by_source[src]["count"]
            by_source[src]["avg_raw"] = round(by_source[src]["avg_raw"] / cnt, 3) if cnt else 0
            by_source[src]["avg_calibrated"] = round(by_source[src]["avg_calibrated"] / cnt, 3) if cnt else 0
            total_outcome = by_source[src]["success"] + by_source[src]["fail"]
            by_source[src]["success_rate"] = round(by_source[src]["success"] / total_outcome * 100, 1) if total_outcome else 0
        
        return {
            "total": len(self.confidence_logs),
            "by_source": by_source,
            "recent": [asdict(l) for l in self.confidence_logs[-10:]],
            "calibration_data": len(self.calibration_data),
            "note": "用于每周重校准和漂移检测，Layer A可观测性"
        }

# 全局
bounded_correction = BoundedCorrection()
