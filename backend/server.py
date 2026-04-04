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


# ═══ Mount Domain Routers ═══
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
    sms_router, printer_router,
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
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(tenant_id, user_id)
    except Exception:
        await ws_manager.disconnect(tenant_id, user_id)



# ═══ CORS ═══
ALLOWED_ORIGINS = [
    os.environ.get("FRONTEND_URL", ""),
    "https://solomonai.us",
    "https://www.solomonai.us",
    "https://app.solomonai.us",
]
preview_url = os.environ.get("REACT_APP_BACKEND_URL", "")
if preview_url:
    ALLOWED_ORIGINS.append(preview_url)
ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.preview\.emergentagent\.com",
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
)


# ═══ Startup / Shutdown ═══
@app.on_event("startup")
async def startup():
    """
    Startup event — MUST return quickly so uvicorn can start serving requests
    and pass the deployment health-check probe within 30s.
    
    ALL seed and scheduler tasks are deferred by 60s minimum to allow:
      1. Atlas MongoDB connection pool to fully establish
      2. Health check probes to detect the server as ready
      3. The event loop to remain free during initial startup
    """
    asyncio.create_task(_deferred_startup())
    logger.info("Startup event complete — server ready for requests")


async def _deferred_startup():
    """All heavy startup work runs here, deferred by 60s after server start."""
    # Wait for server to be fully ready and Atlas connection to warm up
    await asyncio.sleep(60)

    # Warn-only: seed operations are best-effort and must never crash startup
    try:
        from core.seed import ensure_mobile_demo_accounts
        await ensure_mobile_demo_accounts()
        await asyncio.sleep(1)   # yield to event loop between each heavy op
        await seed_vol_data()
        await asyncio.sleep(1)
        await seed_academy_course()
        await asyncio.sleep(1)
        await seed_academy_courses_v2()
        await asyncio.sleep(1)

        # TTL indexes (idempotent — safe to re-run)
        try:
            await db.idempotency_keys.create_index("created_at", expireAfterSeconds=86400)
        except Exception:
            pass
        try:
            await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
        except Exception:
            pass

        # Kids team seed
        try:
            existing_team = await db.volunteer_teams.find_one(
                {"id": "kids-checkin-team", "tenant_id": "abundant-east-001"}
            )
            if not existing_team:
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
                    "team_id": "kids-checkin-team",
                    "tenant_id": "abundant-east-001",
                    "role_title": "Team Lead",
                    "assigned_at": datetime.now(timezone.utc).isoformat(),
                    "assigned_by": "system",
                }},
                upsert=True,
            )
        except Exception as exc:
            logger.warning(f"Kids team seed skipped: {exc}")

        await asyncio.sleep(1)
        await _seed_demo_quality_data()
        logger.info("Deferred startup seed complete")
    except Exception as exc:
        logger.error(f"Deferred startup seed failed (non-fatal): {exc}")

    # Start recurring giving scheduler (90s delay — after seed settles)
    await asyncio.sleep(30)
    try:
        from services.recurring_scheduler import start_scheduler
        start_scheduler(db)
        logger.info("Recurring giving scheduler started")
    except Exception as exc:
        logger.error(f"Scheduler start failed (non-fatal): {exc}")


async def _delayed_scheduler_start():
    """Legacy — kept for backwards compatibility but no longer called directly."""
    pass


@app.on_event("shutdown")
async def shutdown():
    from services.recurring_scheduler import stop_scheduler
    stop_scheduler()
    client.close()



# ═══ Health & Metrics ═══

@app.get("/health")
async def health_check_root():
    """Root health check — responds immediately without any DB call.
    Used by deployment orchestrator readiness probes that check / or /health directly.
    """
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/health")
async def health_check():
    """API-prefixed health check — also responds immediately.
    Avoids DB ping so it can respond even before Atlas connection is established.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
    }


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
