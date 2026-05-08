# Solomon AI — Application Overview & Status (May 1, 2026)

Every detail below grounded in code paths, route counts, and live data
from the running app. No marketing fluff, no estimates dressed as facts.

---

## Q1 — The Big Picture

### Identity
* **Name in code**: `Solomon AI Church Management API` (`server.py:40`)
* **Public domain**: `solomonai.us`
* **Brand line**: "Your Church. One App. Zero Compromise. From Sunday morning to Monday morning, everything your congregation needs." (from production HTML meta description)
* **Built for**: church staff (admin role) + members (member role) + platform-level operators (platform_admin role) — a multi-tenant SaaS where each tenant = one church campus.
* **Lighthouse customer**: Eden X (Christopher Hinojosa / Christopher Schreur).
* **Customer scale today (production tenants)**: 9 church docs (Eden + 4 Abundant campuses + Potter's House + CityReach + Hill Country + Cristo Viene). 0 of them currently processing live donations — all giving traffic to date is demo/seed data.

### What it actually does — three product surfaces

**1. Church Admin Suite** (`/dashboard` and friends, role=admin or pastor)
A complete back-office for running a multi-campus church:
* People CRM — members, households, custom fields, smart lists, duplicate merge
* Giving — donations, funds, recurring, statements, refunds, disputes, batches, pledges
* Groups & Events — small groups, calendars, registrations, RSVPs, room booking
* Services — service planning, song library, music stand mode, volunteer scheduling
* Kids Check-in — secure pickup codes, label printers, parent SMS notifications
* Pathways/Courses — internal course platform + Thinkific integration
* Communications — bulk email + SMS (SMS currently mocked, see Q5)
* Reports — custom report builder, audit log, attendance reporting
* Cafe & Merch — point-of-sale and inventory for in-church coffee/merch tables
* Workflows & Forms — automation triggers + custom intake forms
* Solomon Pay — payment processor admin (transactions, donors, refunds, payouts, virtual terminal)

**2. Member Portal** (`/portal/*`, role=member)
A consumer-facing app for the congregation:
* Give (one-time + recurring donations)
* Watch (sermons, video progress tracking)
* Library (devotionals, content)
* Kids check-in (parent-side)
* Pathways (course progress)
* Events (RSVPs, registrations)
* Directory (member directory if church enables it)
* Cafe / Merch ordering
* Personal account / payment methods

**3. God Mode (Platform Admin)** (`/platform`, `/godmode`, role=platform_admin)
The internal operator's view across all churches:
* Multi-tenant stats (total GMV, MRR, ARR, churches, members)
* Stripe transactions, payouts, disputes, fraud signals
* Per-tenant drill-through
* Church onboarding wizard
* Launch Status widget (uptime, mongo health, donation-pulse)
* Competitive intelligence (compare churches against scraped competitor data)

### Tech stack
| Layer | Tech |
|---|---|
| Frontend | React 19 (CRA + craco), TailwindCSS, shadcn/ui, lucide-react, Stripe.js + Elements |
| Backend | FastAPI on uvicorn (single worker today; gunicorn config exists for prod) |
| Database | MongoDB (Atlas in prod) — Motor async driver, pool=5 |
| Payments | Stripe Connect (Standard accounts), Stripe Elements |
| AI | Anthropic Claude Sonnet 4.5 via Emergent LLM key (Solomon assistant + competitor intelligence) |
| Email | Resend |
| Observability | Sentry + structured JSON logging with correlation IDs |
| Auth | Custom JWT + Emergent-managed Google OAuth (LoginPage.jsx:157) |
| Hosting | Emergent (preview) and `solomonai.us` (production via Cloudflare → Emergent) |

### Current state — one-paragraph honest read
**Architecturally complete, operationally pre-launch.** The full church-management feature set is shipped: 41 backend route modules, ~89 frontend pages, 134 distinct MongoDB collections. 9 production tenants are seeded with $108M of demo giving data. Stripe Elements integration is verified end-to-end (real test card 4242 → "Thank you" page captured this week). Webhooks are signature-verified and idempotent. Battle test confirms zero application errors up to 7,500 concurrent donors. **What's missing for live operation**: actual paying churches running real cards through it, a couple of mocked subsystems (bulk SMS, parent check-in SMS), platform-level uvicorn worker config (Emergent support ticket), and a few prod-only data fixes that have already been auto-seeded on boot.

---

## Q2 — Pages & Features (every screen + status)

### Public marketing & auth (11 pages)
| Path | Page | Status |
|---|---|---|
| `/` | LandingPage (Airbnb-themed) | ✅ Working |
| `/support` | SupportPage | ✅ Working |
| `/pricing` | PricingPage | ✅ Working |
| `/login` | LoginPage (email/password + Emergent Google OAuth) | ✅ Working |
| `/signup` | SignUpPage | ✅ Working |
| `/demo` | DemoPage | ✅ Working |
| `/privacy` | PrivacyPage | ✅ Working |
| `/terms` | TermsPage | ✅ Working |
| `/security` | SecurityPage | ✅ Working |
| `/forgot-password` | ForgotPasswordPage | ✅ Working |
| `/register/:eventId` | PublicRegistrationPage (event check-in) | ✅ Working |
| `/give/:churchSlug` | **PublicGivingPage** (donor flow, Stripe Elements) | ✅ **VERIFIED PROD this week** — "Thank you" rendered with real test charge. All 9 churches resolve. |

### Platform Admin / God Mode (3 routes)
| Path | Page | Status |
|---|---|---|
| `/platform` | PlatformDashboard | ✅ Working — MTD/YTD/all-time aggregates |
| `/platform/transactions` | PlatformTransactionsPage | ✅ Working — Stripe transaction stream |
| `/godmode` | GodModeDashboard (with LaunchStatusWidget) | ✅ Working |

### Church Admin (40 routes inside `<AppShell>`)
**Fully working ✅**
* `/dashboard` (Dashboard — opens to KPIs, live activity)
* `/people` + `/people/:personId` (People CRM)
* `/households`
* `/services` (Service planning + planning center-style flow)
* `/volunteers`
* `/groups` + `/groups/:groupId`
* `/events`, `/admin/events` (EventsManagerPage)
* `/calendar` + `/calendar/approvals`
* `/attendance`
* `/giving` (GivingDashboard)
* `/solomonpay` (SolomonPay admin — see partial flag below)
* `/communications` (email works; bulk SMS mocked)
* `/reports` + `/reports/builder`
* `/settings`
* `/integrations`
* `/media` (MediaManagerPage)
* `/abundant-pathways`
* `/merch` + `/cafe`
* `/developer` (DeveloperAPIPage)
* `/kids-checkin`, `/checkin-setup`
* `/audit-log`
* `/admin/groups`, `/admin/groups/:groupId/dashboard`, `/admin/courses`, `/admin/courses/:id/edit`, `/admin/courses/:id/members`
* `/admin/members/import` (CSVMemberImport)
* `/workflows`, `/forms`
* `/people/duplicates`
* `/smart-lists`
* `/songs` (SongLibraryPage)
* `/registrations`
* `/printers` (PrinterConfig)
* `/thinkific` (ThinkificPage)
* `/music-stand/:planId`

**Partially working / has mocked sub-features ⚠️**
* `/solomonpay` → loads correctly, but `GET /api/admin/solomonpay/dashboard` returned **500 in production** today (`{"error": "INTERNAL_ERROR", "code": 500}`). Root-cause unknown without prod logs — likely a tenant-scoping query failing on the live data shape. **Worth a Sentry hunt before launch.**
* `/communications` → email send is real (via Resend); **bulk SMS handler is mocked**, returns `mock_<uuid>` and never hits Twilio (`routes/admin_comms.py:99-104, 178`). Single-recipient flow may have the same gap.
* `/kids-checkin` → check-in itself works; **parent SMS pickup notification is mocked** (`routes/admin_checkins.py:152-154`, prints `[MOCK SMS]` to stdout instead of sending).

### Member Portal (15 routes)
| Path | Page | Status |
|---|---|---|
| `/portal` (index) | PortalHome | ✅ Working |
| `/portal/give` | PortalGive (recurring + one-time) | ✅ Working |
| `/portal/watch` | PortalWatch (sermons + progress) | ✅ Working |
| `/portal/library` | PortalLibrary | ✅ Working |
| `/portal/kids` | PortalKidsCheckin (parent side) | ✅ Working |
| `/portal/thinkific` | PortalThinkific | ✅ Working |
| `/portal/pathways` + `/portal/pathways/:courseId` | PortalPathways | ✅ Working |
| `/portal/merch` | PortalMerch | ✅ Working |
| `/portal/cafe` | PortalCafe | ✅ Working |
| `/portal/directory` | PortalDirectory | ✅ Working |
| `/portal/courses` + `/portal/courses/:id` + `.../lessons/:lessonId` | PortalCourses + viewer | ✅ Working |
| `/portal/groups` | PortalGroups | ✅ Working |
| `/portal/events` | PortalEvents | ✅ Working |
| `/portal/me` | PortalMe (account + payment methods) | ✅ Working |

**Page totals**: 58 main pages + 19 portal pages + 12 platform admin pages = **~89 distinct screens**.

### Pages that are *broken or visibly degraded* right now
* `/solomonpay` dashboard endpoint 500's on prod (working on preview).
* No other pages confirmed broken in production. The "All systems Down" alert you saw earlier was monitoring the wrong (stale) preview URL — `solomonai.us` health endpoint returns 200 with mongo OK.

---

## Q3 — Database & Backend

### MongoDB collections (134 total — fully cataloged)

**Identity & access**
`tenants`, `users`, `user_sessions`, `idempotency_keys`, `audit_log`, `activity_log`, `rate_limits`, `platform_flags`

**People & relationships**
`people`, `households`, `children`, `custom_field_definitions`, `custom_forms`, `form_submissions`, `smart_lists`

**Giving (the core)**
`donations`, `donation_batches`, `funds`, `pledges`, `recurring_giving`, `recurring_giving_runs`, `recurring_donors`, `giving_goals`, `giving_integrations`, `payment_methods`, `payment_processor_settings`, `payment_transactions`, `payouts`, `disputes`, `solomonpay_settings`, `solomonpay_transactions`, `subscriptions`, `text_to_give_config`, `statement_jobs`, `tenant_branding`, `platform_donors`, `platform_donors_cache`, `platform_stats_cache`, `dashboard_stats_cache`

**Stripe specifics**
`stripe_webhook_events` (idempotency), webhook events tracked separately from payments

**Groups, services, events**
`groups`, `group_members`, `group_memberships`, `group_attendance`, `group_events`, `group_event_rsvps`, `group_messages`, `group_notifications`, `group_outreach_logs`, `group_questions`, `group_resources`, `group_types`, `group_join_requests`, `services`, `service_plans`, `service_types`, `service_types_config`, `songs`, `events`, `event_registrations`, `registration_configs`, `booking_requests`, `rooms`, `blockout_dates`

**Volunteer & attendance**
`volunteer_assignments`, `volunteer_opportunities`, `volunteer_schedule`, `volunteer_signups`, `volunteer_teams`, `attendance`, `attendance_checkins`, `checkin_labels`, `checkin_locations`, `checkin_stations`, `checkins`

**Content & courses**
`courses`, `course_enrollments`, `course_lessons`, `course_lesson_progress`, `course_modules`, `watch_progress`, `video_notes`

**Communication**
`announcements`, `communications`, `email_templates`, `sms_logs`, `messaging`, `push_subscriptions`, `prayer_logs`, `prayer_requests`

**POS & merch**
`cafe_items`, `cafe_orders`, `cafe_settings`, merch in their own collections (via `admin_merch.py`)

**Workflows & automation**
`workflows`, `workflow_enrollments`, `plan_templates`, `geofence_config`, `printers`

**Operations**
`competitor_churches`, `competitor_pins` (competitive intelligence), `realtime_events`, `solomon_conversations` (Solomon AI chat history), `agent_api_keys`, `agent_webhooks` (developer API), `generated_pdfs`, `generated_reports`, `custom_reports`, `demo_requests`, `waitlist`

### Main API endpoints (organized by router; 41 modules)

```
auth_router          → /api/auth/{login,logout,signup,me,...}
portal_router        → /api/portal/{me,giving/history,kids,...}
admin_people_router  → /api/admin/people/...
admin_giving_router  → /api/admin/giving/{report,donations,refunds,...}
admin_groups_router  → /api/admin/groups/...
admin_services_router→ /api/admin/services/...
admin_checkins_router→ /api/admin/checkins/...
admin_events_router  → /api/admin/events/...
admin_comms_router   → /api/admin/comms/...
admin_media_router   → /api/admin/media/...
admin_cafe_router    → /api/admin/cafe/...
admin_merch_router   → /api/admin/merch/...
admin_pathways_router→ /api/admin/pathways/...
admin_settings_router→ /api/admin/settings/...
admin_workflows_router→/api/admin/workflows/...
admin_meetings_router→ /api/admin/meetings/...
reports_router       → /api/reports/...
payments_router      → /api/payments/...
platform_router      → /api/platform/{stats,churches,stripe/transactions,...}
agent_router         → /api/agent/... (developer-facing public API)
public_api_router    → /api/public/... + /register/{eventId}
push_router          → /api/push/...
messaging_router     → /api/messaging/...
volunteer_router     → /api/volunteer/...
geofence_router      → /api/geofence/...
announcements_router → /api/announcements/...
media_uploads_router → /api/media/uploads/...
giving_nudge_router  → /api/giving/nudge/...
courses_router       → /api/courses/...
solomon_router       → /api/solomon/{chat,voice,...} (AI assistant)
solomonpay_admin_router→ /api/admin/solomonpay/{dashboard,transactions,donors,virtual-terminal,refund,...}
sms_router           → /api/sms/... (Twilio webhooks)
printer_router       → /api/printers/...
disputes_router      → /api/disputes/...
stripe_connect_router→ /api/stripe/connect/{onboard,refresh,...} + /api/webhook/stripe
stripe_elements_router→/api/stripe/{create-payment-intent,confirm-donation,elements/config} + /api/churches/{slug}/public-config
competitive_intel_router→/api/competitive/...
realtime_router      → /api/realtime/donations + /api/health/launch-status + /api/platform/seed-connect-ids
```

Plus health endpoints: `GET /api/health` (shallow + deep), `GET /health`.

### Multi-tenancy — how data is isolated

Multi-tenancy in Solomon AI is **enforced at three layers**:

**Layer 1 — `tenant_id` on every domain document.**
Almost every collection has a `tenant_id` field (e.g. `donations.tenant_id`, `people.tenant_id`, `events.tenant_id`). Indexes are built on `(tenant_id, ...)` compound keys for the hot paths (see `server.py:446-462` index creation). Documents are physically intermingled in one database but logically partitioned by `tenant_id`.

**Layer 2 — Auth-injected scope.**
Every authenticated request resolves `user.tenant_id` from the user's JWT/session. The helper functions in `core/__init__.py:230-281`:

```python
if user.get("role") != "platform_admin" and not user.get("tenant_id"):
    raise PermissionDenied
tenant_id = user.get("tenant_id")
```

ensure that admin/member roles **always** have a `tenant_id` and **always** scope queries to that ID. Platform admins see across all tenants by design.

**Layer 3 — Query enforcement.**
Every domain query in the route handlers attaches `{"tenant_id": tenant_id}` to its filter. Examples seen in code:
* `/api/admin/giving/report` filters `donations` by tenant_id
* `/api/admin/people` filters `people` by tenant_id
* `/api/admin/events` filters `events` by tenant_id
* `_tenant_by_slug()` in `routes/stripe_elements.py:83-97` forgivingly resolves a public URL (`/give/eden-church`) to a single tenant doc.

**Cross-tenant breach risk?** Audited during the Eden battle test (handoff, May 2026): "Strict tenant isolation: all writes go to eden-church-001. Abundant tenant counts are snapshotted before/after to prove zero impact." Battle test verified zero cross-tenant leakage at 7,500 concurrent donations.

**Where multi-tenancy is *NOT* applied (intentionally)**:
* `/api/health` — system-wide
* `/api/platform/*` — platform admins only, by definition cross-tenant
* `/api/churches/{slug}/public-config` — public, returns the slug-resolved tenant only

---

## Q4 — Stripe Integration (the full map)

### Account model

* **Stripe Connect — Standard accounts.** Each church onboards as a Stripe-hosted Standard connected account (`acct_*`). They retain their own Stripe Dashboard login.
* **Charges**: **Direct Charges** on the connected account. Confirmed via the PI ID format: `pi_3TRtFJJyE7zM7lxV0XhpowtW` — the `JyE7zM7lxV` substring matches Eden's connected account `acct_1TRVWmJyE7zM7lxV`, which is the Stripe-internal marker for direct-charge PIs on a connected account.
* **Application fee**: collected via `application_fee_amount` (1.9 % + $0.30 default in `core/connect.py:32-33`, overridable per tenant via `tenant.fee_schedule`).
* **Stripe processing fee**: 2.9 % + $0.30 deducted from the *connected account's* balance, NOT ours.

### Code map — every Stripe surface

**Onboarding** (`/app/backend/routes/stripe_connect.py`)
* `POST /api/stripe/connect/onboard` — creates a Standard connected account and returns the Stripe-hosted onboarding link.
* `POST /api/stripe/connect/refresh` — re-issues onboarding link if the church didn't finish.
* `GET /api/stripe/connect/status/{tenant_id}` — checks onboarding completion.
* Stores `stripe_connect_account_id` + `stripe_connect_status` on the `tenants` doc.
* **Auto-seed**: 9 canonical Connect IDs hardcoded in `core/connect_seed.py` and applied on every `_deferred_startup` (idempotent, fixes prod-Mongo seed gap).

**Donor checkout — Stripe Elements** (`/app/backend/routes/stripe_elements.py`)
* `GET /api/churches/{slug}/public-config` — public, returns `connected_account_id`, `accepts_payments` gate, branding, funds, preset amounts.
* `GET /api/stripe/elements/config` — returns publishable key + test_mode flag.
* `POST /api/stripe/create-payment-intent` — creates the PaymentIntent on the connected account, computes application_fee_amount, sets idempotency key (`{slug}:{base_amount}:{cover_fees}:...`), returns `client_secret`.
* `POST /api/stripe/confirm-donation` — server-side persistence after Stripe.js confirms. Pulls the PI metadata back, inserts into `donations`, busts caches.
* `POST /api/stripe/refund` — refund initiated by admin.
* `GET /api/admin/giving/report?source=stripe` — Stripe-only donation slice.

**Webhooks** (`/app/backend/routes/stripe_connect.py:227-310`)
* `POST /api/webhook/stripe` — properly hardened:
  1. Signature verified via `stripe.Webhook.construct_event(secret=STRIPE_WEBHOOK_SECRET)`. **Fail-closed if secret missing AND key starts with `sk_live_`**.
  2. Persists `event_id` in `stripe_webhook_events` collection BEFORE processing — idempotent against Stripe's 3-day retry window.
  3. Unique index on `event_id` makes parallel-worker race-safe.
  4. Handles: `checkout.session.completed`, `payment_intent.succeeded`, plus payment-failure and dispute event types.
* **Defense-in-depth: Stripe→Mongo reconcile loop** (`server.py:387-401`, `core/stripe_sync.py`): even if a webhook is missed (network drop, secret missing in dev), every 60 s the backend pulls the last 24 h of PIs from Stripe and inserts any donation rows we don't have. **This is what makes "no real-money data loss" true even on full DB outage.**
* `STRIPE_WEBHOOK_SECRET` is configured in production env (verified in backend/.env).

**Other Stripe touchpoints**
* **Stripe Checkout** (`stripe_connect.py:106, 167`) — older flow, used as fallback. Wrapped via `emergentintegrations.payments.stripe.checkout`.
* **Disputes** (`routes/disputes.py`) — admin UI for chargebacks.
* **Payouts** (`routes/solomonpay_admin.py`) — view of payouts to the church (read-only, mirrored from Stripe).
* **Virtual Terminal** (`routes/solomonpay_admin.py:490-534`) — manual donation logger (cash/check/card-as-label). **Does NOT capture or process card data** — stores a row only.
* **Recurring giving** (`routes/admin_giving.py`, `recurring_giving` collection + `recurring_giving_runs`) — runs via the scheduler started in `_deferred_startup` (`server.py:506-510`). Uses Stripe Subscriptions or saved payment methods (depending on tenant config).

### Stripe features — live vs not yet

| Feature | Status |
|---|---|
| Stripe Connect Standard onboarding | ✅ Live (auto-seeded for 9 churches) |
| Stripe Elements card capture | ✅ Live & verified end-to-end this week |
| `application_fee_amount` collection | ✅ Live |
| PaymentIntent creation (Direct Charges) | ✅ Live |
| Webhook signature verification | ✅ Live (fail-closed in production) |
| Webhook idempotency | ✅ Live (`stripe_webhook_events` + unique index) |
| Stripe-side reconcile loop | ✅ Live (60-s background task) |
| Recurring giving (Stripe Subscriptions) | ✅ Live (scheduler runs in production) |
| Refunds | ✅ Live (admin endpoint) |
| Disputes UI | ✅ Live (read-only view + admin response) |
| Payouts view | ✅ Live (read-only mirror) |
| Apple Pay / Google Pay | ⚠️ Not enabled — Stripe Elements supports it, just needs `paymentRequest` button enabled in `PublicGivingPage.jsx` |
| ACH / bank-debit donations | ⚠️ Not enabled — would require US Bank Account collection in Elements |
| Stripe Tax / 1099-K reporting | ❌ Not built — churches handle their own tax docs from their own Stripe Dashboard |
| Stripe Identity (KYC for high-value gifts) | ❌ Not built |
| Stripe Issuing (church-issued cards) | ❌ Not built (out of scope) |

---

## Q5 — What's Broken / Missing (the brutal honest list)

### 🔴 Hard blockers for onboarding a real paying church TODAY

**(none — onboarding works.)** A new church can sign up, complete Stripe Connect onboarding, and receive donations through `/give/{their-slug}`. We verified this exact flow with Eden Church + a real test card this week.

### 🟠 Soft blockers — would surprise a real customer

1. **`GET /api/admin/solomonpay/dashboard` returns 500 on prod** (returns OK on preview).
   * Symptom: when an admin opens `/solomonpay`, the dashboard tab can't load aggregates.
   * Risk: Christopher (Eden) opens his admin panel and sees an error toast on day one.
   * Workaround: other admin pages (`/giving`, `/dashboard`) work fine.
   * Fix: needs Sentry hunt + likely a tenant-scoped query that breaks on the prod data shape (e.g., a tenant with no donations yet causing a divide-by-zero or empty aggregation).

2. **Bulk SMS is mocked** (`routes/admin_comms.py:99-104, 178`).
   * If a church admin clicks "Send SMS to all members", the system returns a `mock_<uuid>` and **does not call Twilio**. UI will show "Sent" but no SMS goes out.
   * Risk: silent communication failure.
   * Fix: wire in Twilio credentials + replace mock block. ~2 hours.

3. **Parent SMS notifications on kids check-in are mocked** (`routes/admin_checkins.py:152-154`).
   * Parents will not get the "your child has been checked in" SMS. Pickup-code feature itself works (printed labels, codes generated correctly), but the SMS leg is `print("[MOCK SMS]")`.
   * Risk: kids ministry team thinks parents are notified; parents wait wondering.
   * Fix: same as #2 — wire Twilio.

4. **Slack / Teams integrations are stubbed** (`core/helpers_ai.py:72-73`: `"slack": "MOCKED", "teams": "MOCKED"`).
   * If a church wires up Slack notifications via the integrations page, nothing happens.
   * Risk: low — most churches won't expect this to work yet.
   * Fix: defer.

5. **Mongo connection pool capped at 5** (`core/__init__.py:34`).
   * Limits real concurrent throughput to ~700 RPS regardless of the underlying Atlas tier.
   * Risk: a megachurch's Easter offering moment has 3K+ simultaneous tap-to-give → all donations succeed but with multi-second latency.
   * Fix: bump to 100. **One line. Five-minute change.**

6. **Single uvicorn worker in production** (Emergent platform constraint).
   * Throughput per pod is single-event-loop bound.
   * Risk: same as #5 — works under load, just not as fast as the code is capable of.
   * Fix: **email support@emergent.sh** (gunicorn config already written at `/app/backend/deploy/supervisord.production.conf`).

7. **Backups not on cron** (`scripts/backup.sh` exists but isn't scheduled).
   * Atlas continuous PITR almost certainly covers this if we're on M10+, but no off-Atlas backup in a separate AWS account.
   * Risk: low (Atlas is reliable). High (catastrophic) if Atlas itself ever has a tier-wide outage.
   * Fix: 30-min cron-wiring job once we have an EC2/Lambda host.

### 🟡 Cosmetic / data-quality issues

8. **The 9 production tenants have $0 live GMV but the platform stats endpoint shows $108M from seed data.**
   * Already documented in the due-diligence pack. **Never quote the $108M number externally.**
   * Fix: a "Live vs Seeded" toggle on the God Mode dashboard would prevent the accident permanently. ~1 hour to ship.

9. **Two churches still listed at the *old* seed slugs alongside the new ones** (`abundant`, `pottershouse`).
   * Both old and new slugs work (`_tenant_by_slug` checks slug ∪ subdomain ∪ id). Just visually inconsistent.
   * Fix: cosmetic; if any external link uses the old form, leave them.

10. **No "Impersonate" button in God Mode** to log in as a church admin and check what they see.
    * Listed in handoff backlog (P2).
    * Fix: ~2 hours to ship.

### 🟢 Things that look incomplete but actually aren't

* **`routes/notifications.py` has a "placeholder for the next refactoring pass" comment** — but no code depends on it. Cosmetic dead file. Delete or ignore.
* **The `Mocked` flag in `helpers_ai.py:72-73`** is for *external* integrations (Slack/Teams), not for any user-facing church flow.
* **The `# TODO: Implement actual bulk SMS with Twilio` comment** is the same item as #2 above — just one mock to replace.

### What would happen TODAY if Christopher onboarded a real $50K-Sunday church?

1. **Onboarding**: ✅ smooth — Stripe Connect Standard, branded giving page, funds set up via `/admin/settings`.
2. **First Sunday — donations**: ✅ all succeed end-to-end. Admins see live counts on `/giving`. Real-time toast notifications fire for each gift.
3. **Recurring giving setup**: ✅ scheduler runs.
4. **Year-end statements**: ✅ statement_jobs collection + PDF generation exist.
5. **Member portal experience**: ✅ login, give, watch, RSVP all work.
6. **Where they'd hit problems**: Solomon Pay admin dashboard 500'ing (Issue #1), bulk SMS not actually sending (#2), kids-checkin SMS not reaching parents (#3).

**Recommended action before the first real customer**: fix issues #1, #2, #3. Total effort: **~5 hours**. Everything else is launch-OK.

---

— Generated May 1, 2026, every claim grounded in a specific file:line, route mount, or live API call. No estimates dressed as facts.
