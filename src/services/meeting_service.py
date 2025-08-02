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
from services.google_calendar_dual import DualCalendarCreator
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
        self.dual_calendar_creator = DualCalendarCreator(google_calendar_service)
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
                    logger.info(f"🔍 DEBUG: Creating meeting in both calendars")
                    
                    # Get owner info for dual calendar creation
                    primary_owner = owners[0] if owners else None
                    owner_calendar_id = None
                    owner_name = "Owner"
                    owner_email = None
                    
                    if primary_owner:
                        owner_name = f"{primary_owner.first_name} {primary_owner.last_name}"
                        # Validate owner email - filter out invalid emails like "Я назначил"
                        if primary_owner.email and self._is_valid_email(primary_owner.email):
                            owner_email = primary_owner.email
                        else:
                            logger.warning(f"Owner {owner_name} has invalid email: '{primary_owner.email}' - not using for attendees")
                            owner_email = None
                        # Check if owner has calendar connected
                        if primary_owner.google_calendar_id:
                            owner_calendar_id = primary_owner.google_calendar_id
                    
                    # Use manager's calendar if available, otherwise use owner's
                    manager_calendar_id = manager.google_calendar_id if manager.google_calendar_id else calendar_id_to_use
                    
                    try:
                        # Create meeting in both calendars
                        result = self.dual_calendar_creator.create_meeting_in_both_calendars(
                            manager_calendar_id=manager_calendar_id,
                            owner_calendar_id=owner_calendar_id or manager_calendar_id,
                            manager_name=f"{manager.first_name} {manager.last_name}",
                            owner_name=owner_name,
                            manager_email=manager_email,
                            owner_email=owner_email,
                            department=manager.department.value,
                            scheduled_time=scheduled_time,
                            time_str=time_str
                        )
                        
                        if result['success']:
                            event_id = result['manager_event_id'] or result['owner_event_id']
                            meet_link = result['meet_link']
                            logger.info(f"✅ Created meetings: Manager={result['manager_event_id']}, Owner={result['owner_event_id']}")
                        else:
                            raise Exception(f"Failed to create meetings: {', '.join(result['errors'])}")
                    except Exception as calendar_error:
                        logger.error(f"❌ CALENDAR ERROR: Failed to create in {calendar_owner_name}'s calendar: {calendar_error}")
                        
                        # If manager's calendar failed, try owner's calendar as fallback
                        if "manager" in calendar_owner_name:
                            logger.info("🔄 FALLBACK: Trying owner's calendar...")
                            owners_with_calendar = self.db.query(User).filter(
                                User.role == UserRole.OWNER,
                                User.oauth_credentials.isnot(None),
                                User.google_calendar_id.isnot(None)
                            ).all()
                            
                            if owners_with_calendar:
                                fallback_owner = owners_with_calendar[0]
                                logger.info(f"🔄 FALLBACK: Using owner {fallback_owner.first_name}'s calendar: {fallback_owner.google_calendar_id}")
                                
                                # Use dual calendar creator for fallback too
                                result = self.dual_calendar_creator.create_meeting_in_both_calendars(
                                    manager_calendar_id=fallback_owner.google_calendar_id,
                                    owner_calendar_id=fallback_owner.google_calendar_id,
                                    manager_name=f"{manager.first_name} {manager.last_name}",
                                    owner_name=f"{fallback_owner.first_name} {fallback_owner.last_name}",
                                    manager_email=manager_email,
                                    owner_email=fallback_owner.email,
                                    department=manager.department.value,
                                    scheduled_time=scheduled_time,
                                    time_str=time_str
                                )
                                
                                if result['success']:
                                    event_id = result['manager_event_id'] or result['owner_event_id']
                                    meet_link = result['meet_link']
                                else:
                                    raise Exception(f"Fallback failed: {', '.join(result['errors'])}")
                            else:
                                raise calendar_error
                        else:
                            raise calendar_error
                else:
                    # No owners have connected their calendars via OAuth
                    logger.error(f"❌ CALENDAR SETUP REQUIRED: No users have connected their Google Calendar via OAuth")
                    logger.error(f"📋 SOLUTION: Users need to use /calendar command to connect their calendars")
                    logger.error(f"💡 OAuth calendars are required to create meetings with participants")
                    
                    # Don't fallback to Service Account to avoid attendee errors
                    raise Exception(
                        "Calendar setup required: No OAuth calendars connected. "
                        "Users must connect their Google Calendar using /calendar command to enable meeting creation with participants."
                    )
            
            # Get the result variable from the calendar creation
            if 'result' in locals():
                # Save to database with dual event IDs from successful creation
                meeting = Meeting(
                    manager_id=manager_id,
                    scheduled_time=scheduled_time,
                    google_event_id=event_id,  # Primary event ID (manager's)
                    google_manager_event_id=result.get('manager_event_id'),  # Manager's calendar event ID
                    google_owner_event_id=result.get('owner_event_id'),  # Owner's calendar event ID
                    google_meet_link=meet_link,
                    google_calendar_id=calendar_id_to_use,  # Save which calendar was used
                    status=MeetingStatus.SCHEDULED
                )
            else:
                # Fallback for non-dual calendar creation
                meeting = Meeting(
                    manager_id=manager_id,
                    scheduled_time=scheduled_time,
                    google_event_id=event_id,
                    google_meet_link=meet_link,
                    google_calendar_id=calendar_id_to_use,
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
        """Cancel a meeting from both calendars if applicable."""
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            logger.error(f"Meeting {meeting_id} not found in database")
            return False
        
        try:
            logger.info(f"🗑️ Cancelling meeting {meeting_id}: {meeting.google_event_id}")
            
            # Get manager information for dual calendar deletion
            manager = self.db.query(User).filter(User.id == meeting.manager_id).first()
            
            # Load OAuth credentials for manager
            manager_oauth_creds = None
            if manager and manager.oauth_credentials:
                try:
                    import json
                    manager_oauth_creds = json.loads(manager.oauth_credentials)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse manager OAuth credentials: {e}")
            
            # Find owner with calendar by matching google_calendar_id
            owner_with_calendar = None
            owner_oauth_creds = None
            
            # First, try to find owner by calendar ID from meeting
            if meeting.google_calendar_id:
                owner_with_calendar = self.db.query(User).filter(
                    User.role == UserRole.OWNER,
                    User.google_calendar_id == meeting.google_calendar_id,
                    User.oauth_credentials.isnot(None)
                ).first()
                
                if owner_with_calendar and owner_with_calendar.oauth_credentials:
                    try:
                        import json
                        owner_oauth_creds = json.loads(owner_with_calendar.oauth_credentials)
                        logger.info(f"Found owner calendar credentials for: {owner_with_calendar.first_name}")
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse owner OAuth credentials: {e}")
            
            # If no owner found by calendar ID, find any owner with OAuth
            if not owner_with_calendar:
                owner_with_calendar = self.db.query(User).filter(
                    User.role == UserRole.OWNER,
                    User.oauth_credentials.isnot(None),
                    User.google_calendar_id.isnot(None)
                ).first()
                
                if owner_with_calendar and owner_with_calendar.oauth_credentials:
                    try:
                        import json
                        owner_oauth_creds = json.loads(owner_with_calendar.oauth_credentials)
                        logger.info(f"Using fallback owner calendar: {owner_with_calendar.first_name}")
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse fallback owner OAuth credentials: {e}")
            
            # Try to delete from both calendars using DualCalendarCreator with proper event IDs
            deletion_results = self.dual_calendar_creator.delete_meeting_from_both_calendars_dual(
                manager_event_id=meeting.google_manager_event_id or meeting.google_event_id,
                owner_event_id=meeting.google_owner_event_id or meeting.google_event_id,
                manager_calendar_id=manager.google_calendar_id if manager else None,
                owner_calendar_id=owner_with_calendar.google_calendar_id if owner_with_calendar else meeting.google_calendar_id,
                manager_oauth_credentials=manager_oauth_creds,
                owner_oauth_credentials=owner_oauth_creds
            )
            
            # Log deletion results
            if deletion_results['success']:
                logger.info(f"✅ Successfully deleted meeting from {deletion_results['total_deleted']} calendar(s)")
                if deletion_results['errors']:
                    logger.warning(f"⚠️ Some deletion errors occurred: {deletion_results['errors']}")
            else:
                logger.error(f"❌ Failed to delete from any calendar: {deletion_results['errors']}")
                # Fallback to original method
                logger.info("🔄 Falling back to original deletion method")
                self.calendar_service.cancel_meeting(meeting.google_event_id, meeting.google_calendar_id)
            
            # Update database regardless of calendar deletion success
            meeting.status = MeetingStatus.CANCELLED
            self.db.commit()
            
            logger.info(f"✅ Meeting {meeting_id} marked as cancelled in database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel meeting {meeting_id}: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self.db.rollback()
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
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if email is valid and not empty."""
        if not email or not isinstance(email, str):
            return False
        
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
    
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