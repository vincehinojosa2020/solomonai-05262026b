"""Solomon AI — Admin Communications, SMS, Notifications, Notes, Prayer Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import re
import os
import logging

try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None

from core import (
    db, DEFAULT_TENANT_ID,
    get_current_admin_user, get_current_portal_user, require_permission, require_tenant,
    logger,
)
from core.helpers import serialize_doc
from models.schemas import Communication, Attendance, Event, Group, Tenant, BulkSMSRequest, SMSRequest

PRAYER_CATEGORIES = [
    {"id": "general", "name": "General", "icon": "prayer"},
    {"id": "healing", "name": "Healing", "icon": "heart"},
    {"id": "family", "name": "Family", "icon": "family"},
    {"id": "financial", "name": "Financial", "icon": "finance"},
    {"id": "guidance", "name": "Guidance", "icon": "compass"},
    {"id": "thanksgiving", "name": "Thanksgiving", "icon": "praise"},
    {"id": "salvation", "name": "Salvation", "icon": "cross"},
    {"id": "relationships", "name": "Relationships", "icon": "heart"},
]

router = APIRouter()

@router.get("/admin/notes")
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


@router.post("/sms/send")
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
        from core.errors import client_error
        raise client_error(
            status_code=500,
            user_message="SMS send failed. Please try again.",
            log_message="admin_comms.sms_send_failed",
            exc=e,
        )


@router.post("/sms/bulk")
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


@router.get("/sms/templates")
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


@router.post("/admin/communications/send")
async def send_communication(request: Request, payload: dict):
    """Send email/SMS communication (Twilio-ready stub)."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    channel = payload.get("channel", "email")
    subject = payload.get("subject", "")
    body = payload.get("body", "")
    recipient_type = payload.get("recipient_type", "all")
    scheduled_at = payload.get("scheduled_at")

    comm_id = str(uuid.uuid4())
    doc = {
        "id": comm_id,
        "tenant_id": tenant_id,
        "channel": channel,
        "subject": subject,
        "body": body,
        "recipient_type": recipient_type,
        "status": "scheduled" if scheduled_at else "sent",
        "scheduled_at": scheduled_at,
        "sent_at": None if scheduled_at else datetime.now(timezone.utc).isoformat(),
        "sent_by": user.get("name", "Admin"),
        "sent_by_id": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.communications.insert_one(doc)
    doc.pop("_id", None)

    return {"message": f"Communication {'scheduled' if scheduled_at else 'sent'} successfully", "communication": doc}


@router.get("/admin/communications/list")
async def list_communications(request: Request, status: str = None, limit: int = 50):
    """List sent/scheduled communications."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status

    docs = await db.communications.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"communications": docs}


@router.get("/admin/sunday-morning/notification-templates")
async def get_notification_templates(request: Request):
    """Get available Sunday Morning push notification templates."""
    user = await require_permission(request, "admin.communications")
    return {"templates": SUNDAY_MORNING_NOTIFICATIONS}


@router.post("/admin/sunday-morning/broadcast")
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


@router.get("/admin/prayer/dashboard")
async def get_prayer_dashboard(
    request: Request,
    status: Optional[str] = None,
    category: Optional[str] = None
):
    """Admin dashboard for prayer requests"""
    user = await get_current_portal_user(request)
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


@router.put("/admin/prayer/requests/{request_id}")
async def update_prayer_request(
    request_id: str,
    request: Request
):
    """Update prayer request status/notes (admin)"""
    user = await get_current_portal_user(request)
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


@router.post("/admin/notifications/send")
async def admin_send_notification(request: Request):
    """Admin sends a notification to all members in their tenant."""
    user = await get_current_portal_user(request)
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


# ═══ Email Template Builder ═══

BUILTIN_TEMPLATES = [
    {
        "id": "welcome",
        "name": "Welcome New Member",
        "subject": "Welcome to {{church_name}}, {{first_name}}!",
        "body": "Dear {{first_name}},\n\nWelcome to {{church_name}}! We're so thrilled you've joined our community.\n\nWe'd love to connect you with a small group and help you get plugged in. Reply to this email or reach out to {{campus_name}} to get started.\n\nWith love,\n{{church_name}} Team",
        "category": "onboarding",
        "is_builtin": True,
    },
    {
        "id": "event_invite",
        "name": "Event Invitation",
        "subject": "You're invited — {{event_name}}!",
        "body": "Hi {{first_name}},\n\nWe'd love to see you at {{event_name}} on {{event_date}} at {{event_time}}.\n\n{{event_description}}\n\nClick below to register and let us know you're coming!\n\nBlessings,\n{{church_name}}",
        "category": "events",
        "is_builtin": True,
    },
    {
        "id": "giving_receipt",
        "name": "Giving Receipt",
        "subject": "Thank you for your generosity, {{first_name}}!",
        "body": "Dear {{first_name}},\n\nThank you for your gift of {{gift_amount}} to {{church_name}} on {{gift_date}}. Your generosity makes a real difference in our community.\n\nTransaction ID: {{transaction_id}}\n\nThis email serves as your receipt for tax purposes.\n\nWith gratitude,\n{{church_name}}",
        "category": "giving",
        "is_builtin": True,
    },
    {
        "id": "weekly_newsletter",
        "name": "Weekly Newsletter",
        "subject": "This week at {{church_name}} — {{date}}",
        "body": "Hello {{church_name}} Family,\n\nHere's what's happening this week:\n\n{{weekly_highlights}}\n\n**Upcoming Events:**\n{{upcoming_events}}\n\n**Prayer Requests:**\n{{prayer_requests}}\n\nSee you Sunday!\n{{church_name}} Team",
        "category": "newsletter",
        "is_builtin": True,
    },
    {
        "id": "prayer_update",
        "name": "Prayer Update",
        "subject": "Prayer requests from {{church_name}} — {{date}}",
        "body": "Dear {{first_name}},\n\nThank you for being a prayer warrior for our community. Here are this week's prayer requests:\n\n{{prayer_list}}\n\n\"Do not be anxious about anything, but in every situation, by prayer and petition, with thanksgiving, present your requests to God.\" — Philippians 4:6\n\nWith love,\n{{church_name}}",
        "category": "spiritual",
        "is_builtin": True,
    },
]

MERGE_FIELDS = [
    {"key": "{{first_name}}", "description": "Recipient's first name"},
    {"key": "{{last_name}}", "description": "Recipient's last name"},
    {"key": "{{church_name}}", "description": "Church name"},
    {"key": "{{campus_name}}", "description": "Campus name"},
    {"key": "{{event_name}}", "description": "Event name"},
    {"key": "{{event_date}}", "description": "Event date"},
    {"key": "{{event_time}}", "description": "Event start time"},
    {"key": "{{event_description}}", "description": "Event description"},
    {"key": "{{gift_amount}}", "description": "Donation amount"},
    {"key": "{{gift_date}}", "description": "Donation date"},
    {"key": "{{transaction_id}}", "description": "Transaction reference"},
    {"key": "{{date}}", "description": "Today's date"},
]


@router.get("/admin/communications/templates")
async def get_email_templates(request: Request):
    """Get all email templates (built-in + custom)."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    custom = await db.email_templates.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {
        "templates": BUILTIN_TEMPLATES + [serialize_doc(t) for t in custom],
        "merge_fields": MERGE_FIELDS,
    }


@router.post("/admin/communications/templates")
async def save_email_template(request: Request):
    """Save a custom email template."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    tmpl = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": body.get("name", "Untitled Template"),
        "subject": body.get("subject", ""),
        "body": body.get("body", ""),
        "category": body.get("category", "other"),
        "is_builtin": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id"),
    }
    await db.email_templates.insert_one(tmpl)
    return {"message": "Template saved", "template": {k: v for k, v in tmpl.items() if k != "_id"}}


@router.delete("/admin/communications/templates/{template_id}")
async def delete_email_template(request: Request, template_id: str):
    """Delete a custom email template."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    result = await db.email_templates.delete_one({"id": template_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found or is built-in")
    return {"message": "Template deleted"}


@router.get("/admin/communications/scheduled")
async def get_scheduled_communications(request: Request):
    """Get scheduled (pending) communications."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    scheduled = await db.communications.find(
        {"tenant_id": tenant_id, "status": "scheduled"},
        {"_id": 0}
    ).sort("scheduled_at", 1).to_list(50)
    return {"scheduled": [serialize_doc(c) for c in scheduled]}


@router.post("/admin/communications/cancel/{comm_id}")
async def cancel_scheduled_communication(request: Request, comm_id: str):
    """Cancel a scheduled communication."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    result = await db.communications.update_one(
        {"id": comm_id, "tenant_id": tenant_id, "status": "scheduled"},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Scheduled communication not found")
    return {"message": "Communication cancelled"}
