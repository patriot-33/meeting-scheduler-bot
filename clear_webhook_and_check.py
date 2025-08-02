#!/usr/bin/env python3
"""
Script to clear webhook and check bot status
This resolves "Connection timed out" errors
"""
import os
import requests
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not found in .env")
    sys.exit(1)

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def delete_webhook():
    """Delete current webhook"""
    print("🗑️ Deleting webhook...")
    response = requests.post(f"{BASE_URL}/deleteWebhook")
    data = response.json()
    
    if data.get('ok'):
        print("✅ Webhook deleted successfully")
    else:
        print(f"❌ Failed to delete webhook: {data}")
    
    return data.get('ok', False)

def get_webhook_info():
    """Get current webhook information"""
    print("\n📊 Getting webhook info...")
    response = requests.post(f"{BASE_URL}/getWebhookInfo")
    data = response.json()
    
    if data.get('ok'):
        info = data.get('result', {})
        print(f"✅ Webhook URL: {info.get('url', 'Not set')}")
        print(f"✅ Pending updates: {info.get('pending_update_count', 0)}")
        
        if info.get('last_error_message'):
            print(f"❌ Last error: {info.get('last_error_message')}")
            print(f"❌ Error date: {info.get('last_error_date')}")
        else:
            print("✅ No errors")
            
        if info.get('has_custom_certificate'):
            print("⚠️ Has custom certificate")
            
        print(f"✅ Max connections: {info.get('max_connections', 40)}")
        print(f"✅ Allowed updates: {info.get('allowed_updates', [])}")
    else:
        print(f"❌ Failed to get webhook info: {data}")
    
    return data.get('result', {})

def get_updates():
    """Check if there are pending updates (indicates polling conflict)"""
    print("\n🔍 Checking for pending updates...")
    response = requests.post(f"{BASE_URL}/getUpdates", json={"limit": 1})
    data = response.json()
    
    if data.get('ok'):
        updates = data.get('result', [])
        if updates:
            print(f"⚠️ Found {len(updates)} pending updates - possible polling conflict!")
            return True
        else:
            print("✅ No pending updates")
            return False
    else:
        print(f"❌ Failed to get updates: {data}")
        return None

def main():
    print("🔧 TELEGRAM BOT WEBHOOK DIAGNOSTIC & FIX")
    print("=" * 50)
    
    # Step 1: Check current webhook
    webhook_info = get_webhook_info()
    
    # Step 2: Check for polling conflicts
    has_updates = get_updates()
    
    # Step 3: Clear webhook if there are issues
    if webhook_info.get('last_error_message') or has_updates:
        print("\n⚠️ Issues detected, clearing webhook...")
        if delete_webhook():
            print("✅ Webhook cleared successfully")
            print("\n📌 NEXT STEPS:")
            print("1. Make sure NO other bot instances are running")
            print("2. Restart the bot in Render.com")
            print("3. The bot will set up a fresh webhook on startup")
        else:
            print("❌ Failed to clear webhook")
    else:
        print("\n✅ Webhook appears to be healthy")
        
    # Step 4: Final check
    print("\n📊 Final webhook state:")
    get_webhook_info()

if __name__ == "__main__":
    main()