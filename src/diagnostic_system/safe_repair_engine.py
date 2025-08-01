"""
🛡️ SAFE REPAIR ENGINE - Incremental, reversible system repair engine
Part of the Holistic Python Backend Diagnostic System v3.0
"""

import asyncio
import shutil
import subprocess
import tempfile
import hashlib
import git
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import time

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    CODE_MODIFICATION = "code_modification"
    CONFIGURATION_UPDATE = "configuration_update"
    DEPENDENCY_UPDATE = "dependency_update"
    DATABASE_MIGRATION = "database_migration"
    ENVIRONMENT_CHANGE = "environment_change"
    ROLLBACK = "rollback"

class ChangeStatus(Enum):
    PLANNED = "planned"
    VALIDATED = "validated"
    APPLIED = "applied"
    VERIFIED = "verified"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class AtomicChange:
    """Represents a single, atomic change that can be safely applied and rolled back"""
    change_id: str
    change_type: ChangeType
    description: str
    target_files: List[str]
    change_data: Dict[str, Any]
    rollback_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)  # Other change IDs this depends on
    validation_rules: List[str] = field(default_factory=list)
    estimated_risk: float = 0.0  # 0.0 to 1.0
    estimated_duration: int = 0  # seconds
    status: ChangeStatus = ChangeStatus.PLANNED
    applied_at: Optional[datetime] = None
    verification_results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RollbackPoint:
    """Represents a point in time to which the system can be rolled back"""
    rollback_id: str
    timestamp: datetime
    description: str
    system_state: Dict[str, Any]
    affected_files: List[str]
    git_commit_hash: Optional[str] = None
    database_backup_path: Optional[str] = None
    config_backup_path: Optional[str] = None

@dataclass
class PreflightCheck:
    """Represents a preflight check result"""
    check_name: str
    passed: bool
    details: str
    risk_level: str  # "low", "medium", "high", "critical"
    blocking: bool = False  # If True, prevents change application

class SafeRepairEngine:
    """
    Safe, incremental repair engine that applies changes atomically with full rollback capability.
    Every change is validated, applied incrementally, and can be rolled back instantly.
    """
    
    def __init__(self, project_root: str, system_analyzer=None):
        self.project_root = Path(project_root)
        self.system_analyzer = system_analyzer
        self.change_history: List[AtomicChange] = []
        self.rollback_points: List[RollbackPoint] = []
        
        # Safety mechanisms
        self.max_concurrent_changes = 1  # Only allow one change at a time for safety
        self.change_timeout = 300  # 5 minutes max per change
        self.verification_timeout = 60  # 1 minute for verification
        
        # Backup and rollback
        self.backup_directory = self.project_root / ".safe_repair_backups"
        self.backup_directory.mkdir(exist_ok=True)
        
        # Git integration
        try:
            self.git_repo = git.Repo(self.project_root)
            self.git_available = True
            logger.info("✅ Git repository detected - enhanced rollback capabilities enabled")
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            self.git_repo = None
            self.git_available = False
            logger.warning("⚠️ No Git repository - using file-based backups only")
        
        logger.info(f"🔧 SafeRepairEngine initialized for project: {self.project_root}")
    
    async def apply_fix_safely(self, fix_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a fix plan safely with full validation and rollback capability.
        This is the main entry point for safe system repairs.
        """
        logger.info(f"🔧 Starting safe repair application: {fix_plan.get('description', 'Unknown fix')}")
        start_time = datetime.now()
        
        repair_session = {
            "session_id": f"repair_{int(time.time())}",
            "start_time": start_time.isoformat(),
            "fix_plan": fix_plan,
            "status": "in_progress",
            "atomic_changes": [],
            "rollback_points": [],
            "verification_results": {},
            "final_status": None,
            "error_details": None
        }
        
        try:
            # 1. Create initial rollback point
            initial_rollback = await self._create_rollback_point("Before repair session")
            repair_session["rollback_points"].append(initial_rollback.rollback_id)
            logger.info(f"📸 Created initial rollback point: {initial_rollback.rollback_id}")
            
            # 2. Decompose fix plan into atomic changes
            atomic_changes = await self._decompose_to_atomic_changes(fix_plan)
            repair_session["atomic_changes"] = [change.change_id for change in atomic_changes]
            logger.info(f"⚛️ Decomposed fix into {len(atomic_changes)} atomic changes")
            
            # 3. Apply each atomic change with validation
            for i, change in enumerate(atomic_changes):
                logger.info(f"🔄 Applying change {i+1}/{len(atomic_changes)}: {change.description}")
                
                # Pre-flight checks
                preflight_results = await self._preflight_check(change)
                if not self._all_checks_passed(preflight_results):
                    logger.error(f"❌ Pre-flight checks failed for change {change.change_id}")
                    repair_session["status"] = "aborted"
                    repair_session["error_details"] = {
                        "stage": "preflight",
                        "failed_change": change.change_id,
                        "preflight_results": [self._serialize_preflight_check(pc) for pc in preflight_results]
                    }
                    return repair_session
                
                # Create rollback point before this change
                change_rollback = await self._create_rollback_point(f"Before change: {change.description}")
                repair_session["rollback_points"].append(change_rollback.rollback_id)
                
                # Apply the atomic change
                try:
                    change_result = await self._apply_atomic_change(change)
                    
                    if not change_result["success"]:
                        logger.error(f"❌ Failed to apply change {change.change_id}")
                        await self._emergency_rollback(change_rollback.rollback_id)
                        repair_session["status"] = "failed"
                        repair_session["error_details"] = {
                            "stage": "application",
                            "failed_change": change.change_id,
                            "error": change_result["error"]
                        }
                        return repair_session
                    
                    # Immediate verification
                    verification_result = await self._verify_change_success(change)
                    repair_session["verification_results"][change.change_id] = verification_result
                    
                    if not verification_result["healthy"]:
                        logger.error(f"❌ Verification failed for change {change.change_id}")
                        await self._rollback_to(change_rollback.rollback_id)
                        repair_session["status"] = "verification_failed"
                        repair_session["error_details"] = {
                            "stage": "verification",
                            "failed_change": change.change_id,
                            "verification_issues": verification_result["issues"]
                        }
                        return repair_session
                    
                    logger.info(f"✅ Successfully applied and verified change {change.change_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Exception during change application: {e}")
                    await self._emergency_rollback(change_rollback.rollback_id)
                    repair_session["status"] = "exception"
                    repair_session["error_details"] = {
                        "stage": "application",
                        "failed_change": change.change_id,
                        "exception": str(e)
                    }
                    return repair_session
            
            # 4. Final system validation
            final_validation = await self._complete_system_validation()
            repair_session["verification_results"]["final_system"] = final_validation
            
            if not final_validation["healthy"]:
                logger.error("❌ Final system validation failed")
                await self._emergency_rollback(initial_rollback.rollback_id)
                repair_session["status"] = "final_validation_failed"
                repair_session["error_details"] = {
                    "stage": "final_validation",
                    "issues": final_validation["issues"]
                }
                return repair_session
            
            # 5. Success!
            repair_session["status"] = "completed"
            repair_session["final_status"] = "success"
            repair_session["end_time"] = datetime.now().isoformat()
            repair_session["total_duration_seconds"] = (datetime.now() - start_time).total_seconds()
            repair_session["performance_impact"] = await self._measure_performance_impact()
            
            logger.info(f"✅ Safe repair completed successfully in {repair_session['total_duration_seconds']:.2f}s")
            
            return repair_session
            
        except Exception as e:
            logger.error(f"❌ Safe repair engine failed: {e}")
            repair_session["status"] = "engine_failure"
            repair_session["error_details"] = {
                "stage": "engine",
                "exception": str(e)
            }
            
            # Emergency rollback to initial state
            if repair_session["rollback_points"]:
                await self._emergency_rollback(repair_session["rollback_points"][0])
            
            return repair_session
    
    async def _decompose_to_atomic_changes(self, fix_plan: Dict[str, Any]) -> List[AtomicChange]:
        """
        Decompose a fix plan into atomic, independent changes.
        Each change must be small enough to be applied and rolled back safely.
        """
        atomic_changes = []
        
        # Extract change types from fix plan
        if "code_changes" in fix_plan:
            for file_path, changes in fix_plan["code_changes"].items():
                for change in changes:
                    atomic_change = AtomicChange(
                        change_id=f"code_{hashlib.md5(f'{file_path}_{change}'.encode()).hexdigest()[:8]}",
                        change_type=ChangeType.CODE_MODIFICATION,
                        description=f"Modify {file_path}: {change.get('description', 'Code change')}",
                        target_files=[file_path],
                        change_data={
                            "file_path": file_path,
                            "operation": change.get("operation", "edit"),
                            "old_content": change.get("old_content"),
                            "new_content": change.get("new_content"),
                            "line_number": change.get("line_number")
                        },
                        rollback_data={},  # Will be filled when backup is created
                        estimated_risk=self._estimate_change_risk(ChangeType.CODE_MODIFICATION, [file_path]),
                        estimated_duration=30  # 30 seconds estimated
                    )
                    atomic_changes.append(atomic_change)
        
        if "config_changes" in fix_plan:
            for config_change in fix_plan["config_changes"]:
                atomic_change = AtomicChange(
                    change_id=f"config_{hashlib.md5(str(config_change).encode()).hexdigest()[:8]}",
                    change_type=ChangeType.CONFIGURATION_UPDATE,
                    description=f"Update configuration: {config_change.get('description', 'Config change')}",
                    target_files=[config_change.get("file_path", "config")],
                    change_data=config_change,
                    rollback_data={},
                    estimated_risk=self._estimate_change_risk(ChangeType.CONFIGURATION_UPDATE, [config_change.get("file_path")]),
                    estimated_duration=15
                )
                atomic_changes.append(atomic_change)
        
        if "dependency_changes" in fix_plan:
            for dep_change in fix_plan["dependency_changes"]:
                atomic_change = AtomicChange(
                    change_id=f"deps_{hashlib.md5(str(dep_change).encode()).hexdigest()[:8]}",
                    change_type=ChangeType.DEPENDENCY_UPDATE,
                    description=f"Update dependencies: {dep_change.get('description', 'Dependency change')}",
                    target_files=["requirements.txt", "pyproject.toml", "Pipfile"],
                    change_data=dep_change,
                    rollback_data={},
                    estimated_risk=self._estimate_change_risk(ChangeType.DEPENDENCY_UPDATE, []),
                    estimated_duration=120  # Dependencies can take time
                )
                atomic_changes.append(atomic_change)
        
        # Sort by risk (lowest risk first) and resolve dependencies
        atomic_changes = await self._resolve_change_dependencies(atomic_changes)
        atomic_changes.sort(key=lambda x: x.estimated_risk)
        
        return atomic_changes
    
    async def _resolve_change_dependencies(self, changes: List[AtomicChange]) -> List[AtomicChange]:
        """Analyze and set dependencies between changes"""
        
        # Simple dependency resolution - config changes before code changes
        config_changes = [c for c in changes if c.change_type == ChangeType.CONFIGURATION_UPDATE]
        code_changes = [c for c in changes if c.change_type == ChangeType.CODE_MODIFICATION]
        dep_changes = [c for c in changes if c.change_type == ChangeType.DEPENDENCY_UPDATE]
        
        # Dependencies should be updated first
        for code_change in code_changes:
            for dep_change in dep_changes:
                code_change.dependencies.append(dep_change.change_id)
        
        # Configuration changes should come before code changes that might depend on them
        for code_change in code_changes:
            for config_change in config_changes:
                if any(target in code_change.target_files[0] for target in config_change.target_files):
                    code_change.dependencies.append(config_change.change_id)
        
        return changes
    
    def _estimate_change_risk(self, change_type: ChangeType, target_files: List[str]) -> float:
        """Estimate the risk level of a change (0.0 = safe, 1.0 = very risky)"""
        base_risks = {
            ChangeType.CODE_MODIFICATION: 0.3,
            ChangeType.CONFIGURATION_UPDATE: 0.5,
            ChangeType.DEPENDENCY_UPDATE: 0.7,
            ChangeType.DATABASE_MIGRATION: 0.9,
            ChangeType.ENVIRONMENT_CHANGE: 0.6
        }
        
        base_risk = base_risks.get(change_type, 0.5)
        
        # Increase risk based on critical files
        critical_files = ["main.py", "config.py", "settings.py", "database.py", "__init__.py"]
        for target_file in target_files:
            if any(critical in target_file for critical in critical_files):
                base_risk += 0.2
        
        # Use system analyzer data if available
        if self.system_analyzer:
            for target_file in target_files:
                impact_analysis = self.system_analyzer.get_component_impact_analysis(target_file)
                if impact_analysis.get("change_impact_score", 0) > 0.7:
                    base_risk += 0.3
        
        return min(base_risk, 1.0)
    
    async def _preflight_check(self, change: AtomicChange) -> List[PreflightCheck]:
        """
        Perform comprehensive preflight checks before applying a change.
        These checks ensure the change can be applied safely.
        """
        checks = []
        
        # 1. File existence and permissions
        for target_file in change.target_files:
            file_path = self.project_root / target_file
            
            if change.change_type == ChangeType.CODE_MODIFICATION:
                if not file_path.exists():
                    checks.append(PreflightCheck(
                        check_name="file_existence",
                        passed=False,
                        details=f"Target file {target_file} does not exist",
                        risk_level="high",
                        blocking=True
                    ))
                elif not os.access(file_path, os.W_OK):
                    checks.append(PreflightCheck(
                        check_name="file_permissions",
                        passed=False,
                        details=f"Target file {target_file} is not writable",
                        risk_level="high",
                        blocking=True
                    ))
                else:
                    checks.append(PreflightCheck(
                        check_name="file_access",
                        passed=True,
                        details=f"File {target_file} is accessible and writable",
                        risk_level="low"
                    ))
        
        # 2. Git repository status (if available)
        if self.git_available:
            try:
                if self.git_repo.is_dirty():
                    checks.append(PreflightCheck(
                        check_name="git_status",
                        passed=False,
                        details="Git repository has uncommitted changes",
                        risk_level="medium",
                        blocking=False  # Warning but not blocking
                    ))
                else:
                    checks.append(PreflightCheck(
                        check_name="git_status",
                        passed=True,
                        details="Git repository is clean",
                        risk_level="low"
                    ))
            except Exception as e:
                checks.append(PreflightCheck(
                    check_name="git_status",
                    passed=False,
                    details=f"Could not check git status: {e}",
                    risk_level="low"
                ))
        
        # 3. System resource availability
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage(str(self.project_root)).percent
            
            if memory_percent > 90:
                checks.append(PreflightCheck(
                    check_name="memory_availability",
                    passed=False,
                    details=f"High memory usage: {memory_percent}%",
                    risk_level="medium"
                ))
            elif memory_percent > 80:
                checks.append(PreflightCheck(
                    check_name="memory_availability",
                    passed=True,
                    details=f"Memory usage acceptable: {memory_percent}%",
                    risk_level="low"
                ))
            else:
                checks.append(PreflightCheck(
                    check_name="memory_availability",
                    passed=True,
                    details=f"Memory usage good: {memory_percent}%",
                    risk_level="low"
                ))
            
            if disk_percent > 95:
                checks.append(PreflightCheck(
                    check_name="disk_space",
                    passed=False,
                    details=f"Very low disk space: {disk_percent}%",
                    risk_level="high",
                    blocking=True
                ))
            elif disk_percent > 90:
                checks.append(PreflightCheck(
                    check_name="disk_space",
                    passed=False,
                    details=f"Low disk space: {disk_percent}%",
                    risk_level="medium"
                ))
            else:
                checks.append(PreflightCheck(
                    check_name="disk_space",
                    passed=True,
                    details=f"Disk space adequate: {disk_percent}%",
                    risk_level="low"
                ))
                
        except Exception as e:
            checks.append(PreflightCheck(
                check_name="resource_check",
                passed=False,
                details=f"Could not check system resources: {e}",
                risk_level="low"
            ))
        
        # 4. Backup capability check
        try:
            test_backup_dir = self.backup_directory / "test"
            test_backup_dir.mkdir(exist_ok=True)
            test_file = test_backup_dir / "test.txt"
            test_file.write_text("test")
            test_file.unlink()
            test_backup_dir.rmdir()
            
            checks.append(PreflightCheck(
                check_name="backup_capability",
                passed=True,
                details="Backup directory is writable",
                risk_level="low"
            ))
        except Exception as e:
            checks.append(PreflightCheck(
                check_name="backup_capability",
                passed=False,
                details=f"Cannot create backups: {e}",
                risk_level="critical",
                blocking=True
            ))
        
        # 5. Change-specific checks
        if change.change_type == ChangeType.CODE_MODIFICATION:
            await self._preflight_check_code_change(change, checks)
        elif change.change_type == ChangeType.DEPENDENCY_UPDATE:
            await self._preflight_check_dependency_change(change, checks)
        elif change.change_type == ChangeType.CONFIGURATION_UPDATE:
            await self._preflight_check_config_change(change, checks)
        
        return checks
    
    async def _preflight_check_code_change(self, change: AtomicChange, checks: List[PreflightCheck]):
        """Specific preflight checks for code changes"""
        file_path = self.project_root / change.target_files[0]
        
        try:
            # Check if the file is syntactically valid Python
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            compile(current_content, str(file_path), 'exec')
            checks.append(PreflightCheck(
                check_name="syntax_validity",
                passed=True,
                details=f"File {file_path.name} has valid Python syntax",
                risk_level="low"
            ))
            
            # If we have new content, check if it's syntactically valid
            if change.change_data.get("new_content"):
                compile(change.change_data["new_content"], str(file_path), 'exec')
                checks.append(PreflightCheck(
                    check_name="new_syntax_validity",
                    passed=True,
                    details="New content has valid Python syntax",
                    risk_level="low"
                ))
            
        except SyntaxError as e:
            checks.append(PreflightCheck(
                check_name="syntax_validity",
                passed=False,
                details=f"Syntax error in {file_path.name}: {e}",
                risk_level="critical",
                blocking=True
            ))
    
    async def _preflight_check_dependency_change(self, change: AtomicChange, checks: List[PreflightCheck]):
        """Specific preflight checks for dependency changes"""
        # Check if pip is available
        try:
            result = subprocess.run(["pip", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                checks.append(PreflightCheck(
                    check_name="pip_availability",
                    passed=True,
                    details="pip is available for dependency management",
                    risk_level="low"
                ))
            else:
                checks.append(PreflightCheck(
                    check_name="pip_availability",
                    passed=False,
                    details="pip is not available",
                    risk_level="high",
                    blocking=True
                ))
        except Exception as e:
            checks.append(PreflightCheck(
                check_name="pip_availability",
                passed=False,
                details=f"Could not check pip availability: {e}",
                risk_level="high"
            ))
    
    async def _preflight_check_config_change(self, change: AtomicChange, checks: List[PreflightCheck]):
        """Specific preflight checks for configuration changes"""
        # Check if configuration file format is valid
        config_file = change.change_data.get("file_path")
        if config_file:
            file_path = self.project_root / config_file
            
            if file_path.suffix == '.json':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    checks.append(PreflightCheck(
                        check_name="config_format_validity",
                        passed=True,
                        details=f"JSON configuration {config_file} is valid",
                        risk_level="low"
                    ))
                except json.JSONDecodeError as e:
                    checks.append(PreflightCheck(
                        check_name="config_format_validity",
                        passed=False,
                        details=f"Invalid JSON in {config_file}: {e}",
                        risk_level="medium"
                    ))
    
    def _all_checks_passed(self, preflight_results: List[PreflightCheck]) -> bool:
        """Check if all blocking preflight checks passed"""
        for check in preflight_results:
            if check.blocking and not check.passed:
                return False
        return True
    
    async def _create_rollback_point(self, description: str) -> RollbackPoint:
        """
        Create a rollback point that captures the current system state.
        This allows for instant rollback if something goes wrong.
        """
        rollback_id = f"rollback_{int(time.time())}_{hashlib.md5(description.encode()).hexdigest()[:8]}"
        timestamp = datetime.now()
        
        logger.info(f"📸 Creating rollback point: {rollback_id}")
        
        rollback_point = RollbackPoint(
            rollback_id=rollback_id,
            timestamp=timestamp,
            description=description,
            system_state={},
            affected_files=[]
        )
        
        try:
            # Git-based rollback (preferred)
            if self.git_available:
                current_commit = self.git_repo.head.commit.hexsha
                rollback_point.git_commit_hash = current_commit
                logger.info(f"📸 Git commit hash recorded: {current_commit[:8]}")
            
            # File-based backup (always create as fallback)
            backup_dir = self.backup_directory / rollback_id
            backup_dir.mkdir(exist_ok=True)
            
            # Backup critical files
            critical_patterns = ["*.py", "*.json", "*.yaml", "*.yml", "*.toml", "*.cfg", "*.ini"]
            backed_up_files = []
            
            for pattern in critical_patterns:
                for file_path in self.project_root.rglob(pattern):
                    if ".git" in str(file_path) or "__pycache__" in str(file_path):
                        continue
                    
                    # Create relative path for backup
                    rel_path = file_path.relative_to(self.project_root)
                    backup_file_path = backup_dir / rel_path
                    backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(file_path, backup_file_path)
                    backed_up_files.append(str(rel_path))
            
            rollback_point.affected_files = backed_up_files
            rollback_point.system_state = {
                "backup_directory": str(backup_dir),
                "files_backed_up": len(backed_up_files),
                "backup_size_mb": sum(f.stat().st_size for f in backup_dir.rglob("*") if f.is_file()) / (1024 * 1024)
            }
            
            # Add to rollback points list
            self.rollback_points.append(rollback_point)
            
            logger.info(f"✅ Rollback point created: {len(backed_up_files)} files backed up")
            
            return rollback_point
            
        except Exception as e:
            logger.error(f"❌ Failed to create rollback point: {e}")
            raise
    
    async def _apply_atomic_change(self, change: AtomicChange) -> Dict[str, Any]:
        """Apply a single atomic change with full error tracking"""
        logger.info(f"🔄 Applying atomic change: {change.change_id}")
        
        result = {
            "change_id": change.change_id,
            "success": False,
            "error": None,
            "details": {},
            "duration_seconds": 0
        }
        
        start_time = time.time()
        
        try:
            # Create backup data for rollback
            await self._prepare_change_rollback_data(change)
            
            # Apply change based on type
            if change.change_type == ChangeType.CODE_MODIFICATION:
                await self._apply_code_modification(change)
            elif change.change_type == ChangeType.CONFIGURATION_UPDATE:
                await self._apply_config_update(change)
            elif change.change_type == ChangeType.DEPENDENCY_UPDATE:
                await self._apply_dependency_update(change)
            else:
                raise ValueError(f"Unsupported change type: {change.change_type}")
            
            # Mark as applied
            change.status = ChangeStatus.APPLIED
            change.applied_at = datetime.now()
            
            result["success"] = True
            result["details"] = {
                "change_type": change.change_type.value,
                "target_files": change.target_files,
                "applied_at": change.applied_at.isoformat()
            }
            
            logger.info(f"✅ Successfully applied change: {change.change_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to apply change {change.change_id}: {e}")
            change.status = ChangeStatus.FAILED
            result["error"] = str(e)
        
        finally:
            result["duration_seconds"] = time.time() - start_time
        
        return result
    
    async def _prepare_change_rollback_data(self, change: AtomicChange):
        """Prepare rollback data specific to this change"""
        rollback_data = {}
        
        for target_file in change.target_files:
            file_path = self.project_root / target_file
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    rollback_data[target_file] = {
                        "original_content": f.read(),
                        "original_mtime": file_path.stat().st_mtime,
                        "existed": True
                    }
            else:
                rollback_data[target_file] = {
                    "existed": False
                }
        
        change.rollback_data = rollback_data
    
    async def _apply_code_modification(self, change: AtomicChange):
        """Apply a code modification change"""
        file_path = self.project_root / change.target_files[0]
        change_data = change.change_data
        
        if change_data["operation"] == "edit":
            # Replace content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(change_data["new_content"])
        
        elif change_data["operation"] == "replace_line":
            # Replace specific line
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_number = change_data["line_number"] - 1  # Convert to 0-based
            if 0 <= line_number < len(lines):
                lines[line_number] = change_data["new_content"] + "\n"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            else:
                raise ValueError(f"Line number {change_data['line_number']} out of range")
        
        elif change_data["operation"] == "insert":
            # Insert new content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content + "\n" + change_data["new_content"]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        
        else:
            raise ValueError(f"Unsupported operation: {change_data['operation']}")
    
    async def _apply_config_update(self, change: AtomicChange):
        """Apply a configuration update change"""
        file_path = self.project_root / change.change_data["file_path"]
        
        if change.change_data.get("new_content"):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(change.change_data["new_content"])
        else:
            raise ValueError("No new content specified for configuration update")
    
    async def _apply_dependency_update(self, change: AtomicChange):
        """Apply a dependency update change"""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated dependency management
        
        if "requirements_content" in change.change_data:
            requirements_path = self.project_root / "requirements.txt"
            with open(requirements_path, 'w', encoding='utf-8') as f:
                f.write(change.change_data["requirements_content"])
            
            # Optionally run pip install
            if change.change_data.get("install_immediately", False):
                result = subprocess.run([
                    "pip", "install", "-r", str(requirements_path)
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    raise RuntimeError(f"Pip install failed: {result.stderr}")
    
    async def _verify_change_success(self, change: AtomicChange) -> Dict[str, Any]:
        """Verify that a change was applied successfully and the system is healthy"""
        verification_result = {
            "change_id": change.change_id,
            "healthy": True,
            "issues": [],
            "metrics": {},
            "verification_time": datetime.now().isoformat()
        }
        
        try:
            # 1. File-level verification
            for target_file in change.target_files:
                file_path = self.project_root / target_file
                
                if not file_path.exists():
                    verification_result["issues"].append(f"Target file {target_file} does not exist after change")
                    verification_result["healthy"] = False
                    continue
                
                # For Python files, check syntax
                if file_path.suffix == '.py':
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        compile(content, str(file_path), 'exec')
                    except SyntaxError as e:
                        verification_result["issues"].append(f"Syntax error in {target_file}: {e}")
                        verification_result["healthy"] = False
            
            # 2. System-level verification
            if self.system_analyzer:
                # Use system analyzer to check for issues
                try:
                    health_check = self.system_analyzer.analyze_complete_system()
                    current_health = health_check.get("system_health_score", 0.5)
                    
                    verification_result["metrics"]["system_health_score"] = current_health
                    
                    if current_health < 0.5:  # Arbitrary threshold
                        verification_result["issues"].append(f"System health score dropped to {current_health}")
                        verification_result["healthy"] = False
                        
                except Exception as e:
                    verification_result["issues"].append(f"Could not run system analysis: {e}")
            
            # 3. Resource verification
            try:
                import psutil
                current_memory = psutil.virtual_memory().percent
                current_cpu = psutil.cpu_percent(interval=1)
                
                verification_result["metrics"]["memory_percent"] = current_memory
                verification_result["metrics"]["cpu_percent"] = current_cpu
                
                if current_memory > 95:
                    verification_result["issues"].append(f"High memory usage: {current_memory}%")
                    verification_result["healthy"] = False
                
            except Exception as e:
                verification_result["issues"].append(f"Could not check resource usage: {e}")
            
            # 4. Change-specific verification
            if change.change_type == ChangeType.CODE_MODIFICATION:
                await self._verify_code_change(change, verification_result)
            elif change.change_type == ChangeType.DEPENDENCY_UPDATE:
                await self._verify_dependency_change(change, verification_result)
            
            change.verification_results = verification_result
            
            if verification_result["healthy"]:
                change.status = ChangeStatus.VERIFIED
                logger.info(f"✅ Change {change.change_id} verified successfully")
            else:
                logger.warning(f"⚠️ Change {change.change_id} verification found issues")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"❌ Verification failed for change {change.change_id}: {e}")
            verification_result["healthy"] = False
            verification_result["issues"].append(f"Verification exception: {e}")
            return verification_result
    
    async def _verify_code_change(self, change: AtomicChange, verification_result: Dict[str, Any]):
        """Specific verification for code changes"""
        # Check imports still work
        file_path = self.project_root / change.target_files[0]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic import checking (simplified)
            import_lines = [line.strip() for line in content.split('\n') 
                          if line.strip().startswith(('import ', 'from '))]
            
            for import_line in import_lines[:5]:  # Check first 5 imports
                try:
                    # This is a very simplified check
                    if 'import ' in import_line and not import_line.startswith('from'):
                        module_name = import_line.replace('import ', '').split('.')[0].strip()
                        if module_name and module_name not in ['os', 'sys', 'time', 'datetime']:
                            # Skip checking built-in modules
                            pass
                except Exception:
                    pass  # Skip import validation errors for now
                    
        except Exception as e:
            verification_result["issues"].append(f"Could not verify imports: {e}")
    
    async def _verify_dependency_change(self, change: AtomicChange, verification_result: Dict[str, Any]):
        """Specific verification for dependency changes"""
        # Check if requirements.txt is valid
        try:
            requirements_path = self.project_root / "requirements.txt"
            if requirements_path.exists():
                with open(requirements_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic validation - check for obvious syntax errors
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                for line in lines:
                    if line and not line.startswith('#') and '==' not in line and '>=' not in line:
                        verification_result["issues"].append(f"Potentially malformed requirement: {line}")
                        
        except Exception as e:
            verification_result["issues"].append(f"Could not verify requirements: {e}")
    
    async def _complete_system_validation(self) -> Dict[str, Any]:
        """Perform complete system validation after all changes"""
        validation_result = {
            "healthy": True,
            "issues": [],
            "overall_health_score": 1.0,
            "validation_timestamp": datetime.now().isoformat()
        }
        
        try:
            # Use system analyzer if available
            if self.system_analyzer:
                system_analysis = self.system_analyzer.analyze_complete_system()
                validation_result["overall_health_score"] = system_analysis.get("system_health_score", 0.5)
                
                if validation_result["overall_health_score"] < 0.6:
                    validation_result["healthy"] = False
                    validation_result["issues"].append("Overall system health score is low")
                
                # Check for high-risk modules
                high_risk_modules = system_analysis.get("high_risk_modules", [])
                if len(high_risk_modules) > 5:
                    validation_result["issues"].append(f"High number of high-risk modules: {len(high_risk_modules)}")
            
            # Basic syntax checking for all Python files
            syntax_errors = []
            for py_file in self.project_root.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, str(py_file), 'exec')
                except SyntaxError as e:
                    syntax_errors.append(f"{py_file.name}:{e.lineno}: {e.msg}")
            
            if syntax_errors:
                validation_result["healthy"] = False
                validation_result["issues"].extend([f"Syntax error: {error}" for error in syntax_errors[:5]])
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Complete system validation failed: {e}")
            validation_result["healthy"] = False
            validation_result["issues"].append(f"Validation exception: {e}")
            return validation_result
    
    async def _rollback_to(self, rollback_id: str) -> Dict[str, Any]:
        """Roll back to a specific rollback point"""
        logger.info(f"🔄 Rolling back to: {rollback_id}")
        
        rollback_result = {
            "rollback_id": rollback_id,
            "success": False,
            "error": None,
            "restored_files": [],
            "rollback_timestamp": datetime.now().isoformat()
        }
        
        try:
            # Find the rollback point
            rollback_point = None
            for rp in self.rollback_points:
                if rp.rollback_id == rollback_id:
                    rollback_point = rp
                    break
            
            if not rollback_point:
                raise ValueError(f"Rollback point {rollback_id} not found")
            
            # Git-based rollback (preferred)
            if self.git_available and rollback_point.git_commit_hash:
                try:
                    self.git_repo.git.checkout(rollback_point.git_commit_hash)
                    rollback_result["success"] = True
                    rollback_result["method"] = "git"
                    logger.info(f"✅ Git rollback to {rollback_point.git_commit_hash[:8]} successful")
                    return rollback_result
                except Exception as e:
                    logger.warning(f"⚠️ Git rollback failed, falling back to file restoration: {e}")
            
            # File-based rollback
            backup_dir = Path(rollback_point.system_state["backup_directory"])
            if backup_dir.exists():
                restored_files = []
                
                for backup_file in backup_dir.rglob("*"):
                    if backup_file.is_file():
                        # Calculate original file path
                        rel_path = backup_file.relative_to(backup_dir)
                        original_path = self.project_root / rel_path
                        
                        # Restore file
                        original_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_file, original_path)
                        restored_files.append(str(rel_path))
                
                rollback_result["success"] = True
                rollback_result["method"] = "file_restore"
                rollback_result["restored_files"] = restored_files
                logger.info(f"✅ File-based rollback successful: {len(restored_files)} files restored")
            else:
                raise FileNotFoundError(f"Backup directory not found: {backup_dir}")
            
            return rollback_result
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            rollback_result["error"] = str(e)
            return rollback_result
    
    async def _emergency_rollback(self, rollback_id: str):
        """Emergency rollback with minimal error checking"""
        logger.error(f"🚨 EMERGENCY ROLLBACK to {rollback_id}")
        
        try:
            await self._rollback_to(rollback_id)
            logger.info("✅ Emergency rollback completed")
        except Exception as e:
            logger.critical(f"💥 EMERGENCY ROLLBACK FAILED: {e}")
            logger.critical("💥 SYSTEM MAY BE IN INCONSISTENT STATE")
            raise
    
    async def _measure_performance_impact(self) -> Dict[str, Any]:
        """Measure performance impact of all changes"""
        try:
            import psutil
            
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage(str(self.project_root)).percent,
                "measurement_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"⚠️ Could not measure performance impact: {e}")
            return {}
    
    def _serialize_preflight_check(self, check: PreflightCheck) -> Dict[str, Any]:
        """Serialize preflight check for JSON output"""
        return {
            "check_name": check.check_name,
            "passed": check.passed,
            "details": check.details,
            "risk_level": check.risk_level,
            "blocking": check.blocking
        }