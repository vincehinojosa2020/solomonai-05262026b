# Solomon AI — Product Requirements Document

## Original Problem Statement
SOLOMON AI — Full-parity church management SaaS with proprietary payment processor (Solomon Pay). Competing with Planning Center, Church Center, SecureGive, and Pushpay. 14-Phase Master Build Directive targeting nationwide SaaS distribution.

## Platform Scale (as of April 3, 2026)
- **7 church tenants** (3 Abundant campuses + 4 standalone churches)
- **60,226 total members**
- **$68.9M all-time GMV**
- **$1.2M platform fees earned**
- **$20.3K MRR / $243.6K ARR**
- **171K+ donations for Abundant, 600K+ new donations for extended tenants**

## Architecture
```
Backend: FastAPI + MongoDB (540+ endpoints, 35+ route files, 6 service files)
Frontend: React + Shadcn/UI (50+ admin pages, 20+ portal pages)
AI: Claude (via Emergent LLM Key) with structured action parsing + voice
Payments: Solomon Pay (proprietary, 1.9% + $0.30 card, 0.8% + $0.30 ACH)
Calendar: FullCalendar v6
Scheduler: asyncio background task (recurring_scheduler.py)
Multi-Campus: campus selector modal + /portal/campuses endpoint
```

## Phase / Section Completion Status

| Section | Status | Key Deliverables |
|---------|--------|-----------------|
| DB Refactoring | COMPLETE | Renamed to solomonai, 50+ indexes |
| Seed Data v1 | COMPLETE | Abundant: 25K members, $43M GMV, 171K donations |
| Seed Data v2 | COMPLETE | +3 tenants: Potter's House, EdenX, City Reach |
| Solomon Pay | COMPLETE | Ledger, tokenization, fees, refunds, recurring scheduler |
| Stripe Removal | COMPLETE | Zero traces in codebase |
| Recurring Scheduler | COMPLETE | Hourly asyncio, idempotent, retry, auto-pause |
| Kids Printer/Kiosk | COMPLETE | LabelPrinter.jsx, KioskCheckin.jsx, family lookup |
| Help System | COMPLETE | HelpTooltip on all pages, 30+ entries |
| Calendar | COMPLETE | FullCalendar, CRUD, recurring events |
| Communications | COMPLETE | Templates, merge fields, Twilio scaffold |
| Google OAuth | COMPLETE | Sign in with Google, role-based routing |
| God Mode | COMPLETE | 7-tab view, GMV/MRR/ARR hero KPIs |
| B.1-B.19 UAT Fixes | COMPLETE | All 19 UAT bugs fixed |
| Branding (C) | COMPLETE | Solomon AI sidebar, dynamic tenant names |
| Integrations (D) | COMPLETE | Competitors removed, 5-category layout |
| Multi-Campus (E) | COMPLETE | Campus selector, dynamic portal branding |
| Frank Luntz (S partial) | COMPLETE | Key messaging rewrites done |

## Test Status
- Iteration 79: 26/26 backend pass, 95% frontend — Section B-G UAT
- Iteration 78: 22/22 backend pass — Sprint 1A-2E
- Iteration 77: 100% pass — God Mode Dashboard

## Credentials
- Platform Admin: admin@solomonai.us / Demo2026!
- Church Admin (Abundant East): shannonnieman1030@gmail.com / Demo2026!
- Portal Member: member@abundant.church / Demo2026!
- Church Admin (Potter's House): admin@pottershouse.org / Demo2026!
- Church Admin (EdenX): admin@edenx.church / Demo2026!
- Church Admin (City Reach): admin@cityreach.church / Demo2026!

## MOCKED Integrations
- Solomon Pay: SimulationAdapter (not live acquirer)
- Twilio SMS: Scaffolded (no real keys)
- Printer: Web Print (window.print)
- Google OAuth: Live (Emergent Auth)

## Remaining High-Priority Work

### P0 — UAT Final Polish:
- Full Frank Luntz messaging audit (all pages — S section)
- God Mode church portfolio table with health scores (G.2)
- Services Module Expansion (positions, scheduling, CCLI) — Phase 3A
- Live demo onboarding flow (Add New Church wizard) — Phase T

### P1:
- Commerce multi-payment (Apple Pay, Google Pay, PayPal) — Phase O
- Custom Report Builder + Workflow Builder — Phase P
- People Enhancements (household roles, bulk update) — Phase Q
- Technical Hardening (persistent rate limiting, object storage) — Phase R

### P2 (Future):
- Phase H: Bloomberg-grade Reports (9-tab analytics)
- Phase I: Solomon AI full intelligence (PDF gen, cross-tenant)
- Phase J: Feature education headers on every page
- Phase N: Services module expansion
- Phase U: Bidirectional data sync verification
- Phase W: Full UAT checklist execution

## Deferred / Out of Scope
- Native mobile app (iOS/Android)
- Apple Pay / Google Pay (scaffolded only)
- Monday summary emails
- Final Production Deployment
