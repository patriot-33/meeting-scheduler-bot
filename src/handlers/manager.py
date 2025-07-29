from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
from sqlalchemy import and_

from src.database import get_db, User, Meeting, UserRole, UserStatus, MeetingStatus, Reminder
from src.services.google_calendar import GoogleCalendarService
from src.services.reminder_service import ReminderService
from src.config import settings
from src.utils.decorators import require_registration

logger = logging.getLogger(__name__)

@require_registration
async def show_available_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available meeting slots."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if user.status != UserStatus.ACTIVE:
            status_text = {
                UserStatus.VACATION: "<4 >B?CA:5",
                UserStatus.SICK_LEAVE: "> 1>;L=8G=><",
                UserStatus.BUSINESS_TRIP: " :><0=48@>2:5"
            }.get(user.status, "=50:B82=>< AB0BCA5")
            
            await update.message.reply_text(
                f"� K =0E>48B5AL =0 {status_text}.\n\n"
                f";O =07=0G5=8O 2AB@5G A=0G0;0 25@=8B5AL 2 0:B82=K9 AB0BCA: /active"
            )
            return
    
    try:
        calendar_service = GoogleCalendarService()
        
        # Get available slots for the next 4 weeks
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=28)
        
        available_slots = calendar_service.get_available_slots(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.min.time())
        )
        
        if not any(slots for slots in available_slots.values()):
            await update.message.reply_text(
                "=  A>60;5=8N, =0 1;8609H85 4 =545;8 =5B A2>1>4=KE A;>B>2.\n\n"
                ">?@>1C9B5 ?>765 8;8 A2O68B5AL A 04<8=8AB@0B>@><."
            )
            return
        
        # Create keyboard with available slots
        keyboard = []
        message_text = "=� >ABC?=K5 A;>BK 4;O 2AB@5G\n\n"
        
        for date_str, slots in available_slots.items():
            if slots:  # Only show dates with available slots
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                day_name = date_obj.strftime('%A')
                formatted_date = date_obj.strftime('%d.%m.%Y')
                
                message_text += f"=� **{day_name}, {formatted_date}**\n"
                
                row = []
                for slot in slots:
                    callback_data = f"book_{date_str}_{slot}"
                    row.append(InlineKeyboardButton(slot, callback_data=callback_data))
                    
                    if len(row) == 2:  # Two buttons per row
                        keyboard.append(row)
                        row = []
                
                if row:  # Add remaining buttons
                    keyboard.append(row)
                
                message_text += "\n"
        
        if not keyboard:
            await update.message.reply_text(
                "= 0 4>ABC?=K5 4=8 =5B A2>1>4=KE A;>B>2."
            )
            return
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error getting available slots: {e}")
        await update.message.reply_text(
            "� @>87>H;0 >H81:0 ?@8 ?>;CG5=88 4>ABC?=KE A;>B>2. >?@>1C9B5 ?>765."
        )

async def handle_booking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle slot booking callback."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data  # format: book_2024-01-15_14:00
    
    try:
        _, date_str, time_str = callback_data.split('_')
        
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user or user.status != UserStatus.ACTIVE:
                await query.edit_message_text(
                    "� 5;L7O =07=0G8BL 2AB@5GC 2 =50:B82=>< AB0BCA5."
                )
                return
            
            # Check if user already has a meeting scheduled for next 2 weeks
            two_weeks_ago = datetime.now() - timedelta(days=14)
            recent_meeting = db.query(Meeting).filter(
                and_(
                    Meeting.manager_id == user.id,
                    Meeting.scheduled_time > two_weeks_ago,
                    Meeting.status == MeetingStatus.SCHEDULED
                )
            ).first()
            
            if recent_meeting:
                next_allowed = recent_meeting.scheduled_time + timedelta(days=14)
                await query.edit_message_text(
                    f"� # 20A C65 5ABL 70?;0=8@>20==0O 2AB@5G0.\n\n"
                    f"!;54CNICN 2AB@5GC <>6=> =07=0G8BL =5 @0=55 {next_allowed.strftime('%d.%m.%Y')}."
                )
                return
        
        # Create meeting
        calendar_service = GoogleCalendarService()
        meeting_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Double-check slot availability
        if not calendar_service.check_slot_availability(meeting_date, time_str):
            await query.edit_message_text(
                "�  A>60;5=8N, MB>B A;>B C65 70=OB. >?@>1C9B5 2K1@0BL 4@C3>5 2@5<O."
            )
            return
        
        # Create meeting in Google Calendar
        event_id, meet_link = calendar_service.create_meeting(
            f"{user.first_name} {user.last_name}",
            user.department,
            meeting_date,
            time_str
        )
        
        # Save to database
        hour, minute = map(int, time_str.split(':'))
        scheduled_time = meeting_date.replace(hour=hour, minute=minute)
        
        with get_db() as db:
            meeting = Meeting(
                manager_id=user.id,
                scheduled_time=scheduled_time,
                google_event_id=event_id,
                google_meet_link=meet_link,
                status=MeetingStatus.SCHEDULED
            )
            db.add(meeting)
            db.commit()
            
            # Schedule reminders
            reminder_service = ReminderService()
            await reminder_service.schedule_meeting_reminders(meeting.id)
            await reminder_service.schedule_next_meeting_reminders(user.id, scheduled_time)
        
        # Notify admins
        for admin_id in settings.admin_ids_list:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"=� >20O 2AB@5G0\n\n"
                         f"=d {user.first_name} {user.last_name}\n"
                         f"<� {user.department}\n"
                         f"=� {scheduled_time.strftime('%d.%m.%Y 2 %H:%M')}\n"
                         f"< {meet_link}"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        
        await query.edit_message_text(
            f" AB@5G0 CA?5H=> =07=0G5=0!\n\n"
            f"=� 0B0: {scheduled_time.strftime('%d.%m.%Y')}\n"
            f"� @5<O: {time_str}\n"
            f"< Google Meet: {meet_link}\n\n"
            f"= K ?>;CG8B5 =0?><8=0=85 70 1 G0A 4> 2AB@5G8."
        )
        
    except Exception as e:
        logger.error(f"Error booking meeting: {e}")
        await query.edit_message_text(
            "� @>87>H;0 >H81:0 ?@8 =07=0G5=88 2AB@5G8. >?@>1C9B5 ?>765."
        )

@require_registration
async def show_my_meetings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's scheduled meetings."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        meetings = db.query(Meeting).filter(
            and_(
                Meeting.manager_id == user.id,
                Meeting.status == MeetingStatus.SCHEDULED,
                Meeting.scheduled_time > datetime.now()
            )
        ).order_by(Meeting.scheduled_time).all()
        
        if not meetings:
            await update.message.reply_text(
                ">7B # 20A =5B 70?;0=8@>20==KE 2AB@5G.\n\n"
                "06<8B5 /schedule 4;O =07=0G5=8O =>2>9 2AB@5G8."
            )
            return
        
        message_text = "=� 0H8 70?;0=8@>20==K5 2AB@5G8:\n\n"
        
        keyboard = []
        for meeting in meetings:
            time_str = meeting.scheduled_time.strftime('%d.%m.%Y 2 %H:%M')
            message_text += f"" {time_str}\n"
            
            # Add cancel button
            keyboard.append([
                InlineKeyboardButton(
                    f"L B<5=8BL {meeting.scheduled_time.strftime('%d.%m')}",
                    callback_data=f"cancel_{meeting.id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await update.message.reply_text(message_text, reply_markup=reply_markup)

async def handle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle meeting cancellation."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    meeting_id = int(query.data.split('_')[1])
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        meeting = db.query(Meeting).filter(
            and_(
                Meeting.id == meeting_id,
                Meeting.manager_id == user.id
            )
        ).first()
        
        if not meeting:
            await query.edit_message_text(
                "� AB@5G0 =5 =0945=0."
            )
            return
        
        # Cancel in Google Calendar
        try:
            calendar_service = GoogleCalendarService()
            calendar_service.cancel_meeting(meeting.google_event_id)
        except Exception as e:
            logger.error(f"Error canceling Google Calendar event: {e}")
        
        # Update database
        meeting.status = MeetingStatus.CANCELLED
        db.commit()
        
        # Cancel related reminders
        db.query(Reminder).filter(
            Reminder.meeting_id == meeting.id
        ).update({'sent': True})
        db.commit()
        
        await query.edit_message_text(
            f"L AB@5G0 >B<5=5=0\n\n"
            f"=� {meeting.scheduled_time.strftime('%d.%m.%Y 2 %H:%M')}\n\n"
            f">65B5 =07=0G8BL =>2CN 2AB@5GC G5@57 /schedule"
        )

# Status management functions
@require_registration
async def set_vacation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user status to vacation."""
    await _set_user_status(update, context, UserStatus.VACATION, "<4 >B?CA:")

@require_registration
async def set_sick_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user status to sick leave."""
    await _set_user_status(update, context, UserStatus.SICK_LEAVE, "> 1>;L=8G=K9")

@require_registration
async def set_business_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user status to business trip."""
    await _set_user_status(update, context, UserStatus.BUSINESS_TRIP, " :><0=48@>2:0")

@require_registration
async def set_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user status to active."""
    await _set_user_status(update, context, UserStatus.ACTIVE, " 0:B82=K9")

async def _set_user_status(update: Update, context: ContextTypes.DEFAULT_TYPE, status: UserStatus, status_text: str):
    """Helper function to set user status."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        old_status = user.status
        user.status = status
        db.commit()
        
        await update.message.reply_text(
            f" 0H AB0BCA 87<5=5= =0: {status_text}"
        )
        
        # If returning from non-active status, schedule reminder for next meeting
        if old_status != UserStatus.ACTIVE and status == UserStatus.ACTIVE:
            last_meeting = db.query(Meeting).filter(
                and_(
                    Meeting.manager_id == user.id,
                    Meeting.status == MeetingStatus.COMPLETED
                )
            ).order_by(Meeting.scheduled_time.desc()).first()
            
            if last_meeting:
                reminder_service = ReminderService()
                await reminder_service.schedule_next_meeting_reminders(
                    user.id, last_meeting.scheduled_time
                )

@require_registration
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile."""
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get meeting statistics
        total_meetings = db.query(Meeting).filter(Meeting.manager_id == user.id).count()
        completed_meetings = db.query(Meeting).filter(
            and_(
                Meeting.manager_id == user.id,
                Meeting.status == MeetingStatus.COMPLETED
            )
        ).count()
        
        last_meeting = db.query(Meeting).filter(
            Meeting.manager_id == user.id
        ).order_by(Meeting.scheduled_time.desc()).first()
        
        status_emoji = {
            UserStatus.ACTIVE: "",
            UserStatus.VACATION: "<4",
            UserStatus.SICK_LEAVE: ">",
            UserStatus.BUSINESS_TRIP: ""
        }.get(user.status, "S")
        
        profile_text = (
            f"=d **>9 ?@>D8;L**\n\n"
            f"=� <O: {user.first_name} {user.last_name}\n"
            f"<� B45;: {user.department}\n"
            f"{status_emoji} !B0BCA: {user.status.value}\n\n"
            f"=� **!B0B8AB8:0:**\n"
            f"" A53> 2AB@5G: {total_meetings}\n"
            f"" @>2545=>: {completed_meetings}\n"
        )
        
        if last_meeting:
            profile_text += f"" >A;54=OO 2AB@5G0: {last_meeting.scheduled_time.strftime('%d.%m.%Y')}\n"
        
        await update.message.reply_text(profile_text, parse_mode='Markdown')