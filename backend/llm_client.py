# -*- coding: utf-8 -*-
"""
本地大模型客户端 - Local LLM Client
支持 llama.cpp OpenAI兼容接口，离线可用
设计原则：代码维护现实，AI解释现实
"""
import os
import json
import httpx
import asyncio
from typing import List, Dict, Any, Optional

# 本地模型配置 - 默认指向 llama.cpp server
LOCAL_LLM_CONFIG = {
    "api_base": os.getenv("LOCAL_LLM_API_BASE", "http://127.0.0.1:8080/v1"),
    "model": os.getenv("LOCAL_LLM_MODEL", "qwen2-7b-instruct"),
    "api_key": "local",
    "temperature": 0.7,
    "max_tokens": 2048,
}

# 可选的教师模型配置（云端，仅作顾问）
TEACHER_CONFIG = {
    "enabled": os.getenv("TEACHER_ENABLED", "false").lower() == "true",
    "api_base": os.getenv("TEACHER_API_BASE", ""),
    "api_key": os.getenv("TEACHER_API_KEY", ""),
    "model": os.getenv("TEACHER_MODEL", "gpt-4o-mini"),
}

class LocalLLMClient:
    """本地LLM客户端 - 主要推理引擎"""
    
    def __init__(self):
        self.config = LOCAL_LLM_CONFIG
        self.teacher_config = TEACHER_CONFIG
        self._offline_mode = False

    async def is_local_available(self) -> bool:
        """检测本地模型是否可用"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.config['api_base']}/models")
                return resp.status_code == 200
        except Exception:
            return False

    async def chat_completion(self, messages: List[Dict], tools: List[Dict] = None, stream: bool = False) -> Dict[str, Any]:
        """
        调用本地模型
        若本地不可用，自动进入离线模拟推理模式（保证可用性）
        """
        local_available = await self.is_local_available()
        
        if local_available and not self._offline_mode:
            try:
                return await self._call_local_api(messages, tools)
            except Exception as e:
                print(f"[LLM] 本地调用失败，切换离线模式: {e}")
                self._offline_mode = True

        # 离线智能模拟 - 基于规则的本地推理，保证系统在无模型时仍可演示完整流程
        return await self._offline_reasoning(messages, tools)

    async def _call_local_api(self, messages: List[Dict], tools: List[Dict] = None) -> Dict:
        payload = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": self.config["temperature"],
            "max_tokens": self.config["max_tokens"],
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.config['api_base']}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.config['api_key']}"}
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]

    async def _offline_reasoning(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """
        离线推理模拟器 - 用于演示和无模型环境
        根据用户意图生成合理的工具调用链
        这是保证“本地优先，离线可用”设计的关键
        """
        await asyncio.sleep(0.3)  # 模拟推理延迟
        
        # 获取最后一条用户消息
        last_user = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user = m["content"]
                break
        
        last_user_lower = last_user.lower()
        
        # 意图识别与工具规划（简化的本地推理）
        tool_calls = []
        
        if any(k in last_user_lower for k in ["内存", "进程", "cpu", "占用"]):
            tool_calls = [
                {"id": "call_1", "type": "function", "function": {"name": "inspect_processes", "arguments": json.dumps({"sort_by": "memory", "limit": 10}, ensure_ascii=False)}},
                {"id": "call_2", "type": "function", "function": {"name": "get_system_state", "arguments": json.dumps({}, ensure_ascii=False)}}
            ]
            content = "我来帮你检查当前系统资源占用情况。我将先获取进程列表并按内存排序，然后查看整体系统状态。"
        elif any(k in last_user_lower for k in ["截图", "桌面", "屏幕", "看看"]):
            tool_calls = [
                {"id": "call_1", "type": "function", "function": {"name": "take_screenshot", "arguments": json.dumps({"mode": "full"}, ensure_ascii=False)}},
                {"id": "call_2", "type": "function", "function": {"name": "ocr_screenshot", "arguments": json.dumps({"lang": "chi_sim+eng"}, ensure_ascii=False)}}
            ]
            content = "好的，我来截取当前屏幕并进行视觉分析，看看桌面状态。"
        elif any(k in last_user_lower for k in ["文件", "文件夹", "列出", "下载", "文档"]):
            tool_calls = [
                {"id": "call_1", "type": "function", "function": {"name": "list_files", "arguments": json.dumps({"path": "C:\\Users\\User\\Downloads", "detail": True}, ensure_ascii=False)}}
            ]
            content = "我来查看指定目录的文件列表，帮你整理文件信息。"
        elif any(k in last_user_lower for k in ["微信", "打开", "启动", "应用", "程序"]):
            tool_calls = [
                {"id": "call_1", "type": "function", "function": {"name": "list_windows", "arguments": json.dumps({}, ensure_ascii=False)}},
                {"id": "call_2", "type": "function", "function": {"name": "launch_application", "arguments": json.dumps({"app_name": "wechat", "path": ""}, ensure_ascii=False)}}
            ]
            content = "我先查看当前窗口状态，然后尝试启动目标应用，并验证是否成功打开。"
        elif any(k in last_user_lower for k in ["窗口", "切换", "前台", "焦点"]):
            tool_calls = [
                {"id": "call_1", "type": "function", "function": {"name": "list_windows", "arguments": json.dumps({}, ensure_ascii=False)}},
                {"id": "call_2", "type": "function", "function": {"name": "focus_window", "arguments": json.dumps({"title_keyword": "Chrome"}, ensure_ascii=False)}}
            ]
            content = "我来枚举所有窗口，找到目标窗口并将其切换到前台。"
        elif any(k in last_user_lower for k in ["搜索", "查找", "百度", "谷歌", "资料"]):
            tool_calls = [
                {"id": "call_1", "type": "function", "function": {"name": "web_search", "arguments": json.dumps({"query": last_user[:50], "count": 5}, ensure_ascii=False)}},
            ]
            content = "我来帮你搜索相关资料，并进行交叉验证。"
        else:
            # 通用对话
            return {
                "role": "assistant",
                "content": f"收到你的指令：「{last_user}」。\n\n我是你的本地私有电脑助手，运行在你的PC上，所有数据不出本地。我可以帮你：\n\n• 管理文件和文件夹\n• 监控进程和系统资源\n• 控制窗口和截图\n• 自动化鼠标键盘操作\n• 搜索网络资料并验证\n• 记住你的习惯和经验\n\n请告诉我具体想做什么，比如“看看现在什么程序占内存最多”或“截图给我看看桌面”。",
                "tool_calls": []
            }

        return {
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls
        }

    async def ask_teacher(self, prompt: str, context: str = "") -> Optional[str]:
        """可选的教师模型咨询 - 仅作顾问，不作为主执行引擎"""
        if not self.teacher_config["enabled"]:
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.teacher_config['api_base']}/chat/completions",
                    json={
                        "model": self.teacher_config["model"],
                        "messages": [
                            {"role": "system", "content": "你是资深Windows自动化顾问，提供简洁建议。"},
                            {"role": "user", "content": f"上下文:{context}\n问题:{prompt}"}
                        ]
                    },
                    headers={"Authorization": f"Bearer {self.teacher_config['api_key']}"}
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[Teacher] 教师模型调用失败: {e}")
        return None

# 全局客户端
llm_client = LocalLLMClient()
