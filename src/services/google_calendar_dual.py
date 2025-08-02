"""
Enhanced Google Calendar service with dual calendar support
Creates meetings in both manager and owner calendars
"""
import logging
from datetime import datetime, timedelta
from config import settings
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class DualCalendarCreator:
    """Helper class to create meetings in both participant calendars."""
    
    def __init__(self, calendar_service):
        self.calendar_service = calendar_service
        
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
        results = {
            'success': False,
            'manager_event_id': None,
            'owner_event_id': None,
            'meet_link': None,
            'errors': []
        }
        
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
            'conferenceData': {
                'createRequest': {
                    'requestId': f"meet-{int(datetime.now().timestamp())}-{abs(hash(manager_calendar_id))}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                    {'method': 'email', 'minutes': 1440},  # 24 hours
                ],
            },
        }
        
        # 1. Create in manager's calendar
        try:
            logger.info(f"Creating meeting in manager's calendar: {manager_calendar_id}")
            
            manager_event_data = base_event_data.copy()
            # Add owner as optional attendee if email available (OAuth calendars support attendees)
            if owner_email and self._is_valid_email(owner_email):
                manager_event_data['attendees'] = [{
                    'email': owner_email,
                    'displayName': owner_name,
                    'optional': True,
                    'responseStatus': 'needsAction'
                }]
                logger.info(f"Adding owner {owner_name} ({owner_email}) as attendee to manager's calendar")
            elif owner_email and not self._is_valid_email(owner_email):
                logger.warning(f"⚠️ Invalid owner email '{owner_email}' - creating meeting without owner as attendee")
            
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
        if owner_calendar_id and owner_calendar_id != manager_calendar_id:
            try:
                logger.info(f"Creating meeting in owner's calendar: {owner_calendar_id}")
                
                owner_event_data = base_event_data.copy()
                # Add manager as optional attendee if email available (OAuth calendars support attendees)
                if manager_email and self._is_valid_email(manager_email):
                    owner_event_data['attendees'] = [{
                        'email': manager_email,
                        'displayName': manager_name,
                        'optional': True,
                        'responseStatus': 'needsAction'
                    }]
                    logger.info(f"Adding manager {manager_name} ({manager_email}) as attendee to owner's calendar")
                elif manager_email and not self._is_valid_email(manager_email):
                    logger.warning(f"⚠️ Invalid manager email '{manager_email}' - creating meeting without manager as attendee")
                
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
        
        # Determine overall success
        results['success'] = bool(results['manager_event_id'] or results['owner_event_id'])
        
        return results
    
    def _create_event_with_fallback(self, calendar_id: str, event_data: dict, calendar_type: str):
        """Create event with improved Google Meet conference creation."""
        
        # Log the attempt for debugging
        has_conference = 'conferenceData' in event_data
        has_attendees = 'attendees' in event_data
        logger.info(f"📅 Creating event in {calendar_type}'s calendar: {calendar_id}")
        logger.info(f"🔍 Event details: conference={has_conference}, attendees={has_attendees}")
        
        # Strategy 1: Try multiple conferenceDataVersion values
        if has_conference:
            for version in [1, 0]:  # Try both conference data versions
                try:
                    logger.info(f"🔄 Attempting Google Meet creation with conferenceDataVersion={version}")
                    
                    if version == 0:
                        # For version 0, try without conferenceDataVersion parameter
                        event = self.calendar_service._service.events().insert(
                            calendarId=calendar_id,
                            body=event_data
                        ).execute()
                    else:
                        # For version 1, explicitly set conferenceDataVersion
                        event = self.calendar_service._service.events().insert(
                            calendarId=calendar_id,
                            body=event_data,
                            conferenceDataVersion=version
                        ).execute()
                    
                    # Check if Google Meet was actually created
                    if event.get('conferenceData') and event.get('conferenceData').get('conferenceId'):
                        logger.info(f"✅ SUCCESS: Created event with Google Meet in {calendar_type}'s calendar")
                        logger.info(f"🔗 Google Meet ID: {event.get('conferenceData').get('conferenceId')}")
                        return event
                    else:
                        logger.warning(f"⚠️ Event created but no Google Meet generated (version {version})")
                        # Continue to try other versions or fallbacks
                        
                except Exception as version_error:
                    logger.warning(f"❌ conferenceDataVersion {version} failed: {version_error}")
                    continue
        
        # Strategy 2: Try alternative conference data formats
        if has_conference:
            logger.info("🔄 Trying alternative Google Meet formats...")
            
            alternative_formats = [
                # Format 1: Minimal conference request
                {
                    'conferenceData': {
                        'createRequest': {
                            'requestId': f"meet-min-{int(datetime.now().timestamp())}"
                        }
                    }
                },
                # Format 2: Explicit hangouts meet request  
                {
                    'conferenceData': {
                        'createRequest': {
                            'requestId': f"meet-hang-{int(datetime.now().timestamp())}",
                            'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                        }
                    }
                },
                # Format 3: Conference with entry points
                {
                    'conferenceData': {
                        'conferenceSolution': {
                            'key': {'type': 'hangoutsMeet'},
                            'name': 'Google Meet',
                            'iconUri': 'https://fonts.gstatic.com/s/i/productlogos/meet_2020q4/v6/web-512dp/logo_meet_2020q4_color_2x_web_512dp.png'
                        },
                        'createRequest': {
                            'requestId': f"meet-alt-{int(datetime.now().timestamp())}"
                        }
                    }
                }
            ]
            
            for i, alt_format in enumerate(alternative_formats):
                try:
                    alt_event_data = event_data.copy()
                    alt_event_data.update(alt_format)
                    
                    logger.info(f"🔄 Trying alternative format {i+1}/3")
                    event = self.calendar_service._service.events().insert(
                        calendarId=calendar_id,
                        body=alt_event_data,
                        conferenceDataVersion=1
                    ).execute()
                    
                    # Verify Google Meet was created
                    if event.get('conferenceData') and event.get('conferenceData').get('conferenceId'):
                        logger.info(f"✅ SUCCESS: Alternative format {i+1} created Google Meet!")
                        return event
                    else:
                        logger.warning(f"⚠️ Alternative format {i+1} created event but no Google Meet")
                        
                except Exception as alt_error:
                    logger.warning(f"❌ Alternative format {i+1} failed: {alt_error}")
                    continue
        
        # Strategy 3: Handle attendee errors but keep trying Google Meet
        if has_attendees:
            logger.info("🔄 Retrying without attendees but keeping Google Meet...")
            try:
                no_attendees_data = event_data.copy()
                no_attendees_data.pop('attendees', None)
                
                event = self.calendar_service._service.events().insert(
                    calendarId=calendar_id,
                    body=no_attendees_data,
                    conferenceDataVersion=1
                ).execute()
                
                if event.get('conferenceData'):
                    logger.info(f"✅ SUCCESS: Created Google Meet without attendees in {calendar_type}'s calendar")
                    return event
                else:
                    logger.warning(f"⚠️ Event created without attendees but no Google Meet")
                    
            except Exception as no_attendees_error:
                logger.warning(f"❌ No attendees attempt failed: {no_attendees_error}")
        
        # Strategy 4: Create basic event without Google Meet (last resort)
        logger.warning(f"⚠️ FALLBACK: Creating basic event without Google Meet in {calendar_type}'s calendar")
        try:
            basic_event_data = event_data.copy()
            basic_event_data.pop('conferenceData', None)
            basic_event_data.pop('attendees', None)
            
            event = self.calendar_service._service.events().insert(
                calendarId=calendar_id,
                body=basic_event_data
            ).execute()
            
            logger.info(f"✅ Created basic event (no Google Meet) in {calendar_type}'s calendar")
            return event
            
        except Exception as basic_error:
            logger.error(f"❌ CRITICAL: Even basic event creation failed in {calendar_type}'s calendar: {basic_error}")
            return None
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if email is valid and not empty."""
        if not email or not isinstance(email, str):
            return False
        
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
    
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