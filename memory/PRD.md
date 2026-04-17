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
- **API Routes**: 575+ registered endpoints across 34 route files

## What's Been Implemented

### Phase 1-14 Core Platform (DONE)
- Full multi-tenant church management system
- Solomon Pay payment processing (simulated)
- God Mode with aggregated platform stats and caching
- Solomon AI sidebar with McKinsey persona
- Bloomberg-grade reports, 3-year historical data for 8 churches

### P0 Plumbing Fixes (April 17, 2026) — ALL DONE
- FIX 1: Transactions enriched with person names (3M+ records)
- FIX 2: Donors module with by_campus, recurring_donors (41K+ donors)
- FIX 3: Attendance page loading with seeded services
- FIX 4: Church Detail Drill-Through page
- FIX 5: YTD Revenue calculation bug
- FIX 10: Team section removed from public site

### P1: Public Site Polish (April 17, 2026) — ALL DONE
- FIX 6: Login autocomplete="off"
- FIX 7: /privacy, /terms, /security pages
- FIX 8: Dynamic copyright year
- FIX 9: God Mode KPI screenshot on landing hero
- FIX 11: /pricing page
- FIX 12: Calendly CTA + forgot password flow

### P1: Ask Solomon AI Upgrade (April 17, 2026) — ALL DONE
- Streaming SSE responses (/api/solomon/chat/stream)
- TTS button (UK English Web Speech API)
- PDF generation via reportlab
- PPTX/DOCX scaffolded with honest "Coming Soon"

### P1: Stripe/SecureGive Parity (April 17, 2026) — ALL DONE
- Monday Morning Summary Email (/api/platform/send-summary-email)
- Payout Drill-Down (constituent transactions)
- Fund Reconciliation (/api/platform/funds/reconciliation)

### P1: CSV Import & Stripe Scaffold (April 17, 2026) — ALL DONE
- CSV Import with Planning Center auto-mapping (address fields, 16 system fields)
- Stripe Fraud Risk Scoring scaffold (/api/platform/fraud/risk-scores)
- Disputes/Chargebacks scaffold (/api/platform/disputes)

### P2: Security Hardening (April 17, 2026) — ALL DONE
- DEFAULT_TENANT_ID eliminated from ~40 endpoints in public_api.py and reports.py
- _resolve_tenant() helper derives tenant from authenticated user session
- CORS locked down from wildcard to domain whitelist + preview regex
- Session TTL: 24-hour expiry on all session tokens
- Password reset flow via Resend email

### P3: Polish (April 17, 2026) — ALL DONE
- Mobile responsiveness: Landing page hamburger menu, responsive grid stacking
- Accessibility: aria-labels on login inputs, role="navigation" on sidebar, role="banner" on hero
- Footer links: Privacy, Terms, Security, Calendly CTA all wired

## Pending / Remaining Tasks

### P2 — Technical Debt
- Fix donation person_id cross-referencing (0% match for newer tenants)
- Session cleanup background task (currently tokens are deleted on expiry check)

### P3 — Backlog
- Split oversized components (KidsCheckinAdmin 808 lines, CheckInSetupPage 737 lines)
- WCAG AA full accessibility audit
- Mobile responsiveness for admin dashboard pages
- Apple/Google Pay live integration (currently mocked)
- Custom Report Builder full implementation

## Audit Document
Full 14-section platform audit available at `/app/SOLOMON_AI_PLATFORM_AUDIT.md`

## Technical Notes
- **Rate limiting**: Disabled for demo
- **Solomon Pay**: Mock processor — `sim_ch_` prefix on all transactions
- **CORS**: Locked to preview domain + solomonai.us + regex for preview environments
- **Session TTL**: 24 hours, checked on every authenticated request
- **Tenant isolation**: All endpoints now resolve tenant from user session
