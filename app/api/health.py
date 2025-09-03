"""
Health check endpoint for the geotechnical Q&A service.
"""

from fastapi import APIRouter
from datetime import datetime
from app.api.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )
