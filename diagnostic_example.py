#!/usr/bin/env python3
"""
🛡️ HOLISTIC DIAGNOSTIC SYSTEM - Example Usage
Demonstrates how to use the comprehensive diagnostic and repair system.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from diagnostic_system import HolisticDiagnosticSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def example_complete_workflow():
    """Example of complete diagnostic and repair workflow"""
    logger.info("🛡️ Starting Holistic Diagnostic System Example")
    
    # Initialize the system
    project_root = str(Path(__file__).parent)
    diagnostic_system = HolisticDiagnosticSystem(project_root)
    
    # Example 1: Complete diagnosis and repair workflow
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 1: Complete Diagnosis and Repair Workflow")
    logger.info("="*60)
    
    try:
        result = await diagnostic_system.diagnose_and_fix_safely(
            problem_description="System seems to be running slowly and using too much memory",
            severity="medium",
            auto_fix=True
        )
        
        logger.info(f"✅ Workflow completed with status: {result['final_status']}")
        logger.info(f"📊 System health before: {result['system_health_before']:.2f}")
        logger.info(f"📊 System health after: {result['system_health_after']:.2f}")
        logger.info(f"⏱️ Total duration: {result['total_duration_seconds']:.1f} seconds")
        logger.info(f"🔧 Changes applied: {len(result.get('changes_applied', []))}")
        
        if result.get('lessons_learned'):
            logger.info("📖 Lessons learned:")
            for lesson in result['lessons_learned']:
                logger.info(f"  - {lesson}")
        
        if result.get('recommendations'):
            logger.info("💡 Recommendations:")
            for rec in result['recommendations']:
                logger.info(f"  - {rec}")
                
    except Exception as e:
        logger.error(f"❌ Complete workflow failed: {e}")

async def example_step_by_step():
    """Example of step-by-step diagnostic process"""
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 2: Step-by-Step Diagnostic Process")
    logger.info("="*60)
    
    project_root = str(Path(__file__).parent)
    diagnostic_system = HolisticDiagnosticSystem(project_root)
    
    try:
        # Step 1: Start monitoring
        await diagnostic_system.start_monitoring()
        logger.info("✅ Monitoring started")
        
        # Step 2: Run diagnostics only
        diagnostic_results = await diagnostic_system.run_diagnostics(
            "Database connections seem to be failing intermittently"
        )
        
        logger.info(f"🔍 Diagnostics completed")
        logger.info(f"📊 Overall health score: {diagnostic_results.get('overall_health_score', 'unknown')}")
        
        # Show layer results
        for layer_name, layer_result in diagnostic_results.get('layer_results', {}).items():
            findings_count = len(layer_result.get('findings', []))
            logger.info(f"  - {layer_name}: {findings_count} findings")
        
        # Step 3: Get system health
        health_report = diagnostic_system.get_system_health()
        logger.info(f"🏥 Current system status: {health_report['overall_health']['status']}")
        
        # Step 4: Stop monitoring
        await diagnostic_system.stop_monitoring()
        logger.info("✅ Monitoring stopped")
        
    except Exception as e:
        logger.error(f"❌ Step-by-step process failed: {e}")

async def example_system_analysis():
    """Example of system analysis capabilities"""
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 3: System Analysis Capabilities")
    logger.info("="*60)
    
    project_root = str(Path(__file__).parent)
    diagnostic_system = HolisticDiagnosticSystem(project_root)
    
    try:
        # Get comprehensive system analysis
        system_analysis = diagnostic_system.system_analyzer.analyze_complete_system()
        
        logger.info(f"📦 Total modules: {system_analysis['total_modules']}")
        logger.info(f"🔗 Total components: {system_analysis['total_components']}")
        logger.info(f"📊 Dependency depth: {system_analysis['dependency_depth']}")
        logger.info(f"🏥 System health score: {system_analysis['system_health_score']}")
        logger.info(f"⚠️ High risk modules: {len(system_analysis['high_risk_modules'])}")
        
        # Show complexity metrics
        complexity = system_analysis.get('complexity_metrics', {})
        logger.info(f"📏 Total lines of code: {complexity.get('total_lines_of_code', 0)}")
        logger.info(f"🔗 Coupling score: {complexity.get('coupling_score', 0):.3f}")
        logger.info(f"🎯 Cohesion score: {complexity.get('cohesion_score', 0):.3f}")
        
        # Detect invariants
        invariants = diagnostic_system.invariant_detector.detect_invariants()
        total_invariants = sum(len(inv_list) for inv_list in invariants.values())
        logger.info(f"🔍 Total invariants detected: {total_invariants}")
        
        for category, inv_list in invariants.items():
            if inv_list:
                logger.info(f"  - {category}: {len(inv_list)} invariants")
        
    except Exception as e:
        logger.error(f"❌ System analysis failed: {e}")

async def example_learned_patterns():
    """Example of learned patterns and suggestions"""
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 4: Learned Patterns and Suggestions")
    logger.info("="*60)
    
    project_root = str(Path(__file__).parent)
    diagnostic_system = HolisticDiagnosticSystem(project_root)
    
    try:
        # Get session statistics
        stats = diagnostic_system.get_session_statistics()
        
        logger.info(f"📚 Total diagnostic sessions: {stats['total_sessions']}")
        logger.info(f"✅ Success rate: {stats['success_rate']:.1f}%")
        logger.info(f"⏱️ Average resolution time: {stats['average_resolution_time_minutes']:.1f} minutes")
        logger.info(f"🧠 Learned patterns: {stats['learned_patterns_count']}")
        
        # Show status distribution
        if stats['status_distribution']:
            logger.info("📊 Session outcomes:")
            for status, count in stats['status_distribution'].items():
                logger.info(f"  - {status}: {count}")
        
        # Get suggestions for a sample problem
        suggestions = diagnostic_system.documentation.suggest_solutions(
            "Memory usage is high and system is slow"
        )
        
        if suggestions:
            logger.info(f"💡 Found {len(suggestions)} similar patterns:")
            for suggestion in suggestions[:3]:  # Top 3
                logger.info(f"  - {suggestion['description'][:100]}...")
                logger.info(f"    Confidence: {suggestion['confidence']:.2f}, Frequency: {suggestion['frequency']}")
        else:
            logger.info("💡 No similar patterns found yet - system is learning")
        
    except Exception as e:
        logger.error(f"❌ Pattern analysis failed: {e}")

async def example_monitoring_and_alerts():
    """Example of monitoring and alerting capabilities"""
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 5: Monitoring and Alerting")
    logger.info("="*60)
    
    project_root = str(Path(__file__).parent)
    diagnostic_system = HolisticDiagnosticSystem(project_root)
    
    try:
        # Custom alert handler
        def handle_alert(alert):
            logger.warning(f"🚨 ALERT: {alert.title} (Severity: {alert.severity})")
            logger.warning(f"    Description: {alert.description}")
        
        # Add alert handler
        diagnostic_system.continuous_validator.add_alert_handler(handle_alert)
        
        # Start monitoring
        await diagnostic_system.start_monitoring()
        logger.info("✅ Monitoring started with custom alert handler")
        
        # Let it run for a short time to collect metrics
        logger.info("📊 Collecting metrics for 10 seconds...")
        await asyncio.sleep(10)
        
        # Generate health report
        health_report = diagnostic_system.get_system_health()
        
        logger.info(f"🏥 System Health Report:")
        logger.info(f"  Overall Status: {health_report['overall_health']['status']}")
        logger.info(f"  Health Score: {health_report['overall_health']['score']:.2f}")
        
        if health_report.get('recent_alerts'):
            alert_counts = health_report['recent_alerts']['by_severity']
            logger.info(f"  Recent Alerts: {health_report['recent_alerts']['total_count']}")
            for severity, count in alert_counts.items():
                if count > 0:
                    logger.info(f"    - {severity}: {count}")
        
        # Trigger a manual alert for demonstration
        await diagnostic_system.continuous_validator.trigger_alert({
            "title": "Example Alert",
            "description": "This is a demonstration alert",
            "severity": "info",
            "context": {"example": True}
        })
        
        await asyncio.sleep(2)  # Let alert process
        
        # Stop monitoring
        await diagnostic_system.stop_monitoring()
        logger.info("✅ Monitoring stopped")
        
    except Exception as e:
        logger.error(f"❌ Monitoring example failed: {e}")

async def main():
    """Run all examples"""
    logger.info("🛡️ HOLISTIC DIAGNOSTIC SYSTEM - COMPREHENSIVE EXAMPLES")
    logger.info("=" * 80)
    
    examples = [
        ("Complete Workflow", example_complete_workflow),
        ("Step-by-Step Process", example_step_by_step),
        ("System Analysis", example_system_analysis),
        ("Learned Patterns", example_learned_patterns),
        ("Monitoring & Alerts", example_monitoring_and_alerts)
    ]
    
    for name, example_func in examples:
        try:
            logger.info(f"\n🔍 Running example: {name}")
            await example_func()
            logger.info(f"✅ {name} completed successfully")
        except Exception as e:
            logger.error(f"❌ {name} failed: {e}")
        
        # Small delay between examples
        await asyncio.sleep(2)
    
    logger.info("\n" + "="*80)
    logger.info("🛡️ All examples completed!")
    logger.info("="*80)
    logger.info("\n📚 QUICK REFERENCE:")
    logger.info("- Use HolisticDiagnosticSystem for complete workflows")
    logger.info("- Individual components can be used separately for specific needs")
    logger.info("- System learns from each diagnostic session")
    logger.info("- All changes are safe, incremental, and reversible")
    logger.info("- Comprehensive monitoring ensures system health")
    logger.info("\n🎯 Remember: Every fix makes the system BETTER, not just different!")

if __name__ == "__main__":
    asyncio.run(main())