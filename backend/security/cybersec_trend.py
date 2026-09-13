# -*- coding: utf-8 -*-
"""
网安技能 - 安全扫描历史趋势时间序列端口/启动项异常感知
解决优先级10：cybersec_tools接入飞轮历史趋势
"""
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("zane")

@dataclass
class SecuritySnapshot:
    timestamp: float
    date: str
    open_ports: List[int]
    startup_items: List[str]
    weak_permissions: List[str]
    plaintext_passwords: List[str]
    risk_score: float
    issues: int

class CyberSecTrend:
    """安全趋势 - 时间序列异常感知"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "security"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.trend_file = self.data_dir / "trend.jsonl"
        self.snapshots: List[SecuritySnapshot] = []
        self.load()
    
    def load(self):
        if not self.trend_file.exists():
            return
        try:
            with open(self.trend_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.snapshots.append(SecuritySnapshot(**data))
            logger.info(f"✅ 安全趋势加载 {len(self.snapshots)}条快照")
        except Exception as e:
            logger.warning(f"安全趋势加载失败: {e}")
    
    def add_snapshot(self, scan_result: Dict[str, Any]):
        """添加扫描快照"""
        snapshot = SecuritySnapshot(
            timestamp=time.time(),
            date=time.strftime("%Y-%m-%d %H:%M:%S"),
            open_ports=scan_result.get("open_ports", []),
            startup_items=scan_result.get("startup_items", []),
            weak_permissions=scan_result.get("weak_permissions", []),
            plaintext_passwords=scan_result.get("plaintext_passwords", []),
            risk_score=scan_result.get("risk_score", 0),
            issues=scan_result.get("issues", 0)
        )
        
        self.snapshots.append(snapshot)
        
        # 保存
        try:
            with open(self.trend_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(snapshot), ensure_ascii=False) + "\n")
            logger.info(f"✅ 安全快照已保存 风险:{snapshot.risk_score} 问题:{snapshot.issues}")
        except Exception as e:
            logger.error(f"安全快照保存失败: {e}")
        
        # 保持最近100条
        if len(self.snapshots) > 100:
            self.snapshots = self.snapshots[-100:]
    
    def detect_anomalies(self) -> Dict[str, Any]:
        """异常感知 - 端口/启动项变化"""
        if len(self.snapshots) < 2:
            return {"anomalies": [], "message": "快照不足2条，无法检测异常"}
        
        anomalies = []
        latest = self.snapshots[-1]
        previous = self.snapshots[-2]
        
        # 端口变化
        new_ports = set(latest.open_ports) - set(previous.open_ports)
        closed_ports = set(previous.open_ports) - set(latest.open_ports)
        
        if new_ports:
            anomalies.append({
                "type": "new_ports",
                "severity": "high" if any(p in [22, 3389, 445, 135] for p in new_ports) else "medium",
                "message": f"新增开放端口: {list(new_ports)}",
                "ports": list(new_ports),
                "timestamp": latest.date
            })
        
        if closed_ports:
            anomalies.append({
                "type": "closed_ports",
                "severity": "low",
                "message": f"端口关闭: {list(closed_ports)}",
                "ports": list(closed_ports),
                "timestamp": latest.date
            })
        
        # 启动项变化
        new_startup = set(latest.startup_items) - set(previous.startup_items)
        removed_startup = set(previous.startup_items) - set(latest.startup_items)
        
        if new_startup:
            anomalies.append({
                "type": "new_startup",
                "severity": "high",
                "message": f"新增启动项: {list(new_startup)}",
                "items": list(new_startup),
                "timestamp": latest.date
            })
        
        if removed_startup:
            anomalies.append({
                "type": "removed_startup",
                "severity": "medium",
                "message": f"启动项移除: {list(removed_startup)}",
                "items": list(removed_startup),
                "timestamp": latest.date
            })
        
        # 风险分数突增
        if len(self.snapshots) >= 5:
            recent_scores = [s.risk_score for s in self.snapshots[-5:]]
            avg_score = sum(recent_scores[:-1]) / len(recent_scores[:-1]) if len(recent_scores) > 1 else 0
            if latest.risk_score > avg_score * 1.5 and latest.risk_score > 5:
                anomalies.append({
                    "type": "risk_spike",
                    "severity": "high",
                    "message": f"风险分数突增: {avg_score:.1f} → {latest.risk_score:.1f}",
                    "from": avg_score,
                    "to": latest.risk_score,
                    "timestamp": latest.date
                })
        
        # 明文密码新增
        new_passwords = set(latest.plaintext_passwords) - set(previous.plaintext_passwords)
        if new_passwords:
            anomalies.append({
                "type": "new_plaintext_passwords",
                "severity": "critical",
                "message": f"新增明文密码文件: {list(new_passwords)}",
                "files": list(new_passwords),
                "timestamp": latest.date
            })
        
        return {
            "anomalies": anomalies,
            "total": len(anomalies),
            "critical": len([a for a in anomalies if a["severity"] == "critical"]),
            "high": len([a for a in anomalies if a["severity"] == "high"]),
            "latest": asdict(latest),
            "previous": asdict(previous)
        }
    
    def get_trend(self, days: int = 7) -> Dict[str, Any]:
        """获取趋势 - 最近N天"""
        cutoff = time.time() - days * 24 * 3600
        recent = [s for s in self.snapshots if s.timestamp >= cutoff]
        
        if not recent:
            return {"trend": [], "message": f"最近{days}天无数据"}
        
        # 按天聚合
        by_day = defaultdict(list)
        for s in recent:
            day = time.strftime("%Y-%m-%d", time.localtime(s.timestamp))
            by_day[day].append(s)
        
        trend = []
        for day, snapshots in sorted(by_day.items()):
            avg_risk = sum(s.risk_score for s in snapshots) / len(snapshots)
            total_issues = sum(s.issues for s in snapshots)
            all_ports = set()
            for s in snapshots:
                all_ports.update(s.open_ports)
            
            trend.append({
                "date": day,
                "snapshots": len(snapshots),
                "avg_risk": round(avg_risk, 2),
                "total_issues": total_issues,
                "unique_ports": list(all_ports),
                "ports_count": len(all_ports)
            })
        
        return {
            "days": days,
            "total_snapshots": len(recent),
            "trend": trend,
            "latest": asdict(recent[-1]) if recent else None
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """统计"""
        if not self.snapshots:
            return {"total": 0, "message": "无数据"}
        
        # 端口出现频率
        port_freq = defaultdict(int)
        for s in self.snapshots:
            for p in s.open_ports:
                port_freq[p] += 1
        
        # 启动项频率
        startup_freq = defaultdict(int)
        for s in self.snapshots:
            for item in s.startup_items:
                startup_freq[item] += 1
        
        return {
            "total": len(self.snapshots),
            "first": asdict(self.snapshots[0]) if self.snapshots else None,
            "latest": asdict(self.snapshots[-1]) if self.snapshots else None,
            "port_frequency": dict(sorted(port_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
            "startup_frequency": dict(sorted(startup_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
            "avg_risk": round(sum(s.risk_score for s in self.snapshots) / len(self.snapshots), 2) if self.snapshots else 0,
            "max_risk": max((s.risk_score for s in self.snapshots), default=0),
            "total_issues": sum(s.issues for s in self.snapshots)
        }

# 全局实例
cybersec_trend = CyberSecTrend()
