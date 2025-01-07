from google.auth.external_account_authorized_user import Credentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
import os

from ..logger import setup_logger
from .config import SCOPES

logger = setup_logger(__name__)

class AuthenticatorManager:
    def __init__(self, user_id: int = None):
        self.user_id = user_id
        self.tokens_dir = "tokens"
        if not os.path.exists(self.tokens_dir):
            os.makedirs(self.tokens_dir)

    def _get_token_path(self) -> str:
        """Get the token file path for the current user."""
        if self.user_id:
            return os.path.join(self.tokens_dir, f"token_{self.user_id}.json")
        return os.path.join(self.tokens_dir, "token_default.json")

    def _authenticate(self) -> Credentials:
        """Handles OAuth2 authentication and returns credentials."""
        logger.info(f'Starting authentication process for user {self.user_id}...')
        creds = None
        token_path = self._get_token_path()
        
        if os.path.exists(token_path):
            logger.info(f'Loading credentials from {token_path}')
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info('Refreshing expired credentials')
                creds.refresh(Request())
            else:
                logger.info('Initiating new OAuth flow.')
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                logger.info(f'Saving credentials to {token_path}')
                token.write(creds.to_json())
        
        return creds
    
    def get_gmail_service(self) -> Resource:
        """Builds and returns a Gmail service."""
        creds = self._authenticate()
        return build(serviceName='gmail', version='v1', credentials=creds)
