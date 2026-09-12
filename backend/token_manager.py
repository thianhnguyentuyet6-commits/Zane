# -*- coding: utf-8 -*-
"""
Token Manager - 可替换Tokens管理
前端可配置：GitHub PAT, Bing API Key, Tavily API Key, Zane Token
保存到 .env + 内存 + localStorage
"""

import os
import json
from typing import Dict, Any
from pathlib import Path

class TokenManager:
    """Token管理器 - 可替换Tokens栏"""
    
    def __init__(self):
        self.env_path = Path(__file__).parent.parent / ".env"
        self.config_path = Path(__file__).parent.parent / "data" / "tokens.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Token定义
        self.token_definitions = {
            "github_pat": {
                "name": "GitHub PAT",
                "description": "GitHub Personal Access Token，用于推送和GitHub API搜索",
                "env_key": "GITHUB_PAT",
                "required": False,
                "scopes": ["repo", "workflow"],
                "example": "github_pat_11BV5HKRI0...",
                "sensitive": True
            },
            "bing_api_key": {
                "name": "Bing Search API Key",
                "description": "Bing搜索API，1000次/月免费，用于真实联网搜索",
                "env_key": "BING_API_KEY",
                "required": False,
                "get_key_url": "https://www.microsoft.com/en-us/bing/apis/bing-web-search-api",
                "free_tier": "1000次/月",
                "example": "YOUR_BING_KEY",
                "sensitive": True
            },
            "tavily_api_key": {
                "name": "Tavily API Key",
                "description": "Tavily搜索API，用于AI优化的真实搜索",
                "env_key": "TAVILY_API_KEY",
                "required": False,
                "get_key_url": "https://tavily.com",
                "example": "tvly-...",
                "sensitive": True
            },
            "zane_token": {
                "name": "Zane Token",
                "description": "Zane API认证Token，可选，用于保护危险操作",
                "env_key": "ZANE_TOKEN",
                "required": False,
                "example": "your_secret_token",
                "sensitive": True
            },
            "openai_api_key": {
                "name": "OpenAI API Key (可选教师)",
                "description": "可选云端教师，GPT-4o-mini等，用于建议和训练数据生成",
                "env_key": "OPENAI_API_KEY",
                "required": False,
                "example": "sk-...",
                "sensitive": True
            }
        }
        
        self.tokens: Dict[str, str] = {}
        self.load()
    
    def load(self):
        """加载Tokens - .env优先，其次tokens.json，其次环境变量"""
        # 1. 从环境变量
        for token_id, definition in self.token_definitions.items():
            env_key = definition["env_key"]
            value = os.getenv(env_key, "")
            if value:
                self.tokens[token_id] = value
        
        # 2. 从 .env文件
        if self.env_path.exists():
            try:
                with open(self.env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            # 映射回token_id
                            for token_id, definition in self.token_definitions.items():
                                if definition["env_key"] == key:
                                    if value and value != "your_key" and value != "YOUR_BING_KEY":
                                        self.tokens[token_id] = value
            except Exception as e:
                print(f"加载.env失败: {e}")
        
        # 3. 从 tokens.json
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for token_id, value in data.items():
                        if value and token_id not in self.tokens:
                            self.tokens[token_id] = value
            except Exception as e:
                print(f"加载tokens.json失败: {e}")
    
    def save(self):
        """保存Tokens到 .env + tokens.json"""
        try:
            # 保存到 tokens.json (非敏感或全部，加密待加)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                # 只保存非空
                save_data = {k: v for k, v in self.tokens.items() if v}
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            # 更新 .env文件
            env_lines = []
            existing_keys = set()
            
            if self.env_path.exists():
                with open(self.env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        stripped = line.strip()
                        if not stripped or stripped.startswith('#') or '=' not in stripped:
                            env_lines.append(line)
                            continue
                        
                        key = stripped.split('=', 1)[0].strip()
                        existing_keys.add(key)
                        
                        # 如果是Token相关的key，更新
                        updated = False
                        for token_id, definition in self.token_definitions.items():
                            if definition["env_key"] == key:
                                if token_id in self.tokens and self.tokens[token_id]:
                                    env_lines.append(f"{key}={self.tokens[token_id]}\n")
                                    updated = True
                                    break
                        
                        if not updated:
                            env_lines.append(line)
            
            # 添加不存在的Tokens
            for token_id, definition in self.token_definitions.items():
                env_key = definition["env_key"]
                if env_key not in existing_keys and token_id in self.tokens and self.tokens[token_id]:
                    env_lines.append(f"{env_key}={self.tokens[token_id]}\n")
            
            with open(self.env_path, 'w', encoding='utf-8') as f:
                f.writelines(env_lines)
            
            # 更新环境变量
            for token_id, value in self.tokens.items():
                definition = self.token_definitions.get(token_id, {})
                env_key = definition.get("env_key", token_id.upper())
                os.environ[env_key] = value
            
            return True
        except Exception as e:
            print(f"保存Tokens失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_token(self, token_id: str, value: str) -> Dict:
        """设置Token"""
        if token_id not in self.token_definitions:
            return {"success": False, "error": f"未知Token: {token_id}"}
        
        if not value:
            # 删除
            if token_id in self.tokens:
                del self.tokens[token_id]
        else:
            self.tokens[token_id] = value
        
        self.save()
        
        # 特殊处理：更新相关模块
        if token_id == "github_pat":
            os.environ["GITHUB_PAT"] = value
        elif token_id == "bing_api_key":
            os.environ["BING_API_KEY"] = value
            # 更新搜索实例
            try:
                from .tools.network.web_search_real import web_search_real
                web_search_real.bing_key = value
            except Exception:
                pass
        elif token_id == "zane_token":
            os.environ["ZANE_TOKEN"] = value
            try:
                from .middleware.security import auth_manager
                auth_manager.token = value
                auth_manager.enabled = bool(value)
            except Exception:
                pass
        
        return {"success": True, "token_id": token_id, "message": f"已设置 {self.token_definitions[token_id]['name']}"}
    
    def get_token(self, token_id: str, mask: bool = True) -> Dict:
        """获取Token，可脱敏"""
        if token_id not in self.token_definitions:
            return {"error": f"未知Token: {token_id}"}
        
        value = self.tokens.get(token_id, "")
        definition = self.token_definitions[token_id]
        
        if mask and value:
            # 脱敏：显示前8后4
            if len(value) > 12:
                masked = value[:8] + "*" * (len(value) - 12) + value[-4:]
            else:
                masked = "*" * len(value)
        else:
            masked = value
        
        return {
            "token_id": token_id,
            "name": definition["name"],
            "description": definition["description"],
            "value": masked,
            "real_value": value if not mask else None,
            "has_value": bool(value),
            "env_key": definition["env_key"],
            "sensitive": definition.get("sensitive", True),
            "get_key_url": definition.get("get_key_url", ""),
            "example": definition.get("example", "")
        }
    
    def list_tokens(self, mask: bool = True) -> Dict:
        """列出所有Tokens"""
        result = {}
        for token_id in self.token_definitions:
            result[token_id] = self.get_token(token_id, mask=mask)
        return result
    
    def get_real_search_config(self) -> Dict:
        """获取真实搜索配置"""
        has_bing = bool(self.tokens.get("bing_api_key"))
        has_tavily = bool(self.tokens.get("tavily_api_key"))
        has_github = bool(self.tokens.get("github_pat"))
        
        return {
            "bing": {
                "configured": has_bing,
                "real": True,
                "source": "Bing API" if has_bing else "未配置",
                "free_tier": "1000次/月"
            },
            "tavily": {
                "configured": has_tavily,
                "real": True,
                "source": "Tavily API" if has_tavily else "未配置"
            },
            "github": {
                "configured": has_github,
                "real": True,
                "source": "GitHub API" if has_github else "未配置",
                "note": "使用GitHub PAT搜索GitHub仓库和代码"
            },
            "duckduckgo": {
                "configured": True,
                "real": True,
                "source": "DuckDuckGo HTML",
                "note": "无需Key，但不稳定"
            },
            "overall": {
                "has_real_search": has_bing or has_tavily or has_github,
                "preferred_order": ["Bing", "Tavily", "GitHub", "DuckDuckGo", "演示"],
                "current": "Bing" if has_bing else "Tavily" if has_tavily else "GitHub" if has_github else "DuckDuckGo"
            }
        }

# 全局
token_manager = TokenManager()

# 初始化时从环境变量加载，不硬编码真实Token
# 用户通过前端Token栏或.env配置
if not token_manager.tokens.get("github_pat"):
    # 尝试从环境变量获取（不在代码中硬编码）
    env_pat = os.getenv("GITHUB_PAT", "")
    if env_pat:
        token_manager.set_token("github_pat", env_pat)
        print(f"已从环境变量加载GitHub PAT: {env_pat[:20]}...")
    else:
        print("GitHub PAT未配置，可在前端Token管理栏配置")
