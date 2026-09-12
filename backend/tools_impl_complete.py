# -*- coding: utf-8 -*-
"""
补充工具实现 - 文件操作等缺失工具
"""
import os
import shutil
import time
import platform
from typing import Dict

def _resolve_demo_path(path: str) -> str:
    """路径兼容：Windows路径映射到Linux演示"""
    if platform.system() != "Windows" and path.startswith("C:\\"):
        demo_base = os.path.join(os.path.expanduser("~"), "local-ai-agent-demo")
        os.makedirs(demo_base, exist_ok=True)
        if "Downloads" in path:
            base = os.path.join(demo_base, "Downloads")
        elif "Documents" in path:
            base = os.path.join(demo_base, "Documents")
        elif "Desktop" in path:
            base = os.path.join(demo_base, "Desktop")
        else:
            base = demo_base
        os.makedirs(base, exist_ok=True)
        # 如果路径包含子路径
        if "\\" in path:
            # 提取最后部分之后的
            parts = path.split("\\")
            # 找到Downloads/Documents/Desktop之后的部分
            try:
                idx = next(i for i, p in enumerate(parts) if p in ["Downloads", "Documents", "Desktop"])
                sub = os.path.join(*parts[idx+1:]) if len(parts) > idx+1 else ""
                if sub:
                    # 处理通配符
                    if "*" in sub:
                        return os.path.join(base, os.path.dirname(sub))
                    return os.path.join(base, sub)
            except:
                pass
        return base
    return path

def create_folder(path: str) -> Dict:
    try:
        actual = _resolve_demo_path(path)
        os.makedirs(actual, exist_ok=True)
        return {"success": True, "path": path, "actual_path": actual, "message": f"已创建文件夹: {actual}"}
    except Exception as e:
        return {"success": False, "error": str(e), "path": path}

def delete_file(path: str, to_recycle: bool = True) -> Dict:
    try:
        from .security.sandbox import file_sandbox
        check = file_sandbox.check_path(path)
        if check["risk"] == "high":
            return {"success": False, "error": f"保护路径禁止: {check['reason']}", "path": path, "security": "拦截"}
        
        actual = _resolve_demo_path(path)
        if not os.path.exists(actual):
            return {"success": False, "error": f"文件不存在: {actual}", "path": path}
        
        if to_recycle:
            recycle_dir = os.path.join(os.path.expanduser("~"), "ZaneSandbox", ".recycle")
            os.makedirs(recycle_dir, exist_ok=True)
            dest = os.path.join(recycle_dir, os.path.basename(actual) + f".{int(time.time())}")
            shutil.move(actual, dest)
            return {"success": True, "path": path, "recycle": dest, "can_undo": True, "message": f"已移到回收站: {dest}"}
        else:
            if os.path.isdir(actual):
                shutil.rmtree(actual)
            else:
                os.remove(actual)
            return {"success": True, "path": path, "message": f"已删除: {actual}", "can_undo": False}
    except Exception as e:
        return {"success": False, "error": str(e), "path": path}

def write_file(path: str, content: str) -> Dict:
    try:
        from .security.sandbox import file_sandbox
        # 检查大小
        size = len(content.encode('utf-8'))
        if size > 10*1024*1024:
            return {"success": False, "error": f"文件过大 {size/1024/1024:.1f}MB > 10MB", "path": path}
        
        actual = _resolve_demo_path(path)
        check = file_sandbox.check_path(actual)
        if not check["allowed"] and check["risk"] == "high":
            return {"success": False, "error": f"保护路径: {check['reason']}", "path": path}
        
        dir_path = os.path.dirname(actual)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        with open(actual, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"success": True, "path": path, "actual_path": actual, "size": len(content), "size_bytes": size, "can_undo": True}
    except Exception as e:
        return {"success": False, "error": str(e), "path": path}

def move_file(source: str, dest: str) -> Dict:
    try:
        actual_src = _resolve_demo_path(source)
        actual_dest = _resolve_demo_path(dest)
        
        # 处理通配符源
        if "*" in source:
            import glob
            pattern = actual_src
            # 如果源是 C:\...*.docx 形式，actual_src 已处理为目录
            # 需要重新构造 pattern
            src_dir = os.path.dirname(actual_src) if not os.path.isdir(actual_src) else actual_src
            if "*" in source:
                # 提取通配符
                wildcard = os.path.basename(source)
                pattern = os.path.join(src_dir, wildcard)
            files = glob.glob(pattern)
            if not files:
                return {"success": False, "error": f"无匹配文件: {pattern}", "source": source}
            
            os.makedirs(actual_dest, exist_ok=True)
            moved = []
            for f in files:
                dest_path = os.path.join(actual_dest, os.path.basename(f))
                shutil.move(f, dest_path)
                moved.append(dest_path)
            
            return {"success": True, "source": source, "dest": dest, "moved": moved, "count": len(moved), "message": f"已移动 {len(moved)} 个文件"}
        
        if not os.path.exists(actual_src):
            return {"success": False, "error": f"源不存在: {actual_src}", "source": source}
        
        # 目标如果是目录，移动到目录内
        if os.path.isdir(actual_dest) or dest.endswith("\\") or dest.endswith("/"):
            os.makedirs(actual_dest, exist_ok=True)
            actual_dest = os.path.join(actual_dest, os.path.basename(actual_src))
        else:
            dest_dir = os.path.dirname(actual_dest)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
        
        shutil.move(actual_src, actual_dest)
        return {"success": True, "source": source, "dest": dest, "actual_dest": actual_dest, "message": f"已移动: {actual_src} -> {actual_dest}", "can_undo": True}
    except Exception as e:
        return {"success": False, "error": str(e), "source": source, "dest": dest}

def read_file_complete(path: str, max_chars: int = 5000) -> Dict:
    try:
        actual = _resolve_demo_path(path)
        if not os.path.exists(actual):
            # 尝试在demo目录找同名
            demo_base = os.path.join(os.path.expanduser("~"), "local-ai-agent-demo")
            alt = os.path.join(demo_base, "Downloads", os.path.basename(path))
            if os.path.exists(alt):
                actual = alt
        
        with open(actual, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(max_chars)
        return {"path": path, "actual_path": actual, "content": content, "length": len(content), "truncated": len(content) >= max_chars}
    except Exception as e:
        return {"error": f"读取失败: {e}", "path": path}

# 补充到 TOOL_FUNCTIONS
def patch_tool_functions():
    try:
        from .tools_impl import TOOL_FUNCTIONS, tool_executor
        TOOL_FUNCTIONS["create_folder"] = lambda **kwargs: create_folder(**kwargs)
        TOOL_FUNCTIONS["delete_file"] = lambda **kwargs: delete_file(**kwargs)
        TOOL_FUNCTIONS["write_file"] = lambda **kwargs: write_file(**kwargs)
        TOOL_FUNCTIONS["move_file"] = lambda **kwargs: move_file(**kwargs)
        TOOL_FUNCTIONS["read_file"] = lambda **kwargs: read_file_complete(**kwargs)
        TOOL_FUNCTIONS["web_search_real"] = lambda **kwargs: tool_executor.web_search(**kwargs)  # 临时，回退到演示，真实在 main_v3 用 web_search_real 实例
        # 尝试真实搜索
        try:
            from .tools.network.web_search_real import web_search_real as real_search
            import asyncio
            def sync_search(**kwargs):
                try:
                    return asyncio.run(real_search.search(kwargs.get("query", ""), kwargs.get("count", 5)))
                except:
                    return {"query": kwargs.get("query"), "results": [], "error": "搜索失败"}
            TOOL_FUNCTIONS["web_search_real"] = sync_search
        except:
            pass
        
        # 安全工具
        try:
            from .security.cybersec_tools import cybersec_tools
            TOOL_FUNCTIONS["security_scan"] = lambda **kwargs: cybersec_tools.scan_vulnerability(**kwargs)
            TOOL_FUNCTIONS["scan_large_files"] = lambda **kwargs: cybersec_tools.scan_large_files(**kwargs)
        except:
            pass
        
        try:
            from .security.linux_provider import wsl_provider
            TOOL_FUNCTIONS["wsl_exec"] = lambda **kwargs: wsl_provider.wsl_exec(**kwargs)
        except:
            pass
        
        print(f"工具补全成功，当前工具数: {len(TOOL_FUNCTIONS)}")
        return True
    except Exception as e:
        print(f"工具补全失败: {e}")
        import traceback
        traceback.print_exc()
        return False
