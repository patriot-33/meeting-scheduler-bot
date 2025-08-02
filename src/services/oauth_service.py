"""
OAuth 2.0 service for manager Google Calendar integration
"""
import logging
import secrets
import json
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config import settings
from database import get_db, User

logger = logging.getLogger(__name__)

class ManagerOAuthService:
    """OAuth service for manager Google Calendar integration."""
    
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        self.redirect_uri = f"{settings.webhook_url}/oauth/callback"
        
    @property
    def is_oauth_configured(self) -> bool:
        """Check if OAuth Client is properly configured."""
        return settings.validate_oauth_client_config()
        
    def generate_auth_url(self, telegram_id: int) -> str:
        """Generate OAuth authorization URL for manager."""
        try:
            # Check OAuth Client configuration (NOT Service Account!)
            if not settings.validate_oauth_client_config():
                logger.error("Google OAuth Client not configured. Use GOOGLE_OAUTH_CLIENT_JSON or oauth_client_key.json file")
                return None
            
            if not settings.webhook_url:
                logger.error("Webhook URL not configured for OAuth callback")
                return None
                
            # Get OAuth Client configuration
            google_config = settings.get_oauth_client_config()
            if not google_config:
                logger.error("Failed to load OAuth Client configuration")
                return None
                
            # Validate OAuth Client structure
            if 'web' in google_config:
                client_config = google_config['web']
            elif 'installed' in google_config:
                client_config = google_config['installed'] 
            else:
                logger.error("Invalid OAuth Client JSON - must contain 'web' or 'installed' section")
                return None
                
            if 'client_id' not in client_config or 'client_secret' not in client_config:
                logger.error("Invalid OAuth Client JSON - missing client_id or client_secret")
                return None
            
            # Create OAuth flow with proper client config
            flow = Flow.from_client_config(
                google_config,
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Generate state parameter for security
            state = secrets.token_urlsafe(32)
            
            # Store state temporarily (в продакшене лучше использовать Redis)
            self._store_oauth_state(telegram_id, state)
            
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=f"{telegram_id}:{state}",
                prompt='consent'  # Force consent to get refresh token
            )
            
            logger.info(f"Generated OAuth URL for manager {telegram_id}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating OAuth URL: {e}")
            return None
    
    def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for tokens."""
        try:
            # Parse state parameter
            if ':' not in state:
                raise ValueError("Invalid state parameter")
            
            telegram_id_str, state_token = state.split(':', 1)
            telegram_id = int(telegram_id_str)
            
            # Verify state token
            if not self._verify_oauth_state(telegram_id, state_token):
                raise ValueError("Invalid state token")
            
            # Exchange code for tokens using OAuth Client config
            google_config = settings.get_oauth_client_config()
            if not google_config:
                raise ValueError("OAuth Client configuration not available")
                
            flow = Flow.from_client_config(
                google_config,
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Get user's calendar info
            calendar_service = build('calendar', 'v3', credentials=credentials)
            calendar_info = calendar_service.calendarList().get(calendarId='primary').execute()
            
            # Save credentials and calendar info to database
            self._save_manager_credentials(
                telegram_id=telegram_id,
                credentials=credentials,
                calendar_id=calendar_info['id'],
                email=calendar_info.get('summary', '')
            )
            
            logger.info(f"Successfully connected calendar for manager {telegram_id}")
            return {
                'success': True,
                'telegram_id': telegram_id,
                'email': calendar_info.get('summary', ''),
                'calendar_id': calendar_info['id']
            }
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_manager_calendar_service(self, telegram_id: int):
        """Get authenticated calendar service for manager."""
        try:
            with get_db() as db:
                user = db.query(User).filter(User.telegram_id == telegram_id).first()
                
                if not user or not user.oauth_credentials:
                    return None
                
                # Load credentials from database
                credentials_data = json.loads(user.oauth_credentials)
                credentials = Credentials.from_authorized_user_info(credentials_data)
                
                # Refresh token if needed
                if credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    
                    # Save refreshed credentials
                    user.oauth_credentials = credentials.to_json()
                    db.commit()
                
                return build('calendar', 'v3', credentials=credentials)
                
        except Exception as e:
            logger.error(f"Error getting calendar service for manager {telegram_id}: {e}")
            return None
    
    def create_calendar_service_from_credentials(self, credentials_data: dict):
        """Create authenticated calendar service from credentials data."""
        try:
            # Create credentials from the provided data
            credentials = Credentials.from_authorized_user_info(credentials_data)
            
            # Refresh token if needed
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            
            # Build and return calendar service
            return build('calendar', 'v3', credentials=credentials)
            
        except Exception as e:
            logger.error(f"Error creating calendar service from credentials: {e}")
            return None
    
    def _store_oauth_state(self, telegram_id: int, state: str):
        """Store OAuth state temporarily."""
        # В продакшене лучше использовать Redis
        # Пока сохраняем в память (не безопасно для продакшена!)
        if not hasattr(self, '_oauth_states'):
            self._oauth_states = {}
        
        self._oauth_states[telegram_id] = {
            'state': state,
            'expires': datetime.now() + timedelta(minutes=10)
        }
    
    def _verify_oauth_state(self, telegram_id: int, state: str) -> bool:
        """Verify OAuth state token."""
        if not hasattr(self, '_oauth_states'):
            return False
        
        stored = self._oauth_states.get(telegram_id)
        if not stored:
            return False
        
        # Check expiration
        if datetime.now() > stored['expires']:
            del self._oauth_states[telegram_id]
            return False
        
        # Verify state
        is_valid = stored['state'] == state
        if is_valid:
            del self._oauth_states[telegram_id]  # Clean up
        
        return is_valid
    
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
                    user.calendar_connected = True
                    db.commit()
                    logger.info(f"Saved credentials for manager {telegram_id}")
                else:
                    logger.error(f"Manager {telegram_id} not found in database")
                    
        except Exception as e:
            logger.error(f"Error saving manager credentials: {e}")
            raise

# Global instance
oauth_service = ManagerOAuthService()