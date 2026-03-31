"""
Solomon AI — Pydantic Models (Auto-extracted)
All data models for the Solomon AI platform.
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, date
import uuid


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
    enrollment_type: str = "open"
    campus_id: Optional[str] = None
    category: Optional[str] = None

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

class RegisterFamilyPayload(BaseModel):
    parentName: str
    parentEmail: str
    parentPhone: str = ""
    childName: str
    childBirthdate: str = ""
    childAllergies: str = ""
    childNotes: str = ""

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

class SavePaymentMethodRequest(BaseModel):
    card_last_four: str
    card_brand: str
    card_exp_month: int
    card_exp_year: int
    stripe_payment_method_id: Optional[str] = None
    is_default: bool = False

class SolomonPayProcessRequest(BaseModel):
    card_last_four: str
    card_brand: str
    card_exp_month: str
    card_exp_year: str
    cardholder_name: str
    billing_zip: str
    save_card: bool = False
    amount: float
    context: str = "donation"
    fund_id: Optional[str] = None
    fund_name: Optional[str] = None
    frequency: Optional[str] = "one-time"
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LeadCaptureRequest(BaseModel):
    church_name: str
    name: str
    email: str
    phone: Optional[str] = None
    current_software: Optional[str] = None
    church_size: Optional[str] = None

class SMSRequest(BaseModel):
    recipient_phone: str
    message: str
    person_id: Optional[str] = None

class BulkSMSRequest(BaseModel):
    group_id: Optional[str] = None
    list_ids: Optional[List[str]] = None
    message: str
    template_id: Optional[str] = None

class RoleUpdateRequest(BaseModel):
    role: str = None
    role_template: str = None

class PermissionsUpdateRequest(BaseModel):
    permissions: List[str]

class PermissionGrantRequest(BaseModel):
    permission: str

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
    enrollment_type: str = "open"
    campus_id: Optional[str] = None
    category: Optional[str] = None

class AddMemberToGroupRequest(BaseModel):
    person_id: str
    role: str = "member"

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

class AdminRegisterRequest(BaseModel):
    user_id: Optional[str] = None
    person_id: Optional[str] = None
    name: str
    email: Optional[str] = None

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

class RoomBookingRequest(BaseModel):
    event_name: str
    description: Optional[str] = None
    event_date: str
    start_time: str
    end_time: str
    room_id: str
    room_name: Optional[str] = None
    campus_id: Optional[str] = None
    requested_by: Optional[str] = None
    notes: Optional[str] = None
    recurrence: Optional[str] = None

class ApprovalDecision(BaseModel):
    decision: str  # "approved" or "rejected"
    notes: Optional[str] = None

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger: Optional[str] = "manual"
    steps: Optional[List[Dict[str, Any]]] = None

class FormCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None
    is_public: bool = True
    auto_create_profile: bool = False
    redirect_url: Optional[str] = None

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

class KidsCheckoutRequest(BaseModel):
    child_id: str
    pickup_code: str

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

class GivingDonateRequest(BaseModel):
    amount: float
    fund: str = "general"
    frequency: str = "one_time"
    payment_method_id: Optional[str] = None
    source: str = "direct"

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

class CheckoutWithNudgeRequest(BaseModel):
    items: List[Dict[str, Any]]
    giving_amount: float = 0
    giving_fund: str = "General Fund"
    payment_method_id: Optional[str] = None
    order_type: str = "cafe"  # "cafe" or "merch"
    pickup_time: Optional[str] = None

