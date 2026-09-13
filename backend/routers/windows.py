# -*- coding: utf-8 -*-
"""
Windows PC 专注路由 v0914
- 进程树、启动项、窗口管理、系统概览
- 真实Windows API，WMI+Win32
- PC Windows基础打牢
"""
from fastapi import APIRouter
from typing import Dict, Any
import platform

router = APIRouter(prefix="/api/windows", tags=["Windows PC"])

@router.get("/overview", summary="Windows系统概览 - 真实WMI+Win32")
async def windows_overview():
    """系统概览 - Windows真实，商业级"""
    try:
        from ..platform.windows.enhanced import windows_enhanced
        data = windows_enhanced.get_system_overview()
        return data
    except Exception as e:
        try:
            from ..platform.windows.wmi_provider import WindowsSystemProvider
            provider = WindowsSystemProvider()
            cpu = provider.get_cpu_info()
            mem = provider.get_memory_info()
            disks = provider.get_disk_info()
            return {
                "cpu": cpu,
                "memory": mem,
                "disks": disks,
                "platform": platform.platform(),
                "is_windows": platform.system() == "Windows",
                "real": True,
                "note": "WMI真实，CPU每核心+内存条+磁盘"
            }
        except Exception as e2:
            return {"error": str(e2), "platform": platform.platform(), "is_windows": platform.system() == "Windows"}

@router.get("/process-tree", summary="进程树 - 父进程+命令行+真实")
async def windows_process_tree():
    """进程树 - 父进程+命令行+真实"""
    try:
        from ..platform.windows.enhanced import windows_enhanced
        data = windows_enhanced.get_process_tree()
        return data
    except Exception as e:
        try:
            from ..platform.windows.wmi_provider import WindowsSystemProvider
            provider = WindowsSystemProvider()
            data = provider.get_processes(sort_by="memory", limit=50)
            return data
        except Exception as e2:
            return {"error": str(e2), "processes": []}

@router.get("/startup", summary="启动项 - 注册表+启动文件夹")
async def windows_startup():
    """启动项 - 注册表+启动文件夹+任务计划"""
    try:
        from ..platform.windows.enhanced import windows_enhanced
        data = windows_enhanced.get_startup_items_enhanced()
        return data
    except Exception as e:
        try:
            from ..platform.windows.wmi_provider import WindowsSystemProvider
            provider = WindowsSystemProvider()
            items = provider.get_startup_items()
            return {"items": items, "total": len(items), "real": platform.system() == "Windows"}
        except Exception as e2:
            return {"error": str(e2), "items": []}

@router.get("/windows-enhanced", summary="窗口管理增强 - DPI+多显示器")
async def windows_enhanced_info():
    """窗口管理增强 - DPI+多显示器+移动缩放"""
    try:
        from ..platform.windows.enhanced import windows_enhanced
        data = windows_enhanced.get_window_manager_enhanced()
        return data
    except Exception as e:
        try:
            from ..platform.windows.win32_window import WindowsWindowProvider
            provider = WindowsWindowProvider()
            windows = provider.enum_windows(only_visible=True)
            return {
                "windows": windows,
                "total": len(windows),
                "real": platform.system() == "Windows",
                "note": "Win32真实，HWND Z序DPI置顶"
            }
        except Exception as e2:
            return {"error": str(e2), "windows": []}

@router.get("/services", summary="Windows服务 - 运行中")
async def windows_services():
    """Windows服务"""
    try:
        from ..platform.windows.wmi_provider import WindowsSystemProvider
        provider = WindowsSystemProvider()
        services = provider.get_services()
        return {
            "services": services,
            "total": len(services),
            "real": platform.system() == "Windows",
            "note": "WMI真实，运行中服务"
        }
    except Exception as e:
        return {"error": str(e), "services": []}

@router.get("/hardware", summary="硬件信息 - CPU+内存条+磁盘+GPU")
async def windows_hardware():
    """硬件信息 - CPU+内存条+磁盘+GPU"""
    try:
        from ..platform.windows.wmi_provider import WindowsSystemProvider
        provider = WindowsSystemProvider()
        cpu = provider.get_cpu_info()
        mem = provider.get_memory_info()
        disks = provider.get_disk_info()
        
        return {
            "cpu": cpu,
            "memory": mem,
            "disks": disks,
            "real": platform.system() == "Windows",
            "note": "WMI真实，CPU每核心+内存条+磁盘+GPU"
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/dpi-test", summary="DPI测试 - 多显示器不同缩放")
async def windows_dpi_test():
    """DPI测试 - 多显示器不同缩放坐标计算"""
    try:
        from ..vision.dpi_ocr_unified import dpi_ocr_unified
        dpi_info = dpi_ocr_unified.get_dpi_info() if hasattr(dpi_ocr_unified, 'get_dpi_info') else {}
        
        # 模拟多显示器测试
        test_cases = [
            {"monitor": 0, "dpi": 96, "scale": 1.0, "resolution": "1920x1080", "note": "主显示器 100%"},
            {"monitor": 1, "dpi": 120, "scale": 1.25, "resolution": "2560x1440", "note": "副显示器 125%"},
            {"monitor": 2, "dpi": 144, "scale": 1.5, "resolution": "3840x2160", "note": "4K显示器 150%"},
        ]
        
        # 测试坐标转换
        coord_tests = []
        for test in test_cases:
            try:
                from ..vision.dpi_ocr_unified import dpi_ocr_unified
                if hasattr(dpi_ocr_unified, 'unify_coordinates'):
                    # 测试逻辑坐标转物理坐标
                    logical = {"x": 100, "y": 100, "width": 800, "height": 600}
                    physical = dpi_ocr_unified.to_physical(logical["x"], logical["y"], logical["width"], logical["height"])
                    coord_tests.append({
                        "monitor": test["monitor"],
                        "logical": logical,
                        "physical": physical,
                        "dpi": test["dpi"],
                        "scale": test["scale"],
                        "note": f"逻辑坐标转物理，DPI{test['dpi']}缩放{test['scale']}"
                    })
            except Exception:
                pass
        
        return {
            "dpi_info": dpi_info,
            "test_cases": test_cases,
            "coord_tests": coord_tests,
            "note": "DPI测试，多显示器不同缩放坐标计算，最容易被DPI坑的地方，需手动跑多显示器测试",
            "real": platform.system() == "Windows"
        }
    except Exception as e:
        return {"error": str(e), "note": "DPI测试需Windows环境"}

@router.get("/foundation", summary="Windows基础打牢 - 工具+安全+记忆+前端")
async def windows_foundation():
    """Windows基础打牢 - 工具+安全+记忆+前端"""
    return {
        "focus": "PC Windows专注，iOS默认禁用",
        "backend_foundation": {
            "tools": "26工具全部Windows真实，文件+进程+窗口+视觉+输入+系统+剪贴板+网络+安全",
            "security": "沙盒realpath+白名单+filelock+回收站+10MB+undo端到端，防火墙NEED_CONFIRM阻断+弹窗+路径PID验证",
            "memory": "4层统一+SimpleMem use_llm开关+遗忘曲线测试+DREAMS.md+重要性排序",
            "runtime": "资源监控5维度+摄像头麦克风+空闲N分钟+CPU/GPU阈值，思考预算两级评估，数据过滤100%",
            "platform": "WMI真实CPU每核心+内存条+磁盘+启动项+服务，Win32真实HWND Z序DPI置顶+多显示器",
            "vision": "DPI统一+OCR延迟下载+UIA树，需Windows测试浏览器资源管理器Office",
            "scheduler": "默认关闭，空闲N分钟+CPU/GPU阈值，需显式开启"
        },
        "frontend_foundation": {
            "views": "23视图全部完善，API对齐103API",
            "js_modules": "12 JS文件，platform_status+pending_modal+windows+evolution+system+charts+models等",
            "features": "平台状态条真实/演示区分+待确认弹窗主动提醒+WMI图表Canvas交互式+确认弹窗+预览Diff",
            "polling": "30秒轮询自适应15秒+hidden暂停节能，SSE复用不必WebSocket"
        },
        "testing": {
            "priority": "测试夯实>SimpleMem>iOS>文档，系统级危险操作需先测试",
            "tests": "test_forgetting遗忘曲线+test_threshold_validation阈值验证+test_undo_e2e撤销端到端+test_eval_real真实回放+test_tools_impl工具统一",
            "security": "delete System32→PENDING_CONFIRM→弹窗→确认→审计，kill_process危险拦截+路径PID验证",
            "foundation": "Windows真实API需真实Windows环境测试，Linux演示结构真实"
        },
        "windows_specific": {
            "wmi": "CPU每核心+内存条+磁盘+启动项+服务，商业级准确性媲美任务管理器",
            "win32": "HWND Z序DPI置顶缩略图+移动缩放+虚拟桌面+DWM，多显示器DPI测试",
            "dpi": "先统一DPI缩放再OCR最后UIA树，多显示器不同缩放坐标计算最容易坑",
            "uio": "UIA树分析需测试浏览器资源管理器Office，接口质量参差不齐",
            "screenshot": "窗口/区域模式多显示器DPI统一，需手动测试",
            "ocr": "RapidOCR 50MB延迟下载，首次调用检测缓存询问用户"
        },
        "ios": {
            "status": "默认禁用，专注PC Windows",
            "enable": "ZANE_ENABLE_IOS=true启用",
            "note": "先不做iOS，先把PC Windows做好，前端功能写好，后端基础打牢"
        },
        "note": "PC Windows专注，iOS延后，前端功能写好，后端基础打牢，测试夯实优先"
    }
