# Solomon AI — Product Requirements Document

## Original Problem Statement
SOLOMON AI — FULL PARITY CONFIRMATION + GAP CLOSURE against Planning Center, SecureGive, and Church Center. Multi-phase "MASTER BUILD PROMPT" for production deployment and demo preparation.

## Core Requirements
- 100% functional parity with Planning Center, Church Center, and SecureGive
- NO Publishing (page builder) and NO Church Center Mobile API sync
- SolomonPay admin dashboard and portal giving enhancements
- Phase 1-9 Master Build Execution

## Architecture
```
/app/
├── backend/
│   ├── server.py             # Entry point
│   ├── core/                 # helpers.py, seed.py, auth.py, __init__.py (RBAC)
│   ├── models/               # schemas.py
│   ├── routes/               # 30+ domain files
│   │   ├── solomonpay_admin.py  # SolomonPay Admin Dashboard (NEW)
│   │   ├── portal.py            # Member portal routes
│   │   ├── courses.py           # Academy courses (6 seeded)
│   │   └── ...
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── SolomonPayAdmin.jsx  # 8-tab admin dashboard (NEW)
│   │   │   ├── portal/
│   │   │   │   ├── PortalGroups.jsx   # Group detail/Q&A/Notify
│   │   │   │   ├── PortalGive.jsx     # Tax statement download
│   │   │   │   ├── PortalMe.jsx       # Payment methods tab
│   │   │   │   └── ...
│   │   ├── components/
│   │   │   ├── OnboardingFlow.jsx     # First sign-in (NEW)
│   │   │   └── ...
│   │   ├── hooks/
│   │   │   └── usePolling.js          # Real-time sync
```

## Phase Completion Status

### Phase 1 ✅ COMPLETE — Demo Blockers
- Landing page rewrite, Login UI cleanup, Password visibility
- Admin White-labeling, DemoWalkthrough sessionStorage
- SolomonPay branding system-wide

### Phase 2 ✅ COMPLETE — Demo Data
- 171 donations for Shannon Nieman (4 years)
- 10 sermons by Pastor Charles Nieman
- Premium Unsplash images for Merch/Cafe
- Recurring Giving, Goals, Custom Fields, Registration Add-ons

### Phase 3 ✅ COMPLETE — Member Portal Polish
- Group Enhancements: Detail overlay, Q&A submissions, "Get Notified" toggle
- Tax Statement Download: Year selector (2024-2027), PDF generation
- Stored Payment Methods: Add/view/delete/set-default cards in PortalMe
- First Sign-In Onboarding: 3-step modal (Profile, Payment, Notifications)

### Phase 4 ✅ COMPLETE — SolomonPay Admin Dashboard
- **Main Dashboard**: Today/Week/Month/YTD stats, 12-month trend chart, recent 20 transactions
- **Transactions**: Full list, search, date/fund filters, CSV export, pagination
- **Payouts**: Available balance, instant (1.5% fee) / standard (free) payouts, history
- **Funds**: CRUD management, goal tracking, progress bars
- **Recurring**: Integrated AdminRecurringGiving component
- **Donors**: 187 donors, search, click-into detail (by year, by fund, giving history)
- **Statements**: Year-end bulk generation, results display
- **Settings**: Payout schedule, fee display, receipt emails, bank account placeholder
- **RBAC**: 12 roles (member, kids_volunteer, small_group_leader, cafe_manager, merch_manager, worship_media_team, finance, staff, ministry_leader, senior_pastor, executive_pastor, church_admin, platform_admin)
- **Real-Time Sync**: Polling (5s giving/transactions, 10s registrations/groups, 30s content)
- **Academy Courses**: 6 courses seeded (Becoming a Member, Why We Give, What is Baptism, Premarital Counseling, Food Pantry Volunteer, First-Time Volunteers)

## Remaining Phases

### Phase 5 (P0) — SecureGive & Church Center Research
- Web search SecureGive features/screenshots/pricing
- Document Church Center member-facing features
- Identify gaps → build them

### Phase 6 (P1) — Ask Solomon Agentic AI
- Voice-activated actions
- AI chatbot enhancements

### Phase 7 (P1) — Refactoring
- KidsCheckinAdmin.jsx refactor (1028 lines → split)

### Phase 8 (P2) — Infrastructure
- Twilio SMS integration
- WebSocket for real-time (replace polling)
- Printer scaffolding for check-in labels

### Phase 9 (P2) — Final Parity Verdict
- Full feature comparison matrix
- GO/NO-GO decision

## 3rd Party Integrations
- Anthropic Claude (Ask Solomon) — Emergent LLM Key
- Stripe (SolomonPay) — Test keys in .env (MOCKED for demo)
- Emergent Google Auth — Managed Service

## Test Credentials
- Platform Admin: admin@solomonai.us / Demo2026!
- Church Admin: shannonnieman1030@gmail.com / Demo2026!
- Portal Member: member@abundant.church / Demo2026!

## Key Decisions
- "Solomon Pay" → "SolomonPay" (capital P, no space)
- Database: test_database (not solomonai)
- Payments are MOCKED for demo purposes
- Polling preferred over WebSockets for Phase 4 (WebSocket deferred to Phase 8)
