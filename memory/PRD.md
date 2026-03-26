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
- **Multi-Tenant**: Organizations → Campuses (tenants) → Members
- **Billing Model**: 1 Account = Multiple Campuses (per-org billing)

## Completed Features (as of March 2026)

### Phase A — Frontend Pages (DONE)
- `/pricing` — Pricing page
- `/services` — Services management
- `/households` — Household management
- `/portal/directory` — Member directory
- `/portal/volunteer` — Volunteer portal

### Solomon Academy — LMS (DONE)
- Course builder: Modules, Lessons (Video/Text/Quiz/Download)
- Admin: `/admin/courses` with editors
- Portal: `/portal/courses` with lesson viewer
- Collections: courses, course_modules, course_lessons, course_enrollments, course_lesson_progress
- Seeded "Abundant Next Steps" course

### Pre-Demo Features A–F (DONE — March 26, 2026)
- **A. Campus Switcher "All Campuses"**: Aggregate view in dashboard with campus breakdown KPIs
- **B. Platform God Mode Visual Upgrade**: Enhanced header, 6 KPI cards, Org→Campus hierarchy with billing notes
- **C. Manual Kids Check-In**: Blue [+ Manual Check-In] button with search/classroom modal
- **D. Cafe Enterprise Redesign**: Stripe/Notion-style pure white enterprise aesthetic, no emojis
- **E. CSV Member Import**: 4-step wizard (Upload → Map Columns → Preview → Import)
- **F. Communications Page**: Compose (Email/SMS), Sent, Scheduled, Templates, Segments tabs

### Backend APIs Added
- `POST /api/admin/members/import/parse` — Parse CSV, return headers + preview
- `POST /api/admin/members/import/execute` — Execute import with column mapping
- `GET /api/admin/dashboard/aggregate` — Aggregate stats across all campuses
- `POST /api/admin/communications/send` — Send email/SMS (Twilio-ready stub)
- `GET /api/admin/communications/list` — List sent/scheduled communications

## Mocked Integrations
- **Stripe/Pushpay** — Payment processing (MOCKED)
- **Twilio** — Communications send (STUBBED, records saved to DB)

## Test Reports
- Iteration 47: Phase A (PASSED)
- Iteration 48: Solomon Academy (PASSED)
- Iteration 49: Demo Features A–F (PASSED — 100% backend, 100% frontend)

## Tech Stack
- FastAPI + MongoDB (backend)
- React + Tailwind + Shadcn/UI (frontend)
- react-markdown (text lesson rendering)

## Credentials
- Platform Admin: admin@solomonai.us / Demo2026!
- Church Admin (Multi-Campus): shannonnieman1030@gmail.com / Demo2026!
- Church Admin: jacobpacheco@abundanteast.com / Demo2026!
- Church Member: member@abundant.church / Demo2026!
