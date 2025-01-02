from pydantic import BaseModel, Field
from typing import Literal

class Concept(BaseModel):
    title: str = Field(..., description="The title of the concept")
    concept_text: str = Field(..., description="The textual description of the concept")
    keywords: list[str] = Field(..., description="Keywords that describe the concept")
    links: list[str] = Field(..., description="Links related to the concept")
    centrality: Literal["high", "medium", "low"] = Field(..., description="Centrality of the concept in the email")
    source_email_id: str = Field(default="", description="ID of the source email")

class ConceptList(BaseModel):
    concepts: list[Concept]