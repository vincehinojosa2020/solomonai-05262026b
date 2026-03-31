# Solomon AI — Product Requirements Document

## Original Problem Statement
Comprehensive church management SaaS platform (M&A due diligence) targeting 100% Planning Center parity. Multi-tenant React/FastAPI/MongoDB application with AI-powered features (Ask Solomon, Whisper transcription, image gen). User requested "Modular Monolith" refactor across 5 phases, plus demo-ready UI polish.

## Core Requirements
- Multi-tenant church management (People, Groups, Giving, Services, Check-ins, Events, Calendar, Communications)
- AI Assistant (Solomon) powered by Claude via Emergent LLM Key
- Portal for church members (giving, groups, events, media, pathways)
- Admin dashboard for church staff
- Real-time Sunday morning mode, Kids check-in, Cafe, Merch store
- Developer API (v1 Agent API) with API key management

## Architecture
- **Frontend**: React + Shadcn UI + Tailwind CSS
- **Backend**: FastAPI (Python) — Modular Monolith
- **Database**: MongoDB (96 collections)
- **Auth**: Cookie-based sessions + bcrypt + Google OAuth

## What's Been Implemented

### Completed — Phase R1: Extract Pydantic Models ✅
- 123 models extracted to `/app/backend/models/schemas.py`

### Completed — Phase R2: Extract Core Helpers ✅
- Auth, DB, tenant helpers extracted to `/app/backend/core/__init__.py`

### Completed — Phase R3: Extract Routes ✅ (March 31, 2026)
- **492 routes** extracted from server.py into **30 domain-specific files** in `/app/backend/routes/`
- Route files: auth.py, portal.py, solomon.py, admin_people.py, admin_giving.py, admin_groups.py, admin_services.py, admin_checkins.py, admin_events.py, admin_comms.py, admin_media.py, admin_cafe.py, admin_merch.py, admin_pathways.py, admin_settings.py, admin_workflows.py, admin_meetings.py, reports.py, payments.py, platform.py, agent.py, public_api.py + pre-existing: push.py, messaging.py, volunteer.py, geofence.py, announcements.py, media_uploads.py, giving_nudge.py, courses.py

### Completed — Phase R4: Slim server.py ✅ (March 31, 2026)
- server.py reduced from **17,828 lines → 255 lines** (98.6% reduction)
- Now contains only: app creation, middleware, router mounts, startup/shutdown

### Completed — Phase R5: OWASP Security Audit ✅
- CORS fixed, SHA256→bcrypt password auto-migration on login

### Completed — P1: Demo UI Removals ✅ (March 31, 2026)
- Removed "War Room" from admin sidebar
- Removed "Go-Live Health" widget from Dashboard
- Removed "Directory" from Portal nav
- Removed "Pricing" section from Landing Page
- Removed "The Future/Vision" section from Landing Page

### Completed — Shared Helpers Extraction ✅ (March 31, 2026)
- `/app/backend/core/helpers.py` — Shared utility functions (serialize_doc, AI integrations, agent API helpers, etc.)
- `/app/backend/core/seed.py` — Demo seed data functions

## Testing Status
- Iteration 63: 100% pass rate (14/14 backend, 5/5 frontend)
- All 492 routes verified working post-refactor

## Prioritized Backlog

### P2
- Phase 7: Publishing + Home (Custom page builder, role-based dashboards)
- Phase 8: Church Center Mobile API sync (Push notifications, offline sync)

### P3
- Real-Time WebSocket for Group Chat (Currently HTTP polling)
- Printer driver integration for Check-ins (Currently mocked)
- Solomon Pay live transaction processing (Stripe wrapper currently used)

## 3rd Party Integrations
- Anthropic Claude (Ask Solomon) — Emergent LLM Key
- Gemini Image Gen (OG Tags) — Emergent LLM Key
- OpenAI Whisper (Transcriptions) — Emergent LLM Key
- Stripe (Payments) — Test keys
- Emergent Google Auth — Managed Service
- Twilio (SMS) — Stubbed/DB logging fallback
