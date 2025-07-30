#!/usr/bin/env python3
"""
Быстрое исправление webhook URL
"""
import json
import urllib.request
import urllib.parse

BOT_TOKEN = "8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec"
CORRECT_URL = "https://meeting-scheduler-bot-fkp8.onrender.com/webhook"

def make_request(method, params=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"ok": False, "error": str(e)}

print("🔧 Исправление webhook URL\n")

# 1. Проверяем текущий webhook
print("1️⃣ Текущий webhook:")
info = make_request("getWebhookInfo")
if info.get("ok"):
    result = info.get("result", {})
    current_url = result.get("url", "")
    print(f"   URL: {current_url}")
    print(f"   Pending: {result.get('pending_update_count', 0)}")
    
    if current_url == CORRECT_URL:
        print("✅ Webhook URL уже правильный!")
        exit(0)

# 2. Устанавливаем правильный URL
print(f"\n2️⃣ Устанавливаем правильный URL:")
print(f"   {CORRECT_URL}")

result = make_request("setWebhook", {
    "url": CORRECT_URL,
    "drop_pending_updates": "true"
})

if result.get("ok"):
    print("✅ Webhook обновлен!")
else:
    print(f"❌ Ошибка: {result}")

# 3. Проверяем
print("\n3️⃣ Проверка:")
info = make_request("getWebhookInfo")
if info.get("ok"):
    result = info.get("result", {})
    print(f"✅ Новый URL: {result.get('url')}")
    
    if result.get("last_error_message"):
        print(f"⚠️ Ошибка: {result.get('last_error_message')}")
    else:
        print("✅ Ошибок нет")

# 4. Тестовое сообщение
print("\n4️⃣ Отправляем тест:")
test = make_request("sendMessage", {
    "chat_id": 99006770,
    "text": "✅ Webhook исправлен!\n\nТеперь бот должен отвечать на команды."
})

if test.get("ok"):
    print("✅ Тестовое сообщение отправлено!")
    print("\n🎉 Готово! Попробуйте /start в боте.")
else:
    print(f"❌ Ошибка отправки: {test}")