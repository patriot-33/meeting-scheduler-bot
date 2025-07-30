#!/usr/bin/env python3
"""
Настройка бота для локального запуска
"""
import json
import urllib.request
import urllib.parse

BOT_TOKEN = "8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def make_request(method, params=None):
    url = f"{API_URL}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"ok": False, "error": str(e)}

print("🔧 Настройка бота для локального запуска\n")

# 1. Удаляем webhook
print("1️⃣ Удаляем webhook...")
make_request("deleteWebhook")

# 2. Получаем обновления и находим ID
print("\n2️⃣ Ищем ваш Telegram ID...")
updates = make_request("getUpdates")
telegram_id = None

if updates.get("ok"):
    for update in updates.get("result", []):
        msg = update.get("message", {})
        if msg:
            user = msg.get("from", {})
            if user.get("username") == "PlantatorBob":
                telegram_id = user.get("id")
                print(f"✅ Найден @PlantatorBob: ID = {telegram_id}")
                break

if telegram_id:
    # 3. Обновляем .env
    print("\n3️⃣ Обновляем .env файл...")
    with open('.env', 'r') as f:
        content = f.read()
    
    content = content.replace('YOUR_TELEGRAM_ID_HERE', str(telegram_id))
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print("✅ .env обновлен!")
    
    # 4. Отправляем тестовое сообщение
    print("\n4️⃣ Отправляем тестовое сообщение...")
    msg_result = make_request("sendMessage", {
        "chat_id": telegram_id,
        "text": "✅ Бот готов к локальному запуску!\n\nТеперь запустите:\npython3 -m src.main"
    })
    
    if msg_result.get("ok"):
        print("✅ Сообщение отправлено!")
    
print("\n📋 Следующий шаг:")
print("python3 -m src.main")