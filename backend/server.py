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
import uuid
import logging
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from core import db, client, DEFAULT_TENANT_ID, get_current_member_user, require_permission, logger

# ═══ FastAPI App ═══
app = FastAPI(title="Solomon AI Church Management API")

# ═══ Health endpoints — registered FIRST, before all other imports ═══
# These must respond in <100ms before Atlas connects. Registered at app level
# so they work even if route module imports are still in progress.

@app.get("/health")
async def _health_root():
    return {"status": "ok"}

@app.get("/api/health")
async def _health_api():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/api/health/launch-check")
async def _health_launch_check():
    """Emergent deployment probe — must return 200 instantly, zero DB calls."""
    return {"status": "ok", "service": "solomon-ai"}


# ═══ Middleware ═══
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
    cid = f"req_{uuid.uuid4().hex[:12]}"
    logger.error(f"[{cid}] Internal error: {exc}")
    return JSONResponse(status_code=500, content={
        "error": "INTERNAL_ERROR", "message": "Something went wrong on our end. Please try again, or reach out at support@solomonai.us.",
        "code": 500, "correlation_id": cid,
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
    stripe_elements_router,
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
            logger.warning(f"[startup] ensure_mobile_demo_accounts skipped: {exc}")

        await asyncio.sleep(1)   # yield between every operation

        try:
            await seed_vol_data()
        except Exception as exc:
            logger.warning(f"[startup] seed_vol_data skipped: {exc}")

        await asyncio.sleep(1)

        try:
            await seed_academy_course()
        except Exception as exc:
            logger.warning(f"[startup] seed_academy_course skipped: {exc}")

        await asyncio.sleep(1)

        try:
            await seed_academy_courses_v2()
        except Exception as exc:
            logger.warning(f"[startup] seed_academy_courses_v2 skipped: {exc}")

        await asyncio.sleep(1)

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
                logger.info(f"[startup] Eden Church auto-seed skipped: {result.get('reason')}")
        except Exception as exc:
            logger.warning(f"[startup] eden_auto_seed skipped: {exc}")

        await asyncio.sleep(1)

        # ── TTL indexes (idempotent, safe to retry) ─────────────────────
        for coll, field, ttl in [
            ("idempotency_keys", "created_at", 86400),
            ("user_sessions", "expires_at", 0),
        ]:
            try:
                await getattr(db, coll).create_index(field, expireAfterSeconds=ttl)
            except Exception:
                pass

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
            logger.warning(f"[startup] kids team seed skipped: {exc}")

        await asyncio.sleep(1)

        try:
            await _seed_demo_quality_data()
        except Exception as exc:
            logger.warning(f"[startup] demo quality data skipped: {exc}")

        logger.info("[startup] Deferred seed complete")

        # ── Recurring giving scheduler (starts 30s after seed settles) ───
        await asyncio.sleep(30)
        try:
            from services.recurring_scheduler import start_scheduler
            start_scheduler(db)
            logger.info("[startup] Recurring giving scheduler started")
        except Exception as exc:
            logger.error(f"[startup] Scheduler start failed (non-fatal): {exc}")

    except Exception as exc:
        # Outermost catch — nothing should ever escape to the server process
        logger.error(f"[startup] _deferred_startup crashed (non-fatal): {exc}")


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
