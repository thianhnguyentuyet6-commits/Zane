# -*- coding: utf-8 -*-
"""
自我修正 - 具体实现
怎么操作：错误分类 + 重试 + 自反思 + 验证失败修正
非空中阁楼
"""
import time
import json
from typing import Dict, List, Any, Optional
from enum import Enum

class ErrorType(Enum):
    NOT_FOUND = "NotFound"  # 永久失败，不重试
    PERMISSION_DENIED = "PermissionDenied"  # 需确认
    INVALID_PARAM = "InvalidParam"  # 参数错误，需修正
    TRANSIENT = "Transient"  # 临时失败，可重试
    PERMANENT = "Permanent"  # 永久失败

class SelfCorrection:
    """自我修正 - 具体实现"""
    
    def __init__(self):
        self.correction_history = []
        self.max_retries = 3

    def classify_error(self, error: Exception, tool_name: str, params: Dict) -> Dict:
        """错误分类 - 具体逻辑"""
        error_str = str(error).lower()
        
        if isinstance(error, FileNotFoundError) or "not found" in error_str or "不存在" in error_str:
            return {
                "type": ErrorType.NOT_FOUND.value,
                "retry": False,
                "correction": "文件不存在，尝试列出父目录",
                "next_action": {
                    "tool": "list_files",
                    "params": {"path": "/".join(params.get("path", "").split("/")[:-1])}
                },
                "reason": f"{params.get('path')} 不存在"
            }
        
        elif isinstance(error, PermissionError) or "permission" in error_str or "拒绝" in error_str:
            return {
                "type": ErrorType.PERMISSION_DENIED.value,
                "retry": False,
                "need_confirm": True,
                "correction": "权限被拒绝，需要用户确认或检查沙盒",
                "next_action": None,
                "reason": str(error)
            }
        
        elif isinstance(error, (ValueError, TypeError)) or "invalid" in error_str or "参数" in error_str:
            return {
                "type": ErrorType.INVALID_PARAM.value,
                "retry": False,
                "correction": "参数错误，尝试修正参数",
                "next_action": self._correct_params(tool_name, params, str(error)),
                "reason": str(error)
            }
        
        elif "timeout" in error_str or "超时" in error_str or "connection" in error_str:
            return {
                "type": ErrorType.TRANSIENT.value,
                "retry": True,
                "correction": "临时失败，指数退避重试",
                "next_action": {"tool": tool_name, "params": params},
                "reason": "网络或超时，临时"
            }
        
        else:
            return {
                "type": ErrorType.PERMANENT.value,
                "retry": False,
                "correction": "永久失败，记录并尝试替代方案",
                "next_action": self._alternative_tool(tool_name, params),
                "reason": str(error)
            }

    def _correct_params(self, tool_name: str, params: Dict, error_msg: str) -> Optional[Dict]:
        """参数修正 - 具体逻辑"""
        # 例子：路径错误，尝试修正
        if tool_name == "list_files" and "path" in params:
            path = params["path"]
            # Windows 路径在 Linux 上，映射
            if path.startswith("C:\\") and not os.path.exists(path):
                # 映射到演示目录
                corrected = os.path.join(os.path.expanduser("~"), "local-ai-agent-demo", os.path.basename(path))
                return {"tool": tool_name, "params": {"path": corrected}}
        
        # 例子：PID 不存在，尝试按名称查找
        if tool_name == "kill_process" and "pid" in params:
            return {"tool": "inspect_processes", "params": {"filter_name": str(params["pid"]), "limit": 5}}
        
        return None

    def _alternative_tool(self, tool_name: str, params: Dict) -> Optional[Dict]:
        """替代工具 - 具体逻辑"""
        alternatives = {
            "list_windows": {"tool": "get_system_state", "params": {}},
            "take_screenshot": {"tool": "get_system_state", "params": {}},
            "launch_application": {"tool": "list_windows", "params": {}}
        }
        return alternatives.get(tool_name)

    async def execute_with_correction(self, tool_func, tool_name: str, params: Dict, steps: List[Dict]) -> Dict:
        """带自我修正的执行 - 怎么操作"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # 执行
                result = tool_func(**params)
                
                # 检查结果是否含错误
                if isinstance(result, dict) and "error" in result:
                    raise RuntimeError(result["error"])
                
                # 成功
                if attempt > 0:
                    steps.append({
                        "id": f"correction_{attempt}",
                        "type": "verification",
                        "title": f"🔧 自我修正成功 - 第{attempt+1}次尝试",
                        "content": f"重试成功，之前失败：{last_error}",
                        "status": "通过",
                        "timestamp": time.time()
                    })
                
                return result
                
            except Exception as e:
                last_error = str(e)
                classification = self.classify_error(e, tool_name, params)
                
                steps.append({
                    "id": f"error_{attempt}",
                    "type": "error",
                    "title": f"❌ 执行失败 - {classification['type']} (尝试 {attempt+1}/{self.max_retries})",
                    "content": f"错误：{e}\n分类：{classification['type']}\n修正：{classification['correction']}\n原因：{classification['reason']}",
                    "tool_name": tool_name,
                    "status": "失败",
                    "timestamp": time.time(),
                    "classification": classification
                })
                
                # 判断是否重试
                if not classification["retry"] or attempt >= self.max_retries - 1:
                    # 不重试或已达最大重试
                    if classification["next_action"]:
                        steps.append({
                            "id": f"correction_{attempt}",
                            "type": "reasoning",
                            "title": f"💡 尝试替代方案",
                            "content": f"原工具 {tool_name} 失败，尝试 {classification['next_action']['tool']}",
                            "status": "尝试",
                            "timestamp": time.time()
                        })
                        # 执行替代
                        try:
                            alt_func = TOOL_FUNCTIONS.get(classification["next_action"]["tool"])
                            if alt_func:
                                alt_result = alt_func(**classification["next_action"]["params"])
                                return alt_result
                        except Exception as alt_e:
                            steps.append({
                                "id": f"alt_error_{attempt}",
                                "type": "error",
                                "title": "替代方案也失败",
                                "content": str(alt_e),
                                "status": "失败",
                                "timestamp": time.time()
                            })
                    
                    # 记录失败，用于 DPO
                    self.correction_history.append({
                        "timestamp": time.time(),
                        "tool": tool_name,
                        "params": params,
                        "error": str(e),
                        "classification": classification["type"],
                        "attempt": attempt+1
                    })
                    
                    return {"error": str(e), "classification": classification["type"], "attempts": attempt+1}
                
                # 重试 - 指数退避
                wait_time = 2 ** attempt
                steps.append({
                    "id": f"retry_{attempt}",
                    "type": "reasoning",
                    "title": f"⏳ 重试等待 {wait_time}秒 - 指数退避",
                    "content": f"临时失败，{wait_time}秒后重试第{attempt+2}次",
                    "status": "等待",
                    "timestamp": time.time()
                })
                
                import asyncio
                await asyncio.sleep(wait_time)
                
                # 修正参数后重试
                if classification["next_action"]:
                    params = classification["next_action"]["params"]
                    tool_name = classification["next_action"]["tool"]
                    tool_func = TOOL_FUNCTIONS.get(tool_name)
                    if not tool_func:
                        break

        return {"error": f"重试{self.max_retries}次后仍失败: {last_error}"}

    def get_correction_stats(self) -> Dict:
        """修正统计"""
        if not self.correction_history:
            return {"total": 0, "by_type": {}}
        
        by_type = {}
        for entry in self.correction_history:
            t = entry["classification"]
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total": len(self.correction_history),
            "by_type": by_type,
            "recent": self.correction_history[-5:],
            "success_rate": "N/A"  # 可计算重试成功率
        }

# 全局自我修正
self_correction = SelfCorrection()

# 需要导入 TOOL_FUNCTIONS，避免循环
try:
    from ..tools_impl import TOOL_FUNCTIONS
    import os
except Exception:
    TOOL_FUNCTIONS = {}
    import os
