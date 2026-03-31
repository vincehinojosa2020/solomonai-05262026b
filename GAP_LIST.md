# Solomon AI — Gap List

## Audit Date: April 2026

---

## P0 GAPS (Must-Haves for Parity) — ALL RESOLVED

| # | Gap | Status | Resolution |
|---|-----|--------|------------|
| 1 | `/admin/giving/export` 500 error | RESOLVED | Added missing `StreamingResponse` import |
| 2 | `/admin/giving/settings` permission denied | RESOLVED | Fixed RBAC: `admin.giving` -> `admin.giving.view` |
| 3 | `/admin/giving/processor-settings` POST permission | RESOLVED | Fixed RBAC: `admin.giving` -> `admin.giving.edit` |
| 4 | Dangling decorators (16 instances across 5 files) | RESOLVED | Removed all orphan decorators from extraction |
| 5 | `PAYMENT_PROCESSORS` undefined in admin_giving.py | RESOLVED | Imported from admin_settings.py |
| 6 | `PAYMENT_PROCESSORS` undefined in public_api.py | RESOLVED | Imported from admin_settings.py |
| 7 | `get_session_token_from_request` missing in 5 files | RESOLVED | Added import to payments.py, platform.py, portal.py, public_api.py (solomon.py already had it) |
| 8 | `get_current_portal_user` missing in 3 files | RESOLVED | Added import to payments.py, public_api.py, admin_comms.py |
| 9 | `PRAYER_CATEGORIES` undefined in admin_comms.py | RESOLVED | Defined locally in admin_comms.py |
| 10 | `ROOT_DIR` undefined in admin_meetings.py | RESOLVED | Added `ROOT_DIR = Path(__file__).parent.parent` |
| 11 | `StreamingResponse` mid-file import in public_api.py | RESOLVED | Moved to top-level imports |
| 12 | Duplicate `typing` import in public_api.py | RESOLVED | Removed duplicate |

---

## P1 GAPS (Nice-to-Haves, Currently Functional)

| # | Gap | Notes | Priority |
|---|-----|-------|----------|
| 1 | SMS send (Twilio) | Stubbed to DB. Working as designed. | DEFERRED per user |
| 2 | Physical printer support | Mocked. Working as designed. | DEFERRED per user |
| 3 | WebSocket real-time chat | HTTP polling active. Working as designed. | DEFERRED per user |

---

## P2 GAPS (Future Enhancements)

| # | Gap | Notes |
|---|-----|-------|
| 1 | Publishing (page builder) | Excluded per user constraints |
| 2 | Church Center Mobile API sync | Excluded per user constraints |
| 3 | Stripe live payment processing | Test keys in use; user has not provided production keys |

---

## NO REMAINING P0 GAPS
All identified P0 issues have been resolved in this audit session.
