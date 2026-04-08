# Solomon AI — PRD

## Original Problem Statement
SOLOMON AI — Multi-tenant church management & payment processing SaaS platform. Productized for nationwide distribution. Includes God Mode (Platform Admin), Solomon Pay processor, Bloomberg-grade reporting, Ask Solomon AI intelligence, and 8 seeded church tenants simulating ~$100M+ GMV.

## Architecture
- **Backend**: FastAPI + Motor (async MongoDB) + Anthropic Claude (Solomon AI)
- **Frontend**: React 18 + Tailwind + Shadcn/UI + Recharts
- **Auth**: JWT sessions + Google OAuth
- **Payments**: Solomon Pay (proprietary, Stripe removed)
- **Cache**: platform_stats_cache + dashboard_stats_cache for God Mode
- **AI Provider**: Anthropic Claude (claude-sonnet-4.5)
- **Infrastructure**: Google Cloud Platform

## Key Roles
- `platform_admin`: God Mode (full platform visibility)
- `admin` / `church_admin`: Church-level admin
- `member`: Church member portal

## 8 Seeded Churches
Abundant Downtown, Abundant West, Abundant East, The Potter's House, City Reach, EdenX Ministries, Hill Country Bible, Cristo Viene

## Revenue Model (3 Streams)
1. **Processing Fees** — 1.9% + $0.30 (card), 0.8% + $0.30 (ACH). Per-transaction revenue.
2. **Subscription Fees** — Standard ($499/mo), Growth ($999/mo), Enterprise ($2,000+/mo)
3. **Professional Services** — Starter Migration ($5K), 10-Hour Bundle ($10K), Full Migration ($15K), On-Site Workshop ($25K), Office Hours ($2,500/mo)

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
- Technical Hardening (Rate limiting, JWT sessions, slow query optimization)
- God Mode UI overhaul with 6 sections + cache-first architecture (<150ms)
- Code quality fixes (secrets, hooks, refactoring)
- Architecture doc + 9,017 audit logs seeded (3 years)
- Reports: Per-tab info panels on all 9 tabs
- God Mode KPI Vocabulary Tooltips on all sections
- Abundant-First Sorting + "Abundant Downtown" rename
- Production 500 Fix (stale cache + 25s timeout protection)
- **Revenue Model Clarity**: "How Solomon AI Makes Money" card with 3 revenue streams + "Why Churches Switch" competitive section
- **Solomon AI God Mode Sidebar**: McKinsey/Bain/CPA persona chat with voice recording (Whisper), 6 sample prompts, report generation (CSV/Markdown), inline export buttons
- **Enhanced Cross-Analysis**: 6 powerful cross-domain correlations (Giving↔Attendance, Group↔LTV, Volunteer↔Retention, Kids↔Family, Visitor↔Conversion, Recurring↔Engagement) with Solomon's Insight boxes and specific dollar impact figures
- **9 Pre-Built Analysis Templates** (incl. Donor Churn Risk, Campus Migration, Event ROI)
- **Professional Services Pricing** in Settings (Snyk/Veracode-modeled engagement packages)
- **Settings: AI Provider** → "Anthropic Claude (claude-sonnet-4.5)", **Infrastructure** → "Google Cloud Platform"
- **Settings Key Terms glossary** explaining processing fees, subscription MRR, blended take rate, etc.
- **3-Year Historical Data**: 288 monthly report records seeded across all 8 campuses (membership, attendance, groups, check-in, volunteers)

## Remaining Work
- P0: Redeploy to solomonai.us (production 500 fix + all UI improvements)
- P1: Implement "Founder Role" for unified multi-campus dashboard
- P1: Schedule Automated Platform Summary Email (weekly metrics)
- P2: Custom Report Builder full implementation (preview + export)
- P2: Reports tabs 2-8 with live data from monthly_reports collection
- P2: PDF export for reports (currently markdown/CSV)
- P2: Apple/Google Pay live integration (currently mocked)
- P3: Split oversized components (KidsCheckinAdmin, CheckInSetupPage)
