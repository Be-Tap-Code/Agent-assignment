"""Main FastAPI application."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import time
from datetime import datetime
import os
import json

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import get_metrics_collector
from app.api import ask, health, metrics
from app.api.models import HealthResponse

# Initialize settings and dependencies
settings = get_settings()
logger = get_logger()

# Create FastAPI app
app = FastAPI(
    title="Geotech Q&A Service",
    description="Technical Q&A service for geotechnical engineering with RAG and computational tools",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time and trace ID to response headers."""
    import uuid
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    
    start_time = time.time()
    
    # Log request start
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        trace_id=trace_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else None
    )
    
    try:
        # Handle JSON parsing errors for POST requests
        if request.method == "POST" and request.headers.get("content-type", "").startswith("application/json"):
            try:
                body = await request.body()
                if body:
                    json.loads(body.decode())
            except json.JSONDecodeError as json_error:
                logger.warning(
                    "Invalid JSON in request body",
                    trace_id=trace_id,
                    error=str(json_error)
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid JSON format",
                        "details": "Request body contains invalid JSON",
                        "trace_id": trace_id
                    },
                    headers={"X-Trace-ID": trace_id}
                )
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        process_time_ms = round(process_time * 1000, 2)
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Trace-ID"] = trace_id
        
        # Update metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.increment_requests(success=response.status_code < 400)
        metrics_collector.record_processing_time(process_time_ms)
        
        # Log request completion with timing
        logger.timing(
            f"Request completed: {request.method} {request.url.path}",
            process_time_ms,
            trace_id=trace_id,
            status_code=response.status_code,
            method=request.method,
            path=request.url.path
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        process_time_ms = round(process_time * 1000, 2)
        
        # Update metrics for failed request
        metrics_collector = get_metrics_collector()
        metrics_collector.increment_requests(success=False)
        metrics_collector.record_processing_time(process_time_ms)
        
        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            trace_id=trace_id,
            error=str(e),
            process_time_ms=process_time_ms
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "trace_id": trace_id,
                "details": {"message": str(e)}
            },
            headers={"X-Trace-ID": trace_id}
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    import uuid
    trace_id = getattr(request.state, 'trace_id', str(uuid.uuid4()))
    
    logger.warning(
        "Request validation error",
        trace_id=trace_id,
        errors=exc.errors()
    )
    
    # Format validation errors for better user experience
    error_messages = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": error_messages,
            "trace_id": trace_id
        },
        headers={"X-Trace-ID": trace_id}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error response."""
    import uuid
    trace_id = getattr(request.state, 'trace_id', str(uuid.uuid4()))
    
    logger.warning(
        f"HTTP exception: {exc.status_code}",
        trace_id=trace_id,
        detail=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "trace_id": trace_id
        },
        headers={"X-Trace-ID": trace_id}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured error response."""
    import uuid
    trace_id = getattr(request.state, 'trace_id', str(uuid.uuid4()))
    
    logger.error(
        "Unhandled exception",
        trace_id=trace_id,
        error=str(exc),
        error_type=type(exc).__name__
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "trace_id": trace_id
        },
        headers={"X-Trace-ID": trace_id}
    )


# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Root route to serve the UI
@app.get("/")
async def read_root():
    """Serve the main UI page."""
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "Geotech Q&A Service API", "docs": "/docs"}

# Include routers
app.include_router(ask.router, prefix="", tags=["Q&A"])
app.include_router(health.router, prefix="", tags=["Health"])
app.include_router(metrics.router, prefix="", tags=["Metrics"])


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting Geotech Q&A Service with Pipeline Architecture")

    # Initialize vector store if needed
    try:
        from app.retriever.store import VectorStore
        vector_store = VectorStore()
        if not vector_store.is_initialized():
            logger.info("Building knowledge base index...")
            vector_store.build_index()
            logger.info("Knowledge base index built successfully")
        else:
            logger.info("Knowledge base index already exists")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")

    # Ensure pipeline orchestrator is available
    try:
        from app.pipeline.orchestrator import PipelineOrchestrator
        _ = PipelineOrchestrator()
        logger.info("Pipeline orchestrator ready")
    except Exception as e:
        logger.error(f"Pipeline orchestrator initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Geotech Q&A Service")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower()
    )
