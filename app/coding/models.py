"""
Pydantic models for the coding API
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4


class CodingRequest(BaseModel):
    """Request to code clinical text"""
    clinical_text: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Clinical notes to be coded"
    )


class CandidateCode(BaseModel):
    """A candidate ICD-10-AM code"""
    code: str
    descriptor: str
    score: float
    source: str  # 'tfidf', 'embed', or 'both'
    complexity: int = 1  # 1-3


class CodingResponse(BaseModel):
    """Response with suggested code"""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    suggested_code: Optional[str] = None
    descriptor: Optional[str] = None
    reasoning: str = ""
    confidence: float = 0.0
    complexity: Optional[int] = None  # 1-6
    complexity_label: Optional[str] = None  # "Minor", "Low", etc.
    candidates: List[CandidateCode] = []
    requires_human_review: bool = True  # ACCD requirement
    extracted_text: Optional[str] = None  # Text extracted from uploaded file
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    codes_loaded: int
    embeddings_loaded: bool
