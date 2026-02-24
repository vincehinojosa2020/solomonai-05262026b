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
1. **platform_admin** - Access all tenants, manage subscriptions (admin@solomon.ai)
2. **church_admin** - Full admin within their church (e.g., admin@abundant.church)
3. **member** - Portal access only (e.g., member@abundant.church)

---

## What's Implemented (February 24, 2026)

### P0: Media Library Sync Bug - FIXED
- Removed hardcoded `ALL_CONTENT` array from `PortalWatch.jsx`
- Watch page now exclusively fetches from `/api/portal/media/videos` endpoint
- Videos deleted by church admin no longer appear on member portal
- Proper loading and empty states implemented

### P1: Platform Admin UI - FIXED
- Clean UI for `admin@solomon.ai` without church-specific elements
- Sidebar shows "Solomon" as name (not full email)
- Role displays as "Platform Admin"
- Top bar greeting: "Good morning, Solomon"
- Tenant badge hidden (no "Abundant Living Faith Center")
- "Preview Member Portal" link hidden
- Limited navigation: All Churches, Settings, Integrations only
- Purple accent color for Platform section

### P1: Platform Admin Impersonation Flow - IMPROVED
- When impersonating a church, full Church Admin navigation appears
- Impersonation banner shows which church is being viewed
- "Back to All Churches" button to exit impersonation

### Bidirectional Communication Features - NEW

#### Member Side (/portal)
- **Groups Page**: View available groups, "Request to Join" for open groups, "Leave Group" option
- **Events Page**: View upcoming events, "Register" button, "Cancel Registration" option
- **My Groups API**: `/api/portal/my-groups` - Get member's joined groups
- **My Events API**: `/api/portal/my-events` - Get member's registered events

#### Admin Side (/admin)
- **Group Member Management**: View members, search & add people, remove members
- **Event Registration Management**: View registrations, add manual registrations, remove registrations
- **New APIs**:
  - `POST /api/admin/groups/{id}/members` - Add member to group
  - `DELETE /api/admin/groups/{id}/members/{personId}` - Remove member
  - `GET /api/admin/groups/{id}/available-members` - Search non-members
  - `GET /api/admin/events/{id}/registrations` - List event registrations
  - `POST /api/admin/events/{id}/registrations` - Add registration
  - `DELETE /api/admin/events/{id}/registrations/{id}` - Cancel registration

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

### Groups (Admin)
- `GET /api/admin/groups` - List groups
- `POST /api/admin/groups` - Create group
- `PUT /api/admin/groups/{id}` - Update group
- `DELETE /api/admin/groups/{id}` - Delete group
- `GET /api/admin/groups/{id}/members` - View members
- `POST /api/admin/groups/{id}/members` - Add member
- `DELETE /api/admin/groups/{id}/members/{personId}` - Remove member

### Groups (Member Portal)
- `GET /api/portal/groups` - Available groups
- `GET /api/portal/my-groups` - My groups
- `POST /api/portal/groups/{id}/join` - Join group
- `DELETE /api/portal/groups/{id}/leave` - Leave group

### Events (Admin)
- `GET /api/admin/events` - List events
- `POST /api/admin/events` - Create event
- `PUT /api/admin/events/{id}` - Update event
- `DELETE /api/admin/events/{id}` - Delete event
- `GET /api/admin/events/{id}/registrations` - View registrations
- `POST /api/admin/events/{id}/registrations` - Add registration
- `DELETE /api/admin/events/{id}/registrations/{id}` - Remove registration

### Events (Member Portal)
- `GET /api/portal/events` - Upcoming events
- `GET /api/portal/my-events` - My registered events
- `POST /api/portal/events/{id}/register` - Register
- `DELETE /api/portal/events/{id}/register` - Cancel registration

---

## Demo Test Credentials

### Platform Admin (God Mode)
- **Email:** admin@solomon.ai
- **Password:** Demo2026!
- **Access:** All churches, member directory, platform stats
- **Does NOT see:** Media Library, Groups, Events (church-specific)

### Church Admins
- admin@abundant.church / Demo2026!
- admin@cityreach.church / Demo2026!
- admin@pottershouse.church / Demo2026!
- **See:** Full navigation including Media Library, Groups Manager, Events Manager

### Members
- member@abundant.church (Maria Gonzalez) / Demo2026!
- member@cityreach.church (John Smith) / Demo2026!
- **See:** Watch, Give, Groups, Events, Me

---

## Backlog (Priority Order)

### P0 - Completed This Session
- [x] Media Library Sync Bug - Videos sync between admin and portal
- [x] Platform Admin UI cleanup - Clean interface for Solomon admin
- [x] Bidirectional Group Management - Members join/leave, admins add/remove
- [x] Bidirectional Event Management - Members register/cancel, admins manage

### P1 - Next Priority
- [ ] Saved payment methods for members
- [ ] Giving reports with CSV export
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

### Feb 24, 2026 (Latest Session)
- **Fixed P0 Bug**: Media Library sync - removed hardcoded content, portal now fetches from DB
- **Fixed P1 Bug**: Platform Admin UI - clean interface without tenant-specific elements
- **Added**: Bidirectional group member management (member join/leave, admin add/remove)
- **Added**: Bidirectional event registration management (member register/cancel, admin manage)
- **Added**: `/api/portal/my-groups` and `/api/portal/my-events` endpoints
- **Added**: Admin modals for viewing/managing group members and event registrations
- **Added**: Leave group functionality for members
- **Updated**: AppShell.jsx with conditional rendering for platform admin role
- **Created**: Test suite `/app/backend/tests/test_bidirectional_comm_iter10.py`

### Previous Session
- Built Media Library Manager for church admins
- Built Groups & Bible Studies Manager
- Built Events & Services Manager
- Connected portal Watch page to database (dynamic content)
- Correctly scoped Media Library to church admins only
- Platform admin no longer sees Media Library link
- Rebranded from "Samson" to "Solomon AI"
- Live platform dashboard with real aggregated stats

---

## Test Reports
- Latest: `/app/test_reports/iteration_10.json` - 100% pass rate (16/16 backend tests)
