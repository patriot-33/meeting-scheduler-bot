#!/usr/bin/env python3
"""
🚨 ДИАГНОСТИКА: Проблема "Проблема с подключением" в команде /calendar
"""

import sys
import os
import json
import logging
from datetime import datetime

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Настройка детального логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

def test_oauth_environment():
    """Тестирование переменных окружения для OAuth"""
    print("🔍 ДИАГНОСТИКА OAUTH ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
    print("="*60)
    
    # Проверяем все OAuth переменные
    oauth_vars = {
        'GOOGLE_OAUTH_CLIENT_JSON': 'OAuth Client JSON для менеджеров',
        'GOOGLE_OAUTH_CLIENT_FILE': 'OAuth Client File путь',
        'GOOGLE_OAUTH_CLIENT_ID': 'Public OAuth Client ID',
        'WEBHOOK_URL': 'Webhook URL для redirect'
    }
    
    results = {}
    
    for var_name, description in oauth_vars.items():
        value = os.getenv(var_name)
        if value:
            if 'JSON' in var_name:
                try:
                    parsed = json.loads(value)
                    print(f"✅ {var_name}: Валидный JSON")
                    if 'web' in parsed:
                        client_id = parsed['web'].get('client_id', 'НЕ НАЙДЕН')
                        client_secret = parsed['web'].get('client_secret', 'НЕ НАЙДЕН')
                        redirect_uris = parsed['web'].get('redirect_uris', [])
                        
                        print(f"   📋 Client ID: {client_id[:30]}...")
                        print(f"   🔐 Client Secret: {'✅ Установлен' if client_secret != 'НЕ НАЙДЕН' else '❌ Отсутствует'}")
                        print(f"   🔗 Redirect URIs: {redirect_uris}")
                        
                        results[var_name] = {
                            'status': 'valid',
                            'client_id': client_id,
                            'has_secret': client_secret != 'НЕ НАЙДЕН',
                            'redirect_uris': redirect_uris
                        }
                    else:
                        print(f"❌ {var_name}: JSON не содержит 'web'")
                        results[var_name] = {'status': 'invalid', 'error': 'Missing web section'}
                except json.JSONDecodeError as e:
                    print(f"❌ {var_name}: Некорректный JSON - {e}")
                    results[var_name] = {'status': 'invalid', 'error': f'JSON error: {e}'}
            elif var_name == 'WEBHOOK_URL':
                print(f"✅ {var_name}: {value}")
                results[var_name] = {'status': 'valid', 'value': value}
            else:
                print(f"✅ {var_name}: {value}")
                results[var_name] = {'status': 'valid', 'value': value}
        else:
            print(f"❌ {var_name}: НЕ УСТАНОВЛЕНА ({description})")
            results[var_name] = {'status': 'missing'}
    
    return results

def test_oauth_service_initialization():
    """Тестирование инициализации OAuth Service"""
    print(f"\n🧪 ТЕСТИРОВАНИЕ OAUTH SERVICE")
    print("="*60)
    
    try:
        from services.oauth_service import oauth_service
        
        print(f"📦 OAuth Service импортирован: ✅")
        print(f"🔧 is_oauth_configured: {oauth_service.is_oauth_configured}")
        
        if hasattr(oauth_service, 'client_config'):
            print(f"⚙️ client_config существует: {'✅' if oauth_service.client_config else '❌'}")
            if oauth_service.client_config:
                print(f"   - Type: {type(oauth_service.client_config)}")
        
        if hasattr(oauth_service, 'redirect_uri'):
            print(f"🔗 redirect_uri: {getattr(oauth_service, 'redirect_uri', 'НЕ УСТАНОВЛЕН')}")
        
        # Тестируем генерацию URL
        if oauth_service.is_oauth_configured:
            try:
                test_url = oauth_service.generate_auth_url(12345)
                if test_url:
                    print(f"✅ URL генерация работает")
                    print(f"   Sample URL: {test_url[:100]}...")
                    return True
                else:
                    print(f"❌ URL генерация вернула None")
                    return False
            except Exception as e:
                print(f"❌ Ошибка генерации URL: {type(e).__name__}: {e}")
                return False
        else:
            print(f"❌ OAuth не настроен - URL генерация невозможна")
            return False
            
    except ImportError as e:
        print(f"❌ Ошибка импорта oauth_service: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {type(e).__name__}: {e}")
        return False

def test_manager_calendar_handler():
    """Тестирование обработчика manager_calendar"""
    print(f"\n🎯 ТЕСТИРОВАНИЕ MANAGER CALENDAR HANDLER")
    print("="*60)
    
    try:
        from handlers.manager_calendar import connect_calendar
        print(f"📦 Обработчик connect_calendar импортирован: ✅")
        
        # Проверяем, что функция существует и callable
        if callable(connect_calendar):
            print(f"🔧 connect_calendar вызываемая: ✅")
        else:
            print(f"❌ connect_calendar не вызываемая")
            
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта connect_calendar: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {type(e).__name__}: {e}")
        return False

def simulate_oauth_flow():
    """Симуляция OAuth flow для выявления проблем"""
    print(f"\n🔄 СИМУЛЯЦИЯ OAUTH FLOW")
    print("="*60)
    
    try:
        from config import settings
        
        # Шаг 1: Проверка конфигурации
        print("Шаг 1: Проверка конфигурации...")
        if not settings.google_oauth_client_json:
            print("❌ GOOGLE_OAUTH_CLIENT_JSON не установлен")
            return False
        
        # Шаг 2: Парсинг JSON
        print("Шаг 2: Парсинг OAuth JSON...")
        try:
            oauth_config = json.loads(settings.google_oauth_client_json)
            print("✅ OAuth JSON парсится корректно")
        except Exception as e:
            print(f"❌ Ошибка парсинга OAuth JSON: {e}")
            return False
        
        # Шаг 3: Проверка структуры
        print("Шаг 3: Проверка структуры JSON...")
        required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
        web_config = oauth_config.get('web', {})
        
        missing_fields = []
        for field in required_fields:
            if not web_config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Отсутствуют обязательные поля: {missing_fields}")
            return False
        else:
            print("✅ Все обязательные поля присутствуют")
        
        # Шаг 4: Проверка redirect URI
        print("Шаг 4: Проверка redirect URI...")
        redirect_uris = web_config.get('redirect_uris', [])
        webhook_url = settings.webhook_url
        
        if not webhook_url:
            print("❌ WEBHOOK_URL не установлен")
            return False
        
        expected_redirect = f"{webhook_url}/oauth/callback"
        if expected_redirect in redirect_uris:
            print(f"✅ Redirect URI корректный: {expected_redirect}")
        else:
            print(f"❌ Redirect URI некорректный")
            print(f"   Ожидается: {expected_redirect}")
            print(f"   Найдено: {redirect_uris}")
            return False
        
        # Шаг 5: Тестирование OAuth Service
        print("Шаг 5: Тестирование OAuth Service...")
        from services.oauth_service import oauth_service
        
        if not oauth_service.is_oauth_configured:
            print("❌ OAuth Service не инициализирован")
            return False
        
        print("✅ Все проверки OAuth flow пройдены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка симуляции OAuth flow: {type(e).__name__}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    print("🚨 DEBUG: Команда /calendar возвращает 'Проблема с подключением'")
    print(f"🕐 Время диагностики: {datetime.now()}")
    print("="*80)
    
    # Результаты тестов
    results = {
        'environment': test_oauth_environment(),
        'oauth_service': test_oauth_service_initialization(),
        'handler': test_manager_calendar_handler(),
        'oauth_flow': simulate_oauth_flow()
    }
    
    print(f"\n📊 ИТОГОВЫЙ ДИАГНОСТИЧЕСКИЙ ОТЧЕТ")
    print("="*80)
    
    # Подсчет успешных тестов
    success_count = sum(1 for result in results.values() if result is True)
    
    print(f"Environment Variables: {'✅ PASS' if isinstance(results['environment'], dict) else '❌ FAIL'}")
    print(f"OAuth Service Init: {'✅ PASS' if results['oauth_service'] else '❌ FAIL'}")
    print(f"Handler Import: {'✅ PASS' if results['handler'] else '❌ FAIL'}")
    print(f"OAuth Flow Simulation: {'✅ PASS' if results['oauth_flow'] else '❌ FAIL'}")
    
    print(f"\n🎯 РЕЗУЛЬТАТ: {success_count}/4 компонентов работают")
    
    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
    
    if not results['oauth_service']:
        print("1. ❌ OAuth Service не инициализирован")
        print("   - Проверьте GOOGLE_OAUTH_CLIENT_JSON на Render.com")
        print("   - Убедитесь, что JSON валидный и содержит 'web' секцию")
    
    if not results['oauth_flow']:
        print("2. ❌ OAuth Flow неполный")
        print("   - Проверьте redirect URI в Google Cloud Console")
        print("   - Убедитесь, что WEBHOOK_URL установлен корректно")
    
    if success_count == 4:
        print("✅ Все компоненты работают - проблема может быть в другом месте")
        print("   - Проверьте логи Google Cloud Console")
        print("   - Проверьте настройки OAuth Consent Screen")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()