# -*- coding: utf-8 -*-
"""
Autonomous Optimizer - 闲暇时间自主优化
核心任务：自己上开源网站和网络查询知识，优化自己，完善Skill库

触发条件：CPU<20% + 空闲30分钟 + 凌晨2点定时
能力：GitHub趋势+Arxiv+网络搜索+失败分析+Skill提取适配
"""

import os
import time
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime

class AutonomousOptimizer:
    """自主优化器 - 闲暇时间任务"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "autonomous")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 开源知识源
        self.sources = {
            "github_trending": "https://github.com/trending/python",
            "github_topics": [
                "https://github.com/topics/windows-automation",
                "https://github.com/topics/desktop-assistant",
                "https://github.com/topics/file-management",
                "https://github.com/topics/autohotkey"
            ],
            "arxiv": "https://arxiv.org/list/cs.AI/recent",
            "search_queries": [
                "Windows automation WMI UIA Python 2024",
                "PowerToys FancyZones implementation",
                "Raycast clipboard history Python",
                "AutoHotkey file organization script",
                "desktop assistant skill library"
            ]
        }
        
        # 候选Skill库 - 从开源提取
        self.candidate_skills = [
            {
                "name": "window_layout_fancyzones",
                "description": "窗口布局FancyZones，一键将窗口按预设布局排列",
                "source": "microsoft/PowerToys",
                "trigger": ["窗口布局", "排列窗口", "分屏"],
                "tools": ["list_windows", "focus_window", "move_window"],
                "verification": "检查所有窗口矩形符合布局"
            },
            {
                "name": "clipboard_history",
                "description": "剪贴板历史，记录最近20条，搜索粘贴",
                "source": "Raycast",
                "trigger": ["剪贴板历史", "之前复制的", "粘贴历史"],
                "tools": ["get_clipboard", "set_clipboard"],
                "verification": "剪贴板内容匹配"
            },
            {
                "name": "auto_organize_downloads",
                "description": "监控下载文件夹，新文件自动分类",
                "source": "File Juggler",
                "trigger": ["自动整理", "监控下载"],
                "tools": ["list_files", "create_folder", "move_file"],
                "verification": "新文件被移动到分类"
            },
            {
                "name": "quick_file_search",
                "description": "快速文件搜索，比list_files更快，类似Everything",
                "source": "Everything",
                "trigger": ["快速搜索文件", "找文件", "搜索文件名"],
                "tools": ["list_files", "web_search_real"],
                "verification": "返回文件存在"
            },
            {
                "name": "quick_launch",
                "description": "快速启动，输入app名启动，类似Wox",
                "source": "Wox",
                "trigger": ["快速启动", "打开应用", "启动程序"],
                "tools": ["launch_application", "list_windows"],
                "verification": "进程存在+窗口出现"
            },
            {
                "name": "system_cleanup",
                "description": "系统清理，清理临时文件+回收站+大文件分析",
                "source": "BleachBit",
                "trigger": ["清理系统", "C盘清理", "清理垃圾"],
                "tools": ["scan_large_files", "list_files", "delete_file", "get_system_state"],
                "verification": "磁盘空间增加"
            },
            {
                "name": "startup_manager",
                "description": "启动项管理，查看禁用启动项",
                "source": "Autoruns",
                "trigger": ["启动项", "开机启动", "管理启动"],
                "tools": ["get_system_state", "security_scan"],
                "verification": "返回启动项列表"
            }
        ]
    
    def is_idle(self) -> Dict:
        """检查是否空闲"""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            # 检查最后任务时间
            last_task = self._get_last_task_time()
            idle_minutes = (time.time() - last_task) / 60 if last_task else 999
            
            # 检查当前是否有用户任务
            has_active_task = self._has_active_task()
            
            return {
                "idle": cpu < 20 and idle_minutes > 30 and not has_active_task,
                "cpu": cpu,
                "idle_minutes": int(idle_minutes),
                "has_active_task": has_active_task,
                "reason": f"CPU {cpu}% 空闲 {int(idle_minutes)}分钟 活跃任务:{has_active_task}"
            }
        except Exception as e:
            return {"idle": False, "error": str(e)}
    
    def _get_last_task_time(self) -> float:
        try:
            from .task_trace import trace_logger
            traces = trace_logger.list_traces(limit=1)
            if traces:
                return traces[0].get("start_time", 0)
        except:
            pass
        # 回退：检查data/traces最新文件
        try:
            traces_dir = os.path.join(os.path.dirname(__file__), "..", "data", "traces")
            if os.path.exists(traces_dir):
                files = [os.path.join(traces_dir, f) for f in os.listdir(traces_dir) if f.endswith('.json')]
                if files:
                    latest = max(files, key=os.path.getmtime)
                    return os.path.getmtime(latest)
        except:
            pass
        return 0
    
    def _has_active_task(self) -> bool:
        # 简单：检查是否有最近1分钟的任务
        last = self._get_last_task_time()
        return (time.time() - last) < 60
    
    async def query_open_source(self) -> Dict:
        """查询开源知识 - GitHub趋势+网络搜索"""
        results = {
            "github_repos": [],
            "search_results": [],
            "timestamp": time.time()
        }
        
        try:
            from .tools.network.web_search_real import web_search_real
            
            # 查询GitHub趋势
            for query in self.sources["search_queries"][:3]:
                try:
                    search_res = await web_search_real.search(query, count=3)
                    results["search_results"].extend(search_res.get("results", []))
                    # 提取GitHub仓库
                    for r in search_res.get("results", []):
                        if "github.com" in r.get("url", ""):
                            results["github_repos"].append(r)
                    await asyncio.sleep(1)  # 避免限流
                except Exception as e:
                    print(f"搜索失败 {query}: {e}")
        
        except Exception as e:
            print(f"查询开源失败: {e}")
        
        # 保存
        save_path = os.path.join(self.data_dir, f"open_source_{int(time.time())}.json")
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return results
    
    async def analyze_failures(self) -> List[Dict]:
        """分析失败轨迹，生成改进"""
        improvements = []
        
        try:
            from .task_trace import trace_logger
            from .runtime.recovery_manager import recovery_manager
            
            traces = trace_logger.list_traces(limit=20)
            failed = [t for t in traces if not t.get("success")]
            
            for trace_info in failed[:3]:
                task_id = trace_info.get("task_id")
                if not task_id:
                    continue
                
                trace = trace_logger.get_trace(task_id)
                if not trace:
                    continue
                
                failures = trace.get("failures", [])
                for fail in failures:
                    error = fail.get("error", "")
                    tool = fail.get("tool", "")
                    
                    # 分类
                    failure_type = recovery_manager.classify_failure(tool, error, {})
                    
                    # 生成改进建议
                    if failure_type.value == "not_found":
                        improvements.append({
                            "type": "skill",
                            "reason": f"工具 {tool} 文件不存在错误，需增加路径搜索",
                            "suggestion": f"在 {tool} 前增加 list_files 搜索同名文件",
                            "trace_id": task_id
                        })
                    elif failure_type.value == "permission":
                        improvements.append({
                            "type": "policy",
                            "reason": f"工具 {tool} 权限拒绝，需调整策略或路径",
                            "suggestion": f"将路径移到沙盒 {os.path.expanduser('~/ZaneSandbox')}",
                            "trace_id": task_id
                        })
        
        except Exception as e:
            print(f"分析失败轨迹失败: {e}")
        
        return improvements
    
    async def extract_and_adapt_skill(self, repo_info: Dict) -> Dict:
        """从开源仓库提取Skill并适配"""
        # 简单实现：基于候选库
        # 实际应克隆仓库分析README和代码
        
        # 选择一个候选
        import random
        candidate = random.choice(self.candidate_skills)
        
        # 适配：加沙盒+撤销+验证+契约+中文
        adapted = {
            "name": candidate["name"],
            "description": candidate["description"] + f" (来源: {candidate['source']})",
            "trigger_conditions": candidate["trigger"],
            "required_tools": candidate["tools"],
            "procedure": [
                {"step": 1, "tool": candidate["tools"][0], "params": {}, "verification": "返回非空"},
                {"step": 2, "tool": candidate["tools"][1] if len(candidate["tools"]) > 1 else candidate["tools"][0], "params": {}, "verification": candidate["verification"]}
            ],
            "preconditions": ["路径在沙盒白名单", "非保护路径"],
            "verification_rules": [candidate["verification"], "区分API完成vs真实成功"],
            "failure_recovery": {"retry": 2, "fallback": "ask_user"},
            "tags": ["开源", "自动", candidate["source"]]
        }
        
        return adapted
    
    async def run_idle_task(self) -> Dict:
        """执行闲暇任务 - 完整流程"""
        print(f"[{datetime.now()}] 自主优化任务开始 - 检查空闲...")
        
        idle_check = self.is_idle()
        if not idle_check.get("idle"):
            print(f"非空闲: {idle_check.get('reason')}")
            return {"status": "not_idle", "check": idle_check}
        
        print(f"空闲确认: {idle_check['reason']}，开始优化...")
        
        results = {
            "start_time": time.time(),
            "idle_check": idle_check,
            "open_source": {},
            "failures": [],
            "new_skills": [],
            "dreaming": {}
        }
        
        # 1. 查询开源
        print("1. 查询开源知识...")
        open_source = await self.query_open_source()
        results["open_source"] = {
            "repos": len(open_source.get("github_repos", [])),
            "search": len(open_source.get("search_results", []))
        }
        
        # 2. 分析失败
        print("2. 分析失败轨迹...")
        failures = await self.analyze_failures()
        results["failures"] = failures
        
        # 3. 提取适配Skill
        print("3. 提取适配Skill...")
        if open_source.get("github_repos"):
            for repo in open_source["github_repos"][:1]:
                try:
                    skill = await self.extract_and_adapt_skill(repo)
                    # 创建技能
                    try:
                        from .runtime.skill_manager import skill_manager
                        created = skill_manager.create_skill(**skill)
                        results["new_skills"].append(created.name if hasattr(created, 'name') else skill["name"])
                        print(f"新技能: {skill['name']}")
                    except Exception as e:
                        print(f"创建技能失败: {e}")
                except Exception as e:
                    print(f"提取技能失败: {e}")
        
        # 4. 使用候选库补充
        if len(results["new_skills"]) == 0:
            # 从候选库随机选一个
            try:
                from .runtime.skill_manager import skill_manager
                import random
                candidate = random.choice(self.candidate_skills)
                # 检查是否已存在
                if not skill_manager.get_skill(candidate["name"]):
                    adapted = await self.extract_and_adapt_skill({"url": f"https://github.com/{candidate['source']}"})
                    created = skill_manager.create_skill(**adapted)
                    results["new_skills"].append(candidate["name"])
                    print(f"从候选库添加: {candidate['name']}")
            except Exception as e:
                print(f"候选库添加失败: {e}")
        
        # 5. 梦境
        print("4. 梦境整理...")
        try:
            from .runtime.dreaming import dreaming_system
            dreaming_res = dreaming_system.light_phase(days=7)
            results["dreaming"] = dreaming_res
            # REM
            try:
                rem_res = dreaming_system.rem_phase()
                results["dreaming"]["rem"] = rem_res
            except:
                pass
        except Exception as e:
            print(f"梦境失败: {e}")
            results["dreaming"] = {"error": str(e)}
        
        results["end_time"] = time.time()
        results["duration"] = int(results["end_time"] - results["start_time"])
        results["status"] = "completed"
        
        # 保存报告
        report_path = os.path.join(self.data_dir, f"autonomous_report_{int(time.time())}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"自主优化完成: {results}")
        return results
    
    def get_status(self) -> Dict:
        """获取状态"""
        try:
            reports = [f for f in os.listdir(self.data_dir) if f.startswith("autonomous_report_")]
            latest = None
            if reports:
                latest_path = os.path.join(self.data_dir, sorted(reports)[-1])
                with open(latest_path, 'r', encoding='utf-8') as f:
                    latest = json.load(f)
            
            return {
                "idle_check": self.is_idle(),
                "candidate_skills": len(self.candidate_skills),
                "reports": len(reports),
                "latest_report": latest,
                "sources": self.sources["search_queries"]
            }
        except Exception as e:
            return {"error": str(e)}

# 全局
autonomous_optimizer = AutonomousOptimizer()
