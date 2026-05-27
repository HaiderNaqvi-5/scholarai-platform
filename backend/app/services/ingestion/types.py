"""Shared dataclasses for the ingestion subsystem.

Lives in its own module so the capture-path implementations
(:mod:`app.services.ingestion.firecrawl_capture`) can return
:class:`CaptureResult` without importing the much heavier ``service.py``
(which would create a circular import).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CaptureResult:
    html: str
    final_url: str
    title: str | None
    capture_mode: str
    metadata: dict[str, Any]
