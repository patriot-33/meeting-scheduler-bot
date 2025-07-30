"""
Public OAuth service for manager self-service calendar integration.
Uses Google's implicit flow without client secret.
"""
import logging
import secrets
import json
from typing import Optional, Dict, Any
from urllib.parse import urlencode, quote
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import settings
from database import get_db, User

logger = logging.getLogger(__name__)

class PublicOAuthService:
    """
    OAuth service that doesn't require client_secret.
    Managers can connect their calendars without admin intervention.
    """
    
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        # Public client ID (no secret required)
        self.public_client_id = settings.google_oauth_client_id or "YOUR_PUBLIC_CLIENT_ID.apps.googleusercontent.com"
        self.redirect_uri = f"{settings.webhook_url}/oauth/callback"
        
    def generate_auth_url_implicit(self, telegram_id: int) -> str:
        """
        Generate OAuth URL using implicit grant flow.
        No client_secret required - suitable for public clients.
        """
        try:
            if not settings.webhook_url:
                logger.error("Webhook URL not configured")
                return None
            
            # Generate state for security
            state = secrets.token_urlsafe(32)
            self._store_oauth_state(telegram_id, state)
            
            # Build OAuth URL manually for implicit flow
            params = {
                'client_id': self.public_client_id,
                'redirect_uri': self.redirect_uri,
                'response_type': 'token',  # Implicit flow
                'scope': ' '.join(self.scopes),
                'state': f"{telegram_id}:{state}",
                'access_type': 'offline',
                'prompt': 'consent'
            }
            
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
            
            logger.info(f"Generated implicit OAuth URL for manager {telegram_id}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating implicit OAuth URL: {e}")
            return None
    
    def generate_device_code_url(self, telegram_id: int) -> Dict[str, Any]:
        """
        Generate OAuth using Device Code flow.
        Perfect for Telegram bots - no redirect needed!
        """
        try:
            import requests
            
            # Request device code
            response = requests.post('https://oauth2.googleapis.com/device/code', data={
                'client_id': self.public_client_id,
                'scope': ' '.join(self.scopes)
            })
            
            if response.status_code != 200:
                logger.error(f"Device code request failed: {response.text}")
                return None
            
            device_data = response.json()
            
            # Store device code for later verification
            self._store_device_code(telegram_id, device_data['device_code'])
            
            return {
                'verification_url': device_data['verification_url'],
                'user_code': device_data['user_code'],
                'expires_in': device_data['expires_in'],
                'interval': device_data.get('interval', 5),
                'device_code': device_data['device_code']
            }
            
        except Exception as e:
            logger.error(f"Error with device code flow: {e}")
            return None
    
    def poll_device_code(self, telegram_id: int, device_code: str) -> Optional[Dict[str, Any]]:
        """
        Poll for device code authorization completion.
        Should be called periodically until user authorizes.
        """
        try:
            import requests
            
            response = requests.post('https://oauth2.googleapis.com/token', data={
                'client_id': self.public_client_id,
                'device_code': device_code,
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
            })
            
            if response.status_code == 200:
                # Success! User authorized
                token_data = response.json()
                
                # Create credentials
                credentials = Credentials(
                    token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token'),
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=self.public_client_id,
                    client_secret=None,  # No secret for public client
                    scopes=self.scopes
                )
                
                # Get calendar info
                calendar_service = build('calendar', 'v3', credentials=credentials)
                calendar_info = calendar_service.calendarList().get(calendarId='primary').execute()
                
                # Save to database
                self._save_manager_credentials(
                    telegram_id=telegram_id,
                    credentials=credentials,
                    calendar_id=calendar_info['id'],
                    email=calendar_info.get('summary', '')
                )
                
                return {
                    'success': True,
                    'email': calendar_info.get('summary', ''),
                    'calendar_id': calendar_info['id']
                }
                
            elif response.status_code == 428:
                # Still waiting for user authorization
                return {'success': False, 'status': 'pending'}
                
            elif response.status_code == 403:
                # User denied access
                return {'success': False, 'status': 'denied'}
                
            else:
                # Other error
                logger.error(f"Device code poll error: {response.text}")
                return {'success': False, 'status': 'error'}
                
        except Exception as e:
            logger.error(f"Error polling device code: {e}")
            return {'success': False, 'status': 'error'}
    
    def _store_oauth_state(self, telegram_id: int, state: str):
        """Store OAuth state temporarily."""
        if not hasattr(self, '_oauth_states'):
            self._oauth_states = {}
        
        self._oauth_states[telegram_id] = {
            'state': state,
            'expires': datetime.now() + timedelta(minutes=10)
        }
    
    def _store_device_code(self, telegram_id: int, device_code: str):
        """Store device code temporarily."""
        if not hasattr(self, '_device_codes'):
            self._device_codes = {}
        
        self._device_codes[telegram_id] = {
            'device_code': device_code,
            'expires': datetime.now() + timedelta(minutes=10)
        }
    
    def _save_manager_credentials(self, telegram_id: int, credentials: Credentials, 
                                calendar_id: str, email: str):
        """Save manager's OAuth credentials to database."""
        try:
            with get_db() as db:
                user = db.query(User).filter(User.telegram_id == telegram_id).first()
                
                if user:
                    user.oauth_credentials = credentials.to_json()
                    user.google_calendar_id = calendar_id
                    user.email = email
                    db.commit()
                    logger.info(f"Saved credentials for manager {telegram_id}")
                else:
                    logger.error(f"Manager {telegram_id} not found in database")
                    
        except Exception as e:
            logger.error(f"Error saving manager credentials: {e}")
            raise

# Global instance
public_oauth_service = PublicOAuthService()