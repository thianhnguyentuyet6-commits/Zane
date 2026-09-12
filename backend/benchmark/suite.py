# -*- coding: utf-8 -*-
"""
基准测试套件 - 可复现评估
覆盖进程、窗口、文件、剪贴板、应用启动、UI交互、截图、OCR、视觉定位、多步任务、失败恢复、模糊指令
每个任务有明确成功标准，可重放
"""
import time
import json
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class BenchmarkTask:
    id: str
    category: str  # process, window, file, clipboard, app, ui, screenshot, ocr, multi_step, failure_recovery, ambiguous
    title: str
    description: str
    instruction: str
    success_criteria: List[str]  # 明确成功标准
    required_tools: List[str]
    timeout: int
    risk_level: str

# 基准任务 - 可复现
BENCHMARK_TASKS: List[BenchmarkTask] = [
    # 进程管理
    BenchmarkTask(
        id="proc_001",
        category="process",
        title="列出内存占用前5进程",
        description="按内存排序进程",
        instruction="看看现在什么程序占内存最多",
        success_criteria=["返回进程列表", "按内存降序", "包含内存MB", "总数>0"],
        required_tools=["inspect_processes"],
        timeout=10,
        risk_level="low"
    ),
    BenchmarkTask(
        id="proc_002",
        category="process",
        title="启动应用并验证",
        description="启动记事本并验证进程存在",
        instruction="帮我打开记事本",
        success_criteria=["API返回success", "进程存在", "PID有效"],
        required_tools=["launch_application", "inspect_processes"],
        timeout=15,
        risk_level="medium"
    ),
    # 窗口管理
    BenchmarkTask(
        id="win_001",
        category="window",
        title="枚举窗口",
        description="获取所有可见窗口",
        instruction="看看现在开了哪些窗口",
        success_criteria=["返回窗口列表", "含HWND", "含标题", "总数>0"],
        required_tools=["list_windows"],
        timeout=10,
        risk_level="low"
    ),
    BenchmarkTask(
        id="win_002",
        category="window",
        title="聚焦窗口",
        description="将窗口切到前台",
        instruction="把Chrome窗口切到前台",
        success_criteria=["API返回success", "前台窗口为目标"],
        required_tools=["list_windows", "focus_window"],
        timeout=10,
        risk_level="medium"
    ),
    # 文件操作
    BenchmarkTask(
        id="file_001",
        category="file",
        title="列出文件夹",
        description="列出下载文件夹",
        instruction="列出下载文件夹的文件",
        success_criteria=["返回文件列表", "含文件名", "含是否文件夹"],
        required_tools=["list_files"],
        timeout=10,
        risk_level="low"
    ),
    BenchmarkTask(
        id="file_002",
        category="file",
        title="创建文件夹",
        description="创建新文件夹，可撤销",
        instruction="在沙盒创建一个测试文件夹",
        success_criteria=["API返回success", "文件夹存在", "可撤销"],
        required_tools=["create_folder"],
        timeout=10,
        risk_level="medium"
    ),
    # 视觉
    BenchmarkTask(
        id="vision_001",
        category="screenshot",
        title="全屏截图",
        description="截取全屏",
        instruction="截图给我看看桌面",
        success_criteria=["返回图片路径", "文件存在", "宽高>0"],
        required_tools=["take_screenshot"],
        timeout=10,
        risk_level="low"
    ),
    BenchmarkTask(
        id="vision_002",
        category="ocr",
        title="OCR识别",
        description="识别屏幕文字",
        instruction="识别屏幕上的文字",
        success_criteria=["返回文字", "含文字块", "含坐标"],
        required_tools=["take_screenshot", "ocr_screenshot"],
        timeout=15,
        risk_level="low"
    ),
    # 多步任务
    BenchmarkTask(
        id="multi_001",
        category="multi_step",
        title="文件整理",
        description="列出下载文件夹，按类型创建文件夹",
        instruction="整理下载文件夹，按图片、文档分类",
        success_criteria=["列出文件", "创建分类文件夹", "验证文件夹存在"],
        required_tools=["list_files", "create_folder"],
        timeout=20,
        risk_level="medium"
    ),
    # 失败恢复
    BenchmarkTask(
        id="fail_001",
        category="failure_recovery",
        title="应用未安装恢复",
        description="尝试启动不存在应用，恢复",
        instruction="打开不存在的应用 xyz123",
        success_criteria=["识别失败", "尝试替代", "不崩溃", "返回错误信息"],
        required_tools=["launch_application"],
        timeout=15,
        risk_level="low"
    ),
    BenchmarkTask(
        id="fail_002",
        category="failure_recovery",
        title="文件不存在恢复",
        description="读取不存在文件，恢复",
        instruction="读取 C:\\不存在的文件.txt",
        success_criteria=["识别文件不存在", "尝试列出父目录", "返回明确错误"],
        required_tools=["read_file", "list_files"],
        timeout=15,
        risk_level="low"
    ),
    # 模糊指令
    BenchmarkTask(
        id="amb_001",
        category="ambiguous",
        title="模糊指令",
        description="处理歧义指令",
        instruction="把那个窗口关掉",
        success_criteria=["询问具体哪个窗口", "或列出窗口让用户选择", "不随意关闭"],
        required_tools=["list_windows"],
        timeout=15,
        risk_level="low"
    ),
]

class BenchmarkSuite:
    """基准套件 - 可复现评估"""
    
    def __init__(self):
        self.tasks = BENCHMARK_TASKS
        self.results = []

    def list_tasks(self, category: str = None) -> List[Dict]:
        tasks = self.tasks
        if category:
            tasks = [t for t in tasks if t.category == category]
        return [
            {
                "id": t.id,
                "category": t.category,
                "title": t.title,
                "instruction": t.instruction,
                "success_criteria": t.success_criteria,
                "required_tools": t.required_tools,
                "risk_level": t.risk_level
            }
            for t in tasks
        ]

    def get_stats(self) -> Dict:
        categories = {}
        for task in self.tasks:
            categories[task.category] = categories.get(task.category, 0) + 1
        
        return {
            "total": len(self.tasks),
            "by_category": categories,
            "by_risk": {
                "low": len([t for t in self.tasks if t.risk_level == "low"]),
                "medium": len([t for t in self.tasks if t.risk_level == "medium"]),
                "high": len([t for t in self.tasks if t.risk_level == "high"])
            }
        }

    async def run_task(self, task_id: str, agent_runtime) -> Dict:
        """运行单个基准任务"""
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            return {"error": f"任务未找到: {task_id}"}
        
        start = time.time()
        try:
            # 执行任务
            result = await agent_runtime.execute_task(task.instruction)
            
            # 验证成功标准
            verification = self._verify_task(task, result)
            
            latency = time.time() - start
            
            return {
                "task_id": task_id,
                "title": task.title,
                "instruction": task.instruction,
                "success": verification["success"],
                "success_criteria": task.success_criteria,
                "verification": verification,
                "latency": round(latency, 2),
                "tools_used": result.get("tools_used", []),
                "steps": len(result.get("steps", [])),
                "real": True
            }
        except Exception as e:
            return {
                "task_id": task_id,
                "title": task.title,
                "success": False,
                "error": str(e),
                "latency": round(time.time() - start, 2)
            }

    def _verify_task(self, task: BenchmarkTask, result: Dict) -> Dict:
        """验证任务是否满足成功标准"""
        # 简化验证：检查工具是否调用，是否有错误
        tools_used = result.get("tools_used", [])
        has_error = any("error" in str(s.get("content", "")).lower() for s in result.get("steps", []))
        
        # 检查必需工具是否都调用
        required_called = all(tool in tools_used for tool in task.required_tools)
        
        # 成功标准：必需工具调用 + 无错误 + 有最终报告
        success = required_called and not has_error and result.get("final_report")
        
        return {
            "success": success,
            "required_called": required_called,
            "has_error": has_error,
            "has_report": bool(result.get("final_report")),
            "criteria": task.success_criteria,
            "reason": "满足" if success else f"必需工具: {required_called}, 无错误: {not has_error}"
        }

    async def run_all(self, agent_runtime, category: str = None) -> Dict:
        """运行所有基准任务"""
        tasks = self.tasks
        if category:
            tasks = [t for t in tasks if t.category == category]
        
        results = []
        for task in tasks:
            result = await self.run_task(task.id, agent_runtime)
            results.append(result)
        
        # 统计
        total = len(results)
        success = sum(1 for r in results if r.get("success"))
        avg_latency = sum(r.get("latency", 0) for r in results) / total if total else 0
        avg_tools = sum(len(r.get("tools_used", [])) for r in results) / total if total else 0
        
        return {
            "total": total,
            "success": success,
            "success_rate": round(success / total, 2) if total else 0,
            "avg_latency": round(avg_latency, 2),
            "avg_tools": round(avg_tools, 1),
            "results": results,
            "by_category": self._group_by_category(results)
        }

    def _group_by_category(self, results: List[Dict]) -> Dict:
        grouped = {}
        for r in results:
            task = next((t for t in self.tasks if t.id == r["task_id"]), None)
            if task:
                cat = task.category
                if cat not in grouped:
                    grouped[cat] = {"total": 0, "success": 0}
                grouped[cat]["total"] += 1
                if r.get("success"):
                    grouped[cat]["success"] += 1
        
        for cat in grouped:
            grouped[cat]["rate"] = round(grouped[cat]["success"] / grouped[cat]["total"], 2) if grouped[cat]["total"] else 0
        
        return grouped

benchmark_suite = BenchmarkSuite()
