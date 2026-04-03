# Solomon AI — PRD (Final State April 3, 2026)

## Original Problem Statement
SOLOMON AI — Full-parity church management SaaS with proprietary payment processor (Solomon Pay). 14-Phase Master Build Directive targeting nationwide SaaS distribution. Competing with Planning Center, Church Center, Pushpay, SecureGive, Tithely.

## Platform Scale
- **7 church tenants** (3 Abundant + Potter's House + EdenX + City Reach + parent)
- **60,226 total members**
- **$68.9M all-time GMV processed**
- **$1.2M platform fees earned**
- **$20.3K MRR / $243.6K ARR**
- **540+ API endpoints, ~90 DB collections, 70+ frontend pages**

## Architecture
```
Backend: FastAPI + MongoDB (540+ endpoints)
Frontend: React + Shadcn/UI (70+ pages)
AI: Claude (Emergent LLM Key) + voice + 7 action types
Payments: Solomon Pay (1.9%+$0.30 card, 0.8%+$0.30 ACH)
Calendar: FullCalendar v6
Scheduler: asyncio (recurring giving, hourly)
Multi-Campus: campus selector + /portal/campuses
```

## Complete Feature Inventory

### Core Platform
- Multi-tenant SaaS, strict data segregation
- RBAC (12 roles + permission granularity)
- JWT session auth + Google OAuth
- Rate limiting (5 attempts / 15-min lockout)
- /api/health endpoint + /api/metrics

### People
- Full directory with search, filter, pagination
- Person detail pages with giving history, groups, notes
- Household management
- Bulk update (multi-select → update status/campus)
- Custom fields
- Duplicate detection + merge
- Smart Lists
- Import/Export CSV

### Solomon Pay
- Proprietary payment processor (no Stripe/Pushpay)
- Card + ACH tokenization + refunds
- Fee: 1.9%+$0.30 card, 0.8%+$0.30 ACH
- Recurring giving scheduler (hourly asyncio, idempotent, retry)
- Virtual Terminal
- Payouts management
- 8-tab admin dashboard

### Giving / Stewardship
- Real-time donation recording
- Fund management with goals
- Cover fees option
- Recurring giving (portal + scheduler)
- Tax statement PDF download
- Admin batch entry
- Giving nudge after purchases

### Kids Check-In
- Code-based secure check-in
- DYMO/Brother web print labels (child + parent + allergy)
- Kiosk mode (full-screen, PIN exit)
- Family phone lookup
- Medical alerts, guardian management
- QR code pickup

### Events & Calendar
- FullCalendar (month/week/day views)
- Recurring events (RRULE)
- Drag to reschedule
- Paid registration (Free/Fixed/Donation/Tiered)
- Room booking + conflict detection
- Campus-filtered events

### Communications
- Email template builder (5 built-in + custom)
- Merge fields ({{first_name}}, {{church_name}}, etc.)
- Twilio SMS scaffold
- Scheduled sends + cancel
- Channel selector (Email/SMS/Push)
- Segment targeting

### Services
- Service plan builder
- 9 item types (Song, Scripture, Prayer, Message, Offering, etc.)
- Team assignments + positions
- Live Mode (full-screen, tablet-friendly, Next button)
- Templates + duplicate
- Music Stand view
- CCLI number tracking (stored)

### Groups
- Small groups, Bible studies, ministry teams
- Leader dashboard
- Group chat
- Attendance tracking
- Group health scoring

### Reports (Bloomberg-grade, 9 tabs)
- Giving, Attendance, Groups, Check-In, Cafe & Merch
- Volunteers, Membership, Cross-Analysis, Audit Log
- CSV/PDF export
- Pre-built analysis templates

### Solomon AI
- Member + admin + God Mode context
- 7 action types (give, order, register, join, check-in, etc.)
- Confirmation cards before actions
- Voice mode
- Feature guide + support fallback

### Multi-Campus
- Dynamic portal branding ("Abundant" not "Abundant East")
- First-login campus selector modal
- Campus dropdown in giving, cafe, merch
- Admin campus filter

### Feature Education
- Collapsible education headers on all major pages
- HelpTooltip (ℹ️) on every section
- Empty states with CTAs

### Commerce
- Cafe POS (menu, cart, pickup slots)
- Merch store (inventory, variants)
- Multi-payment: Solomon Pay, guest card, Apple Pay, Google Pay (API scaffold)
- Giving nudge after purchase

### God Mode (Platform Admin)
- 7-tab dashboard: Executive, Transactions, Payouts, Donors, Revenue, Churches, Support
- Hero KPIs: GMV, Revenue, MRR, ARR
- Church portfolio table with Health Scores (A-F grade)
- Add New Church wizard (< 3 min)
- Church impersonation

### Technical Hardening
- Rate limiting (in-memory, fail-open)
- /api/health endpoint
- Pagination on all list endpoints
- Structured error format
- MongoDB indexes (50+ compound)
- Scheduler with idempotency + retry

## Test Status
- Iteration 80: 25/25 backend, 100% frontend — Final UAT (H-W)
- Iteration 79: 26/26 backend, 95% frontend — Sections B-G
- Iteration 78: 22/22 backend — Sprint 1A-2E

## Credentials
See /app/memory/test_credentials.md

## Remaining / Deferred
- Phase P: Visual Workflow Builder (drag-and-drop canvas)
- Phase P: Custom Report Builder (column selector, filters)
- Phase Q: Journey tracking funnel visualization on dashboard
- Phase R: Object storage for file uploads (survives pod restarts)
- Phase R: Persistent rate limiting (MongoDB-backed)
- Phase R: Redis/MongoDB caching layer
- Phase T: Complete church onboarding email delivery
- Native mobile app (iOS/Android)
- Apple Pay / Google Pay live integration
- Monday summary emails
- Final production deployment
