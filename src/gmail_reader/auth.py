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
    def __init__(self):
        pass

    def _authenticate(self) -> Credentials:
        """Handles OAuth2 authentication and returns credentials."""
        logger.info('Starting authentication process ...')
        creds = None
        if os.path.exists('token.json'):
            logger.info('Loading credentials from token.json')
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info('Refreshing expired credentials')
                creds.refresh(Request())
            else:
                logger.info('Initiating new OAuth flow.')
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                logger.info('Saving credentials to token.json')
                token.write(creds.to_json())
        return creds
    
    def get_gmail_service(self) -> Resource:
        """Builds and returns a Gmail service."""
        creds = self._authenticate()
        return build(serviceName='gmail', version='v1', credentials=creds)
