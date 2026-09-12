# -*- coding: utf-8 -*-
"""
Model Interface - 模型接口
统一本地LLM调用，支持OpenAI兼容，Teacher可选
"""
import os
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator

class ModelInterface:
    """模型接口 - 本地优先，云端可选教师"""
    
    def __init__(self):
        self.config = {
            "api_base": os.getenv("LLM_API_BASE", "http://localhost:8080/v1"),
            "model": os.getenv("LLM_MODEL", "qwen3-30b-a3b"),
            "temperature": 0.7,
            "max_tokens": 2048,
            "timeout": 60,
        }
        self.local_available = False
        self.teacher_available = False
        self.teacher_config = {
            "api_base": os.getenv("TEACHER_API_BASE", ""),
            "api_key": os.getenv("TEACHER_API_KEY", ""),
            "model": os.getenv("TEACHER_MODEL", "gpt-4o-mini"),
        }
    
    async def check_local(self) -> bool:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.config['api_base'].replace('/v1', '')}/health")
                self.local_available = resp.status_code == 200
                return self.local_available
        except Exception:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(f"{self.config['api_base']}/models")
                    self.local_available = resp.status_code == 200
                    return self.local_available
            except Exception:
                self.local_available = False
                return False
    
    async def generate(self, messages: List[Dict], tools: List[Dict] = None,
                       temperature: float = None, max_tokens: int = None) -> Dict:
        """生成 - 支持工具调用"""
        
        # 检查本地可用
        available = await self.check_local()
        if not available:
            return self._demo_response(messages, tools)
        
        try:
            import httpx
            payload = {
                "model": self.config["model"],
                "messages": messages,
                "temperature": temperature or self.config["temperature"],
                "max_tokens": max_tokens or self.config["max_tokens"],
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            
            async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                resp = await client.post(
                    f"{self.config['api_base']}/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    choice = data["choices"][0]
                    return {
                        "content": choice["message"].get("content", ""),
                        "tool_calls": choice["message"].get("tool_calls", []),
                        "finish_reason": choice.get("finish_reason", "stop"),
                        "usage": data.get("usage", {}),
                        "real": True
                    }
                else:
                    return self._demo_response(messages, tools, error=f"HTTP {resp.status_code}")
        
        except Exception as e:
            return self._demo_response(messages, tools, error=str(e))
    
    def _demo_response(self, messages: List[Dict], tools: List[Dict] = None, error: str = "") -> Dict:
        """演示响应 - 离线可用"""
        last_msg = messages[-1]["content"] if messages else ""
        
        # 简单意图到工具映射
        tool_calls = []
        if tools:
            if any(k in last_msg for k in ["文件", "下载", "列出"]):
                tool_calls = [{"id": "call_1", "type": "function", "function": {"name": "list_files", "arguments": json.dumps({"path": "C:\\Users\\User\\Downloads", "detail": True}, ensure_ascii=False)}}]
            elif any(k in last_msg for k in ["进程", "任务"]):
                tool_calls = [{"id": "call_1", "type": "function", "function": {"name": "inspect_processes", "arguments": json.dumps({"sort_by": "memory", "limit": 20})}}]
            elif any(k in last_msg for k in ["窗口"]):
                tool_calls = [{"id": "call_1", "type": "function", "function": {"name": "list_windows", "arguments": json.dumps({"only_visible": True})}}]
            elif any(k in last_msg for k in ["系统", "状态", "性能"]):
                tool_calls = [{"id": "call_1", "type": "function", "function": {"name": "get_system_state", "arguments": "{}"}}]
            elif any(k in last_msg for k in ["搜索", "联网"]):
                tool_calls = [{"id": "call_1", "type": "function", "function": {"name": "web_search_real", "arguments": json.dumps({"query": last_msg, "count": 5}, ensure_ascii=False)}}]
        
        content = f"（演示模式，本地LLM离线{': ' + error if error else ''}）\n已分析你的请求：{last_msg[:100]}\n"
        if tool_calls:
            content += f"将调用工具：{tool_calls[0]['function']['name']}"
        
        return {
            "content": content,
            "tool_calls": tool_calls,
            "finish_reason": "tool_calls" if tool_calls else "stop",
            "usage": {"prompt_tokens": len(last_msg), "completion_tokens": len(content)},
            "real": False,
            "demo": True
        }
    
    async def teacher_suggest(self, task: str, current_plan: Dict) -> Optional[Dict]:
        """教师建议 - 可选云端"""
        if not self.teacher_config["api_base"] or not self.teacher_config["api_key"]:
            return None
        
        try:
            import httpx
            messages = [
                {"role": "system", "content": "你是资深工程师，审查本地代理的计划，给出建议。只返回JSON：{\"suggestions\": [], \"risk\": \"low/medium/high\", \"improved_plan\": {}}"},
                {"role": "user", "content": f"任务：{task}\n当前计划：{json.dumps(current_plan, ensure_ascii=False)}"}
            ]
            
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.teacher_config['api_base']}/chat/completions",
                    json={
                        "model": self.teacher_config["model"],
                        "messages": messages,
                        "temperature": 0.3
                    },
                    headers={
                        "Authorization": f"Bearer {self.teacher_config['api_key']}",
                        "Content-Type": "application/json"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception as e:
            print(f"教师建议失败: {e}")
        
        return None

# 全局
model_interface = ModelInterface()
