#!/usr/bin/env python3
"""
🛡️ SIMPLIFIED DIAGNOSTIC RUNNER
A practical, lightweight version that extracts key insights from the comprehensive system.
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedDiagnostic:
    """Simplified diagnostic that focuses on practical insights"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        
    def analyze_bug_patterns(self):
        """Analyze the documented bug patterns for key insights"""
        logger.info("📊 Analyzing bug patterns from bug_report_2025_08_01.json...")
        
        bug_report_path = self.project_root / "bug_report_2025_08_01.json"
        if not bug_report_path.exists():
            return {"error": "Bug report not found"}
            
        with open(bug_report_path, 'r', encoding='utf-8') as f:
            bug_data = json.load(f)
        
        # Extract key patterns
        analysis = {
            "bugs_fixed": bug_data["session_info"]["total_bugs_fixed"],
            "time_spent": bug_data["session_info"]["total_time_spent"],
            "severity_breakdown": bug_data["session_info"]["severity_distribution"],
            "root_cause_patterns": [],
            "fix_patterns": [],
            "critical_lessons": [],
            "prevention_recommendations": []
        }
        
        # Analyze each bug
        for bug in bug_data.get("bugs_detailed", []):
            analysis["root_cause_patterns"].append({
                "bug_id": bug["bug_id"],
                "cause": bug["root_cause"],
                "category": self._categorize_root_cause(bug["root_cause"])
            })
            
            if bug.get("fix_applied"):
                analysis["fix_patterns"].append({
                    "bug_id": bug["bug_id"],
                    "approach": bug["fix_applied"]["description"],
                    "time_to_fix": bug.get("time_to_fix", "unknown")
                })
        
        # Extract lessons learned
        if "lessons_learned" in bug_data:
            analysis["critical_lessons"] = bug_data["lessons_learned"].get("diagnostic_approach", [])
            analysis["prevention_recommendations"] = bug_data["lessons_learned"].get("prevention_measures", [])
        
        return analysis
    
    def _categorize_root_cause(self, root_cause: str) -> str:
        """Categorize root cause into common patterns"""
        cause_lower = root_cause.lower()
        
        if "initialization" in cause_lower or "startup" in cause_lower:
            return "initialization_failure"
        elif "validation" in cause_lower or "check" in cause_lower:
            return "validation_missing"
        elif "recursion" in cause_lower or "infinite" in cause_lower:
            return "logic_error"
        elif "api" in cause_lower or "external" in cause_lower:
            return "external_integration"
        elif "cache" in cause_lower or "flag" in cause_lower:
            return "state_management"
        else:
            return "other"
    
    def analyze_codebase_health(self):
        """Basic codebase health analysis"""
        logger.info("🏥 Analyzing codebase health...")
        
        health_metrics = {
            "file_count": 0,
            "python_files": 0,
            "handlers_count": 0,
            "services_count": 0,
            "test_files": 0,
            "log_files": 0,
            "config_complexity": "medium",
            "documentation_files": 0
        }
        
        # Count different file types
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                health_metrics["file_count"] += 1
                
                if file_path.suffix == ".py":
                    health_metrics["python_files"] += 1
                    
                    if "handler" in file_path.name.lower():
                        health_metrics["handlers_count"] += 1
                    elif "service" in file_path.name.lower():
                        health_metrics["services_count"] += 1
                    elif "test" in file_path.name.lower():
                        health_metrics["test_files"] += 1
                        
                elif file_path.suffix == ".log":
                    health_metrics["log_files"] += 1
                elif file_path.suffix == ".md":
                    health_metrics["documentation_files"] += 1
        
        # Analyze config complexity
        config_path = self.project_root / "src" / "config.py"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_lines = len(f.readlines())
                if config_lines > 300:
                    health_metrics["config_complexity"] = "high"
                elif config_lines < 100:
                    health_metrics["config_complexity"] = "low"
        
        return health_metrics
    
    def check_recent_logs_for_issues(self):
        """Check recent log files for potential issues"""
        logger.info("📋 Checking recent logs for issues...")
        
        log_analysis = {
            "log_files_found": [],
            "error_patterns": {},
            "warning_patterns": {},
            "recent_issues": []
        }
        
        # Find log files
        for log_file in self.project_root.glob("*.log"):
            log_analysis["log_files_found"].append(log_file.name)
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-100:]  # Last 100 lines
                    
                    for line in lines:
                        line_lower = line.lower()
                        
                        # Count error patterns
                        if "error" in line_lower:
                            error_type = self._extract_error_type(line)
                            log_analysis["error_patterns"][error_type] = log_analysis["error_patterns"].get(error_type, 0) + 1
                        
                        # Count warning patterns
                        if "warning" in line_lower or "warn" in line_lower:
                            warning_type = self._extract_warning_type(line)
                            log_analysis["warning_patterns"][warning_type] = log_analysis["warning_patterns"].get(warning_type, 0) + 1
                        
                        # Specific issue patterns
                        if any(pattern in line_lower for pattern in ["badrequest", "timeout", "connection", "failed"]):
                            log_analysis["recent_issues"].append({
                                "file": log_file.name,
                                "issue": line.strip()[:200]
                            })
            
            except Exception as e:
                logger.warning(f"Could not analyze {log_file.name}: {e}")
        
        return log_analysis
    
    def _extract_error_type(self, line: str) -> str:
        """Extract error type from log line"""
        if "badrequest" in line.lower():
            return "BadRequest"
        elif "timeout" in line.lower():
            return "Timeout"
        elif "connection" in line.lower():
            return "Connection"
        elif "permission" in line.lower():
            return "Permission"
        else:
            return "Generic"
    
    def _extract_warning_type(self, line: str) -> str:
        """Extract warning type from log line"""
        if "deprecated" in line.lower():
            return "Deprecated"
        elif "fallback" in line.lower():
            return "Fallback"
        elif "retry" in line.lower():
            return "Retry"
        else:
            return "Generic"
    
    def generate_recommendations(self, bug_analysis, health_metrics, log_analysis):
        """Generate practical recommendations"""
        recommendations = []
        
        # Bug pattern based recommendations
        root_causes = [bug["category"] for bug in bug_analysis.get("root_cause_patterns", [])]
        cause_counts = {}
        for cause in root_causes:
            cause_counts[cause] = cause_counts.get(cause, 0) + 1
        
        # Top cause categories
        top_causes = sorted(cause_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        recommendations.append({
            "priority": "HIGH",
            "category": "Pattern Prevention",
            "title": f"Focus on {top_causes[0][0] if top_causes else 'validation'} improvements",
            "description": f"Most common root cause category: {top_causes[0][0] if top_causes else 'validation'} ({top_causes[0][1] if top_causes else 0} occurrences)"
        })
        
        # Health based recommendations
        if health_metrics["test_files"] < 3:
            recommendations.append({
                "priority": "HIGH", 
                "category": "Testing",
                "title": "Increase test coverage",
                "description": f"Only {health_metrics['test_files']} test files found. Add tests for the {bug_analysis['bugs_fixed']} bug categories."
            })
        
        if health_metrics["config_complexity"] == "high":
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Code Quality",
                "title": "Simplify configuration",
                "description": "Config file is complex. Consider splitting into modules."
            })
        
        # Log based recommendations
        error_count = sum(log_analysis.get("error_patterns", {}).values())
        if error_count > 10:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Error Handling",
                "title": "Investigate recurring errors",
                "description": f"Found {error_count} errors in recent logs. Top patterns: {list(log_analysis.get('error_patterns', {}).keys())[:3]}"
            })
        
        # Success pattern recommendations
        time_spent = bug_analysis.get("time_spent", "unknown")
        if "90" in str(time_spent):
            recommendations.append({
                "priority": "LOW",
                "category": "Process",
                "title": "Maintain current diagnostic approach",
                "description": "Previous 4 bugs were fixed efficiently in ~90 minutes. Document this successful process."
            })
        
        return recommendations
    
    def print_summary(self, bug_analysis, health_metrics, log_analysis, recommendations):
        """Print executive summary"""
        print("\n" + "="*70)
        print("🛡️ SIMPLIFIED DIAGNOSTIC SYSTEM - EXECUTIVE SUMMARY")
        print("="*70)
        
        print(f"\n📊 BUG PATTERN ANALYSIS:")
        print(f"   ✅ Bugs fixed: {bug_analysis['bugs_fixed']}")
        print(f"   ⏱️  Time spent: {bug_analysis['time_spent']}")
        print(f"   🚨 Severity: {bug_analysis['severity_breakdown']}")
        
        # Top root cause patterns
        root_causes = {}
        for bug in bug_analysis.get("root_cause_patterns", []):
            cat = bug["category"]
            root_causes[cat] = root_causes.get(cat, 0) + 1
        
        print(f"\n🔍 ROOT CAUSE PATTERNS:")
        for cause, count in sorted(root_causes.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {cause}: {count} occurrence(s)")
        
        print(f"\n🏥 CODEBASE HEALTH:")
        print(f"   📁 Python files: {health_metrics['python_files']}")
        print(f"   🎯 Handlers: {health_metrics['handlers_count']}")
        print(f"   ⚙️  Services: {health_metrics['services_count']}")
        print(f"   🧪 Test files: {health_metrics['test_files']}")
        print(f"   📋 Log files: {health_metrics['log_files']}")
        print(f"   ⚙️  Config complexity: {health_metrics['config_complexity']}")
        
        print(f"\n📋 LOG ANALYSIS:")
        print(f"   📄 Log files analyzed: {len(log_analysis['log_files_found'])}")
        print(f"   ❌ Error patterns: {len(log_analysis.get('error_patterns', {}))}")
        print(f"   ⚠️  Warning patterns: {len(log_analysis.get('warning_patterns', {}))}")
        print(f"   🚨 Recent issues: {len(log_analysis.get('recent_issues', []))}")
        
        print(f"\n💡 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"   {i}. [{rec['priority']}] {rec['title']}")
            print(f"      Category: {rec['category']}")
            print(f"      {rec['description']}")
            print()
        
        print("="*70)

def main():
    """Main diagnostic runner"""
    diagnostic = SimplifiedDiagnostic("/Users/evgenii/meeting-scheduler-bot")
    
    try:
        # Step 1: Analyze bug patterns
        logger.info("🔍 STEP 1: Analyzing bug patterns...")
        bug_analysis = diagnostic.analyze_bug_patterns()
        
        # Step 2: Check codebase health
        logger.info("🏥 STEP 2: Analyzing codebase health...")
        health_metrics = diagnostic.analyze_codebase_health()
        
        # Step 3: Check recent logs
        logger.info("📋 STEP 3: Checking recent logs...")
        log_analysis = diagnostic.check_recent_logs_for_issues()
        
        # Step 4: Generate recommendations
        logger.info("💡 STEP 4: Generating recommendations...")
        recommendations = diagnostic.generate_recommendations(bug_analysis, health_metrics, log_analysis)
        
        # Step 5: Print summary
        diagnostic.print_summary(bug_analysis, health_metrics, log_analysis, recommendations)
        
        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "bug_analysis": bug_analysis,
            "health_metrics": health_metrics,
            "log_analysis": log_analysis,
            "recommendations": recommendations
        }
        
        results_path = diagnostic.project_root / f"simplified_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Results saved to: {results_path}")
        
    except Exception as e:
        logger.error(f"❌ Diagnostic failed: {e}")
        raise

if __name__ == "__main__":
    main()