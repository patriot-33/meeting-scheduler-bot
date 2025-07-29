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
    "@>4068",
    "0@:5B8=3",
    " 07@01>B:0",
    "IT",
    "HR",
    "$8=0=AK",
    "?5@0F88",
    ">38AB8:0",
    ">445@6:0",
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
                    "9 0H0 70O2:0 =0 @538AB@0F8N C65 >B?@02;5=0 8 >68405B >4>1@5=8O 04<8=8AB@0B>@><."
                )
            elif existing_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
                await update.message.reply_text(
                    " K C65 70@538AB@8@>20=K! A?>;L7C9B5 /help 4;O ?@>A<>B@0 4>ABC?=KE :><0=4."
                )
            return ConversationHandler.END
    
    await update.message.reply_text(
        "=K >1@> ?>60;>20BL!\n\n"
        "/ 1>B 4;O ?;0=8@>20=8O 2AB@5G A @C:>2>48B5;O<8 >B45;>2.\n\n"
        ";O =0G0;0 40209B5 ?>7=0:><8<AO. 0: 0A 7>2CB? 2548B5 20H5 8<O:"
    )
    
    return FIRST_NAME

async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user's first name."""
    first_name = update.message.text.strip()
    
    if len(first_name) < 2:
        await update.message.reply_text(
            " <O A;8H:>< :>@>B:>5. >60;C9AB0, 22548B5 ?>;=>5 8<O:"
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
            " $0<8;8O A;8H:>< :>@>B:0O. >60;C9AB0, 22548B5 ?>;=CN D0<8;8N:"
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
        "< K15@8B5 20H >B45;:",
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
        f" !?0A81> 70 @538AB@0F8N!\n\n"
        f"=d {first_name} {last_name}\n"
        f"< B45;: {department}\n\n"
        f"=Q 0H0 70O2:0 >B?@02;5=0 =0 >4>1@5=85 04<8=8AB@0B>@C.\n"
        f"K ?>;CG8B5 C254><;5=85, :>340 20H0 70O2:0 1C45B >4>1@5=0."
    )
    
    # Notify admins
    for admin_id in settings.admin_ids_list:
        try:
            keyboard = [[
                InlineKeyboardButton(" 4>1@8BL", callback_data=f"admin_approve_{user_id}"),
                InlineKeyboardButton("L B:;>=8BL", callback_data=f"admin_reject_{user_id}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"< >20O 70O2:0 =0 @538AB@0F8N:\n\n"
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
        "=  538AB@0F8O >B<5=5=0. A?>;L7C9B5 /start 4;O =0G0;0 70=>2>."
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