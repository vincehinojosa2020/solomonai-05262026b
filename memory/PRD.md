# Solomon AI — Product Requirements Document

## Original Problem Statement
SOLOMON AI — MASTER BUILD DIRECTIVE. A nationwide SaaS church management platform featuring Solomon Pay (proprietary payment processor), God Mode multi-campus oversight, Bloomberg-grade reporting, "Ask Solomon" AI intelligence, and demo-ready data seeding for 8 church tenants simulating ~$100M+ in GMV.

## Core Architecture
- **Frontend**: React 18 on port 3000 (Supervisor)
- **Backend**: FastAPI on port 8001 (Supervisor)
- **Database**: MongoDB via Motor (async)
- **AI**: Claude Sonnet 4.5 (McKinsey persona) + OpenAI Whisper (voice)
- **Payments**: Solomon Pay (proprietary, mock adapter for demo)

## User Personas
1. **Platform Admin** (`admin@solomonai.us`) — God Mode across all tenants
2. **Church Admin / Founder** (`shannonnieman1030@gmail.com`, `jacobpacheco@abundanteast.com`) — God Mode across 3 Abundant campuses
3. **Church Member** (`member@abundant.church`) — Portal access, giving, cafe, merch, events, kids check-in

## Campuses (Abundant Church)
- **Abundant East** (`abundant-east-001`) — 22,000 members
- **Abundant West** (`abundant-west-001`) — 14,000 members
- **Abundant Downtown** (`abundant-downtown-001`) — 18,500 members
- **Total**: 54,500 members across 3 campuses + 5 other churches

## What's Been Implemented

### Phase 1-14 Core Platform (DONE)
- Full multi-tenant church management system
- Solomon Pay payment processing (card, ACH, tokenization, refunds)
- God Mode with aggregated platform stats and caching
- Solomon AI sidebar (McKinsey persona, Whisper voice, PDF/CSV reports)
- Bloomberg-grade reports (Giving, Attendance, Membership, Groups)
- 3-year historical data seeded for all campuses
- Rate limiting completely disabled for demo
- Authentication for all demo accounts

### Recent Updates (April 2026)
- **Give Page**: Full Solomon Pay flow — select amount, saved card (Visa ****4242), cover fees, one-tap give
- **Giving Streak**: 14-week streak badge with Luntz copy
- **Cover Processing Fees**: All checkout flows (Give, Cafe, Merch)
- **Round Up Feature**: Cafe & Merch
- **Watch Page**: Dark Masterclass theme, 3 videos by Pastor Charles Nieman
- **Portal Nav**: Flat Cafe/Merch links (no dropdown)
- **All Campuses Aggregate**: 54,500+ total members
- **Demo Modals**: Suppressed for all demo accounts

### P0 Plumbing Fixes (April 17, 2026) — ALL DONE
- **FIX 1**: Transactions Tab — enriched 3M+ donations with person names/emails from people collection. Shows full table with donor, church, amount, fund, fee, status columns.
- **FIX 2**: Donors Module — fixed recurring_donors count (from recurring_giving collection), computed by_campus breakdown from per-donor aggregation. Shows 41K+ total donors.
- **FIX 3**: Attendance Page — seeded services & service_types for active tenant IDs (abundant-east/west/downtown). Page now loads 156+ services with headcounts.
- **FIX 4**: Church Detail Drill-Through — NEW endpoint `/api/platform/churches/{tenant_id}/detail` + `ChurchDetail.jsx` component. Shows 12-month giving chart, top donors, member roster, health score, recent transactions.
- **FIX 5**: YTD Revenue calculation bug (fixed earlier)
- **FIX 10**: Removed Team section from public site (fixed earlier)

## Pending / Upcoming Tasks

### P1 — Public Site & Security Polish (FIX 6-9, 11-12)
- Clear pre-filled login email (`autocomplete="off"`)
- Build `/privacy`, `/terms`, `/security` pages
- Update copyright to dynamic year
- Add God Mode screenshot to hero
- Build `/pricing` page
- Wire Calendly CTA and forgot password flow

### P1 — Ask Solomon AI Upgrade
- Streaming responses (Anthropic stream:true)
- Text-to-Speech (English UK voice)
- PPTX/DOCX/PDF generation scaffold
- MCP tool architecture scaffold

### P1 — Stripe/SecureGive Parity
- Monday Morning Platform Summary Email
- Payout Drill-Down (click payout → see every transaction)
- Fund reconciliation view & Fund-specific direct links
- CSV Import wizard for Planning Center migrations
- Stripe parity scaffold (Fraud risk scoring, Disputes/Chargebacks UI)

### P2 — Future
- Custom Report Builder full implementation & PDF export
- Apple/Google Pay live integration (currently mocked)

### P3 — Backlog
- Split oversized components (`KidsCheckinAdmin.jsx`, `CheckInSetupPage.jsx`)

## Technical Notes
- **Rate limiting**: Completely disabled (DO NOT re-enable)
- **Solomon Pay**: Mock processor adapter for demo — always returns success
- **God Mode caching**: `platform_stats_cache` prevents MongoDB timeouts on 3M+ records
- **Dashboard stats**: Uses `dashboard_stats_cache` for member counts
- **Giving History**: Uses `people.id` (not `user_id`) as `person_id` in donations collection
- **Donor stats caching**: `platform_donors_cache` caches donor analytics for 30 minutes
