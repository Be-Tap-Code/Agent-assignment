"""
API models for the geotechnical Q&A service.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class AskRequest(BaseModel):
    """Request model for /ask endpoint."""
    question: str = Field(..., min_length=1, max_length=2000, description="User's question")
    context: Optional[str] = Field(None, max_length=5000, description="Additional context")

    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()

    @validator('context')
    def validate_context(cls, v):
        if v is not None and not v.strip():
            return None
        return v


class Citation(BaseModel):
    """Citation information for retrieved content."""
    source: str = Field(..., description="Source file name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    chunk_id: Optional[str] = Field(None, description="Chunk identifier")


class TraceStep(BaseModel):
    """Individual step in the processing trace."""
    step_type: str = Field(..., description="Type of processing step")
    duration_ms: float = Field(..., description="Duration in milliseconds")
    details: Dict[str, Any] = Field(default_factory=dict, description="Step-specific details")


class AskResponse(BaseModel):
    """Response model for /ask endpoint."""
    answer: str = Field(..., description="The generated answer")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")
    trace_id: str = Field(..., description="Unique trace identifier")
    trace: List[TraceStep] = Field(default_factory=list, description="Processing trace")


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Response timestamp")
