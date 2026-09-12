# -*- coding: utf-8 -*-
"""
JWT Auth - python-jose JWT认证 - 补全
- 商业级认证，替代简易Token
"""

import os
import time
from typing import Dict, Optional
from datetime import datetime, timedelta

try:
    from jose import JWTError, jwt
    JOSE_AVAILABLE = True
    print("✅ python-jose JWT可用 - 商业级认证")
except ImportError:
    JOSE_AVAILABLE = False
    print("⚠️ python-jose未安装，JWT不可用，pip install python-jose[cryptography]")

class JWTAuth:
    def __init__(self):
        self.secret_key = os.getenv("ZANE_JWT_SECRET", os.getenv("ZANE_TOKEN", "zane-local-secret-key-change-in-production"))
        self.algorithm = "HS256"
        self.expire_minutes = 60 * 24 * 7  # 7天
    
    def create_token(self, data: Dict, expires_delta: timedelta = None) -> str:
        """创建JWT"""
        if not JOSE_AVAILABLE:
            return data.get("sub", "demo-token")
        
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """验证JWT"""
        if not JOSE_AVAILABLE:
            # 简易验证
            if token == os.getenv("ZANE_TOKEN", "") or not os.getenv("ZANE_TOKEN"):
                return {"sub": "user", "valid": True, "method": "simple"}
            return None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            print(f"JWT验证失败: {e}")
            return None
    
    def check(self, token: str) -> Dict:
        """兼容旧auth_manager.check"""
        if not token:
            # 如果未配置Token，允许
            if not os.getenv("ZANE_TOKEN") and not os.getenv("ZANE_JWT_SECRET"):
                return {"allowed": True, "reason": "未配置认证，允许"}
            return {"allowed": False, "reason": "缺少Token"}
        
        payload = self.verify_token(token)
        if payload:
            return {"allowed": True, "payload": payload}
        
        # 回退简易Token
        if token == os.getenv("ZANE_TOKEN"):
            return {"allowed": True, "method": "simple"}
        
        return {"allowed": False, "reason": "Token无效"}

jwt_auth = JWTAuth()
