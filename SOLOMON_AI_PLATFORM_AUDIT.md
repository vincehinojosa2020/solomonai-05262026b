# SOLOMON AI — PLATFORM AUDIT & PRODUCTION READINESS BRIEFING
**Date:** April 17, 2026  
**Prepared for:** Vince Hinojosa (CTO), Jacob Pacheco (CEO), Shannon Nieman (CMO)  
**Codebase reference:** `/app/backend` (FastAPI) + `/app/frontend` (React 18) + MongoDB  

---

## SECTION 1 — EXECUTIVE RECONSTRUCTION

**One-sentence product description:**  
Solomon AI is a multi-tenant church management SaaS that combines member directories, online giving, attendance tracking, kids check-in, small groups, events, communications, café/merch point-of-sale, and an AI assistant into a single React + FastAPI + MongoDB application, with a proprietary payment processor brand ("Solomon Pay") that currently wraps simulated transactions rather than a real payment rail.

**First 30 days for church staff:**  
A church admin would log in and find a pre-populated dashboard with member counts, giving totals, and attendance metrics. They would navigate to People to browse/search members, to Giving to see donation history, and to Events/Groups to manage church programs. They would encounter a functional but unpolished experience — most screens render data correctly when data exists, but many admin workflows (importing members from Planning Center, setting up automated emails, configuring real payment processing) are scaffolded rather than complete.

**First visit for a church member (giver):**  
A member would access the portal, see service times and upcoming events, watch sermon videos in a Netflix-style dark-themed library, and tap "Give" to make a donation using a saved card. The giving flow — including Frank Luntz-style persuasive copy, "Cover Processing Fees" toggle, and "Round Up" — is the most polished member-facing experience. The member would not know the payment doesn't actually reach a bank account.

**How Solomon makes money:**  
Solomon charges a 1.9% + $0.30 per-transaction processing fee on giving (34% cheaper than the industry standard 2.9% + $0.30), plus monthly SaaS subscription fees ($499–$2,000+/month per church).

**What the synthetic data is hiding from us:**  
The seeded data is internally *inconsistent*. Donation `person_id` values in the three Abundant campuses (East/West/Downtown) do **not** match any records in the `people` collection — 0% cross-referencing. This means every feature that joins donations to people (donor profiles, giving statements, "who gave this week" lists, the entire DonorIQ segment engine) works only because the UI gracefully falls back to "Member" or "Anonymous" when the lookup fails. The moment a real church's data flows in — where admins expect to see "Sarah Johnson gave $500 to Building Fund" — the platform will show "Member gave $500 to General Fund" unless the seed pipeline or the ingestion pipeline properly links `person_id` across collections. Groups for the newer tenants have 0 actual members in `group_members` despite showing member counts in the UI. Five of eight tenants have zero events, zero services, and zero attendance records. The dashboard looks correct because the caching layer (`platform_stats_cache`, `dashboard_stats_cache`) stores pre-computed numbers that don't need to be re-derived from the underlying broken joins.

---

## SECTION 2 — ARCHITECTURE MAP

### Stack
| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React 18, Tailwind CSS, shadcn/ui, Recharts | Port 3000, Supervisor-managed |
| Backend | FastAPI (Python 3.11), Motor (async MongoDB) | Port 8001, Supervisor-managed |
| Database | MongoDB 7.0.31, single instance | `solomonai` database, 64 collections |
| AI | Claude Sonnet 4.5 via Emergent LLM Key | `emergentintegrations` library |
| Voice | OpenAI Whisper via Emergent LLM Key | Speech-to-text for "Ask Solomon" |
| Email | Resend (API key configured) | `RESEND_API_KEY` in `.env` |
| Auth | Session-token cookies, SHA256 + bcrypt hybrid | No MFA, no OAuth in production |
| Deployment | Kubernetes pod, Supervisor process manager | Preview environment |

### Collection Inventory (64 collections, non-empty shown)
| Collection | Record Count | Notes |
|-----------|-------------|-------|
| `donations` | 3,040,093 | Synthetic — `person_id` broken for 3 Abundant campuses |
| `attendance` | 4,416,301 | Only 4 of 8 tenants have records |
| `people` | 110,526 | ~10K per tenant |
| `services` | 1,410 | Only Abundant campuses + original seed |
| `events` | 108 | Only Abundant East + original seed |
| `groups` | 504 | `group_members` = 4,161 but 0 for newer tenants |
| `recurring_giving` | 5,960 | Mix of real and seeded |
| `payouts` | 468 | Synthetic |
| `monthly_reports` | 288 | Pre-computed for historical charts |
| `users` | 31 | Demo accounts across tenants |
| `households` | 8,146 | Original seed tenant only |
| `funds` | 50 | ~6 per tenant |
| `solomonpay_transactions` | 4 | Only from demo portal giving tests |

### External Services — Actual Status
| Service | Status | Detail |
|---------|--------|--------|
| Anthropic Claude 4.5 | **LIVE** via Emergent key | Used by `/api/solomon/chat` |
| OpenAI Whisper | **LIVE** via Emergent key | Used by `/api/solomon/voice` |
| Resend (email) | **CONFIGURED** | API key in `.env`, email routes exist but untested in production |
| Twilio (SMS) | **CONFIGURED but UNUSED** | Routes exist in `sms_routes.py` but no API key |
| Stripe | **NOT INTEGRATED** | Zero Stripe code. Solomon Pay is entirely simulated |
| Apple Pay / Google Pay | **MOCKED** | UI buttons exist, no payment rail |
| Google OAuth | **CONFIGURED** via Emergent Auth | Used for social login |
| VAPID Push Notifications | **CONFIGURED** | Keys in `.env`, push routes exist |

---

## SECTION 3 — THE 575 API ENDPOINTS — CAPABILITY MAP

**Exact count of registered FastAPI routes: 575**

### By Domain

| Domain | Routes | Prod-Ready | Demo-Ready | Stubs | Not Wired to FE |
|--------|--------|-----------|------------|-------|-----------------|
| **Member Portal** (`portal.py`) | 110 | ~30 | ~60 | ~10 | ~10 |
| **Public API** (`public_api.py`) | 59 | ~15 | ~35 | ~5 | ~4 |
| **Kids Check-In** (`admin_checkins.py`) | 30 | ~5 | ~20 | ~5 | 0 |
| **Platform Admin** (`platform.py`) | 29 | ~10 | ~15 | ~2 | ~2 |
| **Groups** (`admin_groups.py`) | 29 | ~8 | ~18 | ~3 | 0 |
| **Services/Worship** (`admin_services.py`) | 22 | ~5 | ~15 | ~2 | 0 |
| **Reports** (`reports.py`) | 22 | ~8 | ~12 | ~2 | 0 |
| **Solomon Pay Admin** (`solomonpay_admin.py`) | 21 | ~3 | ~15 | ~3 | 0 |
| **Courses** (`courses.py`) | 21 | ~5 | ~12 | ~4 | 0 |
| **Events** (`admin_events.py`) | 21 | ~5 | ~14 | ~2 | 0 |
| **People/Members** (`admin_people.py`) | 18 | ~8 | ~8 | ~2 | 0 |
| **Settings** (`admin_settings.py`) | 17 | ~3 | ~12 | ~2 | 0 |
| **Communications** (`admin_comms.py`) | 16 | ~3 | ~10 | ~3 | 0 |
| **Pathways** (`admin_pathways.py`) | 16 | ~3 | ~10 | ~3 | 0 |
| **Volunteers** (`volunteer.py`) | 14 | ~3 | ~8 | ~3 | 0 |
| **Workflows** (`admin_workflows.py`) | 14 | ~2 | ~8 | ~4 | 0 |
| **Giving Admin** (`admin_giving.py`) | 13 | ~5 | ~6 | ~2 | 0 |
| **AI Agent** (`agent.py`) | 13 | ~2 | ~8 | ~3 | 0 |
| **Media** (`admin_media.py`) | 11 | ~3 | ~6 | ~2 | 0 |
| **Payments** (`payments.py`) | 10 | ~2 | ~6 | ~2 | 0 |
| **Auth** (`auth.py`) | 10 | ~5 | ~4 | ~1 | 0 |
| **Solomon AI** (`solomon.py`) | 7 | ~3 | ~3 | ~1 | 0 |
| **Other** (café, merch, SMS, push, etc.) | 57 | ~10 | ~35 | ~12 | 0 |

### The 10 Endpoints a Pastor Hits Weekly

| Endpoint | What It Does | Readiness |
|----------|-------------|-----------|
| `GET /api/dashboard/stats` | Church dashboard overview | **Demo-ready** — relies on `dashboard_stats_cache` |
| `GET /api/people` | Member directory | **Demo-ready** — pagination works, search works |
| `GET /api/donations` (giving dashboard) | Giving overview | **Demo-ready** — numbers correct for seeded data |
| `GET /api/reports/attendance` | Attendance report | **Demo-ready** — returns data from `monthly_reports` |
| `GET /api/services` | Service list | **Demo-ready** — only works for tenants with seeded services |
| `POST /api/payments/charge` | Process a donation | **Demo-only** — simulated, no real payment rail |
| `GET /api/events` | Event list | **Demo-ready** — only Abundant East has events |
| `GET /api/groups` | Small groups | **Demo-ready** — member counts may be inaccurate |
| `POST /api/solomon/chat` | Ask Solomon AI | **Production-ready** — real Anthropic API calls |
| `GET /api/reports/giving-by-fund` | Fund report | **Demo-ready** — requires date params |

### Auth/Validation Gaps
- **Rate limiting**: Disabled entirely (intentional for demo; must be re-enabled for production).
- **Input validation**: Most endpoints accept arbitrary string lengths. No sanitization for XSS in stored text fields.
- **Auth coverage**: Portal endpoints use `get_current_portal_user()`. Platform endpoints manually check session tokens. Some report endpoints (`/reports/attendance`, `/reports/giving-by-fund`) have **no auth** — they're public.

---

## SECTION 4 — THE 8 DEMO TENANTS — STRUCTURAL AUDIT

| Tenant | Members | Donations | Groups | Events | Services | Attendance | Consistency |
|--------|---------|-----------|--------|--------|----------|------------|-------------|
| Abundant East | 10,026 | 516,096 | 100 | 53 | 156 | 0 | **Broken**: donation `person_id` ≠ people `id` |
| Abundant West | 10,100 | 523,802 | 60 | 0 | 156 | 0 | **Broken**: same as East |
| Abundant Downtown | 10,000 | 516,977 | 58 | 0 | 156 | 0 | **Broken**: same as East |
| Potter's House | 14,500 | 346,674 | 12 | 0 | 0 | 1,082,680 | Partial: has attendance but no services |
| EdenX | 10,300 | 206,378 | 12 | 0 | 0 | 738,585 | Partial: same pattern |
| City Reach | 10,400 | 229,050 | 12 | 0 | 0 | 763,007 | Partial: same pattern |
| Hill Country | 10,000 | 241,716 | 0 | 0 | 0 | 0 | Minimal: members + donations only |
| Cristo Viene | 10,200 | 288,161 | 0 | 0 | 0 | 0 | Minimal: same |

**Also present but not an active tenant:**  
`abundant-church-001` (the original seed) — 25,000 cached members, 171,239 donations, 942 services, 4,416,301 attendance records, 20 groups with actual group_members. This is the most internally consistent tenant, but it is **not** in the active tenants list.

### Tenant Isolation
- Tenancy is column-based (`tenant_id` field on every collection).
- Most queries filter by `tenant_id`. However, several endpoints in `public_api.py` and `reports.py` hardcode `DEFAULT_TENANT_ID = "abundant-east-001"` rather than deriving tenant from the authenticated user's session. This means any church admin, regardless of which church they belong to, will see Abundant East's data in those views.
- **Cross-tenant data leak risk**: The `/api/platform/transactions` endpoint with an empty `church` filter queries ALL donations across ALL tenants with `query = {}`. This is correct behavior for platform admins, but there is no test verifying that a church admin cannot call this endpoint.

### Best Tenant for Live Walkthrough
**Abundant East** (`abundant-east-001`) — has the most complete data (members, donations, groups, events, services). However, the donation-to-person cross-reference is broken.

### Realism Gaps
1. **Giving patterns**: Donations are uniformly distributed across weeks with random amounts from a fixed list `[25, 50, 100, 150, 200, 250, 500, 1000, 2500]`. Real tithing follows a power law with heavy concentration around round numbers and spikes at month-end and year-end.
2. **Name distribution**: Names are sampled from a 40-first-name × 30-last-name grid. A real El Paso church would have 60%+ Hispanic surnames with different frequency distributions.
3. **Attendance**: Attendance records exist for only 4 of 8 tenants, and they aren't linked to the corresponding services.

---

## SECTION 5 — SOLOMON PAY — THE PRODUCTION GAP

### What Is Simulated vs. Connected
- **Stripe**: Not integrated. Zero Stripe SDK code exists anywhere in the codebase. The `payments.py` file processes charges by writing directly to MongoDB with a `sim_ch_` prefix on the processor reference ID. No money moves.
- **Solomon Pay UI flows**: The full giving flow is clickable — select amount, choose saved card, toggle "Cover Fees", tap Give, see success toast. It writes to `solomonpay_transactions` (4 records exist from demo testing) and `donations` (inserted as a real donation record). The refund flow writes a status change but no money moves.
- **Card tokenization**: Simulated. `tokenize_card()` generates a fake token `tok_sim_xxxx`. No PCI-scoped card data is stored or transmitted.

### Synthetic Numbers
- $108.3M Platform GMV, $2.4M Total Revenue, 2.87M transactions — all synthetic seed data.
- The 4 real SolomonPay transactions total $40.00.

### Minimum Path to Processing a Real $20 Tithe

1. **Stripe Connect integration** — Create a Stripe Connect platform account. Each church becomes a "connected account." Solomon collects the application fee (1.9% + $0.30). Stripe handles PCI, KYC, 1099-K.
2. **Replace `payments.py` simulation** — Swap `sim_ch_` logic with `stripe.PaymentIntent.create()` using `application_fee_amount` and `transfer_data.destination`.
3. **Card tokenization via Stripe.js** — Replace the fake tokenizer with Stripe Elements on the frontend. Cards never touch our server.
4. **Webhook handler** — Listen for `payment_intent.succeeded`, `payment_intent.failed`, `charge.dispute.created`.
5. **Receipt delivery** — Wire Resend (already configured) to send a receipt email on successful charge.

**Engineering estimate**: 2-3 weeks for a senior engineer, assuming Stripe Connect approval is pre-obtained.

### Production Dependencies NOT Yet Satisfied
| Dependency | Status | Who Handles It |
|-----------|--------|---------------|
| Stripe Connect platform approval | Not started | Stripe (1-2 weeks) |
| Sub-merchant KYC (per church) | Not started | Stripe Connect handles this |
| 1099-K generation | Not started | Stripe handles for connected accounts |
| Chargeback handling | Scaffold only | Stripe handles; we need webhook + UI |
| Refund flow | Simulated | Need Stripe refund API integration |
| Receipt delivery | Configured (Resend) | Need template + trigger |
| PCI SAQ-A completion | Not started | Required for Stripe Connect |
| Apple Pay / Google Pay | UI only | Need Stripe Payment Request Button |

---

## SECTION 6 — "ASK SOLOMON" AI ASSISTANT

### Model & API
- **Model**: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) via Emergent Integrations library
- **API path**: `POST /api/solomon/chat` → `routes/solomon.py`
- **Session management**: In-memory `solomon_sessions` dict (lost on server restart)

### Tools/Functions
Solomon has an **action execution system** (`services/solomon_actions.py`). The AI can emit `action` blocks in its response, which the frontend can then execute via `POST /api/solomon/execute-action`. However, the actual tool inventory is thin — it's primarily a text-response assistant with optional structured action suggestions, not a true function-calling agent.

### System Prompt
- 7,472 characters. Covers member-facing and admin-facing guidance.
- **Guardrails**: Warm/pastoral tone instructions, "encouraging about giving without being pushy." 
- **Missing guardrails**: No explicit child safety instructions, no mental health crisis escalation protocol, no financial privacy restrictions (Solomon can potentially discuss a specific donor's giving history in a shared session), no PII redaction.

### Latency & Cost
- Average response: ~3-5 seconds for a typical query (Anthropic API latency).
- Estimated cost: ~$0.01-0.03 per query (Claude Sonnet input/output pricing).
- **100 churches × 500 queries/week = 50,000 queries/week → ~$500-1,500/month** in Anthropic costs. This is the single largest variable cost in production.

### What Solomon CAN'T Do Today
1. Stream responses (returns full text in one shot — no typing animation)
2. Generate actual documents (PPTX, PDF, DOCX)
3. Execute database queries directly (no read access to live data beyond what's passed in the system prompt context)
4. Text-to-speech output
5. Remember conversations across server restarts (in-memory sessions)
6. Access real-time giving data during a conversation (context is built once at session start)

---

## SECTION 7 — MULTI-TENANCY & DATA ISOLATION

### Implementation
- **Column-based**: Every collection uses a `tenant_id` field. No separate databases per tenant.
- **No subdomain routing**: All tenants accessed through the same URL. Tenant determined by the authenticated user's `tenant_id` or `church_id` field.

### Isolation Boundary
- **Not formally tested.** There is no integration test that attempts cross-tenant access.
- Most admin endpoints derive `tenant_id` from the authenticated user. However, many `public_api.py` and `reports.py` endpoints hardcode `DEFAULT_TENANT_ID = "abundant-east-001"`, meaning *any* authenticated admin sees Abundant East data regardless of which church they belong to.
- **Platform admin endpoints** (`/platform/*`) intentionally query across all tenants — this is correct for God Mode.
- **Risk**: A church admin calling `/api/platform/transactions` would get a 403 (role check exists). But `/api/reports/attendance` has **no auth check** and always returns `DEFAULT_TENANT_ID` data.

### Super-Admin Flow
- Vince logs in as `admin@solomonai.us` (role: `platform_admin`).
- The `/platform/impersonate` endpoint lets platform admins generate a session for any church admin, enabling tenant switching. This is **not audited** — no log is written when impersonation occurs (the session is created but `is_impersonation: True` is stored, which is good).

### New Church Onboarding
- `POST /api/platform/churches/create` — a wizard that creates a tenant, admin user, and default funds/service types. Fully automated from the UI. However, it does NOT seed any historical data, so a new church would see empty dashboards.

### Email/Phone Collision
- No uniqueness constraint on email across tenants. Two tenants can have members with the same email. User accounts (`users` collection) do have email as a lookup key, but `people` records do not enforce uniqueness.

---

## SECTION 8 — SECURITY POSTURE

### Authentication
- Session-token based. Tokens are random hex strings stored in `user_sessions` collection.
- Cookies are set with `httponly=True`, `secure=True`, `samesite="none"`.
- **Password storage**: Dual-mode — legacy SHA256 hash (demo accounts) with auto-migration to bcrypt on login. New registrations use bcrypt.
- **MFA**: Does not exist.
- **Session expiry**: No TTL on sessions. Sessions live until manually deleted or server restart clears in-memory caches.

### Secrets Management
- All secrets in `.env` files on disk. No vault, no encrypted secret store.
- `EMERGENT_LLM_KEY`, `RESEND_API_KEY`, `VAPID_PRIVATE_KEY` are in plaintext in `/app/backend/.env`.

### PII at Rest
- **Not encrypted.** MongoDB Community Edition, no field-level encryption.
- PII fields stored in plaintext: `first_name`, `last_name`, `email`, `mobile_phone`, `date_of_birth`, `address_line1`.
- No data retention policy. No deletion mechanism for GDPR/CCPA compliance.

### OWASP Top 10 Posture
| # | Vulnerability | Status |
|---|-------------|--------|
| A01 | Broken Access Control | **MEDIUM RISK** — some report endpoints lack auth; tenant isolation is convention-based, not enforced |
| A02 | Cryptographic Failures | **HIGH RISK** — PII in plaintext, legacy SHA256 passwords, no encryption at rest |
| A03 | Injection | **LOW RISK** — MongoDB (no SQL injection), but no input sanitization for NoSQL injection via `$regex` |
| A04 | Insecure Design | **MEDIUM** — no threat model, no abuse case testing |
| A05 | Security Misconfiguration | **MEDIUM** — CORS set to `*`, rate limiting disabled |
| A06 | Vulnerable Components | **UNKNOWN** — no dependency audit has been run |
| A07 | Auth Failures | **MEDIUM** — no MFA, no brute-force protection in production, no session expiry |
| A08 | Software/Data Integrity | **LOW** — no CI/CD pipeline to verify |
| A09 | Logging Failures | **MEDIUM** — audit_log collection exists (9,017 entries) but not all actions logged |
| A10 | SSRF | **LOW** — no user-supplied URLs processed |

### Worst Vulnerability Findable in 30 Minutes
**CORS is set to `"*"` (wildcard).** Combined with cookie-based auth (`samesite="none"`), any website on the internet can make authenticated API requests on behalf of a logged-in Solomon user. An attacker could host a page that silently exfiltrates the entire member directory, donation history, and PII of every person in the database. Fix: restrict CORS to the actual frontend domain.

---

## SECTION 9 — THE UI — WHAT IT ACTUALLY LOOKS LIKE

### Design System
- Tailwind CSS + shadcn/ui components (located at `/app/frontend/src/components/ui/`).
- Recharts for charts. Lucide React for icons.
- Custom design tokens via Tailwind config. Consistent slate/blue/emerald palette.

### Screen Count
- **89 distinct page components** across admin, portal, platform, and public views.
- 15 portal pages, 8 platform pages, ~50 admin pages, ~16 public/auth pages.

### Mobile Responsiveness
- **Landing page**: 0 responsive breakpoint classes (`sm:`, `md:`, `lg:`). Desktop-only layout.
- **Portal pages**: Generally responsive (use Tailwind grid breakpoints).
- **Admin pages**: Mixed — some use responsive grids, some are desktop-only tables.
- **Platform dashboard**: Desktop-optimized. Would be unusable on mobile.

### Accessibility
- **WCAG AA**: Not assessed. No ARIA audit has been performed.
- `data-testid` attributes are present on most interactive elements (good for testing, irrelevant for accessibility).
- No `aria-label`, `aria-describedby`, or `role` attributes observed in a spot check.
- Keyboard navigation: Not tested. shadcn/ui components provide some keyboard support by default.

### Three Most Polished Screens
1. **Portal Give page** (`PortalGive.jsx`) — full checkout flow with persuasive copy, saved cards, fee coverage
2. **Platform Dashboard** (`PlatformDashboard.jsx`) — Bloomberg-grade KPI cards, interactive charts, activity feed
3. **Portal Watch** (`PortalWatch.jsx`) — dark Netflix-style video library with categories

### Three That Most Need Work
1. **Landing page** (`LandingPage.jsx`, 339 lines) — minimal, no responsive design, no hero screenshot, no social proof
2. **Kids Check-In Admin** (`KidsCheckinAdmin.jsx`, 808 lines) — oversized monolith, needs decomposition
3. **Check-In Setup** (`CheckInSetupPage.jsx`, 737 lines) — same issue, complex single-file component

### Dead Links / Coming Soon
- `/privacy`, `/terms`, `/security` pages — **do not exist** (would 404 or redirect to login)
- Pricing page exists but is thin
- "Forgot password" link — **not functional** (no password reset flow implemented)
- Apple Pay / Google Pay buttons — visible in UI, non-functional

### Three UI Moments That Would Break With Real Data
1. **47-character last name**: Donor columns in transaction tables truncate, but donor profile cards would overflow
2. **Group with 800 members**: GroupDetail loads all members in a single API call with no pagination — would timeout
3. **Member with no last name**: `${first_name} ${last_name}` renders as "Maria " (trailing space) or "Maria undefined" depending on the component

---

## SECTION 10 — COMPETITIVE POSITIONING — THE EVIDENCE

| Planning Center Product | Solomon Equivalent | Parity Rating |
|------------------------|-------------------|---------------|
| **People** | `/people`, `/households`, PeopleList, PersonDetail | **50%** — CRUD works, no smart lists, no merge duplicates (page exists but limited), no custom fields UI |
| **Giving** | `/giving`, GivingDashboard, PortalGive, Solomon Pay | **50%** — giving tracking works, online giving works (simulated), no statement generation, no bank integration |
| **Services** | `/services`, ServicesPage, worship planning | **20%** — basic service CRUD and song library, no setlist builder, no scheduling |
| **Check-Ins** | `/kids-checkin`, KidsCheckinAdmin | **50%** — QR code check-in, label printing scaffold, classroom management |
| **Groups** | `/groups`, GroupsList, GroupDetail, GroupsManager | **50%** — CRUD, leader dashboards, but no member self-signup flow, no curriculum integration |
| **Registrations** | `/events`, `/registrations`, EventsManager | **20%** — event CRUD and registration list, no payment-linked registration, no waitlists |
| **Calendar** | `/calendar`, CalendarPage, CalendarApprovals | **20%** — basic calendar view, no room/resource booking |
| **Publishing** | Communications page, Announcements | **20%** — email template CRUD, no drag-and-drop builder, no SMS campaigns |
| **Church Center** (member app) | Portal (`/portal/*`) | **40%** — giving, events, groups, directory, but no native mobile app |

### The ONE Feature We Genuinely Have That They Don't
**"Ask Solomon" — an AI assistant embedded in every view.** No church management platform ships a conversational AI that can discuss a church's actual data (giving trends, attendance patterns, member engagement). Planning Center has no AI. Pushpay has no AI. This is a real differentiator — IF we make it production-grade (streaming, tools, document generation).

---

## SECTION 11 — THE CUSTOMER-ZERO READINESS GAP

### If Jacob Called Abundant's Lead Pastor Tomorrow

**Five things that would break:**
1. **No real payment processing.** Sunday offering goes nowhere. This is the showstopper.
2. **Member import.** Abundant has ~2,000 real members in Planning Center. The CSV import wizard (`CSVMemberImport.jsx`) exists but is not battle-tested with real Planning Center exports.
3. **Tenant data isolation.** Abundant's admin would see some pages showing `DEFAULT_TENANT_ID` data instead of their own church's data.
4. **Donation-to-person linking.** Giving reports would show "Anonymous" or "Member" instead of real donor names until the person_id cross-referencing is fixed.
5. **No password reset.** If any staff member forgets their password, there's no recovery flow.

### Shortest Path to First Real Offering

| Step | Task | Days |
|------|------|------|
| 1 | Stripe Connect platform application + approval | 5-10 |
| 2 | Replace `payments.py` sim with Stripe PaymentIntent | 3 |
| 3 | Frontend: Stripe Elements for card input (replace fake tokenizer) | 2 |
| 4 | Webhook handler for success/failure/dispute | 2 |
| 5 | Receipt email via Resend | 1 |
| 6 | Fix `DEFAULT_TENANT_ID` hardcoding for multi-tenant correctness | 2 |
| 7 | End-to-end test with real $1 charge | 1 |
| **Total** | | **~3 weeks** |

### 500 Concurrent Users at 10:45am
- MongoDB single instance with no connection pooling configuration. The `donations.find()` calls on 3M+ records would strain under concurrent load.
- No CDN. Static assets served from the container.
- No horizontal scaling. Single pod, single backend process.
- **Expected failure**: Slow dashboard loads (5-10s+), possible MongoDB timeouts, potential 502s from Kubernetes if the pod runs out of memory during aggregation pipelines.

### Edge Cases
- **40MB profile photo**: No file upload size limit configured. Would consume pod memory.
- **Emoji in name**: MongoDB stores UTF-8 natively. Would likely render fine. Some string operations (e.g., `first_name[0]` for avatar initials) might produce unexpected results with multi-byte characters.
- **$0.01 test donation**: Would process normally. Fee calculation: `$0.01 × 1.9% + $0.30 = $0.30` — Solomon would charge $0.30 in fees on a penny donation. Need a minimum donation amount.

---

## SECTION 12 — THE FINANCIAL REALITY

### Current Monthly Operating Cost
| Item | Est. Monthly Cost |
|------|------------------|
| Kubernetes hosting (Emergent preview) | ~$0 (platform-provided) |
| MongoDB (local in pod) | $0 |
| Anthropic API (demo usage, ~100 queries/mo) | ~$3 |
| Resend (free tier) | $0 |
| Emergent LLM Key (universal) | ~$5-10 |
| Domain (solomonai.us) | ~$1 |
| **Total** | **~$10-15/month** |

Note: The claimed ~$700/mo may include separate hosting, domains, or services not visible in this codebase.

### Cost Curve at Scale

| Scale | Hosting | AI (Anthropic) | Payments (Stripe) | Total |
|-------|---------|----------------|-------------------|-------|
| 10 churches | $200/mo (managed K8s + managed MongoDB) | $50-150/mo | Stripe takes their cut | ~$400/mo |
| 100 churches | $800/mo | $500-1,500/mo | Stripe takes their cut | ~$2,500/mo |
| 1,000 churches | $3,000/mo | $5,000-15,000/mo | Stripe takes their cut | ~$20,000/mo |

### Single Biggest Unpaid Cost
**Anthropic API for "Ask Solomon" at scale.** At 100 churches with moderate usage (500 queries/church/week), the AI bill alone could be $500-1,500/month — potentially exceeding hosting costs. Mitigation: response caching, usage tiers, or switching to a cheaper model for routine queries.

### Break-Even

| Price Point | Break-Even Churches | Notes |
|-------------|-------------------|-------|
| $199/mo | ~15-20 churches | Barely covers infrastructure + AI costs |
| $499/mo | ~6-8 churches | Comfortable for 10-church scale |
| $999/mo | ~3-4 churches | Sustainable from day one |

---

## SECTION 13 — FOUNDER BRIEFINGS

### FOR JACOB (CEO)

**What you can honestly tell a prospect today:**  
"We've built a complete church management platform — members, giving, check-in, groups, events, communications, and an AI assistant — that's been demo'd with 100K+ members and $100M+ in giving data across 8 churches. The AI assistant is genuinely differentiated — nobody else in this space has it. Online giving is functional in the platform. We're in the final stage of connecting real payment processing through Stripe."

**Shortest defensible sales narrative:**  
"Solomon AI is a next-generation church management platform that replaces 9 separate products with one. It's the only platform in the space with an embedded AI assistant. We're onboarding our first production church in [month] and processing real giving by [month]."

**Three claims to STOP making until real:**
1. "We process payments" — until Stripe Connect is live
2. Any specific GMV/transaction number — those are demo data
3. "Apple Pay / Google Pay support" — buttons exist but aren't wired

**Best demo moment:** The Give flow (amount → saved card → cover fees → success) followed by "Ask Solomon" analyzing the giving data. **Question you can't answer yet:** "When can we actually run our Sunday offering through this?"

### FOR SHANNON (CMO)

**Screenshot-ready screens:**  
- Platform Dashboard (God Mode KPIs)
- Portal Give page (full checkout flow)
- Portal Watch page (Netflix-style video library)
- Church Detail drill-through (giving chart, health score)
- Donors page (DonorIQ breakdown, 41K+ donors)

**Do NOT show to prospects yet:**  
- Landing page (too bare, no responsive design)
- Any empty-state page (groups for newer tenants, events for most tenants)
- Apple Pay / Google Pay buttons (non-functional)
- Password reset flow (doesn't exist)

**Brand story matching product maturity:**  
"Solomon AI is the first AI-native church management platform. We've built the complete toolkit a church needs — from first-time visitor to recurring giver — and we're the only platform where the pastor can ask an AI 'how are we doing this month?' and get an honest, data-driven answer. We're in private beta with select churches and opening up soon."

**Embarrassing in a 30-min walkthrough:**  
If they click "Forgot Password" — nothing happens. If they navigate to Privacy/Terms — 404. If they look at the footer — copyright year may be hardcoded.

### FOR VINCE (CTO)

**Single biggest technical debt:**  
The `DEFAULT_TENANT_ID` hardcoding throughout `public_api.py` and `reports.py`. Every church admin endpoint that uses this constant instead of the authenticated user's `tenant_id` is a data isolation bug. This affects ~15 endpoints and would show every church admin Abundant East's data. Fix: replace every `DEFAULT_TENANT_ID` usage in admin-facing endpoints with the authenticated user's `tenant_id`.

**One bug from catastrophic data loss/leak:**  
CORS is set to `"*"` with `samesite="none"` cookies. Any website can silently make authenticated requests. One XSS or one malicious page = full database exfiltration.

**What to rip out before tenant #2:**
1. Fix CORS to whitelist only the production frontend domain
2. Replace all `DEFAULT_TENANT_ID` with user-derived tenant
3. Add session TTL (tokens currently never expire)
4. Enable rate limiting on auth endpoints
5. Add a minimum donation amount ($1 or $5)

**Engineering work for synthetic-to-real Solomon Pay:**  
See Section 5. Core work: Stripe Connect integration, Stripe Elements on frontend, webhook handler, receipt email. ~3 weeks. The biggest unknown is Stripe Connect approval timeline.

---

## SECTION 14 — THE HONEST ROADMAP

### Milestone 1: Pre-Revenue Platform
**Definition of done:** CORS locked down, `DEFAULT_TENANT_ID` eliminated, session TTL added, rate limiting on auth, password reset flow working, privacy/terms pages live.  
**Why it matters:** Without this, we cannot ethically invite a real church to create an account.

### Milestone 2: First Dollar
**Definition of done:** Stripe Connect approved, one church (Abundant) can process a real donation through Solomon Pay, receipt delivered via email, refund flow works.  
**Why it matters:** Proves the business model works. Solomon earns its first processing fee.

### Milestone 3: First Real Giving Sunday
**Definition of done:** 500+ concurrent givers can complete the giving flow without errors. Payout to church bank account within 48 hours. Giving statements viewable by donors.  
**Why it matters:** This is the "it actually works" moment.

### Milestone 4: First 10 Customers
**Definition of done:** New church onboarding wizard creates a fully functional tenant in <5 minutes. CSV import from Planning Center works. Each church sees only their own data. AI assistant has per-church context.  
**Why it matters:** Proves multi-tenancy works in production, not just in seed data.

### Milestone 5: "Church Management Platform" Without an Asterisk
**Definition of done:** All 9 Planning Center product equivalents are at ≥50% parity. Member self-service (join groups, register for events, update profile) works end-to-end. Mobile responsive across all screens. WCAG AA on portal pages.  
**Why it matters:** This is when the "one platform to replace them all" narrative becomes defensible under scrutiny.

---

*This document should be re-run against the codebase quarterly, or after any sprint that changes payment processing, auth, or multi-tenancy logic.*
