# Solomon AI - Enterprise Church Management SaaS Platform
## Product Requirements Document

### Overview
**Product Name:** Solomon AI  
**Tagline:** "AI-Powered Church Management"  
**Target Scale:** 50,000+ members per tenant, 1M+ concurrent users platform-wide  
**Demo URL:** https://samson-staging-1.preview.emergentagent.com
**Architecture:** Multi-tenant SaaS with subdomain routing

---

## Multi-Tenant Architecture (Feb 24, 2026)

### Tenant Structure
Each church is a tenant with isolated data:
- **Subdomain routing**: `abundant.solomon.ai`, `cityreach.solomon.ai`, etc.
- **Dedicated data**: Members, donations, groups, events per tenant
- **Subscription management**: Active, suspended, cancelled states

### Demo Churches
| Church | Subdomain | Admin Email | Members | Location |
|--------|-----------|-------------|---------|----------|
| Abundant Living Faith Center | abundant | admin@abundant.church | 500 | El Paso, TX |
| City Reach Church | cityreach | admin@cityreach.church | 500 | Cedar Park, TX |
| The Potter's House | pottershouse | admin@pottershouse.church | 500 | Dallas, TX |

### Role Hierarchy
1. **platform_admin** - Access all tenants, manage subscriptions, view member directory
2. **church_admin** - Full admin within their church
3. **member** - Portal access only

### Platform Accounts
| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@solomon.ai | Demo2026! |
| Demo Member | member@solomon.ai | Demo2026! |
| New Member | newmember@solomon.ai | Demo2026! |

---

## What's Implemented (February 24, 2026)

### ✅ Branding Update: "Solomon AI"
- Renamed from "Samson" to "Solomon AI" throughout the application
- Updated logo, email templates, API responses
- All demo accounts now use `@solomon.ai` domain

### ✅ Platform Admin Dashboard (God Mode)
- **Real Stats**: Live aggregation from MongoDB (not hardcoded)
  - Total Churches count
  - Active Subscriptions count
  - Total Members count
  - Platform GMV (Month-to-date donations)
- **Tabs Interface**: Churches | All Members tabs
- **Member Directory**: Searchable list of all members across all churches
  - Name, Email, Church, Status, Join Date
  - Filterable and searchable
- **Church Management**: View, activate/suspend subscriptions
- **Drill-down**: Click any church to impersonate church admin

### ✅ Welcome Email System
- Resend integration sends personalized welcome emails
- Email includes church name dynamically
- Sent from "Solomon AI" with custom HTML template
- Triggered automatically on new user registration

### ✅ Member Portal (6 pages)
1. **Portal Home** (`/portal`)
   - Personalized greeting with Solomon AI widget
   - Quick actions: Give Now, My Groups, Upcoming Events
   
2. **Portal Watch** (`/portal/library`)
   - Premium luxury media experience
   - 12 real Abundant Church YouTube videos
   - Continue Watching (Netflix-style progress tracking)
   
3. **Portal Give** (`/portal/give`)
   - Live Stripe integration
   - Amount presets and custom amounts
   
4. **Portal Groups** (`/portal/groups`)
   - My Groups + Discover Groups
   
5. **Portal Events** (`/portal/events`)
   - Filter by time period
   
6. **Portal Me** (`/portal/me`)
   - Profile with giving/groups tabs

### ✅ Authentication
- Email/Password login with strong password requirements
- Google OAuth via Emergent
- JWT sessions with secure cookies
- Role-based routing (admin → dashboard, member → portal)

### ✅ Public Registration
- Church selector dropdown (fetches active tenants)
- Password strength validation
- Email availability check
- Auto-login after registration
- Welcome email sent automatically

---

## Technical Stack

- **Frontend:** React 18, React Router, TailwindCSS, shadcn/ui, Framer Motion
- **Backend:** FastAPI, Motor (async MongoDB)
- **Database:** MongoDB
- **AI:** Claude Sonnet 4.5 via emergentintegrations
- **Auth:** Email/Password (SHA256) + Google OAuth + JWT sessions
- **Payments:** Stripe (Live keys)
- **Email:** Resend

---

## API Endpoints

### Platform Admin
- `GET /api/platform/stats` - Real platform-wide statistics
- `GET /api/admin/members` - Member directory with search/filter
- `GET /api/tenants` - List all tenants
- `PATCH /api/tenants/{id}/subscription` - Update subscription status

### Authentication
- `POST /api/auth/login` - Email/password login
- `POST /api/auth/register` - New user registration (sends welcome email)
- `POST /api/auth/check-email` - Check email availability
- `GET /api/auth/me` - Get current user

### Portal
- `GET /api/portal/me` - Member profile with giving/groups
- `GET /api/portal/events` - Upcoming events
- `GET /api/portal/groups` - Available groups
- `POST /api/portal/watch/progress` - Save video progress

### Payments
- `POST /api/payments/donate` - Create Stripe checkout
- `GET /api/payments/status/{session_id}` - Check payment status

---

## Demo Test Credentials

### Platform Admin (God Mode)
- **Email:** admin@solomon.ai
- **Password:** Demo2026!
- **Access:** All churches, member directory, stats

### Church Admins
- admin@abundant.church / Demo2026!
- admin@cityreach.church / Demo2026!
- admin@pottershouse.church / Demo2026!

### Members
- member@abundant.church (Maria Gonzalez) / Demo2026!
- member@cityreach.church (John Smith) / Demo2026!

---

## Known Issues / Technical Debt

1. **Sidebar Logo**: Still shows "SAMSON" - needs CSS update
2. **Backend Monolith**: server.py needs refactoring into /routes, /models structure
3. **Preview URL**: Still named `samson-staging-1` (deployment artifact)

---

## Backlog (Priority Order)

### P0 - Immediate (User's Request)
- [x] Rename Samson → Solomon AI throughout
- [x] Fix mocked dashboard data with real aggregations
- [x] Build Admin Member Directory
- [x] Verify welcome email on signup

### P1 - High Priority
- [ ] Fix sidebar logo to show "SOLOMON"
- [ ] Audit logging for critical actions
- [ ] Year-end giving statements (PDF generation)

### P2 - Medium Priority
- [ ] Fund Management admin UI
- [ ] Giving reports (monthly summaries, CSV export)
- [ ] Group attendance tracking
- [ ] Missing Modules: Workflows, Check-In, Services
- [ ] Global Search (⌘K command palette)

### P3 - Lower Priority
- [ ] Backend refactor: Break up server.py
- [ ] AI Sermon Transcription (tabled per user request)
- [ ] AI Sermon Summaries (tabled per user request)
- [ ] Engagement Scoring (tabled per user request)

---

## File Reference

### Core Files
- `/app/backend/server.py` - FastAPI backend (monolithic)
- `/app/frontend/src/pages/PlatformDashboard.jsx` - God Mode UI with tabs
- `/app/frontend/src/pages/LoginPage.jsx` - Login with demo accounts
- `/app/frontend/src/pages/SignUpPage.jsx` - Registration with church selector
- `/app/frontend/src/components/SolomonChat.jsx` - AI chat widget

### CSS
- `/app/frontend/src/App.css` - Core styles including platform dashboard

---

## Changelog

### Feb 24, 2026
- Renamed "Samson" → "Solomon AI" throughout app
- Added real platform stats API (`/api/platform/stats`)
- Added member directory API (`/api/admin/members`)
- Updated Platform Dashboard with tabs (Churches | Members)
- Fixed welcome email to include church name dynamically
- Re-seeded database with `@solomon.ai` accounts
