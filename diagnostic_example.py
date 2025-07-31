#!/usr/bin/env python3
"""
🎯 ULTIMATE DIAGNOSTIC SYSTEM - USAGE EXAMPLE
Complete example of how to use the diagnostic system for meeting-scheduler-bot
"""

import sys
import os
import time
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from diagnostics import UltimateDiagnosticSystem
from database import get_database_engine  # Your existing database module

def example_problem_scenario():
    """
    Example scenario: Meeting creation is failing intermittently
    """
    
    print("🎯 ULTIMATE DIAGNOSTIC SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    # Initialize diagnostic system
    try:
        db_engine = get_database_engine()  # Your database engine
    except Exception as e:
        print(f"Warning: Could not initialize database engine: {e}")
        db_engine = None
    
    diagnostic_system = UltimateDiagnosticSystem(
        project_name="meeting-scheduler-bot",
        db_engine=db_engine,
        log_file="example_diagnostics.log"
    )
    
    # PHASE 1: Triage
    print("\n📋 PHASE 1: TRIAGE")
    print("-" * 30)
    
    triage_result = diagnostic_system.phase_1_triage(
        problem_description="Meeting creation failing intermittently with Google Calendar",
        error_message="TimeoutError: Google Calendar API request timed out after 30 seconds",
        context={
            "user_reports": 15,
            "failure_rate": "30%",
            "time_pattern": "peak hours only",
            "affected_users": "all user types"
        }
    )
    
    print(f"Priority: {triage_result['priority']}")
    print(f"Problem Type: {triage_result['problem_type']}")
    print("Recommended next steps:")
    for step in triage_result['recommended_next_steps']:
        print(f"  • {step}")
    
    # PHASE 2: Systematic Diagnosis
    print("\n🔬 PHASE 2: SYSTEMATIC DIAGNOSIS")
    print("-" * 35)
    
    diagnosis_result = diagnostic_system.phase_2_systematic_diagnosis()
    
    print(f"Overall Health: {diagnosis_result['sweep_results'].get('overall_health', 'unknown')}")
    print(f"Critical Findings: {len(diagnosis_result['critical_findings'])}")
    print(f"Recommended Hypotheses: {diagnosis_result['recommended_hypotheses']}")
    
    # PHASE 3: Hypothesis Testing
    print("\n🧪 PHASE 3: HYPOTHESIS TESTING")
    print("-" * 32)
    
    hypothesis_result = diagnostic_system.phase_3_hypothesis_testing(
        custom_hypotheses=["external_service_failure"],
        db_engine=db_engine
    )
    
    print(f"Hypotheses Tested: {hypothesis_result['hypotheses_tested']}")
    print(f"Confirmed: {hypothesis_result['confirmed_hypotheses']}")
    print(f"Rejected: {hypothesis_result['rejected_hypotheses']}")
    
    # PHASE 4: Root Cause Analysis
    print("\n🎯 PHASE 4: ROOT CAUSE ANALYSIS")
    print("-" * 33)
    
    # Example 5 Whys answers for Google Calendar timeout issue
    why_answers = [
        "Google Calendar API requests are timing out after 30 seconds",
        "The API server is responding slowly during peak hours",
        "High traffic volume is overwhelming the API rate limits",
        "Our application is making too many concurrent requests",
        "Connection pooling is not properly configured for high-load scenarios"
    ]
    
    root_cause_result = diagnostic_system.phase_4_root_cause_analysis(why_answers)
    
    print(f"Root Cause: {root_cause_result['five_whys_analysis']['root_cause']}")
    print(f"Confidence: {root_cause_result['root_cause_confidence']:.2f}")
    print("Recommended Solutions:")
    for solution in root_cause_result['recommended_solutions']:
        print(f"  • {solution}")
    
    # PHASE 5: Solution Implementation
    print("\n⚡ PHASE 5: SOLUTION IMPLEMENTATION")
    print("-" * 36)
    
    def implement_connection_pooling_fix():
        """Example solution: Configure proper connection pooling"""
        print("  📝 Configuring Google API connection pooling...")
        time.sleep(2)  # Simulate implementation work
        
        # In real implementation, you would:
        # 1. Update Google API client configuration
        # 2. Set proper timeout values
        # 3. Configure connection retry logic
        # 4. Add request rate limiting
        
        print("  ✅ Connection pooling configured")
        return True
    
    def verify_solution():
        """Verify that the solution works"""
        print("  🔍 Verifying solution effectiveness...")
        time.sleep(1)
        
        # In real verification, you would:
        # 1. Test Google Calendar API calls
        # 2. Check response times
        # 3. Verify error rates
        # 4. Test under load
        
        print("  ✅ Solution verification passed")
        return True
    
    implementation_result = diagnostic_system.phase_5_safe_solution_implementation(
        solution_description="Configure Google API connection pooling and timeout settings",
        implementation_function=implement_connection_pooling_fix,
        verification_function=verify_solution,
        files_to_backup=["src/services/google_calendar.py", "src/config.py"]
    )
    
    print(f"Implementation Result: {implementation_result['implementation_result']['result']}")
    print(f"Success: {implementation_result['success']}")
    
    # PHASE 6: Post-Solution Monitoring
    print("\n📈 PHASE 6: POST-SOLUTION MONITORING")
    print("-" * 37)
    
    monitoring_result = diagnostic_system.phase_6_post_solution_monitoring(
        monitoring_duration_minutes=5  # Short duration for demo
    )
    
    print(f"Final Health Status: {monitoring_result['final_health']['overall_status']}")
    print(f"Total Alerts: {monitoring_result['total_alerts']}")
    print("Recommendations:")
    for rec in monitoring_result['recommendations']:
        print(f"  • {rec}")
    
    # Generate Comprehensive Report
    print("\n📋 GENERATING COMPREHENSIVE REPORT")
    print("-" * 38)
    
    final_report = diagnostic_system.generate_comprehensive_report()
    
    print(f"Session Duration: {final_report['session_info']['duration_seconds']/60:.1f} minutes")
    print(f"Phases Completed: {len(final_report['phases_completed'])}/6")
    print(f"Diagnostic Success: {final_report['success_metrics']['diagnostic_completed']}")
    
    return final_report

def quick_diagnostic_example():
    """
    Example of quick diagnostic session for simple problems
    """
    
    print("\n" + "=" * 60)
    print("🚀 QUICK DIAGNOSTIC SESSION EXAMPLE")
    print("=" * 60)
    
    from diagnostics.diagnostic_orchestrator import quick_diagnostic_session
    
    def simple_fix():
        """Simple solution example"""
        print("  🔧 Restarting service...")
        time.sleep(1)
        return True
    
    def simple_verification():
        """Simple verification"""
        print("  ✅ Service is responding")
        return True
    
    try:
        db_engine = get_database_engine()
    except:
        db_engine = None
    
    report = quick_diagnostic_session(
        problem_description="Database connection intermittently failing",
        error_message="psycopg2.OperationalError: connection timeout",
        db_engine=db_engine,
        solution_function=simple_fix,
        verification_function=simple_verification
    )
    
    print(f"Quick diagnostic completed in {report['session_info']['duration_seconds']:.1f} seconds")
    print(f"Success: {report['success_metrics']['solution_implemented']}")

def integration_example():
    """
    Example of integrating diagnostic system with existing code
    """
    
    print("\n" + "=" * 60)
    print("🔌 INTEGRATION EXAMPLE")
    print("=" * 60)
    
    # Example: Adding diagnostics to existing meeting creation function
    from diagnostics import diagnose_function, DiagnosticLogger, diagnostic_context
    
    logger = DiagnosticLogger("meeting_service")
    
    @diagnose_function(logger)
    def create_meeting_with_diagnostics(meeting_data):
        """Example meeting creation with built-in diagnostics"""
        
        with diagnostic_context(logger, "MEETING_CREATION", user_id=meeting_data.get('user_id')):
            
            # Validate input data
            logger.validate_data_integrity(meeting_data, "INPUT_VALIDATION")
            
            if not meeting_data.get('title'):
                raise ValueError("Meeting title is required")
            
            # Simulate meeting creation
            logger.debug_context("create_meeting", {'meeting_data': meeting_data}, "PROCESSING")
            
            time.sleep(0.5)  # Simulate work
            
            meeting_id = f"meeting_{int(time.time())}"
            
            # Log success
            logger.validate_data_integrity(meeting_id, "MEETING_CREATED")
            
            return {"meeting_id": meeting_id, "status": "created"}
    
    # Test the instrumented function
    try:
        result = create_meeting_with_diagnostics({
            "title": "Test Meeting",
            "user_id": "user123",
            "duration": 30
        })
        print(f"Meeting created successfully: {result}")
    except Exception as e:
        print(f"Meeting creation failed: {e}")
    
    # Example of validation failure
    try:
        result = create_meeting_with_diagnostics({
            "user_id": "user123",
            # Missing title - will cause validation error
        })
    except Exception as e:
        print(f"Expected validation error: {e}")

def main():
    """Run all examples"""
    
    print("🎯 ULTIMATE PYTHON BACKEND DIAGNOSTIC SYSTEM v2.0")
    print("Complete Demonstration and Examples")
    print("=" * 60)
    
    try:
        # Run main diagnostic scenario
        example_problem_scenario()
        
        # Run quick diagnostic example
        quick_diagnostic_example()
        
        # Run integration example
        integration_example()
        
        print("\n" + "=" * 60)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("Check the generated log files and reports for detailed information:")
        print("  • example_diagnostics.log - Detailed diagnostic logs")
        print("  • diagnostic_report_*.json - Comprehensive session report")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()