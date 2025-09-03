"""Configuration management for the geotech Q&A service."""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="simple", env="LOG_FORMAT")
    
    # Retrieval Configuration
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    chunk_size: int = Field(default=400, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, env="CHUNK_OVERLAP")
    top_k_results: int = Field(default=3, env="TOP_K_RESULTS")
    
    # Tool Configuration
    settlement_timeout_seconds: float = Field(default=1.0, env="SETTLEMENT_TIMEOUT_SECONDS")
    terzaghi_timeout_seconds: float = Field(default=1.0, env="TERZAGHI_TIMEOUT_SECONDS")
    max_retries: int = Field(default=1, env="MAX_RETRIES")
    
    # Safety Configuration
    max_question_length: int = Field(default=2000, env="MAX_QUESTION_LENGTH")
    max_context_length: int = Field(default=5000, env="MAX_CONTEXT_LENGTH")
    max_answer_length: int = Field(default=300, env="MAX_ANSWER_LENGTH")
    max_citations: int = Field(default=3, env="MAX_CITATIONS")
    
    # Circuit Breaker Configuration
    circuit_breaker_failure_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    circuit_breaker_recovery_timeout: int = Field(default=60, env="CIRCUIT_BREAKER_RECOVERY_TIMEOUT")
    
    # LLM Configuration (Gemini only)
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    llm_provider: str = Field(default="gemini", env="LLM_PROVIDER")
    orchestrator_type: str = Field(default="crew", env="ORCHESTRATOR")
    llm_model: str = Field(default="gemini-1.5-flash", env="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=15.0, env="LLM_TIMEOUT_SECONDS")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from environment


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
