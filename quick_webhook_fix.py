#!/usr/bin/env python3
"""
Быстрое исправление webhook для бота на Render
"""
import json
import urllib.request
import urllib.parse
import sys

# ВАЖНО: Вставьте ваш токен сюда
BOT_TOKEN = "8318735096:AAHQZ-GJNxr4Jon0T9lR5DD0EJx-s1O_7Ec"

if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("❌ ОШИБКА: Откройте файл quick_webhook_fix.py и вставьте ваш токен бота!")
    print("   Строка 11: BOT_TOKEN = \"ваш_токен_здесь\"")
    sys.exit(1)

# Настройки
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEBHOOK_URL = "https://meeting-scheduler-bot-fkp8.onrender.com/webhook"

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

print("🔧 Быстрое исправление webhook для Meeting Scheduler Bot\n")

# 1. Проверяем бота
print("1️⃣ Проверяем бота...")
bot_info = make_request("getMe")
if bot_info.get("ok"):
    bot = bot_info.get("result", {})
    print(f"✅ Бот активен: @{bot.get('username')}")
else:
    print("❌ Ошибка подключения к боту!")
    print(bot_info)
    sys.exit(1)

# 2. Проверяем текущий webhook
print("\n2️⃣ Проверяем текущий webhook...")
webhook_info = make_request("getWebhookInfo")
if webhook_info.get("ok"):
    result = webhook_info.get("result", {})
    current_url = result.get("url", "")
    pending = result.get("pending_update_count", 0)
    
    print(f"   Текущий URL: {current_url or 'Не установлен'}")
    print(f"   Необработанных сообщений: {pending}")
    
    if result.get("last_error_message"):
        print(f"   ❌ Последняя ошибка: {result.get('last_error_message')}")

# 3. Удаляем старый webhook
print("\n3️⃣ Удаляем старый webhook...")
delete_result = make_request("deleteWebhook")
if delete_result.get("ok"):
    print("✅ Старый webhook удален")
else:
    print(f"❌ Ошибка: {delete_result}")

# 4. Очищаем необработанные сообщения
print("\n4️⃣ Очищаем необработанные сообщения...")
updates = make_request("getUpdates")
if updates.get("ok"):
    count = len(updates.get("result", []))
    print(f"✅ Очищено {count} сообщений")

# 5. Устанавливаем новый webhook
print(f"\n5️⃣ Устанавливаем webhook: {WEBHOOK_URL}")
set_result = make_request("setWebhook", {"url": WEBHOOK_URL})
if set_result.get("ok"):
    print("✅ Webhook успешно установлен!")
else:
    print(f"❌ Ошибка установки: {set_result}")

# 6. Проверяем результат
print("\n6️⃣ Финальная проверка...")
final_check = make_request("getWebhookInfo")
if final_check.get("ok"):
    result = final_check.get("result", {})
    if result.get("url") == WEBHOOK_URL:
        print("✅ Все настроено правильно!")
        print(f"   Webhook: {result.get('url')}")
        print(f"   Необработанных сообщений: {result.get('pending_update_count', 0)}")
        print("\n🎉 Готово! Попробуйте отправить /start боту.")
    else:
        print("❌ Webhook не соответствует ожидаемому")
        print(result)

# 7. Устанавливаем команды бота
print("\n7️⃣ Устанавливаем команды бота...")
commands = [
    {"command": "start", "description": "Запустить бота"},
    {"command": "help", "description": "Справка по командам"},
    {"command": "schedule", "description": "Назначить встречу"},
    {"command": "my_meetings", "description": "Мои встречи"},
    {"command": "profile", "description": "Мой профиль"},
    {"command": "vacation", "description": "Режим отпуска"},
    {"command": "sick", "description": "Больничный"},
    {"command": "trip", "description": "Командировка"},
    {"command": "active", "description": "Активный статус"},
    {"command": "admin", "description": "Админ панель"},
]

set_commands_result = make_request("setMyCommands", {"commands": json.dumps(commands)})
if set_commands_result.get("ok"):
    print("✅ Команды установлены!")
else:
    print(f"❌ Ошибка установки команд: {set_commands_result}")

print("\n✨ Все готово! Теперь бот должен отвечать на команды.")