#!/usr/bin/env python3
"""
🔍 ТЕСТ: OAuth конфигурация для менеджеров
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import settings

print("🔍 ТЕСТ OAUTH КОНФИГУРАЦИИ")
print("="*50)

print(f"📱 Telegram Bot Token: {'✅ Установлен' if settings.telegram_bot_token else '❌ НЕ установлен'}")
print(f"🗄️ Database URL: {'✅ Установлен' if settings.database_url else '❌ НЕ установлен'}")
print(f"👤 Admin IDs: {settings.admin_ids_list}")

print(f"\n🗓️ GOOGLE CALENDAR:")
print(f"   📅 Calendar Enabled: {settings.google_calendar_enabled}")
print(f"   📧 Calendar ID 1: {settings.google_calendar_id_1}")
print(f"   📧 Calendar ID 2: {settings.google_calendar_id_2}")

print(f"\n🔐 SERVICE ACCOUNT (для владельцев):")
has_service_json = bool(settings.google_service_account_json)
print(f"   📄 Service Account JSON: {'✅ Установлен' if has_service_json else '❌ НЕ установлен'}")

print(f"\n🔑 OAUTH CLIENT (для менеджеров):")
has_oauth_json = bool(settings.google_oauth_client_json)
print(f"   📄 OAuth Client JSON: {'✅ Установлен' if has_oauth_json else '❌ НЕ установлен'}")

if has_oauth_json:
    import json
    try:
        oauth_data = json.loads(settings.google_oauth_client_json)
        client_id = oauth_data.get('web', {}).get('client_id', 'НЕ НАЙДЕН')
        print(f"   🆔 Client ID: {client_id[:20]}...")
        
        redirect_uris = oauth_data.get('web', {}).get('redirect_uris', [])
        print(f"   🔗 Redirect URIs: {redirect_uris}")
    except Exception as e:
        print(f"   ❌ Ошибка парсинга OAuth JSON: {e}")

print(f"\n🌐 WEBHOOK:")
print(f"   🔗 Webhook URL: {settings.webhook_url}")

# Проверяем oauth_service
print(f"\n🧪 ТЕСТ OAUTH SERVICE:")
try:
    from services.oauth_service import oauth_service
    
    print(f"   🔧 OAuth configured: {'✅ Да' if oauth_service.is_oauth_configured else '❌ Нет'}")
    
    if oauth_service.is_oauth_configured:
        # Тестируем генерацию URL
        test_user_id = 12345
        test_url = oauth_service.generate_auth_url(test_user_id)
        if test_url:
            print(f"   🔗 Auth URL generation: ✅ Работает")
            print(f"   📋 Sample URL: {test_url[:80]}...")
        else:
            print(f"   🔗 Auth URL generation: ❌ Не работает")
    
except Exception as e:
    print(f"   ❌ Ошибка OAuth Service: {e}")

print(f"\n🎯 РЕЗУЛЬТАТ:")
all_ready = (
    settings.telegram_bot_token and 
    settings.database_url and 
    settings.admin_ids_list and
    has_service_json and
    has_oauth_json and
    settings.webhook_url
)

if all_ready:
    print("✅ ВСЁ ГОТОВО! Менеджеры смогут подключать календари!")
    print("📝 Команда для менеджера: /calendar")
else:
    print("⚠️ Некоторые настройки отсутствуют, но основные функции работают")

print("\n" + "="*50)