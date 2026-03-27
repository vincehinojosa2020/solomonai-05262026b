# Solomon AI — Product Requirements Document

## Original Problem Statement
Solomon AI is a full-featured, multi-tenant SaaS church management system designed to replace Planning Center. Built with React frontend, FastAPI backend, and MongoDB. The platform features member management, groups, events, worship planning, check-in, giving (scaffolded), media library, cafe/merch ordering, and an AI assistant (Ask Solomon) powered by Claude Sonnet via Emergent LLM Key.

## Architecture
- **Frontend**: React + Shadcn UI (port 3000)
- **Backend**: FastAPI monolith `server.py` ~16K lines (port 8001)
- **Database**: MongoDB Atlas
- **AI**: Claude Sonnet 4.5 via Emergent LLM Key (emergentintegrations)
- **Multi-Tenant**: Organizations -> Campuses (tenants) -> Members

## Key Files
- `/app/backend/server.py` — All API endpoints
- `/app/frontend/src/pages/LandingPage.jsx` — Public marketing page
- `/app/frontend/src/pages/GivingDashboard.jsx` — Giving module UI
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
- Giving platform scaffold (Solomon Pay/Pushpay/SecureGive toggles)
- **Competitor Knowledge Base injection into Ask Solomon** (173 PC video transcripts + SecureGive + Pushpay analysis) — COMPLETED March 2026

## Competitor Knowledge Integration (Latest)
- Scraped 173 Planning Center University training videos
- Created analysis files: `knowledge_base.txt`, `securegive_analysis.txt`, `pushpay_analysis.txt`
- Combined into `competitor_knowledge_combined.txt` (30,516 chars / ~7,600 tokens)
- Loaded at server startup and injected into Solomon Chat system prompt
- Ask Solomon can now answer detailed migration, comparison, and pricing questions
- Verified with testing agent (Iteration 53: 8/10 pass, 2 failures due to LLM budget limit)

## Pricing Tiers (Solomon AI)
- Starter: $99/mo (single campus, core features)
- Growth: $1,499/mo (multi-campus, all features)
- Enterprise: $2,999/mo (unlimited everything)

## 3rd Party Integrations
- Anthropic Claude Sonnet 4.5 (Ask Solomon) — Emergent LLM Key
- Gemini Image Gen (OG Tags) — Emergent LLM Key
- Stripe/Pushpay/SecureGive — MOCKED

## Test Credentials
- Platform Admin: `admin@solomonai.us` / `Demo2026!`
- Church Admin: `shannonnieman1030@gmail.com` / `Demo2026!`
- Church Admin: `jacobpacheco@abundanteast.com` / `Demo2026!`

## Upcoming Tasks (Post-Demo)
- P1: Modular monolith refactor of `server.py` (extract domains into routers) — DEFERRED
- P2: N+1 query optimization in `courses.py`
- P2: Real Pushpay/SecureGive API integration
- P2: Excel (.xlsx) support for Member Import
- P2: PDF Certificate generation for Solomon Academy
- P2: Real Twilio SMS / Stripe integration

## Known Constraints
- LLM budget may need top-up (Profile -> Universal Key -> Add Balance)
- `server.py` is ~16K lines — refactor deferred until after demo
- Giving module is scaffolded/mocked, not processing live transactions
