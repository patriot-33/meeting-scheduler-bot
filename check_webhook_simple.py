#!/usr/bin/env python3
"""
Простой скрипт для проверки webhook - без внешних зависимостей
"""
import os
import sys
import json
import urllib.request
import urllib.parse

# Запрашиваем токен у пользователя
print("🤖 Проверка Telegram Bot Webhook\n")
BOT_TOKEN = input("Введите токен бота (или нажмите Enter для выхода): ").strip()

if not BOT_TOKEN:
    print("❌ Токен не введен. Выход.")
    sys.exit(1)

# Telegram API URL
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEBHOOK_URL = "https://meeting-scheduler-bot-fkp8.onrender.com"
WEBHOOK_PATH = "/webhook"

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

def main():
    print("\n🔍 Проверка настроек...\n")
    
    # Проверяем бота
    bot_info = make_request("getMe")
    if bot_info.get("ok"):
        bot = bot_info.get("result", {})
        print(f"✅ Бот найден: @{bot.get('username', 'Unknown')}")
    else:
        print("❌ Ошибка подключения к боту!")
        print(bot_info.get("error", "Unknown error"))
        return
    
    # Проверяем webhook
    webhook_info = make_request("getWebhookInfo")
    
    if webhook_info.get("ok"):
        result = webhook_info.get("result", {})
        current_url = result.get("url", "")
        
        print(f"\n📌 Текущий webhook URL: {current_url or 'Не установлен'}")
        print(f"📊 Необработанных сообщений: {result.get('pending_update_count', 0)}")
        
        if result.get("last_error_message"):
            print(f"\n❌ Последняя ошибка: {result.get('last_error_message')}")
            print(f"   Время: {result.get('last_error_date')}")
    
    # Меню действий
    print("\n📋 Что сделать?")
    print("1. Установить webhook для Render")
    print("2. Удалить webhook")
    print("3. Посмотреть необработанные сообщения")
    print("4. Выход")
    
    choice = input("\nВыбор (1-4): ")
    
    if choice == "1":
        full_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
        print(f"\n🔄 Устанавливаем webhook: {full_url}")
        
        # Сначала удаляем старый
        make_request("deleteWebhook")
        
        # Устанавливаем новый
        result = make_request("setWebhook", {"url": full_url})
        if result.get("ok"):
            print("✅ Webhook установлен!")
        else:
            print(f"❌ Ошибка: {result}")
    
    elif choice == "2":
        print("\n🔄 Удаляем webhook...")
        result = make_request("deleteWebhook")
        if result.get("ok"):
            print("✅ Webhook удален!")
        else:
            print(f"❌ Ошибка: {result}")
    
    elif choice == "3":
        print("\n🔄 Получаем сообщения...")
        updates = make_request("getUpdates")
        if updates.get("ok"):
            messages = updates.get("result", [])
            print(f"\n📨 Найдено сообщений: {len(messages)}")
            
            if messages:
                print("\nПоследние 5:")
                for msg in messages[-5:]:
                    m = msg.get("message", {})
                    if m:
                        user = m.get("from", {})
                        print(f"\n👤 {user.get('first_name', '')} (@{user.get('username', 'Unknown')})")
                        print(f"💬 {m.get('text', '')}")
                        print(f"🕐 {m.get('date', '')}")

if __name__ == "__main__":
    main()