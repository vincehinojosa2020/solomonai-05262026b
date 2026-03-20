# Solomon AI — Church Management Platform PRD

## Product Overview
Solomon AI is a multi-tenant SaaS Church Management System built with React (frontend), FastAPI (backend), and MongoDB. Supports multiple church tenants with per-campus billing, member portals, admin dashboards, and real-time bidirectional sync.

## Core Architecture
- Frontend: React (CRA) at port 3000, 42 routes
- Backend: FastAPI at port 8001, ~300 endpoints  
- Database: MongoDB
- Auth: Session tokens + Google OAuth + Claims-based RBAC (40+ permissions)
- Domain: samsonaitest.xyz

---

## Complete Feature Inventory

### Foundation (MVP)
- Multi-tenant architecture with campus-level isolation
- Session tokens + Google Auth + Claims-based RBAC
- Member Portal: Home, Kids Check-in, Watch, Merch, Cafe, Give, Groups, Events, Me
- Admin Dashboard: Members, Households, Attendance, Groups, Events, Kids, Giving, Media, Communications
- Platform Admin: SaaS metrics, Church Health Score, Campus Comparison, MRR/ARR

### Phase 1 — RBAC (March 20)
- 40+ permission strings, 10 role templates, Claims-based middleware

### Phase 2 — Security Hardening (March 20)
- Rate limiting, Idempotency (TTL), HSTS/security headers, Session management

### Phase 3 — Volunteer Teams (March 20)
- CRUD for volunteer teams and assignments

### Phase 4 — QR Check-In Polish (March 20)
- 200px QR, 48px pickup code, Screen wake lock, Giving nudges

### Task 5 — Ask Solomon Chat (March 20)
- Floating FAB + chat panel in admin and portal layouts
- Claude AI via Emergent LLM Key

### Task 8 — Sunday Morning Engine (March 20)
- Service mode detection, Attendance streaks, Arrival nudge flow
- 6 push notification templates + admin broadcast endpoint
- Geofence hook for client-side auto check-in

### Task 2 — Church Onboarding Wizard (March 20)
- 5-step wizard: Info -> Services -> Branding -> Admin Account -> Review
- POST /api/platform/churches/create creates tenant + admin

### Task 6 — Reports & Export System (March 20)
- 11 report types with CSV export
- Executive Summary combining all metrics

### War Room — Sunday Morning Command Center (March 20)
- Full-screen dark navy page at /war-room
- Animated live counters, Activity feed, Capacity gauges
- Auto-refresh every 15 seconds with LIVE pulse badge

### Payment Orchestration Layer (March 20)
- 6 processors: Stripe, Pushpay, Tithe.ly, Planning Center, Subsplash, Manual
- Unified POST /api/giving/process routes to active processor
- All processors currently MOCKED

### Task 7a — Audit Trail UI (March 20)
- GET /api/admin/audit-log with filters (date, action, user)
- Full audit log page at /audit-log with filter pills, search, date range
- Expandable rows with before/after values
- CSV export of audit data
- Structured 500 error responses with correlation_id

### Task 7b — PDF Export for Reports (March 20)
- POST /api/admin/reports/export with format=csv|pdf
- Branded PDF: Header, church name, date range, tables, page numbers
- Kids compliance footer: "Records retained 7 years. Encrypted at rest."
- 4 admin report aliases: kids/history, giving/summary, attendance/summary, executive-summary

### Task 7c — Admin Permission Editor UI (March 20)
- Permissions tab in PersonDetail page
- Checkbox grid organized by: Member Access, Ministry Tools, Financial, Administrative
- Role template dropdown with auto-fill
- "Custom" badge when permissions differ from template
- Save and Reset to Template buttons

---

## Test Accounts
| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@solomon.ai | Demo2026! |
| Church Admin (Aivy) | avopham@gmail.com | SolomonTest2026! |
| Member (Vince) | vince@charlottesoftwareengineering.com | SolomonTest2026! |

## Mocked Features
- **Payment Processors**: All 6 return realistic mock responses
- **SMS Notifications**: Logged to console

## Remaining Backlog
- Real Stripe/Pushpay integration (when accounts ready)
- Push notifications with real VAPID keys
- Solomon AI as native payment processor
- server.py modular refactor (~15,000 lines)
- React Native mobile app
