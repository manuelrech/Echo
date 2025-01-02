#!/usr/bin/env python3
"""Script to fetch emails from Gmail and store them in the database."""

from src.gmail_reader.email_fetcher import EmailFetcher
from src.logger import setup_logger
from src.database.sql import SQLDatabase

logger = setup_logger(__name__)

def main():
    """Fetch and store emails from Gmail."""
    logger.info("Starting email fetching process...")
    
    try:
        db = SQLDatabase()
        email_fetcher = EmailFetcher()

        logger.info("Fetching email messages...")
        messages = email_fetcher.list_messages()

        if not messages:
            logger.info("No new messages found.")
            return

        logger.info(f"Found {len(messages)} messages.")
        stored_count = 0
        
        for msg in messages:
            message = email_fetcher.get_raw_message('me', msg['id'])
            if message:
                formatted_message = email_fetcher.format_message(message)
                
                if db.store_email(formatted_message):
                    stored_count += 1
                    logger.info(f"Stored email: {formatted_message['subject']}")
                else:
                    logger.error(f"Failed to store email: {formatted_message['subject']}")

        logger.info(f"Successfully stored {stored_count} new emails.")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main() 