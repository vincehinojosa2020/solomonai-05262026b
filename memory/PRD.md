# Solomon AI - Enterprise Church Management SaaS Platform
## Product Requirements Document

### Overview
**Product Name:** Solomon AI  
**Tagline:** "AI-Powered Church Management"  
**Target Scale:** 50,000+ members per tenant, 1M+ concurrent users platform-wide  
**Demo URL:** https://faith-ops-platform.preview.emergentagent.com
**Architecture:** Multi-tenant SaaS with subdomain routing

---

## Multi-Tenant Architecture

### Tenant Structure
Each church is a tenant with isolated data:
- **Subdomain routing**: `abundant.solomon.ai`, `cityreach.solomon.ai`, etc.
- **Dedicated data**: Members, donations, groups, events, videos per tenant
- **Subscription management**: Active, suspended, cancelled states

### Demo Churches
| Church | Subdomain | Admin Email |
|--------|-----------|-------------|
| Abundant Living Faith Center | abundant | admin@abundant.church |
| City Reach Church | cityreach | admin@cityreach.church |
| The Potter's House | pottershouse | admin@pottershouse.church |

### Role Hierarchy
1. **platform_admin** - Access all tenants, manage subscriptions
2. **church_admin** - Full admin within their church (including Media, Groups, Events)
3. **member** - Portal access only (watch videos, join groups, register for events)

---

## What's Implemented (February 24, 2026)

### ✅ Church Admin Features

**Media Library Manager** (`/media`)
- Add YouTube videos via URL (auto-extracts ID and thumbnail)
- Edit/Delete/Feature videos
- Publish/Unpublish controls
- Category filtering (Faith, Family, Leadership, Worship, Growth, Community)
- Grid and List view options
- Synced to member portal - changes reflect immediately

**Groups & Bible Studies Manager** (`/admin/groups`)
- Create/Edit/Delete groups
- Group types: Small Group, Bible Study, Prayer Group, Youth, Men's, Women's, Couples, Ministry Team
- Set meeting day/time, location, capacity
- Open/Close for new members
- View member roster

**Events & Services Manager** (`/admin/events`)
- Create/Edit/Delete events
- Set date, time, location, capacity
- Enable/disable registration
- Track registration counts
- View registrations

### ✅ Member Portal Features

**Watch Page** (`/portal/library`)
- Dynamically fetches videos from database (managed by church admin)
- Netflix-style hero carousel with featured videos
- Category filtering
- Search functionality
- Church-branded (shows church name)

**Groups Page** (`/portal/groups`)
- View available groups
- **Join Group** functionality - members can join open groups
- Shows "My Groups" vs "Discover Groups"

**Events Page** (`/portal/events`)
- View upcoming events
- **Register for Event** functionality
- **Cancel Registration** option
- Filter by time period

**Giving** (`/portal/give`)
- Live Stripe integration
- Amount presets and custom amounts

### ✅ Platform Admin (God Mode)

**Platform Dashboard** (`/platform`)
- Real stats from database (not hardcoded)
- Tabs: Churches | All Members
- Searchable member directory
- Church management (view, activate/suspend)
- **No Media Library link** (correctly scoped to church admins only)

---

## Technical Stack

- **Frontend:** React 18, React Router, TailwindCSS, shadcn/ui, Framer Motion
- **Backend:** FastAPI, Motor (async MongoDB)
- **Database:** MongoDB
- **AI:** Claude Sonnet 4.5 via emergentintegrations
- **Auth:** Email/Password (bcrypt) + Google OAuth + JWT sessions
- **Payments:** Stripe (Live keys)
- **Email:** Resend

---

## Key API Endpoints

### Media (Church Admin)
- `GET /api/admin/media/videos` - List videos with search/filter
- `POST /api/admin/media/videos` - Add video from YouTube URL
- `PUT /api/admin/media/videos/{id}` - Update video
- `DELETE /api/admin/media/videos/{id}` - Delete video
- `POST /api/admin/media/videos/{id}/feature` - Toggle featured

### Media (Portal)
- `GET /api/portal/media/videos` - Get published videos for member
- `GET /api/portal/media/featured` - Get featured hero video

### Groups (Admin)
- `GET /api/admin/groups` - List groups
- `POST /api/admin/groups` - Create group
- `PUT /api/admin/groups/{id}` - Update group
- `DELETE /api/admin/groups/{id}` - Delete group
- `GET /api/admin/groups/{id}/members` - View members

### Groups (Portal)
- `POST /api/portal/groups/{id}/join` - Join a group

### Events (Admin)
- `GET /api/admin/events` - List events
- `POST /api/admin/events` - Create event
- `PUT /api/admin/events/{id}` - Update event
- `DELETE /api/admin/events/{id}` - Delete event

### Events (Portal)
- `POST /api/portal/events/{id}/register` - Register for event
- `DELETE /api/portal/events/{id}/register` - Cancel registration

---

## Demo Test Credentials

### Platform Admin (God Mode)
- **Email:** admin@solomon.ai
- **Password:** Demo2026!
- **Access:** All churches, member directory, stats
- **Does NOT see:** Media Library (correctly scoped)

### Church Admins
- admin@abundant.church / Demo2026!
- admin@cityreach.church / Demo2026!
- admin@pottershouse.church / Demo2026!
- **See:** Media Library, Groups Manager, Events Manager

### Members
- member@abundant.church (Maria Gonzalez) / Demo2026!
- member@cityreach.church (John Smith) / Demo2026!
- **See:** Watch, Give, Groups, Events, Me

---

## Backlog (Priority Order)

### P0 - Completed This Session
- [x] Media Library Manager (church admin)
- [x] Portal Watch connected to database
- [x] Groups Manager (church admin)
- [x] Events Manager (church admin)
- [x] Member can join groups
- [x] Member can register for events
- [x] Correct scoping (platform admin doesn't see Media Library)

### P1 - Next Priority
- [ ] Seed demo events via admin API
- [ ] Saved payment methods for members
- [ ] Giving reports with CSV export

### P2 - Medium Priority
- [ ] Audit logging for critical actions
- [ ] Year-end tax statements (PDF)
- [ ] Backend refactor: Break up server.py

### P3 - Future
- [ ] AI Sermon Transcription (tabled)
- [ ] AI Sermon Summaries (tabled)
- [ ] Engagement Scoring (tabled)

---

## Changelog

### Feb 24, 2026 (Latest)
- Built Media Library Manager for church admins
- Built Groups & Bible Studies Manager
- Built Events & Services Manager
- Connected portal Watch page to database (dynamic content)
- Added join group API for members
- Added event registration API for members
- Correctly scoped Media Library to church admins only
- Platform admin no longer sees Media Library link
