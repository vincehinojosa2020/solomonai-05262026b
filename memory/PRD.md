# Solomon AI — Product Requirements Document

## Original Problem Statement
SOLOMON AI — Full-parity church management SaaS with proprietary payment processor (Solomon Pay). Competing with Planning Center, Church Center, SecureGive, and Pushpay. Building to demonstrate to co-founders with real revenue data.

## Phase Completion Status

| Phase | Status | Key Deliverables |
|-------|--------|-----------------|
| 1 | COMPLETE | Landing page, Login, White-labeling, SolomonPay branding |
| 2 | COMPLETE | Demo data, Recurring Giving, Goals, Custom Fields |
| 3 | COMPLETE | Groups Q&A, Tax Statements, Payment Methods, Onboarding |
| 4 | COMPLETE | SolomonPay Admin (8 tabs), RBAC (12 roles), Real-time Polling, Academy |
| 5 | COMPLETE | DonorIQ, Virtual Terminal, Refunds, QR Codes, Cover Fees |
| 6 | COMPLETE | Ask Solomon Agentic AI — Voice + 7 Action Types + Confirmation UI |
| 7 | COMPLETE | KidsCheckinAdmin refactor |
| 8 | COMPLETE | Twilio SMS + WebSocket + Printer scaffolding |
| 9 | COMPLETE | Final validation |
| CQ | COMPLETE | Code Quality Recommendations (security, hooks, keys, mutable defaults) |

## Recent Changes (April 2, 2026)

### Code Quality Fixes (CQ Phase)
- **Python Mutable Default Arguments**: Fixed `admin_services.py` (`payload: dict = {}` → `dict = None`) and `public_api.py` (`recipient_ids: List[str] = []` → `Optional[List[str]] = None`)
- **Insecure Random Replaced**: `platform.py` and `volunteer.py` use `SystemRandom` instead of `random`; `solomon_actions.py` uses `secrets.choice` for pickup codes
- **React Hook Dependencies**: Wrapped fetch functions in `useCallback` for `PortalWatch.jsx`, `PortalPrayer.jsx`; added missing deps to `SolomonPayForm.jsx`
- **Array Index Keys**: Fixed in `Dashboard.jsx`, `GivingDashboard.jsx`, `PortalWatch.jsx`, `PortalLibrary.jsx`, `PortalLessonViewer.jsx`, `PortalDirectory.jsx`
- **Hardcoded Secrets**: Replaced in 5 test files with `os.getenv()` (done in previous session)

### Revenue Infrastructure
- **3-Year Giving History**: 537K+ transactions across 8 churches, ~$82M total volume
- **Processing Fee**: 2.2% + $0.22 per transaction (25% below industry 2.9% + $0.30)
- **Godmode Revenue Dashboard**: Platform admin sees total volume, fees earned, per-church/per-year breakdown, monthly trend

### Services Overhaul
- Removed test/CRUD plans, seeded 16 realistic services
- Added 10 templates (Christmas Eve, Easter, Thanksgiving, etc.)
- Added "Publish" button for draft plans (Draft → Published → Live → Completed)

### GitHub-Style "How It Works" Tutorials
Added to 9 admin sections: Services, Groups, Events, Giving, People, Volunteers, Registrations, Communications, Kids Check-In

### Feature Removals
- Pastoral Meetings, Prayer Requests (admin), Leadership Notes

## Architecture
```
Backend: FastAPI + MongoDB (35+ route files, 4 service files)
Frontend: React + Shadcn/UI (46 admin pages, 20 portal pages)
AI: Claude (via Emergent LLM Key) with structured action parsing
Payments: Solomon Pay (proprietary, 2.2% + $0.22)
```

## Test Status
- Iteration 75: 100% pass (Backend 20/20, Frontend 100%) — Code Quality Regression
- Iterations 72-74: All 100% pass
- Total test iterations: 7 (all passing)

## Credentials
- Platform Admin (Godmode): admin@solomonai.us / Demo2026!
- Church Admin: shannonnieman1030@gmail.com / Demo2026!
- Portal Member: member@abundant.church / Demo2026!

## MOCKED Integrations
- Stripe: Donations stay "pending" until regulatory approval
- Twilio SMS: Logs to DB, ready for live keys
- Printer: Preview mode, ZPL generation ready

## Remaining/Deferred
- P2: Refactor oversized components (KidsCheckinAdmin.jsx, CheckInSetupPage.jsx, AbundantPathwaysAdmin.jsx, GroupDetail.jsx, GivingDashboard.jsx, AppShell.jsx, SolomonChat.jsx, core/seed.py, core/helpers.py)
- Solomon AI admin-side actions (create service plans, add children via voice)
- Native mobile app (iOS/Android)
- Apple Pay / Google Pay
- ACH bank transfers
- Monday summary emails
