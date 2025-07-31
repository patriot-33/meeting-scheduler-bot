"""
Enhanced Google Calendar service with dual calendar support
Creates meetings in both manager and owner calendars
"""
import logging
from datetime import datetime, timedelta
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
                    'requestId': f"meet-{int(datetime.now().timestamp())}-{hash(manager_calendar_id)}",
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
            # Add owner as optional attendee if email available
            if owner_email:
                manager_event_data['attendees'] = [{
                    'email': owner_email,
                    'displayName': owner_name,
                    'optional': True,
                    'responseStatus': 'needsAction'
                }]
            
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
                # Add manager as optional attendee if email available
                if manager_email:
                    owner_event_data['attendees'] = [{
                        'email': manager_email,
                        'displayName': manager_name,
                        'optional': True,
                        'responseStatus': 'needsAction'
                    }]
                
                # If we got a meet link from manager's event, reuse it
                if results['meet_link']:
                    # Remove conferenceData to avoid creating new meet
                    owner_event_data.pop('conferenceData', None)
                    # Add meet link to description
                    owner_event_data['description'] += f"\n\nGoogle Meet: {results['meet_link']}"
                
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
        """Create event with fallback for conference data errors."""
        try:
            # First try with conference data
            if 'conferenceData' in event_data:
                try:
                    event = self.calendar_service._service.events().insert(
                        calendarId=calendar_id,
                        body=event_data,
                        conferenceDataVersion=1
                    ).execute()
                    logger.info(f"✅ Created event with Google Meet in {calendar_type}'s calendar")
                    return event
                except Exception as conf_error:
                    logger.warning(f"Conference creation failed for {calendar_type}: {conf_error}")
                    # Remove conference data and try again
                    event_data_fallback = event_data.copy()
                    event_data_fallback.pop('conferenceData', None)
                    event = self.calendar_service._service.events().insert(
                        calendarId=calendar_id,
                        body=event_data_fallback
                    ).execute()
                    logger.info(f"✅ Created event without Google Meet in {calendar_type}'s calendar")
                    return event
            else:
                # No conference data, create directly
                event = self.calendar_service._service.events().insert(
                    calendarId=calendar_id,
                    body=event_data
                ).execute()
                return event
                
        except Exception as e:
            logger.error(f"Failed to create event in {calendar_type}'s calendar: {e}")
            return None