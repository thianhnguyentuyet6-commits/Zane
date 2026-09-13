# -*- coding: utf-8 -*-
"""
策略防火墙 v0913 - 硬化版
解决缺点六：NEED_CONFIRM形式化，仅日志未阻断执行

Zane v0913单版本整合：
- NEED_CONFIRM 真正阻断等待确认，不是仅日志
- 执行前检查，危险操作暂停调度，前端确认事件
- 待确认队列 + 确认超时 + 审计
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import time
import json
import asyncio
from loguru import logger

from .tool_registry import TOOL_REGISTRY, PermissionLevel

class PolicyAction(Enum):
    ALLOW = "allow"
    NEED_CONFIRM = "need_confirm"
    DENY = "deny"
    PENDING_CONFIRM = "pending_confirm"  # 新增：等待确认状态

@dataclass
class PolicyRule:
    tool_name: str
    action: PolicyAction
    reason: str
    require_reason: bool = False
    confirm_id: Optional[str] = None  # 待确认ID

@dataclass
class PendingConfirm:
    """待确认操作"""
    id: str
    tool_name: str
    display_name: str
    parameters: Dict[str, Any]
    reason: str
    risk_level: str
    created_at: float
    expires_at: float
    status: str = "pending"  # pending/confirmed/denied/expired
    confirmed_by: Optional[str] = None

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
    blocked: bool = False

class PolicyFirewallV0913:
    """
    策略防火墙 v0913 硬化版
    
    核心修复：
    1. NEED_CONFIRM不再仅日志，而是真正阻断，返回PENDING_CONFIRM
    2. 待确认队列，执行器必须等待确认结果
    3. 前端确认事件SSE推送
    4. 确认超时自动拒绝
    5. 审计日志记录阻断
    """
    
    def __init__(self):
        self.audit_logs: List[AuditLog] = []
        self.pending_confirms: Dict[str, PendingConfirm] = {}
        self.confirm_callbacks: Dict[str, asyncio.Event] = {}
        self.confirm_results: Dict[str, bool] = {}
        
        self.confirmation_policy = {
            PermissionLevel.READ_ONLY.value: PolicyAction.ALLOW,
            PermissionLevel.WRITE.value: PolicyAction.NEED_CONFIRM,
            PermissionLevel.DANGEROUS.value: PolicyAction.NEED_CONFIRM,
            PermissionLevel.SYSTEM.value: PolicyAction.NEED_CONFIRM,
        }
        
        # 自动确认白名单 - 只读
        self.auto_allow_tools = set([
            "list_files", "read_file", "inspect_processes", "list_windows", 
            "get_system_state", "take_screenshot", "ocr_screenshot", 
            "get_clipboard", "web_search", "verify_info"
        ])
        
        # 黑名单
        self.denied_tools = set()
        
        # 危险路径保护 - 扩展
        self.protected_paths = [
            "C:\\Windows\\System32", "C:\\Windows", "/etc/shadow", "/etc/passwd",
            "/etc/sudoers", "/root/.ssh", "/etc/ssh", "C:\\Windows\\System32\\config",
            "/etc/gshadow", "C:\\Windows\\SysWOW64"
        ]
        
        # 确认超时 5分钟
        self.confirm_timeout = 300

    def check_permission(self, tool_name: str, parameters: Dict[str, Any]) -> PolicyRule:
        """检查权限 - 硬化版，真正阻断"""
        tool_def = TOOL_REGISTRY.get(tool_name)
        if not tool_def:
            return PolicyRule(tool_name, PolicyAction.DENY, f"未知工具: {tool_name}")

        if tool_name in self.denied_tools:
            return PolicyRule(tool_name, PolicyAction.DENY, "该工具已被用户禁用")

        # 保护路径检查 - 任何涉及保护路径的写入/危险操作需要确认
        if "path" in parameters:
            path = parameters["path"]
            for protected in self.protected_paths:
                if protected.lower() in path.lower():
                    if tool_def.permission in [PermissionLevel.WRITE, PermissionLevel.DANGEROUS, PermissionLevel.SYSTEM]:
                        confirm_id = self._create_pending_confirm(
                            tool_name, parameters, 
                            f"涉及系统保护路径: {protected}", 
                            "high"
                        )
                        return PolicyRule(
                            tool_name, PolicyAction.PENDING_CONFIRM, 
                            f"涉及系统保护路径: {protected}，需确认",
                            require_reason=True,
                            confirm_id=confirm_id
                        )

        # 自动放行列表 - 仅只读
        if tool_name in self.auto_allow_tools and tool_def.permission == PermissionLevel.READ_ONLY:
            return PolicyRule(tool_name, PolicyAction.ALLOW, "只读操作，自动放行")

        # 根据权限等级决定
        perm_action = self.confirmation_policy.get(tool_def.permission.value, PolicyAction.NEED_CONFIRM)
        
        if perm_action == PolicyAction.ALLOW:
            return PolicyRule(tool_name, PolicyAction.ALLOW, f"{tool_def.permission.value} 权限自动放行")
        elif perm_action == PolicyAction.NEED_CONFIRM:
            # 真正阻断，创建待确认
            risk = "high" if tool_def.permission == PermissionLevel.DANGEROUS else "medium"
            confirm_id = self._create_pending_confirm(
                tool_name, parameters,
                f"{tool_def.display_name} 需要用户确认：{tool_def.description}",
                risk
            )
            return PolicyRule(
                tool_name, PolicyAction.PENDING_CONFIRM,
                f"{tool_def.display_name} 需要确认，ID: {confirm_id}",
                confirm_id=confirm_id
            )
        else:
            return PolicyRule(tool_name, PolicyAction.DENY, "策略拒绝")

    def _create_pending_confirm(self, tool_name: str, parameters: Dict, reason: str, risk_level: str) -> str:
        """创建待确认操作 - 真正阻断"""
        import uuid
        confirm_id = f"confirm_{uuid.uuid4().hex[:8]}"
        tool_def = TOOL_REGISTRY.get(tool_name)
        
        pending = PendingConfirm(
            id=confirm_id,
            tool_name=tool_name,
            display_name=tool_def.display_name if tool_def else tool_name,
            parameters=parameters,
            reason=reason,
            risk_level=risk_level,
            created_at=time.time(),
            expires_at=time.time() + self.confirm_timeout,
            status="pending"
        )
        
        self.pending_confirms[confirm_id] = pending
        self.confirm_callbacks[confirm_id] = asyncio.Event()
        
        logger.warning(f"🛡️ 策略阻断 {tool_name} 等待确认 {confirm_id} 风险:{risk_level} 原因:{reason}")
        
        return confirm_id

    async def wait_for_confirm(self, confirm_id: str, timeout: float = None) -> bool:
        """等待用户确认 - 异步阻断"""
        if confirm_id not in self.pending_confirms:
            logger.error(f"确认ID不存在: {confirm_id}")
            return False
        
        if timeout is None:
            timeout = self.confirm_timeout
        
        event = self.confirm_callbacks.get(confirm_id)
        if not event:
            return False
        
        try:
            # 等待确认事件
            await asyncio.wait_for(event.wait(), timeout=timeout)
            result = self.confirm_results.get(confirm_id, False)
            
            pending = self.pending_confirms[confirm_id]
            pending.status = "confirmed" if result else "denied"
            
            logger.info(f"✅ 确认结果 {confirm_id} {tool_name if (tool_name:=pending.tool_name) else ''} → {result}")
            return result
        except asyncio.TimeoutError:
            # 超时自动拒绝
            pending = self.pending_confirms[confirm_id]
            pending.status = "expired"
            logger.warning(f"⏰ 确认超时 {confirm_id} 自动拒绝")
            return False
        finally:
            # 清理
            self.confirm_callbacks.pop(confirm_id, None)

    def confirm_operation(self, confirm_id: str, approved: bool, confirmed_by: str = "user") -> bool:
        """用户确认操作 - 前端调用"""
        if confirm_id not in self.pending_confirms:
            logger.error(f"确认ID不存在: {confirm_id}")
            return False
        
        pending = self.pending_confirms[confirm_id]
        if pending.status != "pending":
            logger.warning(f"确认已处理 {confirm_id} 状态:{pending.status}")
            return False
        
        if time.time() > pending.expires_at:
            pending.status = "expired"
            logger.warning(f"确认已过期 {confirm_id}")
            return False
        
        pending.status = "confirmed" if approved else "denied"
        pending.confirmed_by = confirmed_by
        self.confirm_results[confirm_id] = approved
        
        # 触发等待事件
        event = self.confirm_callbacks.get(confirm_id)
        if event:
            event.set()
        
        logger.info(f"👤 用户{'批准' if approved else '拒绝'} {confirm_id} {pending.tool_name} by {confirmed_by}")
        return True

    def get_pending_confirms(self) -> List[Dict]:
        """获取待确认列表 - 前端轮询/SSE"""
        now = time.time()
        result = []
        for pc in self.pending_confirms.values():
            if pc.status == "pending" and now < pc.expires_at:
                result.append({
                    "id": pc.id,
                    "tool_name": pc.tool_name,
                    "display_name": pc.display_name,
                    "parameters": pc.parameters,
                    "reason": pc.reason,
                    "risk_level": pc.risk_level,
                    "created_at": pc.created_at,
                    "expires_in": int(pc.expires_at - now),
                    "status": pc.status
                })
            elif pc.status == "pending" and now >= pc.expires_at:
                pc.status = "expired"
        
        return sorted(result, key=lambda x: x["created_at"], reverse=True)

    def log_execution(self, tool_name: str, parameters: Dict, result: str, user_confirmed: bool, exec_time_ms: int, blocked: bool = False):
        """审计日志 - 记录阻断"""
        tool_def = TOOL_REGISTRY.get(tool_name)
        log = AuditLog(
            timestamp=time.time(),
            tool_name=tool_name,
            parameters=parameters,
            permission=tool_def.permission.value if tool_def else "unknown",
            action=tool_def.display_name if tool_def else tool_name,
            result=result[:500],
            user_confirmed=user_confirmed,
            execution_time_ms=exec_time_ms,
            blocked=blocked
        )
        self.audit_logs.append(log)
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[-1000:]
        
        if blocked:
            logger.warning(f"🛡️ 审计 阻断 {tool_name} confirmed:{user_confirmed} {result[:100]}")
        else:
            logger.debug(f"📝 审计 {tool_name} confirmed:{user_confirmed} {exec_time_ms}ms")

    def get_audit_logs(self, limit: int = 50) -> List[Dict]:
        logs = sorted(self.audit_logs, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [
            {
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(l.timestamp)),
                "tool": l.tool_name,
                "action": l.action,
                "permission": l.permission,
                "confirmed": l.user_confirmed,
                "blocked": l.blocked,
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
        logger.info(f"策略更新 {tool_name} auto_allow:{auto_allow}")

    def clear_expired(self):
        """清理过期确认"""
        now = time.time()
        expired = [k for k, v in self.pending_confirms.items() if v.status == "pending" and now >= v.expires_at]
        for k in expired:
            self.pending_confirms[k].status = "expired"
            event = self.confirm_callbacks.pop(k, None)
            if event:
                event.set()
        if expired:
            logger.info(f"清理过期确认 {len(expired)}个")

# 全局防火墙实例 v0913
policy_firewall_v0913 = PolicyFirewallV0913()
# 兼容旧实例
policy_firewall = policy_firewall_v0913
