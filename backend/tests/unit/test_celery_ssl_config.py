import ssl

from app.tasks.celery_app import _rediss_ssl_options


def test_rediss_url_requires_cert_reqs():
    assert _rediss_ssl_options("rediss://default:pw@host:6379") == {
        "ssl_cert_reqs": ssl.CERT_NONE
    }


def test_plain_redis_url_needs_no_ssl_options():
    assert _rediss_ssl_options("redis://localhost:6379/0") is None


def test_blank_url_returns_none():
    assert _rediss_ssl_options(None) is None
    assert _rediss_ssl_options("") is None
