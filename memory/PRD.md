# Solomon AI — Product Requirements Document

## Original Problem Statement
Build a church management SaaS platform (Solomon AI) to replace Planning Center. Multi-tenant architecture supporting organizations with multiple campuses. Features include giving, check-in, groups, events, sermons, prayer, member management, cafe ordering, and AI-powered assistance.

## User Personas
- **Platform Admin**: God Mode oversight across all churches (admin@solomonai.us)
- **Church Admin**: Manages a single church or multi-campus org (shannonnieman1030@gmail.com)
- **Church Member**: Portal access for giving, groups, events, prayer, cafe, directory, courses
- **Kids Volunteer**: Check-in/checkout of children

## Core Architecture
- **Backend**: FastAPI monolith (`server.py`) with MongoDB
- **Frontend**: React + Tailwind + Shadcn/UI
- **Multi-Tenant**: Organizations -> Campuses (tenants) -> Members
- **Billing Model**: 1 Account = Multiple Campuses (per-org billing)

## Completed Features

### Phase A — Frontend Pages (DONE)
- `/pricing` — Pricing page
- `/services` — Services management
- `/households` — Household management
- `/portal/directory` — Member directory (25+ seeded profiles with search)
- `/portal/volunteer` — Volunteer portal

### Solomon Academy — LMS (DONE)
- Course builder: Modules, Lessons (Video/Text/Quiz/Download)
- Admin: `/admin/courses` with editors
- Portal: `/portal/courses` with lesson viewer

### Pre-Demo Features A-F (DONE — March 26, 2026)
- **A. Campus Switcher "All Campuses"**: Aggregate view in dashboard
- **B. Platform God Mode Visual Upgrade**: Enhanced header, 6 KPI cards
- **C. Manual Kids Check-In**: Blue [+ Manual Check-In] button
- **D. Cafe Enterprise Redesign**: Stripe/Notion-style aesthetic
- **E. CSV Member Import**: 4-step wizard
- **F. Communications Page**: Compose, Sent, Scheduled, Templates, Segments

### Public Pages (DONE — March 26, 2026)
- `/` — Marketing Landing Page (Stripe meets Linear aesthetic)
- `/login` — Login with "Your church. Elevated." tagline
- `/signup` — Church Onboarding Wizard
- `/demo` — Demo Request Page

### War Room Mission Control (DONE)
- `/war-room` — Dark navy dashboard with real-time KPIs

### Quality Improvements (DONE — March 26, 2026)
- **7C: Member Directory Seed**: 25+ realistic member profiles with names, groups, search
- **7D: Solomon Chat Context**: Live church data injected (members, events, announcements, groups)
- **7E: Attendance Streaks**: Shannon & Jacob seeded with 12-week consecutive streaks, 3 badges

### Giving Platform Scaffold (DONE — March 26, 2026)
- Admin Giving Integrations UI with Solomon Pay, Pushpay, SecureGive cards
- Backend endpoints: GET/POST connect/disconnect processors (MOCKED)
- Seed data: Solomon Pay set as default active processor

## Mocked Integrations
- **Stripe/Pushpay/SecureGive** — Payment processing (MOCKED, scaffolded for future)
- **Twilio** — Communications send (STUBBED, records saved to DB)

## Test Reports
- Iteration 47: Phase A (PASSED)
- Iteration 48: Solomon Academy (PASSED)
- Iteration 49: Demo Features A-F (PASSED — 100%)
- Iteration 50: Landing, Signup, Demo, War Room (PASSED — 100%)
- Iteration 51: Quality Improvements 7C/7D/7E + Giving Integrations (PASSED — 100% backend, 80% frontend)

## Tech Stack
- FastAPI + MongoDB (backend)
- React + Tailwind + Shadcn/UI (frontend)
- Anthropic Claude (Solomon Chat via Emergent LLM Key)

## Credentials
- Platform Admin: admin@solomonai.us / Demo2026!
- Church Admin (Multi-Campus): shannonnieman1030@gmail.com / Demo2026!
- Church Admin: jacobpacheco@abundanteast.com / Demo2026!
- Church Member: member@abundant.church / Demo2026!
