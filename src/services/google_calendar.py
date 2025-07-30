import json
import os
from functools import lru_cache
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Enhanced Google Calendar service with environment variable support."""
    
    def __init__(self):
        self._service = None
        self._credentials = None
        self._is_available = False
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar service with fallback options."""
        try:
            self._credentials = self._get_credentials()
            if self._credentials:
                self._service = self._build_service()
                self._is_available = True
                logger.info("✅ Google Calendar service initialized successfully")
            else:
                logger.warning("⚠️ Google Calendar service not available - running in fallback mode")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Calendar service: {e}")
            self._is_available = False
    
    def _get_credentials(self) -> Optional[service_account.Credentials]:
        """Get credentials from environment variable or file."""
        # Method 1: Try to get credentials from environment variable (JSON string)
        google_credentials_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if google_credentials_json:
            try:
                credentials_info = json.loads(google_credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
                logger.info("✅ Loaded Google credentials from environment variable")
                return credentials
            except Exception as e:
                logger.error(f"❌ Failed to load credentials from environment variable: {e}")
        
        # Method 2: Try to load from file (fallback for local development)
        try:
            if hasattr(settings, 'google_service_account_file') and settings.google_service_account_file:
                if os.path.exists(settings.google_service_account_file):
                    credentials = service_account.Credentials.from_service_account_file(
                        settings.google_service_account_file,
                        scopes=['https://www.googleapis.com/auth/calendar']
                    )
                    logger.info(f"✅ Loaded Google credentials from file: {settings.google_service_account_file}")
                    return credentials
                else:
                    logger.warning(f"⚠️ Service account file not found: {settings.google_service_account_file}")
        except Exception as e:
            logger.error(f"❌ Failed to load credentials from file: {e}")
        
        # Method 3: Check if running on Google Cloud (Application Default Credentials)
        try:
            from google.auth import default
            credentials, project = default(scopes=['https://www.googleapis.com/auth/calendar'])
            logger.info("✅ Using Google Cloud Application Default Credentials")
            return credentials
        except Exception as e:
            logger.debug(f"Application Default Credentials not available: {e}")
        
        logger.error("❌ No valid Google Calendar credentials found")
        return None
    
    @lru_cache(maxsize=1)
    def _build_service(self):
        """Build Google Calendar API service (cached)."""
        if not self._credentials:
            raise ValueError("No credentials available")
        
        try:
            return build('calendar', 'v3', credentials=self._credentials, cache_discovery=False)
        except Exception as e:
            logger.error(f"Failed to build Google Calendar service: {e}")
            raise
    
    @property
    def is_available(self) -> bool:
        """Check if Google Calendar service is available."""
        return self._is_available
    
    def get_available_slots(self, calendar_id: str, date: datetime, duration_minutes: int = 60) -> List[str]:
        """Get available time slots for a specific date."""
        if not self.is_available:
            logger.warning("Google Calendar not available - returning fallback slots")
            return self._get_fallback_slots()
        
        try:
            # Get busy times for the day
            time_min = date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
            time_max = date.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
            
            freebusy_query = {
                'timeMin': time_min,
                'timeMax': time_max,
                'items': [{'id': calendar_id}]
            }
            
            freebusy_result = self._service.freebusy().query(body=freebusy_query).execute()
            busy_times = freebusy_result['calendars'][calendar_id].get('busy', [])
            
            # Generate available slots
            available_slots = self._calculate_available_slots(date, busy_times, duration_minutes)
            
            logger.info(f"Found {len(available_slots)} available slots for {date.strftime('%Y-%m-%d')}")
            return available_slots
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return self._get_fallback_slots()
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return self._get_fallback_slots()
    
    def _calculate_available_slots(self, date: datetime, busy_times: List[Dict], duration_minutes: int) -> List[str]:
        """Calculate available time slots based on busy times."""
        # Business hours: 9:00 - 18:00
        start_hour = 9
        end_hour = 18
        slot_duration = timedelta(minutes=duration_minutes)
        
        available_slots = []
        current_time = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        
        while current_time + slot_duration <= end_time:
            slot_end = current_time + slot_duration
            
            # Check if this slot conflicts with any busy time
            is_available = True
            for busy_period in busy_times:
                busy_start = datetime.fromisoformat(busy_period['start'].replace('Z', '+00:00'))
                busy_end = datetime.fromisoformat(busy_period['end'].replace('Z', '+00:00'))
                
                # Convert to local timezone if needed
                if busy_start.tzinfo:
                    busy_start = busy_start.replace(tzinfo=None)
                if busy_end.tzinfo:
                    busy_end = busy_end.replace(tzinfo=None)
                
                # Check for overlap
                if not (slot_end <= busy_start or current_time >= busy_end):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(current_time.strftime('%H:%M'))
            
            # Move to next slot (30 minutes intervals)
            current_time += timedelta(minutes=30)
        
        return available_slots
    
    def _get_fallback_slots(self) -> List[str]:
        """Return default available slots when Google Calendar is not available."""
        return ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00']
    
    def create_event(self, calendar_id: str, event_data: Dict[str, Any]) -> Optional[str]:
        """Create a calendar event."""
        if not self.is_available:
            logger.warning("Google Calendar not available - cannot create event")
            return None
        
        try:
            event = self._service.events().insert(
                calendarId=calendar_id,
                body=event_data
            ).execute()
            
            logger.info(f"✅ Created calendar event: {event.get('id')}")
            return event.get('id')
            
        except HttpError as e:
            logger.error(f"Failed to create calendar event: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check for Google Calendar service."""
        health_status = {
            'service': 'Google Calendar',
            'status': 'healthy' if self.is_available else 'degraded',
            'credentials_source': self._get_credentials_source(),
            'timestamp': datetime.now().isoformat()
        }
        
        if self.is_available:
            try:
                # Test API call
                self._service.calendarList().list(maxResults=1).execute()
                health_status['api_test'] = 'passed'
            except Exception as e:
                health_status['status'] = 'unhealthy'
                health_status['api_test'] = f'failed: {str(e)}'
        
        return health_status
    
    def _get_credentials_source(self) -> str:
        """Get information about credentials source."""
        if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
            return 'environment_variable'
        elif hasattr(settings, 'google_service_account_file') and os.path.exists(settings.google_service_account_file):
            return 'service_account_file'
        else:
            return 'application_default_credentials'


# Global instance
google_calendar_service = GoogleCalendarService()