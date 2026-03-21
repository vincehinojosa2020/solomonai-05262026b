# Solomon AI — Church Management Platform PRD

## Product Overview
Solomon AI is a multi-tenant SaaS Church Management System built with React (frontend), FastAPI (backend), and MongoDB. Supports multiple church tenants with per-campus billing, member portals, admin dashboards, and real-time bidirectional sync. Now supports **multi-campus organizations** where a single admin can manage multiple campuses.

## Core Architecture
- Frontend: React (CRA) at port 3000, 42+ routes
- Backend: FastAPI at port 8001, ~300+ endpoints  
- Database: MongoDB (test_database)
- Auth: Session tokens + Google OAuth + Claims-based RBAC (40+ permissions)
- Domain: samsonaitest.xyz
- Multi-Campus: Organization model with `accessible_tenant_ids` per user, campus switcher in UI

---

## Complete Feature Inventory

### Foundation (MVP)
- Multi-tenant architecture with campus-level isolation
- Session tokens + Google Auth + Claims-based RBAC
- Member Portal: Home, Kids Check-in, Watch, Merch, Cafe, Give, Groups, Events, Me
- Admin Dashboard: Members, Households, Attendance, Groups, Events, Kids, Giving, Media, Communications
- Platform Admin: SaaS metrics, Church Health Score, Campus Comparison, MRR/ARR

### Multi-Campus Organization Support (March 21, 2026)
- Organization model: `organization_id` links tenants, `accessible_tenant_ids` on users
- Campus switcher dropdown in AppShell top bar
- `POST /api/auth/switch-campus` endpoint to change active campus
- `/auth/me` returns `accessible_campuses`, `organization_id`, `active_tenant_id`
- Shannon Nieman (Lead Pastor) can switch between East/Downtown/West

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

### Task 7b — PDF Export for Reports (March 20)
- POST /api/admin/reports/export with format=csv|pdf
- Branded PDF with church name, date range, tables, page numbers

### Task 7c — Admin Permission Editor UI (March 20)
- Permissions tab in PersonDetail page
- Checkbox grid organized by category with role templates

---

## Test Accounts
| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@solomon.ai | Demo2026! |
| Church Admin (Aivy) | avopham@gmail.com | SolomonTest2026! |
| Lead Pastor (Shannon) | shannonnieman1030@gmail.com | SolomonTest2026! |
| Member (Jacob) | jacobpacheco@abundanteast.com | SolomonTest2026! |
| Member (Vince) | vince@charlottesoftwareengineering.com | SolomonTest2026! |

**Shannon Nieman** has GOD MODE (all 38 permissions) and multi-campus access to East, Downtown, West.
**Aivy Vopham** also has multi-campus access.

## Demo Data
- **Abundant East**: 22K members, A+ health score (100)
- **Abundant Downtown**: 18.5K members, A+ health score (100)
- **Abundant West**: 14K members, A+ health score (100)
- **Non-Abundant churches**: F health scores (20-31) for pitch contrast

## Mocked Features
- **Payment Processors**: All 6 return realistic mock responses
- **SMS Notifications**: Logged to console

## Phase A: Planning Center Competitor Features (IN PROGRESS)
Backend routes completed, frontend pages NOT YET built:
- Services/Worship Planning (`/api/admin/services/plans`)
- Volunteer Scheduling (`/api/admin/volunteers/schedule`)
- Households (`/api/admin/households`)
- Member Directory (`/api/portal/directory`)
- Pricing Page (public `/pricing`)
- Church Branding Settings (`/api/admin/settings/branding`)
- Smart Ask Solomon context injection

## Remaining Backlog
- P0: Phase A frontend implementation (Services, Households, Directory, Pricing, Branding)
- P2: Real Stripe/Pushpay integration (when accounts ready)
- P2: Push notifications with real VAPID keys
- P2: server.py modular refactor (~15,000 lines)
- P3: React Native mobile app
- Enhancement: Multi-Campus Analytics rollup view
