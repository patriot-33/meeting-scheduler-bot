#!/usr/bin/env python3
"""
🛡️ FOCUSED HOLISTIC DIAGNOSTIC
A streamlined version that focuses on analysis without JSON serialization issues.
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
        logging.FileHandler(f'focused_diagnostic_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import diagnostic system
sys.path.append('src')
from diagnostic_system.system_analyzer import SystemAnalyzer
from diagnostic_system.invariant_detector import InvariantDetector

class FocusedDiagnostic:
    """Focused diagnostic runner with safe JSON serialization"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        
    async def run_analysis(self):
        """Run focused analysis"""
        logger.info("🛡️ Starting Focused Holistic Diagnostic Analysis...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "project": "meeting-scheduler-bot",
            "analysis_type": "focused_diagnostic"
        }
        
        try:
            # 1. System Analysis
            logger.info("🗺️ Running System Analysis...")
            system_analyzer = SystemAnalyzer(str(self.project_root))
            system_map = system_analyzer.analyze_complete_system()
            
            # Extract key metrics safely
            results["system_analysis"] = {
                "total_components": system_map.get("total_components", 0),
                "system_health_score": system_map.get("system_health_score", 0.0),
                "critical_paths_count": len(system_map.get("critical_paths", [])),
                "high_risk_modules_count": len(system_map.get("high_risk_modules", [])),
                "complexity_score": system_map.get("complexity_metrics", {}).get("overall_complexity", 0.0)
            }
            
            logger.info(f"✅ System Analysis Complete:")
            logger.info(f"   📦 Components: {results['system_analysis']['total_components']}")
            logger.info(f"   🏥 Health Score: {results['system_analysis']['system_health_score']:.2f}")
            logger.info(f"   🎯 Critical Paths: {results['system_analysis']['critical_paths_count']}")
            logger.info(f"   ⚠️  High Risk Modules: {results['system_analysis']['high_risk_modules_count']}")
            
            # 2. Invariant Detection
            logger.info("🔍 Running Invariant Detection...")
            invariant_detector = InvariantDetector(str(self.project_root))
            invariants = invariant_detector.detect_invariants()
            
            # Count invariants safely without including Invariant objects
            results["invariant_analysis"] = {
                "data_contracts": len(invariants.get("data_contracts", [])),
                "timing_assumptions": len(invariants.get("timing_assumptions", [])),
                "ordering_requirements": len(invariants.get("ordering_requirements", [])),
                "resource_limits": len(invariants.get("resource_limits", [])),
                "business_rules": len(invariants.get("business_rules", []))
            }
            
            total_invariants = sum(results["invariant_analysis"].values())
            logger.info(f"✅ Invariant Detection Complete:")
            logger.info(f"   🔒 Total Invariants: {total_invariants}")
            for inv_type, count in results["invariant_analysis"].items():
                logger.info(f"   • {inv_type}: {count}")
            
            # 3. Previous Bug Analysis
            logger.info("📊 Analyzing Previous Bug Patterns...")
            bug_report_path = self.project_root / "bug_report_2025_08_01.json"
            if bug_report_path.exists():
                with open(bug_report_path, 'r', encoding='utf-8') as f:
                    bug_data = json.load(f)
                
                results["bug_analysis"] = {
                    "total_bugs_fixed": bug_data.get("session_info", {}).get("total_bugs_fixed", 0),
                    "severity_distribution": bug_data.get("session_info", {}).get("severity_distribution", {}),
                    "common_patterns": bug_data.get("patterns_analysis", {}).get("common_root_causes", [])
                }
                
                logger.info(f"✅ Bug Analysis Complete:")
                logger.info(f"   🐛 Total Bugs Fixed: {results['bug_analysis']['total_bugs_fixed']}")
                logger.info(f"   📊 Severity Distribution: {results['bug_analysis']['severity_distribution']}")
            
            # 4. File Health Assessment
            logger.info("📂 Assessing File Health...")
            file_health = self.assess_file_health()
            results["file_health"] = file_health
            
            logger.info(f"✅ File Health Assessment Complete:")
            logger.info(f"   📁 Python Files: {file_health['python_files_count']}")
            logger.info(f"   📊 Average File Size: {file_health['average_file_size_kb']:.1f} KB")
            logger.info(f"   🔍 Large Files: {file_health['large_files_count']}")
            
            # 5. Critical Path Analysis
            logger.info("🎯 Analyzing Critical Paths...")
            critical_paths = system_map.get("critical_paths", [])
            if critical_paths:
                # Extract safe data from critical paths
                results["critical_path_analysis"] = {
                    "paths_identified": len(critical_paths),
                    "highest_risk_score": max([path.get("risk_score", 0) for path in critical_paths]),
                    "components_in_critical_paths": len(set([comp for path in critical_paths for comp in path.get("components", [])]))
                }
                logger.info(f"✅ Critical Path Analysis Complete:")
                logger.info(f"   🎯 Critical Paths: {results['critical_path_analysis']['paths_identified']}")
                logger.info(f"   ⚠️  Highest Risk Score: {results['critical_path_analysis']['highest_risk_score']:.2f}")
            
            # 6. Generate Summary
            summary = self.generate_summary(results)
            results["summary"] = summary
            
            # 7. Generate Recommendations
            recommendations = self.generate_recommendations(results)
            results["recommendations"] = recommendations
            
            # Save results (this should work now)
            report_path = self.project_root / f"focused_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📋 Report saved: {report_path}")
            
            # Display Summary
            self.display_summary(results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            raise
    
    def assess_file_health(self):
        """Assess health of project files"""
        python_files = list(self.project_root.rglob("*.py"))
        
        if not python_files:
            return {"error": "No Python files found"}
        
        file_sizes = []
        large_files = []
        
        for file_path in python_files:
            try:
                size_kb = file_path.stat().st_size / 1024
                file_sizes.append(size_kb)
                
                if size_kb > 50:  # Files larger than 50KB
                    large_files.append({
                        "path": str(file_path.relative_to(self.project_root)),
                        "size_kb": round(size_kb, 1)
                    })
            except Exception as e:
                logger.warning(f"Could not analyze file {file_path}: {e}")
        
        return {
            "python_files_count": len(python_files),
            "average_file_size_kb": sum(file_sizes) / len(file_sizes) if file_sizes else 0,
            "largest_file_kb": max(file_sizes) if file_sizes else 0,
            "large_files_count": len(large_files),
            "large_files": large_files[:5]  # Top 5 largest files
        }
    
    def generate_summary(self, results):
        """Generate executive summary"""
        health_score = results.get("system_analysis", {}).get("system_health_score", 0.0)
        
        if health_score >= 0.8:
            status = "EXCELLENT"
        elif health_score >= 0.6:
            status = "GOOD"
        elif health_score >= 0.4:
            status = "FAIR"
        else:
            status = "NEEDS_ATTENTION"
        
        return {
            "overall_status": status,
            "health_score": health_score,
            "total_components": results.get("system_analysis", {}).get("total_components", 0),
            "bugs_previously_fixed": results.get("bug_analysis", {}).get("total_bugs_fixed", 0),
            "invariants_detected": sum(results.get("invariant_analysis", {}).values()),
            "critical_paths": results.get("system_analysis", {}).get("critical_paths_count", 0)
        }
    
    def generate_recommendations(self, results):
        """Generate specific recommendations"""
        recommendations = []
        
        health_score = results.get("system_analysis", {}).get("system_health_score", 0.0)
        high_risk_modules = results.get("system_analysis", {}).get("high_risk_modules_count", 0)
        
        # Health-based recommendations
        if health_score < 0.6:
            recommendations.append({
                "priority": "HIGH",
                "category": "System Health",
                "title": "Improve Overall System Health",
                "description": f"System health score is {health_score:.2f}. Focus on reducing complexity and improving code quality."
            })
        
        if high_risk_modules > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Risk Management",
                "title": "Address High-Risk Modules",
                "description": f"{high_risk_modules} modules identified as high-risk. Review and refactor these components."
            })
        
        # Previous bugs analysis
        bugs_fixed = results.get("bug_analysis", {}).get("total_bugs_fixed", 0)
        if bugs_fixed > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Testing",
                "title": "Add Regression Tests",
                "description": f"Add automated tests for the {bugs_fixed} bug categories that were recently fixed."
            })
        
        # File size recommendations
        large_files = results.get("file_health", {}).get("large_files_count", 0)
        if large_files > 0:
            recommendations.append({
                "priority": "LOW",
                "category": "Code Quality",
                "title": "Refactor Large Files",
                "description": f"{large_files} files are larger than 50KB. Consider breaking them into smaller modules."
            })
        
        # Always add monitoring recommendation
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Monitoring",
            "title": "Implement Continuous Monitoring",
            "description": "Set up continuous health monitoring to detect issues proactively."
        })
        
        return recommendations
    
    def display_summary(self, results):
        """Display executive summary"""
        print("\n" + "="*80)
        print("🛡️ FOCUSED HOLISTIC DIAGNOSTIC - EXECUTIVE SUMMARY")
        print("="*80)
        
        summary = results["summary"]
        print(f"📊 Overall Status: {summary['overall_status']}")
        print(f"🏥 System Health Score: {summary['health_score']:.2f}/1.0")
        print(f"📦 Total Components: {summary['total_components']}")
        print(f"🔒 Invariants Detected: {summary['invariants_detected']}")
        print(f"🎯 Critical Paths: {summary['critical_paths']}")
        print(f"🐛 Bugs Previously Fixed: {summary['bugs_previously_fixed']}")
        
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(results["recommendations"][:3], 1):
            print(f"   {i}. [{rec['priority']}] {rec['title']}")
            print(f"      {rec['description']}")
        
        print(f"\n📊 System Analysis Details:")
        sys_analysis = results.get("system_analysis", {})
        print(f"   🎯 Critical Paths: {sys_analysis.get('critical_paths_count', 0)}")
        print(f"   ⚠️  High Risk Modules: {sys_analysis.get('high_risk_modules_count', 0)}")
        print(f"   📈 Complexity Score: {sys_analysis.get('complexity_score', 0.0):.2f}")
        
        print(f"\n🔍 Invariant Analysis:")
        inv_analysis = results.get("invariant_analysis", {})
        for inv_type, count in inv_analysis.items():
            print(f"   • {inv_type.replace('_', ' ').title()}: {count}")
        
        print(f"\n📂 File Health:")
        file_health = results.get("file_health", {})
        print(f"   📁 Python Files: {file_health.get('python_files_count', 0)}")
        print(f"   📊 Average Size: {file_health.get('average_file_size_kb', 0):.1f} KB")
        print(f"   📈 Largest File: {file_health.get('largest_file_kb', 0):.1f} KB")
        print(f"   🔍 Large Files (>50KB): {file_health.get('large_files_count', 0)}")
        
        print("\n✅ Analysis complete! Full report saved to focused_diagnostic_*.json")
        print("="*80 + "\n")

async def main():
    """Main diagnostic runner"""
    diagnostic = FocusedDiagnostic("/Users/evgenii/meeting-scheduler-bot")
    
    try:
        results = await diagnostic.run_analysis()
        logger.info("✅ Focused diagnostic analysis complete!")
        
    except Exception as e:
        logger.error(f"❌ Diagnostic analysis failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())