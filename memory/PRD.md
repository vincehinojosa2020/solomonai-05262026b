# Samson - Enterprise Church Management SaaS Platform
## Product Requirements Document

### Overview
**Product Name:** SAMSON  
**Tagline:** "Enterprise Church Management System"  
**Demo Tenant:** Abundant Church (El Paso, TX)  
**Target Scale:** 50,000+ members per tenant  
**Target Audience:** Mega churches (Lakewood, Potter's House, Elevation Church)

---

### What Was Implemented (February 2026)

#### DoD-Grade Enterprise UI Redesign - Completed
1. **Design Aesthetic**
   - Palantir/Bloomberg/Salesforce-inspired UI
   - Sharp corners, no playful rounded elements
   - Data-dense, utilitarian layout
   - High information density

2. **Color Palette**
   - Slate sidebar: #0f172a
   - Blue accent: #3b82f6
   - Warm off-white background: #f8fafc
   - All uppercase labels for stats

3. **Typography**
   - Inter font family (system-like)
   - JetBrains Mono for numbers/data
   - Dense, 13px base font size

4. **Google OAuth Authentication (Emergent Auth)**
   - Login page with "Continue with Google" button
   - Session exchange via backend
   - Protected routes with auth guard
   - Logout functionality
   - User profile in sidebar and topbar

5. **System Banner**
   - "Live Worship Service" banner
   - "Join Now" (Zoom) and "Schedule Visit" (Calendly) buttons

6. **Payment Channels Section**
   - Card/ACH - Active
   - PayPal, Venmo, Zelle, Crypto - Pending (placeholders)
   - Wire Transfer - Contact

#### Core Modules - All Functional

1. **Dashboard**
   - Stats: Total Members (201), Active Groups (20), MTD/YTD Giving, Recurring (30)
   - Monthly Stewardship Goal progress (24%)
   - Attendance Trend (12 weeks)
   - Giving by Fund (12 months)
   - Recent Activity feed
   - Upcoming Events list
   - Alert cards for follow-up actions

2. **People/Members Management**
   - 201 seeded members
   - Search, filter, sort functionality
   - Person detail pages

3. **Stewardship/Giving**
   - MTD Giving: $84,250
   - YTD Giving: $236,303
   - Fund Progress bars (5 funds)
   - Recent Gifts table with pagination
   - Record Gift panel

4. **Groups, Events, Attendance, Communications, Reports, Settings**
   - All modules functional with seeded data

---

### Technical Stack

- **Frontend:** React 18, React Router, Recharts, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI (Python), Motor (async MongoDB)
- **Database:** MongoDB
- **Authentication:** Emergent Google OAuth
- **Design:** Inter + JetBrains Mono fonts, DoD-grade enterprise palette

---

### Authentication Flow

1. User clicks "Continue with Google" on login page
2. Redirected to `auth.emergentagent.com` for Google OAuth
3. After Google auth, redirected back with `session_id` in URL fragment
4. Frontend exchanges `session_id` via backend `/api/auth/session`
5. Backend calls Emergent Auth, stores user/session, sets httpOnly cookie
6. User redirected to dashboard with session cookie

---

### Seeded Demo Data

| Entity | Count |
|--------|-------|
| Tenant | 1 (Abundant Church) |
| Households | 80 |
| People | 201 |
| Groups | 20 |
| Group Members | 394 |
| Funds | 5 |
| Services | 156 |
| Attendance Records | 2,147 |
| Donations | 4,710 |
| Recurring Giving | 30 |
| Pledges | 10 |
| Events | 6 |

---

### Prioritized Backlog

#### P0 - Completed
- [x] DoD-grade enterprise UI design
- [x] Google OAuth authentication
- [x] Dashboard with real-time stats
- [x] People CRUD with search/filter
- [x] Groups management
- [x] Giving module with donation entry
- [x] Stewardship/Giving with fund progress
- [x] Basic attendance tracking
- [x] Navigation and routing
- [x] User profile and logout
- [x] Payment channel placeholders

#### P1 - Next Phase
- [ ] Stripe payment integration (live payments)
- [ ] Resend email integration
- [ ] Real Zoom/Calendly integration
- [ ] PDF Giving statements generation
- [ ] Bulk member import from CSV
- [ ] Check-in kiosk mode

#### P2 - Future
- [ ] PayPal donation integration
- [ ] Venmo donation integration
- [ ] Zelle donation integration
- [ ] Crypto donations with live price lookup
- [ ] Advanced reporting with exports
- [ ] Custom fields for people
- [ ] Pledge campaign management
- [ ] Multi-tenant admin panel
- [ ] Mobile app

---

### MOCKED/PLACEHOLDER Integrations

These features have UI placeholders but are NOT functional:
- **Zoom Link:** https://zoom.us/j/placeholder
- **Calendly Link:** https://calendly.com/placeholder
- **PayPal:** paypal.me/placeholder
- **Venmo:** venmo.com/placeholder
- **Stripe:** Payment processing mocked
- **Resend:** Email sending mocked

---

### API Endpoints

**Authentication:**
- `POST /api/auth/session` - Exchange session_id for user data
- `GET /api/auth/me` - Get current authenticated user
- `POST /api/auth/logout` - Clear session and logout

**Dashboard:**
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/dashboard/giving-trend` - Giving trend data
- `GET /api/dashboard/attendance-trend` - Attendance trend data
- `GET /api/dashboard/activity` - Recent activity feed
- `GET /api/dashboard/upcoming-events` - Upcoming events

**People/Giving/Groups/etc:** See server.py for full API documentation

---

### Test Credentials

For automated testing:
- **Session Token:** test_session_1771463210214
- **Test User:** admin@abundantchurch.org / Admin User

---

### Next Action Items

1. Implement real Stripe payment integration
2. Implement real Resend email integration
3. Replace Zoom/Calendly with real links from user
4. Add PayPal, Venmo donation integrations
5. Implement giving statement PDF generation
6. Add bulk member import from CSV
