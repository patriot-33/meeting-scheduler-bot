"""
🛡️ SYSTEM ANALYZER - Core component of the Holistic Python Backend Diagnostic System v3.0
Analyzes complete system architecture, dependencies, and critical paths.
"""

import ast
import os
import sys
import inspect
import importlib.util
import networkx as nx
from pathlib import Path
from typing import Dict, Set, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

@dataclass
class SystemComponent:
    """Represents a system component with its metadata"""
    name: str
    path: Path
    component_type: str  # 'module', 'class', 'function', 'service'
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    complexity_score: float = 0.0
    risk_level: str = "low"  # low, medium, high, critical
    last_modified: datetime = field(default_factory=datetime.now)
    lines_of_code: int = 0
    test_coverage: float = 0.0

@dataclass
class CriticalPath:
    """Represents a critical execution path in the system"""
    path_id: str
    components: List[str]
    entry_points: List[str]
    exit_points: List[str]
    risk_score: float
    failure_impact: str  # "low", "medium", "high", "catastrophic"
    recovery_time: int  # seconds

class SystemAnalyzer:
    """
    Complete system analysis engine that maps architecture, dependencies, and critical paths.
    This class provides the foundation for safe diagnostic and repair operations.
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependency_graph = nx.DiGraph()
        self.call_graph = nx.DiGraph()
        self.data_flow_graph = nx.DiGraph()
        self.components: Dict[str, SystemComponent] = {}
        self.critical_paths: List[CriticalPath] = []
        self.system_snapshot = {}
        
        # Initialize logging for analysis
        self.analysis_log = []
        logger.info(f"🔍 SystemAnalyzer initialized for project: {self.project_root}")
    
    def analyze_complete_system(self) -> Dict[str, Any]:
        """
        Build complete system map BEFORE any diagnostic operations.
        This is mandatory to understand the full impact of any changes.
        """
        logger.info("🗺️ Starting complete system analysis...")
        start_time = datetime.now()
        
        try:
            # 1. Scan all modules and components
            all_modules = self._scan_all_modules()
            logger.info(f"📦 Found {len(all_modules)} modules")
            
            # 2. Build dependency graphs
            self._build_dependency_graph(all_modules)
            logger.info(f"🔗 Built dependency graph with {self.dependency_graph.number_of_nodes()} nodes")
            
            # 3. Analyze function calls and data flows
            self._analyze_call_patterns(all_modules)
            logger.info(f"📞 Analyzed call patterns across {len(all_modules)} modules")
            
            # 4. Identify critical paths
            self._identify_critical_paths()
            logger.info(f"🎯 Identified {len(self.critical_paths)} critical paths")
            
            # 5. Calculate component risks
            self._calculate_risk_scores()
            logger.info("⚡ Calculated risk scores for all components")
            
            # 6. Define safe change boundaries
            change_boundaries = self._define_safe_boundaries()
            logger.info("🛡️ Defined safe change boundaries")
            
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            system_map = {
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_duration_seconds": analysis_time,
                "total_modules": len(all_modules),
                "total_components": len(self.components),
                "dependency_depth": self._calculate_max_dependency_depth(),
                "critical_paths": [self._serialize_critical_path(cp) for cp in self.critical_paths],
                "high_risk_modules": self._identify_high_risk_modules(),
                "change_boundaries": change_boundaries,
                "system_health_score": self._calculate_system_health_score(),
                "complexity_metrics": self._calculate_complexity_metrics(),
                "component_map": {name: self._serialize_component(comp) 
                                for name, comp in self.components.items()}
            }
            
            logger.info(f"✅ System analysis completed in {analysis_time:.2f}s")
            logger.info(f"🏥 System health score: {system_map['system_health_score']:.2f}")
            
            return system_map
            
        except Exception as e:
            logger.error(f"❌ System analysis failed: {e}")
            logger.error(f"📊 Stack trace: {sys.exc_info()}")
            raise
    
    def _scan_all_modules(self) -> List[Path]:
        """Scan all Python modules in the project"""
        modules = []
        
        # Find all Python files
        for py_file in self.project_root.rglob("*.py"):
            # Skip __pycache__ and other generated directories
            if "__pycache__" in str(py_file) or ".git" in str(py_file):
                continue
                
            modules.append(py_file)
            
            # Create component entry
            relative_path = py_file.relative_to(self.project_root)
            module_name = str(relative_path).replace('/', '.').replace('.py', '')
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines_of_code = len([line for line in content.split('\n') if line.strip()])
                
                self.components[module_name] = SystemComponent(
                    name=module_name,
                    path=py_file,
                    component_type='module',
                    lines_of_code=lines_of_code,
                    last_modified=datetime.fromtimestamp(py_file.stat().st_mtime)
                )
                
            except Exception as e:
                logger.warning(f"⚠️ Could not analyze module {py_file}: {e}")
        
        return modules
    
    def _build_dependency_graph(self, modules: List[Path]):
        """Build comprehensive dependency graph"""
        for module_path in modules:
            try:
                # Parse AST to find imports
                with open(module_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                module_name = str(module_path.relative_to(self.project_root)).replace('/', '.').replace('.py', '')
                
                # Add module to dependency graph
                self.dependency_graph.add_node(module_name, 
                                             path=str(module_path),
                                             type='module')
                
                # Find all imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self._add_dependency(module_name, alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self._add_dependency(module_name, node.module)
                        
            except Exception as e:
                logger.warning(f"⚠️ Could not parse dependencies for {module_path}: {e}")
    
    def _add_dependency(self, from_module: str, to_module: str):
        """Add dependency relationship"""
        if to_module and not to_module.startswith('.'):  # Skip relative imports for now
            self.dependency_graph.add_edge(from_module, to_module, 
                                         relationship='imports')
            
            # Update component dependencies
            if from_module in self.components:
                self.components[from_module].dependencies.add(to_module)
            if to_module in self.components:
                self.components[to_module].dependents.add(from_module)
    
    def _analyze_call_patterns(self, modules: List[Path]):
        """Analyze function call patterns to build call graph"""
        for module_path in modules:
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                module_name = str(module_path.relative_to(self.project_root)).replace('/', '.').replace('.py', '')
                
                # Find function definitions and calls
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = f"{module_name}.{node.name}"
                        self.call_graph.add_node(func_name, 
                                               module=module_name,
                                               type='function',
                                               line_number=node.lineno)
                        
                        # Find calls within this function
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call):
                                if isinstance(child.func, ast.Name):
                                    called_func = f"{module_name}.{child.func.id}"
                                    self.call_graph.add_edge(func_name, called_func,
                                                           call_type='direct')
                                elif isinstance(child.func, ast.Attribute):
                                    # Handle object.method() calls
                                    if isinstance(child.func.value, ast.Name):
                                        called_func = f"{child.func.value.id}.{child.func.attr}"
                                        self.call_graph.add_edge(func_name, called_func,
                                                               call_type='method')
                        
            except Exception as e:
                logger.warning(f"⚠️ Could not analyze call patterns for {module_path}: {e}")
    
    def _identify_critical_paths(self):
        """Identify critical execution paths that could cause system failures"""
        # Find paths from entry points (main functions, handlers) to exit points
        entry_points = self._find_entry_points()
        
        for entry_point in entry_points:
            try:
                # Use networkx to find all paths from entry point
                reachable_nodes = nx.descendants(self.call_graph, entry_point)
                
                if len(reachable_nodes) > 5:  # Only consider significant paths
                    path_id = hashlib.md5(f"{entry_point}_{len(reachable_nodes)}".encode()).hexdigest()[:8]
                    
                    critical_path = CriticalPath(
                        path_id=path_id,
                        components=list(reachable_nodes),
                        entry_points=[entry_point],
                        exit_points=self._find_exit_points_for_path(reachable_nodes),
                        risk_score=self._calculate_path_risk(reachable_nodes),
                        failure_impact=self._assess_failure_impact(entry_point),
                        recovery_time=self._estimate_recovery_time(entry_point)
                    )
                    
                    self.critical_paths.append(critical_path)
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not analyze critical path from {entry_point}: {e}")
    
    def _find_entry_points(self) -> List[str]:
        """Find system entry points (main functions, handlers, etc.)"""
        entry_points = []
        
        for node in self.call_graph.nodes():
            node_data = self.call_graph.nodes[node]
            node_name = node.split('.')[-1].lower()
            
            # Common entry point patterns
            if any(pattern in node_name for pattern in [
                'main', 'handler', 'command', 'callback', 'start', 'init',
                'process', 'execute', 'run', 'webhook'
            ]):
                entry_points.append(node)
        
        return entry_points
    
    def _find_exit_points_for_path(self, nodes: Set[str]) -> List[str]:
        """Find exit points for a given path"""
        exit_points = []
        
        for node in nodes:
            # Nodes with no outgoing edges are potential exit points
            if self.call_graph.out_degree(node) == 0:
                exit_points.append(node)
        
        return exit_points
    
    def _calculate_path_risk(self, nodes: Set[str]) -> float:
        """Calculate risk score for a critical path"""
        risk_factors = {
            'external_dependencies': 0,
            'database_operations': 0,
            'network_calls': 0,
            'file_operations': 0,
            'complexity': len(nodes) / 100.0  # Complexity based on path length
        }
        
        for node in nodes:
            node_name = node.lower()
            if any(keyword in node_name for keyword in ['request', 'http', 'api']):
                risk_factors['network_calls'] += 1
            if any(keyword in node_name for keyword in ['db', 'database', 'query', 'session']):
                risk_factors['database_operations'] += 1
            if any(keyword in node_name for keyword in ['file', 'read', 'write', 'open']):
                risk_factors['file_operations'] += 1
        
        # Calculate weighted risk score
        weights = {'external_dependencies': 0.3, 'database_operations': 0.25, 
                  'network_calls': 0.25, 'file_operations': 0.1, 'complexity': 0.1}
        
        risk_score = sum(risk_factors[factor] * weights[factor] 
                        for factor in risk_factors)
        
        return min(risk_score, 1.0)  # Cap at 1.0
    
    def _assess_failure_impact(self, entry_point: str) -> str:
        """Assess the impact if this entry point fails"""
        entry_name = entry_point.lower()
        
        if any(keyword in entry_name for keyword in ['main', 'start', 'init']):
            return "catastrophic"
        elif any(keyword in entry_name for keyword in ['handler', 'process', 'command']):
            return "high"
        elif any(keyword in entry_name for keyword in ['callback', 'helper', 'util']):
            return "medium"
        else:
            return "low"
    
    def _estimate_recovery_time(self, entry_point: str) -> int:
        """Estimate recovery time in seconds if this entry point fails"""
        impact = self._assess_failure_impact(entry_point)
        
        recovery_times = {
            "catastrophic": 300,  # 5 minutes
            "high": 120,         # 2 minutes
            "medium": 60,        # 1 minute
            "low": 30            # 30 seconds
        }
        
        return recovery_times.get(impact, 60)
    
    def _calculate_risk_scores(self):
        """Calculate risk scores for all components"""
        for component_name, component in self.components.items():
            risk_score = 0.0
            
            # Factor 1: Number of dependents (high dependents = high risk)
            dependents_score = min(len(component.dependents) / 10.0, 1.0)
            
            # Factor 2: Complexity (lines of code)
            complexity_score = min(component.lines_of_code / 1000.0, 1.0)
            
            # Factor 3: Last modified (recently changed = higher risk)
            days_since_modified = (datetime.now() - component.last_modified).days
            recency_score = max(0, 1.0 - (days_since_modified / 30.0))
            
            # Factor 4: Critical path involvement
            critical_path_score = 0.0
            for cp in self.critical_paths:
                if component_name in cp.components:
                    critical_path_score += cp.risk_score
            critical_path_score = min(critical_path_score, 1.0)
            
            # Weighted average
            risk_score = (dependents_score * 0.3 + 
                         complexity_score * 0.2 + 
                         recency_score * 0.2 + 
                         critical_path_score * 0.3)
            
            component.complexity_score = risk_score
            
            # Assign risk level
            if risk_score >= 0.8:
                component.risk_level = "critical"
            elif risk_score >= 0.6:
                component.risk_level = "high"
            elif risk_score >= 0.4:
                component.risk_level = "medium"
            else:
                component.risk_level = "low"
    
    def _define_safe_boundaries(self) -> Dict[str, List[str]]:
        """Define safe boundaries for changes based on dependency analysis"""
        boundaries = {
            "isolated_modules": [],  # Modules with few dependencies
            "core_modules": [],      # Critical modules that affect many others
            "interface_modules": [], # Modules that define interfaces
            "utility_modules": []    # Utility modules with many dependents
        }
        
        for component_name, component in self.components.items():
            if len(component.dependencies) <= 2 and len(component.dependents) <= 2:
                boundaries["isolated_modules"].append(component_name)
            elif len(component.dependents) >= 5:
                if "handler" in component_name.lower() or "service" in component_name.lower():
                    boundaries["interface_modules"].append(component_name)
                elif "util" in component_name.lower() or "common" in component_name.lower():
                    boundaries["utility_modules"].append(component_name)
                else:
                    boundaries["core_modules"].append(component_name)
        
        return boundaries
    
    def _calculate_max_dependency_depth(self) -> int:
        """Calculate the maximum depth of dependency chains"""
        try:
            if self.dependency_graph.number_of_nodes() == 0:
                return 0
            
            # Find strongly connected components to handle cycles
            strongly_connected = list(nx.strongly_connected_components(self.dependency_graph))
            
            # Create a condensed graph without cycles
            condensed = nx.condensation(self.dependency_graph, strongly_connected)
            
            # Find the longest path in the condensed graph
            if condensed.number_of_nodes() == 0:
                return 0
                
            longest_path = nx.dag_longest_path_length(condensed)
            return longest_path
            
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate dependency depth: {e}")
            return 0
    
    def _identify_high_risk_modules(self) -> List[str]:
        """Identify modules with high risk scores"""
        high_risk = []
        
        for component_name, component in self.components.items():
            if component.risk_level in ["high", "critical"]:
                high_risk.append(component_name)
        
        return sorted(high_risk, key=lambda x: self.components[x].complexity_score, reverse=True)
    
    def _calculate_system_health_score(self) -> float:
        """Calculate overall system health score"""
        if not self.components:
            return 0.0
        
        total_risk = sum(comp.complexity_score for comp in self.components.values())
        avg_risk = total_risk / len(self.components)
        
        # Health score is inverse of risk (1.0 = perfect health, 0.0 = maximum risk)
        health_score = max(0.0, 1.0 - avg_risk)
        
        return round(health_score, 3)
    
    def _calculate_complexity_metrics(self) -> Dict[str, Any]:
        """Calculate various complexity metrics for the system"""
        total_loc = sum(comp.lines_of_code for comp in self.components.values())
        total_components = len(self.components)
        total_dependencies = self.dependency_graph.number_of_edges()
        
        return {
            "total_lines_of_code": total_loc,
            "average_lines_per_component": total_loc / max(total_components, 1),
            "total_dependencies": total_dependencies,
            "dependency_ratio": total_dependencies / max(total_components, 1),
            "cyclomatic_complexity": self._estimate_cyclomatic_complexity(),
            "coupling_score": self._calculate_coupling_score(),
            "cohesion_score": self._calculate_cohesion_score()
        }
    
    def _estimate_cyclomatic_complexity(self) -> float:
        """Estimate overall cyclomatic complexity"""
        # Simplified estimation based on dependency graph
        complexity = 0.0
        
        for node in self.dependency_graph.nodes():
            # Complexity increases with the number of dependencies
            out_degree = self.dependency_graph.out_degree(node)
            complexity += 1 + out_degree  # Base complexity of 1 + edges
        
        return complexity / max(self.dependency_graph.number_of_nodes(), 1)
    
    def _calculate_coupling_score(self) -> float:
        """Calculate coupling score (0.0 = loosely coupled, 1.0 = tightly coupled)"""
        if self.dependency_graph.number_of_nodes() == 0:
            return 0.0
        
        total_possible_edges = self.dependency_graph.number_of_nodes() * (self.dependency_graph.number_of_nodes() - 1)
        actual_edges = self.dependency_graph.number_of_edges()
        
        coupling_score = actual_edges / max(total_possible_edges, 1)
        return min(coupling_score, 1.0)
    
    def _calculate_cohesion_score(self) -> float:
        """Calculate cohesion score (higher is better)"""
        # Simplified cohesion calculation based on module internal connectivity
        total_cohesion = 0.0
        module_count = 0
        
        for component_name, component in self.components.items():
            if component.component_type == 'module':
                # Calculate internal connectivity of the module
                internal_connections = len([dep for dep in component.dependencies 
                                          if dep.startswith(component_name.split('.')[0])])
                external_connections = len(component.dependencies) - internal_connections
                
                if len(component.dependencies) > 0:
                    module_cohesion = internal_connections / len(component.dependencies)
                    total_cohesion += module_cohesion
                    module_count += 1
        
        return total_cohesion / max(module_count, 1)
    
    def _serialize_component(self, component: SystemComponent) -> Dict[str, Any]:
        """Serialize component for JSON output"""
        return {
            "name": component.name,
            "path": str(component.path),
            "type": component.component_type,
            "dependencies": list(component.dependencies),
            "dependents": list(component.dependents),
            "complexity_score": component.complexity_score,
            "risk_level": component.risk_level,
            "last_modified": component.last_modified.isoformat(),
            "lines_of_code": component.lines_of_code,
            "test_coverage": component.test_coverage
        }
    
    def _serialize_critical_path(self, cp: CriticalPath) -> Dict[str, Any]:
        """Serialize critical path for JSON output"""
        return {
            "path_id": cp.path_id,
            "components": cp.components,
            "entry_points": cp.entry_points,
            "exit_points": cp.exit_points,
            "risk_score": cp.risk_score,
            "failure_impact": cp.failure_impact,
            "recovery_time_seconds": cp.recovery_time
        }
    
    def find_all_usages(self, function_or_class_name: str) -> List[Tuple[str, int]]:
        """Find ALL usages of a function or class across the system"""
        usages = []
        
        for module_path in self.project_root.rglob("*.py"):
            if "__pycache__" in str(module_path):
                continue
                
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for line_no, line in enumerate(lines, 1):
                    if function_or_class_name in line:
                        # More sophisticated matching could be added here
                        usages.append((str(module_path), line_no))
                        
            except Exception as e:
                logger.warning(f"⚠️ Could not scan {module_path} for usages: {e}")
        
        return usages
    
    def get_component_impact_analysis(self, component_name: str) -> Dict[str, Any]:
        """Get detailed impact analysis for a specific component"""
        if component_name not in self.components:
            return {"error": "Component not found"}
        
        component = self.components[component_name]
        
        # Find all components that would be affected by changes to this component
        affected_components = set()
        
        # Direct dependents
        direct_dependents = component.dependents.copy()
        affected_components.update(direct_dependents)
        
        # Transitive dependents (components that depend on the dependents)
        for dependent in direct_dependents:
            if dependent in self.components:
                affected_components.update(self.components[dependent].dependents)
        
        # Critical paths involving this component
        involved_critical_paths = [cp for cp in self.critical_paths 
                                 if component_name in cp.components]
        
        return {
            "component": component_name,
            "risk_level": component.risk_level,
            "complexity_score": component.complexity_score,
            "direct_dependents": list(direct_dependents),
            "total_affected_components": len(affected_components),
            "affected_components": list(affected_components),
            "involved_critical_paths": len(involved_critical_paths),
            "critical_path_details": [self._serialize_critical_path(cp) 
                                    for cp in involved_critical_paths],
            "change_impact_score": self._calculate_change_impact_score(component_name),
            "recommended_testing_strategy": self._recommend_testing_strategy(component_name)
        }
    
    def _calculate_change_impact_score(self, component_name: str) -> float:
        """Calculate the potential impact score of changing this component"""
        component = self.components[component_name]
        
        # Factors contributing to change impact
        dependent_count_score = min(len(component.dependents) / 10.0, 1.0)
        critical_path_score = len([cp for cp in self.critical_paths 
                                 if component_name in cp.components]) / max(len(self.critical_paths), 1)
        complexity_score = component.complexity_score
        
        # Weighted combination
        impact_score = (dependent_count_score * 0.4 + 
                       critical_path_score * 0.4 + 
                       complexity_score * 0.2)
        
        return round(impact_score, 3)
    
    def _recommend_testing_strategy(self, component_name: str) -> List[str]:
        """Recommend testing strategy based on component analysis"""
        component = self.components[component_name]
        recommendations = []
        
        if component.risk_level in ["high", "critical"]:
            recommendations.append("Full regression testing required")
            recommendations.append("Load testing recommended")
        
        if len(component.dependents) > 3:
            recommendations.append("Integration testing for all dependents")
        
        if any(component_name in cp.components for cp in self.critical_paths):
            recommendations.append("End-to-end testing for critical paths")
        
        if component.component_type == 'service':
            recommendations.append("Service-level testing with mocks")
        
        if not recommendations:
            recommendations.append("Unit testing sufficient")
        
        return recommendations