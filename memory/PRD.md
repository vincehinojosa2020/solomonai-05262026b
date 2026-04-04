# Solomon AI — PRD (Final State April 4, 2026)

## Original Problem Statement
SOLOMON AI — Full-parity church management SaaS with proprietary payment processor (Solomon Pay). 14-Phase Master Build Directive. Competing with Planning Center, Church Center, Pushpay, SecureGive, Tithely.

## Platform Scale
- **4 real church tenants** with donation data + 6 empty/test tenants (filtered)
- **60,200 total members**
- **944,826 total donations** (3 years of seed data)
- **$68.99M all-time GMV**
- **$1.21M platform fees earned**
- **$20.3K MRR / $243.6K ARR**
- **538+ API endpoints, 90+ DB collections, 75+ frontend pages**

## Church Portfolio (Real Data)
| Church | City | Members | All-Time Giving | Fees | Health |
|--------|------|---------|-----------------|------|--------|
| Abundant Church | El Paso, TX | 25,000 | $42.96M | $760.4K | C (55) |
| The Potter's House | Dallas, TX | 14,500 | $11.67M | $198.8K | B+ (72) |
| City Reach Church | Cedar Park, TX | 10,400 | $7.54M | $129.3K | B+ (72) |
| EdenX Ministries | Folsom, CA | 10,300 | $6.82M | $117.0K | B+ (72) |

## Architecture
```
Backend: FastAPI + MongoDB (538+ endpoints)
Frontend: React + Shadcn/UI (75+ pages)
AI: Claude (Emergent LLM Key) + voice + 14 action types
Payments: Solomon Pay (proprietary)
Calendar: FullCalendar v6
Schedulers: asyncio (recurring giving + workflow runner)
Caching: In-memory (5-min TTL)
PDF Gen: ReportLab
```

## God Mode Dashboard — COMPLETE ✅

### /platform route — Standalone (no AppShell)
- **Hero KPIs**: Platform GMV $68.99M | Platform Revenue $1.21M | MRR $20.3K | ARR $243.6K
- **Secondary stats**: 4 Churches | 60,200 Members | 944,826 Transactions | YTD Giving | YTD Revenue
- **Stacked bar chart**: Monthly giving by church (last 12 months, color-coded)
- **Revenue trend**: Area chart of monthly Solomon Pay fees
- **Church Portfolio Table**: All 4 churches with City, Members, Active Donors, All-Time Giving, Fees, Health badge, View+Impersonate buttons
- **Activity Feed**: Real-time donations + recurring signups (polls every 15s)
- **Attention Required**: Amber/red alerts for churches with C/D health scores
- **Left Sidebar**: Solomon AI branding + 8-section nav (Dashboard, Churches, Transactions, Payouts, Revenue, Donors, Reports, Settings)
- **Churches section**: Cards with health score breakdown dimensions
- **Transactions section**: Full table with search by donor + filter by church + Export CSV
- **Revenue section**: KPIs + trend chart + breakdown by church
- **Reports section**: 9 tabs (Giving, Attendance, Groups, Check-In, Commerce, Volunteers, Membership, **Cross-Analysis**, Audit Log)

## Health Scores
- Computed from: Engagement Rate (25%), Giving/Member (25%), Groups/100 Members (20%), Attendance Rate (20%), Recurring Donors % (10%)
- Uses YTD/month as monthly giving proxy when MTD=0 (seed data edge case)
- Dashboard stats cache built for all 4 churches
- Grades: A+ (≥90), A (≥80), B+ (≥70), B (≥60), C (≥50), D (≥40), F (<40)

## Key Backend Fixes
- `/api/platform/stats`: Filters TEST_ tenants, returns only real churches with >10 donations
- `/api/platform/activity-feed`: New endpoint — recent large donations + recurring signups
- `/api/platform/transactions`: Search by donor_name added
- `/api/platform/churches`: Full portfolio metrics per church
- `compute_health_score()`: Uses YTD/month proxy when MTD=0

## Test Status
- Iteration 82: 29/29 backend, 95% frontend — God Mode rebuild ✅
- Iteration 81: 100% pass — Final Section W UAT
- Iteration 80: 25/25 backend, 100% frontend

## Credentials
See /app/memory/test_credentials.md

## Remaining Work

### P0 — Immediate:
- Redeploy to solomonai.us (pick up God Mode rebuild + ESLint fix)

### P1:
- Active Donors count for Potter's House/City Reach/EdenX (currently 0 — seed_extended.py doesn't generate person_id cross-referenced with donor records)
- Journey Funnel visualization on Dashboard widget  
- Services Module Expansion (positions, scheduling, CCLI)
- Visual Workflow Builder (drag-and-drop canvas)

### P2 — Future:
- Custom Report Builder (full implementation)
- Commerce multi-payment (Apple/Google Pay live)
- Technical hardening (persistent rate limiting, object storage)
- Production deployment final verification
