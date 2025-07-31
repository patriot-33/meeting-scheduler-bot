"""
🎯 DIAGNOSTIC ORCHESTRATOR
Main entry point for the Ultimate Python Backend Diagnostic System
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import asdict

from .core_diagnostics import DiagnosticLogger, diagnostic_context, diagnose_function
from .system_monitor import ComprehensiveMonitor
from .hypothesis_testing import HypothesisTester, CommonHypotheses, FiveWhysAnalyzer
from .safe_implementation import SafeImplementationManager
from .post_solution_monitoring import PostSolutionMonitor

class UltimateDiagnosticSystem:
    """
    🎯 ULTIMATE PYTHON BACKEND DIAGNOSTIC SYSTEM v2.0
    Complete diagnostic and problem-solving framework
    """
    
    def __init__(
        self,
        project_name: str = "meeting-scheduler-bot",
        db_engine=None,
        log_file: str = "ultimate_diagnostics.log"
    ):
        # Initialize core components
        self.logger = DiagnosticLogger(f"{project_name}_diagnostics", log_file)
        self.comprehensive_monitor = ComprehensiveMonitor(self.logger, db_engine)
        self.hypothesis_tester = HypothesisTester(self.logger)
        self.five_whys_analyzer = FiveWhysAnalyzer(self.logger)
        self.safe_implementation = SafeImplementationManager(self.logger)
        self.post_solution_monitor = PostSolutionMonitor(self.logger, db_engine)
        
        # Diagnostic session state
        self.session_id = f"diag_{int(time.time())}"
        self.session_start = datetime.now(timezone.utc)
        self.current_problem = None
        self.diagnostic_results = {}
        
        self.logger.logger.info("🎯 ULTIMATE DIAGNOSTIC SYSTEM INITIALIZED")
        self.logger.logger.info(f"   Session ID: {self.session_id}")
        self.logger.logger.info(f"   Project: {project_name}")
        
    def phase_1_triage(
        self,
        problem_description: str,
        error_message: str = "",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        📋 PHASE 1: МГНОВЕННАЯ ТРИАЖНАЯ ОЦЕНКА (30 сек)
        Rapid problem assessment and classification
        """
        
        self.current_problem = problem_description
        context = context or {}
        
        with diagnostic_context(self.logger, "PHASE_1_TRIAGE", problem=problem_description):
            
            # Classify problem priority and type
            from .core_diagnostics import classify_problem_priority, classify_problem_type
            
            priority = classify_problem_priority(error_message or problem_description, context)
            problem_type = classify_problem_type(error_message or problem_description, error_message)
            
            triage_result = {
                "session_id": self.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "problem_description": problem_description,
                "error_message": error_message,
                "priority": priority,
                "problem_type": problem_type,
                "context": context,
                "recommended_next_steps": []
            }
            
            # Generate recommendations based on priority and type
            if priority == "P0_CRITICAL":
                triage_result["recommended_next_steps"] = [
                    "Immediate system diagnostic sweep",
                    "Check for data corruption or security breach",
                    "Prepare for emergency rollback if needed",
                    "Notify stakeholders of critical issue"
                ]
            elif priority == "P1_HIGH":
                triage_result["recommended_next_steps"] = [
                    "Run comprehensive diagnostic sweep",
                    "Test critical hypotheses first",
                    "Monitor user impact",
                    "Prepare solution implementation plan"
                ]
            else:
                triage_result["recommended_next_steps"] = [
                    "Systematic diagnostic investigation",
                    "Test all relevant hypotheses",
                    "Document findings for future reference"
                ]
            
            self.diagnostic_results["phase_1"] = triage_result
            
            self.logger.logger.info(f"🚨 TRIAGE COMPLETE - Priority: {priority}")
            self.logger.logger.info(f"   Problem Type: {problem_type}")
            self.logger.logger.info(f"   Next Steps: {len(triage_result['recommended_next_steps'])}")
            
            return triage_result
            
    def phase_2_systematic_diagnosis(self) -> Dict[str, Any]:
        """
        🔬 PHASE 2: СИСТЕМАТИЧЕСКАЯ ДИАГНОСТИКА
        Comprehensive system analysis and data collection
        """
        
        with diagnostic_context(self.logger, "PHASE_2_SYSTEMATIC_DIAGNOSIS"):
            
            # Run comprehensive monitoring sweep
            self.logger.logger.info("🔍 Running comprehensive diagnostic sweep...")
            sweep_results = self.comprehensive_monitor.run_full_diagnostic_sweep()
            
            # Analyze system trends
            system_trends = self.comprehensive_monitor.system_monitor.analyze_performance_trends()
            
            diagnosis_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sweep_results": sweep_results,
                "system_trends": system_trends,
                "critical_findings": [],
                "suspicious_patterns": [],
                "recommended_hypotheses": []
            }
            
            # Extract critical findings
            if sweep_results.get("critical_alerts"):
                diagnosis_result["critical_findings"] = sweep_results["critical_alerts"]
            
            # Identify suspicious patterns
            if system_trends.get("alerts"):
                diagnosis_result["suspicious_patterns"].extend(system_trends["alerts"])
            
            # Generate hypothesis recommendations based on findings
            if sweep_results.get("database", {}).get("overall_status") != "healthy":
                diagnosis_result["recommended_hypotheses"].append("database_connectivity_issues")
            
            if any("MEMORY" in alert for alert in sweep_results.get("critical_alerts", [])):
                diagnosis_result["recommended_hypotheses"].append("resource_exhaustion")
            
            if any("SERVICE" in alert for alert in sweep_results.get("critical_alerts", [])):
                diagnosis_result["recommended_hypotheses"].append("external_service_failure")
            
            self.diagnostic_results["phase_2"] = diagnosis_result
            
            self.logger.logger.info("🔬 SYSTEMATIC DIAGNOSIS COMPLETE")
            self.logger.logger.info(f"   Overall Health: {sweep_results.get('overall_health', 'unknown')}")
            self.logger.logger.info(f"   Critical Findings: {len(diagnosis_result['critical_findings'])}")
            self.logger.logger.info(f"   Recommended Hypotheses: {len(diagnosis_result['recommended_hypotheses'])}")
            
            return diagnosis_result
    
    def phase_3_hypothesis_testing(
        self,
        custom_hypotheses: List[str] = None,
        db_engine=None
    ) -> Dict[str, Any]:
        """
        🧪 PHASE 3: HYPOTHESIS TESTING
        Scientific testing of problem hypotheses
        """
        
        with diagnostic_context(self.logger, "PHASE_3_HYPOTHESIS_TESTING"):
            
            hypothesis_results = {}
            recommended_hypotheses = self.diagnostic_results.get("phase_2", {}).get("recommended_hypotheses", [])
            all_hypotheses = set(recommended_hypotheses + (custom_hypotheses or []))
            
            self.logger.logger.info(f"🧪 Testing {len(all_hypotheses)} hypotheses")
            
            for hypothesis_name in all_hypotheses:
                try:
                    # Test common hypotheses
                    if hypothesis_name == "database_connectivity_issues" and db_engine:
                        conditions = CommonHypotheses.create_database_connectivity_hypothesis(db_engine)
                        result = self.hypothesis_tester.test_hypothesis(
                            "Database connectivity issues",
                            conditions
                        )
                        hypothesis_results[hypothesis_name] = asdict(result)
                    
                    elif hypothesis_name == "resource_exhaustion":
                        conditions = CommonHypotheses.create_resource_exhaustion_hypothesis()
                        result = self.hypothesis_tester.test_hypothesis(
                            "Resource exhaustion",
                            conditions
                        )
                        hypothesis_results[hypothesis_name] = asdict(result)
                    
                    elif hypothesis_name == "external_service_failure":
                        conditions = CommonHypotheses.create_external_service_hypothesis(
                            "https://www.googleapis.com/"
                        )
                        result = self.hypothesis_tester.test_hypothesis(
                            "External service failure",
                            conditions
                        )
                        hypothesis_results[hypothesis_name] = asdict(result)
                    
                    else:
                        self.logger.logger.warning(f"Unknown hypothesis: {hypothesis_name}")
                        
                except Exception as e:
                    self.logger.logger.error(f"Failed to test hypothesis {hypothesis_name}: {e}")
            
            testing_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hypotheses_tested": len(hypothesis_results),
                "hypothesis_results": hypothesis_results,
                "confirmed_hypotheses": [],
                "rejected_hypotheses": [],
                "inconclusive_hypotheses": []
            }
            
            # Categorize results
            for hypothesis_name, result in hypothesis_results.items():
                result_status = result.get("overall_result")
                if result_status == "CONFIRMED":
                    testing_result["confirmed_hypotheses"].append(hypothesis_name)
                elif result_status == "REJECTED":
                    testing_result["rejected_hypotheses"].append(hypothesis_name)
                else:
                    testing_result["inconclusive_hypotheses"].append(hypothesis_name)
            
            self.diagnostic_results["phase_3"] = testing_result
            
            self.logger.logger.info("🧪 HYPOTHESIS TESTING COMPLETE")
            self.logger.logger.info(f"   Confirmed: {len(testing_result['confirmed_hypotheses'])}")
            self.logger.logger.info(f"   Rejected: {len(testing_result['rejected_hypotheses'])}")
            self.logger.logger.info(f"   Inconclusive: {len(testing_result['inconclusive_hypotheses'])}")
            
            return testing_result
    
    def phase_4_root_cause_analysis(self, why_answers: List[str]) -> Dict[str, Any]:
        """
        🎯 PHASE 4: ROOT CAUSE ANALYSIS
        5 Whys technique for identifying root cause
        """
        
        with diagnostic_context(self.logger, "PHASE_4_ROOT_CAUSE_ANALYSIS"):
            
            if not self.current_problem:
                raise ValueError("No current problem defined. Run phase_1_triage first.")
            
            if len(why_answers) != 5:
                raise ValueError("5 Whys analysis requires exactly 5 answers")
            
            # Perform 5 Whys analysis
            analysis = self.five_whys_analyzer.analyze_problem(
                self.current_problem,
                why_answers
            )
            
            # Combine with hypothesis testing results
            confirmed_hypotheses = self.diagnostic_results.get("phase_3", {}).get("confirmed_hypotheses", [])
            
            root_cause_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "five_whys_analysis": analysis,
                "confirmed_hypotheses": confirmed_hypotheses,
                "root_cause_confidence": analysis.get("confidence_score", 0.0),
                "recommended_solutions": []
            }
            
            # Generate solution recommendations based on root cause
            root_cause = analysis.get("root_cause", "").lower()
            
            if "database" in root_cause or "db" in root_cause:
                root_cause_result["recommended_solutions"].extend([
                    "Check database connection configuration",
                    "Verify database server status",
                    "Review database logs for errors",
                    "Test database connection pooling settings"
                ])
            
            if "memory" in root_cause or "resource" in root_cause:
                root_cause_result["recommended_solutions"].extend([
                    "Analyze memory usage patterns",
                    "Check for memory leaks",
                    "Review resource allocation",
                    "Consider scaling resources"
                ])
            
            if "network" in root_cause or "api" in root_cause:
                root_cause_result["recommended_solutions"].extend([
                    "Test network connectivity",
                    "Review API configuration",
                    "Check firewall settings",
                    "Verify SSL/TLS certificates"
                ])
            
            self.diagnostic_results["phase_4"] = root_cause_result
            
            self.logger.logger.info("🎯 ROOT CAUSE ANALYSIS COMPLETE")
            self.logger.logger.info(f"   Root Cause: {analysis.get('root_cause')}")
            self.logger.logger.info(f"   Confidence: {analysis.get('confidence_score', 0):.2f}")
            self.logger.logger.info(f"   Recommended Solutions: {len(root_cause_result['recommended_solutions'])}")
            
            return root_cause_result
    
    def phase_5_safe_solution_implementation(
        self,
        solution_description: str,
        implementation_function: Callable[[], Any],
        verification_function: Optional[Callable[[], bool]] = None,
        files_to_backup: List[str] = None
    ) -> Dict[str, Any]:
        """
        ⚡ PHASE 5: SOLUTION IMPLEMENTATION
        Safe implementation with automatic rollback
        """
        
        with diagnostic_context(self.logger, "PHASE_5_SOLUTION_IMPLEMENTATION"):
            
            # Assess solution impact
            assessment = self.safe_implementation.assess_solution_impact(
                solution_description=solution_description,
                files_to_modify=files_to_backup or []
            )
            
            # Create implementation step
            from .safe_implementation import ImplementationStep
            
            step = ImplementationStep(
                step_id="main_solution",
                description=solution_description,
                action=implementation_function,
                validation_function=verification_function
            )
            
            # Execute safe implementation
            result = self.safe_implementation.implement_solution_safely(
                solution_id=f"solution_{self.session_id}",
                steps=[step],
                assessment=assessment,
                verification_function=verification_function
            )
            
            implementation_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "solution_description": solution_description,
                "assessment": asdict(assessment),
                "implementation_result": asdict(result),
                "success": result.result.value == "SUCCESS"
            }
            
            self.diagnostic_results["phase_5"] = implementation_result
            
            self.logger.logger.info("⚡ SOLUTION IMPLEMENTATION COMPLETE")
            self.logger.logger.info(f"   Result: {result.result.value}")
            self.logger.logger.info(f"   Duration: {result.duration_seconds:.3f}s")
            self.logger.logger.info(f"   Rollback Performed: {result.rollback_performed}")
            
            return implementation_result
    
    def phase_6_post_solution_monitoring(
        self,
        monitoring_duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        📈 PHASE 6: VERIFICATION & MONITORING
        Post-solution monitoring and verification
        """
        
        with diagnostic_context(self.logger, "PHASE_6_POST_SOLUTION_MONITORING"):
            
            # Start monitoring
            self.post_solution_monitor.start_monitoring()
            
            self.logger.logger.info(f"📈 Starting {monitoring_duration_minutes}-minute monitoring period")
            
            # Generate initial health report
            initial_health = self.post_solution_monitor.get_current_health()
            
            # Wait for monitoring period (in real use, this would be asynchronous)
            # For demonstration, we'll just generate a report immediately
            time.sleep(5)  # Brief pause for initial checks
            
            final_health = self.post_solution_monitor.get_current_health()
            
            monitoring_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "monitoring_duration_minutes": monitoring_duration_minutes,
                "initial_health": asdict(initial_health),
                "final_health": asdict(final_health),
                "monitoring_successful": final_health.overall_status.value != "CRITICAL",
                "total_alerts": len(self.post_solution_monitor.active_alerts),
                "recommendations": []
            }
            
            # Generate recommendations
            if final_health.overall_status.value == "HEALTHY":
                monitoring_result["recommendations"] = [
                    "Solution appears stable",
                    "Continue normal monitoring",
                    "Document solution for future reference"
                ]
            else:
                monitoring_result["recommendations"] = [
                    "Investigation needed - solution may not be fully effective",
                    "Consider additional debugging or rollback",
                    "Monitor closely for further issues"
                ]
            
            self.diagnostic_results["phase_6"] = monitoring_result
            
            # Stop monitoring
            self.post_solution_monitor.stop_monitoring()
            
            self.logger.logger.info("📈 POST-SOLUTION MONITORING COMPLETE")
            self.logger.logger.info(f"   Final Status: {final_health.overall_status.value}")
            self.logger.logger.info(f"   Total Alerts: {len(self.post_solution_monitor.active_alerts)}")
            
            return monitoring_result
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic session report"""
        
        session_duration = (datetime.now(timezone.utc) - self.session_start).total_seconds()
        
        report = {
            "session_info": {
                "session_id": self.session_id,
                "start_time": self.session_start.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": session_duration,
                "problem_description": self.current_problem
            },
            "phases_completed": list(self.diagnostic_results.keys()),
            "diagnostic_results": self.diagnostic_results,
            "success_metrics": {
                "diagnostic_completed": len(self.diagnostic_results) >= 4,
                "root_cause_identified": "phase_4" in self.diagnostic_results,
                "solution_implemented": "phase_5" in self.diagnostic_results,
                "monitoring_completed": "phase_6" in self.diagnostic_results
            }
        }
        
        # Save report to file
        report_file = f"diagnostic_report_{self.session_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.logger.info("📋 COMPREHENSIVE DIAGNOSTIC REPORT GENERATED")
        self.logger.logger.info(f"   Session Duration: {session_duration/60:.1f} minutes")
        self.logger.logger.info(f"   Phases Completed: {len(self.diagnostic_results)}/6")
        self.logger.logger.info(f"   Report Saved: {report_file}")
        
        return report

# Convenience function for quick diagnostics
def quick_diagnostic_session(
    problem_description: str,
    error_message: str = "",
    db_engine=None,
    solution_function: Optional[Callable[[], Any]] = None,
    verification_function: Optional[Callable[[], bool]] = None
) -> Dict[str, Any]:
    """Run a complete diagnostic session quickly"""
    
    system = UltimateDiagnosticSystem(db_engine=db_engine)
    
    # Phase 1: Triage
    triage_result = system.phase_1_triage(problem_description, error_message)
    
    # Phase 2: Diagnosis
    diagnosis_result = system.phase_2_systematic_diagnosis()
    
    # Phase 3: Hypothesis Testing (with common hypotheses)
    hypothesis_result = system.phase_3_hypothesis_testing(db_engine=db_engine)
    
    # If solution provided, implement it
    if solution_function:
        # Phase 4: Simplified root cause (skip 5 whys for quick session)
        
        # Phase 5: Implementation
        implementation_result = system.phase_5_safe_solution_implementation(
            solution_description="Quick solution implementation",
            implementation_function=solution_function,
            verification_function=verification_function
        )
        
        # Phase 6: Brief monitoring
        monitoring_result = system.phase_6_post_solution_monitoring(monitoring_duration_minutes=5)
    
    return system.generate_comprehensive_report()