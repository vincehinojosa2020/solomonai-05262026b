# Samson - Church Management SaaS Platform
## Product Requirements Document

### Overview
**Product Name:** Samson  
**Tagline:** "The operating system for the modern church."  
**Demo Tenant:** Abundant Church (El Cajon, CA)

---

### What Was Implemented (January 2026)

#### Core Modules - All Functional

1. **Dashboard**
   - Real-time stats: Total Members, Active Groups, MTD/YTD Giving, Recurring Givers
   - Attendance Trend chart (12 weeks)
   - Giving by Fund chart (12 months)
   - Quick Insights cards
   - Upcoming Events list
   - Activity Feed

2. **People/Members Management**
   - Paginated member list (200 seeded members)
   - Search by name, email, phone
   - Filter by status (Member, Visitor, Regular, Inactive)
   - Sort by name, date added, last attended, YTD giving
   - Bulk selection with actions
   - Add Person modal with form validation
   - Person Detail page with tabs:
     - Overview (contact info, engagement score)
     - Giving (donation history, stats, recurring)
     - Attendance (history, stats)
     - Groups (memberships)
     - Communications (email history)
     - Notes (staff notes)

3. **Groups Management**
   - Group cards with color-coded types
   - Leader info, capacity progress bars
   - Open/Closed status
   - Meeting schedules
   - Group Detail page with:
     - Roster with member roles
     - Attendance tracking
     - Settings

4. **Giving Module**
   - Donation stats (MTD, YTD, Recurring, Batches)
   - Fund Progress bars with goals
   - Giving by Method pie chart
   - Recent Donations table with pagination
   - Enter Donation panel (3-step wizard):
     - Donor search
     - Amount, fund, method selection
     - Confirmation
   - Payment methods: Card, Check, Cash, ACH, Crypto, Stock, Real Estate, Vehicle
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
   - Smart segments (pre-built recipient lists)
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
   - Giving (payment processing, preferences)
   - Integrations (Stripe, Resend, etc.)
   - Staff & Roles

---

### Technical Stack

- **Frontend:** React 18, React Router, Recharts, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI (Python), Motor (async MongoDB)
- **Database:** MongoDB
- **Design:** Sora + Inter + JetBrains Mono fonts, 8px grid system

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
| People | 200 |
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

#### P0 - Completed ✅
- [x] Dashboard with real-time stats
- [x] People CRUD with search/filter
- [x] Groups management
- [x] Giving module with donation entry
- [x] Basic attendance tracking
- [x] Navigation and routing

#### P1 - Next Phase
- [ ] Stripe payment integration (keys provided)
- [ ] Resend email integration (keys provided)
- [ ] Giving statement PDF generation
- [ ] Bulk import from CSV
- [ ] Check-in kiosk mode

#### P2 - Future
- [ ] Crypto donation with live price lookup
- [ ] Asset donation workflows
- [ ] Advanced reporting with exports
- [ ] Custom fields for people
- [ ] Pledge campaign management
- [ ] SSO/SAML authentication
- [ ] Mobile app

---

### Next Action Items

1. Add Stripe and Resend API keys to integrate payments and emails
2. Implement giving statement PDF generation
3. Add bulk member import from CSV
4. Build check-in kiosk mode for tablets
5. Consider adding Coinbase Commerce for crypto donations
