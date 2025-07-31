"""
🧪 HYPOTHESIS TESTING FRAMEWORK
Scientific approach to debugging and problem-solving
"""

import time
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager

from .core_diagnostics import DiagnosticLogger, diagnostic_context

class HypothesisResult(Enum):
    """Possible hypothesis test results"""
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    ERROR = "ERROR"

@dataclass
class TestCondition:
    """Individual test condition within a hypothesis"""
    name: str
    test_function: Callable[[], Any]
    expected_result: Any
    comparison_type: str = "equals"  # equals, greater_than, less_than, contains, not_null
    timeout_seconds: float = 30.0

@dataclass 
class HypothesisTestResult:
    """Result of a hypothesis test"""
    hypothesis_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    overall_result: HypothesisResult
    conditions_tested: int
    conditions_passed: int
    conditions_failed: int
    test_details: List[Dict[str, Any]]
    conclusion: str
    recommendations: List[str]
    error_message: Optional[str] = None

class HypothesisTester:
    """Framework for systematic hypothesis testing"""
    
    def __init__(self, logger: DiagnosticLogger):
        self.logger = logger
        self.test_history: List[HypothesisTestResult] = []
        
    def test_hypothesis(
        self, 
        hypothesis_name: str, 
        conditions: List[TestCondition],
        required_success_rate: float = 1.0
    ) -> HypothesisTestResult:
        """Test a hypothesis with multiple conditions"""
        
        start_time = datetime.now(timezone.utc)
        start_time_str = start_time.isoformat()
        
        self.logger.logger.info(f"🧪 TESTING HYPOTHESIS: {hypothesis_name}")
        self.logger.logger.info(f"   Conditions to test: {len(conditions)}")
        self.logger.logger.info(f"   Required success rate: {required_success_rate * 100}%")
        
        test_details = []
        conditions_passed = 0
        conditions_failed = 0
        overall_result = HypothesisResult.INCONCLUSIVE
        error_message = None
        
        try:
            for i, condition in enumerate(conditions, 1):
                self.logger.logger.debug(f"   Testing condition {i}/{len(conditions)}: {condition.name}")
                
                condition_result = self._test_single_condition(condition)
                test_details.append(condition_result)
                
                if condition_result["result"] == "PASSED":
                    conditions_passed += 1
                    self.logger.logger.debug(f"   ✅ PASSED: {condition.name}")
                else:
                    conditions_failed += 1
                    self.logger.logger.debug(f"   ❌ FAILED: {condition.name} - {condition_result.get('error', 'Unexpected result')}")
            
            # Determine overall result
            success_rate = conditions_passed / len(conditions) if conditions else 0
            
            if success_rate >= required_success_rate:
                overall_result = HypothesisResult.CONFIRMED
                conclusion = f"Hypothesis CONFIRMED with {success_rate * 100:.1f}% success rate"
            elif success_rate == 0:
                overall_result = HypothesisResult.REJECTED
                conclusion = f"Hypothesis REJECTED - no conditions passed"
            else:
                overall_result = HypothesisResult.INCONCLUSIVE
                conclusion = f"Hypothesis INCONCLUSIVE - {success_rate * 100:.1f}% success rate (required: {required_success_rate * 100}%)"
                
        except Exception as e:
            overall_result = HypothesisResult.ERROR
            error_message = str(e)
            conclusion = f"Hypothesis testing failed due to error: {error_message}"
            self.logger.logger.error(f"❌ Hypothesis testing error: {e}")
        
        # Calculate duration
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Create result object
        result = HypothesisTestResult(
            hypothesis_name=hypothesis_name,
            start_time=start_time_str,
            end_time=end_time.isoformat(),
            duration_seconds=round(duration, 3),
            overall_result=overall_result,
            conditions_tested=len(conditions),
            conditions_passed=conditions_passed,
            conditions_failed=conditions_failed,
            test_details=test_details,
            conclusion=conclusion,
            recommendations=self._generate_recommendations(overall_result, test_details),
            error_message=error_message
        )
        
        # Store in history
        self.test_history.append(result)
        
        # Log final result
        self.logger.logger.info(f"🏁 HYPOTHESIS RESULT: {hypothesis_name}")
        self.logger.logger.info(f"   Status: {overall_result.value}")
        self.logger.logger.info(f"   Success rate: {conditions_passed}/{len(conditions)} ({(conditions_passed/len(conditions)*100) if conditions else 0:.1f}%)")
        self.logger.logger.info(f"   Duration: {duration:.3f}s")
        self.logger.logger.info(f"   Conclusion: {conclusion}")
        
        if result.recommendations:
            self.logger.logger.info("   Recommendations:")
            for rec in result.recommendations:
                self.logger.logger.info(f"     • {rec}")
        
        return result
    
    def _test_single_condition(self, condition: TestCondition) -> Dict[str, Any]:
        """Test a single condition"""
        start_time = time.time()
        
        condition_result = {
            "name": condition.name,
            "expected": condition.expected_result,
            "actual": None,
            "comparison_type": condition.comparison_type,
            "result": "FAILED",
            "duration_seconds": 0,
            "error": None
        }
        
        try:
            # Execute test function with timeout
            if asyncio.iscoroutinefunction(condition.test_function):
                # Handle async functions
                actual_result = asyncio.run(
                    asyncio.wait_for(
                        condition.test_function(),
                        timeout=condition.timeout_seconds
                    )
                )
            else:
                # Handle sync functions
                actual_result = condition.test_function()
            
            condition_result["actual"] = actual_result
            
            # Compare results based on comparison type
            passed = self._compare_results(
                actual_result, 
                condition.expected_result, 
                condition.comparison_type
            )
            
            condition_result["result"] = "PASSED" if passed else "FAILED"
            
        except asyncio.TimeoutError:
            condition_result["error"] = f"Test timed out after {condition.timeout_seconds}s"
        except Exception as e:
            condition_result["error"] = str(e)
        
        condition_result["duration_seconds"] = round(time.time() - start_time, 3)
        return condition_result
    
    def _compare_results(self, actual: Any, expected: Any, comparison_type: str) -> bool:
        """Compare actual vs expected results based on comparison type"""
        try:
            if comparison_type == "equals":
                return actual == expected
            elif comparison_type == "greater_than":
                return actual > expected
            elif comparison_type == "less_than":
                return actual < expected
            elif comparison_type == "greater_equal":
                return actual >= expected
            elif comparison_type == "less_equal":
                return actual <= expected
            elif comparison_type == "contains":
                return expected in actual
            elif comparison_type == "not_contains":
                return expected not in actual
            elif comparison_type == "not_null":
                return actual is not None
            elif comparison_type == "is_null":
                return actual is None
            elif comparison_type == "is_true":
                return bool(actual) is True
            elif comparison_type == "is_false":
                return bool(actual) is False
            else:
                raise ValueError(f"Unknown comparison type: {comparison_type}")
        except Exception:
            return False
    
    def _generate_recommendations(self, result: HypothesisResult, test_details: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if result == HypothesisResult.CONFIRMED:
            recommendations.append("Hypothesis confirmed - focus investigation on other areas")
            recommendations.append("Consider this as established fact for future debugging")
        
        elif result == HypothesisResult.REJECTED:
            recommendations.append("Hypothesis rejected - this is NOT the root cause")
            recommendations.append("Investigate alternative hypotheses")
            failed_conditions = [t for t in test_details if t["result"] == "FAILED"]
            if failed_conditions:
                recommendations.append(f"Failed conditions suggest looking into: {', '.join([t['name'] for t in failed_conditions[:3]])}")
        
        elif result == HypothesisResult.INCONCLUSIVE:
            recommendations.append("Results are inconclusive - need more specific tests")
            recommendations.append("Consider refining hypothesis or adding more test conditions")
            passed_conditions = [t for t in test_details if t["result"] == "PASSED"]
            if passed_conditions:
                recommendations.append(f"Partially confirmed aspects: {', '.join([t['name'] for t in passed_conditions[:3]])}")
        
        elif result == HypothesisResult.ERROR:
            recommendations.append("Testing failed due to errors - fix test conditions first")
            recommendations.append("Check test environment and dependencies")
        
        return recommendations

# Predefined common hypotheses for meeting-scheduler-bot
class CommonHypotheses:
    """Common hypotheses for meeting scheduler bot debugging"""
    
    @staticmethod
    def create_input_validation_hypothesis(
        test_data: Any,
        validation_function: Callable[[Any], bool]
    ) -> List[TestCondition]:
        """Hypothesis: Problem is caused by invalid input data"""
        return [
            TestCondition(
                name="Input data is not None",
                test_function=lambda: test_data is not None,
                expected_result=True,
                comparison_type="is_true"
            ),
            TestCondition(
                name="Input passes validation",
                test_function=lambda: validation_function(test_data),
                expected_result=True,
                comparison_type="is_true"
            )
        ]
    
    @staticmethod
    def create_database_connectivity_hypothesis(db_engine) -> List[TestCondition]:
        """Hypothesis: Problem is caused by database connectivity issues"""
        return [
            TestCondition(
                name="Database engine is configured",
                test_function=lambda: db_engine is not None,
                expected_result=True,
                comparison_type="is_true"
            ),
            TestCondition(
                name="Database connection succeeds",
                test_function=lambda: _test_db_connection(db_engine),
                expected_result=True,
                comparison_type="is_true"
            ),
            TestCondition(
                name="Database query response time acceptable",
                test_function=lambda: _test_db_query_time(db_engine),
                expected_result=1000,  # ms
                comparison_type="less_than"
            )
        ]
    
    @staticmethod
    def create_external_service_hypothesis(service_url: str) -> List[TestCondition]:
        """Hypothesis: Problem is caused by external service issues"""
        return [
            TestCondition(
                name="Service URL is reachable",
                test_function=lambda: _test_url_reachable(service_url),
                expected_result=True,
                comparison_type="is_true"
            ),
            TestCondition(
                name="Service response time acceptable",
                test_function=lambda: _test_service_response_time(service_url),
                expected_result=5000,  # ms
                comparison_type="less_than"
            )
        ]
    
    @staticmethod
    def create_resource_exhaustion_hypothesis() -> List[TestCondition]:
        """Hypothesis: Problem is caused by resource exhaustion"""
        return [
            TestCondition(
                name="CPU usage under critical threshold",
                test_function=lambda: _get_cpu_usage(),
                expected_result=90,  # percent
                comparison_type="less_than"
            ),
            TestCondition(
                name="Memory usage under critical threshold", 
                test_function=lambda: _get_memory_usage(),
                expected_result=90,  # percent
                comparison_type="less_than"
            ),
            TestCondition(
                name="Disk space available",
                test_function=lambda: _get_disk_usage(),
                expected_result=95,  # percent
                comparison_type="less_than"
            )
        ]

# Root Cause Analysis using 5 Whys technique
class FiveWhysAnalyzer:
    """Implement the 5 Whys root cause analysis technique"""
    
    def __init__(self, logger: DiagnosticLogger):
        self.logger = logger
        self.analysis_history: List[Dict[str, Any]] = []
    
    def analyze_problem(self, initial_problem: str, why_answers: List[str]) -> Dict[str, Any]:
        """Perform 5 Whys analysis"""
        
        if len(why_answers) != 5:
            raise ValueError("5 Whys analysis requires exactly 5 'why' answers")
        
        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "initial_problem": initial_problem,
            "whys": [],
            "root_cause": why_answers[-1],
            "analysis_depth": "comprehensive" if len(why_answers) == 5 else "shallow",
            "confidence_score": self._calculate_confidence_score(why_answers)
        }
        
        self.logger.logger.info(f"🔍 5 WHYS ANALYSIS: {initial_problem}")
        
        current_problem = initial_problem
        for i, why_answer in enumerate(why_answers, 1):
            why_entry = {
                "question": f"Why does '{current_problem}' happen?",
                "answer": why_answer,
                "level": i
            }
            analysis["whys"].append(why_entry)
            
            self.logger.logger.info(f"   WHY #{i}: {current_problem}")
            self.logger.logger.info(f"   ANSWER: {why_answer}")
            
            current_problem = why_answer
        
        self.logger.logger.info(f"🎯 ROOT CAUSE: {analysis['root_cause']}")
        self.logger.logger.info(f"   Confidence Score: {analysis['confidence_score']:.2f}")
        
        # Store analysis
        self.analysis_history.append(analysis)
        
        return analysis
    
    def _calculate_confidence_score(self, why_answers: List[str]) -> float:
        """Calculate confidence score based on answer quality"""
        score = 0.0
        
        for answer in why_answers:
            # Add points for detailed answers
            if len(answer) > 20:
                score += 0.15
            else:
                score += 0.1
            
            # Add points for technical specificity
            technical_keywords = [
                'configuration', 'database', 'network', 'timeout', 'memory',
                'cpu', 'connection', 'authentication', 'authorization', 'api',
                'service', 'queue', 'cache', 'lock', 'thread', 'process'
            ]
            
            if any(keyword in answer.lower() for keyword in technical_keywords):
                score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0

# Helper functions for common test conditions
def _test_db_connection(db_engine) -> bool:
    """Test database connection"""
    try:
        from sqlalchemy import text
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

def _test_db_query_time(db_engine) -> float:
    """Test database query response time in milliseconds"""
    import time
    try:
        from sqlalchemy import text
        start_time = time.time()
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return (time.time() - start_time) * 1000
    except Exception:
        return float('inf')

def _test_url_reachable(url: str) -> bool:
    """Test if URL is reachable"""
    import requests
    try:
        response = requests.get(url, timeout=5)
        return response.status_code < 500
    except Exception:
        return False

def _test_service_response_time(url: str) -> float:
    """Test service response time in milliseconds"""
    import requests
    import time
    try:
        start_time = time.time()
        requests.get(url, timeout=10)
        return (time.time() - start_time) * 1000
    except Exception:
        return float('inf')

def _get_cpu_usage() -> float:
    """Get current CPU usage percentage"""
    import psutil
    return psutil.cpu_percent(interval=1)

def _get_memory_usage() -> float:
    """Get current memory usage percentage"""
    import psutil
    return psutil.virtual_memory().percent

def _get_disk_usage() -> float:
    """Get current disk usage percentage"""
    import psutil
    return psutil.disk_usage('/').percent