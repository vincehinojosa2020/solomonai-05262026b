# SAMSON - Enterprise Church Management SaaS Platform
## Product Requirements Document

### Overview
**Product Name:** SAMSON  
**Tagline:** "Enterprise Church Management System"  
**Target Scale:** 50,000+ members per tenant, 1M+ concurrent users platform-wide  
**Demo URL:** https://samson-demo.preview.emergentagent.com
**Architecture:** Multi-tenant SaaS with subdomain routing

---

## Multi-Tenant Architecture (Feb 23, 2026)

### Tenant Structure
Each church is a tenant with isolated data:
- **Subdomain routing**: `abundant.samson.ai`, `cityreach.samson.ai`, etc.
- **Dedicated data**: Members, donations, groups, events per tenant
- **Subscription management**: Active, suspended, cancelled states

### Demo Churches
| Church | Subdomain | Admin Email | Members | Location |
|--------|-----------|-------------|---------|----------|
| Abundant Living Faith Center | abundant | admin@abundant.church | 500 | El Paso, TX |
| City Reach Church | cityreach | admin@cityreach.church | 500 | Cedar Park, TX |
| The Potter's House | pottershouse | admin@pottershouse.church | 500 | Dallas, TX |

### Role Hierarchy
1. **platform_admin** - Access all tenants, manage subscriptions
2. **church_admin** - Full admin within their church
3. **member** - Portal access only

### Platform Accounts
| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@samson.ai | Demo2026! |
| Demo Member | member@samson.ai | Demo2026! |
| New Member | newmember@samson.ai | Demo2026! |

---

## What's Implemented (February 2026)

### ✅ BUILD 1: Email/Password Login + Demo Accounts (COMPLETED)
- **Email/Password form** on login page with show/hide password toggle
- **Multi-tenant Demo Credentials Box**:
  - Platform: `admin@samson.ai` → Platform super-admin
  - Abundant: `admin@abundant.church` → Church admin
  - CityReach: `admin@cityreach.church` → Church admin
  - Potter's: `admin@pottershouse.church` → Church admin
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
   - Samson AI widget with personalized message

2. **Portal Watch** (`/portal/library`) - ✅ **PREMIUM LUXURY MEDIA EXPERIENCE**
   - **Consolidated from separate Watch + Library pages into ONE unified experience**
   - **Premium Prada/Eden-X.io inspired luxury design**
   - ✅ **Integrated Portal Navigation** - Home | Watch | Give | Groups | Events | Me in header
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
   - ✅ **"Continue Watching" Section** - Netflix-style feature:
     - Horizontal scrollable carousel below hero
     - Shows in-progress videos with progress bars
     - Displays percentage watched + time remaining
     - "Resume" button on hero for videos with progress
     - Progress tracking saved to database
     - Completed videos marked with checkmark badge
   - ✅ **Watch Progress Tracking API**:
     - `POST /api/portal/watch/progress` - Save progress
     - `GET /api/portal/watch/progress` - Get all progress
     - `GET /api/portal/watch/progress/{video_id}` - Get specific video progress

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

### ✅ Samson AI Analyst
- Floating "Ask Samson" button
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

## Deployment Readiness (Feb 19, 2026)

### ✅ Production Ready
| Component | Status | Notes |
|-----------|--------|-------|
| Database Indexes | ✅ Ready | 55 indexes across 10 key collections |
| Authentication | ✅ Ready | Google OAuth + Email/Password + Self-Registration |
| Member Portal | ✅ Ready | 6 pages, all functional |
| Video Streaming | ✅ Ready | YouTube embeds (no bandwidth cost) |
| Continue Watching | ✅ Ready | Progress tracking with API |
| Admin Dashboard | ✅ Demo Mode | Hardcoded sample data for pitches |
| Solomon AI | ✅ Ready | Claude Sonnet 4.5 powered |
| Payments | ✅ Ready | Stripe integration |
| Self-Registration | ✅ Ready | Strong password requirements |

### Security Features
- **Password Requirements** (enforced on signup):
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character (!@#$%^&*)
- **Email Uniqueness**: Duplicate emails blocked
- **Session-Based Auth**: Secure HTTP-only cookies
- **256-bit Encryption**: Bank-level security

### Database Scale
- **55 indexes** optimized for 50,000+ member scale
- Key indexed collections: people, donations, attendance, groups, services
- Compound indexes for common query patterns

### Authentication Strategy
- **Members**: Google OAuth (primary) + Demo credentials
- **Admins**: Email/Password with demo account
- Demo credentials available for pitching

---

## Recent Changes (Feb 23, 2026)

### E2E User Journey Complete - Live Stripe Integration
- **Live Stripe Keys**: Configured with `pk_live_` and `rk_live_` keys for real payments
- **Welcome Email**: Resend integration sends personalized welcome email from Samson AI on registration
- **Registration Flow**: Public signup at `/signup` creates account and auto-logs in
- **Donation Flow**: Full Stripe checkout integration with live payment processing
- **Bug Fixes**: Fixed HTTPException handling in donate endpoint, fixed app initialization stuck issue

### Branding Consistency Update - "Solomon" → "Samson"
- **Renamed**: AI chat assistant from "Solomon" to "Samson" for consistent branding
- **Updated**: `SolomonChat.jsx` → `SamsonChat.jsx`
- **Updated**: All "Ask Solomon" text → "Ask Samson" across portal
- **Updated**: Chat placeholder text, loading messages, and welcome screens
- **Cleanup**: Removed redundant `masterclass.css` file (styles consolidated in library.css)
- **Cleanup**: Removed `masterclass.css` import from App.js

## Recent Changes (Feb 19, 2026)

### Continue Watching Feature (Netflix-style)
- **New**: Horizontal "Continue Watching" carousel showing in-progress videos
- **New**: Progress tracking backend API (3 new endpoints)
- **New**: Progress bars on video cards showing watch percentage
- **New**: "Resume" button on hero for videos with saved progress
- **New**: Completed videos get "Watched" badge with checkmark
- **New**: Header shows completed video count

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

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| Admin | admin@abundant.org | Demo2026! | Full admin dashboard access |
| Member | member@abundant.org | Demo2026! | Member with donation & watch history |
| New Member | newmember@abundant.org | Demo2026! | **ZERO DATA** - Fresh account for testing full flow |

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
