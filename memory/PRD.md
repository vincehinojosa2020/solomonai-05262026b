# Samson - Church Management SaaS Platform
## Product Requirements Document

### Overview
**Product Name:** Samson  
**Tagline:** "The operating system for the modern church."  
**Demo Tenant:** Abundant Church (El Cajon, CA)

---

### What Was Implemented (February 2026)

#### UI/UX Overhaul - Completed
1. **Sanctuary Green Theme**
   - Primary color: #2D5A47
   - Gold accent: #D4AF37
   - Cream background: #F5F9F7
   - Luxury brand-inspired design

2. **Join Service Banner (Dashboard)**
   - Prominent banner with "Join Service" Zoom button
   - "Schedule a Visit" Calendly button
   - Video icon with animated pulse
   - Accessible in under 3 clicks

3. **Ways to Give Section (Giving Page)**
   - Card/ACH (Online)
   - PayPal (Coming Soon placeholder)
   - Venmo (Coming Soon placeholder)
   - Zelle (Coming Soon placeholder)
   - Crypto (Coming Soon placeholder)
   - Bank Transfer (Contact Us)

4. **Music Player**
   - Ambient worship background music
   - Play/Pause, Mute, Volume controls
   - Fixed position at bottom left

5. **Branding**
   - "SAMSON" logo with gold "O"
   - No Emergent branding
   - OG meta tags configured

#### Core Modules - All Functional

1. **Dashboard**
   - Real-time stats: Total Members (201), Active Groups (20), MTD/YTD Giving, Recurring Givers (30)
   - Attendance Trend chart (12 weeks)
   - Giving by Fund chart (12 months)
   - Monthly Giving Goal progress bar
   - Quick Insights cards
   - Upcoming Events list

2. **People/Members Management**
   - Paginated member list (201 seeded members)
   - Search by name, email, phone
   - Filter by status (Member, Visitor, Regular, Inactive)
   - Sort by name, date added, last attended, YTD giving
   - Bulk selection with actions
   - Add Person modal with form validation
   - Person Detail page with tabs

3. **Groups Management**
   - Group cards with color-coded types (20 groups)
   - Leader info, capacity progress bars
   - Open/Closed status
   - Meeting schedules
   - Group Detail page with roster, attendance, settings

4. **Giving Module**
   - Donation stats (MTD $84,250, YTD $236,303)
   - Fund Progress bars with goals (5 funds)
   - Giving by Method pie chart
   - Recent Donations table with pagination
   - Enter Donation panel (3-step wizard)
   - Batch management

5. **Attendance**
   - Service types and services list
   - Attendance records per service
   - Check-in functionality

6. **Events**
   - Upcoming events grid
   - Event cards with date, location, registrations

7. **Communications**
   - Email compose form
   - Smart segments
   - Email templates
   - Sent history

8. **Reports**
   - Membership Report (by status)
   - Giving by Fund
   - Giving by Method
   - Top Donors

9. **Settings**
   - General (church info, plan)
   - Appearance (colors, logo)
   - Giving (payment processing)
   - Integrations
   - Staff & Roles

---

### Technical Stack

- **Frontend:** React 18, React Router, Recharts, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI (Python), Motor (async MongoDB)
- **Database:** MongoDB
- **Design:** Cormorant Garamond + Inter + JetBrains Mono fonts, Sanctuary Green palette

---

### User Personas

1. **Church Administrator** - Manages members, tracks giving, generates reports
2. **Executive Pastor** - Views dashboard, monitors church health
3. **Finance Team** - Records donations, manages batches, generates statements
4. **Ministry Leader** - Manages groups, tracks attendance

---

### Core Requirements (Static)

- Multi-tenant SaaS architecture
- 50K+ member scale (pagination, indexing)
- Enterprise-grade UI/UX
- No platform branding ("Samson" only)
- Mobile-responsive design

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
- [x] Dashboard with real-time stats
- [x] People CRUD with search/filter
- [x] Groups management
- [x] Giving module with donation entry
- [x] Basic attendance tracking
- [x] Navigation and routing
- [x] Sanctuary Green UI/UX theme
- [x] Join Service Zoom button
- [x] Donation method placeholders
- [x] Calendly scheduling placeholder
- [x] Background music player
- [x] SAMSON branding

#### P1 - Next Phase
- [ ] Stripe payment integration (keys provided)
- [ ] Resend email integration (keys provided)
- [ ] Real Zoom integration (replace placeholder)
- [ ] Real Calendly integration (replace placeholder)
- [ ] Giving statement PDF generation
- [ ] Bulk import from CSV
- [ ] Check-in kiosk mode

#### P2 - Future
- [ ] PayPal donation integration
- [ ] Venmo donation integration
- [ ] Zelle donation integration
- [ ] Crypto donation with live price lookup
- [ ] Asset donation workflows
- [ ] Advanced reporting with exports
- [ ] Custom fields for people
- [ ] Pledge campaign management
- [ ] SSO/SAML authentication
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

### Next Action Items

1. Implement real Stripe payment integration
2. Implement real Resend email integration
3. Replace Zoom/Calendly placeholders with real links
4. Add PayPal, Venmo donation integrations
5. Implement giving statement PDF generation
6. Add bulk member import from CSV
