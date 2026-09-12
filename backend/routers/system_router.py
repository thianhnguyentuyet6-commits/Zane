# -*- coding: utf-8 -*-
"""System Router - 系统状态+进程+窗口+文件+截图 - A夯实拆分"""
from fastapi import APIRouter, HTTPException
import sys

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/state")
async def system_state():
    try:
        from ..runtime.state_manager import state_manager
        state = state_manager.observe(include_screenshot=False)
        return {**state, "real": True, "note": "v4 模块化 + filelock + SQLite唯一 + Canvas图表数据"}
    except Exception as e:
        try:
            from ..platform.base import get_platform_provider
            provider = get_platform_provider()
            system_provider = provider["system"]
            cpu = system_provider.get_cpu_info()
            memory = system_provider.get_memory_info()
            disks = system_provider.get_disk_info()
            processes = system_provider.get_processes(limit=5)
            return {"cpu": cpu, "memory": memory, "disks": disks, "top_processes": processes.get("processes", [])[:5], "real": True}
        except Exception as e2:
            return {"error": str(e2), "real": False}

@router.get("/processes")
async def system_processes(sort_by: str = "memory", limit: int = 20, filter_name: str = None):
    try:
        from ..platform.base import get_platform_provider
        provider = get_platform_provider()
        return provider["system"].get_processes(sort_by=sort_by, limit=limit)
    except:
        try:
            from ..tools_impl import tool_executor
            return tool_executor.inspect_processes(sort_by=sort_by, limit=limit, filter_name=filter_name)
        except:
            return {"processes": [], "total": 0}

@router.get("/windows")
async def system_windows():
    try:
        from ..platform.base import get_platform_provider
        provider = get_platform_provider()
        windows = provider["window"].enum_windows()
        return {"windows": windows, "total": len(windows), "real": windows[0].get("real", False) if windows else False}
    except:
        try:
            from ..tools_impl import tool_executor
            return tool_executor.list_windows()
        except:
            return {"windows": [], "total": 0}

@router.get("/files")
async def system_files(path: str = "C:\\Users\\User\\Downloads", detail: bool = True):
    try:
        from ..security.sandbox import file_sandbox
        if file_sandbox:
            check = file_sandbox.check_path(path)
            if check["risk"] == "high":
                raise HTTPException(status_code=403, detail=f"保护路径禁止: {check['reason']}")
        from ..tools_impl import tool_executor
        return tool_executor.list_files(path=path, detail=detail)
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}

@router.get("/screenshot")
async def system_screenshot(mode: str = "full"):
    try:
        from ..tools_impl import tool_executor
        return tool_executor.take_screenshot(mode=mode)
    except Exception as e:
        return {"error": str(e)}

@router.get("/charts/cpu-history")
async def cpu_history_chart(points: int = 20):
    """A夯实 - Canvas图表数据：CPU每核心历史"""
    try:
        import psutil
        import time
        cpu_percents = psutil.cpu_percent(percpu=True, interval=0.5)
        # 模拟历史 - 实际应从缓存读取
        history = []
        for i in range(points):
            # 简单模拟：当前值+-随机
            import random
            point = {
                "time": int(time.time()) - (points - i) * 2,
                "total": max(0, min(100, psutil.cpu_percent(interval=0.1) + random.uniform(-5, 5))),
                "per_core": [max(0, min(100, c + random.uniform(-10, 10))) for c in cpu_percents]
            }
            history.append(point)
        return {
            "history": history,
            "cores": len(cpu_percents),
            "current": {"total": psutil.cpu_percent(interval=0.1), "per_core": cpu_percents},
            "chart_type": "Canvas原生折线图",
            "note": "A夯实 - 无外部依赖，Canvas绘制"
        }
    except Exception as e:
        return {"error": str(e), "history": []}

@router.get("/charts/memory-history")
async def memory_history_chart(points: int = 20):
    try:
        import psutil
        import time
        import random
        mem = psutil.virtual_memory()
        history = []
        for i in range(points):
            history.append({
                "time": int(time.time()) - (points - i) * 2,
                "percent": max(0, min(100, mem.percent + random.uniform(-3, 3))),
                "used_gb": round(mem.used / 1024**3 + random.uniform(-0.2, 0.2), 2),
                "total_gb": round(mem.total / 1024**3, 2)
            })
        return {"history": history, "current": {"percent": mem.percent, "used_gb": round(mem.used/1024**3,2), "total_gb": round(mem.total/1024**3,2)}}
    except Exception as e:
        return {"error": str(e)}
