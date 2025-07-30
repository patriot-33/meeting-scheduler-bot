from telegram import Update
from telegram.ext import ContextTypes
import logging

from src.database import get_db, User, UserRole
from src.config import settings

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await update.message.reply_text(
                "Привет! Я бот для планирования встреч.\n\n"
                "Для начала работы необходимо зарегистрироваться.\n\n"
                "Нажмите /register для регистрации."
            )
        elif user.role == UserRole.PENDING:
            await update.message.reply_text(
                "⏳ Ваша заявка ожидает одобрения администратором."
            )
        else:
            welcome_text = f"Привет, {user.first_name}!\n\n"
            
            if user.role == UserRole.ADMIN:
                welcome_text += (
                    "👨‍💼 Администратор:\n"
                    "/admin - Админ-панель\n"
                    "/pending - Ожидающие пользователи\n"
                    "/users - Список пользователей\n"
                    "/stats - Статистика\n\n"
                )
            
            welcome_text += (
                "📋 Основные команды:\n"
                "/schedule - Посмотреть доступные слоты\n"
                "/my_meetings - Мои встречи\n"
                "/vacation - Отметить отпуск\n"
                "/profile - Мой профиль\n"
                "/help - Помощь"
            )
            
            await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🤖 Помощь по боту\n\n"
        "📅 **Планирование встреч:**\n"
        "/schedule - Показать доступные слоты\n"
        "/my_meetings - Мои запланированные встречи\n\n"
        "👤 **Статус:**\n"
        "/vacation - Отметить отпуск\n"
        "/sick - Отметить больничный\n"
        "/trip - Отметить командировку\n"
        "/active - Вернуться в активный статус\n\n"
        "👤 **Профиль:**\n"
        "/profile - Посмотреть мой профиль\n\n"
        "📝 **Особенности:**\n"
        "• Встречи проводятся раз в 2 недели\n"
        "• Доступные часы: 11:00, 14:00, 15:00, 16:00, 17:00\n"
        "• Продолжительность: 60 минут\n"
        "• Напоминания приходят автоматически"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    await update.message.reply_text(
        "Операция отменена.\n\nИспользуйте /help для просмотра доступных команд."
    )

async def handle_navigation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle navigation callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "nav_back":
        await query.edit_message_text("⬅️ Возвращаемся назад...")
        # Add navigation logic here
    elif query.data == "nav_main":
        await start_command(update, context)