from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from database import Meeting, User, MeetingStatus, UserStatus, UserRole
from services.google_calendar import google_calendar_service
from services.reminder_service import ReminderService
from services.owner_service import OwnerService

class MeetingService:
    def __init__(self, db: Session):
        self.db = db
        self.calendar_service = google_calendar_service
        self.reminder_service = ReminderService()
    
    def create_meeting(self, manager_id: int, scheduled_time: datetime) -> Optional[Meeting]:
        """Create a new meeting."""
        try:
            # Get manager info
            manager = self.db.query(User).filter(User.id == manager_id).first()
            if not manager:
                return None
            
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
                
                # For now, we'll use a placeholder email for owners
                # In a real implementation, you'd store owner emails in the database
                for owner in owners:
                    # You might want to add an email field to the User model
                    owner_emails.append(f"owner{owner.id}@company.com")  # Placeholder
                
                time_str = scheduled_time.strftime('%H:%M')
                
                # Use the primary Google Calendar for creating meetings
                from config import settings
                if hasattr(settings, 'google_calendar_id_1') and settings.google_calendar_id_1:
                    event_id, meet_link = self.calendar_service.create_meeting_with_owners(
                        settings.google_calendar_id_1,
                        f"{manager.first_name} {manager.last_name}",
                        manager.department.value,
                        scheduled_time,
                        time_str,
                        owner_emails,
                        manager_email=None  # Add manager email if available
                    )
                else:
                    # Fallback to basic event creation
                    event_data = {
                        'summary': f'Созвон с {manager.department.value}',
                        'description': f'Встреча с руководителем {manager.first_name} {manager.last_name}',
                        'start': {
                            'dateTime': scheduled_time.isoformat(),
                            'timeZone': 'Europe/Moscow',
                        },
                        'end': {
                            'dateTime': (scheduled_time + timedelta(minutes=60)).isoformat(),
                            'timeZone': 'Europe/Moscow',
                        }
                    }
                    
                    if hasattr(settings, 'google_calendar_id_1') and settings.google_calendar_id_1:
                        event_result = self.calendar_service.create_event(settings.google_calendar_id_1, event_data)
                        if isinstance(event_result, tuple):
                            event_id, meet_link = event_result
                        else:
                            event_id = event_result
            
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
            
            return meeting
            
        except Exception as e:
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
        # Check if owners are available
        if not OwnerService.are_both_owners_available(slot_datetime):
            return False
        
        # Check if slot is not already booked
        existing_meeting = self.db.query(Meeting).filter(
            and_(
                Meeting.scheduled_time == slot_datetime,
                Meeting.status == MeetingStatus.SCHEDULED
            )
        ).first()
        
        return existing_meeting is None
    
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