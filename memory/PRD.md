# Solomon AI — Church Management Platform PRD

## Original Problem Statement
Solomon AI is a multi-tenant SaaS church management platform. Two projects exist:
1. **Web Application** (this project): React + FastAPI + MongoDB — live at samsonaitest.xyz
2. **Mobile App** (separate): React Native (Expo) — calls samsonaitest.xyz/api

**Mission**: Help the Kingdom of God grow by making giving, community, and discipleship seamlessly accessible for every church member — on web and mobile.

**Business Model**: SaaS. Churches pay monthly subscriptions per campus. Each church/campus is a tenant with fully isolated data.

## Current Architecture
```
/app/
├── backend/
│   ├── server.py              # Main FastAPI server
│   ├── database.py            # Shared DB connection
│   ├── auth.py                # Auth helpers
│   └── routes/                # Modular route modules
├── frontend/
│   ├── src/
│   │   ├── constants/theme.js # Centralized design tokens
│   │   ├── lib/utils.js       # API_URL = '/api' (relative paths)
│   │   ├── components/CampusComparison.jsx
│   │   ├── pages/PlatformDashboard.jsx
│   │   ├── pages/Dashboard.jsx
│   │   └── pages/portal/      # Member portal pages
│   └── public/
└── seed_campuses.py           # Multi-campus data seeder
```

## Completed Features (March 16, 2026)

### MVP Features (Ready for Deploy)
1. **Critical URL Fix** — All API calls use relative paths, fixing production "Failed to fetch"
2. **3 Bug Fixes** — Kids check-in count, geofence config, my groups
3. **Multi-Campus Architecture** — 3 Abundant campuses (50K total), each billed individually
4. **Universal Campus Comparison** — Side-by-side bar/line charts, efficiency metrics
5. **Church Health Score** — Composite 0-100 score (engagement, giving, community, attendance, growth)
6. **Platform Admin Dashboard** — MRR/ARR display, health monitoring, organizations tab
7. **Giving Nudge System** — "While You're Here" cafe & "Add a Gift" merch checkout flows
8. **Design Token Centralization** — theme.js for Figma handoff readiness
9. **SaaS Hardening** — Token aliases, CORS, admin→portal access

### Full Feature List
- Multi-tenant isolation | Bearer Token auth | Global fetch interceptor
- Member Portal: Home, Kids Check-In, Watch/Sermons, Merch, Cafe, Give, Groups, Events, Next Steps, Prayer, Volunteer, Profile
- Admin Dashboard: KPI stats, charts, members, kids, media, announcements, settings
- Platform Admin: All churches, organizations, campus comparison, health scores, health monitoring
- AI Chat (Claude) | Whisper transcription | Push notifications
- Cafe & Merch ordering with giving nudge | Donation processing

## Demo Accounts
| Role | Email | Password | Tenant |
|------|-------|----------|--------|
| Platform Admin | admin@solomon.ai | Demo2026! | All |
| Abundant East Admin | admin@abundant.church | Demo2026! | abundant-east-001 |
| Abundant East Member | member@abundant.church | Demo2026! | abundant-east-001 |
| Downtown Admin | admin@abundant-downtown.church | Demo2026! | abundant-downtown-001 |
| West Admin | admin@abundant-west.church | Demo2026! | abundant-west-001 |
| Cristo Viene Admin | admin@cristoviene.church | Demo2026! | cristoviene-church-001 |
| Potter's House Admin | admin@pottershouse.church | Demo2026! | pottershouse-church-001 |

## Backlog (Post-MVP)
- P1: Client-side geofencing, push notifications, real Stripe integration, bidirectional sync certification
- P2: Refactor server.py, real-time polling, payment processor abstraction, 10K church scaling
