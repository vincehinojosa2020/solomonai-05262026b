# SOLOMON AI — THE COMPLETE UI GUIDE

**Every screen. Every button. Every view.**
Written for founders, investors, and the first church that says "show me everything."

---

## HOW TO READ THIS GUIDE

Solomon AI has three doorways. Three types of people walk through them. Each sees a different platform — same engine, different dashboard.

| Role | Who They Are | What They See | Login |
|------|-------------|---------------|-------|
| **Platform Admin** | Vince, the CTO. The person who sees every church, every dollar, every metric. | God Mode: the Bloomberg terminal for church tech. | `admin@solomonai.us` |
| **Church Admin** | Shannon, the CMO. Jacob, the CEO. The pastor's executive team. | Their church's command center: members, giving, events, volunteers, kids check-in. | `shannonnieman1030@gmail.com` |
| **Member** | The person in the pew. The parent dropping off kids. The first-time giver. | A personal portal: give, watch sermons, check events, buy café drinks. | `member@abundant.church` |

Every password for demo accounts: `Demo2026!`

---

# PART ONE: THE PLATFORM ADMIN VIEW (GOD MODE)

*What Vince sees when he logs in at 6am on Monday.*

God Mode is the nerve center. It exists so that one person — or a small ops team — can monitor every church on the Solomon AI platform from a single screen. No switching tenants. No guessing. Just numbers.

---

## 1.1 — THE SIDEBAR

The left-hand navigation. Always visible. Six sections, each one a different lens on the business.

| Nav Item | What It Opens | Why It Exists |
|----------|--------------|---------------|
| **Dashboard** | Platform Overview — the Bloomberg view | The first thing you see. Are we growing? Is anything broken? |
| **Churches** | All 8 church partners in card format | Click any church → drill into their health score, giving chart, members, transactions |
| **Solomon Pay** | Payment processing hub (3 sub-tabs) | Revenue, Transactions, Payouts — the money layer |
| **Donors** | DonorIQ — the donor intelligence engine | 41,389 donors across all churches. Segmented, scored, ranked. |
| **Reports** | Cross-platform analytics | Giving by fund, attendance trends, membership growth, executive summary |
| **Settings** | Platform configuration | Subscription plans, feature flags, API keys |

At the bottom of the sidebar:
- **Ask Solomon** — Opens the AI assistant (streaming responses, UK English TTS)
- **Add New Church** — Wizard to onboard a new tenant
- **Sign Out**

---

## 1.2 — PLATFORM OVERVIEW (DASHBOARD)

The default screen. Two modes, switchable via the toggle in the top-right corner:

### LIVE DATA MODE
What it shows when the platform is running with real (or synthetic) data.

**Hero KPIs** (top row, 4 cards):

| Card | Current Value | What It Means |
|------|--------------|---------------|
| Platform GMV | $108.3M | Total dollars that have flowed through Solomon Pay. Lifetime. |
| Total Revenue | $2.4M | Solomon's cut: processing fees + subscription revenue. |
| Processing MRR | $731 | Monthly recurring revenue from payment processing fees alone. |
| Total ARR | $200.8K | Annualized revenue (processing + subscriptions). The number investors ask for. |

**Sub-stats** (second row, 5 cards):

| Card | Value | Meaning |
|------|-------|---------|
| Churches | 8 | Active church tenants on the platform |
| Total Members | 109,900 | Sum of all members across all churches |
| Transactions | 2,868,854 | Total giving transactions processed |
| Subscription MRR | $16.0K | Revenue from monthly SaaS subscriptions |
| Avg Transaction | $37.74 | Average donation amount platform-wide |

**How Solomon Makes Money** — Three revenue streams displayed as info cards:
1. **Processing Fees** ($1.9M all-time) — 1.9% + $0.30 per card, 0.8% + $0.30 per ACH
2. **Subscription Fees** ($192.0K annualized) — Standard $499/mo, Growth $999/mo, Enterprise $2,000+/mo
3. **Professional Services** ($80K+ annual potential) — Migration bundles, workshops, consulting

**Monthly Giving by Church** — Bar chart showing the last 12 months of giving volume per church. Color-coded by tenant. Exportable as CSV.

**Revenue Trend** — Line chart of monthly Solomon Pay fee revenue.

**Recent Activity Feed** — Real-time feed of platform events: new donations, new members, check-ins. Auto-refreshes every 30 seconds.

**Health Alerts** — Any church with a declining health score gets flagged in red/amber cards at the bottom.

### NEW CHURCH MODE (Demo Mode)
Toggle to "New Church" in the top-right. Shows what a brand-new customer sees on Day 1:
- All KPIs show $0 / 0
- **Setup Checklist** with 6 steps: Connect Bank → Import Members → Set Up Giving → Configure Kids Check-In → Invite Staff → Launch Sunday
- Empty activity feed with encouraging messaging
- "Switch to Live Data" link at the bottom

---

## 1.3 — CHURCHES

A card grid of all church partners. Each card shows:
- Church name and location
- Member count
- All-time giving
- Fees earned (Solomon's revenue from this church)
- Transaction count
- Health Score (A+ through F, color-coded)

**Click any church card → Church Detail Drill-Through:**
- Health Score breakdown (5 dimensions: growth, giving, engagement, retention, activity)
- 12-month giving trend (bar chart)
- Top 10 Donors (name, total giving, donation count)
- Top 20 Members (by lifetime giving)
- Recent 20 Transactions (date, donor name, amount, fund, method, status)
- Summary cards: total members, total giving, transactions, active donors (90d)

**Add Church** button → Opens the onboarding wizard.

---

## 1.4 — SOLOMON PAY

Three sub-tabs accessed by clicking within the Solomon Pay section:

### Revenue Tab
- Monthly processing fee revenue chart
- Revenue by church breakdown
- Blended take rate (1.73%)
- Month-over-month growth

### Transactions Tab
- Paginated table of ALL transactions across ALL churches
- Columns: Date, Church, Donor, Amount, Fund, Fee, Net, Status, Method
- Search by donor name, filter by church, filter by payment method
- 3,040,093 total records with server-side pagination
- Export to CSV

### Payouts Tab
- Payout history with drill-down
- Each payout row shows: date, church, gross, fees, net, transaction count, status, bank account
- **Click any payout → expands to show constituent transactions** (date, donor, amount, fund)
- Pending payouts summary at top

---

## 1.5 — DONORS (DonorIQ)

The donor intelligence dashboard. A single view into the giving behavior of every person across the platform.

**Headline Stats** (4 cards):
| Stat | Value | Definition |
|------|-------|-----------|
| Total Donors | 41,389 | Unique people who have ever given through Solomon Pay |
| Active (90d) | 3,734 | Gave at least once in the last 90 days |
| Recurring | 84 | Active recurring giving schedules |
| Avg Gift | $38 | Mean donation amount |

**DonorIQ Breakdown** — Horizontal stacked bar showing donor lifecycle stages:
- First-Time: people who gave for the first time in the last 30 days
- Occasional: gave 1-3 times in the last year
- Regular: gave 4+ times in the last year
- Recurring: on an active recurring schedule
- At Risk: was regular but hasn't given in 60+ days
- Lapsed: hasn't given in 90+ days

**Top Donors** — Ranked list by all-time giving. Shows name, total, donation count, church.

**Donors by Campus** — Distribution of unique donors across all 8 churches.

---

## 1.6 — REPORTS

Five report types, each in its own tab:

| Report | What It Shows |
|--------|--------------|
| **Giving by Fund** | Breakdown of giving across all funds (General, Building, Missions, Youth, Children, Benevolence, Operations). Filter by date range. |
| **Attendance** | Weekly attendance across all churches. 16 data points. By-church comparison. |
| **Membership** | Active vs inactive members, new member growth, campus distribution |
| **Giving by Method** | Card vs ACH vs cash breakdown with trend |
| **Executive Summary** | One-page overview of platform health: GMV, revenue, church count, donor retention, top performers |

**Fund Reconciliation** — Available via API (`/api/platform/funds/reconciliation`). Shows each fund's total giving, fees, net, and goal progress across all churches.

---

## 1.7 — PLATFORM SETTINGS

- Subscription plan configuration
- Feature flag management
- API key viewer
- Platform branding (logo, colors)

---

## 1.8 — ASK SOLOMON (AI Assistant)

Floating button in the bottom-left corner of every God Mode page. Opens a slide-out chat panel.

**What it does:**
- Answers questions about platform data in natural language
- McKinsey-grade strategic analysis persona
- **Streaming responses** — words appear in real-time (Server-Sent Events)
- **Text-to-Speech** — click the speaker icon on any response to hear it read aloud in UK English
- Voice input via microphone (OpenAI Whisper transcription)
- Can generate reports (markdown, CSV, PDF)

**Example queries:**
- "How is giving trending this quarter?"
- "Which church has the highest donor retention?"
- "Generate a summary report for the board"
- "Compare Abundant East vs Abundant West giving"

**Session memory:** Conversations persist within the browser session. Cleared on logout.

---

## 1.9 — MONDAY MORNING EMAIL

Platform admins can trigger a weekly summary email from the API. The email includes:
- Platform GMV, Total Revenue, MTD Giving, Church count
- Church-by-church performance table (MTD Giving, Fees)
- Delivered via Resend to the specified recipient list

---

# PART TWO: THE CHURCH ADMIN VIEW

*What Shannon and Jacob see when they manage Abundant Church.*

When a church admin logs in, they land on their church's dashboard — scoped to their tenant. Multi-campus admins (like Shannon, who manages East + West + Downtown) see an "All Campuses" aggregate option.

---

## 2.1 — THE SIDEBAR

| Nav Item | What It Opens |
|----------|--------------|
| **Dashboard** | Church overview: members, giving, attendance at a glance |
| **People** | Member directory — search, filter, edit, add |
| **Households** | Family groupings with shared address |
| **Giving** | Donation dashboard, fund management, recurring giving |
| **Groups** | Small group management (Bible studies, connect groups) |
| **Events** | Event calendar, registration, attendance tracking |
| **Services** | Worship service planning, songs, teams |
| **Kids** | Kids check-in admin (classrooms, security, QR codes) |
| **Check-In Setup** | Kiosk configuration, label printing, medical alerts |
| **Volunteers** | Volunteer scheduling, teams, hour tracking |
| **Communications** | Email composer, SMS (Twilio), announcement builder |
| **Pathways** | Spiritual growth pathways tracking |
| **Calendar** | Room booking, event calendar |
| **Courses** | Online learning (Solomon Academy) |
| **Reports** | Church-specific giving, attendance, membership reports |
| **Settings** | Church profile, branding, payment config, API keys |

Bottom of sidebar:
- **Ask Solomon** — AI assistant (scoped to this church's data)
- **Sign Out**

---

## 2.2 — CHURCH DASHBOARD

The church admin's home screen. Four key metrics at the top:

| Card | What It Shows |
|------|--------------|
| Total Members | Count of active people in the directory |
| This Week's Giving | Total donations received this week |
| Attendance (Last Service) | Headcount from the most recent service |
| Active Groups | Number of active small groups |

Below the cards:
- **Giving Trend** — 6-month giving chart
- **Recent Activity** — Latest donations, new members, check-ins
- **Upcoming Events** — Next 5 events with date and registration count
- **Quick Actions** — Add Person, Record Donation, Create Event, Send Email

For multi-campus admins, a campus selector dropdown appears at the top. Choosing "All Campuses" aggregates data across East, West, and Downtown.

---

## 2.3 — PEOPLE (Member Directory)

A searchable, sortable, paginated table of every person in the church database.

**Columns:** Name, Email, Phone, Membership Status, Campus, Engagement Score, Lifetime Giving

**Features:**
- Full-text search across name, email, phone
- Filter by status (Active, Inactive, Visitor, Prospect)
- Sort by any column
- Click a person → Person Detail page

**Person Detail:**
- Profile card (name, photo placeholder, contact info, address)
- Giving History tab — every donation, amount, date, fund, method
- Attendance History tab — services attended with dates
- Groups tab — small groups they belong to
- Communication History tab — emails/SMS sent to this person
- Notes tab — internal staff notes

**Import Members:** Button to launch the CSV Import Wizard.
- Upload a CSV file (Planning Center, Breeze, or any spreadsheet)
- Auto-detects column mapping for Planning Center exports
- 16 mappable fields: First Name, Last Name, Email, Phone, Gender, DOB, Status, Campus, Address, City, State, Zip, Notes, and more
- Preview before importing
- Duplicate detection by email
- Import summary with success/skip/error counts

---

## 2.4 — GIVING

**Giving Dashboard:**
- MTD, QTD, YTD giving totals
- Giving by fund (pie chart)
- Average gift amount
- Donor count
- Recent donations list

**Fund Management:**
- Create, edit, archive funds (General, Building, Missions, etc.)
- Fund goals with progress bars
- Fund-specific giving links

**Recurring Giving:**
- Active recurring schedules
- Frequency (weekly, biweekly, monthly)
- Next gift date
- Amount and method

**Donation Batches:**
- Group donations by date for reconciliation
- Mark batches as deposited
- Batch total and transaction count

---

## 2.5 — GROUPS

**Groups List:**
- Grid or list view of all small groups
- Filter by type (Bible Study, Connect Group, Service Team, etc.)
- Search by name

**Group Detail:**
- Group info (name, leader, meeting schedule, description)
- Member list with add/remove
- Attendance tracking per meeting
- Communication tools (email group members)

**Leader Dashboard:**
- Groups they lead
- Upcoming meetings
- Member engagement scores

---

## 2.6 — EVENTS

**Events Calendar:**
- Monthly calendar view
- List view of upcoming events
- Click to create new event

**Event Detail:**
- Title, date, time, location
- Description and image
- Registration management
- Attendee list with check-in status
- Public registration link (shareable URL)

---

## 2.7 — SERVICES (Worship Planning)

**Service List:**
- Upcoming and past services
- Service type (Sunday AM, Sunday PM, Wednesday, etc.)
- Headcount per service

**Service Detail:**
- Date and time
- Total attendance
- Attendance by person (who was there)
- Notes

**Service Types:**
- Create/manage service types
- Default times and days

---

## 2.8 — KIDS CHECK-IN

The admin hub for children's ministry. Three tabs:

### Currently Checked In
- Card grid of every child currently checked in
- Each card shows: child name, age, classroom, allergies (flagged in red), pickup code, check-in time, parent name
- "Check Out" button on each card
- Real-time auto-refresh (every 2 seconds)
- New check-in alert with sound notification

### Check In
- Searchable list of all registered children
- Filter by name or parent name
- One-tap "Check In" button per child
- Manual check-in for walk-ins (new family registration)

### Check Out
Two methods:
1. **Scan QR Code** — Camera-based QR reader. Parent shows their QR code on their phone.
2. **Manual Code** — Type the 3-6 character alphanumeric pickup code.

Both verify the code, show the matched child with photo/name/allergies, and require confirmation before release.

**Security features:**
- Unique pickup code per check-in session
- Allergy alerts prominently displayed
- Parent name verification
- Audit trail of all check-in/check-out events

---

## 2.9 — CHECK-IN SETUP

Seven configuration tabs:

| Tab | What You Configure |
|-----|-------------------|
| **Locations** | Classrooms/rooms (name, room number, age range, capacity) |
| **Stations** | Check-in kiosks (self-serve, manned, roster mode, quick mode) |
| **Labels** | Thermal label layout (child name, classroom, security code, allergy icon) |
| **Printers** | Connect label printers (Dymo, Brother, generic ESC/POS) |
| **Medical Alerts** | Flag children with medical conditions, allergies, or special needs |
| **Guardians** | Authorized pickup people per family |
| **Reports** | Check-in analytics: 30-day total, daily trend chart, room breakdown, first-time visitors |

---

## 2.10 — VOLUNTEERS

- Volunteer teams and roles
- Scheduling (who's serving this Sunday)
- Hour tracking
- Leaderboard (top volunteers by hours served)

---

## 2.11 — COMMUNICATIONS

- **Email Composer** — Subject, body (rich text), recipient selection
- **SMS** — Text message to individuals or groups (Twilio integration configured)
- **Announcements** — Church-wide announcements that appear in the member portal
- **Templates** — Save reusable email/SMS templates

---

## 2.12 — REPORTS (Church-Level)

| Report | What It Shows |
|--------|--------------|
| Giving by Fund | Bar chart of giving per fund with date range filter |
| Giving by Method | Card vs ACH vs Cash breakdown |
| Attendance | Weekly attendance trend with service type breakdown |
| Membership | Growth chart, new members, active vs inactive |
| Top Donors | Ranked list by giving amount with giving details |
| Executive Summary | One-page overview for board meetings |
| Kids Check-In | 30-day trend, room breakdown, first-timers |

---

# PART THREE: THE MEMBER VIEW (PORTAL)

*What a church member sees when they open Solomon AI on their phone.*

The member portal is the consumer-facing experience. Clean, fast, mobile-first. Everything a church member needs in one place.

---

## 3.1 — PORTAL NAVIGATION

A horizontal top bar with icons. Six main sections:

| Icon | Section | What It Does |
|------|---------|-------------|
| Home | **Home** | Welcome screen, upcoming events, giving streak, announcements |
| Heart | **Give** | Donate money to the church |
| Play | **Watch** | Sermon video library |
| Calendar | **Events** | Browse and register for events |
| Coffee | **Cafe** | Order food and drinks for pickup |
| Shirt | **Merch** | Church merchandise store |

Additional sections accessible from the profile menu:
- **My Groups** — Small groups you belong to
- **My Giving** — Giving history and statements
- **Kids** — Register children, view check-in codes
- **Courses** — Solomon Academy online learning
- **Directory** — Church member directory
- **Profile** — Edit your personal information

---

## 3.2 — HOME

The landing screen for logged-in members.

**Greeting:** "Good morning, Sarah" (time-aware greeting with the member's first name)

**Giving Streak Badge:**
- Shows your current giving streak (e.g., "14-Week Streak!")
- Motivational copy: "You've been faithful for 14 consecutive weeks. You're in the top 3% of givers."
- Visual badge with streak count

**Upcoming Events:**
- Next 3 events with date, time, and "Register" button
- Cards with event images

**Announcements:**
- Church-wide announcements from the admin team

**Quick Actions:**
- "Give Now" button
- "Watch Latest Sermon" link

---

## 3.3 — GIVE

The donation flow. This is the most polished member-facing experience in the platform.

**Step 1: Choose Amount**
- Suggested amounts: $25, $50, $100, $250, $500, $1,000
- Custom amount input
- Fund selector (General Fund, Building Fund, Missions, etc.)
- Frequency toggle: One-Time, Weekly, Bi-Weekly, Monthly

**Step 2: Payment**
- Saved card on file (Visa ****4242) — one-tap giving
- "Add New Card" option
- ACH bank transfer option

**Step 3: Enhancements** (Frank Luntz-inspired persuasive design)
- **"Cover Processing Fees"** toggle — "Would you like to cover the $X.XX processing fee so 100% of your gift goes to ministry?"
- **"Round Up"** toggle — Rounds to the nearest $5 or $10 (available on Café and Merch purchases too)

**Step 4: Confirmation**
- Summary card: amount, fund, method, fee coverage
- "Give" button → success toast with confetti animation
- Receipt sent via email

---

## 3.4 — WATCH

A dark-themed Netflix-style video library.

**Layout:**
- Category rows (e.g., "Latest Sermons", "Teaching Series", "Worship")
- Each row scrolls horizontally
- Video thumbnails with title, speaker, duration
- Click to play (embedded video player)

**Current content:** 3 videos by Pastor Charles Nieman (seeded demo content)

---

## 3.5 — EVENTS

**Upcoming Events List:**
- Card layout with event image, title, date, time, location
- "Register" button on each card
- Registration confirmation with QR code

**Event Detail:**
- Full description
- Map/location link
- Registration form (name, email, phone, optional fields)
- Share link

---

## 3.6 — CAFE

Church café ordering system. Flat navigation — no nested menus.

**Menu Display:**
- Category tabs (Coffee, Tea, Smoothies, Pastries, Breakfast)
- Item cards with name, price, image
- "Add to Cart" button

**Cart & Checkout:**
- Cart summary in a slide-out panel
- "Round Up" toggle
- "Cover Fees" toggle
- Pay with saved card (Solomon Pay)
- Order confirmation with pickup number

---

## 3.7 — MERCH

Church merchandise store. Same flat navigation pattern as Café.

**Product Display:**
- Grid of products with images, names, prices
- Size/variant selector where applicable
- "Add to Cart" button

**Checkout:**
- Same payment flow as Café
- "Round Up" and "Cover Fees" toggles
- Order confirmation

---

## 3.8 — MY GIVING (Profile Section)

**Giving History:**
- List of all donations with date, amount, fund, method
- Filter by date range
- Year-to-date total
- Downloadable giving statement (for tax purposes)

**Recurring Giving:**
- Active schedules with amount, frequency, next date
- Edit or cancel recurring gifts

---

## 3.9 — KIDS (Portal)

**Registered Children:**
- List of your children with name, age, classroom assignment
- Allergies and medical notes displayed

**Check-In Code:**
- Current session's pickup code (shown as a large, readable code)
- QR code for scanning at check-out kiosk

---

## 3.10 — COURSES (Solomon Academy)

- Course catalog with categories
- Enroll in courses
- Lesson viewer with progress tracking
- Video lessons, reading materials, quizzes

---

# PART FOUR: PUBLIC PAGES

Pages accessible without logging in.

| URL | Page | What's There |
|-----|------|-------------|
| `/` | Landing Page | Hero with "Your Church. One App. Zero Compromise." headline, God Mode KPI screenshot, pricing comparison grid, lead capture form, footer with Privacy/Terms/Security/Calendly links |
| `/login` | Login | Email/password form, Google OAuth button, "Forgot password?" link, autocomplete disabled |
| `/signup` | Sign Up | Registration form for new accounts |
| `/demo` | Demo | Interactive demo walkthrough |
| `/pricing` | Pricing | 4-tier pricing: Standard ($499), Growth ($999), Enterprise ($2,000+), Platform (custom) |
| `/privacy` | Privacy Policy | 7-section privacy policy covering data collection, AI usage, data retention |
| `/terms` | Terms of Service | 8-section terms covering payment processing, data ownership, liability |
| `/security` | Security | 6-card security overview: encryption, auth, access controls, infrastructure, audit logging, vulnerability reporting |
| `/forgot-password` | Password Reset | Email input → sends reset instructions via Resend email |

---

# PART FIVE: THE AI LAYER

Solomon AI appears in two contexts:

**1. Sidebar Chat (All Roles)**
- Floating "Ask Solomon" button in the bottom-left
- Slide-out chat panel
- Text input + microphone button (voice-to-text via Whisper)
- Streaming responses with typing animation
- TTS button on each response (UK English voice)
- Session memory within the browser session

**2. Contextual Intelligence**
- Dashboard insights ("Giving is up 8.8% vs last year")
- Donor risk alerts ("142 donors are at risk of lapsing")
- Health score calculations (automated A+ through F grading)
- Fund reconciliation summaries

---

# PART SIX: TECHNICAL REFERENCE FOR THE UI

**89 distinct page components** across 4 view layers.

**Frontend stack:** React 18 + Tailwind CSS + shadcn/ui + Recharts + Lucide icons + Framer Motion

**Key directories:**
```
/app/frontend/src/
  pages/
    admin/         — Church admin pages (CSVMemberImport, etc.)
    kids/          — Extracted kids check-in sub-components
    platform/      — God Mode components (ChurchDetail, PlatformDonors, etc.)
    portal/        — Member portal pages (PortalGive, PortalWatch, etc.)
    AttendancePage.jsx
    CheckInSetupPage.jsx (646 lines)
    KidsCheckinAdmin.jsx (672 lines)
    LandingPage.jsx
    LoginPage.jsx
    PlatformDashboard.jsx (main God Mode orchestrator)
    PricingPage.jsx
    PrivacyPage.jsx / TermsPage.jsx / SecurityPage.jsx
    ForgotPasswordPage.jsx
  components/
    layout/AppShell.jsx    — Main layout with sidebar, header, bottom nav
    SolomonChat.jsx        — AI assistant chat component
    ui/                    — shadcn/ui component library
```

**Accessibility (WCAG AA):**
- Skip-to-main-content link on every admin page
- `aria-label` on all form inputs, navigation, sidebar toggle
- `role="main"`, `role="navigation"`, `role="banner"` on semantic sections
- `aria-expanded` on collapsible sidebar
- Keyboard-navigable shadcn/ui components

**Mobile Responsiveness:**
- Landing page: hamburger menu at <768px, stacking grids
- Admin: sidebar collapses to bottom navigation at <900px
- Portal: designed mobile-first with horizontal scroll nav
- Tables: horizontal scroll on narrow viewports

---

*This document reflects the state of Solomon AI as of April 17, 2026. Every screen described above exists in the codebase and renders with synthetic demo data. The platform is demo-ready for investor walkthroughs and prospect presentations.*

*Document location: `/app/SOLOMON_AI_UI_GUIDE.md`*
