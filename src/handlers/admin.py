from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
from sqlalchemy import and_

from src.database import get_db, User, Meeting, UserRole, UserStatus, MeetingStatus, Department
from src.config import settings
from src.utils.decorators import require_admin

logger = logging.getLogger(__name__)

@require_admin
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin menu."""
    keyboard = [
        [InlineKeyboardButton("👥 Пользователи на модерации", callback_data="admin_pending")],
        [InlineKeyboardButton("📋 Все пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 Панель администратора:", reply_markup=reply_markup)

@require_admin
async def show_pending_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show users pending approval."""
    with get_db() as db:
        pending_users = db.query(User).filter(User.role == UserRole.PENDING).all()
        
        if not pending_users:
            await update.message.reply_text("✅ Нет пользователей ожидающих одобрения.")
            return
        
        message_text = "👥 **Пользователи на модерации:**\n\n"
        
        for user in pending_users:
            message_text += f"• {user.first_name} {user.last_name}\n"
            message_text += f"  Отдел: {user.department.value}\n"
            message_text += f"  ID: {user.telegram_id}\n\n"
        
        keyboard = []
        for user in pending_users:
            keyboard.append([
                InlineKeyboardButton(f"✅ Одобрить {user.first_name}", 
                                   callback_data=f"admin_approve_{user.id}"),
                InlineKeyboardButton(f"❌ Отклонить", 
                                   callback_data=f"admin_reject_{user.id}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

@require_admin 
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all users."""
    with get_db() as db:
        users = db.query(User).filter(User.role != UserRole.PENDING).all()
        
        if not users:
            await update.message.reply_text("Нет зарегистрированных пользователей.")
            return
        
        message_text = "📋 **Список пользователей:**\n\n"
        
        admins = []
        managers = []
        
        for user in users:
            user_info = f"• {user.first_name} {user.last_name} ({user.department.value})"
            if user.role == UserRole.OWNER:
                admins.append(user_info)
            else:
                managers.append(user_info)
        
        if admins:
            message_text += "👑 **Владельцы бизнеса:**\n"
            message_text += "\n".join(admins) + "\n\n"
        
        if managers:
            message_text += "👥 **Руководители отделов:**\n"
            message_text += "\n".join(managers)
        
        await update.message.reply_text(message_text, parse_mode='Markdown')

@require_admin
async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot usage statistics."""
    with get_db() as db:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.status == UserStatus.ACTIVE).count()
        pending_users = db.query(User).filter(User.role == UserRole.PENDING).count()
        
        # Meeting statistics
        total_meetings = db.query(Meeting).count()
        scheduled_meetings = db.query(Meeting).filter(Meeting.status == MeetingStatus.SCHEDULED).count()
        completed_meetings = db.query(Meeting).filter(Meeting.status == MeetingStatus.COMPLETED).count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_registrations = db.query(User).filter(User.created_at >= week_ago).count()
        recent_meetings = db.query(Meeting).filter(Meeting.created_at >= week_ago).count()
        
        message_text = f"""📊 **Статистика бота:**

👥 **Пользователи:**
• Всего: {total_users}
• Активных: {active_users}
• На модерации: {pending_users}

📅 **Встречи:**
• Всего: {total_meetings}
• Запланированных: {scheduled_meetings}
• Завершенных: {completed_meetings}

📈 **За последние 7 дней:**
• Новых регистраций: {recent_registrations}
• Новых встреч: {recent_meetings}
"""
        
        await update.message.reply_text(message_text, parse_mode='Markdown')

@require_admin
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast message to all users."""
    if not context.args:
        await update.message.reply_text(
            "Использование: /broadcast <сообщение>\n\n"
            "Пример: /broadcast Внимание! Завтра техническое обслуживание."
        )
        return
    
    message = " ".join(context.args)
    
    with get_db() as db:
        users = db.query(User).filter(User.role != UserRole.PENDING).all()
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"📢 **Объявление от администрации:**\n\n{message}",
                    parse_mode='Markdown'
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user.id}: {e}")
                failed_count += 1
        
        await update.message.reply_text(
            f"✅ Рассылка завершена!\n\n"
            f"Отправлено: {sent_count}\n"
            f"Ошибок: {failed_count}"
        )

@require_admin 
async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle notification settings."""
    await update.message.reply_text(
        "🔔 Управление уведомлениями пока не реализовано.\n"
        "В следующих версиях здесь можно будет настроить:\n"
        "• Напоминания о встречах\n"
        "• Уведомления о новых регистрациях\n" 
        "• Отчеты о просроченных встречах"
    )

async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Approve user registration."""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        user.role = UserRole.MANAGER
        db.commit()
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text="🎉 Поздравляем! Ваша регистрация одобрена владельцем бизнеса!\n\n"
                     f"👑 Вы теперь руководитель отдела: {user.department.value}\n"
                     "📅 Используйте /schedule для назначения встреч с владельцами"
            )
        except Exception as e:
            logger.error(f"Failed to notify approved user {user.id}: {e}")
        
        await update.callback_query.edit_message_text(
            f"✅ Руководитель {user.first_name} {user.last_name} одобрен!\n"
            f"🏢 Отдел: {user.department.value}"
        )

async def reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Reject user registration."""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text="❌ К сожалению, ваша заявка на регистрацию отклонена.\n\n"
                     "Обратитесь к администратору для получения дополнительной информации."
            )
        except Exception as e:
            logger.error(f"Failed to notify rejected user {user.id}: {e}")
        
        # Delete user
        db.delete(user)
        db.commit()
        
        await update.callback_query.edit_message_text(
            f"❌ Заявка {user.first_name} {user.last_name} отклонена.\n"
            f"🏢 Отдел: {user.department.value}"
        )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin callback queries."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "admin_pending":
        await show_pending_users(update, context)
    elif data == "admin_users":
        await list_users(update, context)
    elif data == "admin_stats":
        await show_statistics(update, context)
    elif data == "admin_broadcast":
        await query.edit_message_text(
            "📢 Для рассылки используйте команду:\n"
            "/broadcast <ваше сообщение>"
        )
    elif data.startswith("admin_approve_"):
        user_id = int(data.split("_")[2])
        await approve_user(update, context, user_id)
    elif data.startswith("admin_reject_"):
        user_id = int(data.split("_")[2])
        await reject_user(update, context, user_id)