# -*- coding: utf-8 -*-
"""
安全 + WSL + 契约 + 策略 路由 v0913整合版
- 集成cybersec_trend历史趋势时间序列
- 集成policy_firewall_v0913硬化版
- 8层架构：安全层
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel

try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False
    import logging
    loguru_logger = logging.getLogger("zane")

def _log_error(msg: str):
    (loguru_logger.error if LOGURU_AVAILABLE else print)(f"❌ {msg}")

def _log_warning(msg: str):
    (loguru_logger.warning if LOGURU_AVAILABLE else print)(f"⚠️ {msg}")

def _log_info(msg: str):
    (loguru_logger.info if LOGURU_AVAILABLE else print)(msg)

router = APIRouter(prefix="/api", tags=["安全层"])

def get_modules():
    mods = {}
    try:
        from ..security.sandbox import file_sandbox
        mods['file_sandbox'] = file_sandbox
    except ImportError:
        mods['file_sandbox'] = None
    try:
        from ..security.cybersec_tools import cybersec_tools
        mods['cybersec_tools'] = cybersec_tools
    except ImportError:
        mods['cybersec_tools'] = None
    try:
        from ..security.cybersec_trend import cybersec_trend
        mods['cybersec_trend'] = cybersec_trend
    except ImportError:
        mods['cybersec_trend'] = None
    try:
        from ..security.linux_provider import wsl_provider
        mods['wsl_provider'] = wsl_provider
    except ImportError:
        mods['wsl_provider'] = None
    try:
        from ..tool_contract import TOOL_CONTRACTS, list_contracts_by_risk
        mods['TOOL_CONTRACTS'] = TOOL_CONTRACTS
        mods['list_contracts_by_risk'] = list_contracts_by_risk
    except ImportError:
        mods['TOOL_CONTRACTS'] = {}
        mods['list_contracts_by_risk'] = lambda: {}
    try:
        from ..policy_firewall_v0913 import policy_firewall_v0913
        mods['policy_firewall'] = policy_firewall_v0913
        mods['policy_firewall_v0913'] = policy_firewall_v0913
    except ImportError:
        try:
            from ..policy_firewall import policy_firewall
            mods['policy_firewall'] = policy_firewall
            mods['policy_firewall_v0913'] = None
        except ImportError:
            mods['policy_firewall'] = None
            mods['policy_firewall_v0913'] = None
    try:
        from ..runtime.policy_engine import policy_engine
        mods['policy_engine'] = policy_engine
    except ImportError:
        mods['policy_engine'] = None
    return mods

@router.get("/security/sandbox/check", summary="沙盒检查 - 路径风险检测", tags=["安全层"])
async def security_sandbox_check(path: str):
    mods = get_modules()
    try:
        if mods['file_sandbox']:
            return mods['file_sandbox'].check_path(path)
        return {"error": "沙盒不可用"}
    except Exception as e:
        _log_error(f"沙盒检查失败: {e}")
        return {"error": str(e)}

@router.get("/security/scan", summary="安全扫描 - 明文密码+高危端口+启动项", tags=["安全层"])
async def security_scan(path: str = None):
    mods = get_modules()
    try:
        if mods['cybersec_tools']:
            result = mods['cybersec_tools'].scan_vulnerability(scan_path=path)
            # 接入历史趋势
            if mods['cybersec_trend'] and isinstance(result, dict):
                try:
                    mods['cybersec_trend'].add_snapshot(result)
                    _log_info(f"✅ 安全快照已接入历史趋势")
                except Exception as e:
                    _log_warning(f"趋势接入失败: {e}")
            return result
        return {"error": "不可用"}
    except Exception as e:
        _log_error(f"安全扫描失败: {e}")
        return {"error": str(e)}

@router.get("/security/trend", summary="安全趋势 - 时间序列端口/启动项异常感知", tags=["安全层"])
async def security_trend(days: int = 7):
    """安全趋势 - 历史时间序列"""
    mods = get_modules()
    try:
        if mods['cybersec_trend']:
            trend = mods['cybersec_trend'].get_trend(days=days)
            anomalies = mods['cybersec_trend'].detect_anomalies()
            stats = mods['cybersec_trend'].get_stats()
            return {"trend": trend, "anomalies": anomalies, "stats": stats, "technique": "时间序列端口/启动项异常感知"}
        return {"error": "趋势模块不可用"}
    except Exception as e:
        _log_error(f"安全趋势失败: {e}")
        return {"error": str(e)}

@router.get("/security/anomalies", summary="安全异常 - 端口/启动项变化检测", tags=["安全层"])
async def security_anomalies():
    """异常感知"""
    mods = get_modules()
    try:
        if mods['cybersec_trend']:
            return mods['cybersec_trend'].detect_anomalies()
        return {"error": "趋势模块不可用"}
    except Exception as e:
        _log_error(f"异常检测失败: {e}")
        return {"error": str(e)}

@router.get("/security/wsl", summary="WSL列表 - Linux子系统", tags=["安全层"])
async def security_wsl():
    mods = get_modules()
    try:
        if mods['wsl_provider']:
            return mods['wsl_provider'].wsl_list()
        return {"available": False}
    except Exception as e:
        _log_error(f"WSL列表失败: {e}")
        return {"available": False, "error": str(e)}

@router.post("/security/wsl/exec", summary="WSL执行 - 沙盒隔离", tags=["安全层"])
async def security_wsl_exec(distro: str = "Ubuntu", command: str = "ls -la", workdir: str = "~"):
    mods = get_modules()
    try:
        if mods['wsl_provider']:
            return mods['wsl_provider'].wsl_exec(distro=distro, command=command, workdir=workdir)
        return {"error": "不可用"}
    except Exception as e:
        _log_error(f"WSL执行失败: {e}")
        return {"error": str(e)}

@router.get("/contracts", summary="契约列表 - 23工具契约风险分级", tags=["安全层"])
async def list_contracts():
    mods = get_modules()
    try:
        if mods['TOOL_CONTRACTS']:
            return {
                "total": len(mods['TOOL_CONTRACTS']),
                "by_risk": {k: [{"name": c.name, "display_name": c.display_name, "risk": c.risk_level} for c in v] for k, v in mods['list_contracts_by_risk']().items()},
                "all": [{"name": c.name, "display_name": c.display_name, "risk": c.risk_level, "side_effect": c.side_effect, "category": c.category, "is_real": c.is_real} for c in mods['TOOL_CONTRACTS'].values()]
            }
        return {"total": 0, "by_risk": {}, "all": []}
    except Exception as e:
        _log_error(f"契约获取失败: {e}")
        return {"total": 0, "by_risk": {}, "all": [], "error": str(e)}

@router.get("/policy", summary="策略 - 权限分级+保护路径+硬化版", tags=["安全层"])
async def get_policy():
    mods = get_modules()
    try:
        if mods['policy_firewall_v0913']:
            fw = mods['policy_firewall_v0913']
            return {
                "engine": "PolicyFirewall v0913硬化版",
                "version": "v0913",
                "firewall": "NEED_CONFIRM阻断等待确认+前端确认事件+超时拒绝",
                "auto_allow": list(fw.auto_allow_tools),
                "denied": list(fw.denied_tools),
                "rules": {k: v.value for k, v in fw.confirmation_policy.items()},
                "protected_paths": fw.protected_paths,
                "pending": len(fw.get_pending_confirms()),
                "audit_logs": len(fw.audit_logs)
            }
        if mods['policy_engine']:
            return {
                "engine": "PolicyEngine v6.0",
                "protected_paths": mods['policy_engine'].protected_paths,
                "critical_processes": mods['policy_engine'].critical_processes,
                "auto_allow": list(mods['policy_engine'].auto_allow),
                "denied": list(mods['policy_engine'].denied)
            }
        if mods['policy_firewall']:
            return {
                "auto_allow": list(mods['policy_firewall'].auto_allow_tools),
                "denied": list(mods['policy_firewall'].denied_tools),
                "rules": {k.value: v.value for k, v in mods['policy_firewall'].confirmation_policy.items()},
                "protected_paths": mods['policy_firewall'].protected_paths
            }
        return {"policy": "不可用"}
    except Exception as e:
        _log_error(f"策略获取失败: {e}")
        return {"policy": "不可用", "error": str(e)}
