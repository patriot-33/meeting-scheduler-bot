from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from src.database import get_db, User, UserRole

def require_registration(func):
    """Decorator to require user registration."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user:
                await update.message.reply_text(
                    "  K =5 70@538AB@8@>20=K.\n\n"
                    "06<8B5 /register 4;O @538AB@0F88."
                )
                return
            
            if user.role == UserRole.PENDING:
                await update.message.reply_text(
                    "9 0H0 70O2:0 >68405B >4>1@5=8O 04<8=8AB@0B>@><."
                )
                return
        
        return await func(update, context)
    
    return wrapper

def require_admin(func):
    """Decorator to require admin role."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user or user.role != UserRole.ADMIN:
                await update.message.reply_text(
                    "  -B0 :><0=40 4>ABC?=0 B>;L:> 04<8=8AB@0B>@0<."
                )
                return
        
        return await func(update, context)
    
    return wrapper