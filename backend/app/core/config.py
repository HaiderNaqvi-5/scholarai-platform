from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ScholarAI"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | staging | production
    AUTO_CREATE_SCHEMA_ON_STARTUP: bool = False

    # Database (async)
    DATABASE_URL: str = "postgresql+asyncpg://scholarai:password@localhost:5432/scholarai"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_DB: int = 1           # separate DB for HTTP cache
    CACHE_TTL_SECONDS: int = 3600    # 1h default cache TTL

    # Auth
    SECRET_KEY: str = "change-me-in-production-min-32-chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Neo4j (knowledge graph)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # LLM / AI Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""          # optional fallback
    OPENAI_MODEL: str = "gpt-4o-mini"
    HUGGINGFACE_API_KEY: str = ""

    # Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # Whisper (voice interview)
    WHISPER_MODEL: str = "base"       # tiny | base | small | medium | large

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "scholarai-recommender"

    # File Storage (S3-compatible)
    S3_ENDPOINT_URL: str = ""
    S3_BUCKET_NAME: str = "scholarai-documents"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10   # stricter for auth endpoints

    # Scraper
    SCRAPER_HEADLESS: bool = True
    SCRAPER_REQUEST_DELAY_MS: int = 1500   # polite crawl delay

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def coerce_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()
