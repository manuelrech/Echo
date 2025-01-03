from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import sqlite3
from src.logger import setup_logger

logger = setup_logger(__name__)

def migrate_concepts_table():
    """Add used column to concepts table and set default values."""
    try:
        # Connect to the database
        conn = sqlite3.connect("database/echo_sqlite.db")
        cursor = conn.cursor()

        # Add the new column
        cursor.execute("""
        ALTER TABLE concepts 
        ADD COLUMN used BOOLEAN DEFAULT FALSE;
        """)

        conn.commit()
        logger.info("Successfully migrated concepts table!")

    except sqlite3.Error as e:
        logger.error(f"An error occurred during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_concepts_table() 