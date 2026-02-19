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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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
    
    return serialize_doc(user_doc)

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

# ============== APP ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "Samson Church Management API", "version": "1.0.0"}

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
    tenant_id = DEFAULT_TENANT_ID
    
    # Get member counts
    total_members = await db.people.count_documents({"tenant_id": tenant_id})
    active_members = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "member"})
    visitors = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "visitor"})
    
    # Get group count
    active_groups = await db.groups.count_documents({"tenant_id": tenant_id, "is_active": True})
    open_groups = await db.groups.count_documents({"tenant_id": tenant_id, "is_active": True, "is_open": True})
    
    # Get giving stats - MTD and YTD
    today = datetime.now(timezone.utc)
    mtd_start = today.replace(day=1).strftime("%Y-%m-%d")
    ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    
    mtd_pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": mtd_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    ytd_pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": ytd_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    
    mtd_result = await db.donations.aggregate(mtd_pipeline).to_list(1)
    ytd_result = await db.donations.aggregate(ytd_pipeline).to_list(1)
    
    mtd_giving = mtd_result[0]["total"] if mtd_result else 0
    ytd_giving = ytd_result[0]["total"] if ytd_result else 0
    
    # Get last Sunday attendance
    last_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    last_sunday_str = last_sunday.strftime("%Y-%m-%d")
    
    attendance_pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$lookup": {
            "from": "services",
            "localField": "service_id",
            "foreignField": "id",
            "as": "service"
        }},
        {"$unwind": "$service"},
        {"$match": {"service.date": last_sunday_str}},
        {"$count": "total"}
    ]
    attendance_result = await db.attendance.aggregate(attendance_pipeline).to_list(1)
    last_attendance = attendance_result[0]["total"] if attendance_result else 0
    
    # New this week
    week_ago = (today - timedelta(days=7)).isoformat()
    new_this_week = await db.people.count_documents({
        "tenant_id": tenant_id,
        "created_at": {"$gte": week_ago}
    })
    
    # Recurring givers
    recurring_count = await db.recurring_giving.count_documents({
        "tenant_id": tenant_id,
        "is_active": True
    })
    
    return {
        "total_members": total_members,
        "active_members": active_members,
        "visitors": visitors,
        "active_groups": active_groups,
        "open_groups": open_groups,
        "mtd_giving": mtd_giving,
        "ytd_giving": ytd_giving,
        "mtd_goal": 350000,
        "last_attendance": last_attendance,
        "last_attendance_change": 340,
        "new_this_week": new_this_week,
        "recurring_givers": recurring_count
    }

@api_router.get("/dashboard/giving-trend")
async def get_giving_trend():
    tenant_id = DEFAULT_TENANT_ID
    today = datetime.now(timezone.utc)
    
    # Get last 12 months of giving by fund
    months = []
    for i in range(11, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1).strftime("%Y-%m-%d")
        month_end = (month_date.replace(day=28) + timedelta(days=4)).replace(day=1).strftime("%Y-%m-%d")
        
        pipeline = [
            {"$match": {
                "tenant_id": tenant_id,
                "donation_date": {"$gte": month_start, "$lt": month_end}
            }},
            {"$lookup": {
                "from": "funds",
                "localField": "fund_id",
                "foreignField": "id",
                "as": "fund"
            }},
            {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
            {"$group": {
                "_id": "$fund.name",
                "total": {"$sum": "$amount"}
            }}
        ]
        
        results = await db.donations.aggregate(pipeline).to_list(10)
        month_data = {
            "month": month_date.strftime("%b"),
            "General Fund": 0,
            "Building Fund": 0,
            "Missions": 0,
            "Crypto": 0
        }
        for r in results:
            fund_name = r["_id"] or "General Fund"
            if fund_name in month_data:
                month_data[fund_name] = r["total"]
        months.append(month_data)
    
    return months

@api_router.get("/dashboard/attendance-trend")
async def get_attendance_trend():
    tenant_id = DEFAULT_TENANT_ID
    today = datetime.now(timezone.utc)
    
    # Get last 12 weeks of attendance
    weeks = []
    for i in range(11, -1, -1):
        week_date = today - timedelta(weeks=i)
        # Find the Sunday of that week
        sunday = week_date - timedelta(days=week_date.weekday() + 1)
        sunday_str = sunday.strftime("%Y-%m-%d")
        
        pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$lookup": {
                "from": "services",
                "localField": "service_id",
                "foreignField": "id",
                "as": "service"
            }},
            {"$unwind": "$service"},
            {"$match": {"service.date": sunday_str}},
            {"$count": "total"}
        ]
        result = await db.attendance.aggregate(pipeline).to_list(1)
        count = result[0]["total"] if result else 0
        
        weeks.append({
            "week": sunday.strftime("%b %d"),
            "attendance": count,
            "date": sunday_str
        })
    
    return weeks

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
    tenant_id = DEFAULT_TENANT_ID
    
    # Check if already seeded
    existing = await db.tenants.find_one({"id": tenant_id})
    if existing:
        return {"message": "Database already seeded", "seeded": False}
    
    # Create tenant
    tenant = {
        "id": tenant_id,
        "name": "Abundant Church",
        "subdomain": "abundant",
        "plan": "enterprise",
        "member_limit": 100000,
        "logo_url": None,
        "primary_color": "#4f6ef7",
        "accent_color": "#00c896",
        "timezone": "America/Los_Angeles",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.tenants.insert_one(tenant)
    
    # Create funds
    funds_data = [
        {"name": "General Fund", "description": "General operating fund", "goal_amount": 4200000},
        {"name": "Building Fund", "description": "New sanctuary construction", "goal_amount": 2000000},
        {"name": "Missions", "description": "Global missions support", "goal_amount": 500000},
        {"name": "Benevolence", "description": "Community assistance", "goal_amount": 100000},
        {"name": "Youth Ministry", "description": "Youth programs and events", "goal_amount": 150000},
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
    
    # Create 80 households with 200 people
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
