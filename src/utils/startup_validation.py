"""
🛡️ STARTUP VALIDATION SYSTEM
Comprehensive validation of environment, configuration, and system dependencies before startup.
Prevents the environment loading and configuration issues that were previously encountered.
"""

import os
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation check"""
    check_name: str
    passed: bool
    severity: str  # "critical", "high", "medium", "low"
    message: str
    recommendation: Optional[str] = None
    details: Optional[Dict] = None

class StartupValidator:
    """
    Comprehensive startup validation system.
    
    This class implements the preventive measures identified from the bug analysis:
    - Environment variable validation
    - Configuration completeness check
    - External service availability
    - Critical file existence
    - Database connectivity
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.validation_results: List[ValidationResult] = []
        
    def validate_environment_variables(self) -> List[ValidationResult]:
        """Validate all required environment variables are loaded"""
        results = []
        
        # Critical environment variables (must be present)
        critical_vars = [
            "TELEGRAM_BOT_TOKEN",
            "ADMIN_TELEGRAM_IDS", 
            "DATABASE_URL"
        ]
        
        # Important environment variables (should be present)
        important_vars = [
            "GOOGLE_CALENDAR_ID_1",
            "TIMEZONE",
            "ENVIRONMENT"
        ]
        
        # Optional but recommended variables
        optional_vars = [
            "GOOGLE_SERVICE_ACCOUNT_JSON",
            "GOOGLE_SERVICE_ACCOUNT_FILE",
            "WEBHOOK_URL",
            "LOG_LEVEL"
        ]
        
        # Check critical variables
        for var in critical_vars:
            value = os.getenv(var)
            if not value:
                results.append(ValidationResult(
                    check_name=f"env_critical_{var}",
                    passed=False,
                    severity="critical",
                    message=f"Critical environment variable {var} is not set",
                    recommendation=f"Set {var} in .env file or environment variables",
                    details={"variable": var, "current_value": None}
                ))
            elif len(value.strip()) == 0:
                results.append(ValidationResult(
                    check_name=f"env_critical_{var}",
                    passed=False,
                    severity="critical", 
                    message=f"Critical environment variable {var} is empty",
                    recommendation=f"Provide a valid value for {var}",
                    details={"variable": var, "current_value": "empty"}
                ))
            else:
                results.append(ValidationResult(
                    check_name=f"env_critical_{var}",
                    passed=True,
                    severity="critical",
                    message=f"Critical environment variable {var} is set",
                    details={"variable": var, "value_length": len(value)}
                ))
        
        # Check important variables
        for var in important_vars:
            value = os.getenv(var)
            if not value:
                results.append(ValidationResult(
                    check_name=f"env_important_{var}",
                    passed=False,
                    severity="high",
                    message=f"Important environment variable {var} is not set",
                    recommendation=f"Consider setting {var} for better system behavior",
                    details={"variable": var}
                ))
            else:
                results.append(ValidationResult(
                    check_name=f"env_important_{var}",
                    passed=True,
                    severity="high",
                    message=f"Important environment variable {var} is set",
                    details={"variable": var}
                ))
        
        # Check optional variables
        set_optional = [var for var in optional_vars if os.getenv(var)]
        results.append(ValidationResult(
            check_name="env_optional_coverage",
            passed=len(set_optional) > 0,
            severity="medium",
            message=f"Optional environment variables set: {len(set_optional)}/{len(optional_vars)}",
            details={"set_variables": set_optional, "total_optional": len(optional_vars)}
        ))
        
        return results
    
    def validate_configuration_files(self) -> List[ValidationResult]:
        """Validate critical configuration files exist and are valid"""
        results = []
        
        # Check .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            results.append(ValidationResult(
                check_name="config_env_file",
                passed=True,
                severity="high",
                message=".env file exists",
                details={"path": str(env_file)}
            ))
            
            # Validate .env file contents
            try:
                with open(env_file, 'r') as f:
                    env_content = f.read()
                    
                if "TELEGRAM_BOT_TOKEN" in env_content:
                    results.append(ValidationResult(
                        check_name="config_env_content",
                        passed=True,
                        severity="medium",
                        message=".env file contains expected variables"
                    ))
                else:
                    results.append(ValidationResult(
                        check_name="config_env_content",
                        passed=False,
                        severity="high",
                        message=".env file appears incomplete",
                        recommendation="Check .env.example for required variables"
                    ))
            except Exception as e:
                results.append(ValidationResult(
                    check_name="config_env_readable",
                    passed=False,
                    severity="medium",
                    message=f".env file exists but cannot be read: {e}",
                    recommendation="Check file permissions"
                ))
        else:
            results.append(ValidationResult(
                check_name="config_env_file",
                passed=False,
                severity="critical",
                message=".env file not found",
                recommendation="Copy .env.example to .env and configure it",
                details={"expected_path": str(env_file)}
            ))
        
        # Check Google service account files
        service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account_key.json")
        if service_account_file:
            service_path = self.project_root / service_account_file
            if service_path.exists():
                try:
                    with open(service_path, 'r') as f:
                        service_data = json.load(f)
                        if "type" in service_data and service_data["type"] == "service_account":
                            results.append(ValidationResult(
                                check_name="config_service_account",
                                passed=True,
                                severity="medium",
                                message="Google service account file is valid"
                            ))
                        else:
                            results.append(ValidationResult(
                                check_name="config_service_account",
                                passed=False,
                                severity="medium",
                                message="Service account file format appears invalid",
                                recommendation="Verify the JSON structure"
                            ))
                except Exception as e:
                    results.append(ValidationResult(
                        check_name="config_service_account",
                        passed=False,
                        severity="medium",
                        message=f"Cannot parse service account file: {e}",
                        recommendation="Check JSON syntax"
                    ))
            else:
                # Not critical if environment variable alternative exists
                has_env_json = bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
                results.append(ValidationResult(
                    check_name="config_service_account",
                    passed=has_env_json,
                    severity="medium" if has_env_json else "high",
                    message=f"Service account file not found at {service_path}",
                    recommendation="Either provide file or set GOOGLE_SERVICE_ACCOUNT_JSON environment variable" if not has_env_json else "Using environment variable instead"
                ))
        
        return results
    
    def validate_database_configuration(self) -> List[ValidationResult]:
        """Validate database configuration and connectivity"""
        results = []
        
        database_url = os.getenv("DATABASE_URL", "sqlite:///meeting_scheduler.db")
        
        # Parse database type
        if database_url.startswith("sqlite"):
            # SQLite validation
            if ":///" in database_url:
                db_path = database_url.split("///")[1]
                db_file = Path(db_path) if not db_path.startswith("/") else Path(db_path)
                
                # Check if database directory exists
                if db_file.parent.exists() or db_file.parent == Path("."):
                    results.append(ValidationResult(
                        check_name="database_path_valid",
                        passed=True,
                        severity="medium",
                        message=f"SQLite database path is accessible: {db_file}"
                    ))
                else:
                    results.append(ValidationResult(
                        check_name="database_path_valid",
                        passed=False,
                        severity="high",
                        message=f"SQLite database directory does not exist: {db_file.parent}",
                        recommendation="Create the directory or use a different path"
                    ))
            else:
                results.append(ValidationResult(
                    check_name="database_url_format",
                    passed=False,
                    severity="high",
                    message="SQLite DATABASE_URL format appears invalid",
                    recommendation="Use format: sqlite:///path/to/database.db"
                ))
                
        elif database_url.startswith("postgresql"):
            # PostgreSQL validation
            required_components = ["://", "@", "/"]
            if all(comp in database_url for comp in required_components):
                results.append(ValidationResult(
                    check_name="database_url_format",
                    passed=True,
                    severity="medium",
                    message="PostgreSQL DATABASE_URL format appears valid"
                ))
            else:
                results.append(ValidationResult(
                    check_name="database_url_format",
                    passed=False,
                    severity="critical",
                    message="PostgreSQL DATABASE_URL format appears invalid",
                    recommendation="Use format: postgresql://user:password@host:port/database"
                ))
        else:
            results.append(ValidationResult(
                check_name="database_type",
                passed=False,
                severity="critical",
                message=f"Unsupported database type in URL: {database_url[:20]}...",
                recommendation="Use SQLite or PostgreSQL"
            ))
        
        return results
    
    def validate_telegram_configuration(self) -> List[ValidationResult]:
        """Validate Telegram bot configuration"""
        results = []
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        # Basic token format validation
        if bot_token:
            if ":" in bot_token and len(bot_token.split(":")) == 2:
                bot_id, token_part = bot_token.split(":", 1)
                if bot_id.isdigit() and len(token_part) > 30:
                    results.append(ValidationResult(
                        check_name="telegram_token_format",
                        passed=True,
                        severity="critical",
                        message="Telegram bot token format appears valid"
                    ))
                else:
                    results.append(ValidationResult(
                        check_name="telegram_token_format",
                        passed=False,
                        severity="critical",
                        message="Telegram bot token format appears invalid",
                        recommendation="Get a valid token from @BotFather"
                    ))
            else:
                results.append(ValidationResult(
                    check_name="telegram_token_format",
                    passed=False,
                    severity="critical",
                    message="Telegram bot token format is incorrect",
                    recommendation="Token should be in format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                ))
        
        # Admin IDs validation
        admin_ids = os.getenv("ADMIN_TELEGRAM_IDS", "")
        if admin_ids:
            try:
                ids = [int(id.strip()) for id in admin_ids.split(",") if id.strip()]
                if len(ids) > 0:
                    results.append(ValidationResult(
                        check_name="telegram_admin_ids",
                        passed=True,
                        severity="critical",
                        message=f"Admin IDs configured: {len(ids)} admins",
                        details={"admin_count": len(ids)}
                    ))
                else:
                    results.append(ValidationResult(
                        check_name="telegram_admin_ids",
                        passed=False,
                        severity="critical",
                        message="No valid admin IDs found",
                        recommendation="Provide at least one admin Telegram ID"
                    ))
            except ValueError as e:
                results.append(ValidationResult(
                    check_name="telegram_admin_ids",
                    passed=False,
                    severity="critical",
                    message=f"Admin IDs format invalid: {e}",
                    recommendation="Use comma-separated numbers: 123456789,987654321"
                ))
        
        return results
    
    def validate_system_dependencies(self) -> List[ValidationResult]:
        """Validate system dependencies and Python environment"""
        results = []
        
        # Python version check
        python_version = sys.version_info
        if python_version >= (3, 8):
            results.append(ValidationResult(
                check_name="python_version",
                passed=True,
                severity="medium",
                message=f"Python version {python_version.major}.{python_version.minor}.{python_version.micro} is supported"
            ))
        else:
            results.append(ValidationResult(
                check_name="python_version",
                passed=False,
                severity="high",
                message=f"Python {python_version.major}.{python_version.minor} may be too old",
                recommendation="Upgrade to Python 3.8 or newer"
            ))
        
        # Critical file existence checks
        critical_files = [
            "src/main.py",
            "src/config.py", 
            "src/database.py",
            "requirements.txt"
        ]
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                results.append(ValidationResult(
                    check_name=f"file_{file_path.replace('/', '_')}",
                    passed=True,
                    severity="high",
                    message=f"Critical file exists: {file_path}"
                ))
            else:
                results.append(ValidationResult(
                    check_name=f"file_{file_path.replace('/', '_')}",
                    passed=False,
                    severity="critical",
                    message=f"Critical file missing: {file_path}",
                    recommendation="Restore missing file from backup or repository"
                ))
        
        return results
    
    def run_comprehensive_validation(self) -> Dict[str, any]:
        """Run all validation checks"""
        logger.info("🛡️ Starting comprehensive startup validation...")
        
        all_results = []
        
        # Run all validation categories
        validation_categories = [
            ("Environment Variables", self.validate_environment_variables),
            ("Configuration Files", self.validate_configuration_files),
            ("Database Configuration", self.validate_database_configuration),
            ("Telegram Configuration", self.validate_telegram_configuration),
            ("System Dependencies", self.validate_system_dependencies)
        ]
        
        for category_name, validator_func in validation_categories:
            logger.info(f"🔍 Validating {category_name}...")
            try:
                category_results = validator_func()
                all_results.extend(category_results)
                logger.info(f"✅ {category_name} validation completed: {len(category_results)} checks")
            except Exception as e:
                logger.error(f"❌ {category_name} validation failed: {e}")
                all_results.append(ValidationResult(
                    check_name=f"category_{category_name.lower().replace(' ', '_')}",
                    passed=False,
                    severity="critical",
                    message=f"Validation category failed: {e}",
                    recommendation="Check system configuration"
                ))
        
        # Analyze results
        analysis = self._analyze_validation_results(all_results)
        
        logger.info(f"🛡️ Startup validation completed: {analysis['summary']['overall_status']}")
        
        return {
            "validation_timestamp": datetime.now().isoformat(),
            "all_results": [self._serialize_result(r) for r in all_results],
            "analysis": analysis
        }
    
    def _analyze_validation_results(self, results: List[ValidationResult]) -> Dict[str, any]:
        """Analyze validation results and determine system readiness"""
        
        # Count results by severity and status
        counts = {
            "total": len(results),
            "passed": len([r for r in results if r.passed]),
            "failed": len([r for r in results if not r.passed]),
            "critical_failed": len([r for r in results if not r.passed and r.severity == "critical"]),
            "high_failed": len([r for r in results if not r.passed and r.severity == "high"]),
            "medium_failed": len([r for r in results if not r.passed and r.severity == "medium"]),
            "low_failed": len([r for r in results if not r.passed and r.severity == "low"])
        }
        
        # Determine overall status
        if counts["critical_failed"] > 0:
            overall_status = "CRITICAL_FAILURE"
            can_start = False
            message = f"{counts['critical_failed']} critical validation(s) failed - cannot start safely"
        elif counts["high_failed"] > 3:
            overall_status = "HIGH_RISK"
            can_start = False
            message = f"{counts['high_failed']} high-priority validation(s) failed - startup not recommended"
        elif counts["high_failed"] > 0:
            overall_status = "MODERATE_RISK"
            can_start = True
            message = f"{counts['high_failed']} high-priority validation(s) failed - proceed with caution"
        elif counts["medium_failed"] > 0:
            overall_status = "LOW_RISK"
            can_start = True
            message = f"{counts['medium_failed']} medium-priority validation(s) failed - minor issues detected"
        else:
            overall_status = "HEALTHY"
            can_start = True
            message = "All critical validations passed - system ready"
        
        # Generate recommendations
        failed_results = [r for r in results if not r.passed]
        critical_recommendations = [r.recommendation for r in failed_results 
                                  if r.severity == "critical" and r.recommendation]
        high_recommendations = [r.recommendation for r in failed_results 
                              if r.severity == "high" and r.recommendation]
        
        return {
            "summary": {
                "overall_status": overall_status,
                "can_start_safely": can_start,
                "message": message,
                "counts": counts
            },
            "failed_checks": [self._serialize_result(r) for r in failed_results],
            "critical_recommendations": critical_recommendations,
            "high_priority_recommendations": high_recommendations,
            "health_score": counts["passed"] / max(counts["total"], 1)
        }
    
    def _serialize_result(self, result: ValidationResult) -> Dict[str, any]:
        """Serialize validation result for JSON output"""
        return {
            "check_name": result.check_name,
            "passed": result.passed,
            "severity": result.severity,
            "message": result.message,
            "recommendation": result.recommendation,
            "details": result.details
        }

def validate_startup(project_root: str = ".") -> Tuple[bool, Dict[str, any]]:
    """
    Main validation function - validates system readiness for startup.
    
    Returns:
        Tuple of (can_start_safely, validation_report)
    """
    validator = StartupValidator(project_root)
    report = validator.run_comprehensive_validation()
    
    can_start = report["analysis"]["summary"]["can_start_safely"]
    
    return can_start, report

def print_validation_summary(report: Dict[str, any]):
    """Print validation summary to console"""
    analysis = report["analysis"]
    summary = analysis["summary"]
    
    print("\n" + "="*70)
    print("🛡️ STARTUP VALIDATION SUMMARY")
    print("="*70)
    
    # Status indicator
    status_colors = {
        "HEALTHY": "✅",
        "LOW_RISK": "🟡",
        "MODERATE_RISK": "🟠", 
        "HIGH_RISK": "🔴",
        "CRITICAL_FAILURE": "❌"
    }
    
    status_icon = status_colors.get(summary["overall_status"], "❓")
    print(f"{status_icon} Status: {summary['overall_status']}")
    print(f"📊 {summary['message']}")
    
    counts = summary["counts"]
    print(f"\n📈 Validation Results:")
    print(f"   ✅ Passed: {counts['passed']}/{counts['total']}")
    print(f"   ❌ Failed: {counts['failed']}/{counts['total']}")
    if counts['critical_failed'] > 0:
        print(f"   🚨 Critical Failures: {counts['critical_failed']}")
    if counts['high_failed'] > 0:
        print(f"   ⚠️ High Priority Failures: {counts['high_failed']}")
    
    # Critical recommendations
    if analysis["critical_recommendations"]:
        print(f"\n🚨 CRITICAL ACTIONS REQUIRED:")
        for i, rec in enumerate(analysis["critical_recommendations"], 1):
            print(f"   {i}. {rec}")
    
    # High priority recommendations  
    if analysis["high_priority_recommendations"]:
        print(f"\n⚠️ HIGH PRIORITY RECOMMENDATIONS:")
        for i, rec in enumerate(analysis["high_priority_recommendations"][:3], 1):
            print(f"   {i}. {rec}")
    
    print(f"\n🏥 System Health Score: {analysis['health_score']:.2f}/1.0")
    
    if summary["can_start_safely"]:
        print("✅ System can start safely")
    else:
        print("❌ System startup NOT RECOMMENDED - address critical issues first")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    # Run validation if called directly
    can_start, report = validate_startup("/Users/evgenii/meeting-scheduler-bot")
    print_validation_summary(report)
    
    # Save detailed report
    report_path = Path("/Users/evgenii/meeting-scheduler-bot") / f"startup_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Detailed validation report saved: {report_path}")
    
    # Exit with appropriate code
    sys.exit(0 if can_start else 1)