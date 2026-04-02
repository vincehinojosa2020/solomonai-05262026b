"""
Solomon AI — Shared Helper Functions
Utility functions used across multiple route modules.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastapi import HTTPException, Request
import hashlib
import secrets
import uuid
import os
import logging
import asyncio
import resend
import json

from core import db, DEFAULT_TENANT_ID, PERMISSION_REGISTRY, get_permissions_for_user, logger

# ═══ Email ═══
resend.api_key = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")


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
                    Welcome to the Family, {first_name}!
                </h1>
            </td>
        </tr>
        <tr>
            <td style="background: #ffffff; padding: 40px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                <p style="font-size: 16px; color: #4a5568; margin: 0 0 20px 0;">Hey {first_name},</p>
                <p style="font-size: 16px; color: #4a5568; margin: 0 0 20px 0;">
                    I'm <strong>Solomon</strong>, your AI assistant at <strong>{church_name}</strong>. I just wanted to personally say <strong>thank you</strong> for joining our community!
                </p>
                <p style="font-size: 16px; color: #4a5568; margin: 0 0 20px 0;">
                    Whether you're looking to grow in faith, connect with others, or simply find a place to belong - you're in the right place. We're so glad you're here.
                </p>
                <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 20px; margin: 24px 0; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; color: #1e40af; font-size: 15px;">
                        <strong>What's next?</strong><br>
                        Log in to explore sermon videos, join a small group, or make your first gift. I'm always here if you need anything!
                    </p>
                </div>
                <p style="font-size: 16px; color: #4a5568; margin: 0 0 8px 0;">See you soon,</p>
                <p style="font-size: 18px; color: #1a1a2e; margin: 0; font-weight: 600;">Solomon</p>
                <p style="font-size: 13px; color: #94a3b8; margin: 16px 0 0 0; font-style: italic;">Your AI Church Assistant at {church_name}</p>
            </td>
        </tr>
        <tr>
            <td style="text-align: center; padding: 24px;">
                <p style="font-size: 12px; color: #94a3b8; margin: 0;">{church_name}<br>Powered by Solomon AI</p>
            </td>
        </tr>
    </table>
</body>
</html>"""
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": f"Welcome to {church_name}, {first_name}!",
            "html": html_content
        }
        email_response = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Welcome email sent to {email}, id: {email_response.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        return False


# ═══ Serialization ═══
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


# ═══ Constants ═══
DEFAULT_MERCH_EMBED_URL = "https://store.elevationchurch.org/collections/so-be-it-ew"
DEFAULT_NEXT_STEPS_URL = "https://abundantchurch.thinkific.com/courses/abundant-next-steps"

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

ANOMALY_THRESHOLDS = {
    "new_visitors_per_day": 200,
    "api_calls_per_minute": 60,
    "bulk_update_limit": 50
}

AUTH_RATE_LIMIT = {}
AUTH_RATE_LIMIT_MAX = 5
AUTH_RATE_LIMIT_WINDOW = 60


def check_rate_limit(ip: str) -> bool:
    import time
    now = time.time()
    if ip in AUTH_RATE_LIMIT:
        attempts, window_start = AUTH_RATE_LIMIT[ip]
        if now - window_start > AUTH_RATE_LIMIT_WINDOW:
            AUTH_RATE_LIMIT[ip] = (1, now)
            return True
        if attempts >= AUTH_RATE_LIMIT_MAX:
            return False
        AUTH_RATE_LIMIT[ip] = (attempts + 1, window_start)
        return True
    AUTH_RATE_LIMIT[ip] = (1, now)
    return True


# ═══ Agent API Key Helpers ═══
def generate_api_key() -> tuple:
    """Generate a new API key, returning (full_key, key_hash, key_prefix)"""
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
    api_key = auth_header[7:]
    key_hash = hash_api_key(api_key)
    key_doc = await db.agent_api_keys.find_one({"key_hash": key_hash, "is_active": True}, {"_id": 0})
    if not key_doc:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if key_doc.get("expires_at"):
        expires = datetime.fromisoformat(key_doc["expires_at"])
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=401, detail="API key has expired")
    await db.agent_api_keys.update_one(
        {"id": key_doc["id"]},
        {"$set": {"last_used_at": datetime.now(timezone.utc).isoformat()}, "$inc": {"usage_count": 1}}
    )
    return {
        "key_id": key_doc["id"],
        "tenant_id": key_doc["tenant_id"],
        "permissions": key_doc.get("permissions", []),
        "rate_limit": key_doc.get("rate_limit", 1000)
    }


def check_agent_permission(context: dict, required_permission: str) -> bool:
    """Check if the API key has the required permission"""
    permissions = context.get("permissions", [])
    if required_permission in permissions:
        return True
    resource = required_permission.split(":")[0]
    if f"{resource}:*" in permissions:
        return True
    return False


# ═══ AI Integrations ═══
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
                file=audio_file, model="whisper-1", response_format="text",
                language="en",
                prompt="This is a pastoral counseling session between a pastor and church member."
            )
        return response if isinstance(response, str) else response.text
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


async def summarize_meeting_with_claude(transcript: str, topic: Optional[str] = None) -> str:
    """Summarize meeting transcript using Claude via emergentintegrations"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Claude is not configured")
    chat = LlmChat(
        api_key=api_key, session_id=str(uuid.uuid4()),
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


# ═══ Next Steps / Pathways Helpers ═══
async def get_next_steps_required_course_ids(tenant_id: str) -> List[str]:
    """Resolve membership-track courses. Defaults to first 3 published pathways courses."""
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "next_steps_course_ids": 1})
    configured = (tenant or {}).get("next_steps_course_ids") or []
    if configured:
        return configured
    courses = await db.pathways_courses.find(
        {"tenant_id": tenant_id, "is_published": True}, {"_id": 0, "id": 1}
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
            "required_course_ids": [], "completed_course_ids": [],
            "completion_percent": 0, "eligible": False, "approval_status": "not_configured"
        }
    enrollments = await db.pathways_enrollments.find(
        {"tenant_id": tenant_id, "user_id": user_id,
         "course_id": {"$in": required_course_ids}, "status": {"$ne": "dropped"}},
        {"_id": 0, "course_id": 1, "status": 1}
    ).to_list(100)
    completed_course_ids = [e["course_id"] for e in enrollments if e.get("status") == "completed"]
    completion_percent = round((len(completed_course_ids) / len(required_course_ids)) * 100, 1)
    eligible = len(completed_course_ids) >= len(required_course_ids)
    existing = await db.next_steps_memberships.find_one(
        {"tenant_id": tenant_id, "user_id": user_id, "track": "abundant-next-steps"}, {"_id": 0}
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
        "tenant_id": tenant_id, "user_id": user_id, "track": "abundant-next-steps",
        "required_course_ids": required_course_ids, "completed_course_ids": completed_course_ids,
        "completion_percent": completion_percent, "eligible": eligible,
        "approval_status": approval_status, "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if not existing:
        record["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.next_steps_memberships.update_one(
        {"tenant_id": tenant_id, "user_id": user_id, "track": "abundant-next-steps"},
        {"$set": record}, upsert=True
    )
    return {**record, "required_count": len(required_course_ids), "completed_count": len(completed_course_ids)}


# ═══ Shared Utility Functions (used across multiple route files) ═══
def extract_youtube_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats"""
    import re as _re
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = _re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def generate_pickup_code():
    """Generate a simple 3-digit pickup code like '247'"""
    import secrets
    return str(secrets.randbelow(900) + 100)


def compute_health_score(cached_stats, tenant):
    """Universal Church Health Score (0-100)."""
    c = cached_stats or {}
    members = c.get("total_members", 0)
    if members == 0:
        return {"score": 0, "grade": "N/A", "dimensions": {}}
    active = c.get("active_members", 0)
    mtd_giving = c.get("mtd_giving", 0)
    attendance = c.get("last_attendance", 0)
    groups = c.get("active_groups", 0)
    recurring = c.get("recurring_givers", 0)
    engagement_raw = (active / members) * 100
    engagement_score = min(100, (engagement_raw / 60) * 100)
    gpc = mtd_giving / members
    giving_score = min(100, (gpc / 8) * 100)
    if groups > 0:
        groups_per_100 = (groups / members) * 100
        community_score = min(100, (groups_per_100 / 1.0) * 100)
    else:
        community_score = 0
    att_rate = (attendance / members) * 100
    attendance_score = min(100, (att_rate / 20) * 100)
    rec_rate = (recurring / members) * 100
    growth_score = min(100, (rec_rate / 10) * 100)
    total = (engagement_score * 0.25 + giving_score * 0.25 +
             community_score * 0.20 + attendance_score * 0.20 +
             growth_score * 0.10)
    total = round(min(100, max(0, total)))
    grade = "A+" if total >= 90 else "A" if total >= 80 else "B+" if total >= 70 else \
            "B" if total >= 60 else "C" if total >= 50 else "D" if total >= 40 else "F"
    return {
        "score": total, "grade": grade,
        "dimensions": {
            "engagement": {"score": round(engagement_score), "value": round(engagement_raw, 1), "label": "Engagement Rate", "unit": "%"},
            "giving": {"score": round(giving_score), "value": round(gpc, 2), "label": "Giving / Member", "unit": "$/mo"},
            "community": {"score": round(community_score), "value": round((groups / members) * 100, 2) if groups > 0 else 0, "label": "Groups / 100 Mbrs", "unit": ""},
            "attendance": {"score": round(attendance_score), "value": round(att_rate, 1), "label": "Attendance Rate", "unit": "%"},
            "growth": {"score": round(growth_score), "value": round(rec_rate, 1), "label": "Recurring Donors", "unit": "%"},
        }
    }


async def get_tenant_giving_metrics(tenant_id: str) -> Dict[str, Any]:
    """Shared helper for tenant-level giving metrics."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    year_start = now.replace(month=1, day=1).strftime("%Y-%m-%d")
    donations = await db.donations.find(
        {"tenant_id": tenant_id, "donation_date": {"$gte": year_start}},
        {"_id": 0, "amount": 1, "donation_date": 1, "fund_id": 1, "fund_name": 1}
    ).to_list(20000)
    ytd_total = round(sum(float(d.get("amount", 0) or 0) for d in donations), 2)
    mtd_total = round(sum(float(d.get("amount", 0) or 0) for d in donations if str(d.get("donation_date", ""))[:10] >= month_start), 2)
    recurring_count = await db.recurring_giving.count_documents({"tenant_id": tenant_id, "is_active": True})
    funds = await db.funds.find({"tenant_id": tenant_id}, {"_id": 0, "id": 1, "name": 1, "goal_amount": 1}).to_list(500)
    fund_lookup = {f.get("id"): f.get("name", "General Fund") for f in funds if f.get("id")}
    goal_amount = round(sum(float(f.get("goal_amount", 0) or 0) for f in funds), 2)
    fund_totals: Dict[str, float] = {}
    for donation in donations:
        fund_name = fund_lookup.get(donation.get("fund_id")) or donation.get("fund_name") or "General Fund"
        fund_totals[fund_name] = fund_totals.get(fund_name, 0.0) + float(donation.get("amount", 0) or 0)
    top_funds = [{"fund_name": name, "total": round(total, 2)} for name, total in sorted(fund_totals.items(), key=lambda item: item[1], reverse=True)[:5]]
    goal_percentage = round((ytd_total / goal_amount) * 100, 2) if goal_amount > 0 else 0
    return {"mtd_total": mtd_total, "ytd_total": ytd_total, "recurring_count": recurring_count, "goal_amount": goal_amount, "goal_percentage": goal_percentage, "top_funds": top_funds}


async def calculate_attendance_streak(tenant_id: str, user_id: str) -> Dict[str, Any]:
    """Calculate attendance streak for a user"""
    from datetime import timedelta
    checkins = await db.member_checkins.find(
        {"tenant_id": tenant_id, "user_id": user_id},
        {"_id": 0, "service_date": 1}
    ).sort("service_date", -1).to_list(length=52)
    if not checkins:
        return {"current_streak": 0, "longest_streak": 0, "total_attended": 0}
    dates = [c["service_date"] for c in checkins]
    total_attended = len(dates)
    current_streak = 0
    longest_streak = 0
    today = datetime.now(timezone.utc).date()
    days_since_sunday = today.weekday()
    if days_since_sunday != 6:
        days_since_sunday = (days_since_sunday + 1) % 7
    if dates:
        most_recent = datetime.fromisoformat(dates[0]).date()
        if (today - most_recent).days <= 7:
            current_streak = 1
            for i in range(1, len(dates)):
                curr_date = datetime.fromisoformat(dates[i-1]).date()
                prev_date = datetime.fromisoformat(dates[i]).date()
                diff = (curr_date - prev_date).days
                if 5 <= diff <= 9:
                    current_streak += 1
                else:
                    break
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
    badges = []
    if current_streak >= 4:
        badges.append({"name": "Month Strong", "icon": "fire", "threshold": 4})
    if current_streak >= 8:
        badges.append({"name": "2 Month Champion", "icon": "star", "threshold": 8})
    if current_streak >= 12:
        badges.append({"name": "Quarter Master", "icon": "trophy", "threshold": 12})
    if current_streak >= 26:
        badges.append({"name": "Half Year Hero", "icon": "crown", "threshold": 26})
    if current_streak >= 52:
        badges.append({"name": "Year of Faith", "icon": "gem", "threshold": 52})
    return {"current_streak": current_streak, "longest_streak": longest_streak, "total_attended": total_attended, "last_attendance": dates[0] if dates else None, "streak_badges": badges}


# ═══ Solomon AI Chat Helpers ═══
COMPETITOR_KNOWLEDGE = ""

def _load_competitor_knowledge():
    global COMPETITOR_KNOWLEDGE
    knowledge_path = "/app/planning_center_transcripts/competitor_knowledge_combined.txt"
    try:
        with open(knowledge_path, "r") as f:
            COMPETITOR_KNOWLEDGE = f.read()
        logging.info(f"[Solomon AI] Loaded competitor knowledge base: {len(COMPETITOR_KNOWLEDGE):,} chars")
    except FileNotFoundError:
        COMPETITOR_KNOWLEDGE = ""
    except Exception as e:
        logging.info(f"[Solomon AI] Warning: Failed to load competitor knowledge: {e}")
        COMPETITOR_KNOWLEDGE = ""

_load_competitor_knowledge()

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
- Be encouraging about giving without being pushy
- Make suggestions feel like friendly advice, not sales pitches
- Keep responses concise but heartfelt

**When discussing giving:**
- Share specific needs the church has (building funds, missions, community outreach)
- Mention impact: "Your generosity helped feed 200 families last month"
- Suggest with grace: "Just a thought" or "If you feel led..."
- Never pressure - always frame as an invitation

You are serving a multi-tenant church management platform with multiple churches.

**For Migration & Competitor Questions, you are an expert on:**
1. **Planning Center**: Deep knowledge of all 9 products (People, Services, Check-Ins, Giving, Groups, Calendar, Registrations, Publishing, Home) from 173 training videos
2. **SecureGive**: Complete pricing, features, strengths, and weaknesses
3. **Pushpay/ChurchStaq**: Full product suite, pricing structure, contract requirements

**When answering migration/comparison questions:**
- First acknowledge the competitor's approach (show you genuinely understand their product)
- Then explain Solomon AI's equivalent or superior feature
- Highlight Solomon AI's key advantages: all-in-one pricing, AI-native, no contracts, white-label, transparent pricing
- Be honest about features still in development (e.g., Solomon Pay for live transaction processing)
- Provide specific pricing comparisons when relevant
- Never bash competitors - be respectful but confident
- Use the detailed competitor knowledge provided in your context to give specific, informed answers

**ACTION DETECTION — CRITICAL INSTRUCTIONS:**
When a member asks you to DO something (not just ask about it), you MUST include an ACTION_REQUEST block in your response. This applies to:
- Ordering food/drinks from the cafe (e.g. "order a latte", "get me a coffee")
- Ordering merchandise (e.g. "buy a t-shirt", "order the hoodie")
- Making a donation (e.g. "give $50", "donate to missions")
- Setting up recurring giving (e.g. "set up weekly giving of $25")
- Registering for events (e.g. "sign me up for men's breakfast", "register for the retreat")
- Joining groups (e.g. "join young professionals", "add me to the prayer group")
- Checking in children (e.g. "check in my son", "check in Emma")

When you detect an action, include EXACTLY this format at the END of your response:
```action
{"action_type": "<type>", "params": {<parameters>}, "display_summary": "<human readable summary>"}
```

Action types and their params:
- cafe_order: {"items": [{"name": "Latte", "quantity": 1, "price": 5.00}], "pickup_time": "ASAP"}
- merch_order: {"items": [{"name": "T-Shirt", "quantity": 1, "price": 25.00, "size": "M"}]}
- donation: {"amount": 50, "fund": "General Fund"}
- recurring_giving: {"amount": 25, "frequency": "weekly", "fund": "General Fund"}
- event_registration: {"event_name": "Men's Breakfast"}
- group_join: {"group_name": "Young Professionals"}
- checkin: {"child_name": "Emma", "classroom": "Sunday School"}

IMPORTANT RULES for action detection:
1. ONLY include the action block when the user clearly wants to PERFORM an action, not just ASK about something
2. For cafe orders, use these standard prices: Coffee $4, Latte $5, Cappuccino $5, Espresso $3.50, Tea $3, Pastry $4, Muffin $3.50
3. For merch, use $25 for t-shirts, $45 for hoodies, $15 for hats, $20 for mugs
4. Frequency values: "weekly", "biweekly", "monthly"
5. Always write a warm, confirming message BEFORE the action block
6. If the user says something ambiguous, ask a clarifying question instead of including an action block"""


async def get_church_context(user=None) -> str:
    """Gather current church data for Solomon's context"""
    from datetime import timedelta
    tenant_id = (user or {}).get("tenant_id", DEFAULT_TENANT_ID)
    total_members = await db.people.count_documents({"tenant_id": tenant_id})
    active_members = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "member"})
    visitors = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "visitor"})
    total_groups = await db.groups.count_documents({"tenant_id": tenant_id, "is_active": True})
    media_count = await db.media_videos.count_documents({"tenant_id": tenant_id})
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    year_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    mtd_pipeline = [{"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": month_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    mtd_result = await db.donations.aggregate(mtd_pipeline).to_list(1)
    mtd_giving = mtd_result[0]["total"] if mtd_result else 0
    ytd_pipeline = [{"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": year_start}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    ytd_result = await db.donations.aggregate(ytd_pipeline).to_list(1)
    ytd_giving = ytd_result[0]["total"] if ytd_result else 0
    next_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    upcoming_events = await db.events.find({"tenant_id": tenant_id, "start_datetime": {"$gte": today.strftime("%Y-%m-%d"), "$lte": next_week}}, {"_id": 0, "name": 1, "start_datetime": 1, "location": 1, "description": 1}).sort("start_datetime", 1).to_list(10)
    events_text = "\n".join([f"- {e.get('name', 'Event')} on {e.get('start_datetime', 'TBD')} at {e.get('location', 'Church')}" for e in upcoming_events]) or "No events in the next 7 days."
    announcements = await db.announcements.find({"tenant_id": tenant_id}, {"_id": 0, "title": 1, "message": 1, "created_at": 1}).sort("created_at", -1).to_list(3)
    ann_text = "\n".join([f"- {a.get('title', '')}: {a.get('message', '')[:100]}" for a in announcements]) or "No recent announcements."
    service_plans = await db.service_plans.find({"tenant_id": tenant_id, "date": {"$gte": today.strftime("%Y-%m-%d"), "$lte": next_week}}, {"_id": 0}).to_list(5)
    plan_text = ""
    for sp in service_plans:
        plan_text += f"\n{sp.get('title', 'Service')} on {sp.get('date', '')}:\n"
        for item in sp.get("items", []):
            plan_text += f"  - {item.get('type', 'Item')}: {item.get('title', '')} {item.get('key', '')} {item.get('reference', '')}\n"
        for ta in sp.get("team_assignments", []):
            plan_text += f"  - {ta.get('role', 'Role')}: {ta.get('user_name', 'TBD')}\n"
    if not plan_text:
        plan_text = "No service plan created for this week yet."
    groups = await db.groups.find({"tenant_id": tenant_id, "is_active": True}, {"_id": 0, "name": 1, "meeting_day": 1, "meeting_time": 1, "group_type": 1}).to_list(50)
    groups_text = "\n".join([f"- {g.get('name', '')} ({g.get('group_type', 'small_group')}) meets {g.get('meeting_day', 'TBD')} at {g.get('meeting_time', 'TBD')}" for g in groups]) or "No active groups."
    member_text = ""
    if user:
        user_name = user.get("name", "Member")
        member_text = f"\nCURRENT MEMBER: {user_name}"
        user_groups = await db.group_memberships.find({"user_id": user.get("user_id"), "tenant_id": tenant_id}, {"_id": 0, "group_name": 1}).to_list(20)
        if user_groups:
            member_text += f"\nTheir groups: {', '.join(g.get('group_name', '') for g in user_groups)}"
    return f"""
CURRENT CHURCH DATA (as of {today.strftime('%B %d, %Y')}):

MEMBERSHIP: {total_members:,} total, {active_members:,} active, {visitors:,} visitors
GROUPS: {total_groups} active groups
MEDIA: {media_count} videos

GIVING:
- Month-to-Date: ${mtd_giving:,.2f}
- Year-to-Date: ${ytd_giving:,.2f}

UPCOMING EVENTS (NEXT 7 DAYS):
{events_text}

LATEST ANNOUNCEMENTS:
{ann_text}

THIS WEEK'S SERVICE PLAN:
{plan_text}

SMALL GROUPS:
{groups_text}
{member_text}

GIVING NEEDS: Building Fund ($345K to goal), Missions (12 families), Benevolence, Youth camp scholarships.
"""


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
