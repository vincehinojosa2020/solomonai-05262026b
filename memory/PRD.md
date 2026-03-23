# Solomon AI — Church Management Platform PRD

## Product Overview
Solomon AI is a multi-tenant SaaS Church Management System built with React (frontend), FastAPI (backend), and MongoDB. Supports multiple church tenants with per-campus billing, member portals, admin dashboards, and real-time bidirectional sync. Multi-campus organizations supported with campus switcher UI.

## Core Architecture
- Frontend: React (CRA) at port 3000, 44+ routes
- Backend: FastAPI at port 8001, ~300+ endpoints  
- Database: MongoDB (test_database)
- Auth: Session tokens + Google OAuth + Claims-based RBAC (40+ permissions)
- Domain: samsonaitest.xyz / solomonai.us
- Multi-Campus: Organization model with campus switcher

---

## Complete Feature Inventory

### Foundation (MVP)
- Multi-tenant architecture with campus-level isolation
- Session tokens + Google Auth + Claims-based RBAC
- Member Portal + Admin Dashboard + Platform Admin

### Multi-Campus Organization Support (March 21, 2026)
- Organization model linking tenants
- Campus switcher dropdown in AppShell
- `POST /api/auth/switch-campus` endpoint
- Shannon/Aivy can switch between East/Downtown/West

### Landing Page & Support (March 21, 2026)
- Public landing page at `/` - Hero, value props, features grid, CTA, footer
- Support page at `/support` - Contact cards, FAQ accordion
- Apple App Store compliant (copyright, support URL)
- Mobile responsive, Frank Luntz copy style

### Phase 1-8: All Previous Features (March 20)
- RBAC, Security, Volunteers, QR Check-In, Ask Solomon Chat
- Sunday Morning Engine, Onboarding Wizard, Reports & Exports
- War Room, Payment Orchestration, Audit Trail, PDF Export
- Admin Permission Editor

---

## Test Accounts
| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@solomon.ai | Demo2026! |
| Church Admin (Aivy) | avopham@gmail.com | SolomonTest2026! |
| Lead Pastor (Shannon) | shannonnieman1030@gmail.com | SolomonTest2026! |
| Member (Jacob) | jacobpacheco@abundanteast.com | SolomonTest2026! |

Shannon has GOD MODE (38 permissions) + multi-campus access (East, Downtown, West).

## Demo Data
- Abundant East: 22K members, A+ (100)
- Abundant Downtown: 18.5K members, A+ (100)
- Abundant West: 14K members, A+ (100)
- Non-Abundant: F scores (20-31) for pitch contrast

## Mocked Features
- Payment Processors: All 6 return mock responses
- SMS Notifications: Console logged

## Phase A: Planning Center Competitor (IN PROGRESS)
Backend routes done. Frontend pages NOT YET built:
- Services/Worship Planning
- Volunteer Scheduling  
- Households
- Member Directory
- Pricing Page
- Church Branding Settings
- Smart Ask Solomon context injection

## Remaining Backlog
- P0: Phase A frontend implementation
- P1: Pricing page at /pricing
- P1: Privacy policy page
- P2: Real Stripe/Pushpay integration
- P2: Push notifications with real VAPID keys
- P2: server.py modular refactor (~15k lines)
- P3: React Native mobile app
