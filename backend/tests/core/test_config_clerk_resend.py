import pytest

from app.core.config import Settings


def test_clerk_resend_loaded_from_env(monkeypatch):
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_abc")
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", "pk_test_abc")
    monkeypatch.setenv("CLERK_JWKS_URL", "https://example.clerk.accounts.dev/.well-known/jwks.json")
    monkeypatch.setenv("CLERK_WEBHOOK_SECRET", "whsec_xyz")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_xyz")
    monkeypatch.setenv("RESEND_FROM_ADDRESS", "noreply@grantpath.app")
    monkeypatch.setenv("AUTH_PROVIDER", "clerk")
    s = Settings()
    assert s.CLERK_SECRET_KEY == "sk_test_abc"
    assert s.RESEND_FROM_ADDRESS == "noreply@grantpath.app"
    assert s.AUTH_PROVIDER == "clerk"


def test_prod_rejects_blank_clerk_when_provider_clerk(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_PROVIDER", "clerk")
    monkeypatch.setenv("CLERK_SECRET_KEY", "")
    # other prod-required vars must be set so we hit the Clerk check, not another guard
    monkeypatch.setenv("SECRET_KEY", "x" * 33)
    monkeypatch.setenv("NEO4J_PASSWORD", "nondefault")
    monkeypatch.setenv("REDIS_URL", "redis://prod-host:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://prod-host:6379/0")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@prod-db:5432/x")
    monkeypatch.setenv("ALLOWED_HOSTS", '["api.example.com"]')
    monkeypatch.setenv("CORS_ORIGINS", '["https://example.com"]')
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "real-prod-pw")
    monkeypatch.setenv("RESEND_API_KEY", "re_real")
    monkeypatch.setenv("AUTO_SEED_DEMO_DATA", "false")
    s = Settings()
    with pytest.raises(RuntimeError, match="CLERK_SECRET_KEY"):
        s.validate_production_settings()


def test_prod_rejects_blank_clerk_webhook_secret(monkeypatch):
    """P1-4: CLERK_WEBHOOK_SECRET="" with AUTH_PROVIDER=clerk must raise RuntimeError
    at startup so a misconfigured deploy is caught before it accepts any traffic.
    All other Clerk fields and prod-required vars are valid so the loop reaches
    CLERK_WEBHOOK_SECRET specifically (not an earlier guard)."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_PROVIDER", "clerk")
    # All other Clerk fields present and non-empty; only webhook secret is missing.
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_live_abc123")
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", "pk_live_abc123")
    monkeypatch.setenv("CLERK_JWKS_URL", "https://example.clerk.accounts.dev/.well-known/jwks.json")
    monkeypatch.setenv("CLERK_WEBHOOK_SECRET", "")
    # Prod-required vars so other guards don't fire first.
    monkeypatch.setenv("SECRET_KEY", "x" * 33)
    monkeypatch.setenv("NEO4J_PASSWORD", "nondefault")
    monkeypatch.setenv("REDIS_URL", "redis://prod-host:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://prod-host:6379/0")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@prod-db:5432/x")
    monkeypatch.setenv("ALLOWED_HOSTS", '["api.example.com"]')
    monkeypatch.setenv("CORS_ORIGINS", '["https://example.com"]')
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "real-prod-pw")
    monkeypatch.setenv("RESEND_API_KEY", "re_real")
    monkeypatch.setenv("AUTO_SEED_DEMO_DATA", "false")
    s = Settings()
    with pytest.raises(RuntimeError, match="CLERK_WEBHOOK_SECRET"):
        s.validate_production_settings()
