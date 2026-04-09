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
- 2026 donations (20,864+ records) seeded
- Rate limiting completely disabled for demo
- Authentication for all 4 demo accounts

### Recent Updates (April 2026)
- **Watch Page**: Dark Masterclass theme (black background), 3 videos by Pastor Charles Nieman
- **Portal Nav**: Flat Cafe/Merch links (no dropdown)
- **Saved Card Checkout**: Cafe, Merch, and Events use saved Visa ****4242
- **Tithe/Offering Prompts**: Frank Luntz-style persuasive copy on Cafe and Merch checkout
  - Cafe: "While you're here..." warm amber card
  - Merch: "You're already investing in something you believe in."
- **All Campuses Aggregate**: Shannon/Jacob see 35,331 total members across 3 campuses
- **Abundant Downtown**: Renamed from "Abundant Northeast"
- **Demo Modals**: Suppressed for all demo accounts (onboarding, walkthrough)
- **Kids Check-In**: Reset for demo account

## Pending / Upcoming Tasks

### P1 — Upcoming
- Implement "Founder Role" unified multi-campus dashboard for Shannon/Jacob
- Schedule automated weekly platform summary email (GMV/MRR to founders)

### P2 — Future
- Custom Report Builder + PDF export
- Apple/Google Pay live integration (currently mocked)

### P3 — Backlog
- Split oversized components (`KidsCheckinAdmin.jsx` 794 lines, `CheckInSetupPage.jsx` 704 lines)

## Key API Endpoints
- `GET /api/admin/dashboard/aggregate` — Multi-campus aggregate stats
- `POST /api/solomonpay/process` — Process payment via Solomon Pay
- `GET /api/portal/payment-methods` — Saved payment methods
- `GET /api/portal/media/videos` — Watch page videos
- `POST /api/solomon/transcribe` — Whisper voice transcription
- `POST /api/solomon/generate-report` — AI report generation
- `GET /api/reports/*` — Bloomberg-grade reports

## Technical Notes
- **Rate limiting**: Completely disabled (DO NOT re-enable)
- **Solomon Pay**: Uses mock processor adapter for demo
- **God Mode caching**: `platform_stats_cache` prevents MongoDB timeouts on 3M+ records
- **Dashboard stats**: Uses `dashboard_stats_cache` collection for member counts
