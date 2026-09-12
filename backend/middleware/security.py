# -*- coding: utf-8 -*-
"""
安全中间件 - 速率限制+可选Token认证+日志净化
"""
import time
import os
from typing import Dict
from collections import defaultdict, deque

class RateLimiter:
    """速率限制 - 60/分钟"""
    
    def __init__(self, max_requests: int = 60, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def check(self, client_id: str) -> Dict:
        now = time.time()
        q = self.requests[client_id]
        
        # 清理过期
        while q and q[0] < now - self.window:
            q.popleft()
        
        if len(q) >= self.max_requests:
            return {
                "allowed": False,
                "reason": f"速率限制: {len(q)}/{self.max_requests} 请求/ {self.window}秒",
                "retry_after": int(q[0] + self.window - now) if q else self.window
            }
        
        q.append(now)
        return {"allowed": True, "remaining": self.max_requests - len(q)}

class AuthManager:
    """可选 Token 认证 - 环境变量 ZANE_TOKEN"""
    
    def __init__(self):
        self.token = os.getenv("ZANE_TOKEN", "")
        self.enabled = bool(self.token)
    
    def check(self, request_token: str = "") -> Dict:
        if not self.enabled:
            return {"allowed": True, "reason": "未启用认证"}
        
        if not request_token:
            return {"allowed": False, "reason": "需提供 X-Zane-Token 头"}
        
        if request_token == self.token:
            return {"allowed": True, "reason": "认证通过"}
        
        return {"allowed": False, "reason": "Token 错误"}

def sanitize_log(text: str) -> str:
    """日志净化 - 防止换行注入"""
    if not isinstance(text, str):
        text = str(text)
    # 移除换行和控制字符
    text = text.replace("\n", "\\n").replace("\r", "\\r").replace("\x00", "")
    # 截断
    if len(text) > 1000:
        text = text[:1000] + "...[截断]"
    return text

# 全局
rate_limiter = RateLimiter(max_requests=60, window=60)
auth_manager = AuthManager()
