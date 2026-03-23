# Solomon AI — Church Management Platform PRD

## Product Overview
Multi-tenant SaaS Church Management System. React + FastAPI + MongoDB. Multi-campus organizations supported. Admin/Member toggle (Lyft dual-mode). Full platform admin user management with role promotions.

## Accounts (All password: Demo2026!)
| Name | Email | Role | Access |
|------|-------|------|--------|
| Platform Admin | admin@solomonai.us | Platform Admin | All churches, create users, promote roles |
| Shannon Nieman | shannonnieman1030@gmail.com | Lead Pastor (38 perms) | East, Downtown, West (God Mode) |
| Jacob Pacheco | jacobpacheco@abundanteast.com | Pastoral Staff (38 perms) | East, Downtown, West (God Mode) |
| Aivy Vopham | avopham@gmail.com | Church Admin | East, Downtown, West |

## Key Platform Features
- **Create User**: Platform admin creates accounts tied to specific churches (9 role templates)
- **Promote to Admin**: Platform admin changes any member's role -> user gets admin toggle on next login
- **Multi-Campus**: Campus switcher for org-level admins (Abundant: East, Downtown, West)
- **Admin/Member Toggle**: Users with admin permissions can switch between admin and member views
- **Church Isolation**: Church admins cannot see other churches or platform-level data

## Demo Data
- Abundant East: 22K members, A+ (100) health score
- Abundant Downtown: 18.5K members, A+ (100)
- Abundant West: 14K members, A+ (100)
- Non-Abundant: F scores (20-31) for pitch contrast

## Phase A: Planning Center Competitor — COMPLETED (March 2026)
All backend APIs + frontend pages implemented:
- **Pricing Page** (`/pricing`): Public page with 3 tiers (Starter/Free, Growth/$99, Enterprise/$249), FAQ section
- **Services/Worship Planning** (`/services`): Create service plans, add items (songs/prayers/sermons), status management
- **Volunteer Scheduling** (`/volunteers`): Teams tab (create/manage teams), Schedule tab (assign volunteers to dates/roles)
- **Households** (`/households`): Create/search households, address management, member linking
- **Member Directory** (`/portal/directory`): Portal page with search, privacy-respecting member cards
- **Church Branding** (`/settings` -> Appearance tab): App name, tagline, primary color, logo URL, live preview, persists via API

## Navigation Updates
- Admin Sidebar: Services & Volunteers under MINISTRY section
- Portal Nav: Directory link added
- Landing Page: Pricing link in header & footer

## Completed Features (All Sessions)
- Multi-Campus Switcher UI + backend
- "Lyft-style" Admin/Member view toggle
- Public Landing Page (`/`) and Support Page (`/support`)
- Apple AASA file for iOS universal links
- Platform Dashboard: Create User & Promote to Admin
- Startup DB Seed script (safe upserts)
- Production Auth Bug RESOLVED
- Phase A frontend pages (6 pages, all tested)

## Backlog
- P2: Real Stripe/Pushpay integration (currently mocked)
- P2: Push notifications with real VAPID keys
- P2: server.py modular refactor (~15k lines)
- P3: React Native mobile app

## Architecture
```
/app/
├── backend/
│   └── server.py             # ~15,400 line monolith. ALL endpoints & DB seeding.
├── frontend/
│   ├── public/.well-known/apple-app-site-association
│   └── src/
│       ├── components/layout/AppShell.jsx    # Sidebar + campus switcher
│       ├── components/layout/PortalLayout.jsx # Portal nav
│       ├── pages/PricingPage.jsx             # NEW - Public pricing
│       ├── pages/ServicesPage.jsx            # NEW - Service planning
│       ├── pages/HouseholdsPage.jsx          # NEW - Household management
│       ├── pages/VolunteerPage.jsx           # NEW - Volunteer teams & schedule
│       ├── pages/portal/PortalDirectory.jsx  # NEW - Member directory
│       ├── pages/SettingsPage.jsx            # ENHANCED - Branding API integration
│       └── pages/LandingPage.jsx             # ENHANCED - Pricing link
```

## 3rd Party Integrations
- Anthropic Claude (Ask Solomon) — uses Emergent LLM Key
- Stripe/Pushpay — MOCKED
