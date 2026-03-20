# Solomon AI — Church Management Platform PRD

## Product Overview
Solomon AI is a multi-tenant SaaS Church Management System built with React (frontend), FastAPI (backend), and MongoDB. It supports multiple church tenants with per-campus billing, member portals, admin dashboards, and real-time bidirectional sync for mobile/web.

## Target Users
- **Platform Admins**: SaaS operators managing all church tenants
- **Church Admins**: Pastors/staff managing their church campus
- **Members**: Church attendees using the member portal
- **Group Leaders**: Members with leadership roles

## Core Architecture
- Frontend: React (CRA) at port 3000
- Backend: FastAPI at port 8001
- Database: MongoDB
- Auth: JWT session tokens + Google OAuth
- Real-time: Polling-based sync (15-30s intervals)

---

## What's Been Implemented

### MVP Features (Complete)
- Multi-tenant architecture with campus-level isolation
- JWT + Google Auth with session cookies
- Member Portal: Home, Kids Check-in, Watch, Merch, Cafe, Give, Groups, Events, Me
- Admin Dashboard: Members, Households, Attendance, Groups, Events, Kids, Giving, Media, Communications
- Platform Admin: SaaS metrics, Church Health Score, Campus Comparison, MRR/ARR

### Mobile Browser Testing Day Fixes (March 20, 2026)
- **Fix 1**: Removed all hardcoded API URLs — all use relative `/api/` paths
- **Fix 2**: Role management endpoint (`PUT /api/admin/members/{user_id}/role`)
- **Fix 3**: QR code renders persistently on Kids Check-in card (not just modal)
- **Fix 4**: Admin QR scanner + manual code entry for checkout (html5-qrcode)
- **Fix 5**: Kids admin count bug fixed (UTC date range comparison)
- **Fix 6**: Registration with church selector dropdown + auto-login
- **Fix 7**: Enhanced Add Child form (first/last name, grade, classroom)
- **Fix 8**: Mobile Safari optimizations (font-size 16px, 48px tap targets, safe areas)

### Data & Demo
- 50,000+ seeded demo records
- 3 Abundant Church campuses (East, Downtown, West)
- Real test accounts: Vince Hinojosa (member), Aivy Vopham (church_admin)

---

## Test Accounts
| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@solomon.ai | Demo2026! |
| Church Admin | admin@abundant.church | Demo2026! |
| Church Admin | avopham@gmail.com | SolomonTest2026! |
| Member | vince@charlottesoftwareengineering.com | SolomonTest2026! |
| Member | member@abundant.church | Demo2026! |

---

## Key API Endpoints
- `POST /api/auth/login` — Login (returns token + role + tenant)
- `POST /api/auth/register` — Register (returns token for auto-login)
- `GET /api/portal/kids` — Get member's children
- `POST /api/portal/kids/{child_id}/checkin` — Check in child (returns pickup_code)
- `GET /api/admin/kids/checkins/today` — Admin: today's checkins with count
- `POST /api/admin/kids/checkout-by-code` — Admin: checkout by QR/code
- `PUT /api/admin/members/{user_id}/role` — Promote/demote roles
- `GET /api/churches/list` — Public church list for registration
- `GET /api/tenants/list` — Active tenants list

---

## Mocked Features
- **Payment/Stripe**: Give page simulates donations, no real charges
- **SMS Notifications**: Logged to console, not sent

## Post-MVP Backlog (P1)
1. Real Stripe payment integration
2. Push notification delivery (Expo/pywebpush)
3. Client-side geofencing (React Native)
4. Ask Solomon AI chat endpoint

## Future Tasks (P2)
1. Refactor server.py (13K+ lines) into modular routes
2. Refactor App.css into component-specific styles
3. 10K church scaling architecture
4. Bidirectional sync certification
5. Dual role / leader mode switching
6. Church invite code system
