# Solomon AI — Product Requirements Document

## Original Problem Statement
Solomon AI is a full-featured, multi-tenant SaaS church management system competing directly with Planning Center. Built with React frontend, FastAPI backend, and MongoDB. Target: 100% Planning Center feature parity at 1/3 the price ($99/mo).

## Architecture
- **Frontend**: React + Shadcn UI (port 3000)
- **Backend**: FastAPI monolith `server.py` (port 8001)
- **Database**: MongoDB Atlas
- **AI**: Claude Sonnet 4.5 via Emergent LLM Key
- **Multi-Tenant**: Organizations -> Campuses -> Members
- **Mobile**: React Native (separate Emergent project, calls our APIs)

## Current Parity Status: ~82%

## Completed Features

### Phase 0: Core Platform (Pre-existing)
- Member management (People module) with CSV import
- Groups, Calendar/Events, Worship/Services, Check-in, Media Library
- Abundant Cafe, Merch Store, Solomon Academy (Abundant Pathways)
- War Room, Multi-campus, Ask Solomon AI, Member Portal
- Landing page with Frank Luntz copywriting
- OG tags, quality seed data, 14 accounts, 11 tenants

### Phase 1: SolomonPay + Lead Capture (March 2026) ✅
- SolomonPay UI scaffolding (payment form, backend models, all "pending")
- Integrated into Giving, Cafe checkout, Merch checkout
- Landing page Invicti-style lead capture modal
- Lead management (POST /api/leads/capture + GET /api/admin/leads)
- Competitor knowledge base injected into Ask Solomon AI (173 PC transcripts)

### Phase 2: Calendar Approvals + People Workflows (March 2026) ✅
- Calendar room booking approval system with conflict detection
- Rooms management (10 seeded rooms)
- Approve/reject individual + bulk with status tracking
- Conflict resolution UI (side-by-side overlapping bookings)
- People workflow builder (5 step types: email, task, call, add_to_group, wait)
- Workflow enrollments with step tracking
- Form builder with configurable field types (9 types)
- Public form URLs with auto-profile creation for visitors
- Form submissions viewer
- Duplicate detection (fuzzy name matching + email/phone scoring)
- Profile merge with data consolidation
- Smart Lists with rule-based filtering (5 operators: equals, not_equals, contains, exists, not_exists)

## Test Results
- Iteration 53: Competitor AI knowledge (8/10 pass - 2 LLM budget)
- Iteration 54: SolomonPay + Lead Capture (Backend 92%, Frontend 100%)
- Iteration 55: Calendar Approvals + People Workflows (Backend 97%, Frontend 100%)

## Planning Center Parity Roadmap

### Phase 3: Services Module (NEXT - Weeks 3-4)
- Plan templates, team/position management
- Song library (title, artist, CCLI, arrangements)
- Scheduling system with blockout dates
- Music Stand chord chart viewer
- Matrix scheduling (may need consultant, 4-6 hours)

### Phase 4: Groups Module Enhancement (Week 5-6)
- Group types/categories, tag organization
- Enrollment workflows (open/closed/request-to-join)
- Group events, RSVP, chat scaffolding (WebSocket, ~3 hours consultant)

### Phase 5: Registrations Module (Week 7-8)
- Signup wizard, selection types, add-ons
- Custom questions, discounts, scholarships
- SolomonPay integration for event payments, waitlists

### Phase 6: Check-Ins Module Enhancement (Week 9-10)
- Station modes, label design interface
- Medical/allergy alerts, guardian verification
- Printer support (~6 hours hardware consultant)

### Phase 7: Publishing + Home Dashboards (Week 11-12)
- Custom page builder, theme customization
- Role-based dashboards (executive, worship leader, children's ministry)
- Pledge campaigns, year-end giving statements

### Phase 8: Church Center Mobile API (Week 13-14)
- Push notification endpoints, offline data sync
- Mobile-optimized API responses

## Pricing Tiers
- Starter: $99/mo (single campus, core features)
- Growth: $1,499/mo (multi-campus, all features)
- Enterprise: $2,999/mo (unlimited everything)

## 3rd Party Integrations
- Anthropic Claude Sonnet 4.5 (Ask Solomon) — Emergent LLM Key
- Gemini Image Gen (OG Tags) — Emergent LLM Key
- SolomonPay — MOCKED (all transactions pending)
- Workflow notifications — MOCKED (no actual emails sent)

## Test Credentials
- Platform Admin: admin@solomonai.us / Demo2026!
- Church Admin: shannonnieman1030@gmail.com / Demo2026!
- Church Admin: jacobpacheco@abundanteast.com / Demo2026!

## Key Files
- /app/backend/server.py — All API endpoints (~16K+ lines)
- /app/frontend/src/pages/CalendarApprovals.jsx
- /app/frontend/src/pages/WorkflowsPage.jsx
- /app/frontend/src/pages/FormsPage.jsx
- /app/frontend/src/pages/DuplicatesPage.jsx
- /app/frontend/src/pages/SmartListsPage.jsx
- /app/frontend/src/components/SolomonPayForm.jsx
- /app/frontend/src/pages/LandingPage.jsx
