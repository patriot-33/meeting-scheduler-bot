"""
🛡️ CHANGE DOCUMENTATION SYSTEM - Comprehensive change tracking and learning
Part of the Holistic Python Backend Diagnostic System v3.0
"""

import json
import hashlib
import git
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import shutil
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class ChangeRecord:
    """Comprehensive record of a single change"""
    change_id: str
    timestamp: datetime
    change_type: str  # "code", "config", "dependency", "database", "environment"
    description: str
    
    # What changed
    files_modified: List[str] = field(default_factory=list)
    files_added: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    diff_content: Dict[str, str] = field(default_factory=dict)
    lines_added: int = 0
    lines_removed: int = 0
    
    # Context
    reason: str = ""
    hypothesis_id: Optional[str] = None
    parent_change_id: Optional[str] = None
    related_issue: Optional[str] = None
    author: str = "system"
    
    # Impact analysis
    affected_components: Set[str] = field(default_factory=set)
    dependency_changes: Dict[str, Any] = field(default_factory=dict)
    api_contract_changes: List[str] = field(default_factory=list)
    breaking_changes: bool = False
    
    # Metrics
    metrics_before: Dict[str, Any] = field(default_factory=dict)
    metrics_after: Dict[str, Any] = field(default_factory=dict)
    performance_impact: Dict[str, float] = field(default_factory=dict)
    
    # Testing and validation
    tests_run: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    new_tests_added: List[str] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    # Risk and issues
    risks_identified: List[str] = field(default_factory=list)
    issues_encountered: List[str] = field(default_factory=list)
    mitigations_applied: List[str] = field(default_factory=list)
    
    # Rollback information
    rollback_plan: Optional[str] = None
    can_be_reverted: bool = True
    revert_command: Optional[str] = None
    rollback_tested: bool = False
    
    # Success metrics
    change_successful: bool = False
    verification_passed: bool = False
    rollback_required: bool = False
    lessons_learned: List[str] = field(default_factory=list)

@dataclass
class DiagnosticSession:
    """Complete record of a diagnostic and repair session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Problem context
    initial_problem: Dict[str, Any] = field(default_factory=dict)
    problem_severity: str = "unknown"
    user_reported: bool = False
    
    # Diagnostic process
    diagnostic_steps: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses_tested: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    
    # Changes applied
    changes_applied: List[str] = field(default_factory=list)  # Change IDs
    rollbacks_performed: List[str] = field(default_factory=list)
    
    # Environment state
    environment_before: Dict[str, Any] = field(default_factory=dict)
    environment_after: Dict[str, Any] = field(default_factory=dict)
    
    # Outcomes
    final_status: str = "unknown"  # "success", "partial", "failed", "rolled_back"
    resolution_time_minutes: Optional[float] = None
    user_satisfaction: Optional[int] = None  # 1-5 scale
    
    # Learning
    what_worked: List[str] = field(default_factory=list)
    what_didnt_work: List[str] = field(default_factory=list)
    unexpected_findings: List[str] = field(default_factory=list)
    future_preventions: List[str] = field(default_factory=list)

@dataclass
class PatternLearning:
    """Learned patterns from past diagnostic sessions"""
    pattern_id: str
    pattern_type: str  # "bug_pattern", "fix_pattern", "risk_pattern"
    description: str
    
    # Pattern characteristics
    symptoms: List[str] = field(default_factory=list)
    root_causes: List[str] = field(default_factory=list)
    contributing_factors: List[str] = field(default_factory=list)
    
    # Solution patterns
    effective_solutions: List[str] = field(default_factory=list)
    ineffective_solutions: List[str] = field(default_factory=list)
    
    # Context
    environments_seen: Set[str] = field(default_factory=set)
    components_affected: Set[str] = field(default_factory=set)
    frequency: int = 1
    confidence: float = 0.5  # 0.0 to 1.0
    
    # Prevention
    prevention_measures: List[str] = field(default_factory=list)
    early_warning_signs: List[str] = field(default_factory=list)

class ChangeDocumentationSystem:
    """
    Comprehensive system for documenting, tracking, and learning from all changes.
    This creates an institutional memory of what works and what doesn't.
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.documentation_path = self.project_root / ".diagnostic_history"
        self.documentation_path.mkdir(exist_ok=True)
        
        # Database for structured storage
        self.db_path = self.documentation_path / "diagnostic_history.db"
        self._init_database()
        
        # Current session tracking
        self.current_session_id: Optional[str] = None
        self.current_session: Optional[DiagnosticSession] = None
        
        # Git integration
        try:
            self.git_repo = git.Repo(self.project_root)
            self.git_available = True
            logger.info("✅ Git integration enabled for change tracking")
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            self.git_repo = None
            self.git_available = False
            logger.info("ℹ️ No Git repository - using file-based change tracking")
        
        # Pattern learning
        self.learned_patterns: Dict[str, PatternLearning] = {}
        self._load_learned_patterns()
        
        logger.info(f"📚 ChangeDocumentationSystem initialized for project: {self.project_root}")
    
    def _init_database(self):
        """Initialize SQLite database for change tracking"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS diagnostic_sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    initial_problem TEXT,
                    problem_severity TEXT,
                    final_status TEXT,
                    resolution_time_minutes REAL,
                    environment_before TEXT,
                    environment_after TEXT,
                    lessons_learned TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS change_records (
                    change_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    description TEXT,
                    files_modified TEXT,
                    files_added TEXT,
                    files_deleted TEXT,
                    lines_added INTEGER DEFAULT 0,
                    lines_removed INTEGER DEFAULT 0,
                    reason TEXT,
                    affected_components TEXT,
                    change_successful BOOLEAN DEFAULT FALSE,
                    verification_passed BOOLEAN DEFAULT FALSE,
                    rollback_required BOOLEAN DEFAULT FALSE,
                    performance_impact TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(session_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    description TEXT,
                    symptoms TEXT,
                    root_causes TEXT,
                    effective_solutions TEXT,
                    prevention_measures TEXT,
                    frequency INTEGER DEFAULT 1,
                    confidence REAL DEFAULT 0.5,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_status ON diagnostic_sessions(final_status)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_changes_type ON change_records(change_type)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_changes_success ON change_records(change_successful)
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column name access
        try:
            yield conn
        finally:
            conn.close()
    
    def start_diagnostic_session(self, problem_description: str, severity: str = "unknown") -> str:
        """Start a new diagnostic session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(problem_description.encode()).hexdigest()[:8]}"
        
        self.current_session_id = session_id
        self.current_session = DiagnosticSession(
            session_id=session_id,
            start_time=datetime.now(),
            initial_problem={
                "description": problem_description,
                "severity": severity,
                "reported_at": datetime.now().isoformat(),
                "environment": self._capture_environment_state()
            },
            problem_severity=severity
        )
        
        # Store in database
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO diagnostic_sessions 
                (session_id, start_time, initial_problem, problem_severity, environment_before)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session_id,
                self.current_session.start_time.isoformat(),
                json.dumps(self.current_session.initial_problem),
                severity,
                json.dumps(self.current_session.environment_before)
            ))
            conn.commit()
        
        logger.info(f"📚 Started diagnostic session: {session_id}")
        return session_id
    
    def record_diagnostic_step(self, action: str, target: str, findings: List[str], 
                              confidence: float = 0.5, tools_used: List[str] = None):
        """Record a diagnostic step"""
        if not self.current_session:
            logger.warning("⚠️ No active diagnostic session")
            return
        
        step = {
            "timestamp": datetime.now().isoformat(),
            "step_number": len(self.current_session.diagnostic_steps) + 1,
            "action": action,
            "target": target,
            "findings": findings,
            "confidence": confidence,
            "tools_used": tools_used or []
        }
        
        self.current_session.diagnostic_steps.append(step)
        logger.info(f"📝 Recorded diagnostic step: {action} on {target}")
    
    def record_hypothesis_test(self, hypothesis: str, test_method: str, 
                              result: bool, evidence: Dict[str, Any]):
        """Record a hypothesis test"""
        if not self.current_session:
            logger.warning("⚠️ No active diagnostic session")
            return
        
        hypothesis_test = {
            "timestamp": datetime.now().isoformat(),
            "hypothesis": hypothesis,
            "test_method": test_method,
            "result": result,
            "evidence": evidence,
            "confidence": evidence.get("confidence", 0.5)
        }
        
        self.current_session.hypotheses_tested.append(hypothesis_test)
        logger.info(f"🧪 Recorded hypothesis test: {hypothesis} -> {result}")
    
    def record_change(self, change_data: Dict[str, Any]) -> str:
        """Record a comprehensive change with all metadata"""
        change_id = self._generate_change_id(change_data)
        
        # Create change record
        change_record = ChangeRecord(
            change_id=change_id,
            timestamp=datetime.now(),
            change_type=change_data.get("type", "unknown"),
            description=change_data.get("description", ""),
            files_modified=change_data.get("files_modified", []),
            files_added=change_data.get("files_added", []),
            files_deleted=change_data.get("files_deleted", []),
            reason=change_data.get("reason", ""),
            hypothesis_id=change_data.get("hypothesis_id"),
            parent_change_id=change_data.get("parent_change_id"),
            author=change_data.get("author", "system"),
            metrics_before=change_data.get("metrics_before", {}),
            metrics_after=change_data.get("metrics_after", {}),
            tests_run=change_data.get("tests_run", []),
            test_results=change_data.get("test_results", {}),
            risks_identified=change_data.get("risks", []),
            issues_encountered=change_data.get("issues", []),
            mitigations_applied=change_data.get("mitigations", [])
        )
        
        # Capture diff information
        if self.git_available:
            change_record.diff_content = self._capture_git_diff(change_record.files_modified)
        else:
            change_record.diff_content = self._capture_file_diff(change_record.files_modified, change_data)
        
        # Analyze impact
        change_record.affected_components = self._analyze_affected_components(change_record)
        change_record.dependency_changes = self._analyze_dependency_changes(change_record)
        change_record.api_contract_changes = self._analyze_api_changes(change_record)
        change_record.performance_impact = self._calculate_performance_impact(change_record)
        
        # Generate rollback information
        change_record.rollback_plan = self._generate_rollback_plan(change_record)
        change_record.revert_command = self._generate_revert_command(change_record)
        
        # Store in database
        self._store_change_record(change_record)
        
        # Add to current session if active
        if self.current_session:
            self.current_session.changes_applied.append(change_id)
        
        logger.info(f"📝 Recorded change: {change_id}")
        return change_id
    
    def _generate_change_id(self, change_data: Dict[str, Any]) -> str:
        """Generate a unique change ID"""
        timestamp = datetime.now().isoformat()
        content = f"{timestamp}_{change_data.get('description', '')}_{change_data.get('type', '')}"
        return f"change_{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _capture_environment_state(self) -> Dict[str, Any]:
        """Capture current environment state"""
        try:
            import psutil
            import sys
            
            state = {
                "timestamp": datetime.now().isoformat(),
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_total_gb": psutil.disk_usage(str(self.project_root)).total / (1024**3),
                "working_directory": str(self.project_root)
            }
            
            # Git information
            if self.git_available:
                try:
                    state["git_branch"] = self.git_repo.active_branch.name
                    state["git_commit"] = self.git_repo.head.commit.hexsha
                    state["git_dirty"] = self.git_repo.is_dirty()
                except Exception as e:
                    state["git_error"] = str(e)
            
            # Python dependencies
            try:
                requirements_file = self.project_root / "requirements.txt"
                if requirements_file.exists():
                    with open(requirements_file, 'r') as f:
                        state["requirements"] = f.read()
            except Exception:
                pass
            
            return state
            
        except Exception as e:
            logger.warning(f"⚠️ Could not capture full environment state: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _capture_git_diff(self, modified_files: List[str]) -> Dict[str, str]:
        """Capture git diff for modified files"""
        diffs = {}
        
        if not self.git_available:
            return diffs
        
        try:
            for file_path in modified_files:
                try:
                    # Get diff for this file
                    diff = self.git_repo.git.diff(file_path)
                    if diff:
                        diffs[file_path] = diff
                except Exception as e:
                    diffs[file_path] = f"Error capturing diff: {str(e)}"
            
            return diffs
            
        except Exception as e:
            logger.warning(f"⚠️ Could not capture git diff: {e}")
            return {}
    
    def _capture_file_diff(self, modified_files: List[str], change_data: Dict[str, Any]) -> Dict[str, str]:
        """Capture file diff without git"""
        diffs = {}
        
        # If change_data contains before/after content, use that
        if "file_changes" in change_data:
            for file_path, file_change in change_data["file_changes"].items():
                if "before" in file_change and "after" in file_change:
                    # Simple diff representation
                    diffs[file_path] = f"Before:\n{file_change['before']}\n\nAfter:\n{file_change['after']}"
        
        return diffs
    
    def _analyze_affected_components(self, change_record: ChangeRecord) -> Set[str]:
        """Analyze which components are affected by this change"""
        components = set()
        
        for file_path in change_record.files_modified + change_record.files_added:
            # Extract component name from file path
            path_parts = Path(file_path).parts
            
            if len(path_parts) > 1:
                # Use directory structure to identify components
                if "src" in path_parts:
                    src_index = path_parts.index("src")
                    if src_index + 1 < len(path_parts):
                        components.add(path_parts[src_index + 1])
                elif len(path_parts) > 0:
                    components.add(path_parts[0])
        
        return components
    
    def _analyze_dependency_changes(self, change_record: ChangeRecord) -> Dict[str, Any]:
        """Analyze changes to dependencies"""
        dependency_changes = {}
        
        # Check if requirements files were modified
        requirement_files = ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"]
        
        for file_path in change_record.files_modified:
            if any(req_file in file_path for req_file in requirement_files):
                dependency_changes[file_path] = {
                    "type": "dependency_file_modified",
                    "impact": "high",
                    "requires_reinstall": True
                }
        
        return dependency_changes
    
    def _analyze_api_changes(self, change_record: ChangeRecord) -> List[str]:
        """Analyze API contract changes"""
        api_changes = []
        
        # Look for function signature changes, class modifications, etc.
        # This is a simplified implementation
        for file_path in change_record.files_modified:
            if file_path.endswith('.py'):
                diff_content = change_record.diff_content.get(file_path, "")
                
                # Check for function definition changes
                if "def " in diff_content and ("-def " in diff_content or "+def " in diff_content):
                    api_changes.append(f"Function signature change in {file_path}")
                
                # Check for class changes
                if "class " in diff_content and ("-class " in diff_content or "+class " in diff_content):
                    api_changes.append(f"Class definition change in {file_path}")
        
        return api_changes
    
    def _calculate_performance_impact(self, change_record: ChangeRecord) -> Dict[str, float]:
        """Calculate performance impact of the change"""
        impact = {}
        
        # Compare before and after metrics
        before_metrics = change_record.metrics_before
        after_metrics = change_record.metrics_after
        
        performance_metrics = ["cpu_percent", "memory_percent", "response_time_ms", "throughput"]
        
        for metric in performance_metrics:
            if metric in before_metrics and metric in after_metrics:
                before_value = before_metrics[metric]
                after_value = after_metrics[metric]
                
                if before_value != 0:
                    change_percent = ((after_value - before_value) / before_value) * 100
                    impact[f"{metric}_change_percent"] = change_percent
        
        return impact
    
    def _generate_rollback_plan(self, change_record: ChangeRecord) -> str:
        """Generate a rollback plan for this change"""
        steps = []
        
        if self.git_available:
            steps.append("1. Use git to revert changes:")
            if change_record.files_modified:
                for file_path in change_record.files_modified:
                    steps.append(f"   git checkout HEAD~1 -- {file_path}")
            steps.append("2. Verify system functionality")
            steps.append("3. Run tests to confirm rollback success")
        else:
            steps.append("1. Restore files from backup:")
            for file_path in change_record.files_modified:
                steps.append(f"   Restore {file_path} from backup")
            steps.append("2. Verify system functionality")
        
        if change_record.dependency_changes:
            steps.append("4. Reinstall previous dependencies if needed")
        
        return "\n".join(steps)
    
    def _generate_revert_command(self, change_record: ChangeRecord) -> str:
        """Generate a command to revert this change"""
        if self.git_available:
            if len(change_record.files_modified) == 1:
                return f"git checkout HEAD~1 -- {change_record.files_modified[0]}"
            else:
                return f"git revert <commit_hash_of_this_change>"
        else:
            return "# Restore files from backup directory"
    
    def _store_change_record(self, change_record: ChangeRecord):
        """Store change record in database"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO change_records (
                    change_id, session_id, timestamp, change_type, description,
                    files_modified, files_added, files_deleted,
                    lines_added, lines_removed, reason, affected_components,
                    change_successful, verification_passed, rollback_required,
                    performance_impact
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                change_record.change_id,
                self.current_session_id,
                change_record.timestamp.isoformat(),
                change_record.change_type,
                change_record.description,
                json.dumps(change_record.files_modified),
                json.dumps(change_record.files_added),
                json.dumps(change_record.files_deleted),
                change_record.lines_added,
                change_record.lines_removed,
                change_record.reason,
                json.dumps(list(change_record.affected_components)),
                change_record.change_successful,
                change_record.verification_passed,
                change_record.rollback_required,
                json.dumps(change_record.performance_impact)
            ))
            conn.commit()
    
    def end_diagnostic_session(self, final_status: str, lessons_learned: List[str] = None):
        """End the current diagnostic session"""
        if not self.current_session:
            logger.warning("⚠️ No active diagnostic session to end")
            return
        
        self.current_session.end_time = datetime.now()
        self.current_session.final_status = final_status
        self.current_session.resolution_time_minutes = (
            self.current_session.end_time - self.current_session.start_time
        ).total_seconds() / 60
        
        if lessons_learned:
            self.current_session.what_worked.extend(lessons_learned)
        
        # Capture final environment state
        self.current_session.environment_after = self._capture_environment_state()
        
        # Update database
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE diagnostic_sessions
                SET end_time = ?, final_status = ?, resolution_time_minutes = ?,
                    environment_after = ?, lessons_learned = ?
                WHERE session_id = ?
            ''', (
                self.current_session.end_time.isoformat(),
                final_status,
                self.current_session.resolution_time_minutes,
                json.dumps(self.current_session.environment_after),
                json.dumps(self.current_session.what_worked),
                self.current_session_id
            ))
            conn.commit()
        
        # Learn from this session
        self._learn_from_session(self.current_session)
        
        logger.info(f"📚 Ended diagnostic session: {self.current_session_id} ({final_status})")
        
        # Reset current session
        self.current_session = None
        self.current_session_id = None
    
    def _learn_from_session(self, session: DiagnosticSession):
        """Extract learnings from a completed session"""
        if session.final_status == "success" and session.changes_applied:
            # This was a successful resolution - learn the pattern
            self._extract_success_pattern(session)
        elif session.final_status == "failed":
            # This failed - learn what doesn't work
            self._extract_failure_pattern(session)
        
        # Look for recurring issues
        self._identify_recurring_patterns(session)
    
    def _extract_success_pattern(self, session: DiagnosticSession):
        """Extract a success pattern from a successful session"""
        if not session.initial_problem.get("description"):
            return
        
        # Create a success pattern
        pattern_id = f"success_{hashlib.md5(session.initial_problem['description'].encode()).hexdigest()[:8]}"
        
        symptoms = []
        for step in session.diagnostic_steps:
            if step.get("findings"):
                symptoms.extend(step["findings"])
        
        solutions = []
        for change_id in session.changes_applied:
            # Get change details from database
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT description, change_type FROM change_records WHERE change_id = ?', (change_id,))
                row = cursor.fetchone()
                if row:
                    solutions.append(f"{row['change_type']}: {row['description']}")
        
        pattern = PatternLearning(
            pattern_id=pattern_id,
            pattern_type="fix_pattern",
            description=f"Successful resolution for: {session.initial_problem['description'][:100]}",
            symptoms=symptoms[:10],  # Limit to top 10
            effective_solutions=solutions,
            frequency=1,
            confidence=0.8
        )
        
        # Check if we already have a similar pattern
        existing_pattern = self._find_similar_pattern(pattern)
        if existing_pattern:
            # Update existing pattern
            existing_pattern.frequency += 1
            existing_pattern.confidence = min(0.95, existing_pattern.confidence + 0.1)
            existing_pattern.effective_solutions.extend(solutions)
            # Remove duplicates
            existing_pattern.effective_solutions = list(set(existing_pattern.effective_solutions))
        else:
            # Store new pattern
            self.learned_patterns[pattern_id] = pattern
            self._store_pattern(pattern)
        
        logger.info(f"📖 Extracted success pattern: {pattern_id}")
    
    def _extract_failure_pattern(self, session: DiagnosticSession):
        """Extract patterns from failed sessions"""
        # Similar to success pattern but focus on what didn't work
        if not session.initial_problem.get("description"):
            return
        
        pattern_id = f"failure_{hashlib.md5(session.initial_problem['description'].encode()).hexdigest()[:8]}"
        
        failed_approaches = []
        for hypothesis in session.hypotheses_tested:
            if not hypothesis.get("result", True):  # Failed hypothesis
                failed_approaches.append(hypothesis.get("hypothesis", ""))
        
        if failed_approaches:
            pattern = PatternLearning(
                pattern_id=pattern_id,
                pattern_type="risk_pattern",
                description=f"Failed approaches for: {session.initial_problem['description'][:100]}",
                ineffective_solutions=failed_approaches,
                frequency=1,
                confidence=0.7
            )
            
            self.learned_patterns[pattern_id] = pattern
            self._store_pattern(pattern)
            
            logger.info(f"📖 Extracted failure pattern: {pattern_id}")
    
    def _find_similar_pattern(self, new_pattern: PatternLearning) -> Optional[PatternLearning]:
        """Find similar existing patterns"""
        for existing_pattern in self.learned_patterns.values():
            if existing_pattern.pattern_type != new_pattern.pattern_type:
                continue
            
            # Simple similarity check based on description
            if self._calculate_text_similarity(existing_pattern.description, new_pattern.description) > 0.7:
                return existing_pattern
        
        return None
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _identify_recurring_patterns(self, session: DiagnosticSession):
        """Identify recurring issues across sessions"""
        # Get recent sessions from database
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT initial_problem, final_status FROM diagnostic_sessions
                WHERE start_time > datetime('now', '-30 days')
                ORDER BY start_time DESC
                LIMIT 20
            ''')
            recent_sessions = cursor.fetchall()
        
        # Look for patterns in problem descriptions
        current_problem = session.initial_problem.get("description", "").lower()
        similar_problems = []
        
        for row in recent_sessions:
            if row['initial_problem']:
                try:
                    problem_data = json.loads(row['initial_problem'])
                    other_problem = problem_data.get("description", "").lower()
                    
                    if self._calculate_text_similarity(current_problem, other_problem) > 0.6:
                        similar_problems.append({
                            "description": other_problem,
                            "status": row['final_status']
                        })
                except json.JSONDecodeError:
                    continue
        
        if len(similar_problems) >= 2:
            # This is a recurring pattern
            logger.warning(f"🔄 Recurring pattern detected: {len(similar_problems)} similar issues in last 30 days")
    
    def _store_pattern(self, pattern: PatternLearning):
        """Store learned pattern in database"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO learned_patterns (
                    pattern_id, pattern_type, description, symptoms,
                    root_causes, effective_solutions, prevention_measures,
                    frequency, confidence, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id,
                pattern.pattern_type,
                pattern.description,
                json.dumps(pattern.symptoms),
                json.dumps(pattern.root_causes),
                json.dumps(pattern.effective_solutions),
                json.dumps(pattern.prevention_measures),
                pattern.frequency,
                pattern.confidence,
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def _load_learned_patterns(self):
        """Load learned patterns from database"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learned_patterns')
                rows = cursor.fetchall()
                
                for row in rows:
                    pattern = PatternLearning(
                        pattern_id=row['pattern_id'],
                        pattern_type=row['pattern_type'],
                        description=row['description'],
                        symptoms=json.loads(row['symptoms']) if row['symptoms'] else [],
                        root_causes=json.loads(row['root_causes']) if row['root_causes'] else [],
                        effective_solutions=json.loads(row['effective_solutions']) if row['effective_solutions'] else [],
                        prevention_measures=json.loads(row['prevention_measures']) if row['prevention_measures'] else [],
                        frequency=row['frequency'],
                        confidence=row['confidence']
                    )
                    self.learned_patterns[pattern.pattern_id] = pattern
                
                logger.info(f"📖 Loaded {len(self.learned_patterns)} learned patterns")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load learned patterns: {e}")
    
    def suggest_solutions(self, problem_description: str) -> List[Dict[str, Any]]:
        """Suggest solutions based on learned patterns"""
        suggestions = []
        
        for pattern in self.learned_patterns.values():
            if pattern.pattern_type != "fix_pattern":
                continue
            
            # Check similarity to problem description
            similarity = self._calculate_text_similarity(pattern.description, problem_description)
            
            if similarity > 0.3:  # Minimum similarity threshold
                suggestions.append({
                    "pattern_id": pattern.pattern_id,
                    "description": pattern.description,
                    "similarity": similarity,
                    "confidence": pattern.confidence,
                    "frequency": pattern.frequency,
                    "suggested_solutions": pattern.effective_solutions,
                    "prevention_measures": pattern.prevention_measures
                })
        
        # Sort by relevance (similarity * confidence * frequency)
        suggestions.sort(
            key=lambda x: x["similarity"] * x["confidence"] * min(x["frequency"] / 10, 1.0),
            reverse=True
        )
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics about diagnostic sessions"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Overall statistics
            cursor.execute('SELECT COUNT(*) as total FROM diagnostic_sessions')
            total_sessions = cursor.fetchone()['total']
            
            cursor.execute('SELECT final_status, COUNT(*) as count FROM diagnostic_sessions GROUP BY final_status')
            status_counts = {row['final_status']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('SELECT AVG(resolution_time_minutes) as avg_time FROM diagnostic_sessions WHERE resolution_time_minutes IS NOT NULL')
            avg_resolution_time = cursor.fetchone()['avg_time'] or 0
            
            # Recent activity (last 30 days)
            cursor.execute('''
                SELECT COUNT(*) as recent_sessions 
                FROM diagnostic_sessions 
                WHERE start_time > datetime('now', '-30 days')
            ''')
            recent_sessions = cursor.fetchone()['recent_sessions']
            
            # Most common change types
            cursor.execute('''
                SELECT change_type, COUNT(*) as count 
                FROM change_records 
                GROUP BY change_type 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            common_change_types = [(row['change_type'], row['count']) for row in cursor.fetchall()]
            
            return {
                "total_sessions": total_sessions,
                "status_distribution": status_counts,
                "average_resolution_time_minutes": round(avg_resolution_time, 2),
                "recent_sessions_30d": recent_sessions,
                "success_rate": (status_counts.get("success", 0) / max(total_sessions, 1)) * 100,
                "common_change_types": common_change_types,
                "learned_patterns_count": len(self.learned_patterns),
                "total_changes_recorded": self._get_total_changes_count()
            }
    
    def _get_total_changes_count(self) -> int:
        """Get total number of changes recorded"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM change_records')
                return cursor.fetchone()['count']
        except Exception:
            return 0
    
    def export_session_data(self, session_id: str, format: str = "json") -> str:
        """Export complete session data"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get session data
            cursor.execute('SELECT * FROM diagnostic_sessions WHERE session_id = ?', (session_id,))
            session_row = cursor.fetchone()
            
            if not session_row:
                raise ValueError(f"Session {session_id} not found")
            
            # Get associated changes
            cursor.execute('SELECT * FROM change_records WHERE session_id = ?', (session_id,))
            change_rows = cursor.fetchall()
            
            session_data = dict(session_row)
            session_data['changes'] = [dict(row) for row in change_rows]
            
            if format == "json":
                export_file = self.documentation_path / f"{session_id}_export.json"
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, default=str)
                return str(export_file)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")