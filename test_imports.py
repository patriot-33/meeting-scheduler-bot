#!/usr/bin/env python3
"""
Simple import test without requiring dependencies.
Tests module structure and basic syntax.
"""
import sys
import os
import ast

def test_python_syntax(file_path):
    """Test if Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    print("🔍 Testing Python syntax and structure...")
    print("-" * 50)
    
    # Files to test
    test_files = [
        'src/main.py',
        'src/config.py', 
        'src/database.py',
        'src/handlers/common.py',
        'src/handlers/admin.py',
        'src/handlers/manager.py',
        'src/handlers/registration.py',
        'src/services/google_calendar.py',
        'src/services/meeting_service.py',
        'src/services/reminder_service.py',
        'src/services/user_service.py',
        'src/utils/decorators.py',
        'src/utils/scheduler.py',
        'src/utils/health_check.py'
    ]
    
    all_passed = True
    
    for file_path in test_files:
        if os.path.exists(file_path):
            success, message = test_python_syntax(file_path)
            emoji = "✅" if success else "❌"
            print(f"{emoji} {file_path}: {message}")
            if not success:
                all_passed = False
        else:
            print(f"⚠️  {file_path}: File not found")
            all_passed = False
    
    print("-" * 50)
    
    if all_passed:
        print("🎉 All syntax tests passed!")
        print("✅ Ready for dependency installation and deployment")
        return 0
    else:
        print("❌ Some files have syntax errors")
        return 1

if __name__ == '__main__':
    sys.exit(main())