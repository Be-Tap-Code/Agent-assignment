"""Metrics endpoint for observability."""

from fastapi import APIRouter, Response
from app.core.metrics import get_metrics_collector
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger()


@router.get("/metrics")
async def get_metrics():
    """Get application metrics in JSON format."""
    metrics_collector = get_metrics_collector()
    metrics_data = metrics_collector.get_metrics()
    
    logger.info("Metrics endpoint accessed")
    
    return metrics_data



