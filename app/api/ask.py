"""Ask endpoint for Q&A functionality."""

from fastapi import APIRouter, Request, HTTPException
from app.api.models import AskRequest, AskResponse
from app.core.logging import get_logger
from app.core.metrics import get_metrics_collector
from app.pipeline.orchestrator import PipelineOrchestrator
import time

router = APIRouter()
logger = get_logger()


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest, http_request: Request):
    """Process a question and return an answer with citations and trace."""
    trace_id = getattr(http_request.state, 'trace_id', None)
    start_time = time.time()
    
    # Initialize metrics collector
    metrics_collector = get_metrics_collector()
    
    # Update question metrics
    metrics_collector.increment_questions(has_context=request.context is not None)
    
    logger.info(
        "Processing question",
        trace_id=trace_id,
        question_length=len(request.question),
        has_context=request.context is not None
    )
    
    try:
        # Initialize Pipeline Orchestrator
        logger.simple("🚀 STEP 1: Initializing Pipeline Orchestrator", trace_id=trace_id)
        orchestrator = PipelineOrchestrator()
        logger.simple("✅ Pipeline Orchestrator initialized successfully", trace_id=trace_id)

        # Execute pipeline workflow
        logger.simple("🎯 STEP 2: Executing Pipeline Workflow", trace_id=trace_id)
        logger.simple("🔄 Starting pipeline: Decision → Retrieval → Compute → Synthesis", trace_id=trace_id)
        try:
            result = await orchestrator.process_question(request.question)
            logger.simple("✅ Pipeline workflow completed successfully", trace_id=trace_id, 
                         result_type=type(result).__name__)
        except Exception as pipeline_error:
            logger.error("❌ Pipeline execution failed", trace_id=trace_id, error=str(pipeline_error))
            raise RuntimeError(f"Pipeline execution failed: {str(pipeline_error)}")

        # Build AskResponse using pipeline output
        from app.api.models import Citation, TraceStep
        
        logger.simple("📊 STEP 3: Parsing Pipeline Result", trace_id=trace_id, result_type=type(result).__name__)
        
        # Handle pipeline result (should be dict with answer and citations)
        answer = ""
        citations = []
        
        try:
            if isinstance(result, dict):
                # Pipeline result is a dict with answer and citations
                logger.simple("📋 Processing pipeline result", trace_id=trace_id)
                answer = result.get('answer', '')
                citations_data = result.get('citations', [])
                
                # Convert citations to Citation objects
                citations = []
                for citation_data in citations_data:
                    if isinstance(citation_data, dict):
                        citations.append(Citation(
                            source=citation_data.get('source', ''),
                            confidence=citation_data.get('confidence', 0.8),
                            chunk_id=citation_data.get('chunk_id', '')
                        ))
                    else:
                        # Fallback for string citations
                        citations.append(Citation(
                            source=str(citation_data),
                            confidence=0.8,
                            chunk_id=None
                        ))
                
                logger.simple("📚 Found citations from pipeline", trace_id=trace_id, 
                             citations=[c.source for c in citations])
            else:
                # Fallback for unexpected result type
                logger.simple("❓ Processing unexpected result type", trace_id=trace_id, result_type=type(result).__name__)
                answer = str(result)
                citations = []
                
        except Exception as parse_error:
            logger.error("❌ Failed to parse pipeline result, using fallback", trace_id=trace_id, error=str(parse_error))
            answer = str(result)
            citations = []
        
        logger.simple("✅ Result parsing completed", trace_id=trace_id, answer_length=len(answer), citations_count=len(citations))
        
        try:
            # Calculate total processing time
            total_duration_ms = (time.time() - start_time) * 1000
            
            logger.simple("📤 STEP 4: Creating Final Response", trace_id=trace_id)
            response = AskResponse(
                answer=answer,
                citations=citations,
                trace_id=trace_id or "",
                trace=[TraceStep(step_type="pipeline_execution", duration_ms=total_duration_ms, details={"process": "decision_retrieval_compute_synthesis"})]
            )
            
            logger.timing("Question processed successfully", total_duration_ms, trace_id=trace_id, 
                         answer_length=len(response.answer))
            logger.simple("🎯 WORKFLOW COMPLETED", trace_id=trace_id, 
                         question_length=len(request.question),
                         answer_length=len(response.answer),
                         citations_count=len(response.citations),
                         workflow="Decision → Retrieval → Calculation → Synthesis",
                         duration_ms=round(total_duration_ms, 2))
            
            return response
        except Exception as response_error:
            logger.error("❌ Failed to create AskResponse", trace_id=trace_id, error=str(response_error))
            raise
        
    except Exception as e:
        logger.error(
            "Failed to process question",
            trace_id=trace_id,
            error=str(e),
            error_type=type(e).__name__
        )
        
        # Provide more detailed error information
        error_detail = f"Failed to process question: {str(e)}"
        if "GOOGLE_API_KEY" in str(e):
            error_detail = "Google API key not configured. Please set GOOGLE_API_KEY environment variable."
        elif "CrewAI" in str(e):
            error_detail = f"CrewAI execution failed: {str(e)}"
        
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )
