import os
import chromadb
from chromadb import PersistentClient, Collection
from typing import Optional, Any
from datetime import datetime
from chromadb.utils.embedding_functions.openai_embedding_function import OpenAIEmbeddingFunction

from pydantic import BaseModel, Field, ConfigDict

from ..concepts.classes import Concept
from ..logger import setup_logger

logger = setup_logger(__name__)

class ChromaDatabase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    embedding_model_name: str = Field(default=...)
    persist_directory: str = Field(default="./database")
    chroma_client: PersistentClient = Field(default=None)
    collection: Collection = Field(default=None)
    embedding_model: OpenAIEmbeddingFunction = Field(default=None)

    def model_post_init(self, __context: Any) -> None:
        if not os.path.exists(self.persist_directory):
            os.makedirs(os.path.dirname(self.persist_directory), exist_ok=True)
            print(1)
        self.embedding_model = OpenAIEmbeddingFunction(api_key=os.getenv("OPENAI_API_KEY"), model_name=self.embedding_model_name)
        # self.embedding_model = InstructorEmbeddingFunction(model_name="hkunlp/instructor-xl", device="cpu")
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
            similar_concepts = self.get_similar_concepts({'concept_text': concept.concept_text}, similarity_threshold)
            return len(similar_concepts) > 0

        except Exception as e:
            logger.error(f"Error finding similar concepts: {e}", exc_info=True)
            return False

    def store_concept(self, concept: Concept, similarity_threshold_limit: float = 0.85) -> Optional[str]:
        """Store a concept in Chroma if no similar concepts exist."""
        try:
            similar_concepts = self.has_similar_concepts(
                concept=concept, 
                similarity_threshold=similarity_threshold_limit
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
                        "keywords": ', '.join(concept.keywords),
                        "centrality": concept.centrality
                    }
                ]
            )
            
            logger.info(f"Stored new concept with ID: {concept_id}")
            return concept_id
            
        except Exception as e:
            logger.error(f"Error storing concept: {e}", exc_info=True)
            return None