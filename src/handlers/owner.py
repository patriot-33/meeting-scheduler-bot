"""
Обработчики команд для владельцев бизнеса
"""
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from src.database import get_db, User, UserRole, Department, UserStatus
from src.services.owner_service import OwnerService, WEEKDAYS, TIME_SLOTS
from src.utils.decorators import require_owner
from src.config import settings

logger = logging.getLogger(__name__)

# States для conversation handlers
(SET_AVAILABILITY_START, SET_AVAILABILITY_END, BLOCK_TIME_START, BLOCK_TIME_END, BLOCK_TIME_REASON) = range(5)

# Импортируем состояния из owner_slots
from src.handlers.owner_slots import (
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
    """Показать ожидающих одобрения руководителей"""
    with get_db() as db:
        pending_users = db.query(User).filter(User.role == UserRole.PENDING).all()
        
        if not pending_users:
            keyboard = [[InlineKeyboardButton("← Назад", callback_data="owner_managers")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "✅ Нет руководителей, ожидающих одобрения"
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            return
        
        text = "⏳ <b>Ожидают одобрения:</b>\n\n"
        keyboard = []
        
        for user in pending_users:
            text += f"👤 <b>{user.first_name} {user.last_name}</b>\n"
            text += f"🏢 Отдел: {user.department.value}\n"
            text += f"🆔 ID: {user.telegram_id}\n"
            if user.telegram_username:
                text += f"📱 @{user.telegram_username}\n"
            text += "\n"
            
            keyboard.append([
                InlineKeyboardButton(f"✅ Одобрить {user.first_name}", callback_data=f"owner_approve_{user.id}"),
                InlineKeyboardButton(f"❌ Отклонить", callback_data=f"owner_reject_{user.id}")
            ])
        
        keyboard.append([InlineKeyboardButton("← Назад", callback_data="owner_managers")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

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
    """Отклонить заявку руководителя"""
    query = update.callback_query
    user_id = int(query.data.split('_')[2])
    
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await query.answer("❌ Пользователь не найден")
            return
        
        # Уведомляем пользователя
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=f"❌ <b>Заявка отклонена</b>\n\n"
                     f"К сожалению, ваша заявка на должность руководителя отдела не была одобрена.\n\n"
                     f"📞 Обратитесь к владельцу бизнеса для получения дополнительной информации.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to notify rejected user {user.id}: {e}")
        
        # Удаляем пользователя
        db.delete(user)
        db.commit()
        
        await query.edit_message_text(
            f"❌ <b>Заявка отклонена</b>\n\n"
            f"👤 {user.first_name} {user.last_name}\n"
            f"🏢 Отдел: {user.department.value}",
            parse_mode='HTML'
        )

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
            await query.edit_message_text(
                "❌ Неизвестная команда. Используйте /owner для обновления меню.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Главное меню", callback_data="owner_menu")]])
            )
    except Exception as e:
        logger.error(f"Error in owner callback handler: {e}")
        try:
            await query.answer("❌ Произошла ошибка. Попробуйте еще раз.")
        except:
            pass  # Игнорируем ошибки при отправке ответа

def get_owner_conversation_handler():
    """Получить conversation handler для владельцев"""
    from src.handlers.owner_slots import (
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
            CommandHandler('owner', owner_menu),
            CommandHandler('cancel', cancel_conversation)
        ],
        per_message=True
    )

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить текущий conversation"""
    await update.message.reply_text(
        "❌ Операция отменена. Используйте /owner для доступа к панели владельца."
    )
    context.user_data.clear()
    return ConversationHandler.END