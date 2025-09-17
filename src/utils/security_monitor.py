#!/usr/bin/env python3
"""
Security Monitor Module
Integrates security logging and monitoring with existing performance monitoring system.
"""

import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

# Import your existing performance monitor for integration
try:
    from .performance_monitor import PerformanceMonitor
    PERFORMANCE_MONITOR_AVAILABLE = True
except ImportError:
    try:
        from core.performance_monitor import PerformanceMonitor
        PERFORMANCE_MONITOR_AVAILABLE = True
    except ImportError:
        PERFORMANCE_MONITOR_AVAILABLE = False


@dataclass
class SecurityEvent:
    """Security event data structure."""
    timestamp: str
    event_type: str
    risk_level: str
    query_hash: str
    query_preview: str
    violations: List[str]
    warnings: List[str]
    blocked: bool
    execution_time: float = 0.0
    session_id: str = ""
    user_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_context is None:
            self.user_context = {}


class SecurityMonitor:
    """
    Security monitoring system that integrates with your existing performance monitoring.
    Tracks security events, violations, and provides analytics.
    """
    
    def __init__(self, performance_monitor: Optional[Any] = None):
        # Integration with existing performance monitor
        self.performance_monitor = performance_monitor
        
        # Security event storage (recent events in memory)
        self.security_events = deque(maxlen=1000)  # Keep last 1000 events
        
        # Security statistics
        self.security_stats = {
            "total_queries": 0,
            "blocked_queries": 0,
            "high_risk_queries": 0,
            "violations_by_type": defaultdict(int),
            "violations_by_risk": defaultdict(int),
            "sessions_with_violations": set(),
            "start_time": datetime.now(),
            "last_violation": None
        }
        
        # Security metrics for performance analysis
        self.security_metrics = {
            "avg_security_check_time": 0.0,
            "security_overhead_total": 0.0,
            "queries_with_warnings": 0,
            "false_positive_rate": 0.0
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            "blocked_queries_per_minute": 10,
            "high_risk_queries_per_minute": 20,
            "violations_per_session": 5,
            "security_overhead_ms": 100
        }
        
        # Recent activity tracking for alerts
        self.recent_activity = {
            "blocked_queries": deque(maxlen=100),
            "high_risk_queries": deque(maxlen=100),
            "session_violations": defaultdict(list)
        }
    
    def log_security_event(self, event_data: Dict[str, Any]) -> str:
        """
        Log a security event and update statistics.
        
        Args:
            event_data: Security event information
            
        Returns:
            Event ID for tracking
        """
        # Create security event
        event = SecurityEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_data.get("event_type", "query_validation"),
            risk_level=event_data.get("risk_level", "low"),
            query_hash=event_data.get("query_hash", "unknown"),
            query_preview=event_data.get("query_preview", ""),
            violations=event_data.get("violations", []),
            warnings=event_data.get("warnings", []),
            blocked=event_data.get("blocked", False),
            execution_time=event_data.get("execution_time", 0.0),
            session_id=event_data.get("session_id", ""),
            user_context=event_data.get("user_context", {})
        )
        
        # Store event
        self.security_events.append(event)
        
        # Update statistics
        self._update_security_stats(event)
        
        # Check for alerts
        self._check_security_alerts(event)
        
        # Integrate with performance monitor if available
        if self.performance_monitor:
            self._integrate_with_performance_monitor(event)
        
        return f"{event.timestamp}_{event.query_hash}"
    
    def _update_security_stats(self, event: SecurityEvent):
        """Update security statistics with new event."""
        self.security_stats["total_queries"] += 1
        
        if event.blocked:
            self.security_stats["blocked_queries"] += 1
            self.recent_activity["blocked_queries"].append(datetime.now())
        
        if event.risk_level in ["high", "critical"]:
            self.security_stats["high_risk_queries"] += 1
            self.recent_activity["high_risk_queries"].append(datetime.now())
        
        # Count violations by type and risk level
        for violation in event.violations:
            violation_type = violation.split(":")[0] if ":" in violation else violation
            self.security_stats["violations_by_type"][violation_type] += 1
            
        self.security_stats["violations_by_risk"][event.risk_level] += 1
        
        # Track sessions with violations
        if event.violations and event.session_id:
            self.security_stats["sessions_with_violations"].add(event.session_id)
            self.recent_activity["session_violations"][event.session_id].append(event)
        
        # Update last violation
        if event.violations:
            self.security_stats["last_violation"] = {
                "timestamp": event.timestamp,
                "risk_level": event.risk_level,
                "query_hash": event.query_hash,
                "violations": event.violations
            }
        
        # Update security metrics
        if event.warnings:
            self.security_metrics["queries_with_warnings"] += 1
    
    def _check_security_alerts(self, event: SecurityEvent):
        """Check if security event triggers any alerts."""
        current_time = datetime.now()
        one_minute_ago = current_time - timedelta(minutes=1)
        
        # Check blocked queries per minute
        recent_blocked = [
            dt for dt in self.recent_activity["blocked_queries"]
            if dt > one_minute_ago
        ]
        if len(recent_blocked) > self.alert_thresholds["blocked_queries_per_minute"]:
            self._trigger_security_alert(
                "HIGH_BLOCK_RATE",
                f"High rate of blocked queries: {len(recent_blocked)} in last minute",
                "critical"
            )
        
        # Check high-risk queries per minute
        recent_high_risk = [
            dt for dt in self.recent_activity["high_risk_queries"]
            if dt > one_minute_ago
        ]
        if len(recent_high_risk) > self.alert_thresholds["high_risk_queries_per_minute"]:
            self._trigger_security_alert(
                "HIGH_RISK_RATE",
                f"High rate of risky queries: {len(recent_high_risk)} in last minute",
                "high"
            )
        
        # Check violations per session
        if event.session_id:
            session_violations = len(self.recent_activity["session_violations"][event.session_id])
            if session_violations > self.alert_thresholds["violations_per_session"]:
                self._trigger_security_alert(
                    "SESSION_ABUSE",
                    f"Session {event.session_id} has {session_violations} violations",
                    "high"
                )
    
    def _trigger_security_alert(self, alert_type: str, message: str, severity: str):
        """Trigger a security alert."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message,
            "severity": severity
        }
        
        # Print alert (integrates with your existing logging)
        severity_icon = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "⚡",
            "low": "ℹ️"
        }.get(severity, "📢")
        
        print(f"{severity_icon} SECURITY ALERT [{severity.upper()}]: {message}")
        
        # Log alert as security event
        self.security_events.append(SecurityEvent(
            timestamp=alert["timestamp"],
            event_type="security_alert",
            risk_level=severity,
            query_hash="alert",
            query_preview=f"Alert: {alert_type}",
            violations=[message],
            warnings=[],
            blocked=False
        ))
    
    def _integrate_with_performance_monitor(self, event: SecurityEvent):
        """Integrate security event with performance monitoring."""
        if not hasattr(self.performance_monitor, 'record_security_event'):
            return
        
        try:
            # Add security metadata to performance monitoring
            security_metadata = {
                "security_check_time": event.execution_time,
                "risk_level": event.risk_level,
                "violations_count": len(event.violations),
                "warnings_count": len(event.warnings),
                "blocked": event.blocked
            }
            
            self.performance_monitor.record_security_event(security_metadata)
        except Exception as e:
            print(f"⚠️ Failed to integrate with performance monitor: {e}")
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive security dashboard data."""
        current_time = datetime.now()
        uptime = current_time - self.security_stats["start_time"]
        
        # Calculate rates
        total_queries = self.security_stats["total_queries"]
        block_rate = (self.security_stats["blocked_queries"] / max(total_queries, 1)) * 100
        high_risk_rate = (self.security_stats["high_risk_queries"] / max(total_queries, 1)) * 100
        
        # Recent activity (last hour)
        one_hour_ago = current_time - timedelta(hours=1)
        recent_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event.timestamp) > one_hour_ago
        ]
        
        # Top violations
        top_violations = dict(sorted(
            self.security_stats["violations_by_type"].items(),
            key=lambda x: x[1], reverse=True
        )[:10])
        
        return {
            "overview": {
                "uptime_hours": uptime.total_seconds() / 3600,
                "total_queries": total_queries,
                "blocked_queries": self.security_stats["blocked_queries"],
                "high_risk_queries": self.security_stats["high_risk_queries"],
                "block_rate": round(block_rate, 2),
                "high_risk_rate": round(high_risk_rate, 2),
                "sessions_with_violations": len(self.security_stats["sessions_with_violations"])
            },
            "recent_activity": {
                "events_last_hour": len(recent_events),
                "blocked_last_hour": len([e for e in recent_events if e.blocked]),
                "high_risk_last_hour": len([e for e in recent_events if e.risk_level in ["high", "critical"]])
            },
            "violations": {
                "by_type": top_violations,
                "by_risk_level": dict(self.security_stats["violations_by_risk"]),
                "last_violation": self.security_stats["last_violation"]
            },
            "performance": {
                "avg_security_check_time": self.security_metrics["avg_security_check_time"],
                "queries_with_warnings": self.security_metrics["queries_with_warnings"],
                "security_overhead_total": self.security_metrics["security_overhead_total"]
            }
        }
    
    def get_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate security report for specified time period."""
        current_time = datetime.now()
        start_time = current_time - timedelta(hours=hours)
        
        # Filter events by time period
        period_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event.timestamp) > start_time
        ]
        
        if not period_events:
            return {"message": f"No security events in the last {hours} hours"}
        
        # Analyze events
        blocked_events = [e for e in period_events if e.blocked]
        critical_events = [e for e in period_events if e.risk_level == "critical"]
        high_risk_events = [e for e in period_events if e.risk_level == "high"]
        
        # Session analysis
        sessions_analyzed = set(e.session_id for e in period_events if e.session_id)
        sessions_with_violations = set(e.session_id for e in period_events if e.violations and e.session_id)
        
        # Violation patterns
        violation_patterns = defaultdict(int)
        for event in period_events:
            for violation in event.violations:
                violation_patterns[violation] += 1
        
        return {
            "period": f"Last {hours} hours",
            "summary": {
                "total_events": len(period_events),
                "blocked_queries": len(blocked_events),
                "critical_events": len(critical_events),
                "high_risk_events": len(high_risk_events),
                "sessions_analyzed": len(sessions_analyzed),
                "sessions_with_violations": len(sessions_with_violations)
            },
            "top_violations": dict(sorted(
                violation_patterns.items(),
                key=lambda x: x[1], reverse=True
            )[:10]),
            "risk_distribution": {
                "critical": len(critical_events),
                "high": len(high_risk_events),
                "medium": len([e for e in period_events if e.risk_level == "medium"]),
                "low": len([e for e in period_events if e.risk_level == "low"])
            },
            "recommendations": self._generate_security_recommendations(period_events)
        }
    
    def _generate_security_recommendations(self, events: List[SecurityEvent]) -> List[str]:
        """Generate security recommendations based on events."""
        recommendations = []
        
        # Check for common patterns
        blocked_count = len([e for e in events if e.blocked])
        if blocked_count > 10:
            recommendations.append(f"High number of blocked queries ({blocked_count}). Review input validation.")
        
        # Check for injection attempts
        injection_events = [e for e in events if any("injection" in v.lower() for v in e.violations)]
        if injection_events:
            recommendations.append("SQL injection attempts detected. Implement parameterized queries.")
        
        # Check for repeated violations from same session
        session_violations = defaultdict(int)
        for event in events:
            if event.violations and event.session_id:
                session_violations[event.session_id] += len(event.violations)
        
        problematic_sessions = [s for s, count in session_violations.items() if count > 5]
        if problematic_sessions:
            recommendations.append(f"Sessions with repeated violations: {len(problematic_sessions)}. Consider rate limiting.")
        
        # Check for performance impact
        high_overhead_events = [e for e in events if e.execution_time > 0.1]  # 100ms
        if len(high_overhead_events) > len(events) * 0.1:  # More than 10% of queries
            recommendations.append("High security check overhead detected. Consider optimizing security rules.")
        
        return recommendations
    
    def export_security_events(self, format: str = "json", limit: int = 100) -> str:
        """Export security events in specified format."""
        events_to_export = list(self.security_events)[-limit:]
        
        if format.lower() == "json":
            return json.dumps([asdict(event) for event in events_to_export], indent=2)
        elif format.lower() == "csv":
            # Simple CSV export
            lines = ["timestamp,event_type,risk_level,blocked,violations_count,warnings_count"]
            for event in events_to_export:
                lines.append(f"{event.timestamp},{event.event_type},{event.risk_level},{event.blocked},{len(event.violations)},{len(event.warnings)}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def reset_security_stats(self):
        """Reset security statistics."""
        self.security_stats = {
            "total_queries": 0,
            "blocked_queries": 0,
            "high_risk_queries": 0,
            "violations_by_type": defaultdict(int),
            "violations_by_risk": defaultdict(int),
            "sessions_with_violations": set(),
            "start_time": datetime.now(),
            "last_violation": None
        }
        self.security_events.clear()
        self.recent_activity = {
            "blocked_queries": deque(maxlen=100),
            "high_risk_queries": deque(maxlen=100),
            "session_violations": defaultdict(list)
        }
        print("🔄 Security statistics reset")


# Integration helper for your existing architecture
class SecurityIntegrationHelper:
    """Helper class for integrating security monitoring with existing systems."""
    
    @staticmethod
    def create_integrated_monitor(performance_monitor=None) -> SecurityMonitor:
        """Create security monitor integrated with existing performance monitor."""
        return SecurityMonitor(performance_monitor=performance_monitor)
    
    @staticmethod
    def log_query_security_event(security_monitor: SecurityMonitor, 
                                query: str, security_report: Dict[str, Any],
                                execution_result: str = None,
                                session_id: str = None,
                                execution_time: float = 0.0):
        """Helper to log security events from query execution."""
        event_data = {
            "event_type": "query_validation",
            "risk_level": security_report.get("risk_level", "low"),
            "query_hash": security_report.get("query_hash", "unknown"),
            "query_preview": query[:100] + "..." if len(query) > 100 else query,
            "violations": security_report.get("violations", []),
            "warnings": security_report.get("warnings", []),
            "blocked": not security_report.get("is_safe", True),
            "execution_time": execution_time,
            "session_id": session_id or "",
            "user_context": {}
        }
        
        return security_monitor.log_security_event(event_data)



