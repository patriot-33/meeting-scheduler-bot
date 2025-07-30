from telegram import Update
from telegram.ext import ContextTypes
import logging

from database import get_db, User, UserRole
from config import settings

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user_id = update.effective_user.id
    
    # Сохраняем важные данные перед проверкой пользователя
    preserved_data = {}
    if context.user_data:
        # Сохраняем критически важные данные о состоянии пользователя
        preserved_data = {
            key: value for key, value in context.user_data.items() 
            if key in ['availability_settings', 'owner_slots', 'conversation_state']
        }
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Проверяем, является ли пользователь владельцем и автоматически создаем/обновляем
        if user_id in settings.admin_ids_list:
            if not user:
                # Создаем владельца
                from database import Department
                user = User(
                    telegram_id=user_id,
                    telegram_username=update.effective_user.username,
                    first_name=update.effective_user.first_name or "Владелец",
                    last_name=update.effective_user.last_name or "Бизнеса",
                    department=Department.FINANCE,
                    role=UserRole.OWNER
                )
                db.add(user)
                db.commit()
                logger.info(f"Auto-created owner user {user_id} via /start")
            elif user.role != UserRole.OWNER:
                # Обновляем роль
                user.role = UserRole.OWNER
                db.commit()
                logger.info(f"Updated user {user_id} to OWNER role via /start")
        
        # Восстанавливаем сохраненные данные
        if preserved_data:
            context.user_data.update(preserved_data)
        
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
            welcome_text = f"Добро пожаловать, {user.first_name}!\n\n"
            
            if user.role == UserRole.OWNER:
                welcome_text += (
                    "👑 Владелец бизнеса:\n"
                    "/owner - Панель владельца\n"
                    "/admin - Управление пользователями\n"
                    "/stats - Статистика\n\n"
                )
            elif user.role == UserRole.MANAGER:
                welcome_text += (
                    "👨‍💼 Руководитель отдела:\n"
                    "/schedule - Запланировать встречу\n"
                    "/my_meetings - Мои встречи\n"
                    "/calendar - Подключить Google Calendar\n\n"
                )
            
            welcome_text += (
                "📋 Общие команды:\n"
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
        "/my_meetings - Мои запланированные встречи\n"
        "/calendar - Подключение Google Calendar\n\n"
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