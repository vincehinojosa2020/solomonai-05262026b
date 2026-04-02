# Solomon AI — Product Requirements Document

## Original Problem Statement
Full-parity church management SaaS combining Planning Center + Church Center + SecureGive + Thinkific, powered by proprietary AI (Ask Solomon). Production deployment and demo readiness for church leaders.

## Architecture
- **Frontend**: React + Shadcn UI + Tailwind CSS
- **Backend**: FastAPI (Python) — Modular Monolith (30 route files, 500+ routes)
- **Database**: MongoDB (test_database, 96+ collections)
- **Auth**: Cookie-based sessions + bcrypt + Google OAuth (disabled for enterprise)
- **Entry**: server.py (255 lines) -> routes/ (30 domain files)

## Completed Work

### Phase R1-R4: Modular Monolith Refactor — DONE
### Phase R5: OWASP Security Audit — DONE
### Endpoint Parity Audit — DONE (116 endpoints, 97.4%)
### Full CRUD Parity Test — DONE (127/127)

### Recurring Giving + Giving Goals + Custom Fields + Add-ons — DONE
- 8 recurring giving endpoints + portal/admin UI
- Giving goals/pledges with progress tracking
- Custom field definitions (7 types) + person detail integration
- Enhanced registration add-ons (description, required, max qty)

### Phase 1: Demo Blockers (April 2, 2026) — DONE
- **Landing Page**: Complete rewrite — "Your Church. One App. Zero Compromise." hero, problem statement, feature cards (SolomonPay, Kids Check-In, Small Groups, Events, Ask Solomon, Academy), comparison table, Support Promise, Founding Team, enterprise CTA "Talk to Sales"/"Request a Demo"
- **Login Page**: Removed Google login, removed "Start Free Trial" link, fixed password toggle z-index
- **Admin Dashboard**: Removed "Live Worship Service" banner
- **Admin White-Label**: Sidebar shows church name instead of "SOLOMON" logo, "Powered by Solomon AI" footer
- **Portal Dashboard**: Removed 12-week streak card, expanded Membership Journey widget with step details, events are clickable links navigating to detail pages
- **Welcome Message**: Limited to first 2 logins (sessionStorage-based)
- **SolomonPay**: Capitalization audit — "SolomonPay" (one word, capital P) across all surfaces

### Phase 2: Demo Data & Portal Fixes (April 2, 2026) — DONE
- **Watch**: 10 sermons seeded with "Pastor Charles Nieman" attribution
- **Merch**: Updated product images to Unsplash professional photography
- **Cafe**: Already had professional Unsplash images
- **Shannon's Giving**: 171 donations across 2024-2027 (realistic weekly recurring + seasonal one-time gifts: ~$6,747 / ~$7,740 / ~$8,275 / ~$2,001)

## Testing Iterations
- Iteration 63-65: Backend CRUD 127/127 (100%)
- Iteration 66: Recurring Giving 25/25 (100%)
- Iteration 67: Giving Goals + Custom Fields + Add-ons 31/31 (100%)
- Iteration 68: Phase 1 Frontend 18/20 → Fixed data seeding issues

## 3rd Party Integrations
- Anthropic Claude (Ask Solomon) — Emergent LLM Key
- Gemini Image Gen (OG Tags) — Emergent LLM Key
- OpenAI Whisper (Transcriptions) — Emergent LLM Key
- Stripe (Payments) — Test keys (SolomonPay returns "pending")
- Emergent Google Auth — Managed (disabled for enterprise motion)
- Twilio (SMS) — Stubbed/DB logging fallback

## Master Build Remaining Tasks

### PHASE 3 — Member Portal Fixes (IN PROGRESS)
- [ ] Merch cart spacing fix (space between name and price)
- [ ] Groups: "Get Notified" button, enhanced detail view (leader, address, time, capacity), Q&A
- [ ] Giving: Tax statement download verification
- [ ] Payments: Stored payment methods, first sign-in onboarding prompt

### PHASE 4 — Admin Portal + SolomonPay
- [ ] SolomonPay admin dashboard (transactions, payouts, fund management, statements, export)
- [ ] RBAC for giving data (pastor/finance/staff/volunteer/member levels)
- [ ] Bidirectional real-time sync (polling-based)
- [ ] Solomon Academy demo courses (Becoming a Member, Why We Give, Baptism, etc.)

### PHASE 5 — Parity Research
- [ ] SecureGive features research
- [ ] Church Center features research
- [ ] Gap analysis and closure

### PHASE 6 — Ask Solomon Agentic AI (POST-DEMO)
- [ ] Mic stays active until speech finishes
- [ ] Agentic actions (place orders, create donations, register for events)

### PHASE 7 — UI Elevation + Refactoring
- [ ] Design refresh (premium typography, spacing, photography)
- [ ] Favicon update
- [ ] KidsCheckinAdmin.jsx split (1028 lines)

### PHASE 8 — Infrastructure
- [ ] WebSocket for group chat
- [ ] Twilio scaffolding
- [ ] Printer scaffolding
- [ ] FPM vulnerability scan
- [ ] RBAC verification

### PHASE 9 — Final Validation
- [ ] Full test suite (all 127+ tests passing)
- [ ] Smoke tests, browser checks
- [ ] Parity verdict (GO/NO-GO)
