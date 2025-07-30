#!/usr/bin/env python3
"""
Скрипт для настройки webhook при деплое на Render.com
"""
import json
import urllib.request
import urllib.parse
import time
import sys

BOT_TOKEN = "8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec"
RENDER_URL = "https://meeting-scheduler-bot-fkp8.onrender.com"
WEBHOOK_PATH = "/webhook"

def make_request(method, params=None):
    """Выполнить запрос к Telegram API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"ok": False, "error": str(e)}

def check_render_health():
    """Проверить доступность сервиса на Render"""
    health_url = f"{RENDER_URL}/health"
    try:
        with urllib.request.urlopen(health_url, timeout=15) as response:
            if response.status == 200:
                return True, "Сервис доступен"
    except Exception as e:
        return False, f"Сервис недоступен: {e}"
    return False, "Неизвестная ошибка"

def setup_webhook():
    """Настроить webhook для Render"""
    webhook_url = f"{RENDER_URL}{WEBHOOK_PATH}"
    
    print("🚀 Настройка webhook для Render.com\n")
    
    # 1. Проверяем доступность сервиса
    print("1️⃣ Проверяем доступность Render сервиса...")
    is_healthy, health_msg = check_render_health()
    if not is_healthy:
        print(f"❌ {health_msg}")
        print("\n📋 Что делать:")
        print("1. Зайдите на https://dashboard.render.com")
        print("2. Найдите сервис meeting-scheduler-bot")
        print("3. Проверьте логи и статус")
        print("4. Если нужно, сделайте Manual Deploy")
        print("5. Дождитесь запуска и повторите этот скрипт")
        return False
    
    print(f"✅ {health_msg}")
    
    # 2. Удаляем старый webhook
    print("\n2️⃣ Удаляем старый webhook...")
    delete_result = make_request("deleteWebhook", {"drop_pending_updates": "true"})
    if delete_result.get("ok"):
        print("✅ Старый webhook удален")
    else:
        print(f"⚠️ Не удалось удалить webhook: {delete_result}")
    
    # 3. Ждем немного
    print("\n3️⃣ Ожидание 5 секунд...")
    time.sleep(5)
    
    # 4. Устанавливаем новый webhook
    print(f"\n4️⃣ Устанавливаем webhook: {webhook_url}")
    set_result = make_request("setWebhook", {
        "url": webhook_url,
        "max_connections": 40,
        "drop_pending_updates": "true"
    })
    
    if set_result.get("ok"):
        print("✅ Webhook успешно установлен!")
    else:
        print(f"❌ Ошибка установки webhook: {set_result}")
        return False
    
    # 5. Проверяем результат
    print("\n5️⃣ Проверяем webhook...")
    info_result = make_request("getWebhookInfo")
    if info_result.get("ok"):
        result = info_result.get("result", {})
        print(f"✅ URL: {result.get('url')}")
        print(f"✅ Pending updates: {result.get('pending_update_count', 0)}")
        
        if result.get("last_error_message"):
            print(f"⚠️ Последняя ошибка: {result.get('last_error_message')}")
        else:
            print("✅ Ошибок нет")
    
    # 6. Отправляем тестовое сообщение
    print("\n6️⃣ Отправляем тестовое сообщение...")
    test_result = make_request("sendMessage", {
        "chat_id": 99006770,
        "text": "🎉 Бот успешно развернут на Render.com!\n\nWebhook настроен и работает.\nМожете тестировать команды."
    })
    
    if test_result.get("ok"):
        print("✅ Тестовое сообщение отправлено!")
    else:
        print(f"❌ Не удалось отправить сообщение: {test_result}")
    
    print("\n🎉 Настройка завершена!")
    print("Теперь бот должен отвечать на команды в Telegram.")
    
    return True

if __name__ == "__main__":
    success = setup_webhook()
    sys.exit(0 if success else 1)