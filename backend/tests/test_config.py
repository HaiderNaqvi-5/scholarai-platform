from app.core.config import Settings


def test_debug_accepts_release_as_false():
    settings = Settings(DEBUG="release", _env_file=None)

    assert settings.DEBUG is False


def test_debug_accepts_debug_as_true():
    settings = Settings(DEBUG="debug", _env_file=None)

    assert settings.DEBUG is True
