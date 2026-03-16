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
│   ├── server.py              # Main FastAPI server (13K+ lines)
│   ├── database.py            # Shared DB connection
│   ├── auth.py                # Auth helpers
│   ├── routes/                # Modular route modules
│   │   ├── announcements.py, geofence.py, giving_nudge.py
│   │   ├── media_uploads.py, messaging.py, push.py, volunteer.py
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── constants/theme.js # Centralized design tokens
│   │   ├── lib/utils.js       # API_URL = '/api' (relative)
│   │   ├── components/CampusComparison.jsx  # Multi-campus comparison
│   │   ├── pages/PlatformDashboard.jsx      # Platform admin w/ orgs tab
│   │   ├── pages/Dashboard.jsx              # Church admin dashboard
│   │   ├── pages/portal/                    # Member portal pages
│   │   └── hooks/
│   └── public/
└── seed_campuses.py           # Multi-campus data seeder
```

## What's Been Implemented

### Phase 1: Critical URL Fix (March 16, 2026) ✅
- Converted ALL frontend API calls from hardcoded URLs to relative paths (`/api/...`)
- Root cause fix for "Failed to fetch" on production

### Phase 2: Bug Fixes (March 16, 2026) ✅
- Bug A: Admin Kids Check-In count fixed (was 0)
- Bug B: Geofence Config returns valid coordinates (was undefined)
- Bug C: My Groups returns member's groups (was empty)

### Phase 3: Multi-Campus Data Seeding (March 16, 2026) ✅
- 3 Abundant Church campuses: East (20K), Downtown (18K), West (12K) = 50,000 total
- Realistic demo data: donations, cafe, merch, groups, events, kids, attendance, sermons
- Dashboard stats tenant-aware via cached boosted numbers

### Phase 4: Platform Enhancements (March 16, 2026) ✅
- **Universal Campus Comparison**: Organizations tab, side-by-side campus metrics with bar/line charts, efficiency metrics (engagement rate, attendance rate, giving per capita, recurring donor %, members per group)
- **Platform Admin MRR Dashboard**: $7K MRR, $84K ARR, health monitoring banner
- **Giving Nudge System**: "While You're Here" in Cafe checkout, "Add a Gift with Your Purchase" in Merch — with $5-$100 presets, Custom, Skip
- **Design Token Centralization**: `/constants/theme.js` with CSS variable injection
- **SaaS Hardening**: Token aliases (session_token, token, access_token), admin→portal access, CORS open for mobile

### Earlier Completed Work
- Bearer Token authentication system
- Global fetch interceptor (auto-adds Bearer token)
- Login performance fix (<300ms)
- Full member portal (Home, Kids, Watch, Merch, Cafe, Give, Groups, Events, Next Steps, Prayer, Volunteer, Profile)
- Full admin dashboard with charts
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
- Stripe (Payments) — MOCKED for demo
- Resend (Email)
- Emergent-managed Google Auth
- Anthropic Claude (AI Chat)
- OpenAI Whisper (Transcription)
- pywebpush (Web Push Notifications)
- chart.js / react-chartjs-2 / recharts (Charts)

## Prioritized Backlog

### P0 — Production Deploy
- [x] All URL fixes applied
- [x] All bugs fixed
- [x] All features tested (100% pass rate)
- [ ] User deploys to samsonaitest.xyz via "Save to Github"

### P1 — Upcoming
- Client-side Geofencing logic with expo-location
- Push notification setup finalization
- Figma designer handoff (theme.js is ready)
- Real Stripe payment processing integration
- Bidirectional sync formal certification

### P2 — Future
- Refactor server.py into modular route files
- Refactor App.css into component-specific styles
- Real-time polling (30s lists, 15s kids check-in)
- Multi-campus aggregate parent org view
- Payment processor abstraction for future swap
- 10,000 church scaling architecture
