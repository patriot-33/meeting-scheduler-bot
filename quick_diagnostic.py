#!/usr/bin/env python3
"""
🛡️ QUICK DIAGNOSTIC ANALYSIS
Immediate system health assessment based on bug report and codebase analysis.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickDiagnostic:
    """Quick system analysis based on recent fixes and current state"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        
    def analyze_bug_patterns(self) -> Dict[str, Any]:
        """Analyze patterns from the bug report"""
        bug_report_path = self.project_root / "bug_report_2025_08_01.json"
        
        if not bug_report_path.exists():
            logger.warning("Bug report not found")
            return {}
            
        with open(bug_report_path, 'r', encoding='utf-8') as f:
            bug_data = json.load(f)
        
        # Extract key patterns
        patterns = {
            "total_bugs_fixed": bug_data["session_info"]["total_bugs_fixed"],
            "severity_distribution": bug_data["session_info"]["severity_distribution"],
            "time_spent": bug_data["session_info"]["total_time_spent"],
            "common_root_causes": bug_data["patterns_analysis"]["common_root_causes"],
            "fix_patterns": bug_data["patterns_analysis"]["fix_patterns"],
            "prevention_measures": bug_data["lessons_learned"]["prevention_measures"]
        }
        
        return patterns
    
    def analyze_code_health(self) -> Dict[str, Any]:
        """Analyze current code health indicators"""
        health_indicators = {
            "config_fixes_applied": False,
            "error_handling_improved": False,
            "calendar_integration_status": "unknown",
            "defensive_measures_present": False
        }
        
        # Check if config.py has the env loading fix
        config_path = self.project_root / "src" / "config.py"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_content = f.read()
                if "load_dotenv()" in config_content:
                    health_indicators["config_fixes_applied"] = True
        
        # Check manager_calendar.py for safe_send_message fix
        calendar_handler_path = self.project_root / "src" / "handlers" / "manager_calendar.py"
        if calendar_handler_path.exists():
            with open(calendar_handler_path, 'r') as f:
                calendar_content = f.read()
                if "safe_send_message" in calendar_content:
                    health_indicators["error_handling_improved"] = True
                if "test_calendar_access" in calendar_content:
                    health_indicators["calendar_integration_status"] = "improved"
        
        # Check for defensive utilities
        telegram_safe_path = self.project_root / "src" / "utils" / "telegram_safe.py"
        if telegram_safe_path.exists():
            health_indicators["defensive_measures_present"] = True
        
        return health_indicators
    
    def scan_for_potential_issues(self) -> List[Dict[str, Any]]:
        """Scan for potential issues based on patterns"""
        potential_issues = []
        
        # Check for similar patterns that might cause future issues
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Pattern 1: Check for missing error handling in API calls
                if "edit_message_text" in content and "try:" not in content:
                    potential_issues.append({
                        "type": "error_handling",
                        "severity": "medium",
                        "file": str(py_file.relative_to(self.project_root)),
                        "description": "API calls without error handling",
                        "recommendation": "Add try-catch blocks around Telegram API calls"
                    })
                
                # Pattern 2: Check for environment variable usage without loading
                if "os.getenv" in content or "os.environ" in content:
                    if "load_dotenv" not in content and py_file.name != "config.py":
                        potential_issues.append({
                            "type": "configuration",
                            "severity": "low",
                            "file": str(py_file.relative_to(self.project_root)),
                            "description": "Direct env var access without load_dotenv",
                            "recommendation": "Use config.py settings instead of direct env access"
                        })
                
                # Pattern 3: Check for recursive function calls
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "def " in line:
                        func_name = line.split("def ")[1].split("(")[0].strip()
                        # Check if function calls itself in the body
                        func_start = i
                        indent_level = len(line) - len(line.lstrip())
                        for j in range(i + 1, min(i + 50, len(lines))):  # Check next 50 lines
                            if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= indent_level:
                                break  # End of function
                            if func_name in lines[j] and "def " not in lines[j]:
                                potential_issues.append({
                                    "type": "logic_error",
                                    "severity": "high",
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "line": j + 1,
                                    "description": f"Potential recursive call in function {func_name}",
                                    "recommendation": "Review function logic to prevent infinite recursion"
                                })
                                break
                                
            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")
        
        return potential_issues
    
    def generate_health_score(self, code_health: Dict[str, Any], potential_issues: List[Dict[str, Any]]) -> float:
        """Calculate system health score"""
        base_score = 0.5  # Start with neutral
        
        # Positive factors
        if code_health["config_fixes_applied"]:
            base_score += 0.15
        if code_health["error_handling_improved"]:
            base_score += 0.15
        if code_health["calendar_integration_status"] == "improved":
            base_score += 0.1
        if code_health["defensive_measures_present"]:
            base_score += 0.1
        
        # Negative factors based on potential issues
        critical_issues = len([i for i in potential_issues if i["severity"] == "critical"])
        high_issues = len([i for i in potential_issues if i["severity"] == "high"])
        medium_issues = len([i for i in potential_issues if i["severity"] == "medium"])
        
        base_score -= critical_issues * 0.2
        base_score -= high_issues * 0.1
        base_score -= medium_issues * 0.05
        
        return max(0.0, min(1.0, base_score))
    
    def generate_recommendations(self, patterns: Dict[str, Any], potential_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Based on fixed bugs, suggest preventive measures
        recommendations.extend([
            {
                "priority": "high",
                "category": "monitoring",
                "title": "Environment Variable Validation",
                "description": "Add startup validation to ensure all required environment variables are loaded",
                "implementation": "Create a validate_environment() function in config.py"
            },
            {
                "priority": "high",
                "category": "error_handling",
                "title": "Unified Error Handling",
                "description": "Extend safe_send_message pattern to all Telegram API interactions",
                "implementation": "Create a telegram_safe.py utility module"
            },
            {
                "priority": "medium",
                "category": "testing",
                "title": "Regression Testing",
                "description": "Add automated tests for the 4 bug categories that were fixed",
                "implementation": "Create test cases for env loading, recursive calls, API errors, and calendar status"
            }
        ])
        
        # Add recommendations based on potential issues
        critical_issues = [i for i in potential_issues if i["severity"] == "critical"]
        if critical_issues:
            recommendations.insert(0, {
                "priority": "critical",
                "category": "bug_fix",
                "title": "Critical Issues Detected",
                "description": f"Found {len(critical_issues)} critical issues that need immediate attention",
                "implementation": "Review and fix critical issues before deployment"
            })
        
        high_issues = [i for i in potential_issues if i["severity"] == "high"]
        if high_issues:
            recommendations.append({
                "priority": "high",
                "category": "code_quality",
                "title": "High-Priority Code Issues",
                "description": f"Found {len(high_issues)} high-priority issues requiring attention",
                "implementation": "Schedule time to address high-priority code quality issues"
            })
        
        return recommendations
    
    def run_analysis(self) -> Dict[str, Any]:
        """Run complete quick diagnostic analysis"""
        logger.info("🛡️ Starting Quick Diagnostic Analysis...")
        
        # Step 1: Analyze bug patterns
        logger.info("📊 Analyzing bug patterns from recent fixes...")
        bug_patterns = self.analyze_bug_patterns()
        
        # Step 2: Check current code health
        logger.info("🏥 Checking current code health...")
        code_health = self.analyze_code_health()
        
        # Step 3: Scan for potential issues
        logger.info("🔍 Scanning for potential issues...")
        potential_issues = self.scan_for_potential_issues()
        
        # Step 4: Calculate health score
        health_score = self.generate_health_score(code_health, potential_issues)
        
        # Step 5: Generate recommendations
        recommendations = self.generate_recommendations(bug_patterns, potential_issues)
        
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "system_health_score": health_score,
            "bug_patterns": bug_patterns,
            "code_health": code_health,
            "potential_issues": potential_issues,
            "recommendations": recommendations,
            "summary": {
                "total_potential_issues": len(potential_issues),
                "critical_issues": len([i for i in potential_issues if i["severity"] == "critical"]),
                "high_issues": len([i for i in potential_issues if i["severity"] == "high"]),
                "medium_issues": len([i for i in potential_issues if i["severity"] == "medium"]),
                "fixes_applied_successfully": sum([
                    code_health["config_fixes_applied"],
                    code_health["error_handling_improved"],
                    code_health["defensive_measures_present"]
                ])
            }
        }
    
    def print_summary(self, analysis: Dict[str, Any]):
        """Print executive summary"""
        print("\n" + "="*70)
        print("🛡️ QUICK DIAGNOSTIC ANALYSIS - EXECUTIVE SUMMARY")
        print("="*70)
        
        summary = analysis["summary"]
        health_score = analysis["system_health_score"]
        
        # Health status
        if health_score >= 0.8:
            health_status = "EXCELLENT ✅"
        elif health_score >= 0.6:
            health_status = "GOOD 👍"
        elif health_score >= 0.4:
            health_status = "FAIR ⚠️"
        else:
            health_status = "POOR ❌"
        
        print(f"🏥 System Health Score: {health_score:.2f}/1.0 ({health_status})")
        print(f"🔧 Fixes Applied Successfully: {summary['fixes_applied_successfully']}/3")
        print(f"🚨 Critical Issues: {summary['critical_issues']}")
        print(f"⚠️ High Priority Issues: {summary['high_issues']}")
        print(f"💡 Medium Priority Issues: {summary['medium_issues']}")
        
        # Bug pattern analysis
        bug_patterns = analysis["bug_patterns"]
        if bug_patterns:
            print(f"\n📊 Previous Bug Analysis:")
            print(f"   ✅ Bugs Fixed: {bug_patterns.get('total_bugs_fixed', 0)}")
            print(f"   ⏱️ Time Spent: {bug_patterns.get('time_spent', 'Unknown')}")
            severity_dist = bug_patterns.get('severity_distribution', {})
            print(f"   🔴 Critical: {severity_dist.get('critical', 0)}, 🟡 High: {severity_dist.get('high', 0)}, 🟢 Medium: {severity_dist.get('medium', 0)}")
        
        # Code health indicators
        code_health = analysis["code_health"]
        print(f"\n🏥 Code Health Indicators:")
        print(f"   ✅ Environment Loading Fixed: {code_health['config_fixes_applied']}")
        print(f"   ✅ Error Handling Improved: {code_health['error_handling_improved']}")
        print(f"   ✅ Calendar Integration: {code_health['calendar_integration_status']}")
        print(f"   ✅ Defensive Measures: {code_health['defensive_measures_present']}")
        
        # Top recommendations
        recommendations = analysis["recommendations"]
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")
            print(f"      {rec['description']}")
        
        print("="*70)
        
        return analysis

def main():
    """Run quick diagnostic analysis"""
    diagnostic = QuickDiagnostic("/Users/evgenii/meeting-scheduler-bot")
    
    try:
        analysis = diagnostic.run_analysis()
        diagnostic.print_summary(analysis)
        
        # Save detailed report
        report_path = Path("/Users/evgenii/meeting-scheduler-bot") / f"quick_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Detailed report saved: {report_path}")
        logger.info("✅ Quick diagnostic analysis complete!")
        
    except Exception as e:
        logger.error(f"❌ Quick diagnostic failed: {e}")
        raise

if __name__ == "__main__":
    main()