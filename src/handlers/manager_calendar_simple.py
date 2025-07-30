"""
Simple calendar integration for managers using Calendar ID sharing.
No OAuth required - managers just share their calendar with service account.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_db, User, UserRole
from utils.decorators import require_registration
from services.google_calendar import google_calendar_service as calendar_service
from config import settings

logger = logging.getLogger(__name__)

@require_registration
async def simple_calendar_connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Простое подключение календаря через Calendar ID.
    Руководитель дает доступ сервисному аккаунту к своему календарю.
    """
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if user.role != UserRole.MANAGER:
            await update.message.reply_text(
                "❌ Данная функция доступна только руководителям отделов."
            )
            return
        
        # Get service account email
        service_account_email = calendar_service.get_service_account_email()
        
        if not service_account_email:
            await update.message.reply_text(
                "❌ Сервисный аккаунт не настроен. Обратитесь к администратору."
            )
            return
    
    instructions = f"""
🗓️ **Простое подключение Google Calendar**

Вам не нужен OAuth! Просто поделитесь календарем:

1️⃣ **Откройте Google Calendar**
   • Перейдите на https://calendar.google.com
   • Найдите ваш рабочий календарь

2️⃣ **Поделитесь календарем с ботом**
   • Нажмите на 3 точки рядом с календарем
   • Выберите "Настройки и общий доступ"
   • В разделе "Предоставить доступ" добавьте:
   
   📧 `{service_account_email}`
   
   • Установите разрешение: **"Вносить изменения"**
   • Нажмите "Отправить"

3️⃣ **Скопируйте ID календаря**
   • В настройках календаря найдите "ID календаря"
   • Выглядит как: `your.email@gmail.com` или `abc123...@group.calendar.google.com`

4️⃣ **Отправьте ID боту**
   Используйте команду:
   `/setcalendar ВАШ_CALENDAR_ID`

✅ **Преимущества:**
• Не требует OAuth авторизации
• Вы контролируете доступ через Google Calendar
• Можете отозвать доступ в любой момент
• Работает с корпоративными календарями

🔒 **Безопасность:**
• Бот получит доступ только к указанному календарю
• Никаких паролей или токенов не требуется
• Вы можете ограничить доступ только на чтение
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Копировать email бота", callback_data=f"copy_service_email:{service_account_email}")],
        [InlineKeyboardButton("📺 Видео-инструкция", url="https://support.google.com/calendar/answer/37082")],
        [InlineKeyboardButton("❓ Частые вопросы", callback_data="simple_calendar_faq")],
        [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        instructions, 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

@require_registration  
async def set_calendar_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить Calendar ID для руководителя."""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите Calendar ID после команды.\n"
            "Пример: `/setcalendar your.email@gmail.com`",
            parse_mode='Markdown'
        )
        return
    
    calendar_id = context.args[0].strip()
    user_id = update.effective_user.id
    
    # BULLETPROOF валидация calendar_id
    import re
    from html import escape
    
    # Sanitize input
    calendar_id = escape(calendar_id)
    
    # Validate format (email-like structure)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, calendar_id):
        await update.message.reply_text(
            "❌ **Неверный формат Calendar ID**\n\n"
            "Требования:\n"
            "• Должен быть валидным email\n"
            "• Только латинские буквы, цифры, точки, дефисы\n"
            "• Пример: `your.email@gmail.com`\n"
            "• Максимум 320 символов",
            parse_mode='Markdown'
        )
        return
    
    # Additional security checks
    if len(calendar_id) > 320:  # RFC 5321 limit
        await update.message.reply_text("❌ Calendar ID слишком длинный (максимум 320 символов)")
        return
        
    # Prevent common attack vectors
    dangerous_patterns = [
        r'[<>"\']',  # HTML/JS injection
        r'[;|&`$()]',  # Command injection
        r'\.\./',  # Path traversal
        r'script|javascript|vbscript',  # Script injection
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, calendar_id, re.IGNORECASE):
            await update.message.reply_text("❌ Calendar ID содержит недопустимые символы")
            return
    
    # BULLETPROOF: Атомарная транзакция с проверками
    with get_db() as db:
        try:
            # Start transaction
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user or user.role != UserRole.MANAGER:
                await update.message.reply_text("❌ Функция доступна только руководителям.")
                return
            
            # Check for conflicts with existing OAuth setup
            if user.oauth_credentials:
                await update.message.reply_text(
                    "⚠️ **Конфликт методов подключения**\n\n"
                    "Ваш календарь уже подключен через OAuth.\n"
                    "Для переключения на простой метод:\n\n"
                    "1. Отключите OAuth: `/disconnect_calendar`\n"
                    "2. Повторите команду `/setcalendar`",
                    parse_mode='Markdown'
                )
                return
            
            # Check if calendar already used by another user
            existing_user = db.query(User).filter(
                User.google_calendar_id == calendar_id,
                User.telegram_id != user_id
            ).first()
            
            if existing_user:
                await update.message.reply_text(
                    f"❌ **Calendar ID уже используется**\n\n"
                    f"Этот календарь уже подключен к другому пользователю.\n"
                    f"Каждый календарь может быть привязан только к одному руководителю."
                )
                return
            
            # Test calendar access BEFORE saving
            test_result = calendar_service.test_calendar_access(calendar_id)
            
            if test_result['success']:
                # ATOMIC UPDATE: все изменения в одной транзакции
                user.google_calendar_id = calendar_id
                user.calendar_connected = True
                user.oauth_credentials = None  # Clear OAuth if was set
                
                # Commit transaction
                db.commit()
                
                await update.message.reply_text(
                    f"✅ **Календарь успешно подключен!**\n\n"
                    f"📅 Календарь: `{test_result.get('summary', calendar_id)}`\n"
                    f"🎨 Цвет: {test_result.get('backgroundColor', 'стандартный')}\n"
                    f"🌍 Часовой пояс: {test_result.get('timeZone', settings.timezone)}\n\n"
                    f"Теперь вы можете:\n"
                    f"• Планировать встречи: /schedule\n"
                    f"• Просматривать встречи: /my_meetings\n"
                    f"• Проверять календарь: /calendar_status",
                    parse_mode='Markdown'
                )
            else:
                error_msg = test_result.get('error', 'Неизвестная ошибка')
                
                if 'not found' in error_msg.lower():
                    await update.message.reply_text(
                        f"❌ **Календарь не найден**\n\n"
                        f"Убедитесь что:\n"
                        f"1. Вы поделились календарем с:\n`{calendar_service.get_service_account_email()}`\n"
                        f"2. Calendar ID указан правильно: `{calendar_id}`\n"
                        f"3. Разрешения установлены на 'Вносить изменения'",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        f"❌ **Ошибка доступа к календарю**\n\n{error_msg}",
                        parse_mode='Markdown'
                    )
        
        except Exception as e:
            # BULLETPROOF: Single exception handler with proper rollback
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
            
            logger.error(f"Database error during calendar setup: {e}")
            await update.message.reply_text(
                "❌ **Критическая ошибка при настройке календаря**\n\n"
                "Транзакция отменена. Данные не изменены.\n"
                "Попробуйте позже или обратитесь к администратору."
            )

async def simple_calendar_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """FAQ для простого подключения календаря."""
    faq_text = """
❓ **Частые вопросы - Простое подключение**

**Q: Где найти Calendar ID?**
A: Google Calendar → Настройки календаря → раздел "Интеграция"

**Q: Какие разрешения давать боту?**
A: "Вносить изменения" для создания встреч или "Просматривать" для чтения

**Q: Можно использовать корпоративный календарь?**
A: Да, если у вас есть права на предоставление доступа

**Q: Как отозвать доступ?**
A: Google Calendar → Настройки → Удалите email бота из списка доступа

**Q: Бот видит все мои календари?**
A: Нет, только тот календарь, к которому вы дали доступ

**Q: Можно подключить несколько календарей?**
A: В текущей версии - только один основной календарь

**Q: Ошибка "Calendar not found"?**
A: Проверьте что поделились календарем и указали правильный ID

**Q: Нужен ли Google Workspace?**
A: Нет, работает с обычным Gmail аккаунтом
"""
    
    keyboard = [[InlineKeyboardButton("← Назад", callback_data="simple_calendar")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        faq_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

@require_registration
async def disconnect_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отключение календаря руководителя."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user or user.role != UserRole.MANAGER:
                await update.message.reply_text("❌ Функция доступна только руководителям.")
                return
            
            if not user.google_calendar_id and not user.oauth_credentials:
                await update.message.reply_text("ℹ️ Календарь не подключен.")
                return
            
            # Clear all calendar connections
            connection_type = "OAuth" if user.oauth_credentials else "Simple"
            user.google_calendar_id = None
            user.oauth_credentials = None
            user.calendar_connected = False
            
            db.commit()
            
            await update.message.reply_text(
                f"✅ **Календарь отключен**\n\n"
                f"Метод подключения: {connection_type}\n"
                f"Теперь вы можете подключить календарь заново:\n\n"
                f"• Простой метод: `/calendar_simple`\n"
                f"• OAuth метод: `/calendar`",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error disconnecting calendar: {e}")
            await update.message.reply_text("❌ Ошибка при отключении календаря.")