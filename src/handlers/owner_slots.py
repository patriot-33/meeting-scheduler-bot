"""
Обработчики управления временными слотами для владельцев
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from src.services.owner_service import OwnerService, WEEKDAYS, TIME_SLOTS
from src.utils.decorators import require_owner

logger = logging.getLogger(__name__)

# States для conversation handlers слотов
(ADD_SLOT_DAY, ADD_SLOT_TIME, REMOVE_SLOT_DAY, REMOVE_SLOT_TIME, 
 SETUP_DAY, SETUP_SLOTS) = range(6)

# Доступные временные слоты для выбора
AVAILABLE_TIME_SLOTS = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]

@require_owner
async def add_slot_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбрать день для добавления слота"""
    query = update.callback_query
    day_index = int(query.data.split('_')[3])
    
    context.user_data['slot_day'] = day_index
    
    # Показываем доступные временные слоты
    keyboard = []
    
    # Получаем уже занятые слоты пользователя
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    existing_slots = OwnerService.get_owner_time_slots(user.id, day_index)
    
    # Создаем клавиатуру с доступными слотами
    row = []
    for i, slot in enumerate(AVAILABLE_TIME_SLOTS):
        if slot in existing_slots:
            button_text = f"✅ {slot}"  # Уже добавлен
            callback_data = f"slot_exists_{slot.replace(':', '')}"
        else:
            button_text = slot
            callback_data = f"add_slot_time_{slot.replace(':', '')}"
        
        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        # По 3 кнопки в ряд
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:  # Добавляем оставшиеся кнопки
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    day_name = WEEKDAYS[day_index]
    existing_text = f"Уже добавлены: {', '.join(existing_slots)}" if existing_slots else "Слоты не настроены"
    
    text = f"""
⏰ <b>Добавление слота - {day_name}</b>

{existing_text}

Выберите время начала созвона:
<i>✅ = уже добавлен, нажмите на свободное время</i>
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    return ADD_SLOT_TIME

@require_owner
async def add_slot_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить выбранный временной слот"""
    query = update.callback_query
    time_data = query.data.split('_')[3]
    
    # Восстанавливаем формат времени
    time_slot = f"{time_data[:2]}:{time_data[2:]}"
    day_index = context.user_data.get('slot_day')
    
    if day_index is None:
        await query.edit_message_text("❌ Ошибка: день не выбран")
        return ConversationHandler.END
    
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    
    # Добавляем слот
    success = OwnerService.add_owner_time_slot(user.id, day_index, time_slot)
    
    if success:
        day_name = WEEKDAYS[day_index]
        text = f"✅ Слот {time_slot} добавлен для {day_name}"
    else:
        text = "❌ Ошибка при добавлении слота или слот уже существует"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить еще слот", callback_data="add_more_slot_same_day")],
        [InlineKeyboardButton("← К управлению слотами", callback_data="owner_availability")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)
    
    # Не завершаем conversation, чтобы кнопка "Добавить еще слот" работала
    # Остаемся в состоянии ADD_SLOT_TIME для обработки следующего выбора
    return ADD_SLOT_TIME

@require_owner
async def remove_slot_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбрать день для удаления слота"""
    query = update.callback_query
    day_index = int(query.data.split('_')[3])
    
    context.user_data['slot_day'] = day_index
    
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    existing_slots = OwnerService.get_owner_time_slots(user.id, day_index)
    
    if not existing_slots:
        await query.edit_message_text(
            "❌ В этот день нет слотов для удаления",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="owner_availability")]])
        )
        return ConversationHandler.END
    
    # Создаем клавиатуру с существующими слотами
    keyboard = []
    row = []
    for slot in existing_slots:
        row.append(InlineKeyboardButton(slot, callback_data=f"remove_slot_time_{slot.replace(':', '')}"))
        
        # По 3 кнопки в ряд
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:  # Добавляем оставшиеся кнопки
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🗑 Удалить все слоты дня", callback_data="remove_all_day_slots")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    day_name = WEEKDAYS[day_index]
    text = f"""
🗑 <b>Удаление слота - {day_name}</b>

Текущие слоты: {', '.join(existing_slots)}

Выберите слот для удаления:
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    return REMOVE_SLOT_TIME

@require_owner
async def remove_slot_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить выбранный временной слот"""
    query = update.callback_query
    
    if query.data == "remove_all_day_slots":
        # Удаляем все слоты дня
        day_index = context.user_data.get('slot_day')
        user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
        
        success = OwnerService.remove_all_day_slots(user.id, day_index)
        day_name = WEEKDAYS[day_index]
        
        if success:
            text = f"✅ Все слоты удалены для {day_name}"
        else:
            text = "❌ Ошибка при удалении слотов"
    else:
        # Удаляем конкретный слот
        time_data = query.data.split('_')[3]
        time_slot = f"{time_data[:2]}:{time_data[2:]}"
        day_index = context.user_data.get('slot_day')
        
        if day_index is None:
            await query.edit_message_text("❌ Ошибка: день не выбран")
            return ConversationHandler.END
        
        user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
        success = OwnerService.remove_owner_time_slot(user.id, day_index, time_slot)
        
        day_name = WEEKDAYS[day_index]
        if success:
            text = f"✅ Слот {time_slot} удален для {day_name}"
        else:
            text = "❌ Ошибка при удалении слота"
    
    keyboard = [
        [InlineKeyboardButton("🗑 Удалить еще слот", callback_data="owner_remove_slot")],
        [InlineKeyboardButton("← К управлению слотами", callback_data="owner_availability")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)
    return ConversationHandler.END

@require_owner
async def setup_day_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбрать день для полной настройки"""
    query = update.callback_query
    day_index = int(query.data.split('_')[2])
    
    context.user_data['setup_day'] = day_index
    
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    existing_slots = OwnerService.get_owner_time_slots(user.id, day_index)
    
    # Создаем клавиатуру с чекбоксами
    keyboard = []
    row = []
    context.user_data['selected_slots'] = existing_slots.copy()  # Изначально выбраны существующие
    
    for slot in AVAILABLE_TIME_SLOTS:
        if slot in existing_slots:
            button_text = f"✅ {slot}"
            callback_data = f"toggle_slot_{slot.replace(':', '')}"
        else:
            button_text = f"⬜ {slot}"
            callback_data = f"toggle_slot_{slot.replace(':', '')}"
        
        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        # По 3 кнопки в ряд
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:  # Добавляем оставшиеся кнопки
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_day_setup")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    day_name = WEEKDAYS[day_index]
    current_text = f"Текущие: {', '.join(existing_slots)}" if existing_slots else "Не настроены"
    
    text = f"""
📝 <b>Настройка дня - {day_name}</b>

{current_text}

Выберите нужные слоты:
<i>✅ = включен, ⬜ = отключен
Нажмите на слот чтобы переключить</i>
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    return SETUP_SLOTS

@require_owner
async def toggle_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключить выбор слота при настройке дня"""
    query = update.callback_query
    time_data = query.data.split('_')[2]
    time_slot = f"{time_data[:2]}:{time_data[2:]}"
    
    selected_slots = context.user_data.get('selected_slots', [])
    
    if time_slot in selected_slots:
        selected_slots.remove(time_slot)
    else:
        selected_slots.append(time_slot)
        selected_slots.sort()  # Сортируем по времени
    
    context.user_data['selected_slots'] = selected_slots
    
    # Обновляем клавиатуру
    keyboard = []
    row = []
    
    for slot in AVAILABLE_TIME_SLOTS:
        if slot in selected_slots:
            button_text = f"✅ {slot}"
            callback_data = f"toggle_slot_{slot.replace(':', '')}"
        else:
            button_text = f"⬜ {slot}"
            callback_data = f"toggle_slot_{slot.replace(':', '')}"
        
        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_day_setup")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    day_index = context.user_data.get('setup_day')
    day_name = WEEKDAYS[day_index]
    selected_text = f"Выбрано: {', '.join(selected_slots)}" if selected_slots else "Ничего не выбрано"
    
    text = f"""
📝 <b>Настройка дня - {day_name}</b>

{selected_text}

Выберите нужные слоты:
<i>✅ = включен, ⬜ = отключен
Нажмите на слот чтобы переключить</i>
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    return SETUP_SLOTS

@require_owner
async def save_day_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить настройку дня"""
    query = update.callback_query
    
    day_index = context.user_data.get('setup_day')
    selected_slots = context.user_data.get('selected_slots', [])
    
    if day_index is None:
        await query.edit_message_text("❌ Ошибка: день не выбран")
        return ConversationHandler.END
    
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    
    # Устанавливаем новые слоты (заменяем существующие)
    success = OwnerService.set_owner_time_slots(user.id, day_index, selected_slots)
    
    day_name = WEEKDAYS[day_index]
    if success:
        if selected_slots:
            slots_text = ', '.join(selected_slots)
            text = f"✅ Настройка {day_name} сохранена:\n{slots_text}"
        else:
            text = f"✅ Все слоты удалены для {day_name}"
    else:
        text = "❌ Ошибка при сохранении настроек"
    
    keyboard = [
        [InlineKeyboardButton("📝 Настроить другой день", callback_data="owner_setup_day")],
        [InlineKeyboardButton("← К управлению слотами", callback_data="owner_availability")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)
    return ConversationHandler.END

# Обработчики для слотов
async def handle_slot_exists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия на уже существующий слот"""
    query = update.callback_query
    await query.answer("💡 Этот слот уже добавлен", show_alert=False)
    return ADD_SLOT_TIME  # Остаемся в том же состоянии

async def add_more_slot_same_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить еще один слот для того же дня"""
    query = update.callback_query
    day_index = context.user_data.get('slot_day')
    
    if day_index is None:
        await query.edit_message_text("❌ Ошибка: день не найден")
        return ConversationHandler.END
    
    # Показываем доступные временные слоты снова
    # Получаем уже занятые слоты пользователя
    user = OwnerService.get_owner_by_telegram_id(update.effective_user.id)
    existing_slots = OwnerService.get_owner_time_slots(user.id, day_index)
    
    # Создаем клавиатуру с доступными слотами
    keyboard = []
    row = []
    for i, slot in enumerate(AVAILABLE_TIME_SLOTS):
        if slot in existing_slots:
            button_text = f"✅ {slot}"  # Уже добавлен
            callback_data = f"slot_exists_{slot.replace(':', '')}"
        else:
            button_text = slot
            callback_data = f"add_slot_time_{slot.replace(':', '')}"
        
        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        # По 3 кнопки в ряд
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:  # Добавляем оставшиеся кнопки
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="owner_availability")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    day_name = WEEKDAYS[day_index]
    existing_text = f"Уже добавлены: {', '.join(existing_slots)}" if existing_slots else "Слоты не настроены"
    
    text = f"""
⏰ <b>Добавление слота - {day_name}</b>

{existing_text}

Выберите время начала созвона:
<i>✅ = уже добавлен, нажмите на свободное время</i>
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    return ADD_SLOT_TIME