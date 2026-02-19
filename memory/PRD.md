# Samson - Enterprise Church Management SaaS Platform
## Product Requirements Document

### Overview
**Product Name:** SAMSON (Solomon AI)  
**Tagline:** "Enterprise Church Management System"  
**Demo Tenant:** Abundant Church (El Paso, TX)  
**Target Scale:** 50,000+ members per tenant  
**Demo URL:** https://sermon-cinema.preview.emergentagent.com

---

## What's Implemented (February 2026)

### ✅ BUILD 1: Email/Password Login + Demo Accounts (COMPLETED)
- **Email/Password form** on login page with show/hide password toggle
- **Demo Credentials Box** with copy buttons:
  - Admin: `admin@abundant.org / Demo2026!` → routes to `/dashboard`
  - Member: `member@abundant.org / Demo2026!` → routes to `/portal`
- **Google OAuth** still available as alternative login
- **Role-based routing**: admin → /dashboard, member → /portal

### ✅ BUILD 2: Mega-Church Seed Data (COMPLETED)
Dashboard stats scaled to 50,000-member mega-church:
- **TOTAL MEMBERS**: 50,247 (+127 this month)
- **ACTIVE GROUPS**: 284 (18 open for new members)
- **LAST SUNDAY**: 8,420 (+340 vs prior)
- **MTD GIVING**: $847,250 (24% of $3.5M goal)
- **YTD GIVING**: $2,847,303 (+12% vs LY)
- **RECURRING**: 847 active schedules

Church Info Updated:
- Address: 1556 George Dieter Dr, El Paso, TX 79936
- Website: https://www.abundant.org
- Timezone: America/Denver

### ✅ BUILD 3: Member Portal (COMPLETED)
6-page member-facing portal (Church Center equivalent):

1. **Portal Home** (`/portal`)
   - Welcome banner with greeting + date
   - Quick actions: Give Now, My Groups, Upcoming Events
   - Upcoming events list
   - Solomon AI widget with personalized message

2. **Portal Watch / Abundant TV** (`/portal/watch`) - ✅ **MASTERCLASS REDESIGN + VIDEO PLAYER**
   - **Cinematic dark mode** premium streaming experience
   - Full-bleed hero with auto-rotating featured content (3 items, 8-sec interval)
   - Instructor avatars, lesson counts, duration metadata
   - Sticky category filter bar (All Classes, Faith, Worship, Prayer, etc.)
   - Search toggle with animated search bar
   - **4 horizontal carousels**: Popular Classes, Trending, New Releases, Deep Dives
   - **Course cards** with hover play overlay, duration badges, instructor info
   - **Instructor Spotlight** section with stats (12 Classes, 156 Lessons, 40h+)
   - Footer CTA: "Every Lesson. Every Teacher. All Access."
   - Typography: Playfair Display (titles) + DM Sans (body)
   - Framer Motion animations throughout
   - ✅ **Video Player Modal** - Cinema-style fullscreen player with YouTube embeds
   - ✅ **Playlist Sidebar** - Shows all lessons with active state highlighting

3. **Portal Give** (`/portal/give`)
   - Amount input with quick amounts ($25, $50, $100, $250)
   - Fund selector (General, Building, Missions, etc.)
   - Frequency (One-time, Weekly, Monthly, etc.)
   - Payment methods (Card/ACH, PayPal, Venmo, Zelle)
   - YTD giving summary + giving history

4. **Portal Groups** (`/portal/groups`)
   - My Groups section
   - Discover Groups with search/filter
   - Request to Join / Get Notified buttons

5. **Portal Events** (`/portal/events`)
   - Filter tabs (All, This Week, This Month, Registered)
   - Event cards with date, location, registration
   - Registration functionality

6. **Portal Me** (`/portal/me`)
   - Profile header with avatar
   - Tabs: Overview, My Giving, My Groups, Communications
   - Email preferences toggles

### ✅ Solomon AI Analyst (Previously Completed)
- Floating "Ask Solomon" button
- Claude Sonnet 4.5 powered AI chat
- Church data context (members, giving, groups)
- Conversation history in MongoDB

### ✅ Admin Features
- Full SAMSON admin dashboard
- "Preview Member Portal" link in header
- All existing modules (Members, Groups, Events, Giving, Communications, Reports, Settings)

---

## Technical Stack

- **Frontend:** React 18, React Router, TailwindCSS, shadcn/ui
- **Backend:** FastAPI, Motor (async MongoDB)
- **Database:** MongoDB
- **AI:** Claude Sonnet 4.5 via emergentintegrations
- **Auth:** Email/Password (SHA256) + Google OAuth + JWT sessions
- **Payments:** Stripe

---

## API Endpoints

### Authentication
- `POST /api/auth/login` - Email/password login (returns role)
- `GET /api/auth/me` - Get current user (with role)
- `POST /api/auth/logout` - Logout

### Portal (Member)
- `GET /api/portal/me` - Member profile with groups/giving
- `GET /api/portal/giving/history` - Member's giving history
- `GET /api/portal/events` - Upcoming events
- `GET /api/portal/groups` - Available groups

### Dashboard (Admin)
- `GET /api/dashboard/stats` - Mega-church scale stats
- All other admin endpoints unchanged

---

## Demo Flow

1. Open `/login` → Show email/password form with demo credentials
2. Login as **admin@abundant.org** → See full admin dashboard with 50,247 members
3. Click "Ask Solomon" → AI-powered church analytics
4. Logout → Login as **member@abundant.org** → See member portal
5. Navigate Give, Groups, Events, Me pages

---

## Test Credentials

| Account | Email | Password | Role | Destination |
|---------|-------|----------|------|-------------|
| Admin | admin@abundant.org | Demo2026! | admin | /dashboard |
| Member | member@abundant.org | Demo2026! | member | /portal |

---

## Next Action Items

### P0 - Immediate
- [ ] Create Zero-Data Demo Account (second demo tenant with empty data)

### P1 - Design & Polish
- [ ] UPGRADE 2: Design System Elevation (Sora/JetBrains Mono fonts)
- [ ] UPGRADE 6: Dashboard Intelligence - Fix hardcoded data with optimized DB queries
- [ ] UPGRADE 7: Micro-interactions (Framer Motion on dashboard)

### P2 - Feature Expansion
- [ ] UPGRADE 5: Giving Module - Record Gift panel
- [ ] UPGRADE 3: Missing Modules (Workflows, Check-In, Services)
- [ ] UPGRADE 10: Communications - AI writer
- [ ] UPGRADE 8: Global Search (⌘K)
- [ ] Backend Refactor: Break server.py into modular routes/models/services

---

## Code Architecture

```
/app/
├── backend/
│   ├── server.py       # All routes including auth + portal
│   └── tests/          # pytest test files
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx       # Email/password + demo creds
│   │   │   └── portal/             # Member portal pages
│   │   │       ├── PortalHome.jsx
│   │   │       ├── PortalGive.jsx
│   │   │       ├── PortalGroups.jsx
│   │   │       ├── PortalEvents.jsx
│   │   │       ├── PortalMe.jsx
│   │   │       └── PortalWatch.jsx # ✅ MasterClass-style Abundant TV
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppShell.jsx    # Admin layout
│   │   │   │   └── PortalLayout.jsx # Member portal layout (dark mode on Watch)
│   │   │   ├── ProtectedRoute.jsx  # Role-based routing
│   │   │   └── SolomonChat.jsx     # AI chat widget
│   │   ├── App.js                  # Routes
│   │   ├── App.css                 # Main styles + portal dark mode
│   │   └── masterclass.css         # ✅ MasterClass premium dark theme
└── memory/
    └── PRD.md
```
