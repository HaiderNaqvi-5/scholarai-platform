from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "ScholarAI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    API_V2_PREFIX: str = "/api/v2"
    API_V1_DEPRECATION_ENABLED: bool = True
    API_V1_DEPRECATION_DAYS: int = 90

    RECOMMENDATION_KPI_POLICY_VERSION: str = "reco.kpi.v1"
    RECOMMENDATION_KPI_DEFAULT_K_VALUES: str = "1,3,5,10"
    RECOMMENDATION_KPI_PRECISION_MIN: float = 0.4
    RECOMMENDATION_KPI_RECALL_MIN: float = 0.2
    RECOMMENDATION_KPI_NDCG_MIN: float = 0.45
    RECOMMENDATION_KPI_NDCG_DELTA_MIN: float | None = None

    DOCUMENT_QUALITY_POLICY_VERSION: str = "document.quality.v1"
    DOCUMENT_QUALITY_MIN_CITATION_COVERAGE_RATIO: float = 0.8
    DOCUMENT_QUALITY_MAX_CAUTION_NOTE_COUNT: int = 1
    DOCUMENT_QUALITY_MIN_RETRIEVED_GUIDANCE_COUNT: int = 1
    DOCUMENT_QUALITY_MIN_GENERATED_GUIDANCE_COUNT: int = 1
    DOCUMENT_QUALITY_MIN_GROUNDED_PARTITION_COUNT: int = 3
    DOCUMENT_QUALITY_MIN_ACTIONABLE_GUIDANCE_COUNT: int = 2

    INTERVIEW_PROGRESSION_POLICY_VERSION: str = "interview.progression.v1"
    INTERVIEW_PROGRESSION_MIN_ANSWERED_COUNT: int = 2
    INTERVIEW_PROGRESSION_MIN_AVERAGE_SCORE: float = 3.0
    INTERVIEW_PROGRESSION_MIN_SCORE_DELTA: float = 0.0
    INTERVIEW_PROGRESSION_MAX_NEEDS_FOCUS_RATIO: float = 0.5
    INTERVIEW_PROGRESSION_MIN_FOLLOW_UP_ACTIONABILITY_RATIO: float = 0.7
    INTERVIEW_PROGRESSION_MIN_ADAPTIVE_GUIDANCE_COVERAGE: float = 0.7

    KPI_OBSERVABILITY_ENABLED: bool = True
    KPI_HEALTH_LOOKBACK_DAYS: int = 14
    KPI_ALERT_MIN_SNAPSHOTS_PER_DOMAIN: int = 5
    KPI_ALERT_RECOMMENDATION_PASS_RATE_MIN: float = 0.6
    KPI_ALERT_DOCUMENT_PASS_RATE_MIN: float = 0.7
    KPI_ALERT_INTERVIEW_PASS_RATE_MIN: float = 0.6
    KPI_SNAPSHOT_RETENTION_ENABLED: bool = True
    KPI_SNAPSHOT_RETENTION_DAYS: int = 90
    KPI_SNAPSHOT_RETENTION_CRON_HOUR: int = 3
    KPI_SNAPSHOT_RETENTION_CRON_MINUTE: int = 30

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
