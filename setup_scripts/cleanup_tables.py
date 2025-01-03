from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import sqlite3
from src.logger import setup_logger

logger = setup_logger(__name__)

def cleanup_tables():
    """Remove tweets and tweets_concepts tables."""
    try:
        # Connect to the database
        conn = sqlite3.connect("database/echo_sqlite.db")
        cursor = conn.cursor()

        # Drop the tweets_concepts table first (because it references tweets)
        cursor.execute("DROP TABLE IF EXISTS tweets_concepts;")
        
        # Drop the tweets table
        cursor.execute("DROP TABLE IF EXISTS tweets;")

        conn.commit()
        logger.info("Successfully removed tweets and tweets_concepts tables!")

    except sqlite3.Error as e:
        logger.error(f"An error occurred during cleanup: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_tables() 