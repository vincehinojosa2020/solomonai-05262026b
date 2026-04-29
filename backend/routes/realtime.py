"""
Solomon AI — Realtime + Launch Status routes
=============================================

* `GET /api/realtime/donations?since=ISO8601` — what donations landed
  since timestamp T. Used by church-admin and platform-admin frontends
  for sub-3s "you got a new gift" toast notifications. Polls every 10s.

* `GET /api/health/launch-status` — God-Mode launch widget. One call returns
  API status, Mongo status, last-donation timestamp, donations-in-last-hour,
  process uptime, environment. Green/yellow/red trivially derived client-side.
"""
from __future__ import annotations

import asyncio
import os
import time as _time
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from core import db, get_session_token_from_request
from core.realtime import get_recent_donations

router = APIRouter()

# Pull process-start timestamp from server module if available, otherwise
# stamp on first call. Either way it tracks since the worker started.
_REALTIME_PROCESS_START = _time.time()


# ──────────────────────────────────────────────────────────────────────
#  Tiny auth helper — accepts platform_admin or church_admin
# ──────────────────────────────────────────────────────────────────────
async def _require_authenticated(request: Request, *, roles: tuple) -> dict:
    token = get_session_token_from_request(request)
    if not token:
        raise HTTPException(401, "Not authenticated")
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(401, "Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") not in roles:
        raise HTTPException(403, "Insufficient role")
    return user


# ──────────────────────────────────────────────────────────────────────
#  Realtime donations tail
# ──────────────────────────────────────────────────────────────────────
@router.get("/realtime/donations")
async def realtime_donations(request: Request, since: Optional[str] = None, limit: int = 20):
    """Return donations created after `since`. If user is church_admin,
    scoped to their tenant_id. Platform_admin sees cross-tenant.

    The frontend polls this every 10s with `since=<server_time from last response>`
    so the payload is normally empty (no rows) — keeping the endpoint cheap."""
    user = await _require_authenticated(
        request,
        roles=("platform_admin", "church_admin", "admin", "senior_pastor", "finance"),
    )
    tenant_scope = None if user.get("role") == "platform_admin" else user.get("tenant_id")
    return await get_recent_donations(tenant_scope, since, limit=limit)


# ──────────────────────────────────────────────────────────────────────
#  Launch Status (God Mode widget)
# ──────────────────────────────────────────────────────────────────────
@router.get("/health/launch-status")
async def launch_status(request: Request):
    """One-call composite health for the God-Mode dashboard widget.
    Platform_admin only — surfaces enough signal for the on-call to
    decide green/yellow/red at a glance."""
    user = await _require_authenticated(request, roles=("platform_admin",))
    started = _time.perf_counter()

    # ── Mongo ping ──
    mongo_status = "ok"
    mongo_latency_ms = None
    try:
        t0 = _time.perf_counter()
        await asyncio.wait_for(db.command("ping"), timeout=2.0)
        mongo_latency_ms = round((_time.perf_counter() - t0) * 1000, 1)
    except Exception:
        mongo_status = "down"

    # ── Donation pulse ── (each query gets a 2s budget; on timeout we
    #     return None for the field and degrade to 'yellow' overall, never
    #     500 — UptimeRobot must NEVER see a 5xx from this endpoint.)
    async def _safe(coro, timeout=2.0):
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except Exception:
            return None

    last_donation = await _safe(db.donations.find_one(
        {}, {"_id": 0, "amount": 1, "tenant_id": 1, "created_at": 1, "donation_date": 1},
        sort=[("created_at", -1)],
    ))
    last_donation_at = (last_donation or {}).get("created_at")
    last_donation_amount = (last_donation or {}).get("amount")

    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    one_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    donations_last_hour, donations_last_minute, stripe_webhook_recent, stripe_webhook_failed = await asyncio.gather(
        _safe(db.donations.count_documents({"created_at": {"$gte": one_hour_ago}})),
        _safe(db.donations.count_documents({"created_at": {"$gte": one_min_ago}})),
        _safe(db.stripe_webhook_events.count_documents({"received_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=1)}})),
        _safe(db.stripe_webhook_events.count_documents({"processed": False, "received_at": {"$lte": datetime.now(timezone.utc) - timedelta(minutes=5)}})),
    )

    # ── Status derivation ──
    api_status = "ok"
    overall = "green"
    if mongo_status != "ok":
        overall = "red"
    elif (stripe_webhook_failed or 0) > 0 or last_donation is None:
        overall = "yellow"

    return {
        "overall": overall,
        "checks": {
            "api": {"status": api_status, "latency_ms": round((_time.perf_counter() - started) * 1000, 1)},
            "mongo": {"status": mongo_status, "latency_ms": mongo_latency_ms},
            "sentry": {"status": "configured" if os.environ.get("SENTRY_DSN") else "disabled"},
            "stripe_webhooks": {
                "status": "ok" if stripe_webhook_failed == 0 else "degraded",
                "received_last_hour": stripe_webhook_recent,
                "stale_unprocessed": stripe_webhook_failed,
            },
        },
        "donations": {
            "last_amount": last_donation_amount,
            "last_at": last_donation_at,
            "last_minute": donations_last_minute,
            "last_hour": donations_last_hour,
        },
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "version": os.environ.get("APP_VERSION", "2.0.0"),
        "uptime_s": round(_time.time() - _REALTIME_PROCESS_START, 1),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


# ──────────────────────────────────────────────────────────────────────
#  Sentry smoke test — platform_admin only.  Triggers an intentional
#  error so the on-call can verify the project-DSN wiring + tenant tags
#  end-to-end.  Safe in production: returns 500 to the caller too.
# ──────────────────────────────────────────────────────────────────────
@router.get("/health/sentry-test")
async def sentry_test(request: Request):
    user = await _require_authenticated(request, roles=("platform_admin",))
    # Tag with tenant + correlation in case middleware hasn't populated yet
    try:
        import sentry_sdk
        sentry_sdk.set_tag("sentry_test", "true")
        sentry_sdk.set_tag("triggered_by_user_id", user.get("user_id"))
    except Exception:
        pass
    raise RuntimeError(
        "sentry_smoke_test: intentional error from /api/health/sentry-test "
        f"(user={user.get('user_id')}) — if you see this in Sentry, capture is working."
    )
