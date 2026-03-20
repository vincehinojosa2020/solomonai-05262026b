# Solomon AI — Church Management Platform PRD

## Product Overview
Solomon AI is a multi-tenant SaaS Church Management System built with React (frontend), FastAPI (backend), and MongoDB. It supports multiple church tenants with per-campus billing, member portals, admin dashboards, and real-time bidirectional sync for mobile/web.

## Core Architecture
- Frontend: React (CRA) at port 3000
- Backend: FastAPI at port 8001
- Database: MongoDB
- Auth: Session tokens + Google OAuth + Claims-based permissions
- Real-time: Polling-based sync (15-30s intervals)
- Domain: samsonaitest.xyz (future: samsonai.com)

---

## What's Been Implemented

### MVP Features (Complete)
- Multi-tenant architecture with campus-level isolation
- JWT session tokens + Google Auth with session cookies
- Member Portal: Home, Kids Check-in, Watch, Merch, Cafe, Give, Groups, Events, Me
- Admin Dashboard: Members, Households, Attendance, Groups, Events, Kids, Giving, Media, Communications
- Platform Admin: SaaS metrics, Church Health Score, Campus Comparison, MRR/ARR

### Phase 1 — RBAC with Fine-Grained Permissions (March 20, 2026)
- Full permission registry (40+ permission strings)
- 10 role templates (Member → Platform Admin)
- Permissions returned in login response
- `require_permission()` middleware for server-side enforcement
- 6 RBAC endpoints: templates, get/set permissions, grant, revoke, users-by-role
- Aivy promoted to church_admin with 33 permissions
- Lyft-style [Admin] ↔ [Member] mode toggle in top nav

### Phase 2 — Security Hardening (March 20, 2026)
- Rate limiting: 5/min login, in-memory counters
- Idempotency: MongoDB TTL collection for check-in dedup
- Security headers: HSTS, X-Frame-Options DENY, nosniff, XSS
- Health endpoints: /api/health, /api/health/detailed
- Session management: 24hr tokens, max 5 concurrent sessions

### Phase 3 — Volunteer Teams (March 20, 2026)
- CRUD endpoints for volunteer teams and assignments
- Kids Check-In Team seeded for Abundant East
- Aivy assigned as Team Lead

### Phase 4 — QR Check-In Polish (March 20, 2026)
- QR code increased to 200px (bright sunlight readable)
- Pickup code at 48px monospace bold
- Screen wake lock on check-in
- Giving nudge after check-in: [$10][$25][$50][$100][Not today]
- Idempotency key on check-in POST

### Mobile Browser Testing Day Fixes (March 20, 2026)
- All hardcoded URLs removed
- Registration with church selector + auto-login
- Admin QR scanner (html5-qrcode camera) + manual code entry
- Kids admin count bug fixed (UTC date range)
- Enhanced Add Child form (first/last name, grade)
- Mobile Safari optimized (16px inputs, 48px tap targets, safe areas)

### Demo Walkthrough (March 20, 2026)
- Guided first-login tour (5 steps member, 6 steps admin)
- Spotlight tooltips with progress indicators

---

## Test Accounts
| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@solomon.ai | Demo2026! |
| Church Admin | admin@abundant.church | Demo2026! |
| Church Admin (Aivy) | avopham@gmail.com | SolomonTest2026! |
| Member (Vince) | vince@charlottesoftwareengineering.com | SolomonTest2026! |
| Member | member@abundant.church | Demo2026! |

---

## Mocked Features
- **Payment/Stripe**: Give page simulates donations
- **SMS Notifications**: Logged to console

## Upcoming Tasks (Phases 5-8)
1. **Task 5** — Ask Solomon portal nav button + chat panel
2. **Task 6** — Reporting & Export system (10+ reports, CSV/PDF)
3. **Task 2** — Platform admin church onboarding wizard
4. **Task 8** — Sunday Morning Engine (geofence, nudges)
5. **Task 7 remaining** — Audit trail UI, structured error responses

## Future Backlog
- Real Stripe payment integration
- Push notifications (Expo/pywebpush)
- Client-side geofencing (React Native)
- server.py refactor into modular routes
- Admin Permission Editor UI with checkbox grid
- Dual role leader_roles field
