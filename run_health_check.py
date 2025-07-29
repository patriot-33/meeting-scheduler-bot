#!/usr/bin/env python3
"""
Health check script for Meeting Scheduler Bot
Run before deployment to verify everything is configured correctly.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.health_check import health_check

def main():
    print("🔍 Running pre-deployment health check...")
    print("-" * 50)
    
    result = health_check()
    
    print(f"Status: {result['status'].upper()}")
    print(f"Timestamp: {result['checks']['timestamp']}")
    print()
    
    for check_name, check_result in result['checks'].items():
        if check_name == 'timestamp':
            continue
            
        status = check_result['status']
        message = check_result['message']
        emoji = "✅" if status else "❌"
        
        print(f"{emoji} {check_name.title()}: {message}")
    
    print("-" * 50)
    
    if result['status'] == 'healthy':
        print("🎉 All checks passed! Bot is ready for deployment.")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix issues before deployment.")
        return 1

if __name__ == '__main__':
    sys.exit(main())