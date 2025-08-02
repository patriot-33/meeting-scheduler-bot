"""
Enhanced Google Calendar service with dual calendar support
Creates meetings in both manager and owner calendars
"""
import logging
import traceback
from datetime import datetime, timedelta
from config import settings
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class DualCalendarCreator:
    """Helper class to create meetings in both participant calendars."""
    
    def __init__(self, calendar_service):
        self.calendar_service = calendar_service
        logger.error(f"🚑 DualCalendarCreator initialized with service: {calendar_service}")
        logger.error(f"🚑 Service available: {getattr(calendar_service, 'is_available', 'NO_ATTR')}")
        
    def create_meeting_in_both_calendars(
        self,
        manager_calendar_id: str,
        owner_calendar_id: str,
        manager_name: str,
        owner_name: str,
        manager_email: Optional[str],
        owner_email: Optional[str],
        department: str,
        scheduled_time: datetime,
        time_str: str
    ) -> Dict[str, Any]:
        """
        Create the same meeting in both manager and owner calendars.
        Returns dict with event_ids and meet_link.
        """
        logger.error(f"🚑 EMERGENCY: create_meeting_in_both_calendars CALLED")
        logger.error(f"🚑 Manager calendar: {manager_calendar_id}")
        logger.error(f"🚑 Owner calendar: {owner_calendar_id}")
        logger.error(f"🚑 Time: {scheduled_time} / {time_str}")
        results = {
            'success': False,
            'manager_event_id': None,
            'owner_event_id': None,
            'meet_link': None,
            'errors': []
        }
        
        # Check if calendar service is available
        if not self.calendar_service:
            logger.error(f"🚑 NO CALENDAR SERVICE!")
            results['errors'].append("Calendar service not initialized")
            return results
            
        if not hasattr(self.calendar_service, '_service'):
            logger.error(f"🚑 Calendar service has no _service attribute!")
            results['errors'].append("Calendar service not properly initialized")
            return results
        
        # Parse time
        hour, minute = map(int, time_str.split(':'))
        start_time = scheduled_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=60)
        
        # Create base event data
        base_event_data = {
            'summary': f'Созвон с {department}',
            'description': f'''Еженедельный созвон
Руководитель: {manager_name}
Владелец: {owner_name}
Отдел: {department}

Встреча создана автоматически ботом.''',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/Moscow',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Europe/Moscow',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                    {'method': 'email', 'minutes': 1440},  # 24 hours
                ],
            },
        }
        
        # Add conference data with correct type
        conference_request_id = f"meet-{int(datetime.now().timestamp())}-{abs(hash(manager_calendar_id))}"
        base_event_data['conferenceData'] = {
            'createRequest': {
                'requestId': conference_request_id,
                'conferenceSolutionKey': {
                    'type': 'hangoutsMeet'  # Use hangoutsMeet for Service Account, will be changed for OAuth
                }
            }
        }
        
        # 1. Create in manager's calendar
        try:
            logger.info(f"Creating meeting in manager's calendar: {manager_calendar_id}")
            
            manager_event_data = base_event_data.copy()
            # Only add attendees for OAuth calendars
            is_manager_oauth = self._is_oauth_calendar(manager_calendar_id)
            
            # Adjust conference type based on calendar type
            if is_manager_oauth:
                manager_event_data['conferenceData']['createRequest']['conferenceSolutionKey']['type'] = 'eventHangout'
            
            if is_manager_oauth and owner_email and self._is_valid_email(owner_email):
                manager_event_data['attendees'] = [{
                    'email': owner_email,
                    'displayName': owner_name,
                    'optional': True,
                    'responseStatus': 'needsAction'
                }]
                logger.info(f"Adding owner {owner_name} ({owner_email}) as attendee to manager's OAuth calendar")
            elif is_manager_oauth and owner_email and not self._is_valid_email(owner_email):
                logger.warning(f"⚠️ Invalid owner email '{owner_email}' - creating meeting without owner as attendee")
            elif not is_manager_oauth:
                logger.info(f"🔒 Manager calendar is Service Account - not adding attendees")
            
            # Create event
            manager_event = self._create_event_with_fallback(
                manager_calendar_id, 
                manager_event_data,
                "manager"
            )
            
            if manager_event:
                results['manager_event_id'] = manager_event.get('id')
                results['meet_link'] = manager_event.get('hangoutLink', '')
                logger.info(f"✅ Created in manager's calendar: {results['manager_event_id']}")
            else:
                results['errors'].append("Failed to create in manager's calendar")
                
        except Exception as e:
            logger.error(f"Error creating in manager's calendar: {e}")
            results['errors'].append(f"Manager calendar error: {str(e)}")
        
        # 2. Create in owner's calendar (if different from manager)
        logger.info(f"🔍 Owner calendar check: owner_id={owner_calendar_id}, manager_id={manager_calendar_id}")
        if owner_calendar_id and owner_calendar_id != manager_calendar_id:
            try:
                logger.info(f"Creating meeting in owner's calendar: {owner_calendar_id}")
                
                owner_event_data = base_event_data.copy()
                # Only add attendees for OAuth calendars
                is_owner_oauth = self._is_oauth_calendar(owner_calendar_id)
                
                # Adjust conference type based on calendar type
                if is_owner_oauth:
                    owner_event_data['conferenceData']['createRequest']['conferenceSolutionKey']['type'] = 'eventHangout'
                
                if is_owner_oauth and manager_email and self._is_valid_email(manager_email):
                    owner_event_data['attendees'] = [{
                        'email': manager_email,
                        'displayName': manager_name,
                        'optional': True,
                        'responseStatus': 'needsAction'
                    }]
                    logger.info(f"Adding manager {manager_name} ({manager_email}) as attendee to owner's OAuth calendar")
                elif is_owner_oauth and manager_email and not self._is_valid_email(manager_email):
                    logger.warning(f"⚠️ Invalid manager email '{manager_email}' - creating meeting without manager as attendee")
                elif not is_owner_oauth:
                    logger.info(f"🔒 Owner calendar is Service Account - not adding attendees")
                
                # If we got a meet link from manager's event, add it to description but keep conferenceData
                if results['meet_link']:
                    # Add meet link to description (keep conferenceData to ensure Google Meet is created)
                    owner_event_data['description'] += f"\n\nGoogle Meet: {results['meet_link']}"
                    # Note: keeping conferenceData to ensure Google Meet functionality
                
                # Create event
                owner_event = self._create_event_with_fallback(
                    owner_calendar_id,
                    owner_event_data,
                    "owner"
                )
                
                if owner_event:
                    results['owner_event_id'] = owner_event.get('id')
                    # If no meet link yet, try to get from owner's event
                    if not results['meet_link']:
                        results['meet_link'] = owner_event.get('hangoutLink', '')
                    logger.info(f"✅ Created in owner's calendar: {results['owner_event_id']}")
                else:
                    results['errors'].append("Failed to create in owner's calendar")
                    
            except Exception as e:
                logger.error(f"Error creating in owner's calendar: {e}")
                results['errors'].append(f"Owner calendar error: {str(e)}")
        
        # Log final results for debugging
        logger.info(f"📊 DUAL CALENDAR RESULTS: Manager={results['manager_event_id']}, Owner={results['owner_event_id']}, Meet={results['meet_link']}")
        
        # Determine overall success
        results['success'] = bool(results['manager_event_id'] or results['owner_event_id'])
        
        return results
    
    def _create_event_with_fallback(self, calendar_id: str, event_data: dict, calendar_type: str):
        """Create event with OAuth-specific Google Meet conference creation - SINGLE CALL ONLY"""
        
        # EMERGENCY LOGGING - Log everything
        logger.error(f"🚑 EMERGENCY LOG: Starting _create_event_with_fallback")
        logger.error(f"🚑 Calendar ID: {calendar_id}")
        logger.error(f"🚑 Calendar Type: {calendar_type}")
        
        # Log the attempt for debugging
        has_conference = 'conferenceData' in event_data
        has_attendees = 'attendees' in event_data
        logger.info(f"📅 Creating event in {calendar_type}'s calendar: {calendar_id}")
        logger.info(f"🔍 Event details: conference={has_conference}, attendees={has_attendees}")
        
        # Log conference data details
        if has_conference:
            conf_type = event_data.get('conferenceData', {}).get('createRequest', {}).get('conferenceSolutionKey', {}).get('type', 'UNKNOWN')
            logger.error(f"🚑 Conference type: {conf_type}")
        
        # Detect calendar type: OAuth vs Service Account
        is_oauth_calendar = self._is_oauth_calendar(calendar_id)
        logger.info(f"🔍 Calendar type: {'OAuth' if is_oauth_calendar else 'Service Account'}")
        
        # SINGLE ATTEMPT - No multiple fallbacks to prevent duplication
        try:
            logger.error(f"🚑 ATTEMPTING API CALL: OAuth={is_oauth_calendar}")
            logger.error(f"🚑 Event data keys: {list(event_data.keys())}")
            
            if is_oauth_calendar:
                # OAuth calendars ALSO need conferenceDataVersion for Google Meet
                logger.error(f"🚑 Making OAuth calendar insert call")
                event = self.calendar_service._service.events().insert(
                    calendarId=calendar_id,
                    body=event_data,
                    conferenceDataVersion=1
                ).execute()
                logger.error(f"🚑 OAuth insert SUCCESS: {event.get('id', 'NO_ID')}")
            else:
                # Service Account calendars need conferenceDataVersion
                logger.error(f"🚑 Making Service Account calendar insert call")
                event = self.calendar_service._service.events().insert(
                    calendarId=calendar_id,
                    body=event_data,
                    conferenceDataVersion=1
                ).execute()
                logger.error(f"🚑 Service Account insert SUCCESS: {event.get('id', 'NO_ID')}")
            
            # Check if Google Meet was created
            if event.get('conferenceData') and event.get('conferenceData').get('conferenceId'):
                logger.info(f"✅ SUCCESS: Created event with Google Meet in {calendar_type}'s calendar")
                logger.info(f"🔗 Google Meet ID: {event.get('conferenceData').get('conferenceId')}")
                logger.info(f"🔗 Google Meet Link: {event.get('hangoutLink', 'Not available')}")
            else:
                logger.info(f"✅ SUCCESS: Created event (no Google Meet) in {calendar_type}'s calendar")
            
            return event
            
        except Exception as e:
            logger.error(f"❌ Failed to create event in {calendar_type}'s calendar: {e}")
            logger.error(f"🚑 FULL ERROR: {type(e).__name__}: {str(e)}")
            logger.error(f"🚑 TRACEBACK: {traceback.format_exc()}")
            return None

    def _is_valid_email(self, email: str) -> bool:
        """Check if email is valid and not empty."""
        if not email or not isinstance(email, str):
            return False
        
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
    
    def _is_oauth_calendar(self, calendar_id: str) -> bool:
        """Detect if calendar is OAuth-based vs Service Account based."""
        try:
            # IMPORTANT: Check database FIRST to determine if user connected via OAuth
            from database import get_db, User, UserRole
            with get_db() as db:
                oauth_user = db.query(User).filter(
                    User.google_calendar_id == calendar_id,
                    User.oauth_credentials.isnot(None)
                ).first()
                
                if oauth_user:
                    logger.info(f"🔍 Calendar {calendar_id} detected as OAuth (user: {oauth_user.first_name})")
                    return True
            
            # If not found in OAuth users, it's a Service Account calendar
            logger.info(f"🔍 Calendar {calendar_id} detected as Service Account (not found in OAuth users)")
            return False
            
        except Exception as e:
            logger.warning(f"Could not determine calendar type for {calendar_id}: {e}")
            # Default to Service Account approach
            return False
    
    def delete_meeting_from_both_calendars(
        self,
        event_id: str,
        manager_calendar_id: Optional[str] = None,
        owner_calendar_id: Optional[str] = None,
        manager_oauth_credentials: Optional[dict] = None,
        owner_oauth_credentials: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Delete meeting from both manager and owner calendars using proper credentials.
        
        Args:
            event_id: Google Calendar event ID
            manager_calendar_id: Manager's calendar ID
            owner_calendar_id: Owner's calendar ID
            manager_oauth_credentials: Manager's OAuth credentials for their calendar
            owner_oauth_credentials: Owner's OAuth credentials for their calendar
        
        Returns:
            Dict with success status, deleted calendars count, and errors
        """
        results = {
            'success': False,
            'deleted_from_manager': False,
            'deleted_from_owner': False,
            'total_deleted': 0,
            'errors': []
        }
        
        # Delete from manager's calendar
        if manager_calendar_id:
            try:
                success = self._delete_from_calendar(
                    event_id, 
                    manager_calendar_id, 
                    "manager",
                    manager_oauth_credentials
                )
                if success:
                    results['deleted_from_manager'] = True
                    results['total_deleted'] += 1
                    logger.info(f"✅ Deleted event {event_id} from manager's calendar: {manager_calendar_id}")
                else:
                    results['errors'].append("Failed to delete from manager's calendar")
            except Exception as e:
                logger.error(f"Error deleting from manager's calendar: {e}")
                results['errors'].append(f"Manager calendar deletion error: {str(e)}")
        
        # Delete from owner's calendar (if different from manager)
        if owner_calendar_id and owner_calendar_id != manager_calendar_id:
            try:
                success = self._delete_from_calendar(
                    event_id, 
                    owner_calendar_id, 
                    "owner",
                    owner_oauth_credentials
                )
                if success:
                    results['deleted_from_owner'] = True
                    results['total_deleted'] += 1
                    logger.info(f"✅ Deleted event {event_id} from owner's calendar: {owner_calendar_id}")
                else:
                    results['errors'].append("Failed to delete from owner's calendar")
            except Exception as e:
                logger.error(f"Error deleting from owner's calendar: {e}")
                results['errors'].append(f"Owner calendar deletion error: {str(e)}")
        
        # Determine overall success
        results['success'] = results['total_deleted'] > 0
        
        if results['success']:
            logger.info(f"✅ Successfully deleted event from {results['total_deleted']} calendar(s)")
        else:
            logger.error(f"❌ Failed to delete event from any calendar. Errors: {results['errors']}")
            
        return results
    
    def delete_meeting_from_both_calendars_dual(
        self,
        manager_event_id: str,
        owner_event_id: str,
        manager_calendar_id: Optional[str] = None,
        owner_calendar_id: Optional[str] = None,
        manager_oauth_credentials: Optional[dict] = None,
        owner_oauth_credentials: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Delete meeting from both calendars using specific event IDs for each calendar.
        
        Args:
            manager_event_id: Event ID in manager's calendar
            owner_event_id: Event ID in owner's calendar  
            manager_calendar_id: Manager's calendar ID
            owner_calendar_id: Owner's calendar ID
            manager_oauth_credentials: Manager's OAuth credentials
            owner_oauth_credentials: Owner's OAuth credentials
        
        Returns:
            Dict with success status, deleted calendars count, and errors
        """
        results = {
            'success': False,
            'deleted_from_manager': False,
            'deleted_from_owner': False,
            'total_deleted': 0,
            'errors': []
        }
        
        # Delete from manager's calendar
        if manager_calendar_id and manager_event_id:
            try:
                success = self._delete_from_calendar(
                    manager_event_id, 
                    manager_calendar_id, 
                    "manager",
                    manager_oauth_credentials
                )
                if success:
                    results['deleted_from_manager'] = True
                    results['total_deleted'] += 1
                    logger.info(f"✅ Deleted event {manager_event_id} from manager's calendar: {manager_calendar_id}")
                else:
                    results['errors'].append("Failed to delete from manager's calendar")
            except Exception as e:
                logger.error(f"Error deleting from manager's calendar: {e}")
                results['errors'].append(f"Manager calendar deletion error: {str(e)}")
        
        # Delete from owner's calendar (if different event ID and calendar)
        if owner_calendar_id and owner_event_id and (
            owner_event_id != manager_event_id or owner_calendar_id != manager_calendar_id
        ):
            try:
                success = self._delete_from_calendar(
                    owner_event_id, 
                    owner_calendar_id, 
                    "owner",
                    owner_oauth_credentials
                )
                if success:
                    results['deleted_from_owner'] = True
                    results['total_deleted'] += 1
                    logger.info(f"✅ Deleted event {owner_event_id} from owner's calendar: {owner_calendar_id}")
                else:
                    results['errors'].append("Failed to delete from owner's calendar")
            except Exception as e:
                logger.error(f"Error deleting from owner's calendar: {e}")
                results['errors'].append(f"Owner calendar deletion error: {str(e)}")
        
        # Determine overall success
        results['success'] = results['total_deleted'] > 0
        
        if results['success']:
            logger.info(f"✅ Successfully deleted meeting from {results['total_deleted']} calendar(s)")
        else:
            logger.error(f"❌ Failed to delete meeting from any calendar. Errors: {results['errors']}")
            
        return results
    
    def _delete_from_calendar(
        self, 
        event_id: str, 
        calendar_id: str, 
        calendar_type: str,
        oauth_credentials: Optional[dict] = None
    ) -> bool:
        """
        Delete event from specific calendar using appropriate credentials.
        
        Args:
            event_id: Google Calendar event ID
            calendar_id: Calendar ID to delete from
            calendar_type: "manager" or "owner" for logging
            oauth_credentials: OAuth credentials for this specific calendar
        
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # If we have OAuth credentials for this specific calendar, use them
            if oauth_credentials:
                logger.info(f"Using OAuth credentials for {calendar_type} calendar deletion")
                
                # Create OAuth service for specific user
                from services.oauth_service import ManagerOAuthService
                oauth_service = ManagerOAuthService()
                user_calendar_service = oauth_service.create_calendar_service_from_credentials(oauth_credentials)
                
                if user_calendar_service:
                    # Delete using OAuth service
                    user_calendar_service.events().delete(
                        calendarId=calendar_id,
                        eventId=event_id
                    ).execute()
                    
                    logger.info(f"✅ Successfully deleted event {event_id} from {calendar_type} calendar {calendar_id} using OAuth")
                else:
                    # Fallback to Service Account if OAuth failed
                    logger.warning(f"Failed to create OAuth service, falling back to Service Account for {calendar_type}")
                    self.calendar_service._service.events().delete(
                        calendarId=calendar_id,
                        eventId=event_id
                    ).execute()
                    
                    logger.info(f"✅ Successfully deleted event {event_id} from {calendar_type} calendar {calendar_id} using Service Account fallback")
            else:
                # Fallback to main service (Service Account)
                logger.info(f"Using Service Account for {calendar_type} calendar deletion")
                self.calendar_service._service.events().delete(
                    calendarId=calendar_id,
                    eventId=event_id
                ).execute()
                
                logger.info(f"✅ Successfully deleted event {event_id} from {calendar_type} calendar {calendar_id} using Service Account")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete event {event_id} from {calendar_type} calendar {calendar_id}: {e}")
            return False