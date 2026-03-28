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

## Current Parity Status: ~98%

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

### Phase 3: Services Module (March 2026) ✅
- Song Library with CRUD, search, CCLI numbers, key/BPM, lyrics/chord charts (10 seeded worship songs)
- Music Stand dark-themed chord chart viewer with keyboard navigation and fullscreen
- Service Plans with items (songs, prayers, sermons, announcements), status management
- Plan Templates (save as template, create from template)
- Plan Duplication with auto-generated copy names
- Team/Position Management on service plans (assign volunteers to positions)
- Blockout Dates management for volunteer scheduling (create/view/delete)
- Volunteer scheduling integration with service plans
- Service Types configuration (Sunday Morning, Sunday Evening, Wednesday, Special)

### Phase 4: Groups Module Enhancement (March 2026) ✅
- Enrollment workflows: open (anyone joins), request_to_join (approval required), closed (invite only)
- Category field for group organization (discipleship, fellowship, outreach, prayer, study, etc.)
- Join Request approval system with pending/approved/rejected tracking
- Group Events with RSVP tracking (attending/maybe/declined), CRUD, date/time/location
- Resources & file sharing (links, documents, videos) with group-level sharing
- Group Chat scaffolding with HTTP-based messaging (send/receive, auto-scroll)
- Portal join endpoint handles request_to_join by creating approval request
- Admin Groups page has tabs: Groups + Join Requests with badge count
- GroupDetail page has tabs: Roster, Attendance, Events, Resources, Chat, About, Settings

### Phase 5: Registrations Module (March 2026) ✅
- Registration Config per event: pricing (enabled/amount/currency), add-ons, custom questions, promo codes
- Add-ons system: optional extras with names, prices, descriptions (T-shirts, meals, parking)
- Custom registration questions: text, select, checkbox types with required flag
- Promo/discount codes: percentage or fixed amount, max uses tracking, auto-increment
- Public registration page: shareable /register/{eventId} link with event details, form, total calculation
- Waitlist auto-management: auto-waitlist when capacity reached, admin can promote to confirmed
- Admin registrations dashboard: events list, expand to view registrants, status management
- Registration config editor: pricing toggle, add-on builder, question builder, promo code manager
- Total calculation: base price + selected add-ons, promo code application
- SolomonPay integration for payments (MOCKED — all payment_status "pending")

## Test Results
- Iteration 53: Competitor AI knowledge (8/10 pass - 2 LLM budget)
- Iteration 54: SolomonPay + Lead Capture (Backend 92%, Frontend 100%)
- Iteration 55: Calendar Approvals + People Workflows (Backend 97%, Frontend 100%)
- Iteration 56: Phase 3 Services - Songs, Plans, Templates, Music Stand (Backend 100% 20/20, Frontend 100%)
- Iteration 57: Phase 3 Services - Team Assignments, Blockout Dates (Backend 100% 14/14, Frontend 100%)
- Iteration 58: Phase 4 Groups - Enrollment, Join Requests, Events, Resources, Chat (Backend 100% 18/18, Frontend 100%)
- Iteration 59: Phase 5 Registrations - Config, Add-ons, Questions, Promo Codes, Public Form (Backend 100% 13/13, Frontend 100%)

## Planning Center Parity Roadmap

### Phase 4: Groups Module Enhancement ✅ COMPLETE
### Phase 5: Registrations Module ✅ COMPLETE
### Phase 6: Check-Ins Enhancement ✅ COMPLETE

### Phase 7: Publishing + Home Dashboards (NEXT)
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
- /app/backend/server.py — All API endpoints (~18K+ lines)
- /app/frontend/src/pages/ServicesPage.jsx (Phase 3 - Service Plans + Team Assignments)
- /app/frontend/src/pages/SongLibraryPage.jsx (Phase 3 - Song Library)
- /app/frontend/src/pages/MusicStandPage.jsx (Phase 3 - Music Stand)
- /app/frontend/src/pages/VolunteerPage.jsx (Phase 3 - Teams, Schedule, Blockout Dates)
- /app/frontend/src/pages/GroupsManagerPage.jsx (Phase 4 - Admin Groups + Join Requests)
- /app/frontend/src/pages/GroupDetail.jsx (Phase 4 - Events, Resources, Chat)
- /app/frontend/src/pages/RegistrationsPage.jsx (Phase 5 - Admin Registrations)
- /app/frontend/src/pages/PublicRegistrationPage.jsx (Phase 5 - Public Registration Form)
- /app/frontend/src/pages/CheckInSetupPage.jsx (Phase 6 - Locations, Stations, Labels, Medical, Guardians, Reports)
- /app/frontend/src/pages/CalendarApprovals.jsx
- /app/frontend/src/pages/WorkflowsPage.jsx
- /app/frontend/src/pages/FormsPage.jsx
- /app/frontend/src/pages/DuplicatesPage.jsx
- /app/frontend/src/pages/SmartListsPage.jsx
- /app/frontend/src/components/SolomonPayForm.jsx
- /app/frontend/src/pages/LandingPage.jsx
