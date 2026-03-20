# Solomon AI — Church Management Platform PRD

## Product Overview
Solomon AI is a multi-tenant SaaS Church Management System built with React (frontend), FastAPI (backend), and MongoDB. It supports multiple church tenants with per-campus billing, member portals, admin dashboards, and real-time bidirectional sync for mobile/web.

## Core Architecture
- Frontend: React (CRA) at port 3000, 41 routes
- Backend: FastAPI at port 8001, ~290 endpoints
- Database: MongoDB
- Auth: Session tokens + Google OAuth + Claims-based permissions
- Real-time: Polling-based sync (15-30s for War Room)
- Domain: samsonaitest.xyz

---

## What's Been Implemented

### MVP Features (Complete)
- Multi-tenant architecture with campus-level isolation
- Session tokens + Google Auth with session cookies
- Member Portal: Home, Kids Check-in, Watch, Merch, Cafe, Give, Groups, Events, Me
- Admin Dashboard: Members, Households, Attendance, Groups, Events, Kids, Giving, Media, Communications
- Platform Admin: SaaS metrics, Church Health Score, Campus Comparison, MRR/ARR

### Phase 1 — RBAC (March 20, 2026)
- 40+ permission strings, 10 role templates, Claims-based middleware

### Phase 2 — Security Hardening (March 20, 2026)
- Rate limiting, Idempotency (TTL), HSTS/security headers, Session management

### Phase 3 — Volunteer Teams (March 20, 2026)
- CRUD for volunteer teams and assignments

### Phase 4 — QR Check-In Polish (March 20, 2026)
- 200px QR, 48px pickup code, Screen wake lock, Giving nudges

### Task 5 — Ask Solomon Chat (March 20, 2026)
- Floating FAB + chat panel in both admin and portal layouts
- Claude AI via Emergent LLM Key

### Task 8 — Sunday Morning Engine (March 20, 2026)
- Service mode detection, Attendance streaks, Arrival nudge flow
- 6 push notification templates + broadcast endpoint
- Geofence hook for client-side auto check-in

### Task 2 — Church Onboarding Wizard (March 20, 2026)
- 5-step wizard: Info → Services → Branding → Admin Account → Review
- POST /api/platform/churches/create creates tenant + admin

### Task 6 — Reports & Export System (March 20, 2026)
- 11 report types with CSV export
- Executive Summary combining all metrics

### War Room — Sunday Morning Command Center (March 20, 2026)
- Full-screen dark navy page at /war-room
- Animated live counters: Members, Kids Checked In, Cafe Orders, MTD Giving
- Activity feed with real-time events
- Capacity gauges: Kids (green→yellow→red), Cafe queue, Giving goal (MTD vs $250K)
- Quick action buttons: Announcement, Push, Kids, Giving
- Auto-refresh every 15 seconds with LIVE pulse badge
- Sidebar nav entry with green pulse indicator dot

### Payment Orchestration Layer (March 20, 2026)
- Tool-agnostic giving architecture — Solomon AI as orchestration layer
- 6 supported processors: Stripe, Pushpay, Tithe.ly, Planning Center Giving, Subsplash, Manual
- Unified POST /api/giving/process routes to active processor
- Connection status indicators per processor (Active/Connected/Not configured)
- Admin UI in Integrations page with connect/disconnect/set active
- Standardized transaction response format (txn_id, confirmation, fee)
- All processors currently MOCKED with realistic responses
- Future vision: Solomon AI becomes its own payment processor

---

## Test Accounts
| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@solomon.ai | Demo2026! |
| Church Admin (Aivy) | avopham@gmail.com | SolomonTest2026! |
| Member (Vince) | vince@charlottesoftwareengineering.com | SolomonTest2026! |

---

## Mocked Features
- **Payment Processors**: All 6 return realistic mock responses
- **SMS Notifications**: Logged to console

## Upcoming Tasks
- **Task 7** — Audit trail UI, structured error responses
- **PDF Export** — Add PDF generation for reports
- **Admin Permission Editor UI** — Checkbox grid for permissions

## Future Backlog
- Real Stripe/Pushpay integration (when accounts are ready)
- Push notifications with real VAPID keys
- Solomon AI as native payment processor
- server.py modular refactor (~14,000 lines)
- React Native mobile app
