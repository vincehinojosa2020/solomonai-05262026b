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


# ═══ AI Integrations (re-exported from helpers_ai) ═══
from core.helpers_ai import (
    transcribe_audio_with_whisper,
    summarize_meeting_with_claude,
    notify_meeting_event,
)


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


def _score_dimension(value: float, target: float, label: str, unit: str, raw_value: float) -> dict:
    """Compute a single health score dimension (0-100) with metadata."""
    score = round(min(100, (value / max(target, 0.001)) * 100))
    return {"score": score, "value": round(raw_value, 2), "label": label, "unit": unit}


def _resolve_mtd_giving(cached: dict) -> float:
    """Return MTD giving, falling back to YTD/month when MTD = 0 (avoids seed-data edge case)."""
    mtd = cached.get("mtd_giving", 0) or 0
    ytd = cached.get("ytd_giving", 0) or 0
    if mtd == 0 and ytd > 0:
        from datetime import datetime
        return ytd / max(datetime.now().month, 1)
    return mtd


def compute_health_score(cached_stats, tenant):
    """
    Universal Church Health Score (A+ → F).
    Refactored: dimension calculations extracted to _score_dimension helper.
    Uses preset score when available (cached from dashboard admin).
    """
    c = cached_stats or {}

    # Use pre-computed preset when available (set by admin/seed for demo accuracy)
    preset = c.get("preset_health_score")
    if preset is not None:
        return {
            "score": c.get("preset_health_score", 0),
            "grade": c.get("preset_health_grade", "N/A"),
            "dimensions": c.get("preset_health_dimensions", {}),
        }

    members = c.get("total_members", 0)
    if members == 0:
        return {"score": 0, "grade": "N/A", "dimensions": {}}

    active     = c.get("active_members", 0)
    mtd_giving = _resolve_mtd_giving(c)
    attendance = c.get("last_attendance", 0)
    groups     = c.get("active_groups", 0)
    recurring  = c.get("recurring_givers", 0)

    # Five weighted dimensions
    engagement_raw = (active / members) * 100
    gpc            = mtd_giving / members
    groups_per_100 = (groups / members) * 100 if groups > 0 else 0
    att_rate       = (attendance / members) * 100
    rec_rate       = (recurring / members) * 100

    dims = {
        "engagement": _score_dimension(engagement_raw, 60,  "Engagement Rate", "%",   engagement_raw),
        "giving":     _score_dimension(gpc,            8,   "Giving / Member", "$/mo", gpc),
        "community":  _score_dimension(groups_per_100, 1.0, "Groups / 100 Mbrs", "",  groups_per_100),
        "attendance": _score_dimension(att_rate,       20,  "Attendance Rate", "%",   att_rate),
        "growth":     _score_dimension(rec_rate,       10,  "Recurring Donors", "%",  rec_rate),
    }

    total = round(min(100, max(0,
        dims["engagement"]["score"] * 0.25 +
        dims["giving"]["score"]     * 0.25 +
        dims["community"]["score"]  * 0.20 +
        dims["attendance"]["score"] * 0.20 +
        dims["growth"]["score"]     * 0.10
    )))
    grade = ("A+" if total >= 90 else "A" if total >= 80 else "B+" if total >= 70 else
             "B" if total >= 60 else "C" if total >= 50 else "D" if total >= 40 else "F")
    return {"score": total, "grade": grade, "dimensions": dims}


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


# ═══ Solomon AI Chat Helpers (re-exported from helpers_ai) ═══
from core.helpers_ai import (
    COMPETITOR_KNOWLEDGE,
    SOLOMON_SYSTEM_PROMPT,
    get_church_context,
)


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
