from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import traceback
import psutil
import os

from database import Meeting, User, MeetingStatus, UserStatus, UserRole
from services.google_calendar import google_calendar_service
from services.reminder_service import ReminderService
from services.owner_service import OwnerService

logger = logging.getLogger(__name__)

def log_system_state_for_meeting():
    """Log system state for meeting creation diagnostics."""
    try:
        logger.info(f"📊 SYSTEM STATE: CPU {psutil.cpu_percent()}%, Memory {psutil.virtual_memory().percent}%")
        logger.info(f"📊 SYSTEM STATE: Disk {psutil.disk_usage('/').percent}%, Connections {len(psutil.net_connections())}")
        logger.info(f"📊 SYSTEM STATE: Timestamp {datetime.now().isoformat()}")
    except Exception as e:
        logger.warning(f"Failed to log system state: {e}")

class MeetingService:
    def __init__(self, db: Session):
        self.db = db
        self.calendar_service = google_calendar_service
        self.reminder_service = ReminderService()
    
    def create_meeting(self, manager_id: int, scheduled_time: datetime) -> Optional[Meeting]:
        """Create a new meeting."""
        log_system_state_for_meeting()
        logger.info(f"🚀 MEETING CREATION START: Manager ID {manager_id}, Time {scheduled_time}")
        
        try:
            # Get manager info
            manager = self.db.query(User).filter(User.id == manager_id).first()
            if not manager:
                logger.error(f"❌ MANAGER NOT FOUND: ID {manager_id}")
                return None
            
            logger.info(f"✅ MANAGER FOUND: {manager.first_name} {manager.last_name} ({manager.department.value})")
            
            # Check if owners are available at this time
            if not OwnerService.are_both_owners_available(scheduled_time):
                raise ValueError("Owners are not available at this time")
            
            # Create meeting in Google Calendar if available
            event_id = None
            meet_link = None
            
            if self.calendar_service.is_available:
                # Get owner emails for meeting participants
                owners = OwnerService.get_all_owners()
                owner_emails = []
                manager_email = manager.email if manager.email else None
                
                # CRITICAL FIX: Use real emails from database
                for owner in owners:
                    if owner.email:
                        owner_emails.append(owner.email)
                    else:
                        logger.warning(f"Owner {owner.id} ({owner.first_name} {owner.last_name}) has no email configured")
                
                time_str = scheduled_time.strftime('%H:%M')
                
                # PRIORITY: Use manager's calendar if connected, otherwise use owner's calendar
                from database import UserRole
                
                calendar_id_to_use = None
                calendar_owner_name = None
                
                # First check if manager has connected calendar
                if manager.google_calendar_id and manager.oauth_credentials:
                    calendar_id_to_use = manager.google_calendar_id
                    calendar_owner_name = f"manager {manager.first_name}"
                    logger.info(f"🔍 DEBUG: Manager has OAuth calendar connected: {manager.google_calendar_id}")
                else:
                    logger.info(f"🔍 DEBUG: Manager does not have OAuth calendar connected")
                    
                    # Find owners with connected OAuth calendars as fallback
                    owners_with_calendar = self.db.query(User).filter(
                        User.role == UserRole.OWNER,
                        User.oauth_credentials.isnot(None),
                        User.google_calendar_id.isnot(None)
                    ).all()
                    
                    logger.info(f"🔍 DEBUG: Found {len(owners_with_calendar)} owners with OAuth calendars")
                    
                    if owners_with_calendar:
                        # Use the first owner's calendar as fallback
                        primary_owner = owners_with_calendar[0]
                        calendar_id_to_use = primary_owner.google_calendar_id
                        calendar_owner_name = f"owner {primary_owner.first_name}"
                        logger.info(f"🔍 DEBUG: Using owner's calendar as fallback: {primary_owner.google_calendar_id}")
                
                if calendar_id_to_use:
                    logger.info(f"🔍 DEBUG: Creating meeting in {calendar_owner_name}'s calendar: {calendar_id_to_use}")
                    
                    event_id, meet_link = self.calendar_service.create_meeting_with_owners(
                        calendar_id_to_use,
                        f"{manager.first_name} {manager.last_name}",
                        manager.department.value,
                        scheduled_time,
                        time_str,
                        owner_emails,
                        manager_email=manager_email
                    )
                else:
                    # No owners have connected their calendars via OAuth
                    logger.error(f"🔍 DEBUG: No owners have connected their Google Calendar via OAuth")
                    logger.error(f"🔍 DEBUG: Owners need to use /calendar command to connect their calendars")
                    
                    # Check if we have legacy Service Account setup as fallback
                    from config import settings
                    if hasattr(settings, 'google_calendar_id_1') and settings.google_calendar_id_1:
                        logger.info(f"🔍 DEBUG: Falling back to Service Account with calendar: {settings.google_calendar_id_1}")
                        event_id, meet_link = self.calendar_service.create_meeting_with_owners(
                            settings.google_calendar_id_1,
                            f"{manager.first_name} {manager.last_name}",
                            manager.department.value,
                            scheduled_time,
                            time_str,
                            owner_emails,
                            manager_email=manager_email
                        )
                    else:
                        logger.error(f"🔍 DEBUG: No calendar configuration found - neither OAuth owners nor Service Account")
                        return None
            
            # Save to database
            meeting = Meeting(
                manager_id=manager_id,
                scheduled_time=scheduled_time,
                google_event_id=event_id,
                google_meet_link=meet_link,
                status=MeetingStatus.SCHEDULED
            )
            
            self.db.add(meeting)
            self.db.commit()
            self.db.refresh(meeting)
            
            # CRITICAL FIX: Notify all owners about the new meeting
            self._notify_owners_about_meeting(meeting, manager)
            
            return meeting
            
        except Exception as e:
            logger.error(f"❌ MEETING CREATION FAILED: {str(e)}")
            logger.error(f"❌ TRACEBACK: {traceback.format_exc()}")
            log_system_state_for_meeting()
            self.db.rollback()
            raise e
    
    def cancel_meeting(self, meeting_id: int) -> bool:
        """Cancel a meeting."""
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return False
        
        try:
            # Cancel in Google Calendar
            self.calendar_service.cancel_meeting(meeting.google_event_id)
            
            # Update database
            meeting.status = MeetingStatus.CANCELLED
            self.db.commit()
            
            return True
            
        except Exception:
            return False
    
    def get_user_meetings(self, user_id: int, future_only: bool = True) -> List[Meeting]:
        """Get meetings for a specific user."""
        query = self.db.query(Meeting).filter(Meeting.manager_id == user_id)
        
        if future_only:
            query = query.filter(Meeting.scheduled_time > datetime.now())
        
        return query.order_by(Meeting.scheduled_time).all()
    
    def get_recent_meeting(self, user_id: int, days_back: int = 14) -> Optional[Meeting]:
        """Get user's most recent meeting within specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        return self.db.query(Meeting).filter(
            and_(
                Meeting.manager_id == user_id,
                Meeting.scheduled_time > cutoff_date,
                Meeting.status == MeetingStatus.SCHEDULED
            )
        ).order_by(Meeting.scheduled_time.desc()).first()
    
    def mark_completed(self, meeting_id: int) -> bool:
        """Mark a meeting as completed."""
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            meeting.status = MeetingStatus.COMPLETED
            self.db.commit()
            return True
        return False
    
    def get_available_slots(self, days_ahead: int = 14) -> Dict[str, List[str]]:
        """Get available meeting slots when owners are free."""
        return OwnerService.get_available_slots_for_both_owners(days_ahead)
    
    def is_slot_available(self, slot_datetime: datetime) -> bool:
        """Check if a specific slot is available for booking."""
        # Check if owners are available in local database
        if not OwnerService.are_both_owners_available(slot_datetime):
            return False
        
        # Check if slot is not already booked in local database
        existing_meeting = self.db.query(Meeting).filter(
            and_(
                Meeting.scheduled_time == slot_datetime,
                Meeting.status == MeetingStatus.SCHEDULED
            )
        ).first()
        
        if existing_meeting:
            return False
        
        # CRITICAL FIX: Check Google Calendar availability
        if self.calendar_service.is_available:
            from config import settings
            if hasattr(settings, 'google_calendar_id_1') and settings.google_calendar_id_1:
                # Check if the slot is busy in Google Calendar
                if not self._is_google_calendar_slot_free(settings.google_calendar_id_1, slot_datetime):
                    return False
        
        return True
    
    def _is_google_calendar_slot_free(self, calendar_id: str, slot_datetime: datetime, duration_minutes: int = 60) -> bool:
        """Check if a specific time slot is free in Google Calendar."""
        try:
            # Create time range for the slot
            slot_start = slot_datetime
            slot_end = slot_datetime + timedelta(minutes=duration_minutes)
            
            # Query freebusy API
            time_min = slot_start.isoformat() + 'Z'
            time_max = slot_end.isoformat() + 'Z'
            
            freebusy_query = {
                'timeMin': time_min,
                'timeMax': time_max,
                'items': [{'id': calendar_id}]
            }
            
            freebusy_result = self.calendar_service._service.freebusy().query(body=freebusy_query).execute()
            busy_times = freebusy_result['calendars'][calendar_id].get('busy', [])
            
            # If there are any busy times in this slot, it's not available
            if busy_times:
                logger.info(f"❌ Slot {slot_datetime} is busy in Google Calendar: {busy_times}")
                return False
            
            logger.info(f"✅ Slot {slot_datetime} is free in Google Calendar")
            return True
            
        except Exception as e:
            logger.error(f"Error checking Google Calendar availability: {e}")
            # In case of error, be conservative and assume slot is busy
            return False
    
    def _notify_owners_about_meeting(self, meeting: Meeting, manager: User):
        """Notify all owners about new meeting booking."""
        try:
            from services.owner_service import OwnerService
            import asyncio
            from telegram.ext import Application
            from config import settings
            
            owners = OwnerService.get_all_owners()
            if not owners:
                logger.warning("No owners found to notify")
                return
            
            # Format meeting details
            formatted_date = meeting.scheduled_time.strftime('%d.%m.%Y')
            formatted_time = meeting.scheduled_time.strftime('%H:%M')
            day_name = meeting.scheduled_time.strftime('%A')
            
            # Russian day names
            russian_days = {
                'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда',
                'Thursday': 'Четверг', 'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'
            }
            russian_day = russian_days.get(day_name, day_name)
            
            message = f"""🔔 НОВАЯ ВСТРЕЧА ЗАПЛАНИРОВАНА!

📅 {russian_day}, {formatted_date}
🕐 {formatted_time}
👤 {manager.first_name} {manager.last_name}
🏢 {manager.department.value}

ID встречи: {meeting.id}"""
            
            if meeting.google_meet_link:
                message += f"\n🔗 Google Meet: {meeting.google_meet_link}"
            
            # Get bot application - this will be called from async context
            # For now, just log the notification (telegram sending requires async context)
            logger.info(f"📧 OWNER NOTIFICATION: {message}")
            
            # TODO: Implement actual telegram notification when called from proper async context
            # This would require refactoring to make the entire meeting creation async
            
        except Exception as e:
            logger.error(f"Failed to notify owners: {e}")
    
    def get_overdue_users(self, days_overdue: int = 17) -> List[User]:
        """Get users who haven't scheduled meetings in specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_overdue)
        
        return self.db.query(User).filter(
            and_(
                User.status == UserStatus.ACTIVE,
                User.role == UserRole.MANAGER,
                ~User.meetings.any(
                    Meeting.scheduled_time > cutoff_date,
                    Meeting.status == MeetingStatus.SCHEDULED
                )
            )
        ).all()