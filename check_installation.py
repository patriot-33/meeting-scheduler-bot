#!/usr/bin/env python3
"""
🔍 Installation Checker for Ultimate Diagnostic System v2.0
Проверяет все зависимости и компоненты системы
"""

import sys
import importlib
import subprocess
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ❌ Python 3.8+ required")
        return False
    elif version.minor < 9:
        print("   ⚠️  Python 3.9+ recommended")
    else:
        print("   ✅ Python version OK")
    
    return True

def check_module(module_name, package_name=None):
    """Проверка отдельного модуля"""
    try:
        importlib.import_module(module_name)
        print(f"   ✅ {module_name}")
        return True
    except ImportError:
        package = package_name or module_name
        print(f"   ❌ {module_name} - install with: pip install {package}")
        return False

def check_dependencies():
    """Проверка всех зависимостей"""
    print("\n📦 Checking dependencies...")
    
    # Core dependencies
    dependencies = [
        ("telegram", "python-telegram-bot[webhooks]==20.7"),
        ("sqlalchemy", "SQLAlchemy==2.0.23"),
        ("alembic", "alembic==1.13.1"),
        ("psycopg2", "psycopg2-binary==2.9.9"),
        
        # Google APIs
        ("googleapiclient", "google-api-python-client==2.108.0"),
        ("google.auth", "google-auth-httplib2==0.1.1"),
        ("google_auth_oauthlib", "google-auth-oauthlib==1.1.0"),
        
        # Async and scheduling
        ("apscheduler", "apscheduler==3.10.4"),
        ("aiohttp", "aiohttp==3.9.1"),
        
        # Environment and config
        ("dotenv", "python-dotenv==1.0.0"),
        ("pydantic", "pydantic==2.5.2"),
        
        # Utils
        ("pytz", "pytz==2023.3"),
        ("dateutil", "python-dateutil==2.8.2"),
        ("psutil", "psutil==5.9.6"),
        
        # Diagnostic System dependencies
        ("schedule", "schedule==1.2.0"),
        ("click", "click==8.1.7"),
        ("requests", "requests==2.31.0"),
    ]
    
    failed = []
    for module_name, package_name in dependencies:
        if not check_module(module_name, package_name):
            failed.append(package_name)
    
    return failed

def check_diagnostic_components():
    """Проверка компонентов диагностической системы"""
    print("\n🎯 Checking diagnostic system components...")
    
    components = [
        "src.diagnostics.core_diagnostics",
        "src.diagnostics.diagnostic_orchestrator", 
        "src.diagnostics.system_monitor",
        "src.diagnostics.hypothesis_testing",
        "src.diagnostics.safe_implementation",
        "src.diagnostics.post_solution_monitoring",
    ]
    
    failed = []
    for component in components:
        try:
            importlib.import_module(component)
            print(f"   ✅ {component}")
        except ImportError as e:
            print(f"   ❌ {component} - {e}")
            failed.append(component)
    
    return failed

def check_cli_functionality():
    """Проверка CLI функциональности"""
    print("\n🔧 Checking CLI functionality...")
    
    cli_file = Path("ultimate_diagnostic_cli.py")
    demo_file = Path("ultimate_diagnostic_demo.py")
    
    if not cli_file.exists():
        print("   ❌ ultimate_diagnostic_cli.py not found")
        return False
    
    if not demo_file.exists():
        print("   ❌ ultimate_diagnostic_demo.py not found")
        return False
    
    print("   ✅ CLI files found")
    
    # Test CLI import
    try:
        import ultimate_diagnostic_cli
        print("   ✅ CLI import successful")
    except Exception as e:
        print(f"   ❌ CLI import failed: {e}")
        return False
    
    return True

def check_examples():
    """Проверка примеров"""
    print("\n📋 Checking examples...")
    
    examples_dir = Path("examples")
    if not examples_dir.exists():
        print("   ❌ examples/ directory not found")
        return False
    
    required_examples = [
        "examples/fix_timeout_solution.py",
        "examples/verify_timeout_fix.py"
    ]
    
    for example in required_examples:
        if Path(example).exists():
            print(f"   ✅ {example}")
        else:
            print(f"   ❌ {example} not found")
            return False
    
    return True

def run_quick_test():
    """Быстрый тест диагностической системы"""
    print("\n🧪 Running quick diagnostic test...")
    
    try:
        from src.diagnostics.core_diagnostics import DiagnosticLogger
        logger = DiagnosticLogger("installation_test")
        print("   ✅ Diagnostic logger created")
        
        from src.diagnostics.system_monitor import SystemMonitor
        monitor = SystemMonitor(logger)
        metrics = monitor.get_current_metrics()
        print(f"   ✅ System metrics: CPU {metrics.cpu_percent}%, Memory {metrics.memory_percent}%")
        
        from src.diagnostics.hypothesis_testing import HypothesisTester
        tester = HypothesisTester(logger)
        print("   ✅ Hypothesis tester created")
        
        print("   ✅ Quick diagnostic test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Quick diagnostic test failed: {e}")
        return False

def generate_report(failed_deps, failed_components):
    """Генерация отчета о проблемах"""
    if not failed_deps and not failed_components:
        print("\n🎉 INSTALLATION SUCCESSFUL!")
        print("   All components are working correctly.")
        print("   You can now use the diagnostic system:")
        print("   - python3 ultimate_diagnostic_cli.py version")
        print("   - python3 ultimate_diagnostic_cli.py quick-check")
        print("   - python3 ultimate_diagnostic_demo.py --auto")
        return True
    
    print("\n❌ INSTALLATION ISSUES DETECTED!")
    
    if failed_deps:
        print("\n📦 Missing dependencies:")
        for dep in failed_deps:
            print(f"   pip install {dep}")
        
        print("\n🔧 To install all missing dependencies:")
        print("   pip install " + " ".join(f'"{dep}"' for dep in failed_deps))
    
    if failed_components:
        print("\n🎯 Failed diagnostic components:")
        for comp in failed_components:
            print(f"   {comp}")
    
    print("\n📋 For help, see INSTALLATION.md or create an issue at:")
    print("   https://github.com/patriot-33/meeting-scheduler-bot/issues")
    
    return False

def main():
    """Главная функция проверки"""
    print("🎯 ULTIMATE DIAGNOSTIC SYSTEM v2.0 - INSTALLATION CHECKER")
    print("=" * 60)
    
    # Проверка версии Python
    if not check_python_version():
        sys.exit(1)
    
    # Проверка зависимостей
    failed_deps = check_dependencies()
    
    # Проверка компонентов диагностической системы (только если зависимости OK)
    failed_components = []
    if not failed_deps:
        failed_components = check_diagnostic_components()
        
        # Проверка CLI функциональности
        check_cli_functionality()
        
        # Проверка примеров
        check_examples()
        
        # Быстрый тест
        run_quick_test()
    
    # Генерация отчета
    success = generate_report(failed_deps, failed_components)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Ready to use Ultimate Diagnostic System v2.0!")
        sys.exit(0)
    else:
        print("❌ Please fix the issues above before using the system.")
        sys.exit(1)

if __name__ == "__main__":
    main()