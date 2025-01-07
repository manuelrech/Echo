import sqlite3
import os
from src.backend.database.sql import SQLDatabase
from src.backend.logger import setup_logger

logger = setup_logger(__name__)

def migrate_to_user_id():
    """Migrate existing database entries to include user_id."""
    try:
        # Initialize database connection
        db = SQLDatabase()
        conn = db.connect()
        cursor = conn.cursor()

        # Create a default user if it doesn't exist
        cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, password_hash, chroma_collection_id)
        VALUES (1, 'default_user', 'migration_placeholder', 'default_collection');
        """)

        # Update all existing tables to add user_id column if it doesn't exist
        tables_to_update = [
            ("emails", "ALTER TABLE emails ADD COLUMN user_id INTEGER REFERENCES users(id)"),
            ("tweets", "ALTER TABLE tweets ADD COLUMN user_id INTEGER REFERENCES users(id)"),
            ("concepts", "ALTER TABLE concepts ADD COLUMN user_id INTEGER REFERENCES users(id)"),
            ("email_concepts", "ALTER TABLE email_concepts ADD COLUMN user_id INTEGER REFERENCES users(id)"),
            ("tweets_concepts", "ALTER TABLE tweets_concepts ADD COLUMN user_id INTEGER REFERENCES users(id)")
        ]

        for table, alter_sql in tables_to_update:
            try:
                cursor.execute(alter_sql)
                logger.info(f"Added user_id column to {table}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    raise
                logger.info(f"Column user_id already exists in {table}")

        # Update all existing records to use the default user_id (1)
        update_statements = [
            "UPDATE emails SET user_id = 1 WHERE user_id IS NULL",
            "UPDATE tweets SET user_id = 1 WHERE user_id IS NULL",
            "UPDATE concepts SET user_id = 1 WHERE user_id IS NULL",
            "UPDATE email_concepts SET user_id = 1 WHERE user_id IS NULL",
            "UPDATE tweets_concepts SET user_id = 1 WHERE user_id IS NULL"
        ]

        for statement in update_statements:
            cursor.execute(statement)
            logger.info(f"Executed: {statement}")

        # Make user_id NOT NULL
        recreate_statements = [
            """
            CREATE TABLE emails_new (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                subject TEXT,
                sender TEXT,
                date DATETIME,
                snippet TEXT,
                body TEXT,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            """
            CREATE TABLE tweets_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                concept_id TEXT,
                tweet_text TEXT,
                source_type TEXT CHECK(source_type IN ('concept', 'external')) NOT NULL,
                published BOOLEAN DEFAULT FALSE,
                publish_date DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (concept_id) REFERENCES concepts (id)
            )
            """,
            """
            CREATE TABLE concepts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                concept_text TEXT NOT NULL,
                keywords TEXT,
                links TEXT,
                times_referenced INTEGER DEFAULT 0,
                used BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chroma_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        ]

        tables_to_recreate = ["emails", "tweets", "concepts"]
        
        for i, table in enumerate(tables_to_recreate):
            # Create new table
            cursor.execute(recreate_statements[i])
            
            # Copy data
            cursor.execute(f"INSERT INTO {table}_new SELECT * FROM {table}")
            
            # Drop old table
            cursor.execute(f"DROP TABLE {table}")
            
            # Rename new table
            cursor.execute(f"ALTER TABLE {table}_new RENAME TO {table}")
            
            logger.info(f"Recreated table {table} with NOT NULL constraint on user_id")

        conn.commit()
        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Error during migration: {e}", exc_info=True)
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_to_user_id() 