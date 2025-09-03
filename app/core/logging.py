"""Structured logging with trace ID support."""

import sys
import json
import uuid
import re
import time
from typing import Any, Dict, Optional
from loguru import logger
from .config import get_settings


class StructuredLogger:
    """Structured logger with trace ID support and secret sanitization."""
    
    def __init__(self):
        self.settings = get_settings()
        self._setup_logger()
        
        # Patterns to identify and sanitize secrets
        self.secret_patterns = [
            r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        ]
    
    def _setup_logger(self):
        """Configure loguru logger."""
        # Remove default handler
        logger.remove()
        
        # Add simple console handler for API workflow
        logger.add(
            sys.stdout,
            format="<level>{message}</level>",
            level="INFO",
            filter=lambda record: record["extra"].get("simple_log", False)
        )
        
        # Add clean console handler for other logs (no JSON, no verbose details)
        logger.add(
            sys.stdout,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <5}</level> | <level>{message}</level>",
            level=self.settings.log_level,
            filter=lambda record: not record["extra"].get("simple_log", False)
        )
    
    def _json_formatter(self, record: Dict[str, Any]) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
        }
        
        # Add extra fields from record
        if "extra" in record:
            log_entry.update(record["extra"])
        
        return json.dumps(log_entry) + "\n"
    
    def _sanitize_secrets(self, text: str) -> str:
        """Sanitize secrets from log messages."""
        if not isinstance(text, str):
            return text
            
        sanitized = text
        for pattern in self.secret_patterns:
            sanitized = re.sub(pattern, r'\1=***REDACTED***', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def log_with_trace(
        self,
        level: str,
        message: str,
        trace_id: Optional[str] = None,
        **kwargs
    ):
        """Log message with trace ID and additional context."""
        # Sanitize message and kwargs
        sanitized_message = self._sanitize_secrets(message)
        sanitized_kwargs = {k: self._sanitize_secrets(str(v)) if isinstance(v, str) else v 
                           for k, v in kwargs.items()}
        
        extra = {
            "trace_id": trace_id or str(uuid.uuid4()),
            **sanitized_kwargs
        }
        
        # Use Loguru's bind to attach extra context; works with serialize=True
        logger.bind(**extra).log(level.upper(), sanitized_message)
    
    def info(self, message: str, trace_id: Optional[str] = None, **kwargs):
        self.log_with_trace("INFO", message, trace_id, **kwargs)
    def error(self, message: str, trace_id: Optional[str] = None, **kwargs):
        self.log_with_trace("ERROR", message, trace_id, **kwargs)
    def warning(self, message: str, trace_id: Optional[str] = None, **kwargs):
        self.log_with_trace("WARNING", message, trace_id, **kwargs)
    def debug(self, message: str, trace_id: Optional[str] = None, **kwargs):
        self.log_with_trace("DEBUG", message, trace_id, **kwargs)

    # Convenience structured logs for steps
    def step(self, message: str, trace_id: Optional[str] = None, duration_ms: Optional[float] = None, **kwargs):
        """Log a processing step with optional duration."""
        step_data = {"step": message}
        if duration_ms is not None:
            step_data["duration_ms"] = round(duration_ms, 2)
        self.log_with_trace("INFO", f"STEP | {message}", trace_id, **{**step_data, **kwargs})
    
    def event(self, message: str, trace_id: Optional[str] = None, **kwargs):
        self.log_with_trace("INFO", f"EVENT | {message}", trace_id, **kwargs)
    
    def data(self, message: str, trace_id: Optional[str] = None, **kwargs):
        self.log_with_trace("DEBUG", f"DATA | {message}", trace_id, **kwargs)
    
    def timing(self, operation: str, duration_ms: float, trace_id: Optional[str] = None, **kwargs):
        """Log timing information for operations."""
        self.log_with_trace("INFO", f"TIMING | {operation}", trace_id, 
                          operation=operation, duration_ms=round(duration_ms, 2), **kwargs)
    
    # Simple logging for API workflow
    def simple(self, message: str, trace_id: Optional[str] = None, **kwargs):
        """Log simple message without JSON formatting."""
        # Sanitize message and kwargs
        sanitized_message = self._sanitize_secrets(message)
        sanitized_kwargs = {k: self._sanitize_secrets(str(v)) if isinstance(v, str) else v 
                           for k, v in kwargs.items()}
        
        extra = {
            "trace_id": trace_id or str(uuid.uuid4()),
            "simple_log": True
        }
        # Add any additional kwargs to the message if provided
        if sanitized_kwargs:
            # Format kwargs as key=value pairs
            kwargs_str = " | ".join([f"{k}={v}" for k, v in sanitized_kwargs.items()])
            sanitized_message = f"{sanitized_message} | {kwargs_str}"
        logger.bind(**extra).info(sanitized_message)


# Global logger instance
structured_logger = StructuredLogger()


def get_logger() -> StructuredLogger:
    """Get the global structured logger instance."""
    return structured_logger
