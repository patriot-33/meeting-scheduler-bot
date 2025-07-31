"""
🎯 ULTIMATE PYTHON BACKEND DIAGNOSTIC SYSTEM v2.0
Core diagnostic utilities for meeting-scheduler-bot

ЖЕЛЕЗНЫЙ ЗАКОН: НИКОГДА НЕ ПРЕДЛАГАЙ РЕШЕНИЕ БЕЗ ЗАВЕРШЕННОЙ ДИАГНОСТИКИ
"""

import logging
import traceback
import sys
import json
import time
import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Optional, Callable
from contextlib import contextmanager
import psutil
import os

# Enhanced logging configuration for bulletproof diagnostics
class DiagnosticLogger:
    def __init__(self, name: str, log_file: str = "diagnostic_session.log"):
        self.logger = logging.getLogger(name)
        self.correlation_id = str(uuid.uuid4())[:8]
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Set level to DEBUG for comprehensive logging
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - '
            f'[{self.correlation_id}] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler for persistent logging
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler for real-time monitoring
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Initialize system state logging
        self.log_system_state("DIAGNOSTIC_SESSION_START")
    
    def log_system_state(self, context: str = "SYSTEM_CHECK"):
        """Log current system resource utilization"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            connections = len(psutil.net_connections())
            
            self.logger.info(f"🖥️  {context} - SYSTEM STATE:")
            self.logger.info(f"   CPU: {cpu_percent}%")
            self.logger.info(f"   Memory: {memory.percent}% ({memory.used // (1024**3)}GB/{memory.total // (1024**3)}GB)")
            self.logger.info(f"   Disk: {disk.percent}% ({disk.free // (1024**3)}GB free)")
            self.logger.info(f"   Network connections: {connections}")
            self.logger.info(f"   Process PID: {os.getpid()}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to log system state: {e}")
    
    def debug_context(self, func_name: str, local_vars: Dict[str, Any], step: str):
        """Log detailed context information for debugging"""
        self.logger.debug(f"🔍 {func_name} - Step: {step}")
        for var_name, var_value in local_vars.items():
            if var_name.startswith('_'):  # Skip private variables
                continue
            try:
                var_str = str(var_value)[:200]  # Limit string length
                self.logger.debug(f"   {var_name}: {type(var_value).__name__} = {var_str}")
            except Exception:
                self.logger.debug(f"   {var_name}: {type(var_value).__name__} = <unable to serialize>")
    
    def validate_data_integrity(self, data: Any, checkpoint_name: str):
        """Validate and log data integrity at checkpoints"""
        self.logger.debug(f"📊 DATA CHECKPOINT: {checkpoint_name}")
        self.logger.debug(f"   Type: {type(data).__name__}")
        
        try:
            if hasattr(data, '__len__'):
                self.logger.debug(f"   Size: {len(data)}")
            
            data_str = str(data)[:200]
            self.logger.debug(f"   Content preview: {data_str}...")
            
            # Type-specific validation
            if isinstance(data, dict):
                self.logger.debug(f"   Keys: {list(data.keys())}")
                if not data:
                    self.logger.warning(f"   ⚠️  Empty dictionary at {checkpoint_name}")
            elif isinstance(data, list):
                self.logger.debug(f"   Sample items: {data[:3] if data else 'Empty'}")
                if not data:
                    self.logger.warning(f"   ⚠️  Empty list at {checkpoint_name}")
            elif data is None:
                self.logger.warning(f"   ⚠️  None value at {checkpoint_name}")
                
        except Exception as e:
            self.logger.error(f"   ❌ Data validation failed: {e}")

# Priority classification system
class ProblemPriority:
    P0_CRITICAL = "P0_CRITICAL"
    P1_HIGH = "P1_HIGH"
    P2_MEDIUM = "P2_MEDIUM"
    P3_LOW = "P3_LOW"

def classify_problem_priority(error_msg: str, context: Dict[str, Any]) -> str:
    """Classify problem priority based on error message and context"""
    error_lower = error_msg.lower()
    
    # P0 Critical indicators
    if any(keyword in error_lower for keyword in [
        "production down", "data loss", "security breach", "database connection failed",
        "critical error", "webhook failed", "bot not responding"
    ]):
        return ProblemPriority.P0_CRITICAL
    
    # P1 High indicators
    if any(keyword in error_lower for keyword in [
        "users affected", "performance degraded", "google calendar", "oauth",
        "meeting creation failed", "timeout", "memory"
    ]):
        return ProblemPriority.P1_HIGH
    
    # P2 Medium indicators
    if any(keyword in error_lower for keyword in [
        "feature broken", "integration failed", "validation error",
        "reminder failed", "notification"
    ]):
        return ProblemPriority.P2_MEDIUM
    
    return ProblemPriority.P3_LOW

def classify_problem_type(error_msg: str, traceback_str: str) -> str:
    """Classify the type of problem based on error information"""
    error_lower = error_msg.lower()
    traceback_lower = traceback_str.lower()
    
    if any(keyword in error_lower for keyword in ["exception", "error", "failed", "crash"]):
        if "database" in error_lower or "sqlalchemy" in traceback_lower:
            return "🗄️  DATABASE_ERROR"
        elif "network" in error_lower or "timeout" in error_lower or "connection" in error_lower:
            return "🔌 INTEGRATION_ERROR" 
        elif "memory" in error_lower or "cpu" in error_lower:
            return "⚡ PERFORMANCE_ERROR"
        else:
            return "🐛 RUNTIME_ERROR"
    
    if "slow" in error_lower or "performance" in error_lower:
        return "⚡ PERFORMANCE_ERROR"
    
    if "google" in error_lower or "oauth" in error_lower or "api" in error_lower:
        return "🔌 INTEGRATION_ERROR"
    
    if "security" in error_lower or "authentication" in error_lower:
        return "🔐 SECURITY_ERROR"
    
    return "🏗️  ARCHITECTURE_ERROR"

# Function instrumentation decorator
def diagnose_function(logger: DiagnosticLogger):
    """Decorator to add comprehensive diagnostics to functions"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            # Log function entry
            logger.logger.debug(f"🚀 ENTRY: {func_name}")
            logger.logger.debug(f"   Args: {args}")
            logger.logger.debug(f"   Kwargs: {kwargs}")
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log successful execution
                execution_time = time.time() - start_time
                logger.logger.debug(f"✅ SUCCESS: {func_name} ({execution_time:.3f}s)")
                logger.logger.debug(f"   Result type: {type(result).__name__}")
                
                return result
                
            except Exception as e:
                # Log error details
                execution_time = time.time() - start_time
                error_msg = str(e)
                traceback_str = traceback.format_exc()
                
                priority = classify_problem_priority(error_msg, {})
                problem_type = classify_problem_type(error_msg, traceback_str)
                
                logger.logger.error(f"❌ ERROR: {func_name} ({execution_time:.3f}s)")
                logger.logger.error(f"   Priority: {priority}")
                logger.logger.error(f"   Type: {problem_type}")
                logger.logger.error(f"   Error: {type(e).__name__}: {error_msg}")
                logger.logger.error(f"   Traceback: {traceback_str}")
                
                # Log system state on error
                logger.log_system_state(f"ERROR_IN_{func_name}")
                
                raise
                
            finally:
                logger.logger.debug(f"🏁 EXIT: {func_name}")
                
        return wrapper
    return decorator

# Context manager for diagnostic blocks
@contextmanager
def diagnostic_context(logger: DiagnosticLogger, operation_name: str, **context):
    """Context manager for diagnostic code blocks"""
    start_time = time.time()
    logger.logger.info(f"🎯 START: {operation_name}")
    
    for key, value in context.items():
        logger.logger.debug(f"   Context {key}: {value}")
    
    try:
        yield logger
        
        execution_time = time.time() - start_time
        logger.logger.info(f"✅ COMPLETED: {operation_name} ({execution_time:.3f}s)")
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        priority = classify_problem_priority(error_msg, context)
        problem_type = classify_problem_type(error_msg, traceback_str)
        
        logger.logger.error(f"❌ FAILED: {operation_name} ({execution_time:.3f}s)")
        logger.logger.error(f"   Priority: {priority}")
        logger.logger.error(f"   Type: {problem_type}")
        logger.logger.error(f"   Error: {type(e).__name__}: {error_msg}")
        logger.logger.error(f"   Context: {context}")
        logger.logger.error(f"   Traceback: {traceback_str}")
        
        logger.log_system_state(f"ERROR_IN_{operation_name}")
        raise

# Global diagnostic logger instance
diagnostic_logger = DiagnosticLogger("meeting_scheduler_diagnostics")

# Convenience functions
def log_system_state(context: str = "MANUAL_CHECK"):
    """Quick system state logging"""
    diagnostic_logger.log_system_state(context)

def debug_context(func_name: str, local_vars: Dict[str, Any], step: str):
    """Quick context debugging"""
    diagnostic_logger.debug_context(func_name, local_vars, step)

def validate_data(data: Any, checkpoint_name: str):
    """Quick data validation"""
    diagnostic_logger.validate_data_integrity(data, checkpoint_name)