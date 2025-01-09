from pydantic import BaseModel, Field
from typing import Literal, List

class Concept(BaseModel):
    """Schema for LLM-generated concept data."""
    title: str = Field(..., description="The title of the concept")
    concept_text: str = Field(..., description="The textual description of the concept")
    keywords: List[str] = Field(..., description="Keywords that describe the concept")
    links: List[str] = Field(..., description="Links related to the concept")
    centrality: Literal["high", "medium", "low"] = Field(..., description="Centrality of the concept in the email")
    source_email_id: str = Field(default="", description="ID of the source email")
    source_email_date: str = Field(default="", description="Date of the source email")

class ConceptList(BaseModel):
    """Schema for a list of LLM-generated concepts."""
    concepts: List[Concept] 