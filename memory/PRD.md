# Solomon AI — PRD

## Original Problem Statement
SOLOMON AI — Multi-tenant church management & payment processing SaaS platform. Productized for nationwide distribution. Includes God Mode (Platform Admin), Solomon Pay processor, Bloomberg-grade reporting, Ask Solomon AI intelligence, and 8 seeded church tenants simulating ~$100M+ GMV.

## Architecture
- **Backend**: FastAPI + Motor (async MongoDB) + Anthropic Claude (Solomon AI)
- **Frontend**: React 18 + Tailwind + Shadcn/UI + Recharts
- **Auth**: JWT sessions + Google OAuth
- **Payments**: Solomon Pay (proprietary, Stripe removed)
- **Cache**: platform_stats_cache + dashboard_stats_cache for God Mode

## Key Roles
- `platform_admin`: God Mode (full platform visibility)
- `admin` / `church_admin`: Church-level admin
- `member`: Church member portal

## 8 Seeded Churches
Abundant Downtown, Abundant West, Abundant East, The Potter's House, City Reach, EdenX Ministries, Hill Country Bible, Cristo Viene

## Completed Work (All Sessions)
- Stripe fully removed, Solomon Pay processor built
- Recurring Giving Background Scheduler
- Kids Check-In (Printer & Kiosk mode)
- Feature Education Headers / Contextual Help system
- Calendar & Events + Mobile-first Paid Event Registration
- Communications (Email template builder)
- Google OAuth integrated
- Commerce Multi-Payment Selector
- Visual Workflow Builder & Custom Report Builder scaffolded
- Technical Hardening (Rate limiting to MongoDB, JWT sessions, slow query optimization)
- God Mode UI overhaul (PlatformDashboard.jsx) with 6 sections
- Cache-first architecture (<150ms load times) for God Mode
- Code quality fixes (secrets, hooks, refactoring)
- Architecture doc generated
- 9,017 audit logs seeded (3 years across all tenants)
- Reports Page: Per-tab info panels on all 9 report tabs (Giving, Attendance, Groups, Check-In, Cafe & Merch, Volunteers, Membership, Cross-Analysis, Audit Log)
- **God Mode KPI Vocabulary Tooltips**: Added GlossaryPanel + KpiInfo components to Dashboard, Church Portfolio, Churches, Solomon Pay, and Donors sections with full definitions for all metrics (Platform GMV, MRR, ARR, Active Donors, Fees Earned, etc.)
- **Abundant-First Sorting**: Churches always sorted with Abundant campuses at top
- **Abundant Downtown Rename**: "Abundant Northeast" renamed to "Abundant Downtown" in DB + cache
- **Production 500 Fix**: Platform stats endpoint now always serves stale cache (never blocks on expensive aggregation), added 25s timeout protection for cache-miss scenarios

## Remaining Work
- P0: Redeploy to solomonai.us (production 500 fix + all UI improvements)
- P1: Implement "Founder Role" — role above church_admin for unified multi-campus dashboard
- P1: Schedule Automated Platform Summary Email (weekly metrics to founders@solomonai.us)
- P2: Custom Report Builder full implementation (preview + export edge cases)
- P2: Reports tabs 2-8 with live data
- P2: PDF export for platform reports
- P2: Payment method breakdown on Revenue page
- P2: Apple/Google Pay live integration (currently mocked)
- P3: Split oversized components (KidsCheckinAdmin.jsx 794 lines, CheckInSetupPage.jsx 704 lines)
