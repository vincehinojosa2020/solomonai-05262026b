# Solomon AI — Product Requirements Document

## Original Problem Statement
Comprehensive church management SaaS platform (M&A due diligence) targeting 100% Planning Center parity. Multi-tenant React/FastAPI/MongoDB application with AI-powered features (Ask Solomon, Whisper transcription, image gen). User requested "Modular Monolith" refactor across 5 phases, plus demo-ready UI polish. Latest request: FULL PARITY CONFIRMATION + GAP CLOSURE.

## Core Requirements
- Multi-tenant church management (People, Groups, Giving, Services, Check-ins, Events, Calendar, Communications)
- AI Assistant (Solomon) powered by Claude via Emergent LLM Key
- Portal for church members (giving, groups, events, media, pathways)
- Admin dashboard for church staff
- Real-time Sunday morning mode, Kids check-in, Cafe, Merch store
- Developer API (v1 Agent API) with API key management

## Architecture
- **Frontend**: React + Shadcn UI + Tailwind CSS
- **Backend**: FastAPI (Python) — Modular Monolith (30 route files, 492 routes)
- **Database**: MongoDB (96 collections)
- **Auth**: Cookie-based sessions + bcrypt + Google OAuth
- **Entry**: server.py (255 lines) -> routes/ (30 domain files)

## What's Been Implemented

### Completed — Phase R1-R4: Modular Monolith Refactor (March 31, 2026)
- 123 Pydantic models in `/app/backend/models/schemas.py`
- Core helpers in `/app/backend/core/` (auth, db, helpers, seed)
- 492 routes in 30 domain files in `/app/backend/routes/`
- server.py: 17,828 → 255 lines (98.6% reduction)

### Completed — Phase R5: OWASP Security Audit
- CORS, SHA256→bcrypt migration, rate limiting

### Completed — P1: Demo UI Removals (March 31, 2026)
- Removed: War Room, Go-Live Health, Directory, Pricing, Vision

### Completed — Full Parity Audit + Gap Closure (March 31, 2026)
- Fixed 12 P0 bugs:
  1. StreamingResponse import in admin_giving.py
  2. RBAC admin.giving → admin.giving.view/edit
  3. 16 dangling decorators removed across 5 files
  4. PAYMENT_PROCESSORS imported in admin_giving.py & public_api.py
  5. get_session_token_from_request added to 4 route files
  6. get_current_portal_user added to 3 route files
  7. PRAYER_CATEGORIES defined in admin_comms.py
  8. ROOT_DIR defined in admin_meetings.py
  9-10. Duplicate imports cleaned
- 116 endpoints tested: 113 pass (97.4%)
- 5 Deliverables generated: Parity Matrix, Gap List, Ask Solomon Report, Landing Page Status, Deployment Readiness

### Testing Status
- Iteration 63: 100% (14/14 backend, 5/5 frontend) — Post-refactor
- Iteration 64: 100% (24/24 backend, 5/5 frontend) — Post-parity-audit

## Prioritized Backlog

### P2 (Deferred per user)
- Physical printer driver integration for Check-ins (currently mocked)
- Live Twilio SMS integration (currently stubbed to DB)
- Real-Time WebSocket for Group Chat (currently HTTP polling)

### P3 (Excluded per user)
- Publishing / page builder
- Church Center Mobile API sync
- Solomon Pay live transaction processing (Stripe test keys in use)

## 3rd Party Integrations
- Anthropic Claude (Ask Solomon) — Emergent LLM Key
- Gemini Image Gen (OG Tags) — Emergent LLM Key
- OpenAI Whisper (Transcriptions) — Emergent LLM Key
- Stripe (Payments) — Test keys
- Emergent Google Auth — Managed Service
- Twilio (SMS) — Stubbed/DB logging fallback
