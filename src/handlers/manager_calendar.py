"""
Обработчики для подключения Google Calendar руководителями
"""
import logging
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from database import get_db, User, UserRole
from utils.decorators import require_registration
from utils.telegram_safe import safe_send_message, safe_context_send
from config import settings

logger = logging.getLogger(__name__)

# safe_send_message теперь импортируется из utils.telegram_safe

@require_registration
async def connect_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подключение Google Calendar через OAuth для руководителей."""
    user_id = update.effective_user.id
    logger.info(f"🔍 DEBUG: connect_calendar started for user {user_id}")
    
    # Defensive fix for UnboundLocalError: ensure get_db is explicitly available
    from database import get_db as db_context_manager
    
    try:
        with db_context_manager() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            logger.info(f"🔍 DEBUG: User found - ID: {user.telegram_id}, role: {user.role.value}, calendar: {user.google_calendar_id}")
            
            # Allow both MANAGER and OWNER to connect calendars via OAuth
            if user.role not in [UserRole.MANAGER, UserRole.OWNER]:
                logger.warning(f"❌ DEBUG: Access denied - user role is {user.role.value}, expected MANAGER or OWNER")
                await safe_send_message(update, "❌ Данная функция доступна только руководителям и владельцам.")
                return
            
            # Check calendar connection status
            calendar_status = "❌ Не подключен"
            status_icon = "🔴"
            status_details = ""
            
            if user.oauth_credentials and user.google_calendar_id:
                # Проверим реальный доступ к календарю
                from services.google_calendar import google_calendar_service as calendar_service
                calendar_access_test = None
                
                if calendar_service.is_available:
                    try:
                        calendar_access_test = calendar_service.test_calendar_access(user.google_calendar_id)
                    except Exception as e:
                        logger.warning(f"Failed to test calendar access: {e}")
                
                if calendar_access_test and calendar_access_test['success']:
                    calendar_status = "✅ Подключен"
                    status_icon = "🟢"
                    status_details = f"\n📧 Email: {user.email or 'не указан'}\n📅 Calendar ID: {user.google_calendar_id[:30]}...\n🎨 Название: {calendar_access_test.get('summary', 'N/A')}"
                    
                    # Обновляем статус в БД, если он был неправильным
                    if not user.calendar_connected:
                        user.calendar_connected = True
                        # Сохраняем в контексте транзакции (db уже открыт в текущем контексте)
                        try:
                            # commit будет автоматически при выходе из with get_db()
                            pass
                        except:
                            pass
                elif calendar_access_test and not calendar_access_test['success']:
                    calendar_status = "❌ Нет доступа к календарю"
                    status_icon = "🔴"
                    error_msg = calendar_access_test.get('error', 'Unknown error')
                    if 'not found' in error_msg.lower():
                        status_details = f"\n📧 Email: {user.email or 'не указан'}\n📅 Calendar ID: {user.google_calendar_id}\n❌ Календарь не найден или не предоставлен доступ\n\n💡 **Требуется настройка доступа:**\n1. Откройте Google Calendar\n2. Поделитесь календарем с:\n   `meeting-bot-service@meeting-scheduler-bot-467415.iam.gserviceaccount.com`\n3. Установите права: 'Вносить изменения'"
                    else:
                        status_details = f"\n📧 Email: {user.email or 'не указан'}\n📅 Calendar ID: {user.google_calendar_id}\n❌ Ошибка доступа: {error_msg}"
                    
                    # Обновляем статус в БД
                    if user.calendar_connected:
                        user.calendar_connected = False
                else:
                    calendar_status = "⚠️ Требуется переподключение"
                    status_icon = "🟡"
                    status_details = "\n❗ Обнаружены сохраненные данные, но статус подключения неизвестен\n💡 Попробуйте переподключить календарь"
            elif user.email:
                status_details = f"\n📧 Email сохранен: {user.email}\n⏳ Ожидает подключения через OAuth"
                
            status_message = f"""📊 **Статус Google Calendar**

{status_icon} Статус: {calendar_status}{status_details}

💡 Для планирования встреч необходим подключенный календарь."""
            
            # Show different buttons based on REAL connection status
            calendar_really_connected = (calendar_access_test and calendar_access_test['success']) if 'calendar_access_test' in locals() else user.calendar_connected
            
            if calendar_really_connected:
                keyboard = [
                    [InlineKeyboardButton("📅 Запланировать встречу", callback_data="schedule_meeting")],
                    [InlineKeyboardButton("🔄 Переподключить календарь", callback_data="reconnect_calendar")],
                    [InlineKeyboardButton("🗑 Отключить календарь", callback_data="disconnect_calendar")],
                    [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")]
                ]
                await safe_send_message(
                    update,
                    status_message,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            elif user.oauth_credentials:
                # Has credentials but not connected - different options based on problem
                if 'calendar_access_test' in locals() and calendar_access_test and not calendar_access_test['success']:
                    # Calendar exists but no access - sharing problem
                    keyboard = [
                        [InlineKeyboardButton("📋 Инструкция по настройке доступа", callback_data="calendar_sharing_guide")],
                        [InlineKeyboardButton("📅 Использовать простое подключение", callback_data="switch_to_simple_calendar")],
                        [InlineKeyboardButton("🔄 Переподключить через OAuth", callback_data="reconnect_calendar")],
                        [InlineKeyboardButton("🗑 Очистить данные", callback_data="disconnect_calendar")]
                    ]
                    extra_message = "\n\n❌ **Нет доступа к календарю**\nТребуется настроить доступ или использовать другой метод подключения."
                else:
                    # General reconnection needed
                    keyboard = [
                        [InlineKeyboardButton("🔄 Переподключить календарь", callback_data="reconnect_calendar")],
                        [InlineKeyboardButton("🆕 Подключить заново", callback_data="connect_calendar_fresh")],
                        [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")]
                    ]
                    extra_message = "\n\n⚠️ **Требуется переподключение календаря**"
                
                await safe_send_message(
                    update,
                    status_message + extra_message,
                    reply_markup=InlineKeyboardMarkup(keyboard)
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
                    instructions += "1. APIs & Services -> Credentials\n"
                    instructions += "2. Create OAuth 2.0 Client -> Web Application\n"
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
                instructions += "\n\n❌ **Проблема с настройкой OAuth**\n"
                instructions += "Администратор должен проверить конфигурацию.\n\n"
                instructions += "Альтернативные способы подключения:\n"
                instructions += "• /calendar_simple - простое подключение\n"
                instructions += "• /email ваш_email@gmail.com - добавление вручную"
                keyboard = [
                    [InlineKeyboardButton("❓ Частые вопросы", callback_data="calendar_faq")],
                    [InlineKeyboardButton("📧 Сообщить email владельцу", callback_data="send_email_to_owner")],
                    [InlineKeyboardButton("← Назад", callback_data="nav_main_menu")]
                ]
                logger.info(f"🔍 DEBUG: OAuth error path - message prepared")
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            logger.info(f"🔍 DEBUG: Sending response to user {user_id}")
            logger.info(f"🔍 DEBUG: Message length: {len(instructions)} characters")
            logger.info(f"🔍 DEBUG: Keyboard buttons count: {len(keyboard)}")
            
            try:
                await safe_send_message(update,
                    instructions, 
                    reply_markup=reply_markup,
                    parse_mode='Markdown',
                    force_send=True  # Allow duplicate for calendar setup
                )
                logger.info(f"🔍 DEBUG: Response sent successfully to user {user_id}")
            except Exception as send_error:
                logger.error(f"🔍 DEBUG: Failed to send message to user {user_id}: {type(send_error).__name__}: {send_error}")
                # Try sending without markdown formatting but keep the keyboard
                try:
                    clean_instructions = instructions.replace('**', '').replace('`', '').replace('*', '')
                    await safe_send_message(update,
                        clean_instructions,
                        reply_markup=reply_markup,
                        force_send=True
                    )
                    logger.info(f"🔍 DEBUG: Response sent without markdown formatting but with keyboard")
                except Exception as fallback_error:
                    logger.error(f"🔍 DEBUG: Fallback send also failed: {type(fallback_error).__name__}: {fallback_error}")
                    # Last resort - send without keyboard
                    try:
                        await safe_send_message(update, clean_instructions, force_send=True)
                        logger.info(f"🔍 DEBUG: Response sent without markdown and without keyboard")
                    except Exception as final_error:
                        logger.error(f"🔍 DEBUG: All send attempts failed: {type(final_error).__name__}: {final_error}")
                        raise send_error
        
    except Exception as main_error:
        error_type = type(main_error).__name__
        logger.error(f"🔍 DEBUG: Exception in connect_calendar for user {user_id}: {error_type}: {main_error}")
        logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        
        # Provide user-friendly error message instead of generic network error
        try:
            await safe_send_message(update,
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
        # Используем обычный update с callback_query
        await connect_calendar(update, context)
    elif query.data == "reconnect_calendar":
        # Переподключение календаря
        await connect_calendar(update, context)
    elif query.data == "send_email_to_owner":
        await send_email_prompt(update, context)
    elif query.data == "calendar_faq":
        await show_calendar_faq(update, context)
    elif query.data == "disconnect_calendar":
        await disconnect_calendar_handler(update, context)
    elif query.data == "connect_calendar_fresh":
        # Same as connect_calendar but force fresh connection
        await connect_calendar(update, context)
    elif query.data == "calendar_sharing_guide":
        await show_calendar_sharing_guide(update, context)
    elif query.data == "switch_to_simple_calendar":
        await switch_to_simple_calendar(update, context)

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
    
    await safe_send_message(update,
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def save_manager_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить email менеджера и уведомить владельца."""
    if not context.args:
        await safe_send_message(update,
            "❌ Укажите email после команды.\n"
            "Пример: `/email john.doe@gmail.com`",
            parse_mode='Markdown'
        )
        return
    
    email = context.args[0]
    
    # Простая проверка email
    if '@' not in email or '.' not in email.split('@')[1]:
        await safe_send_message(update,
            "❌ Неверный формат email.\n"
            "Пример: `john.doe@gmail.com`",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    
    # Defensive fix for potential UnboundLocalError
    from database import get_db as db_context_manager
    with db_context_manager() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user or user.role != UserRole.MANAGER:
            await safe_send_message(update,"❌ Функция доступна только руководителям.")
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
                await safe_context_send(
                    context,
                    chat_id=owner.telegram_id,
                    text=notification_text,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify owner {owner.id}: {e}")
    
    await safe_send_message(update,
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
    
    await safe_send_message(update,
        faq_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def disconnect_calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отключить календарь."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Defensive fix for potential UnboundLocalError
    from database import get_db as db_context_manager
    with db_context_manager() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Allow both MANAGER and OWNER to disconnect calendars
        if user and user.role in [UserRole.MANAGER, UserRole.OWNER]:
            # Clear calendar connection
            user.oauth_credentials = None
            user.google_calendar_id = None
            user.calendar_connected = False
            db.commit()
            
            role_name = "владельца" if user.role == UserRole.OWNER else "руководителя"
            await safe_send_message(update,
                f"✅ **Календарь отключен**\n\n"
                f"Ваши данные Google Calendar были удалены из системы.\n"
                f"Вы можете подключить календарь заново в любое время командой /calendar",
                parse_mode='Markdown'
            )
        else:
            await safe_send_message(update,"❌ Ошибка при отключении календаря")

async def show_calendar_sharing_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать подробную инструкцию по настройке доступа к календарю."""
    from services.google_calendar import google_calendar_service as calendar_service
    service_email = calendar_service.get_service_account_email() or "service-account@example.com"
    
    guide_text = f"""
📋 **Инструкция по настройке доступа к календарю**

Ваш календарь найден, но у бота нет доступа к нему.

🔧 **Пошаговая настройка:**

1️⃣ **Откройте Google Calendar**
   • Перейдите на https://calendar.google.com
   • Найдите нужный календарь в левой панели

2️⃣ **Откройте настройки календаря**
   • Нажмите на 3 точки рядом с календарем
   • Выберите "Настройки и общий доступ"

3️⃣ **Добавьте доступ боту**
   • В разделе "Предоставить доступ определенным пользователям"
   • Нажмите "+ Добавить пользователей"
   • Введите email бота:
   
   📧 `{service_email}`
   
   • Установите разрешения: **"Вносить изменения"**
   • Нажмите "Отправить"

4️⃣ **Проверка**
   • Вернитесь в бот
   • Нажмите /calendar для проверки статуса

🔒 **Безопасность:**
• Бот получит доступ только к указанному календарю
• Вы можете отозвать доступ в любой момент
• Доступ используется только для создания встреч

❓ **Альтернативы:**
• Используйте простое подключение: /calendar_simple
• Переподключитесь через OAuth заново
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Копировать email бота", callback_data=f"copy_service_email:{service_email}")],
        [InlineKeyboardButton("🔄 Проверить доступ", callback_data="connect_calendar")],
        [InlineKeyboardButton("📅 Простое подключение", callback_data="switch_to_simple_calendar")],
        [InlineKeyboardButton("← Назад", callback_data="connect_calendar")]
    ]
    
    await safe_send_message(update, guide_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def switch_to_simple_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключиться на простое подключение календаря."""
    from handlers.manager_calendar_simple import simple_calendar_connect
    
    # Очистим старые OAuth данные
    user_id = update.effective_user.id
    
    # Defensive fix for potential UnboundLocalError
    from database import get_db as db_context_manager
    with db_context_manager() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if user:
            user.oauth_credentials = None
            user.calendar_connected = False
            # Сохраняем google_calendar_id если есть
            db.commit()
    
    # Показываем инструкцию для простого подключения
    await simple_calendar_connect(update, context)