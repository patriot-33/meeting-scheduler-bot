#!/usr/bin/env python3
"""
Скрипт для установки команд бота в Telegram
"""
import os
import asyncio
from telegram import Bot, BotCommand
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Команды для всех пользователей
COMMANDS = [
    BotCommand("start", "Запустить бота"),
    BotCommand("help", "Справка по командам"),
    BotCommand("schedule", "Назначить встречу"),
    BotCommand("my_meetings", "Мои встречи"),
    BotCommand("profile", "Мой профиль"),
    BotCommand("vacation", "Режим отпуска"),
    BotCommand("sick", "Больничный"),
    BotCommand("trip", "Командировка"),
    BotCommand("active", "Активный статус"),
    BotCommand("admin", "Админ панель"),
    BotCommand("cancel", "Отмена операции"),
]

async def setup_commands():
    """Установить команды бота"""
    if not BOT_TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Устанавливаем команды
        await bot.set_my_commands(COMMANDS)
        print("✅ Команды бота успешно установлены!")
        
        # Проверяем
        commands = await bot.get_my_commands()
        print("\n📋 Установленные команды:")
        for cmd in commands:
            print(f"   /{cmd.command} - {cmd.description}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(setup_commands())