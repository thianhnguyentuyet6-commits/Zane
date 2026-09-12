# -*- coding: utf-8 -*-
"""
Cleanup Utils - 截图清理+日志清理+备份清理 - 补全
"""

import os
import time
import glob
from pathlib import Path

class CleanupManager:
    def __init__(self):
        self.screenshot_dirs = [
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "screenshots"),
            os.path.join(os.path.dirname(__file__), "..", "..", "screenshots"),
            "./screenshots",
            "/tmp/screenshots"
        ]
        self.log_dirs = [
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "logs"),
            "./logs"
        ]
        self.backup_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "backups")
    
    def cleanup_screenshots(self, keep=50) -> dict:
        """清理截图，保留最新50张"""
        cleaned = 0
        kept = 0
        for dir_path in self.screenshot_dirs:
            if not os.path.exists(dir_path):
                continue
            try:
                files = glob.glob(os.path.join(dir_path, "*.png")) + glob.glob(os.path.join(dir_path, "*.jpg"))
                files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                if len(files) > keep:
                    to_delete = files[keep:]
                    for f in to_delete:
                        try:
                            os.remove(f)
                            cleaned += 1
                        except Exception:
                            pass
                    kept = keep
                else:
                    kept = len(files)
            except Exception as e:
                print(f"清理截图失败 {dir_path}: {e}")
        
        return {"cleaned": cleaned, "kept": kept, "note": f"保留最新{keep}张截图"}
    
    def cleanup_old_backups(self, keep=10, days=30) -> dict:
        """清理旧备份，保留10个或30天内"""
        cleaned = 0
        kept = 0
        if not os.path.exists(self.backup_dir):
            return {"cleaned": 0, "kept": 0}
        
        try:
            files = glob.glob(os.path.join(self.backup_dir, "*.db"))
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            now = time.time()
            for i, f in enumerate(files):
                try:
                    age_days = (now - os.path.getmtime(f)) / 86400
                    if i >= keep or age_days > days:
                        os.remove(f)
                        cleaned += 1
                    else:
                        kept += 1
                except Exception:
                    pass
        except Exception as e:
            print(f"清理备份失败: {e}")
        
        return {"cleaned": cleaned, "kept": kept, "note": f"保留{keep}个或{days}天内备份"}
    
    def cleanup_old_traces(self, keep=100) -> dict:
        """清理旧轨迹，保留100条"""
        cleaned = 0
        try:
            from ..database import database
            # SQLite中删除旧轨迹
            cursor = database.conn.execute("SELECT COUNT(*) as cnt FROM traces")
            total = cursor.fetchone()["cnt"]
            if total > keep:
                # 删除最旧的
                to_delete = total - keep
                database.conn.execute("""
                    DELETE FROM traces WHERE task_id IN (
                        SELECT task_id FROM traces ORDER BY start_time ASC LIMIT ?
                    )
                """, (to_delete,))
                database.conn.commit()
                cleaned = to_delete
            return {"cleaned": cleaned, "kept": min(total, keep), "total": total}
        except Exception as e:
            print(f"清理轨迹失败: {e}")
            return {"cleaned": 0, "error": str(e)}

cleanup_manager = CleanupManager()
