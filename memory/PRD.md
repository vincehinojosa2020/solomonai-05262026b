# Solomon AI — PRD (Final State April 3, 2026)

## Original Problem Statement
SOLOMON AI — Full-parity church management SaaS with proprietary payment processor (Solomon Pay). 14-Phase Master Build Directive. Competing with Planning Center, Church Center, Pushpay, SecureGive, Tithely.

## Platform Scale
- **7 church tenants** (3 Abundant + Potter's House + EdenX + City Reach + parent)
- **60,226 total members**
- **$68.9M all-time GMV processed**
- **$1.2M platform fees earned**
- **$20.3K MRR / $243.6K ARR**
- **540+ API endpoints, 90+ DB collections, 75+ frontend pages**

## Architecture
```
Backend: FastAPI + MongoDB (540+ endpoints)
Frontend: React + Shadcn/UI (75+ pages)
AI: Claude (Emergent LLM Key) + voice + 14 action types
Payments: Solomon Pay (proprietary, 1.9%+$0.30 card, 0.8%+$0.30 ACH)
Calendar: FullCalendar v6
Schedulers: asyncio (recurring giving + workflow runner)
Caching: In-memory (5-min TTL dashboard, 1-hr lists)
PDF Gen: ReportLab (giving statements, reports)
```

## Final Test Status
- **Iteration 81: 45/45 backend + 36/36 frontend = 100% PASS — Final Section W UAT**
- **Iteration 80: 25/25 backend + 100% frontend — Sections H-W partial**
- **Iteration 79: 26/26 backend + 95% frontend — Sections B-G**
- **Iteration 78: 22/22 backend — Sprint 1A-2E**

## Complete Feature Inventory (ALL COMPLETE)

### God Mode (Platform Admin)
- 7-tab dashboard: Executive, Transactions, Payouts, Donors, Revenue, Churches, Support
- Hero KPIs: GMV, Revenue, MRR, ARR (4 large cards)
- Attention Required widget (churches with Health Score C or below, with specific declining metric)
- Church portfolio table with Health Score A-F badges (expandable dimension breakdown)
- Add New Church wizard (< 3 min, 5-step)
- Impersonation / drill-in to church admin
- MRR/ARR calculated from active recurring schedules × fee rates

### Solomon AI Intelligence
- Member context: name, campus, YTD giving, lifetime giving, last gift, groups, recurring schedule, saved cards, registered events
- 14 action types with confirmation cards before each:
  donate, recurring_giving_create, recurring_giving_pause, recurring_giving_resume, recurring_giving_cancel, event_register, group_join, group_leave, cafe_order, merch_order, kids_checkin, prayer_request, generate_statement, member_checkin
- PDF generation via ReportLab (giving statements, downloadable in chat)
- Admin context: church-wide analytics, member lookup, report generation
- God Mode context: cross-tenant intelligence, investor report generation
- Frank Luntz voice: warm, sharp, personal tone throughout

### Feature Education System
- FeatureEducationHeader on: Giving, Services, Groups, People, Communications, Reports, Calendar, SolomonPay + all major pages
- HelpTooltip (ℹ️) on every section header
- Collapsible, dismissible, localStorage-persisted
- 30+ help entries in helpContent.js

### Bloomberg Reports (9 tabs)
- Giving, Attendance, Groups, Check-In, Cafe & Merch, Volunteers, Membership, Cross-Analysis, Audit Log
- Cross-Analysis: 4 correlation cards (Giving↔Attendance, Groups↔Giving, Cafe↔Kids, Volunteer↔Retention)
- CSV export on all tabs

### Visual Workflow Builder
- All 12 trigger types (New Member, First Donation, Birthday, Lapsed Donor, etc.)
- All 9 action types (Send Email, SMS, Add to Group, Update Field, etc.)
- Condition nodes, Delay nodes, End nodes
- Visual canvas with add-node buttons between steps
- Background runner placeholder (15-min idempotent)

### Custom Report Builder
- 7-step wizard: Source → Columns → Filters → Grouping → Preview → Save → Export
- 5 data sources: People, Donations, Attendance, Groups, Check-Ins
- 7 pre-built templates
- CSV export, save/reuse reports

### People Enhancements
- Multi-select bulk update (status change for multiple members)
- Directory privacy toggles (show email/phone/address in portal)
- Journey Funnel widget on Dashboard (Visitor → Regular → Member → Serving → Leading)

### Multi-Campus
- "Abundant" branding in portal (not "Abundant East")
- First-login campus selector modal
- Campus dropdown in giving, cafe, merch flows
- /api/portal/campuses endpoint

### Technical
- Dashboard stats caching (5-min TTL in-memory)
- Persistent rate limiting (in-memory with MongoDB backup)
- /api/health endpoint
- Bulk update endpoint: /api/admin/people/bulk-update
- Privacy endpoint: /api/portal/profile/privacy
- PDF download: /api/portal/giving/statement-pdf/{id}
- Custom reports: /api/admin/reports/custom (CRUD + preview + export)

## Remaining / Deferred
- JWT-signed session tokens (currently UUID-based, functional)
- Object storage for file uploads (persistent volume)
- Apple Pay / Google Pay live integration (Payment Request API scaffold done)
- Monday summary emails
- Household role auto-assignment UI (field stored, UI basic)
- Email analytics via Resend webhooks
- Full SMS send capability (Twilio scaffolded, needs API keys)
- Final production deployment

## Credentials
See /app/memory/test_credentials.md
