import functools
import logging
from telegram import Update
from telegram.ext import ContextTypes

from src.database import get_db, User, UserRole

logger = logging.getLogger(__name__)

def require_registration(func):
    """Decorator to require user registration."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user:
                await update.message.reply_text(
                    "Вы не зарегистрированы.\n\n"
                    "Нажмите /register для регистрации."
                )
                return
            
            if user.role == UserRole.PENDING:
                await update.message.reply_text(
                    "Ваша заявка на рассмотрении.\n\n"
                    "Ожидайте одобрения от администратора."
                )
                return
            
            return await func(update, context, *args, **kwargs)
    
    return wrapper

def require_admin(func):
    """Decorator to require admin privileges."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user or user.role != UserRole.ADMIN:
                await update.message.reply_text(
                    "❌ Недостаточно прав доступа.\n\n"
                    "Эта команда доступна только администраторам."
                )
                return
            
            return await func(update, context, *args, **kwargs)
    
    return wrapper