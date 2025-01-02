import os
import chromadb
from typing import Optional, Any
from datetime import datetime
from chromadb.utils.embedding_functions.openai_embedding_function import OpenAIEmbeddingFunction
from pydantic import BaseModel, Field, ConfigDict

from ..concepts.classes import Concept
from ..logger import setup_logger

logger = setup_logger(__name__)

class ChromaDatabase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    embedding_model: str = Field(default="text-embedding-ada-002")
    persist_directory: str = Field(default="./database/echo_vector")
    chroma_client: chromadb.PersistentClient = Field(default=None)
    collection: chromadb.Collection = Field(default=None)

    def model_post_init(self, __context: Any) -> None:
        self.embedding_model = OpenAIEmbeddingFunction(api_key=os.getenv("OPENAI_API_KEY"), model_name=self.embedding_model)
        self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
        try:
            self.collection = self.chroma_client.get_or_create_collection(name="concepts", embedding_function=self.embedding_model)
            logger.info("Connected to Chroma collection 'concepts'")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}", exc_info=True)
            raise

    def _filter_docs_by_distance(self, docs, threshold=0.85) -> list[dict[str, str | dict[str, str]]]:
        distances = docs['distances'][0]
        valid_indices = [i for i, d in enumerate(distances) if d >= threshold]
        filtered_docs = [docs['documents'][0][i] for i in valid_indices]
        filtered_metadatas = [docs['metadatas'][0][i] for i in valid_indices]
        return [
            {
                'document': filtered_docs[i],
                'metadata': filtered_metadatas[i]
            }
            for i in range(len(filtered_docs))
        ]

    def get_similar_concepts(self, concept: dict, similarity_threshold: float = 0.85) -> list[dict]:
        try:
            results = self.collection.query(
                query_texts=[concept['concept_text']],
                n_results=5,
                include=["metadatas", "distances", "documents"]
            )
            return self._filter_docs_by_distance(results, similarity_threshold)
        except Exception as e:
            logger.error(f"Error finding similar concepts: {e}", exc_info=True)
            return []
    
    def has_similar_concepts(self, concept: Concept, similarity_threshold: float = 0.85) -> bool:
        """Find similar concepts in Chroma."""
        try:
            similar_concepts = self.get_similar_concepts(concept, similarity_threshold)
            return len(similar_concepts) > 0

        except Exception as e:
            logger.error(f"Error finding similar concepts: {e}", exc_info=True)
            return False

    def store_concept(self, concept: Concept) -> Optional[str]:
        """Store a concept in Chroma if no similar concepts exist."""
        try:
            similar_concepts = self.has_similar_concepts(
                concept=concept, 
                similarity_threshold=0.85
            )
            if similar_concepts:
                logger.info(f"Found similar concept(s) - skipping storage")
                return None
            
            concept_id = f"concept_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(concept.concept_text) % 10000}"
            
            self.collection.upsert(
                ids=[concept_id],
                documents=[concept.concept_text],
                metadatas=[
                    {
                        "source_email_id": concept.source_email_id,
                        "created_at": datetime.now().isoformat(),
                        "keywords": concept.keywords,
                        "centrality": concept.centrality
                    }
                ]
            )
            
            logger.info(f"Stored new concept with ID: {concept_id}")
            return concept_id
            
        except Exception as e:
            logger.error(f"Error storing concept: {e}", exc_info=True)
            return None