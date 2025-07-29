from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import func
import logging

from src.database import get_db, User, Meeting, UserRole, UserStatus, MeetingStatus
from src.config import settings
from src.utils.decorators import require_admin

logger = logging.getLogger(__name__)

@require_admin
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu."""
    keyboard = [
        [
            InlineKeyboardButton("=e >;L7>20B5;8", callback_data="admin_users"),
            InlineKeyboardButton("S 6840NI85", callback_data="admin_pending")
        ],
        [
            InlineKeyboardButton("=Ê !B0B8AB8:0", callback_data="admin_stats"),
            InlineKeyboardButton("= #254><;5=8O", callback_data="admin_notifications")
        ],
        [
            InlineKeyboardButton("=â  0AAK;:0", callback_data="admin_broadcast")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "=à **4<8=-?0=5;L**\n\nK15@8B5 459AB285:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

@require_admin
async def show_pending_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending users for approval."""
    with get_db() as db:
        pending_users = db.query(User).filter(User.role == UserRole.PENDING).all()
        
        if not pending_users:
            await update.message.reply_text(
                " 5B ?>;L7>20B5;59, >6840NI8E >4>1@5=8O."
            )
            return
        
        message_text = "S **>;L7>20B5;8, >6840NI85 >4>1@5=8O:**\n\n"
        
        keyboard = []
        for user in pending_users:
            message_text += (
                f"=d {user.first_name} {user.last_name}\n"
                f"<í {user.department}\n"
                f"=ñ @{user.telegram_username or 'N/A'}\n"
                f"<” {user.telegram_id}\n\n"
            )
            
            keyboard.append([
                InlineKeyboardButton(
                    f" 4>1@8BL {user.first_name}",
                    callback_data=f"admin_approve_{user.telegram_id}"
                ),
                InlineKeyboardButton(
                    f"L B:;>=8BL {user.first_name}",
                    callback_data=f"admin_reject_{user.telegram_id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

@require_admin
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users."""
    with get_db() as db:
        users = db.query(User).filter(User.role != UserRole.PENDING).all()
        
        if not users:
            await update.message.reply_text(
                ">7B 5B 70@538AB@8@>20==KE ?>;L7>20B5;59."
            )
            return
        
        message_text = "=e **!?8A>: ?>;L7>20B5;59:**\n\n"
        
        admins = []
        managers = []
        
        for user in users:
            user_info = f"=d {user.first_name} {user.last_name} ({user.department})"
            
            if user.role == UserRole.ADMIN:
                admins.append(user_info)
            else:
                status_emoji = {
                    UserStatus.ACTIVE: "",
                    UserStatus.VACATION: "<4",
                    UserStatus.SICK_LEAVE: ">",
                    UserStatus.BUSINESS_TRIP: ""
                }.get(user.status, "S")
                managers.append(f"{user_info} {status_emoji}")
        
        if admins:
            message_text += "=à **4<8=8AB@0B>@K:**\n"
            for admin in admins:
                message_text += f"{admin}\n"
            message_text += "\n"
        
        if managers:
            message_text += "=¼ ** C:>2>48B5;8:**\n"
            for manager in managers:
                message_text += f"{manager}\n"
        
        # Split message if too long
        if len(message_text) > 4000:
            parts = message_text.split('\n')
            current_part = ""
            
            for part in parts:
                if len(current_part + part + '\n') > 4000:
                    await update.message.reply_text(current_part, parse_mode='Markdown')
                    current_part = part + '\n'
                else:
                    current_part += part + '\n'
            
            if current_part:
                await update.message.reply_text(current_part, parse_mode='Markdown')
        else:
            await update.message.reply_text(message_text, parse_mode='Markdown')

@require_admin
async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics."""
    with get_db() as db:
        # User statistics
        total_users = db.query(User).count()
        pending_users = db.query(User).filter(User.role == UserRole.PENDING).count()
        active_managers = db.query(User).filter(
            User.role == UserRole.MANAGER,
            User.status == UserStatus.ACTIVE
        ).count()
        
        # Meeting statistics
        total_meetings = db.query(Meeting).count()
        scheduled_meetings = db.query(Meeting).filter(
            Meeting.status == MeetingStatus.SCHEDULED
        ).count()
        completed_meetings = db.query(Meeting).filter(
            Meeting.status == MeetingStatus.COMPLETED
        ).count()
        
        # Department statistics
        dept_stats = db.query(
            User.department,
            func.count(User.id).label('count')
        ).filter(
            User.role == UserRole.MANAGER
        ).group_by(User.department).all()
        
        stats_text = (
            f"=Ê **!B0B8AB8:0 1>B0**\n\n"
            f"=e **>;L7>20B5;8:**\n"
            f"" A53>: {total_users}\n"
            f"" 6840NB >4>1@5=8O: {pending_users}\n"
            f"" :B82=K5 @C:>2>48B5;8: {active_managers}\n\n"
            f"=Å **AB@5G8:**\n"
            f"" A53>: {total_meetings}\n"
            f"" 0?;0=8@>20=>: {scheduled_meetings}\n"
            f"" @>2545=>: {completed_meetings}\n\n"
        )
        
        if dept_stats:
            stats_text += "<í **> >B45;0<:**\n"
            for dept, count in dept_stats:
                stats_text += f"" {dept}: {count}\n"
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')

@require_admin
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users."""
    if not context.args:
        await update.message.reply_text(
            "  #:068B5 A>>1I5=85 4;O @0AAK;:8.\n\n"
            "@8<5@: `/broadcast 06=>5 >1JO2;5=85!`"
        )
        return
    
    message = ' '.join(context.args)
    
    with get_db() as db:
        users = db.query(User).filter(User.role != UserRole.PENDING).all()
        
        success_count = 0
        failed_count = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"=â **1JO2;5=85 >B 04<8=8AB@0F88:**\n\n{message}",
                    parse_mode='Markdown'
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user.telegram_id}: {e}")
                failed_count += 1
        
        await update.message.reply_text(
            f"=â  0AAK;:0 7025@H5=0!\n\n"
            f" B?@02;5=>: {success_count}\n"
            f"L H81>:: {failed_count}"
        )

@require_admin
async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle admin notifications."""
    user_id = update.effective_user.id
    
    # This would need to be stored in database or settings
    # For now, just show current status
    await update.message.reply_text(
        "= **0AB@>9:8 C254><;5=89**\n\n"
        " #254><;5=8O > =>2KE 2AB@5G0E: 2:;\n"
        " #254><;5=8O > ?@>A@>G5==KE 2AB@5G0E: 2:;\n\n"
        "9 #?@02;5=85 C254><;5=8O<8 1C45B 4>102;5=> 2 A;54CNI8E >1=>2;5=8OE.",
        parse_mode='Markdown'
    )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callback queries."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check admin permissions
    with get_db() as db:
        admin = db.query(User).filter(
            User.telegram_id == user_id,
            User.role == UserRole.ADMIN
        ).first()
        
        if not admin:
            await query.edit_message_text(
                "  # 20A =5B ?@02 04<8=8AB@0B>@0."
            )
            return
    
    if query.data.startswith('admin_approve_'):
        telegram_id = int(query.data.split('_')[2])
        await approve_user(query, telegram_id)
    
    elif query.data.startswith('admin_reject_'):
        telegram_id = int(query.data.split('_')[2])
        await reject_user(query, telegram_id, context.bot)
    
    elif query.data == 'admin_users':
        await query.edit_message_text("1=>2;ON A?8A>: ?>;L7>20B5;59...")
        # Would call list_users here
    
    elif query.data == 'admin_pending':
        await query.edit_message_text("1=>2;ON A?8A>: >6840NI8E...")
        # Would call show_pending_users here

async def approve_user(query, telegram_id: int):
    """Approve a pending user."""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user or user.role != UserRole.PENDING:
            await query.edit_message_text(
                "  >;L7>20B5;L =5 =0945= 8;8 C65 >1@01>B0=."
            )
            return
        
        user.role = UserRole.MANAGER
        db.commit()
        
        await query.edit_message_text(
            f" >;L7>20B5;L {user.first_name} {user.last_name} >4>1@5=!\n\n"
            f"= <>65B =0G0BL ?>;L7>20BLAO 1>B><."
        )
        
        # Notify the user
        try:
            await query.bot.send_message(
                chat_id=telegram_id,
                text=(
                    f" >74@02;O5<!\n\n"
                    f"0H0 70O2:0 =0 @538AB@0F8N >4>1@5=0!\n\n"
                    f""5?5@L 2K <>65B5 =07=0G0BL 2AB@5G8.\n\n"
                    f"06<8B5 /schedule 4;O ?@>A<>B@0 4>ABC?=KE A;>B>2."
                )
            )
        except Exception as e:
            logger.error(f"Failed to notify approved user {telegram_id}: {e}")

async def reject_user(query, telegram_id: int, bot):
    """Reject a pending user."""
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user or user.role != UserRole.PENDING:
            await query.edit_message_text(
                "  >;L7>20B5;L =5 =0945= 8;8 C65 >1@01>B0=."
            )
            return
        
        user_name = f"{user.first_name} {user.last_name}"
        db.delete(user)
        db.commit()
        
        await query.edit_message_text(
            f"L 0O2:0 ?>;L7>20B5;O {user_name} >B:;>=5=0."
        )
        
        # Notify the user
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=(
                    f"L  A>60;5=8N, 20H0 70O2:0 =0 @538AB@0F8N >B:;>=5=0.\n\n"
                    f"A;8 C 20A 5ABL 2>?@>AK, >1@0B8B5AL : 04<8=8AB@0B>@C."
                )
            )
        except Exception as e:
            logger.error(f"Failed to notify rejected user {telegram_id}: {e}")