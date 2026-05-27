"""Geo IP -> currency resolution.

Backend proxy for ipwho.is so the frontend doesn't have to call third-party
services directly (CSP-blocked + PDPB privacy concern). Caches per-IP in
Redis for 1h.
"""

from app.services.geo.ipwho_client import resolve_currency

__all__ = ["resolve_currency"]
