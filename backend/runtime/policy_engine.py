# -*- coding: utf-8 -*-
"""
策略引擎 - 安全边界
LLM只提议，Policy Engine决定是否允许、需确认、拒绝
永不依赖模型判断安全
"""
from typing import Dict, List
from ..tool_contract import TOOL_CONTRACTS

class PolicyLevel:
    READ_ONLY = "read_only"
    REVERSIBLE_WRITE = "reversible_write"
    DESTRUCTIVE = "destructive"
    SYSTEM = "system"

class PolicyEngine:
    """策略引擎 - 安全边界"""
    
    def __init__(self):
        # 保护路径
        self.protected_paths = [
            "C:\\Windows\\System32",
            "C:\\Windows\\SysWOW64",
            "C:\\Windows\\System",
            "C:\\Program Files\\Windows",
            "/etc",
            "/usr/bin",
            "/bin",
            "/sbin",
            "/boot"
        ]
        
        # 关键进程
        self.critical_processes = [
            "csrss.exe", "winlogon.exe", "services.exe", "lsass.exe",
            "svchost.exe", "wininit.exe", "System", "Registry"
        ]
        
        # 白名单 - 自动放行
        self.auto_allow = set([
            "list_files", "read_file", "inspect_processes", "list_windows",
            "get_system_state", "take_screenshot", "ocr_screenshot",
            "get_clipboard", "web_search", "verify_info"
        ])
        
        # 黑名单 - 拒绝
        self.denied = set()

    def decide(self, tool_name: str, params: Dict) -> Dict:
        """决定是否允许 - 安全边界，兼容 decision/action"""
        contract = TOOL_CONTRACTS.get(tool_name)
        if not contract:
            # 如果工具在白名单或已知只读工具，允许
            if tool_name in self.auto_allow:
                return {"action": "allow", "decision": "allow", "reason": f"白名单工具: {tool_name}", "risk": "low"}
            # 常见只读工具即使无契约也允许
            read_only_tools = {"get_system_state", "list_files", "read_file", "inspect_processes", "list_windows", "get_clipboard", "web_search", "web_search_real", "security_scan", "wsl_exec", "take_screenshot", "ocr_screenshot"}
            if tool_name in read_only_tools:
                return {"action": "allow", "decision": "allow", "reason": f"只读工具: {tool_name}", "risk": "low"}
            return {"action": "deny", "decision": "deny", "reason": f"未知工具: {tool_name}", "risk": "high"}
        
        if tool_name in self.denied:
            return {"action": "deny", "decision": "deny", "reason": f"工具已被禁用: {tool_name}", "risk": "high"}
        
        # 检查保护路径
        if "path" in params:
            path = params["path"]
            for protected in self.protected_paths:
                if protected.lower() in path.lower():
                    if contract.side_effect in ["destructive", "system"]:
                        return {
                            "action": "need_confirm",
                            "decision": "need_confirm",
                            "level": "critical",
                            "reason": f"涉及系统保护路径: {protected}",
                            "need_reason": True,
                            "risk": "critical"
                        }
        
        # 检查关键进程
        if tool_name == "kill_process":
            pid = params.get("pid")
            name = params.get("name", "")
            if name and name.lower() in [c.lower() for c in self.critical_processes]:
                return {
                    "action": "deny",
                    "decision": "deny",
                    "reason": f"关键系统进程，不能结束: {name}",
                    "risk": "critical"
                }
        
        # 根据副作用决定
        if contract.side_effect == "none":
            # 只读，自动放行
            if tool_name in self.auto_allow:
                return {"action": "allow", "decision": "allow", "reason": "只读白名单", "risk": "low"}
            return {"action": "allow", "decision": "allow", "reason": "只读操作", "risk": "low"}
        
        elif contract.side_effect == "reversible":
            # 可逆写入，需低级确认
            return {
                "action": "need_confirm",
                "decision": "need_confirm",
                "level": "low",
                "reason": f"{contract.display_name} - 可逆操作，需确认",
                "preview": self._generate_preview(tool_name, params),
                "risk": "medium"
            }
        
        elif contract.side_effect == "destructive":
            # 破坏性，需高级确认+原因
            return {
                "action": "need_confirm",
                "decision": "need_confirm",
                "level": "high",
                "need_reason": True,
                "reason": f"{contract.display_name} - 破坏性操作，需二次确认",
                "preview": self._generate_preview(tool_name, params),
                "risk": "high"
            }
        
        elif contract.side_effect == "system":
            # 系统级，拒绝
            return {
                "action": "deny",
                "decision": "deny",
                "reason": f"{contract.display_name} - 系统级操作，拒绝",
                "risk": "critical"
            }
        
        return {"action": "need_confirm", "decision": "need_confirm", "level": "medium", "reason": "默认需确认", "risk": "medium"}

    def _generate_preview(self, tool_name: str, params: Dict) -> Dict:
        """生成预览Diff - 具体实现"""
        if tool_name == "delete_file":
            path = params.get("path", "")
            return {
                "type": "delete",
                "message": f"将删除: {path}",
                "can_undo": params.get("to_recycle", True),
                "undo_method": "从回收站恢复" if params.get("to_recycle", True) else "无法撤销"
            }
        elif tool_name == "write_file":
            path = params.get("path", "")
            content = params.get("content", "")
            return {
                "type": "write",
                "message": f"将写入: {path}",
                "size": len(content),
                "preview": content[:200] + ("..." if len(content) > 200 else ""),
                "can_undo": True,
                "undo_method": "删除文件"
            }
        elif tool_name == "focus_window":
            return {
                "type": "window",
                "message": f"将聚焦窗口: {params.get('title_keyword') or params.get('hwnd')}",
                "can_undo": True,
                "undo_method": "聚焦回原窗口"
            }
        
        return {"type": "generic", "message": f"{tool_name}: {params}"}

policy_engine = PolicyEngine()
