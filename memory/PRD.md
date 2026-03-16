# Solomon AI — Church Management Platform PRD

## Original Problem Statement
Solomon AI is a multi-tenant SaaS church management platform. Two projects exist:
1. **Web Application** (this project): React + FastAPI + MongoDB — live at samsonaitest.xyz
2. **Mobile App** (separate): React Native (Expo) — calls samsonaitest.xyz/api

**Mission**: Help the Kingdom of God grow by making giving, community, and discipleship seamlessly accessible for every church member — on web and mobile.

**Business Model**: SaaS. Churches pay monthly subscriptions. Each church is a tenant with fully isolated data.

## Current Architecture
```
/app/
├── backend/
│   ├── server.py           # Main FastAPI server (13K+ lines)
│   ├── database.py         # Shared DB connection
│   ├── auth.py             # Auth helpers
│   ├── routes/             # Extracted route modules
│   │   ├── announcements.py
│   │   ├── geofence.py
│   │   ├── giving_nudge.py
│   │   ├── media_uploads.py
│   │   ├── messaging.py
│   │   ├── push.py
│   │   └── volunteer.py
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── lib/utils.js    # API_URL = '/api' (relative)
│   │   ├── utils/authFetch.js
│   │   ├── pages/          # Admin + Portal pages
│   │   ├── components/     # Shared components
│   │   └── hooks/
│   └── public/
└── seed_campuses.py        # Multi-campus data seeder
```

## What's Been Implemented

### Phase 1: Critical URL Fix (March 16, 2026)
- Converted ALL frontend API calls from hardcoded URLs to relative paths (`/api/...`)
- Removed all references to `REACT_APP_BACKEND_URL`, `emergentagent.com`, `localhost`
- Root cause fix for "Failed to fetch" on production (samsonaitest.xyz)

### Phase 2: Bug Fixes (March 16, 2026)
- **Bug A**: Admin Kids Check-In count now shows correct number (was showing 0)
- **Bug B**: Geofence Config returns valid lat/lng coordinates (was undefined)
- **Bug C**: My Groups returns member's groups (was returning empty)

### Phase 3: Multi-Campus Data Seeding (March 16, 2026)
- Created 3 Abundant Church campuses as separate tenants:
  - **Abundant East** (20,000 members, $2,500/mo MRR, $125K monthly giving)
  - **Abundant Downtown** (18,000 members, $2,000/mo MRR, $110K monthly giving)
  - **Abundant West** (12,000 members, $1,500/mo MRR, $75K monthly giving)
- Seeded realistic demo data per campus: donations, cafe orders, merch orders, groups, events, kids, attendance, sermons, announcements, prayer requests
- Dashboard stats are tenant-aware (cached boosted numbers for demo)
- Platform admin sees all 5 tenants (3 Abundant + Cristo Viene + Potter's House)

### Earlier Completed Work
- Bearer Token authentication system (stateless, mobile-compatible)
- Global fetch interceptor (auto-adds Bearer token)
- Login performance fix (removed redundant DB seeding from login)
- Cache-busting mechanisms for stale service workers
- Multi-tenant isolation
- Kids check-in/checkout system
- Sermon media management
- Cafe and Merch ordering systems
- Giving/donation system
- Groups, Events, Attendance, Prayer, Volunteer modules
- AI chat (Claude), Whisper transcription
- Push notifications (web)

## Demo Accounts
| Role | Email | Password | Tenant |
|------|-------|----------|--------|
| Platform Admin | admin@solomon.ai | Demo2026! | All |
| Abundant East Admin | admin@abundant.church | Demo2026! | abundant-east-001 |
| Abundant East Member | member@abundant.church | Demo2026! | abundant-east-001 |
| Abundant Downtown Admin | admin@abundant-downtown.church | Demo2026! | abundant-downtown-001 |
| Abundant West Admin | admin@abundant-west.church | Demo2026! | abundant-west-001 |
| Cristo Viene Admin | admin@cristoviene.church | Demo2026! | cristoviene-church-001 |
| Cristo Viene Member | member@cristoviene.church | Demo2026! | cristoviene-church-001 |
| Potter's House Admin | admin@pottershouse.church | Demo2026! | pottershouse-church-001 |

## 3rd Party Integrations
- Stripe (Payments)
- Resend (Email)
- Emergent-managed Google Auth
- Anthropic Claude (AI Chat)
- OpenAI Whisper (Transcription)
- pywebpush (Web Push Notifications)
- chart.js / react-chartjs-2 (Dashboard Graphs)

## Prioritized Backlog

### P0 — Production Deploy
- Deploy to samsonaitest.xyz (user action: "Save to Github")
- Verify post-deploy with all 6 accounts

### P1 — Upcoming
- Giving & Commerce Nudge System (4-step checkout with giving moment)
- Platform Admin Dashboard enhancements (MRR display, health monitoring, impersonation)
- Design token centralization (theme.js for Figma handoff readiness)
- Bidirectional sync certification (kids, sermons, announcements, events)
- Client-side Geofencing with expo-location
- Push notification finalization

### P2 — Future
- Refactor server.py into modular route files
- Refactor App.css into component-specific styles
- Real-time polling (30s lists, 15s kids check-in)
- Payment processor abstraction for future swap
- Multi-campus aggregate view for Abundant parent org
