#!/usr/bin/env python3
"""
Скрипт для проверки и настройки webhook для Telegram бота
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://meeting-scheduler-bot-fkp8.onrender.com")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")

if not BOT_TOKEN:
    print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен!")
    sys.exit(1)

# Telegram API URL
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_webhook_info():
    """Получить текущую информацию о webhook"""
    response = requests.get(f"{API_URL}/getWebhookInfo")
    return response.json()

def delete_webhook():
    """Удалить текущий webhook"""
    response = requests.get(f"{API_URL}/deleteWebhook")
    return response.json()

def set_webhook(url):
    """Установить новый webhook"""
    response = requests.get(f"{API_URL}/setWebhook", params={"url": url})
    return response.json()

def get_updates():
    """Получить обновления (для режима polling)"""
    response = requests.get(f"{API_URL}/getUpdates")
    return response.json()

def main():
    print("🔍 Проверка webhook настроек...\n")
    
    # Проверяем текущий webhook
    webhook_info = get_webhook_info()
    
    if webhook_info.get("ok"):
        result = webhook_info.get("result", {})
        current_url = result.get("url", "")
        
        print(f"📌 Текущий webhook URL: {current_url or 'Не установлен'}")
        print(f"📊 Количество pending updates: {result.get('pending_update_count', 0)}")
        
        if result.get("last_error_message"):
            print(f"❌ Последняя ошибка: {result.get('last_error_message')}")
            print(f"   Время ошибки: {result.get('last_error_date')}")
        
        if result.get("has_custom_certificate"):
            print("🔒 Используется кастомный сертификат")
    else:
        print("❌ Не удалось получить информацию о webhook")
        print(webhook_info)
    
    # Опции для пользователя
    print("\n📋 Выберите действие:")
    print("1. Установить webhook для Render.com")
    print("2. Удалить webhook (переключиться на polling)")
    print("3. Проверить обновления")
    print("4. Переустановить webhook")
    print("5. Выход")
    
    choice = input("\nВаш выбор (1-5): ")
    
    if choice == "1":
        full_webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
        print(f"\n🔄 Устанавливаем webhook: {full_webhook_url}")
        result = set_webhook(full_webhook_url)
        if result.get("ok"):
            print("✅ Webhook успешно установлен!")
        else:
            print(f"❌ Ошибка установки webhook: {result}")
    
    elif choice == "2":
        print("\n🔄 Удаляем webhook...")
        result = delete_webhook()
        if result.get("ok"):
            print("✅ Webhook удален! Бот переключен в режим polling.")
            print("ℹ️  Для работы в режиме polling запустите бота локально.")
        else:
            print(f"❌ Ошибка удаления webhook: {result}")
    
    elif choice == "3":
        print("\n🔄 Проверяем обновления...")
        updates = get_updates()
        if updates.get("ok"):
            update_list = updates.get("result", [])
            print(f"📨 Найдено обновлений: {len(update_list)}")
            if update_list:
                print("\nПоследние обновления:")
                for update in update_list[-5:]:  # Показываем последние 5
                    message = update.get("message", {})
                    if message:
                        print(f"- От: {message.get('from', {}).get('username', 'Unknown')}")
                        print(f"  Текст: {message.get('text', '')}")
                        print(f"  ID: {update.get('update_id')}")
        else:
            print(f"❌ Ошибка получения обновлений: {updates}")
    
    elif choice == "4":
        print("\n🔄 Переустанавливаем webhook...")
        # Сначала удаляем
        delete_result = delete_webhook()
        if delete_result.get("ok"):
            print("✅ Старый webhook удален")
            
            # Затем устанавливаем новый
            full_webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
            print(f"🔄 Устанавливаем новый webhook: {full_webhook_url}")
            result = set_webhook(full_webhook_url)
            if result.get("ok"):
                print("✅ Webhook успешно переустановлен!")
            else:
                print(f"❌ Ошибка установки webhook: {result}")
        else:
            print(f"❌ Ошибка удаления webhook: {delete_result}")

if __name__ == "__main__":
    main()