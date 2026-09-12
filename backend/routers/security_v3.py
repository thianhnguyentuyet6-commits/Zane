# -*- coding: utf-8 -*-
"""
安全 + WSL + 契约 + 策略 路由
拆分自 main_v6.py
"""
from fastapi import APIRouter, HTTPException

try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False
    import logging
    loguru_logger = logging.getLogger("zane")

def _log_error(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.error(msg)
    else:
        print(f"❌ {msg}")

def _log_warning(msg: str):
    if LOGURU_AVAILABLE:
        loguru_logger.warning(msg)
    else:
        print(f"⚠️ {msg}")

router = APIRouter(prefix="/api", tags=["安全"])

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
        from ..policy_firewall import policy_firewall
        mods['policy_firewall'] = policy_firewall
    except ImportError:
        mods['policy_firewall'] = None
    try:
        from ..runtime.policy_engine import policy_engine
        mods['policy_engine'] = policy_engine
    except ImportError:
        mods['policy_engine'] = None
    return mods

@router.get("/security/sandbox/check")
async def security_sandbox_check(path: str):
    mods = get_modules()
    try:
        if mods['file_sandbox']:
            return mods['file_sandbox'].check_path(path)
        return {"error": "沙盒不可用"}
    except Exception as e:
        _log_error(f"沙盒检查失败: {e}")
        return {"error": str(e)}

@router.get("/security/scan")
async def security_scan(path: str = None):
    mods = get_modules()
    try:
        if mods['cybersec_tools']:
            return mods['cybersec_tools'].scan_vulnerability(scan_path=path)
        return {"error": "不可用"}
    except Exception as e:
        _log_error(f"安全扫描失败: {e}")
        return {"error": str(e)}

@router.get("/security/wsl")
async def security_wsl():
    mods = get_modules()
    try:
        if mods['wsl_provider']:
            return mods['wsl_provider'].wsl_list()
        return {"available": False}
    except Exception as e:
        _log_error(f"WSL列表失败: {e}")
        return {"available": False, "error": str(e)}

@router.post("/security/wsl/exec")
async def security_wsl_exec(distro: str = "Ubuntu", command: str = "ls -la", workdir: str = "~"):
    mods = get_modules()
    try:
        if mods['wsl_provider']:
            return mods['wsl_provider'].wsl_exec(distro=distro, command=command, workdir=workdir)
        return {"error": "不可用"}
    except Exception as e:
        _log_error(f"WSL执行失败: {e}")
        return {"error": str(e)}

@router.get("/contracts")
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

@router.get("/policy")
async def get_policy():
    mods = get_modules()
    try:
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
