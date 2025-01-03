from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ConfigDict
from typing import Any
import requests
import os

from ..database.vector import ChromaDatabase
from ..database.sql import SQLDatabase
from ..logger import setup_logger
from .classes import ConceptList

logger = setup_logger(__name__)

class ConceptExtractor(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    model: str = Field(default=None)
    sql_db: SQLDatabase = Field(default=None)
    vector_db: ChromaDatabase = Field(default=None)
    llm: ChatOpenAI = Field(default=None)
    
    def model_post_init(self, __context: Any) -> None:
        if 'deepseek' in self.model:
            self.llm = ChatOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), model='deepseek-chat', base_url='https://api.deepseek.com/')
        else:
            self.llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model=self.model)

    def _extract_concepts(self, email_content: str, email_id: str) -> ConceptList:
        """Extract concepts from email content using OpenAI."""
        try:
            prompt = PromptTemplate.from_template(
                "Extract key concepts from the following newsletter content. Each concept text should be paragraph long.\n\n{email_content}"
            )
            chain = prompt | self.llm.with_structured_output(ConceptList)
            
            concept_list: ConceptList = chain.invoke({"email_content": email_content})
            
            for concept in concept_list.concepts:
                concept.source_email_id = email_id
                if concept.links:
                    for link in concept.links:
                        response = requests.get(link, allow_redirects=True)
                        if response.status_code == 200:
                            link = response.url
            

            return concept_list
            
        except Exception as e:
            logger.error(f"Error extracting concepts: {e}", exc_info=True)
            return []
    
    def process_email_concepts(self, email_data: dict, similarity_threshold_limit: float = 0.85):
        """Process an email to extract and store concepts."""
        try:
            logger.info(f"Processing concepts for email: {email_data['subject']}")
            
            email_content = f"Subject: {email_data['subject']}\n\n{email_data['body']}"
            concepts = self._extract_concepts(email_content, email_data['id'])
            
            if not concepts:
                logger.info("No concepts found in email.")
                return
                
            logger.info(f"Extracted {len(concepts.concepts)} concepts.")
            stored_count = 0
            
            for concept in concepts.concepts:
                chroma_concept_id = self.vector_db.store_concept(concept, similarity_threshold_limit=similarity_threshold_limit)
                if chroma_concept_id:
                    sql_concept_id = self.sql_db.store_concept(concept, chroma_concept_id)
                    if sql_concept_id:
                        self.sql_db.link_email_to_concept(email_id=email_data['id'], concept_id=sql_concept_id, relevance=concept.centrality)
                        stored_count += 1
            
            logger.info(f"Successfully stored {stored_count} new concepts.")
            self.sql_db.mark_email_as_processed(email_data['id'])
            
        except Exception as e:
            logger.error(f"Error processing concepts for email: {e}", exc_info=True)