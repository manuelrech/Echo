from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class BaseUserRequest(BaseModel):
    """Base schema for requests that require user authentication."""
    user_id: int

class TweetRequest(BaseUserRequest):
    """Schema for tweet generation requests."""
    concept_id: int
    generation_type: str
    num_tweets: Optional[int] = 5
    extra_instructions: Optional[str] = None
    model_name: str
    embedding_model_name: str
    prompt: str
    collection_name: str = "concepts"

class EmailFetchRequest(BaseUserRequest):
    """Schema for email fetching and concept generation requests."""
    only_unread: bool = True
    recipients: List[str] = []
    similarity_threshold: float = 0.85
    model_name: str
    embedding_model_name: str

class UserAuth(BaseModel):
    """Schema for user authentication requests."""
    username: str
    password: str

class UserResponse(BaseModel):
    """Schema for user information responses."""
    id: int
    username: str
    chroma_collection_id: str
    created_at: str
    last_login: Optional[str]

class MboxUploadRequest(BaseModel):
    """Schema for mbox file upload request."""
    embedding_model_name: str = "text-embedding-ada-002"
    model_name: str = "gpt-3.5-turbo-16k"
    similarity_threshold: float = 0.85