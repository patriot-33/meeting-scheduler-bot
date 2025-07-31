"""
Обработчики для подключения Google Calendar руководителями
"""
import logging
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_db, User, UserRole
from utils.decorators import require_registration
from config import settings

logger = logging.getLogger(__name__)

@require_registration
async def connect_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подключение Google Calendar через OAuth для руководителей."""
    user_id = update.effective_user.id
    logger.info(f"🔍 DEBUG: connect_calendar started for user {user_id}")
    
    try:
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if user.role != UserRole.MANAGER:
                await update.message.reply_text(
                    "❌ Данная функция доступна только руководителям отделов."
                )
                return
            
            # Check if calendar is already connected
            if user.oauth_credentials and user.google_calendar_id:
                await update.message.reply_text(
                    f"✅ **Google Calendar уже подключен!**\n\n"
                    f"📧 Календарь: {user.email}\n"
                    f"🎉 Вы можете планировать встречи командой /schedule\n\n"
                    f"Чтобы переподключить календарь, нажмите кнопку ниже.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Переподключить календарь", callback_data="reconnect_calendar")],
                        [InlineKeyboardButton("📅 Запланировать встречу", callback_data="schedule_meeting")]
                    ]),
                    parse_mode='Markdown'
                )
                return
            
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
                logger.info(f"🔍 DEBUG: OAuth service is_configured: {oauth_service.is_oauth_configured}")
            
                # Pre-check OAuth configuration 
                if not oauth_service.is_oauth_configured:
                    logger.info(f"🔍 DEBUG: OAuth not configured, showing setup instructions")
                    instructions += "\n\n❌ **OAuth Client не настроен**\n"
                    instructions += "Администратор должен добавить:\n"
                    instructions += "• `GOOGLE_OAUTH_CLIENT_JSON` переменную окружения\n"
                    instructions += "• Или файл `oauth_client_key.json`\n\n"
                    instructions += "💡 Используйте Google Cloud Console:\n"
                    instructions += "1. APIs & Services → Credentials\n"
                    instructions += "2. Create OAuth 2.0 Client → Web Application\n"
                    webhook_url = settings.webhook_url or "YOUR_WEBHOOK_URL"
                    instructions += f"3. Add redirect URI: `{webhook_url}/oauth/callback`"
                    
                    keyboard = [
                        [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                        [InlineKeyboardButton("📧 Сообщить email владельцу", callback_data="send_email_to_owner")],
                        [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
                    ]
                    logger.info(f"🔍 DEBUG: OAuth not configured path - message prepared")
                else:
                    logger.info(f"🔍 DEBUG: Generating OAuth URL for user {user_id}")
                    oauth_url = oauth_service.generate_auth_url(user_id)
                    logger.info(f"🔍 DEBUG: OAuth URL result: {'Generated' if oauth_url else 'None'}")
                    
                    if oauth_url:
                        logger.info(f"🔍 DEBUG: OAuth URL generated successfully, length: {len(oauth_url)}")
                        keyboard = [
                            [InlineKeyboardButton("🔗 Подключить Google Calendar", url=oauth_url)],
                            [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                            [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
                        ]
                        logger.info(f"🔍 DEBUG: OAuth configured path - message with URL prepared")
                    else:
                        logger.info(f"🔍 DEBUG: OAuth URL generation failed")
                        # OAuth URL generation failed
                        instructions += "\n\n❌ **Ошибка генерации OAuth URL**\n"
                        instructions += "Проверьте:\n"
                        instructions += "• Корректность OAuth Client JSON\n"
                        instructions += "• Настройку WEBHOOK_URL\n"
                        instructions += "• Redirect URI в Google Console"
                        keyboard = [
                            [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                            [InlineKeyboardButton("📧 Сообщить email владельцу", callback_data="send_email_to_owner")],
                            [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
                        ]
                        logger.info(f"🔍 DEBUG: OAuth URL failed path - message prepared")
            except Exception as oauth_error:
                logger.error(f"🔍 DEBUG: OAuth service error for user {user_id}: {type(oauth_error).__name__}: {oauth_error}")
                logger.error(f"🔍 DEBUG: OAuth traceback: {traceback.format_exc()}")
                instructions += f"\n\n❌ **Критическая ошибка OAuth**\n`{str(oauth_error)}`\n\nОбратитесь к администратору."
                keyboard = [
                    [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                    [InlineKeyboardButton("📧 Сообщить email владельцу", callback_data="send_email_to_owner")],
                    [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            logger.info(f"🔍 DEBUG: Sending response to user {user_id}")
            logger.info(f"🔍 DEBUG: Message length: {len(instructions)} characters")
            logger.info(f"🔍 DEBUG: Keyboard buttons count: {len(keyboard)}")
            
            try:
                await update.message.reply_text(
                    instructions, 
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                logger.info(f"🔍 DEBUG: Response sent successfully to user {user_id}")
            except Exception as send_error:
                logger.error(f"🔍 DEBUG: Failed to send message to user {user_id}: {type(send_error).__name__}: {send_error}")
                # Try sending without markdown formatting
                try:
                    await update.message.reply_text(
                        instructions.replace('**', '').replace('`', ''),
                        reply_markup=reply_markup
                    )
                    logger.info(f"🔍 DEBUG: Response sent without markdown formatting")
                except Exception as fallback_error:
                    logger.error(f"🔍 DEBUG: Fallback send also failed: {type(fallback_error).__name__}: {fallback_error}")
                    raise send_error
        
    except Exception as main_error:
        error_type = type(main_error).__name__
        logger.error(f"🔍 DEBUG: Exception in connect_calendar for user {user_id}: {error_type}: {main_error}")
        logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        
        # Provide user-friendly error message instead of generic network error
        try:
            await update.message.reply_text(
                f"❌ **Ошибка подключения календаря**\n\n"
                f"Произошла техническая ошибка: `{error_type}`\n\n"
                f"Обратитесь к администратору или попробуйте:\n"
                f"• Команду `/calendar_simple` для простого подключения\n"
                f"• Команду `/email ваш_email@gmail.com` для ручного добавления",
                parse_mode='Markdown'
            )
        except Exception as reply_error:
            logger.error(f"Failed to send error message to user {user_id}: {reply_error}")
            # If we can't send a custom message, let the global error handler take over
            raise main_error

async def handle_calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback для календаря."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "connect_calendar":
        # Перенаправляем на основную функцию подключения
        # Создаем фиктивный update объект для команды
        fake_update = type('obj', (object,), {
            'effective_user': query.from_user,
            'message': type('obj', (object,), {
                'reply_text': query.edit_message_text
            })()
        })()
        await connect_calendar(fake_update, context)
    elif query.data == "reconnect_calendar":
        # Переподключение календаря
        fake_update = type('obj', (object,), {
            'effective_user': query.from_user,
            'message': type('obj', (object,), {
                'reply_text': query.edit_message_text
            })()
        })()
        await connect_calendar(fake_update, context)
    elif query.data == "send_email_to_owner":
        await send_email_prompt(update, context)
    elif query.data == "calendar_faq":
        await show_calendar_faq(update, context)

async def send_email_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос email для отправки владельцу."""
    text = """
📧 **Отправка email владельцу**

Введите ваш Google email в формате:
`ваше_имя@gmail.com` или `ваше_имя@компания.ru`

Владелец получит уведомление и добавит вас в календарь.

💡 Используйте команду:
`/email ваш_email@gmail.com`
"""
    
    keyboard = [[InlineKeyboardButton("← Назад", callback_data="connect_calendar")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def save_manager_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить email менеджера и уведомить владельца."""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите email после команды.\n"
            "Пример: `/email john.doe@gmail.com`",
            parse_mode='Markdown'
        )
        return
    
    email = context.args[0]
    
    # Простая проверка email
    if '@' not in email or '.' not in email.split('@')[1]:
        await update.message.reply_text(
            "❌ Неверный формат email.\n"
            "Пример: `john.doe@gmail.com`",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user or user.role != UserRole.MANAGER:
            await update.message.reply_text("❌ Функция доступна только руководителям.")
            return
        
        # Сохраняем email
        user.email = email
        db.commit()
        
        # Уведомляем владельцев
        owners = db.query(User).filter(User.role == UserRole.OWNER).all()
        
        notification_text = f"""
📧 **Новый email руководителя**

👤 {user.first_name} {user.last_name}
🏢 Отдел: {user.department.value}
📧 Email: {email}

Руководитель запросил подключение к Google Calendar.
Добавьте этот email в календарь для участия во встречах.
"""
        
        for owner in owners:
            try:
                await context.bot.send_message(
                    chat_id=owner.telegram_id,
                    text=notification_text,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify owner {owner.id}: {e}")
    
    await update.message.reply_text(
        f"✅ Email сохранен: `{email}`\n\n"
        f"Владельцы получили уведомление и добавят вас в календарь.\n"
        f"Вы получите приглашение на указанную почту.",
        parse_mode='Markdown'
    )

async def show_calendar_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать частые вопросы по календарю."""
    faq_text = """
❓ **Частые вопросы по Google Calendar**

**Q: Нужен ли платный аккаунт Google?**
A: Нет, достаточно бесплатного аккаунта Gmail.

**Q: Могу ли я использовать корпоративную почту?**
A: Да, если она подключена к Google Workspace.

**Q: Как изменить email?**
A: Используйте команду `/email новый_email@gmail.com`

**Q: Не приходит приглашение**
A: Проверьте папку "Спам" и правильность email.

**Q: Можно ли подключиться с телефона?**
A: Да, через приложение Google Meet или браузер.

**Q: Нужна ли камера для встречи?**
A: Желательно, но не обязательно. Можно участвовать только с микрофоном.

**Q: Как отменить участие во встрече?**
A: Используйте команду `/my_meetings` и отмените встречу.

**Q: Встреча не отображается в календаре**
A: Убедитесь, что приняли приглашение в письме.
"""
    
    keyboard = [[InlineKeyboardButton("← Назад", callback_data="connect_calendar")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        faq_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )