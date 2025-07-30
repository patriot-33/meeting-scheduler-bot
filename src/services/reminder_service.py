from datetime import datetime, timedelta
import logging
from typing import List
import asyncio
from telegram import Bot
from sqlalchemy import and_

from database import get_db, User, Meeting, Reminder, UserStatus, MeetingStatus
from config import settings

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
                    f"🔔 Напоминание\n\n"
                    f"Прошло 7 дней с последней встречи.\n"
                    f"Пожалуйста, назначьте следующую встречу.\n\n"
                    f"Нажмите /schedule для просмотра доступных слотов."
                )
            elif days == '3':
                message = (
                    f"⚠️ Важное напоминание\n\n"
                    f"Осталось 3 дня до крайнего срока назначения встречи.\n"
                    f"Пожалуйста, обязательно назначьте встречу!\n\n"
                    f"/schedule - Посмотреть доступные слоты"
                )
            else:  # 1 day
                message = (
                    f"🚨 Критичное напоминание\n\n"
                    f"Остался 1 день до крайнего срока!\n"
                    f"Если вы не назначите встречу, администраторы будут уведомлены.\n\n"
                    f"/schedule - Назначить встречу СЕЙЧАС"
                )
        
        elif reminder.reminder_type == 'meeting_1h':
            # 1 hour before meeting reminder
            meeting = reminder.meeting
            time_str = meeting.scheduled_time.strftime('%H:%M')
            date_str = meeting.scheduled_time.strftime('%d.%m.%Y')
            
            message = (
                f"🔔 Напоминание > 2AB@5G5\n\n"
                f"Через 1 час у вас встреча!\n\n"
                f"=� {date_str} 2 {time_str}\n"
                f"< Google Meet: {meeting.google_meet_link}\n\n"
                f"Подготовьтесь к созвону!"
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
        message = "⏰ Просроченные встречи\n\n"
        message += "Следующие руководители не назначили 2-недельную встречу:\n\n"
        
        for user in overdue_users:
            message += f"👤 {user.first_name} {user.last_name} ({user.department})\n"
        
        message += "\nПожалуйста, свяжитесь с ними для назначения встречи."
        
        for admin_id in settings.admin_ids_list:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")