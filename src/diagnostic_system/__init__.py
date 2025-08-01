"""
🛡️ HOLISTIC PYTHON BACKEND DIAGNOSTIC & REPAIR SYSTEM v3.0

A comprehensive diagnostic and repair system that provides:
- Complete system analysis and dependency mapping
- Invariant detection and contract monitoring
- Multi-layer deep diagnostics
- Safe, incremental repair with rollback capability
- Continuous monitoring and validation
- Comprehensive change documentation and learning

This system follows the principle: "Every fix should make the system BETTER, not just different"

Usage:
    from diagnostic_system import HolisticDiagnosticSystem
    
    # Initialize the system
    diagnostic_system = HolisticDiagnosticSystem("/path/to/project")
    
    # Run complete diagnostics
    results = await diagnostic_system.diagnose_and_fix_safely("System is slow")
    
    # Get health report
    health = diagnostic_system.get_system_health()
"""

from .system_analyzer import SystemAnalyzer, SystemComponent, CriticalPath
from .invariant_detector import InvariantDetector, Invariant, InvariantViolation
from .deep_diagnostics import DeepDiagnostics, DiagnosticFinding, PerformanceMetric
from .safe_repair_engine import SafeRepairEngine, AtomicChange, RollbackPoint, ChangeType, ChangeStatus
from .continuous_validator import ContinuousValidator, HealthMetric, Alert, MonitoringRule
from .change_documentation import ChangeDocumentationSystem, ChangeRecord, DiagnosticSession, PatternLearning
from .holistic_system import HolisticDiagnosticSystem

__version__ = "3.0.0"
__author__ = "Holistic Diagnostic System Team"

# Export main classes for easy importing
__all__ = [
    # Main orchestrator
    "HolisticDiagnosticSystem",
    
    # Core components
    "SystemAnalyzer",
    "InvariantDetector", 
    "DeepDiagnostics",
    "SafeRepairEngine",
    "ContinuousValidator",
    "ChangeDocumentationSystem",
    
    # Data structures
    "SystemComponent",
    "CriticalPath",
    "Invariant",
    "InvariantViolation",
    "DiagnosticFinding",
    "PerformanceMetric",
    "AtomicChange",
    "RollbackPoint",
    "HealthMetric",
    "Alert",
    "MonitoringRule",
    "ChangeRecord",
    "DiagnosticSession",
    "PatternLearning",
    
    # Enums
    "ChangeType",
    "ChangeStatus"
]

# Version information
VERSION_INFO = {
    "version": __version__,
    "components": {
        "SystemAnalyzer": "Complete system mapping and dependency analysis",
        "InvariantDetector": "Detects and monitors system contracts and assumptions",
        "DeepDiagnostics": "Multi-layer diagnostic analysis engine",
        "SafeRepairEngine": "Safe, incremental repair with rollback capability",
        "ContinuousValidator": "Real-time system health monitoring",
        "ChangeDocumentationSystem": "Comprehensive change tracking and learning",
        "HolisticDiagnosticSystem": "Main orchestrator that coordinates all components"
    },
    "safety_features": [
        "Atomic changes with rollback capability",
        "Comprehensive preflight checks",
        "Real-time health monitoring",
        "Invariant preservation verification",
        "Complete change documentation",
        "Learning from past experiences",
        "Fail-safe defaults"
    ],
    "design_principles": [
        "NEVER assume - verify everything",
        "Think globally - every change affects the whole system", 
        "Incremental fixes with validation after each step",
        "Preserve system invariants and contracts",
        "Test everything - untested change = new bug",
        "Document everything for future learning",
        "Make the system BETTER, not just different"
    ]
}

def get_version_info():
    """Get comprehensive version and capability information"""
    return VERSION_INFO

def get_quick_start_guide():
    """Get quick start guide for using the diagnostic system"""
    return """
🛡️ HOLISTIC DIAGNOSTIC SYSTEM - QUICK START GUIDE

1. BASIC USAGE:
   ```python
   from diagnostic_system import HolisticDiagnosticSystem
   
   # Initialize
   system = HolisticDiagnosticSystem("/path/to/your/project")
   
   # Run diagnostics and repair
   result = await system.diagnose_and_fix_safely("Problem description")
   
   # Check system health
   health = system.get_system_health()
   ```

2. STEP-BY-STEP DIAGNOSTICS:
   ```python
   # Start monitoring
   await system.start_monitoring()
   
   # Run just diagnostics
   diagnosis = await system.run_diagnostics("Issue description")
   
   # Apply fixes manually
   fix_result = await system.apply_fix_safely(fix_plan)
   
   # Stop monitoring
   await system.stop_monitoring()
   ```

3. ADVANCED USAGE:
   ```python
   # Get system analysis
   analysis = system.system_analyzer.analyze_complete_system()
   
   # Detect invariants
   invariants = system.invariant_detector.detect_invariants()
   
   # Run specific diagnostic layer
   findings = await system.deep_diagnostics.surface_diagnostics(context)
   
   # Get learned patterns
   suggestions = system.documentation.suggest_solutions("problem")
   ```

4. SAFETY FEATURES:
   - All changes are atomic and reversible
   - Comprehensive preflight checks before any change
   - Real-time monitoring during operations
   - Complete documentation of all changes
   - Learning from past successes and failures

5. MONITORING:
   ```python
   # Add custom alert handler
   def handle_alert(alert):
       print(f"Alert: {alert.title}")
   
   system.continuous_validator.add_alert_handler(handle_alert)
   
   # Generate health report
   report = system.continuous_validator.generate_health_report()
   ```

Remember: This system is designed to make your system BETTER and more reliable,
not just fix immediate problems. Every operation contributes to the system's
long-term health and maintainability.
"""