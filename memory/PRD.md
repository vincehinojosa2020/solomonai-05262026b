# Solomon AI — Product Requirements Document

## Original Problem Statement
Multi-tenant church management SaaS — Solomon Pay, God Mode, Bloomberg-grade reporting, Ask Solomon AI, 8 demo churches, ~$108M GMV.

## Architecture
React 18 + FastAPI + MongoDB 7.0 | 575+ endpoints | 89 pages | Claude Sonnet 4.5 + Whisper

## Everything Built (All Verified)

### Core Platform ✅
Full multi-tenant ChMS: People, Giving, Groups, Events, Services, Kids Check-In, Volunteers, Comms, Pathways, Courses, Reports

### P0 Plumbing ✅
Transactions (3M+ enriched), Donors (41K+), Attendance, Church Drill-Through, YTD Revenue

### P1 Public Site ✅
/privacy, /terms, /security, /pricing, forgot-password, God Mode hero, Calendly CTA

### P1 Solomon AI ✅
Streaming SSE, TTS (UK English), PDF generation, PPTX/DOCX scaffold

### P1 SecureGive Parity ✅
Monday Morning Email, Payout Drill-Down, Fund Reconciliation ($108M+)

### P1 CSV Import & Disputes ✅
Planning Center auto-mapping (16 fields), Disputes scaffold, Fraud Risk Scoring

### P2 Security ✅
Tenant isolation (40 endpoints), CORS lockdown, Session TTL 24h

### P3 Polish ✅
Component splitting, WCAG AA accessibility, Mobile responsiveness

### Demo Mode Toggle ✅
Live Data / New Church toggle with 6-step Setup Checklist

### Data Integrity ✅
100% person_id cross-referencing across all 8 tenants

### Stripe Connect Integration ✅ (NEW)
- Feature-flagged via `STRIPE_LIVE` env variable (false = Solomon Pay demo, true = real Stripe)
- Real Stripe Checkout Sessions with platform fee (1.9% + $0.30)
- `payment_transactions` collection for tracking all payments
- Webhook handler for payment_intent.succeeded/failed and charge.dispute.created
- Status polling endpoint for payment verification
- Receipt email via Resend on successful payment
- Frontend: dual "Solomon Pay" + "Stripe" buttons on Give page
- **To go live**: Set `STRIPE_LIVE=true` in backend/.env

## Documentation
- Platform Audit: `/app/SOLOMON_AI_PLATFORM_AUDIT.md`
- UI Guide: `/app/SOLOMON_AI_UI_GUIDE.md`

## Remaining Backlog
- Apple/Google Pay (via Stripe Payment Request Button)
- Custom Report Builder
- ElevenLabs TTS
- PPTX/DOCX generation
