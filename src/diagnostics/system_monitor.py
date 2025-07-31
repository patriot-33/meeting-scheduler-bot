"""
🔬 SYSTEM MONITORING UTILITIES
Advanced system monitoring for meeting-scheduler-bot diagnostics
"""

import asyncio
import time
import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import psutil
import sqlalchemy
from sqlalchemy import text
from contextlib import asynccontextmanager

from .core_diagnostics import DiagnosticLogger, diagnostic_context

@dataclass
class SystemMetrics:
    """System performance metrics snapshot"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_free_gb: float
    network_connections: int
    process_count: int
    load_average: List[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    timestamp: str
    connection_count: int
    active_connections: int
    idle_connections: int
    query_response_time_ms: float
    connection_test_success: bool
    last_error: Optional[str] = None

@dataclass
class ExternalServiceMetrics:
    """External service availability metrics"""
    timestamp: str
    service_name: str
    url: str
    response_time_ms: float
    status_code: int
    success: bool
    error_message: Optional[str] = None

class SystemMonitor:
    """Comprehensive system monitoring utility"""
    
    def __init__(self, logger: DiagnosticLogger):
        self.logger = logger
        self.metrics_history: List[SystemMetrics] = []
        self.max_history = 1000  # Keep last 1000 measurements
    
    def get_current_metrics(self) -> SystemMetrics:
        """Capture current system metrics snapshot"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_free_gb = disk.free / (1024**3)
            
            # Network metrics (with fallback for permission issues)
            try:
                network_connections = len(psutil.net_connections())
            except (psutil.AccessDenied, PermissionError):
                network_connections = 0  # Fallback if no permission
            
            # Process metrics
            process_count = len(psutil.pids())
            
            # Load average (Unix/Linux only)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                load_avg = [0.0, 0.0, 0.0]  # Windows fallback
            
            metrics = SystemMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=round(memory_used_gb, 2),
                memory_total_gb=round(memory_total_gb, 2),
                disk_percent=disk.percent,
                disk_free_gb=round(disk_free_gb, 2),
                network_connections=network_connections,
                process_count=process_count,
                load_average=load_avg
            )
            
            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            self.logger.logger.error(f"❌ Failed to collect system metrics: {e}")
            raise
    
    def analyze_performance_trends(self, minutes: int = 10) -> Dict[str, Any]:
        """Analyze performance trends over specified time period"""
        if not self.metrics_history:
            return {"error": "No metrics history available"}
        
        # Get recent metrics (approximate based on collection frequency)
        recent_count = min(minutes * 6, len(self.metrics_history))  # Assume 10s intervals
        recent_metrics = self.metrics_history[-recent_count:]
        
        if len(recent_metrics) < 2:
            return {"error": "Insufficient metrics for trend analysis"}
        
        # Calculate trends
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        analysis = {
            "time_period_minutes": minutes,
            "sample_count": len(recent_metrics),
            "cpu": {
                "current": cpu_values[-1],
                "average": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
                "trend": "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"
            },
            "memory": {
                "current": memory_values[-1],
                "average": sum(memory_values) / len(memory_values),
                "min": min(memory_values),
                "max": max(memory_values),
                "trend": "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
            },
            "alerts": []
        }
        
        # Generate alerts
        if analysis["cpu"]["current"] > 80:
            analysis["alerts"].append("🚨 HIGH CPU USAGE")
        if analysis["memory"]["current"] > 85:
            analysis["alerts"].append("🚨 HIGH MEMORY USAGE")
        if analysis["cpu"]["trend"] == "increasing" and analysis["cpu"]["current"] > 60:
            analysis["alerts"].append("⚠️  CPU USAGE TRENDING UP")
        if analysis["memory"]["trend"] == "increasing" and analysis["memory"]["current"] > 70:
            analysis["alerts"].append("⚠️  MEMORY USAGE TRENDING UP")
        
        return analysis
    
    def log_performance_summary(self):
        """Log comprehensive performance summary"""
        metrics = self.get_current_metrics()
        trends = self.analyze_performance_trends()
        
        self.logger.logger.info("📊 SYSTEM PERFORMANCE SUMMARY:")
        self.logger.logger.info(f"   CPU: {metrics.cpu_percent}%")
        self.logger.logger.info(f"   Memory: {metrics.memory_percent}% ({metrics.memory_used_gb}GB/{metrics.memory_total_gb}GB)")
        self.logger.logger.info(f"   Disk: {metrics.disk_percent}% ({metrics.disk_free_gb}GB free)")
        self.logger.logger.info(f"   Network connections: {metrics.network_connections}")
        self.logger.logger.info(f"   Load average: {metrics.load_average}")
        
        if trends.get("alerts"):
            for alert in trends["alerts"]:
                self.logger.logger.warning(f"   {alert}")

class DatabaseMonitor:
    """Database-specific monitoring utilities"""
    
    def __init__(self, logger: DiagnosticLogger, engine: sqlalchemy.Engine):
        self.logger = logger
        self.engine = engine
    
    def test_database_connectivity(self) -> DatabaseMetrics:
        """Test database connectivity and performance"""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            with diagnostic_context(self.logger, "DATABASE_CONNECTIVITY_TEST"):
                # Test basic connectivity
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                
                response_time_ms = (time.time() - start_time) * 1000
                
                # Get connection pool info
                pool = self.engine.pool
                connection_count = pool.size()
                active_connections = pool.checkedout()
                idle_connections = connection_count - active_connections
                
                metrics = DatabaseMetrics(
                    timestamp=timestamp,
                    connection_count=connection_count,
                    active_connections=active_connections,
                    idle_connections=idle_connections,
                    query_response_time_ms=round(response_time_ms, 2),
                    connection_test_success=True
                )
                
                self.logger.logger.info(f"✅ Database connectivity test passed ({response_time_ms:.2f}ms)")
                return metrics
                
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            metrics = DatabaseMetrics(
                timestamp=timestamp,
                connection_count=0,
                active_connections=0,
                idle_connections=0,
                query_response_time_ms=round(response_time_ms, 2),
                connection_test_success=False,
                last_error=str(e)
            )
            
            self.logger.logger.error(f"❌ Database connectivity test failed: {e}")
            return metrics
    
    def analyze_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health analysis"""
        metrics = self.test_database_connectivity()
        
        health_analysis = {
            "overall_status": "healthy" if metrics.connection_test_success else "unhealthy",
            "connectivity": metrics.connection_test_success,
            "response_time_ms": metrics.query_response_time_ms,
            "connection_pool": {
                "total": metrics.connection_count,
                "active": metrics.active_connections,
                "idle": metrics.idle_connections,
                "utilization_percent": (metrics.active_connections / max(metrics.connection_count, 1)) * 100
            },
            "alerts": []
        }
        
        # Generate alerts
        if not metrics.connection_test_success:
            health_analysis["alerts"].append("🚨 DATABASE CONNECTION FAILED")
        elif metrics.query_response_time_ms > 1000:
            health_analysis["alerts"].append("⚠️  SLOW DATABASE RESPONSE")
        elif health_analysis["connection_pool"]["utilization_percent"] > 80:
            health_analysis["alerts"].append("⚠️  HIGH CONNECTION POOL UTILIZATION")
        
        return health_analysis

class ExternalServiceMonitor:
    """Monitor external service availability and performance"""
    
    def __init__(self, logger: DiagnosticLogger):
        self.logger = logger
    
    def test_service_connectivity(self, service_name: str, url: str, timeout: int = 5) -> ExternalServiceMetrics:
        """Test external service connectivity"""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            with diagnostic_context(self.logger, f"EXTERNAL_SERVICE_TEST_{service_name}"):
                response = requests.get(url, timeout=timeout)
                response_time_ms = (time.time() - start_time) * 1000
                
                metrics = ExternalServiceMetrics(
                    timestamp=timestamp,
                    service_name=service_name,
                    url=url,
                    response_time_ms=round(response_time_ms, 2),
                    status_code=response.status_code,
                    success=response.status_code < 400
                )
                
                if metrics.success:
                    self.logger.logger.info(f"✅ {service_name} connectivity test passed ({response_time_ms:.2f}ms)")
                else:
                    self.logger.logger.warning(f"⚠️  {service_name} returned status {response.status_code}")
                
                return metrics
                
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            metrics = ExternalServiceMetrics(
                timestamp=timestamp,
                service_name=service_name,
                url=url,
                response_time_ms=round(response_time_ms, 2),
                status_code=0,
                success=False,
                error_message=str(e)
            )
            
            self.logger.logger.error(f"❌ {service_name} connectivity test failed: {e}")
            return metrics
    
    def monitor_google_services(self) -> Dict[str, ExternalServiceMetrics]:
        """Monitor Google services availability"""
        services = {
            "google_oauth": "https://oauth2.googleapis.com/token",
            "google_calendar": "https://www.googleapis.com/calendar/v3/",
            "google_apis": "https://www.googleapis.com/"
        }
        
        results = {}
        for service_name, url in services.items():
            results[service_name] = self.test_service_connectivity(service_name, url)
        
        return results

# Comprehensive monitoring orchestrator
class ComprehensiveMonitor:
    """Orchestrates all monitoring systems"""
    
    def __init__(self, logger: DiagnosticLogger, db_engine: Optional[sqlalchemy.Engine] = None):
        self.logger = logger
        self.system_monitor = SystemMonitor(logger)
        self.database_monitor = DatabaseMonitor(logger, db_engine) if db_engine else None
        self.service_monitor = ExternalServiceMonitor(logger)
    
    def run_full_diagnostic_sweep(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic sweep of all systems"""
        sweep_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": {},
            "database": {},
            "external_services": {},
            "overall_health": "unknown",
            "critical_alerts": []
        }
        
        try:
            # System monitoring
            with diagnostic_context(self.logger, "SYSTEM_DIAGNOSTIC_SWEEP"):
                system_metrics = self.system_monitor.get_current_metrics()
                system_trends = self.system_monitor.analyze_performance_trends()
                
                sweep_results["system"] = {
                    "metrics": system_metrics.to_dict(),
                    "trends": system_trends
                }
                
                # Database monitoring
                if self.database_monitor:
                    db_health = self.database_monitor.analyze_database_health()
                    sweep_results["database"] = db_health
                
                # External service monitoring
                google_services = self.service_monitor.monitor_google_services()
                sweep_results["external_services"] = {
                    service: metrics.__dict__ for service, metrics in google_services.items()
                }
                
                # Overall health assessment
                critical_alerts = []
                
                # Collect all alerts
                if system_trends.get("alerts"):
                    critical_alerts.extend(system_trends["alerts"])
                
                if self.database_monitor and sweep_results["database"].get("alerts"):
                    critical_alerts.extend(sweep_results["database"]["alerts"])
                
                for service_name, service_metrics in google_services.items():
                    if not service_metrics.success:
                        critical_alerts.append(f"🚨 {service_name.upper()} SERVICE DOWN")
                
                sweep_results["critical_alerts"] = critical_alerts
                
                # Determine overall health
                if any("🚨" in alert for alert in critical_alerts):
                    sweep_results["overall_health"] = "critical"
                elif critical_alerts:
                    sweep_results["overall_health"] = "degraded"
                else:
                    sweep_results["overall_health"] = "healthy"
                
                self.logger.logger.info(f"🏥 DIAGNOSTIC SWEEP COMPLETED - Status: {sweep_results['overall_health'].upper()}")
                
                if critical_alerts:
                    self.logger.logger.warning("🚨 CRITICAL ALERTS DETECTED:")
                    for alert in critical_alerts:
                        self.logger.logger.warning(f"   {alert}")
                
                return sweep_results
                
        except Exception as e:
            self.logger.logger.error(f"❌ Diagnostic sweep failed: {e}")
            sweep_results["overall_health"] = "error"
            sweep_results["error"] = str(e)
            return sweep_results