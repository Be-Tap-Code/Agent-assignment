"""Gemini LLM client wrapper with timeouts and single retry."""
from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any
from contextlib import suppress

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import get_metrics_collector

settings = get_settings()
logger = get_logger()

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore


class GeminiClient:
    """Thin wrapper around Google Generative AI (Gemini) text generation."""

    def __init__(self):
        self.model_name = settings.llm_model
        self.timeout_s = settings.llm_timeout_seconds
        self.api_key = settings.google_api_key
        self._configured = False

    def _ensure_configured(self):
        if self._configured:
            return
        if genai is None:
            raise RuntimeError("google-generativeai is not installed")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        genai.configure(api_key=self.api_key)
        self._configured = True

    def _build_model(self):
        self._ensure_configured()
        return genai.GenerativeModel(self.model_name)

    async def agenerate(self, prompt: str, system: Optional[str] = None) -> str:
        """Async text generation with one retry and timeout."""
        self._ensure_configured()
        model = self._build_model()
        metrics_collector = get_metrics_collector()

        full_prompt = prompt if not system else f"System: {system}\n\nUser: {prompt}"

        def _call() -> str:
            resp = model.generate_content(full_prompt)
            if not resp or not getattr(resp, "text", None):
                return ""
            return resp.text.strip()

        # First attempt
        start_time = time.time()
        try:
            result = await asyncio.wait_for(asyncio.to_thread(_call), timeout=self.timeout_s)
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.increment_llm_calls(success=True)
            logger.timing("Gemini call successful", duration_ms)
            return result
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            logger.warning("Gemini call timed out, retrying once", timeout=self.timeout_s, duration_ms=duration_ms)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.warning("Gemini call failed, retrying once", error=str(e), error_type=type(e).__name__, duration_ms=duration_ms)
        
        # Retry once
        retry_start_time = time.time()
        try:
            result = await asyncio.wait_for(asyncio.to_thread(_call), timeout=self.timeout_s)
            retry_duration_ms = (time.time() - retry_start_time) * 1000
            metrics_collector.increment_llm_calls(success=True, retry=True)
            logger.timing("Gemini call successful on retry", retry_duration_ms)
            return result
        except asyncio.TimeoutError:
            retry_duration_ms = (time.time() - retry_start_time) * 1000
            metrics_collector.increment_llm_calls(success=False, retry=True)
            metrics_collector.increment_error("timeout")
            logger.error("Gemini call timed out on retry", timeout=self.timeout_s, duration_ms=retry_duration_ms)
            return "I'm experiencing high load right now. Please try again in a moment."
        except Exception as e:
            retry_duration_ms = (time.time() - retry_start_time) * 1000
            metrics_collector.increment_llm_calls(success=False, retry=True)
            logger.error("Gemini call failed on retry", error=str(e), error_type=type(e).__name__, duration_ms=retry_duration_ms)
            return "I'm having trouble processing your request. Please try again."

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Synchronous wrapper; uses current loop if running, else runs its own."""
        try:
            loop = asyncio.get_running_loop()
            # If we're inside an event loop, schedule and block until done
            return loop.run_until_complete(self.agenerate(prompt, system))  # type: ignore
        except RuntimeError:
            # No running loop; safe to create one
            return asyncio.run(self.agenerate(prompt, system))


_llm_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = GeminiClient()
    return _llm_client

