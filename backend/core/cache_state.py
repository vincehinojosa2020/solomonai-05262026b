"""
Solomon AI — shared in-process cache state
===========================================

Single owner of the two hot-path caches that gate the Stripe transactions
dashboard. Lives in `core/` so both the producer (`routes/stripe_elements.py`)
and the invalidator (`core/realtime.py`) can import from a neutral module
without re-introducing the routes↔core import coupling we just removed.

  • `_STATS_CACHE`        — 30 s TTL, the /platform/stripe/transactions/stats payload
  • `_PLATFORM_TXN_CACHE` — 60 s TTL, the /platform/stripe/transactions list payload
"""
from __future__ import annotations

# 30 s TTL — gates platform-level Stripe stats aggregation
_STATS_CACHE: dict = {"ts": 0.0, "data": None}

# 60 s TTL — keyed by (filter args tuple) → (cached_at_ts, payload)
_PLATFORM_TXN_CACHE: dict[tuple, tuple[float, dict]] = {}
