import ssl

from app.tasks.celery_app import _rediss_ssl_options, celery_app


def test_rediss_url_requires_cert_reqs():
    assert _rediss_ssl_options("rediss://default:pw@host:6379") == {
        "ssl_cert_reqs": ssl.CERT_REQUIRED
    }


def test_plain_redis_url_needs_no_ssl_options():
    assert _rediss_ssl_options("redis://localhost:6379/0") is None


def test_blank_url_returns_none():
    assert _rediss_ssl_options(None) is None
    assert _rediss_ssl_options("") is None


def test_broker_connection_retry_on_startup_enabled():
    # Celery 6 flips this default to False; without it a broker hiccup at
    # worker/beat boot is a hard crash instead of a retry loop.
    assert celery_app.conf.broker_connection_retry_on_startup is True
