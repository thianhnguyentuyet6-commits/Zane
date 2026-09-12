# -*- coding: utf-8 -*-
"""
策略防火墙 - Policy Firewall
权限控制、确认、审计、安全
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import time
import json
from .tool_registry import TOOL_REGISTRY, PermissionLevel

class PolicyAction(Enum):
    ALLOW = "allow"
    NEED_CONFIRM = "need_confirm"
    DENY = "deny"

@dataclass
class PolicyRule:
    tool_name: str
    action: PolicyAction
    reason: str
    require_reason: bool = False

@dataclass
class AuditLog:
    timestamp: float
    tool_name: str
    parameters: Dict[str, Any]
    permission: str
    action: str
    result: str
    user_confirmed: bool = False
    execution_time_ms: int = 0

class PolicyFirewall:
    """策略防火墙 - 所有计算机操作的守门人"""
    
    def __init__(self):
        self.audit_logs: List[AuditLog] = []
        self.confirmation_policy = {
            PermissionLevel.READ_ONLY.value: PolicyAction.ALLOW,
            PermissionLevel.WRITE.value: PolicyAction.NEED_CONFIRM,
            PermissionLevel.DANGEROUS.value: PolicyAction.NEED_CONFIRM,
            PermissionLevel.SYSTEM.value: PolicyAction.NEED_CONFIRM,
        }
        # 用户可配置的自动确认白名单
        self.auto_allow_tools = set(["list_files", "read_file", "inspect_processes", "list_windows", "get_system_state", "take_screenshot", "ocr_screenshot", "get_clipboard", "web_search"])
        # 黑名单
        self.denied_tools = set()
        # 危险路径保护
        self.protected_paths = ["C:\\Windows\\System32", "C:\\Windows", "/etc", "/usr/bin"]
        
    def check_permission(self, tool_name: str, parameters: Dict[str, Any]) -> PolicyRule:
        """检查工具调用权限"""
        tool_def = TOOL_REGISTRY.get(tool_name)
        if not tool_def:
            return PolicyRule(tool_name, PolicyAction.DENY, f"未知工具: {tool_name}")

        if tool_name in self.denied_tools:
            return PolicyRule(tool_name, PolicyAction.DENY, "该工具已被用户禁用")

        # 保护路径检查
        if "path" in parameters:
            path = parameters["path"]
            for protected in self.protected_paths:
                if protected.lower() in path.lower() and tool_def.permission in [PermissionLevel.WRITE, PermissionLevel.DANGEROUS]:
                    return PolicyRule(tool_name, PolicyAction.NEED_CONFIRM, f"涉及系统保护路径: {protected}", require_reason=True)

        # 自动放行列表
        if tool_name in self.auto_allow_tools and tool_def.permission == PermissionLevel.READ_ONLY:
            return PolicyRule(tool_name, PolicyAction.ALLOW, "只读操作，自动放行")

        # 根据权限等级决定
        perm_action = self.confirmation_policy.get(tool_def.permission.value, PolicyAction.NEED_CONFIRM)
        
        if perm_action == PolicyAction.ALLOW:
            return PolicyRule(tool_name, PolicyAction.ALLOW, f"{tool_def.permission.value} 权限自动放行")
        elif perm_action == PolicyAction.NEED_CONFIRM:
            return PolicyRule(tool_name, PolicyAction.NEED_CONFIRM, f"{tool_def.display_name} 需要用户确认：{tool_def.description}")
        else:
            return PolicyRule(tool_name, PolicyAction.DENY, "策略拒绝")

    def log_execution(self, tool_name: str, parameters: Dict, result: str, user_confirmed: bool, exec_time_ms: int):
        """审计日志"""
        tool_def = TOOL_REGISTRY.get(tool_name)
        log = AuditLog(
            timestamp=time.time(),
            tool_name=tool_name,
            parameters=parameters,
            permission=tool_def.permission.value if tool_def else "unknown",
            action=tool_def.display_name if tool_def else tool_name,
            result=result[:500],  # 截断
            user_confirmed=user_confirmed,
            execution_time_ms=exec_time_ms
        )
        self.audit_logs.append(log)
        # 保持最近1000条
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[-1000:]

    def get_audit_logs(self, limit: int = 50) -> List[Dict]:
        logs = sorted(self.audit_logs, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [
            {
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(l.timestamp)),
                "tool": l.tool_name,
                "action": l.action,
                "permission": l.permission,
                "confirmed": l.user_confirmed,
                "result": l.result[:200],
                "exec_ms": l.execution_time_ms
            }
            for l in logs
        ]

    def update_policy(self, tool_name: str, auto_allow: bool):
        """用户更新策略"""
        if auto_allow:
            self.auto_allow_tools.add(tool_name)
        else:
            self.auto_allow_tools.discard(tool_name)

# 全局防火墙实例
policy_firewall = PolicyFirewall()
