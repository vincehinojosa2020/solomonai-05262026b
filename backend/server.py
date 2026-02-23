from fastapi import FastAPI, APIRouter, HTTPException, Query, Request, Response, Cookie
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

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Samson Church Management API")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== MULTI-TENANT CONFIGURATION ==============

# Platform admin accounts (can access all tenants)
PLATFORM_ADMIN_EMAILS = ["admin@samson.ai", "admin@abundant.org"]

# Role hierarchy
ROLES = {
    "platform_admin": 100,  # Can access everything
    "church_admin": 50,     # Can manage their church
    "member": 10            # Portal access only
}

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

async def send_welcome_email(email: str, first_name: str):
    """Send a creative welcome email from Samson AI when a new user registers"""
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
                    I'm <strong>Samson</strong>, your AI assistant at Abundant Church. I just wanted to personally say <strong>thank you</strong> for joining our community! 
                </p>
                <p style="font-size: 16px; color: #4a5568; margin: 0 0 20px 0;">
                    Whether you're looking to grow in faith, connect with others, or simply find a place to belong — you're in the right place. We're so glad you're here.
                </p>
                <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 20px; margin: 24px 0; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; color: #1e40af; font-size: 15px;">
                        <strong>What's next?</strong><br>
                        Log in to explore sermon videos, join a group, or make your first gift. I'm always here if you need anything!
                    </p>
                </div>
                <p style="font-size: 16px; color: #4a5568; margin: 0 0 8px 0;">
                    See you soon,
                </p>
                <p style="font-size: 18px; color: #1a1a2e; margin: 0; font-weight: 600;">
                    Samson 🤖✨
                </p>
                <p style="font-size: 13px; color: #94a3b8; margin: 16px 0 0 0; font-style: italic;">
                    Your AI Church Assistant at Abundant Church
                </p>
            </td>
        </tr>
        <tr>
            <td style="text-align: center; padding: 24px;">
                <p style="font-size: 12px; color: #94a3b8; margin: 0;">
                    Abundant Church • El Paso, TX<br>
                    Powered by SAMSON AI
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
            "subject": f"Welcome to Abundant Church, {first_name}! 🎉",
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

class UserRole(BaseModel):
    role: str = "member"  # "admin" or "member"

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

# ============== HELPER FUNCTIONS ==============

def serialize_doc(doc: dict) -> dict:
    """Remove MongoDB _id and convert datetime objects"""
    if doc is None:
        return None
    result = {k: v for k, v in doc.items() if k != '_id'}
    for key, value in result.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
    return result

# Default tenant ID for demo
DEFAULT_TENANT_ID = "abundant-church-001"

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

@api_router.get("/auth/me")
async def get_current_user(request: Request):
    """Get current user from session cookie or Authorization header"""
    # Try cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
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
    # Ensure role is included
    result["role"] = user_doc.get("role", "admin")  # Default to admin for Google OAuth users
    return result

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Clear session and cookie"""
    session_token = request.cookies.get("session_token")
    
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
async def email_password_login(request: EmailLoginRequest, response: Response):
    """Login with email and password (for demo accounts)"""
    import hashlib
    
    # Find user by email
    user_doc = await db.users.find_one({"email": request.email}, {"_id": 0})
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password (simple hash comparison for demo)
    stored_hash = user_doc.get("password_hash")
    if not stored_hash:
        raise HTTPException(status_code=401, detail="Password login not enabled for this account")
    
    input_hash = hashlib.sha256(request.password.encode()).hexdigest()
    if input_hash != stored_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create session
    session_token = f"sess_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.delete_many({"user_id": user_doc["user_id"]})
    await db.user_sessions.insert_one({
        "user_id": user_doc["user_id"],
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
    
    return {
        "user_id": user_doc["user_id"],
        "email": user_doc["email"],
        "name": user_doc["name"],
        "picture": user_doc.get("picture"),
        "role": user_doc.get("role", "member")
    }

# ============== USER REGISTRATION ==============

import re
import hashlib

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
        "church_id": DEFAULT_TENANT_ID,
        "tenant_id": DEFAULT_TENANT_ID,
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
    
    logger.info(f"New user registered: {request.email}")
    
    # Send welcome email from Samson AI (non-blocking)
    asyncio.create_task(send_welcome_email(request.email, request.first_name))
    
    return {
        "message": "Account created successfully",
        "user_id": user_id,
        "email": new_user["email"],
        "name": new_user["name"],
        "role": "member"
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
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find linked person record
    person = await db.people.find_one({"email": user["email"]}, {"_id": 0})
    
    # Get member's groups
    groups = []
    if person:
        group_memberships = await db.group_members.find(
            {"person_id": person["id"], "is_active": True},
            {"_id": 0}
        ).to_list(100)
        
        for gm in group_memberships:
            group = await db.groups.find_one({"id": gm["group_id"]}, {"_id": 0})
            if group:
                groups.append(serialize_doc(group))
    
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
            {"_id": 0}
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

@api_router.get("/portal/giving/history")
async def get_member_giving_history(request: Request, limit: int = 50):
    """Get member's giving history for portal"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    person = await db.people.find_one({"email": user["email"]}, {"_id": 0})
    
    if not person:
        return {"donations": [], "total": 0}
    
    donations = await db.donations.find(
        {"person_id": person["id"]},
        {"_id": 0}
    ).sort("donation_date", -1).limit(limit).to_list(limit)
    
    # Enrich with fund names
    for d in donations:
        fund = await db.funds.find_one({"id": d.get("fund_id")}, {"_id": 0})
        d["fund_name"] = fund["name"] if fund else "General Fund"
    
    return {
        "donations": [serialize_doc(d) for d in donations],
        "total": len(donations)
    }

@api_router.get("/portal/events")
async def get_member_events(request: Request):
    """Get upcoming events for member portal"""
    tenant_id = DEFAULT_TENANT_ID
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    events = await db.events.find(
        {"tenant_id": tenant_id, "start_datetime": {"$gte": today}},
        {"_id": 0}
    ).sort("start_datetime", 1).limit(20).to_list(20)
    
    return [serialize_doc(e) for e in events]

@api_router.get("/portal/groups")
async def get_available_groups(request: Request):
    """Get groups available to join for member portal"""
    tenant_id = DEFAULT_TENANT_ID
    
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
    session_token = request.cookies.get("session_token")
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
    session_token = request.cookies.get("session_token")
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
    session_token = request.cookies.get("session_token")
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
        session_token = request.cookies.get("session_token")
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
    return {"message": "Samson Church Management API", "version": "1.0.0"}

# ============== TENANT/CHURCH MANAGEMENT ROUTES ==============

@api_router.get("/tenants")
async def list_tenants(request: Request):
    """List all tenants (platform admin only)"""
    # Verify platform admin
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(100)
    
    # Get member count for each tenant
    for tenant in tenants:
        tenant["member_count"] = await db.users.count_documents({"tenant_id": tenant["id"]})
    
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
    session_token = request.cookies.get("session_token")
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
    session_token = request.cookies.get("session_token")
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
    session_token = request.cookies.get("session_token")
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

# --- SAMSON AI ROUTES ---
# Store active chat sessions
solomon_sessions: Dict[str, LlmChat] = {}

SOLOMON_SYSTEM_PROMPT = """You are Solomon, an intelligent AI analyst for Samson Church Management System. You assist church administrators with:

1. **Data Analysis**: Analyze membership trends, giving patterns, attendance statistics
2. **Pastoral Advice**: Provide guidance on member care, follow-up strategies, engagement
3. **Operational Strategy**: Help with event planning, group management, communication strategies
4. **Quick Insights**: Answer questions about church data and provide actionable recommendations

You have access to church data including:
- Members: names, contact info, membership status, engagement scores, giving history
- Groups: small groups, ministries, volunteer teams with member counts
- Giving: donations, funds, recurring gifts, pledges
- Attendance: service attendance, trends, check-in data
- Events: upcoming services, special events, registrations

When answering:
- Be warm, professional, and pastoral in tone
- Provide specific, actionable insights when possible
- Reference actual data when available (it will be provided in context)
- Suggest follow-up actions or next steps
- Keep responses concise but thorough

You are serving Abundant Church in El Paso, TX - a mega church with 50,000+ members."""

async def get_church_context() -> str:
    """Gather current church data for Solomon's context"""
    tenant_id = DEFAULT_TENANT_ID
    
    # Get key stats
    total_members = await db.people.count_documents({"tenant_id": tenant_id})
    active_members = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "member"})
    visitors = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "visitor"})
    
    # Get groups info
    total_groups = await db.groups.count_documents({"tenant_id": tenant_id, "is_active": True})
    
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

GIVING:
- Month-to-Date: ${mtd_giving:,.2f}
- Year-to-Date: ${ytd_giving:,.2f}
- Monthly Goal: $350,000

RECENT ACTIVITY:
{activities_text}

UPCOMING EVENTS:
{events_text}
"""
    return context

@api_router.post("/solomon/chat")
async def solomon_chat(request: SolomonChatRequest):
    """Chat with Solomon AI analyst"""
    try:
        # Validate message is not empty
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
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
        user_message = UserMessage(text=request.message)
        
        # Get response from Claude
        response_text = await chat.send_message(user_message)
        
        # Store conversation in database for persistence
        await db.solomon_conversations.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": request.message, "timestamp": datetime.now(timezone.utc).isoformat()},
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
        
        # Check if response suggests actions
        if "follow-up" in response_text.lower() or "reach out" in response_text.lower():
            actions = [
                {"label": "View Members Needing Follow-up", "action": "navigate", "path": "/people?status=inactive"},
                {"label": "Send Bulk Message", "action": "navigate", "path": "/communications"}
            ]
        elif "giving" in response_text.lower() or "donation" in response_text.lower():
            actions = [
                {"label": "View Giving Dashboard", "action": "navigate", "path": "/giving"},
                {"label": "Generate Report", "action": "navigate", "path": "/reports"}
            ]
        elif "group" in response_text.lower() or "ministry" in response_text.lower():
            actions = [
                {"label": "View Groups", "action": "navigate", "path": "/groups"},
                {"label": "Create New Group", "action": "modal", "type": "createGroup"}
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
async def get_tenant():
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
            "timezone": "America/Los_Angeles"
        }
    return serialize_doc(tenant)

# --- DASHBOARD ROUTES ---
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Return dashboard stats - using demo values for Abundant Church (500 members, El Paso TX)"""
    # Return static demo values for fast loading
    return {
        "total_members": 487,
        "active_members": 414,
        "visitors": 15,
        "active_groups": 12,
        "open_groups": 4,
        "mtd_giving": 24750,
        "ytd_giving": 87303,
        "mtd_goal": 95000,
        "last_attendance": 312,
        "last_attendance_change": 24,
        "new_this_week": 8,
        "recurring_givers": 47
    }

@api_router.get("/dashboard/giving-trend")
async def get_giving_trend():
    """Return demo giving trend data - 12 months for Abundant Church"""
    return [
        {"month": "Mar", "General Fund": 18500, "Building Fund": 4200, "Missions": 1800, "Crypto": 0},
        {"month": "Apr", "General Fund": 19200, "Building Fund": 4500, "Missions": 1900, "Crypto": 200},
        {"month": "May", "General Fund": 21000, "Building Fund": 4800, "Missions": 2100, "Crypto": 0},
        {"month": "Jun", "General Fund": 18900, "Building Fund": 4100, "Missions": 1750, "Crypto": 0},
        {"month": "Jul", "General Fund": 17500, "Building Fund": 3900, "Missions": 1600, "Crypto": 150},
        {"month": "Aug", "General Fund": 19800, "Building Fund": 4300, "Missions": 1850, "Crypto": 0},
        {"month": "Sep", "General Fund": 22500, "Building Fund": 5100, "Missions": 2200, "Crypto": 0},
        {"month": "Oct", "General Fund": 21200, "Building Fund": 4700, "Missions": 2050, "Crypto": 300},
        {"month": "Nov", "General Fund": 24800, "Building Fund": 5500, "Missions": 2400, "Crypto": 0},
        {"month": "Dec", "General Fund": 32500, "Building Fund": 7200, "Missions": 3100, "Crypto": 500},
        {"month": "Jan", "General Fund": 20100, "Building Fund": 4400, "Missions": 1950, "Crypto": 0},
        {"month": "Feb", "General Fund": 24750, "Building Fund": 5200, "Missions": 2350, "Crypto": 0}
    ]

@api_router.get("/dashboard/attendance-trend")
async def get_attendance_trend():
    """Return demo attendance trend data - 12 weeks for Abundant Church"""
    return [
        {"week": "Week 1", "attendance": 285, "date": "Dec 1"},
        {"week": "Week 2", "attendance": 298, "date": "Dec 8"},
        {"week": "Week 3", "attendance": 312, "date": "Dec 15"},
        {"week": "Week 4", "attendance": 445, "date": "Dec 22"},
        {"week": "Week 5", "attendance": 478, "date": "Dec 29"},
        {"week": "Week 6", "attendance": 302, "date": "Jan 5"},
        {"week": "Week 7", "attendance": 295, "date": "Jan 12"},
        {"week": "Week 8", "attendance": 308, "date": "Jan 19"},
        {"week": "Week 9", "attendance": 318, "date": "Jan 26"},
        {"week": "Week 10", "attendance": 305, "date": "Feb 2"},
        {"week": "Week 11", "attendance": 288, "date": "Feb 9"},
        {"week": "Week 12", "attendance": 312, "date": "Feb 16"}
    ]

@api_router.get("/dashboard/activity")
async def get_recent_activity(limit: int = 15):
    tenant_id = DEFAULT_TENANT_ID
    
    activities = await db.activity_log.find(
        {"tenant_id": tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [serialize_doc(a) for a in activities]

@api_router.get("/dashboard/upcoming-events")
async def get_upcoming_events(limit: int = 5):
    tenant_id = DEFAULT_TENANT_ID
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    events = await db.events.find(
        {"tenant_id": tenant_id, "start_datetime": {"$gte": today}},
        {"_id": 0}
    ).sort("start_datetime", 1).limit(limit).to_list(limit)
    
    return [serialize_doc(e) for e in events]

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

@api_router.get("/groups/{group_id}/members")
async def get_group_members(group_id: str):
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
    """Seed the entire SAMSON platform with multiple churches and demo data"""
    import hashlib
    
    demo_password_hash = hashlib.sha256("Demo2026!".encode()).hexdigest()
    
    # Define the three demo churches
    churches = [
        {
            "id": "abundant-church-001",
            "name": "Abundant Living Faith Center",
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
            "accent_color": "#00c896"
        },
        {
            "id": "cityreach-church-001",
            "name": "City Reach Church",
            "subdomain": "cityreach",
            "plan": "enterprise",
            "member_limit": 50000,
            "subscription_status": "active",
            "address": "1401 Medical Pkwy",
            "city": "Cedar Park",
            "state": "TX",
            "timezone": "America/Chicago",
            "website": "https://cityreachchurch.com",
            "phone": "(512) 528-8600",
            "primary_color": "#10b981",
            "accent_color": "#f59e0b"
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
            "accent_color": "#ec4899"
        }
    ]
    
    results = {"churches": [], "platform_accounts": []}
    
    # Create/update Samson platform admin accounts
    platform_accounts = [
        {
            "user_id": "platform_admin_001",
            "email": "admin@samson.ai",
            "name": "Samson Platform Admin",
            "role": "platform_admin",
            "tenant_id": None  # Platform admin has no tenant restriction
        },
        {
            "user_id": "platform_member_001",
            "email": "member@samson.ai",
            "name": "Demo Member",
            "role": "member",
            "tenant_id": "abundant-church-001"  # Default to Abundant for demo
        },
        {
            "user_id": "platform_newmember_001",
            "email": "newmember@samson.ai",
            "name": "New Member Demo",
            "role": "member",
            "tenant_id": "abundant-church-001"
        }
    ]
    
    for account in platform_accounts:
        await db.users.update_one(
            {"email": account["email"]},
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
    
    return {
        "message": "Platform seeded successfully",
        "results": results,
        "demo_credentials": {
            "password": "Demo2026!",
            "platform_admin": "admin@samson.ai",
            "abundant_admin": "admin@abundant.church",
            "cityreach_admin": "admin@cityreach.church",
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

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
