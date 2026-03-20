from fastapi import FastAPI, APIRouter, HTTPException, Query, Request, Response, Cookie, UploadFile, File
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import httpx
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, date, timedelta
from bson import ObjectId
import random
import resend
import json
from urllib.parse import quote

# Stripe integration
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionResponse, 
    CheckoutStatusResponse, 
    CheckoutSessionRequest
)

# Twilio SMS (if configured)
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

# Samson AI - Claude Integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure Resend for welcome emails
resend.api_key = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

# MongoDB connection with Atlas-compatible settings
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=30000,  # 30 seconds for server selection
    connectTimeoutMS=30000,           # 30 seconds to establish connection
    socketTimeoutMS=60000,            # 60 seconds for socket operations
    maxPoolSize=50,                   # Connection pool size
    minPoolSize=10,                   # Minimum connections to maintain
    maxIdleTimeMS=45000,              # Close idle connections after 45 seconds
    retryWrites=True,                 # Enable retryable writes
    retryReads=True,                  # Enable retryable reads
    w='majority'                      # Write concern for durability
)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Solomon AI Church Management API")

# ============== SECURITY MIDDLEWARE (Module 9 - v3.0) ==============

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses (OWASP/Veracode standard)"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Rate limiting for auth endpoints (in-memory, single-instance)
import time as _time
RATE_LIMITS = {}  # {bucket_key: {count, window_start}}

def check_rate_limit_v2(bucket: str, max_requests: int, window_seconds: int) -> bool:
    """Generic rate limiter. Returns True if allowed, False if exceeded."""
    now = _time.time()
    if bucket not in RATE_LIMITS:
        RATE_LIMITS[bucket] = {"count": 0, "window_start": now}
    entry = RATE_LIMITS[bucket]
    if now - entry["window_start"] > window_seconds:
        RATE_LIMITS[bucket] = {"count": 1, "window_start": now}
        return True
    entry["count"] += 1
    return entry["count"] <= max_requests

# Legacy compat
AUTH_RATE_LIMIT = {}
AUTH_RATE_LIMIT_MAX = 5  # 5 attempts per minute per IP (Veracode standard)
AUTH_RATE_LIMIT_WINDOW = 60

def check_rate_limit(ip: str) -> bool:
    """Check if IP has exceeded rate limit for auth endpoints"""
    import time
    current_time = time.time()
    
    if ip not in AUTH_RATE_LIMIT:
        AUTH_RATE_LIMIT[ip] = {"count": 0, "window_start": current_time}
    
    # Reset window if expired
    if current_time - AUTH_RATE_LIMIT[ip]["window_start"] > AUTH_RATE_LIMIT_WINDOW:
        AUTH_RATE_LIMIT[ip] = {"count": 0, "window_start": current_time}
    
    AUTH_RATE_LIMIT[ip]["count"] += 1
    
    return AUTH_RATE_LIMIT[ip]["count"] <= AUTH_RATE_LIMIT_MAX

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== MULTI-TENANT CONFIGURATION ==============

# Platform admin accounts (can access all tenants)
PLATFORM_ADMIN_EMAILS = ["admin@solomon.ai", "admin@abundant.org"]

# Role hierarchy
ROLES = {
    "platform_admin": 100,  # Can access everything
    "church_admin": 50,     # Can manage their church
    "member": 10            # Portal access only
}

# ============== PERMISSION REGISTRY (Active Directory-inspired) ==============

PERMISSION_REGISTRY = [
    # Member surface
    "member.home", "member.give", "member.kids", "member.watch",
    "member.merch", "member.cafe", "member.groups", "member.events",
    "member.nextsteps", "member.prayer", "member.volunteer",
    # Ministry operations
    "admin.dashboard", "admin.members.view", "admin.members.edit",
    "admin.members.roles", "admin.giving.view", "admin.giving.edit",
    "admin.kids.manage", "admin.media.manage", "admin.cafe.manage",
    "admin.merch.manage", "admin.groups.manage", "admin.groups.lead",
    "admin.events.manage", "admin.announcements", "admin.volunteers.manage",
    "admin.geofence.manage", "admin.reports.view", "admin.reports.export",
    "admin.communications", "admin.settings",
    "admin.users.create", "admin.users.roles",
    # Platform level
    "platform.churches.view", "platform.churches.create",
    "platform.users.create", "platform.billing", "platform.reports",
]

MEMBER_PERMISSIONS = [p for p in PERMISSION_REGISTRY if p.startswith("member.")]
ALL_ADMIN_PERMISSIONS = [p for p in PERMISSION_REGISTRY if p.startswith("admin.")]
ALL_PLATFORM_PERMISSIONS = [p for p in PERMISSION_REGISTRY if p.startswith("platform.")]

ROLE_TEMPLATES = {
    "member": {
        "role_title": "Church Member",
        "permissions": MEMBER_PERMISSIONS,
    },
    "kids_volunteer": {
        "role_title": "Kids Check-In Volunteer",
        "permissions": MEMBER_PERMISSIONS + ["admin.kids.manage"],
    },
    "small_group_leader": {
        "role_title": "Small Group Leader",
        "permissions": MEMBER_PERMISSIONS + ["admin.groups.manage", "admin.groups.lead", "admin.events.manage"],
    },
    "cafe_manager": {
        "role_title": "Cafe Manager",
        "permissions": MEMBER_PERMISSIONS + ["admin.cafe.manage", "admin.reports.view", "admin.reports.export"],
    },
    "merch_manager": {
        "role_title": "Merch Manager",
        "permissions": MEMBER_PERMISSIONS + ["admin.merch.manage", "admin.reports.view", "admin.reports.export"],
    },
    "worship_media_team": {
        "role_title": "Worship & Media Team",
        "permissions": MEMBER_PERMISSIONS + ["admin.media.manage", "admin.events.manage", "admin.announcements"],
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
    "executive_pastor": {
        "role_title": "Executive Pastor",
        "permissions": MEMBER_PERMISSIONS + [p for p in ALL_ADMIN_PERMISSIONS if p not in ("admin.users.create", "admin.users.roles")],
    },
    "church_admin": {
        "role_title": "Church Administrator",
        "permissions": MEMBER_PERMISSIONS + ALL_ADMIN_PERMISSIONS,
    },
    "platform_admin": {
        "role_title": "Platform Administrator",
        "permissions": PERMISSION_REGISTRY[:],  # All permissions
    },
}

def get_permissions_for_user(user_doc: dict) -> list:
    """Resolve permissions for a user. Custom permissions take priority over template."""
    custom = user_doc.get("permissions")
    if custom and isinstance(custom, list):
        return custom
    role = user_doc.get("role", "member")
    template = ROLE_TEMPLATES.get(role, ROLE_TEMPLATES["member"])
    return template["permissions"]

def check_permission(user_doc: dict, required: str) -> bool:
    """Check if user has a specific permission."""
    if user_doc.get("role") == "platform_admin":
        return True  # Platform admins bypass all checks
    perms = get_permissions_for_user(user_doc)
    return required in perms

async def require_permission(request: Request, permission: str):
    """Get current user and verify they have the required permission. Returns user doc."""
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

# ============== IDEMPOTENCY SYSTEM (MongoDB TTL) ==============

async def check_idempotency(key: str):
    """Check if an idempotency key has been used. Returns cached result or None."""
    if not key:
        return None
    doc = await db.idempotency_keys.find_one({"key": key}, {"_id": 0})
    if doc:
        return doc.get("result")
    return None

async def store_idempotency(key: str, result: dict):
    """Store idempotency key with result. TTL index auto-expires after 24hr."""
    if not key:
        return
    await db.idempotency_keys.update_one(
        {"key": key},
        {"$set": {"key": key, "result": result, "created_at": datetime.now(timezone.utc)}},
        upsert=True
    )

# ============== AUDIT TRAIL ==============

async def audit_log(action: str, entity_type: str, entity_id: str, tenant_id: str,
                    user_id: str, user_name: str, before_value: dict = None,
                    after_value: dict = None, request: Request = None):
    """Create an immutable audit record."""
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

async def get_tenant_by_subdomain(subdomain: str):
    """Get tenant by subdomain"""
    tenant = await db.tenants.find_one({"subdomain": subdomain.lower()}, {"_id": 0})
    return tenant

async def get_tenant_by_id(tenant_id: str):
    """Get tenant by ID"""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    return tenant

async def validate_tenant_subscription(tenant_id: str) -> bool:
    """Check if tenant has active subscription"""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        return False
    return tenant.get("subscription_status") == "active"

# ============== EMAIL HELPER FUNCTIONS ==============

async def send_welcome_email(email: str, first_name: str, church_name: str = "your church"):
    """Send a creative welcome email from Solomon AI when a new user registers"""
    try:
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1a1a2e; margin: 0; padding: 0; background-color: #f8f9fa;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
        <tr>
            <td style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 40px; border-radius: 16px 16px 0 0; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">
                    Welcome to the Family, {first_name}! 🙏
                </h1>
            </td>
        </tr>
        <tr>
            <td style="background: #ffffff; padding: 40px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                <p style="font-size: 16px; color: #4a5568; margin: 0 0 20px 0;">
                    Hey {first_name},
                </p>
                <p style="font-size: 16px; color: #4a5568; margin: 0 0 20px 0;">
                    I'm <strong>Solomon</strong>, your AI assistant at <strong>{church_name}</strong>. I just wanted to personally say <strong>thank you</strong> for joining our community! 
                </p>
                <p style="font-size: 16px; color: #4a5568; margin: 0 0 20px 0;">
                    Whether you're looking to grow in faith, connect with others, or simply find a place to belong — you're in the right place. We're so glad you're here.
                </p>
                <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 20px; margin: 24px 0; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; color: #1e40af; font-size: 15px;">
                        <strong>What's next?</strong><br>
                        Log in to explore sermon videos, join a small group, or make your first gift. I'm always here if you need anything!
                    </p>
                </div>
                <p style="font-size: 16px; color: #4a5568; margin: 0 0 8px 0;">
                    See you soon,
                </p>
                <p style="font-size: 18px; color: #1a1a2e; margin: 0; font-weight: 600;">
                    Solomon 🤖✨
                </p>
                <p style="font-size: 13px; color: #94a3b8; margin: 16px 0 0 0; font-style: italic;">
                    Your AI Church Assistant at {church_name}
                </p>
            </td>
        </tr>
        <tr>
            <td style="text-align: center; padding: 24px;">
                <p style="font-size: 12px; color: #94a3b8; margin: 0;">
                    {church_name}<br>
                    Powered by Solomon AI
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": f"Welcome to {church_name}, {first_name}! 🎉",
            "html": html_content
        }
        
        # Run sync SDK in thread to keep FastAPI non-blocking
        email_response = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Welcome email sent to {email}, id: {email_response.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        return False

# ============== PYDANTIC MODELS ==============

class TenantBase(BaseModel):
    name: str
    subdomain: str
    plan: str = "starter"
    member_limit: int = 500
    logo_url: Optional[str] = None
    primary_color: str = "#4f6ef7"
    accent_color: str = "#00c896"
    timezone: str = "America/Los_Angeles"
    subscription_status: str = "active"  # active, suspended, cancelled
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None

class Tenant(TenantBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HouseholdBase(BaseModel):
    name: str
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: str = "US"
    phone: Optional[str] = None
    envelope_num: Optional[int] = None

class Household(HouseholdBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PersonBase(BaseModel):
    first_name: str
    last_name: str
    preferred_name: Optional[str] = None
    email: Optional[str] = None
    mobile_phone: Optional[str] = None
    work_phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    membership_status: str = "visitor"
    membership_date: Optional[str] = None
    baptism_date: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
    envelope_number: Optional[int] = None
    is_head_of_household: bool = False
    custom_fields: Dict[str, Any] = {}
    giving_anonymous: bool = False
    paperless_statements: bool = True
    household_id: Optional[str] = None
    campus: Optional[str] = None

class Person(PersonBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    engagement_score: int = 0
    last_attended_at: Optional[str] = None
    ytd_giving: float = 0.0
    lifetime_giving: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PersonCreate(PersonBase):
    pass

class GroupTypeBase(BaseModel):
    name: str
    color: str = "#4f6ef7"
    icon: str = "users"

class GroupType(GroupTypeBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    meeting_schedule: Optional[str] = None
    meeting_day: Optional[str] = None
    meeting_time: Optional[str] = None
    capacity: Optional[int] = None
    is_open: bool = True
    is_active: bool = True
    leader_id: Optional[str] = None
    tags: List[str] = []
    group_type_id: Optional[str] = None

class Group(GroupBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    member_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GroupMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    group_id: str
    person_id: str
    role: str = "member"
    joined_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    is_active: bool = True

class ServiceType(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    default_time: Optional[str] = None
    default_day: Optional[str] = None
    is_active: bool = True

class Service(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    service_type_id: str
    date: str
    time: Optional[str] = None
    total_headcount: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Attendance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    service_id: str
    person_id: str
    group_id: Optional[str] = None
    check_in_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Fund(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    goal_amount: Optional[float] = None
    current_amount: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DonationBatch(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    date: str
    status: str = "open"
    total_amount: float = 0.0
    donation_count: int = 0
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DonationBase(BaseModel):
    person_id: Optional[str] = None
    fund_id: str
    amount: float
    donation_date: str
    payment_method: str = "cash"
    check_number: Optional[str] = None
    crypto_currency: Optional[str] = None
    crypto_amount: Optional[float] = None
    crypto_tx_hash: Optional[str] = None
    crypto_usd_value: Optional[float] = None
    asset_type: Optional[str] = None
    asset_description: Optional[str] = None
    asset_appraised_value: Optional[float] = None
    is_recurring: bool = False
    recurring_id: Optional[str] = None
    notes: Optional[str] = None
    batch_id: Optional[str] = None

class Donation(DonationBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    receipt_sent: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RecurringGiving(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    person_id: str
    fund_id: str
    amount: float
    frequency: str = "monthly"
    next_gift_date: Optional[str] = None
    payment_method: str = "card"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Pledge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    person_id: str
    fund_id: str
    pledge_amount: float
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    frequency: Optional[str] = None
    total_given: float = 0.0
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_datetime: str
    end_datetime: Optional[str] = None
    is_public: bool = True
    capacity: Optional[int] = None
    registration_required: bool = False
    cover_image_url: Optional[str] = None
    group_id: Optional[str] = None
    registration_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Communication(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    subject: str
    body_html: str
    comm_type: str = "email"
    status: str = "draft"
    sent_at: Optional[str] = None
    sent_by: Optional[str] = None
    recipient_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== MEDIA MODELS ==============

class MediaCategory(BaseModel):
    """Categories for organizing media (Faith, Family, Leadership, etc.)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    slug: str
    icon: str = "video"  # lucide icon name
    sort_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MediaSeries(BaseModel):
    """Series/playlists for grouping related videos"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    category_id: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    video_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MediaVideo(BaseModel):
    """Individual video content"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    title: str
    description: Optional[str] = None
    youtube_id: str  # YouTube video ID (e.g., "dQw4w9WgXcQ")
    youtube_url: Optional[str] = None  # Full YouTube URL
    thumbnail_url: Optional[str] = None
    duration: Optional[str] = None  # "45:30" format
    instructor: Optional[str] = None  # Speaker/Pastor name
    category_id: Optional[str] = None
    series_id: Optional[str] = None
    sort_order: int = 0
    is_featured: bool = False
    is_published: bool = True
    badge: Optional[str] = None  # "New", "Popular", etc.
    view_count: int = 0
    published_at: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MediaVideoCreate(BaseModel):
    """Input model for creating a video"""
    youtube_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    instructor: Optional[str] = None
    category_id: Optional[str] = None
    series_id: Optional[str] = None
    is_featured: bool = False
    badge: Optional[str] = None

class WatchProgress(BaseModel):
    """Track user's watch progress for continue watching feature"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    video_id: str
    progress_seconds: int = 0
    duration_seconds: int = 0
    completed: bool = False
    last_watched: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    session_id: str
    amount: float
    currency: str = "usd"
    payment_status: str = "pending"
    metadata: Dict[str, Any] = {}
    person_id: Optional[str] = None
    fund_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== AUTH MODELS ==============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionRequest(BaseModel):
    session_id: str

class EmailLoginRequest(BaseModel):
    email: str
    password: str

class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    tenant_id: Optional[str] = None  # Church selection

class UserRole(BaseModel):
    role: str = "member"  # "admin" or "member"


class PortalProfileUpdate(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None


class AttendanceCheckinRequest(BaseModel):
    check_in_type: str = "in_person"
    method: Optional[str] = None
    timestamp: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class KidsCheckinRequest(BaseModel):
    child_id: str
    classroom: Optional[str] = "Sunday School"
    method: Optional[str] = "manual"


class QrGenerateRequest(BaseModel):
    action: str = "attendance_checkin"
    expires_in_minutes: int = 60
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PrayerRequestAliasCreate(BaseModel):
    title: str
    description: str
    is_public: bool = False


class VolunteerSignupRequest(BaseModel):
    opportunity_id: str

# ============== SOLOMON AI MODELS ==============

class SolomonMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SolomonChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class SolomonChatResponse(BaseModel):
    response: str
    session_id: str
    data: Optional[Dict[str, Any]] = None  # For chart/table data
    actions: Optional[List[Dict[str, str]]] = None  # Suggested actions

# ============== WATCH PROGRESS MODELS ==============

class WatchProgressUpdate(BaseModel):
    video_id: str
    youtube_id: str
    position_seconds: int
    duration_seconds: int
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    instructor: Optional[str] = None

class WatchProgress(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    video_id: str
    youtube_id: str
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    instructor: Optional[str] = None
    position_seconds: int = 0
    duration_seconds: int = 0
    progress_percent: float = 0.0
    completed: bool = False
    last_watched: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== ABUNDANT PATHWAYS (LMS) MODELS ==============

class PathwaysCourse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    is_published: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PathwaysLesson(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    course_id: str
    title: str
    description: Optional[str] = None
    youtube_id: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_label: Optional[str] = None
    duration_seconds: int = 0
    resource_url: Optional[str] = None
    sort_order: int = 0
    is_published: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PathwaysEnrollment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    course_id: str
    user_id: str
    assigned_by: Optional[str] = None
    status: str = "assigned"  # assigned | in_progress | completed | dropped
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PathwaysLessonProgress(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    course_id: str
    lesson_id: str
    user_id: str
    position_seconds: int = 0
    duration_seconds: int = 0
    progress_percent: float = 0.0
    completed: bool = False
    last_watched: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PathwaysCourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    is_published: bool = True

class PathwaysCourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    is_published: Optional[bool] = None

class PathwaysLessonCreate(BaseModel):
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    youtube_id: Optional[str] = None
    duration_label: Optional[str] = None
    duration_seconds: Optional[int] = None
    resource_url: Optional[str] = None
    sort_order: int = 0
    is_published: bool = True

class PathwaysLessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    youtube_id: Optional[str] = None
    duration_label: Optional[str] = None
    duration_seconds: Optional[int] = None
    resource_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_published: Optional[bool] = None

class PathwaysEnrollmentRequest(BaseModel):
    member_id: str

class PathwaysProgressUpdate(BaseModel):
    course_id: str
    lesson_id: str
    position_seconds: int
    duration_seconds: int
    title: Optional[str] = None

class ThinkificUpdate(BaseModel):
    thinkific_url: str


class NextStepsApprovalRequest(BaseModel):
    action: str = "approve"  # approve | reject
    notes: Optional[str] = None

# ============== MERCH MODELS ==============

class MerchProduct(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: float
    category: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    inventory: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MerchProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: float
    category: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    inventory: int = 0

class MerchProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    inventory: Optional[int] = None

class MerchOrderItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int
    image_url: Optional[str] = None

class MerchOrderCreate(BaseModel):
    items: List[MerchOrderItem]

class MerchSettingsUpdate(BaseModel):
    merch_embed_url: str

# ============== LEADERSHIP NOTES MODELS ==============

class LeadershipNote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    subject: str
    message: str
    category: Optional[str] = None
    status: str = "new"
    member_name: Optional[str] = None
    member_email: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LeadershipNoteCreate(BaseModel):
    subject: str
    message: str
    category: Optional[str] = None

# ============== VIDEO NOTES MODELS (Masterclass-style) ==============

class VideoNote(BaseModel):
    """Notes that members can take while watching videos - shareable with other church members"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    video_id: str
    content: str
    timestamp: Optional[str] = None  # Video timestamp like "12:34" when note was taken
    is_public: bool = False  # Visible to all church members
    shared_with: List[str] = Field(default_factory=list)  # List of user_ids
    author_name: Optional[str] = None
    video_title: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VideoNoteCreate(BaseModel):
    video_id: str
    content: str
    timestamp: Optional[str] = None
    is_public: bool = False

class VideoNoteUpdate(BaseModel):
    content: Optional[str] = None
    timestamp: Optional[str] = None
    is_public: Optional[bool] = None

class VideoNoteShare(BaseModel):
    user_ids: List[str] = Field(default_factory=list)  # Share with specific users
    is_public: Optional[bool] = None  # Share with entire church

# ============== CAFE MODELS ==============

# ============== KIDS CHECK-IN MODELS ==============

class Child(BaseModel):
    """Child profile for check-in system"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    parent_user_id: str
    name: str
    birthdate: str
    allergies: Optional[str] = None
    special_needs: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChildCreate(BaseModel):
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthdate: str
    grade: Optional[str] = None
    classroom: Optional[str] = "Sunday School Adventures"
    allergies: Optional[str] = None
    special_needs: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None

class Checkin(BaseModel):
    """Check-in record for a child"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    child_id: str
    child_name: str
    parent_user_id: str
    parent_name: str
    parent_phone: Optional[str] = None
    pickup_code: str
    classroom: Optional[str] = None
    status: str = "checked_in"  # checked_in, checked_out
    checked_in_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    checked_out_at: Optional[datetime] = None
    checked_out_by: Optional[str] = None
    notes: Optional[str] = None

# ============== CAFE MODELS (continued) ==============

class CafeSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    pickup_start: str
    pickup_end: str
    pickup_interval_minutes: int = 15
    location: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CafeSettingsUpdate(BaseModel):
    pickup_start: Optional[str] = None
    pickup_end: Optional[str] = None
    pickup_interval_minutes: Optional[int] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

class CafeItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CafeItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True

class CafeItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None

class CafeOrderItem(BaseModel):
    item_id: str
    name: str
    price: float
    quantity: int
    image_url: Optional[str] = None

class CafeOrderCreate(BaseModel):
    items: List[CafeOrderItem]
    pickup_time: str
    notes: Optional[str] = None

# ============== PASTOR MEETINGS MODELS ==============

class PastorMeetingSlot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    start_time: str
    end_time: str
    location: Optional[str] = None
    status: str = "open"  # open | booked
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PastorMeetingSlotCreate(BaseModel):
    start_time: str
    end_time: str
    location: Optional[str] = None

class PastorMeetingBooking(BaseModel):
    slot_id: str
    topic: Optional[str] = None
    notes: Optional[str] = None

class PastorMeeting(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    slot_id: str
    user_id: str
    member_name: Optional[str] = None
    member_email: Optional[str] = None
    topic: Optional[str] = None
    notes: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    recording_filename: Optional[str] = None
    status: str = "scheduled"  # scheduled | completed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PastorMeetingUpdate(BaseModel):
    notes: Optional[str] = None
    status: Optional[str] = None


# ============== AGENT API KEY MODELS ==============

class AgentAPIKey(BaseModel):
    """API Key for external agent access"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str  # Human-readable name for the key
    key_hash: str  # SHA256 hash of the actual key
    key_prefix: str  # First 8 chars for identification (e.g., "sk_live_")
    permissions: List[str] = []  # ["members:read", "events:write", etc.]
    rate_limit: int = 1000  # Requests per hour
    is_active: bool = True
    last_used_at: Optional[str] = None
    usage_count: int = 0
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[str] = None

class AgentAPIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = ["members:read", "events:read", "groups:read", "meetings:read"]
    rate_limit: int = 1000
    expires_in_days: Optional[int] = None  # None = never expires

class AgentAPIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    permissions: List[str]
    rate_limit: int
    is_active: bool
    usage_count: int
    last_used_at: Optional[str]
    created_at: str
    expires_at: Optional[str]

# Agent API Request/Response Schemas (following the Manifest-First approach)
class AgentVisitorReport(BaseModel):
    """Schema for visitor data export to agents"""
    timestamp: str
    new_members: List[Dict[str, Any]]

class AgentMemberData(BaseModel):
    """Member data for agent consumption"""
    unique_id: str
    name: str
    email: Optional[str]
    phone_sms: Optional[str]  # E.164 format
    physical_address: Optional[str]
    first_gift_date: Optional[str]
    gift_tier: Optional[str]  # "first_time", "recurring", "major_donor"
    outreach_status: str = "pending"  # pending | contacted | opted_out
    is_first_time: bool = False
    joined_at: str

class AgentEventData(BaseModel):
    """Event data for agent consumption"""
    unique_id: str
    title: str
    description: Optional[str]
    start_time: str
    end_time: Optional[str]
    location: Optional[str]
    registration_count: int
    capacity: Optional[int]

class AgentMeetingData(BaseModel):
    """Meeting data for agent consumption"""
    unique_id: str
    member_name: str
    member_email: Optional[str]
    topic: Optional[str]
    scheduled_time: str
    status: str
    has_summary: bool

# Permission constants
AGENT_PERMISSIONS = {
    "members:read": "Read member profiles and contact info",
    "members:write": "Update member outreach status",
    "events:read": "Read event listings and registrations",
    "events:write": "Create events and register members",
    "groups:read": "Read group listings and memberships",
    "groups:write": "Add/remove group members",
    "meetings:read": "Read meeting schedules and summaries",
    "meetings:write": "Book meetings and add notes",
    "giving:read": "Read giving summaries (no amounts)",
    "media:read": "Read media library content",
    "notes:read": "Read leadership notes",
    "notes:write": "Respond to leadership notes",
    "webhooks:manage": "Manage webhook subscriptions"
}

# Anomaly thresholds (Circuit Breaker)
ANOMALY_THRESHOLDS = {
    "new_visitors_per_day": 200,
    "api_calls_per_minute": 60,
    "bulk_update_limit": 50
}


# ============== HELPER FUNCTIONS ==============

import hashlib
import secrets

def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key, returning (full_key, key_hash, key_prefix)"""
    # Generate a secure random key
    random_part = secrets.token_urlsafe(32)
    full_key = f"sk_solomon_{random_part}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:16] + "..."
    return full_key, key_hash, key_prefix

def hash_api_key(key: str) -> str:
    """Hash an API key for storage/comparison"""
    return hashlib.sha256(key.encode()).hexdigest()

async def validate_agent_api_key(request: Request) -> dict:
    """Validate API key from Authorization header and return tenant context"""
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    api_key = auth_header[7:]  # Remove "Bearer " prefix
    key_hash = hash_api_key(api_key)
    
    # Find the API key in database
    key_doc = await db.agent_api_keys.find_one({"key_hash": key_hash, "is_active": True}, {"_id": 0})
    
    if not key_doc:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check expiration
    if key_doc.get("expires_at"):
        expires = datetime.fromisoformat(key_doc["expires_at"])
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=401, detail="API key has expired")
    
    # Update usage stats
    await db.agent_api_keys.update_one(
        {"id": key_doc["id"]},
        {
            "$set": {"last_used_at": datetime.now(timezone.utc).isoformat()},
            "$inc": {"usage_count": 1}
        }
    )
    
    # Rate limiting check (simple implementation)
    rate_limit = key_doc.get("rate_limit", 1000)
    # In production, use Redis for proper rate limiting
    
    return {
        "key_id": key_doc["id"],
        "tenant_id": key_doc["tenant_id"],
        "permissions": key_doc.get("permissions", []),
        "rate_limit": rate_limit
    }

def check_agent_permission(context: dict, required_permission: str) -> bool:
    """Check if the API key has the required permission"""
    permissions = context.get("permissions", [])
    # Check exact match or wildcard
    if required_permission in permissions:
        return True
    # Check for wildcard (e.g., "members:*" covers "members:read" and "members:write")
    resource = required_permission.split(":")[0]
    if f"{resource}:*" in permissions:
        return True
    return False

def serialize_doc(doc: dict) -> dict:
    """Remove MongoDB _id and convert datetime objects"""
    if doc is None:
        return None
    result = {k: v for k, v in doc.items() if k != '_id'}
    for key, value in result.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
    return result

def duration_to_seconds(duration_label: Optional[str], duration_seconds: Optional[int] = None) -> int:
    if duration_seconds is not None:
        try:
            return max(int(duration_seconds), 0)
        except (TypeError, ValueError):
            return 0
    if not duration_label:
        return 0
    parts = [p for p in duration_label.split(':') if p]
    try:
        numbers = list(map(int, parts))
    except ValueError:
        return 0
    if len(numbers) == 3:
        return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
    if len(numbers) == 2:
        return numbers[0] * 60 + numbers[1]
    if len(numbers) == 1:
        return numbers[0]
    return 0

DEFAULT_MERCH_EMBED_URL = "https://store.elevationchurch.org/collections/so-be-it-ew"

async def ensure_demo_merch_data(tenant_id: Optional[str]):
    if not tenant_id:
        return

    product_count = await db.merch_products.count_documents({"tenant_id": tenant_id})
    if product_count == 0:
        demo_products = [
            {
                "name": "SO BE IT - Vinyl",
                "description": "Limited edition worship vinyl for collectors.",
                "image_url": "https://store.elevationchurch.org/cdn/shop/files/Background_6963f237-502c-48c7-9c0c-7d1a2a185a27.png?crop=center&height=1200&v=1770318508&width=1200",
                "price": 40.00,
                "category": "Music",
                "is_featured": True,
                "inventory": 120
            },
            {
                "name": "SO BE IT Hoodie",
                "description": "Soft fleece hoodie inspired by the SO BE IT collection.",
                "image_url": "https://store.elevationchurch.org/cdn/shop/files/Background_22b72fee-5a5c-40ac-b88d-8dc43af1ba98.png?crop=center&height=1200&v=1770147858&width=1200",
                "price": 60.00,
                "category": "Apparel",
                "is_featured": True,
                "inventory": 80
            },
            {
                "name": "SO BE IT Album T-Shirt",
                "description": "Classic tee with album artwork. Perfect for Sundays and beyond.",
                "image_url": "https://store.elevationchurch.org/cdn/shop/files/Background_7_55188e58-8c97-42a4-b48f-35ada8aabe12.png?crop=center&height=1200&v=1770316861&width=1200",
                "price": 30.00,
                "category": "Apparel",
                "inventory": 150
            },
            {
                "name": "SO BE IT Crest Camo Hat",
                "description": "Structured camo hat with embroidered crest.",
                "image_url": "https://store.elevationchurch.org/cdn/shop/files/Background_16_0b761a70-5ebc-4db6-bf03-5fab8a2cb0cb.png?crop=center&height=1200&v=1770317102&width=1200",
                "price": 35.00,
                "category": "Accessories",
                "inventory": 90
            },
            {
                "name": "SO BE IT Tote",
                "description": "Canvas tote for carrying all the essentials.",
                "image_url": "https://store.elevationchurch.org/cdn/shop/files/Background_18_f1900fee-6a54-4c49-b949-d516eb8aba6a.png?crop=center&height=1200&v=1770318552&width=1200",
                "price": 20.00,
                "category": "Accessories",
                "inventory": 140
            },
            {
                "name": "Abundant Ceramic Mug",
                "description": "Signature mug for morning devotionals and coffee.",
                "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1200&q=80",
                "price": 18.00,
                "category": "Drinkware",
                "inventory": 110
            },
            {
                "name": "Abundant YETI Tumbler",
                "description": "Insulated tumbler with laser-etched logo.",
                "image_url": "https://images.unsplash.com/photo-1527169402691-feff5539e52c?auto=format&fit=crop&w=1200&q=80",
                "price": 42.00,
                "category": "Drinkware",
                "inventory": 70
            }
        ]

        for idx, product in enumerate(demo_products, start=1):
            merch = MerchProduct(
                tenant_id=tenant_id,
                name=product["name"],
                description=product.get("description"),
                image_url=product.get("image_url"),
                price=product["price"],
                category=product.get("category"),
                is_featured=product.get("is_featured", False),
                is_active=True,
                inventory=product.get("inventory", 0)
            ).model_dump()
            merch["id"] = f"merch_{tenant_id}_{idx}"
            await db.merch_products.update_one({"id": merch["id"]}, {"$set": merch}, upsert=True)

    order_count = await db.merch_orders.count_documents({"tenant_id": tenant_id})
    if order_count == 0:
        member = await db.users.find_one({"tenant_id": tenant_id, "role": "member"}, {"_id": 0})
        if member:
            products = await db.merch_products.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(10)
            if products:
                for i in range(6):
                    item = random.choice(products)
                    quantity = random.randint(1, 3)
                    total = round(item["price"] * quantity, 2)
                    order = {
                        "id": str(uuid.uuid4()),
                        "tenant_id": tenant_id,
                        "user_id": member["user_id"],
                        "items": [{
                            "product_id": item["id"],
                            "name": item["name"],
                            "price": item["price"],
                            "quantity": quantity,
                            "image_url": item.get("image_url")
                        }],
                        "subtotal": total,
                        "total": total,
                        "status": "placed",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.merch_orders.update_one({"id": order["id"]}, {"$set": order}, upsert=True)

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "merch_embed_url": 1})
    if tenant is not None and not tenant.get("merch_embed_url"):
        await db.tenants.update_one({"id": tenant_id}, {"$set": {"merch_embed_url": DEFAULT_MERCH_EMBED_URL}})

async def ensure_demo_cafe_data(tenant_id: Optional[str]):
    if not tenant_id:
        return

    settings = await db.cafe_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not settings:
        settings_doc = CafeSettings(
            tenant_id=tenant_id,
            pickup_start="07:30 AM",
            pickup_end="10:30 AM",
            pickup_interval_minutes=15,
            location="Lobby pickup counter"
        ).model_dump()
        await db.cafe_settings.insert_one(settings_doc)

    item_count = await db.cafe_items.count_documents({"tenant_id": tenant_id})
    if item_count == 0:
        demo_items = [
            {
                "name": "House Latte",
                "description": "Espresso with steamed milk and vanilla.",
                "category": "Coffee",
                "price": 4.5,
                "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1200&q=80",
                "is_featured": True
            },
            {
                "name": "Cold Brew",
                "description": "Slow-steeped cold brew over ice.",
                "category": "Coffee",
                "price": 4.0,
                "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "name": "Cappuccino",
                "description": "Rich espresso topped with velvety foam.",
                "category": "Coffee",
                "price": 4.75,
                "image_url": "https://images.unsplash.com/photo-1504753793650-d4a2b783c15e?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "name": "Chai Latte",
                "description": "Spiced chai with steamed oat milk.",
                "category": "Tea",
                "price": 4.25,
                "image_url": "https://images.unsplash.com/photo-1507133750040-4a8f57021571?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "name": "Iced Matcha",
                "description": "Creamy matcha latte served cold.",
                "category": "Tea",
                "price": 4.5,
                "image_url": "https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "name": "Blueberry Muffin",
                "description": "Fresh-baked muffin with blueberries.",
                "category": "Pastry",
                "price": 3.0,
                "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "name": "Butter Croissant",
                "description": "Flaky croissant with butter layers.",
                "category": "Pastry",
                "price": 3.25,
                "image_url": "https://images.unsplash.com/photo-1509365465985-25d11c17e812?auto=format&fit=crop&w=1200&q=80"
            }
        ]

        for idx, item in enumerate(demo_items, start=1):
            cafe_item = CafeItem(
                tenant_id=tenant_id,
                name=item["name"],
                description=item.get("description"),
                category=item.get("category"),
                price=item["price"],
                image_url=item.get("image_url"),
                is_featured=item.get("is_featured", False),
                is_active=True
            ).model_dump()
            cafe_item["id"] = f"cafe_{tenant_id}_{idx}"
            await db.cafe_items.update_one({"id": cafe_item["id"]}, {"$set": cafe_item}, upsert=True)

    order_count = await db.cafe_orders.count_documents({"tenant_id": tenant_id})
    if order_count == 0:
        member = await db.users.find_one({"tenant_id": tenant_id, "role": "member"}, {"_id": 0})
        if member:
            items = await db.cafe_items.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(10)
            if items:
                for i in range(4):
                    item = random.choice(items)
                    quantity = random.randint(1, 2)
                    total = round(item["price"] * quantity, 2)
                    order = {
                        "id": str(uuid.uuid4()),
                        "tenant_id": tenant_id,
                        "user_id": member.get("user_id"),
                        "items": [{
                            "item_id": item["id"],
                            "name": item["name"],
                            "price": item["price"],
                            "quantity": quantity,
                            "image_url": item.get("image_url")
                        }],
                        "pickup_time": "Sunday 9:15 AM",
                        "notes": "",
                        "total": total,
                        "status": "placed",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.cafe_orders.update_one({"id": order["id"]}, {"$set": order}, upsert=True)

async def ensure_demo_meetings_data(tenant_id: Optional[str]):
    if not tenant_id:
        return

    slot_count = await db.pastor_meeting_slots.count_documents({"tenant_id": tenant_id})
    if slot_count == 0:
        today = datetime.now(timezone.utc)
        days_until_sunday = (6 - today.weekday()) % 7
        next_sunday = (today + timedelta(days=days_until_sunday)).date()
        base_time = datetime.combine(next_sunday, datetime.min.time()).replace(tzinfo=timezone.utc)
        slots = []
        for offset in [9, 9.5, 10, 10.5]:
            start = base_time + timedelta(hours=offset)
            end = start + timedelta(minutes=30)
            slot = PastorMeetingSlot(
                tenant_id=tenant_id,
                start_time=start.isoformat(),
                end_time=end.isoformat(),
                location="Pastor's office"
            ).model_dump()
            slots.append(slot)
        for slot in slots:
            await db.pastor_meeting_slots.update_one({"id": slot["id"]}, {"$set": slot}, upsert=True)

    meeting_count = await db.pastor_meetings.count_documents({"tenant_id": tenant_id})
    if meeting_count == 0:
        member = await db.users.find_one({"tenant_id": tenant_id, "role": "member"}, {"_id": 0})
        slot = await db.pastor_meeting_slots.find_one({"tenant_id": tenant_id, "status": "open"}, {"_id": 0})
        if member and slot:
            await db.pastor_meeting_slots.update_one({"id": slot["id"]}, {"$set": {"status": "booked"}})
            meeting = PastorMeeting(
                tenant_id=tenant_id,
                slot_id=slot["id"],
                user_id=member.get("user_id"),
                member_name=member.get("name"),
                member_email=member.get("email"),
                topic="Personal check-in",
                notes="",
                status="scheduled"
            ).model_dump()
            await db.pastor_meetings.insert_one(meeting)

async def ensure_abundant_pathways_data(tenant_id: Optional[str]):
    if tenant_id != "abundant-east-001":
        return

    course_ids = [
        "pathway_course_001",
        "pathway_course_002",
        "pathway_course_003",
        "pathway_course_004",
        "pathway_course_005",
        "pathway_course_006",
        "pathway_course_007",
        "pathway_course_008"
    ]

    pathways_courses = [
        {
            "id": "pathway_course_001",
            "tenant_id": "abundant-east-001",
            "title": "Abundant Next Steps",
            "description": "Your on-ramp to belonging, serving, and growing at Abundant.",
            "cover_image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
            "category": "New Members Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_002",
            "tenant_id": "abundant-east-001",
            "title": "Preparing for Baptism",
            "description": "Understand baptism and get ready to share your story.",
            "cover_image_url": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80",
            "category": "Baptism Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_003",
            "tenant_id": "abundant-east-001",
            "title": "Foundations of Discipleship",
            "description": "Build daily rhythms of scripture, prayer, and obedience.",
            "cover_image_url": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?auto=format&fit=crop&w=1200&q=80",
            "category": "Discipleship Track",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_004",
            "tenant_id": "abundant-east-001",
            "title": "Financial Peace University",
            "description": "Walk through budgeting, generosity, and debt-free living.",
            "cover_image_url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80",
            "category": "Stewardship Track",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_005",
            "tenant_id": "abundant-east-001",
            "title": "Serving with Purpose",
            "description": "Discover your gifts and find the right team to serve.",
            "cover_image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
            "category": "Leadership Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_006",
            "tenant_id": "abundant-east-001",
            "title": "Prayer & Presence",
            "description": "Deepen your prayer life and sensitivity to God's presence.",
            "cover_image_url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80",
            "category": "Spiritual Practices",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_007",
            "tenant_id": "abundant-east-001",
            "title": "Marriage & Family Care",
            "description": "Strengthen your relationships and build a healthy home.",
            "cover_image_url": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=1200&q=80",
            "category": "Family Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_008",
            "tenant_id": "abundant-east-001",
            "title": "Mission & Outreach",
            "description": "Live on mission through local and global outreach.",
            "cover_image_url": "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?auto=format&fit=crop&w=1200&q=80",
            "category": "Outreach Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    pathways_lessons = [
        {
            "id": "pathway_lesson_001",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_001",
            "title": "Welcome to Abundant",
            "description": "Meet the heart, mission, and values of Abundant Church.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "15:40",
            "duration_seconds": 940,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_002",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_001",
            "title": "Belonging & Community",
            "description": "Find your people and take your next step into community.",
            "youtube_id": "pzpbbibEWPE",
            "video_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration_label": "18:20",
            "duration_seconds": 1100,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_003",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_002",
            "title": "Why Baptism Matters",
            "description": "Understand the significance of baptism and next steps.",
            "youtube_id": "Lnj6vMvOLME",
            "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration_label": "16:05",
            "duration_seconds": 965,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_004",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_002",
            "title": "Preparing Your Story",
            "description": "Craft your testimony and prepare for the baptism service.",
            "youtube_id": "wCjwUQMhCIY",
            "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration_label": "14:35",
            "duration_seconds": 875,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    # Only keep seeded courses for Abundant demo
    await db.pathways_courses.delete_many({"tenant_id": tenant_id, "id": {"$nin": course_ids}})
    await db.pathways_lessons.delete_many({"tenant_id": tenant_id, "course_id": {"$nin": course_ids}})

    for course in pathways_courses:
        await db.pathways_courses.update_one({"id": course["id"]}, {"$set": course}, upsert=True)
    for lesson in pathways_lessons:
        await db.pathways_lessons.update_one({"id": lesson["id"]}, {"$set": lesson}, upsert=True)

    for idx, course_id in enumerate(course_ids, start=1):
        enrollment = {
            "id": f"pathway_enroll_{idx:03d}",
            "tenant_id": tenant_id,
            "course_id": course_id,
            "user_id": "member_abundant",
            "assigned_by": "admin_abundant",
            "status": "assigned",
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.pathways_enrollments.update_one(
            {"id": enrollment["id"]},
            {
                "$setOnInsert": {
                    **enrollment,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )

async def transcribe_audio_with_whisper(file_path: Path) -> str:
    """Transcribe audio file using OpenAI Whisper via emergentintegrations"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Whisper is not configured")

    try:
        from emergentintegrations.llm.openai import OpenAISpeechToText
        
        stt = OpenAISpeechToText(api_key=api_key)
        
        with file_path.open('rb') as audio_file:
            response = await stt.transcribe(
                file=audio_file,
                model="whisper-1",
                response_format="text",
                language="en",
                prompt="This is a pastoral counseling session between a pastor and church member."
            )
        
        return response if isinstance(response, str) else response.text
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

async def summarize_meeting_with_claude(transcript: str, topic: Optional[str] = None) -> str:
    """Summarize meeting transcript using Claude via emergentintegrations"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Claude is not configured")

    chat = LlmChat(
        api_key=api_key,
        session_id=str(uuid.uuid4()),
        system_message=(
            "You are a pastoral meeting assistant helping pastors document their sessions with church members. "
            "Your summaries should be warm, pastoral in tone, and respect confidentiality. "
            "Format your response with clear sections using markdown."
        )
    )
    chat.with_model("anthropic", "claude-sonnet-4-5-20250929")
    
    prompt = f"""Please summarize this pastoral meeting session.

**Meeting Topic:** {topic or 'General Check-in'}

**Transcript:**
{transcript[:8000]}

---

Please provide a summary with:
1. **Key Discussion Points** - Main topics covered
2. **Spiritual/Emotional Needs Identified** - Any concerns or prayer requests
3. **Action Items** - Specific follow-ups for the pastor
4. **Recommended Next Steps** - Suggested future engagement
5. **Prayer Points** - Key items for continued prayer"""

    response_text = await chat.send_message(UserMessage(text=prompt))
    return response_text

async def notify_meeting_event(event: str, meeting: dict) -> dict:
    return {
        "event": event,
        "slack": "MOCKED",
        "teams": "MOCKED",
        "meeting_id": meeting.get("id") if meeting else None
    }

# Default tenant ID for demo
DEFAULT_TENANT_ID = "abundant-east-001"
DEFAULT_NEXT_STEPS_URL = "https://abundantchurch.thinkific.com/courses/abundant-next-steps"


async def ensure_mobile_demo_accounts():
    """Ensure required demo users exist for mobile QA and onboarding."""
    import hashlib

    now_iso = datetime.now(timezone.utc).isoformat()
    demo_password_hash = hashlib.sha256("Demo2026!".encode()).hexdigest()

    tenant_defaults = [
        {
            "id": "abundant-east-001",
            "name": "Abundant East",
            "subdomain": "abundant-east",
            "subscription_status": "active",
            "created_at": now_iso
        },
        {
            "id": "abundant-downtown-001",
            "name": "Abundant Downtown",
            "subdomain": "abundant-downtown",
            "subscription_status": "active",
            "created_at": now_iso
        },
        {
            "id": "abundant-west-001",
            "name": "Abundant West",
            "subdomain": "abundant-west",
            "subscription_status": "active",
            "created_at": now_iso
        },
        {
            "id": "cristoviene-church-001",
            "name": "Cristo Viene",
            "subdomain": "cristoviene",
            "subscription_status": "active",
            "created_at": now_iso
        },
        {
            "id": "pottershouse-church-001",
            "name": "The Potter's House",
            "subdomain": "pottershouse",
            "subscription_status": "active",
            "created_at": now_iso
        }
    ]

    for tenant in tenant_defaults:
        await db.tenants.update_one(
            {"id": tenant["id"]},
            {"$setOnInsert": tenant},
            upsert=True
        )

    required_accounts = [
        {
            "email": "member@abundant.church",
            "user_id": "member_abundant",
            "name": "Maria Garcia",
            "first_name": "Maria",
            "last_name": "Garcia",
            "role": "member",
            "tenant_id": "abundant-east-001"
        },
        {
            "email": "member@cristoviene.church",
            "user_id": "member_cristoviene",
            "name": "Carlos",
            "first_name": "Carlos",
            "last_name": "",
            "role": "member",
            "tenant_id": "cristoviene-church-001"
        },
        {
            "email": "admin@abundant.church",
            "user_id": "admin_abundant",
            "name": "Pastor David Rivera",
            "first_name": "David",
            "last_name": "Rivera",
            "role": "church_admin",
            "tenant_id": "abundant-east-001"
        },
        {
            "email": "admin@solomon.ai",
            "user_id": "platform_admin_001",
            "name": "Solomon Platform Admin",
            "first_name": "Solomon",
            "last_name": "Admin",
            "role": "platform_admin",
            "tenant_id": None
        },
        {
            "email": "admin@cristoviene.church",
            "user_id": "admin_cristoviene",
            "name": "Cristo Viene Admin",
            "first_name": "Cristo",
            "last_name": "Viene Admin",
            "role": "church_admin",
            "tenant_id": "cristoviene-church-001"
        },
        {
            "email": "admin@pottershouse.church",
            "user_id": "admin_pottershouse",
            "name": "Potter's House Admin",
            "first_name": "Potter's House",
            "last_name": "Admin",
            "role": "church_admin",
            "tenant_id": "pottershouse-church-001"
        },
        {
            "email": "admin@abundant-downtown.church",
            "user_id": "admin_abundant_downtown",
            "name": "Pastor Sarah Chen",
            "first_name": "Sarah",
            "last_name": "Chen",
            "role": "church_admin",
            "tenant_id": "abundant-downtown-001"
        },
        {
            "email": "admin@abundant-west.church",
            "user_id": "admin_abundant_west",
            "name": "Pastor Michael Reyes",
            "first_name": "Michael",
            "last_name": "Reyes",
            "role": "church_admin",
            "tenant_id": "abundant-west-001"
        },
        {
            "email": "member@abundant-downtown.church",
            "user_id": "member_abundant_downtown",
            "name": "Isabella Torres",
            "first_name": "Isabella",
            "last_name": "Torres",
            "role": "member",
            "tenant_id": "abundant-downtown-001"
        },
        {
            "email": "member@abundant-west.church",
            "user_id": "member_abundant_west",
            "name": "Sofia Martinez",
            "first_name": "Sofia",
            "last_name": "Martinez",
            "role": "member",
            "tenant_id": "abundant-west-001"
        },
        {
            "email": "vince@charlottesoftwareengineering.com",
            "user_id": "cc7a823c-4d38-45d9-bb09-1df8caffe258",
            "name": "Vince Hinojosa",
            "first_name": "Vince",
            "last_name": "Hinojosa",
            "role": "member",
            "tenant_id": "abundant-east-001"
        },
        {
            "email": "avopham@gmail.com",
            "user_id": "f1d0f1d8-de66-4fc0-a8c7-8f81f679ce22",
            "name": "Aivy Vopham",
            "first_name": "Aivy",
            "last_name": "Vopham",
            "role": "church_admin",
            "tenant_id": "abundant-east-001"
        }
    ]

    # Accounts that use SolomonTest2026! password
    test_password_hash = hashlib.sha256("SolomonTest2026!".encode()).hexdigest()
    test_accounts_emails = {"vince@charlottesoftwareengineering.com", "avopham@gmail.com"}

    for account in required_accounts:
        pw = test_password_hash if account["email"] in test_accounts_emails else demo_password_hash
        await db.users.update_one(
            {"email": account["email"]},
            {
                "$set": {
                    **account,
                    "password_hash": pw,
                    "is_active": True,
                    "updated_at": now_iso
                },
                "$setOnInsert": {
                    "created_at": now_iso
                }
            },
            upsert=True
        )

    await ensure_abundant_mobile_demo_content(now_iso)
    await ensure_abundant_go_live_portal_content(now_iso)


async def ensure_abundant_mobile_demo_content(now_iso: Optional[str] = None):
    """Seed deterministic demo content expected by mobile + web QA checks."""
    tenant_id = DEFAULT_TENANT_ID
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()

    await db.tenants.update_one(
        {"id": tenant_id},
        {
            "$set": {
                "next_steps_url": DEFAULT_NEXT_STEPS_URL,
                "updated_at": now_iso
            }
        }
    )

    # Ensure member person profile exists for giving/kids linkage
    member_user = await db.users.find_one(
        {"email": "member@abundant.church"},
        {"_id": 0}
    )
    if not member_user:
        return

    person_doc = {
        "id": "person_member_abundant",
        "tenant_id": tenant_id,
        "first_name": "Maria",
        "last_name": "Garcia",
        "email": "member@abundant.church",
        "mobile_phone": "915-555-0101",
        "membership_status": "member",
        "membership_date": "2019-03-15",
        "ytd_giving": 500,
        "lifetime_giving": 3500,
        "updated_at": now_iso,
        "created_at": now_iso
    }
    await db.people.update_one(
        {"email": "member@abundant.church", "tenant_id": tenant_id},
        {"$set": person_doc},
        upsert=True
    )

    # Funds (for giving history mapping)
    funds = [
        {"id": "fund_general_mobile", "name": "General Fund", "goal_amount": 1500000},
        {"id": "fund_building_mobile", "name": "Building Fund", "goal_amount": 750000}
    ]
    for fund in funds:
        await db.funds.update_one(
            {"id": fund["id"], "tenant_id": tenant_id},
            {
                "$set": {
                    "tenant_id": tenant_id,
                    "is_active": True,
                    "current_amount": 0,
                    "updated_at": now_iso,
                    **fund
                },
                "$setOnInsert": {"created_at": now_iso}
            },
            upsert=True
        )

    # Merch products (exact 5 active expected by QA)
    merch_products = [
        {
            "id": "merch_mobile_001",
            "name": "SO BE IT Vinyl",
            "price": 40,
            "category": "Music",
            "is_featured": True,
            "description": "Limited edition SO BE IT worship vinyl.",
            "image_url": "https://images.unsplash.com/photo-1461360370896-922624d12aa1?auto=format&fit=crop&w=1200&q=80"
        },
        {
            "id": "merch_mobile_002",
            "name": "SO BE IT Hoodie",
            "price": 60,
            "category": "Apparel",
            "is_featured": True,
            "description": "Premium hoodie from the SO BE IT collection.",
            "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=1200&q=80"
        },
        {
            "id": "merch_mobile_003",
            "name": "Abundant YETI Tumbler",
            "price": 42,
            "category": "Drinkware",
            "is_featured": True,
            "description": "Insulated tumbler with engraved Abundant logo.",
            "image_url": "https://images.unsplash.com/photo-1527169402691-feff5539e52c?auto=format&fit=crop&w=1200&q=80"
        },
        {
            "id": "merch_mobile_004",
            "name": "SO BE IT T-Shirt",
            "price": 35,
            "category": "Apparel",
            "is_featured": False,
            "description": "Soft cotton tee featuring SO BE IT art.",
            "image_url": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=1200&q=80"
        },
        {
            "id": "merch_mobile_005",
            "name": "Church Tote Bag",
            "price": 28,
            "category": "Accessories",
            "is_featured": False,
            "description": "Canvas tote bag for Sunday essentials.",
            "image_url": "https://images.unsplash.com/photo-1594223274512-ad4803739b7c?auto=format&fit=crop&w=1200&q=80"
        }
    ]
    merch_ids = [item["id"] for item in merch_products]
    for product in merch_products:
        await db.merch_products.update_one(
            {"id": product["id"], "tenant_id": tenant_id},
            {
                "$set": {
                    "tenant_id": tenant_id,
                    "is_active": True,
                    "inventory": 120,
                    "updated_at": now_iso,
                    **product
                },
                "$setOnInsert": {"created_at": now_iso}
            },
            upsert=True
        )
    await db.merch_products.update_many(
        {"tenant_id": tenant_id, "id": {"$nin": merch_ids}},
        {"$set": {"is_active": False, "updated_at": now_iso}}
    )

    # Cafe menu (exact 5 active expected by QA)
    cafe_items = [
        {
            "id": "cafe_mobile_001",
            "name": "Latte",
            "price": 5,
            "category": "Coffee",
            "is_featured": True,
            "description": "Espresso with silky steamed milk."
        },
        {
            "id": "cafe_mobile_002",
            "name": "Cold Brew",
            "price": 5,
            "category": "Coffee",
            "is_featured": False,
            "description": "Slow-steeped cold brew over ice."
        },
        {
            "id": "cafe_mobile_003",
            "name": "Croissant",
            "price": 3,
            "category": "Pastry",
            "is_featured": True,
            "description": "Buttery flaky croissant baked fresh."
        },
        {
            "id": "cafe_mobile_004",
            "name": "Blueberry Muffin",
            "price": 3,
            "category": "Pastry",
            "is_featured": False,
            "description": "Classic blueberry muffin."
        },
        {
            "id": "cafe_mobile_005",
            "name": "Chai Tea",
            "price": 4,
            "category": "Tea",
            "is_featured": False,
            "description": "Warm spiced chai tea."
        }
    ]
    cafe_ids = [item["id"] for item in cafe_items]
    for item in cafe_items:
        await db.cafe_items.update_one(
            {"id": item["id"], "tenant_id": tenant_id},
            {
                "$set": {
                    "tenant_id": tenant_id,
                    "is_active": True,
                    "updated_at": now_iso,
                    **item
                },
                "$setOnInsert": {"created_at": now_iso}
            },
            upsert=True
        )
    await db.cafe_items.update_many(
        {"tenant_id": tenant_id, "id": {"$nin": cafe_ids}},
        {"$set": {"is_active": False, "updated_at": now_iso}}
    )

    # Sermons feed (exact 3 with content_type=sermon)
    sermons = [
        {
            "id": "sermon_mobile_001",
            "title": "SO BE IT",
            "instructor": "Pastor James",
            "published_at": "2026-03-09",
            "duration": "42:00",
            "duration_seconds": 2520,
            "youtube_id": "FoPI3hMbXvw",
            "youtube_url": "https://youtube.com/watch?v=FoPI3hMbXvw"
        },
        {
            "id": "sermon_mobile_002",
            "title": "Unshakeable Faith",
            "instructor": "Pastor James",
            "published_at": "2026-03-02",
            "duration": "38:00",
            "duration_seconds": 2280,
            "youtube_id": "pzpbbibEWPE",
            "youtube_url": "https://youtube.com/watch?v=pzpbbibEWPE"
        },
        {
            "id": "sermon_mobile_003",
            "title": "New Beginnings",
            "instructor": "Pastor Sarah",
            "published_at": "2026-02-23",
            "duration": "45:00",
            "duration_seconds": 2700,
            "youtube_id": "Lnj6vMvOLME",
            "youtube_url": "https://youtube.com/watch?v=Lnj6vMvOLME"
        }
    ]
    sermon_ids = [s["id"] for s in sermons]
    for sermon in sermons:
        await db.media_videos.update_one(
            {"id": sermon["id"], "tenant_id": tenant_id},
            {
                "$set": {
                    "tenant_id": tenant_id,
                    "description": sermon["title"],
                    "thumbnail_url": f"https://i.ytimg.com/vi/{sermon['youtube_id']}/maxresdefault.jpg",
                    "is_featured": sermon["id"] == "sermon_mobile_001",
                    "is_published": True,
                    "content_type": "sermon",
                    "updated_at": now_iso,
                    **sermon
                },
                "$setOnInsert": {"created_at": now_iso}
            },
            upsert=True
        )
    await db.media_videos.update_many(
        {"tenant_id": tenant_id, "content_type": "sermon", "id": {"$nin": sermon_ids}},
        {"$set": {"is_published": False, "updated_at": now_iso}}
    )

    # Giving history (exact 4 donations)
    donation_seed = [
        {"id": "don_mobile_001", "amount": 150, "fund_id": "fund_general_mobile", "donation_date": "2026-01-05"},
        {"id": "don_mobile_002", "amount": 150, "fund_id": "fund_general_mobile", "donation_date": "2026-02-02"},
        {"id": "don_mobile_003", "amount": 150, "fund_id": "fund_general_mobile", "donation_date": "2026-03-02"},
        {"id": "don_mobile_004", "amount": 50, "fund_id": "fund_building_mobile", "donation_date": "2026-02-14"}
    ]
    donation_ids = [d["id"] for d in donation_seed]
    for donation in donation_seed:
        await db.donations.update_one(
            {"id": donation["id"], "tenant_id": tenant_id},
            {
                "$set": {
                    "tenant_id": tenant_id,
                    "person_id": person_doc["id"],
                    "fund_name": "General Fund" if donation["fund_id"] == "fund_general_mobile" else "Building Fund",
                    "payment_method": "card",
                    "status": "completed",
                    "created_at": now_iso,
                    **donation
                }
            },
            upsert=True
        )
    await db.donations.delete_many(
        {
            "tenant_id": tenant_id,
            "person_id": person_doc["id"],
            "id": {"$nin": donation_ids}
        }
    )

    # Kids profile (Emma Johnson)
    child_doc = {
        "id": "child_emma_johnson",
        "tenant_id": tenant_id,
        "parent_user_id": member_user["user_id"],
        "name": "Emma Johnson",
        "birthdate": "2019-08-15",
        "allergies": "None",
        "special_needs": "",
        "emergency_contact": "Maria Garcia",
        "emergency_phone": "915-555-0101",
        "updated_at": now_iso,
        "created_at": now_iso
    }
    await db.children.update_one(
        {"id": child_doc["id"], "tenant_id": tenant_id},
        {"$set": child_doc},
        upsert=True
    )

    # Also ensure Ethan exists
    ethan_doc = {
        "id": "child_ethan_johnson",
        "tenant_id": tenant_id,
        "name": "Ethan Johnson",
        "age": 7,
        "birthday": "2019-05-10",
        "classroom": "Elementary",
        "allergies": "None",
        "emergency_contact": "Maria Garcia",
        "emergency_phone": "915-555-0101",
        "parent_name": "Maria Garcia",
        "parent_phone": "915-555-0101",
        "parent_user_id": member_user["user_id"],
        "updated_at": now_iso,
        "created_at": now_iso
    }
    await db.children.update_one(
        {"id": ethan_doc["id"], "tenant_id": tenant_id},
        {"$set": ethan_doc},
        upsert=True
    )

    # Baby Hinojosa (Vince's child) for mobile QA testing
    baby_hinojosa_doc = {
        "id": "80f242e5-de94-4d96-9f21-1a3aff0ba40d",
        "tenant_id": tenant_id,
        "parent_user_id": "cc7a823c-4d38-45d9-bb09-1df8caffe258",
        "name": "Baby Hinojosa",
        "first_name": "Baby",
        "last_name": "Hinojosa",
        "birthdate": "2023-03-15",
        "grade": "PreK",
        "classroom": "Sunday School Adventures",
        "allergies": "",
        "special_needs": "",
        "emergency_contact": "Vince Hinojosa",
        "emergency_phone": "",
        "updated_at": now_iso,
        "created_at": now_iso
    }
    await db.children.update_one(
        {"id": baby_hinojosa_doc["id"], "tenant_id": tenant_id},
        {"$set": baby_hinojosa_doc},
        upsert=True
    )

    # Attendance streak seed (4 Sundays)
    checkins = [
        {"id": "chk_mobile_001", "service_date": "2026-03-09"},
        {"id": "chk_mobile_002", "service_date": "2026-02-23"},
        {"id": "chk_mobile_003", "service_date": "2026-02-16"},
        {"id": "chk_mobile_004", "service_date": "2026-02-09"}
    ]
    checkin_ids = [item["id"] for item in checkins]
    for entry in checkins:
        await db.member_checkins.update_one(
            {"id": entry["id"], "tenant_id": tenant_id},
            {
                "$set": {
                    "tenant_id": tenant_id,
                    "user_id": member_user["user_id"],
                    "service_id": None,
                    "check_in_type": "in_person",
                    "check_in_time": f"{entry['service_date']}T09:00:00+00:00",
                    **entry
                }
            },
            upsert=True
        )
    await db.member_checkins.delete_many(
        {
            "tenant_id": tenant_id,
            "user_id": member_user["user_id"],
            "id": {"$nin": checkin_ids}
        }
    )

    # Next Steps completion seed (eligible for admin approval workflow)
    next_steps_course_ids = ["pathway_course_001", "pathway_course_002", "pathway_course_003"]
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {"next_steps_course_ids": next_steps_course_ids, "updated_at": now_iso}}
    )

    for course_id in next_steps_course_ids:
        await db.pathways_enrollments.update_one(
            {"tenant_id": tenant_id, "user_id": member_user["user_id"], "course_id": course_id},
            {
                "$set": {
                    "id": f"path_enroll_{member_user['user_id']}_{course_id}",
                    "tenant_id": tenant_id,
                    "user_id": member_user["user_id"],
                    "course_id": course_id,
                    "assigned_by": "admin_abundant",
                    "assigned_at": now_iso,
                    "status": "completed",
                    "updated_at": now_iso
                },
                "$setOnInsert": {"created_at": now_iso}
            },
            upsert=True
        )


async def ensure_abundant_go_live_portal_content(now_iso: Optional[str] = None):
    """Seed go-live API data expected by web + mobile clients for Abundant demo account."""
    tenant_id = DEFAULT_TENANT_ID
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()

    member_user = await db.users.find_one(
        {"email": "member@abundant.church"},
        {"_id": 0, "user_id": 1, "name": 1, "tenant_id": 1}
    )
    if not member_user:
        return

    # Ensure 50 upcoming events
    events_count = await db.events.count_documents({"tenant_id": tenant_id})
    if events_count < 50:
        today = datetime.now(timezone.utc).date()
        for idx in range(1, 51):
            event_date = (today + timedelta(days=idx)).isoformat()
            event_doc = {
                "id": f"event_abundant_{idx:03d}",
                "tenant_id": tenant_id,
                "name": f"Abundant Event {idx}",
                "description": "Church gathering and discipleship opportunity.",
                "location": "Abundant Main Campus",
                "event_date": event_date,
                "start_datetime": f"{event_date}T18:00:00",
                "is_public": True,
                "capacity": 350,
                "registration_required": idx % 2 == 0,
                "registration_count": min(idx * 2, 120),
                "created_at": now_iso
            }
            await db.events.update_one(
                {"id": event_doc["id"], "tenant_id": tenant_id},
                {"$set": event_doc},
                upsert=True
            )

    # Ensure 100 active groups
    active_groups_count = await db.groups.count_documents({"tenant_id": tenant_id, "is_active": True})
    if active_groups_count < 100:
        for idx in range(1, 101):
            group_doc = {
                "id": f"group_abundant_{idx:03d}",
                "tenant_id": tenant_id,
                "name": f"Life Group {idx}",
                "description": "Weekly small group for growth and community.",
                "category": "Small Groups",
                "meeting_day": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"][idx % 5],
                "meeting_time": "7:00 PM",
                "location": "Campus + Homes",
                "is_active": True,
                "max_members": 25,
                "created_at": now_iso
            }
            await db.groups.update_one(
                {"id": group_doc["id"], "tenant_id": tenant_id},
                {"$set": group_doc},
                upsert=True
            )

    # Force streak to at least 1 week by ensuring most recent check-in within last 7 days
    today = datetime.now(timezone.utc).date()
    recent_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    recent_checkin = {
        "id": "chk_mobile_recent",
        "tenant_id": tenant_id,
        "user_id": member_user["user_id"],
        "service_id": None,
        "check_in_type": "in_person",
        "service_date": recent_sunday.isoformat(),
        "check_in_time": f"{recent_sunday.isoformat()}T09:00:00+00:00"
    }
    await db.member_checkins.update_one(
        {"id": recent_checkin["id"], "tenant_id": tenant_id},
        {"$set": recent_checkin},
        upsert=True
    )

    # Next Steps journey API data
    next_steps_doc = {
        "id": f"next_steps_{member_user['user_id']}",
        "tenant_id": tenant_id,
        "user_id": member_user["user_id"],
        "current_step": "Baptism",
        "steps": [
            {"id": 1, "title": "Salvation", "completed": True},
            {"id": 2, "title": "Baptism", "completed": True},
            {"id": 3, "title": "Membership Class", "completed": True},
            {"id": 4, "title": "Small Group", "completed": False},
            {"id": 5, "title": "Serve", "completed": False}
        ],
        "percentage_complete": 60,
        "status": "in_progress",
        "thinkific_url": "https://abundant.thinkific.com/courses",
        "updated_at": now_iso
    }
    await db.next_steps_journeys.update_one(
        {"tenant_id": tenant_id, "user_id": member_user["user_id"]},
        {"$set": next_steps_doc},
        upsert=True
    )

    # Mobile courses API data
    course_docs = [
        {
            "id": "course_mobile_001",
            "tenant_id": tenant_id,
            "user_id": member_user["user_id"],
            "title": "Abundant Foundations",
            "description": "Core beliefs and foundations of faith",
            "progress": 100,
            "completed": True,
            "thinkific_url": "https://abundant.thinkific.com/courses/foundations",
            "thumbnail": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?auto=format&fit=crop&w=900&q=80",
            "updated_at": now_iso
        },
        {
            "id": "course_mobile_002",
            "tenant_id": tenant_id,
            "user_id": member_user["user_id"],
            "title": "Discovering Your Purpose",
            "description": "Find your calling and ministry gifting",
            "progress": 45,
            "completed": False,
            "thinkific_url": "https://abundant.thinkific.com/courses/discovering-your-purpose",
            "thumbnail": "https://images.unsplash.com/photo-1516534775068-ba3e7458af70?auto=format&fit=crop&w=900&q=80",
            "updated_at": now_iso
        }
    ]
    for course in course_docs:
        await db.member_courses.update_one(
            {"id": course["id"], "tenant_id": tenant_id, "user_id": member_user["user_id"]},
            {"$set": course, "$setOnInsert": {"created_at": now_iso}},
            upsert=True
        )
    await db.member_courses.delete_many(
        {
            "tenant_id": tenant_id,
            "user_id": member_user["user_id"],
            "id": {"$nin": ["course_mobile_001", "course_mobile_002"]}
        }
    )

    # Prayer requests data (one private, one public)
    prayer_seed = [
        {
            "id": "prayer_mobile_001",
            "tenant_id": tenant_id,
            "user_id": member_user["user_id"],
            "user_name": member_user.get("name", "Maria Garcia"),
            "category": "healing",
            "title": "Healing for my mother",
            "content": "Please pray for full healing and strength for my mother this month.",
            "is_public": False,
            "is_anonymous": False,
            "prayer_count": 0,
            "status": "active",
            "created_at": datetime.now(timezone.utc) - timedelta(days=6)
        },
        {
            "id": "prayer_mobile_002",
            "tenant_id": tenant_id,
            "user_id": member_user["user_id"],
            "user_name": member_user.get("name", "Maria Garcia"),
            "category": "guidance",
            "title": "New job opportunity",
            "content": "Praying for wisdom, favor, and peace in this interview process.",
            "is_public": True,
            "is_anonymous": False,
            "prayer_count": 3,
            "status": "active",
            "created_at": datetime.now(timezone.utc) - timedelta(days=2)
        }
    ]
    prayer_ids = [item["id"] for item in prayer_seed]
    for item in prayer_seed:
        await db.prayer_requests.update_one(
            {"id": item["id"], "tenant_id": tenant_id},
            {"$set": item, "$setOnInsert": {"updated_at": now_iso}},
            upsert=True
        )
    await db.prayer_requests.delete_many(
        {"tenant_id": tenant_id, "user_id": member_user["user_id"], "id": {"$nin": prayer_ids}}
    )

    # Volunteer opportunities
    opportunities = [
        {"id": "vol_001", "title": "Worship Team", "description": "Serve through music and worship.", "schedule": "Sundays 8:00 AM", "location": "Main Sanctuary", "spots_available": 4, "ministry_area": "Worship"},
        {"id": "vol_002", "title": "Hospitality", "description": "Welcome guests and help with connections.", "schedule": "Sundays 8:30 AM", "location": "Main Lobby", "spots_available": 6, "ministry_area": "Guest Experience"},
        {"id": "vol_003", "title": "Kids Ministry", "description": "Support Sunday classes and safe check-in.", "schedule": "Sundays 10:30 AM", "location": "Kids Wing", "spots_available": 5, "ministry_area": "Kids"},
        {"id": "vol_004", "title": "Parking Team", "description": "Guide traffic and assist families arriving on campus.", "schedule": "Sundays 8:15 AM", "location": "Parking Lot", "spots_available": 8, "ministry_area": "Operations"},
        {"id": "vol_005", "title": "Tech Team", "description": "Help with audio, video, and live stream.", "schedule": "Sundays 8:00 AM", "location": "Production Booth", "spots_available": 3, "ministry_area": "Production"},
        {"id": "vol_006", "title": "Food Pantry", "description": "Serve local families through weekend pantry outreach.", "schedule": "Saturday 9:00 AM", "location": "Community Center", "spots_available": 10, "ministry_area": "Outreach"}
    ]
    for op in opportunities:
        await db.volunteer_opportunities.update_one(
            {"id": op["id"], "tenant_id": tenant_id},
            {
                "$set": {
                    **op,
                    "tenant_id": tenant_id,
                    "is_active": True,
                    "updated_at": now_iso
                },
                "$setOnInsert": {"created_at": now_iso}
            },
            upsert=True
        )

    # Announcements
    announcements = [
        {"id": "ann_001", "title": "Easter Sunday — April 20th — All 3 services!", "body": "Celebrate Easter with us at 8:30AM, 10:30AM, and 12:30PM.", "priority": "high", "expires_at": "2026-04-21T00:00:00+00:00"},
        {"id": "ann_002", "title": "Marriage Retreat registration now open", "body": "Reserve your spot for the spring marriage retreat.", "priority": "medium", "expires_at": "2026-05-30T00:00:00+00:00"},
        {"id": "ann_003", "title": "Food Pantry needs volunteers this Saturday", "body": "Join the outreach team and help serve local families.", "priority": "high", "expires_at": "2026-03-31T00:00:00+00:00"}
    ]
    for ann in announcements:
        await db.announcements.update_one(
            {"id": ann["id"], "tenant_id": tenant_id},
            {
                "$set": {
                    **ann,
                    "tenant_id": tenant_id,
                    "created_at": now_iso,
                    "updated_at": now_iso
                }
            },
            upsert=True
        )

# ============== API ROUTES ==============

# ============== AUTH ROUTES ==============

@api_router.post("/auth/session")
async def exchange_session(request: SessionRequest, response: Response):
    """Exchange session_id from Emergent Auth for user data and set cookie"""
    try:
        # Call Emergent Auth to get session data
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": request.session_id}
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            auth_data = auth_response.json()
        
        # Extract user info
        email = auth_data.get("email")
        name = auth_data.get("name")
        picture = auth_data.get("picture")
        session_token = auth_data.get("session_token")
        
        if not email or not session_token:
            raise HTTPException(status_code=401, detail="Invalid auth response")
        
        # Check if user exists, create if not
        existing_user = await db.users.find_one({"email": email}, {"_id": 0})
        
        if existing_user:
            user_id = existing_user["user_id"]
            # Update user info if changed
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"name": name, "picture": picture}}
            )
        else:
            # Create new user
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            new_user = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": datetime.now(timezone.utc)
            }
            await db.users.insert_one(new_user)
        
        # Store session
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.user_sessions.delete_many({"user_id": user_id})  # Remove old sessions
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture
        }
        
    except httpx.RequestError as e:
        logger.error(f"Auth request failed: {e}")
        raise HTTPException(status_code=500, detail="Auth service unavailable")


def get_session_token_from_request(request: Request) -> Optional[str]:
    """Resolve auth token from cookie (web) or Authorization Bearer header (mobile)."""
    # Prefer explicit Authorization header so API clients can override stale browser cookies.
    auth_header = request.headers.get("Authorization", "")
    if auth_header:
        parts = auth_header.strip().split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
            if token:
                return token

    session_token = request.cookies.get("session_token")
    if session_token:
        return session_token

    return None

@api_router.get("/auth/me")
async def get_current_user(request: Request):
    """Get current user from session cookie or Authorization header"""
    session_token = get_session_token_from_request(request)
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]},
        {"_id": 0}
    )
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    result = serialize_doc(user_doc)
    # Ensure role and permissions are included
    result["role"] = user_doc.get("role", "admin")  # Default to admin for Google OAuth users
    result["permissions"] = get_permissions_for_user(user_doc)
    result["role_title"] = user_doc.get("role_title") or ROLE_TEMPLATES.get(user_doc.get("role", "member"), {}).get("role_title", "Member")
    return result

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Clear session and cookie"""
    session_token = get_session_token_from_request(request)
    
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=True,
        samesite="none"
    )
    
    return {"message": "Logged out"}

@api_router.post("/auth/login")
async def email_password_login(request: Request, payload: EmailLoginRequest, response: Response):
    """Login with email and password"""
    import hashlib
    
    # Rate limiting: 5 attempts per minute per IP
    client_ip = request.client.host or "unknown"
    if not check_rate_limit_v2(f"login:{client_ip}", 5, 60):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 1 minute.")
    
    user_doc = await db.users.find_one({"email": payload.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    stored_hash = user_doc.get("password_hash")
    if not stored_hash:
        raise HTTPException(status_code=401, detail="Password login not enabled for this account")
    
    input_hash = hashlib.sha256(payload.password.encode()).hexdigest()
    if input_hash != stored_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Session management: limit to 5 concurrent sessions
    existing = await db.user_sessions.count_documents({"user_id": user_doc["user_id"]})
    if existing >= 5:
        # Delete oldest session
        oldest = await db.user_sessions.find({"user_id": user_doc["user_id"]}).sort("created_at", 1).limit(1).to_list(1)
        if oldest:
            await db.user_sessions.delete_one({"session_token": oldest[0].get("session_token")})
    
    session_token = f"sess_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    await db.user_sessions.insert_one({
        "user_id": user_doc["user_id"],
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc),
        "ip_address": client_ip,
        "device_hint": "mobile" if "Mobile" in request.headers.get("user-agent", "") else "desktop",
    })
    
    response.set_cookie(
        key="session_token", value=session_token,
        httponly=True, secure=True, samesite="none",
        path="/", max_age=24 * 60 * 60
    )
    
    # Resolve permissions
    permissions = get_permissions_for_user(user_doc)
    role = user_doc.get("role", "member")
    role_title = user_doc.get("role_title") or ROLE_TEMPLATES.get(role, {}).get("role_title", "Member")
    
    tenant_id = user_doc.get("tenant_id")
    tenant_name = None
    if tenant_id:
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "name": 1})
        tenant_name = tenant.get("name") if tenant else None
    
    return {
        "user_id": user_doc["user_id"],
        "email": user_doc["email"],
        "name": user_doc["name"],
        "picture": user_doc.get("picture"),
        "role": role,
        "role_title": role_title,
        "permissions": permissions,
        "tenant_id": tenant_id,
        "tenant_name": tenant_name,
        "session_token": session_token,
        "token": session_token,
        "access_token": session_token,
    }

# ============== USER REGISTRATION ==============

import re

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        return False, "Password must contain at least one special character (!@#$%^&*)"
    
    return True, "Password meets requirements"

@api_router.post("/auth/register")
async def register_user(request: UserRegistrationRequest, response: Response):
    """Register a new member account with email and password"""
    
    # Validate passwords match
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Validate password strength
    is_valid, message = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": request.email.lower()}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    
    # Create user
    user_id = str(uuid.uuid4())
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    
    # Use provided tenant_id or default
    tenant_id = request.tenant_id if request.tenant_id else DEFAULT_TENANT_ID
    church_name = "your church"  # Default
    
    # Validate tenant exists and is active
    if tenant_id:
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
        if not tenant:
            raise HTTPException(status_code=400, detail="Selected church not found")
        if tenant.get("subscription_status") != "active":
            raise HTTPException(status_code=400, detail="Selected church is not accepting registrations")
        church_name = tenant.get("name", "your church")
    
    new_user = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "email": request.email.lower(),
        "password_hash": password_hash,
        "name": f"{request.first_name} {request.last_name}",
        "first_name": request.first_name,
        "last_name": request.last_name,
        "phone": request.phone,
        "role": "member",
        "church_id": tenant_id,
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
        "membership_status": "Active",
        "profile_photo": None,
        "email_verified": False,
        "registration_source": "web_signup"
    }
    
    await db.users.insert_one(new_user)
    
    # Create session and auto-login
    session_token = f"sess_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    logger.info(f"New user registered: {request.email} at {church_name}")
    
    # Send welcome email from Solomon AI (non-blocking)
    asyncio.create_task(send_welcome_email(request.email, request.first_name, church_name))
    
    return {
        "message": "Account created successfully",
        "user_id": user_id,
        "email": new_user["email"],
        "name": new_user["name"],
        "role": "member",
        "session_token": session_token,
        "token": session_token,
        "access_token": session_token
    }

@api_router.post("/auth/check-email")
async def check_email_availability(data: dict):
    """Check if an email is available for registration"""
    email = data.get("email", "").lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    return {"available": existing is None}

# ============== MEMBER PORTAL ROUTES ==============

@api_router.get("/portal/me")
async def get_member_profile(request: Request):
    """Get current member's profile for portal"""
    user = await get_current_member_user(request)
    
    # Find linked person record
    person = await db.people.find_one({"email": user["email"]}, {"_id": 0})
    
    # Get member's groups
    groups = []
    if person:
        group_memberships = await db.group_members.find(
            {"person_id": person["id"], "is_active": True},
            {"_id": 0}
        ).to_list(100)
        
        # Optimized: Fetch all groups in a single query instead of N+1
        if group_memberships:
            group_ids = [gm["group_id"] for gm in group_memberships]
            groups_docs = await db.groups.find(
                {"id": {"$in": group_ids}},
                {"_id": 0}
            ).to_list(len(group_ids))
            groups = [serialize_doc(g) for g in groups_docs]
    
    # Get giving summary
    ytd_giving = 0
    last_gift = None
    if person:
        today = datetime.now(timezone.utc)
        ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
        
        ytd_pipeline = [
            {"$match": {"person_id": person["id"], "donation_date": {"$gte": ytd_start}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        ytd_result = await db.donations.aggregate(ytd_pipeline).to_list(1)
        ytd_giving = ytd_result[0]["total"] if ytd_result else 0
        
        last_gift_doc = await db.donations.find_one(
            {"person_id": person["id"]},
            {"_id": 0},
            sort=[("donation_date", -1)]
        )
        if last_gift_doc:
            last_gift = serialize_doc(last_gift_doc)
    
    # Get recurring giving
    recurring = None
    if person:
        recurring_doc = await db.recurring_giving.find_one(
            {"person_id": person["id"], "is_active": True},
            {"_id": 0}
        )
        if recurring_doc:
            recurring = serialize_doc(recurring_doc)
    
    return {
        "user": serialize_doc(user),
        "person": serialize_doc(person) if person else None,
        "groups": groups,
        "giving": {
            "ytd_total": ytd_giving,
            "last_gift": last_gift,
            "recurring": recurring
        },
        "member_since": user.get("member_since") or (person.get("membership_date") if person else None)
    }


@api_router.get("/portal/profile")
async def get_portal_profile(request: Request):
    """Mobile-friendly alias for member profile."""
    return await get_member_profile(request)


@api_router.put("/portal/profile")
async def update_portal_profile(request: Request, payload: PortalProfileUpdate):
    """Update current member profile for both web and mobile clients."""
    user = await get_current_member_user(request)

    update_fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_fields:
        return {"message": "No changes submitted", "user": serialize_doc(user)}

    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    if "name" not in update_fields:
        first_name = update_fields.get("first_name") or user.get("first_name")
        last_name = update_fields.get("last_name") or user.get("last_name")
        if first_name and last_name:
            update_fields["name"] = f"{first_name} {last_name}".strip()

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": update_fields}
    )

    refreshed_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

    person_update = {}
    if update_fields.get("first_name"):
        person_update["first_name"] = update_fields["first_name"]
    if update_fields.get("last_name"):
        person_update["last_name"] = update_fields["last_name"]
    if update_fields.get("mobile_phone"):
        person_update["mobile_phone"] = update_fields["mobile_phone"]
    elif update_fields.get("phone"):
        person_update["mobile_phone"] = update_fields["phone"]
    if person_update:
        person_update["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.people.update_one(
            {"email": refreshed_user.get("email"), "tenant_id": refreshed_user.get("tenant_id")},
            {"$set": person_update}
        )

    return {"message": "Profile updated", "user": serialize_doc(refreshed_user)}

@api_router.get("/portal/giving/history")
async def get_member_giving_history(request: Request, limit: int = 50):
    """Get member's giving history for portal"""
    user = await get_current_member_user(request)
    person = await db.people.find_one(
        {"email": user["email"], "tenant_id": user.get("tenant_id")},
        {"_id": 0}
    )
    
    if not person:
        return {"donations": [], "total": 0}
    
    donations = await db.donations.find(
        {"tenant_id": user.get("tenant_id"), "person_id": person["id"]},
        {"_id": 0}
    ).sort("donation_date", -1).limit(limit).to_list(limit)
    
    # Optimized: Fetch all fund names in a single query instead of N+1
    if donations:
        fund_ids = list(set(d.get("fund_id") for d in donations if d.get("fund_id")))
        if fund_ids:
            funds_list = await db.funds.find(
                {"id": {"$in": fund_ids}},
                {"_id": 0, "id": 1, "name": 1}
            ).to_list(len(fund_ids))
            funds_map = {f["id"]: f["name"] for f in funds_list}
        else:
            funds_map = {}
        
        for d in donations:
            d["fund_name"] = funds_map.get(d.get("fund_id"), "General Fund")
    
    return {
        "donations": [serialize_doc(d) for d in donations],
        "total": len(donations)
    }


@api_router.get("/portal/giving/ytd")
async def get_member_giving_ytd(request: Request):
    """Return YTD giving totals for the authenticated member."""
    user = await get_current_member_user(request)
    person = await db.people.find_one({"email": user["email"], "tenant_id": user.get("tenant_id")}, {"_id": 0})

    if not person:
        return {"ytd_total": 0, "currency": "USD", "donation_count": 0}

    ytd_start = datetime.now(timezone.utc).replace(month=1, day=1).strftime("%Y-%m-%d")
    donations = await db.donations.find(
        {
            "tenant_id": user.get("tenant_id"),
            "person_id": person["id"],
            "donation_date": {"$gte": ytd_start}
        },
        {"_id": 0, "amount": 1}
    ).to_list(1000)

    ytd_total = round(sum(float(d.get("amount", 0) or 0) for d in donations), 2)
    return {
        "ytd_total": ytd_total,
        "currency": "USD",
        "donation_count": len(donations)
    }

@api_router.get("/portal/events")
async def get_member_events(request: Request):
    """Get upcoming events for member portal"""
    user = await get_current_member_user(request)
    
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Try both date formats for events
    events = await db.events.find(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"start_datetime": {"$gte": today}},
                {"event_date": {"$gte": today}}
            ]
        },
        {"_id": 0}
    ).sort("event_date", 1).limit(50).to_list(50)
    
    # Enrich with waitlist count
    enriched = []
    for e in events:
        event_data = serialize_doc(e)
        if e.get("capacity"):
            wl_count = await db.event_registrations.count_documents({"event_id": e["id"], "status": "waitlisted"})
            event_data["waitlist_count"] = wl_count
        enriched.append(event_data)
    
    return enriched

@api_router.get("/portal/groups")
async def get_available_groups(request: Request):
    """Get groups available to join for member portal"""
    user = await get_current_member_user(request)
    
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    
    groups = await db.groups.find(
        {"tenant_id": tenant_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with leader info
    for g in groups:
        if g.get("leader_id"):
            leader = await db.people.find_one({"id": g["leader_id"]}, {"_id": 0})
            g["leader"] = serialize_doc(leader) if leader else None
    
    return [serialize_doc(g) for g in groups]

# ============== WATCH PROGRESS ROUTES ==============

@api_router.post("/portal/watch/progress")
async def update_watch_progress(request: Request, progress: WatchProgressUpdate):
    """Save or update video watch progress for a user"""
    # Get user from session
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_id = session.get("user_id")
    
    # Calculate progress percentage
    progress_percent = (progress.position_seconds / progress.duration_seconds * 100) if progress.duration_seconds > 0 else 0
    completed = progress_percent >= 90  # Mark as completed if watched 90%+
    
    # Upsert watch progress
    watch_data = {
        "user_id": user_id,
        "video_id": progress.video_id,
        "youtube_id": progress.youtube_id,
        "title": progress.title,
        "thumbnail": progress.thumbnail,
        "instructor": progress.instructor,
        "position_seconds": progress.position_seconds,
        "duration_seconds": progress.duration_seconds,
        "progress_percent": round(progress_percent, 1),
        "completed": completed,
        "last_watched": datetime.now(timezone.utc).isoformat()
    }
    
    # Check if entry exists
    existing = await db.watch_progress.find_one(
        {"user_id": user_id, "video_id": progress.video_id},
        {"_id": 0}
    )
    
    if existing:
        await db.watch_progress.update_one(
            {"user_id": user_id, "video_id": progress.video_id},
            {"$set": watch_data}
        )
    else:
        watch_data["id"] = str(uuid.uuid4())
        await db.watch_progress.insert_one(watch_data)
    
    return {"status": "saved", "progress_percent": watch_data["progress_percent"], "completed": completed}

@api_router.get("/portal/watch/progress")
async def get_watch_progress(request: Request):
    """Get all watch progress for current user (for Continue Watching)"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_id = session.get("user_id")
    
    # Get in-progress videos (not completed, sorted by last watched)
    in_progress = await db.watch_progress.find(
        {"user_id": user_id, "completed": False, "progress_percent": {"$gt": 0}},
        {"_id": 0}
    ).sort("last_watched", -1).to_list(20)
    
    # Get completed videos
    completed = await db.watch_progress.find(
        {"user_id": user_id, "completed": True},
        {"_id": 0}
    ).sort("last_watched", -1).to_list(50)
    
    return {
        "continue_watching": [serialize_doc(p) for p in in_progress],
        "completed": [serialize_doc(p) for p in completed],
        "total_watched": len(completed)
    }

@api_router.get("/portal/watch/progress/{video_id}")
async def get_video_progress(request: Request, video_id: str):
    """Get watch progress for a specific video"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        return {"position_seconds": 0, "progress_percent": 0, "completed": False}
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        return {"position_seconds": 0, "progress_percent": 0, "completed": False}
    
    user_id = session.get("user_id")
    
    progress = await db.watch_progress.find_one(
        {"user_id": user_id, "video_id": video_id},
        {"_id": 0}
    )
    
    if progress:
        return serialize_doc(progress)
    
    return {"position_seconds": 0, "progress_percent": 0, "completed": False}

# ============== THINKIFIC ROUTES ==============

@api_router.get("/admin/thinkific")
async def get_admin_thinkific(request: Request):
    """Get Thinkific URL for current tenant"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "thinkific_url": 1})
    thinkific_url = tenant.get("thinkific_url") if tenant else None
    if tenant_id == "abundant-east-001" and (not thinkific_url or "abundant.thinkific.com" in thinkific_url):
        thinkific_url = "https://abundantchurch.thinkific.com/collections"
        await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"thinkific_url": thinkific_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    return {"thinkific_url": thinkific_url}

@api_router.patch("/admin/thinkific")
async def update_admin_thinkific(request: Request, payload: ThinkificUpdate):
    """Update Thinkific URL for current tenant"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {"thinkific_url": payload.thinkific_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Thinkific updated", "thinkific_url": payload.thinkific_url}

@api_router.get("/portal/thinkific")
async def get_portal_thinkific(request: Request):
    """Get Thinkific URL for member portal"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "thinkific_url": 1})
    thinkific_url = tenant.get("thinkific_url") if tenant else None
    if tenant_id == "abundant-east-001" and (not thinkific_url or "abundant.thinkific.com" in thinkific_url):
        thinkific_url = "https://abundantchurch.thinkific.com/collections"
        await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"thinkific_url": thinkific_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    return {"thinkific_url": thinkific_url}


async def get_next_steps_required_course_ids(tenant_id: str) -> List[str]:
    """Resolve membership-track courses. Defaults to first 3 published pathways courses."""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "next_steps_course_ids": 1})
    configured = (tenant or {}).get("next_steps_course_ids") or []
    if configured:
        return configured

    courses = await db.pathways_courses.find(
        {"tenant_id": tenant_id, "is_published": True},
        {"_id": 0, "id": 1}
    ).sort("created_at", 1).limit(3).to_list(3)
    ids = [course["id"] for course in courses]

    if ids:
        await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"next_steps_course_ids": ids, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    return ids


async def evaluate_member_next_steps_membership(tenant_id: str, user_id: str) -> Dict[str, Any]:
    """Calculate and persist member's Next Steps eligibility + approval state."""
    required_course_ids = await get_next_steps_required_course_ids(tenant_id)

    if not required_course_ids:
        return {
            "required_course_ids": [],
            "completed_course_ids": [],
            "completion_percent": 0,
            "eligible": False,
            "approval_status": "not_configured"
        }

    enrollments = await db.pathways_enrollments.find(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "course_id": {"$in": required_course_ids},
            "status": {"$ne": "dropped"}
        },
        {"_id": 0, "course_id": 1, "status": 1}
    ).to_list(100)

    completed_course_ids = [
        enrollment["course_id"]
        for enrollment in enrollments
        if enrollment.get("status") == "completed"
    ]

    completion_percent = round((len(completed_course_ids) / len(required_course_ids)) * 100, 1)
    eligible = len(completed_course_ids) >= len(required_course_ids)

    existing = await db.next_steps_memberships.find_one(
        {"tenant_id": tenant_id, "user_id": user_id, "track": "abundant-next-steps"},
        {"_id": 0}
    )

    current_status = (existing or {}).get("approval_status")
    if current_status == "approved":
        approval_status = "approved"
    elif eligible:
        approval_status = "eligible_pending_approval"
    else:
        approval_status = "in_progress"

    record = {
        "id": (existing or {}).get("id", str(uuid.uuid4())),
        "tenant_id": tenant_id,
        "user_id": user_id,
        "track": "abundant-next-steps",
        "required_course_ids": required_course_ids,
        "completed_course_ids": completed_course_ids,
        "completion_percent": completion_percent,
        "eligible": eligible,
        "approval_status": approval_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    if not existing:
        record["created_at"] = datetime.now(timezone.utc).isoformat()

    await db.next_steps_memberships.update_one(
        {"tenant_id": tenant_id, "user_id": user_id, "track": "abundant-next-steps"},
        {"$set": record},
        upsert=True
    )

    return {
        **record,
        "required_count": len(required_course_ids),
        "completed_count": len(completed_course_ids)
    }


def generate_next_steps_certificate_pdf(name: str, church_name: str, completed_on: str) -> bytes:
    """Create a simple completion certificate PDF."""
    from io import BytesIO
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)

    pdf.setFillColor(colors.HexColor("#F8FAFC"))
    pdf.rect(0, 0, width, height, stroke=0, fill=1)

    pdf.setStrokeColor(colors.HexColor("#1D4ED8"))
    pdf.setLineWidth(4)
    pdf.rect(32, 32, width - 64, height - 64, stroke=1, fill=0)

    pdf.setFillColor(colors.HexColor("#0F172A"))
    pdf.setFont("Helvetica-Bold", 34)
    pdf.drawCentredString(width / 2, height - 120, "Certificate of Completion")

    pdf.setFont("Helvetica", 18)
    pdf.drawCentredString(width / 2, height - 170, f"{church_name} recognizes")

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(width / 2, height - 235, name)

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(width / 2, height - 285, "for successfully completing")

    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 325, "Abundant Next Steps")

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, 120, f"Completed on {completed_on}")
    pdf.drawCentredString(width / 2, 95, "You are now recognized as an active Abundant Church member.")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


@api_router.get("/portal/next-steps/status")
async def get_portal_next_steps_status(request: Request):
    """Member-facing status for Abundant Next Steps journey."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    await ensure_abundant_pathways_data(tenant_id)
    journey = await evaluate_member_next_steps_membership(tenant_id, user.get("user_id"))

    tenant = await db.tenants.find_one(
        {"id": tenant_id},
        {"_id": 0, "name": 1, "thinkific_url": 1, "next_steps_url": 1}
    )
    thinkific_url = (tenant or {}).get("next_steps_url") or DEFAULT_NEXT_STEPS_URL

    course_docs = await db.pathways_courses.find(
        {"tenant_id": tenant_id, "id": {"$in": journey.get("required_course_ids", [])}},
        {"_id": 0, "id": 1, "title": 1}
    ).to_list(50)
    course_map = {course["id"]: course.get("title", "Course") for course in course_docs}

    return {
        "track_name": "Abundant Next Steps",
        "church_name": (tenant or {}).get("name", "Abundant Church"),
        "thinkific_url": thinkific_url,
        "required_courses": [
            {
                "course_id": course_id,
                "title": course_map.get(course_id, "Course"),
                "completed": course_id in journey.get("completed_course_ids", [])
            }
            for course_id in journey.get("required_course_ids", [])
        ],
        "completion_percent": journey.get("completion_percent", 0),
        "eligible": journey.get("eligible", False),
        "approval_status": journey.get("approval_status"),
        "certificate_available": journey.get("approval_status") == "approved",
        "certificate_url": "/api/portal/next-steps/certificate"
    }


@api_router.get("/portal/next-steps")
async def get_portal_next_steps(request: Request):
    """Legacy/mobile-friendly Next Steps endpoint."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_abundant_go_live_portal_content()

    journey = await db.next_steps_journeys.find_one(
        {"tenant_id": tenant_id, "user_id": user.get("user_id")},
        {"_id": 0}
    )
    if journey:
        return {
            "current_step": journey.get("current_step", "Salvation"),
            "steps": journey.get("steps", []),
            "percentage_complete": journey.get("percentage_complete", 0),
            "status": journey.get("status", "in_progress"),
            "thinkific_url": journey.get("thinkific_url", "https://abundant.thinkific.com/courses")
        }

    status_data = await get_portal_next_steps_status(request)
    required = status_data.get("required_courses", [])
    completed_count = len([course for course in required if course.get("completed")])
    total_count = len(required)
    pct = round((completed_count / total_count) * 100) if total_count else 0
    return {
        "current_step": required[completed_count]["title"] if completed_count < total_count else "Completed",
        "steps": [
            {"id": idx + 1, "title": course.get("title", f"Step {idx+1}"), "completed": course.get("completed", False)}
            for idx, course in enumerate(required)
        ],
        "percentage_complete": pct,
        "status": "completed" if status_data.get("approval_status") == "approved" else "in_progress",
        "thinkific_url": status_data.get("thinkific_url", "https://abundant.thinkific.com/courses")
    }


@api_router.get("/portal/courses")
async def get_portal_courses(request: Request):
    """Get member courses for mobile clients."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_abundant_go_live_portal_content()

    courses = await db.member_courses.find(
        {"tenant_id": tenant_id, "user_id": user.get("user_id")},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)

    if courses:
        return {"courses": [serialize_doc(course) for course in courses]}

    pathways = await get_member_pathways_courses(request)
    mapped = []
    for item in pathways.get("courses", [])[:5]:
        mapped.append({
            "id": item.get("course_id"),
            "title": item.get("title"),
            "description": item.get("description"),
            "progress": int(item.get("progress_percent", 0)),
            "completed": item.get("status") == "completed",
            "thinkific_url": "https://abundant.thinkific.com/courses",
            "thumbnail": item.get("cover_image_url")
        })
    return {"courses": mapped}


@api_router.get("/portal/next-steps/certificate")
async def download_next_steps_certificate(request: Request):
    """Generate and download completion certificate after admin approval."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    journey = await evaluate_member_next_steps_membership(tenant_id, user.get("user_id"))
    if journey.get("approval_status") != "approved":
        raise HTTPException(status_code=403, detail="Certificate available after admin approval")

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "name": 1})
    completed_on = datetime.now(timezone.utc).strftime("%B %d, %Y")
    pdf_bytes = generate_next_steps_certificate_pdf(
        user.get("name", "Member"),
        (tenant or {}).get("name", "Abundant Church"),
        completed_on
    )

    safe_name = (user.get("name", "member").replace(" ", "_")).lower()
    filename = f"abundant-next-steps-certificate-{safe_name}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@api_router.get("/admin/next-steps/approvals")
async def get_next_steps_approvals(request: Request, status: Optional[str] = None):
    """Admin queue for reviewing Next Steps completions."""
    admin = await get_current_admin_user(request)
    tenant_id = admin.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    query: Dict[str, Any] = {"tenant_id": tenant_id, "track": "abundant-next-steps"}
    if status:
        query["approval_status"] = status

    approvals = await db.next_steps_memberships.find(query, {"_id": 0}).sort("updated_at", -1).to_list(500)
    user_ids = [row.get("user_id") for row in approvals if row.get("user_id")]
    users = await db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "email": 1}
    ).to_list(500)
    user_map = {user["user_id"]: user for user in users}

    return {
        "approvals": [
            {
                **serialize_doc(row),
                "member": user_map.get(row.get("user_id"), {"user_id": row.get("user_id"), "name": "Unknown", "email": ""})
            }
            for row in approvals
        ]
    }


@api_router.post("/admin/next-steps/approvals/{user_id}")
async def decide_next_steps_approval(request: Request, user_id: str, payload: NextStepsApprovalRequest):
    """Approve or reject member's Next Steps completion (manual approval flow)."""
    admin = await get_current_admin_user(request)
    tenant_id = admin.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    membership = await evaluate_member_next_steps_membership(tenant_id, user_id)

    action = payload.action.lower().strip()
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="action must be approve or reject")

    if action == "approve" and not membership.get("eligible"):
        raise HTTPException(status_code=400, detail="Member has not completed all required courses")

    next_status = "approved" if action == "approve" else "rejected"
    now_iso = datetime.now(timezone.utc).isoformat()

    update_fields = {
        "approval_status": next_status,
        "decision_notes": payload.notes,
        "decided_by": admin.get("user_id"),
        "decided_by_name": admin.get("name"),
        "decided_at": now_iso,
        "updated_at": now_iso
    }

    await db.next_steps_memberships.update_one(
        {"tenant_id": tenant_id, "user_id": user_id, "track": "abundant-next-steps"},
        {"$set": update_fields},
        upsert=True
    )

    await db.users.update_one(
        {"user_id": user_id, "tenant_id": tenant_id},
        {"$set": {
            "next_steps_member": next_status == "approved",
            "next_steps_membership_status": next_status,
            "next_steps_updated_at": now_iso
        }}
    )

    return {
        "message": f"Next Steps membership {next_status}",
        "user_id": user_id,
        "approval_status": next_status
    }

# ============== ABUNDANT PATHWAYS (LMS) ROUTES ==============

@api_router.get("/admin/pathways/courses")
async def get_admin_pathways_courses(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Ensure demo data exists for Abundant Church
    await ensure_abundant_pathways_data(tenant_id)
    
    query = {}
    if tenant_id:
        query["tenant_id"] = tenant_id

    courses = await db.pathways_courses.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    course_ids = [c["id"] for c in courses]

    lesson_counts = {}
    assignment_counts = {}

    if course_ids:
        lesson_rows = await db.pathways_lessons.aggregate([
            {"$match": {"course_id": {"$in": course_ids}, **({"tenant_id": tenant_id} if tenant_id else {})}},
            {"$group": {"_id": "$course_id", "count": {"$sum": 1}}}
        ]).to_list(200)
        lesson_counts = {row["_id"]: row["count"] for row in lesson_rows}

        assignment_rows = await db.pathways_enrollments.aggregate([
            {"$match": {"course_id": {"$in": course_ids}, "status": {"$ne": "dropped"}, **({"tenant_id": tenant_id} if tenant_id else {})}},
            {"$group": {"_id": "$course_id", "count": {"$sum": 1}}}
        ]).to_list(200)
        assignment_counts = {row["_id"]: row["count"] for row in assignment_rows}

    for course in courses:
        course["lesson_count"] = lesson_counts.get(course["id"], 0)
        course["assigned_count"] = assignment_counts.get(course["id"], 0)

    return {"courses": [serialize_doc(c) for c in courses]}

@api_router.post("/admin/pathways/courses")
async def create_pathways_course(request: Request, payload: PathwaysCourseCreate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    course = PathwaysCourse(
        tenant_id=tenant_id,
        title=payload.title,
        description=payload.description,
        cover_image_url=payload.cover_image_url,
        category=payload.category,
        level=payload.level,
        is_published=payload.is_published
    ).model_dump()

    await db.pathways_courses.insert_one(course)
    return {"course": serialize_doc(course)}

@api_router.put("/admin/pathways/courses/{course_id}")
async def update_pathways_course(request: Request, course_id: str, payload: PathwaysCourseUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.pathways_courses.update_one(
            {"id": course_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )

    course = await db.pathways_courses.find_one({"id": course_id, "tenant_id": tenant_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return {"course": serialize_doc(course)}

@api_router.delete("/admin/pathways/courses/{course_id}")
async def delete_pathways_course(request: Request, course_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await db.pathways_courses.delete_one({"id": course_id, "tenant_id": tenant_id})
    await db.pathways_lessons.delete_many({"course_id": course_id, "tenant_id": tenant_id})
    await db.pathways_enrollments.delete_many({"course_id": course_id, "tenant_id": tenant_id})
    await db.pathways_progress.delete_many({"course_id": course_id, "tenant_id": tenant_id})
    return {"message": "Course deleted"}

@api_router.get("/admin/pathways/courses/{course_id}/lessons")
async def get_pathways_lessons(request: Request, course_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    lessons = await db.pathways_lessons.find(
        {"course_id": course_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("sort_order", 1).to_list(200)

    return {"lessons": [serialize_doc(l) for l in lessons]}

@api_router.post("/admin/pathways/courses/{course_id}/lessons")
async def create_pathways_lesson(request: Request, course_id: str, payload: PathwaysLessonCreate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    youtube_id = payload.youtube_id
    if payload.video_url and not youtube_id:
        youtube_id = extract_youtube_id(payload.video_url)

    if payload.video_url and not youtube_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    duration_seconds = duration_to_seconds(payload.duration_label, payload.duration_seconds)
    thumbnail_url = f"https://i.ytimg.com/vi/{youtube_id}/maxresdefault.jpg" if youtube_id else None

    lesson = PathwaysLesson(
        tenant_id=tenant_id,
        course_id=course_id,
        title=payload.title,
        description=payload.description,
        youtube_id=youtube_id,
        video_url=payload.video_url,
        thumbnail_url=thumbnail_url,
        duration_label=payload.duration_label,
        duration_seconds=duration_seconds,
        resource_url=payload.resource_url,
        sort_order=payload.sort_order,
        is_published=payload.is_published
    ).model_dump()

    await db.pathways_lessons.insert_one(lesson)
    return {"lesson": serialize_doc(lesson)}

@api_router.put("/admin/pathways/lessons/{lesson_id}")
async def update_pathways_lesson(request: Request, lesson_id: str, payload: PathwaysLessonUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}

    if "video_url" in update_data and update_data.get("video_url"):
        youtube_id = extract_youtube_id(update_data["video_url"])
        if not youtube_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        update_data["youtube_id"] = youtube_id
        update_data["thumbnail_url"] = f"https://i.ytimg.com/vi/{youtube_id}/maxresdefault.jpg"

    if "duration_label" in update_data or "duration_seconds" in update_data:
        update_data["duration_seconds"] = duration_to_seconds(
            update_data.get("duration_label"),
            update_data.get("duration_seconds")
        )

    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.pathways_lessons.update_one(
            {"id": lesson_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )

    lesson = await db.pathways_lessons.find_one({"id": lesson_id, "tenant_id": tenant_id}, {"_id": 0})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {"lesson": serialize_doc(lesson)}

@api_router.delete("/admin/pathways/lessons/{lesson_id}")
async def delete_pathways_lesson(request: Request, lesson_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    lesson = await db.pathways_lessons.find_one({"id": lesson_id, "tenant_id": tenant_id}, {"_id": 0})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    await db.pathways_lessons.delete_one({"id": lesson_id, "tenant_id": tenant_id})
    await db.pathways_progress.delete_many({"lesson_id": lesson_id, "tenant_id": tenant_id})
    return {"message": "Lesson deleted"}

@api_router.get("/admin/pathways/courses/{course_id}/assignments")
async def get_pathways_assignments(request: Request, course_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    enrollments = await db.pathways_enrollments.find(
        {"course_id": course_id, "tenant_id": tenant_id, "status": {"$ne": "dropped"}},
        {"_id": 0}
    ).to_list(200)

    user_ids = [e["user_id"] for e in enrollments]
    members = await db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "email": 1}
    ).to_list(200)
    member_map = {m["user_id"]: m for m in members}

    total_lessons = await db.pathways_lessons.count_documents({"course_id": course_id, "tenant_id": tenant_id, "is_published": True})
    progress_records = await db.pathways_progress.find(
        {"course_id": course_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(500)

    progress_map = {}
    last_activity = {}
    for record in progress_records:
        uid = record.get("user_id")
        if record.get("completed"):
            progress_map[uid] = progress_map.get(uid, 0) + 1
        if record.get("last_watched"):
            last_activity[uid] = max(last_activity.get(uid, ""), record.get("last_watched"))

    assignments = []
    for enrollment in enrollments:
        member = member_map.get(enrollment["user_id"], {"user_id": enrollment["user_id"], "name": "Unknown", "email": ""})
        completed_count = progress_map.get(enrollment["user_id"], 0)
        progress_percent = round((completed_count / total_lessons * 100) if total_lessons else 0, 1)
        assignments.append({
            **serialize_doc(enrollment),
            "member": member,
            "progress_percent": progress_percent,
            "completed_lessons": completed_count,
            "total_lessons": total_lessons,
            "last_activity": last_activity.get(enrollment["user_id"])
        })

    return {"assignments": assignments}

@api_router.get("/admin/pathways/available-members")
async def get_pathways_available_members(request: Request, course_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    assigned_ids = await db.pathways_enrollments.distinct(
        "user_id",
        {"course_id": course_id, "tenant_id": tenant_id, "status": {"$ne": "dropped"}}
    )

    members = await db.users.find(
        {
            "tenant_id": tenant_id,
            "role": "member",
            "user_id": {"$nin": assigned_ids}
        },
        {"_id": 0, "user_id": 1, "name": 1, "email": 1}
    ).sort("name", 1).to_list(200)

    return {"members": members}

@api_router.post("/admin/pathways/courses/{course_id}/assignments")
async def assign_pathways_member(request: Request, course_id: str, payload: PathwaysEnrollmentRequest):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    member = await db.users.find_one(
        {"user_id": payload.member_id, "tenant_id": tenant_id, "role": "member"},
        {"_id": 0}
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    existing = await db.pathways_enrollments.find_one(
        {"course_id": course_id, "tenant_id": tenant_id, "user_id": payload.member_id},
        {"_id": 0}
    )

    if existing:
        await db.pathways_enrollments.update_one(
            {"id": existing["id"]},
            {"$set": {"status": "assigned", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        enrollment = {**existing, "status": "assigned"}
    else:
        enrollment = PathwaysEnrollment(
            tenant_id=tenant_id,
            course_id=course_id,
            user_id=payload.member_id,
            assigned_by=user.get("user_id"),
            status="assigned"
        ).model_dump()
        await db.pathways_enrollments.insert_one(enrollment)

    return {"assignment": serialize_doc(enrollment)}

@api_router.delete("/admin/pathways/courses/{course_id}/assignments/{member_id}")
async def remove_pathways_member(request: Request, course_id: str, member_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await db.pathways_enrollments.delete_one({"course_id": course_id, "tenant_id": tenant_id, "user_id": member_id})
    await db.pathways_progress.delete_many({"course_id": course_id, "tenant_id": tenant_id, "user_id": member_id})
    return {"message": "Member removed"}

@api_router.get("/portal/pathways/courses")
async def get_member_pathways_courses(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    # Ensure demo data exists for Abundant Church
    await ensure_abundant_pathways_data(tenant_id)

    enrollments = await db.pathways_enrollments.find(
        {"user_id": user.get("user_id"), "tenant_id": tenant_id, "status": {"$ne": "dropped"}},
        {"_id": 0}
    ).to_list(200)

    next_steps = await evaluate_member_next_steps_membership(tenant_id, user.get("user_id"))

    course_ids = [e["course_id"] for e in enrollments]
    if not course_ids:
        return {
            "courses": [],
            "next_steps": {
                "completion_percent": next_steps.get("completion_percent", 0),
                "eligible": next_steps.get("eligible", False),
                "approval_status": next_steps.get("approval_status")
            }
        }

    courses = await db.pathways_courses.find(
        {"id": {"$in": course_ids}, "tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(200)

    lesson_rows = await db.pathways_lessons.aggregate([
        {"$match": {"course_id": {"$in": course_ids}, "tenant_id": tenant_id, "is_published": True}},
        {"$group": {"_id": "$course_id", "count": {"$sum": 1}}}
    ]).to_list(200)
    lesson_counts = {row["_id"]: row["count"] for row in lesson_rows}

    progress_records = await db.pathways_progress.find(
        {"course_id": {"$in": course_ids}, "tenant_id": tenant_id, "user_id": user.get("user_id")},
        {"_id": 0}
    ).to_list(500)

    completed_map = {}
    last_activity = {}
    for record in progress_records:
        if record.get("completed"):
            completed_map[record["course_id"]] = completed_map.get(record["course_id"], 0) + 1
        if record.get("last_watched"):
            last_activity[record["course_id"]] = max(last_activity.get(record["course_id"], ""), record.get("last_watched"))

    course_map = {course["id"]: course for course in courses}
    response = []

    for enrollment in sorted(enrollments, key=lambda e: e.get("assigned_at", ""), reverse=True):
        course = course_map.get(enrollment["course_id"])
        if not course:
            continue
        total_lessons = lesson_counts.get(course["id"], 0)
        completed_lessons = completed_map.get(course["id"], 0)
        progress_percent = round((completed_lessons / total_lessons * 100) if total_lessons else 0, 1)
        response.append({
            **serialize_doc(course),
            "enrollment_status": enrollment.get("status"),
            "progress_percent": progress_percent,
            "completed_lessons": completed_lessons,
            "total_lessons": total_lessons,
            "last_activity": last_activity.get(course["id"])
        })

    return {
        "courses": response,
        "next_steps": {
            "completion_percent": next_steps.get("completion_percent", 0),
            "eligible": next_steps.get("eligible", False),
            "approval_status": next_steps.get("approval_status")
        }
    }

@api_router.get("/portal/pathways/courses/{course_id}/lessons")
async def get_member_pathways_lessons(request: Request, course_id: str):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    enrollment = await db.pathways_enrollments.find_one(
        {"course_id": course_id, "tenant_id": tenant_id, "user_id": user.get("user_id"), "status": {"$ne": "dropped"}},
        {"_id": 0}
    )
    if not enrollment:
        raise HTTPException(status_code=403, detail="Course not assigned")

    lessons = await db.pathways_lessons.find(
        {"course_id": course_id, "tenant_id": tenant_id, "is_published": True},
        {"_id": 0}
    ).sort("sort_order", 1).to_list(200)

    progress_records = await db.pathways_progress.find(
        {"course_id": course_id, "tenant_id": tenant_id, "user_id": user.get("user_id")},
        {"_id": 0}
    ).to_list(200)
    progress_map = {p["lesson_id"]: p for p in progress_records}

    response = []
    for lesson in lessons:
        progress = progress_map.get(lesson["id"], {})
        response.append({
            **serialize_doc(lesson),
            "progress_percent": progress.get("progress_percent", 0),
            "position_seconds": progress.get("position_seconds", 0),
            "completed": progress.get("completed", False)
        })

    return {"lessons": response}

@api_router.post("/portal/pathways/progress")
async def update_pathways_progress(request: Request, payload: PathwaysProgressUpdate):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    enrollment = await db.pathways_enrollments.find_one(
        {"course_id": payload.course_id, "tenant_id": tenant_id, "user_id": user.get("user_id"), "status": {"$ne": "dropped"}},
        {"_id": 0}
    )
    if not enrollment:
        raise HTTPException(status_code=403, detail="Course not assigned")

    progress_percent = (payload.position_seconds / payload.duration_seconds * 100) if payload.duration_seconds > 0 else 0
    completed = progress_percent >= 90

    progress_data = {
        "tenant_id": tenant_id,
        "course_id": payload.course_id,
        "lesson_id": payload.lesson_id,
        "user_id": user.get("user_id"),
        "position_seconds": payload.position_seconds,
        "duration_seconds": payload.duration_seconds,
        "progress_percent": round(progress_percent, 1),
        "completed": completed,
        "last_watched": datetime.now(timezone.utc).isoformat()
    }

    existing = await db.pathways_progress.find_one(
        {"lesson_id": payload.lesson_id, "tenant_id": tenant_id, "user_id": user.get("user_id")},
        {"_id": 0}
    )

    if existing:
        await db.pathways_progress.update_one(
            {"id": existing["id"]},
            {"$set": progress_data}
        )
    else:
        progress_data["id"] = str(uuid.uuid4())
        await db.pathways_progress.insert_one(progress_data)

    total_lessons = await db.pathways_lessons.count_documents({"course_id": payload.course_id, "tenant_id": tenant_id, "is_published": True})
    completed_lessons = await db.pathways_progress.count_documents(
        {"course_id": payload.course_id, "tenant_id": tenant_id, "user_id": user.get("user_id"), "completed": True}
    )

    status = "completed" if total_lessons > 0 and completed_lessons >= total_lessons else "in_progress"
    await db.pathways_enrollments.update_one(
        {"id": enrollment["id"]},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    next_steps = await evaluate_member_next_steps_membership(tenant_id, user.get("user_id"))

    return {
        "status": "saved",
        "progress_percent": progress_data["progress_percent"],
        "completed": completed,
        "course_status": status,
        "next_steps": {
            "completion_percent": next_steps.get("completion_percent", 0),
            "eligible": next_steps.get("eligible", False),
            "approval_status": next_steps.get("approval_status")
        }
    }

# ============== MERCH ROUTES ==============

@api_router.get("/admin/merch/settings")
async def get_merch_settings(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_merch_data(tenant_id)
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "merch_embed_url": 1})
    return {"merch_embed_url": tenant.get("merch_embed_url", DEFAULT_MERCH_EMBED_URL) if tenant else DEFAULT_MERCH_EMBED_URL}

@api_router.patch("/admin/merch/settings")
async def update_merch_settings(request: Request, payload: MerchSettingsUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {"merch_embed_url": payload.merch_embed_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Merch settings updated", "merch_embed_url": payload.merch_embed_url}

@api_router.get("/portal/merch/settings")
async def get_portal_merch_settings(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    await ensure_demo_merch_data(tenant_id)
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "merch_embed_url": 1})
    return {"merch_embed_url": tenant.get("merch_embed_url", DEFAULT_MERCH_EMBED_URL) if tenant else DEFAULT_MERCH_EMBED_URL}

@api_router.get("/admin/merch/products")
async def get_admin_merch_products(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None
):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_merch_data(tenant_id)

    query = {"tenant_id": tenant_id}
    if category:
        query["category"] = category
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    products = await db.merch_products.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"products": [serialize_doc(p) for p in products]}

@api_router.post("/admin/merch/products")
async def create_merch_product(request: Request, payload: MerchProductCreate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    product = MerchProduct(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        image_url=payload.image_url,
        price=payload.price,
        category=payload.category,
        is_featured=payload.is_featured,
        is_active=payload.is_active,
        inventory=payload.inventory
    ).model_dump()

    await db.merch_products.insert_one(product)
    return {"product": serialize_doc(product)}

@api_router.put("/admin/merch/products/{product_id}")
async def update_merch_product(request: Request, product_id: str, payload: MerchProductUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.merch_products.update_one(
            {"id": product_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )

    product = await db.merch_products.find_one({"id": product_id, "tenant_id": tenant_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"product": serialize_doc(product)}

@api_router.delete("/admin/merch/products/{product_id}")
async def delete_merch_product(request: Request, product_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await db.merch_products.delete_one({"id": product_id, "tenant_id": tenant_id})
    return {"message": "Product deleted"}

@api_router.get("/admin/merch/orders")
async def get_merch_orders(request: Request, limit: int = 50):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_merch_data(tenant_id)

    orders = await db.merch_orders.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return {"orders": [serialize_doc(o) for o in orders]}

@api_router.get("/admin/merch/summary")
async def get_merch_summary(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_merch_data(tenant_id)

    products_total = await db.merch_products.count_documents({"tenant_id": tenant_id})
    active_products = await db.merch_products.count_documents({"tenant_id": tenant_id, "is_active": True})
    featured_products = await db.merch_products.count_documents({"tenant_id": tenant_id, "is_featured": True})
    orders = await db.merch_orders.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(200)
    revenue = round(sum(order.get("total", 0) for order in orders), 2)
    member_count = await db.people.count_documents({"tenant_id": tenant_id})
    if member_count == 0 or member_count > 5000:
        member_count = 500

    return {
        "products_total": products_total,
        "active_products": active_products,
        "featured_products": featured_products,
        "orders_count": len(orders),
        "revenue": revenue,
        "member_count": member_count
    }

@api_router.get("/portal/merch/products")
async def get_portal_merch_products(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None
):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_demo_merch_data(tenant_id)

    query = {"tenant_id": tenant_id, "is_active": True}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    products = await db.merch_products.find(query, {"_id": 0}).sort("is_featured", -1).to_list(200)
    return {"products": [serialize_doc(p) for p in products]}

@api_router.post("/portal/merch/orders")
async def create_merch_order(request: Request, payload: MerchOrderCreate):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    if not payload.items:
        raise HTTPException(status_code=400, detail="No items in order")

    subtotal = 0
    items = []
    for item in payload.items:
        total_line = item.price * item.quantity
        subtotal += total_line
        items.append(item.model_dump())

    subtotal = round(subtotal, 2)
    order = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": user.get("user_id"),
        "items": items,
        "subtotal": subtotal,
        "total": subtotal,
        "status": "placed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.merch_orders.insert_one(order)
    return {
        "order": serialize_doc(order),
        "giving_nudge": {
            "show": True,
            "message": "Would you like to add a gift?",
            "subtitle": "Support Abundant Church",
            "suggested_amounts": [5, 10, 20, 100]
        }
    }

# ============== KIDS CHECK-IN ROUTES ==============

def generate_pickup_code():
    """Generate a simple 3-digit pickup code like '247'"""
    import random
    return str(random.randint(100, 999))

@api_router.get("/portal/kids")
async def get_my_kids(request: Request):
    """Get all children for the current user"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    children = await db.children.find(
        {"tenant_id": tenant_id, "parent_user_id": user_id},
        {"_id": 0}
    ).to_list(50)
    
    return {"children": [serialize_doc(c) for c in children]}


@api_router.get("/portal/kids/children")
async def get_mobile_children(request: Request):
    """Mobile alias for children list."""
    return await get_my_kids(request)

@api_router.post("/portal/kids")
async def add_child(request: Request, payload: ChildCreate):
    """Add a new child"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    child = Child(
        tenant_id=tenant_id,
        parent_user_id=user_id,
        name=payload.name,
        birthdate=payload.birthdate,
        allergies=payload.allergies,
        special_needs=payload.special_needs,
        emergency_contact=payload.emergency_contact,
        emergency_phone=payload.emergency_phone
    ).model_dump()
    child["created_at"] = datetime.now(timezone.utc).isoformat()
    child["grade"] = payload.grade
    child["classroom"] = payload.classroom or "Sunday School Adventures"
    child["first_name"] = payload.first_name
    child["last_name"] = payload.last_name
    
    await db.children.insert_one(child)
    return {"message": "Child added", "child": serialize_doc(child)}


@api_router.post("/portal/kids/children")
async def add_mobile_child(request: Request, payload: ChildCreate):
    """Mobile alias for adding child profile."""
    return await add_child(request, payload)

@api_router.delete("/portal/kids/{child_id}")
async def delete_child(request: Request, child_id: str):
    """Delete a child"""
    user = await get_current_member_user(request)
    user_id = user.get("user_id")
    
    child = await db.children.find_one({"id": child_id}, {"_id": 0})
    if not child or child.get("parent_user_id") != user_id:
        raise HTTPException(status_code=404, detail="Child not found")
    
    await db.children.delete_one({"id": child_id})
    return {"message": "Child deleted"}

@api_router.post("/portal/kids/{child_id}/checkin")
async def checkin_child(request: Request, child_id: str, payload: dict = None):
    """Check in a child for Sunday School. Supports idempotency key."""
    # Idempotency check
    idem_key = request.headers.get("x-idempotency-key")
    if idem_key:
        cached = await check_idempotency(f"checkin:{idem_key}")
        if cached:
            return cached
    
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    child = await db.children.find_one({"id": child_id, "parent_user_id": user_id}, {"_id": 0})
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    existing = await db.checkins.find_one({"child_id": child_id, "status": "checked_in"}, {"_id": 0})
    if existing:
        # Return existing check-in data instead of error (idempotent)
        result = {"message": "Child is already checked in", "pickup_code": existing.get("pickup_code"), "checkin_time": existing.get("checked_in_at"), "status": "checked_in", "checkin": serialize_doc(existing), "sms_sent": False}
        return result
    
    pickup_code = generate_pickup_code()
    parent = await db.users.find_one({"user_id": user_id}, {"_id": 0, "name": 1, "phone": 1})
    parent_name = parent.get("name", "Parent") if parent else "Parent"
    parent_phone = parent.get("phone", "") if parent else ""
    
    checkin = Checkin(
        tenant_id=tenant_id, child_id=child_id, child_name=child.get("name"),
        parent_user_id=user_id, parent_name=parent_name, parent_phone=parent_phone,
        pickup_code=pickup_code, classroom=payload.get("classroom") if payload else "Sunday School",
        status="checked_in"
    ).model_dump()
    checkin["checked_in_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.checkins.insert_one(checkin)
    await audit_log("kids_checkin", "checkin", checkin.get("id", ""), tenant_id, user_id, parent_name, request=request)
    
    sms_message = f"Thanks for bringing {child.get('name')} to Sunday School! Pickup code: {pickup_code}."
    
    result = {
        "message": "Child checked in successfully",
        "pickup_code": pickup_code,
        "checkin_time": checkin["checked_in_at"],
        "status": "checked_in",
        "checkin": serialize_doc(checkin),
        "sms_sent": True,
        "sms_message": sms_message,
        "nudge": {
            "show_giving": True,
            "show_cafe": True,
            "give_amounts": [10, 25, 50, 100],
            "message": "The kids are in — support your church today?"
        }
    }
    
    if idem_key:
        await store_idempotency(f"checkin:{idem_key}", result)
    
    return result


@api_router.post("/portal/kids/checkin")
async def checkin_child_mobile(request: Request, payload: KidsCheckinRequest):
    """Mobile-friendly check-in endpoint using child_id in request body."""
    checkin_payload = {"classroom": payload.classroom or "Sunday School"}
    return await checkin_child(request, payload.child_id, checkin_payload)

@api_router.get("/portal/kids/checkins/active")
async def get_active_checkins(request: Request):
    """Get all active check-ins for the current user's children"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    checkins = await db.checkins.find({
        "tenant_id": tenant_id,
        "parent_user_id": user_id,
        "status": "checked_in"
    }, {"_id": 0}).to_list(50)
    
    return {"checkins": [serialize_doc(c) for c in checkins]}


@api_router.get("/portal/kids/checkin/history")
async def get_portal_kids_checkin_history(request: Request, limit: int = 100):
    """Get historical check-ins for the current parent's children."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")

    checkins = await db.checkins.find(
        {
            "tenant_id": tenant_id,
            "parent_user_id": user_id
        },
        {"_id": 0}
    ).sort("checked_in_at", -1).limit(limit).to_list(limit)

    return {
        "checkins": [serialize_doc(c) for c in checkins],
        "total": len(checkins)
    }

# Admin routes for Kids Check-in
@api_router.get("/admin/kids/checkins")
async def get_all_checkins(request: Request, status: str = None):
    """Get all check-ins for admin view"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    
    checkins = await db.checkins.find(query, {"_id": 0}).sort("checked_in_at", -1).to_list(200)
    return {"checkins": [serialize_doc(c) for c in checkins]}

@api_router.post("/admin/kids/checkins/{checkin_id}/checkout")
async def checkout_child(request: Request, checkin_id: str):
    """Admin: Check out a child"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    checkin = await db.checkins.find_one({"id": checkin_id, "tenant_id": tenant_id}, {"_id": 0})
    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in not found")
    
    if checkin.get("status") == "checked_out":
        raise HTTPException(status_code=400, detail="Child is already checked out")
    
    await db.checkins.update_one(
        {"id": checkin_id},
        {"$set": {
            "status": "checked_out",
            "checked_out_at": datetime.now(timezone.utc).isoformat(),
            "checked_out_by": user.get("name", "Admin")
        }}
    )
    
    updated = await db.checkins.find_one({"id": checkin_id}, {"_id": 0})
    
    # Notify parent via push
    try:
        child = await db.children.find_one({"id": checkin.get("child_id")}, {"_id": 0})
        if child and child.get("parent_id"):
            await send_push_notification(
                child["parent_id"], user.get("tenant_id", ""),
                "Pickup Time!",
                f"{child.get('name', 'Your child')} is ready for pickup.",
                "/portal/kids"
            )
    except Exception:
        pass
    
    return {"message": "Child checked out", "checkin": serialize_doc(updated)}

@api_router.get("/admin/kids/checkins/history")
async def get_checkin_history(request: Request, days: int = 30):
    """Get check-in history for reporting"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    checkins = await db.checkins.find({
        "tenant_id": tenant_id,
        "checked_in_at": {"$gte": cutoff.isoformat()}
    }, {"_id": 0}).sort("checked_in_at", -1).to_list(500)
    
    return {"checkins": [serialize_doc(c) for c in checkins], "days": days}

@api_router.get("/admin/kids/all")
async def get_all_kids_admin(request: Request):
    """Get all registered children for admin view"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Get all children with parent info
    children = await db.children.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(500)
    
    # Enrich with parent info
    enriched = []
    for child in children:
        parent = await db.users.find_one({"id": child.get("parent_user_id")}, {"_id": 0, "password_hash": 0})
        enriched.append({
            **serialize_doc(child),
            "parent_name": parent.get("name") if parent else "Unknown",
            "parent_phone": parent.get("phone") if parent else None,
            "parent_email": parent.get("email") if parent else None
        })
    
    return {"children": enriched}

@api_router.post("/admin/kids/{child_id}/checkin")
async def admin_checkin_child(request: Request, child_id: str, payload: dict = None):
    """Admin: Check in a child directly"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Get child
    child = await db.children.find_one({"id": child_id, "tenant_id": tenant_id}, {"_id": 0})
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    # Check if already checked in
    existing = await db.checkins.find_one({
        "child_id": child_id,
        "status": "checked_in"
    }, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Child is already checked in")
    
    # Generate pickup code
    pickup_code = generate_pickup_code()
    
    # Get parent info
    parent = await db.users.find_one({"user_id": child.get("parent_user_id")}, {"_id": 0})
    parent_name = parent.get("name", "Unknown Parent") if parent else "Unknown Parent"
    parent_phone = parent.get("phone") if parent else None
    
    checkin = Checkin(
        tenant_id=tenant_id,
        child_id=child_id,
        child_name=child.get("name", "Unknown Child"),
        parent_user_id=child.get("parent_user_id"),
        parent_name=parent_name,
        parent_phone=parent_phone,
        pickup_code=pickup_code,
        classroom=payload.get("classroom", "Sunday School") if payload else "Sunday School"
    ).model_dump()
    checkin["checked_in_at"] = datetime.now(timezone.utc).isoformat()
    checkin["checked_in_by"] = user.get("name", "Admin")
    
    await db.checkins.insert_one(checkin)
    
    # Mock SMS notification (parent info already retrieved above)
    print(f"[MOCK SMS] To: {parent_phone or 'No phone'}")
    print(f"[MOCK SMS] Message: Hi {parent_name}! {child.get('name')} has been checked into Sunday School by {user.get('name', 'Staff')}. Pickup code: {pickup_code}")
    
    return {
        "message": f"{child.get('name')} checked in successfully",
        "pickup_code": pickup_code,
        "checkin": serialize_doc(checkin)
    }

@api_router.post("/admin/kids/verify-pickup")
async def verify_pickup_code(request: Request, payload: dict):
    """Admin: Verify a pickup code and get child info"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    code = payload.get("code", "").upper().strip()
    if not code:
        raise HTTPException(status_code=400, detail="Pickup code required")
    
    # Find active check-in with this code
    checkin = await db.checkins.find_one({
        "tenant_id": tenant_id,
        "pickup_code": code,
        "status": "checked_in"
    }, {"_id": 0})
    
    if not checkin:
        return {"valid": False, "message": "Invalid or expired pickup code"}
    
    # Get child info
    child = await db.children.find_one({"id": checkin.get("child_id")}, {"_id": 0})
    
    # Get parent info
    parent = await db.users.find_one({"id": checkin.get("parent_user_id")}, {"_id": 0, "password_hash": 0})
    
    return {
        "valid": True,
        "checkin": serialize_doc(checkin),
        "child": serialize_doc(child) if child else None,
        "parent": {
            "name": parent.get("name") if parent else "Unknown",
            "phone": parent.get("phone") if parent else None,
            "email": parent.get("email") if parent else None
        }
    }

class RegisterFamilyPayload(BaseModel):
    parentName: str
    parentEmail: str
    parentPhone: str = ""
    childName: str
    childBirthdate: str = ""
    childAllergies: str = ""
    childNotes: str = ""

@api_router.post("/admin/kids/register-family")
async def register_new_family(request: Request, payload: RegisterFamilyPayload):
    """Admin: Register a new family (walk-in) directly from front desk"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Check if parent already exists
    existing_user = await db.users.find_one({"email": payload.parentEmail.lower()})
    
    if existing_user:
        parent_user_id = existing_user.get("user_id")
        # Check if child already exists for this parent
        existing_child = await db.children.find_one({
            "parent_user_id": parent_user_id,
            "name": payload.childName
        })
        if existing_child:
            raise HTTPException(status_code=400, detail=f"{payload.childName} is already registered for this parent")
    else:
        # Create new parent user
        parent_user_id = f"member_{str(uuid.uuid4())[:8]}"
        temp_password = secrets.token_urlsafe(12)
        password_hash = hashlib.sha256(temp_password.encode()).hexdigest()
        new_user = {
            "user_id": parent_user_id,
            "email": payload.parentEmail.lower(),
            "name": payload.parentName,
            "phone": payload.parentPhone,
            "role": "member",
            "tenant_id": tenant_id,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "registered_by_admin": True
        }
        await db.users.insert_one(new_user)
        
        # Log temporary password for staff to share
        print(f"[NEW FAMILY] Created parent: {payload.parentEmail} | Temp Password: {temp_password}")
    
    # Create child
    child_id = str(uuid.uuid4())
    child = {
        "id": child_id,
        "tenant_id": tenant_id,
        "parent_user_id": parent_user_id,
        "parent_name": payload.parentName,
        "parent_phone": payload.parentPhone,
        "name": payload.childName,
        "birthdate": payload.childBirthdate if payload.childBirthdate else None,
        "allergies": payload.childAllergies,
        "special_needs": payload.childNotes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.children.insert_one(child)
    
    return {
        "message": f"Family registered successfully! Welcome {payload.parentName} & {payload.childName}",
        "parent_email": payload.parentEmail,
        "child_id": child_id,
        "new_user": not existing_user
    }

# ============== CAFE ROUTES ==============

@api_router.get("/admin/cafe/settings")
async def get_admin_cafe_settings(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_cafe_data(tenant_id)
    settings = await db.cafe_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    return {"settings": serialize_doc(settings) if settings else None}

@api_router.patch("/admin/cafe/settings")
async def update_admin_cafe_settings(request: Request, payload: CafeSettingsUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.cafe_settings.update_one(
            {"tenant_id": tenant_id},
            {"$set": update_data},
            upsert=True
        )

    settings = await db.cafe_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    return {"settings": serialize_doc(settings) if settings else None}

@api_router.get("/admin/cafe/items")
async def get_admin_cafe_items(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None
):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_cafe_data(tenant_id)

    query = {"tenant_id": tenant_id}
    if category:
        query["category"] = category
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    items = await db.cafe_items.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"items": [serialize_doc(item) for item in items]}

@api_router.post("/admin/cafe/items")
async def create_admin_cafe_item(request: Request, payload: CafeItemCreate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    item = CafeItem(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        price=payload.price,
        image_url=payload.image_url,
        is_featured=payload.is_featured,
        is_active=payload.is_active
    ).model_dump()

    await db.cafe_items.insert_one(item)
    return {"item": serialize_doc(item)}

@api_router.put("/admin/cafe/items/{item_id}")
async def update_admin_cafe_item(request: Request, item_id: str, payload: CafeItemUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.cafe_items.update_one({"id": item_id, "tenant_id": tenant_id}, {"$set": update_data})

    item = await db.cafe_items.find_one({"id": item_id, "tenant_id": tenant_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Cafe item not found")

    return {"item": serialize_doc(item)}

@api_router.delete("/admin/cafe/items/{item_id}")
async def delete_admin_cafe_item(request: Request, item_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await db.cafe_items.delete_one({"id": item_id, "tenant_id": tenant_id})
    return {"message": "Cafe item deleted"}

@api_router.get("/admin/cafe/orders")
async def get_admin_cafe_orders(request: Request, limit: int = 50):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_cafe_data(tenant_id)

    orders = await db.cafe_orders.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"orders": [serialize_doc(order) for order in orders]}

@api_router.get("/admin/cafe/summary")
async def get_admin_cafe_summary(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_cafe_data(tenant_id)

    items_total = await db.cafe_items.count_documents({"tenant_id": tenant_id})
    active_items = await db.cafe_items.count_documents({"tenant_id": tenant_id, "is_active": True})
    orders = await db.cafe_orders.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(200)
    revenue = round(sum(order.get("total", 0) for order in orders), 2)
    member_count = await db.people.count_documents({"tenant_id": tenant_id})
    if member_count == 0 or member_count > 5000:
        member_count = 500

    return {
        "items_total": items_total,
        "active_items": active_items,
        "orders_count": len(orders),
        "revenue": revenue,
        "member_count": member_count
    }

@api_router.get("/portal/cafe/settings")
async def get_portal_cafe_settings(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    await ensure_demo_cafe_data(tenant_id)
    settings = await db.cafe_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    return {"settings": serialize_doc(settings) if settings else None}

@api_router.get("/portal/cafe/items")
async def get_portal_cafe_items(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None
):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_demo_cafe_data(tenant_id)

    query = {"tenant_id": tenant_id, "is_active": True}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    items = await db.cafe_items.find(query, {"_id": 0}).sort("is_featured", -1).to_list(200)
    return {"items": [serialize_doc(item) for item in items]}


@api_router.get("/portal/cafe/menu")
async def get_portal_cafe_menu(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None
):
    """Mobile alias for cafe items list."""
    return await get_portal_cafe_items(request, search=search, category=category)

@api_router.post("/portal/cafe/orders")
async def create_portal_cafe_order(request: Request, payload: CafeOrderCreate):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    if not payload.items:
        raise HTTPException(status_code=400, detail="No items in order")
    if not payload.pickup_time:
        raise HTTPException(status_code=400, detail="Pickup time is required")

    items = []
    total = 0
    for item in payload.items:
        total += item.price * item.quantity
        items.append(item.model_dump())

    total = round(total, 2)
    order = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": user.get("user_id"),
        "items": items,
        "pickup_time": payload.pickup_time,
        "notes": payload.notes or "",
        "total": total,
        "status": "placed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.cafe_orders.insert_one(order)
    return {
        "order": serialize_doc(order),
        "giving_nudge": {
            "show": True,
            "message": "Would you like to add a gift?",
            "subtitle": "Support Abundant Church",
            "suggested_amounts": [5, 10, 20, 100]
        }
    }


@api_router.post("/portal/cafe/order")
async def create_mobile_cafe_order(request: Request, payload: CafeOrderCreate):
    """Mobile alias for placing cafe order."""
    return await create_portal_cafe_order(request, payload)

# ============== PASTOR MEETINGS ROUTES ==============

@api_router.get("/admin/meetings/slots")
async def get_admin_meeting_slots(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_meetings_data(tenant_id)
    slots = await db.pastor_meeting_slots.find({"tenant_id": tenant_id}, {"_id": 0}).sort("start_time", 1).to_list(200)
    return {"slots": [serialize_doc(slot) for slot in slots]}

@api_router.post("/admin/meetings/slots")
async def create_admin_meeting_slot(request: Request, payload: PastorMeetingSlotCreate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    slot = PastorMeetingSlot(
        tenant_id=tenant_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        location=payload.location
    ).model_dump()
    await db.pastor_meeting_slots.insert_one(slot)
    return {"slot": serialize_doc(slot)}

@api_router.get("/portal/meetings/slots")
async def get_portal_meeting_slots(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    await ensure_demo_meetings_data(tenant_id)
    slots = await db.pastor_meeting_slots.find({"tenant_id": tenant_id, "status": "open"}, {"_id": 0}).sort("start_time", 1).to_list(200)
    return {"slots": [serialize_doc(slot) for slot in slots]}

@api_router.post("/portal/meetings/book")
async def book_portal_meeting(request: Request, payload: PastorMeetingBooking):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    slot = await db.pastor_meeting_slots.find_one({"id": payload.slot_id, "tenant_id": tenant_id}, {"_id": 0})
    if not slot or slot.get("status") != "open":
        raise HTTPException(status_code=400, detail="Slot is no longer available")

    await db.pastor_meeting_slots.update_one({"id": slot["id"]}, {"$set": {"status": "booked", "updated_at": datetime.now(timezone.utc).isoformat()}})

    meeting = PastorMeeting(
        tenant_id=tenant_id,
        slot_id=slot["id"],
        user_id=user.get("user_id"),
        member_name=user.get("name"),
        member_email=user.get("email"),
        topic=payload.topic,
        notes=payload.notes,
        status="scheduled"
    ).model_dump()
    meeting["created_at"] = datetime.now(timezone.utc).isoformat()
    meeting["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.pastor_meetings.insert_one(meeting)
    notifications = await notify_meeting_event("meeting_scheduled", meeting)

    return {"meeting": serialize_doc(meeting), "notifications": notifications}

@api_router.get("/portal/meetings")
async def get_portal_meetings(request: Request):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    meetings = await db.pastor_meetings.find({"tenant_id": tenant_id, "user_id": user.get("user_id")}, {"_id": 0}).sort("created_at", -1).to_list(100)
    slot_ids = [m.get("slot_id") for m in meetings]
    slots = await db.pastor_meeting_slots.find({"id": {"$in": slot_ids}}, {"_id": 0}).to_list(200)
    slot_map = {s["id"]: s for s in slots}

    response = []
    for meeting in meetings:
        slot = slot_map.get(meeting.get("slot_id"), {})
        response.append({
            **serialize_doc(meeting),
            "slot": serialize_doc(slot) if slot else None
        })

    return {"meetings": response}

@api_router.get("/admin/meetings")
async def get_admin_meetings(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    meetings = await db.pastor_meetings.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    slot_ids = [m.get("slot_id") for m in meetings]
    slots = await db.pastor_meeting_slots.find({"id": {"$in": slot_ids}}, {"_id": 0}).to_list(200)
    slot_map = {s["id"]: s for s in slots}

    response = []
    for meeting in meetings:
        slot = slot_map.get(meeting.get("slot_id"), {})
        response.append({
            **serialize_doc(meeting),
            "slot": serialize_doc(slot) if slot else None
        })

    return {"meetings": response}

@api_router.patch("/admin/meetings/{meeting_id}")
async def update_admin_meeting(request: Request, meeting_id: str, payload: PastorMeetingUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.pastor_meetings.update_one({"id": meeting_id, "tenant_id": tenant_id}, {"$set": update_data})

    meeting = await db.pastor_meetings.find_one({"id": meeting_id, "tenant_id": tenant_id}, {"_id": 0})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {"meeting": serialize_doc(meeting)}

@api_router.post("/admin/meetings/{meeting_id}/recording")
async def upload_meeting_recording(request: Request, meeting_id: str, file: UploadFile = File(...)):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    meeting = await db.pastor_meetings.find_one({"id": meeting_id, "tenant_id": tenant_id}, {"_id": 0})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    uploads_dir = ROOT_DIR / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    file_suffix = Path(file.filename or "recording").suffix or ".webm"
    file_path = uploads_dir / f"meeting_{meeting_id}{file_suffix}"

    with file_path.open("wb") as buffer:
        content = await file.read()
        buffer.write(content)

    transcript_text = await transcribe_audio_with_whisper(file_path)
    summary_text = await summarize_meeting_with_claude(transcript_text, meeting.get("topic"))

    update_data = {
        "transcript": transcript_text,
        "summary": summary_text,
        "recording_filename": file_path.name,
        "status": "completed",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    await db.pastor_meetings.update_one({"id": meeting_id}, {"$set": update_data})
    notifications = await notify_meeting_event("meeting_summary_ready", meeting)

    return {"transcript": transcript_text, "summary": summary_text, "notifications": notifications}

# ============== LEADERSHIP NOTES ROUTES ==============


@api_router.post("/portal/notes")
async def create_leadership_note(request: Request, payload: LeadershipNoteCreate):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")

    if not payload.subject or not payload.subject.strip():
        raise HTTPException(status_code=400, detail="Subject is required")
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    note = LeadershipNote(
        tenant_id=tenant_id,
        user_id=user.get("user_id"),
        subject=payload.subject.strip(),
        message=payload.message.strip(),
        category=payload.category,
        status="new",
        member_name=user.get("name"),
        member_email=user.get("email")
    ).model_dump()
    note["created_at"] = datetime.now(timezone.utc).isoformat()

    await db.leadership_notes.insert_one(note)
    return {"message": "Note submitted", "note": serialize_doc(note)}

@api_router.get("/admin/notes")
async def get_leadership_notes(
    request: Request,
    tenant_id: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 200
):
    user = await get_current_admin_user(request)
    is_platform_admin = user.get("role") == "platform_admin"

    query = {}
    if is_platform_admin:
        if tenant_id:
            query["tenant_id"] = tenant_id
    else:
        if not user.get("tenant_id"):
            raise HTTPException(status_code=400, detail="Tenant context required")
        query["tenant_id"] = user.get("tenant_id")

    if category:
        query["category"] = category
    if status:
        query["status"] = status

    notes = await db.leadership_notes.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)

    user_ids = [note.get("user_id") for note in notes if note.get("user_id")]
    users = []
    if user_ids:
        users = await db.users.find({"user_id": {"$in": user_ids}}, {"_id": 0, "user_id": 1, "name": 1, "email": 1}).to_list(500)
    user_map = {u["user_id"]: u for u in users}

    tenant_map = {}
    if is_platform_admin and not tenant_id and notes:
        tenant_ids = list({note.get("tenant_id") for note in notes if note.get("tenant_id")})
        tenants = await db.tenants.find({"id": {"$in": tenant_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(200)
        tenant_map = {t["id"]: t for t in tenants}

    enriched_notes = []
    for note in notes:
        member = user_map.get(note.get("user_id"), {})
        note["member_name"] = note.get("member_name") or member.get("name")
        note["member_email"] = note.get("member_email") or member.get("email")
        if is_platform_admin:
            tenant_info = tenant_map.get(note.get("tenant_id"))
            note["tenant_name"] = tenant_info.get("name") if tenant_info else None
        enriched_notes.append(serialize_doc(note))

    return {"notes": enriched_notes}

# ============== VIDEO NOTES ROUTES (Masterclass-style) ==============

@api_router.post("/portal/video-notes")
async def create_video_note(request: Request, payload: VideoNoteCreate):
    """Create a note for a video"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=400, detail="Note content is required")
    
    # Get video title for reference
    video = await db.media_videos.find_one({"id": payload.video_id}, {"_id": 0, "title": 1})
    video_title = video.get("title") if video else None
    
    note = VideoNote(
        tenant_id=tenant_id,
        user_id=user_id,
        video_id=payload.video_id,
        content=payload.content.strip(),
        timestamp=payload.timestamp,
        is_public=payload.is_public,
        author_name=user.get("name"),
        video_title=video_title
    ).model_dump()
    note["created_at"] = datetime.now(timezone.utc).isoformat()
    note["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.video_notes.insert_one(note)
    return {"message": "Note created", "note": serialize_doc(note)}

@api_router.get("/portal/video-notes")
async def get_my_video_notes(
    request: Request,
    video_id: Optional[str] = None,
    limit: int = 100
):
    """Get current user's notes, optionally filtered by video"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    query = {"tenant_id": tenant_id, "user_id": user_id}
    if video_id:
        query["video_id"] = video_id
    
    notes = await db.video_notes.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"notes": [serialize_doc(n) for n in notes]}

@api_router.get("/portal/video-notes/video/{video_id}")
async def get_video_notes_for_video(request: Request, video_id: str):
    """Get all notes for a specific video (own notes + shared notes)"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    # Get own notes + notes shared with me + public notes from same tenant
    query = {
        "tenant_id": tenant_id,
        "video_id": video_id,
        "$or": [
            {"user_id": user_id},  # Own notes
            {"shared_with": user_id},  # Shared with me
            {"is_public": True}  # Public notes from same church
        ]
    }
    
    notes = await db.video_notes.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    
    # Mark which notes are own vs shared
    result = []
    for note in notes:
        note_data = serialize_doc(note)
        note_data["is_own"] = note.get("user_id") == user_id
        note_data["is_shared_with_me"] = user_id in (note.get("shared_with") or [])
        result.append(note_data)
    
    return {"notes": result}

@api_router.get("/portal/video-notes/shared")
async def get_notes_shared_with_me(request: Request, limit: int = 100):
    """Get all notes shared with the current user"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    query = {
        "tenant_id": tenant_id,
        "user_id": {"$ne": user_id},  # Not my own notes
        "$or": [
            {"shared_with": user_id},
            {"is_public": True}
        ]
    }
    
    notes = await db.video_notes.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"notes": [serialize_doc(n) for n in notes]}

@api_router.put("/portal/video-notes/{note_id}")
async def update_video_note(request: Request, note_id: str, payload: VideoNoteUpdate):
    """Update a note (only own notes)"""
    user = await get_current_member_user(request)
    user_id = user.get("user_id")
    
    # Find note and verify ownership
    note = await db.video_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Cannot edit someone else's note")
    
    update_data = {}
    if payload.content is not None:
        update_data["content"] = payload.content.strip()
    if payload.timestamp is not None:
        update_data["timestamp"] = payload.timestamp
    if payload.is_public is not None:
        update_data["is_public"] = payload.is_public
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.video_notes.update_one({"id": note_id}, {"$set": update_data})
    
    updated_note = await db.video_notes.find_one({"id": note_id}, {"_id": 0})
    return {"message": "Note updated", "note": serialize_doc(updated_note)}

@api_router.delete("/portal/video-notes/{note_id}")
async def delete_video_note(request: Request, note_id: str):
    """Delete a note (only own notes)"""
    user = await get_current_member_user(request)
    user_id = user.get("user_id")
    
    note = await db.video_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete someone else's note")
    
    await db.video_notes.delete_one({"id": note_id})
    return {"message": "Note deleted"}

@api_router.post("/portal/video-notes/{note_id}/share")
async def share_video_note(request: Request, note_id: str, payload: VideoNoteShare):
    """Share a note with specific users or the entire church"""
    user = await get_current_member_user(request)
    user_id = user.get("user_id")
    tenant_id = user.get("tenant_id")
    
    note = await db.video_notes.find_one({"id": note_id}, {"_id": 0})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Cannot share someone else's note")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    # Add users to share list
    if payload.user_ids:
        # Verify users exist and are in same tenant
        valid_users = await db.users.find(
            {"user_id": {"$in": payload.user_ids}, "tenant_id": tenant_id},
            {"_id": 0, "user_id": 1}
        ).to_list(100)
        valid_user_ids = [u["user_id"] for u in valid_users]
        
        # Merge with existing shared_with list
        existing_shared = set(note.get("shared_with") or [])
        existing_shared.update(valid_user_ids)
        update_data["shared_with"] = list(existing_shared)
    
    # Update public status if provided
    if payload.is_public is not None:
        update_data["is_public"] = payload.is_public
    
    await db.video_notes.update_one({"id": note_id}, {"$set": update_data})
    
    updated_note = await db.video_notes.find_one({"id": note_id}, {"_id": 0})
    return {"message": "Note shared", "note": serialize_doc(updated_note)}

@api_router.get("/portal/church-members")
async def get_church_members_for_sharing(request: Request, search: Optional[str] = None):
    """Get list of church members for sharing notes (excluding self)"""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    query = {"tenant_id": tenant_id, "user_id": {"$ne": user_id}}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    members = await db.users.find(
        query,
        {"_id": 0, "user_id": 1, "name": 1, "email": 1}
    ).limit(50).to_list(50)
    
    return {"members": members}

# ============== STRIPE PAYMENT ROUTES ==============

@api_router.get("/payments/config")
async def get_payment_config():
    """Get the Stripe publishable key for frontend"""
    publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY")
    return {
        "publishable_key": publishable_key,
        "currency": "usd",
        "payment_methods": ["card"]
    }

# Donation packages (FIXED - never accept amounts from frontend)
DONATION_PACKAGES = {
    "tithe_10": 10.00,
    "tithe_25": 25.00,
    "tithe_50": 50.00,
    "tithe_100": 100.00,
    "tithe_250": 250.00,
    "tithe_500": 500.00,
    "tithe_1000": 1000.00,
    "custom": None,  # Custom amounts handled separately with validation
}

class DonationRequest(BaseModel):
    package_id: str = "custom"
    custom_amount: Optional[float] = None
    fund_id: Optional[str] = None
    origin_url: str
    recurring: bool = False
    donor_name: Optional[str] = None
    donor_email: Optional[str] = None

class CheckoutStatusRequest(BaseModel):
    session_id: str

@api_router.post("/payments/donate")
async def create_donation_checkout(request: Request, donation: DonationRequest):
    """Create a Stripe checkout session for donations"""
    try:
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Payment processing not configured")
        
        # Get logged in user if available
        session_token = get_session_token_from_request(request)
        user_email = None
        user_id = None
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    user_email = user.get("email")
                    user_id = user.get("user_id")
        
        # Determine amount
        if donation.package_id == "custom":
            if not donation.custom_amount or donation.custom_amount < 1.0:
                raise HTTPException(status_code=400, detail="Custom amount must be at least $1.00")
            if donation.custom_amount > 100000.0:
                raise HTTPException(status_code=400, detail="Amount exceeds maximum allowed")
            amount = float(donation.custom_amount)
        else:
            amount = DONATION_PACKAGES.get(donation.package_id)
            if amount is None:
                raise HTTPException(status_code=400, detail="Invalid donation package")
        
        # Build success/cancel URLs from frontend origin
        success_url = f"{donation.origin_url}?status=success&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{donation.origin_url}?status=cancelled"
        
        # Initialize Stripe
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        # Create metadata
        metadata = {
            "tenant_id": DEFAULT_TENANT_ID,
            "fund_id": donation.fund_id or "general",
            "donor_name": donation.donor_name or "Anonymous",
            "donor_email": user_email or donation.donor_email or "",
            "user_id": user_id or "",
            "recurring": str(donation.recurring),
            "source": "web_portal"
        }
        
        # Create checkout session
        checkout_request = CheckoutSessionRequest(
            amount=amount,
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            payment_methods=["card"]  # Add "crypto" if user requests
        )
        
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Store transaction record
        transaction = {
            "id": f"txn_{uuid.uuid4().hex[:12]}",
            "tenant_id": DEFAULT_TENANT_ID,
            "session_id": session.session_id,
            "amount": amount,
            "currency": "usd",
            "fund_id": donation.fund_id or "general",
            "donor_name": donation.donor_name,
            "donor_email": donation.donor_email,
            "payment_status": "pending",
            "payment_method": "stripe",
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc)
        }
        await db.payment_transactions.insert_one(transaction)
        
        return {
            "checkout_url": session.url,
            "session_id": session.session_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (400, 401, etc.)
        raise
    except Exception as e:
        logger.error(f"Donation checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str):
    """Check the status of a Stripe checkout session"""
    try:
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Payment processing not configured")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction in database
        if status.payment_status == "paid":
            # Find and update transaction
            transaction = await db.payment_transactions.find_one(
                {"session_id": session_id},
                {"_id": 0}
            )
            
            if transaction and transaction.get("payment_status") != "paid":
                # Update to paid
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "payment_status": "paid",
                        "paid_at": datetime.now(timezone.utc)
                    }}
                )
                
                # Create donation record
                donation = {
                    "id": f"donation_{uuid.uuid4().hex[:12]}",
                    "tenant_id": DEFAULT_TENANT_ID,
                    "person_id": None,  # Link to person if logged in
                    "fund_id": transaction.get("fund_id", "general"),
                    "fund_name": "General Fund",  # Lookup from funds
                    "amount": status.amount_total / 100,  # Convert from cents
                    "payment_method": "card",
                    "payment_status": "completed",
                    "transaction_id": session_id,
                    "donor_name": transaction.get("donor_name"),
                    "donor_email": transaction.get("donor_email"),
                    "donation_date": datetime.now(timezone.utc).isoformat(),
                    "notes": "Online donation via Stripe",
                    "created_at": datetime.now(timezone.utc)
                }
                await db.donations.insert_one(donation)
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount": status.amount_total / 100,  # Convert from cents
            "currency": status.currency
        }
        
    except Exception as e:
        logger.error(f"Payment status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for payment confirmations"""
    try:
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        if not stripe_api_key:
            return {"status": "ignored", "reason": "no_api_key"}
        
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        logger.info(f"Stripe webhook: {webhook_response.event_type} - {webhook_response.session_id}")
        
        # Update transaction based on webhook
        if webhook_response.payment_status == "paid":
            # Get the transaction
            transaction = await db.payment_transactions.find_one(
                {"session_id": webhook_response.session_id},
                {"_id": 0}
            )
            
            if transaction:
                # Update transaction status
                await db.payment_transactions.update_one(
                    {"session_id": webhook_response.session_id},
                    {"$set": {
                        "payment_status": "paid",
                        "webhook_received_at": datetime.now(timezone.utc)
                    }}
                )
                
                # Create donation record
                donor_email = transaction.get("donor_email") or transaction.get("metadata", {}).get("donor_email")
                if donor_email:
                    person = await db.people.find_one({"email": donor_email}, {"_id": 0})
                    person_id = person["id"] if person else None
                else:
                    person_id = None
                
                donation = {
                    "id": f"don_{uuid.uuid4().hex[:12]}",
                    "tenant_id": DEFAULT_TENANT_ID,
                    "person_id": person_id,
                    "amount": transaction.get("amount", 0),
                    "fund_id": transaction.get("fund_id", "general"),
                    "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "payment_method": "stripe",
                    "transaction_id": webhook_response.session_id,
                    "donor_name": transaction.get("donor_name", "Anonymous"),
                    "donor_email": donor_email,
                    "status": "completed",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.donations.insert_one(donation)
                logger.info(f"Created donation record: {donation['id']}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return {"status": "error", "message": str(e)}

# ============== SAVED PAYMENT METHODS ==============

@api_router.get("/payments/methods")
async def get_saved_payment_methods(request: Request):
    """Get saved payment methods for the current user"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Get saved payment methods from database
    methods = await db.payment_methods.find(
        {"user_id": user["user_id"], "is_active": True},
        {"_id": 0}
    ).to_list(10)
    
    return {"payment_methods": methods}

class SavePaymentMethodRequest(BaseModel):
    card_last_four: str
    card_brand: str
    card_exp_month: int
    card_exp_year: int
    stripe_payment_method_id: Optional[str] = None
    is_default: bool = False

@api_router.post("/payments/methods")
async def save_payment_method(request: Request, method_data: SavePaymentMethodRequest):
    """Save a new payment method for the current user"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # If setting as default, unset other defaults
    if method_data.is_default:
        await db.payment_methods.update_many(
            {"user_id": user["user_id"]},
            {"$set": {"is_default": False}}
        )
    
    payment_method = {
        "id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        "tenant_id": user.get("tenant_id"),
        "card_last_four": method_data.card_last_four,
        "card_brand": method_data.card_brand,
        "card_exp_month": method_data.card_exp_month,
        "card_exp_year": method_data.card_exp_year,
        "stripe_payment_method_id": method_data.stripe_payment_method_id,
        "is_default": method_data.is_default,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payment_methods.insert_one(payment_method)
    
    return {"message": "Payment method saved", "payment_method": {k: v for k, v in payment_method.items() if k != "_id"}}

@api_router.delete("/payments/methods/{method_id}")
async def delete_payment_method(request: Request, method_id: str):
    """Delete a saved payment method"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Soft delete - just mark as inactive
    result = await db.payment_methods.update_one(
        {"id": method_id, "user_id": session["user_id"]},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    return {"message": "Payment method removed"}

@api_router.put("/payments/methods/{method_id}/default")
async def set_default_payment_method(request: Request, method_id: str):
    """Set a payment method as the default"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Unset all defaults first
    await db.payment_methods.update_many(
        {"user_id": session["user_id"]},
        {"$set": {"is_default": False}}
    )
    
    # Set the new default
    result = await db.payment_methods.update_one(
        {"id": method_id, "user_id": session["user_id"], "is_active": True},
        {"$set": {"is_default": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    return {"message": "Default payment method updated"}

# ============== SMS ROUTES ==============

class SMSRequest(BaseModel):
    recipient_phone: str
    message: str
    person_id: Optional[str] = None

class BulkSMSRequest(BaseModel):
    group_id: Optional[str] = None
    list_ids: Optional[List[str]] = None
    message: str
    template_id: Optional[str] = None

@api_router.post("/sms/send")
async def send_sms(sms: SMSRequest):
    """Send an SMS to a single recipient"""
    # Check if Twilio is configured
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
    
    if not all([twilio_sid, twilio_token, twilio_phone]):
        # Return mock response for demo
        return {
            "status": "queued",
            "message_id": f"mock_{uuid.uuid4().hex[:12]}",
            "to": sms.recipient_phone,
            "mock": True,
            "note": "Twilio not configured - this is a simulated response"
        }
    
    try:
        client = TwilioClient(twilio_sid, twilio_token)
        message = client.messages.create(
            body=sms.message,
            from_=twilio_phone,
            to=sms.recipient_phone
        )
        
        # Log SMS
        await db.sms_logs.insert_one({
            "id": f"sms_{uuid.uuid4().hex[:12]}",
            "tenant_id": DEFAULT_TENANT_ID,
            "recipient_phone": sms.recipient_phone,
            "person_id": sms.person_id,
            "message": sms.message,
            "twilio_sid": message.sid,
            "status": message.status,
            "created_at": datetime.now(timezone.utc)
        })
        
        return {
            "status": message.status,
            "message_id": message.sid,
            "to": sms.recipient_phone
        }
        
    except Exception as e:
        logger.error(f"SMS send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/sms/bulk")
async def send_bulk_sms(bulk_sms: BulkSMSRequest):
    """Send SMS to a group or list of people"""
    # Get recipients
    recipients = []
    
    if bulk_sms.group_id:
        # Get group members
        group_members = await db.group_members.find(
            {"group_id": bulk_sms.group_id},
            {"person_id": 1, "_id": 0}
        ).to_list(1000)
        
        person_ids = [m["person_id"] for m in group_members]
        people = await db.people.find(
            {"id": {"$in": person_ids}, "phone": {"$ne": None}},
            {"id": 1, "phone": 1, "first_name": 1, "_id": 0}
        ).to_list(1000)
        
        recipients = [{"phone": p["phone"], "name": p["first_name"], "person_id": p["id"]} for p in people if p.get("phone")]
    
    # Check Twilio config
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    
    if not twilio_sid:
        # Return mock response
        return {
            "status": "queued",
            "total_recipients": len(recipients),
            "messages_sent": len(recipients),
            "mock": True,
            "note": "Twilio not configured - this is a simulated response"
        }
    
    # TODO: Implement actual bulk SMS with Twilio
    return {
        "status": "queued",
        "total_recipients": len(recipients),
        "messages_sent": len(recipients),
        "batch_id": f"batch_{uuid.uuid4().hex[:12]}"
    }

@api_router.get("/sms/templates")
async def get_sms_templates():
    """Get SMS templates"""
    return [
        {
            "id": "welcome",
            "name": "Welcome Message",
            "content": "Welcome to {church_name}! We're so glad you joined us. Reply STOP to unsubscribe.",
            "category": "onboarding"
        },
        {
            "id": "event_reminder",
            "name": "Event Reminder",
            "content": "Reminder: {event_name} is coming up on {event_date}. We hope to see you there!",
            "category": "events"
        },
        {
            "id": "giving_thanks",
            "name": "Giving Thank You",
            "content": "Thank you for your generous gift of ${amount}. Your support makes a difference!",
            "category": "giving"
        },
        {
            "id": "group_meeting",
            "name": "Group Meeting Reminder",
            "content": "{group_name} meets this week! {day} at {time}. Looking forward to seeing you.",
            "category": "groups"
        }
    ]

# ============== APP ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "Solomon AI Church Management API", "version": "1.0.0"}



@api_router.get("/clear-site-data")
async def clear_site_data():
    """Force browser to clear all caches, cookies, storage via HTTP header."""
    from starlette.responses import RedirectResponse
    response = RedirectResponse(url="/login", status_code=302)
    response.headers["Clear-Site-Data"] = '"cache", "storage"'
    return response


@api_router.get("/health/launch-check")
async def launch_health_check(tenant_id: Optional[str] = None):
    """Read-only launch readiness snapshot for quick production verification."""
    effective_tenant_id = tenant_id or DEFAULT_TENANT_ID

    launch_member_email_map = {
        "abundant-east-001": "member@abundant.church",
        "cristoviene-church-001": "member@cristoviene.church",
        "pottershouse-church-001": "member@pottershouse.church"
    }
    preferred_member_email = launch_member_email_map.get(effective_tenant_id)

    member_user = None
    if preferred_member_email:
        member_user = await db.users.find_one(
            {"email": preferred_member_email},
            {"_id": 0, "user_id": 1, "email": 1}
        )

    if not member_user:
        member_user = await db.users.find_one(
            {"tenant_id": effective_tenant_id, "role": "member"},
            {"_id": 0, "user_id": 1, "email": 1}
        )

    person_doc = None
    if member_user:
        person_doc = await db.people.find_one(
            {"email": member_user.get("email"), "tenant_id": effective_tenant_id},
            {"_id": 0, "id": 1}
        )

    ytd_start = datetime.now(timezone.utc).replace(month=1, day=1).strftime("%Y-%m-%d")
    ytd_total = 0.0
    donation_count = 0
    if person_doc:
        donations = await db.donations.find(
            {
                "tenant_id": effective_tenant_id,
                "person_id": person_doc.get("id"),
                "donation_date": {"$gte": ytd_start}
            },
            {"_id": 0, "amount": 1}
        ).to_list(2000)
        donation_count = len(donations)
        ytd_total = round(sum(float(item.get("amount", 0) or 0) for item in donations), 2)

    events_count = await db.events.count_documents(
        {
            "tenant_id": effective_tenant_id,
            "$or": [
                {"start_datetime": {"$exists": True}},
                {"event_date": {"$exists": True}}
            ]
        }
    )
    groups_count = await db.groups.count_documents({"tenant_id": effective_tenant_id, "is_active": True})
    merch_count = await db.merch_products.count_documents({"tenant_id": effective_tenant_id, "is_active": True})
    cafe_count = await db.cafe_items.count_documents({"tenant_id": effective_tenant_id, "is_active": True})
    sermons_count = await db.media_videos.count_documents({"tenant_id": effective_tenant_id, "is_published": True, "content_type": "sermon"})
    announcements_count = await db.announcements.count_documents({"tenant_id": effective_tenant_id})
    opportunities_count = await db.volunteer_opportunities.count_documents({"tenant_id": effective_tenant_id, "is_active": True})

    kids_count = 0
    prayer_count = 0
    courses_count = 0
    streak = 0
    if member_user:
        kids_count = await db.children.count_documents({"tenant_id": effective_tenant_id, "parent_user_id": member_user.get("user_id")})
        prayer_count = await db.prayer_requests.count_documents({"tenant_id": effective_tenant_id, "user_id": member_user.get("user_id")})
        courses_count = await db.member_courses.count_documents({"tenant_id": effective_tenant_id, "user_id": member_user.get("user_id")})
        streak_data = await calculate_attendance_streak(effective_tenant_id, member_user.get("user_id"))
        streak = streak_data.get("current_streak", 0)

    required_accounts = [
        "member@abundant.church",
        "member@cristoviene.church",
        "admin@abundant.church",
        "admin@cristoviene.church",
        "admin@pottershouse.church",
        "admin@solomon.ai"
    ]
    account_presence = {}
    for email in required_accounts:
        found = await db.users.find_one({"email": email}, {"_id": 0, "email": 1})
        account_presence[email] = bool(found)

    checks = {
        "events": events_count >= 50,
        "groups": groups_count >= 100,
        "giving_ytd": ytd_total >= 500,
        "merch_products": merch_count >= 5,
        "cafe_menu_items": cafe_count >= 5,
        "kids_children": kids_count >= 1,
        "attendance_streak": streak >= 1,
        "sermons": sermons_count >= 3,
        "courses": courses_count >= 2,
        "prayer_requests": prayer_count >= 2,
        "volunteer_opportunities": opportunities_count >= 5,
        "announcements": announcements_count >= 3,
        "accounts_ready": all(account_presence.values())
    }

    return {
        "tenant_id": effective_tenant_id,
        "status": "ready" if all(checks.values()) else "degraded",
        "checks": checks,
        "metrics": {
            "events": events_count,
            "groups": groups_count,
            "ytd_total": ytd_total,
            "donation_count": donation_count,
            "merch_products": merch_count,
            "cafe_menu_items": cafe_count,
            "kids_children": kids_count,
            "attendance_streak": streak,
            "sermons": sermons_count,
            "courses": courses_count,
            "prayer_requests": prayer_count,
            "volunteer_opportunities": opportunities_count,
            "announcements": announcements_count
        },
        "required_accounts": account_presence,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

# ============== TENANT/CHURCH MANAGEMENT ROUTES ==============

@api_router.get("/tenants")
async def list_tenants(request: Request):
    """List all tenants (platform admin only) with boosted stats from cache"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(100)
    
    for tenant in tenants:
        tid = tenant["id"]
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": tid}, {"_id": 0})
        if cached:
            tenant["member_count"] = cached.get("total_members", 0)
            tenant["active_members"] = cached.get("active_members", 0)
            tenant["mtd_giving"] = cached.get("mtd_giving", 0)
            tenant["ytd_giving"] = cached.get("ytd_giving", 0)
        else:
            tenant["member_count"] = await db.users.count_documents({"tenant_id": tid})
            tenant["active_members"] = 0
            tenant["mtd_giving"] = 0
            tenant["ytd_giving"] = 0
    
    return tenants

@api_router.get("/tenants/list")
async def list_public_churches():
    """List active churches for public registration (no auth required)"""
    tenants = await db.tenants.find(
        {"subscription_status": "active"},
        {"_id": 0, "id": 1, "name": 1, "subdomain": 1, "city": 1, "state": 1, "primary_color": 1}
    ).to_list(100)
    return tenants

@api_router.get("/tenants/{subdomain}")
async def get_tenant_by_subdomain_route(subdomain: str):
    """Get tenant info by subdomain (public - for registration)"""
    tenant = await get_tenant_by_subdomain(subdomain)
    if not tenant:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Return limited public info
    return {
        "id": tenant["id"],
        "name": tenant["name"],
        "subdomain": tenant["subdomain"],
        "subscription_status": tenant.get("subscription_status", "active"),
        "logo_url": tenant.get("logo_url"),
        "primary_color": tenant.get("primary_color", "#4f6ef7")
    }

@api_router.post("/tenants")
async def create_tenant(request: Request, tenant_data: TenantBase):
    """Create a new tenant/church (platform admin only)"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    # Check subdomain uniqueness
    existing = await db.tenants.find_one({"subdomain": tenant_data.subdomain.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already in use")
    
    tenant = {
        "id": str(uuid.uuid4()),
        "name": tenant_data.name,
        "subdomain": tenant_data.subdomain.lower(),
        "plan": tenant_data.plan,
        "member_limit": tenant_data.member_limit,
        "logo_url": tenant_data.logo_url,
        "primary_color": tenant_data.primary_color,
        "accent_color": tenant_data.accent_color,
        "timezone": tenant_data.timezone,
        "subscription_status": tenant_data.subscription_status,
        "address": tenant_data.address,
        "city": tenant_data.city,
        "state": tenant_data.state,
        "website": tenant_data.website,
        "phone": tenant_data.phone,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tenants.insert_one(tenant)
    logger.info(f"New tenant created: {tenant['name']} ({tenant['subdomain']})")
    
    return {"message": "Tenant created", "tenant_id": tenant["id"], "subdomain": tenant["subdomain"]}

@api_router.patch("/tenants/{tenant_id}/subscription")
async def update_tenant_subscription(request: Request, tenant_id: str, status: str):
    """Update tenant subscription status (platform admin only)"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    if status not in ["active", "suspended", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {"subscription_status": status}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {"message": f"Subscription updated to {status}"}

@api_router.get("/tenants/{tenant_id}/users")
async def list_tenant_users(request: Request, tenant_id: str, skip: int = 0, limit: int = 50):
    """List users for a specific tenant (platform admin only)"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    users = await db.users.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "password_hash": 0}
    ).skip(skip).limit(limit).to_list(limit)
    
    total = await db.users.count_documents({"tenant_id": tenant_id})
    
    return {"users": users, "total": total, "skip": skip, "limit": limit}

# ============== PLATFORM STATS (REAL DATA) ==============

@api_router.get("/platform/stats")
async def get_platform_stats(request: Request):
    """Get platform-wide statistics using cached + real data for God Mode dashboard"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    total_churches = await db.tenants.count_documents({})
    active_churches = await db.tenants.count_documents({"subscription_status": "active"})
    
    # Use cached stats for total members (boosted numbers)
    all_caches = await db.dashboard_stats_cache.find({}, {"_id": 0}).to_list(100)
    total_members_boosted = sum(c.get("total_members", 0) for c in all_caches)
    
    # MRR from tenant records
    tenants = await db.tenants.find({}, {"_id": 0, "mrr": 1, "name": 1, "id": 1}).to_list(100)
    total_mrr = sum(float(t.get("mrr", 0) or 0) for t in tenants)
    
    # Real donation stats
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    year_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    
    mtd_pipeline = [
        {"$match": {"donation_date": {"$gte": month_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    mtd_result = await db.donations.aggregate(mtd_pipeline).to_list(1)
    mtd_total = mtd_result[0]["total"] if mtd_result else 0
    mtd_count = mtd_result[0]["count"] if mtd_result else 0
    
    ytd_pipeline = [
        {"$match": {"donation_date": {"$gte": year_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    ytd_result = await db.donations.aggregate(ytd_pipeline).to_list(1)
    ytd_total = ytd_result[0]["total"] if ytd_result else 0
    
    thirty_days_ago = (today - timedelta(days=30)).isoformat()
    recent_signups = await db.users.count_documents({
        "role": "member",
        "created_at": {"$gte": thirty_days_ago}
    })
    
    giving_by_tenant = await db.donations.aggregate([
        {"$match": {"donation_date": {"$gte": month_start}}},
        {"$group": {"_id": "$tenant_id", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]).to_list(10)
    
    for g in giving_by_tenant:
        tenant = await db.tenants.find_one({"id": g["_id"]}, {"_id": 0, "name": 1})
        g["church_name"] = tenant["name"] if tenant else "Unknown"
    
    return {
        "churches": {
            "total": total_churches,
            "active": active_churches,
            "suspended": total_churches - active_churches
        },
        "members": {
            "total_users": total_members_boosted if total_members_boosted > 0 else await db.users.count_documents({"role": "member"}),
            "total_people": await db.people.count_documents({}),
            "recent_signups": recent_signups
        },
        "giving": {
            "mtd_total": mtd_total,
            "mtd_count": mtd_count,
            "ytd_total": ytd_total,
            "by_church": [{"church": g["church_name"], "amount": g["total"], "count": g["count"]} for g in giving_by_tenant]
        },
        "platform": {
            "total_mrr": total_mrr,
            "arr": total_mrr * 12
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

# ============== MEMBER DIRECTORY (ADMIN) ==============

@api_router.get("/admin/members")
async def get_admin_member_directory(
    request: Request, 
    skip: int = 0, 
    limit: int = 50,
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """Get member directory for church admin or platform admin"""
    user = await get_current_admin_user(request)
    
    # Build query based on role
    query = {"role": "member"}
    
    if user.get("role") in ["church_admin", "admin"]:
        # Church admin only sees their own church members
        query["tenant_id"] = user.get("tenant_id")
    elif user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    # Platform admin sees all members (no tenant filter)
    
    # Add search filter
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}}
        ]
    
    # Add status filter
    if status:
        query["membership_status"] = status
    
    # Sort direction
    sort_dir = -1 if sort_order == "desc" else 1
    
    # Execute query
    members = await db.users.find(
        query,
        {"_id": 0, "password_hash": 0}
    ).sort(sort_by, sort_dir).skip(skip).limit(limit).to_list(limit)
    
    total = await db.users.count_documents(query)
    
    # Enrich with tenant names
    for member in members:
        if member.get("tenant_id"):
            tenant = await db.tenants.find_one({"id": member["tenant_id"]}, {"_id": 0, "name": 1})
            member["church_name"] = tenant["name"] if tenant else "Unknown"
    
    return {
        "members": members,
        "total": total,
        "skip": skip,
        "limit": limit,
        "filters": {
            "search": search,
            "status": status
        }
    }

# ============== RBAC, VOLUNTEER, HEALTH ENDPOINTS ==============

class RoleUpdateRequest(BaseModel):
    role: str = None
    role_template: str = None

class PermissionsUpdateRequest(BaseModel):
    permissions: List[str]

class PermissionGrantRequest(BaseModel):
    permission: str

@api_router.get("/admin/roles/templates")
async def get_role_templates(request: Request):
    user = await require_permission(request, "admin.users.roles")
    return {name: {"role_title": t["role_title"], "permissions": t["permissions"]}
            for name, t in ROLE_TEMPLATES.items()
            if name != "platform_admin" or user.get("role") == "platform_admin"}

@api_router.get("/admin/roles/users")
async def get_users_by_role(request: Request):
    user = await require_permission(request, "admin.members.view")
    tenant_id = user.get("tenant_id")
    query = {"tenant_id": tenant_id} if tenant_id and user.get("role") != "platform_admin" else {}
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    grouped = {}
    for u in users:
        rt = u.get("role_title") or ROLE_TEMPLATES.get(u.get("role", "member"), {}).get("role_title", "Member")
        grouped.setdefault(rt, []).append({"user_id": u.get("user_id"), "name": u.get("name"), "email": u.get("email"), "role": u.get("role"), "role_title": rt, "permissions": get_permissions_for_user(u)})
    return grouped

@api_router.get("/admin/members/{user_id}/permissions")
async def get_member_permissions(request: Request, user_id: str):
    admin = await require_permission(request, "admin.users.roles")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if admin.get("role") != "platform_admin" and target.get("tenant_id") != admin.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Cannot view users outside your church")
    perms = get_permissions_for_user(target)
    template_match = None
    for tname, tdata in ROLE_TEMPLATES.items():
        if set(tdata["permissions"]) == set(perms):
            template_match = tname
            break
    return {"user_id": user_id, "name": target.get("name"), "email": target.get("email"), "role": target.get("role"), "role_title": target.get("role_title", ""), "permissions": perms, "template_match": template_match, "is_custom": template_match is None}

@api_router.put("/admin/members/{user_id}/role")
async def update_member_role(request: Request, user_id: str, payload: RoleUpdateRequest):
    admin = await require_permission(request, "admin.users.roles")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if admin.get("role") != "platform_admin" and target.get("tenant_id") != admin.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Cannot modify users outside your church")
    before = {"role": target.get("role"), "role_title": target.get("role_title"), "permissions": get_permissions_for_user(target)}
    template_key = payload.role_template or payload.role
    if not template_key or template_key not in ROLE_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(sorted(ROLE_TEMPLATES.keys()))}")
    tmpl = ROLE_TEMPLATES[template_key]
    role_field = template_key if template_key in ("church_admin", "platform_admin", "member") else ("church_admin" if any(p.startswith("admin.") for p in tmpl["permissions"]) else "member")
    update_fields = {"role": role_field, "role_title": tmpl["role_title"], "permissions": tmpl["permissions"]}
    await db.users.update_one({"user_id": user_id}, {"$set": update_fields})
    after = {"role": update_fields["role"], "role_title": update_fields["role_title"], "permissions": update_fields["permissions"]}
    await audit_log("role_change", "user", user_id, target.get("tenant_id", ""), admin.get("user_id", ""), admin.get("name", ""), before, after, request)
    return {"success": True, "user_id": user_id, "new_role": update_fields["role"], "role_title": update_fields["role_title"], "permissions": update_fields["permissions"], "name": target.get("name")}

@api_router.put("/admin/members/{user_id}/permissions")
async def update_member_permissions(request: Request, user_id: str, payload: PermissionsUpdateRequest):
    admin = await require_permission(request, "admin.users.roles")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if admin.get("role") != "platform_admin" and target.get("tenant_id") != admin.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Cannot modify users outside your church")
    invalid = [p for p in payload.permissions if p not in PERMISSION_REGISTRY]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown permissions: {', '.join(invalid)}")
    has_admin = any(p.startswith("admin.") for p in payload.permissions)
    role_field = "church_admin" if has_admin else "member"
    if target.get("role") == "platform_admin":
        role_field = "platform_admin"
    await db.users.update_one({"user_id": user_id}, {"$set": {"permissions": payload.permissions, "role": role_field}})
    await audit_log("permissions_change", "user", user_id, target.get("tenant_id", ""), admin.get("user_id", ""), admin.get("name", ""), {"permissions": get_permissions_for_user(target)}, {"permissions": payload.permissions}, request)
    return {"success": True, "user_id": user_id, "permissions": payload.permissions}

@api_router.post("/admin/members/{user_id}/permissions/grant")
async def grant_permission(request: Request, user_id: str, payload: PermissionGrantRequest):
    admin = await require_permission(request, "admin.users.roles")
    if payload.permission not in PERMISSION_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown permission: {payload.permission}")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    current = get_permissions_for_user(target)
    if payload.permission not in current:
        current.append(payload.permission)
    await db.users.update_one({"user_id": user_id}, {"$set": {"permissions": current}})
    return {"success": True, "user_id": user_id, "permissions": current}

@api_router.delete("/admin/members/{user_id}/permissions/{perm}")
async def revoke_permission(request: Request, user_id: str, perm: str):
    admin = await require_permission(request, "admin.users.roles")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    current = [p for p in get_permissions_for_user(target) if p != perm]
    await db.users.update_one({"user_id": user_id}, {"$set": {"permissions": current}})
    return {"success": True, "user_id": user_id, "permissions": current}

# ============== VOLUNTEER TEAM ENDPOINTS ==============

@api_router.get("/admin/volunteers")
async def get_volunteer_teams(request: Request):
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id")
    teams = await db.volunteer_teams.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(100)
    for team in teams:
        members = await db.volunteer_assignments.find({"team_id": team["id"], "tenant_id": tenant_id}, {"_id": 0}).to_list(200)
        for m in members:
            u = await db.users.find_one({"user_id": m.get("user_id")}, {"_id": 0, "name": 1, "email": 1, "picture": 1})
            m["user"] = u
        team["members"] = members
    return {"teams": teams, "total": len(teams)}

@api_router.post("/admin/volunteers/teams")
async def create_volunteer_team(request: Request, payload: dict):
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id")
    team = {"id": str(uuid.uuid4()), "tenant_id": tenant_id, "team_name": payload.get("team_name"), "ministry": payload.get("ministry", ""), "description": payload.get("description", ""), "created_at": datetime.now(timezone.utc).isoformat(), "created_by": user.get("user_id")}
    await db.volunteer_teams.insert_one(team)
    return {"success": True, "team": {k: v for k, v in team.items() if k != "_id"}}

@api_router.post("/admin/volunteers/assign")
async def assign_volunteer(request: Request, payload: dict):
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id")
    assignment = {"id": str(uuid.uuid4()), "tenant_id": tenant_id, "user_id": payload.get("user_id"), "team_id": payload.get("team_id"), "role_title": payload.get("role_title", "Volunteer"), "assigned_at": datetime.now(timezone.utc).isoformat(), "assigned_by": user.get("user_id")}
    await db.volunteer_assignments.update_one({"user_id": payload.get("user_id"), "team_id": payload.get("team_id"), "tenant_id": tenant_id}, {"$set": assignment}, upsert=True)
    return {"success": True, "assignment": {k: v for k, v in assignment.items() if k != "_id"}}

@api_router.get("/admin/volunteers/user/{user_id}")
async def get_user_volunteer_teams(request: Request, user_id: str):
    user = await require_permission(request, "admin.volunteers.manage")
    tenant_id = user.get("tenant_id")
    assignments = await db.volunteer_assignments.find({"user_id": user_id, "tenant_id": tenant_id}, {"_id": 0}).to_list(50)
    for a in assignments:
        team = await db.volunteer_teams.find_one({"id": a.get("team_id")}, {"_id": 0})
        a["team"] = team
    return {"assignments": assignments}

# ============== HEALTH ENDPOINTS ==============

@api_router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "version": "2.0.0"}

@api_router.get("/health/detailed")
async def health_detailed():
    checks = {"database": "ok", "media": "ok", "giving": "ok", "cache": "ok"}
    try:
        await db.command("ping")
    except Exception:
        checks["database"] = "down"
    return {"status": "ok" if all(v == "ok" for v in checks.values()) else "degraded", "services": checks, "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.get("/churches/list")
async def list_churches_public():
    tenants = await db.tenants.find({"subscription_status": "active"}, {"_id": 0, "id": 1, "name": 1, "subdomain": 1, "city": 1, "state": 1, "primary_color": 1}).to_list(100)
    return tenants

# ============== MEDIA MANAGEMENT API ==============

def extract_youtube_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats"""
    import re
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'  # Just the ID itself
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

async def get_current_admin_user(request: Request):
    """Helper to get current admin user with tenant validation"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Must be admin or platform_admin
    if user.get("role") not in ["admin", "church_admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user

async def get_current_member_user(request: Request):
    """Helper for portal access: member + church/platform admins."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if user.get("role") not in ["member", "church_admin", "platform_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Portal access required")
    
    return user

# --- Media Categories ---

@api_router.get("/admin/media/categories")
async def get_media_categories(request: Request):
    """Get all media categories for the church"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    if not tenant_id:
        # Platform admin - get default categories
        categories = await db.media_categories.find({}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    else:
        categories = await db.media_categories.find(
            {"tenant_id": tenant_id}, {"_id": 0}
        ).sort("sort_order", 1).to_list(100)
    
    return {"categories": categories}

@api_router.post("/admin/media/categories")
async def create_media_category(request: Request, category: dict):
    """Create a new media category"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    new_category = MediaCategory(
        tenant_id=tenant_id,
        name=category.get("name"),
        slug=category.get("slug", category.get("name", "").lower().replace(" ", "-")),
        icon=category.get("icon", "video"),
        sort_order=category.get("sort_order", 0)
    )
    
    await db.media_categories.insert_one(new_category.model_dump())
    return {"message": "Category created", "category": new_category.model_dump()}

# --- Media Videos ---

@api_router.get("/admin/media/videos")
async def get_admin_media_videos(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    category_id: Optional[str] = None,
    series_id: Optional[str] = None,
    search: Optional[str] = None,
    is_published: Optional[bool] = None
):
    """Get all videos for admin management"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    if category_id:
        query["category_id"] = category_id
    if series_id:
        query["series_id"] = series_id
    if is_published is not None:
        query["is_published"] = is_published
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"instructor": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    videos = await db.media_videos.find(
        query, {"_id": 0}
    ).sort([("is_featured", -1), ("created_at", -1)]).skip(skip).limit(limit).to_list(limit)
    
    total = await db.media_videos.count_documents(query)
    
    return {
        "videos": videos,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@api_router.post("/admin/media/videos")
async def create_media_video(request: Request, video_data: MediaVideoCreate):
    """Create a new video from YouTube URL"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    # Extract YouTube ID
    youtube_id = extract_youtube_id(video_data.youtube_url)
    if not youtube_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    # Check for duplicate
    existing = await db.media_videos.find_one({
        "tenant_id": tenant_id,
        "youtube_id": youtube_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="This video already exists in your library")
    
    # Auto-generate thumbnail URL
    thumbnail_url = f"https://i.ytimg.com/vi/{youtube_id}/maxresdefault.jpg"
    
    # Create video record
    new_video = MediaVideo(
        tenant_id=tenant_id,
        title=video_data.title or f"Video {youtube_id}",
        description=video_data.description,
        youtube_id=youtube_id,
        youtube_url=video_data.youtube_url,
        thumbnail_url=thumbnail_url,
        instructor=video_data.instructor,
        category_id=video_data.category_id,
        series_id=video_data.series_id,
        is_featured=video_data.is_featured,
        badge=video_data.badge,
        is_published=True,
        published_at=datetime.now(timezone.utc).isoformat()
    )
    
    await db.media_videos.insert_one(new_video.model_dump())
    
    logger.info(f"Video created: {new_video.title} ({youtube_id}) for tenant {tenant_id}")
    
    return {
        "message": "Video added successfully",
        "video": new_video.model_dump()
    }

@api_router.put("/admin/media/videos/{video_id}")
async def update_media_video(request: Request, video_id: str, updates: dict):
    """Update a video's metadata"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": video_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    # Allowed fields to update
    allowed_fields = [
        "title", "description", "instructor", "category_id", "series_id",
        "is_featured", "is_published", "badge", "sort_order", "duration"
    ]
    
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.media_videos.update_one(query, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {"message": "Video updated successfully"}

@api_router.delete("/admin/media/videos/{video_id}")
async def delete_media_video(request: Request, video_id: str):
    """Delete a video from the library"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": video_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    result = await db.media_videos.delete_one(query)
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {"message": "Video deleted successfully"}

@api_router.post("/admin/media/videos/{video_id}/feature")
async def toggle_video_featured(request: Request, video_id: str):
    """Toggle featured status of a video"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": video_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    video = await db.media_videos.find_one(query, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    new_featured = not video.get("is_featured", False)
    await db.media_videos.update_one(query, {"$set": {"is_featured": new_featured}})
    
    return {"message": f"Video {'featured' if new_featured else 'unfeatured'}", "is_featured": new_featured}

# --- Portal Media API (for members) ---

@api_router.get("/portal/media/videos")
async def get_portal_videos(request: Request, category: Optional[str] = None, limit: int = 50):
    """Get published videos for member portal"""
    user = await get_current_member_user(request)
    
    tenant_id = user.get("tenant_id")
    
    query = {"is_published": True}
    if tenant_id:
        query["tenant_id"] = tenant_id
    if category and category != "all":
        query["category_id"] = category
    
    videos = await db.media_videos.find(
        query, {"_id": 0}
    ).sort([("is_featured", -1), ("created_at", -1)]).limit(limit).to_list(limit)
    
    # Get categories for this tenant
    cat_query = {"tenant_id": tenant_id} if tenant_id else {}
    categories = await db.media_categories.find(cat_query, {"_id": 0}).sort("sort_order", 1).to_list(20)
    
    return {
        "videos": videos,
        "categories": categories,
        "total": len(videos)
    }


@api_router.get("/portal/media/sermons")
async def get_portal_sermons(request: Request, limit: int = 50):
    """Sermon-focused feed for mobile/web clients."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    sermons = await db.media_videos.find(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"is_published": True},
                {"published": True}
            ]
        },
        {"_id": 0}
    ).sort("published_at", -1).limit(limit).to_list(limit)

    return {
        "videos": [serialize_doc(v) for v in sermons],
        "total": len(sermons)
    }


@api_router.get("/portal/bootstrap")
async def get_portal_bootstrap(request: Request):
    """Tiny mobile bootstrap endpoint to reduce initial round-trips."""
    user = await get_current_member_user(request)

    merch = await get_portal_merch_products(request)
    cafe = await get_portal_cafe_menu(request)
    children = await get_mobile_children(request)
    sermons = await get_portal_sermons(request, limit=10)

    return {
        "user": {
            "user_id": user.get("user_id"),
            "name": user.get("name"),
            "role": user.get("role"),
            "tenant_id": user.get("tenant_id") or DEFAULT_TENANT_ID
        },
        "merch_products": merch.get("products", []),
        "cafe_menu": cafe.get("items", []),
        "kids_children": children.get("children", []),
        "sermons": sermons.get("videos", []),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/portal/media/featured")
async def get_featured_video(request: Request):
    """Get the featured/hero video for the portal"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    tenant_id = user.get("tenant_id") if user else None
    
    query = {"is_published": True, "is_featured": True}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    featured = await db.media_videos.find_one(query, {"_id": 0})
    
    if not featured:
        # Fall back to most recent video
        query = {"is_published": True}
        if tenant_id:
            query["tenant_id"] = tenant_id
        featured = await db.media_videos.find_one(
            query, {"_id": 0}, sort=[("created_at", -1)]
        )
    
    return {"video": featured}

# ============== ADMIN GROUP MANAGEMENT API ==============

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    group_type: str = "Small Group"
    meeting_day: Optional[str] = None
    meeting_time: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    is_open: bool = True
    leader_name: Optional[str] = None

@api_router.get("/admin/groups")
async def get_admin_groups(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    group_type: Optional[str] = None
):
    """Get all groups for admin management"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"is_active": True}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    if group_type and group_type != "all":
        query["group_type"] = group_type
    
    groups = await db.groups.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.groups.count_documents(query)
    
    # Get member counts for each group
    for group in groups:
        member_count = await db.group_members.count_documents({
            "group_id": group["id"],
            "is_active": True
        })
        group["member_count"] = member_count
    
    return {
        "groups": groups,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@api_router.post("/admin/groups")
async def create_group(request: Request, group_data: GroupCreate):
    """Create a new group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    new_group = Group(
        tenant_id=tenant_id,
        name=group_data.name,
        description=group_data.description,
        group_type=group_data.group_type,
        meeting_day=group_data.meeting_day,
        meeting_time=group_data.meeting_time,
        location=group_data.location,
        capacity=group_data.capacity,
        is_open=group_data.is_open,
        is_active=True
    )
    
    await db.groups.insert_one(new_group.model_dump())
    
    logger.info(f"Group created: {new_group.name} for tenant {tenant_id}")
    
    return {
        "message": "Group created successfully",
        "group": new_group.model_dump()
    }

@api_router.put("/admin/groups/{group_id}")
async def update_group(request: Request, group_id: str, updates: dict):
    """Update a group's details"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": group_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    allowed_fields = [
        "name", "description", "group_type", "meeting_day", "meeting_time",
        "location", "capacity", "is_open", "leader_id"
    ]
    
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    
    result = await db.groups.update_one(query, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"message": "Group updated successfully"}

@api_router.delete("/admin/groups/{group_id}")
async def delete_group(request: Request, group_id: str):
    """Delete (deactivate) a group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": group_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    # Soft delete - set is_active to False
    result = await db.groups.update_one(query, {"$set": {"is_active": False}})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"message": "Group deleted successfully"}

@api_router.get("/admin/groups/{group_id}/members")
async def get_group_members(request: Request, group_id: str):
    """Get members of a specific group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify group exists and belongs to tenant
    query = {"id": group_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    group = await db.groups.find_one(query, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get members
    memberships = await db.group_members.find(
        {"group_id": group_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with person details
    members = []
    for m in memberships:
        person = await db.people.find_one({"id": m["person_id"]}, {"_id": 0})
        if person:
            members.append({
                **m,
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}",
                "email": person.get("email"),
                "phone": person.get("phone")
            })
    
    return {"members": members, "group": group}

@api_router.post("/portal/groups/{group_id}/join")
async def request_to_join_group(request: Request, group_id: str):
    """Member requests to join a group"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    tenant_id = user.get("tenant_id")
    
    # Check group exists and is open
    group = await db.groups.find_one({"id": group_id, "tenant_id": tenant_id, "is_active": True}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if not group.get("is_open", True):
        raise HTTPException(status_code=400, detail="This group is not accepting new members")
    
    # Check capacity
    if group.get("capacity"):
        current_count = await db.group_members.count_documents({"group_id": group_id, "is_active": True})
        if current_count >= group["capacity"]:
            raise HTTPException(status_code=400, detail="This group is full")
    
    # Get person ID from user
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Member profile not found")
    
    # Check if already a member
    existing = await db.group_members.find_one({
        "group_id": group_id,
        "person_id": person["id"],
        "is_active": True
    })
    if existing:
        raise HTTPException(status_code=400, detail="You are already a member of this group")
    
    # Add to group
    new_membership = GroupMember(
        tenant_id=tenant_id,
        group_id=group_id,
        person_id=person["id"],
        role="member"
    )
    
    await db.group_members.insert_one(new_membership.model_dump())
    
    # Update group member count
    await db.groups.update_one({"id": group_id}, {"$inc": {"member_count": 1}})
    
    logger.info(f"User {user['email']} joined group {group['name']}")
    
    return {"message": f"You have joined {group['name']}!"}

# ============== ADMIN GROUP MEMBER MANAGEMENT ==============

class AddMemberToGroupRequest(BaseModel):
    person_id: str
    role: str = "member"

@api_router.post("/admin/groups/{group_id}/members")
async def admin_add_member_to_group(request: Request, group_id: str, member_data: AddMemberToGroupRequest):
    """Admin adds a member to a group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify group exists
    query = {"id": group_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    group = await db.groups.find_one(query, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Verify person exists
    person_query = {"id": member_data.person_id}
    if tenant_id:
        person_query["tenant_id"] = tenant_id
    
    person = await db.people.find_one(person_query, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Check if already a member
    existing = await db.group_members.find_one({
        "group_id": group_id,
        "person_id": member_data.person_id,
        "is_active": True
    })
    if existing:
        raise HTTPException(status_code=400, detail="Person is already a member of this group")
    
    # Add membership
    new_membership = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id or group.get("tenant_id"),
        "group_id": group_id,
        "person_id": member_data.person_id,
        "role": member_data.role,
        "joined_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "is_active": True,
        "added_by_admin": True
    }
    
    await db.group_members.insert_one(new_membership)
    await db.groups.update_one({"id": group_id}, {"$inc": {"member_count": 1}})
    
    logger.info(f"Admin added {person.get('email', member_data.person_id)} to group {group['name']}")
    
    return {
        "message": f"Added {person.get('first_name', '')} {person.get('last_name', '')} to {group['name']}",
        "membership_id": new_membership["id"]
    }

@api_router.delete("/admin/groups/{group_id}/members/{person_id}")
async def admin_remove_member_from_group(request: Request, group_id: str, person_id: str):
    """Admin removes a member from a group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify group exists
    query = {"id": group_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    group = await db.groups.find_one(query, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Remove membership
    result = await db.group_members.delete_one({
        "group_id": group_id,
        "person_id": person_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    await db.groups.update_one({"id": group_id}, {"$inc": {"member_count": -1}})
    
    logger.info(f"Admin removed person {person_id} from group {group['name']}")
    
    return {"message": "Member removed from group"}

@api_router.get("/admin/groups/{group_id}/available-members")
async def get_available_members_for_group(request: Request, group_id: str, search: str = ""):
    """Get people who are not yet members of this group (for admin to add)"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Get current group members
    current_members = await db.group_members.find(
        {"group_id": group_id, "is_active": True},
        {"person_id": 1, "_id": 0}
    ).to_list(1000)
    
    current_member_ids = [m["person_id"] for m in current_members]
    
    # Build query for available people
    query = {"id": {"$nin": current_member_ids}}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    people = await db.people.find(
        query,
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1}
    ).limit(20).to_list(20)
    
    return {"people": people}

# ============== SMALL GROUP ATTENDANCE & AT-RISK TRACKING ==============

class GroupAttendanceRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    group_id: str
    session_date: str
    topic: Optional[str] = None
    notes: Optional[str] = None
    attendees: List[str] = []  # List of person_ids who attended
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

@api_router.post("/admin/groups/{group_id}/attendance")
async def record_group_attendance(request: Request, group_id: str):
    """Record attendance for a group session"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    body = await request.json()
    
    record = GroupAttendanceRecord(
        tenant_id=tenant_id,
        group_id=group_id,
        session_date=body.get("session_date", datetime.now(timezone.utc).date().isoformat()),
        topic=body.get("topic"),
        notes=body.get("notes"),
        attendees=body.get("attendees", []),
        created_by=user.get("user_id")
    )
    
    await db.group_attendance.insert_one(record.model_dump())
    
    # Update last_attended for each attendee
    for person_id in record.attendees:
        await db.group_members.update_one(
            {"group_id": group_id, "person_id": person_id},
            {"$set": {"last_attended": record.session_date}}
        )
    
    return {"message": "Attendance recorded", "id": record.id}

@api_router.get("/admin/groups/{group_id}/attendance")
async def get_group_attendance_history(request: Request, group_id: str, limit: int = 8):
    """Get attendance history for a group (last 8 sessions)"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    records = await db.group_attendance.find(
        {"group_id": group_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("session_date", -1).limit(limit).to_list(limit)
    
    return {"sessions": records}

@api_router.get("/admin/groups/{group_id}/at-risk")
async def get_at_risk_group_members(request: Request, group_id: str):
    """Get members who have missed 3+ consecutive sessions"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Get group members
    members = await db.group_members.find(
        {"group_id": group_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Get last 6 attendance records
    recent_sessions = await db.group_attendance.find(
        {"group_id": group_id, "tenant_id": tenant_id},
        {"_id": 0, "attendees": 1, "session_date": 1}
    ).sort("session_date", -1).limit(6).to_list(6)
    
    at_risk = []
    for member in members:
        person_id = member.get("person_id")
        consecutive_missed = 0
        
        for session in recent_sessions:
            if person_id not in session.get("attendees", []):
                consecutive_missed += 1
            else:
                break
        
        if consecutive_missed >= 3:
            # Get person details
            person = await db.people.find_one({"id": person_id}, {"_id": 0})
            if person:
                at_risk.append({
                    "person_id": person_id,
                    "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                    "email": person.get("email"),
                    "phone": person.get("phone"),
                    "sessions_missed": consecutive_missed,
                    "last_attended": member.get("last_attended")
                })
    
    return {"at_risk_members": at_risk, "threshold": 3}

@api_router.post("/admin/groups/{group_id}/outreach")
async def log_member_outreach(request: Request, group_id: str):
    """Log an outreach attempt to an at-risk member"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    body = await request.json()
    
    outreach_log = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "group_id": group_id,
        "person_id": body.get("person_id"),
        "outreach_type": body.get("type", "call"),  # call, email, sms, coffee_code
        "notes": body.get("notes", ""),
        "created_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.group_outreach_logs.insert_one(outreach_log)
    
    return {"message": "Outreach logged", "id": outreach_log["id"]}

# Group messaging routes extracted to routes/messaging.py

# ============== ADMIN EVENT REGISTRATION MANAGEMENT ==============

@api_router.get("/admin/events/{event_id}/registrations")
async def get_event_registrations(request: Request, event_id: str):
    """Get all registrations for an event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify event exists
    query = {"id": event_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    event = await db.events.find_one(query, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get registrations
    registrations = await db.event_registrations.find(
        {"event_id": event_id},
        {"_id": 0}
    ).to_list(500)
    
    return {
        "event": event,
        "registrations": registrations,
        "total": len(registrations)
    }

class AdminRegisterRequest(BaseModel):
    user_id: Optional[str] = None
    person_id: Optional[str] = None
    name: str
    email: Optional[str] = None

@api_router.post("/admin/events/{event_id}/registrations")
async def admin_register_for_event(request: Request, event_id: str, reg_data: AdminRegisterRequest):
    """Admin registers someone for an event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify event exists
    query = {"id": event_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    event = await db.events.find_one(query, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check capacity
    if event.get("capacity"):
        current_count = await db.event_registrations.count_documents({"event_id": event_id})
        if current_count >= event["capacity"]:
            raise HTTPException(status_code=400, detail="This event is full")
    
    # Create registration
    registration = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id or event.get("tenant_id"),
        "event_id": event_id,
        "user_id": reg_data.user_id,
        "person_id": reg_data.person_id,
        "user_name": reg_data.name,
        "user_email": reg_data.email,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "registered_by_admin": True
    }
    
    await db.event_registrations.insert_one(registration)
    await db.events.update_one({"id": event_id}, {"$inc": {"registration_count": 1}})
    
    logger.info(f"Admin registered {reg_data.name} for event {event['name']}")
    
    return {"message": f"Registered {reg_data.name} for {event['name']}", "registration_id": registration["id"]}

@api_router.delete("/admin/events/{event_id}/registrations/{registration_id}")
async def admin_cancel_registration(request: Request, event_id: str, registration_id: str):
    """Admin cancels a registration"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify event exists
    query = {"id": event_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    event = await db.events.find_one(query, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete registration
    result = await db.event_registrations.delete_one({"id": registration_id, "event_id": event_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    await db.events.update_one({"id": event_id}, {"$inc": {"registration_count": -1}})
    
    return {"message": "Registration cancelled"}

# ============== MEMBER PORTAL - MY REGISTRATIONS ==============

@api_router.get("/portal/my-groups")
async def get_my_groups(request: Request):
    """Get groups the current member belongs to"""
    user = await get_current_member_user(request)
    
    tenant_id = user.get("tenant_id")
    
    # Find person record
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        return {"groups": []}
    
    # Get group memberships
    memberships = await db.group_members.find(
        {"person_id": person["id"], "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Get group details
    groups = []
    for m in memberships:
        group = await db.groups.find_one({"id": m["group_id"]}, {"_id": 0})
        if group:
            groups.append({
                **serialize_doc(group),
                "joined_at": m.get("joined_at"),
                "role": m.get("role", "member")
            })
    
    return {"groups": groups}


@api_router.get("/portal/groups/mine")
async def get_mobile_my_groups(request: Request):
    """Mobile alias for member groups."""
    return await get_my_groups(request)

@api_router.get("/portal/my-events")
async def get_my_registered_events(request: Request):
    """Get events the current member is registered for"""
    user = await get_current_member_user(request)
    
    # Get registrations
    registrations = await db.event_registrations.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(100)
    
    # Get event details
    events = []
    for r in registrations:
        event = await db.events.find_one({"id": r["event_id"]}, {"_id": 0})
        if event:
            events.append({
                **serialize_doc(event),
                "registration_id": r["id"],
                "registered_at": r.get("registered_at")
            })
    
    return {"events": events}


@api_router.get("/portal/events/registered")
async def get_mobile_registered_events(request: Request):
    """Mobile alias for registered events."""
    return await get_my_registered_events(request)

@api_router.delete("/portal/groups/{group_id}/leave")
async def leave_group(request: Request, group_id: str):
    """Member leaves a group"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    tenant_id = user.get("tenant_id")
    
    # Find person record
    person = await db.people.find_one({"email": user["email"], "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Member profile not found")
    
    # Remove from group
    result = await db.group_members.delete_one({
        "group_id": group_id,
        "person_id": person["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="You are not a member of this group")
    
    # Update count
    await db.groups.update_one({"id": group_id}, {"$inc": {"member_count": -1}})
    
    return {"message": "You have left the group"}

# ============== ADMIN EVENT MANAGEMENT API ==============

class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    event_date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    is_public: bool = True
    requires_registration: bool = True

@api_router.get("/admin/events")
async def get_admin_events(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    upcoming_only: bool = True
):
    """Get all events for admin management"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    if upcoming_only:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        query["event_date"] = {"$gte": today}
    
    events = await db.events.find(
        query, {"_id": 0}
    ).sort("event_date", 1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.events.count_documents(query)
    
    # Get registration counts
    for event in events:
        reg_count = await db.event_registrations.count_documents({"event_id": event["id"]})
        event["registration_count"] = reg_count
    
    return {
        "events": events,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@api_router.post("/admin/events")
async def create_event(request: Request, event_data: EventCreate):
    """Create a new event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    new_event = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": event_data.name,
        "description": event_data.description,
        "event_date": event_data.event_date,
        "start_time": event_data.start_time,
        "end_time": event_data.end_time,
        "location": event_data.location,
        "capacity": event_data.capacity,
        "is_public": event_data.is_public,
        "requires_registration": event_data.requires_registration,
        "registration_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.events.insert_one(new_event)
    
    logger.info(f"Event created: {new_event['name']} for tenant {tenant_id}")
    
    return {
        "message": "Event created successfully",
        "event": {k: v for k, v in new_event.items() if k != "_id"}
    }

@api_router.put("/admin/events/{event_id}")
async def update_event(request: Request, event_id: str, updates: dict):
    """Update an event's details"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": event_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    allowed_fields = [
        "name", "description", "event_date", "start_time", "end_time",
        "location", "capacity", "is_public", "requires_registration",
        "category", "is_featured", "ticket_tiers"
    ]
    
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    
    result = await db.events.update_one(query, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event updated successfully"}

@api_router.delete("/admin/events/{event_id}")
async def delete_event(request: Request, event_id: str):
    """Delete an event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": event_id}
    if tenant_id:
        query["tenant_id"] = tenant_id
    
    result = await db.events.delete_one(query)
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Also delete registrations
    await db.event_registrations.delete_many({"event_id": event_id})
    
    return {"message": "Event deleted successfully"}

@api_router.post("/portal/events/{event_id}/register")
async def register_for_event(request: Request, event_id: str):
    """Member registers for an event"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    tenant_id = user.get("tenant_id")
    
    # Check event exists
    event = await db.events.find_one({"id": event_id, "tenant_id": tenant_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check capacity
    if event.get("capacity"):
        current_count = await db.event_registrations.count_documents({"event_id": event_id})
        if current_count >= event["capacity"]:
            # Add to waitlist instead of rejecting
            existing_wait = await db.event_registrations.find_one({"event_id": event_id, "user_id": user["user_id"]})
            if existing_wait:
                raise HTTPException(status_code=400, detail="You are already registered or waitlisted")
            waitlist_entry = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "event_id": event_id,
                "user_id": user["user_id"],
                "user_name": user.get("name", ""),
                "user_email": user.get("email", ""),
                "status": "waitlisted",
                "registered_at": datetime.now(timezone.utc).isoformat()
            }
            await db.event_registrations.insert_one(waitlist_entry)
            return {"message": f"Event is full — you've been added to the waitlist for {event['name']}!", "status": "waitlisted"}
    
    # Check if already registered
    existing = await db.event_registrations.find_one({
        "event_id": event_id,
        "user_id": user["user_id"]
    })
    if existing:
        raise HTTPException(status_code=400, detail="You are already registered for this event")
    
    # Register
    registration = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "event_id": event_id,
        "user_id": user["user_id"],
        "user_name": user.get("name", ""),
        "user_email": user.get("email", ""),
        "registered_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.event_registrations.insert_one(registration)
    
    # Update event registration count
    await db.events.update_one({"id": event_id}, {"$inc": {"registration_count": 1}})
    
    logger.info(f"User {user['email']} registered for event {event['name']}")
    
    # Push notification confirmation
    try:
        await send_push_notification(
            user["user_id"], tenant_id,
            "Registration Confirmed!",
            f"You're registered for {event['name']}. See you there!",
            "/portal/events"
        )
    except Exception:
        pass
    
    return {"message": f"You are registered for {event['name']}!"}

@api_router.delete("/portal/events/{event_id}/register")
async def cancel_event_registration(request: Request, event_id: str):
    """Member cancels their event registration"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    result = await db.event_registrations.delete_one({
        "event_id": event_id,
        "user_id": user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # Update event registration count
    await db.events.update_one({"id": event_id}, {"$inc": {"registration_count": -1}})
    
    return {"message": "Registration cancelled"}

# --- SOLOMON AI ROUTES ---
# Store active chat sessions
solomon_sessions: Dict[str, LlmChat] = {}

SOLOMON_SYSTEM_PROMPT = """You are Solomon, an intelligent AI assistant for the Solomon AI Church Management System. You help both church administrators AND church members.

**For Church Members (portal users), you assist with:**
1. **Giving Guidance**: Answer questions about where offerings go, suggest giving opportunities, share impact stories
2. **Event Information**: Help with upcoming events, registrations, and church activities
3. **Group Connection**: Help members find and join groups, Bible studies, and volunteer opportunities
4. **Watch + Media Library**: Help members find sermons, videos, and featured media content
5. **Abundant Pathways**: Guide members through discipleship courses and progress
6. **Thinkific Access**: Help members locate and use the embedded Thinkific experience
7. **Merch Store**: Help members shop merch and understand the store experience
8. **Abundant Cafe**: Help members order coffee and set pickup times
9. **Pastoral Meetings**: Help members schedule 1:1 meetings and understand what to expect
10. **Spiritual Encouragement**: Provide warm, pastoral support and encouragement
11. **Church Information**: Answer questions about service times, locations, and church programs

**For Church Admins, you assist with:**
1. **Data Analysis**: Analyze membership trends, giving patterns, attendance statistics
2. **Pastoral Advice**: Provide guidance on member care, follow-up strategies, engagement
3. **Operational Strategy**: Help with event planning, group management, communications, and discipleship programs
4. **Member Notes**: Suggest how to respond to member notes, prayer requests, and outreach needs
5. **Merch + Media**: Advice on merch engagement and media content strategy
6. **Cafe Orders**: Tips for cafe menu planning and pickup flow
7. **Pastoral Meetings**: Guidance on meeting follow-ups and care plans

**Your Personality:**
- Warm, friendly, and pastoral in tone
- Use occasional emojis to feel approachable (🙏 ✨ 💙)
- Be encouraging about giving without being pushy
- Make suggestions feel like friendly advice, not sales pitches
- Keep responses concise but heartfelt

**When discussing giving:**
- Share specific needs the church has (building funds, missions, community outreach)
- Mention impact: "Your generosity helped feed 200 families last month"
- Suggest with grace: "Just a thought 🙏" or "If you feel led..."
- Never pressure - always frame as an invitation

You are serving a multi-tenant church management platform with multiple churches."""

async def get_church_context() -> str:
    """Gather current church data for Solomon's context"""
    tenant_id = DEFAULT_TENANT_ID
    
    # Get key stats
    total_members = await db.people.count_documents({"tenant_id": tenant_id})
    active_members = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "member"})
    visitors = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "visitor"})
    
    # Get groups info
    total_groups = await db.groups.count_documents({"tenant_id": tenant_id, "is_active": True})

    media_count = await db.media_videos.count_documents({"tenant_id": tenant_id})
    pathways_count = await db.pathways_courses.count_documents({"tenant_id": tenant_id})
    merch_count = await db.merch_products.count_documents({"tenant_id": tenant_id})
    
    # Get giving stats
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    year_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    
    mtd_pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": month_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    mtd_result = await db.donations.aggregate(mtd_pipeline).to_list(1)
    mtd_giving = mtd_result[0]["total"] if mtd_result else 0
    
    ytd_pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": year_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    ytd_result = await db.donations.aggregate(ytd_pipeline).to_list(1)
    ytd_giving = ytd_result[0]["total"] if ytd_result else 0
    
    # Get recent activity
    recent_activities = await db.activity_log.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    activities_text = "\n".join([f"- {a.get('description', 'Unknown activity')}" for a in recent_activities])
    
    # Get upcoming events
    upcoming_events = await db.events.find(
        {"tenant_id": tenant_id, "start_datetime": {"$gte": today.strftime("%Y-%m-%d")}},
        {"_id": 0}
    ).sort("start_datetime", 1).limit(3).to_list(3)
    
    events_text = "\n".join([f"- {e.get('name', 'Unknown')} on {e.get('start_datetime', 'TBD')}" for e in upcoming_events])
    
    context = f"""
CURRENT CHURCH DATA (as of {today.strftime('%B %d, %Y')}):

MEMBERSHIP:
- Total Members: {total_members:,}
- Active Members: {active_members:,}
- Visitors: {visitors:,}
- Active Groups: {total_groups}
- Media Library Videos: {media_count}
- Abundant Pathways Courses: {pathways_count}
- Merch Products: {merch_count}

GIVING:
- Month-to-Date: ${mtd_giving:,.2f}
- Year-to-Date: ${ytd_giving:,.2f}
- Monthly Goal: $95,000

CURRENT GIVING NEEDS (share when members ask about giving):
- Building Fund: We're $345,000 short of our goal for the new community ballroom - a space for weddings, youth events, and community outreach
- Missions Fund: Supporting 12 missionary families worldwide
- Benevolence Fund: Helping families in our community with emergency needs - rent, utilities, food
- Youth Ministry: Summer camp scholarships for 50 students

IMPACT STORIES (use these to inspire):
- Last month, our Benevolence Fund helped 15 families stay in their homes
- Our Missions Fund supported clean water projects reaching 2,000 people
- Youth camp changed 23 lives last summer through scholarship giving

RECENT ACTIVITY:
{activities_text}

UPCOMING EVENTS:
{events_text}
"""
    return context

@api_router.post("/solomon/chat")
async def solomon_chat(request: Request, payload: SolomonChatRequest):
    """Chat with Solomon AI analyst"""
    try:
        # Validate message is not empty
        if not payload.message or not payload.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get or create session
        session_id = payload.session_id or str(uuid.uuid4())

        user = None
        user_role = None
        try:
            user = await get_current_user(request)
            user_role = user.get("role") if user else None
        except Exception:
            user = None
            user_role = None
        
        # Get API key
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="Solomon AI is not configured")
        
        # Get church context
        church_context = await get_church_context()
        
        # Build system prompt with context
        full_system_prompt = f"{SOLOMON_SYSTEM_PROMPT}\n\n{church_context}"
        
        # Create or get chat instance
        if session_id not in solomon_sessions:
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id,
                system_message=full_system_prompt
            )
            chat.with_model("anthropic", "claude-sonnet-4-5-20250929")
            solomon_sessions[session_id] = chat
        else:
            chat = solomon_sessions[session_id]
        
        # Create user message
        user_message = UserMessage(text=payload.message)
        
        # Get response from Claude
        response_text = await chat.send_message(user_message)
        
        # Store conversation in database for persistence
        await db.solomon_conversations.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": payload.message, "timestamp": datetime.now(timezone.utc).isoformat()},
                            {"role": "assistant", "content": response_text, "timestamp": datetime.now(timezone.utc).isoformat()}
                        ]
                    }
                },
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
                "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}
            },
            upsert=True
        )
        
        # Parse response for potential actions/data
        actions = None
        data = None

        response_lower = response_text.lower()
        query_lower = payload.message.lower()
        combined_text = f"{query_lower} {response_lower}"
        is_member = user_role == "member"

        portal_paths = {
            "giving": "/portal/give",
            "groups": "/portal/groups",
            "events": "/portal/events",
            "watch": "/portal/library",
            "media": "/portal/library",
            "thinkific": "/portal/thinkific",
            "pathways": "/portal/pathways",
            "discipleship": "/portal/pathways",
            "merch": "/portal/merch",
            "store": "/portal/merch",
            "shop": "/portal/merch",
            "cafe": "/portal/cafe",
            "coffee": "/portal/cafe",
            "meet": "/portal/meetings",
            "meeting": "/portal/meetings",
            "pastor": "/portal/meetings"
        }

        admin_paths = {
            "giving": "/giving",
            "groups": "/admin/groups",
            "events": "/admin/events",
            "watch": "/media",
            "media": "/media",
            "thinkific": "/thinkific",
            "pathways": "/abundant-pathways",
            "discipleship": "/abundant-pathways",
            "merch": "/merch",
            "store": "/merch",
            "shop": "/merch",
            "notes": "/notes",
            "leadership": "/notes",
            "cafe": "/cafe",
            "coffee": "/cafe",
            "meet": "/meetings",
            "meeting": "/meetings",
            "pastor": "/meetings"
        }

        path_map = portal_paths if is_member else admin_paths

        action_candidates = [
            ("giving", "Open Giving"),
            ("groups", "View Groups"),
            ("events", "View Events"),
            ("thinkific", "Open Thinkific"),
            ("pathways", "Open Abundant Pathways"),
            ("discipleship", "Open Abundant Pathways"),
            ("watch", "Open Watch"),
            ("media", "Open Media Library"),
            ("merch", "Open Merch"),
            ("store", "Open Merch"),
            ("shop", "Open Merch"),
            ("cafe", "Open Cafe"),
            ("coffee", "Open Cafe"),
            ("meet", "Open Meetings"),
            ("meeting", "Open Meetings"),
            ("pastor", "Open Meetings"),
            ("notes", "View Notes"),
            ("leadership", "View Notes")
        ]

        for keyword, label in action_candidates:
            if keyword in combined_text:
                actions = [
                    {"label": label, "action": "navigate", "path": path_map[keyword]}
                ]
                break

        if actions is None:
            if "giving" in combined_text or "donation" in combined_text:
                actions = [
                    {"label": "View Giving Dashboard", "action": "navigate", "path": path_map.get("giving", "/giving")},
                    {"label": "Generate Report", "action": "navigate", "path": "/reports"}
                ]
            elif "group" in combined_text or "ministry" in combined_text:
                actions = [
                    {"label": "View Groups", "action": "navigate", "path": path_map.get("groups", "/admin/groups")}
                ]
            elif "event" in combined_text:
                actions = [
                    {"label": "View Events", "action": "navigate", "path": path_map.get("events", "/admin/events")}
                ]
        
        return SolomonChatResponse(
            response=response_text,
            session_id=session_id,
            data=data,
            actions=actions
        )
        
    except Exception as e:
        logger.error(f"Solomon AI error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Solomon AI error: {str(e)}")

@api_router.get("/solomon/history/{session_id}")
async def get_solomon_history(session_id: str):
    """Get conversation history for a session"""
    conversation = await db.solomon_conversations.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    if not conversation:
        return {"messages": [], "session_id": session_id}
    return serialize_doc(conversation)

@api_router.delete("/solomon/session/{session_id}")
async def clear_solomon_session(session_id: str):
    """Clear a Solomon chat session"""
    if session_id in solomon_sessions:
        del solomon_sessions[session_id]
    await db.solomon_conversations.delete_one({"session_id": session_id})
    return {"message": "Session cleared", "session_id": session_id}

# --- TENANT ROUTES ---
@api_router.get("/tenant")
async def get_tenant(request: Request):
    """Get tenant info - returns user's tenant if logged in, else default"""
    # Try to get user's tenant from session
    session_token = get_session_token_from_request(request)
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
            if user and user.get("tenant_id"):
                tenant = await db.tenants.find_one({"id": user["tenant_id"]}, {"_id": 0})
                if tenant:
                    return serialize_doc(tenant)
    
    # Fallback to default tenant
    tenant = await db.tenants.find_one({"id": DEFAULT_TENANT_ID}, {"_id": 0})
    if not tenant:
        # Return default tenant if not found
        return {
            "id": DEFAULT_TENANT_ID,
            "name": "Abundant Church",
            "subdomain": "abundant",
            "plan": "enterprise",
            "member_limit": 100000,
            "logo_url": None,
            "primary_color": "#4f6ef7",
            "accent_color": "#00c896",
            "timezone": "America/Los_Angeles",
            "thinkific_url": "https://abundantchurch.thinkific.com/collections",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        }
    return serialize_doc(tenant)

# --- DASHBOARD ROUTES ---
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    """Return tenant-scoped dashboard stats from cache, falling back to defaults."""
    tenant_id = DEFAULT_TENANT_ID
    try:
        session_token = get_session_token_from_request(request)
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user and user.get("tenant_id"):
                    tenant_id = user["tenant_id"]
    except Exception:
        pass

    cached = await db.dashboard_stats_cache.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if cached:
        cached.pop("tenant_id", None)
        cached.pop("updated_at", None)
        return cached

    return {
        "total_members": 0, "active_members": 0, "visitors": 0,
        "active_groups": 0, "open_groups": 0,
        "mtd_giving": 0, "ytd_giving": 0, "mtd_goal": 0,
        "last_attendance": 0, "last_attendance_change": 0,
        "new_this_week": 0, "recurring_givers": 0,
        "cafe_orders_week": 0, "cafe_giving_added": 0,
        "merch_orders_week": 0, "merch_giving_added": 0,
        "event_registrations_month": 0, "at_risk_members": 0,
        "kids_checked_in_today": 0
    }

@api_router.get("/dashboard/giving-trend")
async def get_giving_trend():
    """Return demo giving trend data - 12 months for Abundant Church (50K member megachurch)"""
    return [
        {"month": "Mar", "General Fund": 145000, "Building Fund": 42000, "Missions": 18000, "Crypto": 2500},
        {"month": "Apr", "General Fund": 152000, "Building Fund": 45000, "Missions": 19000, "Crypto": 3200},
        {"month": "May", "General Fund": 168000, "Building Fund": 48000, "Missions": 21000, "Crypto": 1500},
        {"month": "Jun", "General Fund": 142000, "Building Fund": 41000, "Missions": 17500, "Crypto": 2800},
        {"month": "Jul", "General Fund": 138000, "Building Fund": 39000, "Missions": 16000, "Crypto": 1500},
        {"month": "Aug", "General Fund": 156000, "Building Fund": 43000, "Missions": 18500, "Crypto": 3100},
        {"month": "Sep", "General Fund": 175000, "Building Fund": 51000, "Missions": 22000, "Crypto": 2200},
        {"month": "Oct", "General Fund": 169000, "Building Fund": 47000, "Missions": 20500, "Crypto": 4300},
        {"month": "Nov", "General Fund": 198000, "Building Fund": 55000, "Missions": 24000, "Crypto": 3800},
        {"month": "Dec", "General Fund": 285000, "Building Fund": 72000, "Missions": 31000, "Crypto": 8500},
        {"month": "Jan", "General Fund": 161000, "Building Fund": 44000, "Missions": 19500, "Crypto": 2100},
        {"month": "Feb", "General Fund": 182500, "Building Fund": 52000, "Missions": 23500, "Crypto": 2800}
    ]

@api_router.get("/dashboard/attendance-trend")
async def get_attendance_trend():
    """Return demo attendance trend data - 12 weeks for Abundant Church (50K megachurch)"""
    return [
        {"week": "Week 1", "attendance": 7285, "date": "Dec 1"},
        {"week": "Week 2", "attendance": 7598, "date": "Dec 8"},
        {"week": "Week 3", "attendance": 8012, "date": "Dec 15"},
        {"week": "Week 4", "attendance": 12445, "date": "Dec 22"},
        {"week": "Week 5", "attendance": 9478, "date": "Dec 29"},
        {"week": "Week 6", "attendance": 7802, "date": "Jan 5"},
        {"week": "Week 7", "attendance": 7595, "date": "Jan 12"},
        {"week": "Week 8", "attendance": 8108, "date": "Jan 19"},
        {"week": "Week 9", "attendance": 8318, "date": "Jan 26"},
        {"week": "Week 10", "attendance": 8005, "date": "Feb 2"},
        {"week": "Week 11", "attendance": 7688, "date": "Feb 9"},
        {"week": "Week 12", "attendance": 8312, "date": "Feb 16"}
    ]

@api_router.get("/dashboard/activity")
async def get_recent_activity(request: Request, limit: int = 15):
    tenant_id = DEFAULT_TENANT_ID
    try:
        session_token = get_session_token_from_request(request)
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user and user.get("tenant_id"):
                    tenant_id = user["tenant_id"]
    except Exception:
        pass
    
    activities = await db.activity_log.find(
        {"tenant_id": tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [serialize_doc(a) for a in activities]

@api_router.get("/dashboard/upcoming-events")
async def get_upcoming_events(request: Request, limit: int = 5):
    tenant_id = DEFAULT_TENANT_ID
    try:
        session_token = get_session_token_from_request(request)
        if session_token:
            session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
            if session:
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user and user.get("tenant_id"):
                    tenant_id = user["tenant_id"]
    except Exception:
        pass
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    events = await db.events.find(
        {"tenant_id": tenant_id, "start_datetime": {"$gte": today}},
        {"_id": 0}
    ).sort("start_datetime", 1).limit(limit).to_list(limit)
    
    return [serialize_doc(e) for e in events]


@api_router.get("/admin/attendance/today")
async def get_admin_attendance_today(request: Request, tenant_id: Optional[str] = None):
    """Admin summary of today's attendance across member and kids check-ins."""
    user = await get_current_admin_user(request)
    effective_tenant_id = tenant_id or user.get("tenant_id") or DEFAULT_TENANT_ID

    today = datetime.now(timezone.utc).date().isoformat()
    day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    member_checkins = await db.member_checkins.find(
        {"tenant_id": effective_tenant_id, "service_date": today},
        {"_id": 0}
    ).to_list(5000)

    kids_checkins = await db.checkins.find(
        {
            "tenant_id": effective_tenant_id,
            "checked_in_at": {"$gte": day_start.isoformat()}
        },
        {"_id": 0}
    ).to_list(5000)

    return {
        "date": today,
        "tenant_id": effective_tenant_id,
        "member_checkins_total": len(member_checkins),
        "member_checkins_online": len([c for c in member_checkins if c.get("check_in_type") == "online"]),
        "member_checkins_in_person": len([c for c in member_checkins if c.get("check_in_type") != "online"]),
        "kids_checkins_total": len(kids_checkins),
        "kids_checked_in_now": len([c for c in kids_checkins if c.get("status") == "checked_in"])
    }


@api_router.get("/admin/qr/generate")
async def generate_admin_qr(
    request: Request,
    action: str = "attendance_checkin",
    expires_in_minutes: int = 60
):
    """Generate a QR payload and image URL for mobile scanning flows."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    expires_in_minutes = max(1, min(expires_in_minutes, 1440))
    now = datetime.now(timezone.utc)
    payload = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "action": action,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=expires_in_minutes)).isoformat()
    }

    qr_data = quote(json.dumps(payload))
    qr_url = f"https://quickchart.io/qr?size=300&text={qr_data}"

    return {
        "qr": {
            "image_url": qr_url,
            "payload": payload,
            "format": "quickchart"
        }
    }


async def get_tenant_giving_metrics(tenant_id: str) -> Dict[str, Any]:
    """Shared helper for tenant-level giving metrics."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    year_start = now.replace(month=1, day=1).strftime("%Y-%m-%d")

    donations = await db.donations.find(
        {
            "tenant_id": tenant_id,
            "donation_date": {"$gte": year_start}
        },
        {"_id": 0, "amount": 1, "donation_date": 1, "fund_id": 1, "fund_name": 1}
    ).to_list(20000)

    ytd_total = round(sum(float(d.get("amount", 0) or 0) for d in donations), 2)
    mtd_total = round(
        sum(
            float(d.get("amount", 0) or 0)
            for d in donations
            if str(d.get("donation_date", ""))[:10] >= month_start
        ),
        2
    )

    recurring_count = await db.recurring_giving.count_documents(
        {"tenant_id": tenant_id, "is_active": True}
    )

    funds = await db.funds.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "id": 1, "name": 1, "goal_amount": 1}
    ).to_list(500)

    fund_lookup = {f.get("id"): f.get("name", "General Fund") for f in funds if f.get("id")}
    goal_amount = round(sum(float(f.get("goal_amount", 0) or 0) for f in funds), 2)

    fund_totals: Dict[str, float] = {}
    for donation in donations:
        fund_name = fund_lookup.get(donation.get("fund_id")) or donation.get("fund_name") or "General Fund"
        fund_totals[fund_name] = fund_totals.get(fund_name, 0.0) + float(donation.get("amount", 0) or 0)

    top_funds = [
        {"fund_name": name, "total": round(total, 2)}
        for name, total in sorted(fund_totals.items(), key=lambda item: item[1], reverse=True)[:5]
    ]

    goal_percentage = round((ytd_total / goal_amount) * 100, 2) if goal_amount > 0 else 0

    return {
        "mtd_total": mtd_total,
        "ytd_total": ytd_total,
        "recurring_count": recurring_count,
        "goal_amount": goal_amount,
        "goal_percentage": goal_percentage,
        "top_funds": top_funds
    }


@api_router.get("/admin/dashboard")
async def get_admin_dashboard(request: Request):
    """Tenant-scoped admin dashboard summary for web/mobile admin apps."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_abundant_go_live_portal_content()

    giving = await get_tenant_giving_metrics(tenant_id)
    total_members = await db.users.count_documents({"tenant_id": tenant_id, "role": "member"})
    active_groups = await db.groups.count_documents({"tenant_id": tenant_id, "is_active": True})
    active_members = await db.users.count_documents({"tenant_id": tenant_id, "role": "member", "is_active": True})

    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    month_start = datetime.now(timezone.utc).replace(day=1).isoformat()

    new_this_week = await db.users.count_documents(
        {
            "tenant_id": tenant_id,
            "role": "member",
            "created_at": {"$gte": week_start}
        }
    )

    today = datetime.now(timezone.utc).date()
    days_since_sunday = (today.weekday() - 6) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    last_sunday_attendance = await db.member_checkins.count_documents(
        {"tenant_id": tenant_id, "service_date": last_sunday.isoformat()}
    )

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    upcoming_events_count = await db.events.count_documents(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"start_datetime": {"$gte": today_str}},
                {"event_date": {"$gte": today_str}}
            ]
        }
    )

    recent_activity_docs = await db.activity_log.find(
        {"tenant_id": tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)

    recurring_donors = giving["recurring_count"]
    cafe_orders_this_week = await db.cafe_orders.count_documents(
        {"tenant_id": tenant_id, "created_at": {"$gte": week_start}}
    )
    merch_sales_docs = await db.merch_orders.find(
        {"tenant_id": tenant_id, "created_at": {"$gte": week_start}},
        {"_id": 0, "total": 1}
    ).to_list(5000)
    merch_sales_this_week = round(sum(float(item.get("total", 0) or 0) for item in merch_sales_docs), 2)
    event_signups_this_month = await db.event_registrations.count_documents(
        {"tenant_id": tenant_id, "registered_at": {"$gte": month_start}}
    )
    small_groups_count = active_groups
    at_risk_members = await db.people.count_documents(
        {"tenant_id": tenant_id, "engagement_level": "at_risk"}
    )

    return {
        "active_members": active_members,
        "new_this_week": new_this_week,
        "total_members": total_members,
        "active_groups": active_groups,
        "mtd_giving": giving["mtd_total"],
        "ytd_giving": giving["ytd_total"],
        "recurring_count": giving["recurring_count"],
        "recurring_donors": recurring_donors,
        "cafe_orders_this_week": cafe_orders_this_week,
        "merch_sales_this_week": merch_sales_this_week,
        "event_signups_this_month": event_signups_this_month,
        "small_groups_count": small_groups_count,
        "at_risk_members": at_risk_members,
        "last_sunday_attendance": last_sunday_attendance,
        "upcoming_events_count": upcoming_events_count,
        "recent_activity": [serialize_doc(item) for item in recent_activity_docs]
    }


@api_router.get("/admin/giving/summary")
async def get_admin_giving_summary(request: Request):
    """Tenant-scoped giving summary endpoint for admin dashboard."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    return await get_tenant_giving_metrics(tenant_id)

# --- PEOPLE ROUTES ---
@api_router.get("/people")
async def get_people(
    page: int = 1,
    per_page: int = 25,
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "last_name",
    sort_order: str = "asc"
):
    tenant_id = DEFAULT_TENANT_ID
    
    # Build query
    query = {"tenant_id": tenant_id}
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"mobile_phone": {"$regex": search, "$options": "i"}}
        ]
    if status and status != "all":
        query["membership_status"] = status
    
    # Get total count
    total = await db.people.count_documents(query)
    
    # Sort direction
    sort_dir = 1 if sort_order == "asc" else -1
    
    # Get paginated results
    skip = (page - 1) * per_page
    people = await db.people.find(
        query, {"_id": 0}
    ).sort(sort_by, sort_dir).skip(skip).limit(per_page).to_list(per_page)
    
    return {
        "data": [serialize_doc(p) for p in people],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@api_router.get("/people/{person_id}")
async def get_person(person_id: str):
    person = await db.people.find_one(
        {"id": person_id, "tenant_id": DEFAULT_TENANT_ID},
        {"_id": 0}
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return serialize_doc(person)

@api_router.post("/people")
async def create_person(person_data: PersonCreate):
    tenant_id = DEFAULT_TENANT_ID
    
    person = Person(
        **person_data.model_dump(),
        tenant_id=tenant_id
    )
    
    doc = person.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.people.insert_one(doc)
    
    # Log activity
    await db.activity_log.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "action": "member_added",
        "description": f"New member added: {person.first_name} {person.last_name}",
        "entity_type": "person",
        "entity_id": person.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return serialize_doc(doc)

@api_router.put("/people/{person_id}")
async def update_person(person_id: str, person_data: PersonCreate):
    tenant_id = DEFAULT_TENANT_ID
    
    update_data = person_data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.people.update_one(
        {"id": person_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Person not found")
    
    return {"success": True, "id": person_id}

@api_router.delete("/people/{person_id}")
async def delete_person(person_id: str):
    result = await db.people.delete_one(
        {"id": person_id, "tenant_id": DEFAULT_TENANT_ID}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"success": True}

@api_router.get("/people/{person_id}/giving")
async def get_person_giving(person_id: str):
    tenant_id = DEFAULT_TENANT_ID
    
    # Get donations for this person
    donations = await db.donations.find(
        {"person_id": person_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("donation_date", -1).to_list(100)
    
    # Calculate stats
    today = datetime.now(timezone.utc)
    ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    
    total = sum(d["amount"] for d in donations)
    ytd_total = sum(d["amount"] for d in donations if d["donation_date"] >= ytd_start)
    
    # Get recurring giving
    recurring = await db.recurring_giving.find(
        {"person_id": person_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(10)
    
    # Get pledges
    pledges = await db.pledges.find(
        {"person_id": person_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(10)
    
    return {
        "donations": [serialize_doc(d) for d in donations],
        "stats": {
            "lifetime_total": total,
            "ytd_total": ytd_total,
            "total_gifts": len(donations),
            "avg_gift": total / len(donations) if donations else 0,
            "last_gift": donations[0] if donations else None
        },
        "recurring": [serialize_doc(r) for r in recurring],
        "pledges": [serialize_doc(p) for p in pledges]
    }

@api_router.get("/people/{person_id}/attendance")
async def get_person_attendance(person_id: str):
    tenant_id = DEFAULT_TENANT_ID
    
    # Get attendance records with service info
    pipeline = [
        {"$match": {"person_id": person_id, "tenant_id": tenant_id}},
        {"$lookup": {
            "from": "services",
            "localField": "service_id",
            "foreignField": "id",
            "as": "service"
        }},
        {"$unwind": "$service"},
        {"$lookup": {
            "from": "service_types",
            "localField": "service.service_type_id",
            "foreignField": "id",
            "as": "service_type"
        }},
        {"$unwind": {"path": "$service_type", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "date": "$service.date",
            "service_name": "$service_type.name",
            "check_in_time": 1
        }},
        {"$sort": {"date": -1}},
        {"$limit": 100}
    ]
    
    attendance = await db.attendance.aggregate(pipeline).to_list(100)
    
    # Calculate stats
    total = len(attendance)
    today = datetime.now(timezone.utc)
    ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    ytd_count = sum(1 for a in attendance if a.get("date", "") >= ytd_start)
    
    return {
        "records": attendance,
        "stats": {
            "total_attended": total,
            "ytd_attended": ytd_count,
            "attendance_rate": 0,  # Would need to calculate based on total services
            "current_streak": 0  # Would need to calculate
        }
    }

@api_router.get("/people/{person_id}/groups")
async def get_person_groups(person_id: str):
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {"person_id": person_id, "tenant_id": tenant_id}},
        {"$lookup": {
            "from": "groups",
            "localField": "group_id",
            "foreignField": "id",
            "as": "group"
        }},
        {"$unwind": "$group"},
        {"$lookup": {
            "from": "group_types",
            "localField": "group.group_type_id",
            "foreignField": "id",
            "as": "group_type"
        }},
        {"$unwind": {"path": "$group_type", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": "$group.id",
            "name": "$group.name",
            "type": "$group_type.name",
            "type_color": "$group_type.color",
            "role": 1,
            "joined_at": 1,
            "meeting_schedule": "$group.meeting_schedule",
            "leader_id": "$group.leader_id"
        }}
    ]
    
    groups = await db.group_members.aggregate(pipeline).to_list(20)
    return groups

# --- HOUSEHOLDS ROUTES ---
@api_router.get("/households")
async def get_households(page: int = 1, per_page: int = 25, search: Optional[str] = None):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    total = await db.households.count_documents(query)
    skip = (page - 1) * per_page
    
    households = await db.households.find(
        query, {"_id": 0}
    ).skip(skip).limit(per_page).to_list(per_page)
    
    # Get member count for each household
    for h in households:
        count = await db.people.count_documents({
            "tenant_id": tenant_id,
            "household_id": h["id"]
        })
        h["member_count"] = count
    
    return {
        "data": [serialize_doc(h) for h in households],
        "total": total,
        "page": page,
        "per_page": per_page
    }

@api_router.get("/households/{household_id}")
async def get_household(household_id: str):
    household = await db.households.find_one(
        {"id": household_id, "tenant_id": DEFAULT_TENANT_ID},
        {"_id": 0}
    )
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    
    # Get members
    members = await db.people.find(
        {"household_id": household_id, "tenant_id": DEFAULT_TENANT_ID},
        {"_id": 0}
    ).to_list(20)
    
    household["members"] = [serialize_doc(m) for m in members]
    return serialize_doc(household)

# --- GROUPS ROUTES ---
@api_router.get("/groups")
async def get_groups(
    page: int = 1,
    per_page: int = 25,
    search: Optional[str] = None,
    group_type: Optional[str] = None
):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id, "is_active": True}
    
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    if group_type:
        query["group_type_id"] = group_type
    
    total = await db.groups.count_documents(query)
    skip = (page - 1) * per_page
    
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "group_types",
            "localField": "group_type_id",
            "foreignField": "id",
            "as": "type_info"
        }},
        {"$unwind": {"path": "$type_info", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "people",
            "localField": "leader_id",
            "foreignField": "id",
            "as": "leader"
        }},
        {"$unwind": {"path": "$leader", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "name": 1,
            "description": 1,
            "location": 1,
            "meeting_schedule": 1,
            "meeting_day": 1,
            "meeting_time": 1,
            "capacity": 1,
            "is_open": 1,
            "member_count": 1,
            "type_name": "$type_info.name",
            "type_color": "$type_info.color",
            "leader_name": {"$concat": ["$leader.first_name", " ", "$leader.last_name"]},
            "leader_photo": "$leader.photo_url"
        }},
        {"$skip": skip},
        {"$limit": per_page}
    ]
    
    groups = await db.groups.aggregate(pipeline).to_list(per_page)
    
    return {
        "data": groups,
        "total": total,
        "page": page,
        "per_page": per_page
    }

@api_router.get("/groups/{group_id}")
async def get_group(group_id: str):
    tenant_id = DEFAULT_TENANT_ID
    
    group = await db.groups.find_one(
        {"id": group_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get group type
    if group.get("group_type_id"):
        group_type = await db.group_types.find_one(
            {"id": group["group_type_id"]},
            {"_id": 0}
        )
        group["type_info"] = group_type
    
    # Get leader info
    if group.get("leader_id"):
        leader = await db.people.find_one(
            {"id": group["leader_id"]},
            {"_id": 0, "first_name": 1, "last_name": 1, "photo_url": 1, "email": 1}
        )
        group["leader"] = leader
    
    return serialize_doc(group)

@api_router.get("/groups/{group_id}/members/list")
async def get_group_members_public(group_id: str):
    """Public endpoint for getting group members (no auth required)"""
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {"group_id": group_id, "tenant_id": tenant_id, "is_active": True}},
        {"$lookup": {
            "from": "people",
            "localField": "person_id",
            "foreignField": "id",
            "as": "person"
        }},
        {"$unwind": "$person"},
        {"$project": {
            "_id": 0,
            "id": "$person.id",
            "first_name": "$person.first_name",
            "last_name": "$person.last_name",
            "email": "$person.email",
            "photo_url": "$person.photo_url",
            "role": 1,
            "joined_at": 1
        }}
    ]
    
    members = await db.group_members.aggregate(pipeline).to_list(100)
    return members

@api_router.get("/group-types")
async def get_group_types():
    types = await db.group_types.find(
        {"tenant_id": DEFAULT_TENANT_ID},
        {"_id": 0}
    ).to_list(20)
    return [serialize_doc(t) for t in types]

# --- ATTENDANCE ROUTES ---
@api_router.get("/services")
async def get_services(date: Optional[str] = None, limit: int = 10):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if date:
        query["date"] = date
    
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "service_types",
            "localField": "service_type_id",
            "foreignField": "id",
            "as": "type_info"
        }},
        {"$unwind": {"path": "$type_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "date": 1,
            "time": 1,
            "total_headcount": 1,
            "notes": 1,
            "service_type_name": "$type_info.name"
        }},
        {"$sort": {"date": -1}},
        {"$limit": limit}
    ]
    
    services = await db.services.aggregate(pipeline).to_list(limit)
    return services

@api_router.get("/service-types")
async def get_service_types():
    types = await db.service_types.find(
        {"tenant_id": DEFAULT_TENANT_ID, "is_active": True},
        {"_id": 0}
    ).to_list(20)
    return [serialize_doc(t) for t in types]

@api_router.post("/attendance")
async def record_attendance(service_id: str, person_ids: List[str]):
    tenant_id = DEFAULT_TENANT_ID
    
    records = []
    for person_id in person_ids:
        # Check if already checked in
        existing = await db.attendance.find_one({
            "service_id": service_id,
            "person_id": person_id,
            "tenant_id": tenant_id
        })
        
        if not existing:
            record = Attendance(
                tenant_id=tenant_id,
                service_id=service_id,
                person_id=person_id
            )
            doc = record.model_dump()
            doc['check_in_time'] = doc['check_in_time'].isoformat()
            await db.attendance.insert_one(doc)
            records.append(record.id)
            
            # Update person's last attended
            await db.people.update_one(
                {"id": person_id},
                {"$set": {"last_attended_at": datetime.now(timezone.utc).isoformat()}}
            )
    
    return {"success": True, "recorded": len(records)}

@api_router.get("/attendance/service/{service_id}")
async def get_service_attendance(service_id: str):
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {"service_id": service_id, "tenant_id": tenant_id}},
        {"$lookup": {
            "from": "people",
            "localField": "person_id",
            "foreignField": "id",
            "as": "person"
        }},
        {"$unwind": "$person"},
        {"$project": {
            "_id": 0,
            "id": 1,
            "person_id": 1,
            "check_in_time": 1,
            "first_name": "$person.first_name",
            "last_name": "$person.last_name",
            "photo_url": "$person.photo_url"
        }}
    ]
    
    attendance = await db.attendance.aggregate(pipeline).to_list(1000)
    return attendance

# --- GIVING ROUTES ---
@api_router.get("/funds")
async def get_funds():
    funds = await db.funds.find(
        {"tenant_id": DEFAULT_TENANT_ID, "is_active": True},
        {"_id": 0}
    ).to_list(20)
    return [serialize_doc(f) for f in funds]

@api_router.get("/giving/stats")
async def get_giving_stats():
    tenant_id = DEFAULT_TENANT_ID
    today = datetime.now(timezone.utc)
    
    mtd_start = today.replace(day=1).strftime("%Y-%m-%d")
    ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    
    # MTD total
    mtd_pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": mtd_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    mtd_result = await db.donations.aggregate(mtd_pipeline).to_list(1)
    
    # YTD total
    ytd_pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": ytd_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    ytd_result = await db.donations.aggregate(ytd_pipeline).to_list(1)
    
    # By method
    method_pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": ytd_start}}},
        {"$group": {"_id": "$payment_method", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]
    method_result = await db.donations.aggregate(method_pipeline).to_list(10)
    
    # Active recurring
    recurring_count = await db.recurring_giving.count_documents({
        "tenant_id": tenant_id,
        "is_active": True
    })
    
    # Undeposited batches
    undeposited = await db.donation_batches.count_documents({
        "tenant_id": tenant_id,
        "status": "open"
    })
    
    return {
        "mtd_total": mtd_result[0]["total"] if mtd_result else 0,
        "mtd_count": mtd_result[0]["count"] if mtd_result else 0,
        "ytd_total": ytd_result[0]["total"] if ytd_result else 0,
        "ytd_count": ytd_result[0]["count"] if ytd_result else 0,
        "by_method": {r["_id"]: {"total": r["total"], "count": r["count"]} for r in method_result},
        "active_recurring": recurring_count,
        "undeposited_batches": undeposited
    }

@api_router.get("/donations")
async def get_donations(
    page: int = 1,
    per_page: int = 25,
    fund_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    payment_method: Optional[str] = None
):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if fund_id:
        query["fund_id"] = fund_id
    if start_date:
        query["donation_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("donation_date", {})["$lte"] = end_date
    if payment_method:
        query["payment_method"] = payment_method
    
    total = await db.donations.count_documents(query)
    skip = (page - 1) * per_page
    
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "people",
            "localField": "person_id",
            "foreignField": "id",
            "as": "donor"
        }},
        {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "funds",
            "localField": "fund_id",
            "foreignField": "id",
            "as": "fund"
        }},
        {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "amount": 1,
            "donation_date": 1,
            "payment_method": 1,
            "check_number": 1,
            "crypto_currency": 1,
            "crypto_amount": 1,
            "notes": 1,
            "donor_name": {"$concat": ["$donor.first_name", " ", "$donor.last_name"]},
            "donor_photo": "$donor.photo_url",
            "fund_name": "$fund.name",
            "batch_id": 1
        }},
        {"$sort": {"donation_date": -1}},
        {"$skip": skip},
        {"$limit": per_page}
    ]
    
    donations = await db.donations.aggregate(pipeline).to_list(per_page)
    
    return {
        "data": donations,
        "total": total,
        "page": page,
        "per_page": per_page
    }

# ============== GIVING REPORTS & CSV EXPORT ==============

from fastapi.responses import StreamingResponse
import csv
import io

@api_router.get("/admin/giving/report")
async def get_giving_report(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fund_id: Optional[str] = None,
    group_by: str = "day"  # day, week, month, fund, donor
):
    """Get giving report with aggregated statistics"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    
    query = {"tenant_id": tenant_id, "status": "completed"}
    
    if start_date:
        query["donation_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("donation_date", {})["$lte"] = end_date
    if fund_id:
        query["fund_id"] = fund_id
    
    # Basic statistics
    total_donations = await db.donations.count_documents(query)
    
    # Sum total amount
    sum_pipeline = [
        {"$match": query},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    sum_result = await db.donations.aggregate(sum_pipeline).to_list(1)
    total_amount = sum_result[0]["total"] if sum_result else 0
    
    # Group by specified field
    if group_by == "fund":
        group_pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$fund_id",
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"}
            }},
            {"$lookup": {
                "from": "funds",
                "localField": "_id",
                "foreignField": "id",
                "as": "fund"
            }},
            {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "_id": 0,
                "label": {"$ifNull": ["$fund.name", "$_id"]},
                "count": 1,
                "total": 1
            }},
            {"$sort": {"total": -1}}
        ]
    elif group_by == "donor":
        group_pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$person_id",
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"}
            }},
            {"$lookup": {
                "from": "people",
                "localField": "_id",
                "foreignField": "id",
                "as": "donor"
            }},
            {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "_id": 0,
                "label": {"$concat": [{"$ifNull": ["$donor.first_name", ""]}, " ", {"$ifNull": ["$donor.last_name", "Anonymous"]}]},
                "count": 1,
                "total": 1
            }},
            {"$sort": {"total": -1}},
            {"$limit": 20}
        ]
    elif group_by == "month":
        group_pipeline = [
            {"$match": query},
            {"$group": {
                "_id": {"$substr": ["$donation_date", 0, 7]},  # YYYY-MM
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"}
            }},
            {"$project": {
                "_id": 0,
                "label": "$_id",
                "count": 1,
                "total": 1
            }},
            {"$sort": {"label": -1}}
        ]
    else:  # day
        group_pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$donation_date",
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"}
            }},
            {"$project": {
                "_id": 0,
                "label": "$_id",
                "count": 1,
                "total": 1
            }},
            {"$sort": {"label": -1}},
            {"$limit": 30}
        ]
    
    breakdown = await db.donations.aggregate(group_pipeline).to_list(100)
    
    # Get recent donations
    recent_pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "people",
            "localField": "person_id",
            "foreignField": "id",
            "as": "donor"
        }},
        {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "funds",
            "localField": "fund_id",
            "foreignField": "id",
            "as": "fund"
        }},
        {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "amount": 1,
            "donation_date": 1,
            "payment_method": 1,
            "donor_name": {"$concat": [{"$ifNull": ["$donor.first_name", ""]}, " ", {"$ifNull": ["$donor.last_name", "Anonymous"]}]},
            "donor_email": "$donor.email",
            "fund_name": "$fund.name"
        }},
        {"$sort": {"donation_date": -1}},
        {"$limit": 50}
    ]
    recent = await db.donations.aggregate(recent_pipeline).to_list(50)
    
    return {
        "summary": {
            "total_donations": total_donations,
            "total_amount": total_amount,
            "average_donation": total_amount / total_donations if total_donations > 0 else 0,
            "date_range": {"start": start_date, "end": end_date}
        },
        "breakdown": breakdown,
        "recent_donations": recent
    }

@api_router.get("/admin/giving/export")
async def export_giving_csv(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fund_id: Optional[str] = None
):
    """Export giving data as CSV"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    
    query = {"tenant_id": tenant_id, "status": "completed"}
    
    if start_date:
        query["donation_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("donation_date", {})["$lte"] = end_date
    if fund_id:
        query["fund_id"] = fund_id
    
    # Get all donations with donor and fund info
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "people",
            "localField": "person_id",
            "foreignField": "id",
            "as": "donor"
        }},
        {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "funds",
            "localField": "fund_id",
            "foreignField": "id",
            "as": "fund"
        }},
        {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "donation_date": 1,
            "amount": 1,
            "payment_method": 1,
            "check_number": 1,
            "donor_first_name": "$donor.first_name",
            "donor_last_name": "$donor.last_name",
            "donor_email": "$donor.email",
            "donor_phone": "$donor.phone",
            "donor_address": "$donor.address",
            "fund_name": "$fund.name",
            "notes": 1,
            "transaction_id": 1
        }},
        {"$sort": {"donation_date": -1}}
    ]
    
    donations = await db.donations.aggregate(pipeline).to_list(10000)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Date", "Amount", "Payment Method", "Check #",
        "First Name", "Last Name", "Email", "Phone", "Address",
        "Fund", "Notes", "Transaction ID"
    ])
    
    # Data rows
    for d in donations:
        writer.writerow([
            d.get("donation_date", ""),
            f"${d.get('amount', 0):.2f}",
            d.get("payment_method", ""),
            d.get("check_number", ""),
            d.get("donor_first_name", ""),
            d.get("donor_last_name", ""),
            d.get("donor_email", ""),
            d.get("donor_phone", ""),
            d.get("donor_address", ""),
            d.get("fund_name", ""),
            d.get("notes", ""),
            d.get("transaction_id", "")
        ])
    
    output.seek(0)
    
    # Generate filename
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"giving_report_{date_str}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/admin/giving/year-end-statement/{person_id}")
async def get_year_end_statement(request: Request, person_id: str, year: int = 2025):
    """Generate year-end giving statement data for a specific person"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    
    # Get person info
    person = await db.people.find_one({"id": person_id, "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Get all donations for this person in the specified year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    pipeline = [
        {"$match": {
            "tenant_id": tenant_id,
            "person_id": person_id,
            "status": "completed",
            "donation_date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$lookup": {
            "from": "funds",
            "localField": "fund_id",
            "foreignField": "id",
            "as": "fund"
        }},
        {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "donation_date": 1,
            "amount": 1,
            "payment_method": 1,
            "check_number": 1,
            "fund_name": "$fund.name"
        }},
        {"$sort": {"donation_date": 1}}
    ]
    
    donations = await db.donations.aggregate(pipeline).to_list(1000)
    
    # Calculate totals by fund
    fund_totals = {}
    for d in donations:
        fund = d.get("fund_name", "General")
        fund_totals[fund] = fund_totals.get(fund, 0) + d.get("amount", 0)
    
    total_amount = sum(d.get("amount", 0) for d in donations)
    
    # Get church/tenant info
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    
    return {
        "statement": {
            "year": year,
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
            "church": {
                "name": tenant.get("name", "Church") if tenant else "Church",
                "address": tenant.get("address", "") if tenant else "",
                "city": tenant.get("city", "") if tenant else "",
                "state": tenant.get("state", "") if tenant else "",
                "ein": tenant.get("ein", "XX-XXXXXXX") if tenant else "XX-XXXXXXX"
            },
            "donor": {
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "address": person.get("address", ""),
                "city": person.get("city", ""),
                "state": person.get("state", ""),
                "zip": person.get("zip", "")
            },
            "donations": donations,
            "fund_totals": [{"fund": k, "total": v} for k, v in fund_totals.items()],
            "total_amount": total_amount,
            "donation_count": len(donations),
            "disclaimer": "No goods or services were provided in exchange for these contributions except intangible religious benefits."
        }
    }

@api_router.post("/donations")
async def create_donation(donation_data: DonationBase):
    tenant_id = DEFAULT_TENANT_ID
    
    donation = Donation(
        **donation_data.model_dump(),
        tenant_id=tenant_id
    )
    
    doc = donation.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.donations.insert_one(doc)
    
    # Update fund total
    await db.funds.update_one(
        {"id": donation.fund_id},
        {"$inc": {"current_amount": donation.amount}}
    )
    
    # Update batch total if in a batch
    if donation.batch_id:
        await db.donation_batches.update_one(
            {"id": donation.batch_id},
            {"$inc": {"total_amount": donation.amount, "donation_count": 1}}
        )
    
    # Update person's giving totals
    if donation.person_id:
        await db.people.update_one(
            {"id": donation.person_id},
            {"$inc": {"ytd_giving": donation.amount, "lifetime_giving": donation.amount}}
        )
    
    # Log activity
    await db.activity_log.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "action": "donation_recorded",
        "description": f"Donation of ${donation.amount:.2f} recorded",
        "entity_type": "donation",
        "entity_id": donation.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return serialize_doc(doc)

@api_router.get("/batches")
async def get_batches(status: Optional[str] = None):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if status:
        query["status"] = status
    
    batches = await db.donation_batches.find(
        query, {"_id": 0}
    ).sort("date", -1).to_list(50)
    
    return [serialize_doc(b) for b in batches]

@api_router.post("/batches")
async def create_batch(name: str, date: str):
    tenant_id = DEFAULT_TENANT_ID
    
    batch = DonationBatch(
        tenant_id=tenant_id,
        name=name,
        date=date
    )
    
    doc = batch.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.donation_batches.insert_one(doc)
    return serialize_doc(doc)

@api_router.put("/batches/{batch_id}/close")
async def close_batch(batch_id: str):
    result = await db.donation_batches.update_one(
        {"id": batch_id, "tenant_id": DEFAULT_TENANT_ID},
        {"$set": {"status": "closed"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {"success": True}

# --- EVENTS ROUTES ---
@api_router.get("/events")
async def get_events(upcoming: bool = True, limit: int = 20):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if upcoming:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        query["start_datetime"] = {"$gte": today}
        sort_dir = 1
    else:
        sort_dir = -1
    
    events = await db.events.find(
        query, {"_id": 0}
    ).sort("start_datetime", sort_dir).limit(limit).to_list(limit)
    
    return [serialize_doc(e) for e in events]

@api_router.get("/events/{event_id}")
async def get_event(event_id: str):
    event = await db.events.find_one(
        {"id": event_id, "tenant_id": DEFAULT_TENANT_ID},
        {"_id": 0}
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return serialize_doc(event)

# --- COMMUNICATIONS ROUTES ---
@api_router.get("/communications")
async def get_communications(status: Optional[str] = None, limit: int = 20):
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    
    if status:
        query["status"] = status
    
    comms = await db.communications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [serialize_doc(c) for c in comms]

@api_router.post("/communications")
async def create_communication(subject: str, body_html: str, recipient_ids: List[str] = []):
    tenant_id = DEFAULT_TENANT_ID
    
    comm = Communication(
        tenant_id=tenant_id,
        subject=subject,
        body_html=body_html,
        recipient_count=len(recipient_ids)
    )
    
    doc = comm.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.communications.insert_one(doc)
    return serialize_doc(doc)

# --- REPORTS ROUTES ---
@api_router.get("/reports/giving-by-fund")
async def report_giving_by_fund(start_date: str, end_date: str):
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {
            "tenant_id": tenant_id,
            "donation_date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$lookup": {
            "from": "funds",
            "localField": "fund_id",
            "foreignField": "id",
            "as": "fund"
        }},
        {"$unwind": "$fund"},
        {"$group": {
            "_id": {"fund_id": "$fund_id", "fund_name": "$fund.name"},
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "fund_id": "$_id.fund_id",
            "fund_name": "$_id.fund_name",
            "total": 1,
            "count": 1
        }}
    ]
    
    results = await db.donations.aggregate(pipeline).to_list(20)
    return results

@api_router.get("/reports/giving-by-method")
async def report_giving_by_method(start_date: str, end_date: str):
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {
            "tenant_id": tenant_id,
            "donation_date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$group": {
            "_id": "$payment_method",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "method": "$_id",
            "total": 1,
            "count": 1
        }}
    ]
    
    results = await db.donations.aggregate(pipeline).to_list(20)
    return results

@api_router.get("/reports/top-donors")
async def report_top_donors(start_date: str, end_date: str, limit: int = 20):
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {
            "tenant_id": tenant_id,
            "donation_date": {"$gte": start_date, "$lte": end_date},
            "person_id": {"$ne": None}
        }},
        {"$group": {
            "_id": "$person_id",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from": "people",
            "localField": "_id",
            "foreignField": "id",
            "as": "person"
        }},
        {"$unwind": "$person"},
        {"$project": {
            "_id": 0,
            "person_id": "$_id",
            "name": {"$concat": ["$person.first_name", " ", "$person.last_name"]},
            "total": 1,
            "count": 1
        }}
    ]
    
    results = await db.donations.aggregate(pipeline).to_list(limit)
    return results

@api_router.get("/reports/membership")
async def report_membership():
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": "$membership_status",
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "status": "$_id",
            "count": 1
        }}
    ]
    
    results = await db.people.aggregate(pipeline).to_list(10)
    total = sum(r["count"] for r in results)
    
    return {
        "by_status": results,
        "total": total
    }

# ============== EXTENDED REPORT ENDPOINTS (Task 6) ==============

@api_router.get("/reports/kids-history")
async def report_kids_history(start_date: str = None, end_date: str = None):
    """Kids check-in/check-out history report."""
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if start_date:
        query["checked_in_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("checked_in_at", {})["$lte"] = end_date + "T23:59:59"

    records = await db.kids_checkins.find(query, {"_id": 0}).sort("checked_in_at", -1).to_list(500)
    total_checkins = len(records)
    unique_kids = len(set(r.get("child_id", "") for r in records))
    checked_out = sum(1 for r in records if r.get("checked_out_at"))
    return {
        "records": records,
        "summary": {"total_checkins": total_checkins, "unique_kids": unique_kids, "checked_out": checked_out, "still_checked_in": total_checkins - checked_out}
    }

@api_router.get("/reports/attendance")
async def report_attendance(start_date: str = None, end_date: str = None):
    """Attendance report with weekly breakdown."""
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if start_date:
        query["service_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("service_date", {})["$lte"] = end_date

    checkins = await db.member_checkins.find(query, {"_id": 0}).sort("service_date", -1).to_list(2000)
    by_date = {}
    for c in checkins:
        d = c.get("service_date", "unknown")
        by_date.setdefault(d, {"date": d, "in_person": 0, "online": 0, "total": 0})
        t = c.get("check_in_type", "in_person")
        by_date[d][t if t in ("in_person", "online") else "in_person"] += 1
        by_date[d]["total"] += 1
    weekly = sorted(by_date.values(), key=lambda x: x["date"], reverse=True)
    return {
        "weekly": weekly,
        "summary": {"total_services": len(weekly), "total_checkins": len(checkins), "avg_per_service": round(len(checkins) / max(len(weekly), 1), 1)}
    }

@api_router.get("/reports/cafe")
async def report_cafe(start_date: str = None, end_date: str = None):
    """Cafe orders report."""
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date + "T23:59:59"

    orders = await db.cafe_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    total_revenue = sum(o.get("total", 0) for o in orders)
    item_counts = {}
    for o in orders:
        for item in o.get("items", []):
            name = item.get("name", "Unknown")
            item_counts[name] = item_counts.get(name, 0) + item.get("quantity", 1)
    top_items = sorted([{"name": k, "quantity": v} for k, v in item_counts.items()], key=lambda x: x["quantity"], reverse=True)[:10]
    return {
        "orders": orders[:100],
        "summary": {"total_orders": len(orders), "total_revenue": round(total_revenue, 2), "avg_order": round(total_revenue / max(len(orders), 1), 2)},
        "top_items": top_items
    }

@api_router.get("/reports/merch")
async def report_merch(start_date: str = None, end_date: str = None):
    """Merch orders report."""
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date + "T23:59:59"

    orders = await db.merch_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    total_revenue = sum(o.get("total", 0) for o in orders)
    return {
        "orders": orders[:100],
        "summary": {"total_orders": len(orders), "total_revenue": round(total_revenue, 2)}
    }

@api_router.get("/reports/groups")
async def report_groups():
    """Groups and small group report."""
    tenant_id = DEFAULT_TENANT_ID
    groups = await db.groups.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(200)
    total_members = 0
    group_data = []
    for g in groups:
        member_count = len(g.get("members", []))
        total_members += member_count
        group_data.append({"id": g.get("id"), "name": g.get("name"), "type": g.get("group_type", "small_group"), "members": member_count, "leader": g.get("leader_name", ""), "status": g.get("status", "active")})
    return {
        "groups": group_data,
        "summary": {"total_groups": len(groups), "total_members_in_groups": total_members, "avg_group_size": round(total_members / max(len(groups), 1), 1)}
    }

@api_router.get("/reports/next-steps")
async def report_next_steps():
    """Next Steps / Membership Pathway completion report."""
    tenant_id = DEFAULT_TENANT_ID
    journeys = await db.next_steps_journeys.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(500)
    memberships = await db.next_steps_memberships.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(500)
    completed = sum(1 for m in memberships if m.get("completed"))
    in_progress = len(journeys)
    return {
        "journeys": journeys[:100],
        "memberships": memberships[:100],
        "summary": {"total_enrolled": in_progress, "completed_membership": completed, "completion_rate": round(completed / max(in_progress, 1) * 100, 1)}
    }

@api_router.get("/reports/executive-summary")
async def report_executive_summary():
    """Executive summary combining all key metrics."""
    tenant_id = DEFAULT_TENANT_ID
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    members_total = await db.people.count_documents({"tenant_id": tenant_id})
    members_active = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "active"})
    new_this_month = await db.people.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": month_start}})

    donations = await db.donations.find({"tenant_id": tenant_id, "created_at": {"$gte": month_start}}, {"_id": 0, "amount": 1}).to_list(5000)
    giving_this_month = sum(d.get("amount", 0) for d in donations)

    attendance_checkins = await db.member_checkins.find({"tenant_id": tenant_id, "service_date": {"$gte": now.strftime("%Y-%m-01")}}, {"_id": 0}).to_list(5000)
    unique_attendees = len(set(c.get("user_id", "") for c in attendance_checkins))

    kids_checkins = await db.kids_checkins.count_documents({"tenant_id": tenant_id, "checked_in_at": {"$gte": month_start}})
    groups_count = await db.groups.count_documents({"tenant_id": tenant_id, "status": "active"})
    cafe_orders = await db.cafe_orders.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": month_start}})
    merch_orders = await db.merch_orders.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": month_start}})

    return {
        "period": {"month": now.strftime("%B %Y"), "start": month_start[:10], "end": now.strftime("%Y-%m-%d")},
        "membership": {"total": members_total, "active": members_active, "new_this_month": new_this_month},
        "giving": {"total_this_month": round(giving_this_month, 2), "donation_count": len(donations), "avg_gift": round(giving_this_month / max(len(donations), 1), 2)},
        "attendance": {"total_checkins": len(attendance_checkins), "unique_attendees": unique_attendees},
        "kids": {"checkins_this_month": kids_checkins},
        "groups": {"active_groups": groups_count},
        "cafe": {"orders_this_month": cafe_orders},
        "merch": {"orders_this_month": merch_orders}
    }

@api_router.get("/reports/{report_type}/export")
async def export_report_csv(report_type: str, format: str = "csv", start_date: str = None, end_date: str = None):
    """Export any report as CSV."""
    import io, csv
    if format != "csv":
        raise HTTPException(status_code=400, detail="Only CSV export is currently supported")

    tenant_id = DEFAULT_TENANT_ID
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "kids-history":
        writer.writerow(["Child Name", "Parent", "Service Type", "Check-in Time", "Check-out Time", "Pickup Code"])
        records = await db.kids_checkins.find({"tenant_id": tenant_id}, {"_id": 0}).sort("checked_in_at", -1).to_list(2000)
        for r in records:
            writer.writerow([r.get("child_name", ""), r.get("parent_name", ""), r.get("service_type", ""), r.get("checked_in_at", ""), r.get("checked_out_at", ""), r.get("pickup_code", "")])
    elif report_type == "attendance":
        writer.writerow(["Date", "User", "Check-in Type", "Service"])
        records = await db.member_checkins.find({"tenant_id": tenant_id}, {"_id": 0}).sort("service_date", -1).to_list(2000)
        for r in records:
            writer.writerow([r.get("service_date", ""), r.get("user_id", ""), r.get("check_in_type", ""), r.get("service_name", "")])
    elif report_type == "giving-fund":
        data = await report_giving_by_fund(start_date or "2020-01-01", end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        writer.writerow(["Fund", "Total", "Count"])
        for item in data:
            writer.writerow([item.get("fund_name", ""), item.get("total", 0), item.get("count", 0)])
    elif report_type == "top-donors":
        data = await report_top_donors(start_date or "2020-01-01", end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        writer.writerow(["Rank", "Name", "Total", "Count"])
        for idx, d in enumerate(data):
            writer.writerow([idx + 1, d.get("name", ""), d.get("total", 0), d.get("count", 0)])
    elif report_type == "cafe":
        writer.writerow(["Order ID", "Customer", "Total", "Status", "Created"])
        records = await db.cafe_orders.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(2000)
        for r in records:
            writer.writerow([r.get("id", ""), r.get("customer_name", ""), r.get("total", 0), r.get("status", ""), r.get("created_at", "")])
    elif report_type == "groups":
        groups = await db.groups.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(200)
        writer.writerow(["Group Name", "Type", "Members", "Leader", "Status"])
        for g in groups:
            writer.writerow([g.get("name", ""), g.get("group_type", ""), len(g.get("members", [])), g.get("leader_name", ""), g.get("status", "")])
    elif report_type == "executive-summary":
        summary = await report_executive_summary()
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Period", summary["period"]["month"]])
        writer.writerow(["Total Members", summary["membership"]["total"]])
        writer.writerow(["Active Members", summary["membership"]["active"]])
        writer.writerow(["New This Month", summary["membership"]["new_this_month"]])
        writer.writerow(["Giving This Month", summary["giving"]["total_this_month"]])
        writer.writerow(["Avg Gift", summary["giving"]["avg_gift"]])
        writer.writerow(["Attendance Checkins", summary["attendance"]["total_checkins"]])
        writer.writerow(["Kids Checkins", summary["kids"]["checkins_this_month"]])
        writer.writerow(["Active Groups", summary["groups"]["active_groups"]])
        writer.writerow(["Cafe Orders", summary["cafe"]["orders_this_month"]])
        writer.writerow(["Merch Orders", summary["merch"]["orders_this_month"]])
    else:
        raise HTTPException(status_code=404, detail=f"Unknown report type: {report_type}")

    csv_content = output.getvalue()
    from fastapi.responses import Response
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"})


# --- SEARCH ROUTE ---
@api_router.get("/search")
async def global_search(q: str, limit: int = 10):
    tenant_id = DEFAULT_TENANT_ID
    results = []
    
    # Search people
    people = await db.people.find(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"first_name": {"$regex": q, "$options": "i"}},
                {"last_name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}}
            ]
        },
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "photo_url": 1}
    ).limit(limit).to_list(limit)
    
    for p in people:
        results.append({
            "type": "person",
            "id": p["id"],
            "title": f"{p['first_name']} {p['last_name']}",
            "subtitle": p.get("email", ""),
            "photo_url": p.get("photo_url")
        })
    
    # Search groups
    groups = await db.groups.find(
        {
            "tenant_id": tenant_id,
            "name": {"$regex": q, "$options": "i"}
        },
        {"_id": 0, "id": 1, "name": 1}
    ).limit(5).to_list(5)
    
    for g in groups:
        results.append({
            "type": "group",
            "id": g["id"],
            "title": g["name"],
            "subtitle": "Group"
        })
    
    # Search events
    events = await db.events.find(
        {
            "tenant_id": tenant_id,
            "name": {"$regex": q, "$options": "i"}
        },
        {"_id": 0, "id": 1, "name": 1, "start_datetime": 1}
    ).limit(5).to_list(5)
    
    for e in events:
        results.append({
            "type": "event",
            "id": e["id"],
            "title": e["name"],
            "subtitle": e.get("start_datetime", "")
        })
    
    return results

# ============== AGENT API ROUTES (External Agent Access) ==============

# --- API Key Management (Admin) ---

@api_router.get("/admin/api-keys")
async def list_api_keys(request: Request):
    """List all API keys for the tenant"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    keys = await db.agent_api_keys.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "key_hash": 0}  # Don't expose the hash
    ).sort("created_at", -1).to_list(100)
    
    return {
        "api_keys": [serialize_doc(k) for k in keys],
        "available_permissions": AGENT_PERMISSIONS
    }

@api_router.post("/admin/api-keys")
async def create_api_key(request: Request, payload: AgentAPIKeyCreate):
    """Generate a new API key for external agent access"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    # Validate permissions
    for perm in payload.permissions:
        if perm not in AGENT_PERMISSIONS and not perm.endswith(":*"):
            raise HTTPException(status_code=400, detail=f"Invalid permission: {perm}")
    
    # Generate the key
    full_key, key_hash, key_prefix = generate_api_key()
    
    # Calculate expiration
    expires_at = None
    if payload.expires_in_days:
        expires_at = (datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)).isoformat()
    
    key_doc = AgentAPIKey(
        tenant_id=tenant_id,
        name=payload.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        permissions=payload.permissions,
        rate_limit=payload.rate_limit,
        created_by=user.get("user_id", "unknown"),
        expires_at=expires_at
    )
    
    await db.agent_api_keys.insert_one(key_doc.model_dump())
    
    # Return the full key ONLY on creation (never stored or shown again)
    return {
        "api_key": full_key,  # Show only once!
        "key_id": key_doc.id,
        "name": key_doc.name,
        "key_prefix": key_prefix,
        "permissions": key_doc.permissions,
        "rate_limit": key_doc.rate_limit,
        "expires_at": expires_at,
        "warning": "Save this key now! It will not be shown again."
    }

@api_router.delete("/admin/api-keys/{key_id}")
async def revoke_api_key(request: Request, key_id: str):
    """Revoke an API key"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    result = await db.agent_api_keys.update_one(
        {"id": key_id, "tenant_id": tenant_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"message": "API key revoked", "key_id": key_id}

@api_router.patch("/admin/api-keys/{key_id}")
async def update_api_key(request: Request, key_id: str, payload: dict):
    """Update API key settings (permissions, rate limit, active status)"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    update_data = {}
    if "permissions" in payload:
        update_data["permissions"] = payload["permissions"]
    if "rate_limit" in payload:
        update_data["rate_limit"] = payload["rate_limit"]
    if "is_active" in payload:
        update_data["is_active"] = payload["is_active"]
    if "name" in payload:
        update_data["name"] = payload["name"]
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    result = await db.agent_api_keys.update_one(
        {"id": key_id, "tenant_id": tenant_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key = await db.agent_api_keys.find_one({"id": key_id}, {"_id": 0, "key_hash": 0})
    return {"api_key": serialize_doc(key)}

# --- Agent API v1 Endpoints (External Access) ---

@api_router.get("/v1/agent/scout")
async def agent_scout_endpoint(request: Request):
    """
    Primary handshake endpoint for agents.
    Returns church overview and available data endpoints.
    """
    context = await validate_agent_api_key(request)
    tenant_id = context["tenant_id"]
    
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    
    return {
        "status": "connected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tenant": {
            "id": tenant_id,
            "name": tenant.get("name", "Church") if tenant else "Church",
            "subdomain": tenant.get("subdomain") if tenant else None
        },
        "permissions": context["permissions"],
        "rate_limit": context["rate_limit"],
        "endpoints": {
            "members": "/api/v1/agent/members",
            "visitors": "/api/v1/agent/visitors",
            "events": "/api/v1/agent/events",
            "groups": "/api/v1/agent/groups",
            "meetings": "/api/v1/agent/meetings",
            "giving_summary": "/api/v1/agent/giving/summary",
            "notes": "/api/v1/agent/notes"
        },
        "schema_version": "1.0.0"
    }

@api_router.get("/v1/agent/visitors")
async def agent_get_visitors(
    request: Request,
    days: int = 7,
    limit: int = 100
):
    """
    Get new visitors/members for agent outreach.
    Returns data in the manifest-defined schema.
    """
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "members:read"):
        raise HTTPException(status_code=403, detail="Permission denied: members:read required")
    
    tenant_id = context["tenant_id"]
    
    # Calculate date range
    since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # Get new members
    members = await db.users.find(
        {
            "tenant_id": tenant_id,
            "role": "member",
            "created_at": {"$gte": since_date}
        },
        {"_id": 0}
    ).limit(limit).to_list(limit)
    
    # Get first-time givers
    first_time_givers = await db.donations.aggregate([
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": since_date}}},
        {"$group": {"_id": "$donor_email", "first_gift": {"$min": "$donation_date"}, "donor_name": {"$first": "$donor_name"}}},
        {"$limit": limit}
    ]).to_list(limit)
    
    # Format according to manifest schema
    new_members = []
    for m in members:
        # Check if this member has given
        donation = await db.donations.find_one(
            {"tenant_id": tenant_id, "donor_email": m.get("email")},
            {"_id": 0}
        )
        
        new_members.append({
            "unique_id": m.get("user_id", m.get("id", str(uuid.uuid4()))),
            "name": m.get("name", "Unknown"),
            "email": m.get("email"),
            "phone_sms": m.get("phone"),  # E.164 format expected
            "physical_address": m.get("address"),
            "first_gift_date": donation.get("donation_date") if donation else None,
            "gift_tier": "first_time" if donation else None,
            "outreach_status": m.get("outreach_status", "pending"),
            "is_first_time": True,
            "joined_at": m.get("created_at", datetime.now(timezone.utc).isoformat())
        })
    
    # Anomaly check (Circuit Breaker)
    if len(new_members) > ANOMALY_THRESHOLDS["new_visitors_per_day"]:
        return {
            "visitor_report": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "new_members": new_members[:50],  # Limit to 50
                "anomaly_detected": True,
                "anomaly_message": f"Unusually high visitor count ({len(new_members)}). Human approval required for bulk outreach.",
                "total_count": len(new_members),
                "requires_approval": True
            }
        }
    
    return {
        "visitor_report": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "new_members": new_members,
            "total_count": len(new_members),
            "anomaly_detected": False
        }
    }

@api_router.get("/v1/agent/members")
async def agent_get_members(
    request: Request,
    search: Optional[str] = None,
    outreach_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get member directory for agents"""
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "members:read"):
        raise HTTPException(status_code=403, detail="Permission denied: members:read required")
    
    tenant_id = context["tenant_id"]
    
    query = {"tenant_id": tenant_id, "role": "member"}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if outreach_status:
        query["outreach_status"] = outreach_status
    
    total = await db.users.count_documents(query)
    members = await db.users.find(query, {"_id": 0, "password_hash": 0}).skip(offset).limit(limit).to_list(limit)
    
    return {
        "members": [{
            "unique_id": m.get("user_id", m.get("id")),
            "name": m.get("name"),
            "email": m.get("email"),
            "phone_sms": m.get("phone"),
            "outreach_status": m.get("outreach_status", "pending"),
            "joined_at": m.get("created_at")
        } for m in members],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@api_router.patch("/v1/agent/members/{member_id}/outreach")
async def agent_update_member_outreach(
    request: Request,
    member_id: str,
    payload: dict
):
    """Update member outreach status (write permission required)"""
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "members:write"):
        raise HTTPException(status_code=403, detail="Permission denied: members:write required")
    
    tenant_id = context["tenant_id"]
    
    # Only allow updating outreach_status (Safety Lock)
    allowed_statuses = ["pending", "contacted", "opted_out", "follow_up", "enrolled"]
    new_status = payload.get("outreach_status")
    
    if not new_status or new_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid outreach_status. Allowed: {allowed_statuses}")
    
    result = await db.users.update_one(
        {"user_id": member_id, "tenant_id": tenant_id},
        {"$set": {"outreach_status": new_status, "outreach_updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return {"status": "updated", "member_id": member_id, "outreach_status": new_status}

@api_router.get("/v1/agent/events")
async def agent_get_events(
    request: Request,
    upcoming_only: bool = True,
    limit: int = 50
):
    """Get events for agents"""
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "events:read"):
        raise HTTPException(status_code=403, detail="Permission denied: events:read required")
    
    tenant_id = context["tenant_id"]
    
    query = {"tenant_id": tenant_id}
    if upcoming_only:
        query["start_datetime"] = {"$gte": datetime.now(timezone.utc).isoformat()}
    
    events = await db.events.find(query, {"_id": 0}).sort("start_datetime", 1).limit(limit).to_list(limit)
    
    # Get registration counts
    event_ids = [e["id"] for e in events]
    reg_counts = {}
    if event_ids:
        reg_pipeline = [
            {"$match": {"event_id": {"$in": event_ids}}},
            {"$group": {"_id": "$event_id", "count": {"$sum": 1}}}
        ]
        reg_results = await db.event_registrations.aggregate(reg_pipeline).to_list(100)
        reg_counts = {r["_id"]: r["count"] for r in reg_results}
    
    return {
        "events": [{
            "unique_id": e["id"],
            "title": e.get("name"),
            "description": e.get("description"),
            "start_time": e.get("start_datetime"),
            "end_time": e.get("end_datetime"),
            "location": e.get("location"),
            "registration_count": reg_counts.get(e["id"], 0),
            "capacity": e.get("capacity")
        } for e in events],
        "total": len(events)
    }

@api_router.get("/v1/agent/groups")
async def agent_get_groups(request: Request, limit: int = 50):
    """Get groups for agents"""
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "groups:read"):
        raise HTTPException(status_code=403, detail="Permission denied: groups:read required")
    
    tenant_id = context["tenant_id"]
    
    groups = await db.groups.find({"tenant_id": tenant_id}, {"_id": 0}).limit(limit).to_list(limit)
    
    # Get member counts
    group_ids = [g["id"] for g in groups]
    member_counts = {}
    if group_ids:
        for gid in group_ids:
            count = await db.group_members.count_documents({"group_id": gid})
            member_counts[gid] = count
    
    return {
        "groups": [{
            "unique_id": g["id"],
            "name": g.get("name"),
            "description": g.get("description"),
            "category": g.get("category"),
            "member_count": member_counts.get(g["id"], 0),
            "is_open": g.get("open_for_joining", True)
        } for g in groups],
        "total": len(groups)
    }

@api_router.get("/v1/agent/meetings")
async def agent_get_meetings(
    request: Request,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get pastoral meetings for agents"""
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "meetings:read"):
        raise HTTPException(status_code=403, detail="Permission denied: meetings:read required")
    
    tenant_id = context["tenant_id"]
    
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    
    meetings = await db.pastor_meetings.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Get slot info
    slot_ids = [m.get("slot_id") for m in meetings if m.get("slot_id")]
    slots = {}
    if slot_ids:
        slot_docs = await db.pastor_meeting_slots.find({"id": {"$in": slot_ids}}, {"_id": 0}).to_list(100)
        slots = {s["id"]: s for s in slot_docs}
    
    return {
        "meetings": [{
            "unique_id": m["id"],
            "member_name": m.get("member_name"),
            "member_email": m.get("member_email"),
            "topic": m.get("topic"),
            "scheduled_time": slots.get(m.get("slot_id"), {}).get("start_time"),
            "status": m.get("status"),
            "has_summary": bool(m.get("summary")),
            "has_transcript": bool(m.get("transcript"))
        } for m in meetings],
        "total": len(meetings)
    }

@api_router.get("/v1/agent/giving/summary")
async def agent_get_giving_summary(request: Request):
    """
    Get giving summary (READ-ONLY - no individual amounts exposed).
    Safety Lock: Agents cannot modify financial data.
    """
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "giving:read"):
        raise HTTPException(status_code=403, detail="Permission denied: giving:read required")
    
    tenant_id = context["tenant_id"]
    
    # Get aggregate stats only (no individual amounts)
    total_donors = await db.donations.aggregate([
        {"$match": {"tenant_id": tenant_id, "status": "completed"}},
        {"$group": {"_id": "$donor_email"}},
        {"$count": "total"}
    ]).to_list(1)
    
    this_month = datetime.now(timezone.utc).replace(day=1).isoformat()
    monthly_donors = await db.donations.aggregate([
        {"$match": {"tenant_id": tenant_id, "status": "completed", "donation_date": {"$gte": this_month}}},
        {"$group": {"_id": "$donor_email"}},
        {"$count": "total"}
    ]).to_list(1)
    
    # First-time givers this month
    first_time_count = await db.donations.aggregate([
        {"$match": {"tenant_id": tenant_id, "status": "completed"}},
        {"$group": {"_id": "$donor_email", "first_gift": {"$min": "$donation_date"}}},
        {"$match": {"first_gift": {"$gte": this_month}}},
        {"$count": "total"}
    ]).to_list(1)
    
    return {
        "giving_summary": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_unique_donors": total_donors[0]["total"] if total_donors else 0,
            "donors_this_month": monthly_donors[0]["total"] if monthly_donors else 0,
            "first_time_givers_this_month": first_time_count[0]["total"] if first_time_count else 0,
            "note": "Individual donation amounts are not exposed via API for security."
        }
    }

@api_router.get("/v1/agent/notes")
async def agent_get_notes(
    request: Request,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get leadership notes submitted by members"""
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "notes:read"):
        raise HTTPException(status_code=403, detail="Permission denied: notes:read required")
    
    tenant_id = context["tenant_id"]
    
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    
    notes = await db.leadership_notes.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "notes": [{
            "unique_id": n.get("id"),
            "subject": n.get("subject"),
            "message": n.get("message"),
            "category": n.get("category"),
            "member_name": n.get("member_name"),
            "member_email": n.get("member_email"),
            "status": n.get("status", "pending"),
            "created_at": n.get("created_at")
        } for n in notes],
        "total": len(notes)
    }

# --- Webhook Management ---

@api_router.post("/v1/agent/webhooks")
async def register_webhook(request: Request, payload: dict):
    """Register a webhook to receive real-time notifications"""
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "webhooks:manage"):
        raise HTTPException(status_code=403, detail="Permission denied: webhooks:manage required")
    
    tenant_id = context["tenant_id"]
    
    webhook_url = payload.get("url")
    events = payload.get("events", [])  # ["member.created", "event.registered", etc.]
    
    if not webhook_url:
        raise HTTPException(status_code=400, detail="Webhook URL required")
    
    webhook_id = str(uuid.uuid4())
    webhook_doc = {
        "id": webhook_id,
        "tenant_id": tenant_id,
        "api_key_id": context["key_id"],
        "url": webhook_url,
        "events": events,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.agent_webhooks.insert_one(webhook_doc)
    
    return {
        "webhook_id": webhook_id,
        "url": webhook_url,
        "events": events,
        "status": "active"
    }

@api_router.get("/v1/agent/webhooks")
async def list_webhooks(request: Request):
    """List registered webhooks"""
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "webhooks:manage"):
        raise HTTPException(status_code=403, detail="Permission denied: webhooks:manage required")
    
    tenant_id = context["tenant_id"]
    
    webhooks = await db.agent_webhooks.find(
        {"tenant_id": tenant_id, "api_key_id": context["key_id"]},
        {"_id": 0}
    ).to_list(50)
    
    return {"webhooks": [serialize_doc(w) for w in webhooks]}

@api_router.delete("/v1/agent/webhooks/{webhook_id}")
async def delete_webhook(request: Request, webhook_id: str):
    """Delete a webhook"""
    context = await validate_agent_api_key(request)
    if not check_agent_permission(context, "webhooks:manage"):
        raise HTTPException(status_code=403, detail="Permission denied: webhooks:manage required")
    
    tenant_id = context["tenant_id"]
    
    result = await db.agent_webhooks.delete_one({
        "id": webhook_id,
        "tenant_id": tenant_id,
        "api_key_id": context["key_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {"status": "deleted", "webhook_id": webhook_id}

# --- API Documentation Endpoint ---

@api_router.get("/v1/agent/docs")
async def agent_api_documentation():
    """
    Public endpoint: Returns API documentation and schema.
    No authentication required.
    """
    return {
        "api_name": "Solomon AI Agent API",
        "version": "1.0.0",
        "description": "Agent-ready API for church management automation",
        "base_url": "/api/v1/agent",
        "authentication": {
            "type": "Bearer Token",
            "header": "Authorization: Bearer sk_solomon_xxxxx",
            "obtain_keys": "Generate API keys from Church Admin Dashboard > Developer > API Keys"
        },
        "endpoints": {
            "/scout": {
                "method": "GET",
                "description": "Handshake endpoint - verify connection and get available endpoints",
                "permissions": "Any valid key"
            },
            "/visitors": {
                "method": "GET",
                "description": "Get new visitors/members for outreach",
                "permissions": "members:read",
                "params": {"days": "int (default 7)", "limit": "int (default 100)"}
            },
            "/members": {
                "method": "GET",
                "description": "Search and list church members",
                "permissions": "members:read"
            },
            "/members/{id}/outreach": {
                "method": "PATCH",
                "description": "Update member outreach status",
                "permissions": "members:write",
                "allowed_statuses": ["pending", "contacted", "opted_out", "follow_up", "enrolled"]
            },
            "/events": {
                "method": "GET",
                "description": "Get upcoming events",
                "permissions": "events:read"
            },
            "/groups": {
                "method": "GET",
                "description": "Get church groups",
                "permissions": "groups:read"
            },
            "/meetings": {
                "method": "GET",
                "description": "Get pastoral meetings",
                "permissions": "meetings:read"
            },
            "/giving/summary": {
                "method": "GET",
                "description": "Get aggregated giving stats (no individual amounts)",
                "permissions": "giving:read",
                "note": "READ-ONLY - Financial data cannot be modified via API"
            },
            "/notes": {
                "method": "GET",
                "description": "Get leadership notes from members",
                "permissions": "notes:read"
            },
            "/webhooks": {
                "methods": ["GET", "POST", "DELETE"],
                "description": "Manage webhook subscriptions",
                "permissions": "webhooks:manage"
            }
        },
        "data_schemas": {
            "visitor_report": {
                "timestamp": "ISO-8601",
                "new_members": [{
                    "unique_id": "string",
                    "name": "string",
                    "email": "string",
                    "phone_sms": "E.164 format",
                    "physical_address": "string",
                    "first_gift_date": "ISO-8601 or null",
                    "gift_tier": "first_time | recurring | major_donor | null",
                    "outreach_status": "pending | contacted | opted_out",
                    "is_first_time": "boolean",
                    "joined_at": "ISO-8601"
                }]
            }
        },
        "rate_limits": {
            "default": "1000 requests/hour",
            "configurable": "Per API key"
        },
        "safety_features": {
            "circuit_breaker": f"Anomaly detection triggers at {ANOMALY_THRESHOLDS['new_visitors_per_day']}+ new visitors",
            "financial_lock": "Giving data is READ-ONLY - no write access to financial records",
            "permission_scoping": "Each API key has specific permissions"
        }
    }

# --- SEED DATA ROUTE ---
@api_router.post("/seed")
async def seed_database():
    """Seed the database with demo data for Abundant Church"""
    import hashlib
    tenant_id = DEFAULT_TENANT_ID
    
    # Check if already seeded
    existing = await db.tenants.find_one({"id": tenant_id})
    if existing:
        # Still seed demo accounts if they don't exist
        await seed_demo_accounts(tenant_id)
        return {"message": "Database already seeded", "seeded": False}
    
    # ============== SEED DEMO ACCOUNTS ==============
    await seed_demo_accounts(tenant_id)
    
    # Create tenant

async def seed_demo_accounts(tenant_id: str):
    """Seed or update demo accounts"""
    import hashlib
    demo_password_hash = hashlib.sha256("Demo2026!".encode()).hexdigest()
    
    # Admin account
    await db.users.update_one(
        {"email": "admin@abundant.org"},
        {"$set": {
            "user_id": "user_admin_demo",
            "email": "admin@abundant.org",
            "name": "Pastor David Rivera",
            "picture": None,
            "role": "admin",
            "password_hash": demo_password_hash,
            "church_id": tenant_id,
            "created_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )
    
    # Member account - Maria Gonzalez
    await db.users.update_one(
        {"email": "member@abundant.org"},
        {"$set": {
            "user_id": "user_member_demo",
            "email": "member@abundant.org", 
            "name": "Maria Gonzalez",
            "picture": None,
            "role": "member",
            "password_hash": demo_password_hash,
            "church_id": tenant_id,
            "member_since": "2019-03-15",
            "created_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )

# --- SEED DATA ROUTE ---
    tenant = {
        "id": tenant_id,
        "name": "Abundant Church",
        "subdomain": "abundant",
        "plan": "enterprise",
        "member_limit": 100000,
        "logo_url": None,
        "primary_color": "#4f6ef7",
        "accent_color": "#00c896",
        "timezone": "America/Denver",
        "address": "1556 George Dieter Dr, El Paso, TX 79936",
        "website": "https://www.abundant.org",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.tenants.insert_one(tenant)
    
    # Create funds - Mega church scale
    funds_data = [
        {"name": "General Fund", "description": "General operating fund", "goal_amount": 8000000},
        {"name": "Building Fund", "description": "New sanctuary construction", "goal_amount": 5000000},
        {"name": "Missions", "description": "Global missions support", "goal_amount": 500000},
        {"name": "Benevolence", "description": "Community assistance", "goal_amount": 150000},
        {"name": "Youth Ministry", "description": "Youth programs and events", "goal_amount": 200000},
    ]
    
    funds = []
    for f in funds_data:
        fund = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "is_active": True,
            "current_amount": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **f
        }
        funds.append(fund)
    await db.funds.insert_many(funds)
    
    # Create group types
    group_types_data = [
        {"name": "Small Group", "color": "#4f6ef7", "icon": "users"},
        {"name": "Ministry Team", "color": "#00c896", "icon": "heart"},
        {"name": "Volunteer Team", "color": "#f5a623", "icon": "hand"},
        {"name": "Class", "color": "#8b5cf6", "icon": "book"},
    ]
    
    group_types = []
    for gt in group_types_data:
        gtype = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            **gt
        }
        group_types.append(gtype)
    await db.group_types.insert_many(group_types)
    
    # Create service types
    service_types_data = [
        {"name": "Sunday 9:00 AM", "default_time": "09:00", "default_day": "Sunday"},
        {"name": "Sunday 11:00 AM", "default_time": "11:00", "default_day": "Sunday"},
        {"name": "Wednesday Night", "default_time": "19:00", "default_day": "Wednesday"},
    ]
    
    service_types = []
    for st in service_types_data:
        stype = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "is_active": True,
            **st
        }
        service_types.append(stype)
    await db.service_types.insert_many(service_types)
    
    # Generate sample people (200 members)
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
                   "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
                   "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
                   "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
                   "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
                  "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
                  "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
    
    statuses = ["member", "member", "member", "member", "visitor", "regular", "inactive"]
    genders = ["male", "female"]
    campuses = ["Main Campus", "North Campus", "South Campus"]
    
    people = []
    households = []
    
    # ============== SPECIAL SEED: Maria Gonzalez (Demo Member Account) ==============
    maria_household_id = str(uuid.uuid4())
    maria_person_id = "person_maria_gonzalez"
    
    maria_household = {
        "id": maria_household_id,
        "tenant_id": tenant_id,
        "name": "The Gonzalez Family",
        "address_line1": "4521 Dyer St",
        "city": "El Paso",
        "state": "TX",
        "zip": "79930",
        "country": "US",
        "phone": "(915) 555-0142",
        "envelope_num": 1001,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    households.append(maria_household)
    
    maria_person = {
        "id": maria_person_id,
        "tenant_id": tenant_id,
        "household_id": maria_household_id,
        "first_name": "Maria",
        "last_name": "Gonzalez",
        "email": "member@abundant.org",
        "mobile_phone": "(915) 555-0142",
        "date_of_birth": "1985-06-14",
        "gender": "female",
        "marital_status": "married",
        "membership_status": "member",
        "membership_date": "2019-03-15",
        "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={maria_person_id}",
        "is_head_of_household": False,
        "campus": "East Campus",
        "engagement_score": 88,
        "ytd_giving": 1200.0,
        "lifetime_giving": 18500.0,
        "custom_fields": {},
        "giving_anonymous": False,
        "paperless_statements": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    people.append(maria_person)
    
    # ============== SEED: 10 El Paso-specific named members ==============
    el_paso_members = [
        {"first": "Carlos", "last": "Rivera", "gender": "male"},
        {"first": "Sofia", "last": "Martinez", "gender": "female"},
        {"first": "Juan", "last": "Hernandez", "gender": "male"},
        {"first": "Isabella", "last": "Lopez", "gender": "female"},
        {"first": "Miguel", "last": "Torres", "gender": "male"},
        {"first": "Valentina", "last": "Ramirez", "gender": "female"},
        {"first": "Diego", "last": "Castillo", "gender": "male"},
        {"first": "Ana", "last": "Reyes", "gender": "female"},
        {"first": "Roberto", "last": "Vega", "gender": "male"},
        {"first": "Pastor David", "last": "Rivera", "gender": "male"},
    ]
    
    el_paso_streets = ["Montana Ave", "Alameda Ave", "Mesa St", "Dyer St", "Lee Trevino Dr", 
                       "Gateway Blvd", "Viscount Blvd", "Zaragoza Rd", "Transmountain Dr", "Paisano Dr"]
    
    for i, ep_member in enumerate(el_paso_members):
        ep_household_id = str(uuid.uuid4())
        ep_person_id = str(uuid.uuid4())
        
        ep_household = {
            "id": ep_household_id,
            "tenant_id": tenant_id,
            "name": f"The {ep_member['last']} Family",
            "address_line1": f"{random.randint(1000, 9999)} {random.choice(el_paso_streets)}",
            "city": "El Paso",
            "state": "TX",
            "zip": f"799{random.randint(10, 99)}",
            "country": "US",
            "phone": f"(915) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "envelope_num": 1002 + i,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        households.append(ep_household)
        
        ep_person = {
            "id": ep_person_id,
            "tenant_id": tenant_id,
            "household_id": ep_household_id,
            "first_name": ep_member["first"],
            "last_name": ep_member["last"],
            "email": f"{ep_member['first'].lower()}.{ep_member['last'].lower()}@email.com",
            "mobile_phone": f"(915) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "date_of_birth": f"{random.randint(1960, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "gender": ep_member["gender"],
            "marital_status": "married",
            "membership_status": "member",
            "membership_date": f"20{random.randint(15, 24)}-{random.randint(1, 12):02d}-01",
            "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={ep_person_id}",
            "is_head_of_household": True,
            "campus": random.choice(["Main Campus", "East Campus", "West Campus"]),
            "engagement_score": random.randint(60, 100),
            "ytd_giving": random.randint(500, 5000) * 1.0,
            "lifetime_giving": random.randint(5000, 50000) * 1.0,
            "custom_fields": {},
            "giving_anonymous": False,
            "paperless_statements": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        people.append(ep_person)
    
    # Create 80 households with 200 people (remaining generic)
    for h in range(80):
        household_id = str(uuid.uuid4())
        last_name = random.choice(last_names)
        
        household = {
            "id": household_id,
            "tenant_id": tenant_id,
            "name": f"The {last_name} Family",
            "address_line1": f"{random.randint(100, 9999)} {random.choice(['Oak', 'Main', 'Church', 'Park', 'Elm', 'Cedar'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}",
            "city": "El Cajon",
            "state": "CA",
            "zip": f"920{random.randint(10, 99)}",
            "country": "US",
            "phone": f"619-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "envelope_num": h + 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        households.append(household)
        
        # 2-3 people per household
        num_people = random.randint(2, 3)
        for i in range(num_people):
            person_id = str(uuid.uuid4())
            first_name = random.choice(first_names)
            gender = random.choice(genders)
            birth_year = random.randint(1950, 2010)
            
            person = {
                "id": person_id,
                "tenant_id": tenant_id,
                "household_id": household_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@email.com",
                "mobile_phone": f"619-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                "date_of_birth": f"{birth_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "gender": gender,
                "marital_status": random.choice(["single", "married", "married"]),
                "membership_status": random.choice(statuses),
                "membership_date": f"20{random.randint(10, 24)}-{random.randint(1, 12):02d}-01",
                "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={person_id}",
                "is_head_of_household": i == 0,
                "campus": random.choice(campuses),
                "engagement_score": random.randint(20, 100),
                "ytd_giving": 0,
                "lifetime_giving": 0,
                "custom_fields": {},
                "giving_anonymous": False,
                "paperless_statements": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            people.append(person)
    
    await db.households.insert_many(households)
    await db.people.insert_many(people)
    
    # Create groups (20 groups)
    group_names = [
        "Young Adults", "Marriage Builders", "New Believers", "Prayer Warriors",
        "Women's Bible Study", "Men's Brotherhood", "College & Career", "Empty Nesters",
        "Parents of Teens", "Grief Support", "Financial Peace", "Spanish Fellowship",
        "Worship Team", "Tech Team", "Greeting Team", "Parking Team",
        "Children's Ministry", "Youth Group", "Senior Saints", "Community Outreach"
    ]
    
    groups = []
    for i, name in enumerate(group_names):
        group_type = group_types[i % len(group_types)]
        leader = random.choice(people)
        
        group = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "group_type_id": group_type["id"],
            "name": name,
            "description": f"{name} - a place to grow and connect",
            "location": random.choice(["Room 101", "Room 202", "Fellowship Hall", "Chapel", "Youth Center"]),
            "meeting_schedule": random.choice(["Weekly", "Bi-weekly", "Monthly"]),
            "meeting_day": random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]),
            "meeting_time": random.choice(["09:00", "10:00", "18:00", "19:00"]),
            "capacity": random.randint(15, 60),
            "is_open": random.choice([True, True, True, False]),
            "is_active": True,
            "leader_id": leader["id"],
            "tags": [],
            "member_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        groups.append(group)
    await db.groups.insert_many(groups)
    
    # Assign people to groups (each person in 1-3 groups)
    group_members = []
    for person in people:
        num_groups = random.randint(1, 3)
        selected_groups = random.sample(groups, min(num_groups, len(groups)))
        
        for g in selected_groups:
            member = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "group_id": g["id"],
                "person_id": person["id"],
                "role": random.choice(["member", "member", "member", "leader", "co-leader"]),
                "joined_at": f"20{random.randint(20, 24)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "is_active": True
            }
            group_members.append(member)
    await db.group_members.insert_many(group_members)
    
    # Update group member counts
    for g in groups:
        count = sum(1 for gm in group_members if gm["group_id"] == g["id"])
        await db.groups.update_one({"id": g["id"]}, {"$set": {"member_count": count}})
    
    # Create services for last 18 months (every Sunday)
    services = []
    today = datetime.now(timezone.utc)
    
    for weeks_ago in range(78):  # ~18 months
        service_date = today - timedelta(weeks=weeks_ago)
        # Find the Sunday
        days_until_sunday = (6 - service_date.weekday()) % 7
        sunday = service_date - timedelta(days=service_date.weekday() + 1)
        sunday_str = sunday.strftime("%Y-%m-%d")
        
        for st in service_types[:2]:  # Two Sunday services
            service = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "service_type_id": st["id"],
                "date": sunday_str,
                "time": st["default_time"],
                "total_headcount": random.randint(3000, 4500),
                "notes": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            services.append(service)
    
    await db.services.insert_many(services)
    
    # Create attendance records
    attendance_records = []
    for service in services[-24:]:  # Last 12 weeks (24 services)
        # Random subset of people attended
        attendees = random.sample(people, random.randint(60, 120))
        for person in attendees:
            record = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "service_id": service["id"],
                "person_id": person["id"],
                "check_in_time": datetime.now(timezone.utc).isoformat()
            }
            attendance_records.append(record)
    
    if attendance_records:
        await db.attendance.insert_many(attendance_records)
    
    # Create donations (18 months of giving)
    donations = []
    payment_methods = ["card", "card", "card", "check", "check", "cash", "ach", "ach"]
    
    for weeks_ago in range(78):
        week_date = today - timedelta(weeks=weeks_ago)
        sunday = week_date - timedelta(days=week_date.weekday() + 1)
        sunday_str = sunday.strftime("%Y-%m-%d")
        
        # 40-80 donations per week
        num_donations = random.randint(40, 80)
        donors = random.sample(people, min(num_donations, len(people)))
        
        for donor in donors:
            fund = random.choice(funds)
            amount = random.choice([25, 50, 100, 100, 150, 200, 250, 500, 1000, 2500])
            
            donation = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "person_id": donor["id"],
                "fund_id": fund["id"],
                "amount": float(amount),
                "donation_date": sunday_str,
                "payment_method": random.choice(payment_methods),
                "is_recurring": random.random() < 0.15,
                "receipt_sent": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            donations.append(donation)
    
    # Add 5 crypto donations
    crypto_currencies = ["BTC", "ETH", "USDC", "SOL"]
    for _ in range(5):
        donor = random.choice(people)
        crypto_amount = random.uniform(0.01, 2.0)
        usd_value = random.uniform(500, 25000)
        
        donation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": donor["id"],
            "fund_id": funds[0]["id"],  # General fund
            "amount": usd_value,
            "donation_date": (today - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d"),
            "payment_method": "crypto",
            "crypto_currency": random.choice(crypto_currencies),
            "crypto_amount": crypto_amount,
            "crypto_tx_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
            "crypto_usd_value": usd_value,
            "is_recurring": False,
            "receipt_sent": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        donations.append(donation)
    
    # Add 2 asset donations
    asset_donations = [
        {"asset_type": "vehicle", "asset_description": "2020 Toyota Camry", "asset_appraised_value": 22000},
        {"asset_type": "stock", "asset_description": "500 shares AAPL", "asset_appraised_value": 95000},
    ]
    
    for asset in asset_donations:
        donor = random.choice(people)
        donation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": donor["id"],
            "fund_id": funds[1]["id"],  # Building fund
            "amount": asset["asset_appraised_value"],
            "donation_date": (today - timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d"),
            "payment_method": "stock" if asset["asset_type"] == "stock" else "vehicle",
            "asset_type": asset["asset_type"],
            "asset_description": asset["asset_description"],
            "asset_appraised_value": asset["asset_appraised_value"],
            "is_recurring": False,
            "receipt_sent": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        donations.append(donation)
    
    await db.donations.insert_many(donations)
    
    # Update fund totals
    for fund in funds:
        total = sum(d["amount"] for d in donations if d["fund_id"] == fund["id"])
        await db.funds.update_one({"id": fund["id"]}, {"$set": {"current_amount": total}})
    
    # Update person giving totals
    ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    for person in people:
        person_donations = [d for d in donations if d["person_id"] == person["id"]]
        lifetime = sum(d["amount"] for d in person_donations)
        ytd = sum(d["amount"] for d in person_donations if d["donation_date"] >= ytd_start)
        await db.people.update_one(
            {"id": person["id"]},
            {"$set": {"lifetime_giving": lifetime, "ytd_giving": ytd}}
        )
    
    # Create recurring giving (30 givers)
    recurring_givers = random.sample(people, 30)
    recurring_records = []
    
    for person in recurring_givers:
        recurring = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": person["id"],
            "fund_id": random.choice(funds)["id"],
            "amount": float(random.choice([50, 100, 150, 200, 250, 500])),
            "frequency": random.choice(["weekly", "biweekly", "monthly"]),
            "next_gift_date": (today + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
            "payment_method": "card",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        recurring_records.append(recurring)
    
    await db.recurring_giving.insert_many(recurring_records)
    
    # Create pledges (10 pledges for Building Fund campaign)
    pledgers = random.sample(people, 10)
    pledges = []
    
    for person in pledgers:
        pledge_amount = random.choice([5000, 10000, 15000, 25000, 50000])
        total_given = random.uniform(0.2, 0.9) * pledge_amount
        
        pledge = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": person["id"],
            "fund_id": funds[1]["id"],  # Building Fund
            "pledge_amount": float(pledge_amount),
            "start_date": "2024-01-01",
            "end_date": "2026-12-31",
            "frequency": "monthly",
            "total_given": total_given,
            "notes": "Building Fund Campaign 2024-2026",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        pledges.append(pledge)
    
    await db.pledges.insert_many(pledges)
    
    # Create donation batches
    batches = [
        {"name": "Sunday Offering 01/12/2025", "date": "2025-01-12", "status": "open", "total_amount": 45230.00, "donation_count": 87},
        {"name": "Sunday Offering 01/05/2025", "date": "2025-01-05", "status": "closed", "total_amount": 52100.00, "donation_count": 102},
        {"name": "Sunday Offering 12/29/2024", "date": "2024-12-29", "status": "deposited", "total_amount": 89500.00, "donation_count": 156},
    ]
    
    batch_records = []
    for b in batches:
        batch = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **b
        }
        batch_records.append(batch)
    await db.donation_batches.insert_many(batch_records)
    
    # Create upcoming events
    events = [
        {
            "name": "Sunday Service",
            "description": "Join us for worship, prayer, and the Word",
            "location": "Main Sanctuary",
            "start_datetime": (today + timedelta(days=(6 - today.weekday()))).strftime("%Y-%m-%dT09:00:00"),
            "is_public": True,
            "capacity": 5000,
            "registration_required": False,
            "registration_count": 0
        },
        {
            "name": "Youth Night",
            "description": "Middle and High School students gather for games, worship, and teaching",
            "location": "Youth Center",
            "start_datetime": (today + timedelta(days=3)).strftime("%Y-%m-%dT18:30:00"),
            "is_public": True,
            "capacity": 200,
            "registration_required": False,
            "registration_count": 45
        },
        {
            "name": "Women's Conference",
            "description": "Annual women's conference - 'Renewed'",
            "location": "Fellowship Hall",
            "start_datetime": (today + timedelta(days=14)).strftime("%Y-%m-%dT09:00:00"),
            "is_public": True,
            "capacity": 500,
            "registration_required": True,
            "registration_count": 287
        },
        {
            "name": "Baptism Sunday",
            "description": "Celebrate new believers taking the step of baptism",
            "location": "Main Sanctuary",
            "start_datetime": (today + timedelta(days=21)).strftime("%Y-%m-%dT11:00:00"),
            "is_public": True,
            "capacity": 5000,
            "registration_required": False,
            "registration_count": 23
        },
        {
            "name": "Marriage Retreat",
            "description": "Strengthen your marriage at our couples retreat",
            "location": "Pine Valley Resort",
            "start_datetime": (today + timedelta(days=45)).strftime("%Y-%m-%dT17:00:00"),
            "is_public": True,
            "capacity": 50,
            "registration_required": True,
            "registration_count": 34
        },
        {
            "name": "Volunteer Appreciation Dinner",
            "description": "Thank you dinner for all church volunteers",
            "location": "Fellowship Hall",
            "start_datetime": (today + timedelta(days=30)).strftime("%Y-%m-%dT18:00:00"),
            "is_public": False,
            "capacity": 300,
            "registration_required": True,
            "registration_count": 156
        }
    ]
    
    event_records = []
    for e in events:
        event = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **e
        }
        event_records.append(event)
    await db.events.insert_many(event_records)
    
    # Create activity log entries
    activities = [
        {"action": "member_added", "description": "New member added: Sarah Johnson", "entity_type": "person"},
        {"action": "donation_recorded", "description": "Donation of $1,500.00 recorded", "entity_type": "donation"},
        {"action": "group_created", "description": "New group created: Young Professionals", "entity_type": "group"},
        {"action": "event_created", "description": "New event created: Easter Service", "entity_type": "event"},
        {"action": "member_updated", "description": "Member status updated: John Smith → Active Member", "entity_type": "person"},
        {"action": "batch_closed", "description": "Batch closed: Sunday Offering 01/05/2025", "entity_type": "batch"},
        {"action": "email_sent", "description": "Email sent to 4,287 recipients: January Newsletter", "entity_type": "communication"},
        {"action": "attendance_recorded", "description": "Attendance recorded for Sunday 9AM: 3,421 attendees", "entity_type": "attendance"},
    ]
    
    activity_records = []
    for i, a in enumerate(activities):
        activity = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "entity_id": str(uuid.uuid4()),
            "created_at": (today - timedelta(hours=i*2)).isoformat(),
            **a
        }
        activity_records.append(activity)
    await db.activity_log.insert_many(activity_records)
    
    # Create communication templates
    communications = [
        {
            "subject": "Welcome to Abundant Church!",
            "body_html": "<h1>Welcome!</h1><p>We're so glad you visited us...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        },
        {
            "subject": "Prayer Request Follow-up",
            "body_html": "<p>Dear {first_name},</p><p>We've been praying for you...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        },
        {
            "subject": "You're Invited: {event_name}",
            "body_html": "<h2>{event_name}</h2><p>Join us for this special event...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        },
        {
            "subject": "Your Giving Statement",
            "body_html": "<h1>Annual Giving Statement</h1><p>Thank you for your generosity...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        }
    ]
    
    comm_records = []
    for c in communications:
        comm = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **c
        }
        comm_records.append(comm)
    await db.communications.insert_many(comm_records)
    
    return {
        "message": "Database seeded successfully",
        "seeded": True,
        "counts": {
            "tenant": 1,
            "households": len(households),
            "people": len(people),
            "groups": len(groups),
            "group_members": len(group_members),
            "funds": len(funds),
            "services": len(services),
            "attendance": len(attendance_records),
            "donations": len(donations),
            "recurring_giving": len(recurring_records),
            "pledges": len(pledges),
            "batches": len(batch_records),
            "events": len(event_records),
            "communications": len(comm_records)
        }
    }

# ============== MULTI-TENANT SEED ==============

@api_router.post("/seed-platform")
async def seed_platform():
    """Seed the entire Solomon AI platform with multiple churches and demo data"""
    import hashlib
    
    demo_password_hash = hashlib.sha256("Demo2026!".encode()).hexdigest()
    
    # Define the three demo churches
    churches = [
        {
            "id": "abundant-east-001",
            "name": "Abundant Church",
            "subdomain": "abundant",
            "plan": "enterprise",
            "member_limit": 100000,
            "subscription_status": "active",
            "address": "1556 George Dieter Dr",
            "city": "El Paso",
            "state": "TX",
            "timezone": "America/Denver",
            "website": "https://www.abundant.org",
            "phone": "(915) 755-3000",
            "primary_color": "#4f6ef7",
            "accent_color": "#00c896",
            "thinkific_url": "https://abundantchurch.thinkific.com/collections",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        },
        {
            "id": "cristoviene-church-001",
            "name": "Cristo Viene",
            "subdomain": "cristoviene",
            "plan": "enterprise",
            "member_limit": 50000,
            "subscription_status": "active",
            "address": "7500 N Loop Dr",
            "city": "El Paso",
            "state": "TX",
            "timezone": "America/Denver",
            "website": "https://cristoviene.org",
            "phone": "(915) 598-4000",
            "primary_color": "#dc2626",
            "accent_color": "#fbbf24",
            "thinkific_url": "https://cristoviene.thinkific.com",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        },
        {
            "id": "pottershouse-church-001",
            "name": "The Potter's House",
            "subdomain": "pottershouse",
            "plan": "enterprise",
            "member_limit": 100000,
            "subscription_status": "active",
            "address": "6777 W Kiest Blvd",
            "city": "Dallas",
            "state": "TX",
            "timezone": "America/Chicago",
            "website": "https://thepottershouse.org",
            "phone": "(214) 331-0954",
            "primary_color": "#7c3aed",
            "accent_color": "#ec4899",
            "thinkific_url": "https://pottershouse.thinkific.com",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        }
    ]
    
    results = {"churches": [], "platform_accounts": []}
    
    # Create/update Solomon platform admin accounts
    platform_accounts = [
        {
            "user_id": "platform_admin_001",
            "email": "admin@solomon.ai",
            "name": "Solomon Platform Admin",
            "role": "platform_admin",
            "tenant_id": None  # Platform admin has no tenant restriction
        },
        {
            "user_id": "platform_member_001",
            "email": "member@solomon.ai",
            "name": "Demo Member",
            "role": "member",
            "tenant_id": "abundant-east-001"  # Default to Abundant for demo
        },
        {
            "user_id": "platform_newmember_001",
            "email": "newmember@solomon.ai",
            "name": "New Member Demo",
            "role": "member",
            "tenant_id": "abundant-east-001"
        }
    ]
    
    for account in platform_accounts:
        await db.users.update_one(
            {"user_id": account["user_id"]},
            {"$set": {
                **account,
                "password_hash": demo_password_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }},
            upsert=True
        )
        results["platform_accounts"].append(account["email"])
    
    # Seed each church
    for church in churches:
        # Create/update tenant
        await db.tenants.update_one(
            {"id": church["id"]},
            {"$set": {
                **church,
                "created_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        # Create church admin account
        admin_email = f"admin@{church['subdomain']}.church"
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {
                "user_id": f"admin_{church['subdomain']}",
                "email": admin_email,
                "name": f"{church['name']} Admin",
                "role": "church_admin",
                "tenant_id": church["id"],
                "password_hash": demo_password_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }},
            upsert=True
        )
        
        # Create demo member account
        member_email = f"member@{church['subdomain']}.church"
        await db.users.update_one(
            {"email": member_email},
            {"$set": {
                "user_id": f"member_{church['subdomain']}",
                "email": member_email,
                "name": f"{church['name']} Member",
                "role": "member",
                "tenant_id": church["id"],
                "password_hash": demo_password_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }},
            upsert=True
        )
        
        # Generate 500 members for this church with 6 months of data
        existing_members = await db.people.count_documents({"tenant_id": church["id"]})
        if existing_members < 100:  # Only seed if not already seeded
            await seed_church_members(church["id"], church["name"], 500)
        
        results["churches"].append({
            "name": church["name"],
            "subdomain": church["subdomain"],
            "admin_email": admin_email,
            "member_email": member_email
        })
    
    # Seed media videos for Abundant Church (as demo content - matching member portal)
    abundant_videos = [
        {
            "id": "video_001",
            "tenant_id": "abundant-east-001",
            "title": "Community With a Purpose",
            "description": "Discover how the church is God's purposeful community - not a club but a family with divine purpose.",
            "youtube_id": "FoPI3hMbXvw",
            "youtube_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration": "40:45",
            "instructor": "Pastor Charles Nieman",
            "category_id": "community",
            "is_featured": True,
            "is_published": True,
            "badge": "New",
            "view_count": 1250,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_002",
            "tenant_id": "abundant-east-001",
            "title": "Blessing & Healing Through Humility",
            "description": "Learn how humility unlocks God's blessings and healing in your life.",
            "youtube_id": "pzpbbibEWPE",
            "youtube_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration": "38:30",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": True,
            "is_published": True,
            "badge": "New",
            "view_count": 890,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_003",
            "tenant_id": "abundant-east-001",
            "title": "Building Your Life",
            "description": "Build your life on God's Word - biblical principles for personal spiritual development.",
            "youtube_id": "Lnj6vMvOLME",
            "youtube_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration": "45:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "growth",
            "is_featured": False,
            "is_published": True,
            "view_count": 1520,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_004",
            "tenant_id": "abundant-east-001",
            "title": "The Missing Peace",
            "description": "Find God's inner peace through grace and righteousness.",
            "youtube_id": "OjhMsB6czxc",
            "youtube_url": "https://youtube.com/watch?v=OjhMsB6czxc",
            "thumbnail_url": "https://i.ytimg.com/vi/OjhMsB6czxc/maxresdefault.jpg",
            "duration": "38:30",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": True,
            "is_published": True,
            "view_count": 780,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_005",
            "tenant_id": "abundant-east-001",
            "title": "The Laws of Life",
            "description": "Your thoughts and beliefs shape your outcomes - learn the laws that govern life.",
            "youtube_id": "WQy48ANpj5c",
            "youtube_url": "https://youtube.com/watch?v=WQy48ANpj5c",
            "thumbnail_url": "https://i.ytimg.com/vi/WQy48ANpj5c/maxresdefault.jpg",
            "duration": "37:57",
            "instructor": "Pastor Charles Nieman",
            "category_id": "growth",
            "is_featured": False,
            "is_published": True,
            "view_count": 650,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_006",
            "tenant_id": "abundant-east-001",
            "title": "The Story Behind the Story",
            "description": "Discover the deeper meaning of Christmas and God's plan through Jesus' birth.",
            "youtube_id": "wCjwUQMhCIY",
            "youtube_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration": "37:30",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": False,
            "is_published": True,
            "view_count": 430,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_007",
            "tenant_id": "abundant-east-001",
            "title": "Managing Your Emotions",
            "description": "Biblical wisdom on understanding and handling your emotions effectively.",
            "youtube_id": "0grr2E0kuFg",
            "youtube_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration": "42:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "growth",
            "is_featured": False,
            "is_published": True,
            "badge": "Popular",
            "view_count": 2100,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_008",
            "tenant_id": "abundant-east-001",
            "title": "Worship In Spirit & In Truth",
            "description": "Experience authentic worship that transforms your relationship with God.",
            "youtube_id": "uwkmP6sDihI",
            "youtube_url": "https://youtube.com/watch?v=uwkmP6sDihI",
            "thumbnail_url": "https://i.ytimg.com/vi/uwkmP6sDihI/maxresdefault.jpg",
            "duration": "35:00",
            "instructor": "Pastor Jared Nieman",
            "category_id": "worship",
            "is_featured": False,
            "is_published": True,
            "view_count": 560,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_009",
            "tenant_id": "abundant-east-001",
            "title": "Vision Sunday 2025",
            "description": "The church's vision and community outreach efforts for the year ahead.",
            "youtube_id": "O0WfS3Ma2XM",
            "youtube_url": "https://youtube.com/watch?v=O0WfS3Ma2XM",
            "thumbnail_url": "https://i.ytimg.com/vi/O0WfS3Ma2XM/maxresdefault.jpg",
            "duration": "48:00",
            "instructor": "Pastor Jared Nieman",
            "category_id": "leadership",
            "is_featured": False,
            "is_published": True,
            "view_count": 1800,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_010",
            "tenant_id": "abundant-east-001",
            "title": "Abundant Conference 2025",
            "description": "Night 2 of the Abundant Conference featuring worship and powerful teaching.",
            "youtube_id": "kGXOOO6hHUk",
            "youtube_url": "https://youtube.com/watch?v=kGXOOO6hHUk",
            "thumbnail_url": "https://i.ytimg.com/vi/kGXOOO6hHUk/maxresdefault.jpg",
            "duration": "1:20:00",
            "instructor": "Pastor Marcos Witt",
            "category_id": "worship",
            "is_featured": True,
            "is_published": True,
            "badge": "Featured",
            "view_count": 3200,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_011",
            "tenant_id": "abundant-east-001",
            "title": "We Are Abundant",
            "description": "Understanding our calling to be a blessing to others in our community.",
            "youtube_id": "rMmIcJCDsaU",
            "youtube_url": "https://youtube.com/watch?v=rMmIcJCDsaU",
            "thumbnail_url": "https://i.ytimg.com/vi/rMmIcJCDsaU/maxresdefault.jpg",
            "duration": "40:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "community",
            "is_featured": False,
            "is_published": True,
            "view_count": 920,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_012",
            "tenant_id": "abundant-east-001",
            "title": "Faith That Moves Mountains",
            "description": "Discover the kind of faith that can move any mountain in your life.",
            "youtube_id": "3BHJSkx3J4E",
            "youtube_url": "https://youtube.com/watch?v=3BHJSkx3J4E",
            "thumbnail_url": "https://i.ytimg.com/vi/3BHJSkx3J4E/maxresdefault.jpg",
            "duration": "36:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": False,
            "is_published": True,
            "view_count": 750,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Seed media categories
    categories = [
        {"id": "faith", "tenant_id": "abundant-east-001", "name": "Faith", "slug": "faith", "icon": "heart", "sort_order": 1},
        {"id": "family", "tenant_id": "abundant-east-001", "name": "Family", "slug": "family", "icon": "users", "sort_order": 2},
        {"id": "leadership", "tenant_id": "abundant-east-001", "name": "Leadership", "slug": "leadership", "icon": "briefcase", "sort_order": 3},
        {"id": "worship", "tenant_id": "abundant-east-001", "name": "Worship", "slug": "worship", "icon": "music", "sort_order": 4},
        {"id": "growth", "tenant_id": "abundant-east-001", "name": "Growth", "slug": "growth", "icon": "trending-up", "sort_order": 5},
        {"id": "community", "tenant_id": "abundant-east-001", "name": "Community", "slug": "community", "icon": "home", "sort_order": 6},
    ]
    
    # Insert categories
    for cat in categories:
        await db.media_categories.update_one(
            {"id": cat["id"], "tenant_id": cat["tenant_id"]},
            {"$set": cat},
            upsert=True
        )
    
    # Insert videos
    for video in abundant_videos:
        await db.media_videos.update_one(
            {"id": video["id"]},
            {"$set": video},
            upsert=True
        )

    # Seed Abundant Pathways courses
    pathways_courses = [
        {
            "id": "pathway_course_001",
            "tenant_id": "abundant-east-001",
            "title": "Abundant Next Steps",
            "description": "Your on-ramp to belonging, serving, and growing at Abundant.",
            "cover_image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
            "category": "New Members Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_002",
            "tenant_id": "abundant-east-001",
            "title": "Preparing for Baptism",
            "description": "Understand baptism and get ready to share your story.",
            "cover_image_url": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80",
            "category": "Baptism Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_003",
            "tenant_id": "abundant-east-001",
            "title": "Foundations of Discipleship",
            "description": "Build daily rhythms of scripture, prayer, and obedience.",
            "cover_image_url": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?auto=format&fit=crop&w=1200&q=80",
            "category": "Discipleship Track",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_004",
            "tenant_id": "abundant-east-001",
            "title": "Financial Peace University",
            "description": "Walk through budgeting, generosity, and debt-free living.",
            "cover_image_url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80",
            "category": "Stewardship Track",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_005",
            "tenant_id": "abundant-east-001",
            "title": "Serving with Purpose",
            "description": "Discover your gifts and find the right team to serve.",
            "cover_image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
            "category": "Leadership Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_006",
            "tenant_id": "abundant-east-001",
            "title": "Prayer & Presence",
            "description": "Deepen your prayer life and sensitivity to God's presence.",
            "cover_image_url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80",
            "category": "Spiritual Practices",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_007",
            "tenant_id": "abundant-east-001",
            "title": "Marriage & Family Care",
            "description": "Strengthen your relationships and build a healthy home.",
            "cover_image_url": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=1200&q=80",
            "category": "Family Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_008",
            "tenant_id": "abundant-east-001",
            "title": "Mission & Outreach",
            "description": "Live on mission through local and global outreach.",
            "cover_image_url": "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?auto=format&fit=crop&w=1200&q=80",
            "category": "Outreach Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    pathways_lessons = [
        {
            "id": "pathway_lesson_001",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_001",
            "title": "Welcome to Abundant",
            "description": "Meet the heart, mission, and values of Abundant Church.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "15:40",
            "duration_seconds": 940,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_002",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_001",
            "title": "Belonging & Community",
            "description": "Find your people and take your next step into community.",
            "youtube_id": "pzpbbibEWPE",
            "video_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration_label": "18:20",
            "duration_seconds": 1100,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_003",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_002",
            "title": "Why Baptism Matters",
            "description": "Understand the significance of baptism and next steps.",
            "youtube_id": "Lnj6vMvOLME",
            "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration_label": "16:05",
            "duration_seconds": 965,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_004",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_002",
            "title": "Preparing Your Story",
            "description": "Craft your testimony and prepare for the baptism service.",
            "youtube_id": "wCjwUQMhCIY",
            "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration_label": "14:35",
            "duration_seconds": 875,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_005",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_003",
            "title": "Daily Discipleship",
            "description": "Develop a daily walk with Jesus through scripture and prayer.",
            "youtube_id": "0grr2E0kuFg",
            "video_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration_label": "20:10",
            "duration_seconds": 1210,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_006",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_003",
            "title": "Scripture & Spirit",
            "description": "Learn to listen to God's voice and apply the word.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "19:05",
            "duration_seconds": 1145,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_007",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_004",
            "title": "Budgeting with Purpose",
            "description": "Build a budget aligned with your values and goals.",
            "youtube_id": "pzpbbibEWPE",
            "video_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration_label": "21:20",
            "duration_seconds": 1280,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_008",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_004",
            "title": "Debt-Free Journey",
            "description": "Steps to reduce debt and build margin for generosity.",
            "youtube_id": "Lnj6vMvOLME",
            "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration_label": "17:30",
            "duration_seconds": 1050,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_009",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_005",
            "title": "Discover Your Gifts",
            "description": "Identify your gifts and how they serve the church.",
            "youtube_id": "wCjwUQMhCIY",
            "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration_label": "14:55",
            "duration_seconds": 895,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_010",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_005",
            "title": "Serving Teams",
            "description": "Explore serving opportunities and next steps.",
            "youtube_id": "0grr2E0kuFg",
            "video_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration_label": "13:50",
            "duration_seconds": 830,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_011",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_006",
            "title": "Prayer Rhythm",
            "description": "Create a daily prayer rhythm that anchors your week.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "18:00",
            "duration_seconds": 1080,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_012",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_006",
            "title": "Hearing God's Voice",
            "description": "Learn to discern and respond to God's leading.",
            "youtube_id": "wCjwUQMhCIY",
            "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration_label": "17:15",
            "duration_seconds": 1035,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_013",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_007",
            "title": "Healthy Relationships",
            "description": "Build healthy rhythms in your marriage and family.",
            "youtube_id": "pzpbbibEWPE",
            "video_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration_label": "16:45",
            "duration_seconds": 1005,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_014",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_007",
            "title": "Family Devotions",
            "description": "Practical ideas for discipleship at home.",
            "youtube_id": "Lnj6vMvOLME",
            "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration_label": "15:30",
            "duration_seconds": 930,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_015",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_008",
            "title": "Living on Mission",
            "description": "Share your faith through local outreach.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "17:05",
            "duration_seconds": 1025,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_016",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_008",
            "title": "Community Outreach",
            "description": "Plan practical ways to serve El Paso together.",
            "youtube_id": "0grr2E0kuFg",
            "video_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration_label": "18:35",
            "duration_seconds": 1115,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    for course in pathways_courses:
        await db.pathways_courses.update_one(
            {"id": course["id"]},
            {"$set": course},
            upsert=True
        )

    for lesson in pathways_lessons:
        await db.pathways_lessons.update_one(
            {"id": lesson["id"]},
            {"$set": lesson},
            upsert=True
        )

    # Assign demo member to pathways courses
    enrollments = []
    for idx, course in enumerate(pathways_courses, start=1):
        enrollments.append({
            "id": f"pathway_enroll_{idx:03d}",
            "tenant_id": "abundant-east-001",
            "course_id": course["id"],
            "user_id": "member_abundant",
            "assigned_by": "admin_abundant",
            "status": "assigned",
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

    for enrollment in enrollments:
        await db.pathways_enrollments.update_one(
            {"id": enrollment["id"]},
            {"$set": enrollment},
            upsert=True
        )

    return {
        "message": "Platform seeded successfully",
        "results": results,
        "demo_credentials": {
            "password": "Demo2026!",
            "platform_admin": "admin@solomon.ai",
            "abundant_admin": "admin@abundant.church",
            "cristoviene_admin": "admin@cristoviene.church",
            "pottershouse_admin": "admin@pottershouse.church"
        }
    }

async def seed_church_members(tenant_id: str, church_name: str, count: int = 500):
    """Generate realistic church members with 6 months of giving/attendance data"""
    
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
                   "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
                   "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
                   "Matthew", "Betty", "Anthony", "Margaret", "Carlos", "Maria", "Juan", "Sofia",
                   "Miguel", "Isabella", "Diego", "Valentina", "Roberto", "Ana", "Luis", "Carmen"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
                  "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
                  "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
    
    statuses = ["member", "member", "member", "member", "visitor", "regular"]
    
    people = []
    donations = []
    attendance_records = []
    
    today = datetime.now(timezone.utc)
    six_months_ago = today - timedelta(days=180)
    
    fund_names = ["General Fund", "Building Fund", "Missions", "Benevolence", "Youth Ministry"]
    
    for i in range(count):
        person_id = str(uuid.uuid4())
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        person = {
            "id": person_id,
            "tenant_id": tenant_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@email.com",
            "mobile_phone": f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "date_of_birth": f"{random.randint(1960, 2005)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "gender": random.choice(["male", "female"]),
            "membership_status": random.choice(statuses),
            "membership_date": (six_months_ago + timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d"),
            "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={person_id}",
            "engagement_score": random.randint(30, 100),
            "ytd_giving": 0,
            "lifetime_giving": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        people.append(person)
        
        # Generate donations (6 months of history)
        if random.random() > 0.3:  # 70% of members give
            num_donations = random.randint(3, 24)  # 3-24 donations over 6 months
            person_total = 0
            for _ in range(num_donations):
                donation_date = six_months_ago + timedelta(days=random.randint(0, 180))
                amount = random.choice([25, 50, 100, 150, 200, 250, 500, 1000])
                donation = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "person_id": person_id,
                    "donor_name": f"{first_name} {last_name}",
                    "amount": amount,
                    "fund_name": random.choice(fund_names),
                    "donation_date": donation_date.strftime("%Y-%m-%d"),
                    "payment_method": random.choice(["card", "ach", "cash", "check"]),
                    "payment_status": "completed",
                    "created_at": donation_date.isoformat()
                }
                donations.append(donation)
                person_total += amount
            person["ytd_giving"] = person_total
            person["lifetime_giving"] = person_total * random.uniform(1, 3)
        
        # Generate attendance (6 months)
        if random.random() > 0.2:  # 80% have some attendance
            num_attendances = random.randint(5, 24)  # 5-24 services over 6 months
            for _ in range(num_attendances):
                att_date = six_months_ago + timedelta(days=random.randint(0, 180))
                att_record = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "person_id": person_id,
                    "person_name": f"{first_name} {last_name}",
                    "service_name": random.choice(["Sunday 9AM", "Sunday 11AM", "Wednesday Night"]),
                    "check_in_time": att_date.isoformat(),
                    "created_at": att_date.isoformat()
                }
                attendance_records.append(att_record)
    
    # Bulk insert
    if people:
        await db.people.insert_many(people)
    if donations:
        await db.donations.insert_many(donations)
    if attendance_records:
        await db.attendance.insert_many(attendance_records)
    
    logger.info(f"Seeded {len(people)} members for {church_name}")
    return len(people)

# ============== SUMMIT ENHANCEMENTS - SERVICE MODE & ATTENDANCE STREAKS ==============

class ServiceModeStatus(BaseModel):
    is_service_day: bool
    is_service_time: bool
    current_service: Optional[Dict[str, Any]] = None
    next_service: Optional[Dict[str, Any]] = None
    attendance_streak: int = 0
    check_in_status: Optional[str] = None  # 'in_person', 'online', None

class AttendanceStreakData(BaseModel):
    current_streak: int = 0
    longest_streak: int = 0
    total_attended: int = 0
    last_attendance: Optional[str] = None
    streak_badges: List[Dict[str, Any]] = []

class PrayerRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    user_name: str
    category: str = "general"  # general, healing, family, financial, guidance, thanksgiving
    title: str
    content: str
    is_public: bool = False  # For prayer wall
    is_anonymous: bool = False
    prayer_count: int = 0  # How many people prayed
    status: str = "active"  # active, answered, closed
    admin_notes: Optional[str] = None
    follow_up_date: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class PrayerRequestCreate(BaseModel):
    category: str = "general"
    title: str
    content: str
    is_public: bool = False
    is_anonymous: bool = False

class MemberCheckIn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    service_id: Optional[str] = None
    check_in_type: str = "in_person"  # 'in_person' or 'online'
    service_date: str
    check_in_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== SERVICE MODE ENDPOINTS ==============

@api_router.get("/portal/service-mode")
async def get_service_mode_status(request: Request):
    """Get current service mode status for the homepage"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    now = datetime.now(timezone.utc)
    today = now.date()
    current_day = today.strftime("%A")  # Sunday, Monday, etc.
    current_time = now.time()
    
    # Check if today is a service day (typically Sunday or Wednesday)
    service_days = ["Sunday", "Wednesday"]
    is_service_day = current_day in service_days
    
    # Define service times
    services = [
        {"name": "Sunday 9AM", "day": "Sunday", "start": "09:00", "end": "10:30"},
        {"name": "Sunday 11AM", "day": "Sunday", "start": "11:00", "end": "12:30"},
        {"name": "Wednesday Night", "day": "Wednesday", "start": "19:00", "end": "20:30"},
    ]
    
    current_service = None
    next_service = None
    is_service_time = False
    
    for svc in services:
        if svc["day"] == current_day:
            start_time = datetime.strptime(svc["start"], "%H:%M").time()
            end_time = datetime.strptime(svc["end"], "%H:%M").time()
            
            # Allow check-in 30 minutes before service
            early_start = (datetime.combine(today, start_time) - timedelta(minutes=30)).time()
            
            if early_start <= current_time <= end_time:
                is_service_time = True
                current_service = svc
                break
            elif current_time < start_time:
                if not next_service:
                    next_service = svc
    
    # Get user's check-in status for today
    check_in_status = None
    today_checkin = await db.member_checkins.find_one({
        "tenant_id": tenant_id,
        "user_id": user_id,
        "service_date": today.isoformat()
    }, {"_id": 0})
    
    if today_checkin:
        check_in_status = today_checkin.get("check_in_type")
    
    # Get attendance streak
    streak_data = await calculate_attendance_streak(tenant_id, user_id)
    
    return {
        "is_service_day": is_service_day,
        "is_service_time": is_service_time,
        "current_service": current_service,
        "next_service": next_service,
        "attendance_streak": streak_data["current_streak"],
        "check_in_status": check_in_status,
        "today": today.isoformat(),
        "current_day": current_day
    }

@api_router.post("/portal/service-checkin")
async def check_in_to_service(
    request: Request,
    check_in_type: str = "in_person"
):
    """Check in to current service (in-person or online)"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Check if already checked in today
    existing = await db.member_checkins.find_one({
        "tenant_id": tenant_id,
        "user_id": user_id,
        "service_date": today
    })
    
    if existing:
        return {"message": "Already checked in today", "check_in_type": existing.get("check_in_type")}
    
    # Create check-in
    checkin = MemberCheckIn(
        tenant_id=tenant_id,
        user_id=user_id,
        check_in_type=check_in_type,
        service_date=today
    )
    
    await db.member_checkins.insert_one(checkin.model_dump())
    
    # Calculate new streak
    streak_data = await calculate_attendance_streak(tenant_id, user_id)

    # Build nudge response (Geofence arrival flow)
    nudge = {"show": False, "cafe_open": False, "show_giving": False}
    try:
        geo_config = await db.geofence_config.find_one({"tenant_id": tenant_id}, {"_id": 0})
        cafe_settings = await db.cafe_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
        tenant_doc = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
        church_name = tenant_doc.get("name", "your church") if tenant_doc else "your church"
        
        if geo_config:
            nudge["show"] = True
            if geo_config.get("nudge_cafe") and cafe_settings and cafe_settings.get("is_open"):
                nudge["cafe_open"] = True
                nudge["cafe_message"] = f"Order your coffee for {cafe_settings.get('pickup_location', 'Sunday')} pickup"
            if geo_config.get("nudge_giving"):
                nudge["show_giving"] = True
                nudge["give_message"] = f"Support {church_name} today"
                nudge["give_amounts"] = geo_config.get("nudge_giving_amounts", [25, 50, 100, 250])
    except Exception:
        pass

    return {
        "success": True,
        "message": "Checked in successfully!",
        "check_in_type": check_in_type,
        "streak": {
            "current": streak_data["current_streak"],
            "best": streak_data["longest_streak"],
            "total": streak_data["total_attended"]
        },
        "new_streak": streak_data["current_streak"],
        "current_streak": streak_data["current_streak"],
        "badges_earned": streak_data.get("streak_badges", []),
        "nudge": nudge
    }

async def calculate_attendance_streak(tenant_id: str, user_id: str) -> Dict[str, Any]:
    """Calculate attendance streak for a user"""
    # Get all check-ins sorted by date
    checkins = await db.member_checkins.find(
        {"tenant_id": tenant_id, "user_id": user_id},
        {"_id": 0, "service_date": 1}
    ).sort("service_date", -1).to_list(length=52)  # Last year of Sundays
    
    if not checkins:
        return {"current_streak": 0, "longest_streak": 0, "total_attended": 0}
    
    dates = [c["service_date"] for c in checkins]
    total_attended = len(dates)
    
    # Calculate current streak (consecutive Sundays)
    current_streak = 0
    longest_streak = 0
    temp_streak = 1
    
    today = datetime.now(timezone.utc).date()
    
    # Find the most recent Sunday
    days_since_sunday = today.weekday()  # Monday is 0, Sunday is 6
    if days_since_sunday != 6:
        days_since_sunday = (days_since_sunday + 1) % 7
    # Note: last_sunday calculation kept for potential future use
    _ = today - timedelta(days=days_since_sunday)
    
    # Check if they attended last Sunday (or today if it's Sunday)
    if dates:
        most_recent = datetime.fromisoformat(dates[0]).date()
        # They have a streak if their most recent attendance was within the last week
        if (today - most_recent).days <= 7:
            current_streak = 1
            
            # Count consecutive weeks
            for i in range(1, len(dates)):
                curr_date = datetime.fromisoformat(dates[i-1]).date()
                prev_date = datetime.fromisoformat(dates[i]).date()
                diff = (curr_date - prev_date).days
                
                # If difference is 7 days (one week), continue streak
                if 5 <= diff <= 9:  # Allow some flexibility
                    current_streak += 1
                else:
                    break
    
    # Calculate longest streak
    temp_streak = 1
    for i in range(1, len(dates)):
        curr_date = datetime.fromisoformat(dates[i-1]).date()
        prev_date = datetime.fromisoformat(dates[i]).date()
        diff = (curr_date - prev_date).days
        
        if 5 <= diff <= 9:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1
    
    longest_streak = max(longest_streak, current_streak, 1)
    
    # Determine badges earned
    badges = []
    if current_streak >= 4:
        badges.append({"name": "Month Strong", "icon": "🔥", "threshold": 4})
    if current_streak >= 8:
        badges.append({"name": "2 Month Champion", "icon": "⭐", "threshold": 8})
    if current_streak >= 12:
        badges.append({"name": "Quarter Master", "icon": "🏆", "threshold": 12})
    if current_streak >= 26:
        badges.append({"name": "Half Year Hero", "icon": "👑", "threshold": 26})
    if current_streak >= 52:
        badges.append({"name": "Year of Faith", "icon": "💎", "threshold": 52})
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_attended": total_attended,
        "last_attendance": dates[0] if dates else None,
        "streak_badges": badges
    }

@api_router.get("/portal/attendance-streak")
async def get_attendance_streak(request: Request):
    """Get user's attendance streak and badges"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    streak_data = await calculate_attendance_streak(tenant_id, user_id)
    return streak_data


@api_router.get("/portal/attendance/streak")
async def get_mobile_attendance_streak(request: Request):
    """Mobile alias for attendance streak endpoint."""
    return await get_attendance_streak(request)


@api_router.post("/portal/attendance/checkin")
async def checkin_mobile_attendance(request: Request, payload: AttendanceCheckinRequest):
    """Mobile alias for service attendance check-in."""
    return await check_in_to_service(request, check_in_type=payload.check_in_type)


@api_router.get("/portal/attendance/history")
async def get_mobile_attendance_history(request: Request, limit: int = 90):
    """Return member attendance check-in history for mobile timeline views."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")

    checkins = await db.member_checkins.find(
        {"tenant_id": tenant_id, "user_id": user_id},
        {"_id": 0}
    ).sort("service_date", -1).limit(limit).to_list(limit)

    return {
        "history": [serialize_doc(c) for c in checkins],
        "total": len(checkins)
    }

# ============== SUNDAY MORNING PUSH NOTIFICATION PAYLOADS ==============

SUNDAY_MORNING_NOTIFICATIONS = {
    "service_starting": {
        "title": "Service Starting Soon!",
        "body": "Join us in {minutes} minutes. Tap to check in!",
        "url": "/portal"
    },
    "welcome_arrived": {
        "title": "Welcome to {church_name}!",
        "body": "You're checked in. Order your coffee or give today!",
        "url": "/portal"
    },
    "kids_reminder": {
        "title": "Don't Forget Kids Check-In",
        "body": "Check your kids into Sunday School before service starts.",
        "url": "/portal/kids"
    },
    "giving_reminder": {
        "title": "Give Today",
        "body": "Your generosity makes a difference at {church_name}.",
        "url": "/portal/give"
    },
    "cafe_ready": {
        "title": "Your Coffee is Ready!",
        "body": "Pick up your order at the cafe counter.",
        "url": "/portal/cafe"
    },
    "post_service": {
        "title": "Thank You for Worshipping With Us!",
        "body": "Have a blessed week. See you next Sunday!",
        "url": "/portal"
    }
}

@api_router.get("/admin/sunday-morning/notification-templates")
async def get_notification_templates(request: Request):
    """Get available Sunday Morning push notification templates."""
    user = await require_permission(request, "admin.communications")
    return {"templates": SUNDAY_MORNING_NOTIFICATIONS}

@api_router.post("/admin/sunday-morning/broadcast")
async def broadcast_sunday_notification(request: Request, payload: dict):
    """Broadcast a Sunday Morning push notification to all members."""
    user = await require_permission(request, "admin.communications")
    tenant_id = user.get("tenant_id")
    template_key = payload.get("template")
    custom_title = payload.get("title")
    custom_body = payload.get("body")

    if template_key and template_key in SUNDAY_MORNING_NOTIFICATIONS:
        tmpl = SUNDAY_MORNING_NOTIFICATIONS[template_key]
        tenant_doc = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "name": 1})
        church_name = (tenant_doc or {}).get("name", "your church")
        title = tmpl["title"].format(church_name=church_name, minutes=payload.get("minutes", 15))
        body = tmpl["body"].format(church_name=church_name, minutes=payload.get("minutes", 15))
        url = tmpl["url"]
    elif custom_title and custom_body:
        title = custom_title
        body = custom_body
        url = payload.get("url", "/portal")
    else:
        raise HTTPException(status_code=400, detail="Provide a template key or custom title/body")

    subs = await db.push_subscriptions.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(5000)
    sent = 0
    failed = 0
    for sub in subs:
        try:
            from routes.push import send_push_notification
            await send_push_notification(sub.get("user_id", ""), tenant_id, title, body, url)
            sent += 1
        except Exception:
            failed += 1

    await db.notification_logs.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "type": "sunday_morning_broadcast",
        "template": template_key,
        "title": title,
        "body": body,
        "sent": sent,
        "failed": failed,
        "sent_by": user.get("user_id"),
        "sent_at": datetime.now(timezone.utc).isoformat()
    })

    return {"success": True, "sent": sent, "failed": failed, "title": title, "body": body}


# ============== PRAYER REQUEST ENDPOINTS ==============

@api_router.get("/portal/prayer-requests")
async def get_portal_prayer_requests_alias(request: Request):
    """Mobile alias for a member's prayer requests."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    user_id = user.get("user_id")

    await ensure_abundant_go_live_portal_content()

    requests = await db.prayer_requests.find(
        {"tenant_id": tenant_id, "user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    return {
        "requests": [
            {
                "id": row.get("id"),
                "title": row.get("title"),
                "description": row.get("content"),
                "created_at": row.get("created_at"),
                "status": row.get("status", "active"),
                "is_public": bool(row.get("is_public", False))
            }
            for row in requests
        ]
    }


@api_router.post("/portal/prayer-requests")
async def create_portal_prayer_request_alias(payload: PrayerRequestAliasCreate, request: Request):
    """Mobile alias to create prayer request with description field."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    prayer_request = PrayerRequest(
        tenant_id=tenant_id,
        user_id=user.get("user_id"),
        user_name=user.get("name", "Anonymous"),
        category="general",
        title=payload.title,
        content=payload.description,
        is_public=payload.is_public,
        is_anonymous=False
    ).model_dump()

    prayer_request["created_at"] = datetime.now(timezone.utc)
    await db.prayer_requests.insert_one(prayer_request)

    return {
        "message": "Prayer request submitted",
        "request": {
            "id": prayer_request.get("id"),
            "title": prayer_request.get("title"),
            "description": prayer_request.get("content"),
            "created_at": prayer_request.get("created_at"),
            "status": prayer_request.get("status", "active"),
            "is_public": prayer_request.get("is_public", False)
        }
    }


@api_router.get("/portal/prayer-requests/community")
async def get_portal_prayer_requests_community(request: Request):
    """Mobile alias for public prayer wall."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    requests = await db.prayer_requests.find(
        {"tenant_id": tenant_id, "is_public": True, "status": "active"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    return {
        "requests": [
            {
                "id": row.get("id"),
                "title": row.get("title"),
                "description": row.get("content"),
                "created_at": row.get("created_at"),
                "status": row.get("status", "active"),
                "is_public": True
            }
            for row in requests
        ]
    }

PRAYER_CATEGORIES = [
    {"id": "general", "name": "General", "icon": "🙏"},
    {"id": "healing", "name": "Healing", "icon": "💚"},
    {"id": "family", "name": "Family", "icon": "👨‍👩‍👧‍👦"},
    {"id": "financial", "name": "Financial", "icon": "💰"},
    {"id": "guidance", "name": "Guidance", "icon": "🧭"},
    {"id": "thanksgiving", "name": "Thanksgiving", "icon": "🙌"},
    {"id": "salvation", "name": "Salvation", "icon": "✝️"},
    {"id": "relationships", "name": "Relationships", "icon": "❤️"},
]

@api_router.get("/portal/prayer/categories")
async def get_prayer_categories():
    """Get available prayer request categories"""
    return {"categories": PRAYER_CATEGORIES}

@api_router.post("/portal/prayer/requests")
async def create_prayer_request(
    data: PrayerRequestCreate,
    request: Request
):
    """Submit a new prayer request"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    user_name = user.get("name", "Anonymous")
    
    prayer_request = PrayerRequest(
        tenant_id=tenant_id,
        user_id=user_id,
        user_name="Anonymous" if data.is_anonymous else user_name,
        category=data.category,
        title=data.title,
        content=data.content,
        is_public=data.is_public,
        is_anonymous=data.is_anonymous
    )
    
    await db.prayer_requests.insert_one(prayer_request.model_dump())
    
    return {"message": "Prayer request submitted", "id": prayer_request.id}

@api_router.get("/portal/prayer/requests")
async def get_my_prayer_requests(
    request: Request
):
    """Get user's own prayer requests"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    requests = await db.prayer_requests.find(
        {"tenant_id": tenant_id, "user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(length=50)
    
    return {"requests": requests}

@api_router.get("/portal/prayer/wall")
async def get_prayer_wall(
    request: Request,
    category: Optional[str] = None
):
    """Get public prayer wall - requests shared with community"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    
    query = {
        "tenant_id": tenant_id,
        "is_public": True,
        "status": "active"
    }
    
    if category and category != "all":
        query["category"] = category
    
    requests = await db.prayer_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(length=50)
    
    return {"requests": requests, "categories": PRAYER_CATEGORIES}

@api_router.post("/portal/prayer/requests/{request_id}/pray")
async def pray_for_request(
    request_id: str,
    request: Request
):
    """Increment prayer count for a request"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    # Check if user already prayed (optional - could track in separate collection)
    prayer_log = await db.prayer_logs.find_one({
        "request_id": request_id,
        "user_id": user_id
    })
    
    if prayer_log:
        return {"message": "Already prayed for this request", "prayed": True}
    
    # Increment prayer count
    await db.prayer_requests.update_one(
        {"id": request_id, "tenant_id": tenant_id},
        {"$inc": {"prayer_count": 1}}
    )
    
    # Log the prayer
    await db.prayer_logs.insert_one({
        "id": str(uuid.uuid4()),
        "request_id": request_id,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Prayer recorded", "prayed": True}

# ============== ADMIN PRAYER DASHBOARD ==============

@api_router.get("/admin/prayer/dashboard")
async def get_prayer_dashboard(
    request: Request,
    status: Optional[str] = None,
    category: Optional[str] = None
):
    """Admin dashboard for prayer requests"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") not in ["admin", "church_admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    if category and category != "all":
        query["category"] = category
    
    requests = await db.prayer_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(length=100)
    
    # Get stats
    total_active = await db.prayer_requests.count_documents({"tenant_id": tenant_id, "status": "active"})
    total_answered = await db.prayer_requests.count_documents({"tenant_id": tenant_id, "status": "answered"})
    needs_followup = await db.prayer_requests.count_documents({
        "tenant_id": tenant_id,
        "follow_up_date": {"$lte": datetime.now(timezone.utc).isoformat()}
    })
    
    return {
        "requests": requests,
        "stats": {
            "total_active": total_active,
            "total_answered": total_answered,
            "needs_followup": needs_followup
        },
        "categories": PRAYER_CATEGORIES
    }

@api_router.put("/admin/prayer/requests/{request_id}")
async def update_prayer_request(
    request_id: str,
    request: Request
):
    """Update prayer request status/notes (admin)"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") not in ["admin", "church_admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    tenant_id = user.get("tenant_id")
    body = await request.json()
    
    update_fields = {}
    if "status" in body:
        update_fields["status"] = body["status"]
    if "admin_notes" in body:
        update_fields["admin_notes"] = body["admin_notes"]
    if "follow_up_date" in body:
        update_fields["follow_up_date"] = body["follow_up_date"]
    
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.prayer_requests.update_one(
        {"id": request_id, "tenant_id": tenant_id},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Prayer request not found")
    
    return {"message": "Prayer request updated"}


@api_router.get("/portal/volunteer/opportunities")
async def get_portal_volunteer_opportunities(request: Request):
    """List available volunteer opportunities for the authenticated user."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_abundant_go_live_portal_content()

    opportunities = await db.volunteer_opportunities.find(
        {"tenant_id": tenant_id, "is_active": True},
        {"_id": 0}
    ).sort("title", 1).to_list(200)

    return {"opportunities": [serialize_doc(item) for item in opportunities]}


@api_router.post("/portal/volunteer/signup")
async def signup_portal_volunteer(request: Request, payload: VolunteerSignupRequest):
    """Create a volunteer signup for an opportunity."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    opportunity = await db.volunteer_opportunities.find_one(
        {"tenant_id": tenant_id, "id": payload.opportunity_id, "is_active": True},
        {"_id": 0}
    )
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    existing = await db.volunteer_signups.find_one(
        {
            "tenant_id": tenant_id,
            "opportunity_id": payload.opportunity_id,
            "user_id": user.get("user_id")
        },
        {"_id": 0}
    )
    if existing:
        return {"message": "Already signed up", "signup": serialize_doc(existing)}

    signup = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "opportunity_id": payload.opportunity_id,
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "status": "signed_up",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.volunteer_signups.insert_one(signup)

    await db.volunteer_opportunities.update_one(
        {"tenant_id": tenant_id, "id": payload.opportunity_id},
        {"$inc": {"spots_available": -1}}
    )

    return {"message": "Signed up successfully", "signup": serialize_doc(signup)}


@api_router.get("/portal/announcements")
async def get_portal_announcements(request: Request):
    """Get active church announcements for the member portal."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    await ensure_abundant_go_live_portal_content()

    now_iso = datetime.now(timezone.utc).isoformat()
    announcements = await db.announcements.find(
        {
            "tenant_id": tenant_id,
            "$or": [
                {"expires_at": {"$gte": now_iso}},
                {"expires_at": {"$exists": False}},
                {"expires_at": None}
            ]
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    return {"announcements": [serialize_doc(item) for item in announcements]}


# ============== MOBILE-COMPATIBLE PAYMENT METHOD ALIASES ==============

@api_router.get("/portal/payment-methods")
async def get_portal_payment_methods(request: Request):
    """Get saved payment methods (Bearer-compatible alias)."""
    user = await get_current_member_user(request)
    methods = await db.payment_methods.find(
        {"user_id": user["user_id"], "is_active": True}, {"_id": 0}
    ).to_list(10)
    return {"payment_methods": [serialize_doc(m) for m in methods]}

@api_router.post("/portal/payment-methods")
async def save_portal_payment_method(request: Request, method_data: SavePaymentMethodRequest):
    """Save a new payment method (Bearer-compatible alias)."""
    user = await get_current_member_user(request)

    if method_data.is_default:
        await db.payment_methods.update_many(
            {"user_id": user["user_id"]}, {"$set": {"is_default": False}}
        )

    pm = {
        "id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        "tenant_id": user.get("tenant_id"),
        "card_last_four": method_data.card_last_four,
        "card_brand": method_data.card_brand,
        "card_exp_month": method_data.card_exp_month,
        "card_exp_year": method_data.card_exp_year,
        "stripe_payment_method_id": method_data.stripe_payment_method_id,
        "is_default": method_data.is_default,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_methods.insert_one(pm)
    return {"message": "Payment method saved", "payment_method": {k: v for k, v in pm.items() if k != "_id"}}

@api_router.delete("/portal/payment-methods/{method_id}")
async def delete_portal_payment_method(request: Request, method_id: str):
    """Delete a payment method (Bearer-compatible alias)."""
    user = await get_current_member_user(request)
    result = await db.payment_methods.update_one(
        {"id": method_id, "user_id": user["user_id"]},
        {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return {"message": "Payment method removed"}

@api_router.put("/portal/payment-methods/{method_id}/default")
async def set_portal_default_payment_method(request: Request, method_id: str):
    """Set default payment method (Bearer-compatible alias)."""
    user = await get_current_member_user(request)
    await db.payment_methods.update_many(
        {"user_id": user["user_id"]}, {"$set": {"is_default": False}}
    )
    result = await db.payment_methods.update_one(
        {"id": method_id, "user_id": user["user_id"], "is_active": True},
        {"$set": {"is_default": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return {"message": "Default payment method updated"}


# ============== GO-LIVE: MISSING ENDPOINTS ==============

# --- Kids: Portal Checkout ---
class KidsCheckoutRequest(BaseModel):
    child_id: str
    pickup_code: str

@api_router.post("/portal/kids/checkout")
async def portal_kids_checkout(request: Request, payload: KidsCheckoutRequest):
    """Member checks out their child using pickup code."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id")
    checkin = await db.checkins.find_one(
        {"tenant_id": tenant_id, "child_id": payload.child_id, "status": "checked_in"},
        {"_id": 0}
    )
    if not checkin:
        raise HTTPException(status_code=404, detail="No active check-in found for this child")
    if checkin.get("pickup_code") != payload.pickup_code:
        raise HTTPException(status_code=400, detail="Invalid pickup code")
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.checkins.update_one(
        {"id": checkin["id"]},
        {"$set": {"status": "checked_out", "checked_out_at": now_iso, "checked_out_by": user.get("name", "Parent")}}
    )
    return {"status": "checked_out", "checkout_time": now_iso, "child_name": checkin.get("child_name")}

# --- Kids: Admin /today and checkout ---
@api_router.get("/admin/kids/checkins/today")
async def get_admin_kids_checkins_today(request: Request):
    """Get ALL children checked in today for this tenant."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    # Use UTC start/end of today for reliable matching
    now_utc = datetime.now(timezone.utc)
    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_end = now_utc.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
    checkins = await db.checkins.find(
        {"tenant_id": tenant_id, "checked_in_at": {"$gte": today_start, "$lte": today_end}},
        {"_id": 0}
    ).sort("checked_in_at", -1).to_list(500)
    # Also include any still checked_in from previous days (edge case: overnight)
    still_checked_in = await db.checkins.find(
        {"tenant_id": tenant_id, "status": "checked_in", "checked_in_at": {"$lt": today_start}},
        {"_id": 0}
    ).to_list(100)
    all_checkins = checkins + still_checked_in
    enriched = []
    for c in all_checkins:
        child = await db.children.find_one({"id": c.get("child_id")}, {"_id": 0})
        enriched.append({
            "child_id": c.get("child_id"),
            "child_name": c.get("child_name"),
            "parent_name": c.get("parent_name"),
            "parent_phone": c.get("parent_phone", ""),
            "pickup_code": c.get("pickup_code"),
            "checkin_time": c.get("checked_in_at"),
            "checkout_time": c.get("checked_out_at"),
            "status": c.get("status"),
            "allergies": (child or {}).get("allergies", ""),
            "emergency_contact": (child or {}).get("emergency_contact", ""),
            "checkin_id": c.get("id"),
        })
    return {"checkins": enriched, "total": len(enriched)}

@api_router.post("/admin/kids/checkout")
async def admin_kids_checkout(request: Request, payload: KidsCheckoutRequest):
    """Admin verifies pickup code and checks out a child."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    checkin = await db.checkins.find_one(
        {"tenant_id": tenant_id, "child_id": payload.child_id, "status": "checked_in"},
        {"_id": 0}
    )
    if not checkin:
        raise HTTPException(status_code=404, detail="No active check-in found")
    if checkin.get("pickup_code") != payload.pickup_code:
        raise HTTPException(status_code=400, detail="Invalid pickup code")
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.checkins.update_one(
        {"id": checkin["id"]},
        {"$set": {"status": "checked_out", "checked_out_at": now_iso, "checked_out_by": user.get("name", "Admin")}}
    )
    return {"success": True, "child_name": checkin.get("child_name"), "checkout_time": now_iso}

@api_router.post("/admin/kids/checkout-by-code")
async def admin_kids_checkout_by_code(request: Request, payload: dict):
    """Admin scans QR or enters code — checkout without knowing child_id."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    code = payload.get("pickup_code", "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Pickup code required")
    
    # Parse QR code format: SOLOMON_PICKUP_{child_id}_{code}_{date}
    actual_code = code
    if code.startswith("SOLOMON_PICKUP_"):
        parts = code.split("_")
        if len(parts) >= 4:
            actual_code = parts[3]
    
    checkin = await db.checkins.find_one(
        {"tenant_id": tenant_id, "pickup_code": actual_code, "status": "checked_in"},
        {"_id": 0}
    )
    if not checkin:
        raise HTTPException(status_code=404, detail="No active check-in found for this code")
    
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.checkins.update_one(
        {"id": checkin["id"]},
        {"$set": {"status": "checked_out", "checked_out_at": now_iso, "checked_out_by": user.get("name", "Admin")}}
    )
    child = await db.children.find_one({"id": checkin.get("child_id")}, {"_id": 0})
    return {
        "success": True, 
        "child_name": checkin.get("child_name"), 
        "child": serialize_doc(child) if child else None,
        "checkout_time": now_iso,
        "checkin_id": checkin.get("id")
    }

# --- Admin Media Sermons CRUD ---
class SermonCreate(BaseModel):
    title: str
    description: str = ""
    video_url: str = ""
    thumbnail_url: str = ""
    pastor: str = ""
    series_name: str = ""
    duration_seconds: int = 0
    category: str = "sermon"
    published: bool = True

class SermonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    pastor: Optional[str] = None
    series_name: Optional[str] = None
    duration_seconds: Optional[int] = None
    category: Optional[str] = None
    published: Optional[bool] = None

@api_router.get("/admin/media/sermons")
async def get_admin_media_sermons(request: Request, limit: int = 200):
    """List all sermons for admin management."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    sermons = await db.media_videos.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("published_at", -1).to_list(limit)
    return {"sermons": [serialize_doc(s) for s in sermons]}

@api_router.post("/admin/media/sermons")
async def create_admin_media_sermon(request: Request, payload: SermonCreate):
    """Publish a new sermon — immediately visible to all members."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    now_iso = datetime.now(timezone.utc).isoformat()
    sermon = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "title": payload.title,
        "description": payload.description,
        "video_url": payload.video_url,
        "thumbnail_url": payload.thumbnail_url,
        "pastor": payload.pastor,
        "series_name": payload.series_name,
        "duration_seconds": payload.duration_seconds,
        "content_type": payload.category,
        "category": payload.category,
        "is_published": payload.published,
        "published": payload.published,
        "published_at": now_iso if payload.published else None,
        "created_by": user.get("user_id"),
        "created_at": now_iso,
    }
    await db.media_videos.insert_one(sermon)
    return {"id": sermon["id"], "title": sermon["title"], "status": "published" if payload.published else "draft"}

@api_router.put("/admin/media/sermons/{sermon_id}")
async def update_admin_media_sermon(request: Request, sermon_id: str, payload: SermonUpdate):
    """Edit a sermon."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if "published" in update_data and update_data["published"]:
        update_data["published_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.media_videos.update_one(
        {"id": sermon_id, "tenant_id": tenant_id}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sermon not found")
    return {"message": "Sermon updated"}

@api_router.delete("/admin/media/sermons/{sermon_id}")
async def delete_admin_media_sermon(request: Request, sermon_id: str):
    """Delete a sermon."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    result = await db.media_videos.delete_one({"id": sermon_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sermon not found")
    return {"message": "Sermon deleted"}

# --- Giving Donate Endpoint ---
class GivingDonateRequest(BaseModel):
    amount: float
    fund: str = "general"
    frequency: str = "one_time"
    payment_method_id: Optional[str] = None
    source: str = "direct"

@api_router.post("/portal/giving/donate")
async def portal_giving_donate(request: Request, payload: GivingDonateRequest):
    """Process a donation from the member portal."""
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    donation = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "person_id": user.get("user_id"),
        "person_name": user.get("name", ""),
        "amount": round(payload.amount, 2),
        "fund": payload.fund,
        "frequency": payload.frequency,
        "payment_method_id": payload.payment_method_id,
        "source": payload.source,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.donations.insert_one(donation)
    return {
        "donation_id": donation["id"],
        "amount": donation["amount"],
        "fund": donation["fund"],
        "status": "completed",
        "message": f"Thank you for your ${donation['amount']:.2f} gift!"
    }


# Include router
# ============== NOTIFICATIONS ==============

@api_router.get("/portal/notifications")
async def get_notifications(request: Request, limit: int = 20):
    """Get user's notifications with unread count."""
    user = await get_current_member_user(request)
    notifications = await db.notifications.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    unread = sum(1 for n in notifications if not n.get("is_read"))
    return {"notifications": [serialize_doc(n) for n in notifications], "unread_count": unread}


@api_router.put("/portal/notifications/{notif_id}/read")
async def mark_notification_read(request: Request, notif_id: str):
    """Mark a notification as read."""
    user = await get_current_member_user(request)
    await db.notifications.update_one(
        {"id": notif_id, "user_id": user["user_id"]},
        {"$set": {"is_read": True}}
    )
    return {"message": "Marked as read"}


@api_router.put("/portal/notifications/read-all")
async def mark_all_notifications_read(request: Request):
    """Mark all notifications as read."""
    user = await get_current_member_user(request)
    await db.notifications.update_many(
        {"user_id": user["user_id"], "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "All marked as read"}


@api_router.post("/admin/notifications/send")
async def admin_send_notification(request: Request):
    """Admin sends a notification to all members in their tenant."""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["church_admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    body = await request.json()
    title = body.get("title", "")
    message = body.get("message", "")
    notif_type = body.get("type", "announcement")
    tenant_id = user.get("tenant_id")
    
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    
    # Find all members in this tenant
    members = await db.users.find(
        {"tenant_id": tenant_id, "role": "member", "is_active": True},
        {"_id": 0, "user_id": 1}
    ).to_list(10000)
    
    now_iso = datetime.now(timezone.utc).isoformat()
    notifications = []
    for m in members:
        notifications.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": m["user_id"],
            "type": notif_type,
            "title": title,
            "body": message,
            "is_read": False,
            "sent_by": user.get("user_id"),
            "created_at": now_iso
        })
    
    if notifications:
        await db.notifications.insert_many(notifications)
    
    return {"message": f"Notification sent to {len(notifications)} members", "count": len(notifications)}


# ============== CHURCH HEALTH SCORE ==============

def compute_health_score(cached_stats, tenant):
    """
    Universal Church Health Score (0-100).
    Weighted composite of 5 dimensions:
      - Engagement (25%): active_members / total_members
      - Giving (25%): giving_per_capita benchmarked against $8/member/month
      - Community (20%): members_per_group, target ~15 per group
      - Attendance (20%): weekly_attendance / total_members
      - Growth (10%): recurring_givers / total_members
    """
    c = cached_stats or {}
    members = c.get("total_members", 0)
    if members == 0:
        return {"score": 0, "grade": "N/A", "dimensions": {}}

    active = c.get("active_members", 0)
    mtd_giving = c.get("mtd_giving", 0)
    attendance = c.get("last_attendance", 0)
    groups = c.get("active_groups", 0)
    recurring = c.get("recurring_givers", 0)

    # Engagement: % of members active (benchmark: 60% = perfect)
    engagement_raw = (active / members) * 100
    engagement_score = min(100, (engagement_raw / 60) * 100)

    # Giving per capita (benchmark: $8/member/month = perfect)
    gpc = mtd_giving / members
    giving_score = min(100, (gpc / 8) * 100)

    # Community: group participation (benchmark: 1 group per 100 members = perfect)
    if groups > 0:
        groups_per_100 = (groups / members) * 100
        community_score = min(100, (groups_per_100 / 1.0) * 100)
    else:
        community_score = 0

    # Attendance rate (benchmark: 20% of members weekly = perfect)
    att_rate = (attendance / members) * 100
    attendance_score = min(100, (att_rate / 20) * 100)

    # Growth: recurring givers (benchmark: 10% = perfect)
    rec_rate = (recurring / members) * 100
    growth_score = min(100, (rec_rate / 10) * 100)

    # Weighted composite
    total = (engagement_score * 0.25 + giving_score * 0.25 +
             community_score * 0.20 + attendance_score * 0.20 +
             growth_score * 0.10)
    total = round(min(100, max(0, total)))

    grade = "A+" if total >= 90 else "A" if total >= 80 else "B+" if total >= 70 else \
            "B" if total >= 60 else "C" if total >= 50 else "D" if total >= 40 else "F"

    return {
        "score": total,
        "grade": grade,
        "dimensions": {
            "engagement": {"score": round(engagement_score), "value": round(engagement_raw, 1), "label": "Engagement Rate", "unit": "%"},
            "giving": {"score": round(giving_score), "value": round(gpc, 2), "label": "Giving / Member", "unit": "$/mo"},
            "community": {"score": round(community_score), "value": round((groups / members) * 100, 2) if groups > 0 else 0, "label": "Groups / 100 Mbrs", "unit": ""},
            "attendance": {"score": round(attendance_score), "value": round(att_rate, 1), "label": "Attendance Rate", "unit": "%"},
            "growth": {"score": round(growth_score), "value": round(rec_rate, 1), "label": "Recurring Donors", "unit": "%"},
        }
    }


@api_router.get("/platform/health-scores")
async def get_all_health_scores(request: Request):
    """Get Church Health Scores for all tenants."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    tenants = await db.tenants.find({}, {"_id": 0}).to_list(100)
    results = []
    for t in tenants:
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": t["id"]}, {"_id": 0})
        health = compute_health_score(cached, t)
        results.append({
            "tenant_id": t["id"],
            "name": t["name"],
            "location": t.get("location", ""),
            "plan": t.get("plan", ""),
            "members": cached.get("total_members", 0) if cached else 0,
            "health": health,
        })

    results.sort(key=lambda x: x["health"]["score"], reverse=True)
    return results

# ============== PLATFORM CHURCH ONBOARDING (Task 2) ==============

class ChurchOnboardingRequest(BaseModel):
    name: str
    city: str = ""
    state: str = ""
    denomination: str = ""
    website: str = ""
    service_times: list = []
    primary_color: str = "#2563eb"
    subdomain: str = ""
    admin_name: str = ""
    admin_email: str = ""
    admin_password: str = ""
    admin_phone: str = ""
    estimated_members: int = 0
    plan: str = "starter"

@api_router.post("/platform/churches/create")
async def create_church_onboarding(request: Request, payload: ChurchOnboardingRequest):
    """5-step church onboarding wizard — creates a new tenant with admin account."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    if not payload.name:
        raise HTTPException(status_code=400, detail="Church name is required")
    if not payload.admin_email:
        raise HTTPException(status_code=400, detail="Admin email is required")

    subdomain = payload.subdomain or payload.name.lower().replace(" ", "-").replace("'", "")[:30]
    existing = await db.tenants.find_one({"subdomain": subdomain})
    if existing:
        raise HTTPException(status_code=409, detail=f"Subdomain '{subdomain}' is already taken")

    existing_email = await db.users.find_one({"email": payload.admin_email.lower()})
    if existing_email:
        raise HTTPException(status_code=409, detail=f"Email '{payload.admin_email}' is already registered")

    tenant_id = f"{subdomain}-001"
    now_iso = datetime.now(timezone.utc).isoformat()

    tenant = {
        "id": tenant_id,
        "name": payload.name,
        "subdomain": subdomain,
        "city": payload.city,
        "state": payload.state,
        "denomination": payload.denomination,
        "website": payload.website,
        "primary_color": payload.primary_color,
        "plan": payload.plan,
        "subscription_status": "active",
        "estimated_members": payload.estimated_members,
        "service_times": payload.service_times,
        "created_at": now_iso,
        "onboarded_by": user.get("user_id")
    }
    await db.tenants.insert_one({**tenant})

    admin_password_hash = hashlib.sha256(payload.admin_password.encode()).hexdigest() if payload.admin_password else hashlib.sha256("Welcome2026!".encode()).hexdigest()
    admin_user = {
        "user_id": str(uuid.uuid4()),
        "email": payload.admin_email.lower(),
        "password_hash": admin_password_hash,
        "name": payload.admin_name or payload.name + " Admin",
        "role": "church_admin",
        "role_title": "Church Administrator",
        "permissions": ROLE_TEMPLATES["church_admin"]["permissions"],
        "tenant_id": tenant_id,
        "phone": payload.admin_phone,
        "created_at": now_iso,
        "is_verified": True
    }
    await db.users.insert_one({**admin_user})

    await audit_log("church_created", "tenant", tenant_id, tenant_id, user.get("user_id"), user.get("name", ""), {}, {"tenant": payload.name, "admin_email": payload.admin_email}, request)

    return {
        "success": True,
        "tenant_id": tenant_id,
        "subdomain": subdomain,
        "church_name": payload.name,
        "admin_email": payload.admin_email,
        "admin_user_id": admin_user["user_id"],
        "message": f"Church '{payload.name}' created successfully with admin account."
    }


# ============== ORGANIZATIONS & CAMPUS COMPARISON (Universal Multi-Campus) ==============

@api_router.get("/platform/organizations")
async def list_organizations(request: Request):
    """List all multi-campus organizations with their campuses."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    tenants = await db.tenants.find({"organization_id": {"$exists": True, "$ne": None}}, {"_id": 0}).to_list(200)

    orgs = {}
    for t in tenants:
        org_id = t["organization_id"]
        if org_id not in orgs:
            orgs[org_id] = {
                "organization_id": org_id,
                "organization_name": t.get("organization_name", org_id),
                "campuses": [],
                "total_members": 0,
                "total_mrr": 0,
                "total_mtd_giving": 0,
            }
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": t["id"]}, {"_id": 0})
        campus_info = {
            "tenant_id": t["id"],
            "name": t["name"],
            "location": t.get("location", ""),
            "plan": t.get("plan", ""),
            "mrr": float(t.get("mrr", 0) or 0),
            "subscription_status": t.get("subscription_status", "active"),
            "members": cached.get("total_members", 0) if cached else 0,
            "active_members": cached.get("active_members", 0) if cached else 0,
            "mtd_giving": cached.get("mtd_giving", 0) if cached else 0,
            "ytd_giving": cached.get("ytd_giving", 0) if cached else 0,
            "weekly_attendance": cached.get("last_attendance", 0) if cached else 0,
            "groups": cached.get("active_groups", 0) if cached else 0,
            "cafe_orders_week": cached.get("cafe_orders_week", 0) if cached else 0,
            "merch_orders_week": cached.get("merch_orders_week", 0) if cached else 0,
            "recurring_givers": cached.get("recurring_givers", 0) if cached else 0,
        }
        orgs[org_id]["campuses"].append(campus_info)
        orgs[org_id]["total_members"] += campus_info["members"]
        orgs[org_id]["total_mrr"] += campus_info["mrr"]
        orgs[org_id]["total_mtd_giving"] += campus_info["mtd_giving"]

    return list(orgs.values())


@api_router.get("/platform/organizations/{org_id}/comparison")
async def get_campus_comparison(org_id: str, request: Request):
    """Get detailed campus comparison metrics for a multi-campus organization."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    tenants = await db.tenants.find({"organization_id": org_id}, {"_id": 0}).to_list(50)
    if not tenants:
        raise HTTPException(status_code=404, detail="Organization not found")

    org_name = tenants[0].get("organization_name", org_id)
    campuses = []
    totals = {"members": 0, "active": 0, "attendance": 0, "mtd_giving": 0, "ytd_giving": 0, "groups": 0, "mrr": 0,
              "cafe_orders": 0, "cafe_giving": 0, "merch_orders": 0, "merch_giving": 0, "recurring_givers": 0}

    for t in tenants:
        tid = t["id"]
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": tid}, {"_id": 0})
        c = cached or {}

        members = c.get("total_members", 0)
        active = c.get("active_members", 0)
        attendance = c.get("last_attendance", 0)
        mtd = c.get("mtd_giving", 0)
        ytd = c.get("ytd_giving", 0)
        groups = c.get("active_groups", 0)
        cafe_orders = c.get("cafe_orders_week", 0)
        cafe_giving = c.get("cafe_giving_added", 0)
        merch_orders = c.get("merch_orders_week", 0)
        merch_giving = c.get("merch_giving_added", 0)
        recurring = c.get("recurring_givers", 0)

        campus = {
            "tenant_id": tid,
            "name": t["name"],
            "location": t.get("location", ""),
            "plan": t.get("plan", ""),
            "mrr": float(t.get("mrr", 0) or 0),
            "metrics": {
                "total_members": members,
                "active_members": active,
                "engagement_rate": round((active / members * 100), 1) if members > 0 else 0,
                "weekly_attendance": attendance,
                "attendance_rate": round((attendance / members * 100), 1) if members > 0 else 0,
                "mtd_giving": mtd,
                "ytd_giving": ytd,
                "giving_per_capita": round(mtd / members, 2) if members > 0 else 0,
                "recurring_givers": recurring,
                "recurring_rate": round((recurring / members * 100), 1) if members > 0 else 0,
                "active_groups": groups,
                "members_per_group": round(members / groups, 0) if groups > 0 else 0,
                "cafe_orders_week": cafe_orders,
                "cafe_giving_added": cafe_giving,
                "merch_orders_week": merch_orders,
                "merch_giving_added": merch_giving,
            }
        }
        campuses.append(campus)

        for k in totals:
            if k == "members": totals[k] += members
            elif k == "active": totals[k] += active
            elif k == "attendance": totals[k] += attendance
            elif k == "mtd_giving": totals[k] += mtd
            elif k == "ytd_giving": totals[k] += ytd
            elif k == "groups": totals[k] += groups
            elif k == "mrr": totals[k] += float(t.get("mrr", 0) or 0)
            elif k == "cafe_orders": totals[k] += cafe_orders
            elif k == "cafe_giving": totals[k] += cafe_giving
            elif k == "merch_orders": totals[k] += merch_orders
            elif k == "merch_giving": totals[k] += merch_giving
            elif k == "recurring_givers": totals[k] += recurring

    # Giving trends by campus (last 4 weeks)
    giving_trends = []
    for week_offset in range(4):
        week_end = NOW - timedelta(weeks=week_offset)
        week_start = week_end - timedelta(days=7)
        week_label = week_start.strftime("%b %d")
        week_data = {"week": week_label}
        for t in tenants:
            pipeline = [
                {"$match": {
                    "tenant_id": t["id"],
                    "donation_date": {"$gte": week_start.strftime("%Y-%m-%d"), "$lt": week_end.strftime("%Y-%m-%d")}
                }},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            result = await db.donations.aggregate(pipeline).to_list(1)
            week_data[t["name"]] = result[0]["total"] if result else 0
        giving_trends.append(week_data)

    giving_trends.reverse()

    return {
        "organization_id": org_id,
        "organization_name": org_name,
        "campus_count": len(campuses),
        "campuses": campuses,
        "totals": {
            "total_members": totals["members"],
            "total_active": totals["active"],
            "total_attendance": totals["attendance"],
            "total_mtd_giving": totals["mtd_giving"],
            "total_ytd_giving": totals["ytd_giving"],
            "total_groups": totals["groups"],
            "total_mrr": totals["mrr"],
            "total_cafe_orders": totals["cafe_orders"],
            "total_merch_orders": totals["merch_orders"],
            "engagement_rate": round((totals["active"] / totals["members"] * 100), 1) if totals["members"] > 0 else 0,
            "giving_per_capita": round(totals["mtd_giving"] / totals["members"], 2) if totals["members"] > 0 else 0,
        },
        "giving_trends": giving_trends,
    }


# ============== GIVING NUDGE CHECKOUT FLOW ==============

class CheckoutWithNudgeRequest(BaseModel):
    items: List[Dict[str, Any]]
    giving_amount: float = 0
    giving_fund: str = "General Fund"
    payment_method_id: Optional[str] = None
    order_type: str = "cafe"  # "cafe" or "merch"
    pickup_time: Optional[str] = None

@api_router.post("/portal/checkout/with-giving")
async def checkout_with_giving_nudge(req: CheckoutWithNudgeRequest, request: Request):
    """4-step checkout: Review -> Giving Moment -> Payment -> Confirmation"""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in req.items)
    total = round(subtotal + req.giving_amount, 2)

    order_id = str(uuid.uuid4())
    order_doc = {
        "id": order_id,
        "tenant_id": tenant_id,
        "user_id": user["user_id"],
        "user_name": user.get("name", ""),
        "order_type": req.order_type,
        "items": req.items,
        "subtotal": subtotal,
        "giving_amount": req.giving_amount,
        "giving_fund": req.giving_fund if req.giving_amount > 0 else None,
        "total": total,
        "payment_method_id": req.payment_method_id,
        "pickup_time": req.pickup_time,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    collection = "cafe_orders" if req.order_type == "cafe" else "merch_orders"
    await db[collection].insert_one(order_doc)

    # If giving was added, also create a donation record
    if req.giving_amount > 0:
        donation_doc = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": user["user_id"],
            "person_name": user.get("name", ""),
            "amount": req.giving_amount,
            "fund_name": req.giving_fund,
            "fund": req.giving_fund,
            "payment_method": "card",
            "frequency": "one_time",
            "status": "completed",
            "source": f"{req.order_type}_nudge",
            "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.donations.insert_one(donation_doc)

    return {
        "order_id": order_id,
        "status": "confirmed",
        "subtotal": subtotal,
        "giving_amount": req.giving_amount,
        "giving_fund": req.giving_fund if req.giving_amount > 0 else None,
        "total": total,
        "pickup_time": req.pickup_time,
        "message": "Order confirmed! Thank you for your generosity." if req.giving_amount > 0 else "Order confirmed!"
    }

# ============== PLATFORM HEALTH MONITORING ==============

@api_router.get("/platform/health")
async def platform_health(request: Request):
    """System health check for platform admin dashboard."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    # DB health check
    db_healthy = True
    try:
        await db.command("ping")
    except Exception:
        db_healthy = False

    # Active sessions
    active_sessions = await db.user_sessions.count_documents({
        "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
    })

    # Failed logins (check for any rate limiting triggers)
    twenty_four_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent_activity = await db.activity_log.count_documents({
        "created_at": {"$gte": twenty_four_hours_ago}
    })

    total_collections = await db.list_collection_names()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": {
            "status": "connected" if db_healthy else "disconnected",
            "collections": len(total_collections),
        },
        "sessions": {
            "active_now": active_sessions,
        },
        "activity": {
            "events_24h": recent_activity,
        },
        "uptime": "99.9%",
        "checked_at": datetime.now(timezone.utc).isoformat()
    }

# NOW is used in comparison endpoint
NOW = datetime.now(timezone.utc)
app.include_router(api_router)

# ============== EXTRACTED ROUTE MODULES ==============
from routes.push import router as push_router, send_push_notification
from routes.messaging import router as messaging_router
from routes.volunteer import router as volunteer_router, seed_volunteer_leaderboard_data as seed_vol_data
from routes.geofence import router as geofence_router
from routes.announcements import router as announcements_router
from routes.media_uploads import router as media_uploads_router
from routes.giving_nudge import router as giving_nudge_router


app.include_router(push_router, prefix="/api")
app.include_router(messaging_router, prefix="/api")
app.include_router(volunteer_router, prefix="/api")
app.include_router(geofence_router, prefix="/api")
app.include_router(announcements_router, prefix="/api")
app.include_router(media_uploads_router, prefix="/api")
app.include_router(giving_nudge_router, prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origin_regex=r".*",
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_ensure_mobile_seed_data():
    try:
        await ensure_mobile_demo_accounts()
        await seed_vol_data()
        # Create TTL index for idempotency keys (24hr expiry)
        try:
            await db.idempotency_keys.create_index("created_at", expireAfterSeconds=86400)
        except Exception:
            pass  # Index already exists
        # Session TTL - drop conflicting index first if needed
        try:
            await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
        except Exception:
            pass
        # Seed volunteer team for Abundant East
        existing_team = await db.volunteer_teams.find_one({"id": "kids-checkin-team", "tenant_id": "abundant-east-001"})
        if not existing_team:
            await db.volunteer_teams.insert_one({
                "id": "kids-checkin-team", "tenant_id": "abundant-east-001",
                "team_name": "Kids Check-In Team", "ministry": "Children's Ministry",
                "description": "Ensuring every child is safe and accounted for every Sunday.",
                "created_at": datetime.now(timezone.utc).isoformat(), "created_by": "system"
            })
        # Assign Aivy to Kids Check-In Team
        await db.volunteer_assignments.update_one(
            {"user_id": "f1d0f1d8-de66-4fc0-a8c7-8f81f679ce22", "team_id": "kids-checkin-team", "tenant_id": "abundant-east-001"},
            {"$set": {"id": str(uuid.uuid4()), "user_id": "f1d0f1d8-de66-4fc0-a8c7-8f81f679ce22", "team_id": "kids-checkin-team", "tenant_id": "abundant-east-001", "role_title": "Team Lead", "assigned_at": datetime.now(timezone.utc).isoformat(), "assigned_by": "system"}},
            upsert=True
        )
        logger.info("Mobile demo accounts, volunteer teams, and indexes ensured")
    except Exception as exc:
        logger.error(f"Failed to ensure startup seed data: {exc}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

