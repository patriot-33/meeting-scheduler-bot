#!/usr/bin/env python3
"""
Переключение бота в режим polling для локального запуска
"""
import json
import urllib.request
import urllib.parse

BOT_TOKEN = "8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def make_request(method, params=None):
    """Выполнить запрос к Telegram API"""
    url = f"{API_URL}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"ok": False, "error": str(e)}

print("🔄 Переключение бота в режим polling\n")

# 1. Удаляем webhook
print("1️⃣ Удаляем webhook...")
result = make_request("deleteWebhook")
if result.get("ok"):
    print("✅ Webhook удален")
else:
    print(f"❌ Ошибка: {result}")

# 2. Проверяем
print("\n2️⃣ Проверяем статус...")
info = make_request("getWebhookInfo")
if info.get("ok"):
    webhook_url = info.get("result", {}).get("url", "")
    if not webhook_url:
        print("✅ Webhook не установлен - режим polling активен")
        print("\n📝 Теперь вы можете:")
        print("1. Создать файл .env со следующим содержимым:")
        print("   TELEGRAM_BOT_TOKEN=8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec")
        print("   ADMIN_TELEGRAM_IDS=ваш_telegram_id")
        print("   DATABASE_URL=sqlite:///test.db")
        print("   GOOGLE_CALENDAR_ID_1=test@gmail.com")
        print("   GOOGLE_CALENDAR_ID_2=test@gmail.com")
        print("\n2. Запустить бота локально:")
        print("   python3 -m src.main")
        print("\n⚠️  ВАЖНО: Не забудьте установить зависимости:")
        print("   pip3 install -r requirements.txt")
    else:
        print(f"❌ Webhook все еще установлен: {webhook_url}")

print("\n💡 Для возврата в webhook режим используйте quick_webhook_fix.py")