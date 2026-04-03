# Solomon AI — CHANGELOG

## April 3, 2026 — Sprint Blocks 1A–2E

### Block 1A: Stripe Complete Removal
- Eliminated ALL Stripe references (variables, field names, CSS, text, API keys, backend routes)
- `showStripeCheckout` → `showDonationCheckout` in GivingDashboard
- `stripe_payment_method_id` → `solomonpay_token` in PortalMe, OnboardingFlow, portal.py, schemas.py
- Updated SettingsPage, IntegrationsPage, SupportPage, PricingPage to reflect Solomon Pay
- Removed STRIPE_API_KEY and STRIPE_PUBLISHABLE_KEY from backend/.env
- CSS: `.icon-box.stripe` → `.icon-box.solomonpay`

### Block 1B: Recurring Giving Background Scheduler
- Created `/app/backend/services/recurring_scheduler.py`
  - Runs every hour via asyncio background task
  - Idempotency guard: `last_processed_date` prevents double-charging
  - Retry logic: 3 attempts → auto-pause after 3 consecutive failures
  - Logs every run to `recurring_giving_runs` collection
- Endpoints: scheduler/status, scheduler/run-now, scheduler/resume/{id}
- SolomonPay Admin Recurring tab revamped with scheduler dashboard

### Block 2A: Kids Check-In Printer Integration
- LabelPrinter.jsx: web-print child/parent/allergy labels
- KioskCheckin.jsx: full-screen kiosk mode with PIN exit
- Printers tab + Launch Kiosk Mode in CheckInSetupPage
- Backend: family-lookup endpoint for kiosk phone search
- labels.css: print-optimized DYMO/Brother/standard label styles

### Block 2B: Contextual Help System
- HelpTooltip.jsx: reusable help button with sliding panel
- helpContent.js: 30+ feature help entries
- Added HelpTooltip to all major admin pages
- Solomon AI system prompt updated with feature guide

### Block 2C: Calendar & Events Expansion
- FullCalendar installed (@fullcalendar/react, daygrid, timegrid, interaction, core)
- CalendarPage.jsx: full Month/Week/Day views with drag-reschedule
- Event type color-coding, filtering, recurring events, paid registration
- New endpoints: /admin/events/calendar, /admin/events/{id}/clone
- Calendar added to AppShell navigation

### Block 2D: Communications Upgrade
- 5 built-in email templates with merge fields
- Template CRUD endpoints added to admin_comms.py
- Twilio SMS setup banner in CommunicationsPage
- Merge field quick-insert buttons in compose
- Scheduled comms cancel API

### Block 2E: Google OAuth
- Google Sign-In button on LoginPage
- AuthCallback: role-based routing + session_token storage
- auth/session endpoint returns role + session_token

## New DB Collections
- `recurring_giving_runs`, `email_templates`

## New Files
- /app/backend/services/recurring_scheduler.py
- /app/frontend/src/components/LabelPrinter.jsx
- /app/frontend/src/components/KioskCheckin.jsx
- /app/frontend/src/components/HelpTooltip.jsx
- /app/frontend/src/lib/helpContent.js
- /app/frontend/src/pages/CalendarPage.jsx
- /app/frontend/src/styles/labels.css
