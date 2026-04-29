# SOLOMON AI — COMPLETE PLATFORM ARCHITECTURE
## Technical Reference Document for Engineering Leadership
### Version 2.0 — April 2026

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Business Architecture — Multi-Tenancy Model](#2-business-architecture)
3. [Infrastructure Overview — GCP + Kubernetes](#3-infrastructure)
4. [Technology Stack — Full Inventory](#4-technology-stack)
5. [Backend Architecture — FastAPI + MongoDB](#5-backend-architecture)
6. [Frontend Architecture — React + Shadcn/UI](#6-frontend-architecture)
7. [Data Architecture — 57 Collections Documented](#7-data-architecture)
8. [Authentication & RBAC — Role System](#8-authentication-and-rbac)
9. [Solomon Pay — Proprietary Payment Processor](#9-solomon-pay)
10. [Solomon AI — Intelligence Layer](#10-solomon-ai)
11. [Multi-Campus Architecture](#11-multi-campus-architecture)
12. [Security Architecture](#12-security-architecture)
13. [Platform Operations — God Mode](#13-god-mode)
14. [Feature Inventory — All 561 Endpoints](#14-feature-inventory)
15. [Data Scale & Performance](#15-data-scale-and-performance)
16. [Integration Architecture](#16-integrations)
17. [Design System](#17-design-system)
18. [Build Pipeline & Deployment](#18-build-and-deployment)

---

## 1. EXECUTIVE SUMMARY

Solomon AI is a **multi-tenant church management SaaS platform** with a proprietary payment processor (Solomon Pay). It competes with Planning Center, Pushpay, SecureGive, and Tithely by owning the full payment stack and charging lower fees.

### Key Numbers (Live, April 2026)

| Metric | Value |
|--------|-------|
| API Endpoints | 561 |
| Frontend Pages | 88 |
| Database Collections | 57 |
| Active Church Tenants | 7 |
| Total Members on Platform | 90,326 |
| Total Donations Processed | 2,496,016 |
| Platform GMV (All-Time) | $96,841,797 |
| Platform Revenue (Fees) | $1,821,135 |
| MRR | $20,299 |
| ARR | $243,598 |
| Avg Transaction Size | $38.80 |

### Fee Structure (Our Competitive Advantage)
- **Card**: 1.9% + $0.30 (industry: 2.9% + $0.30 — 34% cheaper)
- **ACH**: 0.8% + $0.30 (industry: 1.0% + $0.30)
- **Cash/Check**: $0

---

## 2. BUSINESS ARCHITECTURE — MULTI-TENANCY MODEL

### The AWS Model Applied to Church Software

Solomon AI operates on the same principle as AWS: **one flagship platform, infinite tenant isolation**. Every church is a fully isolated tenant. They share infrastructure but share zero data.

```
┌─────────────────────────────────────────────────────────────┐
│                     SOLOMON AI PLATFORM                     │
│                   (solomonai.us / GCP)                      │
│                                                             │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │  Abundant Church │  │ Potter's House │  │ City Reach │ │
│  │  (Multi-Campus)  │  │   (Dallas TX)  │  │ (Cedar Pk) │ │
│  │                  │  │                │  │            │ │
│  │ ┌─────────────┐  │  │ tenant_id:     │  │ tenant_id: │ │
│  │ │Abundant East│  │  │ potters-house  │  │ cityreach  │ │
│  │ │   -001      │  │  │     -001       │  │   -001     │ │
│  │ └─────────────┘  │  └────────────────┘  └────────────┘ │
│  │ ┌─────────────┐  │                                      │
│  │ │Abundant West│  │  ┌────────────────┐  ┌────────────┐ │
│  │ │   -001      │  │  │    EdenX       │  │  TEST_     │ │
│  │ └─────────────┘  │  │  Ministries    │  │ (filtered  │ │
│  │ ┌─────────────┐  │  │  (Folsom CA)   │  │  out of    │ │
│  │ │Abundant Down│  │  └────────────────┘  │  God Mode) │ │
│  │ │    town-001 │  │                      └────────────┘ │
│  │ └─────────────┘  │                                      │
│  └──────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

### Tenant Isolation Rules

Every single MongoDB query is scoped by `tenant_id`. There are no cross-tenant queries except at the platform admin level (God Mode). If a query does not include `tenant_id`, it will not return data.

**Enforcement pattern (in every route):**
```python
# Example: Get people for a church
people = await db.people.find(
    {"tenant_id": tenant_id},  # ALWAYS required
    {"_id": 0}
).to_list(100)
```

**Platform admin exception:** God Mode aggregates across all `tenant_ids` in the campuses array, but only after role verification (`user.role == "platform_admin"`).

### Church Onboarding

New churches are onboarded in under 3 minutes via:
1. God Mode → "Add New Church" wizard
2. 5 steps: Name/Location → Service Times → Branding → Admin Account → Review
3. On submit: tenant created, admin user created, subdomain activated, welcome email sent
4. New tenant starts empty — no seed data, clean slate

---

## 3. INFRASTRUCTURE — GCP + KUBERNETES

### Deployment Architecture

```
Internet
   │
   ▼
┌─────────────────────────────────────┐
│    Cloudflare (CDN + DDoS Layer)    │
│    solomonai.us / *.solomonai.us    │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│    GCP / Kubernetes Cluster         │
│    (Emergent Platform — Managed K8s)│
│                                     │
│  ┌────────────────────────────────┐ │
│  │  Kubernetes Ingress (nginx)    │ │
│  │  /api/* → Port 8001 (Backend)  │ │
│  │  /*     → Port 3000 (Frontend) │ │
│  └────────────────────────────────┘ │
│          │              │            │
│   ┌──────▼──────┐ ┌────▼──────┐    │
│   │  Backend Pod │ │Frontend   │    │
│   │  FastAPI     │ │Pod React  │    │
│   │  Uvicorn     │ │CRA/Craco  │    │
│   │  Port 8001   │ │Port 3000  │    │
│   └──────┬───────┘ └───────────┘    │
│          │                           │
│   ┌──────▼───────┐                  │
│   │  MongoDB Pod │                  │
│   │  localhost   │                  │
│   │  :27017      │                  │
│   │  DB: solomonai│                 │
│   └──────────────┘                  │
└─────────────────────────────────────┘
```

### Process Management (Supervisor)

Both services are managed by `supervisord`:

```ini
[program:backend]
command=uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload
directory=/app/backend

[program:frontend]
command=yarn start
environment=HOST="0.0.0.0",PORT="3000"
directory=/app/frontend

[program:mongodb]
command=mongod --bind_ip_all
```

### Environment Configuration

**Backend** (`/app/backend/.env`):
```
MONGO_URL=mongodb://localhost:27017     # local dev fallback
DB_NAME=solomonai                       # always "solomonai"
EMERGENT_LLM_KEY=...                    # Claude API via Emergent
CORS_ORIGINS=*
```

**Frontend** (`/app/frontend/.env`):
```
REACT_APP_BACKEND_URL=https://[preview].emergentagent.com
```

> **Production override**: Emergent injects the real Atlas MONGO_URL and production REACT_APP_BACKEND_URL as OS environment variables at container start. python-dotenv respects existing env vars (does not override them), so production values always win.

### AI Provider — Anthropic Claude via Emergent

All AI functionality uses **Anthropic Claude Sonnet 4.5** through Emergent's universal LLM key system:

```python
from emergentintegrations.llm.chat import LlmChat, UserMessage

chat = LlmChat(
    api_key=os.environ.get('EMERGENT_LLM_KEY'),
    session_id=session_id,
    system_message=full_system_prompt
)
chat.with_model("anthropic", "claude-sonnet-4-5-20250929")
response = await chat.send_message(UserMessage(text=message))
```

The Emergent LLM key is a single unified key that works across Anthropic, OpenAI, and Google Gemini models. The platform uses Anthropic Claude exclusively for the Solomon AI assistant.

---

## 4. TECHNOLOGY STACK — FULL INVENTORY

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Web Framework | **FastAPI** | 0.110.1 | REST API, async endpoints |
| ASGI Server | **Uvicorn** | Latest | Production HTTP server |
| Database Driver | **Motor** | Latest | Async MongoDB driver |
| Database | **MongoDB** | Latest | Primary datastore |
| AI Integration | **emergentintegrations** | 0.1.0 | Claude LLM via Emergent key |
| PDF Generation | **ReportLab** | 4.4.10 | Tax statements, investor reports |
| Password Hashing | **bcrypt** | 4.1.3 | User password security |
| HTTP Client | **aiohttp** | 3.13.3 | External API calls |
| AWS SDK | **boto3** | 1.42.51 | S3 object storage (scaffolded) |
| Data Validation | **Pydantic** | v2 | Request/response schemas |
| Email Validation | **email-validator** | 2.3.0 | Signup validation |
| Env Vars | **python-dotenv** | Latest | .env file loading |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| UI Framework | **React** | 18 | Component-based UI |
| Build Tool | **Craco** | Latest | CRA config extension |
| Router | **React Router** | v6 | Client-side routing |
| UI Components | **Shadcn/UI** | Latest | Accessible component library |
| Primitives | **Radix UI** | Latest | Headless accessible primitives |
| Charts | **Recharts** | Latest | All data visualization |
| Calendar | **FullCalendar** | 6.1.20 | Calendar views (month/week/day) |
| Forms | **React Hook Form** | Latest | Form state management |
| Styling | **Tailwind CSS** | v3 | Utility-first CSS |
| Icons | **Lucide React** | Latest | All iconography |
| Notifications | **Sonner** | Latest | Toast notifications |
| HTTP | **fetch API** | Native | All API calls |
| State | **useState/useContext** | React 18 | Local + shared state |

### No External State Management
The platform uses **React's built-in useState and custom hooks** only. No Redux, Zustand, or MobX. Each page component owns its data and fetches directly via `fetch()`.

---

## 5. BACKEND ARCHITECTURE — FASTAPI + MONGODB

### Directory Structure

```
/app/backend/
├── server.py                    # Entry point — FastAPI app, all router mounts
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (dev fallback)
│
├── core/                        # Shared utilities
│   ├── __init__.py              # DB client, session helpers, RATE_LIMITS, caching
│   ├── auth.py                  # Auth middleware, get_current_admin_user()
│   ├── helpers.py               # compute_health_score(), serialize_doc(), etc.
│   ├── helpers_ai.py            # Solomon system prompts, get_church_context()
│   ├── seed.py                  # Seed orchestration
│   ├── seed_accounts.py         # Demo account creation
│   ├── seed_commerce.py         # Cafe + merch demo data
│   └── seed_pathways.py         # Academy/discipleship demo data
│
├── models/
│   └── schemas.py               # Pydantic request/response models
│
├── routes/                      # 35 route modules (561 endpoints total)
│   ├── server.py                # [ENTRY] Mounts all routers
│   ├── auth.py                  # Login, logout, session, OAuth
│   ├── platform.py              # God Mode: all-church aggregations
│   ├── portal.py                # Member portal: give, groups, events
│   ├── solomon.py               # Ask Solomon AI chat + action execution
│   ├── payments.py              # Solomon Pay: tokenize, charge, refund
│   ├── solomonpay_admin.py      # Solomon Pay admin dashboard
│   ├── admin_people.py          # People directory, households, bulk ops
│   ├── admin_giving.py          # Fund management, donations, statements
│   ├── admin_groups.py          # Small groups CRUD, membership
│   ├── admin_services.py        # Service plans, songs, positions
│   ├── admin_checkins.py        # Kids check-in, classrooms, pickup codes
│   ├── admin_events.py          # Events, registrations, calendar
│   ├── admin_comms.py           # Email/SMS, templates, scheduled sends
│   ├── admin_media.py           # Video library, sermons
│   ├── admin_cafe.py            # Cafe menu, orders, POS
│   ├── admin_merch.py           # Merchandise catalog, inventory
│   ├── admin_pathways.py        # Discipleship courses, enrollments
│   ├── admin_settings.py        # Church config, branding, integrations
│   ├── admin_workflows.py       # Automated care workflows
│   ├── admin_meetings.py        # Staff/leader meetings
│   ├── reports.py               # All analytics + report generation
│   ├── agent.py                 # AI agent HTTP endpoints
│   ├── public_api.py            # Dashboard stats, public endpoints
│   ├── push.py                  # Web push notifications (VAPID)
│   ├── messaging.py             # In-app messaging
│   ├── volunteer.py             # Volunteer management, scheduling
│   ├── geofence.py              # Location-aware check-in
│   ├── announcements.py         # Church announcements
│   ├── media_uploads.py         # File upload handling
│   ├── giving_nudge.py          # Post-purchase giving prompts
│   ├── courses.py               # Solomon Academy LMS
│   ├── sms_routes.py            # Twilio SMS integration
│   └── printer_routes.py        # DYMO/Brother label printer
│
├── services/                    # Background services
│   ├── processor_adapter.py     # Solomon Pay charge simulation adapter
│   ├── recurring_scheduler.py   # Hourly recurring giving processor
│   ├── solomon_actions.py       # 14 AI action handlers
│   ├── websocket_service.py     # Real-time WebSocket connections
│   ├── print_service.py         # Label print orchestration
│   └── sms_service.py           # Twilio SMS service wrapper
│
└── scripts/                     # Data scripts
    ├── seed_master.py           # Abundant Church 3-year seed (25K members)
    ├── seed_extended.py         # Potter's House, EdenX, City Reach
    ├── seed_abundant_campuses.py # East, West, Downtown campus seed
    └── refactor_analysis.py     # Codebase analysis utilities
```

### Request Lifecycle

```
Browser Request
      │
      ▼
Cloudflare (TLS termination, DDoS)
      │
      ▼
Kubernetes Ingress
      │ Route: /api/* → port 8001
      ▼
FastAPI (Uvicorn)
      │
      ├── CORS Middleware (allow_origins=[solomonai.us, *.preview.emergentagent.com])
      │
      ├── Session Extraction (get_session_token_from_request)
      │       └── Reads "Authorization: Bearer {token}" header
      │
      ├── Route Handler
      │       ├── Auth check (get_current_admin_user / get_current_portal_user)
      │       ├── Tenant resolution (user.tenant_id or DEFAULT_TENANT_ID)
      │       ├── MongoDB query (always filtered by tenant_id)
      │       └── Response (serialize_doc removes _id ObjectId)
      │
      └── Response (JSON)
```

### Key Shared Utilities (`core/__init__.py`)

```python
# Database client
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=20000,
    socketTimeoutMS=45000,
    maxPoolSize=5,
    minPoolSize=0,
)
db = client[DB_NAME]  # Always "solomonai"

# Session auth pattern
async def get_current_admin_user(request):
    token = get_session_token_from_request(request)
    session = await db.user_sessions.find_one({"session_token": token})
    user = await db.users.find_one({"user_id": session["user_id"]})
    return user  # Contains role, tenant_id, permissions[]

# In-memory caching (5-min TTL for dashboard stats)
async def cache_get(key: str): ...
async def cache_set(key: str, value, ttl_seconds: int = 300): ...

# In-memory rate limiting (login: 5 attempts / 15-min lockout)
RATE_LIMITS = {}
def check_rate_limit_v2(bucket, max_requests, window_seconds): ...
```

### Background Services

```python
# Startup sequence (server.py)
@app.on_event("startup")
async def startup():
    # Returns in MILLISECONDS — critical for health probe
    loop = asyncio.get_event_loop()
    loop.call_later(0, lambda: asyncio.ensure_future(_deferred_startup()))

async def _deferred_startup():
    await asyncio.sleep(60)          # Atlas MongoDB warmup
    await ensure_mobile_demo_accounts()
    await seed_vol_data()
    await seed_academy_course()
    await asyncio.sleep(30)
    start_scheduler(db)              # Recurring giving scheduler
```

**Recurring Giving Scheduler** (`services/recurring_scheduler.py`):
- Runs every 3,600 seconds (1 hour) via `asyncio` background task
- Queries `recurring_giving` where `next_charge_date <= today AND is_active = true`
- Idempotency guard: `last_processed_date` prevents double-charging
- Retry logic: 3 attempts over 3 days, then auto-pause + notification
- Logs every run to `recurring_giving_runs` collection

---

## 6. FRONTEND ARCHITECTURE — REACT + SHADCN/UI

### Directory Structure

```
/app/frontend/src/
├── App.js                       # Root router — all 88 routes
├── App.css                      # Global styles (16,000+ lines)
│
├── pages/                       # 88 page components
│   ├── LandingPage.jsx          # Public marketing page
│   ├── LoginPage.jsx            # Unified login (email/pw + Google OAuth)
│   ├── Dashboard.jsx            # Church admin home
│   ├── PlatformDashboard.jsx    # God Mode (platform_admin only)
│   ├── GodModeDashboard.jsx     # Legacy God Mode wrapper
│   │
│   ├── platform/                # God Mode sub-components
│   │   ├── PlatformExecDashboard.jsx  # Hero KPIs, charts
│   │   ├── PlatformChurches.jsx       # Portfolio table + health scores
│   │   ├── PlatformTransactions.jsx   # All-church transaction table
│   │   ├── PlatformPayouts.jsx        # Payout history
│   │   ├── PlatformRevenue.jsx        # Revenue breakdown
│   │   ├── PlatformDonors.jsx         # Donor analytics
│   │   └── PlatformSupport.jsx        # Support tickets
│   │
│   ├── portal/                  # Member-facing pages
│   │   ├── PortalHome.jsx       # Member home dashboard
│   │   ├── PortalGive.jsx       # Online giving
│   │   ├── PortalGroups.jsx     # Browse + join groups
│   │   ├── PortalEvents.jsx     # Event discovery
│   │   ├── PortalMe.jsx         # Profile + giving history
│   │   ├── PortalWatch.jsx      # Sermon library
│   │   ├── PortalCafe.jsx       # Cafe ordering
│   │   ├── PortalMerch.jsx      # Merch store
│   │   ├── PortalCourses.jsx    # Academy courses
│   │   └── PortalPrayer.jsx     # Prayer wall
│   │
│   └── [admin pages]            # 50+ church admin pages
│       ├── PeopleList.jsx       # Member directory
│       ├── GivingDashboard.jsx  # Stewardship
│       ├── SolomonPayAdmin.jsx  # Payment processor admin
│       ├── ServicesPage.jsx     # Worship planning
│       ├── GroupsList.jsx       # Small groups
│       ├── CheckInSetupPage.jsx # Kids check-in config
│       ├── KidsCheckinAdmin.jsx # Check-in operations
│       ├── CalendarPage.jsx     # FullCalendar view
│       ├── CommunicationsPage.jsx # Email/SMS
│       ├── ReportsPage.jsx      # 9-tab analytics
│       ├── WorkflowsPage.jsx    # Automation builder
│       ├── CustomReportBuilder.jsx # Report wizard
│       └── ...
│
├── components/                  # 50+ shared components
│   ├── layout/
│   │   ├── AppShell.jsx         # Church admin shell (dark sidebar)
│   │   ├── PortalLayout.jsx     # Member portal shell
│   │   └── AppShellNav.js       # Navigation config
│   │
│   ├── ui/                      # Shadcn/UI components (30+)
│   │   ├── button.jsx
│   │   ├── dialog.jsx
│   │   ├── input.jsx
│   │   ├── select.jsx
│   │   ├── tabs.jsx
│   │   └── ...
│   │
│   ├── SolomonChat.jsx          # AI assistant chat widget
│   ├── SolomonPayForm.jsx       # Payment form
│   ├── HelpTooltip.jsx          # Contextual help (ℹ️)
│   ├── FeatureEducationHeader.jsx # Page education banners
│   ├── LabelPrinter.jsx         # DYMO/Brother label printing
│   ├── KioskCheckin.jsx         # Full-screen kiosk mode
│   ├── CampusSelectorModal.jsx  # Multi-campus first login
│   ├── ChurchOnboardingWizard.jsx # New church wizard
│   ├── MultiPaymentSelector.jsx # Payment method picker
│   └── ...
│
├── hooks/                       # Custom React hooks
│   ├── useWebSocket.js          # Real-time connection (window.location.origin)
│   └── usePolling.js            # API polling helper
│
├── lib/
│   ├── utils.js                 # API_URL, formatCurrency, formatDate
│   └── helpContent.js           # 30+ contextual help entries
│
└── styles/
    └── labels.css               # DYMO/Brother label print styles
```

### Routing Architecture

```javascript
// App.js — Three routing contexts

// 1. PUBLIC (no auth required)
<Route path="/" element={<LandingPage />} />
<Route path="/login" element={<LoginPage />} />
<Route path="/auth/callback" element={<AuthCallback />} />

// 2. PLATFORM ADMIN — Standalone (no AppShell)
<Route path="/platform" element={
  <ProtectedRoute requiredRole="platform_admin">
    <PlatformDashboard />    // Has its own sidebar
  </ProtectedRoute>
} />

// 3. CHURCH ADMIN — Inside AppShell (church admin sidebar)
<Route element={
  <ProtectedRoute requiredRole="admin">
    <AppShell />
  </ProtectedRoute>
}>
  <Route path="/dashboard" element={<Dashboard />} />
  <Route path="/giving" element={<GivingDashboard />} />
  <Route path="/people" element={<PeopleList />} />
  // ... 40+ admin routes
</Route>

// 4. MEMBER PORTAL — Inside PortalLayout
<Route path="/portal" element={<PortalLayout />}>
  <Route index element={<PortalHome />} />
  <Route path="give" element={<PortalGive />} />
  // ... 12 portal routes
</Route>
```

### State Management Pattern

No global state library. Each page is self-contained:

```javascript
export default function GivingDashboard() {
  // Local state
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // Auth headers from sessionStorage
  const token = sessionStorage.getItem('session_token');
  const headers = { 'Authorization': `Bearer ${token}` };

  // API call (always to /api/* relative path)
  useEffect(() => {
    fetch(`${API_URL}/giving/stats`, { headers })
      .then(r => r.json())
      .then(setStats);
  }, []);
}

// utils.js
export const API_URL = '/api';  // Relative — works on any domain
```

---

## 7. DATA ARCHITECTURE — 57 COLLECTIONS DOCUMENTED

### Core Entities

#### `tenants`
Church organization record. The root of all data.
```json
{
  "id": "abundant-east-001",
  "name": "Abundant East",
  "city": "El Paso",
  "state": "TX",
  "subscription_status": "active",
  "plan": "standard",
  "primary_color": "#1e40af",
  "subdomain": "abundanteast",
  "parent_organization": "Abundant",
  "created_at": "2023-01-15T00:00:00Z"
}
```

#### `users`
Authentication identities. One user per church (typically), or multi-role users.
```json
{
  "user_id": "uuid",
  "email": "pastor@church.com",
  "name": "Pastor James",
  "role": "church_admin",
  "tenant_id": "abundant-east-001",
  "password_hash": "bcrypt",
  "home_campus_id": "abundant-east-001",
  "campus_selected": true,
  "created_at": "..."
}
```

**Roles:** `platform_admin` | `church_admin` | `admin` | `member`

#### `people`
Church directory. Every member, visitor, contact.
```json
{
  "id": "uuid",
  "tenant_id": "abundant-east-001",
  "first_name": "Maria",
  "last_name": "Garcia",
  "email": "maria@email.com",
  "mobile_phone": "(915) 555-1234",
  "membership_status": "member",
  "membership_date": "2019-03-15",
  "gender": "F",
  "age": 34,
  "date_of_birth": "1990-03-15",
  "home_campus_id": "abundant-east-001",
  "share_email": true,
  "share_phone": false,
  "share_address": false
}
```

#### `user_sessions`
Active authentication sessions (UUID tokens).
```json
{
  "session_token": "sess_abc123...",
  "user_id": "uuid",
  "created_at": "...",
  "expires_at": "..."  // TTL index for auto-expiry
}
```

### Financial Collections

#### `donations`
Every financial transaction. Core of the platform.
```json
{
  "id": "uuid",
  "tenant_id": "abundant-east-001",
  "person_id": "uuid",
  "donor_name": "Maria Garcia",
  "fund_id": "uuid",
  "fund_name": "General Fund",
  "amount": 250.00,
  "fee_amount": 5.05,        // 1.9% + $0.30
  "net_amount": 244.95,
  "donation_date": "2025-11-17",
  "payment_method": "card",  // card | ach | cash | check
  "status": "completed",
  "source": "solomonpay",
  "is_recurring": false,
  "transaction_id": "sp_abc123",
  "created_at": "2025-11-17T10:30:00Z"
}
```
**Scale**: 2,496,016 records — largest collection by volume.

#### `recurring_giving`
Scheduled giving plans.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "person_id": "uuid",
  "fund_id": "uuid",
  "amount": 100.00,
  "frequency": "monthly",     // weekly | biweekly | monthly | annually
  "next_charge_date": "2026-05-01",
  "last_processed_date": "2026-04-01",
  "is_active": true,
  "consecutive_failures": 0,
  "payment_method_id": "uuid",
  "solomonpay_token": "tok_..."
}
```

#### `payouts`
Weekly disbursements to churches.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "church_name": "Abundant East",
  "gross_amount": 45230.50,
  "total_fees": 855.00,
  "net_payout": 44375.50,
  "payout_date": "2025-11-21",
  "status": "completed",
  "bank_last_four": "4242"
}
```

#### `funds`
Giving designations.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "name": "Building Fund",
  "goal_amount": 2500000,
  "current_amount": 1847320,
  "is_active": true
}
```

### Ministry Collections

#### `groups`
Small groups, Bible studies, ministry teams.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "name": "Tuesday Night Life Group",
  "group_type": "life_group",
  "leader_id": "uuid",
  "meeting_day": "Tuesday",
  "meeting_time": "7:00 PM",
  "capacity": 20,
  "member_count": 14,
  "is_open": true,
  "is_active": true
}
```

#### `service_plans`
Worship service planning.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "title": "Sunday 9AM Service",
  "date": "2026-04-06",
  "items": [
    {"type": "song", "title": "Great Is Thy Faithfulness", "key": "G", "duration": 5},
    {"type": "prayer", "title": "Opening Prayer", "duration": 3},
    {"type": "sermon", "title": "The Sermon on the Mount", "duration": 45}
  ],
  "team_assignments": [
    {"role": "Worship Leader", "user_name": "Carlos M."},
    {"role": "Sound", "user_name": "Sarah J."}
  ]
}
```

#### `checkins`
Kids check-in records with pickup codes.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "child_id": "uuid",
  "child_name": "Emma Johnson",
  "classroom": "Kindergarten — Room 104",
  "service_date": "2026-04-06",
  "pickup_code": "X7K2",
  "status": "checked_in",
  "allergies": "Peanuts",
  "checked_in_at": "2026-04-06T09:15:00Z"
}
```

#### `events`
All church events.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "name": "Men's Prayer Breakfast",
  "event_date": "2026-04-18",
  "start_time": "07:00",
  "end_time": "09:00",
  "location": "Fellowship Hall",
  "event_type": "community",
  "requires_registration": true,
  "price": 0,
  "pricing_type": "free",
  "recurring": "monthly",
  "is_public": true
}
```

### Communication Collections

#### `communications`
Email/SMS campaign records.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "subject": "This Sunday at Abundant East",
  "body": "Hi {{first_name}}, this Sunday...",
  "channel": "email",
  "recipient_type": "all",
  "status": "sent",            // draft | scheduled | sending | sent
  "scheduled_at": null,
  "sent_count": 4287,
  "created_by": "uuid",
  "created_at": "..."
}
```

#### `email_templates`
Reusable email templates.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "name": "Welcome New Member",
  "subject": "Welcome to {{church_name}}, {{first_name}}!",
  "body": "Dear {{first_name}}, Welcome...",
  "category": "onboarding",
  "is_builtin": false
}
```

#### `prayer_requests`
Community prayer wall.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "user_id": "uuid",
  "author_name": "Anonymous",
  "text": "Please pray for healing...",
  "is_public": true,
  "prayer_count": 14,
  "status": "active",
  "created_at": "..."
}
```

### Commerce Collections

#### `cafe_items`
Church cafe menu.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "name": "Latte",
  "price": 5.00,
  "category": "drinks",
  "image_url": "https://images.unsplash.com/...",
  "is_available": true,
  "inventory_count": null
}
```

#### `cafe_orders`
Cafe purchase records.
```json
{
  "id": "uuid",
  "tenant_id": "...",
  "member_id": "uuid",
  "items": [{"name": "Latte", "quantity": 1, "price": 5.00}],
  "total": 5.00,
  "pickup_time": "9:30 AM",
  "status": "ready",
  "payment_method": "card_on_file"
}
```

#### `merch_products` / `merch_orders`
Church store catalog and purchase records.

### AI Collections

#### `solomon_conversations`
AI chat history per session.
```json
{
  "session_id": "...",
  "tenant_id": "...",
  "user_id": "uuid",
  "messages": [
    {"role": "user", "content": "What's our MRR?"},
    {"role": "assistant", "content": "**$20,299.88 MRR**..."}
  ],
  "created_at": "..."
}
```

### Platform-Only Collections

#### `recurring_giving_runs`
Scheduler audit log.
```json
{
  "id": "run_abc123",
  "run_date": "2026-04-04",
  "total_scheduled": 2450,
  "successful": 2431,
  "failed": 7,
  "skipped": 12,
  "duration_ms": 34521,
  "errors": [...]
}
```

#### `dashboard_stats_cache`
Pre-computed KPI cache (5-min TTL).
```json
{
  "tenant_id": "...",
  "total_members": 10000,
  "active_members": 8300,
  "mtd_giving": 287500,
  "ytd_giving": 2400000,
  "mtd_goal": 200000,
  "last_attendance": 4565,
  "recurring_givers": 1200,
  "active_groups": 84,
  "updated_at": "..."
}
```

---

## 8. AUTHENTICATION AND RBAC

### Auth Flow

```
1. User submits email + password (or Google OAuth)
2. Backend checks bcrypt hash in users collection
3. Rate limit check: 5 failures = 15-min lockout (in-memory RATE_LIMITS{})
4. On success: create session in user_sessions collection
5. Return session_token (UUID) to frontend
6. Frontend stores token in sessionStorage (clears on tab close)
7. Backend sets httpOnly cookie as primary auth method
8. Every subsequent request: Authorization: Bearer {token}
```

### Role Hierarchy

```
platform_admin
    │  Full access to all tenants, God Mode dashboard
    │  Can: view all churches, impersonate admins, create tenants
    │
    ▼
church_admin
    │  Full access to ONE tenant
    │  Can: manage all church data, view all members, process payments
    │
    ▼
admin (legacy)
    │  Equivalent to church_admin in most contexts
    │
    ▼
leader (implicit)
    │  Group leader — sees their group's data only
    │
    ▼
member
    │  Portal access only
    │  Can: give, register for events, join groups, chat with Solomon
    │  Cannot: see other members' data (except public directory)
```

### Permission System

Beyond roles, the platform has a granular permission system:
```python
ROLE_TEMPLATES = {
    "church_admin": [
        "admin.people.view", "admin.people.edit",
        "admin.giving.view", "admin.giving.edit",
        "admin.groups.manage", "admin.services.manage",
        "admin.checkin.manage", "admin.comms.send",
        "admin.reports.view", "admin.settings.edit",
        # ... 40+ permissions
    ],
    "volunteer_coordinator": [
        "admin.volunteers.manage",
        "admin.services.view",
    ],
    "give_admin": [
        "admin.giving.view", "admin.giving.edit",
        "admin.giving.refund",
    ]
}
```

### Google OAuth Flow

```
User clicks "Sign in with Google"
    │
    ▼
Redirect to https://auth.emergentagent.com/?redirect={origin}/platform
    │
    ▼
Emergent Auth (Google OAuth 2.0)
    │
    ▼
Callback: GET /auth/callback?session_id={id}
    │
    ▼
Backend: POST /api/auth/session {session_id}
    ├── Exchange session_id → Google profile via Emergent
    ├── Match email to existing user → log in
    └── Return {session_token, role} → route by role
        ├── platform_admin → /platform
        ├── church_admin → /dashboard
        └── member → /portal
```

---

## 9. SOLOMON PAY — PROPRIETARY PAYMENT PROCESSOR

### Architecture Philosophy

> "We ARE the payment processor. We don't integrate with Stripe. We don't integrate with Pushpay. We ARE the payment stack."

Solomon Pay is a **processor-adapter pattern**:

```
Donor enters card → Solomon Pay Tokenizer
                          │
                          ▼
                    Token stored (never raw card)
                          │
                          ▼
                    PROCESSOR_ADAPTER
                    (SimulationAdapter in dev,
                     Real acquirer API in prod)
                          │
                          ▼
                    Charge result
                          │
                          ▼
                    solomonpay_transactions (ledger)
                          │
                          ▼
                    donations record created
```

### Fee Calculation

```python
SOLOMON_FEE_RATE = 0.019   # 1.9% (card)
SOLOMON_FEE_FLAT = 0.30    # $0.30 flat

def calculate_fee(amount, method):
    if method == "card":
        return round(amount * 0.019 + 0.30, 2)
    elif method == "ach":
        return round(min(amount * 0.008 + 0.30, 5.00), 2)  # ACH capped at $5
    else:
        return 0.00  # cash / check
```

### Admin Dashboard (8 Tabs)

The `/solomonpay` route exposes an 8-tab admin console:
1. **Overview** — Real-time giving, MTD/YTD stats
2. **Transactions** — Full ledger with filter/search/export
3. **Recurring** — Active schedules, scheduler status, retry queue
4. **Donors** — Donor profiles, giving history, DonorIQ
5. **Funds** — Fund management, goal tracking
6. **Payouts** — Weekly disbursement history
7. **Virtual Terminal** — Manual card entry for staff
8. **Settings** — Fee display, cover-fee toggle

### Recurring Scheduler

```python
# services/recurring_scheduler.py
SCHEDULER_INTERVAL_SECONDS = 3600  # Every hour

async def run_recurring_batch(db):
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    due = await db.recurring_giving.find({
        "is_active": True,
        "next_charge_date": {"$lte": today_str}
    }).to_list(500)
    
    for schedule in due:
        # Idempotency check
        if schedule.get("last_processed_date") == today_str:
            continue  # Already processed today
        
        # Charge via adapter
        result = await ACTIVE_ADAPTER.charge_card(token, amount_cents)
        
        if result.status == ChargeStatus.SUCCESS:
            # Create donation record
            # Advance next_charge_date
            # Reset consecutive_failures
        else:
            # Increment failures
            # If failures >= 3: auto_pause + notify donor
```

---

## 10. SOLOMON AI — INTELLIGENCE LAYER

### Context Routing

Solomon AI detects the user's role and injects the appropriate context:

```python
@router.post("/solomon/chat")
async def solomon_chat(request, payload):
    user = await _get_user_safe(request)
    user_role = user.get("role")
    
    if user_role == "platform_admin":
        # GOD MODE: inject all-church platform stats
        system_prompt = await build_platform_admin_context()
        # Includes: 7 churches, $96.8M GMV, MRR, ARR, per-church breakdown
    else:
        # CHURCH/MEMBER: inject that church's data
        system_prompt = await get_church_context(user)
        # Includes: members, giving, events, groups, member's personal data
```

### 14 Action Types

Solomon can execute real actions — not just answer questions:

| Action | What It Does |
|--------|-------------|
| `donate` | Process a gift through Solomon Pay |
| `recurring_giving_create` | Set up a new recurring schedule |
| `recurring_giving_pause` | Pause an active recurring gift |
| `recurring_giving_resume` | Resume a paused schedule |
| `recurring_giving_cancel` | Cancel a recurring schedule |
| `event_registration` | Register for an event ("Save My Spot") |
| `group_join` | Join a small group |
| `group_leave` | Leave a small group ("Step Away") |
| `cafe_order` | Place a cafe order |
| `merch_order` | Purchase merchandise |
| `kids_checkin` | Check in children for service |
| `prayer_request` | Submit a prayer request |
| `generate_statement` | Generate PDF tax statement via ReportLab |
| `member_checkin` | Check in member for service |

### Action Parsing Pattern

Solomon's responses include a structured action block:

```
User: "Give $100 to the building fund"

Solomon response:
"Let me take care of that for you. Here's your gift summary before we confirm..."

```action
{
  "action_type": "donate",
  "params": {
    "amount": 100,
    "fund": "Building Fund"
  }
}
```"
```

The frontend parses this, shows a confirmation card:
```
┌─────────────────────────────────────┐
│ Gift Confirmation                   │
│                                     │
│ Amount:     $100.00                 │
│ Fund:       Building Fund           │
│ Payment:    Visa ending 4242        │
│                                     │
│  [ ✓ Confirm ]   [ ✗ Cancel ]      │
└─────────────────────────────────────┘
```

On confirm, the backend executes the action, creates the donation record, and charges the card.

### PDF Generation (ReportLab)

```python
# Tax statement generation example
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table

async def _generate_statement(params, user_id, tenant_id):
    donations = await db.donations.find(
        {"person_id": user_id, "donation_date": {"$regex": f"^{year}"}}
    ).to_list(500)
    
    # Build PDF with ReportLab
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = [church_header, donor_info, donation_table, legal_disclaimer]
    doc.build(elements)
    
    # Store in generated_pdfs collection
    await db.generated_pdfs.insert_one({"id": pdf_id, "content": pdf_bytes})
    
    # Return download URL in chat
    return {"pdf_download": f"/portal/giving/statement-pdf/{pdf_id}"}
```

---

## 11. MULTI-CAMPUS ARCHITECTURE

### The Challenge

Abundant Church has 3 physical campuses:
- Abundant East (El Paso, TX) — 10,000 members
- Abundant West (El Paso, TX) — 10,100 members
- Abundant Downtown (El Paso, TX) — 10,000 members

**Member experience rule**: Members see "Abundant" — not "Abundant East." The campus is a detail, not the brand.

**Admin rule**: Each campus admin sees only their campus data.

**Founder rule**: The church founder sees all three campuses in a unified view.

### Implementation

#### Member Portal Branding

```javascript
// PortalLayout.jsx
const getChurchDisplayName = () => {
  const name = tenant?.name || '';
  // Strip campus suffix
  const suffixes = [' East', ' West', ' Downtown', ' North', ' South', ' Central'];
  for (const suffix of suffixes) {
    if (name.endsWith(suffix)) {
      return name.slice(0, -suffix.length).toUpperCase();  // "ABUNDANT"
    }
  }
  return name.toUpperCase();
};
```

#### Campus Selector (First Login)

```javascript
// CampusSelectorModal.jsx — shown on first portal login
"Which campus do you call home?"
  [ Abundant East ]
  [ Abundant West ]
  [ Abundant Downtown ]
  [ This is my campus → ]
```

The selection is stored on `users.home_campus_id` and used as the default for:
- Giving campus dropdown
- Event/group filtering
- Cafe order routing

#### Campus Detection API

```python
@router.get("/portal/campuses")
async def get_available_campuses(request):
    # Auto-detect parent org from name suffix
    name = current_tenant.get("name", "")
    for suffix in [" East", " West", " Downtown", ...]:
        if name.endswith(suffix):
            parent_name = name[:-len(suffix)]
            break
    
    # Find all tenants sharing the parent name
    all_campuses = await db.tenants.find(
        {"name": {"$regex": f"^{parent_name}"}},
    ).to_list(10)
    
    return {"campuses": campuses, "is_multi_campus": len(campuses) > 1}
```

#### Founder Unified View (Planned)

The `parent_organization` field in tenants enables cross-campus aggregation:
```json
{
  "id": "abundant-east-001",
  "parent_organization": "Abundant"
}
```

Planned: A "Founder" role (above church_admin, below platform_admin) that:
- Sees aggregated giving across all 3 Abundant campuses
- Can post church-wide communications
- Cannot see other churches (Potter's House, EdenX, etc.)
- Gets a unified dashboard showing combined metrics

---

## 12. SECURITY ARCHITECTURE

### Defense Layers

| Layer | Implementation |
|-------|---------------|
| Network | Cloudflare DDoS + rate limiting |
| Transport | TLS 1.3 via Cloudflare |
| Auth | bcrypt hashed passwords, UUID session tokens |
| Session | httpOnly cookies (primary) + sessionStorage (fallback) |
| Rate Limiting | 5 login attempts per account = 15-min lockout |
| CORS | Explicit origin whitelist (solomonai.us + preview domains) |
| Tenant Isolation | Every query requires tenant_id |
| Input Validation | Pydantic schemas on all POST/PUT endpoints |
| PCI Compliance | Raw card data never stored — tokenized via Solomon Pay adapter |
| RBAC | Role + permission check on every protected endpoint |

### CORS Configuration

```python
ALLOWED_ORIGINS = [
    os.environ.get("FRONTEND_URL", ""),
    "https://solomonai.us",
    "https://www.solomonai.us",
    "https://app.solomonai.us",
]
# Dynamic: also allows the current preview URL
if preview_url:
    ALLOWED_ORIGINS.append(preview_url)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.preview\.emergentagent\.com",
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
)
```

### Rate Limiting Pattern

```python
# In-memory rate limiter (resets on server restart)
# Production: should migrate to MongoDB-backed for persistence
RATE_LIMITS = {}

def check_rate_limit_v2(bucket, max_requests, window_seconds):
    now = time.time()
    if bucket not in RATE_LIMITS:
        RATE_LIMITS[bucket] = {"count": 0, "window_start": now}
    entry = RATE_LIMITS[bucket]
    if now - entry["window_start"] > window_seconds:
        RATE_LIMITS[bucket] = {"count": 1, "window_start": now}
        return True
    entry["count"] += 1
    return entry["count"] <= max_requests
```

---

## 13. GOD MODE — PLATFORM ADMIN DASHBOARD

### Access Control

God Mode is accessible only to users with `role = "platform_admin"`. One such user exists: `admin@solomonai.us`.

The `/platform` route is **completely standalone** — it has its own sidebar and does not use the church admin `AppShell` component. This prevents any data leakage between the platform view and church views.

### Dashboard Sections

| Section | What It Shows |
|---------|--------------|
| **Dashboard** | Hero KPIs (GMV/Revenue/MRR/ARR), stacked bar chart, revenue trend, church portfolio table, activity feed, attention required |
| **Churches** | All 7 church cards with health score dimensions |
| **Transactions** | All 2.5M+ transactions across all churches, searchable/filterable |
| **Payouts** | 468 payout records, by church |
| **Revenue** | $1.82M fees by church, by year, monthly trend |
| **Donors** | 35,837 unique donors, DonorIQ breakdown, top 20 by lifetime giving |
| **Reports** | 9-tab analytics + Cross-Analysis correlations |
| **Settings** | Fee structure display, platform config |

### Health Score Algorithm

Each church receives an A-F composite grade based on 5 dimensions:

```python
def compute_health_score(cached_stats, tenant):
    members = cached_stats.get("total_members", 0)
    active = cached_stats.get("active_members", 0)
    mtd = cached_stats.get("mtd_giving", 0) or ytd/month_of_year  # proxy if mtd=0
    groups = cached_stats.get("active_groups", 0)
    recurring = cached_stats.get("recurring_givers", 0)
    attendance = cached_stats.get("last_attendance", 0)

    # Five dimensions, weighted:
    engagement  = (active / members) * 100          # 25%
    giving      = (mtd / members)   / 8 * 100       # 25% — target: $8/member/month
    community   = (groups / members) * 100 / 1.0    # 20% — target: 1 group/100 members
    attendance  = (attendance / members) * 100 / 20 # 20% — target: 20% attendance rate
    growth      = (recurring / members) * 100 / 10  # 10% — target: 10% recurring rate

    score = (engagement * 0.25 + giving * 0.25 +
             community * 0.20 + attendance * 0.20 +
             growth * 0.10)

    # A+ ≥ 90, A ≥ 80, B+ ≥ 70, B ≥ 60, C ≥ 50, D ≥ 40, F < 40
```

### Impersonation

```python
@router.post("/platform/impersonate")
async def impersonate_church(request):
    # Verify caller is platform_admin
    # Find church admin user for the target tenant
    church_admin = await db.users.find_one(
        {"tenant_id": tenant_id, "role": "church_admin"}
    )
    # Create a new session scoped to that church admin
    session_token = f"sess_{secrets.token_hex(16)}"
    await db.user_sessions.insert_one({
        "session_token": session_token,
        "user_id": church_admin["user_id"],
        "impersonated_by": platform_admin_user_id,
    })
    return {"token": session_token}
```

---

## 14. FEATURE INVENTORY — ALL 561 ENDPOINTS

### Auth (auth.py — ~25 endpoints)
- POST /api/auth/login — Email/password login
- POST /api/auth/logout — Session invalidation
- GET /api/auth/me — Current user profile
- POST /api/auth/session — Google OAuth session exchange
- POST /api/auth/register — New user registration
- POST /api/auth/change-password — Password update
- PUT /api/auth/profile — Update user profile

### Member Portal (portal.py — ~120 endpoints)
- GET /api/portal/me — Member profile
- GET /api/portal/give/summary — Giving history + YTD
- POST /api/portal/give — Process donation
- GET /api/portal/funds — Available giving funds
- GET /api/portal/groups — Browse groups
- POST /api/portal/groups/join — Join a group
- GET /api/portal/events — Upcoming events
- POST /api/portal/events/register — Register for event
- GET /api/portal/giving/statement/{year} — Download tax statement PDF
- GET /api/portal/campuses — Multi-campus list + home campus
- POST /api/portal/campus/select — Set home campus
- PUT /api/portal/profile/privacy — Directory privacy toggles
- GET /api/portal/payment-methods — Saved cards
- POST /api/portal/payment-methods — Add card
- GET /api/portal/attendance-streak — Consecutive Sundays
- GET /api/portal/service-mode — Current service state
- GET /api/portal/next-steps/status — Discipleship journey
- GET /api/portal/notifications — In-app notifications
- GET /api/portal/events — Calendar events

### Solomon AI (solomon.py — ~10 endpoints)
- POST /api/solomon/chat — Main AI conversation
- POST /api/solomon/execute-action — Confirmed action execution
- GET /api/solomon/sessions — Conversation history

### Platform / God Mode (platform.py — ~80 endpoints)
- GET /api/platform/stats — Aggregate platform KPIs
- GET /api/platform/churches — All 7 churches with metrics
- GET /api/platform/health-scores — A-F grades per church
- GET /api/platform/transactions — All 2.5M transactions
- GET /api/platform/payouts — Payout history
- GET /api/platform/revenue — Fee revenue breakdown
- GET /api/platform/donors — Platform-wide donor analytics
- GET /api/platform/activity-feed — Real-time donation events
- POST /api/platform/impersonate — Log in as church admin
- POST /api/platform/churches/create — Onboard new church

### People Management (admin_people.py — ~30 endpoints)
- GET /api/admin/people — Directory list with search/filter
- POST /api/admin/people — Create person
- GET /api/admin/people/{id} — Person detail
- PUT /api/admin/people/{id} — Update person
- GET /api/admin/people/duplicates — Duplicate detection
- POST /api/admin/people/bulk-update — Bulk status update
- GET /api/admin/households — Household management
- POST /api/admin/smart-lists — Smart list creation

### Giving / Solomon Pay (admin_giving.py + solomonpay_admin.py — ~80 endpoints)
- GET /api/giving/stats — MTD/YTD giving summary
- GET /api/admin/funds — Fund list
- POST /api/admin/funds — Create fund
- GET /api/admin/donations — Donation records
- POST /api/admin/donations — Manual donation entry
- GET /api/admin/recurring-giving — Active schedules
- GET /api/admin/solomonpay/dashboard — 8-tab payment processor dashboard
- POST /api/admin/solomonpay/scheduler/run-now — Trigger batch run
- GET /api/admin/solomonpay/scheduler/status — Scheduler health
- GET /api/admin/giving/statements — Tax statement generation

### Groups (admin_groups.py — ~25 endpoints)
- GET /api/admin/groups — Group directory
- POST /api/admin/groups — Create group
- GET /api/admin/groups/{id} — Group detail
- GET /api/admin/groups/{id}/members — Member roster
- POST /api/admin/groups/{id}/members — Add member
- GET /api/admin/groups/{id}/attendance — Attendance history

### Services / Worship (admin_services.py — ~30 endpoints)
- GET /api/admin/services/plans — Service plan list
- POST /api/admin/services/plans — Create plan
- PUT /api/admin/services/plans/{id} — Update plan
- GET /api/admin/songs — Song library
- POST /api/admin/songs — Add song
- GET /api/admin/volunteers — Volunteer roster
- GET /api/admin/services/templates — Service templates

### Kids Check-In (admin_checkins.py — ~30 endpoints)
- GET /api/admin/checkin/sessions — Check-in sessions
- POST /api/admin/checkin/checkin — Check in child
- POST /api/admin/checkin/checkout — Check out child
- GET /api/admin/checkin/family-lookup?phone= — Kiosk phone lookup
- GET /api/admin/checkin/locations — Location config
- GET /api/admin/checkin/stations — Station config

### Events & Calendar (admin_events.py — ~25 endpoints)
- GET /api/admin/events — Event list
- POST /api/admin/events — Create event
- GET /api/admin/events/calendar — FullCalendar format
- POST /api/admin/events/{id}/clone — Clone event
- POST /api/admin/registrations — Register attendee
- GET /api/admin/calendar/rooms — Room availability

### Communications (admin_comms.py — ~25 endpoints)
- GET /api/admin/communications/list — Communication history
- POST /api/admin/communications/send — Send email/SMS
- GET /api/admin/communications/templates — Template library
- POST /api/admin/communications/templates — Save template
- GET /api/admin/communications/scheduled — Scheduled queue
- POST /api/admin/communications/cancel/{id} — Cancel scheduled

### Reports (reports.py — ~30 endpoints)
- GET /api/reports/giving-by-fund — Giving breakdown
- GET /api/reports/attendance — Attendance analytics
- GET /api/reports/groups — Group analytics
- GET /api/reports/membership — Member growth
- GET /api/reports/executive-summary — Cross-domain summary
- GET /api/admin/reports/custom — Saved custom reports
- POST /api/admin/reports/custom/preview — Run custom query
- POST /api/admin/reports/custom/export — CSV export
- GET /api/admin/audit-log — Full audit trail

### Commerce (admin_cafe.py + admin_merch.py — ~30 endpoints)
- GET /api/admin/cafe/menu — Cafe menu
- POST /api/admin/cafe/orders — Place order
- GET /api/admin/cafe/orders — Order history
- GET /api/admin/merch/products — Product catalog
- POST /api/admin/merch/orders — Process purchase

### Academy / Courses (courses.py — ~25 endpoints)
- GET /api/admin/courses — Course catalog
- POST /api/admin/courses/{id}/enroll — Enroll member
- GET /api/admin/courses/{id}/progress — Track completion
- GET /api/portal/courses — Member course list

### Settings (admin_settings.py — ~20 endpoints)
- GET /api/admin/settings — Church configuration
- PUT /api/admin/settings — Update settings
- GET /api/admin/settings/branding — Logo/colors
- PUT /api/admin/settings/branding — Update branding
- GET /api/admin/settings/integrations — Integration status

---

## 15. DATA SCALE AND PERFORMANCE

### MongoDB Indexing

50+ compound indexes were created during Phase 1 to optimize query performance:

```python
# Key indexes (all include tenant_id for isolation)
await db.donations.create_index([("tenant_id", 1), ("donation_date", -1)])
await db.donations.create_index([("tenant_id", 1), ("person_id", 1)])
await db.donations.create_index([("tenant_id", 1), ("fund_id", 1)])
await db.people.create_index([("tenant_id", 1), ("membership_status", 1)])
await db.people.create_index([("tenant_id", 1), ("email", 1)], unique=True)
await db.groups.create_index([("tenant_id", 1), ("is_active", 1)])
await db.checkins.create_index([("tenant_id", 1), ("service_date", -1)])
await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
```

**Impact**: Before indexing, `GET /api/platform/revenue` took 6.3 seconds. After: 1.05 seconds.

### Caching Layer

```python
# In-memory cache (core/__init__.py)
_cache: dict = {}
_cache_ttl: dict = {}

# Dashboard stats: 5-minute TTL
cache_key = f"dashboard_stats_{tenant_id}"
cached = await cache_get(cache_key)
if cached:
    return cached
result = await db.dashboard_stats_cache.find_one({"tenant_id": tenant_id})
await cache_set(cache_key, result, ttl_seconds=300)
```

### Current Scale

| Collection | Records |
|-----------|---------|
| donations | 2,496,016 |
| checkins | ~600,000 |
| attendance | ~1,500,000 |
| people | 90,326 |
| groups | ~600 |
| service_plans | ~1,000 |
| payouts | 468 |
| user_sessions | ~30 |

---

## 16. INTEGRATIONS

### Active Integrations

| Integration | Status | Purpose |
|-------------|--------|---------|
| **Anthropic Claude** | ✅ Active | Solomon AI assistant (via Emergent LLM key) |
| **Google OAuth** | ✅ Active | "Sign in with Google" (via Emergent Auth) |
| **FullCalendar** | ✅ Active | Church calendar views |
| **ReportLab** | ✅ Active | PDF generation (tax statements, reports) |

### Scaffolded (Zero Code Changes to Activate)

| Integration | What's Built | Activation |
|-------------|-------------|-----------|
| **Twilio SMS** | Service wrapper, UI prompt, all sending code | Add TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN to .env |
| **Resend Email** | Template system, send logic | Add RESEND_API_KEY to .env |
| **CCLI Reporting** | Song usage tracking in service plans | Enable in settings UI |
| **Background Checks** | UI tab, status field on person profiles | Connect Checkr/PMM API |
| **Apple Pay** | Payment Request API code | Runs when browser supports it |
| **Google Pay** | Payment Request API code | Runs when browser supports it |
| **Zapier** | Webhook endpoints scaffolded | Configure in Zapier dashboard |

### Removed (by design)

- ❌ Stripe — "We ARE the payment processor"
- ❌ Pushpay — Competitor
- ❌ SecureGive — Competitor
- ❌ Tithely — Competitor
- ❌ Planning Center Giving — Competitor
- ❌ Slack — Not needed for church use case
- ❌ Microsoft Teams — Same

---

## 17. DESIGN SYSTEM

### Visual Identity

The platform uses a custom design system built on Tailwind CSS with Shadcn/UI as the component foundation.

**Color Palette:**
```css
:root {
  --solomon-dark: #0f172a;     /* Sidebar, dark headers */
  --solomon-blue: #3b82f6;     /* Primary actions */
  --solomon-slate: #1e293b;    /* Text, secondary */
}
```

**Typography:** Inter (300-800 weight) + Nunito (700-900 for display)

**Component Library:** Shadcn/UI (Radix UI primitives + Tailwind) — components live in `/app/frontend/src/components/ui/`

### Three Visual Contexts

1. **Landing Page** — Dark navy hero, blue accents, marketing-focused
2. **Church Admin** — Clean white/slate, sidebar dark, data-dense cards
3. **Member Portal** — Warm and welcoming, mobile-first, quick-action cards

### Design Rules (Frank Luntz Principles)

| Old | New |
|-----|-----|
| "Make a Donation" | "Give" |
| "Donation Amount" | "Gift Amount" |
| "Submit Payment" | "Complete Your Gift" |
| "Register" | "Save My Spot" |
| "Log Out" | "Sign Out" |
| "Dashboard" (portal) | "Home" |
| "Tax Statement" | "Year-End Giving Summary" |
| "Check In" | "I'm Here" |
| "Recurring Donation" | "Scheduled Giving" |

---

## 18. BUILD AND DEPLOYMENT

### Current State

The platform runs on **Emergent's managed Kubernetes** infrastructure on GCP. Two deployment environments:

1. **Preview**: `https://startup-automation.preview.emergentagent.com` — development/staging
2. **Production**: `https://solomonai.us` — live (via Cloudflare → Emergent K8s)

### Deployment Process

```
Developer → Emergent Chat → "Deploy" button
                │
                ▼
        Emergent Build Pipeline
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
   yarn build         pip install
   (React → static)   (FastAPI + deps)
        │                │
        └───────┬────────┘
                │
                ▼
        Docker image build
                │
                ▼
        Push to GCR (Google Container Registry)
                │
                ▼
        Kubernetes rolling deploy
                │
                ▼
        Health check: GET /health → 200 OK (< 10 seconds)
```

### Health Check Design

The `/health` endpoint **must return 200 within 10 seconds** of startup. This is why all startup operations are deferred:

```python
@app.get("/health")
async def health_check_root():
    return {"status": "ok"}  # Zero DB calls. Responds in <10ms.

@app.on_event("startup")
async def startup():
    # Returns INSTANTLY — just schedules deferred work
    asyncio.ensure_future(_deferred_startup())

async def _deferred_startup():
    await asyncio.sleep(60)   # Wait for Atlas connection pool
    await ensure_mobile_demo_accounts()
    await seed_vol_data()
    # ... etc
```

### Domain Architecture (Planned)

```
solomonai.us                    → Platform landing / God Mode login
admin.solomonai.us              → Church admin login redirect
abundant.solomonai.us           → Abundant Church member portal
pottershouse.solomonai.us       → Potter's House member portal
edenx.solomonai.us              → EdenX Ministries portal
cityreach.solomonai.us          → City Reach Church portal
```

Subdomain routing via hostname detection:
```javascript
// Planned: hostname → tenant mapping
const hostname = window.location.hostname;
const subdomain = hostname.split('.')[0];
if (subdomain !== 'solomonai' && subdomain !== 'www') {
    // tenant = lookup(subdomain)  → set portal context
}
```

---

## APPENDIX A — THE 14-PHASE MASTER BUILD DIRECTIVE

This is what was built over the engineering engagement:

| Phase | What Was Built | Status |
|-------|---------------|--------|
| 1 | DB rename → `solomonai`, 50+ MongoDB indexes, 25K-member Abundant seed | ✅ Done |
| 2 | Solomon Pay proprietary processor, recurring scheduler, ledger | ✅ Done |
| Stripe Removal | Zero Stripe references anywhere in codebase | ✅ Done |
| God Mode | 7-tab platform admin dashboard, health scores, impersonation | ✅ Done |
| Kids Printer | DYMO/Brother web print labels, kiosk mode | ✅ Done |
| Help System | HelpTooltip on all pages, 30+ help entries | ✅ Done |
| Calendar | FullCalendar (month/week/day), recurring events | ✅ Done |
| Communications | Email template builder, Twilio scaffold | ✅ Done |
| Google OAuth | Sign in with Google, role-based routing | ✅ Done |
| Multi-Campus | Campus selector, "Abundant" branding, campus dropdown | ✅ Done |
| Abundant Campuses | East/West/Downtown seeded (30K members, 1.5M donations) | ✅ Done |
| God Mode P0/P1 | Solomon platform context, donors fixed, revenue fixed | ✅ Done |
| Workflow Builder | Visual node-based automation builder | ✅ Done |
| Report Builder | 7-step custom report wizard | ✅ Done |
| Services Expansion | Live Mode, 9 item types, CCLI tracking | ✅ Done |
| People Enhancements | Bulk update, journey funnel, directory privacy | ✅ Done |
| Technical Hardening | Caching, startup fixes, health probe | ✅ Done |
| Code Quality | Secrets from test files, hook deps, array keys | ✅ Done |

---

## APPENDIX B — PLATFORM METRICS SNAPSHOT (April 4, 2026)

```
Platform GMV (All-Time):     $96,841,797.71
Platform Revenue (Fees):     $1,821,135.80
MRR:                         $20,299.88
ARR:                         $243,598.53
Active Churches:             7
Total Members:               90,326
Total Transactions:          2,496,016
Avg Transaction Size:        $38.80

Church Portfolio:
  Abundant Church            $42,955,140  (171,239 txns)
  The Potter's House         $11,669,268  (340,824 txns)
  Abundant Downtown          $10,856,015  (515,677 txns)
  Abundant West               $9,228,177  (521,527 txns)
  Abundant East               $7,771,780  (513,986 txns)
  City Reach Church           $7,540,992  (227,425 txns)
  EdenX Ministries            $6,820,424  (205,338 txns)
```

---

*Document generated: April 4, 2026*
*Platform Version: 2.0.0*
*Prepared by: Solomon AI Engineering — Charlotte Software Engineering*
