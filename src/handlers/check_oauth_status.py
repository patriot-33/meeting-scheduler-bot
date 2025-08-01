"""
Handler для проверки статуса OAuth подключения
"""
import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from sqlalchemy.orm import Session
from database import SessionLocal, User
from config import settings

logger = logging.getLogger(__name__)

async def check_oauth_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса OAuth подключения для руководителя или owner."""
    user_id = update.effective_user.id
    
    logger.info(f"🔍 Checking OAuth status for user {user_id}")
    
    with SessionLocal() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        
        if not user:
            await update.message.reply_text("❌ Вы не зарегистрированы в системе. Используйте /start")
            return
            
        # Проверяем, является ли пользователь owner
        is_owner = user_id in settings.admin_ids_list
        
        # Формируем отчет о статусе
        status_message = f"""
🔐 **Статус OAuth подключения**

👤 Пользователь: {user.name} (@{user.username})
🆔 ID: {user.user_id}
👔 Роль: {'Владелец' if is_owner else 'Руководитель' if user.is_manager else 'Пользователь'}

📧 **Email:** {user.email or '❌ Не указан'}
🔗 **OAuth статус:** {'✅ Подключен' if user.oauth_credentials else '❌ Не подключен'}
📅 **Google Calendar ID:** {user.google_calendar_id or '❌ Не указан'}
🗓️ **Календарь подключен:** {'✅ Да' if user.calendar_connected else '❌ Нет'}

"""

        # Добавляем инструкции в зависимости от статуса
        if not user.oauth_credentials and not user.google_calendar_id:
            status_message += """
⚠️ **Требуется настройка:**

Выберите один из способов:

1️⃣ **OAuth авторизация** (полный доступ):
   Используйте /connect_google

2️⃣ **Service Account** (рекомендуется):
   • Используйте /calendar_instructions для инструкций
   • Затем /setcalendar ВАШ_CALENDAR_ID
"""
        elif user.google_calendar_id and not user.oauth_credentials:
            status_message += """
✅ **Используется Service Account**
Это рекомендуемый способ подключения.
"""
        elif user.oauth_credentials and not user.google_calendar_id:
            status_message += """
⚠️ **OAuth подключен, но не указан Calendar ID**
Используйте /setcalendar ВАШ_CALENDAR_ID
"""
        else:
            status_message += """
✅ **Полностью настроено!**
Система готова к работе.
"""
            
        # Для owner показываем дополнительную информацию
        if is_owner:
            manager_count = session.query(User).filter_by(is_manager=True).count()
            connected_count = session.query(User).filter(
                User.is_manager == True,
                (User.calendar_connected == True) | (User.oauth_credentials != None)
            ).count()
            
            status_message += f"""

📊 **Статистика системы (для владельца):**
• Всего руководителей: {manager_count}
• Подключили календари: {connected_count}
• Без подключения: {manager_count - connected_count}
"""
            
        await update.message.reply_text(status_message, parse_mode='Markdown')

def create_check_oauth_handler():
    """Создает handler для проверки OAuth статуса."""
    return CommandHandler('check_oauth', check_oauth_status)