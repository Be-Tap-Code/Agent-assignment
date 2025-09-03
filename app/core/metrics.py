"""Metrics collection for observability."""

import time
from typing import Dict, Any, Optional
from threading import Lock
from dataclasses import dataclass, field
from app.core.logging import get_logger

logger = get_logger()


@dataclass
class Metrics:
    """Application metrics."""
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Question metrics
    total_questions: int = 0
    questions_with_context: int = 0
    
    # Tool call metrics
    total_tool_calls: int = 0
    terzaghi_calculations: int = 0
    settlement_calculations: int = 0
    tool_call_failures: int = 0
    
    # LLM metrics
    llm_calls: int = 0
    llm_successes: int = 0
    llm_failures: int = 0
    llm_retries: int = 0
    
    # Performance metrics
    total_processing_time_ms: float = 0.0
    average_response_time_ms: float = 0.0
    
    # Error metrics
    validation_errors: int = 0
    timeout_errors: int = 0
    json_parse_errors: int = 0
    
    # Timestamps
    first_request_time: Optional[float] = None
    last_request_time: Optional[float] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Thread-safe metrics collector."""
    
    def __init__(self):
        self.metrics = Metrics()
        self.lock = Lock()
    
    def increment_requests(self, success: bool = True):
        """Increment request counters."""
        with self.lock:
            self.metrics.total_requests += 1
            if success:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1
            
            # Update timestamps
            current_time = time.time()
            if self.metrics.first_request_time is None:
                self.metrics.first_request_time = current_time
            self.metrics.last_request_time = current_time
    
    def increment_questions(self, has_context: bool = False):
        """Increment question counters."""
        with self.lock:
            self.metrics.total_questions += 1
            if has_context:
                self.metrics.questions_with_context += 1
    
    def increment_tool_calls(self, tool_type: str, success: bool = True):
        """Increment tool call counters."""
        with self.lock:
            self.metrics.total_tool_calls += 1
            if not success:
                self.metrics.tool_call_failures += 1
            
            if tool_type == "terzaghi":
                self.metrics.terzaghi_calculations += 1
            elif tool_type == "settlement":
                self.metrics.settlement_calculations += 1
    
    def increment_llm_calls(self, success: bool = True, retry: bool = False):
        """Increment LLM call counters."""
        with self.lock:
            self.metrics.llm_calls += 1
            if retry:
                self.metrics.llm_retries += 1
            if success:
                self.metrics.llm_successes += 1
            else:
                self.metrics.llm_failures += 1
    
    def record_processing_time(self, duration_ms: float):
        """Record processing time."""
        with self.lock:
            self.metrics.total_processing_time_ms += duration_ms
            if self.metrics.total_requests > 0:
                self.metrics.average_response_time_ms = (
                    self.metrics.total_processing_time_ms / self.metrics.total_requests
                )
    
    def increment_error(self, error_type: str):
        """Increment error counters."""
        with self.lock:
            if error_type == "validation":
                self.metrics.validation_errors += 1
            elif error_type == "timeout":
                self.metrics.timeout_errors += 1
            elif error_type == "json_parse":
                self.metrics.json_parse_errors += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics as dictionary."""
        with self.lock:
            # Calculate uptime
            uptime_seconds = 0
            if self.metrics.first_request_time:
                uptime_seconds = time.time() - self.metrics.first_request_time
            
            return {
                "requests": {
                    "total": self.metrics.total_requests,
                    "successful": self.metrics.successful_requests,
                    "failed": self.metrics.failed_requests,
                    "success_rate": (
                        self.metrics.successful_requests / self.metrics.total_requests * 100
                        if self.metrics.total_requests > 0 else 0
                    )
                },
                "questions": {
                    "total": self.metrics.total_questions,
                    "with_context": self.metrics.questions_with_context,
                    "context_rate": (
                        self.metrics.questions_with_context / self.metrics.total_questions * 100
                        if self.metrics.total_questions > 0 else 0
                    )
                },
                "tool_calls": {
                    "total": self.metrics.total_tool_calls,
                    "terzaghi": self.metrics.terzaghi_calculations,
                    "settlement": self.metrics.settlement_calculations,
                    "failures": self.metrics.tool_call_failures,
                    "success_rate": (
                        (self.metrics.total_tool_calls - self.metrics.tool_call_failures) / 
                        self.metrics.total_tool_calls * 100
                        if self.metrics.total_tool_calls > 0 else 0
                    )
                },
                "llm": {
                    "calls": self.metrics.llm_calls,
                    "successes": self.metrics.llm_successes,
                    "failures": self.metrics.llm_failures,
                    "retries": self.metrics.llm_retries,
                    "success_rate": (
                        self.metrics.llm_successes / self.metrics.llm_calls * 100
                        if self.metrics.llm_calls > 0 else 0
                    )
                },
                "performance": {
                    "total_processing_time_ms": round(self.metrics.total_processing_time_ms, 2),
                    "average_response_time_ms": round(self.metrics.average_response_time_ms, 2)
                },
                "errors": {
                    "validation": self.metrics.validation_errors,
                    "timeout": self.metrics.timeout_errors,
                    "json_parse": self.metrics.json_parse_errors,
                    "total": (
                        self.metrics.validation_errors + 
                        self.metrics.timeout_errors + 
                        self.metrics.json_parse_errors
                    )
                },
                "uptime": {
                    "seconds": round(uptime_seconds, 2),
                    "first_request": self.metrics.first_request_time,
                    "last_request": self.metrics.last_request_time
                },
                "metadata": self.metrics.metadata
            }
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        with self.lock:
            self.metrics = Metrics()
            logger.info("Metrics reset")


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
