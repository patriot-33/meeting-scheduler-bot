#!/usr/bin/env python3
"""
Test script to reproduce the get_db UnboundLocalError issue
"""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_get_db_import():
    """Test basic get_db import and functionality"""
    print("🔍 Testing get_db import...")
    
    try:
        from database import get_db, User, UserRole
        print("✅ Successfully imported get_db, User, UserRole")
        
        # Test creating a context manager
        db_context = get_db()
        print(f"✅ get_db() returns: {type(db_context)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manager_calendar_import():
    """Test importing the manager_calendar module"""
    print("\n🔍 Testing manager_calendar import...")
    
    try:
        import handlers.manager_calendar as mc
        print("✅ Successfully imported manager_calendar")
        
        # Check if get_db is in the namespace
        if hasattr(mc, 'get_db'):
            print("✅ get_db found in manager_calendar namespace")
            print(f"   Type: {type(mc.get_db)}")
        else:
            print("❌ get_db NOT found in manager_calendar namespace")
            
        return True
        
    except Exception as e:
        print(f"❌ Manager calendar import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_function_execution_context():
    """Test the actual execution context where the error occurs"""
    print("\n🔍 Testing function execution context...")
    
    try:
        # Simulate the exact context where the error occurs
        from database import get_db, User, UserRole
        
        # Create a mock user_id 
        user_id = 12345
        
        print(f"   Testing with user_id: {user_id}")
        print(f"   get_db available: {get_db}")
        print(f"   get_db callable: {callable(get_db)}")
        
        # Test the exact line that's failing
        with get_db() as db:
            print("✅ Successfully created database context")
            # Don't actually query since we might not have the DB set up
            
        return True
        
    except Exception as e:
        print(f"❌ Execution context error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🛡️ TESTING GET_DB UNBOUNDLOCALERROR ISSUE")
    print("=" * 50)
    
    test_results = []
    
    # Test 1: Basic import
    test_results.append(test_get_db_import())
    
    # Test 2: Manager calendar import
    test_results.append(test_manager_calendar_import())
    
    # Test 3: Function execution context
    test_results.append(test_function_execution_context())
    
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS:")
    print(f"   Tests passed: {sum(test_results)}/{len(test_results)}")
    
    if all(test_results):
        print("✅ All tests passed - the issue might be runtime-specific")
        print("💡 Suggestion: The error might occur only under specific conditions")
        print("   like when the bot is running with full Telegram integration")
    else:
        print("❌ Some tests failed - found the root cause")
    
    return all(test_results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)