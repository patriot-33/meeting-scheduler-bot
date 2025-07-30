import functools
import logging
from telegram import Update
from telegram.ext import ContextTypes

from src.database import get_db, User, UserRole
from src.config import settings

logger = logging.getLogger(__name__)

def require_registration(func):
    """Декоратор для проверки регистрации пользователя"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user:
                await update.effective_message.reply_text(
                    "❌ Вы не зарегистрированы в системе. Используйте /start для регистрации."
                )
                return
            
            if user.role == UserRole.PENDING:
                await update.effective_message.reply_text(
                    "⏳ Ваша заявка ожидает одобрения администратором."
                )
                return
        
        return await func(update, context, *args, **kwargs)
    return wrapper

def require_owner(func):
    """Декоратор для проверки прав владельца"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Проверяем, что пользователь в списке владельцев
        if user_id not in settings.admin_ids_list:
            await update.effective_message.reply_text(
                "❌ У вас нет прав для выполнения этой команды."
            )
            return
        
        # Проверяем/создаем пользователя-владельца если его нет в БД
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user:
                # Автоматически создаем владельца если его нет в БД
                logger.info(f"Creating owner user for ID {user_id}")
                try:
                    from src.database import Department
                    owner_user = User(
                        telegram_id=user_id,
                        telegram_username=update.effective_user.username,
                        first_name=update.effective_user.first_name or "Владелец",
                        last_name=update.effective_user.last_name or "Бизнеса",
                        department=Department.FINANCE,
                        role=UserRole.OWNER
                    )
                    db.add(owner_user)
                    db.commit()
                    logger.info(f"Successfully created owner user for ID {user_id}")
                except Exception as e:
                    logger.error(f"Failed to create owner user: {e}")
                    await update.effective_message.reply_text(
                        "❌ Ошибка инициализации владельца. Попробуйте команду /start."
                    )
                    return
            elif user.role != UserRole.OWNER:
                # Обновляем роль до владельца, если пользователь в админском списке
                logger.info(f"Updating user {user_id} role to OWNER")
                user.role = UserRole.OWNER
                db.commit()
        
        return await func(update, context, *args, **kwargs)
    return wrapper

def require_manager(func):
    """Декоратор для проверки прав руководителя"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user:
                await update.effective_message.reply_text(
                    "❌ Вы не зарегистрированы в системе. Используйте /start для регистрации."
                )
                return
            
            if user.role not in [UserRole.MANAGER, UserRole.OWNER]:
                await update.effective_message.reply_text(
                    "❌ У вас нет прав руководителя для выполнения этой команды."
                )
                return
        
        return await func(update, context, *args, **kwargs)
    return wrapper

def require_admin(func):
    """Декоратор для проверки прав администратора (владельца)"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if user_id not in settings.admin_ids_list:
            await update.effective_message.reply_text(
                "❌ У вас нет административных прав."
            )
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper

def log_user_action(action_name: str):
    """Декоратор для логирования действий пользователей"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            username = update.effective_user.username or "Unknown"
            
            logger.info(f"👤 User {user_id} (@{username}) performed action: {action_name}")
            
            try:
                result = await func(update, context, *args, **kwargs)
                logger.info(f"✅ Action {action_name} completed successfully for user {user_id}")
                return result
            except Exception as e:
                logger.error(f"❌ Action {action_name} failed for user {user_id}: {e}")
                raise
        
        return wrapper
    return decorator