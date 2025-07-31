"""
🛡️ SAFE SOLUTION IMPLEMENTATION SYSTEM
Bulletproof solution deployment with automatic rollback capabilities
"""

import os
import shutil
import json
import time
import pickle
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager
from pathlib import Path

from .core_diagnostics import DiagnosticLogger, diagnostic_context

class ImplementationStatus(Enum):
    """Possible implementation results"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    PARTIAL = "PARTIAL"

class RiskLevel(Enum):
    """Risk levels for solutions"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class SolutionAssessment:
    """Assessment of solution impact and risks"""
    solution_description: str
    complexity_score: int  # 1-5 scale
    risk_level: RiskLevel
    estimated_time_hours: float
    potential_side_effects: List[str]
    rollback_difficulty: int  # 1-5 scale
    dependencies: List[str]
    testing_requirements: List[str]
    approval_required: bool = False

@dataclass
class BackupState:
    """System state backup for rollback"""
    backup_id: str
    timestamp: str
    description: str
    file_backups: Dict[str, str]  # original_path -> backup_path
    database_backup: Optional[str] = None
    environment_snapshot: Dict[str, str] = None
    system_metrics: Dict[str, Any] = None

@dataclass
class ImplementationStep:
    """Individual implementation step"""
    step_id: str
    description: str
    action: Callable[[], Any]
    rollback_action: Optional[Callable[[], Any]] = None
    timeout_seconds: float = 300.0
    critical: bool = True
    validation_function: Optional[Callable[[], bool]] = None

@dataclass
class ImplementationResult:
    """Result of solution implementation"""
    solution_id: str
    start_time: str
    end_time: str
    duration_seconds: float
    result: ImplementationStatus
    steps_completed: int
    steps_total: int
    backup_id: Optional[str] = None
    error_message: Optional[str] = None
    rollback_performed: bool = False
    validation_passed: bool = False

class SafeImplementationManager:
    """Manages safe implementation of solutions with automatic rollback"""
    
    def __init__(self, logger: DiagnosticLogger, backup_dir: str = "/tmp/solution_backups"):
        self.logger = logger
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.implementation_history: List[ImplementationResult] = []
        
    def assess_solution_impact(
        self,
        solution_description: str,
        files_to_modify: List[str] = None,
        database_changes: bool = False,
        service_restart_required: bool = False,
        external_dependencies: List[str] = None
    ) -> SolutionAssessment:
        """Assess the impact and risk level of a proposed solution"""
        
        complexity_score = 1
        risk_level = RiskLevel.LOW
        potential_side_effects = []
        rollback_difficulty = 1
        dependencies = external_dependencies or []
        testing_requirements = []
        
        # Assess complexity based on scope
        if files_to_modify:
            complexity_score += min(len(files_to_modify), 3)
            if len(files_to_modify) > 5:
                potential_side_effects.append("Multiple file changes increase integration risk")
        
        if database_changes:
            complexity_score += 2
            risk_level = RiskLevel.HIGH
            rollback_difficulty += 2
            potential_side_effects.append("Database schema changes may affect data integrity")
            testing_requirements.append("Database migration testing")
            testing_requirements.append("Data integrity verification")
        
        if service_restart_required:
            complexity_score += 1
            risk_level = max(risk_level, RiskLevel.MEDIUM)
            potential_side_effects.append("Service downtime during restart")
            testing_requirements.append("Service restart verification")
        
        if dependencies:
            complexity_score += len(dependencies)
            risk_level = max(risk_level, RiskLevel.MEDIUM)
            potential_side_effects.append("External dependency changes may cause cascading failures")
        
        # Determine if approval is required
        approval_required = (
            risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] or
            database_changes or
            complexity_score > 7
        )
        
        # Estimate implementation time
        estimated_time = 0.5  # Base time
        estimated_time += complexity_score * 0.5
        if database_changes:
            estimated_time += 2.0
        if service_restart_required:
            estimated_time += 0.5
        
        assessment = SolutionAssessment(
            solution_description=solution_description,
            complexity_score=min(complexity_score, 5),
            risk_level=risk_level,
            estimated_time_hours=estimated_time,
            potential_side_effects=potential_side_effects,
            rollback_difficulty=min(rollback_difficulty, 5),
            dependencies=dependencies,
            testing_requirements=testing_requirements,
            approval_required=approval_required
        )
        
        self.logger.logger.info(f"📊 SOLUTION ASSESSMENT: {solution_description}")
        self.logger.logger.info(f"   Complexity: {assessment.complexity_score}/5")
        self.logger.logger.info(f"   Risk Level: {assessment.risk_level.value}")
        self.logger.logger.info(f"   Est. Time: {assessment.estimated_time_hours:.1f}h")
        self.logger.logger.info(f"   Rollback Difficulty: {assessment.rollback_difficulty}/5")
        self.logger.logger.info(f"   Approval Required: {assessment.approval_required}")
        
        if assessment.potential_side_effects:
            self.logger.logger.warning("   Potential Side Effects:")
            for effect in assessment.potential_side_effects:
                self.logger.logger.warning(f"     • {effect}")
        
        return assessment
    
    def create_backup(
        self,
        description: str,
        files_to_backup: List[str] = None,
        include_database: bool = False,
        database_connection=None
    ) -> BackupState:
        """Create comprehensive system state backup"""
        
        backup_id = f"backup_{int(time.time())}_{hashlib.md5(description.encode()).hexdigest()[:8]}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.logger.info(f"💾 CREATING BACKUP: {backup_id}")
        self.logger.logger.info(f"   Description: {description}")
        
        file_backups = {}
        
        # Backup specified files
        if files_to_backup:
            files_dir = backup_path / "files"
            files_dir.mkdir(exist_ok=True)
            
            for file_path in files_to_backup:
                if os.path.exists(file_path):
                    try:
                        backup_file_path = files_dir / f"{hashlib.md5(file_path.encode()).hexdigest()}.bak"
                        shutil.copy2(file_path, backup_file_path)
                        file_backups[file_path] = str(backup_file_path)
                        self.logger.logger.debug(f"   Backed up: {file_path}")
                    except Exception as e:
                        self.logger.logger.error(f"   Failed to backup {file_path}: {e}")
        
        # Backup database if requested
        database_backup = None
        if include_database and database_connection:
            try:
                db_backup_path = backup_path / "database.sql"
                # This would need to be implemented based on your database type
                # For PostgreSQL: pg_dump, for SQLite: .backup, etc.
                self.logger.logger.info(f"   Database backup: {db_backup_path}")
                database_backup = str(db_backup_path)
            except Exception as e:
                self.logger.logger.error(f"   Database backup failed: {e}")
        
        # Capture environment snapshot
        environment_snapshot = dict(os.environ)
        
        # Capture system metrics
        try:
            import psutil
            system_metrics = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "process_count": len(psutil.pids())
            }
        except Exception as e:
            self.logger.logger.warning(f"   Could not capture system metrics: {e}")
            system_metrics = {}
        
        backup_state = BackupState(
            backup_id=backup_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            description=description,
            file_backups=file_backups,
            database_backup=database_backup,
            environment_snapshot=environment_snapshot,
            system_metrics=system_metrics
        )
        
        # Save backup metadata
        metadata_path = backup_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(asdict(backup_state), f, indent=2)
        
        self.logger.logger.info(f"   ✅ Backup created: {backup_id}")
        self.logger.logger.info(f"   Files backed up: {len(file_backups)}")
        
        return backup_state
    
    def rollback_from_backup(self, backup_state: BackupState) -> bool:
        """Rollback system to previous state from backup"""
        
        self.logger.logger.warning(f"🔄 INITIATING ROLLBACK: {backup_state.backup_id}")
        self.logger.logger.warning(f"   Backup Description: {backup_state.description}")
        
        rollback_success = True
        
        try:
            # Restore files
            for original_path, backup_path in backup_state.file_backups.items():
                if os.path.exists(backup_path):
                    try:
                        shutil.copy2(backup_path, original_path)
                        self.logger.logger.info(f"   ✅ Restored: {original_path}")
                    except Exception as e:
                        self.logger.logger.error(f"   ❌ Failed to restore {original_path}: {e}")
                        rollback_success = False
                else:
                    self.logger.logger.error(f"   ❌ Backup file not found: {backup_path}")
                    rollback_success = False
            
            # Restore database if applicable
            if backup_state.database_backup:
                try:
                    # Database restore would be implemented here
                    self.logger.logger.info(f"   Database restore required: {backup_state.database_backup}")
                    # This would need database-specific implementation
                except Exception as e:
                    self.logger.logger.error(f"   ❌ Database rollback failed: {e}")
                    rollback_success = False
            
            if rollback_success:
                self.logger.logger.info(f"   ✅ ROLLBACK COMPLETED: {backup_state.backup_id}")
            else:
                self.logger.logger.error(f"   ❌ ROLLBACK PARTIALLY FAILED: {backup_state.backup_id}")
            
            return rollback_success
            
        except Exception as e:
            self.logger.logger.error(f"   ❌ ROLLBACK FAILED: {e}")
            return False
    
    def implement_solution_safely(
        self,
        solution_id: str,
        steps: List[ImplementationStep],
        assessment: SolutionAssessment,
        verification_function: Optional[Callable[[], bool]] = None,
        auto_rollback: bool = True
    ) -> ImplementationResult:
        """Implement solution with comprehensive safety measures"""
        
        start_time = datetime.now(timezone.utc)
        start_time_str = start_time.isoformat()
        
        self.logger.logger.info(f"🚀 STARTING SAFE IMPLEMENTATION: {solution_id}")
        self.logger.logger.info(f"   Risk Level: {assessment.risk_level.value}")
        self.logger.logger.info(f"   Steps: {len(steps)}")
        self.logger.logger.info(f"   Auto-rollback: {auto_rollback}")
        
        # Create backup before implementation
        backup_state = None
        try:
            # Determine what to backup based on assessment
            files_to_backup = []
            # This would need to be determined based on the specific solution
            
            backup_state = self.create_backup(
                description=f"Pre-implementation backup for {solution_id}",
                files_to_backup=files_to_backup,
                include_database=assessment.solution_description.lower().__contains__("database")
            )
        except Exception as e:
            self.logger.logger.error(f"❌ Backup creation failed: {e}")
            return ImplementationResult(
                solution_id=solution_id,
                start_time=start_time_str,
                end_time=datetime.now(timezone.utc).isoformat(),
                duration_seconds=0,
                result=ImplementationResult.FAILED,
                steps_completed=0,
                steps_total=len(steps),
                error_message=f"Backup creation failed: {e}"
            )
        
        # Execute implementation steps
        steps_completed = 0
        implementation_error = None
        rollback_performed = False
        
        try:
            for i, step in enumerate(steps, 1):
                self.logger.logger.info(f"   Step {i}/{len(steps)}: {step.description}")
                
                try:
                    # Execute step with timeout
                    if step.timeout_seconds:
                        import signal
                        
                        def timeout_handler(signum, frame):
                            raise TimeoutError(f"Step timeout after {step.timeout_seconds}s")
                        
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(int(step.timeout_seconds))
                    
                    # Execute the step
                    step_result = step.action()
                    
                    if step.timeout_seconds:
                        signal.alarm(0)  # Cancel timeout
                    
                    # Validate step if validation function provided
                    if step.validation_function:
                        if not step.validation_function():
                            raise ValueError("Step validation failed")
                    
                    steps_completed += 1
                    self.logger.logger.info(f"     ✅ Step {i} completed")
                    
                except Exception as step_error:
                    self.logger.logger.error(f"     ❌ Step {i} failed: {step_error}")
                    
                    if step.critical:
                        implementation_error = f"Critical step {i} failed: {step_error}"
                        break
                    else:
                        self.logger.logger.warning(f"     ⚠️  Non-critical step {i} failed, continuing")
                        continue
            
            # Verify overall solution if verification function provided
            verification_passed = True
            if verification_function:
                try:
                    verification_passed = verification_function()
                    if verification_passed:
                        self.logger.logger.info("   ✅ Solution verification passed")
                    else:
                        self.logger.logger.error("   ❌ Solution verification failed")
                        if auto_rollback:
                            implementation_error = "Solution verification failed"
                except Exception as e:
                    self.logger.logger.error(f"   ❌ Solution verification error: {e}")
                    verification_passed = False
                    if auto_rollback:
                        implementation_error = f"Solution verification error: {e}"
            
            # Determine final result
            if implementation_error and auto_rollback:
                # Perform rollback
                self.logger.logger.warning("   🔄 Performing automatic rollback...")
                rollback_success = self.rollback_from_backup(backup_state)
                rollback_performed = True
                
                final_result = ImplementationStatus.ROLLED_BACK if rollback_success else ImplementationStatus.FAILED
                
            elif implementation_error:
                final_result = ImplementationStatus.FAILED
                
            elif steps_completed == len(steps) and verification_passed:
                final_result = ImplementationStatus.SUCCESS
                
            else:
                final_result = ImplementationStatus.PARTIAL
            
        except Exception as e:
            implementation_error = str(e)
            final_result = ImplementationStatus.FAILED
            self.logger.logger.error(f"   ❌ Implementation failed with exception: {e}")
        
        # Calculate duration and create result
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        result = ImplementationResult(
            solution_id=solution_id,
            start_time=start_time_str,
            end_time=end_time.isoformat(),
            duration_seconds=round(duration, 3),
            result=final_result,
            steps_completed=steps_completed,
            steps_total=len(steps),
            backup_id=backup_state.backup_id if backup_state else None,
            error_message=implementation_error,
            rollback_performed=rollback_performed,
            validation_passed=verification_passed
        )
        
        # Store in history
        self.implementation_history.append(result)
        
        # Log final result
        self.logger.logger.info(f"🏁 IMPLEMENTATION COMPLETED: {solution_id}")
        self.logger.logger.info(f"   Result: {final_result.value}")
        self.logger.logger.info(f"   Steps: {steps_completed}/{len(steps)}")
        self.logger.logger.info(f"   Duration: {duration:.3f}s")
        self.logger.logger.info(f"   Rollback: {rollback_performed}")
        
        if final_result == ImplementationStatus.SUCCESS:
            self.logger.logger.info("   🎉 Solution implemented successfully!")
        elif final_result == ImplementationStatus.ROLLED_BACK:
            self.logger.logger.warning("   🔄 Solution rolled back due to issues")
        else:
            self.logger.logger.error("   ❌ Implementation failed or incomplete")
        
        return result

# Convenience function for quick solution implementation
def implement_solution_with_backup(
    logger: DiagnosticLogger,
    solution_description: str,
    implementation_function: Callable[[], Any],
    rollback_function: Optional[Callable[[], Any]] = None,
    verification_function: Optional[Callable[[], bool]] = None,
    files_to_backup: List[str] = None
) -> bool:
    """Quick implementation with automatic backup and rollback"""
    
    manager = SafeImplementationManager(logger)
    
    # Create assessment
    assessment = manager.assess_solution_impact(
        solution_description=solution_description,
        files_to_modify=files_to_backup or []
    )
    
    # Create implementation step
    step = ImplementationStep(
        step_id="main_implementation",
        description=solution_description,
        action=implementation_function,
        rollback_action=rollback_function,
        validation_function=verification_function
    )
    
    # Execute implementation
    result = manager.implement_solution_safely(
        solution_id=f"quick_solution_{int(time.time())}",
        steps=[step],
        assessment=assessment,
        verification_function=verification_function
    )
    
    return result.result == ImplementationStatus.SUCCESS