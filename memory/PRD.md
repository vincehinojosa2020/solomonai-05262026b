# Solomon AI — Product Requirements Document

## Architecture
React 18 + FastAPI + MongoDB 7.0 | 575+ endpoints | 89 pages | Claude Sonnet 4.5 + Whisper

## Everything Built (All Verified)
- Core Platform, P0 Plumbing, P1 Public Site/AI/Parity, P2 Security, P3 Polish
- Demo Mode Toggle, Stripe Connect, Custom Report Builder, PPTX/DOCX Generation
- Snyk SAST Remediation (71 code vulnerabilities)
- Snyk SCA Remediation (58 dependency vulnerabilities)

## Security Posture (Current)

### Snyk SCA — Backend (47 → 0 remaining)
- PyJWT 2.12.1, pyasn1 0.6.3, aiohttp 3.13.5, cryptography 46.0.7
- requests 2.33.1, pymongo 4.16.0, motor 3.7.1, urllib3 2.6.3
- ecdsa + python-jose: REMOVED (not needed, eliminated 3 HIGH vulns)

### Snyk SCA — Frontend (11 → 2 accepted risks)
- Yarn resolutions: underscore 1.13.8, serialize-javascript 7.0.5, nth-check ~2.1.1 (pinned to CJS-compatible patched version; 3.x is ESM-only and breaks CRA build), postcss 8.5.6
- Accepted risks: eslint@8.x (react-scripts compat), inflight@1.0.6 (no fix, dev-only)

### Snyk DAST / Probely (6 → 0)
- Strict CORS allowlist (allow_origin_regex) in server.py
- TLS 1.2+ only, secure cipher suites (Nginx)
- CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff, HSTS, Referrer-Policy

### Snyk SAST (98 → 0)
- DOMPurify on all dangerouslySetInnerHTML
- Centralized sanitize.js: safeHref, safeImgSrc, safeIframeSrc, safeMailto, safeTel, safeRedirect, safeStripeCheckoutUrl, blobFromResponse
- Host-allowlisted iframes (Thinkific, Shopify/Square/BigCartel for merch)
- Mailto/tel regex-validated
- Blob download guards validate content-type (application/pdf)
- Stripe Checkout URL uses `new URL()` hostname === 'checkout.stripe.com' (defeats subdomain tricks)
- Dev-server /edit-file rate-limited (20 req/min, express-rate-limit)
- CSP meta tag, path traversal protection, credential env vars
- Hardcoded test passwords removed — tests skip when TEST_PASSWORD env missing

## Documentation
- `/app/SOLOMON_AI_PLATFORM_AUDIT.md`
- `/app/SOLOMON_AI_UI_GUIDE.md`

## Session — Apr 23, 2026 — Vince's "God Mode" Prompts 1-4 (DONE)
- **Prompt 1** — `/api/platform/churches` now includes **zero-donation tenants** so Eden (and any new church) renders even before a first gift. DONE.
- **Prompt 2** — **Platform Transactions feed** live at `/platform/transactions` (`PlatformTransactionsPage.jsx`). Standalone God-Mode chrome, stats-card skeleton→real, status filter testid, stripe-live/demo toggle, export CSV. DONE.
- **Prompt 3** — **Enhanced Exec Dashboard** on `/godmode`: new `PaymentMetricsRow` (Total Stripe Processed, Solomon Revenue all-time, Active Stripe Churches, Unique Donors), `StripeTrendChart` (30-day AreaChart, LIVE badge), `RecentStripeActivity` (last 10 Stripe donations). DONE.
- **Prompt 4** — **Churches grid enhancements**: Stripe Status badge column (Connected/Pending/Not Connected), Stripe Processed column, per-row **View** button opens `ChurchStripeDrawer` with per-church KPIs + 5 most-recent Stripe payments + give-page + all-transactions links. DONE.
- **Backend additions**: `GET /api/platform/stripe/transactions/recent?limit=N`; `/api/platform/churches` rows now carry `stripe_status`, `stripe_total_processed` (cents), `stripe_txn_count`.
- **UX fix**: `DemoWalkthrough` auto-suppressed for `userRole === 'platform_admin'` (Quick-Tour modal was blocking /godmode clicks).
- **Testing**: iteration_101 (100% backend pytest / 80% frontend — 1 HIGH bug), iteration_102 (100% / 100% post-fix). Regression suite: `/app/backend/tests/test_godmode_iter101.py`.
- **Credentials unchanged**: `admin@solomonai.us / Demo2026!`, Eden Church `christopher@eden-x.io / EdenChurch2026!`.


- Wiped legacy "EdenX Ministries" tenant + seeded clean `eden-church-001` (1 admin, 4 funds, 0 everything else). Reset via `POST /api/admin/eden-church/reset` (platform_admin only).
- Real Stripe test mode wired: new router `/app/backend/routes/stripe_elements.py` with `/api/stripe/elements/config`, `/api/churches/:slug/public-config`, `/api/stripe/create-payment-intent`, `/api/stripe/confirm-donation`, `/api/stripe/balance`, `/api/stripe/payouts`.
- Public guest giving page at `/give/:churchSlug` (`PublicGivingPage.jsx`) — Eden Church rendered in black + cyan + Playfair Display; other tenants render dynamically from their primary/accent colors.
- `SolomonPayAdmin.jsx` dashboard now has a 3-pill source toggle (All / Stripe / Demo data) + STRIPE·TEST vs DEMO badges on recent transactions. Backend dashboard + transactions endpoints accept `?source=stripe|demo|all`.
- Christopher's credentials: `christopher@eden-x.io` / `EdenChurch2026!`.
- Verified end-to-end: real PaymentIntents created, donations persisted with `payment_source='stripe'` + `test_mode=true`, idempotent confirm flow, live Stripe balance in dashboard, reset endpoint clears demo-run data on demand.

## Remaining
- Vite migration — **DEFERRED / BLOCKED on platform** (see `/app/VITE_MIGRATION_DEFERRED.md`). Requires Emergent to port webpack-based `visual-edits` + `health-check` plugins to Vite first.
- Apple/Google Pay — **MOCK UI shipped** (Feb 2026) at `/portal/give` + `/giving`. Auto-upgrades to real Stripe Payment Request Button when `REACT_APP_STRIPE_PUBLISHABLE_KEY` or `window.__STRIPE_PUBLISHABLE_KEY__` is set. See `/app/STRIPE_PAYMENT_REQUEST_INTEGRATION.md`.
- ElevenLabs TTS upgrade for Ask Solomon AI.
- K8s ingress wildcard CORS — **YAML prepared** in `/app/K8S_INGRESS_CORS_REMEDIATION.md`; requires Emergent platform engineer to apply.

## Session — Feb 20, 2026
- Fixed `craco build` ERR_REQUIRE_ESM by pinning `nth-check` resolution to `~2.1.1` (was `>=2.0.1` which pulled ESM-only 3.0.1).
- Built `StripePaymentRequestButton` component (mock + live-ready) with official Apple Pay / Google Pay brand buttons and realistic auth sheet.
- Wired wallet button into `MultiPaymentSelector`, `DonationCheckout` (at /giving), and `PortalGive` (at /portal/give).
- Tested end-to-end (iterations 96 + 97): 100% pass on both flows.
- Documented Vite migration blockers (webpack-specific Emergent plugins) in `/app/VITE_MIGRATION_DEFERRED.md`.
- Prepared K8s ingress CORS remediation YAML in `/app/K8S_INGRESS_CORS_REMEDIATION.md`.
