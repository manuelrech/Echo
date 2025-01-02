from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import sqlite3
from src.logger import setup_logger

logger = setup_logger(__name__)

def migrate_tweets_table():
    """Add source_type column to tweets table and set default values."""
    try:
        # Connect to the database
        conn = sqlite3.connect("database/echo_sqlite.db")
        cursor = conn.cursor()

        # Add the new column
        cursor.execute("""
        ALTER TABLE tweets 
        ADD COLUMN source_type TEXT CHECK(source_type IN ('concept', 'external'));
        """)

        # Set default value 'concept' for existing tweets
        # since all existing tweets were from concepts
        cursor.execute("""
        UPDATE tweets 
        SET source_type = 'concept' 
        WHERE source_type IS NULL;
        """)

        # Add NOT NULL constraint
        cursor.execute("""
        CREATE TABLE tweets_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id TEXT,
            tweet_text TEXT,
            source_type TEXT CHECK(source_type IN ('concept', 'external')) NOT NULL,
            published BOOLEAN DEFAULT FALSE,
            publish_date DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (concept_id) REFERENCES concepts (id)
        );
        """)

        # Copy data to new table
        cursor.execute("""
        INSERT INTO tweets_new 
        SELECT * FROM tweets;
        """)

        # Drop old table and rename new one
        cursor.execute("DROP TABLE tweets;")
        cursor.execute("ALTER TABLE tweets_new RENAME TO tweets;")

        conn.commit()
        logger.info("Successfully migrated tweets table!")

    except sqlite3.Error as e:
        logger.error(f"An error occurred during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_tweets_table() 