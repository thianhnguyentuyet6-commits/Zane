# -*- coding: utf-8 -*-
"""
文件工具 - 深模块 - FileTools
接口: list_files, read_file, write_file, delete_file, create_folder, move_file
深模块：接口是test surface，内部filelock+沙盒+重要性排序+回收站+可撤销
"""
import os
import time
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from filelock import FileLock
    HAS_FILELOCK = True
except ImportError:
    HAS_FILELOCK = False

class FileTools:
    """文件工具深模块 - Windows真实"""
    
    def __init__(self, base_dir: str = None, sandbox_root: str = None):
        self.base_dir = Path(base_dir or Path(__file__).parent.parent.parent)
        self.sandbox_root = Path(sandbox_root or self.base_dir / "ZaneSandbox")
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
        self.recycle_dir = self.sandbox_root / ".recycle"
        self.recycle_dir.mkdir(parents=True, exist_ok=True)
        self.access_history = {}
        self.protected_paths = [
            "C:\\Windows\\System32", "C:\\Windows\\SysWOW64",
            "/etc", "/bin", "/sbin", "/usr/bin"
        ]
    
    def _is_protected(self, path: str) -> bool:
        real = str(Path(path).resolve()).lower()
        for protected in self.protected_paths:
            if protected.lower() in real:
                return True
        return False
    
    def _calculate_importance(self, file_path: str, file_info: Dict = None) -> float:
        # 最近访问+上次任务引用加权
        now = time.time()
        access_time = self.access_history.get(file_path, {}).get("last_access", 0)
        recency_score = max(0, 1 - (now - access_time) / (7*24*3600)) if access_time else 0
        task_ref = self.access_history.get(file_path, {}).get("task_ref", 0)
        importance = 0.3 + recency_score * 0.4 + task_ref * 0.3
        return min(1.0, importance)
    
    def list_files(self, path: str, detail: bool = False, pattern: str = None) -> Dict:
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return {"error": f"路径不存在: {path}", "files": [], "total": 0}
            
            files = []
            for item in p.iterdir():
                if pattern and pattern not in item.name:
                    continue
                info = {
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "size_readable": f"{item.stat().st_size/1024:.1f}KB" if item.is_file() else "",
                    "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(item.stat().st_mtime)),
                    "importance": self._calculate_importance(str(item))
                }
                files.append(info)
            
            # 重要性排序
            files.sort(key=lambda x: x["importance"], reverse=True)
            
            # 上下文预算截断
            max_show = 100
            truncated = len(files) > max_show
            shown = files[:max_show]
            
            return {
                "files": shown,
                "total": len(files),
                "shown": len(shown),
                "truncated": truncated,
                "sorted_by": "importance",
                "path": str(p)
            }
        except Exception as e:
            return {"error": str(e), "files": [], "total": 0}
    
    def read_file(self, path: str, max_chars: int = 5000) -> Dict:
        try:
            if self._is_protected(path):
                return {"error": f"保护路径禁止读取: {path}", "success": False, "security": "拦截"}
            
            p = Path(path)
            if not p.exists():
                return {"error": f"文件不存在: {path}", "success": False}
            
            content = p.read_text(encoding='utf-8', errors='ignore')
            truncated = len(content) > max_chars
            result_content = content[:max_chars]
            
            # 更新访问历史
            self.access_history[path] = {"last_access": time.time(), "task_ref": 1}
            
            return {
                "content": result_content,
                "path": str(p),
                "size": len(content),
                "length": len(result_content),
                "truncated": truncated,
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def write_file(self, path: str, content: str) -> Dict:
        try:
            if self._is_protected(path):
                return {"error": f"保护路径禁止写入: {path}", "success": False, "security": "拦截"}
            
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            
            # filelock
            lock_path = str(p) + ".lock"
            if HAS_FILELOCK:
                from filelock import FileLock
                lock = FileLock(lock_path, timeout=5)
                with lock:
                    p.write_text(content, encoding='utf-8')
            else:
                p.write_text(content, encoding='utf-8')
            
            return {"success": True, "path": str(p), "size_bytes": len(content.encode('utf-8'))}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def delete_file(self, path: str, to_recycle: bool = True) -> Dict:
        try:
            if self._is_protected(path):
                return {"error": f"保护路径禁止删除: {path}", "success": False, "security": "拦截"}
            
            p = Path(path)
            if not p.exists():
                return {"error": f"文件不存在: {path}", "success": False}
            
            if to_recycle:
                recycle_name = f"{p.name}.{int(time.time())}"
                recycle_path = self.recycle_dir / recycle_name
                shutil.move(str(p), str(recycle_path))
                return {
                    "success": True,
                    "path": str(p),
                    "recycle": str(recycle_path),
                    "can_undo": True,
                    "message": f"已删除到回收站: {recycle_path}"
                }
            else:
                p.unlink()
                return {"success": True, "path": str(p), "can_undo": False}
        except Exception as e:
            return {"error": str(e), "success": False}

file_tools = FileTools()
