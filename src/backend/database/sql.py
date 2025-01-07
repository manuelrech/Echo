import os
import sqlite3
import hmac
import pandas as pd
import uuid
import hashlib
from functools import wraps
from typing import Optional, Callable, Any, List, Dict
from email.utils import parsedate_to_datetime
from pydantic import BaseModel, Field, ConfigDict
from src.backend.logger import setup_logger
from src.backend.schemas.llm import Concept
from .sql_statements import (
    CREATE_EMAILS_TABLE, CREATE_TWEETS_TABLE, CREATE_CONCEPTS_TABLE,
    CREATE_EMAIL_CONCEPTS_TABLE, INSERT_EMAIL, SELECT_UNPROCESSED_EMAILS,
    MARK_EMAIL_AS_PROCESSED, LOOK_FOR_EMAIL_BY_ID, INSERT_CONCEPT,
    INSERT_EMAIL_CONCEPT, UPDATE_CONCEPT_REFERENCE_COUNT,
    GET_UNUSED_CONCEPTS_FOR_TWEETS, INSERT_TWEET, LINK_TWEET_TO_CONCEPT,
    CREATE_TWEETS_CONCEPTS_TABLE, UPDATE_CONCEPT_LINKS, MARK_CONCEPT_AS_USED,
    CREATE_USERS_TABLE
)

logger = setup_logger(__name__)

class SQLDatabase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')
    db_path: str = Field(default="database/echo_sqlite.db")
    
    def model_post_init(self, __context: Any) -> None:
        if not os.path.exists(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._create_tables()
        return self

    def connect(self) -> sqlite3.Connection:
        """Create a database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return self.conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}", exc_info=True)
            raise

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(CREATE_USERS_TABLE)
                cursor.execute(CREATE_EMAILS_TABLE)
                cursor.execute(CREATE_TWEETS_TABLE)
                cursor.execute(CREATE_CONCEPTS_TABLE)
                cursor.execute(CREATE_EMAIL_CONCEPTS_TABLE)
                cursor.execute(CREATE_TWEETS_CONCEPTS_TABLE)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}", exc_info=True)
            raise

    def with_connection(func: Callable) -> Callable:
        """Decorator to manage database connections and cursors."""
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            try:
                with self.connect() as conn:
                    cursor = conn.cursor()
                    result = func(self, cursor, *args, **kwargs)
                    conn.commit()
                    return result
            except sqlite3.Error as e:
                logger.error(f"Database error in {func.__name__}: {e}", exc_info=True)
                return False
        return wrapper

    @with_connection
    def store_email(self, cursor: sqlite3.Cursor, email_data: dict, user_id: int) -> bool:
        """Store email data in the database only if it doesn't already exist."""
        cursor.execute(LOOK_FOR_EMAIL_BY_ID, (email_data.get('id'),))
        if cursor.fetchone() is not None:
            return True

        email_data['date'] = parsedate_to_datetime(email_data.get('date'))

        cursor.execute(
            "INSERT INTO emails (id, user_id, subject, sender, date, snippet, body) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                email_data.get('id'),
                user_id,
                email_data.get('subject'),
                email_data.get('sender'),
                email_data.get('date'),
                email_data.get('snippet'),
                email_data.get('body')
            )
        )
        return True

    @with_connection
    def store_concept(self, cursor: sqlite3.Cursor, concept: Concept, chroma_id: str, user_id: int) -> Optional[int]:
        """Store a concept in the database and return its ID."""
        try:
            links = ', '.join(concept.links)
            keywords = ', '.join(concept.keywords)
            cursor.execute(
                "INSERT INTO concepts (user_id, title, concept_text, keywords, links, chroma_id) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, concept.title, concept.concept_text, keywords, links, chroma_id)
            )
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error storing concept: {e}", exc_info=True)
            return None

    @with_connection
    def store_tweet(self, cursor: sqlite3.Cursor, tweet_text: str, source_type: str, user_id: int, concept_id: Optional[int] = None) -> Optional[int]:
        """Store a tweet and optionally link it to a concept if it's from a concept source."""
        try:
            cursor.execute(
                "INSERT INTO tweets (user_id, concept_id, tweet_text, source_type, published, publish_date) VALUES (?, ?, ?, ?, TRUE, CURRENT_TIMESTAMP)",
                (user_id, concept_id, tweet_text, source_type)
            )
            tweet_id = cursor.lastrowid
            
            if source_type == 'concept' and concept_id is not None:
                cursor.execute(
                    "INSERT INTO tweets_concepts (tweet_id, concept_id, user_id) VALUES (?, ?, ?)",
                    (tweet_id, concept_id, user_id)
                )
            
            logger.info(f"Tweet stored with ID: {tweet_id} and concept ID: {concept_id}")
            return tweet_id
        except sqlite3.Error as e:
            logger.error(f"Error storing tweet: {e}", exc_info=True)
            return None

    @with_connection
    def link_email_to_concept(self, cursor: sqlite3.Cursor, email_id: str, concept_id: int, user_id: int, relevance: str) -> bool:
        """Create a link between an email and a concept."""
        cursor.execute(
            "INSERT INTO email_concepts (email_id, concept_id, user_id, relevance) VALUES (?, ?, ?, ?)",
            (email_id, concept_id, user_id, relevance)
        )
        cursor.execute(UPDATE_CONCEPT_REFERENCE_COUNT, (concept_id,))
        return True

    @with_connection
    def get_unprocessed_emails(self, cursor: sqlite3.Cursor, user_id: int) -> list[dict]:
        """Retrieve emails that haven't been processed for concepts."""
        cursor.execute("SELECT * FROM emails WHERE processed = FALSE AND user_id = ?", (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    @with_connection
    def mark_email_as_processed(self, cursor: sqlite3.Cursor, email_id: str) -> bool:
        """Mark an email as processed."""
        cursor.execute(MARK_EMAIL_AS_PROCESSED, (email_id,))
        return True

    @with_connection
    def get_unused_concepts_for_tweets(self, cursor: sqlite3.Cursor, user_id: int, days_before: int = 30) -> list[dict]:
        """Get concepts that haven't been used for tweets in the last N days."""
        try:
            cursor.execute(
                GET_UNUSED_CONCEPTS_FOR_TWEETS,
                (user_id, f'-{days_before} days')
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Database error in get_unused_concepts_for_tweets: {str(e)}", exc_info=True)
            return []

    @with_connection
    def get_tables_in_dataframes(self, cursor: sqlite3.Cursor) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Converti la tabella emails in un pandas DataFrame."""
        cursor.execute("SELECT * FROM emails")
        email_rows = cursor.fetchall()
        rows = [dict(row) for row in email_rows]
        ids = [row.pop('id') for row in rows]
        emails_df = pd.DataFrame(rows, index=ids)
        cursor.execute("SELECT * FROM tweets")
        tweet_rows = cursor.fetchall()
        rows = [dict(row) for row in tweet_rows]
        ids = [row.pop('id') for row in rows]
        tweets_df = pd.DataFrame(rows, index=ids)
        cursor.execute("SELECT * FROM concepts")
        concept_rows = cursor.fetchall()
        rows = [dict(row) for row in concept_rows]
        ids = [row.pop('id') for row in rows]
        concepts_df = pd.DataFrame(rows, index=ids)
        return emails_df, tweets_df, concepts_df

    @with_connection
    def update_concept_links(self, cursor: sqlite3.Cursor, concept_id: int, new_links: str) -> bool:
        """Update the links for a concept."""
        cursor.execute(UPDATE_CONCEPT_LINKS, (new_links, concept_id))
        return True

    @with_connection
    def mark_concept_as_used(self, cursor: sqlite3.Cursor, concept_id: int) -> bool:
        """Mark a concept as used."""
        try:
            cursor.execute(MARK_CONCEPT_AS_USED, (concept_id,))
            return True
        except sqlite3.Error as e:
            logger.error(f"Error marking concept as used: {e}", exc_info=True)
            return False

    @with_connection
    def get_concept_by_id(self, cursor: sqlite3.Cursor, concept_id: int, user_id: int) -> Optional[dict]:
        """Get a concept by its ID and user_id."""
        cursor.execute(
            "SELECT * FROM concepts WHERE id = ? AND user_id = ?",
            (concept_id, user_id)
        )
        return cursor.fetchone()

    @with_connection
    def create_user(self, cursor: sqlite3.Cursor, username: str, password: str, chroma_collection_id: Optional[str] = None) -> Optional[int]:
        """Create a new user in the database with hashed password."""
        try:
            salt = os.urandom(32)
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000
            )
            # Combine salt and hash for storage
            stored_password = salt + password_hash
            
            # Generate unique Chroma collection ID if not provided
            if not chroma_collection_id:
                chroma_collection_id = f"collection_{username}_{uuid.uuid4().hex[:8]}"
            
            cursor.execute(
                "INSERT INTO users (username, password_hash, chroma_collection_id) VALUES (?, ?, ?)",
                (username, stored_password.hex(), chroma_collection_id)
            )
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            return None

    @with_connection
    def verify_password(self, cursor: sqlite3.Cursor, username: str, password: str) -> bool:
        """Verify a user's password."""
        try:
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            if not result:
                return False
            
            stored_password = bytes.fromhex(result['password_hash'])
            salt = stored_password[:32]  # Get the salt
            stored_hash = stored_password[32:]  # Get the hash
            
            # Hash the provided password with the stored salt
            hash_to_check = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000
            )
            
            return hmac.compare_digest(hash_to_check, stored_hash)
        except sqlite3.Error as e:
            logger.error(f"Error verifying password: {e}", exc_info=True)
            return False

    @with_connection
    def update_password(self, cursor: sqlite3.Cursor, username: str, new_password: str) -> bool:
        """Update a user's password."""
        try:
            # Generate new salt and hash password
            salt = os.urandom(32)
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                new_password.encode('utf-8'),
                salt,
                100000
            )
            stored_password = salt + password_hash
            
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (stored_password.hex(), username)
            )
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating password: {e}", exc_info=True)
            return False

    @with_connection
    def list_users(self, cursor: sqlite3.Cursor) -> List[Dict]:
        """List all users with their last login time and Chroma collection ID."""
        try:
            cursor.execute(
                "SELECT id, username, chroma_collection_id, created_at, last_login FROM users"
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error listing users: {e}", exc_info=True)
            return []

    @with_connection
    def get_user(self, cursor: sqlite3.Cursor, user_id: int = None, username: str = None) -> Optional[dict]:
        """Get user by username."""
        try:
            if user_id:
                cursor.execute(
                    "SELECT * FROM users WHERE id = ?",
                    (user_id,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM users WHERE username = ?",
                    (username,)
                )
            user = cursor.fetchone()
            return dict(user) if user else None
        except sqlite3.Error as e:
            logger.error(f"Error getting user: {e}", exc_info=True)
            return None

    @with_connection
    def update_last_login(self, cursor: sqlite3.Cursor, username: str) -> bool:
        """Update user's last login timestamp."""
        try:
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?",
                (username,)
            )
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating last login: {e}", exc_info=True)
            return False

