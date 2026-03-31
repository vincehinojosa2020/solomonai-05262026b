"""Solomon AI — v1 Agent API Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import uuid
import logging

from core import db, logger
from core.helpers import (
    serialize_doc, validate_agent_api_key, check_agent_permission,
    ANOMALY_THRESHOLDS,
)

router = APIRouter()

@router.get("/v1/agent/scout")
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


@router.get("/v1/agent/visitors")
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


@router.get("/v1/agent/members")
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


@router.patch("/v1/agent/members/{member_id}/outreach")
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


@router.get("/v1/agent/events")
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


@router.get("/v1/agent/groups")
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


@router.get("/v1/agent/meetings")
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


@router.get("/v1/agent/giving/summary")
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


@router.get("/v1/agent/notes")
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


@router.post("/v1/agent/webhooks")
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


@router.get("/v1/agent/webhooks")
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


@router.delete("/v1/agent/webhooks/{webhook_id}")
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


@router.get("/v1/agent/docs")
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
