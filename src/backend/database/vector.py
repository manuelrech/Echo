import os
import chromadb
from typing import Optional, Any, Dict
from datetime import datetime
from chromadb import Collection
from pydantic import BaseModel, Field, ConfigDict
from chromadb import PersistentClient
from chromadb.utils.embedding_functions.openai_embedding_function import OpenAIEmbeddingFunction

from ..schemas.llm import Concept
from ..logger import setup_logger

logger = setup_logger(__name__)

class ChromaDatabase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='allow')
    embedding_model_name: str = Field(default=...)
    persist_directory: str = Field(default="./database")
    collection_name: str = Field(default='concepts')
    _collections: Dict[str, Collection] = {}

    def model_post_init(self, __context: Any) -> None:
        if not os.path.exists(self.persist_directory):
            os.makedirs(os.path.dirname(self.persist_directory), exist_ok=True)
        
        self.embedding_model = OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"), 
            model_name=self.embedding_model_name
        )
        self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Initialize default collection for backward compatibility
        self._get_or_create_collection(self.collection_name)
        logger.info(f"Connected to default Chroma collection '{self.collection_name}'")

    def _get_or_create_collection(self, collection_name: str) -> Collection:
        """Get or create a collection by name."""
        try:
            if collection_name not in self._collections:
                self._collections[collection_name] = self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_model
                )
            return self._collections[collection_name]
        except Exception as e:
            logger.error(f"Error getting/creating collection {collection_name}: {e}", exc_info=True)
            raise

    def get_user_collection(self, user_collection_id: str) -> Collection:
        """Get the collection for a specific user."""
        return self._get_or_create_collection(user_collection_id)

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

    def get_similar_concepts(self, concept: dict, similarity_threshold: float = 0.85, user_collection_id: Optional[str] = None) -> list[dict]:
        """Get similar concepts from the specified collection."""
        try:
            collection = self.get_user_collection(user_collection_id) if user_collection_id else self._collections[self.collection_name]
            results = collection.query(
                query_texts=[concept['concept_text']],
                n_results=5,
                include=["metadatas", "distances", "documents"]
            )
            return self._filter_docs_by_distance(results, similarity_threshold)
        except Exception as e:
            logger.error(f"Error finding similar concepts: {e}", exc_info=True)
            return []
    
    def has_similar_concepts(self, concept: Concept, similarity_threshold: float = 0.85, user_collection_id: Optional[str] = None) -> bool:
        """Find similar concepts in the specified collection."""
        try:
            similar_concepts = self.get_similar_concepts(
                {'concept_text': concept.concept_text}, 
                similarity_threshold,
                user_collection_id
            )
            return len(similar_concepts) > 0
        except Exception as e:
            logger.error(f"Error finding similar concepts: {e}", exc_info=True)
            return False

    def store_concept(self, concept: Concept, similarity_threshold_limit: float = 0.85, user_collection_id: Optional[str] = None) -> Optional[str]:
        """Store a concept in the specified collection if no similar concepts exist."""
        try:
            # Check for similar concepts in the user's collection
            similar_concepts = self.has_similar_concepts(
                concept=concept, 
                similarity_threshold=similarity_threshold_limit,
                user_collection_id=user_collection_id
            )
            if similar_concepts:
                logger.info(f"Found similar concept(s) in collection {user_collection_id} - skipping storage")
                return None
            
            concept_id = f"concept_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(concept.concept_text) % 10000}"
            
            # Get the appropriate collection
            collection = self.get_user_collection(user_collection_id) if user_collection_id else self._collections[self.collection_name]
            
            collection.upsert(
                ids=[concept_id],
                documents=[concept.concept_text],
                metadatas=[
                    {
                        "source_email_id": concept.source_email_id,
                        "created_at": datetime.now().isoformat(),
                        "keywords": ', '.join(concept.keywords),
                        "centrality": concept.centrality,
                        "collection_id": user_collection_id or self.collection_name
                    }
                ]
            )
            
            logger.info(f"Stored new concept with ID: {concept_id} in collection {user_collection_id or self.collection_name}")
            return concept_id
            
        except Exception as e:
            logger.error(f"Error storing concept: {e}", exc_info=True)
            return None