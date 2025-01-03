import sqlite3
from functools import wraps
from typing import Optional, Callable, Any
from email.utils import parsedate_to_datetime
from pydantic import BaseModel, Field, ConfigDict
import pandas as pd
import os
from ..logger import setup_logger
from .sql_statements import (
    CREATE_EMAILS_TABLE, CREATE_TWEETS_TABLE, CREATE_CONCEPTS_TABLE,
    CREATE_EMAIL_CONCEPTS_TABLE, INSERT_EMAIL, SELECT_UNPROCESSED_EMAILS,
    MARK_EMAIL_AS_PROCESSED, LOOK_FOR_EMAIL_BY_ID, INSERT_CONCEPT,
    INSERT_EMAIL_CONCEPT, UPDATE_CONCEPT_REFERENCE_COUNT,
    GET_UNUSED_CONCEPTS_FOR_TWEETS, INSERT_TWEET, LINK_TWEET_TO_CONCEPT,
    CREATE_TWEETS_CONCEPTS_TABLE, UPDATE_CONCEPT_LINKS, MARK_CONCEPT_AS_USED
)
from ..concepts.classes import Concept

logger = setup_logger(__name__)

class SQLDatabase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db_path: str = Field(default="database/echo_sqlite.db")
    conn: Optional[sqlite3.Connection] = Field(default=None)
    
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
    def store_email(self, cursor: sqlite3.Cursor, email_data: dict) -> bool:
        """Store email data in the database only if it doesn't already exist."""
        cursor.execute(LOOK_FOR_EMAIL_BY_ID, (email_data.get('id'),))
        if cursor.fetchone() is not None:
            return True

        email_data['date'] = parsedate_to_datetime(email_data.get('date'))

        cursor.execute(
            INSERT_EMAIL, 
            (
                email_data.get('id'),
                email_data.get('subject'),
                email_data.get('sender'),
                email_data.get('date'),
                email_data.get('snippet'),
                email_data.get('body')
            )
        )
        return True

    @with_connection
    def store_concept(self, cursor: sqlite3.Cursor, concept: Concept, chroma_id: str) -> Optional[int]:
        """Store a concept in the database and return its ID."""
        try:
            links = ', '.join(concept.links)
            keywords = ', '.join(concept.keywords)
            cursor.execute(INSERT_CONCEPT, (concept.title, concept.concept_text, keywords, links, chroma_id))
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error storing concept: {e}", exc_info=True)
            return None

    @with_connection
    def store_tweet(self, cursor: sqlite3.Cursor, tweet_text: str, source_type: str, concept_id: Optional[int] = None) -> Optional[int]:
        """Store a tweet and optionally link it to a concept if it's from a concept source."""
        try:
            cursor.execute(INSERT_TWEET, (concept_id, tweet_text, source_type))
            tweet_id = cursor.lastrowid
            
            if source_type == 'concept' and concept_id is not None:
                cursor.execute(LINK_TWEET_TO_CONCEPT, (tweet_id, concept_id))
            
            return tweet_id
        except sqlite3.Error as e:
            logger.error(f"Error storing tweet: {e}", exc_info=True)
            return None

    @with_connection
    def link_email_to_concept(self, cursor: sqlite3.Cursor, email_id: str, concept_id: int, relevance: str) -> bool:
        """Create a link between an email and a concept."""
        cursor.execute(INSERT_EMAIL_CONCEPT, (email_id, concept_id, relevance))
        cursor.execute(UPDATE_CONCEPT_REFERENCE_COUNT, (concept_id,))
        return True

    @with_connection
    def get_unprocessed_emails(self, cursor: sqlite3.Cursor) -> list[dict]:
        """Retrieve emails that haven't been processed for concepts."""
        cursor.execute(SELECT_UNPROCESSED_EMAILS)
        return [dict(row) for row in cursor.fetchall()]

    @with_connection
    def mark_email_as_processed(self, cursor: sqlite3.Cursor, email_id: str) -> bool:
        """Mark an email as processed."""
        cursor.execute(MARK_EMAIL_AS_PROCESSED, (email_id,))
        return True

    @with_connection
    def get_unused_concepts_for_tweets(self, cursor: sqlite3.Cursor, days_before: int = 1) -> list[dict]:
        """Get concepts from the last day that haven't been used for tweets yet.
        Example return:
        [
            {
                'id': 1,
                'title': 'Concept 1',
                'concept_text': 'Text of the concept',
                'keywords': 'Keyword 1, Keyword 2',
                'links': 'Link 1, Link 2'
            }
        ]
        """
        cursor.execute(GET_UNUSED_CONCEPTS_FOR_TWEETS.format(days_before=days_before))
        concepts = [
            {
                'id': row[0],
                'title': row[1],
                'concept_text': row[2],
                'keywords': row[3],
                'links': row[4],
                'chroma_id': row[5],
                'updated_at': row[6],
                'times_referenced': row[7]
            }
            for row in cursor.fetchall()
        ]
        return concepts

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



