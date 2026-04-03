# Solomon AI — CHANGELOG

## April 3, 2026 — Sprint Blocks 1A–2E (Earlier session)
See CHANGELOG_SPRINT1.md for details

## April 3, 2026 — Ultimate Build Directive (This session)

### Section B: 19 UAT Bug Fixes
- B.1: Fixed $NaN in God Mode Payout History — backend normalizes gross_amount/total_fees/net_payout from DB fields
- B.2/B.3: Fixed NaN% of goal on Dashboard — guarded mtd_goal division + backend returns sensible default from ytd/12
- B.4: Fixed hardcoded "Abundant Church" on Give page → dynamic tenant name
- B.5: Fixed hardcoded "Abundant Church" on Groups page → dynamic tenant name
- B.6: Fixed duplicate Cafe images — 20 items now have distinct Unsplash photo URLs
- B.7: Fixed All Churches KPI showing 0 — PlatformDashboard now sends auth headers to /platform/stats
- B.8: Fixed God Mode sidebar showing "Abundant East" — now shows "Solomon AI" for platform_admin
- B.9: Removed Pushpay/SecureGive integration cards from Giving Dashboard → clean Solomon Pay status card
- B.10: Payment form now masks card input with encryption notice
- B.11: Watch page background changed from black (#0a0a0a) to light (#f8fafc) to match design system
- B.12: Tax statement buttons hidden when YTD = $0 (shows "Statements available after your first gift")
- B.13: Group icon buttons already had title attributes — verified
- B.14: "Legacy View" renamed to "Previous Dashboard" with tooltip
- B.15: Admin/Member toggle buttons have descriptive title tooltips
- B.16: Removed duplicate "Preview Member Portal" text link — toggle button is sufficient
- B.17: Services empty state improved with descriptive copy + "See How It Works" button
- B.18: Dashboard KPI cards now have "View details →" links to relevant pages
- B.19: Portal nav grouped: Shop ▾ (Cafe+Merch) and Learn ▾ (Watch+Courses) — max 6 visible items

### Section C/D: Branding + Integrations Cleanup
- God Mode sidebar now shows "Solomon AI" for platform admins
- IntegrationsPage: Removed Pushpay, Tithely, SecureGive, Slack, Teams from all listings
- IntegrationsPage: Reorganized into 5 categories: Communication, Media & Worship, Automation, Authentication, Compliance
- PROCESSORS list: Solomon Pay + Cash & Check only (no competitors)
- Backend admin_settings.py: PAYMENT_PROCESSORS cleaned to 2 entries

### Section E: Multi-Campus UX
- Created `/api/portal/campuses` — detects multi-campus by name prefix, returns campus list
- Created `/api/portal/campus/select` — saves home campus to user profile
- Created `CampusSelectorModal.jsx` — shows on first portal login for multi-campus churches
- PortalLayout: `getChurchDisplayName()` strips campus suffixes ("Abundant East" → "ABUNDANT")
- PortalGive: Added campus dropdown pre-selected to home campus (only for multi-campus)
- PortalGive: Fetches /portal/campuses to detect is_multi_campus

### Section F: Seed Data — 6 Tenants
- Created `/app/backend/scripts/seed_extended.py`
- Seeded 3 new tenants: Potter's House (Dallas), EdenX (Folsom CA), City Reach (Cedar Park TX)
- Each with 10K-14.5K members, 3 years of Pareto giving, attendance, groups
- Platform totals: 7 churches, 60K+ members, $68.9M GMV all-time, $1.2M fees
- Admin accounts added for each new tenant

### Section G: God Mode Dashboard Upgrades
- PlatformExecDashboard: Added 4 Hero KPI cards (GMV All-Time, Revenue All-Time, MRR, ARR)
- Backend /platform/stats now returns MRR (calculated from recurring schedules × fee rates), ARR, total_members
- Platform stats: 7 churches, $68.9M GMV, $1.2M fees, $20.3K MRR, $243.6K ARR

### Section S: Frank Luntz Messaging
- "Register Now" → "Save My Spot" on Events page
- "Log Out" → "Sign Out" in portal
- Donation success message: "Thank you for your generosity" language preserved
- Solomon AI chat fallback: "I'm not sure... send a note to support@solomonai.us"

## New Endpoints
- GET /api/portal/campuses — multi-campus detection + home campus
- POST /api/portal/campus/select — save home campus preference

## New Files
- /app/backend/scripts/seed_extended.py — 3 new tenant seed
- /app/frontend/src/components/CampusSelectorModal.jsx — first-login campus picker
