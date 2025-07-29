from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List, Optional

from src.database import Meeting, User, MeetingStatus, UserStatus, UserRole
from src.services.google_calendar import GoogleCalendarService
from src.services.reminder_service import ReminderService

class MeetingService:
    def __init__(self, db: Session):
        self.db = db
        self.calendar_service = GoogleCalendarService()
        self.reminder_service = ReminderService()
    
    def create_meeting(self, manager_id: int, scheduled_time: datetime) -> Optional[Meeting]:
        """Create a new meeting."""
        try:
            # Get manager info
            manager = self.db.query(User).filter(User.id == manager_id).first()
            if not manager:
                return None
            
            # Create meeting in Google Calendar
            time_str = scheduled_time.strftime('%H:%M')
            event_id, meet_link = self.calendar_service.create_meeting(
                f"{manager.first_name} {manager.last_name}",
                manager.department,
                scheduled_time,
                time_str
            )
            
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