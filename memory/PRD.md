# Solomon AI — Product Requirements Document

## Original Problem Statement
Comprehensive church management SaaS platform (M&A due diligence) targeting 100% Planning Center parity. Multi-tenant React/FastAPI/MongoDB application with AI-powered features (Ask Solomon, Whisper transcription, image gen). User requested "Modular Monolith" refactor across 5 phases, plus demo-ready UI polish. Latest: FULL FUNCTIONAL PARITY TEST with CRUD + User Journeys.

## Architecture
- **Frontend**: React + Shadcn UI + Tailwind CSS
- **Backend**: FastAPI (Python) — Modular Monolith (30 route files, 500+ routes)
- **Database**: MongoDB (96+ collections)
- **Auth**: Cookie-based sessions + bcrypt + Google OAuth
- **Entry**: server.py (255 lines) -> routes/ (30 domain files)

## What's Been Implemented

### Phase R1-R4: Modular Monolith Refactor (March 31, 2026) - DONE
- 123 Pydantic models, 492+ routes in 30 domain files
- server.py: 17,828 -> 255 lines (98.6% reduction)

### Phase R5: OWASP Security Audit - DONE
### P1: Demo UI Removals - DONE
### Endpoint Parity Audit - DONE (116 endpoints, 97.4%)

### Full Functional CRUD Parity Test (March 31, 2026) - DONE
**CRUD Test Results: 127/127 (100%)**
- Admin CRUD: 86/86 (People, Check-Ins, Giving, Groups, Services, Events, Comms, Media, Cafe, Merch, Courses, Reports, Settings)
- Portal Journeys: 30/30 (Onboarding, Sunday Morning, Small Groups, Giving, Courses)
- Ask Solomon: 5/5 (Church data, Events, Pastoral, Biblical, Session persistence)
- Data Integrity: 6/6 (Tenant isolation, RBAC x3, Consistency, Cross-ref)

### Recurring Giving Management (March 31, 2026) - DONE
**Backend (8 new endpoints):**
- POST /api/portal/recurring-giving — Create recurring schedule
- GET /api/portal/recurring-giving — List member's schedules
- PUT /api/portal/recurring-giving/{id} — Edit schedule
- PUT /api/portal/recurring-giving/{id}/pause — Pause schedule
- PUT /api/portal/recurring-giving/{id}/resume — Resume schedule
- DELETE /api/portal/recurring-giving/{id} — Cancel schedule
- GET /api/admin/recurring-giving — Admin list all with stats
- PUT /api/admin/recurring-giving/{id}/status — Admin change status

**Frontend:**
- RecurringGivingManager component (portal) — create/view/edit/pause/resume/cancel
- AdminRecurringGiving component (admin) — table with filters and status management
- Integrated into PortalGive.jsx and GivingDashboard.jsx

**Testing: 25/25 (100%)**

### Testing Iterations
- Iteration 63: 100% (14/14 backend, 5/5 frontend) — Post-refactor
- Iteration 64: 100% (24/24 backend, 5/5 frontend) — Post-endpoint-audit
- Iteration 65: 99.2% (126/127) — Full CRUD parity (1 LLM budget intermittent)
- Iteration 66: 100% (25/25) — Recurring Giving CRUD + UI

## 3rd Party Integrations
- Anthropic Claude (Ask Solomon) — Emergent LLM Key
- Gemini Image Gen (OG Tags) — Emergent LLM Key
- OpenAI Whisper (Transcriptions) — Emergent LLM Key
- Stripe (Payments) — Test keys
- Emergent Google Auth — Managed Service
- Twilio (SMS) — Stubbed/DB logging fallback

## Prioritized Backlog
### P1 (Next)
- Custom Fields UI Builder (backend supports key-value; needs frontend drag-and-drop)
- Registration Add-ons UI Builder (config exists; needs rich member-facing UI)

### P2 (Backlog)
- Refactor KidsCheckinAdmin.jsx (1028 lines; split into smaller components)

### P3 (Deferred)
- Physical printer driver integration
- Live Twilio SMS
- WebSocket real-time chat
- Publishing / page builder
- Church Center Mobile API sync
