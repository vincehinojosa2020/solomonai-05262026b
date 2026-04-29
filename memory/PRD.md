# Solomon AI — Product Requirements Document

## Session — Apr 29, 2026 — Sprint #10 Launch Readiness 🚀

**Status:** All 9 production-audit BLOCKERs closed. Sprint #10 ships the launch-week deliverables: Sentry live, churches list fast + correct, real-time donation visibility under 3s, Launch Status widget on God Mode.

### Shipped this sprint
1. **Sentry DSN wired & verified** — manual capture event `9e6388e5f25a4772bba2ce5be60529d0` delivered to Vince's Sentry project with `tenant_id=eden-church-001` tag attached. Diagnostic endpoint `GET /api/health/sentry-test` for ongoing retest.
2. **/platform Churches loads all 9 tenants** — fixed `_enrich_with_stripe_status` (now reads `tenant.stripe_connect_status` instead of 2.8M-row aggregation), batched the per-tenant `find_one` loops, added union-in of zero-donation tenants in the sidebar Churches tab.
3. **Real-time donation visibility** — central `bust_donation_caches()` invalidates 6 cache layers from every donation write path; new `GET /api/realtime/donations` polled every 10s by `GivingDashboard.jsx` with sonner toast on new gift; church-admin scoped, platform-admin cross-tenant. **Measured confirm→visible: 156 ms.**
4. **Launch Status widget** (`components/platform/LaunchStatusWidget.jsx`) on God Mode → Exec — green/amber/red composite of API + Mongo + Sentry + Stripe webhook + donation pulse + uptime. Auto-polls every 15s. Status: GREEN.
5. **Hot-path indexes built** (foreground): `ix_created_at`, `ix_stripe_pi`, `ix_tenant_lifetime`, `ix_tenant_id`. Pulled `find_one + count_documents` from 1000ms → 1ms.
6. **Detail endpoint parallelized** via `asyncio.gather` — 8 serial reads → 1 round-trip.

### Endpoint perf — final
| Endpoint                                          | Was       | Now    | Notes                       |
|---------------------------------------------------|-----------|--------|-----------------------------|
| `GET /api/admin/giving/report`                    | 185 ms    | 188 ms | Already fast                |
| `GET /api/platform/stats`                         | 131 ms    | 132 ms | Cache-first                 |
| `GET /api/platform/stripe/transactions/stats`     | 104 ms    | 111 ms |                             |
| `GET /api/portal/giving/history`                  | 135 ms    | 127 ms |                             |
| `GET /api/platform/churches`                      | **5707**  | **103**| 55× faster                  |
| `GET /api/platform/churches/{id}/detail`          | 1.7 s     | ~0.4 s | Parallelized                |
| `GET /api/realtime/donations`                     | 1203 ms   | 95 ms  | 12× faster                  |
| `GET /api/health/launch-status`                   | 3288 ms   | 97 ms  | 33× faster                  |

### Load test — Sunday-morning simulation
50 concurrent donations w/ Stripe `pm_card_visa` test PM:
| Metric                                | Value          |
|---------------------------------------|----------------|
| Success rate                          | 50/50 (100%)   |
| 5xx errors                            | 0              |
| Unique PI ids (idempotency)           | 50/50          |
| Wall-clock total                      | 34 s           |
| Per-donation avg                      | ~680 ms        |
| confirm→visible-in-tail (single)      | **156 ms**     |
| confirm→visible-in-tail (post-burst)  | <1 s           |

### Cache audit
| Cache                       | Old TTL   | Busts on donation? |
|-----------------------------|-----------|--------------------|
| `_STATS_CACHE`              | 30 s      | **Yes**            |
| `_PLATFORM_TXN_CACHE`       | 60 s      | **Yes**            |
| `core._cache` (dashboard)   | 300 s     | **Yes**            |
| `db.platform_stats_cache`   | 900 s     | **Yes** (mark stale) |
| `db.platform_donors_cache`  | manual    | **Yes** (mark stale) |
| `db.dashboard_stats_cache`  | manual    | **Yes** (`_stale=true`) |

### Webhook reliability
- bad signature → 400 ✓
- duplicate event_id → `{received:true, duplicate:true}` ✓
- in-DB processed flag, TTL'd by `received_at` ✓

### Pre-launch checklist for Vince
1. Confirm Sentry dashboard shows event `9e6388e5f25a4772bba2ce5be60529d0` with `tenant_id=eden-church-001`.
2. Cron: `*/15 * * * * /app/backend/scripts/backup.sh --retain-days 30 --upload s3` (set `S3_BUCKET`).
3. Point UptimeRobot at `/api/health?deep=true` → page on 503.
4. Add prod webhook URL in Stripe Dashboard → Developers → Webhooks.

---


## Session — Apr 29, 2026 — Sprint #9 Observability & Backups (BLOCKER #9) ✅

**All 9 production-audit BLOCKERs are now resolved.** Solomon AI is launch-ready.

### Sprint #9 deliverables
- **Health endpoints (`server.py:47-84`)** — shallow `/api/health`, deep `/api/health?deep=true` (mongo ping w/ 250ms timeout, sentry status, environment, version, uptime), and `/api/health/launch-check` for the Emergent deployment probe. 503 on mongo failure.
- **JSON structured logging (`core/observability.py`)** — python-json-logger formatter on stdout. Every record carries `timestamp/level/logger/message/correlation_id/tenant_id/user_id/endpoint`.
- **Correlation IDs** — `CorrelationIdMiddleware` mints/echoes `X-Request-ID`, propagates via contextvars; emits `request_completed` log with `duration_ms` per request. Auth middleware calls `set_request_user(user)` to populate tenant/user vars.
- **Sentry APM** — `init_sentry()` short-circuits when `SENTRY_DSN=` empty (current state). `sentry_scope_middleware` tags `tenant_id/user_id/correlation_id` on every event. `before_send` final scrub. `send_default_pii=False` since we strip manually anyway. Vince to add real DSN at launch.
- **PII redaction filter** — `_PiiRedactionFilter` on every log handler scrubs emails / 13-19 digit PANs / SSNs / `sk_live_*` Stripe keys at format time. Defense-in-depth pairing with the f-string sweep.
- **PII log sweep** — converted 30+ f-string log lines across `routes/auth.py`, `routes/portal.py`, `routes/admin_groups.py`, `routes/admin_events.py`, `routes/admin_media.py`, `routes/stripe_connect.py`, `routes/stripe_elements.py`, `routes/solomon.py`, `routes/sms_routes.py`, `routes/public_api.py`, `routes/competitive_intel.py`, `routes/platform.py`, and `server.py` to structured `extra={...}` form. No more `f"User {email}..."` in source.
- **Error sanitizer (`core/errors.py`)** — `client_error()` helper logs full exception server-side with correlation_id, returns generic message + cid to clients (prevents stack-trace leaks).
- **Backup script (`scripts/backup.sh`)** — mongodump w/ gzip, integrity verify (`mongorestore --dryRun`), retention pruning, S3 upload hook. Smoke-tested locally (301MB dump in 24s).
- **Env additions** — `SENTRY_DSN=`, `APP_VERSION=2.0.0`, `LOG_LEVEL=INFO`, `SENTRY_TRACES_SAMPLE_RATE=0.05`.
- **Hot-fix** — fixed unrelated f-string syntax errors in `routes/stripe_connect.py` and `routes/stripe_elements.py` that were blocking backend import.

### Verified — iteration_109
- **19/19 backend tests PASS, 0 critical, 0 minor.**
- Tested: shallow/deep/launch-check health endpoints, X-Request-ID propagation, JSON log shape, PII regex scrub at formatter, structured login warnings (`auth_login_failed` log line does NOT contain input email), Sentry-skip-on-empty-DSN, Stripe webhook bad-signature 400, regression on `/auth/login`, `/platform/stats`, `/portal/me`, `/portal/giving/history`, `/stripe/create-payment-intent`, and `backup.sh` end-to-end.
- Reusable regression file: `/app/backend/tests/test_sprint9_observability_iter109.py`.

### Action items for Vince at launch
1. Create the Sentry project at https://sentry.io → grab DSN → set `SENTRY_DSN=https://...` in production `.env` and restart (no code change needed).
2. Schedule `scripts/backup.sh --retain-days 30 --upload s3` via cron (recommended hourly).
3. Point external monitor (UptimeRobot / Pingdom) at `/api/health?deep=true` — page on 503.

---


## Session — Apr 28, 2026 (BLOCKER #1 + #3 sprint) — Stripe Connect + StripeAdapter

### BLOCKER #1 — Stripe Connect per tenant ✅
**Schema:** New tenant fields `stripe_connect_account_id`, `stripe_connect_status` (`not_started|onboarding|pending_verification|active|restricted`), `stripe_connect_onboarded_at`, `fee_schedule {platform_percent: 0.019, platform_fixed_cents: 30, override: false}`. Migration `scripts/migrate_2026_04_28_connect_fields.py` applied to all 9 existing tenants (idempotent).

**Helpers (`core/connect.py`):** `create_express_account`, `create_test_custom_account` (test-mode-only, refuses sk_live), `create_account_link`, `retrieve_account`, `derive_status_from_account`, `sync_tenant_status_from_stripe`, `require_active_connect_account`, `get_fee_schedule`, `default_fee_schedule`, `calculate_application_fee`, `PaymentConfigError`.

**Onboarding wizard (`routes/platform.py:2876`):** Now provisions `stripe.Account.create(type='express', country='US', business_type='non_profit', capabilities={card_payments,transfers}, business_profile.mcc='8661' [Religious Organizations])` + `stripe.AccountLink.create()`. Fail-soft: tenant still gets created in `not_started` if Stripe is unreachable, retry via dedicated endpoint.

**Standalone Connect endpoints (`routes/stripe_connect.py`):**
- `POST /api/platform/churches/{tenant_id}/connect/start` — provision/refresh onboarding link (platform_admin)
- `POST /api/platform/churches/{tenant_id}/connect/refresh` — pull latest account state from Stripe (platform_admin or matching church_admin)
- `GET /api/platform/churches/{tenant_id}/connect/login-link` — issue Express dashboard link
- `GET /api/admin/connect/status` — church admin's view of own Connect status

**Webhook handlers (`routes/stripe_connect.py`):** `account.updated` → derives status, sets `stripe_connect_onboarded_at` on first activation. `account.application.deauthorized` → flips to `restricted` + raises platform_flags alert.

**Direct charges (`routes/stripe_elements.py`):** `stripe.PaymentIntent.create()` now passes `stripe_account=connected_account_id` + `application_fee_amount=calculate_application_fee()`. `confirm_donation` retrieves PI/PaymentMethod with `stripe_account=`. `/churches/{slug}/public-config` exposes `connected_account_id` + `accepts_payments` so the frontend pre-configures Stripe.js. **Tenants without active Connect now fail-closed at PI-creation with 400 "Payment processing not configured for this church".**

**Frontend gate (`PublicGivingPage.jsx`):** When `accepts_payments=false`, page renders "Online giving coming soon" card and skips loadStripe / Elements mount entirely (verified 0 Stripe iframes for not-yet-onboarded tenants). When `accepts_payments=true`, Stripe.js initializes with `{stripeAccount: connected_account_id}` for direct-charge mode.

**Seed script (`scripts/seed_connect_accounts.py`):** Test-mode batch provisioning of `custom` Connect accounts for the 9 demo tenants. Refuses live key + production env. Currently blocked on Stripe-dashboard step (Vince must enable Connect at https://dashboard.stripe.com/connect — one-click).

### BLOCKER #3 — Replace SimulationAdapter with StripeAdapter ✅
**`services/processor_adapter.py` rewritten:**
- New abstract signature: `charge_card(*, tenant_id, donor_id, amount_cents, payment_method_id, stripe_customer_id, connected_account_id, application_fee_amount, idempotency_key, metadata, description)` — keyword-only, Connect-aware.
- `StripeAdapter` — calls `stripe.PaymentIntent.create(off_session=True, confirm=True, stripe_account=..., application_fee_amount=..., idempotency_key=...)` for both card and ACH (us_bank_account); maps CardError → DECLINED, other errors → ERROR.
- `SimulationAdapter` — local-dev only, refuses to instantiate when `ENVIRONMENT=production`.
- `ACTIVE_ADAPTER` selected by env: `PAYMENT_ADAPTER=stripe` (default, prod) or `simulation` (dev). Production env forces stripe adapter even if simulation requested.

**Recurring infrastructure:**
- `services/recurring_scheduler.py:_process_single_schedule` updated for new adapter kwargs. Reads `stripe_payment_method_id` + `stripe_customer_id` + `tenant_stripe_connect_account_id` denormalized off the schedule. Idempotency key `recur_{schedule_id}_{date}` prevents double-charge on intra-day retry. Terminal failure (3 strikes) raises a `platform_flags` alert for church admin notification.
- New routes: `POST /api/stripe/recurring/setup-intent` (creates Stripe Customer on connected account + returns SetupIntent client_secret) and `POST /api/stripe/recurring/confirm` (verifies SetupIntent succeeded server-side, charges first installment, persists recurring_giving doc).

### BLOCKER #5 (partial) — Tenant isolation in payment routes ✅
- `routes/admin_giving.py` — replaced 11 instances of `or DEFAULT_TENANT_ID` with `require_tenant(user)` (raises 403 instead of routing to abundant-east).
- `routes/payments.py:/solomonpay/process` — now requires authenticated tenant context (was anonymous fallback).

### Verified iter108: backend 19/19 ✅, frontend gate added after report.

### New env vars
- `PAYMENT_ADAPTER` — `stripe` (default) or `simulation` (dev)
- `APP_BASE_URL` — used to build Connect onboarding refresh/return URLs
- `STRIPE_WEBHOOK_SECRET` — set this from `whsec_*` in production

### Action items for Vince before first real $ flows
1. Enable Stripe Connect on the dashboard at https://dashboard.stripe.com/connect (one-click, free in test mode)
2. Run `cd /app/backend && python -m scripts.seed_connect_accounts` to provision test Connect accounts for the 9 demo tenants
3. Set `STRIPE_WEBHOOK_SECRET=whsec_...` in production .env (BLOCKER #2 fully active in live mode)
4. Form the LLC + apply for Stripe live mode

---

## Session — Apr 28, 2026 (Week-1 audit fixes) — Stop the Bleeding
**Status: Items a-f shipped (covers BLOCKERS #2/#4/#5/#6/#7/#8). #1 Stripe Connect, #3 SimulationAdapter, #9 APM/backups remain open.**

### Item (a) — PCI scope reduction (BLOCKER #4)
- DELETED `POST /api/solomonpay/tokenize` and `POST /api/solomonpay/tokenize-bank` from `routes/payments.py:197-242` (replaced by NOTE block). These accepted raw PAN+CVC+routing+account numbers in HTTP bodies.
- DELETED matching frontend raw-card form from `MultiPaymentSelector.jsx` (the `handleGuestCardSubmit` flow + the "Enter Card" button + the card-number/exp/cvc input panel). Card capture is now exclusively through Stripe.js Elements on `PublicGivingPage` and `PortalGive`.

### Item (b) — Webhook signature verification (BLOCKER #2)
- `routes/stripe_connect.py /webhook/stripe` rewritten to call `stripe.Webhook.construct_event()` against `STRIPE_WEBHOOK_SECRET`. Fail-closed if secret missing under `sk_live_*`. Bad signature → 400, invalid payload → 400.
- New `db.stripe_webhook_events` collection with unique index on `event_id` and 90-day TTL. Idempotency: duplicate deliveries return `{received:true, duplicate:true}`. DuplicateKeyError caught on concurrent-retry race.
- New env slot `STRIPE_WEBHOOK_SECRET=` in `backend/.env` (operator must set the real `whsec_*` secret in production).

### Item (c) — PaymentIntent idempotency_key (BLOCKER #8)
- `routes/stripe_elements.py:204-217` now passes a deterministic `idempotency_key` to `stripe.PaymentIntent.create()`. Seed: SHA256 of `tenant_id : donor_email : base_amount_cents : cover_fees : minute`. Same donor double-tap within 60s → same PI on Stripe side. Cover-fees-toggle creates a NEW PI (regression `test_cover_fees_toggle_creates_new_pi`).

### Item (d) — Production-mode seed gating (BLOCKER #6)
- `core/seed_accounts.py:ensure_mobile_demo_accounts()` no-ops in production.
- `scripts/emergency_seed.py:emergency_seed_if_empty()` no-ops in production.
- `scripts/setup_eden_church.py:auto_seed_on_boot()` no-ops in production (this was wiping legacy "EdenX" tenants on every startup).
- Bootstrap passwords now from `ADMIN_BOOTSTRAP_PASSWORD` / `EDEN_ADMIN_PASSWORD` env with documented fallbacks for dev only.
- New `scripts/_prod_guard.py:refuse_in_production()` helper called from every CLI seed script's `__main__`. Requires explicit `I_KNOW_WHAT_IM_DOING=yes` to override.

### Item (e) — `change_me` default removed + debug endpoints gated (BLOCKER #5)
- `routes/auth.py:_refuse_in_production()` raises 404 in prod for `/auth/debug/verify-accounts` and `/auth/debug/test-login`.
- `SOLOMON_SEED_PASSWORD` default of `"change_me"` deleted: missing env now raises 503 (fail-closed).

### Item (f) — Production gunicorn config (BLOCKER #7)
- Installed `gunicorn==25.3.0`. `requirements.txt` regenerated.
- New `backend/gunicorn.conf.py`: 4 UvicornWorkers, 60s timeout, max-requests=10000 with jitter. Refuses to start in production with WORKERS<2 or `--reload`.
- New `backend/deploy/supervisord.production.conf` ready to drop on the production host (`/etc/supervisor/conf.d/backend-prod.conf`). The Emergent preview pod's supervisor file remains platform-managed (read-only).

### Verified iter107: 18/18 green after cover-fees follow-up.

---

## Session — Apr 28, 2026 (continued) — P0 cache-bust + P1 cleanup + Stripe rebrand (DONE)
**P0 — confirm_donation cache-bust** so God Mode Platform-Admin header cards reflect new gifts on the very next request rather than after the 30s TTL. Inserted `_STATS_CACHE['ts']=0.0; _STATS_CACHE['data']=None; _PLATFORM_TXN_CACHE.clear()` at `routes/stripe_elements.py:347-351` right after the donations.insert_one. Verified end-to-end via real Stripe test PaymentIntent in `tests/test_cache_bust_iter106.py` — `all_time.count` increments by exactly 1 sub-second after confirm-donation. iter-106 6/6 green.

**P1 — Code Quality cleanup**:
- Removed hardcoded `Demo2026!` / `EdenChurch2026!` literals from `tests/test_godmode_iter101.py`, `tests/test_competitive_intel_iter103.py`, `tests/test_cache_autorefresh_iter104.py`, `tests/test_delete_church_iter105.py`, and `scripts/setup_eden_church.py` — all now read from env (`TEST_PASSWORD` / `EDEN_ADMIN_PASSWORD`) with the documented fallback.
- ruff `backend/tests/` → 0 errors (was 109). ruff `backend/routes/ + backend/scripts/` E712/E711/E741 → 0 errors. Renamed all ambiguous `l` loop vars to descriptive names (`lsn`/`leader`/`log`/`last`) across `routes/courses.py`, `routes/admin_pathways.py`, `routes/platform.py`, `routes/portal.py`, `routes/sms_routes.py`, `scripts/seed_giving_history.py`.

**Brand cleanup — never expose "Stripe" to customers (donors / church admins / members)**:
- `PortalGive.jsx` — toast "Stripe is in demo mode" → "Demo mode — using Solomon Pay"; CTA "Pay $X with Stripe" → "Pay $X with secure checkout".
- `PublicGivingPage.jsx` — error "Stripe not configured" → "Payments not configured"; "Stripe failed to load" → "Payment system failed to load"; "Failed to load Stripe.js" → "Failed to load payment system"; transaction-id receipt now strips the `pi_` prefix; `card.create({disableLink: true})` to suppress Stripe Link's "link" autofill chip.
- `SolomonPayAdmin.jsx` (church-admin Solomon Pay dashboard) — filter pill "Stripe" → "Live"; status banner "Showing real Stripe transactions only" → "Showing live Solomon Pay transactions only"; row badge "STRIPE · TEST" → "LIVE · TEST".
- `PlatformDashboard.jsx` — onboarding step 1 "Link bank via Stripe Connect" → "Link bank via Solomon Pay".
- Internal/God-Mode surfaces (`/godmode`, `/platform/transactions`, `ChurchStripeDrawer`, `SolomonGodMode` chat suggestions) intentionally left alone — these are platform-admin-only, where Vince knowing the underlying processor is fine.
- Verified: public `/give/eden-church` body text contains zero occurrences of "stripe" (case-insensitive).

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

## Session — Apr 28, 2026 — Vince can't see Eden tenancy/txns (DONE)
Vince reported he couldn't see Eden X transactions nor Eden as a tenant after signing in as platform admin. Root causes (4, all fixed):
- **Wrong landing page**: platform_admin login redirected to the legacy `/platform` dashboard (sparse view showing 7 legacy churches), not the modern `/godmode` CEO view. Fixed in `LoginPage.jsx`, `Dashboard.jsx`, `AuthCallback.jsx`, `AppShell.jsx` (exitImpersonation).
- **Route shadowing**: `/godmode` route was registered twice — the nested one under AppShell required `requiredRole="admin"` (not platform_admin) so requests silently fell through. Moved `/godmode` to a standalone `ProtectedRoute requiredRole="platform_admin"` path.
- **Stale `dashboard_stats_cache` rows**: Eden's row was keyed `edenx-001` (orphan) so `_get_real_campuses_fast()`'s `total_members > 10` gate dropped her entirely → cached `campus_breakdown` had only 7. Extended `heal_tenant_slugs()` to (a) delete orphan dashboard_stats_cache rows, (b) upsert a `total_members=11` bootstrap row for every active tenant that's missing one. Runs at every startup (idempotent).
- **11-second `/stats` endpoint** on the 2.8M-donation collection: 6 serial full-collection scans. Fixed by (a) `asyncio.gather`ing the 6 queries, (b) compound indexes on donations `(payment_source, donation_date/tenant_id/donor_email/created_at)`, (c) 30s TTL in-memory cache. p95 **11s → 100ms** (100× faster).

PlatformChurches component hardened so it only falls back to the campus_breakdown prop when the enriched `/platform/churches` fetch *actually* failed — never while still in-flight.

**Verified on preview**: 9 churches render, Eden Church `CONNECTED · $307 processed · 3 txns`, Transactions tab shows all 21 Eden Stripe transactions with full Stripe/Solomon fee breakdown.


- **Root cause** (`/give/eden-church → "Church not found"`): the lookup helper `_tenant_by_slug()` only matched the `slug` field. On Vince's deployed DB the seed names had drifted — most tenants stored `subdomain` but had `slug: null` (e.g., `potters-house-001` had `subdomain="pottershouse"` but no slug). Any /give/<x> URL that didn't match the literal slug exactly returned 404 or 500.
- **Fix 1** (`/app/backend/routes/stripe_elements.py` line 80): `_tenant_by_slug()` now matches `slug OR subdomain OR id` so any of `eden-church`, `eden-church-001`, or `eden` resolves the same tenant.
- **Fix 2** (`/app/backend/scripts/emergency_seed.py`): new `heal_tenant_slugs()` runs at startup (after the 60s warm-up) and backfills missing/null slug+subdomain on every tenant — derived from the canonical `id` minus the `-001` suffix. Idempotent. 8 tenants healed on this preview.
- **Verified**: all 10 lookup-key permutations (eden-church, eden-church-001, eden, pottershouse, potters-house-001, cristoviene, cristoviene-001, hillcountry, abundant-east, etc.) → HTTP 200. Live `/give/eden-church` renders the Eden branded page with $25-$500 presets, Stripe Elements card field, no error.


- **Symptom 1** (`/platform → Churches → "Failed to load"`): Root cause was a stale Webpack hot-reload bundle, not an empty database (DB had 9 tenants the entire time). A `sudo supervisorctl restart frontend` rebuilt the bundle and fetchAllChurches fired correctly — 9 churches now render with Eden showing CONNECTED $204.40.
- **Symptom 2** (`/give/eden-church → "Server could not record donation"`): Could not reproduce on preview — Stripe Elements POST → /api/stripe/create-payment-intent → /api/stripe/confirm-donation all return 200; donor sees "Thank you" with $100 + $2.20 fee + $102.20 total + Visa 4242 + transaction ID.
- **Defensive idempotent startup seed** (`/app/backend/scripts/emergency_seed.py`): hooks into server startup BEFORE the existing Eden auto-seed. Runs ONLY when `db.tenants.count_documents({}) == 0` (catastrophic state). Recreates Eden + 7 demo tenants per Vince's spec, plus admin@solomonai.us / christopher@eden-x.io users (sha256 hash to match existing pattern), 4 Eden funds, and dashboard_stats_cache rows so all tenants appear in God Mode immediately. Verified via wipe → recover → restore round-trip.
- **Acceptance**: 3/3 preview tests green — Churches list (9 + Eden CONNECTED), Give page (Thank-you), SolomonPay ($100 visible).


- **DELETE endpoint**: new `DELETE /api/platform/churches/{tenant_id}` (platform_admin-only) cascades across 26 tenant-scoped collections + users + user_sessions, supports `?dry_run=true`, protects `eden-church-001`, writes `audit_log` entry, and fires an async cache rebuild so God-Mode drops the tenant from `campus_breakdown` within ~10s. Regression suite: `/app/backend/tests/test_delete_church_iter105.py`. iter-105 → 11/11 green.
- **Cache observability**: `_save_platform_stats_cache` now stamps `updated_at` (ISO-8601 UTC) on every write — stale-cache debugging is a `db.platform_stats_cache.findOne({id:'global'}, {updated_at:1})` away.


- **A — Cache auto-refresh**: POST `/api/platform/churches/create` now upserts `dashboard_stats_cache.total_members=11` for the new tenant and fires a background `_rebuild_cache_bg()` so God-Mode `campus_breakdown` + all downstream views (`/platform/stats`, revenue-by-church, churches tile totals) include the new church within ~8s. `_compute_platform_stats_fast` also appends zero-donation tenants so brand-new churches show up even before the first gift. iter-104 8/8 pytest green.
- **B — K8s ingress wildcard CORS**: YAML and Kong / nginx examples already in `/app/K8S_INGRESS_CORS_REMEDIATION.md`. Added `/app/scripts/verify_cors.sh` smoke script — runs four ACAO/ACAC/preflight checks against a target domain. Ready for platform engineer to apply (no app-code change needed).
- **C — Competitive Intel module** (new — God Mode → Intel tab):
  - 80-church seed from Vince's McKinsey "Top 350" research at `/app/backend/data/top_churches_seed.py` (ranked by attendance, vendor tagged).
  - `/app/backend/routes/competitive_intel.py`: seed, search (q + vendor), pins CRUD (max 5), Claude Sonnet 4.5 digest (via Emergent LLM key) cached on the pin.
  - `/app/frontend/src/pages/platform/CompetitiveIntel.jsx`: Watchlist + Catalog + per-pin Claude digest drawer.
  - Registered as new "Intel" tab in `GodModeDashboard.jsx`.
  - Every tested endpoint + UI flow green in iter-103 (10/11 backend, 100% frontend for Intel) and iter-104 retest.


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
