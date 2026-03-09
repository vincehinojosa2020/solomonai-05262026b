# Solomon AI - Enterprise Church Management SaaS Platform
## Product Requirements Document

### Overview
**Product Name:** Solomon AI  
**Target Scale:** 50,000+ members per tenant, 1M+ concurrent users platform-wide  
**Demo URL:** https://abundant-demo.preview.emergentagent.com  
**Architecture:** Multi-tenant SaaS with subdomain routing

---

## Multi-Tenant Architecture

### Tenant Structure
Each church is a tenant with isolated data:
- **Subdomain routing**: `abundant.solomon.ai`, `cristoviene.solomon.ai`, etc.
- **Dedicated data**: Members, donations, groups, events, videos per tenant
- **Subscription management**: Active, suspended, cancelled states

### Demo Churches
| Church | Subdomain | City |
|--------|-----------|------|
| Abundant Church | abundant | El Paso, TX |
| Cristo Viene | cristoviene | El Paso, TX |
| The Potter's House | pottershouse | Dallas, TX |
| Eden X | edenx | Austin, TX |

### Role Hierarchy
1. **platform_admin** - Access all tenants, manage subscriptions (admin@solomon.ai)
2. **church_admin** - Full admin within their church (e.g., admin@abundant.church)
3. **member** - Portal access only (e.g., member@abundant.church)

---

## What's Implemented (February 27, 2026)

### P0: Pastor's CRM / Meeting Scheduler - ✅ COMPLETE
- **Admin Features** (`/meetings`):
  - Create meeting time slots (date, time, location)
  - View all meeting slots with OPEN/BOOKED status
  - View scheduled meetings with member info
  - Save meeting notes, record sessions, upload audio
  - **MOCKED**: Teams/Slack notifications return simulated responses
- **Member Features** (`/portal/meet`):
  - View available open time slots
  - Book meetings with topic and notes
  - View upcoming scheduled sessions

### P0: Merch Store (Admin + Member)
- Admin dashboard for merch: embed store URL, product catalog, orders summary
- Admin can add/edit/delete merch products (mugs, shirts, YETI, etc.)
- Member portal merch experience with embedded storefront + curated product grid
- Cart and checkout flow for demo ordering (**CHECKOUT IS MOCKED**)

### P0: Abundant Cafe (Admin + Member)
- Admin manages cafe pickup window + menu CRUD + order feed
- Members order coffee with pickup time selection inside portal
- Cafe order placement is demo-only (**PAYMENT IS MOCKED**)

### P0: Leave a Note (Member + Admin)
- Members submit subject + optional category + message on Portal Home
- Church and platform admins review notes in the /notes dashboard

### P0: Ask Solomon Upgrade - UI POLISHED
- Updated Solomon prompt to cover giving, groups, events, Watch, Thinkific, Abundant Pathways, Merch, Cafe
- Portal Home “Open” button launches the Ask Solomon chat
- Added voice input mic (browser Web Speech API) for members + admins

### P0: Media Library Sync Bug - FIXED
- Removed hardcoded `ALL_CONTENT` array from `PortalWatch.jsx`
- Watch page now exclusively fetches from `/api/portal/media/videos`
- Videos deleted by church admin no longer appear on member portal

### Bidirectional Communication Features - NEW

#### Member Side (/portal)
- **Groups Page**: View available groups, request to join, leave group
- **Events Page**: View upcoming events, register, cancel registration

#### Admin Side (/admin)
- **Group Member Management**: View members, search & add people, remove members
- **Event Registration Management**: View registrations, add manual registrations, remove registrations

### Existing Features (Still Working)
- **Authentication**: JWT-based with email/password, Google OAuth
- **Media Library Manager**: Full CRUD for YouTube videos
- **Groups Manager**: Create/edit/delete groups, open/close for joining
- **Events Manager**: Create/edit/delete events, manage registrations
- **Giving**: Live Stripe integration for donations
- **Solomon AI Chat**: Claude-powered assistant (Ask Solomon button)
- **Platform Dashboard**: Real aggregated statistics

---

## Technical Stack
- **Frontend:** React 18, React Router, TailwindCSS, shadcn/ui, Framer Motion
- **Backend:** FastAPI, Motor (async MongoDB)
- **Database:** MongoDB
- **AI:** Claude Sonnet 4.5 via emergentintegrations
- **Auth:** Email/Password (SHA256) + Google OAuth + JWT sessions
- **Payments:** Stripe (Live keys)
- **Email:** Resend (Welcome emails)

---

## Key API Endpoints

### Authentication
- `POST /api/auth/login` - Email/password login
- `POST /api/auth/register` - New member registration
- `POST /api/auth/logout` - Clear session
- `GET /api/auth/me` - Get current user

### Media (Church Admin)
- `GET /api/admin/media/videos` - List videos
- `POST /api/admin/media/videos` - Add video
- `PUT /api/admin/media/videos/{id}` - Update video
- `DELETE /api/admin/media/videos/{id}` - Delete video

### Media (Member Portal)
- `GET /api/portal/media/videos` - Get published videos

### LMS (Admin)
- `GET /api/admin/thinkific` - Get Thinkific URL
- `PATCH /api/admin/thinkific` - Update Thinkific URL
- `GET /api/admin/pathways/courses` - List Pathways courses
- `POST /api/admin/pathways/courses` - Create course
- `PUT /api/admin/pathways/courses/{id}` - Update course
- `DELETE /api/admin/pathways/courses/{id}` - Delete course
- `POST /api/admin/pathways/courses/{id}/lessons` - Add lesson
- `POST /api/admin/pathways/courses/{id}/assignments` - Assign members

### LMS (Member)
- `GET /api/portal/thinkific` - Member Thinkific URL
- `GET /api/portal/pathways/courses` - Assigned courses
- `GET /api/portal/pathways/courses/{id}/lessons` - Course lessons
- `POST /api/portal/pathways/progress` - Update lesson progress

### Merch (Admin)
- `GET /api/admin/merch/settings` - Merch embed URL
- `PATCH /api/admin/merch/settings` - Update embed URL
- `GET /api/admin/merch/products` - List products
- `POST /api/admin/merch/products` - Create product
- `PUT /api/admin/merch/products/{id}` - Update product
- `DELETE /api/admin/merch/products/{id}` - Delete product
- `GET /api/admin/merch/orders` - Recent orders
- `GET /api/admin/merch/summary` - Stats summary

### Cafe (Admin)
- `GET /api/admin/cafe/settings` - Cafe pickup window
- `PATCH /api/admin/cafe/settings` - Update pickup window
- `GET /api/admin/cafe/items` - List menu items
- `POST /api/admin/cafe/items` - Create menu item
- `PUT /api/admin/cafe/items/{id}` - Update menu item
- `DELETE /api/admin/cafe/items/{id}` - Delete menu item
- `GET /api/admin/cafe/orders` - Recent cafe orders
- `GET /api/admin/cafe/summary` - Cafe stats summary

### Cafe (Member)
- `GET /api/portal/cafe/settings` - Pickup settings
- `GET /api/portal/cafe/items` - Active menu items
- `POST /api/portal/cafe/orders` - Place cafe order (**MOCKED**)

### Merch (Member)
- `GET /api/portal/merch/settings` - Merch embed URL
- `GET /api/portal/merch/products` - Active products
- `POST /api/portal/merch/orders` - Place order (**MOCKED**)

### Leave a Note
- `POST /api/portal/notes` - Submit member note
- `GET /api/admin/notes` - Admin review notes

---

## Demo Test Credentials

### Platform Admin (God Mode)
- **Email:** admin@solomon.ai
- **Password:** Demo2026!

### Church Admins
- admin@abundant.church / Demo2026!
- admin@cristoviene.church / Demo2026!
- admin@pottershouse.church / Demo2026!
- admin@edenx.church / Demo2026!

### Members
- member@abundant.church / Demo2026!
- member@cristoviene.church / Demo2026!
- kaylen@edenx.church / Demo2026!

---

## Backlog (Priority Order)

### P1 - Next Priority
- [ ] Saved payment methods for members (frontend wiring)
- [ ] Giving reports with CSV export (frontend wiring)
- [ ] Year-end tax statements (PDF generation)

### P2 - Medium Priority
- [ ] Audit logging for critical actions
- [ ] Backend refactor: Break up server.py into modules
- [ ] Notification system for group/event updates

### P3 - Future (API Keys Required)
- [ ] AI Sermon Transcription
- [ ] AI Sermon Summaries
- [ ] Engagement Scoring
- [ ] SMS notifications (Twilio)

---

## Changelog

### Feb 27, 2026 (Latest Session)
- ✅ Pastor's CRM / Meeting Scheduler complete (Admin + Member)
- ✅ Abundant Pathways populated with 8 courses
- ✅ Solomon Chat voice input UI polished (circular mic button, pulsing animation)
- ✅ All features tested (100% pass rate - 12/12 backend tests)
- ✅ Whisper transcription + Claude summarization for meeting recordings
  - Uses emergentintegrations library for OpenAI Whisper (whisper-1 model)
  - Claude Sonnet 4.5 generates pastoral meeting summaries with action items
  - Summary includes: Key Discussion Points, Spiritual Needs, Action Items, Next Steps, Prayer Points
- ✅ **AGENT-READY API PLATFORM** (100% - 24/24 tests passed)
  - API Key Management: Admins generate keys with scoped permissions
  - Agent Endpoints (/api/v1/agent/*):
    - `/scout` - Handshake, verify connection
    - `/visitors` - New members in manifest schema for outreach
    - `/members` - Member directory with search
    - `/events` - Upcoming events with registration counts
    - `/groups` - Groups with member counts
    - `/meetings` - Pastoral meetings
    - `/giving/summary` - Aggregate stats (READ-ONLY - no amounts)
    - `/notes` - Leadership notes
    - `/webhooks` - Webhook registration for real-time events
    - `/docs` - Public API documentation
  - Circuit Breaker: Anomaly detection for bulk operations
  - External agents (MoltBot/OpenClaw) can now connect to Solomon AI!
- MOCKED: Teams/Slack notifications return simulated responses

### Feb 26, 2026
- Added Thinkific integration + Abundant Pathways LMS flows
- Built merch admin dashboard + member merch experience
- Added merch embed + demo catalog + order placement (mocked)
- Added Abundant Cafe admin + member ordering experience (orders mocked)
- Added Leave a Note (member submission + admin review)
- Expanded Ask Solomon coverage (Watch, Pathways, Thinkific, Merch, Cafe)
- Added voice mic input for Ask Solomon (members + admins)
- Polished Portal Home layout for card symmetry + nav spacing

### Feb 24, 2026
- Redesigned Login Page to minimalist Prada-style aesthetic
- Added Eden X tenant + updated demo credentials
- Enabled Ask Solomon AI chat assistant
