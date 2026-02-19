# Samson - Enterprise Church Management SaaS Platform
## Product Requirements Document

### Overview
**Product Name:** SAMSON (Solomon AI)  
**Tagline:** "Enterprise Church Management System"  
**Demo Tenant:** Abundant Church (El Paso, TX)  
**Target Scale:** 50,000+ members per tenant  
**Demo URL:** https://abundant-media.preview.emergentagent.com

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
Dashboard stats scaled to 50,000-member mega-church (NOTE: Currently hardcoded demo values)

### ✅ BUILD 3: Member Portal (COMPLETED)
6-page member-facing portal (Church Center equivalent):

1. **Portal Home** (`/portal`)
   - Welcome banner with greeting + date
   - Quick actions: Give Now, My Groups, Upcoming Events
   - Upcoming events list
   - Solomon AI widget with personalized message

2. **Portal Watch** (`/portal/library`) - ✅ **PREMIUM LUXURY MEDIA EXPERIENCE**
   - **Consolidated from separate Watch + Library pages into ONE unified experience**
   - **Premium Prada/Eden-X.io inspired luxury design**
   - Sora font family for refined typography
   - Cinematic hero section with auto-rotating featured content
   - Gold accent colors + elegant category pills
   - **4-column premium card grid** with glassmorphism hover effects
   - Micro-animations throughout (Framer Motion)
   - Search bar with focus effects
   - **12 REAL Abundant Church YouTube videos**:
     - "Community With a Purpose" - Pastor Charles Nieman
     - "Blessing & Healing Through Humility" - Pastor Charles Nieman
     - "Building Your Life" - Pastor Charles Nieman
     - "The Missing Peace" - Pastor Charles Nieman
     - And more...
   - **Video Player Modal**: Cinema-style overlay with YouTube embed, "NOW PLAYING" label, autoplay
   - Category filtering (All, Faith, Family, Leadership, Worship, Growth, Community)
   - Premium badges: "NEW" (burgundy), "POPULAR" (gold), "FEATURED" (white)

3. **Portal Give** (`/portal/give`)
   - Amount input with quick amounts ($25, $50, $100, $250)
   - Fund selector (General, Building, Missions, etc.)
   - Frequency options
   - Payment methods

4. **Portal Groups** (`/portal/groups`)
   - My Groups section
   - Discover Groups with search/filter

5. **Portal Events** (`/portal/events`)
   - Filter tabs (All, This Week, This Month)
   - Event cards with registration

6. **Portal Me** (`/portal/me`)
   - Profile with giving/groups tabs

### ✅ Solomon AI Analyst
- Floating "Ask Solomon" button
- Claude Sonnet 4.5 powered AI chat

### ✅ Admin Dashboard
- Full SAMSON admin dashboard (stats hardcoded for demo)

---

## Technical Stack

- **Frontend:** React 18, React Router, TailwindCSS, shadcn/ui, Framer Motion
- **Backend:** FastAPI, Motor (async MongoDB)
- **Database:** MongoDB
- **AI:** Claude Sonnet 4.5 via emergentintegrations
- **Auth:** Email/Password (SHA256) + Google OAuth + JWT sessions
- **Payments:** Stripe

---

## Recent Changes (Feb 19, 2026)

### Media Experience Consolidation
- **Removed**: Separate `/portal/watch` route (now redirects to `/portal/library`)
- **Removed**: "Library" nav item (replaced with unified "Watch" that goes to library)
- **Updated**: Navigation simplified to 6 items: Home | Watch | Give | Groups | Events | Me

### Premium Luxury Design Upgrade
- **New font**: Sora (luxury typography)
- **New color palette**: Rich black, gold accents, burgundy highlights
- **New effects**: Ambient light animation, grain texture, glassmorphism
- **Enhanced hover states**: Smooth scale animations, elegant play buttons
- **Refined spacing**: More generous padding and margins

---

## Known Issues / Technical Debt

1. **Dashboard Data**: Stats are HARDCODED demo values (not live MongoDB queries)
2. **Library Content**: Video data is HARDCODED in frontend (no API)
3. **Backend Monolith**: server.py needs refactoring into /routes, /models structure

---

## Backlog (Priority Order)

### P1 - High Priority
- [ ] Create zero-data demo account
- [ ] Fix dashboard with real MongoDB queries + indexes
- [ ] Design system: Add JetBrains Mono for data values

### P2 - Medium Priority
- [ ] Giving Module: "Record Gift" side panel
- [ ] Missing Modules: Workflows, Check-In, Services
- [ ] Communications: AI writer + rich text editor
- [ ] Global Search (⌘K command palette)

### P3 - Lower Priority
- [ ] Backend refactor: Break up server.py
- [ ] Create API endpoints for sermon content
- [ ] Standalone seed script (replace /api/seed endpoint)

---

## Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@abundant.org | Demo2026! |
| Member | member@abundant.org | Demo2026! |

---

## File Reference

### Core Files
- `/app/frontend/src/pages/portal/PortalLibrary.jsx` - Premium media experience
- `/app/frontend/src/library.css` - Luxury styling (Sora font, gold accents)
- `/app/frontend/src/components/layout/PortalLayout.jsx` - Portal navigation
- `/app/frontend/src/App.js` - Route configuration
- `/app/backend/server.py` - FastAPI backend (monolithic)

### CSS Architecture
- `App.css` - Core app styles + portal styles
- `library.css` - Premium media page styles
- `index.css` - Base Tailwind + custom utilities
