#!/usr/bin/env python3
"""
Получить Telegram ID пользователя
"""
import json
import urllib.request

BOT_TOKEN = "8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

print("🔍 Получение Telegram ID\n")

# Получаем последние сообщения
url = f"{API_URL}/getUpdates"
try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
        
    if data.get("ok"):
        updates = data.get("result", [])
        
        if updates:
            # Ищем сообщения от @PlantatorBob
            for update in updates:
                msg = update.get("message", {})
                if msg:
                    user = msg.get("from", {})
                    if user.get("username") == "PlantatorBob":
                        print(f"✅ Найден пользователь @PlantatorBob")
                        print(f"   ID: {user.get('id')}")
                        print(f"   Имя: {user.get('first_name')} {user.get('last_name', '')}")
                        
                        # Обновляем .env
                        with open('.env', 'r') as f:
                            content = f.read()
                        
                        content = content.replace('YOUR_TELEGRAM_ID_HERE', str(user.get('id')))
                        
                        with open('.env', 'w') as f:
                            f.write(content)
                        
                        print("\n✅ Файл .env обновлен!")
                        break
        else:
            print("❌ Нет сообщений от пользователей")
            
except Exception as e:
    print(f"❌ Ошибка: {e}")