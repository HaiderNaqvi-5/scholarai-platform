from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "ScholarAI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = (
        "postgresql+asyncpg://scholarai:password@localhost:5432/scholarai"
    )
    SQL_ECHO: bool = False
    
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me-in-production-min-32-chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    MVP_PRIMARY_COUNTRY: str = "CA"
    MVP_SECONDARY_COUNTRY: str = "US"
    MVP_FULBRIGHT_KEYWORD: str = "fulbright"
    AUTO_SEED_DEMO_DATA: bool = True
    DEMO_STUDENT_EMAIL: str = "student@example.com"
    DEMO_STUDENT_PASSWORD: str = "strongpass1"
    DEMO_STUDENT_FULL_NAME: str = "ScholarAI Demo Student"
    DEMO_ADMIN_EMAIL: str = "admin@example.com"
    DEMO_ADMIN_PASSWORD: str = "strongpass1"
    DEMO_ADMIN_FULL_NAME: str = "ScholarAI Demo Admin"

    def validate_production_settings(self):
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == "change-me-in-production-min-32-chars!!":
                raise RuntimeError("PROD_ERROR: SECRET_KEY must be overridden in production!")
            if self.NEO4J_PASSWORD == "password":
                raise RuntimeError("PROD_ERROR: NEO4J_PASSWORD must be overridden in production!")
            if "password" in self.DATABASE_URL and "@localhost" not in self.DATABASE_URL:
                raise RuntimeError("PROD_ERROR: DATABASE_URL appears to use default password in production!")


settings = Settings()
settings.validate_production_settings()
