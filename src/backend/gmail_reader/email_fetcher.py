"""
API reference:
https://developers.google.com/gmail/api/reference/rest/v1/users
"""
import base64
from typing import Optional
from googleapiclient.discovery import Resource
from pydantic import BaseModel, model_validator, Field

from .auth import AuthenticatorManager
from ..logger import setup_logger

logger = setup_logger(__name__)

class EmailFetcher(BaseModel):
    model_config = {'arbitrary_types_allowed': True}
    service: Resource = Field(default=None)
    user_id: Optional[int] = None

    @model_validator(mode='after')
    def _load_gmail_service(self):
        if not self.service:
            authenticator = AuthenticatorManager(user_id=self.user_id)
            self.service = authenticator.get_gmail_service()
        return self

    def list_messages(self, user_id: str = 'me', only_unread: bool = True, recipients: list[str] = []) -> list[dict[str, str]]:
        """List all messages matching a query."""
        try:
            query_parts = []
            if only_unread:
                query_parts.append('is:unread')
            
            if recipients:
                if len(recipients) == 1:
                    query_parts.append(f'from:{recipients[0]}')
                else:
                    formatted_recipients = ' OR '.join(f'from:{email}' for email in recipients)
                    query_parts.append(f'({formatted_recipients})')
            
            query = ' '.join(query_parts)
            
            logger.info(f'Listing messages for user {user_id} with query: {query}')
            response = self.service.users().messages().list(
                userId=user_id, 
                q=query,
                maxResults=100 # max 500
            ).execute()
            return response.get('messages', [])
        except Exception as error:
            logger.error(f'An error occurred while listing messages: {error}', exc_info=True)
            return []
    
    def _mark_as_read(self, user_id: str, msg_id: str) -> bool:
        """Mark a message as read by removing the UNREAD label."""
        try:
            logger.info(f"Marking message {msg_id} as read for user {user_id}")
            self.service.users().messages().modify(
                userId=user_id,
                id=msg_id,
                body={
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()
            logger.info(f"Message {msg_id} marked as read")
            return True
        except Exception as error:
            logger.error(f"An error occurred while marking message as read: {error}", exc_info=True)
            return False
        
    def get_raw_message(self, user_id: str, msg_id: str) -> dict:
        """Retrieve the raw message details by its ID."""
        try:
            logger.info(f"Fetching raw message with ID: {msg_id}")
            message = self.service.users().messages().get(userId=user_id, id=msg_id).execute()
            self._mark_as_read(user_id, msg_id)
            return message
        except Exception as error:
            logger.error(f"An error occurred while fetching raw message: {error}", exc_info=True)
            return None

    def format_message(self, raw_message: dict) -> dict:
        """Format the raw message into a readable dictionary."""
        try:
            if not raw_message:
                return {"error": "No message data provided"}

            payload = raw_message.get('payload', {})
            headers = payload.get('headers', [])
            parts = payload.get('parts', [])
            snippet = raw_message.get('snippet', '')
            internal_date = raw_message.get('internalDate', '')

            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '(No subject)')
            sender = next((header['value'] for header in headers if header['name'] == 'From'), '(No sender)')
            date = next((header['value'] for header in headers if header['name'] == 'Date'), '(No date)')

            body = None
            for part in parts:
                if part.get('mimeType') in ['text/plain', 'text/html']:
                    body_data = part.get('body', {}).get('data')
                    if body_data:
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')
                        break

            return {
                "id": raw_message['id'],
                "subject": subject,
                "sender": sender,
                "date": date,
                "snippet": snippet,
                "body": body or "(No content)"
            }

        except Exception as error:
            logger.error(f"An error occurred while formatting message: {error}", exc_info=True)
            return {"error": "Failed to format message"}
