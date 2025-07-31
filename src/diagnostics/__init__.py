"""
🎯 ULTIMATE PYTHON BACKEND DIAGNOSTIC SYSTEM v2.0
Complete diagnostic framework for meeting-scheduler-bot
"""

# Core diagnostics
from .core_diagnostics import (
    DiagnosticLogger,
    ProblemPriority,
    classify_problem_priority,
    classify_problem_type,
    diagnose_function,
    diagnostic_context,
    diagnostic_logger,
    log_system_state,
    debug_context,
    validate_data
)

# System monitoring
from .system_monitor import (
    SystemMonitor,
    DatabaseMonitor,
    ExternalServiceMonitor,
    ComprehensiveMonitor,
    SystemMetrics,
    DatabaseMetrics,
    ExternalServiceMetrics
)

# Hypothesis testing
from .hypothesis_testing import (
    HypothesisTester,
    CommonHypotheses,
    FiveWhysAnalyzer,
    HypothesisResult,
    TestCondition
)

# Safe implementation
from .safe_implementation import (
    SafeImplementationManager,
    SolutionAssessment,
    BackupState,
    ImplementationStep,
    RiskLevel,
    implement_solution_with_backup
)

# Post-solution monitoring
from .post_solution_monitoring import (
    PostSolutionMonitor,
    HealthCheck,
    MonitoringAlert,
    HealthReport,
    HealthStatus,
    create_health_endpoint,
    temporary_monitoring
)

# Main orchestrator
from .diagnostic_orchestrator import (
    UltimateDiagnosticSystem,
    quick_diagnostic_session
)

__version__ = "2.0.0"

__all__ = [
    # Core diagnostics
    'DiagnosticLogger',
    'ProblemPriority', 
    'classify_problem_priority',
    'classify_problem_type',
    'diagnose_function',
    'diagnostic_context',
    'diagnostic_logger',
    'log_system_state',
    'debug_context',
    'validate_data',
    
    # System monitoring
    'SystemMonitor',
    'DatabaseMonitor', 
    'ExternalServiceMonitor',
    'ComprehensiveMonitor',
    'SystemMetrics',
    'DatabaseMetrics',
    'ExternalServiceMetrics',
    
    # Hypothesis testing
    'HypothesisTester',
    'CommonHypotheses',
    'FiveWhysAnalyzer',
    'HypothesisResult',
    'TestCondition',
    
    # Safe implementation
    'SafeImplementationManager',
    'SolutionAssessment',
    'BackupState',
    'ImplementationStep',
    'RiskLevel',
    'implement_solution_with_backup',
    
    # Post-solution monitoring
    'PostSolutionMonitor',
    'HealthCheck',
    'MonitoringAlert', 
    'HealthReport',
    'HealthStatus',
    'create_health_endpoint',
    'temporary_monitoring',
    
    # Main orchestrator
    'UltimateDiagnosticSystem',
    'quick_diagnostic_session'
]