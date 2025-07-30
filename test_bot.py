#!/usr/bin/env python3
"""
Скрипт для тестирования Telegram бота
"""
import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def test_bot():
    """Тестирование основных функций бота"""
    if not BOT_TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Получаем информацию о боте
        print("🤖 Проверка бота...")
        bot_info = await bot.get_me()
        print(f"✅ Бот активен!")
        print(f"   Имя: {bot_info.first_name}")
        print(f"   Username: @{bot_info.username}")
        print(f"   ID: {bot_info.id}")
        
        # Проверяем webhook
        print("\n🔗 Проверка webhook...")
        webhook_info = await bot.get_webhook_info()
        print(f"   URL: {webhook_info.url or 'Не установлен'}")
        print(f"   Pending updates: {webhook_info.pending_update_count}")
        
        if webhook_info.last_error_message:
            print(f"   ❌ Последняя ошибка: {webhook_info.last_error_message}")
            print(f"   Время: {webhook_info.last_error_date}")
        
        # Проверяем команды
        print("\n📋 Установленные команды:")
        commands = await bot.get_my_commands()
        if commands:
            for cmd in commands:
                print(f"   /{cmd.command} - {cmd.description}")
        else:
            print("   Команды не установлены")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании бота: {e}")

async def send_test_message():
    """Отправить тестовое сообщение"""
    admin_id = input("Введите ваш Telegram ID для тестового сообщения: ")
    if not admin_id:
        return
        
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=int(admin_id),
            text="✅ Тестовое сообщение от бота!\n\nЕсли вы видите это сообщение, бот работает корректно."
        )
        print("✅ Тестовое сообщение отправлено!")
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")

async def main():
    """Главная функция"""
    print("🔧 Тестирование Telegram бота\n")
    
    await test_bot()
    
    print("\n📋 Дополнительные опции:")
    print("1. Отправить тестовое сообщение")
    print("2. Выход")
    
    choice = input("\nВыбор (1-2): ")
    
    if choice == "1":
        await send_test_message()

if __name__ == "__main__":
    asyncio.run(main())