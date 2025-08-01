#!/usr/bin/env python3
"""
Simple diagnostic analysis for meeting-scheduler-bot
Analyzing system health and previous bug patterns
"""

import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_bug_patterns():
    """Analyze the documented bugs for patterns"""
    logger.info("📊 Analyzing previous bug patterns...")
    
    try:
        with open("bug_report_2025_08_01.json", 'r', encoding='utf-8') as f:
            bug_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read bug report: {e}")
        return {}
    
    # Extract patterns
    patterns = {
        "total_bugs_fixed": bug_data.get("session_info", {}).get("total_bugs_fixed", 0),
        "severity_distribution": bug_data.get("session_info", {}).get("severity_distribution", {}),
        "common_root_causes": [],
        "fix_patterns": [],
        "symptoms": []
    }
    
    for bug in bug_data.get("bugs_detailed", []):
        # Root causes
        if bug.get("root_cause"):
            patterns["common_root_causes"].append({
                "bug_id": bug["bug_id"],
                "cause": bug["root_cause"],
                "severity": bug["severity"]
            })
        
        # Fix patterns
        if bug.get("fix_applied"):
            patterns["fix_patterns"].append({
                "bug_id": bug["bug_id"], 
                "approach": bug["fix_applied"]["description"],
                "files": bug["fix_applied"].get("files_modified", [])
            })
        
        # Symptoms
        patterns["symptoms"].extend([
            {"bug_id": bug["bug_id"], "symptom": symptom}
            for symptom in bug.get("symptoms", [])
        ])
    
    return patterns

def analyze_system_structure():
    """Analyze current system structure"""
    logger.info("🏗️ Analyzing system structure...")
    
    # Count components
    src_path = Path("src")
    if not src_path.exists():
        return {"error": "src directory not found"}
    
    structure = {
        "total_python_files": 0,
        "handlers": 0,
        "services": 0, 
        "utils": 0,
        "diagnostic_system": 0,
        "tests": 0,
        "migrations": 0
    }
    
    # Count files
    for py_file in Path(".").rglob("*.py"):
        structure["total_python_files"] += 1
        
        if "handlers" in str(py_file):
            structure["handlers"] += 1
        elif "services" in str(py_file):
            structure["services"] += 1
        elif "utils" in str(py_file):
            structure["utils"] += 1
        elif "diagnostic_system" in str(py_file):
            structure["diagnostic_system"] += 1
        elif "tests" in str(py_file):
            structure["tests"] += 1
        elif "migrations" in str(py_file):
            structure["migrations"] += 1
    
    return structure

def check_configuration():
    """Check configuration files and environment"""
    logger.info("⚙️ Checking configuration...")
    
    config_status = {
        "env_file_exists": os.path.exists(".env"),
        "requirements_exists": os.path.exists("requirements.txt"),
        "config_py_exists": os.path.exists("src/config.py"),
        "database_file_exists": os.path.exists("meeting_scheduler.db"),
        "render_yaml_exists": os.path.exists("render.yaml"),
        "dockerfile_exists": os.path.exists("Dockerfile")
    }
    
    # Check critical environment variables
    critical_vars = [
        "TELEGRAM_BOT_TOKEN",
        "DATABASE_URL", 
        "ADMIN_TELEGRAM_IDS",
        "GOOGLE_SERVICE_ACCOUNT_JSON"
    ]
    
    if config_status["env_file_exists"]:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            env_vars = {}
            for var in critical_vars:
                env_vars[var] = bool(os.getenv(var))
            
            config_status["environment_variables"] = env_vars
        except Exception as e:
            config_status["env_load_error"] = str(e)
    
    return config_status

def check_dependencies():
    """Check dependency status"""
    logger.info("📦 Checking dependencies...")
    
    deps_status = {}
    
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", 'r') as f:
            deps = [line.strip().split('==')[0] for line in f if line.strip() and not line.startswith('#')]
        
        deps_status["total_dependencies"] = len(deps)
        deps_status["key_dependencies"] = {
            "telegram": any("telegram" in dep for dep in deps),
            "google_api": any("google" in dep for dep in deps),
            "database": any(dep in ["psycopg2-binary", "sqlalchemy"] for dep in deps),
            "async": any(dep in ["aiohttp", "asyncio"] for dep in deps),
            "diagnostic": any("networkx" in dep for dep in deps)
        }
    
    return deps_status

def generate_health_assessment():
    """Generate overall health assessment"""
    logger.info("🏥 Generating health assessment...")
    
    health = {
        "overall_score": 0.0,
        "factors": {},
        "issues": [],
        "strengths": []
    }
    
    # Analyze bug fixes - positive factor
    with open("bug_report_2025_08_01.json", 'r') as f:
        bug_data = json.load(f)
    
    total_bugs = bug_data.get("session_info", {}).get("total_bugs_fixed", 0)
    if total_bugs >= 4:
        health["factors"]["recent_bug_fixes"] = 0.8
        health["strengths"].append(f"✅ {total_bugs} critical bugs recently fixed")
    
    # Check configuration completeness
    config = check_configuration()
    config_score = sum(1 for v in config.values() if v is True) / len(config)
    health["factors"]["configuration"] = config_score
    
    if config_score > 0.8:
        health["strengths"].append("✅ Configuration is well-structured")
    else:
        health["issues"].append("⚠️ Configuration may need attention")
    
    # Check system structure
    structure = analyze_system_structure()
    if structure.get("diagnostic_system", 0) > 5:
        health["factors"]["diagnostic_capability"] = 0.9
        health["strengths"].append("✅ Advanced diagnostic system implemented")
    
    # Calculate overall score
    factors = health["factors"]
    if factors:
        health["overall_score"] = sum(factors.values()) / len(factors)
    
    return health

def analyze_deployment_readiness():
    """Analyze readiness for GitHub and Render.com deployment"""
    logger.info("🚀 Analyzing deployment readiness...")
    
    deployment = {
        "github_ready": False,
        "render_ready": False,
        "issues": [],
        "recommendations": []
    }
    
    # GitHub readiness
    github_files = [
        ("README.md", "Project documentation"),
        (".gitignore", "Git ignore file"),
        ("requirements.txt", "Dependencies"),
        ("src/main.py", "Main application")
    ]
    
    github_score = 0
    for file_path, description in github_files:
        if os.path.exists(file_path):
            github_score += 1
        else:
            deployment["issues"].append(f"❌ Missing {description}: {file_path}")
    
    deployment["github_ready"] = github_score >= 3
    
    # Render.com readiness
    render_files = [
        ("render.yaml", "Render configuration"),
        ("Dockerfile", "Docker configuration"),
        ("requirements.txt", "Dependencies")
    ]
    
    render_score = 0
    for file_path, description in render_files:
        if os.path.exists(file_path):
            render_score += 1
        else:
            deployment["issues"].append(f"❌ Missing {description}: {file_path}")
    
    deployment["render_ready"] = render_score >= 2
    
    # Environment variables check
    if os.path.exists(".env"):
        deployment["recommendations"].append("🔒 Remember to set environment variables in Render.com dashboard")
    
    # Database check  
    if os.path.exists("meeting_scheduler.db"):
        deployment["recommendations"].append("🗄️ Configure PostgreSQL database URL for production")
    
    return deployment

def main():
    """Main diagnostic function"""
    logger.info("🛡️ Starting Simple Diagnostic Analysis...")
    
    # Generate comprehensive report
    report = {
        "diagnostic_timestamp": datetime.now().isoformat(),
        "project_name": "meeting-scheduler-bot",
        
        # Pattern analysis
        "bug_patterns": analyze_bug_patterns(),
        
        # System structure
        "system_structure": analyze_system_structure(),
        
        # Configuration
        "configuration": check_configuration(),
        
        # Dependencies
        "dependencies": check_dependencies(),
        
        # Health assessment
        "health_assessment": generate_health_assessment(),
        
        # Deployment readiness
        "deployment_readiness": analyze_deployment_readiness()
    }
    
    # Save report
    report_file = f"simple_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("🛡️ MEETING SCHEDULER BOT - DIAGNOSTIC SUMMARY")
    print("="*60)
    
    health = report["health_assessment"]
    print(f"🏥 Overall Health Score: {health['overall_score']:.2f}/1.0")
    
    print(f"\n📊 System Overview:")
    structure = report["system_structure"] 
    print(f"   📁 Total Python files: {structure['total_python_files']}")
    print(f"   🔧 Handlers: {structure['handlers']}")
    print(f"   ⚙️ Services: {structure['services']}")
    print(f"   🛠️ Utils: {structure['utils']}")
    print(f"   🔍 Diagnostic system: {structure['diagnostic_system']}")
    
    print(f"\n🐛 Previous Bug Analysis:")
    bugs = report["bug_patterns"]
    print(f"   ✅ Bugs fixed: {bugs['total_bugs_fixed']}")
    print(f"   🔍 Root causes identified: {len(bugs['common_root_causes'])}")
    print(f"   🔧 Fix patterns learned: {len(bugs['fix_patterns'])}")
    
    print(f"\n🚀 Deployment Readiness:")
    deploy = report["deployment_readiness"]
    print(f"   📦 GitHub ready: {'✅' if deploy['github_ready'] else '❌'}")
    print(f"   🌐 Render.com ready: {'✅' if deploy['render_ready'] else '❌'}")
    
    print(f"\n💪 Strengths:")
    for strength in health["strengths"]:
        print(f"   {strength}")
    
    if health["issues"]:
        print(f"\n⚠️ Issues to Address:")
        for issue in health["issues"]:
            print(f"   {issue}")
    
    if deploy["recommendations"]:
        print(f"\n💡 Deployment Recommendations:")
        for rec in deploy["recommendations"]:
            print(f"   {rec}")
    
    print(f"\n📋 Full report saved: {report_file}")
    print("="*60)
    
    logger.info("✅ Simple diagnostic analysis complete!")
    return report

if __name__ == "__main__":
    main()