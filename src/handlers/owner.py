"""
Обработчики команд для владельцев бизнеса
"""
import logging
import traceback
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from database import get_db, User, UserRole, Department, UserStatus
from services.owner_service import OwnerService, WEEKDAYS, TIME_SLOTS
from utils.decorators import require_owner
from config import settings

logger = logging.getLogger(__name__)

# States для conversation handlers
(SET_AVAILABILITY_START, SET_AVAILABILITY_END, BLOCK_TIME_START, BLOCK_TIME_END, BLOCK_TIME_REASON) = range(5)

# Импортируем состояния из owner_slots
from handlers.owner_slots import (
    ADD_SLOT_DAY, ADD_SLOT_TIME, REMOVE_SLOT_DAY, REMOVE_SLOT_TIME, 
    SETUP_DAY, SETUP_SLOTS
)

@require_owner
async def owner_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню владельца"""
    keyboard = [
        [InlineKeyboardButton("📅 Управление доступностью", callback_data="owner_availability")],
        [InlineKeyboardButton("🚫 Заблокировать время", callback_data="owner_block_time")],
        [InlineKeyboardButton("👥 Управление руководителями", callback_data="owner_managers")],
        [InlineKeyboardButton("📊 Статистика встреч", callback_data="owner_stats")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="owner_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
👑 <b>Панель владельца</b>

Добро пожаловать в панель управления!

Здесь вы можете:
• Настроить свою доступность для встреч
• Заблокировать время когда вы недоступны
• Управлять руководителями отделов
• Просматривать статистику
"""
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

@require_owner
async def show_availability_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню управления временными слотами"""
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    availability_text = OwnerService.format_availability_text(user.id)
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить слот", callback_data="owner_add_slot")],
        [InlineKeyboardButton("❌ Удалить слот", callback_data="owner_remove_slot")],
        [InlineKeyboardButton("📝 Настроить день полностью", callback_data="owner_setup_day")],
        [InlineKeyboardButton("🔄 Обновить расписание", callback_data="owner_availability")],
        [InlineKeyboardButton("← Назад", callback_data="owner_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
📅 <b>Управление временными слотами</b>

{availability_text}

<i>💡 Каждый слот = 1 час созвона
Встречи возможны только когда свободны оба владельца</i>
"""
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def start_add_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс добавления слота"""
    keyboard = []
    
    # Показываем дни недели
    for i, day in enumerate(WEEKDAYS):
        keyboard.append([InlineKeyboardButton(day, callback_data=f"add_slot_day_{i}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📅 Выберите день недели для добавления слота:"
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    return ADD_SLOT_DAY

async def start_remove_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс удаления слота"""
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    keyboard = []
    
    # Показываем только дни, где есть слоты
    for i, day in enumerate(WEEKDAYS):
        slots = OwnerService.get_owner_time_slots(user.id, i)
        if slots:
            keyboard.append([InlineKeyboardButton(f"{day} ({', '.join(slots)})", callback_data=f"remove_slot_day_{i}")])
    
    if not keyboard:
        await update.callback_query.edit_message_text(
            "❌ У вас нет настроенных слотов для удаления.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="owner_availability")]])
        )
        return ConversationHandler.END
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "📅 Выберите день для удаления слота:",
        reply_markup=reply_markup
    )
    return REMOVE_SLOT_DAY

async def start_setup_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс полной настройки дня"""
    keyboard = []
    
    # Показываем дни недели
    for i, day in enumerate(WEEKDAYS):
        keyboard.append([InlineKeyboardButton(day, callback_data=f"setup_day_{i}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "📅 Выберите день для полной настройки слотов:",
        reply_markup=reply_markup
    )
    return SETUP_DAY

async def set_availability_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить день доступности"""
    query = update.callback_query
    day_index = int(query.data.split('_')[2])
    
    context.user_data['availability_day'] = day_index
    
    # Создаем клавиатуру с временными слотами для начала
    keyboard = []
    row = []
    for i, time_slot in enumerate(TIME_SLOTS):
        row.append(InlineKeyboardButton(time_slot, callback_data=f"start_time_{time_slot}"))
        if len(row) == 3:  # 3 кнопки в ряду
            keyboard.append(row)
            row = []
    
    if row:  # Добавляем оставшиеся кнопки
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"⏰ Выберите время начала работы в {WEEKDAYS[day_index]}:"
    
    await query.edit_message_text(text, reply_markup=reply_markup)
    return SET_AVAILABILITY_START

async def set_availability_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить время начала доступности"""
    query = update.callback_query
    start_time = query.data.split('_')[2]
    
    context.user_data['availability_start'] = start_time
    
    # Создаем клавиатуру с временными слотами для окончания (после времени начала)
    start_hour = int(start_time.split(':')[0])
    available_end_times = [slot for slot in TIME_SLOTS if int(slot.split(':')[0]) > start_hour]
    
    keyboard = []
    row = []
    for time_slot in available_end_times:
        row.append(InlineKeyboardButton(time_slot, callback_data=f"end_time_{time_slot}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    day_name = WEEKDAYS[context.user_data['availability_day']]
    text = f"⏰ Выберите время окончания работы в {day_name} (начало: {start_time}):"
    
    await query.edit_message_text(text, reply_markup=reply_markup)
    return SET_AVAILABILITY_END

async def set_availability_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить установку доступности"""
    query = update.callback_query
    end_time = query.data.split('_')[2]
    
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    day_index = context.user_data['availability_day']
    start_time = context.user_data['availability_start']
    
    # Сохраняем доступность
    success = OwnerService.set_owner_availability(user.id, day_index, start_time, end_time)
    
    if success:
        day_name = WEEKDAYS[day_index]
        text = f"✅ Доступность установлена!\n\n📅 {day_name}: {start_time} - {end_time}"
    else:
        text = "❌ Ошибка при сохранении доступности"
    
    keyboard = [[InlineKeyboardButton("📅 Управление доступностью", callback_data="owner_availability")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)
    
    # Очищаем данные
    context.user_data.clear()
    return ConversationHandler.END

async def show_remove_day_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню удаления дней"""
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    availability = OwnerService.get_owner_availability(user.id)
    
    if not availability:
        keyboard = [[InlineKeyboardButton("← Назад", callback_data="owner_availability")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "❌ У вас нет настроенных дней для удаления"
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        return
    
    keyboard = []
    for avail in availability:
        day_name = WEEKDAYS[avail.day_of_week]
        keyboard.append([InlineKeyboardButton(
            f"❌ {day_name} ({avail.start_time}-{avail.end_time})",
            callback_data=f"remove_day_{avail.day_of_week}"
        )])
    
    keyboard.append([InlineKeyboardButton("← Назад", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📅 Выберите день для удаления:"
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def remove_availability_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить день доступности"""
    query = update.callback_query
    day_index = int(query.data.split('_')[2])
    
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    success = OwnerService.remove_owner_availability(user.id, day_index)
    
    if success:
        day_name = WEEKDAYS[day_index]
        text = f"✅ Доступность удалена для {day_name}"
    else:
        text = "❌ Ошибка при удалении доступности"
    
    keyboard = [[InlineKeyboardButton("📅 Управление доступностью", callback_data="owner_availability")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

@require_owner
async def show_managers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню управления руководителями"""
    with get_db() as db:
        pending_managers = db.query(User).filter(User.role == UserRole.PENDING).count()
        approved_managers = db.query(User).filter(User.role == UserRole.MANAGER).count()
    
    keyboard = [
        [InlineKeyboardButton(f"⏳ Ожидают одобрения ({pending_managers})", callback_data="owner_pending")],
        [InlineKeyboardButton(f"✅ Одобренные руководители ({approved_managers})", callback_data="owner_approved")],
        [InlineKeyboardButton("📊 Статистика по отделам", callback_data="owner_dept_stats")],
        [InlineKeyboardButton("← Назад", callback_data="owner_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
👥 <b>Управление руководителями</b>

Здесь вы можете:
• Одобрить новых руководителей
• Просмотреть список одобренных
• Посмотреть статистику по отделам
"""
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def show_pending_managers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать ожидающих одобрения руководителей - делегируем в admin.py"""
    # Импортируем функцию из admin для избежания дублирования
    from handlers.admin import show_pending_users_callback
    # Устанавливаем правильный callback для возврата в меню владельца
    context.user_data['return_to'] = 'owner_managers'
    await show_pending_users_callback(update, context)

async def show_approved_managers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать одобренных руководителей"""
    with get_db() as db:
        managers = db.query(User).filter(User.role == UserRole.MANAGER).all()
        
        if not managers:
            keyboard = [[InlineKeyboardButton("← Назад", callback_data="owner_managers")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "📋 Пока нет одобренных руководителей"
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            return
        
        text = "✅ <b>Одобренные руководители:</b>\n\n"
        
        # Группируем по отделам
        departments = {}
        for manager in managers:
            dept = manager.department.value
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(manager)
        
        for dept, dept_managers in departments.items():
            text += f"🏢 <b>{dept}:</b>\n"
            for manager in dept_managers:
                status_emoji = "🟢" if manager.status == UserStatus.ACTIVE else "🔴"
                text += f"  {status_emoji} {manager.first_name} {manager.last_name}\n"
            text += "\n"
        
        keyboard = [[InlineKeyboardButton("← Назад", callback_data="owner_managers")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def approve_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Одобрить руководителя"""
    query = update.callback_query
    user_id = int(query.data.split('_')[2])
    
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await query.answer("❌ Пользователь не найден")
            return
        
        # Одобряем пользователя
        user.role = UserRole.MANAGER
        db.commit()
        
        # Уведомляем пользователя
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=f"🎉 <b>Поздравляем!</b>\n\n"
                     f"Ваша заявка одобрена владельцем бизнеса.\n"
                     f"👑 Вы теперь руководитель отдела: <b>{user.department.value}</b>\n\n"
                     f"📅 Используйте /schedule для назначения встреч с владельцами",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to notify approved user {user.id}: {e}")
        
        await query.edit_message_text(
            f"✅ <b>Руководитель одобрен!</b>\n\n"
            f"👤 {user.first_name} {user.last_name}\n"
            f"🏢 Отдел: {user.department.value}",
            parse_mode='HTML'
        )

async def reject_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отклонить руководителя - делегируем в admin.py"""
    from handlers.admin import reject_user_callback
    await reject_user_callback(update, context, int(update.callback_query.data.split('_')[2]))

async def handle_owner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для владельцев"""
    query = update.callback_query
    
    try:
        await query.answer()
        
        if query.data == "owner_menu":
            await owner_menu(update, context)
        elif query.data == "owner_availability":
            await show_availability_menu(update, context)
        elif query.data == "owner_add_slot":
            return await start_add_slot(update, context)
        elif query.data == "owner_remove_slot":
            return await start_remove_slot(update, context)
        elif query.data == "owner_setup_day":
            return await start_setup_day(update, context)
        elif query.data == "owner_remove_day":
            await show_remove_day_menu(update, context)
        elif query.data.startswith("remove_day_"):
            await remove_availability_day(update, context)
        elif query.data == "owner_managers":
            await show_managers_menu(update, context)
        elif query.data == "owner_pending":
            await show_pending_managers(update, context)
        elif query.data == "owner_approved":
            await show_approved_managers(update, context)
        elif query.data.startswith("owner_approve_"):
            await approve_manager(update, context)
        elif query.data.startswith("owner_reject_"):
            await reject_manager(update, context)
        else:
            logger.warning(f"Unhandled owner callback: {query.data}")
            # Очищаем user_data на всякий случай
            context.user_data.clear()
            await query.answer("⚠️ Устаревшая кнопка", show_alert=True)
            try:
                await query.edit_message_text(
                    "🔄 Меню обновлено. Используйте /owner для доступа к панели.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 Панель владельца", callback_data="owner_menu")]])
                )
            except:
                # Если не можем редактировать, отправляем новое
                await update.effective_chat.send_message(
                    "🔄 Используйте /owner для доступа к панели владельца."
                )
    except Exception as e:
        logger.error(f"Error in owner callback handler: {e}")
        # Очищаем user_data при любой ошибке
        context.user_data.clear()
        try:
            await query.answer("⚠️ Произошла ошибка. Меню обновлено.", show_alert=True)
            await update.effective_chat.send_message(
                "❌ Произошла ошибка. Используйте /owner для продолжения."
            )
        except:
            pass  # Ничего не можем сделать

def get_owner_conversation_handler():
    """Получить conversation handler для владельцев"""
    from handlers.owner_slots import (
        add_slot_day, add_slot_time, remove_slot_day, remove_slot_time,
        setup_day_select, toggle_slot, save_day_setup, handle_slot_exists,
        add_more_slot_same_day, ADD_SLOT_DAY, ADD_SLOT_TIME, REMOVE_SLOT_DAY, 
        REMOVE_SLOT_TIME, SETUP_DAY, SETUP_SLOTS
    )
    
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_add_slot, pattern="^owner_add_slot$"),
            CallbackQueryHandler(start_remove_slot, pattern="^owner_remove_slot$"),
            CallbackQueryHandler(start_setup_day, pattern="^owner_setup_day$")
        ],
        states={
            ADD_SLOT_DAY: [CallbackQueryHandler(add_slot_day, pattern="^add_slot_day_")],
            ADD_SLOT_TIME: [
                CallbackQueryHandler(add_slot_time, pattern="^add_slot_time_"),
                CallbackQueryHandler(handle_slot_exists, pattern="^slot_exists_"),
                CallbackQueryHandler(add_more_slot_same_day, pattern="^add_more_slot_same_day$")
            ],
            REMOVE_SLOT_DAY: [CallbackQueryHandler(remove_slot_day, pattern="^remove_slot_day_")],
            REMOVE_SLOT_TIME: [
                CallbackQueryHandler(remove_slot_time, pattern="^remove_slot_time_"),
                CallbackQueryHandler(remove_slot_time, pattern="^remove_all_day_slots$")
            ],
            SETUP_DAY: [CallbackQueryHandler(setup_day_select, pattern="^setup_day_")],
            SETUP_SLOTS: [
                CallbackQueryHandler(toggle_slot, pattern="^toggle_slot_"),
                CallbackQueryHandler(save_day_setup, pattern="^save_day_setup$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(show_availability_menu, pattern="^owner_availability$"),
            CallbackQueryHandler(owner_menu, pattern="^owner_menu$"),
            CallbackQueryHandler(handle_stale_conversation, pattern=".*"),  # Ловит все остальные callback'и
            CommandHandler('owner', cancel_and_redirect_owner),
            CommandHandler('cancel', cancel_conversation),
            CommandHandler('admin', cancel_and_redirect_admin),
            CommandHandler('start', cancel_and_redirect_start),
            CommandHandler('help', cancel_and_redirect_help),
            CommandHandler('schedule', cancel_and_redirect_schedule),
            CommandHandler('my_meetings', cancel_and_redirect_meetings),
            MessageHandler(filters.ALL, handle_stale_conversation)  # Ловит все сообщения
        ],
        per_chat=True,
        per_user=True,
    )

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить текущий conversation"""
    await update.message.reply_text(
        "❌ Операция отменена. Используйте /owner для доступа к панели владельца."
    )
    context.user_data.clear()
    return ConversationHandler.END

# Функции для правильного перенаправления из ConversationHandler
async def cancel_and_redirect_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить conversation и перейти в /owner"""
    context.user_data.clear()
    await owner_menu(update, context)
    return ConversationHandler.END

async def cancel_and_redirect_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить conversation и перейти в /admin"""
    context.user_data.clear()
    from handlers.admin import admin_menu
    await admin_menu(update, context)
    return ConversationHandler.END

async def cancel_and_redirect_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить conversation и перейти в /start"""
    context.user_data.clear()
    from handlers.common import start_command
    await start_command(update, context)
    return ConversationHandler.END

async def cancel_and_redirect_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить conversation и перейти в /help"""
    context.user_data.clear()
    from handlers.common import help_command
    await help_command(update, context)
    return ConversationHandler.END

async def cancel_and_redirect_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить conversation и перейти в /schedule"""
    context.user_data.clear()
    from handlers.manager import show_available_slots
    await show_available_slots(update, context)
    return ConversationHandler.END

async def cancel_and_redirect_meetings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить conversation и перейти в /my_meetings"""
    context.user_data.clear()
    from handlers.manager import show_my_meetings
    await show_my_meetings(update, context)
    return ConversationHandler.END

async def handle_stale_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка 'застрявших' состояний ConversationHandler"""
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.answer(
            "⚠️ Устаревшее меню. Обновляю...",
            show_alert=True
        )
        try:
            await update.callback_query.edit_message_text(
                "🔄 Меню обновлено. Используйте /owner для доступа к панели."
            )
        except:
            # Если не можем редактировать, отправляем новое сообщение
            await update.effective_chat.send_message(
                "🔄 Меню обновлено. Используйте /owner для доступа к панели."
            )
    else:
        await update.message.reply_text(
            "⚠️ Настройка слотов прервана. Используйте /owner для продолжения."
        )


@require_owner
async def connect_owner_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подключение Google Calendar для владельцев через OAuth."""
    user_id = update.effective_user.id
    logger.info(f"🔍 DEBUG: connect_owner_calendar started for owner {user_id}")
    
    try:
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if user.role != UserRole.OWNER:
                await update.message.reply_text(
                    "❌ Данная функция доступна только владельцам."
                )
                return
            
            # Check if calendar is already connected
            if user.oauth_credentials and user.google_calendar_id:
                await update.message.reply_text(
                    f"✅ **Google Calendar уже подключен!**\n\n"
                    f"📧 Календарь: {user.email}\n"
                    f"🎉 Владельцы могут создавать встречи с Google Meet!\n\n"
                    f"Чтобы переподключить календарь, нажмите кнопку ниже.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Переподключить календарь", callback_data="reconnect_owner_calendar")],
                        [InlineKeyboardButton("← Назад в меню", callback_data="owner_menu")]
                    ]),
                    parse_mode='Markdown'
                )
                return
            
            instructions = """
🔗 **Подключение Google Calendar для владельца**

Подключив календарь, вы получите:

🎯 **Возможности:**
• Автоматическое создание встреч в вашем календаре
• Google Meet ссылки для всех встреч
• Приглашения менеджеров как участников
• Напоминания перед встречами

📋 **Процесс подключения:**
1️⃣ Нажмите "Подключить Google Calendar"
2️⃣ Войдите в ваш Google аккаунт
3️⃣ Разрешите доступ к календарю
4️⃣ Вернитесь в бот для подтверждения

🔒 **Безопасность:**
• Официальный OAuth 2.0 Google
• Доступ только к календарю
• Можно отозвать в любой момент
"""
            
            # Generate OAuth URL
            logger.info(f"🔍 DEBUG: Starting OAuth service import for owner {user_id}")
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
                        [InlineKeyboardButton("← Назад в меню", callback_data="owner_menu")]
                    ]
                    logger.info(f"🔍 DEBUG: OAuth not configured path - message prepared")
                else:
                    logger.info(f"🔍 DEBUG: Generating OAuth URL for owner {user_id}")
                    oauth_url = oauth_service.generate_auth_url(user_id)
                    logger.info(f"🔍 DEBUG: OAuth URL result: {'Generated' if oauth_url else 'None'}")
                    
                    if oauth_url:
                        logger.info(f"🔍 DEBUG: OAuth URL generated successfully, length: {len(oauth_url)}")
                        keyboard = [
                            [InlineKeyboardButton("🔗 Подключить Google Calendar", url=oauth_url)],
                            [InlineKeyboardButton("← Назад в меню", callback_data="owner_menu")]
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
                            [InlineKeyboardButton("← Назад в меню", callback_data="owner_menu")]
                        ]
                        logger.info(f"🔍 DEBUG: OAuth URL failed path - message prepared")
            except Exception as oauth_error:
                logger.error(f"🔍 DEBUG: OAuth service error for owner {user_id}: {type(oauth_error).__name__}: {oauth_error}")
                logger.error(f"🔍 DEBUG: OAuth traceback: {traceback.format_exc()}")
                instructions += "\n\n❌ **Проблема с настройкой OAuth**\n"
                instructions += "Администратор должен проверить конфигурацию.\n\n"
                keyboard = [
                    [InlineKeyboardButton("← Назад в меню", callback_data="owner_menu")]
                ]
                logger.info(f"🔍 DEBUG: OAuth error path - message prepared")
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            logger.info(f"🔍 DEBUG: Sending response to owner {user_id}")
            logger.info(f"🔍 DEBUG: Message length: {len(instructions)} characters")
            logger.info(f"🔍 DEBUG: Keyboard buttons count: {len(keyboard)}")
            
            try:
                await update.message.reply_text(
                    instructions, 
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                logger.info(f"🔍 DEBUG: Response sent successfully to owner {user_id}")
            except Exception as send_error:
                logger.error(f"🔍 DEBUG: Failed to send message to owner {user_id}: {type(send_error).__name__}: {send_error}")
                # Try sending without markdown formatting but keep the keyboard
                try:
                    clean_instructions = instructions.replace('**', '').replace('`', '').replace('*', '')
                    await update.message.reply_text(
                        clean_instructions,
                        reply_markup=reply_markup
                    )
                    logger.info(f"🔍 DEBUG: Response sent without markdown formatting but with keyboard")
                except Exception as fallback_error:
                    logger.error(f"🔍 DEBUG: Fallback send also failed: {type(fallback_error).__name__}: {fallback_error}")
                    # Last resort - send without keyboard
                    try:
                        await update.message.reply_text(clean_instructions)
                        logger.info(f"🔍 DEBUG: Response sent without markdown and without keyboard")
                    except Exception as final_error:
                        logger.error(f"🔍 DEBUG: All send attempts failed: {type(final_error).__name__}: {final_error}")
                        raise send_error
        
    except Exception as main_error:
        error_type = type(main_error).__name__
        logger.error(f"🔍 DEBUG: Exception in connect_owner_calendar for owner {user_id}: {error_type}: {main_error}")
        logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        
        # Provide user-friendly error message
        try:
            await update.message.reply_text(
                f"❌ **Ошибка подключения календаря**\n\n"
                f"Произошла техническая ошибка: `{error_type}`\n\n"
                f"Обратитесь к администратору.",
                parse_mode='Markdown'
            )
        except Exception as reply_error:
            logger.error(f"Failed to send error message to owner {user_id}: {reply_error}")
            raise main_error


async def handle_owner_calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback для календаря владельца."""
    from utils.telegram_safe import telegram_safe
    
    query = update.callback_query
    await query.answer()
    
    @telegram_safe(max_retries=1)
    async def safe_edit_message(text, reply_markup=None):
        """Safe wrapper for editing messages."""
        return await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    if query.data == "connect_owner_calendar":
        # Перенаправляем на основную функцию подключения
        fake_update = type('obj', (object,), {
            'effective_user': query.from_user,
            'message': type('obj', (object,), {
                'reply_text': safe_edit_message
            })()
        })()
        await connect_owner_calendar(fake_update, context)
    elif query.data == "reconnect_owner_calendar":
        # Переподключение календаря  
        fake_update = type('obj', (object,), {
            'effective_user': query.from_user,
            'message': type('obj', (object,), {
                'reply_text': safe_edit_message
            })()
        })()
        await connect_owner_calendar(fake_update, context)
    
    return ConversationHandler.END