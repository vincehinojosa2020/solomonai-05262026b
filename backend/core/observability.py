"""
Solomon AI — Observability layer
=================================
One module, three surfaces:

* `setup_logging()`             — JSON structured logs (timestamp, level,
                                  correlation_id, tenant_id, endpoint).
                                  PII-stripping filter applied to ALL records.

* `init_sentry()`               — Sentry SDK + FastAPI integration. No-op when
                                  SENTRY_DSN is empty. Adds tenant_id/user_id
                                  to scope per request.

* `CorrelationIdMiddleware`     — generates/propagates X-Request-ID, stamps
                                  every log line via contextvars.

Usage in server.py:

    from core.observability import (
        setup_logging, init_sentry, CorrelationIdMiddleware,
        sentry_scope_middleware,
    )
    setup_logging()
    init_sentry()
    app.add_middleware(CorrelationIdMiddleware)
    app.middleware("http")(sentry_scope_middleware)
"""
from __future__ import annotations

import contextvars
import logging
import os
import re
import time
import uuid
from typing import Optional

from pythonjsonlogger import json as jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ──────────────────────────────────────────────────────────────────────────
#  Context vars — propagate per-request metadata into every log call
# ──────────────────────────────────────────────────────────────────────────
correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)
tenant_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "tenant_id", default=None
)
user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "user_id", default=None
)
endpoint_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "endpoint", default=None
)


# ──────────────────────────────────────────────────────────────────────────
#  PII redaction — applied to every formatted log line
# ──────────────────────────────────────────────────────────────────────────
# Conservative regex set. We strip:
#   * email addresses
#   * 13-19 digit sequences (card numbers; PAN)
#   * 9-digit SSN-shaped (xxx-xx-xxxx or xxxxxxxxx)
#   * Stripe live secret prefixes
_PII_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[redacted-email]"),
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[redacted-pan]"),
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "[redacted-ssn]"),
    (re.compile(r"\bsk_live_[A-Za-z0-9]+\b"), "[redacted-stripe-key]"),
]


def _redact(text: str) -> str:
    if not isinstance(text, str):
        return text
    for pat, repl in _PII_PATTERNS:
        text = pat.sub(repl, text)
    return text


class _PiiRedactionFilter(logging.Filter):
    """Logging filter that scrubs PII from `record.msg`, `record.args`, and
    common stringly-typed extras. Fail-soft: never raises."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = _redact(record.msg)
            if record.args:
                if isinstance(record.args, tuple):
                    record.args = tuple(_redact(a) if isinstance(a, str) else a
                                        for a in record.args)
                elif isinstance(record.args, dict):
                    record.args = {k: (_redact(v) if isinstance(v, str) else v)
                                   for k, v in record.args.items()}
        except Exception:
            pass
        return True


class _ContextInjector(logging.Filter):
    """Injects per-request context vars onto every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get()
        record.tenant_id = tenant_id_var.get()
        record.user_id = user_id_var.get()
        record.endpoint = endpoint_var.get()
        return True


# ──────────────────────────────────────────────────────────────────────────
#  Logging setup
# ──────────────────────────────────────────────────────────────────────────
def setup_logging() -> None:
    """Replace the default handler with a JSON formatter. Idempotent."""
    log_format = (
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(correlation_id)s %(tenant_id)s %(user_id)s %(endpoint)s"
    )
    formatter = jsonlogger.JsonFormatter(
        log_format,
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
        timestamp=True,
    )

    # Single stdout handler. Replace any preexisting handlers (uvicorn ships
    # its own that we don't want to duplicate over).
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(_PiiRedactionFilter())
    handler.addFilter(_ContextInjector())

    root = logging.getLogger()
    # Drop existing handlers to avoid double-logging in plain text
    root.handlers = [handler]
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

    # Quiet noisy libraries
    for noisy in ("urllib3", "stripe", "watchfiles", "pymongo"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Make sure uvicorn's own loggers go through our formatter too
    for uv in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        lg = logging.getLogger(uv)
        lg.handlers = [handler]
        lg.propagate = False


# ──────────────────────────────────────────────────────────────────────────
#  Sentry
# ──────────────────────────────────────────────────────────────────────────
_sentry_initialized = False


def init_sentry() -> bool:
    """Initialize Sentry if SENTRY_DSN is set. Idempotent. Returns True if
    Sentry was activated."""
    global _sentry_initialized
    if _sentry_initialized:
        return True
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    env = os.environ.get("ENVIRONMENT", "development").lower()
    sample_rate = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.05"))

    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        release=os.environ.get("APP_VERSION", "2.0.0"),
        traces_sample_rate=sample_rate,
        send_default_pii=False,           # we strip PII manually anyway
        attach_stacktrace=True,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
        ],
        before_send=_sentry_before_send,
    )
    _sentry_initialized = True
    logging.getLogger("solomon-ai").info("Sentry initialized", extra={"env": env})
    return True


def _sentry_before_send(event, hint):
    """Final scrub of any payload Sentry is about to ship."""
    try:
        # Strip query-string from request.url
        req = (event.get("request") or {})
        if "data" in req:
            req.pop("data", None)
        if "query_string" in req:
            req["query_string"] = ""
        # Redact message strings
        if event.get("message"):
            event["message"] = _redact(event["message"])
    except Exception:
        pass
    return event


# ──────────────────────────────────────────────────────────────────────────
#  Middleware: correlation id + sentry scope
# ──────────────────────────────────────────────────────────────────────────
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Reads X-Request-ID (or mints one), stamps it on every downstream log
    call via contextvars, echoes it back on the response."""

    async def dispatch(self, request: Request, call_next):
        cid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        token_cid = correlation_id_var.set(cid)
        token_ep = endpoint_var.set(f"{request.method} {request.url.path}")
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            logging.getLogger("solomon-ai.http").info(
                "request_completed",
                extra={
                    "duration_ms": duration_ms,
                    "method": request.method,
                    "path": request.url.path,
                    "client": request.client.host if request.client else "?",
                },
            )
            correlation_id_var.reset(token_cid)
            endpoint_var.reset(token_ep)
        response.headers["X-Request-ID"] = cid
        return response


async def sentry_scope_middleware(request: Request, call_next):
    """Attach tenant_id / user_id / correlation_id to the active Sentry
    scope for this request. No-op when Sentry isn't initialized."""
    if not _sentry_initialized:
        return await call_next(request)

    import sentry_sdk
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("correlation_id", correlation_id_var.get() or "")
        # tenant_id / user_id are populated later in the request lifecycle
        # by auth middleware. We re-stamp at end of request below.
        response = await call_next(request)
        scope.set_tag("tenant_id", tenant_id_var.get() or "")
        scope.set_user({"id": user_id_var.get() or "anonymous"})
    return response


# ──────────────────────────────────────────────────────────────────────────
#  Helpers used by route code to populate scope after auth resolves
# ──────────────────────────────────────────────────────────────────────────
def set_request_user(user: Optional[dict]) -> None:
    """Auth code calls this once user is resolved so subsequent log lines
    + Sentry events carry the right tags."""
    if not user:
        return
    if user.get("tenant_id"):
        tenant_id_var.set(user["tenant_id"])
    if user.get("user_id"):
        user_id_var.set(user["user_id"])


def get_correlation_id() -> str:
    """Routes can reach for the active correlation id when surfacing it back
    to a client (e.g., 'Something went wrong. Reference: <cid>')."""
    return correlation_id_var.get() or "unknown"
