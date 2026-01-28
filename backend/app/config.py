"""
Application Configuration

Centralized settings management using Pydantic Settings.
Supports .env files and environment variable overrides.
"""

from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "Holistic Novel Engine"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./novelai.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # LLM Providers (OpenAI/Anthropic fallback)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # NVIDIA NIM Configuration (Cloud API - no local GPU needed)
    nvidia_nim_enabled: bool = True
    nvidia_reranker_enabled: bool = False  # Reranker not available via cloud API
    ngc_api_key: str = ""
    nvidia_llm_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_embeddings_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_reranker_url: str = ""  # Not used with cloud API
    
    # Default models
    planning_model: str = "meta/llama-3.1-405b-instruct"
    writing_model: str = "meta/llama-3.1-405b-instruct"
    embedding_model: str = "nvidia/nv-embedqa-e5-v5"
    reranker_model: str = "nvidia/llama-3.2-nv-rerankqa-1b-v2"
    
    # Fallback models (when NVIDIA NIM is disabled)
    fallback_planning_model: str = "gpt-4o"
    fallback_writing_model: str = "claude-3-5-sonnet-20241022"
    
    # Vector Database
    vector_db_type: Literal["pinecone", "chromadb"] = "chromadb"
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index: str = "novelai"
    chromadb_path: str = "./chroma_data"
    
    # Generation settings
    max_tokens_per_beat: int = 800
    max_beats_per_chapter: int = 20
    max_chapters: int = 50
    
    # Cost tracking
    track_token_usage: bool = True
    max_tokens_per_project: int = 2_000_000  # ~$20-40 depending on model


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenient access
settings = get_settings()
