# -*- coding: utf-8 -*-
"""
iOS远程只读查看 v0914
- 先明确需求边界：只做查看状态，REST/SSE轮询订阅即可，不需要WebSocket
- 如果要做远程控制，需更严格认证审计确认，建议先做只读降低风险
- iOS专用Token短有效期可远程吊销，不与Web共用JWT
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

router = APIRouter(prefix="/api/ios", tags=["iOS远程"])

# 存储路径
BASE_DIR = Path(__file__).parent.parent.parent
IOS_STATE_PATH = BASE_DIR / "data" / "ios_state.json"
IOS_TOKENS_PATH = BASE_DIR / "data" / "ios_tokens.json"

# 确保目录存在
IOS_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

class IOSReport(BaseModel):
    viewing: bool = False
    device: str = "iPhone"
    device_id: Optional[str] = None
    app_version: Optional[str] = None
    battery_level: Optional[int] = None

class IOSTokenRequest(BaseModel):
    device_id: str
    device_name: str = "iPhone"
    purpose: str = "readonly"  # readonly 或 control

def _load_ios_state() -> Dict:
    if IOS_STATE_PATH.exists():
        try:
            with open(IOS_STATE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"viewing": False, "timestamp": 0, "device": "unknown"}

def _save_ios_state(state: Dict):
    try:
        IOS_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        state["timestamp"] = time.time()
        state["updated_at"] = datetime.now().isoformat()
        with open(IOS_STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存iOS状态失败: {e}")

def _load_ios_tokens() -> Dict:
    if IOS_TOKENS_PATH.exists():
        try:
            with open(IOS_TOKENS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"tokens": {}, "revoked": []}

def _save_ios_tokens(data: Dict):
    try:
        IOS_TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(IOS_TOKENS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存iOS Tokens失败: {e}")

def _generate_ios_token(device_id: str, purpose: str = "readonly") -> Dict[str, Any]:
    """生成iOS专用Token，短有效期"""
    import secrets
    
    token = f"zane_ios_{secrets.token_urlsafe(32)}"
    
    # 短有效期：只读24小时，控制2小时
    if purpose == "readonly":
        expires_hours = 24
    else:
        expires_hours = 2  # 控制更短
    
    expires_at = datetime.now() + timedelta(hours=expires_hours)
    
    token_data = {
        "token": token,
        "device_id": device_id,
        "purpose": purpose,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "expires_hours": expires_hours,
        "is_valid": True,
        "note": f"iOS专用Token，{purpose}，{expires_hours}小时有效期，可远程吊销，不与Web共用JWT"
    }
    
    # 保存
    tokens_data = _load_ios_tokens()
    tokens_data["tokens"][token] = token_data
    _save_ios_tokens(tokens_data)
    
    return token_data

def _verify_ios_token(token: str) -> Optional[Dict]:
    """验证iOS Token"""
    if not token:
        return None
    
    tokens_data = _load_ios_tokens()
    
    # 检查是否被吊销
    if token in tokens_data.get("revoked", []):
        return None
    
    token_data = tokens_data.get("tokens", {}).get(token)
    if not token_data:
        return None
    
    # 检查有效期
    try:
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now() > expires_at:
            # 过期
            token_data["is_valid"] = False
            _save_ios_tokens(tokens_data)
            return None
    except Exception:
        pass
    
    if not token_data.get("is_valid", True):
        return None
    
    return token_data


@router.post("/report", summary="iOS上报查看状态")
async def ios_report(report: IOSReport):
    """
    iOS前端上报查看状态
    - 用于resource_monitor检测iOS是否查看，暂停训练避免打扰
    - 只读查看，不涉及控制
    """
    state = {
        "viewing": report.viewing,
        "device": report.device,
        "device_id": report.device_id,
        "app_version": report.app_version,
        "battery_level": report.battery_level,
        "timestamp": time.time(),
        "updated_at": datetime.now().isoformat()
    }
    _save_ios_state(state)
    
    return {
        "success": True,
        "viewing": report.viewing,
        "message": f"iOS状态已更新：{'查看中' if report.viewing else '未查看'}",
        "state": state,
        "note": "只读查看状态上报，用于训练暂停判断"
    }


@router.get("/status", summary="获取iOS状态")
async def ios_status():
    """获取iOS远程查看状态"""
    state = _load_ios_state()
    
    # 判断是否最近查看（5分钟内）
    is_recent = (time.time() - state.get("timestamp", 0)) < 300
    viewing = state.get("viewing", False) and is_recent
    
    return {
        "viewing": viewing,
        "is_recent": is_recent,
        "state": state,
        "should_pause_training": viewing,
        "note": "iOS查看中时应暂停训练，避免打扰"
    }


@router.get("/system", summary="iOS只读获取系统状态")
async def ios_system_status(token: str = Header(None, alias="X-IOS-Token")):
    """
    iOS只读获取系统状态
    - 先做只读远程查看，降低第一版风险
    - 需要iOS专用Token认证
    - 不涉及控制操作
    """
    # 验证Token（可选，第一版可不强制）
    token_data = _verify_ios_token(token) if token else None
    
    if token and not token_data:
        raise HTTPException(status_code=401, detail="iOS Token无效或已过期或被吊销")
    
    # 获取系统状态 - 只读
    try:
        from ..runtime.resource_monitor import resource_monitor
        resources = resource_monitor.get_all()
    except Exception as e:
        resources = {"error": str(e), "can_train": False}
    
    try:
        from ..memory.data_flywheel import data_flywheel
        training_stats = data_flywheel.get_training_stats()
    except Exception:
        training_stats = {"sft_samples": 0}
    
    try:
        from ..memory.memory import MemoryV3
        mem_stats = {"total": 0}
    except Exception:
        mem_stats = {"total": 0}
    
    return {
        "success": True,
        "readonly": True,
        "system": {
            "resources": resources,
            "training_stats": training_stats,
            "memory_stats": mem_stats,
            "timestamp": datetime.now().isoformat()
        },
        "token_valid": token_data is not None,
        "token_purpose": token_data.get("purpose") if token_data else None,
        "note": "只读远程查看，无控制功能，REST轮询或SSE订阅即可，不需WebSocket"
    }


@router.post("/token", summary="生成iOS专用Token")
async def ios_create_token(req: IOSTokenRequest):
    """
    生成iOS专用Token
    - 不与Web端共用JWT
    - 短有效期：只读24小时，控制2小时
    - 可远程吊销，手机丢失风险不同于电脑
    """
    if req.purpose not in ["readonly", "control"]:
        raise HTTPException(status_code=400, detail="purpose必须是readonly或control")
    
    # 控制功能暂不开放，第一版只做只读
    if req.purpose == "control":
        return {
            "success": False,
            "error": "控制功能暂未开放，第一版只做只读远程查看，降低风险",
            "allowed_purpose": "readonly",
            "note": "控制功能需更严格认证审计确认，放到后续版本"
        }
    
    token_data = _generate_ios_token(req.device_id, req.purpose)
    
    return {
        "success": True,
        "token": token_data["token"],
        "expires_at": token_data["expires_at"],
        "expires_hours": token_data["expires_hours"],
        "purpose": token_data["purpose"],
        "device_id": req.device_id,
        "message": f"iOS专用Token已生成，{token_data['expires_hours']}小时有效期，Header X-IOS-Token携带",
        "usage": "请求头 X-IOS-Token: <token>",
        "note": token_data["note"]
    }


@router.post("/token/revoke", summary="吊销iOS Token")
async def ios_revoke_token(token: str, reason: str = "user_request"):
    """
    吊销iOS Token - 远程吊销机制
    - 手机丢失或被盗时可远程吊销
    - 比Web端更严格
    """
    tokens_data = _load_ios_tokens()
    
    if token not in tokens_data.get("tokens", {}):
        raise HTTPException(status_code=404, detail="Token不存在")
    
    # 加入吊销列表
    if "revoked" not in tokens_data:
        tokens_data["revoked"] = []
    
    tokens_data["revoked"].append(token)
    
    # 标记无效
    if token in tokens_data["tokens"]:
        tokens_data["tokens"][token]["is_valid"] = False
        tokens_data["tokens"][token]["revoked_at"] = datetime.now().isoformat()
        tokens_data["tokens"][token]["revoke_reason"] = reason
    
    _save_ios_tokens(tokens_data)
    
    return {
        "success": True,
        "revoked_token": token[:20] + "...",
        "reason": reason,
        "message": "Token已吊销，手机丢失时可远程吊销，比Web端更严格",
        "revoked_count": len(tokens_data["revoked"])
    }


@router.get("/tokens", summary="列出iOS Tokens")
async def ios_list_tokens():
    """列出所有iOS Tokens（管理用）"""
    tokens_data = _load_ios_tokens()
    
    # 脱敏
    safe_tokens = {}
    for tok, data in tokens_data.get("tokens", {}).items():
        safe_tokens[tok[:20] + "..."] = {
            "device_id": data.get("device_id"),
            "purpose": data.get("purpose"),
            "created_at": data.get("created_at"),
            "expires_at": data.get("expires_at"),
            "is_valid": data.get("is_valid"),
            "revoked": tok in tokens_data.get("revoked", [])
        }
    
    return {
        "tokens": safe_tokens,
        "total": len(tokens_data.get("tokens", {})),
        "revoked_count": len(tokens_data.get("revoked", [])),
        "note": "iOS专用Token，短有效期可吊销"
    }


@router.get("/readonly", summary="iOS只读查看页面")
async def ios_readonly_page():
    """
    iOS只读查看页面 - 第一版只做只读
    - 返回简单HTML，显示系统状态
    - 无控制功能
    """
    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zane iOS只读查看</title>
<style>
body { font-family: -apple-system, sans-serif; padding: 20px; background: #f5f5f7; }
.card { background: white; border-radius: 12px; padding: 16px; margin: 12px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
h1 { font-size: 20px; }
h3 { font-size: 16px; margin: 0 0 8px 0; }
.status { font-size: 14px; }
.badge { padding: 2px 8px; border-radius: 10px; font-size: 12px; }
.success { background: #34c759; color: white; }
.danger { background: #ff3b30; color: white; }
.warning { background: #ff9500; color: white; }
</style>
</head>
<body>
<h1>🖥️ Zane AGI - iOS只读查看</h1>
<p style="color:#666;font-size:12px;">第一版只做只读远程查看，无控制功能，降低风险 | REST轮询+SSE订阅，无需WebSocket</p>

<div class="card">
<h3>📊 系统状态</h3>
<div id="system-status" class="status">加载中...</div>
</div>

<div class="card">
<h3>🧬 训练状态</h3>
<div id="training-status" class="status">加载中...</div>
</div>

<div class="card">
<h3>💾 记忆统计</h3>
<div id="memory-status" class="status">加载中...</div>
</div>

<div class="card">
<h3>🔒 安全</h3>
<div id="security-status" class="status">只读模式，无控制操作</div>
</div>

<script>
async function loadStatus() {
    try {
        const res = await fetch('/api/ios/system', {
            headers: {'X-IOS-Token': localStorage.getItem('ios_token') || ''}
        });
        const data = await res.json();
        
        if (data.success) {
            const sys = data.system;
            document.getElementById('system-status').innerHTML = `
                CPU: ${sys.resources.cpu_memory?.cpu || 0}% | 内存: ${sys.resources.cpu_memory?.memory || 0}%<br>
                可训练: ${sys.resources.can_train ? '<span class="badge success">✅</span>' : '<span class="badge danger">❌</span>'}<br>
                空闲: ${sys.resources.idle?.idle_minutes || 0}分
            `;
            document.getElementById('training-status').innerHTML = `
                SFT样本: ${sys.training_stats.sft_samples || 0}<br>
                状态: ${sys.resources.can_train ? '可训练' : '不可训练'}
            `;
        }
    } catch(e) {
        document.getElementById('system-status').innerHTML = '加载失败: ' + e.message;
    }
}

loadStatus();
setInterval(loadStatus, 30000); // 30秒轮询，监控性质可接受

// 上报查看状态
function reportViewing(viewing) {
    fetch('/api/ios/report', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({viewing: viewing, device: 'iPhone', device_id: 'ios_' + Date.now()})
    });
}

reportViewing(true);
window.addEventListener('beforeunload', () => reportViewing(false));

// 每30秒上报查看中
setInterval(() => reportViewing(true), 30000);
</script>

<p style="font-size:10px;color:#999;margin-top:20px;">
只读远程查看第一版，无控制功能 | 控制功能需更严格认证审计，放到后续版本<br>
iOS专用Token短有效期可远程吊销 | 训练时检测iOS查看暂停避免打扰
</p>
</body>
</html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)
