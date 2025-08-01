"""
🛡️ INVARIANT DETECTOR - Detects and monitors system invariants and contracts
Part of the Holistic Python Backend Diagnostic System v3.0
"""

import ast
import re
import inspect
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class Invariant:
    """Represents a system invariant or contract"""
    invariant_id: str
    invariant_type: str  # 'data_contract', 'timing_assumption', 'ordering_requirement', etc.
    description: str
    location: str  # file:line where detected
    confidence: float  # 0.0 to 1.0
    validation_code: str  # Code to validate this invariant
    violation_impact: str  # 'low', 'medium', 'high', 'critical'
    examples: List[str] = field(default_factory=list)
    related_components: Set[str] = field(default_factory=set)
    last_verified: Optional[datetime] = None
    violation_count: int = 0

@dataclass
class InvariantViolation:
    """Represents a detected invariant violation"""
    invariant_id: str
    violation_time: datetime
    violation_details: str
    context: Dict[str, Any]
    severity: str
    suggested_fix: Optional[str] = None

class InvariantDetector:
    """
    Detects implicit rules, contracts, and assumptions in the system.
    These are the hidden "rules" that the system depends on but aren't explicitly documented.
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.invariants: Dict[str, Invariant] = {}
        self.violation_history: List[InvariantViolation] = []
        
        # Patterns for detecting different types of invariants
        self.detection_patterns = {
            'data_contracts': [
                r'assert\s+.*',  # Assert statements
                r'if\s+.*:\s*raise\s+.*',  # Validation with exceptions
                r'@.*validator.*',  # Pydantic validators
                r'isinstance\s*\(',  # Type checks
                r'len\s*\(.*\)\s*[<>=!]+\s*\d+',  # Length constraints
                r'.*\.startswith\s*\(',  # String format checks
                r'.*\.endswith\s*\(',  # String format checks
                r'.*in\s+\[.*\]',  # Enum-like constraints
            ],
            'timing_assumptions': [
                r'time\.sleep\s*\(',  # Explicit timing
                r'asyncio\.sleep\s*\(',  # Async timing
                r'timeout\s*=\s*\d+',  # Timeout parameters
                r'deadline\s*=',  # Deadline assumptions
                r'retry.*\d+',  # Retry logic
                r'schedule\.every\s*\(',  # Scheduled operations
            ],
            'ordering_requirements': [
                r'before\s+.*after',  # Ordering comments
                r'first.*then',  # Sequential operations
                r'initialize.*before',  # Initialization order
                r'setup.*teardown',  # Setup/teardown pairs
                r'acquire.*release',  # Resource management
                r'begin.*commit',  # Transaction patterns
            ],
            'resource_limits': [
                r'max.*\d+',  # Maximum limits
                r'limit\s*=\s*\d+',  # Explicit limits
                r'pool.*size',  # Connection pools
                r'concurrent.*\d+',  # Concurrency limits
                r'memory.*limit',  # Memory constraints
                r'disk.*space',  # Disk constraints
            ],
            'business_rules': [
                r'if.*role.*==.*',  # Role-based logic
                r'permission.*required',  # Permission checks
                r'authorized.*only',  # Authorization rules
                r'admin.*only',  # Admin restrictions
                r'owner.*can',  # Ownership rules
                r'status.*==.*',  # Status-based logic
            ]
        }
        
        logger.info(f"🔍 InvariantDetector initialized for project: {self.project_root}")
    
    def detect_invariants(self, codebase_path: Optional[str] = None) -> Dict[str, List[Invariant]]:
        """
        Detect all implicit invariants in the codebase.
        This is crucial for understanding what assumptions the system makes.
        """
        if codebase_path is None:
            codebase_path = str(self.project_root)
        
        logger.info("🔍 Starting invariant detection...")
        start_time = datetime.now()
        
        invariants = {
            "data_contracts": [],
            "timing_assumptions": [],
            "ordering_requirements": [],
            "resource_limits": [],
            "business_rules": []
        }
        
        try:
            # Scan all Python files
            for py_file in Path(codebase_path).rglob("*.py"):
                if "__pycache__" in str(py_file) or ".git" in str(py_file):
                    continue
                
                file_invariants = self._extract_invariants_from_file(py_file)
                
                # Merge results
                for category, invs in file_invariants.items():
                    invariants[category].extend(invs)
            
            # Detect cross-file invariants
            cross_file_invariants = self._detect_cross_file_invariants(codebase_path)
            for category, invs in cross_file_invariants.items():
                invariants[category].extend(invs)
            
            # Store all invariants
            for category, invs in invariants.items():
                for inv in invs:
                    self.invariants[inv.invariant_id] = inv
            
            detection_time = (datetime.now() - start_time).total_seconds()
            total_invariants = sum(len(invs) for invs in invariants.values())
            
            logger.info(f"✅ Detected {total_invariants} invariants in {detection_time:.2f}s")
            logger.info(f"📊 Breakdown: {dict((k, len(v)) for k, v in invariants.items())}")
            
            return invariants
            
        except Exception as e:
            logger.error(f"❌ Invariant detection failed: {e}")
            raise
    
    def _extract_invariants_from_file(self, file_path: Path) -> Dict[str, List[Invariant]]:
        """Extract invariants from a single file"""
        invariants = {
            "data_contracts": [],
            "timing_assumptions": [],
            "ordering_requirements": [],
            "resource_limits": [],
            "business_rules": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Parse AST for structural analysis
            try:
                tree = ast.parse(content)
                ast_invariants = self._extract_ast_invariants(tree, file_path)
                for category, invs in ast_invariants.items():
                    invariants[category].extend(invs)
            except SyntaxError:
                logger.warning(f"⚠️ Could not parse AST for {file_path}")
            
            # Pattern-based detection
            for line_no, line in enumerate(lines, 1):
                line_invariants = self._analyze_line_for_invariants(
                    line, file_path, line_no
                )
                for category, invs in line_invariants.items():
                    invariants[category].extend(invs)
            
            # Comment-based invariants
            comment_invariants = self._extract_comment_invariants(lines, file_path)
            for category, invs in comment_invariants.items():
                invariants[category].extend(invs)
            
            # Docstring-based invariants
            docstring_invariants = self._extract_docstring_invariants(tree, file_path)
            for category, invs in docstring_invariants.items():
                invariants[category].extend(invs)
                
        except Exception as e:
            logger.warning(f"⚠️ Could not analyze {file_path}: {e}")
        
        return invariants
    
    def _extract_ast_invariants(self, tree: ast.AST, file_path: Path) -> Dict[str, List[Invariant]]:
        """Extract invariants from AST analysis"""
        invariants = {
            "data_contracts": [],
            "timing_assumptions": [],
            "ordering_requirements": [],
            "resource_limits": [],
            "business_rules": []
        }
        
        class InvariantVisitor(ast.NodeVisitor):
            def __init__(self, detector):
                self.detector = detector
                self.current_function = None
                self.current_class = None
            
            def visit_FunctionDef(self, node):
                old_function = self.current_function
                self.current_function = node.name
                
                # Check function decorators for invariants
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if decorator.id in ['validator', 'validates', 'check']:
                            inv = self._create_data_contract_invariant(
                                f"Function {node.name} has validation decorator",
                                f"{file_path}:{node.lineno}",
                                f"@{decorator.id} decorator ensures data validation"
                            )
                            invariants["data_contracts"].append(inv)
                
                # Check function parameters for type hints (contracts)
                if node.args.args:
                    for arg in node.args.args:
                        if arg.annotation:
                            inv = self._create_data_contract_invariant(
                                f"Parameter {arg.arg} has type annotation",
                                f"{file_path}:{node.lineno}",
                                f"Parameter {arg.arg} must be of type {ast.unparse(arg.annotation)}"
                            )
                            invariants["data_contracts"].append(inv)
                
                self.generic_visit(node)
                self.current_function = old_function
            
            def visit_ClassDef(self, node):
                old_class = self.current_class
                self.current_class = node.name
                
                # Check for Pydantic models or dataclasses
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        if base.id in ['BaseModel', 'BaseSettings']:
                            inv = self._create_data_contract_invariant(
                                f"Class {node.name} inherits from {base.id}",
                                f"{file_path}:{node.lineno}",
                                f"Class {node.name} has Pydantic validation"
                            )
                            invariants["data_contracts"].append(inv)
                
                self.generic_visit(node)
                self.current_class = old_class
            
            def visit_Assert(self, node):
                # Assert statements are explicit invariants
                try:
                    test_code = ast.unparse(node.test)
                    msg = ast.unparse(node.msg) if node.msg else "Assertion failed"
                    
                    inv = self._create_data_contract_invariant(
                        f"Assertion: {test_code}",
                        f"{file_path}:{node.lineno}",
                        f"assert {test_code}, {msg}"
                    )
                    invariants["data_contracts"].append(inv)
                except:
                    pass  # Skip if can't unparse
                
                self.generic_visit(node)
            
            def visit_If(self, node):
                # Look for validation patterns
                try:
                    test_code = ast.unparse(node.test)
                    
                    # Check if this looks like a validation
                    if any(keyword in test_code.lower() for keyword in 
                          ['isinstance', 'len(', 'not ', '== none', 'is none']):
                        
                        # Check if it raises an exception
                        for child in ast.walk(node):
                            if isinstance(child, ast.Raise):
                                inv = self._create_data_contract_invariant(
                                    f"Validation check: {test_code}",
                                    f"{file_path}:{node.lineno}",
                                    f"if {test_code}: raise Exception"
                                )
                                invariants["data_contracts"].append(inv)
                                break
                except:
                    pass
                
                self.generic_visit(node)
            
            def _create_data_contract_invariant(self, description, location, validation_code):
                return Invariant(
                    invariant_id=f"data_{hash(description + location)}",
                    invariant_type="data_contract",
                    description=description,
                    location=location,
                    confidence=0.8,
                    validation_code=validation_code,
                    violation_impact="medium"
                )
        
        visitor = InvariantVisitor(self)
        visitor.visit(tree)
        
        return invariants
    
    def _analyze_line_for_invariants(self, line: str, file_path: Path, line_no: int) -> Dict[str, List[Invariant]]:
        """Analyze a single line for invariant patterns"""
        invariants = {
            "data_contracts": [],
            "timing_assumptions": [],
            "ordering_requirements": [],
            "resource_limits": [],
            "business_rules": []
        }
        
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('#'):
            return invariants
        
        # Check each pattern category
        for category, patterns in self.detection_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    inv = self._create_invariant_from_pattern(
                        category, pattern, line_stripped, f"{file_path}:{line_no}"
                    )
                    invariants[category].append(inv)
        
        return invariants
    
    def _create_invariant_from_pattern(self, category: str, pattern: str, line: str, location: str) -> Invariant:
        """Create an invariant from a detected pattern"""
        confidence_map = {
            'data_contracts': 0.8,
            'timing_assumptions': 0.7,
            'ordering_requirements': 0.6,
            'resource_limits': 0.8,
            'business_rules': 0.9
        }
        
        impact_map = {
            'data_contracts': 'high',
            'timing_assumptions': 'medium',
            'ordering_requirements': 'high',
            'resource_limits': 'critical',
            'business_rules': 'critical'
        }
        
        return Invariant(
            invariant_id=f"{category}_{hash(line + location)}",
            invariant_type=category,
            description=f"Pattern detected: {pattern} in '{line[:50]}...'",
            location=location,
            confidence=confidence_map.get(category, 0.5),
            validation_code=line,
            violation_impact=impact_map.get(category, 'medium'),
            examples=[line]
        )
    
    def _extract_comment_invariants(self, lines: List[str], file_path: Path) -> Dict[str, List[Invariant]]:
        """Extract invariants mentioned in comments"""
        invariants = {
            "data_contracts": [],
            "timing_assumptions": [],
            "ordering_requirements": [],
            "resource_limits": [],
            "business_rules": []
        }
        
        comment_keywords = {
            'data_contracts': ['must be', 'should be', 'expected', 'valid', 'format', 'type'],
            'timing_assumptions': ['timeout', 'deadline', 'wait', 'delay', 'after', 'before'],
            'ordering_requirements': ['first', 'then', 'before', 'after', 'order', 'sequence'],
            'resource_limits': ['limit', 'max', 'maximum', 'pool', 'concurrent'],
            'business_rules': ['only', 'admin', 'owner', 'permission', 'role', 'authorized']
        }
        
        for line_no, line in enumerate(lines, 1):
            if '#' in line:
                comment = line[line.index('#'):].lower()
                
                for category, keywords in comment_keywords.items():
                    if any(keyword in comment for keyword in keywords):
                        inv = Invariant(
                            invariant_id=f"comment_{category}_{hash(line + str(line_no))}",
                            invariant_type=category,
                            description=f"Comment-based invariant: {comment[:100]}",
                            location=f"{file_path}:{line_no}",
                            confidence=0.5,  # Lower confidence for comment-based
                            validation_code=f"# {comment}",
                            violation_impact='medium'
                        )
                        invariants[category].append(inv)
        
        return invariants
    
    def _extract_docstring_invariants(self, tree: ast.AST, file_path: Path) -> Dict[str, List[Invariant]]:
        """Extract invariants from docstrings"""
        invariants = {
            "data_contracts": [],
            "timing_assumptions": [],
            "ordering_requirements": [],
            "resource_limits": [],
            "business_rules": []
        }
        
        class DocstringVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                if ast.get_docstring(node):
                    docstring = ast.get_docstring(node).lower()
                    
                    # Look for Args/Returns sections (data contracts)
                    if 'args:' in docstring or 'parameters:' in docstring or 'returns:' in docstring:
                        inv = Invariant(
                            invariant_id=f"docstring_data_{hash(docstring + str(node.lineno))}",
                            invariant_type="data_contract",
                            description=f"Function {node.name} has documented data contracts",
                            location=f"{file_path}:{node.lineno}",
                            confidence=0.9,
                            validation_code=f"# {node.name} docstring specifies data contracts",
                            violation_impact='medium'
                        )
                        invariants["data_contracts"].append(inv)
                    
                    # Look for Raises sections (error conditions)
                    if 'raises:' in docstring or 'throws:' in docstring:
                        inv = Invariant(
                            invariant_id=f"docstring_error_{hash(docstring + str(node.lineno))}",
                            invariant_type="data_contract",
                            description=f"Function {node.name} documents error conditions",
                            location=f"{file_path}:{node.lineno}",
                            confidence=0.8,
                            validation_code=f"# {node.name} raises documented exceptions",
                            violation_impact='high'
                        )
                        invariants["data_contracts"].append(inv)
                
                self.generic_visit(node)
        
        visitor = DocstringVisitor()
        visitor.visit(tree)
        
        return invariants
    
    def _detect_cross_file_invariants(self, codebase_path: str) -> Dict[str, List[Invariant]]:
        """Detect invariants that span multiple files"""
        invariants = {
            "data_contracts": [],
            "timing_assumptions": [],
            "ordering_requirements": [],
            "resource_limits": [],
            "business_rules": []
        }
        
        try:
            # Look for configuration patterns
            config_files = list(Path(codebase_path).rglob("*config*.py"))
            for config_file in config_files:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Database URL patterns
                    if 'database_url' in content.lower():
                        inv = Invariant(
                            invariant_id=f"cross_file_db_{hash(str(config_file))}",
                            invariant_type="resource_limits",
                            description="Database URL configuration defines connection parameters",
                            location=str(config_file),
                            confidence=0.9,
                            validation_code="DATABASE_URL must be valid connection string",
                            violation_impact='critical'
                        )
                        invariants["resource_limits"].append(inv)
                    
                    # Token/API key patterns
                    if any(keyword in content.lower() for keyword in ['token', 'api_key', 'secret']):
                        inv = Invariant(
                            invariant_id=f"cross_file_auth_{hash(str(config_file))}",
                            invariant_type="business_rules",
                            description="Authentication tokens/keys required for operation",
                            location=str(config_file),
                            confidence=0.9,
                            validation_code="Authentication credentials must be valid",
                            violation_impact='critical'
                        )
                        invariants["business_rules"].append(inv)
            
            # Look for database models (data contracts)
            model_files = []
            for py_file in Path(codebase_path).rglob("*.py"):
                if "model" in py_file.name.lower() or "database" in py_file.name.lower():
                    model_files.append(py_file)
            
            for model_file in model_files[:5]:  # Limit to avoid too many
                try:
                    with open(model_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if any(keyword in content for keyword in ['Column', 'Table', 'relationship']):
                        inv = Invariant(
                            invariant_id=f"cross_file_model_{hash(str(model_file))}",
                            invariant_type="data_contract",
                            description=f"Database model in {model_file.name} defines data schema",
                            location=str(model_file),
                            confidence=0.9,
                            validation_code="Database schema must match model definitions",
                            violation_impact='high'
                        )
                        invariants["data_contracts"].append(inv)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not analyze model file {model_file}: {e}")
        
        except Exception as e:
            logger.warning(f"⚠️ Cross-file invariant detection failed: {e}")
        
        return invariants
    
    def verify_invariant_preserved(self, invariant_id: str, before_state: Dict[str, Any], 
                                 after_state: Dict[str, Any]) -> bool:
        """
        Verify that an invariant is preserved after a change.
        This is critical for ensuring changes don't break system assumptions.
        """
        if invariant_id not in self.invariants:
            logger.warning(f"⚠️ Unknown invariant: {invariant_id}")
            return False
        
        invariant = self.invariants[invariant_id]
        
        try:
            # Use the invariant's validation code to check preservation
            validation_result = self._execute_invariant_validation(
                invariant, before_state, after_state
            )
            
            if not validation_result:
                # Record violation
                violation = InvariantViolation(
                    invariant_id=invariant_id,
                    violation_time=datetime.now(),
                    violation_details=f"Invariant {invariant.description} violated",
                    context={"before": before_state, "after": after_state},
                    severity=invariant.violation_impact
                )
                self.violation_history.append(violation)
                invariant.violation_count += 1
                
                logger.warning(f"⚠️ Invariant violation detected: {invariant.description}")
                return False
            
            # Update last verified time
            invariant.last_verified = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying invariant {invariant_id}: {e}")
            return False
    
    def _execute_invariant_validation(self, invariant: Invariant, 
                                    before_state: Dict[str, Any], 
                                    after_state: Dict[str, Any]) -> bool:
        """Execute validation logic for an invariant"""
        
        # For different types of invariants, we need different validation strategies
        if invariant.invariant_type == "data_contract":
            return self._validate_data_contract(invariant, before_state, after_state)
        elif invariant.invariant_type == "timing_assumption":
            return self._validate_timing_assumption(invariant, before_state, after_state)
        elif invariant.invariant_type == "ordering_requirement":
            return self._validate_ordering_requirement(invariant, before_state, after_state)
        elif invariant.invariant_type == "resource_limits":
            return self._validate_resource_limits(invariant, before_state, after_state)
        elif invariant.invariant_type == "business_rules":
            return self._validate_business_rules(invariant, before_state, after_state)
        
        return True  # Default to assuming preservation if we can't validate
    
    def _validate_data_contract(self, invariant: Invariant, 
                              before_state: Dict[str, Any], 
                              after_state: Dict[str, Any]) -> bool:
        """Validate data contract invariants"""
        # Check if data types and structures are preserved
        if 'data_types' in before_state and 'data_types' in after_state:
            return before_state['data_types'] == after_state['data_types']
        
        # Check if validation logic is still present
        if 'validation_present' in before_state and 'validation_present' in after_state:
            return after_state['validation_present'] >= before_state['validation_present']
        
        return True
    
    def _validate_timing_assumption(self, invariant: Invariant, 
                                  before_state: Dict[str, Any], 
                                  after_state: Dict[str, Any]) -> bool:
        """Validate timing assumption invariants"""
        # Check if timing constraints are preserved
        if 'max_execution_time' in before_state and 'max_execution_time' in after_state:
            return after_state['max_execution_time'] <= before_state['max_execution_time'] * 1.1
        
        if 'timeout_values' in before_state and 'timeout_values' in after_state:
            return after_state['timeout_values'] == before_state['timeout_values']
        
        return True
    
    def _validate_ordering_requirement(self, invariant: Invariant, 
                                     before_state: Dict[str, Any], 
                                     after_state: Dict[str, Any]) -> bool:
        """Validate ordering requirement invariants"""
        # Check if execution order is preserved
        if 'execution_order' in before_state and 'execution_order' in after_state:
            return after_state['execution_order'] == before_state['execution_order']
        
        return True
    
    def _validate_resource_limits(self, invariant: Invariant, 
                                before_state: Dict[str, Any], 
                                after_state: Dict[str, Any]) -> bool:
        """Validate resource limit invariants"""
        # Check if resource limits are not exceeded
        resource_metrics = ['memory_usage', 'cpu_usage', 'connection_count', 'file_handles']
        
        for metric in resource_metrics:
            if metric in before_state and metric in after_state:
                if after_state[metric] > before_state[metric] * 1.2:  # 20% tolerance
                    return False
        
        return True
    
    def _validate_business_rules(self, invariant: Invariant, 
                               before_state: Dict[str, Any], 
                               after_state: Dict[str, Any]) -> bool:
        """Validate business rule invariants"""
        # Check if business logic constraints are preserved
        if 'access_control' in before_state and 'access_control' in after_state:
            # Business rules should not become more permissive
            before_perms = set(before_state['access_control'])
            after_perms = set(after_state['access_control'])
            return before_perms.issubset(after_perms)
        
        return True
    
    def get_violation_report(self) -> Dict[str, Any]:
        """Generate a comprehensive violation report"""
        if not self.violation_history:
            return {"status": "no_violations", "total_violations": 0}
        
        violations_by_type = {}
        violations_by_severity = {}
        recent_violations = []
        
        for violation in self.violation_history:
            # Group by invariant type
            invariant = self.invariants.get(violation.invariant_id)
            if invariant:
                inv_type = invariant.invariant_type
                if inv_type not in violations_by_type:
                    violations_by_type[inv_type] = 0
                violations_by_type[inv_type] += 1
            
            # Group by severity
            if violation.severity not in violations_by_severity:
                violations_by_severity[violation.severity] = 0
            violations_by_severity[violation.severity] += 1
            
            # Recent violations (last 24 hours)
            if (datetime.now() - violation.violation_time).days < 1:
                recent_violations.append({
                    "invariant_id": violation.invariant_id,
                    "time": violation.violation_time.isoformat(),
                    "details": violation.violation_details,
                    "severity": violation.severity
                })
        
        return {
            "status": "violations_detected",
            "total_violations": len(self.violation_history),
            "violations_by_type": violations_by_type,
            "violations_by_severity": violations_by_severity,
            "recent_violations": recent_violations,
            "most_violated_invariants": self._get_most_violated_invariants(),
            "recommendations": self._generate_violation_recommendations()
        }
    
    def _get_most_violated_invariants(self) -> List[Dict[str, Any]]:
        """Get the invariants that are violated most frequently"""
        violations = sorted(
            [(inv_id, inv.violation_count) for inv_id, inv in self.invariants.items()
             if inv.violation_count > 0],
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                "invariant_id": inv_id,
                "description": self.invariants[inv_id].description,
                "violation_count": count,
                "impact": self.invariants[inv_id].violation_impact
            }
            for inv_id, count in violations[:10]  # Top 10
        ]
    
    def _generate_violation_recommendations(self) -> List[str]:
        """Generate recommendations based on violation patterns"""
        recommendations = []
        
        # Check for patterns in violations
        violation_types = [v.severity for v in self.violation_history]
        
        if violation_types.count('critical') > 0:
            recommendations.append("URGENT: Critical invariants are being violated. Immediate attention required.")
        
        if violation_types.count('high') > 3:
            recommendations.append("Multiple high-impact invariants violated. Review recent changes.")
        
        if len(self.violation_history) > 10:
            recommendations.append("High volume of violations detected. Consider system audit.")
        
        # Check for repeated violations of same invariant
        repeated_violations = {}
        for violation in self.violation_history:
            if violation.invariant_id not in repeated_violations:
                repeated_violations[violation.invariant_id] = 0
            repeated_violations[violation.invariant_id] += 1
        
        for inv_id, count in repeated_violations.items():
            if count > 3:
                recommendations.append(f"Invariant {inv_id} repeatedly violated ({count} times). May need refactoring.")
        
        if not recommendations:
            recommendations.append("Monitor trends and investigate root causes of violations.")
        
        return recommendations
    
    def export_invariants(self, output_path: str) -> None:
        """Export all detected invariants to a JSON file"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_invariants": len(self.invariants),
            "invariants": {}
        }
        
        for inv_id, invariant in self.invariants.items():
            export_data["invariants"][inv_id] = {
                "id": invariant.invariant_id,
                "type": invariant.invariant_type,
                "description": invariant.description,
                "location": invariant.location,
                "confidence": invariant.confidence,
                "validation_code": invariant.validation_code,
                "violation_impact": invariant.violation_impact,
                "examples": invariant.examples,
                "related_components": list(invariant.related_components),
                "last_verified": invariant.last_verified.isoformat() if invariant.last_verified else None,
                "violation_count": invariant.violation_count
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Exported {len(self.invariants)} invariants to {output_path}")