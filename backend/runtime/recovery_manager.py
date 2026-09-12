# -*- coding: utf-8 -*-
"""
Recovery Manager - 恢复管理器
失败分类+重试策略+重规划
"""
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class FailureType(Enum):
    PERMISSION = "permission"      # 权限拒绝
    NOT_FOUND = "not_found"        # 文件/进程不存在
    TIMEOUT = "timeout"            # 超时
    NETWORK = "network"            # 网络错误
    INVALID_PARAM = "invalid_param" # 参数错误
    SYSTEM = "system"              # 系统错误
    UNKNOWN = "unknown"

@dataclass
class RecoveryAction:
    type: str  # retry, alternative, skip, ask_user, replan
    reason: str
    new_params: Optional[Dict] = None
    delay: int = 0  # 重试延迟秒

class RecoveryManager:
    """恢复管理器 - 自主恢复"""
    
    def __init__(self):
        self.failure_counts: Dict[str, int] = {}
        self.max_retries = 3
    
    def classify_failure(self, tool: str, error: str, params: Dict) -> FailureType:
        error_lower = error.lower()
        if "permission" in error_lower or "拒绝" in error or "保护" in error:
            return FailureType.PERMISSION
        if "不存在" in error or "not found" in error_lower or "no such" in error_lower:
            return FailureType.NOT_FOUND
        if "超时" in error or "timeout" in error_lower:
            return FailureType.TIMEOUT
        if "网络" in error or "network" in error_lower or "connection" in error_lower:
            return FailureType.NETWORK
        if "参数" in error or "invalid" in error_lower:
            return FailureType.INVALID_PARAM
        return FailureType.UNKNOWN
    
    def get_recovery(self, tool: str, error: str, params: Dict, failure_type: FailureType, attempt: int = 1) -> RecoveryAction:
        """根据失败类型决定恢复策略"""
        
        if attempt >= self.max_retries:
            return RecoveryAction(type="ask_user", reason=f"重试{attempt}次仍失败: {error}")
        
        if failure_type == FailureType.NOT_FOUND:
            if tool == "read_file":
                # 尝试在沙盒找同名
                import os
                basename = os.path.basename(params.get("path", ""))
                return RecoveryAction(
                    type="alternative",
                    reason=f"文件不存在，尝试在沙盒搜索 {basename}",
                    new_params={"path": os.path.join(os.path.expanduser("~"), "ZaneSandbox", basename)}
                )
            elif tool == "list_files":
                return RecoveryAction(
                    type="alternative",
                    reason="路径不存在，列出沙盒",
                    new_params={"path": os.path.expanduser("~/ZaneSandbox")}
                )
        
        elif failure_type == FailureType.PERMISSION:
            return RecoveryAction(
                type="ask_user",
                reason=f"权限被拒绝: {error}，需用户确认或移到沙盒"
            )
        
        elif failure_type == FailureType.TIMEOUT:
            return RecoveryAction(
                type="retry",
                reason=f"超时，重试 {attempt+1}/{self.max_retries}",
                delay=2 ** attempt  # 指数退避
            )
        
        elif failure_type == FailureType.NETWORK:
            return RecoveryAction(
                type="retry",
                reason="网络错误，重试",
                delay=3
            )
        
        elif failure_type == FailureType.INVALID_PARAM:
            return RecoveryAction(
                type="ask_user",
                reason=f"参数错误: {error}，需修正参数"
            )
        
        # 默认重试
        return RecoveryAction(
            type="retry",
            reason=f"未知错误，重试 {attempt+1}/{self.max_retries}: {error}",
            delay=1
        )
    
    def should_circuit_break(self, task_id: str, consecutive_failures: int) -> bool:
        """熔断判断"""
        return consecutive_failures >= 5

# 全局
recovery_manager = RecoveryManager()
