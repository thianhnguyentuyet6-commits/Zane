# -*- coding: utf-8 -*-
"""
自主调度器 v0914 - 用户空闲N分钟+CPU/GPU阈值，默认关闭自动微调
- 修复：凌晨2点固定窗口 -> 空闲检测+资源阈值，更贴近不打扰用户初衷
- 允许用户在配置里关闭自动微调，默认关闭，风险较高
- 支持：环境变量ZANE_AUTO_EVOLVE=false关闭
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta


class SchedulerV0914:
    """自主调度器 v0914 - 默认关闭，空闲检测"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.config_path = self.base_dir / "config" / "evolution_schedule.json"
        self.logs_dir = self.base_dir / "data" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.logs_dir / "scheduler.log"
        self.state_path = self.base_dir / "data" / "scheduler_state.json"
        
        self.config = self._load_config()
        self.scheduler = None
        self.last_user_activity = datetime.now()
        self.last_train_time = None
    
    def _load_config(self) -> Dict:
        # v0914 默认关闭自动微调，风险较高，需用户显式开启
        default = {
            "enabled": False,  # 默认关闭！用户需显式开启
            "auto_evolve": False,  # 兼容旧配置，默认关闭
            "idle_minutes": 30,  # 用户空闲N分钟后可训练
            "cpu_threshold": 20,  # CPU利用率低于阈值
            "memory_threshold": 70,
            "vram_threshold_gb": 18,
            "gpu_util_threshold": 30,  # GPU利用率低于阈值
            "check_interval_minutes": 15,  # 检查间隔15分钟
            "min_samples": 50,
            "require_plugged": True,  # 默认要求插电
            "pause_on_game": True,
            "pause_on_meeting": True,
            "pause_on_ios_viewing": True,
            "allow_nightly": False,  # 是否允许凌晨训练，默认不允许
            "nightly_time": "02:00",  # 如果允许，凌晨时间
            "max_train_per_day": 1,  # 每天最多训练次数
            "cooldown_hours": 6,  # 训练冷却时间
            "note": "默认关闭自动微调，需用户在config/evolution_schedule.json中设置enabled=true显式开启，或设置环境变量ZANE_AUTO_EVOLVE=true"
        }
        
        # 环境变量覆盖 - 最高优先级
        env_enabled = os.getenv("ZANE_AUTO_EVOLVE", "").lower()
        if env_enabled in ("true", "1", "yes"):
            default["enabled"] = True
        elif env_enabled in ("false", "0", "no"):
            default["enabled"] = False
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default.update(loaded)
                    # 兼容旧配置
                    if "enabled" not in loaded and "auto_evolve" in loaded:
                        default["enabled"] = loaded["auto_evolve"]
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
    
    def _load_state(self) -> Dict:
        if self.state_path.exists():
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"last_train": None, "train_count_today": 0, "last_date": None}
    
    def _save_state(self, state: Dict):
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception:
            pass
        print(log_line.strip())
    
    def update_user_activity(self):
        """更新用户活动时间 - 前端调用"""
        self.last_user_activity = datetime.now()
    
    def check_idle(self) -> Dict[str, Any]:
        """检查用户是否空闲N分钟"""
        idle_duration = datetime.now() - self.last_user_activity
        idle_minutes = idle_duration.total_seconds() / 60
        is_idle = idle_minutes >= self.config["idle_minutes"]
        
        return {
            "is_idle": is_idle,
            "idle_minutes": round(idle_minutes, 1),
            "required_idle": self.config["idle_minutes"],
            "last_activity": self.last_user_activity.isoformat(),
            "reason": f"空闲 {idle_minutes:.1f}分钟 / 需 {self.config['idle_minutes']}分钟"
        }
    
    def check_ready(self) -> Dict[str, Any]:
        """检查是否准备好训练 - 空闲N分钟+CPU/GPU阈值组合"""
        # 检查是否启用
        if not self.config.get("enabled", False):
            return {
                "ready": False,
                "reason": "自动微调已禁用（默认关闭，需在config/evolution_schedule.json设置enabled=true或环境变量ZANE_AUTO_EVOLVE=true显式开启）",
                "enabled": False,
                "config": self.config
            }
        
        # 检查冷却时间
        state = self._load_state()
        if state.get("last_train"):
            try:
                last_train = datetime.fromisoformat(state["last_train"])
                cooldown = timedelta(hours=self.config.get("cooldown_hours", 6))
                if datetime.now() - last_train < cooldown:
                    remaining = cooldown - (datetime.now() - last_train)
                    return {
                        "ready": False,
                        "reason": f"冷却中，剩余 {remaining.total_seconds()/3600:.1f}小时，配置cooldown_hours={self.config['cooldown_hours']}",
                        "last_train": state["last_train"],
                        "cooldown_remaining": str(remaining)
                    }
            except Exception:
                pass
        
        # 检查每天次数限制
        today = datetime.now().date().isoformat()
        if state.get("last_date") == today:
            if state.get("train_count_today", 0) >= self.config.get("max_train_per_day", 1):
                return {
                    "ready": False,
                    "reason": f"今日训练次数已达上限 {self.config['max_train_per_day']}次",
                    "train_count_today": state["train_count_today"]
                }
        
        # 资源监控
        try:
            from ..runtime.resource_monitor import resource_monitor
            resources = resource_monitor.get_all()
        except Exception as e:
            resources = {"can_train": False, "error": str(e), "reason": str(e)}
        
        # 空闲检测
        idle_check = self.check_idle()
        
        # 数据统计
        try:
            from ..memory.data_flywheel import data_flywheel
            stats = data_flywheel.get_training_stats()
        except Exception:
            try:
                from ..memory.data_flywheel_v3 import data_flywheel_v3
                stats = data_flywheel_v3.get_training_stats()
            except Exception:
                stats = {"sft_samples": 0, "dpo_samples": 0}
        
        ready_samples = stats.get("sft_samples", 0) >= self.config["min_samples"]
        can_train_resources = resources.get("can_train", False)
        is_idle = idle_check["is_idle"]
        
        # 组合条件：样本足够 + 资源可训练 + 用户空闲
        ready = ready_samples and can_train_resources and is_idle
        
        reasons = []
        if not ready_samples:
            reasons.append(f"样本不足 {stats.get('sft_samples',0)}/{self.config['min_samples']}")
        if not can_train_resources:
            reasons.append(f"资源不可训练: {resources.get('reason','未知')}")
        if not is_idle:
            reasons.append(f"用户未空闲: {idle_check['reason']}")
        
        if ready:
            reason = f"✅ 准备好: 样本 {stats.get('sft_samples',0)}/{self.config['min_samples']} + 资源可训练 + {idle_check['reason']}"
        else:
            reason = f"未准备好: {'; '.join(reasons)}"
        
        return {
            "ready": ready,
            "stats": stats,
            "resources": resources,
            "idle": idle_check,
            "config": self.config,
            "reason": reason,
            "checks": {
                "samples": ready_samples,
                "resources": can_train_resources,
                "idle": is_idle
            },
            "next_check": f"{self.config['check_interval_minutes']}分钟后"
        }
    
    def start_scheduler(self):
        """启动调度器"""
        if not self.config.get("enabled", False):
            self._log("⏸️ 自动微调已禁用（默认关闭），需显式开启：config/evolution_schedule.json设置enabled=true或环境变量ZANE_AUTO_EVOLVE=true")
            return False
        
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            from apscheduler.triggers.interval import IntervalTrigger
            
            self.scheduler = BackgroundScheduler()
            
            # 空闲检查 - 主要触发方式：空闲N分钟+资源阈值
            self.scheduler.add_job(
                self._job_idle_check,
                IntervalTrigger(minutes=self.config["check_interval_minutes"]),
                id="idle_check",
                name="空闲检查（主要）"
            )
            
            # 凌晨训练 - 可选，需allow_nightly=true
            if self.config.get("allow_nightly", False):
                train_hour, train_minute = map(int, self.config.get("nightly_time", "02:00").split(":"))
                self.scheduler.add_job(
                    self._job_nightly_train,
                    CronTrigger(hour=train_hour, minute=train_minute),
                    id="nightly_train",
                    name="凌晨训练（可选）"
                )
            
            # 梦境整理 3点 - 仅在启用时
            if self.config.get("enabled", False):
                self.scheduler.add_job(
                    self._job_dreaming,
                    CronTrigger(hour=3, minute=0),
                    id="dreaming",
                    name="梦境整理"
                )
            
            self.scheduler.start()
            self._log(f"✅ 调度器已启动（自动微调已启用）：空闲{self.config['idle_minutes']}分钟+CPU<{self.config['cpu_threshold']}%+GPU<{self.config['gpu_util_threshold']}% + 每{self.config['check_interval_minutes']}分检查，冷却{self.config['cooldown_hours']}小时，每天最多{self.config['max_train_per_day']}次")
            
            return True
        except ImportError as e:
            self._log(f"❌ APScheduler未安装: {e}")
            return False
        except Exception as e:
            self._log(f"❌ 调度器启动失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_scheduler(self):
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            self._log("⏹️ 调度器已停止")
    
    def _job_nightly_train(self):
        """凌晨训练任务 - 仅在allow_nightly=true时"""
        if not self.config.get("allow_nightly", False):
            return
        
        self._log("🌙 凌晨训练任务触发（可选）")
        check = self.check_ready()
        
        if not check["ready"]:
            self._log(f"   未准备好: {check['reason']}")
            return
        
        self._execute_train(check)
    
    def _job_idle_check(self):
        """空闲检查任务 - 主要触发方式"""
        check = self.check_ready()
        
        if check["ready"]:
            self._log(f"💤 空闲检查：准备好训练 {check['reason']}")
            self._execute_train(check)
    
    def _execute_train(self, check: Dict):
        """执行训练"""
        self._log(f"   开始进化... {check['reason']}")
        
        try:
            import asyncio
            try:
                from ..learning.evolution_engine import evolution_engine
            except ImportError:
                from ..learning.evolution_engine_v25 import evolution_engine_v25 as evolution_engine
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(evolution_engine.start_evolution(manual=False))
            loop.close()
            
            # 更新状态
            state = self._load_state()
            today = datetime.now().date().isoformat()
            if state.get("last_date") != today:
                state["train_count_today"] = 0
                state["last_date"] = today
            state["last_train"] = datetime.now().isoformat()
            state["train_count_today"] = state.get("train_count_today", 0) + 1
            self._save_state(state)
            
            if result.get("success"):
                self._log(f"   ✅ 进化成功: {result.get('message','')}")
            else:
                self._log(f"   ❌ 进化失败: {result.get('message','')}")
        except Exception as e:
            self._log(f"   ❌ 进化异常: {e}")
            import traceback
            traceback.print_exc()
    
    def _job_dreaming(self):
        """梦境整理任务"""
        self._log("🌙 梦境整理任务触发")
        
        try:
            import asyncio
            try:
                from ..learning.evolution_engine import evolution_engine
            except ImportError:
                from ..learning.evolution_engine_v25 import evolution_engine_v25 as evolution_engine
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(evolution_engine.start_dreaming())
            loop.close()
            
            if result.get("success"):
                self._log(f"   ✅ 梦境完成: {result.get('message','')}")
            else:
                self._log(f"   ❌ 梦境失败: {result.get('message','')}")
        except Exception as e:
            self._log(f"   ❌ 梦境异常: {e}")


# 全局 - v0914
scheduler = SchedulerV0914()
# 兼容旧命名
scheduler_v3 = scheduler
