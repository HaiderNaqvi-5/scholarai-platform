from app.core.config import settings
from app.core.rate_limit import AUTH_RATE_LIMIT, DEFAULT_RATE_LIMIT


def test_rate_limit_strings_match_settings():
    assert DEFAULT_RATE_LIMIT == f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
    assert AUTH_RATE_LIMIT == f"{settings.RATE_LIMIT_AUTH_PER_MINUTE}/minute"
