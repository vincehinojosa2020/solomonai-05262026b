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
- **Abundant East** (`abundant-east-001`) — 12,847 members
- **Abundant West** (`abundant-west-001`) — 11,563 members
- **Abundant Downtown** (`abundant-downtown-001`) — 10,921 members
- **Total**: 35,331 members across 3 campuses

## What's Been Implemented

### Phase 1-14 Core Platform (DONE)
- Full multi-tenant church management system
- Solomon Pay payment processing (card, ACH, tokenization, refunds)
- God Mode with aggregated platform stats and caching
- Solomon AI sidebar (McKinsey persona, Whisper voice, PDF/CSV reports)
- Bloomberg-grade reports (Giving, Attendance, Membership, Groups)
- 3-year historical data seeded for all campuses
- Rate limiting completely disabled for demo
- Authentication for all 4 demo accounts

### Recent Updates (April 2026)
- **Give Page**: Full Solomon Pay flow — select amount, saved card (Visa ****4242), cover fees, one-tap give. Payment processes and shows success toast.
- **Giving Streak**: 14-week streak badge with Luntz copy: "That's not a habit — that's a lifestyle. 14 consecutive weeks of faithfulness."
- **Cover Processing Fees**: All checkout flows (Give, Cafe, Merch) show "I'd like to cover the processing fee — 100% of your gift reaches the church. Not one penny lost."
- **Round Up Feature**: Cafe & Merch — "Small change, big kingdom impact." Appears when total has cents.
- **Tithe/Offering Prompts**: Frank Luntz copy on Cafe ("While you're here...") and Merch ("You're already investing in something you believe in.")
- **Watch Page**: Dark Masterclass theme, 3 videos by Pastor Charles Nieman
- **Portal Nav**: Flat Cafe/Merch links (no dropdown)
- **All Campuses Aggregate**: 35,331 total members across 3 campuses
- **Abundant Downtown**: Renamed from "Abundant Northeast"
- **Demo Modals**: Suppressed for all demo accounts

## Pending / Upcoming Tasks

### P1 — Upcoming
- Implement "Founder Role" unified multi-campus dashboard for Shannon/Jacob
- Schedule automated weekly platform summary email (GMV/MRR to founders)

### P2 — Future
- Custom Report Builder + PDF export
- Apple/Google Pay live integration (currently mocked)

### P3 — Backlog
- Split oversized components (`KidsCheckinAdmin.jsx`, `CheckInSetupPage.jsx`)

## Technical Notes
- **Rate limiting**: Completely disabled (DO NOT re-enable)
- **Solomon Pay**: Mock processor adapter for demo — always returns success
- **God Mode caching**: `platform_stats_cache` prevents MongoDB timeouts on 3M+ records
- **Dashboard stats**: Uses `dashboard_stats_cache` for member counts
- **Giving History**: Uses `people.id` (not `user_id`) as `person_id` in donations collection
