"""
Solomon AI — Core Dependencies Module
Shared helpers for all route modules.
Provides: db, auth helpers, tenant validation, permissions, audit, email.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException, Request
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import time as _time
import uuid
import os
import logging

logger = logging.getLogger("solomon-ai")

# ═══ Database ═══
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
db_name = os.environ["DB_NAME"]

client = AsyncIOMotorClient(
    mongo_url,
    # ── Timeouts tuned for Atlas cold-start ──────────────────────────────
    # serverSelectionTimeoutMS: how long Motor waits to find a primary.
    #   30s gives Atlas time to respond without blocking indefinitely.
    serverSelectionTimeoutMS=30000,
    # connectTimeoutMS: max time to open a TCP connection to Atlas.
    #   20s is enough for cross-region Atlas clusters.
    connectTimeoutMS=20000,
    # socketTimeoutMS: max time waiting for a response on an open socket.
    socketTimeoutMS=45000,
    # ── Pool: small pool keeps cold-start fast ───────────────────────────
    maxPoolSize=5,
    minPoolSize=0,
    maxIdleTimeMS=60000,
    # ── Reliability ──────────────────────────────────────────────────────
    retryWrites=True,
    retryReads=True,
    heartbeatFrequencyMS=10000,
    appname="solomon-ai",
)
db = client[db_name]

# ═══ Constants ═══
DEFAULT_TENANT_ID = "abundant-east-001"
PLATFORM_ADMIN_EMAILS = ["admin@solomonai.us", "admin@abundant.org", "admin@solomon.ai"]

ROLES = {
    "platform_admin": 100,
    "church_admin": 50,
    "member": 10,
}

PERMISSION_REGISTRY = [
    "member.home", "member.give", "member.kids", "member.watch",
    "member.merch", "member.cafe", "member.groups", "member.events",
    "member.nextsteps", "member.prayer", "member.volunteer", "member.courses",
    "admin.dashboard", "admin.members.view", "admin.members.edit",
    "admin.members.roles", "admin.giving.view", "admin.giving.edit",
    "admin.giving.donors", "admin.giving.payouts", "admin.giving.statements",
    "admin.kids.manage", "admin.media.manage", "admin.cafe.manage",
    "admin.merch.manage", "admin.groups.manage", "admin.groups.lead",
    "admin.events.manage", "admin.announcements", "admin.volunteers.manage",
    "admin.geofence.manage", "admin.reports.view", "admin.reports.export",
    "admin.communications", "admin.settings",
    "admin.courses.view", "admin.courses.edit",
    "admin.users.create", "admin.users.roles",
    "platform.churches.view", "platform.churches.create",
    "platform.users.create", "platform.billing", "platform.reports",
]

MEMBER_PERMISSIONS = [p for p in PERMISSION_REGISTRY if p.startswith("member.")]
ALL_ADMIN_PERMISSIONS = [p for p in PERMISSION_REGISTRY if p.startswith("admin.")]
ALL_PLATFORM_PERMISSIONS = [p for p in PERMISSION_REGISTRY if p.startswith("platform.")]

ROLE_TEMPLATES = {
    "member": {"role_title": "Church Member", "permissions": MEMBER_PERMISSIONS},
    "kids_volunteer": {"role_title": "Kids Check-In Volunteer", "permissions": MEMBER_PERMISSIONS + ["admin.kids.manage"]},
    "small_group_leader": {"role_title": "Small Group Leader", "permissions": MEMBER_PERMISSIONS + ["admin.groups.manage", "admin.groups.lead", "admin.events.manage"]},
    "cafe_manager": {"role_title": "Cafe Manager", "permissions": MEMBER_PERMISSIONS + ["admin.cafe.manage", "admin.reports.view", "admin.reports.export"]},
    "merch_manager": {"role_title": "Merch Manager", "permissions": MEMBER_PERMISSIONS + ["admin.merch.manage", "admin.reports.view", "admin.reports.export"]},
    "worship_media_team": {"role_title": "Worship & Media Team", "permissions": MEMBER_PERMISSIONS + ["admin.media.manage", "admin.events.manage", "admin.announcements"]},
    "finance": {
        "role_title": "Finance Team",
        "permissions": MEMBER_PERMISSIONS + [
            "admin.dashboard", "admin.giving.view", "admin.giving.edit",
            "admin.giving.donors", "admin.giving.payouts", "admin.giving.statements",
            "admin.reports.view", "admin.reports.export",
        ],
    },
    "staff": {
        "role_title": "Staff",
        "permissions": MEMBER_PERMISSIONS + [
            "admin.dashboard", "admin.members.view", "admin.giving.view",
            "admin.events.manage", "admin.groups.manage", "admin.announcements",
            "admin.reports.view", "admin.communications",
        ],
    },
    "ministry_leader": {
        "role_title": "Ministry Leader",
        "permissions": MEMBER_PERMISSIONS + [
            "admin.dashboard", "admin.members.view", "admin.members.edit",
            "admin.groups.manage", "admin.events.manage", "admin.announcements",
            "admin.volunteers.manage", "admin.media.manage", "admin.reports.view",
            "admin.communications",
        ],
    },
    "senior_pastor": {
        "role_title": "Senior Pastor / Founder",
        "permissions": MEMBER_PERMISSIONS + ALL_ADMIN_PERMISSIONS,
    },
    "executive_pastor": {
        "role_title": "Executive Pastor",
        "permissions": MEMBER_PERMISSIONS + [p for p in ALL_ADMIN_PERMISSIONS if p not in ("admin.users.create", "admin.users.roles")],
    },
    "church_admin": {"role_title": "Church Administrator", "permissions": MEMBER_PERMISSIONS + ALL_ADMIN_PERMISSIONS},
    "platform_admin": {"role_title": "Platform Administrator", "permissions": PERMISSION_REGISTRY[:]},
}


# ═══ Rate Limiting (MongoDB-backed for persistence across restarts) ═══
RATE_LIMITS = {}  # In-memory fallback

async def check_rate_limit_mongo(bucket: str, max_requests: int, window_seconds: int) -> bool:
    """MongoDB-backed persistent rate limiter."""
    try:
        import time as _t
        now = _t.time()
        window_start = now - window_seconds
        # Count recent requests in this window
        result = await db.rate_limits.find_one_and_update(
            {"bucket": bucket},
            {
                "$setOnInsert": {"bucket": bucket, "window_start": now, "count": 0},
                "$push": {"requests": {"$each": [now], "$slice": -max_requests * 2}},  # keep recent
            },
            upsert=True,
            return_document=True,
        )
        if not result:
            return True
        recent = [r for r in (result.get("requests") or []) if r > window_start]
        return len(recent) <= max_requests
    except Exception:
        return True  # Fail open

def check_rate_limit_v2(bucket: str, max_requests: int, window_seconds: int) -> bool:
    """Sync in-memory rate limiter (for use in sync contexts)."""
    try:
        import time as _t
        now = _t.time()
        if bucket not in RATE_LIMITS:
            RATE_LIMITS[bucket] = {"count": 0, "window_start": now}
        entry = RATE_LIMITS[bucket]
        if now - entry["window_start"] > window_seconds:
            RATE_LIMITS[bucket] = {"count": 1, "window_start": now}
            return True
        entry["count"] += 1
        return entry["count"] <= max_requests
    except Exception:
        return True

# ═══ In-memory caching ═══
_cache: dict = {}
_cache_ttl: dict = {}

async def cache_get(key: str):
    """Get cached value if not expired."""
    import time
    if key in _cache and time.time() < _cache_ttl.get(key, 0):
        return _cache[key]
    return None

async def cache_set(key: str, value, ttl_seconds: int = 300):
    """Cache a value with TTL."""
    import time
    _cache[key] = value
    _cache_ttl[key] = time.time() + ttl_seconds

def cache_invalidate(pattern: str = None):
    """Invalidate all cache or keys matching pattern."""
    if pattern:
        to_delete = [k for k in _cache if pattern in k]
        for k in to_delete:
            _cache.pop(k, None)
            _cache_ttl.pop(k, None)
    else:
        _cache.clear()
        _cache_ttl.clear()


# ═══ Auth Helpers ═══
def get_session_token_from_request(request: Request) -> str:
    token = request.cookies.get("session_token")
    if token:
        return token
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def get_current_admin_user(request: Request):
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if user.get("role") not in ["admin", "church_admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.get("role") != "platform_admin" and not user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Tenant context required for admin access")
    return user


async def get_current_portal_user(request: Request):
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Alias for backward compat
get_current_member_user = get_current_portal_user


def require_tenant(user: dict) -> str:
    tenant_id = user.get("tenant_id")
    if not tenant_id and user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Tenant context required")
    return tenant_id


# ═══ Permissions ═══
def get_permissions_for_user(user_doc: dict) -> list:
    custom = user_doc.get("permissions")
    if custom and isinstance(custom, list):
        return custom
    role = user_doc.get("role", "member")
    template = ROLE_TEMPLATES.get(role, ROLE_TEMPLATES["member"])
    return template["permissions"]

def check_permission(user_doc: dict, required: str) -> bool:
    if user_doc.get("role") == "platform_admin":
        return True
    perms = get_permissions_for_user(user_doc)
    return required in perms

async def require_permission(request: Request, permission: str):
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not check_permission(user, permission):
        raise HTTPException(status_code=403, detail=f"Permission denied: {permission} required")
    return user


# ═══ Idempotency ═══
async def check_idempotency(key: str):
    if not key:
        return None
    doc = await db.idempotency_keys.find_one({"key": key}, {"_id": 0})
    return doc.get("result") if doc else None

async def store_idempotency(key: str, result: dict):
    if not key:
        return
    await db.idempotency_keys.update_one(
        {"key": key},
        {"$set": {"key": key, "result": result, "created_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


# ═══ Audit Trail ═══
async def audit_log(action, entity_type, entity_id, tenant_id, user_id, user_name,
                    before_value=None, after_value=None, request=None):
    doc = {
        "id": str(uuid.uuid4()),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "tenant_id": tenant_id,
        "performed_by_user_id": user_id,
        "performed_by_name": user_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "before_value": before_value,
        "after_value": after_value,
        "ip_address": request.client.host if request else None,
        "user_agent": request.headers.get("user-agent", "") if request else None,
    }
    await db.audit_log.insert_one(doc)


# ═══ Tenant Helpers ═══
async def get_tenant_by_subdomain(subdomain: str):
    return await db.tenants.find_one({"subdomain": subdomain.lower()}, {"_id": 0})

async def get_tenant_by_id(tenant_id: str):
    return await db.tenants.find_one({"id": tenant_id}, {"_id": 0})

async def validate_tenant_subscription(tenant_id: str) -> bool:
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    return bool(tenant and tenant.get("subscription_status") == "active")
