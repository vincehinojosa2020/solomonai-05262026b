# Solomon AI — Church Management Platform PRD

## Original Problem Statement
Solomon AI is a multi-tenant SaaS church management platform with:
1. **Web Application** (this project): React + FastAPI + MongoDB — samsonaitest.xyz
2. **Mobile App** (separate): React Native (Expo) — calls samsonaitest.xyz/api

**Mission**: Help the Kingdom of God grow by making giving, community, and discipleship seamlessly accessible for every church member.

## Architecture
```
/app/
├── backend/
│   ├── server.py              # Main FastAPI server
│   ├── database.py            # Shared DB
│   ├── routes/                # Modular routes (geofence, push, media, etc.)
│   └── tests/                 # Pytest test suites
├── frontend/
│   ├── src/
│   │   ├── constants/theme.js # Centralized design tokens (Figma-ready)
│   │   ├── lib/utils.js       # API_URL = '/api' (relative paths)
│   │   ├── components/        # NotificationBell, CampusComparison, etc.
│   │   ├── pages/             # Admin + Portal pages
│   │   └── hooks/usePolling.js
│   └── public/
└── seed_campuses.py           # Multi-campus seeder
```

## Complete Feature List (Production-Ready)

### Core Platform
- Multi-tenant SaaS with per-campus billing
- Bearer Token auth (3 token aliases for web + mobile compat)
- Global fetch interceptor, CORS open for mobile app
- All API calls use relative paths (/api/...)

### Member Portal
- Home: Greeting, streak badge, quick actions, events, announcements
- Kids Check-In: Check in/out with pickup codes, QR scan
- Watch: Sermons with video, categories, search, notes
- Merch: Product grid, cart, checkout with giving nudge ($10/$20/$50/$100)
- Cafe: Menu, ordering, checkout with giving nudge ($5/$10/$20/$100)
- Give: Amount presets, fund selection, frequency, saved cards (MOCKED Stripe)
- Groups: Browse, join, my groups (with real group membership data)
- Events: Browse, register, my events
- Next Steps: Membership journey with progress tracking
- Prayer: Submit requests, community feed, pray count
- Volunteer: Browse ministries, sign up
- Profile: Overview, giving history, groups, payment methods

### Admin Dashboard
- KPI stats: Members, giving, attendance, cafe, merch, groups
- Charts: Attendance trend, giving by fund
- Members management
- Kids Check-In admin (live list, checkout processing)
- Media/Sermon management
- Geofence configuration (lat/lng, radius, active hours, nudge settings)
- Settings

### Platform Admin (admin@solomon.ai)
- All churches overview with MRR, member counts, MTD giving
- Organizations tab: Multi-campus church grouping
- Campus Comparison: Bar/line charts, efficiency metrics
- Church Health Score: 0-100 composite (engagement, giving, community, attendance, growth)
- Health monitoring: DB status, active sessions, uptime
- MRR/ARR display

### Notifications
- Notification bell with unread badge count
- Read/unread management
- Admin broadcast to all tenant members
- 30-second polling for real-time updates

### Bidirectional Sync
- Polling: 15s kids check-in, 30s all other screens
- Visibility-aware (pauses when tab hidden)
- CRUD operations on web reflect on mobile within poll cycle

### Geofence Arrival Flow
- Check-in returns nudge data (cafe open, giving amounts)
- Arrival card: "Order Coffee" + "Give Today" quick actions
- Configurable per-tenant via admin settings

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

## MOCKED Components
- **Stripe Payments**: Donations create records but no real charges. Cards are seeded mock data.
- All other features use real MongoDB data.

## Testing Status
- Iteration 37: 19/19 (Phase 1-3)
- Iteration 38: 18/18 (Phase 4 enhancements)  
- Iteration 39: 27/27 (Post-MVP all batches)
- **Total: 100% pass rate across all iterations**

## Deployment Status
- **MVP Status**: READY FOR DEPLOYMENT (March 16, 2026)
- **Final Health Check**: All systems operational — Backend, Frontend, MongoDB running
- **Login**: Verified working for all demo accounts
- **Dashboard**: Platform Admin view loads with church data, health scores, MRR
- **Testing**: 100% pass rate (64/64 tests across 3 iterations)

## Future Backlog (P2)
- Real Stripe payment integration
- Refactor server.py (13K lines) into modular route files
- Refactor App.css into component-specific styles
- 10K church scaling architecture
- Push notification delivery (actual device push via Expo)
