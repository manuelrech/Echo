from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from src.logger import setup_logger
from src.database.sql import SQLDatabase
from src.database.vector import ChromaDatabase
from src.concepts.extractor import ConceptExtractor

logger = setup_logger(__name__)

def main():
    """Process all unprocessed emails for concept extraction."""
    logger.info("Starting concept extraction process...")
    
    try:
        sql_db = SQLDatabase()
        vector_db = ChromaDatabase()
        concept_extractor = ConceptExtractor(
            sql_db = sql_db, 
            vector_db = vector_db
        )

        unprocessed_emails = sql_db.get_unprocessed_emails()
        
        if not unprocessed_emails:
            logger.info("No unprocessed emails found.")
            return
            
        logger.info(f"Found {len(unprocessed_emails)} unprocessed emails.")
        
        for email in unprocessed_emails:
            concept_extractor.process_email_concepts(email, similarity_threshold_limit=0.85)

        logger.info("Completed concept extraction process.")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main() 