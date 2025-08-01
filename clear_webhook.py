#!/usr/bin/env python3
"""
Очистка webhook и pending updates для тестирования
"""

import asyncio
import sys
from pathlib import Path

# Добавляем src в Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def clear_webhook():
    from telegram import Bot
    from config import settings
    
    bot = Bot(token=settings.bot_token)
    
    # Удаляем webhook
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook удален и pending updates очищены")
    
    # Проверяем статус
    info = await bot.get_webhook_info()
    print(f"📋 Webhook URL: {info.url}")
    print(f"📋 Pending updates: {info.pending_update_count}")

if __name__ == "__main__":
    asyncio.run(clear_webhook())