#!/usr/bin/env python3
"""
🔧 ИСПРАВЛЕНИЕ: Добавление детального логирования для отладки команды /calendar
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_debug_patch():
    """Создаем патч для manager_calendar.py с улучшенным логированием"""
    
    debug_code = '''
# ВРЕМЕННОЕ УЛУЧШЕННОЕ ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
import traceback

@require_registration
async def connect_calendar_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подключение Google Calendar через OAuth для руководителей (с отладкой)."""
    user_id = update.effective_user.id
    logger.info(f"🔍 DEBUG: connect_calendar started for user {user_id}")
    
    try:
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            logger.info(f"🔍 DEBUG: User found: {user.first_name} {user.last_name}, role: {user.role}")
            
            if user.role != UserRole.MANAGER:
                logger.warning(f"🔍 DEBUG: Access denied for user {user_id}, role: {user.role}")
                await update.message.reply_text(
                    "❌ Данная функция доступна только руководителям отделов."
                )
                return
            
            # Check if calendar is already connected
            if user.oauth_credentials and user.google_calendar_id:
                logger.info(f"🔍 DEBUG: Calendar already connected for user {user_id}")
                await update.message.reply_text(
                    f"✅ **Google Calendar уже подключен!**\\n\\n"
                    f"📧 Календарь: {user.email}\\n"
                    f"🎉 Вы можете планировать встречи командой /schedule\\n\\n"
                    f"Чтобы переподключить календарь, нажмите кнопку ниже.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Переподключить календарь", callback_data="reconnect_calendar")],
                        [InlineKeyboardButton("📅 Запланировать встречу", callback_data="schedule_meeting")]
                    ]),
                    parse_mode='Markdown'
                )
                return
        
        logger.info(f"🔍 DEBUG: Preparing OAuth instructions for user {user_id}")
        
        instructions = """
🔗 **Подключение Google Calendar**

Для автоматического создания встреч в вашем календаре:

1️⃣ **Нажмите "Подключить календарь"**
   • Вы перейдете на страницу авторизации Google
   • Войдите в ваш Google аккаунт

2️⃣ **Разрешите доступ к календарю**
   • Система запросит разрешение на управление календарем
   • Нажмите "Разрешить" для продолжения

3️⃣ **Подтверждение подключения**
   • После успешной авторизации вернитесь в бот
   • Вы получите уведомление о подключении

🎯 **Что вы получите:**
• Автоматическое создание встреч в вашем календаре
• Google Meet ссылки для видеоконференций
• Приглашения владельцев как участников
• Напоминания перед встречами

🔒 **Безопасность:**
• Мы используем официальный OAuth 2.0 Google
• Доступ только к календарю, никаких других данных
• Вы можете отозвать доступ в любой момент
"""
        
        # Generate OAuth URL
        logger.info(f"🔍 DEBUG: Starting OAuth service import for user {user_id}")
        
        try:
            from services.oauth_service import oauth_service
            logger.info(f"🔍 DEBUG: OAuth service imported successfully")
            logger.info(f"🔍 DEBUG: oauth_service.is_oauth_configured = {oauth_service.is_oauth_configured}")
            
            # Pre-check OAuth configuration 
            if not oauth_service.is_oauth_configured:
                logger.error(f"🔍 DEBUG: OAuth not configured for user {user_id}")
                instructions += "\\n\\n❌ **OAuth Client не настроен**\\n"
                instructions += "Администратор должен добавить:\\n"
                instructions += "• `GOOGLE_OAUTH_CLIENT_JSON` переменную окружения\\n"
                instructions += "• Или файл `oauth_client_key.json`\\n\\n"
                instructions += "💡 Используйте Google Cloud Console:\\n"
                instructions += "1. APIs & Services → Credentials\\n"
                instructions += "2. Create OAuth 2.0 Client → Web Application\\n"
                instructions += "3. Add redirect URI: `{}/oauth/callback`".format(settings.webhook_url or "YOUR_WEBHOOK_URL")
                
                keyboard = [
                    [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                    [InlineKeyboardButton("📧 Сообщить email владельцу", callback_data="send_email_to_owner")],
                    [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
                ]
            else:
                logger.info(f"🔍 DEBUG: Generating OAuth URL for user {user_id}")
                
                try:
                    oauth_url = oauth_service.generate_auth_url(user_id)
                    logger.info(f"🔍 DEBUG: OAuth URL generation result: {oauth_url is not None}")
                    
                    if oauth_url:
                        logger.info(f"🔍 DEBUG: OAuth URL generated successfully: {oauth_url[:50]}...")
                        keyboard = [
                            [InlineKeyboardButton("🔗 Подключить Google Calendar", url=oauth_url)],
                            [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                            [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
                        ]
                    else:
                        logger.error(f"🔍 DEBUG: OAuth URL generation returned None for user {user_id}")
                        # OAuth URL generation failed
                        instructions += "\\n\\n❌ **Ошибка генерации OAuth URL**\\n"
                        instructions += "Проверьте:\\n"
                        instructions += "• Корректность OAuth Client JSON\\n"
                        instructions += "• Настройку WEBHOOK_URL\\n"
                        instructions += "• Redirect URI в Google Console"
                        keyboard = [
                            [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                            [InlineKeyboardButton("📧 Сообщить email владельцу", callback_data="send_email_to_owner")],
                            [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
                        ]
                
                except Exception as url_error:
                    logger.error(f"🔍 DEBUG: Exception during OAuth URL generation for user {user_id}: {type(url_error).__name__}: {url_error}")
                    logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
                    
                    instructions += f"\\n\\n❌ **Ошибка генерации OAuth URL**\\n`{str(url_error)}`\\n"
                    keyboard = [
                        [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                        [InlineKeyboardButton("📧 Сообщить email владельцу", callback_data="send_email_to_owner")],
                        [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
                    ]
                    
        except ImportError as import_error:
            logger.error(f"🔍 DEBUG: OAuth service import failed for user {user_id}: {import_error}")
            logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
            
            instructions += f"\\n\\n❌ **Ошибка импорта OAuth сервиса**\\n`{str(import_error)}`\\n"
            keyboard = [
                [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                [InlineKeyboardButton("📧 Сообщить email владельцу", callback_data="send_email_to_owner")],
                [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
            ]
            
        except Exception as oauth_error:
            logger.error(f"🔍 DEBUG: General OAuth error for user {user_id}: {type(oauth_error).__name__}: {oauth_error}")
            logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
            
            instructions += f"\\n\\n❌ **Критическая ошибка OAuth**\\n`{str(oauth_error)}`\\n\\nОбратитесь к администратору."
            keyboard = [
                [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                [InlineKeyboardButton("📧 Сообщить email владельцу", callback_data="send_email_to_owner")],
                [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        logger.info(f"🔍 DEBUG: Sending response to user {user_id}")
        
        try:
            await update.message.reply_text(
                instructions, 
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            logger.info(f"🔍 DEBUG: Response sent successfully to user {user_id}")
            
        except Exception as send_error:
            logger.error(f"🔍 DEBUG: Failed to send message to user {user_id}: {type(send_error).__name__}: {send_error}")
            logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
            raise send_error
        
    except Exception as main_error:
        logger.error(f"🔍 DEBUG: Main exception in connect_calendar for user {user_id}: {type(main_error).__name__}: {main_error}")
        logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        raise main_error
'''
    
    return debug_code

if __name__ == "__main__":
    print("🔧 DEBUG PATCH для manager_calendar.py")
    print("="*50)
    
    debug_patch = create_debug_patch()
    
    print("📋 Этот патч добавляет детальное логирование в connect_calendar:")
    print("- Логирование каждого шага выполнения")
    print("- Отлов и логирование всех исключений")
    print("- Проверка конфигурации OAuth Service")
    print("- Детальная диагностика генерации OAuth URL")
    
    print("\\n💡 Для применения патча:")
    print("1. Добавьте эту функцию в manager_calendar.py")
    print("2. Замените обработчик команды в main.py на connect_calendar_debug")
    print("3. Перезапустите бота")
    print("4. Проверьте логи Render.com после выполнения /calendar")
    
    print("\\n🎯 После получения логов мы точно найдем источник NetworkError!")