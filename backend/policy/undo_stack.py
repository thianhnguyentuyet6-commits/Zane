# -*- coding: utf-8 -*-
"""
撤销栈 - Undo Stack
商业级：每个写操作可回滚，类似 Git
"""
import time
import json
from typing import Dict, List, Any, Optional
from enum import Enum

class OperationType(Enum):
    CREATE_FILE = "创建文件"
    DELETE_FILE = "删除文件"
    WRITE_FILE = "写入文件"
    CREATE_FOLDER = "创建文件夹"
    DELETE_FOLDER = "删除文件夹"
    KILL_PROCESS = "结束进程"
    FOCUS_WINDOW = "聚焦窗口"

class UndoStack:
    """撤销栈 - 记录所有写操作，支持回滚"""
    
    def __init__(self, max_size: int = 100):
        self.stack: List[Dict] = []
        self.max_size = max_size
        self.redo_stack: List[Dict] = []

    def push(self, operation: str, params: Dict, reverse_params: Dict, description: str) -> Dict:
        """推入操作"""
        entry = {
            "id": f"op_{int(time.time()*1000)}",
            "timestamp": time.time(),
            "operation": operation,
            "params": params,
            "reverse_params": reverse_params,  # 逆操作参数
            "description": description,
            "can_undo": True
        }
        self.stack.append(entry)
        if len(self.stack) > self.max_size:
            self.stack = self.stack[-self.max_size:]
        
        # 清空重做栈
        self.redo_stack = []
        
        return entry

    def undo(self) -> Optional[Dict]:
        """撤销最后一个操作"""
        if not self.stack:
            return None
        
        entry = self.stack.pop()
        self.redo_stack.append(entry)
        
        # 执行逆操作
        # 这里演示逻辑，实际调用工具
        reverse_op = entry["reverse_params"]
        
        return {
            "undone": entry,
            "reverse_op": reverse_op,
            "message": f"已撤销：{entry['description']}"
        }

    def redo(self) -> Optional[Dict]:
        """重做"""
        if not self.redo_stack:
            return None
        
        entry = self.redo_stack.pop()
        self.stack.append(entry)
        
        return {
            "redone": entry,
            "message": f"已重做：{entry['description']}"
        }

    def get_history(self, limit: int = 20) -> List[Dict]:
        return list(reversed(self.stack[-limit:]))

    def clear(self):
        self.stack = []
        self.redo_stack = []

undo_stack = UndoStack()
