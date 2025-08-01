#!/usr/bin/env python3
"""
🛡️ HOLISTIC DIAGNOSTIC RUNNER
Practical runner for the comprehensive diagnostic and repair system.
"""

import asyncio
import logging
import sys
import json
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('diagnostic_session.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import diagnostic system
sys.path.append('src')
from diagnostic_system.holistic_system import HolisticDiagnosticSystem

class DiagnosticRunner:
    """Practical runner for the holistic diagnostic system"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.diagnostic_system = None
        
    async def initialize_system(self):
        """Initialize the diagnostic system"""
        logger.info("🛡️ Initializing Holistic Diagnostic System...")
        self.diagnostic_system = HolisticDiagnosticSystem(str(self.project_root))
        logger.info("✅ Diagnostic system initialized")
        
    async def analyze_previous_bugs(self):
        """Analyze the documented bugs for patterns and learning"""
        logger.info("📊 Analyzing previous bug patterns...")
        
        bug_report_path = self.project_root / "bug_report_2025_08_01.json"
        if not bug_report_path.exists():
            logger.warning("❌ Bug report not found")
            return
            
        with open(bug_report_path, 'r', encoding='utf-8') as f:
            bug_data = json.load(f)
            
        # Analyze patterns from the 4 fixed bugs
        patterns_found = {
            "root_causes": [],
            "fix_patterns": [],
            "prevention_measures": [],
            "symptoms": []
        }
        
        for bug in bug_data.get("bugs_detailed", []):
            # Extract root causes
            if bug.get("root_cause"):
                patterns_found["root_causes"].append({
                    "bug_id": bug["bug_id"],
                    "cause": bug["root_cause"],
                    "severity": bug["severity"]
                })
            
            # Extract fix patterns
            if bug.get("fix_applied"):
                patterns_found["fix_patterns"].append({
                    "bug_id": bug["bug_id"],
                    "approach": bug["fix_applied"]["description"],
                    "files_modified": bug["fix_applied"].get("files_modified", [])
                })
            
            # Extract symptoms
            patterns_found["symptoms"].extend([
                {"bug_id": bug["bug_id"], "symptom": symptom}
                for symptom in bug.get("symptoms", [])
            ])
        
        logger.info(f"📊 Pattern analysis complete:")
        logger.info(f"   Root causes identified: {len(patterns_found['root_causes'])}")
        logger.info(f"   Fix patterns found: {len(patterns_found['fix_patterns'])}")
        logger.info(f"   Symptoms catalogued: {len(patterns_found['symptoms'])}")
        
        return patterns_found
    
    async def run_comprehensive_health_check(self):
        """Run a comprehensive health check of the system"""
        logger.info("🏥 Running comprehensive health check...")
        
        problem_description = """
        Comprehensive health assessment of meeting-scheduler-bot after recent bug fixes.
        Previous issues fixed: ENV_LOADING, INFINITE_RECURSION, CALENDAR_STATUS, BADREQUEST.
        Need to ensure system stability and identify any remaining risks.
        """
        
        # Run diagnostics only (no auto-fix) for safety
        result = await self.diagnostic_system.diagnose_and_fix_safely(
            problem_description=problem_description,
            severity="medium",
            auto_fix=False  # Just diagnose, don't auto-fix
        )
        
        return result
    
    async def run_preventive_analysis(self):
        """Run preventive analysis to identify potential future issues"""
        logger.info("🔮 Running preventive analysis...")
        
        problem_description = """
        Preventive analysis to identify potential future issues in meeting-scheduler-bot.
        Focus on: security vulnerabilities, performance bottlenecks, error handling gaps,
        dependency issues, configuration problems, and code quality concerns.
        """
        
        result = await self.diagnostic_system.run_diagnostics(problem_description)
        return result
    
    def generate_report(self, health_check_result, preventive_result, pattern_analysis):
        """Generate comprehensive diagnostic report"""
        report = {
            "diagnostic_session": {
                "timestamp": datetime.now().isoformat(),
                "project": "meeting-scheduler-bot",
                "diagnostic_system_version": "3.0"
            },
            "pattern_analysis": pattern_analysis,
            "health_check": health_check_result,
            "preventive_analysis": preventive_result,
            "summary": self._generate_summary(health_check_result, preventive_result),
            "recommendations": self._generate_recommendations(health_check_result, preventive_result)
        }
        
        # Save report
        report_path = self.project_root / f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Diagnostic report saved: {report_path}")
        return report
    
    def _generate_summary(self, health_result, preventive_result):
        """Generate executive summary"""
        summary = {
            "overall_status": "unknown",
            "system_health_score": 0.0,
            "critical_issues": 0,
            "warnings": 0,
            "improvements_suggested": 0
        }
        
        # Analyze health check results
        if health_result.get("final_status") == "diagnosis_only":
            summary["overall_status"] = "stable"
            summary["system_health_score"] = health_result.get("system_health_after", 0.5)
        
        # Count issues from preventive analysis
        if preventive_result:
            layer_results = preventive_result.get("layer_results", {})
            for layer_name, layer_data in layer_results.items():
                findings = layer_data.get("findings", [])
                for finding in findings:
                    severity = finding.get("severity", "unknown").lower()
                    if severity in ["critical", "high"]:
                        summary["critical_issues"] += 1
                    elif severity == "medium":
                        summary["warnings"] += 1
                    elif severity == "low":
                        summary["improvements_suggested"] += 1
        
        return summary
    
    def _generate_recommendations(self, health_result, preventive_result):
        """Generate specific recommendations"""
        recommendations = []
        
        # Health-based recommendations
        health_score = health_result.get("system_health_after", 0.5)
        if health_score < 0.7:
            recommendations.append({
                "priority": "high",
                "category": "system_health",
                "title": "Improve System Health",
                "description": f"System health score is {health_score:.2f}. Consider addressing identified issues."
            })
        
        # Add specific recommendations based on analysis
        recommendations.extend([
            {
                "priority": "medium",
                "category": "monitoring",
                "title": "Continuous Monitoring",
                "description": "Implement continuous health monitoring for proactive issue detection"
            },
            {
                "priority": "medium", 
                "category": "testing",
                "title": "Automated Testing",
                "description": "Add comprehensive tests for the 4 bug categories that were fixed"
            },
            {
                "priority": "low",
                "category": "documentation",
                "title": "Pattern Documentation",
                "description": "Document successful fix patterns for future reference"
            }
        ])
        
        return recommendations
    
    def print_summary(self, report):
        """Print executive summary to console"""
        print("\n" + "="*60)
        print("🛡️ HOLISTIC DIAGNOSTIC SYSTEM - EXECUTIVE SUMMARY")
        print("="*60)
        
        summary = report["summary"]
        print(f"📊 Overall Status: {summary['overall_status'].upper()}")
        print(f"🏥 System Health Score: {summary['system_health_score']:.2f}/1.0")
        print(f"🚨 Critical Issues: {summary['critical_issues']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        print(f"💡 Improvements Suggested: {summary['improvements_suggested']}")
        
        print(f"\n📋 Pattern Analysis from Previous Bugs:")
        patterns = report["pattern_analysis"]
        print(f"   🔍 Root causes analyzed: {len(patterns.get('root_causes', []))}")
        print(f"   🔧 Fix patterns learned: {len(patterns.get('fix_patterns', []))}")
        print(f"   🎯 Symptoms catalogued: {len(patterns.get('symptoms', []))}")
        
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(report["recommendations"][:3], 1):
            print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")
            print(f"      {rec['description']}")
        
        print("\n✅ Full diagnostic report saved to: diagnostic_report_*.json")
        print("="*60 + "\n")

async def main():
    """Main diagnostic runner"""
    runner = DiagnosticRunner("/Users/evgenii/meeting-scheduler-bot")
    
    try:
        # Initialize system
        await runner.initialize_system()
        
        # Step 1: Analyze previous bug patterns
        logger.info("🔍 STEP 1: Analyzing previous bug patterns...")
        pattern_analysis = await runner.analyze_previous_bugs()
        
        # Step 2: Comprehensive health check
        logger.info("🏥 STEP 2: Running comprehensive health check...")
        health_result = await runner.run_comprehensive_health_check()
        
        # Step 3: Preventive analysis
        logger.info("🔮 STEP 3: Running preventive analysis...")
        preventive_result = await runner.run_preventive_analysis()
        
        # Step 4: Generate comprehensive report
        logger.info("📋 STEP 4: Generating comprehensive report...")
        report = runner.generate_report(health_result, preventive_result, pattern_analysis)
        
        # Step 5: Display summary
        runner.print_summary(report)
        
        logger.info("✅ Holistic diagnostic analysis complete!")
        
    except Exception as e:
        logger.error(f"❌ Diagnostic runner failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())