from datetime import datetime, timedelta
import logging
from typing import List
import asyncio
from telegram import Bot
from sqlalchemy import and_

from src.database import get_db, User, Meeting, Reminder, UserStatus, MeetingStatus
from src.config import settings

logger = logging.getLogger(__name__)

class ReminderService:
    def __init__(self):
        self.timezone = settings.timezone
    
    async def schedule_meeting_reminders(self, meeting_id: int):
        """Schedule all reminders for a meeting."""
        with get_db() as db:
            meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
            if not meeting:
                return
            
            user = meeting.manager
            meeting_time = meeting.scheduled_time
            
            # Schedule 1 hour before meeting reminder
            reminder_time = meeting_time - timedelta(hours=1)
            if reminder_time > datetime.now():
                reminder = Reminder(
                    user_id=user.id,
                    meeting_id=meeting.id,
                    reminder_type='meeting_1h',
                    scheduled_for=reminder_time
                )
                db.add(reminder)
            
            db.commit()
    
    async def schedule_next_meeting_reminders(self, user_id: int, last_meeting_date: datetime):
        """Schedule reminders for next meeting (2 weeks after last one)."""
        next_meeting_due = last_meeting_date + timedelta(days=14)
        
        with get_db() as db:
            # Clear existing reminders for this user
            db.query(Reminder).filter(
                and_(
                    Reminder.user_id == user_id,
                    Reminder.meeting_id.is_(None),
                    Reminder.sent == False
                )
            ).delete()
            
            # Schedule reminders at 7, 3, and 1 days before due date
            for days_before in settings.reminder_intervals:
                reminder_time = next_meeting_due - timedelta(days=days_before)
                
                if reminder_time > datetime.now():
                    reminder = Reminder(
                        user_id=user_id,
                        reminder_type=f'schedule_meeting_{days_before}d',
                        scheduled_for=reminder_time
                    )
                    db.add(reminder)
            
            db.commit()
    
    async def process_pending_reminders(self, bot: Bot):
        """Process all pending reminders."""
        with get_db() as db:
            now = datetime.now()
            pending_reminders = db.query(Reminder).filter(
                and_(
                    Reminder.sent == False,
                    Reminder.scheduled_for <= now
                )
            ).all()
            
            for reminder in pending_reminders:
                try:
                    await self._send_reminder(bot, reminder)
                    reminder.sent = True
                    reminder.sent_at = now
                except Exception as e:
                    logger.error(f"Failed to send reminder {reminder.id}: {e}")
            
            db.commit()
    
    async def _send_reminder(self, bot: Bot, reminder: Reminder):
        """Send a specific reminder."""
        user = reminder.user
        
        # Skip if user is not active
        if user.status != UserStatus.ACTIVE:
            return
        
        if reminder.reminder_type.startswith('schedule_meeting'):
            # Reminder to schedule next meeting
            days = reminder.reminder_type.split('_')[-1].replace('d', '')
            
            if days == '7':
                message = (
                    f"= 0?><8=0=85\n\n"
                    f"@>H;> 7 4=59 A ?>A;54=59 2AB@5G8.\n"
                    f">60;C9AB0, =07=0GLB5 A;54CNICN 2AB@5GC.\n\n"
                    f"06<8B5 /schedule 4;O ?@>A<>B@0 4>ABC?=KE A;>B>2."
                )
            elif days == '3':
                message = (
                    f"� 06=>5 =0?><8=0=85\n\n"
                    f"AB0;>AL 3 4=O 4> :@09=53> A@>:0 =07=0G5=8O 2AB@5G8.\n"
                    f">60;C9AB0, >1O70B5;L=> =07=0GLB5 2AB@5GC!\n\n"
                    f"/schedule - >A<>B@5BL 4>ABC?=K5 A;>BK"
                )
            else:  # 1 day
                message = (
                    f"=4 @8B8G=>5 =0?><8=0=85\n\n"
                    f"AB0;AO 1 45=L 4> :@09=53> A@>:0!\n"
                    f"A;8 2K =5 =07=0G8B5 2AB@5GC, 04<8=8AB@0B>@K 1C4CB C254><;5=K.\n\n"
                    f"/schedule - 07=0G8BL 2AB@5GC !'!"
                )
        
        elif reminder.reminder_type == 'meeting_1h':
            # 1 hour before meeting reminder
            meeting = reminder.meeting
            time_str = meeting.scheduled_time.strftime('%H:%M')
            date_str = meeting.scheduled_time.strftime('%d.%m.%Y')
            
            message = (
                f"= 0?><8=0=85 > 2AB@5G5\n\n"
                f"'5@57 1 G0A C 20A 2AB@5G0!\n\n"
                f"=� {date_str} 2 {time_str}\n"
                f"< Google Meet: {meeting.google_meet_link}\n\n"
                f">43>B>2LB5AL : A>72>=C!"
            )
        
        await bot.send_message(
            chat_id=user.telegram_id,
            text=message
        )
    
    async def check_overdue_meetings(self, bot: Bot):
        """Check for users who haven't scheduled meetings and notify admins."""
        with get_db() as db:
            # Find users who should have had a meeting by now
            cutoff_date = datetime.now() - timedelta(days=17)  # 14 + 3 grace days
            
            overdue_users = db.query(User).filter(
                and_(
                    User.status == UserStatus.ACTIVE,
                    User.role.in_([UserRole.MANAGER]),
                    ~User.meetings.any(
                        Meeting.scheduled_time > cutoff_date,
                        Meeting.status == MeetingStatus.SCHEDULED
                    )
                )
            ).all()
            
            if overdue_users:
                await self._notify_admins_about_overdue(bot, overdue_users)
    
    async def _notify_admins_about_overdue(self, bot: Bot, overdue_users: List[User]):
        """Notify admins about users with overdue meetings."""
        message = "=� @>A@>G5==K5 2AB@5G8\n\n"
        message += "!;54CNI85 @C:>2>48B5;8 =5 =07=0G8;8 2-=545;L=CN 2AB@5GC:\n\n"
        
        for user in overdue_users:
            message += f"" {user.first_name} {user.last_name} ({user.department})\n"
        
        message += "\n>60;C9AB0, A2O68B5AL A =8<8 4;O =07=0G5=8O 2AB@5G8."
        
        for admin_id in settings.admin_ids_list:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")