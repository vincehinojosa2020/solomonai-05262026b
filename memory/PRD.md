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
- Giving nudge after check-in
- Idempotency key on check-in POST

### Task 5 — Ask Solomon Chat (March 20, 2026)
- SolomonChat floating FAB + chat panel rendered in both AppShell (admin) and PortalLayout (member)
- AI-powered responses via /api/solomon/chat (Claude via Emergent LLM Key)
- Features: sample prompts, voice input, clear chat, markdown formatting
- Fixed: portal dual-mode allowing admins to access member portal

### Task 8 — Sunday Morning Engine (March 20, 2026)
- Service mode detection (Sunday/Wednesday, multi-service)
- ServiceModeBanner with "I'm Here" / "Watching Online" check-in
- Attendance streak tracking with badges and progress bars
- Arrival nudge flow: Welcome → Cafe order → Giving prompt
- Geofence auto-detection hook (useGeofence) for client-side check-in
- 6 push notification templates + admin broadcast endpoint
- Geofence routes: config, check-in with haversine distance

### Task 2 — Church Onboarding Wizard (March 20, 2026)
- POST /api/platform/churches/create: Creates tenant + admin account
- 5-step wizard UI: Church Info → Services → Branding → Admin Account → Review
- Validates subdomain uniqueness and email uniqueness
- Color picker with presets, plan selection (starter/growth/enterprise)
- Integrated into PlatformDashboard "Add Church" button

### Task 6 — Reports & Export System (March 20, 2026)
- 11 report types: Executive Summary, Membership, Giving by Fund, Giving by Method, Top Donors, Attendance, Kids History, Cafe, Merch, Groups, Next Steps
- CSV export for all report types via /api/reports/{type}/export?format=csv
- Executive Summary: combined monthly metrics across all operations
- Charts: Bar charts (attendance, giving), Pie charts (membership, giving method)
- Date range filtering for time-based reports

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

## Upcoming Tasks
1. **Task 7 remaining** — Audit trail UI, structured error responses
2. **Admin Permission Editor UI** — Checkbox grid for fine-grained permission assignment
3. **PDF Export** — Add PDF generation for reports (currently CSV only)

## Future Backlog
- Real Stripe payment integration
- Push notifications (Expo/pywebpush) — infrastructure ready
- Client-side geofencing (React Native)
- server.py refactor into modular routes (~14,000 lines)
- CSS refactor and design system consolidation
