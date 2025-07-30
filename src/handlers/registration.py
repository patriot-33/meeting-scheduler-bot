from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
import logging

from src.database import get_db, User, UserRole
from src.config import settings

logger = logging.getLogger(__name__)

# Conversation states
FIRST_NAME, LAST_NAME, DEPARTMENT = range(3)

# Departments list
DEPARTMENTS = [
    "Продажи",
    "Маркетинг",
    "Разработка",
    "IT",
    "HR",
    "Финансы",
    "Операции",
    "Логистика",
    "Поддержка",
]

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the registration process."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        # Check if user already exists
        existing_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if existing_user:
            if existing_user.role == UserRole.PENDING:
                await update.message.reply_text(
                    "⏳ Ваша заявка на регистрацию уже отправлена и ожидает одобрения администратором."
                )
            elif existing_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
                await update.message.reply_text(
                    "Вы уже зарегистрированы! Используйте /help для просмотра доступных команд."
                )
            return ConversationHandler.END
    
    await update.message.reply_text(
        "Добро пожаловать!\n\n"
        "Я бот для планирования встреч с руководителями отделов.\n\n"
        "Для начала давайте познакомимся. Как вас зовут? Введите ваше имя:"
    )
    
    return FIRST_NAME

async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user's first name."""
    first_name = update.message.text.strip()
    
    if len(first_name) < 2:
        await update.message.reply_text(
            "Имя слишком короткое. Пожалуйста, введите полное имя:"
        )
        return FIRST_NAME
    
    context.user_data['first_name'] = first_name
    await update.message.reply_text(
        f"Приятно познакомиться, {first_name}!\n\nТеперь введите вашу фамилию:"
    )
    
    return LAST_NAME

async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user's last name."""
    last_name = update.message.text.strip()
    
    if len(last_name) < 2:
        await update.message.reply_text(
            "Фамилия слишком короткая. Пожалуйста, введите полную фамилию:"
        )
        return LAST_NAME
    
    context.user_data['last_name'] = last_name
    
    # Create department selection keyboard
    keyboard = []
    for i in range(0, len(DEPARTMENTS), 2):
        row = []
        row.append(InlineKeyboardButton(DEPARTMENTS[i], callback_data=f"dept_{i}"))
        if i + 1 < len(DEPARTMENTS):
            row.append(InlineKeyboardButton(DEPARTMENTS[i + 1], callback_data=f"dept_{i + 1}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏢 Выберите ваш отдел:",
        reply_markup=reply_markup
    )
    
    return DEPARTMENT

async def get_department(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user's department and complete registration."""
    query = update.callback_query
    await query.answer()
    
    # Parse department index
    dept_index = int(query.data.split('_')[1])
    department = DEPARTMENTS[dept_index]
    
    # Save to database
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = context.user_data.get('first_name')
    last_name = context.user_data.get('last_name')
    
    with get_db() as db:
        new_user = User(
            telegram_id=user_id,
            telegram_username=username,
            first_name=first_name,
            last_name=last_name,
            department=department,
            role=UserRole.PENDING
        )
        db.add(new_user)
        db.commit()
    
    await query.edit_message_text(
        f"✅ Спасибо за регистрацию!\n\n"
        f"=d {first_name} {last_name}\n"
        f"< B45;: {department}\n\n"
        f"⏳ Ваша заявка отправлена на одобрение администратору.\n"
        f"Вы получите уведомление, когда ваша заявка будет одобрена."
    )
    
    # Notify admins
    for admin_id in settings.admin_ids_list:
        try:
            keyboard = [[
                InlineKeyboardButton("✅ Одобрить", callback_data=f"admin_approve_{user_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{user_id}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📝 Новая заявка на регистрацию:\n\n"
                     f"< {user_id}\n"
                     f"=d {first_name} {last_name}\n"
                     f"= @{username}\n"
                     f"< {department}",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the registration process."""
    await update.message.reply_text(
        "❌ Регистрация отменена. Используйте /start для начала заново."
    )
    context.user_data.clear()
    return ConversationHandler.END

def get_registration_handler():
    """Return the registration conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler('register', start_registration)],
        states={
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_first_name)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_last_name)],
            DEPARTMENT: [CallbackQueryHandler(get_department, pattern="^dept_")]
        },
        fallbacks=[CommandHandler('cancel', cancel_registration)],
    )