# Solomon AI — Product Requirements Document

## Original Problem Statement
Comprehensive church management SaaS platform (M&A due diligence) targeting 100% Planning Center parity. Multi-tenant React/FastAPI/MongoDB application with AI-powered features (Ask Solomon, Whisper transcription, image gen).

## Architecture
- **Frontend**: React + Shadcn UI + Tailwind CSS
- **Backend**: FastAPI (Python) — Modular Monolith (30 route files, 500+ routes)
- **Database**: MongoDB (96+ collections)
- **Auth**: Cookie-based sessions + bcrypt + Google OAuth
- **Entry**: server.py (255 lines) -> routes/ (30 domain files)

## What's Been Implemented

### Phase R1-R4: Modular Monolith Refactor — DONE
- 123 Pydantic models, 492+ routes in 30 domain files
- server.py: 17,828 -> 255 lines (98.6% reduction)

### Phase R5: OWASP Security Audit — DONE
### P1: Demo UI Removals — DONE
### Endpoint Parity Audit — DONE (116 endpoints, 97.4%)

### Full Functional CRUD Parity Test — DONE
**127/127 tests passed (100%)**

### Recurring Giving Management (March 31, 2026) — DONE
- Portal: Create/list/edit/pause/resume/cancel recurring donation schedules
- Admin: View all recurring schedules with stats, filter by status, change status
- 8 new backend endpoints, 2 new frontend components
- **Testing: 25/25 (100%) — Iteration 66**

### Giving Goals/Pledges (March 31, 2026) — DONE
- Portal: Members set annual giving goals with visual progress tracking
- Progress bar, YTD given, remaining amount, donation count
- 3 new endpoints (GET/POST/DELETE /portal/giving-goal)
- **Testing: Passed in Iteration 67**

### Custom Fields UI Builder (March 31, 2026) — DONE
- Admin: Define custom data fields (7 types: text, textarea, number, date, boolean, select, multiselect)
- Fields organized by category (personal, church, medical, other)
- Per-field options: name, type, required, options list, active/inactive
- Reorder support, toggle active/inactive
- PersonDetail integration: custom fields shown in overview tab
- 7 new endpoints + Settings tab + PersonCustomFields component
- **Testing: 31/31 (100%) — Iteration 67**

### Registration Add-ons UI Enhancement (March 31, 2026) — DONE
- Admin builder: Enhanced with description, required checkbox, max_qty per add-on
- Public page: Auto-selects required add-ons, shows "Required" badge, "Free" for $0 items
- Blue highlight for selected add-ons
- **Testing: Verified in Iteration 67**

## 3rd Party Integrations
- Anthropic Claude (Ask Solomon) — Emergent LLM Key
- Gemini Image Gen (OG Tags) — Emergent LLM Key
- OpenAI Whisper (Transcriptions) — Emergent LLM Key
- Stripe (Payments) — Test keys
- Emergent Google Auth — Managed Service
- Twilio (SMS) — Stubbed/DB logging fallback

## Testing Iterations
- Iteration 63: 100% (14/14 + 5/5) — Post-refactor
- Iteration 64: 100% (24/24 + 5/5) — Post-endpoint-audit
- Iteration 65: 99.2% (126/127) — Full CRUD parity
- Iteration 66: 100% (25/25) — Recurring Giving
- Iteration 67: 100% (31/31) — Giving Goals + Custom Fields + Registration Add-ons

## Prioritized Backlog
### P2 (Backlog)
- Refactor KidsCheckinAdmin.jsx (1028 lines; split into smaller components)

### P3 (Deferred)
- Physical printer driver integration
- Live Twilio SMS
- WebSocket real-time chat
- Publishing / page builder
- Church Center Mobile API sync
