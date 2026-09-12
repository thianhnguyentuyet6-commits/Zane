# -*- coding: utf-8 -*-
"""
自主调度器 v3 - 资源感知+凌晨2点+空闲30分
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class SchedulerV3:
    """自主调度器 v3"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.config_path = self.base_dir / "config" / "evolution_schedule.json"
        self.logs_dir = self.base_dir / "data" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.logs_dir / "scheduler.log"
        
        self.config = self._load_config()
        self.scheduler = None
    
    def _load_config(self) -> Dict:
        default = {
            "enabled": True,
            "train_time": "02:00",
            "check_interval_minutes": 30,
            "cpu_threshold": 20,
            "memory_threshold": 70,
            "vram_threshold_gb": 18,
            "idle_minutes": 30,
            "require_plugged": False,
            "pause_on_game": True,
            "pause_on_meeting_fullscreen": True,
            "min_samples": 50,
            "auto_trigger": True
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default.update(loaded)
            except Exception:
                pass
        
        # 保存默认
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
        return default
    
    def _log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
            print(log_line.strip())
        except Exception:
            print(log_line.strip())
    
    def check_ready(self) -> Dict[str, Any]:
        """检查是否准备好训练"""
        # 资源监控
        try:
            from ..runtime.resource_monitor import resource_monitor
            resources = resource_monitor.get_all()
        except Exception as e:
            resources = {"can_train": False, "error": str(e)}
        
        # 数据统计
        try:
            from ..memory.data_flywheel_v3 import data_flywheel_v3
            stats = data_flywheel_v3.get_training_stats()
        except Exception:
            try:
                from ..memory.data_flywheel import data_flywheel
                stats = data_flywheel.get_training_stats()
            except Exception:
                stats = {"sft_samples": 0, "dpo_samples": 0}
        
        ready = stats.get("sft_samples", 0) >= self.config["min_samples"]
        can_train = resources.get("can_train", False)
        
        return {
            "ready": ready and can_train,
            "stats": stats,
            "resources": resources,
            "config": self.config,
            "reason": f"样本 {stats.get('sft_samples',0)}/{self.config['min_samples']} + 资源可训练 {can_train}",
            "next_check": f"{self.config['check_interval_minutes']}分钟后"
        }
    
    def start_scheduler(self):
        """启动调度器"""
        if not self.config["enabled"]:
            self._log("调度器已禁用")
            return
        
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            from apscheduler.triggers.interval import IntervalTrigger
            
            self.scheduler = BackgroundScheduler()
            
            # 凌晨2点训练
            train_hour, train_minute = map(int, self.config["train_time"].split(":"))
            self.scheduler.add_job(
                self._job_nightly_train,
                CronTrigger(hour=train_hour, minute=train_minute),
                id="nightly_train",
                name="凌晨训练"
            )
            
            # 每30分钟检查空闲
            self.scheduler.add_job(
                self._job_idle_check,
                IntervalTrigger(minutes=self.config["check_interval_minutes"]),
                id="idle_check",
                name="空闲检查"
            )
            
            # 梦境整理 3点
            self.scheduler.add_job(
                self._job_dreaming,
                CronTrigger(hour=3, minute=0),
                id="dreaming",
                name="梦境整理"
            )
            
            self.scheduler.start()
            self._log(f"✅ 调度器已启动：凌晨{self.config['train_time']}训练 + 每{self.config['check_interval_minutes']}分空闲检查 + 3点梦境")
            
            return True
        except ImportError as e:
            self._log(f"❌ APScheduler未安装: {e}")
            return False
        except Exception as e:
            self._log(f"❌ 调度器启动失败: {e}")
            return False
    
    def stop_scheduler(self):
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            self._log("⏹️ 调度器已停止")
    
    def _job_nightly_train(self):
        """凌晨训练任务"""
        self._log("🌙 凌晨训练任务触发")
        check = self.check_ready()
        
        if not check["ready"]:
            self._log(f"   未准备好: {check['reason']}")
            return
        
        self._log(f"   准备好: {check['reason']}")
        self._log("   开始进化...")
        
        try:
            import asyncio
            from ..learning.evolution_engine_v25 import evolution_engine_v25
            
            # 异步执行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(evolution_engine_v25.start_evolution(manual=False))
            loop.close()
            
            if result["success"]:
                self._log(f"   ✅ 进化成功: {result['message']}")
            else:
                self._log(f"   ❌ 进化失败: {result['message']}")
        except Exception as e:
            self._log(f"   ❌ 进化异常: {e}")
            import traceback
            traceback.print_exc()
    
    def _job_idle_check(self):
        """空闲检查任务"""
        check = self.check_ready()
        
        if check["ready"]:
            self._log(f"💤 空闲检查：准备好训练 {check['reason']}")
            # 空闲时也可触发，但频率限制
            # 这里仅记录，不自动训练，避免打扰，凌晨为主
        else:
            # 仅在调试时记录
            pass
    
    def _job_dreaming(self):
        """梦境整理任务"""
        self._log("🌙 梦境整理任务触发")
        
        try:
            import asyncio
            from ..learning.evolution_engine_v25 import evolution_engine_v25
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(evolution_engine_v25.start_dreaming())
            loop.close()
            
            if result["success"]:
                self._log(f"   ✅ 梦境完成: {result['message']}")
            else:
                self._log(f"   ❌ 梦境失败: {result['message']}")
        except Exception as e:
            self._log(f"   ❌ 梦境异常: {e}")

# 全局
scheduler_v3 = SchedulerV3()
