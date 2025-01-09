from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Tuple, Optional
import requests
import os

from ..database.vector import ChromaDatabase
from ..database.sql import SQLDatabase
from ..logger import setup_logger
from ..schemas.llm import ConceptList

logger = setup_logger(__name__)

class ConceptExtractor(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')
    model: str = Field(default=...)
    sql_db: SQLDatabase = Field(default=...)
    vector_db: ChromaDatabase = Field(default=...)
    
    def model_post_init(self, __context: Any) -> None:
        if 'deepseek' in self.model:
            self.llm = ChatOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), model='deepseek-chat', base_url='https://api.deepseek.com/')
        else:
            self.llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model=self.model)

    def _extract_concepts(self, email_content: str, email_id: str, email_date: str) -> ConceptList:
        """Extract concepts from email content using OpenAI."""
        try:
            prompt = PromptTemplate.from_template(
                "Extract key concepts from the following newsletter content. Each concept text should be paragraph long.\n\n{email_content}"
            )
            chain = prompt | self.llm.with_structured_output(ConceptList)
            
            concept_list: ConceptList = chain.invoke({"email_content": email_content})
            
            for concept in concept_list.concepts:
                concept.source_email_id = email_id
                concept.source_email_date = email_date
                if concept.links:
                    for link in concept.links:
                        response = requests.get(link, allow_redirects=True)
                        if response.status_code == 200:
                            link = response.url
            
            return concept_list
            
        except Exception as e:
            logger.error(f"Error extracting concepts: {e}", exc_info=True)
            return []
    
    def process_email_concepts(self, email_data: dict, similarity_threshold_limit: float, user_id: int, chroma_collection_id: Optional[str] = None) -> Tuple[bool, int]:
        """Process an email to extract and store concepts.
        
        Args:
            email_data: Dictionary containing email data
            similarity_threshold_limit: Threshold for concept similarity check
            user_id: ID of the user who owns the email
            chroma_collection_id: Optional ID of the user's Chroma collection
            
        Returns:
            Tuple of (success: bool, stored_count: int)
        """
        try:
            logger.info(f"Processing concepts for email: {email_data['subject']} for user {user_id} in collection {chroma_collection_id}")
            
            email_content = f"Subject: {email_data['subject']}\n\n{email_data['body']}"
            concepts = self._extract_concepts(email_content, email_data['id'], email_data['date'])
            
            if not concepts:
                logger.info("No concepts found in email.")
                return False, 0
                
            logger.info(f"Extracted {len(concepts.concepts)} concepts.")
            
            stored_count = 0
            for concept in concepts.concepts:
                chroma_concept_id = self.vector_db.store_concept(
                    concept=concept, 
                    similarity_threshold_limit=similarity_threshold_limit,
                    user_collection_id=chroma_collection_id
                )
                
                if chroma_concept_id:
                    sql_concept_id = self.sql_db.store_concept(
                        concept=concept,
                        chroma_id=chroma_concept_id,
                        user_id=user_id
                    )
                    
                    if sql_concept_id:
                        self.sql_db.link_email_to_concept(
                            email_id=email_data['id'],
                            concept_id=sql_concept_id,
                            user_id=user_id,
                            relevance=concept.centrality
                        )
                        stored_count += 1
            
            logger.info(f"Successfully stored {stored_count} new concepts for user {user_id} in collection {chroma_collection_id}")
            self.sql_db.mark_email_as_processed(email_data['id'])
            return True, stored_count
            
        except Exception as e:
            logger.error(f"Error processing concepts for email: {e}", exc_info=True)
            return False, 0