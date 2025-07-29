from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from functools import lru_cache

from src.config import settings

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(self):
        self.timezone = pytz.timezone(settings.timezone)
        self.service = self._build_service()
        self.calendar_ids = [settings.google_calendar_id_1, settings.google_calendar_id_2]
        self._cache_timeout = 300  # 5 minutes cache for small team
        
    @lru_cache(maxsize=1)
    def _build_service(self):
        """Build Google Calendar API service (cached)."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                settings.google_service_account_file,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            return build('calendar', 'v3', credentials=credentials, cache_discovery=False)
        except Exception as e:
            logger.error(f"Failed to build Google Calendar service: {e}")
            raise
    
    def check_slot_availability(self, date: datetime, time_str: str) -> bool:
        """Check if a time slot is available in both calendars."""
        # Parse time string (e.g., "14:00")
        hour, minute = map(int, time_str.split(':'))
        
        # Create timezone-aware datetime
        slot_start = self.timezone.localize(
            date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        )
        slot_end = slot_start + timedelta(minutes=settings.meeting_duration_minutes)
        
        # Convert to RFC3339 format for Google API
        time_min = slot_start.isoformat()
        time_max = slot_end.isoformat()
        
        # Check both calendars
        for calendar_id in self.calendar_ids:
            if not self._is_calendar_free(calendar_id, time_min, time_max):
                return False
        
        return True
    
    def _is_calendar_free(self, calendar_id: str, time_min: str, time_max: str) -> bool:
        """Check if a specific calendar is free during the given time."""
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return len(events) == 0
            
        except HttpError as e:
            logger.error(f"Error checking calendar {calendar_id}: {e}")
            return False
    
    def get_available_slots(self, start_date: datetime, end_date: datetime) -> Dict[str, List[str]]:
        """Get all available slots between two dates."""
        available_slots = {}
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                date_str = current_date.strftime('%Y-%m-%d')
                available_slots[date_str] = []
                
                for time_slot in settings.available_slots:
                    if self.check_slot_availability(current_date, time_slot):
                        available_slots[date_str].append(time_slot)
            
            current_date += timedelta(days=1)
        
        return available_slots
    
    def create_meeting(self, manager_name: str, department: str, 
                      date: datetime, time_str: str) -> Tuple[str, str]:
        """Create a meeting in both calendars and return event ID and Meet link."""
        hour, minute = map(int, time_str.split(':'))
        
        start_time = self.timezone.localize(
            date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        )
        end_time = start_time + timedelta(minutes=settings.meeting_duration_minutes)
        
        event = {
            'summary': f'!>72>= A {department}',
            'description': f' 53C;O@=K9 A>72>= A @C:>2>48B5;5< >B45;0 {department}\n C:>2>48B5;L: {manager_name}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': settings.timezone,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': settings.timezone,
            },
            'attendees': [
                {'email': settings.google_calendar_id_1},
                {'email': settings.google_calendar_id_2},
            ],
            'conferenceData': {
                'createRequest': {
                    'requestId': f"meeting-{datetime.now().timestamp()}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        
        try:
            # Create event in the first calendar
            created_event = self.service.events().insert(
                calendarId=settings.google_calendar_id_1,
                body=event,
                conferenceDataVersion=1,
                sendUpdates='all'
            ).execute()
            
            event_id = created_event['id']
            meet_link = created_event.get('hangoutLink', '')
            
            # Also add to second calendar if different
            if settings.google_calendar_id_1 != settings.google_calendar_id_2:
                try:
                    self.service.events().insert(
                        calendarId=settings.google_calendar_id_2,
                        body=event,
                        conferenceDataVersion=1,
                        sendUpdates='none'
                    ).execute()
                except Exception as e:
                    logger.error(f"Failed to add event to second calendar: {e}")
            
            return event_id, meet_link
            
        except HttpError as e:
            logger.error(f"Error creating meeting: {e}")
            raise
    
    def cancel_meeting(self, event_id: str):
        """Cancel a meeting in both calendars."""
        for calendar_id in self.calendar_ids:
            try:
                self.service.events().delete(
                    calendarId=calendar_id,
                    eventId=event_id,
                    sendUpdates='all'
                ).execute()
            except HttpError as e:
                if e.resp.status != 404:  # Ignore if event not found
                    logger.error(f"Error canceling meeting in {calendar_id}: {e}")
    
    def setup_webhook(self, webhook_url: str):
        """Setup webhook for calendar changes (optional)."""
        # This would require additional setup with Google Pub/Sub
        # For now, we'll use polling instead
        pass