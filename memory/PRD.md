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
- `/` — Marketing Landing Page (clean white, Frank Luntz copy)
- `/login` — Login with "Your church. Elevated." tagline
- `/signup` — Church Onboarding Wizard
- `/demo` — Demo Request Page

### War Room Mission Control (DONE)
- `/war-room` — Dark navy dashboard with real-time KPIs

### Quality Improvements (DONE — March 26, 2026)
- **7C: Member Directory Seed**: 25+ realistic member profiles
- **7D: Solomon Chat Context**: Live church data injected
- **7E: Attendance Streaks**: Shannon & Jacob with 12-week streaks

### Giving Platform Scaffold (DONE — March 26, 2026)
- Admin UI with Solomon Pay, Pushpay, SecureGive cards
- Backend: GET/POST connect/disconnect processors (MOCKED)

### Landing Page Refinements (DONE — March 26, 2026)
- Clean white hero: "Your Church. One App. Zero Compromise."
- 3 stats only: 64,500 Members / $151M+ Given / 140+ Small Groups
- Frank Luntz copy on all sections
- Mobile responsive with hamburger menu nav
- OG preview tile for gorgeous iMessage/SMS link sharing
- Nav: Pricing | Watch Demo | Login (hamburger on mobile)
- Footer: "Built on Google Cloud Platform · Powered by Anthropic"

## Final QA Status
- **Iteration 52**: 100% pass (20/20 backend, all frontend pages verified)
- **Deployment Check**: PASS - No blockers

## Mocked Integrations
- Stripe/Pushpay/SecureGive — Payment processing (MOCKED)
- Twilio — Communications send (STUBBED)

## Credentials
- Platform Admin: admin@solomonai.us / Demo2026!
- Church Admin: shannonnieman1030@gmail.com / Demo2026!
- Church Admin: jacobpacheco@abundanteast.com / Demo2026!
- Church Member: member@abundant.church / Demo2026!

## Post-Demo Backlog
- P1: Modular monolith refactor of server.py
- P1: Real Pushpay/SecureGive API integration
- P2: Excel (.xlsx) Member Import
- P2: PDF Certificate generation
- P2: Real Stripe integration for Solomon Pay
- P2: Real Twilio SMS integration
- P2: N+1 query optimization in courses.py
