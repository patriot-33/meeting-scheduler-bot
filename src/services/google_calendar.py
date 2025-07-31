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
    
    def get_service_account_email(self) -> Optional[str]:
        """Get service account email for calendar sharing."""
        try:
            if self._credentials and hasattr(self._credentials, 'service_account_email'):
                return self._credentials.service_account_email
            
            # Try to get from environment variable
            google_credentials_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if google_credentials_json:
                credentials_info = json.loads(google_credentials_json)
                return credentials_info.get('client_email')
            
            # Try to get from file
            if settings.google_service_account_file and os.path.exists(settings.google_service_account_file):
                with open(settings.google_service_account_file, 'r') as f:
                    credentials_info = json.load(f)
                    return credentials_info.get('client_email')
                    
        except Exception as e:
            logger.error(f"Error getting service account email: {e}")
        
        return None
    
    def test_calendar_access(self, calendar_id: str) -> Dict[str, Any]:
        """Test if service account has access to a calendar."""
        try:
            if not self._is_available:
                return {'success': False, 'error': 'Google Calendar service not available'}
            
            # Try to get calendar metadata
            calendar = self._service.calendars().get(calendarId=calendar_id).execute()
            
            # Try to list a few events to verify read access
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self._service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=1,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return {
                'success': True,
                'summary': calendar.get('summary', 'Unknown'),
                'description': calendar.get('description', ''),
                'timeZone': calendar.get('timeZone', 'UTC'),
                'backgroundColor': calendar.get('backgroundColor', '#1a73e8'),
                'accessRole': calendar.get('accessRole', 'unknown'),
                'canWrite': calendar.get('accessRole') in ['writer', 'owner'],
                'eventsCount': len(events_result.get('items', []))
            }
            
        except HttpError as e:
            error_details = json.loads(e.content.decode('utf-8'))
            error_message = error_details.get('error', {}).get('message', str(e))
            
            if e.resp.status == 404:
                return {'success': False, 'error': f'Calendar not found: {calendar_id}'}
            elif e.resp.status == 403:
                return {'success': False, 'error': f'No access to calendar: {error_message}'}
            else:
                return {'success': False, 'error': f'API Error: {error_message}'}
                
        except Exception as e:
            logger.error(f"Error testing calendar access: {e}")
            return {'success': False, 'error': str(e)}
    
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
                body=event_data,
                conferenceDataVersion=1 if 'conferenceData' in event_data else 0
            ).execute()
            
            logger.info(f"✅ Created calendar event: {event.get('id')}")
            return event.get('id'), event.get('hangoutLink', '')
            
        except HttpError as e:
            if 'Invalid conference type value' in str(e) and 'conferenceData' in event_data:
                logger.warning(f"Conference creation failed: {e}")
                logger.info("Retrying without conferenceData...")
                # Remove conferenceData and try again
                event_data_fallback = event_data.copy()
                event_data_fallback.pop('conferenceData', None)
                try:
                    event = self._service.events().insert(
                        calendarId=calendar_id,
                        body=event_data_fallback
                    ).execute()
                    logger.info("✅ Created event without Google Meet link due to API restrictions")
                    return event.get('id'), ''
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    return None, None
            else:
                logger.error(f"Failed to create calendar event: {e}")
                return None, None
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return None, None
    
    def create_meeting_with_owners(self, manager_calendar_id: str, manager_name: str, 
                                 department: str, date: datetime, time_str: str, 
                                 owner_emails: List[str], manager_email: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        """BULLETPROOF: Create meeting with fallback strategies for Service Account limitations."""
        if not self.is_available:
            logger.warning("Google Calendar not available - cannot create meeting")
            return None, None
        
        # BULLETPROOF: Check configuration to decide strategy
        if settings.google_calendar_force_attendee_free:
            logger.info("🔧 BULLETPROOF: Using attendee-free strategy (forced by configuration)")
            return self._create_without_attendees_strategy(manager_calendar_id, manager_name, department, 
                                                         date, time_str, owner_emails, manager_email)
        
        try:
            # BULLETPROOF STRATEGY 1: Try with attendees only if enabled
            if settings.google_calendar_try_attendees:
                logger.info("🔧 BULLETPROOF: Trying attendees strategy first")
                return self._create_with_attendees_strategy(manager_calendar_id, manager_name, department, 
                                                          date, time_str, owner_emails, manager_email)
            else:
                logger.info("🔧 BULLETPROOF: Attendees strategy disabled, using attendee-free strategy")
                return self._create_without_attendees_strategy(manager_calendar_id, manager_name, department, 
                                                             date, time_str, owner_emails, manager_email)
            
        except HttpError as e:
            # Check if it's the specific Domain-Wide Delegation error
            if 'forbiddenForServiceAccounts' in str(e) or 'Service accounts cannot invite attendees' in str(e):
                logger.warning("🔧 BULLETPROOF FALLBACK: Domain-Wide Delegation not configured, using attendee-free strategy")
                return self._create_without_attendees_strategy(manager_calendar_id, manager_name, department, 
                                                             date, time_str, owner_emails, manager_email)
            else:
                logger.error(f"Failed to create meeting: {e}")
                return None, None
        except Exception as e:
            logger.error(f"Error creating meeting: {e}")
            return None, None

    def _create_with_attendees_strategy(self, manager_calendar_id: str, manager_name: str, 
                                      department: str, date: datetime, time_str: str, 
                                      owner_emails: List[str], manager_email: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        """Strategy 1: Create meeting with attendees (requires Domain-Wide Delegation)."""
        
        # Parse time
        hour, minute = map(int, time_str.split(':'))
        start_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=60)  # 1 hour meeting
        
        # Create attendees list
        attendees = []
        
        # Add owners as attendees
        for email in owner_emails:
            attendees.append({
                'email': email,
                'responseStatus': 'needsAction'
            })
        
        # Add manager if email provided
        if manager_email:
            attendees.append({
                'email': manager_email,
                'displayName': manager_name,
                'responseStatus': 'accepted'  # Manager accepts by default
            })
        
        # Create event data WITH attendees
        event_data = {
            'summary': f'Созвон с {department}',
            'description': f'Еженедельный созвон с руководителем отдела {department}\nРуководитель: {manager_name}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/Moscow',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Europe/Moscow',
            },
            'attendees': attendees,  # WILL CAUSE ERROR WITHOUT DOMAIN-WIDE DELEGATION
            # NOTE: conferenceData removed due to API restrictions
            # Google Meet links require specific API permissions
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                    {'method': 'email', 'minutes': 1440},  # 24 hours
                ],
            },
        }
        
        # Create event in manager's calendar WITH sendUpdates
        try:
            event = self._service.events().insert(
                calendarId=manager_calendar_id,
                body=event_data,
                conferenceDataVersion=1,
                sendUpdates='all'  # WILL CAUSE ERROR WITHOUT DOMAIN-WIDE DELEGATION
            ).execute()
        except Exception as conference_error:
            logger.warning(f"Failed to create event with conferenceData: {conference_error}")
            logger.info("Trying to create event without conferenceData...")
            # Remove conferenceData and try again
            event_data_fallback = event_data.copy()
            event_data_fallback.pop('conferenceData', None)
            event = self._service.events().insert(
                calendarId=manager_calendar_id,
                body=event_data_fallback,
                sendUpdates='all'
            ).execute()
            logger.info("✅ Created event without Google Meet link due to API restrictions")
        
        event_id = event.get('id')
        meet_link = event.get('hangoutLink', '')
        
        logger.info(f"✅ STRATEGY 1 SUCCESS: Created meeting with attendees in {manager_calendar_id}: {event_id}")
        logger.info(f"✅ Google Meet link: {meet_link}")
        logger.info(f"✅ Attendees invited via Google Calendar: {len(attendees)}")
        
        return event_id, meet_link

    def _create_without_attendees_strategy(self, manager_calendar_id: str, manager_name: str, 
                                         department: str, date: datetime, time_str: str, 
                                         owner_emails: List[str], manager_email: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        """BULLETPROOF Strategy 2: Create meeting without attendees, notify via Telegram."""
        
        # Parse time
        hour, minute = map(int, time_str.split(':'))
        start_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=60)  # 1 hour meeting
        
        # Build participant list for description
        participants_text = f"\n\nУчастники встречи:\n• {manager_name} (Руководитель {department})"
        for email in owner_emails:
            if email:
                participants_text += f"\n• {email}"
        if manager_email and manager_email not in owner_emails:
            participants_text += f"\n• {manager_email}"
        
        # Create event data WITHOUT attendees
        event_data = {
            'summary': f'Созвон с {department}',
            'description': f'Еженедельный созвон с руководителем отдела {department}\nРуководитель: {manager_name}{participants_text}\n\n⚠️ Уведомления отправлены через Telegram Bot',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/Moscow',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Europe/Moscow',
            },
            # NO attendees field - this avoids the Service Account error
            # NOTE: conferenceData removed due to API restrictions
            # Google Meet links require specific API permissions
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        
        # Create event in manager's calendar WITHOUT sendUpdates
        event = self._service.events().insert(
            calendarId=manager_calendar_id,
            body=event_data
            # NO conferenceDataVersion - not needed without conferenceData
            # NO sendUpdates - this avoids the Service Account error
        ).execute()
        
        event_id = event.get('id')
        meet_link = event.get('hangoutLink', '')
        
        logger.info(f"✅ STRATEGY 2 SUCCESS: Created meeting without attendees in {manager_calendar_id}: {event_id}")
        logger.info(f"✅ Google Meet link: {meet_link}")
        logger.info(f"📱 Participants will be notified via Telegram Bot instead of Google Calendar")
        
        # Try to duplicate event to other participants' calendars
        self._duplicate_event_to_participants(event_data, manager_calendar_id, owner_emails, manager_email)
        
        return event_id, meet_link
    
    def _duplicate_event_to_participants(self, event_data: dict, primary_calendar_id: str, 
                                       owner_emails: List[str], manager_email: Optional[str]):
        """Duplicate event to other participants' calendars if they have OAuth connected."""
        try:
            logger.info(f"📋 DUPLICATION: Attempting to duplicate event to other participants")
            logger.info(f"📋 DUPLICATION: Primary calendar: {primary_calendar_id}")
            logger.info(f"📋 DUPLICATION: Target emails: {owner_emails + ([manager_email] if manager_email else [])}")
            
            # Skip duplication for now due to database session conflicts
            # TODO: Implement async duplication in background task
            logger.info("📋 DUPLICATION: Skipped for now - will be implemented in background task")
                            
        except Exception as e:
            logger.warning(f"⚠️ DUPLICATION ERROR: {e}")
    
    def cancel_meeting(self, event_id: str) -> bool:
        """Cancel a meeting in Google Calendar by event ID."""
        if not self.is_available:
            logger.warning("Google Calendar not available - cannot cancel meeting")
            return False
        
        if not event_id:
            logger.error("No event ID provided for cancellation")
            return False
        
        try:
            # Delete the event from Google Calendar
            self._service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"Successfully cancelled Google Calendar event: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling Google Calendar event {event_id}: {e}")
            return False
    
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