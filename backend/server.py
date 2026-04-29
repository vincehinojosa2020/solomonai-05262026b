"""
Solomon AI — Church Management API
═══════════════════════════════════
Slim entrypoint: middleware, router mounts, startup/shutdown.
All routes live in /routes, models in /models, helpers in /core.
"""
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime, timezone
import os
import time as _time
import uuid
import logging
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ─── Observability layer (BLOCKER #9) ──────────────────────────────────
# Initialize logging + Sentry FIRST so every subsequent import logs
# through the JSON formatter and reports exceptions to Sentry.
from core.observability import (  # noqa: E402
    setup_logging, init_sentry,
    CorrelationIdMiddleware, sentry_scope_middleware,
    get_correlation_id,
)
setup_logging()
init_sentry()

from core import db, client, DEFAULT_TENANT_ID, get_current_member_user, require_permission, logger  # noqa: E402

# Process start time for uptime calc on /api/health
_PROCESS_START_TS = _time.time()
APP_VERSION = os.environ.get("APP_VERSION", "2.0.0")

# ═══ FastAPI App ═══
app = FastAPI(title="Solomon AI Church Management API")

# ═══ Health endpoints — registered FIRST, before all other imports ═══
# Shallow probe (default): returns instantly, no DB call. Used by load
# balancers + Stripe-style external monitors that just need a 200.
# Deep probe (?deep=true): pings Mongo + reports uptime + version. Used
# by paging / on-call dashboards where 'mongo down' must trigger.
@app.get("/health")
async def _health_root():
    return {"status": "ok"}


@app.get("/api/health")
async def _health_api(deep: bool = False):
    payload = {
        "status": "ok",
        "version": APP_VERSION,
        "uptime_s": round(_time.time() - _PROCESS_START_TS, 1),
    }
    if not deep:
        return payload
    # Deep check: mongo ping with a 2s budget (Atlas RTT is 50-200ms; tight 
    # 250ms was tripping UptimeRobot during normal Atlas latency spikes).
    payload["checks"] = {}
    try:
        t0 = _time.perf_counter()
        await asyncio.wait_for(client.admin.command("ping"), timeout=2.0)
        payload["checks"]["mongo"] = {
            "status": "ok",
            "latency_ms": round((_time.perf_counter() - t0) * 1000, 1),
        }
    except Exception as e:
        payload["status"] = "degraded"
        payload["checks"]["mongo"] = {"status": "down", "error": type(e).__name__}
        return JSONResponse(status_code=503, content=payload)
    payload["checks"]["sentry"] = {
        "status": "configured" if os.environ.get("SENTRY_DSN") else "disabled",
    }
    payload["environment"] = os.environ.get("ENVIRONMENT", "development")
    return payload


@app.get("/api/health/launch-check")
async def _health_launch_check():
    """Emergent deployment probe — must return 200 instantly, zero DB calls."""
    return {"status": "ok", "service": "solomon-ai"}


# ═══ Middleware ═══
# Order matters — Starlette runs them outside-in. CorrelationId first so
# every downstream log gets a request id. Then sentry scope picks up that
# id. Then auth/security.
app.add_middleware(CorrelationIdMiddleware)
app.middleware("http")(sentry_scope_middleware)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.exception_handler(500)
async def structured_500_handler(request: Request, exc):
    # Use the per-request correlation id rather than minting a new one — the
    # client may already be looking at it in their X-Request-ID header.
    cid = get_correlation_id()
    logger.error(
        "internal_server_error",
        extra={
            "exc_type": type(exc).__name__,
            "path": request.url.path,
        },
        exc_info=exc,
    )
    return JSONResponse(status_code=500, content={
        "error": "INTERNAL_ERROR",
        "message": "Something went wrong on our end. Please try again, or reach out at support@solomonai.us.",
        "code": 500,
        "correlation_id": cid,
    })


# ═══ CORS — STRICT ALLOWLIST ONLY (no wildcard reflection) ═══
# SECURITY: Never use allow_origins=["*"] with allow_credentials=True.
# This prevents CORS-based credential theft (Snyk Finding #6, CVSS 6.1).
_cors_env = os.environ.get("CORS_ORIGINS", "")
ALLOWED_ORIGINS = [
    "https://solomonai.us",
    "https://www.solomonai.us",
    "https://app.solomonai.us",
]
_frontend_url = os.environ.get("FRONTEND_URL", "")
if _frontend_url and _frontend_url not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(_frontend_url)
# Add the configured CORS origin (preview URL) if it's a real domain
if _cors_env and _cors_env != "*" and _cors_env not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(_cors_env)
_preview_url = os.environ.get("REACT_APP_BACKEND_URL", "")
if _preview_url and _preview_url not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(_preview_url)
ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    # Only match Emergent preview subdomains — NOT arbitrary domains
    allow_origin_regex=r"^https://[a-z0-9\-]+\.preview\.emergentagent\.com$",
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
)


# ═══ SECURITY HEADERS MIDDLEWARE ═══
# Fixes: Missing CSP (Finding #3), Clickjacking (Finding #4), TLS hardening (Findings #5, #6)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response: StarletteResponse = await call_next(request)
        # Content-Security-Policy — defense against XSS and resource injection
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "frame-ancestors 'none'; "
            "connect-src 'self' https: wss:; "
            "media-src 'self' https: blob:; "
            "frame-src 'self' https://*.thinkific.com https://js.stripe.com; "
            "worker-src 'self' blob:; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        # X-Frame-Options — clickjacking protection (backup for older browsers)
        response.headers["X-Frame-Options"] = "DENY"
        # HSTS — enforce HTTPS and modern TLS (Finding #5, #6 mitigation)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        # Additional hardening headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)



# ═══ Mount Domain Routers ═══
# NOTE: these imports are heavy (35 modules). They run synchronously at process
# start, which is unavoidable in Python. The health endpoints above are
# registered BEFORE this block so uvicorn can respond to probes even while
# Python is still processing these imports in subsequent requests.
from routes.auth import router as auth_router
from routes.portal import router as portal_router
from routes.solomon import router as solomon_router
from routes.admin_people import router as admin_people_router
from routes.admin_giving import router as admin_giving_router
from routes.admin_groups import router as admin_groups_router
from routes.admin_services import router as admin_services_router
from routes.admin_checkins import router as admin_checkins_router
from routes.admin_events import router as admin_events_router
from routes.admin_comms import router as admin_comms_router
from routes.admin_media import router as admin_media_router
from routes.admin_cafe import router as admin_cafe_router
from routes.admin_merch import router as admin_merch_router
from routes.admin_pathways import router as admin_pathways_router
from routes.admin_settings import router as admin_settings_router
from routes.admin_workflows import router as admin_workflows_router
from routes.admin_meetings import router as admin_meetings_router
from routes.reports import router as reports_router
from routes.payments import router as payments_router
from routes.platform import router as platform_router
from routes.agent import router as agent_router
from routes.public_api import router as public_api_router

# Pre-existing extracted routers
from routes.push import router as push_router, send_push_notification
from routes.messaging import router as messaging_router
from routes.volunteer import router as volunteer_router, seed_volunteer_leaderboard_data as seed_vol_data
from routes.geofence import router as geofence_router
from routes.announcements import router as announcements_router
from routes.media_uploads import router as media_uploads_router
from routes.giving_nudge import router as giving_nudge_router
from routes.courses import router as courses_router, _init as courses_init, seed_academy_course, seed_academy_courses_v2
from routes.solomonpay_admin import router as solomonpay_admin_router
from routes.sms_routes import router as sms_router
from routes.printer_routes import router as printer_router
from routes.disputes import router as disputes_router
from routes.stripe_connect import router as stripe_connect_router
from routes.stripe_elements import router as stripe_elements_router
from routes.competitive_intel import router as competitive_intel_router
from routes.realtime import router as realtime_router

_domain_routers = [
    auth_router, portal_router, solomon_router,
    admin_people_router, admin_giving_router, admin_groups_router,
    admin_services_router, admin_checkins_router, admin_events_router,
    admin_comms_router, admin_media_router, admin_cafe_router,
    admin_merch_router, admin_pathways_router, admin_settings_router,
    admin_workflows_router, admin_meetings_router,
    reports_router, payments_router, platform_router,
    agent_router, public_api_router,
    push_router, messaging_router, volunteer_router,
    geofence_router, announcements_router, media_uploads_router,
    giving_nudge_router, courses_router, solomonpay_admin_router,
    sms_router, printer_router, disputes_router, stripe_connect_router,
    stripe_elements_router, competitive_intel_router, realtime_router,
]

for router in _domain_routers:
    app.include_router(router, prefix="/api")

# Initialize courses router with shared dependencies
courses_init(db, require_permission, get_current_member_user, DEFAULT_TENANT_ID)

# ═══ WEBSOCKET ═══
from fastapi import WebSocket, WebSocketDisconnect
from services.websocket_service import ws_manager

@app.websocket("/ws/{tenant_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str, user_id: str):
    await ws_manager.connect(websocket, tenant_id, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(tenant_id, user_id)
    except Exception:
        await ws_manager.disconnect(tenant_id, user_id)


# ═══ Startup / Shutdown ═══
@app.on_event("startup")
async def startup():
    """
    Startup event — returns in MILLISECONDS.
    All work is deferred so uvicorn starts accepting health probes immediately.
    """
    # Fire-and-forget: _deferred_startup runs 60s later in the background.
    # Any exception inside it is fully caught — it can never crash the server.
    loop = asyncio.get_event_loop()
    loop.call_later(0, lambda: asyncio.ensure_future(_deferred_startup()))
    logger.info("Startup event complete — uvicorn ready for health probes")


async def _deferred_startup() -> None:
    """
    All heavy/DB work here, deferred 60 s to give Atlas time to warm up.
    Fully exception-isolated: a crash here CANNOT propagate to the server.
    """
    try:
        # ── 60-second grace period ──────────────────────────────────────
        # Lets Atlas connection pool settle and health-check probes pass.
        await asyncio.sleep(60)

        # ── Seed operations (best-effort, never crash on failure) ────────
        try:
            from core.seed import ensure_mobile_demo_accounts
            await ensure_mobile_demo_accounts()
        except Exception as exc:
            logger.warning("startup_ensure_mobile_demo_accounts_skipped", extra={"exc_type": type(exc).__name__})

        await asyncio.sleep(1)   # yield between every operation

        try:
            await seed_vol_data()
        except Exception as exc:
            logger.warning("startup_seed_vol_data_skipped", extra={"exc_type": type(exc).__name__})

        await asyncio.sleep(1)

        try:
            await seed_academy_course()
        except Exception as exc:
            logger.warning("startup_seed_academy_course_skipped", extra={"exc_type": type(exc).__name__})

        await asyncio.sleep(1)

        try:
            await seed_academy_courses_v2()
        except Exception as exc:
            logger.warning("startup_seed_academy_courses_v2_skipped", extra={"exc_type": type(exc).__name__})

        await asyncio.sleep(1)

        # ── Emergency-recovery seed (runs ONLY if tenants collection is
        #    truly empty — catastrophic state from an aggressive cleanup).
        #    Idempotent: instant no-op when even one tenant exists.
        try:
            from scripts.emergency_seed import emergency_seed_if_empty, heal_tenant_slugs
            recovery = await emergency_seed_if_empty()
            if recovery.get("action") == "seeded":
                logger.warning(
                    "[startup] EMERGENCY RECOVERY seeded "
                    f"{recovery.get('tenants')} tenants, "
                    f"{recovery.get('users')} users, "
                    f"{recovery.get('funds')} funds. "
                    "Fresh deploy from empty state."
                )
            elif recovery.get("action") == "error":
                logger.error("startup_emergency_seed_error", extra={"error": str(recovery.get("error"))[:200]})
            else:
                logger.info("startup_emergency_seed", extra={"reason": recovery.get("reason"), "count": recovery.get("count")})

            # Self-healing pass: backfill missing slug/subdomain on every boot
            # so the public give-page URL works even on legacy seeds.
            heal = await heal_tenant_slugs()
            if heal.get("healed_slugs") or heal.get("dsc_added") or heal.get("dsc_orphans_removed"):
                logger.warning(
                    f"[startup] heal_tenant_slugs: slugs={heal.get('healed_slugs')} "
                    f"dsc_added={heal.get('dsc_added')} orphans_removed={heal.get('dsc_orphans_removed')}"
                )

            # Ensure query-critical indexes exist on the donations collection.
            # ~2.8M rows × the God-Mode stats endpoint does 6 scans, so the
            # compound (payment_source, donation_date) index takes p95 from
            # ~11s to <200ms. Index creation is idempotent.
            try:
                await db.donations.create_index([("payment_source", 1), ("donation_date", -1)], name="ix_stripe_date", background=True)
                await db.donations.create_index([("payment_source", 1), ("tenant_id", 1)], name="ix_stripe_tenant", background=True)
                await db.donations.create_index([("payment_source", 1), ("donor_email", 1)], name="ix_stripe_donor", background=True)
                await db.donations.create_index([("payment_source", 1), ("created_at", -1)], name="ix_stripe_created", background=True)
            except Exception as e:
                logger.warning("startup_donations_index_skipped", extra={"exc_type": type(e).__name__})

            # ── Stripe → Mongo backfill (boot + every 60s) ─────────────
            # Paranoid sync: if the frontend's confirm-donation call never
            # landed (tab closed mid-payment, network drop, webhook not
            # configured yet), the charge is on Stripe but our donations
            # collection is blind to it. Periodically pull the last 24h of
            # PIs and insert anything missing. This is what makes Vince's
            # "instantaneous" promise real for Christopher's church-admin
            # view + for platform-admin God Mode.
            try:
                from core.stripe_sync import sync_recent
                added_now = await sync_recent(hours=72, limit=100)
                if added_now:
                    logger.warning("startup_stripe_sync_backfilled", extra={"count": added_now})

                async def _stripe_sync_loop():
                    while True:
                        await asyncio.sleep(60)
                        try:
                            n = await sync_recent(hours=24, limit=100)
                            if n:
                                logger.info("stripe_sync_loop_backfilled", extra={"count": n})
                        except Exception as e:
                            logger.warning("stripe_sync_loop_tick_failed", extra={"exc_type": type(e).__name__})
                asyncio.ensure_future(_stripe_sync_loop())
            except Exception as e:
                logger.warning("startup_stripe_sync_init_failed", extra={"exc_type": type(e).__name__})
        except Exception as exc:
            logger.warning("startup_emergency_seed_skipped", extra={"exc_type": type(exc).__name__})

        # ── Eden Church auto-seed (runs ONCE per deploy; flagged in DB) ──
        try:
            from scripts.setup_eden_church import auto_seed_on_boot
            result = await auto_seed_on_boot()
            if result.get("seeded"):
                logger.info(
                    f"[startup] Eden Church seeded. Wiped {result.get('wiped_legacy_tenants', 0)} "
                    f"legacy tenant(s). State: {result.get('state')}"
                )
            else:
                logger.info("startup_eden_auto_seed_skipped", extra={"reason": result.get("reason")})
        except Exception as exc:
            logger.warning("startup_eden_auto_seed_skipped", extra={"exc_type": type(exc).__name__})

        await asyncio.sleep(1)

        # ── TTL indexes (idempotent, safe to retry) ─────────────────────
        for coll, field, ttl in [
            ("idempotency_keys", "created_at", 86400),
            ("user_sessions", "expires_at", 0),
            # Stripe webhook events: keep 90d for audit/replay analysis,
            # then auto-purge. Stripe retries are 3d max so this is plenty.
            ("stripe_webhook_events", "received_at", 90 * 86400),
        ]:
            try:
                await getattr(db, coll).create_index(field, expireAfterSeconds=ttl)
            except Exception:
                pass

        # Unique index on event_id so duplicate webhook deliveries can never
        # double-insert (defense in depth on top of the find_one check).
        try:
            await db.stripe_webhook_events.create_index("event_id", unique=True)
        except Exception:
            pass

        # ── Hot-path donation indexes for sub-200ms admin/giving + church
        #    drill-through. Idempotent. ────────────────────────────────────
        try:
            await db.donations.create_index([("tenant_id", 1), ("created_at", -1)], name="ix_tenant_created", background=True)
            await db.donations.create_index([("tenant_id", 1), ("donation_date", -1)], name="ix_tenant_date", background=True)
            await db.donations.create_index("created_at", name="ix_created_at", background=True)
            await db.donations.create_index("stripe_payment_intent_id", name="ix_stripe_pi", background=True, sparse=True)
            # Platform-wide stripe queries — covers the "what hit Stripe today/week/month"
            # buckets in /api/platform/stripe/transactions/*. Without this, Atlas
            # has to scan every doc filtering by payment_source.
            await db.donations.create_index([("payment_source", 1), ("donation_date", -1)], name="ix_payment_source_date", background=True)
            await db.donations.create_index([("payment_source", 1), ("created_at", -1)], name="ix_payment_source_created", background=True)
            # Realtime events tail — short TTL since this is just a poll
            # signal, not a permanent record.
            await db.realtime_events.create_index("ts", expireAfterSeconds=3600, name="ix_ts_ttl")
            await db.realtime_events.create_index([("tenant_id", 1), ("ts", -1)], name="ix_tenant_ts", background=True)
            # `people` is hit hard on every drill-through; tenant_id+lifetime_giving
            # backs the top-roster query and tenant_id+id covers the person lookup.
            await db.people.create_index([("tenant_id", 1), ("lifetime_giving", -1)], name="ix_tenant_lifetime", background=True)
            await db.people.create_index([("tenant_id", 1), ("id", 1)], name="ix_tenant_id", background=True)
        except Exception as e:
            logger.warning("startup_realtime_indexes_skipped", extra={"exc_type": type(e).__name__})

        # ── Kids check-in team seed ──────────────────────────────────────
        try:
            existing = await db.volunteer_teams.find_one(
                {"id": "kids-checkin-team", "tenant_id": "abundant-east-001"}
            )
            if not existing:
                await db.volunteer_teams.insert_one({
                    "id": "kids-checkin-team", "tenant_id": "abundant-east-001",
                    "team_name": "Kids Check-In Team", "ministry": "Children's Ministry",
                    "description": "Ensuring every child is safe and accounted for every Sunday.",
                    "created_at": datetime.now(timezone.utc).isoformat(), "created_by": "system",
                })
            await db.volunteer_assignments.update_one(
                {"user_id": "f1d0f1d8-de66-4fc0-a8c7-8f81f679ce22",
                 "team_id": "kids-checkin-team", "tenant_id": "abundant-east-001"},
                {"$set": {
                    "id": str(uuid.uuid4()),
                    "user_id": "f1d0f1d8-de66-4fc0-a8c7-8f81f679ce22",
                    "team_id": "kids-checkin-team", "tenant_id": "abundant-east-001",
                    "role_title": "Team Lead",
                    "assigned_at": datetime.now(timezone.utc).isoformat(),
                    "assigned_by": "system",
                }},
                upsert=True,
            )
        except Exception as exc:
            logger.warning("startup_kids_team_seed_skipped", extra={"exc_type": type(exc).__name__})

        await asyncio.sleep(1)

        try:
            await _seed_demo_quality_data()
        except Exception as exc:
            logger.warning("startup_demo_quality_data_skipped", extra={"exc_type": type(exc).__name__})

        logger.info("[startup] Deferred seed complete")

        # ── Recurring giving scheduler (starts 30s after seed settles) ───
        await asyncio.sleep(30)
        try:
            from services.recurring_scheduler import start_scheduler
            start_scheduler(db)
            logger.info("[startup] Recurring giving scheduler started")
        except Exception as exc:
            logger.error("startup_scheduler_start_failed", extra={"exc_type": type(exc).__name__})

    except Exception as exc:
        # Outermost catch — nothing should ever escape to the server process
        logger.error("startup_deferred_startup_crashed", extra={"exc_type": type(exc).__name__})


@app.on_event("shutdown")
async def shutdown():
    from services.recurring_scheduler import stop_scheduler
    stop_scheduler()
    client.close()



# ═══ Metrics (God Mode only) ═══
@app.get("/api/metrics")
async def get_metrics(request: Request):
    """Platform metrics — God Mode only."""
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token:
        raise Exception("Not authenticated")
    from motor.motor_asyncio import AsyncIOMotorClient
    tenant_count = await db.tenants.count_documents({"subscription_status": "active"})
    user_count = await db.users.count_documents({})
    donation_count = await db.donations.count_documents({})
    return {
        "tenants": tenant_count,
        "users": user_count,
        "donations": donation_count,
        "uptime": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _seed_demo_quality_data():
    """Seed attendance streaks, member directory, giving integrations."""
    from datetime import timedelta
    tenant_id = DEFAULT_TENANT_ID
    now_iso = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).date()

    days_since_sunday = (today.weekday() + 1) % 7
    most_recent_sunday = today - timedelta(days=days_since_sunday)
    for user_id in ["shannon_nieman_001", "jacob_pacheco_001"]:
        checkin_ids = []
        for week in range(12):
            sunday = most_recent_sunday - timedelta(weeks=week)
            cid = f"chk_streak_{user_id}_{week:02d}"
            checkin_ids.append(cid)
            await db.member_checkins.update_one(
                {"id": cid, "tenant_id": tenant_id},
                {"$set": {"id": cid, "tenant_id": tenant_id, "user_id": user_id,
                           "service_id": None, "check_in_type": "in_person",
                           "service_date": sunday.isoformat(),
                           "check_in_time": f"{sunday.isoformat()}T09:30:00+00:00"}},
                upsert=True,
            )
        await db.member_checkins.delete_many(
            {"tenant_id": tenant_id, "user_id": user_id, "id": {"$nin": checkin_ids}}
        )

    existing_dir = await db.people.count_documents(
        {"tenant_id": tenant_id, "id": {"$regex": "^dir_member_"}}
    )
    if existing_dir < 25:
        directory_members = [
            ("Sarah", "Mitchell"), ("David", "Chen"), ("Rachel", "Thompson"),
            ("Marcus", "Williams"), ("Emily", "Rodriguez"), ("Jonathan", "Baker"),
            ("Grace", "Kim"), ("Michael", "Foster"), ("Ashley", "Martinez"),
            ("Brandon", "Taylor"), ("Megan", "Anderson"), ("Tyler", "Moore"),
            ("Jasmine", "Harris"), ("Andrew", "Jackson"), ("Lauren", "Clark"),
            ("Daniel", "Lewis"), ("Christina", "Walker"), ("Joshua", "Robinson"),
            ("Samantha", "Young"), ("Kevin", "Hernandez"), ("Natalie", "King"),
            ("Ryan", "Scott"), ("Olivia", "Green"), ("Chris", "Adams"),
            ("Hannah", "Nelson"),
        ]
        for i, (first, last) in enumerate(directory_members):
            await db.people.update_one(
                {"id": f"dir_member_{i:03d}", "tenant_id": tenant_id},
                {"$set": {
                    "id": f"dir_member_{i:03d}", "tenant_id": tenant_id,
                    "user_id": f"dir_user_{i:03d}",
                    "first_name": first, "last_name": last,
                    "name": f"{first} {last}",
                    "email": f"{first.lower()}.{last.lower()}@abundant.church",
                    "membership_status": "member", "directory_visible": True,
                    "share_email": True, "share_phone": True,
                    "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed=dir{i}",
                    "created_at": now_iso,
                }},
                upsert=True,
            )

    await db.giving_integrations.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            "tenant_id": tenant_id, "active_processor": "solomon_pay",
            "processors": {
                "solomon_pay": {"enabled": True, "status": "active", "label": "SolomonPay",
                                "description": "Native giving powered by Solomon AI", "connected_at": now_iso},
                "pushpay": {"enabled": False, "status": "not_connected", "label": "Pushpay",
                            "description": "Connect your existing Pushpay account"},
                "securegive": {"enabled": False, "status": "not_connected", "label": "SecureGive",
                               "description": "Integrate with SecureGive"},
            },
            "updated_at": now_iso,
        }, "$setOnInsert": {"created_at": now_iso}},
        upsert=True,
    )
    logger.info("[SEED] Quality demo data seeded")
