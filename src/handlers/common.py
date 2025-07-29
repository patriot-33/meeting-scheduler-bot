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
                "=K @825B! / 1>B 4;O ?;0=8@>20=8O 2AB@5G.\n\n"
                ";O =0G0;0 @01>BK =5>1E>48<> 70@538AB@8@>20BLAO.\n\n"
                "06<8B5 /register 4;O @538AB@0F88."
            )
        elif user.role == UserRole.PENDING:
            await update.message.reply_text(
                "9 0H0 70O2:0 >68405B >4>1@5=8O 04<8=8AB@0B>@><."
            )
        else:
            welcome_text = f"=K @825B, {user.first_name}!\n\n"
            
            if user.role == UserRole.ADMIN:
                welcome_text += (
                    "=à 4<8=8AB@0B>@:\n"
                    "/admin - 4<8=-?0=5;L\n"
                    "/pending - 6840NI85 ?>;L7>20B5;8\n"
                    "/users - !?8A>: ?>;L7>20B5;59\n"
                    "/stats - !B0B8AB8:0\n\n"
                )
            
            welcome_text += (
                "=Å A=>2=K5 :><0=4K:\n"
                "/schedule - >A<>B@5BL 4>ABC?=K5 A;>BK\n"
                "/my_meetings - >8 2AB@5G8\n"
                "/vacation - B<5B8BL >B?CA:\n"
                "/profile - >9 ?@>D8;L\n"
                "/help - ><>IL"
            )
            
            await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "> ><>IL ?> 1>BC\n\n"
        "=Å **;0=8@>20=85 2AB@5G:**\n"
        "/schedule - >:070BL 4>ABC?=K5 A;>BK\n"
        "/my_meetings - >8 70?;0=8@>20==K5 2AB@5G8\n\n"
        "<4 **!B0BCA:**\n"
        "/vacation - B<5B8BL >B?CA:\n"
        "/sick - B<5B8BL 1>;L=8G=K9\n"
        "/trip - B<5B8BL :><0=48@>2:C\n"
        "/active - 5@=CBLAO 2 0:B82=K9 AB0BCA\n\n"
        "=d **@>D8;L:**\n"
        "/profile - >A<>B@5BL <>9 ?@>D8;L\n\n"
        "9 **A>15==>AB8:**\n"
        "" AB@5G8 ?@>2>4OBAO @07 2 2 =545;8\n"
        "" >ABC?=K5 G0AK: 11:00, 14:00, 15:00, 16:00, 17:00\n"
        "" @>4>;68B5;L=>ABL: 60 <8=CB\n"
        "" 0?><8=0=8O ?@8E>4OB 02B><0B8G5A:8"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    await update.message.reply_text(
        "L ?5@0F8O >B<5=5=0.\n\nA?>;L7C9B5 /help 4;O ?@>A<>B@0 4>ABC?=KE :><0=4."
    )

async def handle_navigation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle navigation callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "nav_back":
        await query.edit_message_text(" >72@0I05<AO =0704...")
        # Add navigation logic here
    elif query.data == "nav_main":
        await start_command(update, context)