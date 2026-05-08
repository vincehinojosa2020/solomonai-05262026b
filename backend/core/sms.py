"""
Solomon AI — Twilio SMS helper.

Single chokepoint for transactional SMS. Used by:
  * /api/admin/comms/sms/send       (single recipient)
  * /api/admin/comms/sms/bulk       (many recipients)
  * /api/admin/checkins/...         (parent pickup notification)

Why this module exists:
  * Twilio's official Python SDK (twilio>=9) is sync-only — calling it
    from a FastAPI handler blocks the event loop. We wrap every call in
    `asyncio.to_thread` so the worker stays responsive.
  * Phone numbers come in from admins as "(555) 123-4567" or "555-1234";
    `to_e164()` normalises every input to `+15551234567` because Twilio
    rejects non-E.164 outright.
  * Bulk send paces requests to ~5 req/sec to stay under Twilio's
    default per-account rate limit (1 message/sec for trial, 100 for
    paid; 5 is a safe middle ground that won't burst trip).
  * If env vars are missing the helper returns a `{"mock": True, ...}`
    response so dev/preview deploys keep working without burning live
    SMS quota during automated tests.

Env vars (all required for live sends):
  TWILIO_ACCOUNT_SID           AC...
  TWILIO_AUTH_TOKEN            (32-char secret)
  TWILIO_FROM_NUMBER           +15551234567  (or TWILIO_PHONE_NUMBER — legacy alias)

Audit trail: every successful or failed send is logged via the structured
logger with PII-safe fields (phone hashed in logs, never the body).
"""
from __future__ import annotations

import asyncio
import os
import re
import uuid
from typing import Optional

from core import logger


def _twilio_creds() -> tuple[Optional[str], Optional[str], Optional[str]]:
    sid = os.environ.get("TWILIO_ACCOUNT_SID") or None
    tok = os.environ.get("TWILIO_AUTH_TOKEN") or None
    # Accept both env-var names: Vince's spec is TWILIO_FROM_NUMBER, the
    # legacy admin_comms code used TWILIO_PHONE_NUMBER. Either works.
    frm = (
        os.environ.get("TWILIO_FROM_NUMBER")
        or os.environ.get("TWILIO_PHONE_NUMBER")
        or None
    )
    return sid, tok, frm


def is_configured() -> bool:
    return all(_twilio_creds())


# E.164: + then 8-15 digits. We accept US-style inputs without "+1".
_DIGITS_ONLY = re.compile(r"\D+")


def to_e164(phone: str, default_country_code: str = "1") -> Optional[str]:
    """Normalise a US-leaning phone string to E.164. Return None if input
    cannot be salvaged into a sane number (caller decides what to do)."""
    if not phone:
        return None
    s = phone.strip()
    # Already E.164?
    if s.startswith("+") and len(_DIGITS_ONLY.sub("", s)) >= 8:
        digits = _DIGITS_ONLY.sub("", s)
        return f"+{digits}"
    digits = _DIGITS_ONLY.sub("", s)
    if not digits:
        return None
    # 10-digit US: prepend country code
    if len(digits) == 10:
        return f"+{default_country_code}{digits}"
    # 11-digit starting with country code: just prepend +
    if len(digits) == 11:
        return f"+{digits}"
    # Anything else international-ish: assume the user knows
    if 8 <= len(digits) <= 15:
        return f"+{digits}"
    return None


def _hash_phone(phone: str) -> str:
    """8-char hash for log lines so we don't write raw PII to disk."""
    import hashlib
    return hashlib.sha256(phone.encode("utf-8")).hexdigest()[:8]


def _mock_response(to: str, body: str, *, reason: str) -> dict:
    return {
        "status": "queued",
        "message_id": f"mock_{uuid.uuid4().hex[:12]}",
        "to": to,
        "mock": True,
        "note": f"Twilio not configured ({reason}) — simulated send",
        "body_preview": (body[:60] + "…") if len(body) > 60 else body,
    }


async def send_sms(to: str, body: str, *, status_callback: Optional[str] = None) -> dict:
    """Send a single SMS. Returns a dict with `status`, `message_id`, and
    `mock: bool`. Never raises on Twilio errors — returns
    `{"status":"failed","error":"..."}` so callers can decide whether
    one bad number should fail a whole bulk batch."""
    e164 = to_e164(to)
    if not e164:
        logger.warning("sms_invalid_phone", extra={"phone_hash": _hash_phone(to or "")})
        return {"status": "failed", "error": "invalid_phone", "to": to}

    sid, tok, frm = _twilio_creds()
    if not all([sid, tok, frm]):
        return _mock_response(e164, body, reason="missing_env_vars")

    def _send_sync():
        from twilio.rest import Client
        client = Client(sid, tok)
        kwargs = {"body": body, "from_": frm, "to": e164}
        if status_callback:
            kwargs["status_callback"] = status_callback
        return client.messages.create(**kwargs)

    try:
        msg = await asyncio.to_thread(_send_sync)
        logger.info(
            "sms_sent",
            extra={"sid": getattr(msg, "sid", None),
                   "phone_hash": _hash_phone(e164),
                   "status": getattr(msg, "status", None)},
        )
        return {
            "status": getattr(msg, "status", "queued"),
            "message_id": getattr(msg, "sid", None),
            "to": e164,
            "mock": False,
        }
    except Exception as exc:
        logger.warning(
            "sms_send_failed",
            extra={"phone_hash": _hash_phone(e164),
                   "exc_type": type(exc).__name__,
                   "error": str(exc)[:200]},
        )
        return {"status": "failed", "error": type(exc).__name__, "to": e164}


async def send_bulk_sms(recipients: list[dict], body_template: str, *,
                         per_second: float = 5.0) -> dict:
    """Bulk send. `recipients` is a list of dicts each having at least
    `phone` and optionally `name`/`person_id` for templating.

    `body_template` may contain `{name}` which we'll substitute per
    recipient. Pacing: defaults to 5 req/s to stay well under Twilio's
    paid-tier 100/s limit while not overwhelming a trial account.
    """
    if not recipients:
        return {"status": "queued", "sent": 0, "failed": 0, "results": []}

    interval = 1.0 / max(per_second, 0.1)
    results = []
    sent = 0
    failed = 0

    for r in recipients:
        phone = r.get("phone") or ""
        name = r.get("name") or "friend"
        body = body_template.replace("{name}", name)
        res = await send_sms(phone, body)
        if res["status"] == "failed":
            failed += 1
        else:
            sent += 1
        results.append({"phone_hash": _hash_phone(phone), "result": res})
        await asyncio.sleep(interval)

    return {
        "status": "completed",
        "total_recipients": len(recipients),
        "sent": sent,
        "failed": failed,
        "batch_id": f"batch_{uuid.uuid4().hex[:12]}",
        "mock": not is_configured(),
        "results": results,
    }
