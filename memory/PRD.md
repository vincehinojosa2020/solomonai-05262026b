# Solomon AI - Enterprise Church Management Platform

## Original Problem Statement
Build and maintain "Solomon AI" Church Management System for go-live deployment. Backend must support both web app and mobile app from a single database.

## Architecture
- **Frontend**: React (CRA) on port 3000
- **Backend**: FastAPI on port 8001
- **Database**: MongoDB
- **Preview URL**: https://auth-fix-preview-5.preview.emergentagent.com

## Test Accounts
| Role | Email | Password |
|---|---|---|
| Platform Admin | admin@solomon.ai | Demo2026! |
| Abundant Admin | admin@abundant.church | Demo2026! |
| Abundant Member | member@abundant.church | Demo2026! |
| Cristo Viene Admin | admin@cristoviene.church | Demo2026! |
| Cristo Viene Member | member@cristoviene.church | Demo2026! |
| Potter's House Admin | admin@pottershouse.church | Demo2026! |

## What's Been Implemented

### Core Infrastructure
- [x] Multi-tenant architecture (4 churches)
- [x] Role-based access (platform_admin, church_admin, member)
- [x] JWT/Bearer token authentication (cookie + header support)
- [x] Google OAuth integration
- [x] Global fetch interceptor for auto Bearer token injection
- [x] Service worker (push notifications only, no static caching)
- [x] Real-time polling (15-30s intervals on 8+ pages)

### Member Portal (14 screens)
- [x] Home (streak, events, announcements, Sunday check-in)
- [x] Give (amount, fund, frequency, YTD, history)
- [x] Groups (browse, search, filter, request to join)
- [x] Events (browse, filter, register)
- [x] Watch (sermons, categories, search)
- [x] Sermon Detail (YouTube player, auto-save notes, templates)
- [x] Merch (products, cart, 3 pickup locations, checkout)
- [x] Cafe (menu, cart, 3 pickup locations, checkout)
- [x] Kids Check-in (children list, check-in, pickup codes, QR)
- [x] Next Steps (membership journey, courses, progress)
- [x] Prayer (my requests + community, submit form)
- [x] Volunteer (opportunities, ministry filter, sign up)
- [x] Profile (multi-tab, giving, groups, comms)
- [x] More (navigation hub)

### Admin Dashboard (11 screens)
- [x] Dashboard (stats, monthly goal, activity feed)
- [x] Members (searchable, profile detail)
- [x] Kids Check-in (checkout with pickup code verification)
- [x] Media (sermon CRUD, upload, publish toggle)
- [x] Events (CRUD with create form)
- [x] Groups (CRUD with create form)
- [x] Giving (MTD/YTD stats, goal progress, donations)
- [x] Announcements (CRUD, priority, push toggle)
- [x] Attendance (weekly trend chart, summary)
- [x] Settings (church info, geofencing, service times)
- [x] Admin More (navigation, sign out)

### Backend Features
- [x] All CRUD endpoints for events, groups, announcements, media, kids, volunteer
- [x] Bidirectional kids check-in (parent check-in, admin checkout with pickup code)
- [x] Giving nudges (context-aware suggested amounts)
- [x] Geofence configuration
- [x] Attendance streak tracking
- [x] Service mode detection
- [x] Health/launch-check endpoint
- [x] Modular route files (volunteer, geofence, announcements, prayer, media)

## Bugs Fixed (Mar 15, 2026)

### P0: Login 9-second delay (ROOT CAUSE of "can't sign in")
- `ensure_mobile_demo_accounts()` was running 38 DB operations on EVERY login call
- Removed from login endpoint — now runs only at server startup
- Login time: 9+ seconds → 0.15 seconds (60x faster)

### P0: CORS / credentials: 'include' incompatibility
- Kubernetes/Cloudflare proxy rewrites `Access-Control-Allow-Origin` to `*`
- `credentials: 'include'` + wildcard origin = browser blocks response
- Fix: Removed `credentials: 'include'` from all 142 frontend source files
- Added global fetch interceptor in index.js to auto-inject Bearer tokens
- Backend CORS updated to `allow_origin_regex=r".*"`

### P1: Cookie-only auth endpoints
- 21 backend endpoints only read `request.cookies.get("session_token")`
- Fixed: All now use `get_session_token_from_request()` which supports both cookies and Bearer tokens
- Critical for mobile app compatibility

### P1: authFetch.js wrong API URL
- Was using `process.env.REACT_APP_BACKEND_URL` (missing `/api` prefix)
- Fixed to `process.env.REACT_APP_BACKEND_URL + '/api'`

### Service Worker Cache Issues
- Old SW v1 used stale-while-revalidate for static assets → served old cached JS
- New SW v4: no static caching, push notifications only
- index.html clears old SWs on every page load
- Added /api/clear-site-data endpoint with Clear-Site-Data HTTP header
- Added /test-login.html diagnostic page (standalone, no React)
- Added /clear.html cache-clearing page

## 3rd Party Integrations
- Stripe (Payments)
- Resend (Email)
- Emergent-managed Google Auth
- Anthropic Claude (AI Chat)
- OpenAI Whisper (Transcription)
- pywebpush (Web Push Notifications)
- chart.js / react-chartjs-2 (Dashboard Graphs)

## Remaining Tasks

### P1 - Next Priority
- [ ] Deploy fixes to production (samsonaitest.xyz) — user needs to "Save to Github" and redeploy
- [ ] Update mobile app API URL to point to correct deployment
- [ ] Full QA sweep across all 6 accounts on production
- [ ] Giving reports with CSV export (frontend wiring)

### P2 - Future
- [ ] Geofencing with expo-location (device-only)
- [ ] Giving nudge multi-step checkout in Merch/Cafe
- [ ] Push notifications end-to-end testing
- [ ] Deep linking for push notifications
- [ ] Year-end tax statements (PDF generation)
- [ ] Backend refactor: extract remaining routes from server.py
- [ ] Global CSS refactor: break App.css into component files

## Key Files
- `/app/frontend/src/index.js` — Global fetch interceptor (lines 6-23)
- `/app/frontend/src/pages/LoginPage.jsx` — Login form
- `/app/frontend/src/components/ProtectedRoute.jsx` — Auth guard
- `/app/frontend/src/components/layout/PortalLayout.jsx` — Member portal layout
- `/app/frontend/src/components/layout/AppShell.jsx` — Admin layout
- `/app/frontend/public/index.html` — SW clearing script
- `/app/frontend/public/test-login.html` — Standalone diagnostic login
- `/app/frontend/public/sw.js` — Service worker v4 (push only)
- `/app/backend/server.py` — Main backend (CORS, auth, all endpoints)
