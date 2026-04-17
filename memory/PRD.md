# Solomon AI — Product Requirements Document

## Original Problem Statement
SOLOMON AI — MASTER BUILD DIRECTIVE. A nationwide SaaS church management platform featuring Solomon Pay, God Mode multi-campus oversight, Bloomberg-grade reporting, "Ask Solomon" AI intelligence, and demo-ready data seeding for 8 church tenants simulating ~$100M+ in GMV.

## Core Architecture
- **Frontend**: React 18, Tailwind CSS, shadcn/ui, Recharts (Port 3000)
- **Backend**: FastAPI, Motor async MongoDB driver (Port 8001)
- **Database**: MongoDB 7.0, 64 collections, `solomonai` database
- **AI**: Claude Sonnet 4.5 via Emergent LLM Key + OpenAI Whisper
- **Payments**: Solomon Pay (proprietary, mock adapter for demo)
- **Email**: Resend API (configured, sandbox key)

## What's Been Implemented

### Phase 1-14 Core Platform (DONE)
- Full multi-tenant church management (575 API endpoints, 89 frontend pages)
- Solomon Pay payment processing (simulated)
- God Mode with aggregated platform stats and caching
- Solomon AI sidebar with McKinsey persona
- Bloomberg-grade reports
- 3-year historical data seeded for 8 churches

### P0 Plumbing Fixes (April 17, 2026) — ALL DONE
- FIX 1: Transactions enriched with person names (3M+ records)
- FIX 2: Donors module with by_campus, recurring_donors (41K+ donors)
- FIX 3: Attendance page loading with seeded services
- FIX 4: Church Detail Drill-Through (giving chart, members, health score)
- FIX 5: YTD Revenue calculation bug
- FIX 10: Team section removed from public site

### P1: Public Site Polish (April 17, 2026) — ALL DONE
- FIX 6: Login autocomplete="off" on email/password inputs
- FIX 7: /privacy, /terms, /security pages with full content
- FIX 8: Dynamic copyright year in footer (login + landing)
- FIX 9: God Mode screenshot on landing hero (KPI cards)
- FIX 11: /pricing page (4 tiers: $499-$2K+)
- FIX 12: Calendly CTA in footer, forgot password flow (/forgot-password)

### P1: Ask Solomon AI Upgrade (April 17, 2026) — ALL DONE
- Streaming responses via SSE (POST /api/solomon/chat/stream)
- Text-to-Speech (Web Speech API with UK English voice preference)
- TTS button on assistant messages
- PDF generation via reportlab (POST /api/solomon/generate-deliverable)
- PPTX/DOCX scaffolded with honest "Coming Soon" per Honesty Pact
- Report generation (markdown, CSV, PDF formats)

### P1: Stripe/SecureGive Parity (April 17, 2026) — ALL DONE
- Monday Morning Platform Summary Email (POST /api/platform/send-summary-email)
- Payout Drill-Down (click payout → see constituent transactions)
- Fund Reconciliation View (GET /api/platform/funds/reconciliation) — 7 funds, $108M+ total

### Earlier Features (DONE)
- Give Page: Solomon Pay flow, saved card, cover fees
- Giving Streak: 14-week badge with Luntz copy
- Cover Processing Fees & Round Up in all checkout flows
- Watch Page: Dark Masterclass theme
- Multi-campus aggregate dashboards
- Flat Cafe/Merch navigation

## Pending / Upcoming Tasks

### P1 — Remaining
- CSV Import wizard for Planning Center migrations (battle-test with real data)
- Stripe parity scaffold (Fraud risk scoring, Disputes/Chargebacks UI)

### P2 — Future
- Custom Report Builder full implementation + PDF export
- Apple/Google Pay live integration (currently mocked)
- Fix DEFAULT_TENANT_ID hardcoding in public_api.py and reports.py
- CORS lockdown (currently wildcard *)
- Session TTL (tokens never expire currently)

### P3 — Backlog
- Split oversized components (KidsCheckinAdmin, CheckInSetupPage)
- Fix donation person_id cross-referencing (0% match for newer tenants)
- WCAG AA accessibility audit
- Mobile responsiveness for admin pages

## Technical Notes
- **Rate limiting**: Disabled for demo (DO NOT re-enable without per-route config)
- **Solomon Pay**: Mock processor — `sim_ch_` prefix on all transaction IDs
- **Caching**: `platform_stats_cache` (15min TTL), `platform_donors_cache` (30min TTL)
- **Auth**: Session tokens + bcrypt/SHA256 hybrid, Google OAuth via Emergent Auth
- **575 registered API routes** across 33 route files
