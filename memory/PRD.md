# Solomon AI — Product Requirements Document

## Original Problem Statement
Solomon AI is a full-featured, multi-tenant SaaS church management system competing directly with Planning Center. Built with React frontend, FastAPI backend, and MongoDB. The platform features member management, groups, events, worship planning, check-in, giving (SolomonPay scaffolded), media library, cafe/merch ordering, and an AI assistant (Ask Solomon) powered by Claude Sonnet via Emergent LLM Key.

## Architecture
- **Frontend**: React + Shadcn UI (port 3000)
- **Backend**: FastAPI monolith `server.py` ~16K lines (port 8001)
- **Database**: MongoDB Atlas
- **AI**: Claude Sonnet 4.5 via Emergent LLM Key (emergentintegrations)
- **Multi-Tenant**: Organizations -> Campuses (tenants) -> Members

## Key Files
- `/app/backend/server.py` — All API endpoints
- `/app/frontend/src/pages/LandingPage.jsx` — Public marketing page with lead capture
- `/app/frontend/src/pages/GivingDashboard.jsx` — Admin giving module
- `/app/frontend/src/components/SolomonPayForm.jsx` — Reusable SolomonPay payment component
- `/app/frontend/src/components/modals/DonationCheckout.jsx` — Admin donation with SolomonPay
- `/app/frontend/src/pages/portal/PortalGive.jsx` — Member portal giving with SolomonPay
- `/app/frontend/src/pages/portal/PortalCafe.jsx` — Cafe checkout with SolomonPay
- `/app/frontend/src/pages/portal/PortalMerch.jsx` — Merch checkout with SolomonPay
- `/app/planning_center_transcripts/` — Competitor knowledge files

## Completed Features (All Sessions)
- Full member management (People module) with CSV import
- Groups module with enrollment, chat, events
- Calendar/Events with room booking and conflict detection
- Worship/Services planning with song library and team scheduling
- Check-in system with QR codes
- Media library (Watch) with MasterClass-quality streaming
- Abundant Cafe and Merch Store ordering
- Pastoral meeting scheduling
- Solomon Academy (Abundant Pathways) discipleship courses
- War Room real-time dashboard
- Multi-campus management
- Ask Solomon AI chat assistant
- Member portal with giving, groups, events, media access
- Landing page with Frank Luntz-style copywriting
- Snyk-style respectful competitor comparison section
- Mobile hamburger nav and responsive design
- OG tags with Gemini-generated image for iMessage previews
- Quality seed data (12-week attendance streaks, 25 named members, 14 accounts)
- **Competitor Knowledge Base** injection into Ask Solomon (173 PC transcripts + SecureGive + Pushpay)
- **SolomonPay UI Scaffolding** — Payment form component, backend endpoints, integrated into Giving/Cafe/Merch (MOCKED - all transactions pending)
- **Landing Page Lead Capture** — Invicti-style "Request a Demo" modal with lead storage in MongoDB
- **Lead Management** — POST /api/leads/capture (public) + GET /api/admin/leads (admin view)

## SolomonPay Integration Points
- **Giving Module** (Admin + Portal) — Full SolomonPay form replaces old Stripe/PayPal/Venmo/Zelle
- **Cafe Checkout** — SolomonPay payment step before order placement
- **Merch Checkout** — SolomonPay payment step before order placement
- **Status**: ALL transactions stay "pending" — no real payment processing yet

## Pricing Tiers (Solomon AI)
- Starter: $499/mo (up to 500 members, 1 campus)
- Growth: $1,499/mo (up to 5,000 members, 3 campuses)
- Enterprise: $2,999/mo (unlimited everything)

## 3rd Party Integrations
- Anthropic Claude Sonnet 4.5 (Ask Solomon) — Emergent LLM Key
- Gemini Image Gen (OG Tags) — Emergent LLM Key
- Stripe/Pushpay/SecureGive — MOCKED (SolomonPay scaffolded)

## Test Credentials
- Platform Admin: `admin@solomonai.us` / `Demo2026!`
- Church Admin: `shannonnieman1030@gmail.com` / `Demo2026!`
- Church Admin: `jacobpacheco@abundanteast.com` / `Demo2026!`
- Church Member: `member@abundant.church` / `Demo2026!`

## Planning Center Parity Roadmap (12 weeks)

### Phase 1: COMPLETE ✅
- SolomonPay UI Scaffolding
- Landing Page + Lead Capture
- Competitor Knowledge in AI Chat

### Phase 2: Calendar & People (Week 2) — NEXT
- Calendar approval workflows + conflict resolution UI
- People workflows & forms
- Duplicate detection improvements
- Advanced list filtering

### Phase 3: Services Module (Weeks 3-4)
- Plan templates, team/position management
- Song library (without CCLI initially)
- Scheduling system with blockout dates
- Music Stand chord chart viewer

### Phase 4: Groups Module (Week 5)
- Group types/categories, tag organization
- Enrollment workflows (open/closed/request)
- Group events, RSVP, chat scaffolding

### Phase 5: Registrations Module (Week 6)
- Signup wizard, selection types
- Add-ons, custom questions, discounts
- SolomonPay integration for event payments

### Phase 6: Check-Ins Module (Weeks 7-8)
- Station modes, label design
- Medical/allergy alerts, guardian verification
- Printer support (Brother, Citizen, Dymo, Zebra)

### Phase 7: Publishing + Home + Giving Polish (Weeks 9-10)
- Custom page builder, theme customization
- Role-based dashboards
- Pledge campaigns, year-end statements

### Phase 8: Church Center Mobile (Weeks 11-12)
- Event browsing, directory, giving
- Group chat, profile management, push notifications

## Known Constraints
- LLM budget may need top-up (Profile -> Universal Key -> Add Balance)
- `server.py` is ~16K lines — refactor deferred until after demo
- SolomonPay is scaffolded/mocked — not processing live transactions
- 2 test failures in iteration 54 are CloudFlare proxy behavior, not code bugs
