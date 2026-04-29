"""Tiny helper for sanitized error responses.

`raise HTTPException(detail=str(e))` leaks internal exception text to the
client (stack-trace fragments, Mongo error strings, library internals).
Use `client_error()` instead — it logs the real exception server-side
with the request's correlation_id, and returns a generic message the
client can quote to support.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException

from core.observability import get_correlation_id

logger = logging.getLogger("solomon-ai.errors")


def client_error(
    *,
    status_code: int = 500,
    user_message: str = "Something went wrong. Please try again.",
    log_message: str = "client_error",
    exc: Optional[BaseException] = None,
    extra: Optional[dict] = None,
) -> HTTPException:
    """Build an HTTPException whose detail is a sanitized payload.

    The full exception text is logged server-side (visible to engineers)
    but never sent to the client. The correlation_id IS returned so
    Vince's support team can reverse-look-up the failure in logs/Sentry.

    Usage:
        try:
            ...
        except SomeError as e:
            raise client_error(status_code=502, user_message="Stripe call failed",
                               exc=e, extra={"step": "create_pi"})
    """
    cid = get_correlation_id()
    logger.error(
        log_message,
        extra={
            "exc_type": type(exc).__name__ if exc else None,
            "status_code": status_code,
            **(extra or {}),
        },
        exc_info=exc,
    )
    return HTTPException(
        status_code=status_code,
        detail={
            "error": user_message,
            "correlation_id": cid,
        },
    )
