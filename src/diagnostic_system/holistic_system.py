"""
🛡️ HOLISTIC DIAGNOSTIC SYSTEM - Main orchestrator
Coordinates all diagnostic and repair components for comprehensive system health management.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from datetime import datetime
import json
import time

from .system_analyzer import SystemAnalyzer
from .invariant_detector import InvariantDetector
from .deep_diagnostics import DeepDiagnostics
from .safe_repair_engine import SafeRepairEngine
from .continuous_validator import ContinuousValidator
from .change_documentation import ChangeDocumentationSystem

logger = logging.getLogger(__name__)

class HolisticDiagnosticSystem:
    """
    Main orchestrator for the holistic diagnostic and repair system.
    
    This class coordinates all components to provide comprehensive system analysis,
    safe repair operations, and continuous learning capabilities.
    
    Key principles:
    1. SAFETY FIRST - Never make changes without understanding full impact
    2. COMPREHENSIVE ANALYSIS - Understand the system before making changes
    3. INCREMENTAL FIXES - Small, reversible changes with validation
    4. CONTINUOUS LEARNING - Learn from every operation
    5. HOLISTIC APPROACH - Consider the entire system, not just individual components
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
        # Initialize all components
        logger.info("🛡️ Initializing Holistic Diagnostic System...")
        
        # Core analysis components
        self.system_analyzer = SystemAnalyzer(str(self.project_root))
        logger.info("✅ SystemAnalyzer initialized")
        
        self.invariant_detector = InvariantDetector(str(self.project_root))
        logger.info("✅ InvariantDetector initialized")
        
        self.deep_diagnostics = DeepDiagnostics(str(self.project_root), self.system_analyzer)
        logger.info("✅ DeepDiagnostics initialized")
        
        # Repair and monitoring components
        self.safe_repair_engine = SafeRepairEngine(str(self.project_root), self.system_analyzer)
        logger.info("✅ SafeRepairEngine initialized")
        
        self.continuous_validator = ContinuousValidator(
            str(self.project_root), 
            self.system_analyzer, 
            self.invariant_detector
        )
        logger.info("✅ ContinuousValidator initialized")
        
        # Documentation and learning
        self.documentation = ChangeDocumentationSystem(str(self.project_root))
        logger.info("✅ ChangeDocumentationSystem initialized")
        
        # System state
        self.system_map: Optional[Dict[str, Any]] = None
        self.system_invariants: Optional[Dict[str, Any]] = None
        self.monitoring_active = False
        
        logger.info("🛡️ Holistic Diagnostic System initialization complete")
    
    async def diagnose_and_fix_safely(self, problem_description: str, 
                                     severity: str = "unknown",
                                     auto_fix: bool = True) -> Dict[str, Any]:
        """
        Main entry point: Complete diagnosis and safe repair workflow.
        
        This method orchestrates the entire process:
        1. System analysis and mapping
        2. Problem diagnosis across multiple layers
        3. Solution hypothesis generation and testing
        4. Safe, incremental repair application
        5. Continuous monitoring and validation
        6. Complete documentation and learning
        
        Args:
            problem_description: Description of the problem to diagnose and fix
            severity: Problem severity ("low", "medium", "high", "critical")
            auto_fix: Whether to automatically apply fixes or just diagnose
            
        Returns:
            Complete workflow results including diagnosis, fixes applied, and system state
        """
        logger.info(f"🛡️ Starting holistic diagnosis and repair: {problem_description}")
        workflow_start = datetime.now()
        
        # Start documentation session
        session_id = self.documentation.start_diagnostic_session(problem_description, severity)
        
        workflow_result = {
            "session_id": session_id,
            "workflow_start": workflow_start.isoformat(),
            "problem_description": problem_description,
            "severity": severity,
            "auto_fix_enabled": auto_fix,
            "phases_completed": [],
            "final_status": "unknown",
            "total_duration_seconds": 0,
            "system_health_before": 0.0,
            "system_health_after": 0.0,
            "changes_applied": [],
            "rollbacks_performed": [],
            "lessons_learned": [],
            "recommendations": []
        }
        
        try:
            # PHASE 0: SYSTEM CONTEXT MAPPING (MANDATORY)
            logger.info("🗺️ PHASE 0: System Context Mapping")
            phase_start = time.time()
            
            await self._ensure_system_mapped()
            workflow_result["system_health_before"] = self.system_map.get("system_health_score", 0.0)
            
            self.documentation.record_diagnostic_step(
                "system_mapping", 
                "complete_system", 
                [f"Mapped {self.system_map.get('total_components', 0)} components"],
                confidence=0.9,
                tools_used=["SystemAnalyzer"]
            )
            
            phase_duration = time.time() - phase_start
            workflow_result["phases_completed"].append({
                "phase": "system_mapping",
                "duration_seconds": phase_duration,
                "status": "completed"
            })
            
            # PHASE 1: START CONTINUOUS MONITORING
            logger.info("📊 PHASE 1: Starting Continuous Monitoring")
            phase_start = time.time()
            
            await self.start_monitoring()
            
            phase_duration = time.time() - phase_start
            workflow_result["phases_completed"].append({
                "phase": "start_monitoring",
                "duration_seconds": phase_duration,
                "status": "completed"
            })
            
            # PHASE 2: COMPREHENSIVE DIAGNOSTICS
            logger.info("🔍 PHASE 2: Multi-Layer Diagnostics")
            phase_start = time.time()
            
            diagnostic_results = await self.run_diagnostics(problem_description)
            
            # Record diagnostic findings
            for layer_name, layer_result in diagnostic_results.get("layer_results", {}).items():
                findings = layer_result.get("findings", [])
                self.documentation.record_diagnostic_step(
                    f"diagnostic_{layer_name}",
                    layer_name,
                    [f.get("title", "") for f in findings[:5]],  # Top 5 findings
                    confidence=layer_result.get("confidence", 0.5),
                    tools_used=["DeepDiagnostics"]
                )
            
            phase_duration = time.time() - phase_start
            workflow_result["phases_completed"].append({
                "phase": "diagnostics",
                "duration_seconds": phase_duration,
                "status": "completed",
                "results": diagnostic_results
            })
            
            # PHASE 3: SOLUTION GENERATION AND TESTING
            logger.info("🧪 PHASE 3: Solution Generation and Testing")
            phase_start = time.time()
            
            solution_hypotheses = await self._generate_solution_hypotheses(diagnostic_results)
            tested_solutions = await self._test_solution_hypotheses(solution_hypotheses)
            
            # Record hypothesis testing
            for hypothesis in tested_solutions:
                self.documentation.record_hypothesis_test(
                    hypothesis["description"],
                    hypothesis["test_method"],
                    hypothesis["viable"],
                    hypothesis.get("evidence", {})
                )
            
            phase_duration = time.time() - phase_start
            workflow_result["phases_completed"].append({
                "phase": "solution_testing",
                "duration_seconds": phase_duration,
                "status": "completed",
                "hypotheses_tested": len(tested_solutions),
                "viable_solutions": len([h for h in tested_solutions if h["viable"]])
            })
            
            # PHASE 4: SAFE REPAIR APPLICATION (if auto_fix enabled)
            if auto_fix:
                logger.info("🔧 PHASE 4: Safe Repair Application")
                phase_start = time.time()
                
                viable_solutions = [h for h in tested_solutions if h["viable"]]
                
                if viable_solutions:
                    # Select best solution
                    best_solution = max(viable_solutions, key=lambda x: x.get("confidence", 0))
                    
                    # Apply fix
                    repair_result = await self._apply_solution_safely(best_solution)
                    workflow_result["changes_applied"] = repair_result.get("atomic_changes", [])
                    workflow_result["rollbacks_performed"] = repair_result.get("rollback_points", [])
                    
                    if repair_result["status"] == "completed":
                        workflow_result["final_status"] = "success"
                    else:
                        workflow_result["final_status"] = "partial_success"
                        workflow_result["repair_issues"] = repair_result.get("error_details", {})
                else:
                    logger.warning("⚠️ No viable solutions found")
                    workflow_result["final_status"] = "no_solution_found"
                
                phase_duration = time.time() - phase_start
                workflow_result["phases_completed"].append({
                    "phase": "repair_application",
                    "duration_seconds": phase_duration,
                    "status": "completed" if viable_solutions else "no_solutions"
                })
            else:
                workflow_result["final_status"] = "diagnosis_only"
                logger.info("ℹ️ Auto-fix disabled - diagnosis only")
            
            # PHASE 5: FINAL VALIDATION AND HEALTH CHECK
            logger.info("🏥 PHASE 5: Final Validation and Health Check")
            phase_start = time.time()
            
            # Wait a moment for system to stabilize
            await asyncio.sleep(5)
            
            final_health = await self._assess_final_system_health()
            workflow_result["system_health_after"] = final_health.get("overall_health_score", 0.0)
            workflow_result["final_health_report"] = final_health
            
            phase_duration = time.time() - phase_start
            workflow_result["phases_completed"].append({
                "phase": "final_validation",
                "duration_seconds": phase_duration,
                "status": "completed"
            })
            
            # PHASE 6: LEARNING AND DOCUMENTATION
            logger.info("📚 PHASE 6: Learning and Documentation")
            phase_start = time.time()
            
            lessons_learned = await self._extract_lessons_learned(workflow_result)
            workflow_result["lessons_learned"] = lessons_learned
            
            recommendations = await self._generate_recommendations(workflow_result)
            workflow_result["recommendations"] = recommendations
            
            phase_duration = time.time() - phase_start
            workflow_result["phases_completed"].append({
                "phase": "learning_documentation",
                "duration_seconds": phase_duration,
                "status": "completed"
            })
            
            # Calculate total duration
            total_duration = (datetime.now() - workflow_start).total_seconds()
            workflow_result["total_duration_seconds"] = total_duration
            workflow_result["workflow_end"] = datetime.now().isoformat()
            
            # End documentation session
            final_status = workflow_result["final_status"]
            self.documentation.end_diagnostic_session(final_status, lessons_learned)
            
            logger.info(f"✅ Holistic diagnosis and repair completed: {final_status} in {total_duration:.1f}s")
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"❌ Holistic diagnosis and repair failed: {e}")
            workflow_result["final_status"] = "failed"
            workflow_result["error"] = str(e)
            
            # End session with failure status
            self.documentation.end_diagnostic_session("failed", [f"Workflow failed: {str(e)}"])
            
            return workflow_result
        
        finally:
            # Always stop monitoring
            try:
                await self.stop_monitoring()
            except Exception as e:
                logger.error(f"❌ Failed to stop monitoring: {e}")
    
    async def run_diagnostics(self, problem_description: str) -> Dict[str, Any]:
        """Run comprehensive diagnostics without applying fixes"""
        logger.info("🔍 Running comprehensive diagnostics...")
        
        # Ensure system is mapped
        await self._ensure_system_mapped()
        
        # Ensure invariants are detected
        await self._ensure_invariants_detected()
        
        # Run deep diagnostics
        problem_context = {
            "description": problem_description,
            "system_map": self.system_map,
            "invariants": self.system_invariants,
            "timestamp": datetime.now().isoformat()
        }
        
        diagnostic_results = await self.deep_diagnostics.run_complete_diagnostics(problem_context)
        
        # Add learned patterns to results
        pattern_suggestions = self.documentation.suggest_solutions(problem_description)
        diagnostic_results["learned_pattern_suggestions"] = pattern_suggestions
        
        return diagnostic_results
    
    async def apply_fix_safely(self, fix_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a fix plan safely with full monitoring and rollback capability"""
        logger.info("🔧 Applying fix plan safely...")
        
        # Ensure monitoring is active
        if not self.monitoring_active:
            await self.start_monitoring()
        
        # Apply fix using safe repair engine
        repair_result = await self.safe_repair_engine.apply_fix_safely(fix_plan)
        
        # Document the changes
        if repair_result.get("atomic_changes"):
            for change_id in repair_result["atomic_changes"]:
                # This would need more detailed change information in a real implementation
                self.documentation.record_change({
                    "type": "automated_fix",
                    "description": f"Fix applied via safe repair engine: {change_id}",
                    "change_id": change_id,
                    "fix_plan": fix_plan
                })
        
        return repair_result
    
    async def start_monitoring(self):
        """Start continuous system monitoring"""
        if self.monitoring_active:
            logger.info("📊 Monitoring already active")
            return
        
        logger.info("📊 Starting continuous monitoring...")
        
        # Start continuous validator
        await self.continuous_validator.start_monitoring()
        self.monitoring_active = True
        
        logger.info("✅ Continuous monitoring started")
    
    async def stop_monitoring(self):
        """Stop continuous system monitoring"""
        if not self.monitoring_active:
            return
        
        logger.info("📊 Stopping continuous monitoring...")
        
        # Stop continuous validator
        await self.continuous_validator.stop_monitoring()
        self.monitoring_active = False
        
        logger.info("✅ Continuous monitoring stopped")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health report"""
        if self.monitoring_active:
            return self.continuous_validator.generate_health_report()
        else:
            # Generate basic health report without active monitoring
            return {
                "overall_health": {
                    "score": self.system_map.get("system_health_score", 0.5) if self.system_map else 0.5,
                    "status": "unknown",
                    "description": "Monitoring not active - limited health information available"
                },
                "monitoring_status": {
                    "active": False,
                    "message": "Start monitoring for detailed health information"
                },
                "system_analysis": self.system_map,
                "learned_patterns": len(self.documentation.learned_patterns)
            }
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about all diagnostic sessions"""
        return self.documentation.get_session_statistics()
    
    async def _ensure_system_mapped(self):
        """Ensure complete system mapping is available"""
        if self.system_map is None:
            logger.info("🗺️ Performing complete system analysis...")
            self.system_map = self.system_analyzer.analyze_complete_system()
            logger.info(f"✅ System mapped: {self.system_map.get('total_components', 0)} components")
    
    async def _ensure_invariants_detected(self):
        """Ensure system invariants are detected"""
        if self.system_invariants is None:
            logger.info("🔍 Detecting system invariants...")
            self.system_invariants = self.invariant_detector.detect_invariants()
            total_invariants = sum(len(invs) for invs in self.system_invariants.values())
            logger.info(f"✅ Detected {total_invariants} system invariants")
    
    async def _generate_solution_hypotheses(self, diagnostic_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate solution hypotheses based on diagnostic results"""
        hypotheses = []
        
        # Extract critical findings from diagnostics
        critical_findings = []
        for layer_name, layer_result in diagnostic_results.get("layer_results", {}).items():
            if layer_result.get("critical_finding"):
                critical_findings.append({
                    "layer": layer_name,
                    "finding": layer_result["critical_finding"]
                })
        
        # Generate hypotheses for each critical finding
        for critical_finding in critical_findings:
            finding = critical_finding["finding"]
            
            # Generate specific hypotheses based on finding category
            if finding.get("category") == "performance":
                hypotheses.append({
                    "id": f"perf_hypothesis_{len(hypotheses)}",
                    "description": f"Performance issue in {finding.get('title', 'unknown area')}",
                    "approach": "performance_optimization",
                    "target_finding": finding,
                    "confidence": 0.7,
                    "estimated_impact": "medium"
                })
            
            elif finding.get("category") == "error":
                hypotheses.append({
                    "id": f"error_hypothesis_{len(hypotheses)}",
                    "description": f"Error handling issue: {finding.get('title', 'unknown error')}",
                    "approach": "error_correction",
                    "target_finding": finding,
                    "confidence": 0.8,
                    "estimated_impact": "high"
                })
            
            elif finding.get("category") == "security":
                hypotheses.append({
                    "id": f"security_hypothesis_{len(hypotheses)}",
                    "description": f"Security vulnerability: {finding.get('title', 'unknown vulnerability')}",
                    "approach": "security_hardening",
                    "target_finding": finding,
                    "confidence": 0.9,
                    "estimated_impact": "critical"
                })
        
        # Add hypotheses from learned patterns
        pattern_suggestions = diagnostic_results.get("learned_pattern_suggestions", [])
        for suggestion in pattern_suggestions[:3]:  # Top 3 suggestions
            hypotheses.append({
                "id": f"pattern_hypothesis_{len(hypotheses)}",
                "description": f"Apply learned pattern: {suggestion['description'][:100]}",
                "approach": "learned_pattern",
                "pattern_data": suggestion,
                "confidence": suggestion["confidence"],
                "estimated_impact": "medium"
            })
        
        # If no specific hypotheses, generate generic ones
        if not hypotheses:
            hypotheses.append({
                "id": "generic_hypothesis_1",
                "description": "Generic system optimization and cleanup",
                "approach": "general_optimization",
                "confidence": 0.5,
                "estimated_impact": "low"
            })
        
        logger.info(f"💡 Generated {len(hypotheses)} solution hypotheses")
        return hypotheses
    
    async def _test_solution_hypotheses(self, hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test solution hypotheses in isolation"""
        tested_hypotheses = []
        
        for hypothesis in hypotheses:
            logger.info(f"🧪 Testing hypothesis: {hypothesis['description']}")
            
            test_result = {
                **hypothesis,
                "test_timestamp": datetime.now().isoformat(),
                "test_method": "simulation",
                "viable": False,
                "evidence": {},
                "risks": [],
                "estimated_time": 60  # Default 1 minute
            }
            
            try:
                # Simulate testing (in a real implementation, this would use the SafeRepairEngine's
                # isolated testing capabilities)
                
                # Basic viability checks
                if hypothesis.get("confidence", 0) > 0.6:
                    test_result["viable"] = True
                    test_result["evidence"]["confidence_check"] = "passed"
                else:
                    test_result["evidence"]["confidence_check"] = "failed"
                
                # Check if we have resources to implement
                if hypothesis.get("estimated_impact") != "critical":
                    test_result["evidence"]["resource_check"] = "passed"
                else:
                    test_result["evidence"]["resource_check"] = "requires_review"
                
                # Pattern-based hypotheses are generally safer
                if hypothesis.get("approach") == "learned_pattern":
                    test_result["viable"] = True
                    test_result["evidence"]["pattern_based"] = "trusted"
                
                # Security issues should be viable to fix
                if hypothesis.get("approach") == "security_hardening":
                    test_result["viable"] = True
                    test_result["evidence"]["security_priority"] = "high"
                
                logger.info(f"🧪 Hypothesis test result: {'viable' if test_result['viable'] else 'not viable'}")
                
            except Exception as e:
                logger.error(f"❌ Hypothesis testing failed: {e}")
                test_result["test_error"] = str(e)
            
            tested_hypotheses.append(test_result)
        
        viable_count = len([h for h in tested_hypotheses if h["viable"]])
        logger.info(f"🧪 Hypothesis testing complete: {viable_count}/{len(tested_hypotheses)} viable")
        
        return tested_hypotheses
    
    async def _apply_solution_safely(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a solution using the safe repair engine"""
        logger.info(f"🔧 Applying solution: {solution['description']}")
        
        # Convert solution to fix plan format
        fix_plan = self._convert_solution_to_fix_plan(solution)
        
        # Apply using safe repair engine
        return await self.safe_repair_engine.apply_fix_safely(fix_plan)
    
    def _convert_solution_to_fix_plan(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a solution hypothesis to a fix plan"""
        fix_plan = {
            "description": solution["description"],
            "approach": solution.get("approach", "unknown"),
            "confidence": solution.get("confidence", 0.5),
            "estimated_impact": solution.get("estimated_impact", "medium")
        }
        
        # Add specific actions based on solution type
        if solution.get("approach") == "learned_pattern":
            pattern_data = solution.get("pattern_data", {})
            fix_plan["code_changes"] = {}
            
            # This would be more sophisticated in a real implementation
            for suggested_solution in pattern_data.get("suggested_solutions", []):
                if ":" in suggested_solution:
                    change_type, description = suggested_solution.split(":", 1)
                    if change_type.strip() == "code_modification":
                        fix_plan["code_changes"]["generic_file.py"] = [{
                            "description": description.strip(),
                            "operation": "edit"
                        }]
                        
        elif solution.get("approach") == "performance_optimization":
            fix_plan["code_changes"] = {
                "performance_target.py": [{
                    "description": "Performance optimization",
                    "operation": "edit"
                }]
            }
            
        elif solution.get("approach") == "error_correction":
            fix_plan["code_changes"] = {
                "error_target.py": [{
                    "description": "Error handling improvement",
                    "operation": "edit"
                }]
            }
        
        elif solution.get("approach") == "security_hardening":
            fix_plan["config_changes"] = [{
                "description": "Security configuration update",
                "file_path": "config.py"
            }]
        
        else:
            # Generic optimization
            fix_plan["code_changes"] = {
                "main.py": [{
                    "description": "General system optimization",
                    "operation": "edit"
                }]
            }
        
        return fix_plan
    
    async def _assess_final_system_health(self) -> Dict[str, Any]:
        """Assess final system health after repairs"""
        health_report = self.continuous_validator.generate_health_report()
        
        # Add system analysis health if monitoring isn't providing it
        if self.system_map:
            health_report["system_analysis_health"] = {
                "system_health_score": self.system_map.get("system_health_score", 0.5),
                "total_components": self.system_map.get("total_components", 0),
                "high_risk_modules": len(self.system_map.get("high_risk_modules", []))
            }
        
        return health_report
    
    async def _extract_lessons_learned(self, workflow_result: Dict[str, Any]) -> List[str]:
        """Extract lessons learned from the workflow"""
        lessons = []
        
        # Analyze what worked
        if workflow_result["final_status"] == "success":
            lessons.append("✅ Holistic approach successfully resolved the issue")
            
            if workflow_result.get("changes_applied"):
                lessons.append(f"✅ Applied {len(workflow_result['changes_applied'])} changes successfully")
            
            health_improvement = (
                workflow_result["system_health_after"] - workflow_result["system_health_before"]
            )
            if health_improvement > 0:
                lessons.append(f"✅ System health improved by {health_improvement:.2f}")
        
        # Analyze what could be improved
        total_duration = workflow_result["total_duration_seconds"]
        if total_duration > 300:  # More than 5 minutes
            lessons.append("⚠️ Workflow took longer than expected - consider optimization")
        
        # Check if rollbacks were needed
        if workflow_result.get("rollbacks_performed"):
            lessons.append("⚠️ Rollbacks were required - need better pre-flight validation")
        
        # Analyze phase performance
        for phase in workflow_result.get("phases_completed", []):
            if phase.get("duration_seconds", 0) > 60:  # More than 1 minute
                lessons.append(f"⚠️ {phase['phase']} phase took {phase['duration_seconds']:.1f}s - consider optimization")
        
        return lessons
    
    async def _generate_recommendations(self, workflow_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on workflow results"""
        recommendations = []
        
        # Health-based recommendations
        final_health = workflow_result["system_health_after"]
        if final_health < 0.6:
            recommendations.append("🏥 System health is still below optimal - consider additional improvements")
        elif final_health > 0.9:
            recommendations.append("✅ Excellent system health - maintain current practices")
        
        # Performance recommendations
        if workflow_result["total_duration_seconds"] > 600:  # More than 10 minutes
            recommendations.append("⚡ Consider implementing faster diagnostic methods for quicker resolution")
        
        # Success pattern recommendations
        if workflow_result["final_status"] == "success":
            recommendations.append("📖 Document this successful pattern for future similar issues")
        
        # Monitoring recommendations
        if not self.monitoring_active:
            recommendations.append("📊 Enable continuous monitoring for proactive issue detection")
        
        # Learning recommendations
        pattern_count = len(self.documentation.learned_patterns)
        if pattern_count < 5:
            recommendations.append("🧠 Continue building pattern library for better future diagnostics")
        
        return recommendations