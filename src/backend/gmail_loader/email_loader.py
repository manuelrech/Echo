"""
Module for loading emails from .mbox files uploaded by users.
"""
import mailbox
import email
import base64
from datetime import datetime
from typing import Optional, Iterator
from email.utils import parsedate_to_datetime
from pydantic import BaseModel

from ..logger import setup_logger

logger = setup_logger(__name__)

class EmailLoader(BaseModel):
    """Handles loading and parsing of .mbox files."""
    
    def process_mbox_file(self, file_path: str) -> Iterator[dict]:
        """Process an .mbox file and yield formatted messages."""
        try:
            mbox = mailbox.mbox(file_path)
            for message in mbox:
                try:
                    formatted_message = self.format_message(message)
                    if formatted_message:
                        yield formatted_message
                except Exception as e:
                    logger.error(f"Error processing individual message: {e}", exc_info=True)
                    continue
        except Exception as e:
            logger.error(f"Error opening mbox file: {e}", exc_info=True)
            yield {"error": f"Failed to process mbox file: {str(e)}"}

    def format_message(self, message: email.message.Message) -> Optional[dict]:
        """Format an email message into a dictionary similar to Gmail API format."""
        try:
            # Extract basic headers
            subject = message.get('Subject', '(No subject)')
            sender = message.get('From', '(No sender)')
            date_str = message.get('Date')
            
            # Parse and format date
            try:
                date = parsedate_to_datetime(date_str) if date_str else datetime.now()
                formatted_date = date.strftime("%a, %d %b %Y %H:%M:%S %z")
            except:
                formatted_date = '(No date)'

            # Extract body
            body = None
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() in ['text/plain', 'text/html']:
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
            else:
                body = message.get_payload(decode=True).decode('utf-8', errors='replace')

            # Create a unique ID (using the Message-ID header or fallback to hash of content)
            msg_id = message.get('Message-ID', hash(f"{sender}{subject}{date_str}"))
            
            return {
                "id": str(msg_id),
                "subject": subject,
                "sender": sender,
                "date": formatted_date,
                "snippet": body[:100] if body else "(No content)",  # First 100 chars as snippet
                "body": body or "(No content)"
            }

        except Exception as error:
            logger.error(f"An error occurred while formatting message: {error}", exc_info=True)
            return None
