from __future__ import annotations

import logging
import os


def setup_logging(level: str | int | None = None) -> None:
    """
    Configure process-wide logging once.

    This is intentionally lightweight so it can be imported safely from both
    app runtime and tests without side effects beyond standard logging setup.
    """
    resolved_level = level or os.getenv("LOG_LEVEL", "INFO")
    if isinstance(resolved_level, str):
        numeric_level = logging.getLevelName(resolved_level.upper())
        if isinstance(numeric_level, str):
            numeric_level = logging.INFO
    else:
        numeric_level = int(resolved_level)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(numeric_level)
        return

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

