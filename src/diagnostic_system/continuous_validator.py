"""
🛡️ CONTINUOUS VALIDATOR - Real-time system health monitoring and validation
Part of the Holistic Python Backend Diagnostic System v3.0
"""

import asyncio
import threading
import time
import psutil
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor
import weakref

logger = logging.getLogger(__name__)

@dataclass
class HealthMetric:
    """Represents a single health metric measurement"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    source: str  # "system", "application", "business", "user"
    category: str  # "performance", "reliability", "availability", "security"
    threshold_breached: bool = False
    severity: str = "info"  # "info", "warning", "error", "critical"
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alert:
    """Represents a system alert"""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    timestamp: datetime
    source_metrics: List[str] = field(default_factory=list)
    affected_components: Set[str] = field(default_factory=set)
    suggested_actions: List[str] = field(default_factory=list)
    acknowledged: bool = False
    resolved: bool = False
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MonitoringRule:
    """Defines a monitoring rule with thresholds and alerting"""
    rule_id: str
    metric_name: str
    condition: str  # "greater_than", "less_than", "equals", "not_equals", "percentage_change"
    threshold_value: float
    severity: str
    alert_message: str
    cooldown_seconds: int = 300  # 5 minutes default cooldown
    enabled: bool = True
    last_triggered: Optional[datetime] = None

class ContinuousValidator:
    """
    Continuous validation engine that monitors system health in real-time
    and triggers alerts when problems are detected.
    """
    
    def __init__(self, project_root: str, system_analyzer=None, invariant_detector=None):
        self.project_root = Path(project_root)
        self.system_analyzer = system_analyzer
        self.invariant_detector = invariant_detector
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_threads = []
        self.monitoring_executor = ThreadPoolExecutor(max_workers=4)
        
        # Metrics storage
        self.metrics_history: deque = deque(maxlen=10000)  # Keep last 10K metrics
        self.current_metrics: Dict[str, HealthMetric] = {}
        self.baseline_metrics: Dict[str, float] = {}
        
        # Alerting
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable] = []
        self.monitoring_rules: Dict[str, MonitoringRule] = {}
        
        # Performance tracking
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        
        # Degradation detection
        self.degradation_window = 300  # 5 minutes
        self.degradation_threshold = 0.2  # 20% degradation
        
        # Setup default monitoring rules
        self._setup_default_monitoring_rules()
        
        logger.info(f"📊 ContinuousValidator initialized for project: {self.project_root}")
    
    def _setup_default_monitoring_rules(self):
        """Setup default monitoring rules for common issues"""
        default_rules = [
            MonitoringRule(
                rule_id="high_cpu_usage",
                metric_name="cpu_percent",
                condition="greater_than",
                threshold_value=80.0,
                severity="warning",
                alert_message="High CPU usage detected",
                cooldown_seconds=180
            ),
            MonitoringRule(
                rule_id="critical_cpu_usage",
                metric_name="cpu_percent",
                condition="greater_than",
                threshold_value=95.0,
                severity="critical",
                alert_message="Critical CPU usage - system may become unresponsive",
                cooldown_seconds=60
            ),
            MonitoringRule(
                rule_id="high_memory_usage",
                metric_name="memory_percent",
                condition="greater_than",
                threshold_value=85.0,
                severity="warning",
                alert_message="High memory usage detected",
                cooldown_seconds=180
            ),
            MonitoringRule(
                rule_id="critical_memory_usage",
                metric_name="memory_percent",
                condition="greater_than",
                threshold_value=95.0,
                severity="critical",
                alert_message="Critical memory usage - risk of OOM",
                cooldown_seconds=60
            ),
            MonitoringRule(
                rule_id="low_disk_space",
                metric_name="disk_percent",
                condition="greater_than",
                threshold_value=90.0,
                severity="error",
                alert_message="Low disk space - system operations may fail",
                cooldown_seconds=300
            ),
            MonitoringRule(
                rule_id="high_error_rate",
                metric_name="error_rate_per_minute",
                condition="greater_than",
                threshold_value=10.0,
                severity="error",
                alert_message="High error rate detected",
                cooldown_seconds=120
            ),
            MonitoringRule(
                rule_id="response_time_degradation",
                metric_name="avg_response_time_ms",
                condition="percentage_change",
                threshold_value=50.0,  # 50% increase
                severity="warning",
                alert_message="Response time degradation detected",
                cooldown_seconds=240
            )
        ]
        
        for rule in default_rules:
            self.monitoring_rules[rule.rule_id] = rule
    
    async def start_monitoring(self, components: List[str] = None):
        """
        Start continuous monitoring of system health.
        This should be called BEFORE any diagnostic or repair operations.
        """
        if self.monitoring_active:
            logger.warning("⚠️ Monitoring already active")
            return
        
        logger.info("📊 Starting continuous monitoring...")
        self.monitoring_active = True
        
        # Collect baseline metrics
        await self._collect_baseline_metrics()
        logger.info("📊 Baseline metrics collected")
        
        # Start monitoring threads
        monitors = [
            ("system_metrics", self._monitor_system_metrics),
            ("application_metrics", self._monitor_application_metrics),
            ("error_monitoring", self._monitor_errors),
            ("performance_monitoring", self._monitor_performance),
            ("business_metrics", self._monitor_business_metrics),
            ("degradation_detection", self._monitor_degradation)
        ]
        
        for monitor_name, monitor_func in monitors:
            thread = threading.Thread(
                target=self._run_monitor_thread,
                args=(monitor_name, monitor_func),
                daemon=True
            )
            thread.start()
            self.monitoring_threads.append(thread)
            logger.info(f"📊 Started {monitor_name} monitor")
        
        # Start alert processing
        alert_thread = threading.Thread(
            target=self._process_alerts,
            daemon=True
        )
        alert_thread.start()
        self.monitoring_threads.append(alert_thread)
        
        logger.info("✅ Continuous monitoring started successfully")
    
    async def stop_monitoring(self):
        """Stop continuous monitoring"""
        if not self.monitoring_active:
            return
        
        logger.info("📊 Stopping continuous monitoring...")
        self.monitoring_active = False
        
        # Wait for threads to finish
        for thread in self.monitoring_threads:
            thread.join(timeout=5)
        
        # Shutdown executor
        self.monitoring_executor.shutdown(wait=True)
        
        logger.info("✅ Continuous monitoring stopped")
    
    def _run_monitor_thread(self, monitor_name: str, monitor_func: Callable):
        """Run a monitoring function in a thread with error handling"""
        logger.info(f"📊 Starting monitor thread: {monitor_name}")
        
        while self.monitoring_active:
            try:
                monitor_func()
                time.sleep(5)  # 5-second monitoring interval
            except Exception as e:
                logger.error(f"❌ Monitor {monitor_name} error: {e}")
                time.sleep(10)  # Longer sleep on error
        
        logger.info(f"📊 Monitor thread stopped: {monitor_name}")
    
    async def _collect_baseline_metrics(self):
        """Collect baseline metrics for comparison"""
        logger.info("📊 Collecting baseline metrics...")
        
        # System metrics
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self.project_root))
            
            self.baseline_metrics.update({
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 * 1024 * 1024)
            })
            
            # Network connections
            try:
                connections = len(psutil.net_connections())
                self.baseline_metrics["network_connections"] = connections
            except (psutil.AccessDenied, PermissionError):
                logger.info("📊 Network connections monitoring requires elevated permissions")
            
            # Load average (Unix systems)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                self.baseline_metrics.update({
                    "load_avg_1min": load_avg[0],
                    "load_avg_5min": load_avg[1],
                    "load_avg_15min": load_avg[2]
                })
        
        except Exception as e:
            logger.error(f"❌ Failed to collect system baseline: {e}")
        
        # Application-specific baselines
        if self.system_analyzer:
            try:
                system_analysis = self.system_analyzer.analyze_complete_system()
                self.baseline_metrics.update({
                    "system_health_score": system_analysis.get("system_health_score", 0.5),
                    "total_components": system_analysis.get("total_components", 0),
                    "dependency_depth": system_analysis.get("dependency_depth", 0)
                })
                
                # Store performance baselines
                complexity_metrics = system_analysis.get("complexity_metrics", {})
                self.performance_baselines["system"] = {
                    "total_lines_of_code": complexity_metrics.get("total_lines_of_code", 0),
                    "coupling_score": complexity_metrics.get("coupling_score", 0),
                    "cohesion_score": complexity_metrics.get("cohesion_score", 0)
                }
                
            except Exception as e:
                logger.error(f"❌ Failed to collect application baseline: {e}")
        
        logger.info(f"✅ Collected {len(self.baseline_metrics)} baseline metrics")
    
    def _monitor_system_metrics(self):
        """Monitor system-level metrics"""
        try:
            timestamp = datetime.now()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self._record_metric(HealthMetric(
                metric_name="cpu_percent",
                value=cpu_percent,
                unit="percent",
                timestamp=timestamp,
                source="system",
                category="performance"
            ))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self._record_metric(HealthMetric(
                metric_name="memory_percent",
                value=memory.percent,
                unit="percent",
                timestamp=timestamp,
                source="system",
                category="performance"
            ))
            
            self._record_metric(HealthMetric(
                metric_name="memory_available_mb",
                value=memory.available / (1024 * 1024),
                unit="MB",
                timestamp=timestamp,
                source="system",
                category="performance"
            ))
            
            # Disk metrics
            disk = psutil.disk_usage(str(self.project_root))
            self._record_metric(HealthMetric(
                metric_name="disk_percent",
                value=disk.percent,
                unit="percent",
                timestamp=timestamp,
                source="system",
                category="performance"
            ))
            
            # Process-specific metrics
            current_process = psutil.Process()
            self._record_metric(HealthMetric(
                metric_name="process_memory_mb",
                value=current_process.memory_info().rss / (1024 * 1024),
                unit="MB",
                timestamp=timestamp,
                source="system",
                category="performance"
            ))
            
            self._record_metric(HealthMetric(
                metric_name="process_cpu_percent",
                value=current_process.cpu_percent(),
                unit="percent",
                timestamp=timestamp,
                source="system",
                category="performance"
            ))
            
            # Load average (Unix systems)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                self._record_metric(HealthMetric(
                    metric_name="load_avg_1min",
                    value=load_avg[0],
                    unit="load",
                    timestamp=timestamp,
                    source="system",
                    category="performance"
                ))
            
        except Exception as e:
            logger.error(f"❌ System metrics monitoring error: {e}")
    
    def _monitor_application_metrics(self):
        """Monitor application-specific metrics"""
        try:
            timestamp = datetime.now()
            
            # System analyzer metrics
            if self.system_analyzer:
                try:
                    # Quick health check (without full analysis to avoid overhead)
                    health_score = self._quick_health_check()
                    self._record_metric(HealthMetric(
                        metric_name="system_health_score",
                        value=health_score,
                        unit="score",
                        timestamp=timestamp,
                        source="application",
                        category="reliability"
                    ))
                    
                except Exception as e:
                    logger.debug(f"Could not get application health score: {e}")
            
            # File system health
            python_files = list(self.project_root.rglob("*.py"))
            self._record_metric(HealthMetric(
                metric_name="python_files_count",
                value=len(python_files),
                unit="count",
                timestamp=timestamp,
                source="application",
                category="reliability"
            ))
            
            # Log file sizes (if they exist)
            log_files = list(self.project_root.rglob("*.log"))
            total_log_size = sum(f.stat().st_size for f in log_files if f.exists()) / (1024 * 1024)
            self._record_metric(HealthMetric(
                metric_name="total_log_size_mb",
                value=total_log_size,
                unit="MB",
                timestamp=timestamp,
                source="application",
                category="performance"
            ))
            
        except Exception as e:
            logger.error(f"❌ Application metrics monitoring error: {e}")
    
    def _monitor_errors(self):
        """Monitor error rates and patterns"""
        try:
            timestamp = datetime.now()
            
            # Check log files for recent errors
            log_files = list(self.project_root.rglob("*.log"))
            total_errors = 0
            total_warnings = 0
            
            cutoff_time = timestamp - timedelta(minutes=1)  # Last minute
            
            for log_file in log_files:
                try:
                    if not log_file.exists():
                        continue
                    
                    # Read last part of log file
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # Read last 1000 lines
                        lines = deque(f, maxlen=1000)
                    
                    for line in lines:
                        line_lower = line.lower()
                        
                        # Simple timestamp extraction (this would need improvement for production)
                        if any(keyword in line_lower for keyword in ['error', 'exception', 'traceback']):
                            total_errors += 1
                        elif 'warning' in line_lower:
                            total_warnings += 1
                            
                except Exception as e:
                    logger.debug(f"Could not read log file {log_file}: {e}")
            
            self._record_metric(HealthMetric(
                metric_name="error_rate_per_minute",
                value=total_errors,
                unit="count",
                timestamp=timestamp,
                source="application",
                category="reliability"
            ))
            
            self._record_metric(HealthMetric(
                metric_name="warning_rate_per_minute",
                value=total_warnings,
                unit="count",
                timestamp=timestamp,
                source="application",
                category="reliability"
            ))
            
        except Exception as e:
            logger.error(f"❌ Error monitoring error: {e}")
    
    def _monitor_performance(self):
        """Monitor performance metrics"""
        try:
            timestamp = datetime.now()
            
            # Simulate response time monitoring (in a real system, this would measure actual requests)
            # For now, we'll use CPU and memory as proxies for performance
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # Estimate response time based on resource usage
            # This is a simplified heuristic
            estimated_response_time = 100 + (cpu_percent * 2) + (memory_percent * 1.5)
            
            self._record_metric(HealthMetric(
                metric_name="estimated_response_time_ms",
                value=estimated_response_time,
                unit="ms",
                timestamp=timestamp,
                source="application",
                category="performance"
            ))
            
            # Database connection monitoring (if applicable)
            # This would check actual database connections in a real system
            
            # File I/O performance
            try:
                start_time = time.time()
                test_file = self.project_root / ".monitoring_test"
                test_file.write_text("test")
                test_file.unlink()
                io_time = (time.time() - start_time) * 1000  # Convert to ms
                
                self._record_metric(HealthMetric(
                    metric_name="disk_io_latency_ms",
                    value=io_time,
                    unit="ms",
                    timestamp=timestamp,
                    source="system",
                    category="performance"
                ))
                
            except Exception as e:
                logger.debug(f"Could not measure disk I/O: {e}")
            
        except Exception as e:
            logger.error(f"❌ Performance monitoring error: {e}")
    
    def _monitor_business_metrics(self):
        """Monitor business-level metrics (application-specific)"""
        try:
            timestamp = datetime.now()
            
            # For the meeting scheduler bot, we could monitor:
            # - Number of active users
            # - Meeting creation rate
            # - Error rates in specific features
            
            # This is a placeholder - real implementation would depend on the application
            self._record_metric(HealthMetric(
                metric_name="application_uptime_minutes",
                value=self._get_uptime_minutes(),
                unit="minutes",
                timestamp=timestamp,
                source="business",
                category="availability"
            ))
            
        except Exception as e:
            logger.error(f"❌ Business metrics monitoring error: {e}")
    
    def _monitor_degradation(self):
        """Monitor for performance degradation patterns"""
        try:
            timestamp = datetime.now()
            
            # Check for degradation in key metrics
            degradation_metrics = ["cpu_percent", "memory_percent", "estimated_response_time_ms"]
            
            for metric_name in degradation_metrics:
                degradation_score = self._calculate_degradation_score(metric_name)
                
                if degradation_score > 0:
                    self._record_metric(HealthMetric(
                        metric_name=f"{metric_name}_degradation",
                        value=degradation_score,
                        unit="score",
                        timestamp=timestamp,
                        source="application",
                        category="performance",
                        severity="warning" if degradation_score > self.degradation_threshold else "info"
                    ))
            
        except Exception as e:
            logger.error(f"❌ Degradation monitoring error: {e}")
    
    def _calculate_degradation_score(self, metric_name: str) -> float:
        """Calculate degradation score for a metric over time"""
        try:
            # Get recent metrics for this metric name
            cutoff_time = datetime.now() - timedelta(seconds=self.degradation_window)
            recent_metrics = [
                m for m in self.metrics_history 
                if m.metric_name == metric_name and m.timestamp >= cutoff_time
            ]
            
            if len(recent_metrics) < 5:  # Need at least 5 data points
                return 0.0
            
            # Calculate trend
            values = [m.value for m in recent_metrics]
            
            # Simple trend calculation: compare first half with second half
            mid_point = len(values) // 2
            first_half_avg = sum(values[:mid_point]) / mid_point
            second_half_avg = sum(values[mid_point:]) / (len(values) - mid_point)
            
            if first_half_avg == 0:
                return 0.0
            
            # For metrics where increase is bad (CPU, memory, response time)
            bad_metrics = ["cpu_percent", "memory_percent", "estimated_response_time_ms", "error_rate_per_minute"]
            
            if metric_name in bad_metrics:
                degradation = (second_half_avg - first_half_avg) / first_half_avg
            else:
                # For metrics where decrease is bad (health score, throughput)
                degradation = (first_half_avg - second_half_avg) / first_half_avg
            
            return max(0.0, degradation)  # Only return positive degradation
            
        except Exception as e:
            logger.debug(f"Could not calculate degradation for {metric_name}: {e}")
            return 0.0
    
    def _record_metric(self, metric: HealthMetric):
        """Record a metric and check for threshold breaches"""
        # Store metric
        self.metrics_history.append(metric)
        self.current_metrics[metric.metric_name] = metric
        
        # Check monitoring rules
        self._check_monitoring_rules(metric)
    
    def _check_monitoring_rules(self, metric: HealthMetric):
        """Check if a metric breaches any monitoring rules"""
        for rule_id, rule in self.monitoring_rules.items():
            if not rule.enabled:
                continue
            
            if rule.metric_name != metric.metric_name:
                continue
            
            # Check cooldown
            if rule.last_triggered:
                time_since_last = (datetime.now() - rule.last_triggered).total_seconds()
                if time_since_last < rule.cooldown_seconds:
                    continue
            
            # Check condition
            threshold_breached = False
            
            if rule.condition == "greater_than":
                threshold_breached = metric.value > rule.threshold_value
            elif rule.condition == "less_than":
                threshold_breached = metric.value < rule.threshold_value
            elif rule.condition == "equals":
                threshold_breached = abs(metric.value - rule.threshold_value) < 0.001
            elif rule.condition == "not_equals":
                threshold_breached = abs(metric.value - rule.threshold_value) >= 0.001
            elif rule.condition == "percentage_change":
                # Compare with baseline
                baseline_value = self.baseline_metrics.get(metric.metric_name)
                if baseline_value and baseline_value > 0:
                    percentage_change = abs((metric.value - baseline_value) / baseline_value) * 100
                    threshold_breached = percentage_change > rule.threshold_value
            
            if threshold_breached:
                # Create alert
                alert = Alert(
                    alert_id=f"{rule_id}_{int(time.time())}",
                    alert_type=rule_id,
                    severity=rule.severity,
                    title=rule.alert_message,
                    description=f"{rule.alert_message}: {metric.metric_name} = {metric.value} {metric.unit}",
                    timestamp=datetime.now(),
                    source_metrics=[metric.metric_name],
                    context={
                        "metric_value": metric.value,
                        "threshold_value": rule.threshold_value,
                        "condition": rule.condition,
                        "baseline_value": self.baseline_metrics.get(metric.metric_name)
                    }
                )
                
                self.alerts.append(alert)
                rule.last_triggered = datetime.now()
                
                logger.warning(f"⚠️ Alert triggered: {alert.title}")
    
    def _process_alerts(self):
        """Process alerts and call alert handlers"""
        while self.monitoring_active:
            try:
                # Process unacknowledged alerts
                unacknowledged_alerts = [a for a in self.alerts if not a.acknowledged]
                
                for alert in unacknowledged_alerts:
                    # Call alert handlers
                    for handler in self.alert_handlers:
                        try:
                            handler(alert)
                        except Exception as e:
                            logger.error(f"❌ Alert handler error: {e}")
                    
                    # Auto-acknowledge info alerts after processing
                    if alert.severity == "info":
                        alert.acknowledged = True
                
                time.sleep(10)  # Process alerts every 10 seconds
                
            except Exception as e:
                logger.error(f"❌ Alert processing error: {e}")
                time.sleep(30)
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
    
    def _quick_health_check(self) -> float:
        """Perform a quick health check without full system analysis"""
        try:
            # Simple health score based on current metrics
            cpu_score = max(0, 1.0 - (self.current_metrics.get("cpu_percent", HealthMetric("", 0, "", datetime.now(), "", "")).value / 100))
            memory_score = max(0, 1.0 - (self.current_metrics.get("memory_percent", HealthMetric("", 0, "", datetime.now(), "", "")).value / 100))
            
            # Average the scores
            health_score = (cpu_score + memory_score) / 2
            return health_score
            
        except Exception as e:
            logger.debug(f"Quick health check error: {e}")
            return 0.5  # Default moderate health
    
    def _get_uptime_minutes(self) -> float:
        """Get application uptime in minutes"""
        try:
            # This is a simplified implementation
            # In a real system, you'd track actual application startup time
            current_process = psutil.Process()
            create_time = datetime.fromtimestamp(current_process.create_time())
            uptime = (datetime.now() - create_time).total_seconds() / 60
            return uptime
        except Exception:
            return 0.0
    
    def is_degraded(self, metric_name: str, metric: HealthMetric) -> bool:
        """Check if a metric indicates system degradation"""
        # Simple degradation check
        baseline_value = self.baseline_metrics.get(metric_name)
        if baseline_value is None:
            return False
        
        # Define what constitutes degradation for different metrics
        degradation_thresholds = {
            "cpu_percent": 1.5,  # 50% increase
            "memory_percent": 1.3,  # 30% increase  
            "estimated_response_time_ms": 1.5,  # 50% increase
            "error_rate_per_minute": 2.0,  # 100% increase
            "system_health_score": 0.8,  # 20% decrease
        }
        
        threshold = degradation_thresholds.get(metric_name, 1.2)  # Default 20% increase
        
        if metric_name in ["system_health_score"]:
            # For metrics where lower is worse
            return metric.value < (baseline_value * threshold)
        else:
            # For metrics where higher is worse
            return metric.value > (baseline_value * threshold)
    
    async def trigger_alert(self, alert_data: Dict[str, Any]):
        """Manually trigger an alert"""
        alert = Alert(
            alert_id=f"manual_{int(time.time())}",
            alert_type="manual",
            severity=alert_data.get("severity", "warning"),
            title=alert_data.get("title", "Manual Alert"),
            description=alert_data.get("description", "Manually triggered alert"),
            timestamp=datetime.now(),
            context=alert_data.get("context", {})
        )
        
        self.alerts.append(alert)
        logger.warning(f"⚠️ Manual alert triggered: {alert.title}")
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health report"""
        report_time = datetime.now()
        
        # Calculate overall health
        overall_health = self._calculate_overall_health()
        
        # Get recent alerts
        recent_alerts = [a for a in self.alerts 
                        if (report_time - a.timestamp).total_seconds() < 3600]  # Last hour
        
        # Get current metrics summary
        current_metrics_summary = {}
        for metric_name, metric in self.current_metrics.items():
            current_metrics_summary[metric_name] = {
                "value": metric.value,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat(),
                "severity": metric.severity
            }
        
        # Performance trends
        performance_trends = self._calculate_performance_trends()
        
        # System components health
        component_health = self._assess_component_health()
        
        report = {
            "report_timestamp": report_time.isoformat(),
            "overall_health": {
                "score": overall_health,
                "status": self._health_score_to_status(overall_health),
                "description": self._get_health_description(overall_health)
            },
            "current_metrics": current_metrics_summary,
            "recent_alerts": {
                "total_count": len(recent_alerts),
                "by_severity": self._group_alerts_by_severity(recent_alerts),
                "active_alerts": [self._serialize_alert(a) for a in recent_alerts if not a.resolved]
            },
            "performance_trends": performance_trends,
            "component_health": component_health,
            "monitoring_status": {
                "active": self.monitoring_active,
                "active_rules": len([r for r in self.monitoring_rules.values() if r.enabled]),
                "metrics_collected": len(self.metrics_history),
                "uptime_minutes": self._get_uptime_minutes()
            },
            "recommendations": self._generate_health_recommendations(overall_health, recent_alerts)
        }
        
        return report
    
    def _calculate_overall_health(self) -> float:
        """Calculate overall system health score"""
        if not self.current_metrics:
            return 0.5  # Default moderate health
        
        # Weight different metrics
        metric_weights = {
            "cpu_percent": 0.2,
            "memory_percent": 0.2,
            "system_health_score": 0.3,
            "error_rate_per_minute": 0.2,
            "estimated_response_time_ms": 0.1
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric_name, weight in metric_weights.items():
            if metric_name in self.current_metrics:
                metric = self.current_metrics[metric_name]
                
                # Normalize metric to 0-1 scale
                if metric_name == "cpu_percent":
                    score = max(0, 1.0 - (metric.value / 100))
                elif metric_name == "memory_percent":
                    score = max(0, 1.0 - (metric.value / 100))
                elif metric_name == "system_health_score":
                    score = metric.value
                elif metric_name == "error_rate_per_minute":
                    score = max(0, 1.0 - (metric.value / 10))  # 10 errors = 0 score
                elif metric_name == "estimated_response_time_ms":
                    score = max(0, 1.0 - (metric.value / 1000))  # 1000ms = 0 score
                else:
                    score = 0.5
                
                total_score += score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        return min(1.0, max(0.0, total_score / total_weight))
    
    def _health_score_to_status(self, health_score: float) -> str:
        """Convert health score to status string"""
        if health_score >= 0.8:
            return "healthy"
        elif health_score >= 0.6:
            return "degraded"
        elif health_score >= 0.4:
            return "unhealthy"
        else:
            return "critical"
    
    def _get_health_description(self, health_score: float) -> str:
        """Get description for health score"""
        status = self._health_score_to_status(health_score)
        
        descriptions = {
            "healthy": "System is operating normally with good performance",
            "degraded": "System is functional but showing signs of performance degradation",
            "unhealthy": "System has significant issues that may impact functionality",
            "critical": "System is in critical condition and may fail soon"
        }
        
        return descriptions.get(status, "Unknown health status")
    
    def _group_alerts_by_severity(self, alerts: List[Alert]) -> Dict[str, int]:
        """Group alerts by severity"""
        severity_counts = defaultdict(int)
        for alert in alerts:
            severity_counts[alert.severity] += 1
        return dict(severity_counts)
    
    def _serialize_alert(self, alert: Alert) -> Dict[str, Any]:
        """Serialize alert for JSON output"""
        return {
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type, 
            "severity": alert.severity,
            "title": alert.title,
            "description": alert.description,
            "timestamp": alert.timestamp.isoformat(),
            "source_metrics": alert.source_metrics,
            "affected_components": list(alert.affected_components),
            "suggested_actions": alert.suggested_actions,
            "acknowledged": alert.acknowledged,
            "resolved": alert.resolved,
            "context": alert.context
        }
    
    def _calculate_performance_trends(self) -> Dict[str, Any]:
        """Calculate performance trends over time"""
        trends = {}
        
        # Get metrics from last hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        # Group by metric name
        metrics_by_name = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_name[metric.metric_name].append(metric)
        
        # Calculate trends for key metrics
        key_metrics = ["cpu_percent", "memory_percent", "estimated_response_time_ms", "error_rate_per_minute"]
        
        for metric_name in key_metrics:
            if metric_name in metrics_by_name:
                values = [m.value for m in metrics_by_name[metric_name]]
                if len(values) >= 2:
                    # Simple trend: compare first and last values
                    trend_direction = "stable"
                    if values[-1] > values[0] * 1.1:
                        trend_direction = "increasing"
                    elif values[-1] < values[0] * 0.9:
                        trend_direction = "decreasing"
                    
                    trends[metric_name] = {
                        "direction": trend_direction,
                        "start_value": values[0],
                        "end_value": values[-1],
                        "change_percent": ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0,
                        "data_points": len(values)
                    }
        
        return trends
    
    def _assess_component_health(self) -> Dict[str, Any]:
        """Assess health of individual components"""
        component_health = {
            "system_resources": "healthy",
            "application": "healthy", 
            "monitoring": "healthy"
        }
        
        # Check system resources
        cpu_metric = self.current_metrics.get("cpu_percent")
        memory_metric = self.current_metrics.get("memory_percent")
        
        if cpu_metric and cpu_metric.value > 80:
            component_health["system_resources"] = "degraded"
        if memory_metric and memory_metric.value > 85:
            component_health["system_resources"] = "unhealthy"
        
        # Check application health
        health_score_metric = self.current_metrics.get("system_health_score")
        if health_score_metric and health_score_metric.value < 0.6:
            component_health["application"] = "degraded"
        
        error_rate_metric = self.current_metrics.get("error_rate_per_minute")
        if error_rate_metric and error_rate_metric.value > 5:
            component_health["application"] = "unhealthy"
        
        return component_health
    
    def _generate_health_recommendations(self, health_score: float, recent_alerts: List[Alert]) -> List[str]:
        """Generate health recommendations based on current state"""
        recommendations = []
        
        if health_score < 0.4:
            recommendations.append("🚨 URGENT: System health is critical - immediate attention required")
        elif health_score < 0.6:
            recommendations.append("⚠️ System health is poor - investigate and resolve issues")
        elif health_score < 0.8:
            recommendations.append("🔍 System health is fair - monitor closely and address degradation")
        
        # Check for specific issues
        cpu_metric = self.current_metrics.get("cpu_percent")
        if cpu_metric and cpu_metric.value > 80:
            recommendations.append("💻 High CPU usage detected - check for resource-intensive processes")
        
        memory_metric = self.current_metrics.get("memory_percent")
        if memory_metric and memory_metric.value > 85:
            recommendations.append("🧠 High memory usage detected - check for memory leaks")
        
        error_rate_metric = self.current_metrics.get("error_rate_per_minute")
        if error_rate_metric and error_rate_metric.value > 3:
            recommendations.append("🐛 High error rate detected - check application logs")
        
        # Alert-based recommendations
        critical_alerts = [a for a in recent_alerts if a.severity == "critical" and not a.resolved]
        if critical_alerts:
            recommendations.append(f"🚨 {len(critical_alerts)} critical alerts require immediate attention")
        
        error_alerts = [a for a in recent_alerts if a.severity == "error" and not a.resolved]
        if error_alerts:
            recommendations.append(f"❌ {len(error_alerts)} error alerts need investigation")
        
        if not recommendations:
            recommendations.append("✅ System health is good - continue monitoring")
        
        return recommendations
    
    def get_dashboard_url(self) -> str:
        """Get URL for monitoring dashboard (placeholder)"""
        # In a real implementation, this would return a URL to a monitoring dashboard
        return f"http://localhost:8080/monitoring/dashboard?project={self.project_root.name}"