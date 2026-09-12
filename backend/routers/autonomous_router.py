# -*- coding: utf-8 -*-
"""Autonomous Router - 20 Skill + APScheduler + 习惯学习 - C扩展"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/autonomous", tags=["autonomous"])

@router.get("/status")
async def autonomous_status():
    try:
        from ..autonomous_optimizer import autonomous_optimizer
        return autonomous_optimizer.get_status()
    except Exception as e:
        return {"error": str(e)}

@router.post("/run")
async def autonomous_run():
    try:
        from ..autonomous_optimizer import autonomous_optimizer
        result = await autonomous_optimizer.run_idle_task()
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.post("/query-open-source")
async def autonomous_query():
    try:
        from ..autonomous_optimizer import autonomous_optimizer
        result = await autonomous_optimizer.query_open_source()
        return result
    except Exception as e:
        return {"error": str(e)}

@router.get("/candidate-skills")
async def autonomous_candidate_skills():
    try:
        from ..autonomous_optimizer import autonomous_optimizer
        return {
            "candidates": autonomous_optimizer.candidate_skills,
            "count": len(autonomous_optimizer.candidate_skills),
            "total": 20,
            "note": "A+C扩展：原7+新增13=20，含窗口置顶/音量/夜间/备份/监控/热键/通知/进程/取色/扩展/工作区/便签/监控小组件"
        }
    except Exception as e:
        return {"candidates": [], "count": 0, "error": str(e)}

@router.get("/habits/learn")
async def learn_habits():
    """C扩展 - 触发习惯学习"""
    try:
        from ..autonomous_optimizer import autonomous_optimizer
        habits = autonomous_optimizer.analyze_habits()
        personalized = autonomous_optimizer.generate_personalized_skills(habits)
        return {
            "habits": habits,
            "personalized_skills": [s["name"] for s in personalized],
            "count": len(habits),
            "full_auto": True,
            "note": "C扩展：从traces分析高频任务，生成个性化Skill，默认开启"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.post("/scheduler/start")
async def start_scheduler():
    try:
        from ..autonomous_optimizer import autonomous_optimizer
        autonomous_optimizer.start_scheduler()
        return {"success": True, "scheduler": "APScheduler已启动，凌晨2点+每30分钟"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/scheduler/stop")
async def stop_scheduler():
    try:
        from ..autonomous_optimizer import autonomous_optimizer
        autonomous_optimizer.stop_scheduler()
        return {"success": True, "message": "调度器已停止"}
    except Exception as e:
        return {"success": False, "error": str(e)}
