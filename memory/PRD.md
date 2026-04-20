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

### Snyk SAST (71 → 0)
- DOMPurify on all dangerouslySetInnerHTML
- safeHref/safeSrc/safeRedirect utilities
- CSP meta tag, path traversal protection, credential env vars

## Documentation
- `/app/SOLOMON_AI_PLATFORM_AUDIT.md`
- `/app/SOLOMON_AI_UI_GUIDE.md`

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
