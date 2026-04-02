"""Solomon AI — Admin Groups Routes"""
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc
from models.schemas import Group, Attendance, Event, Person, Tenant, GroupCreate, AddMemberToGroupRequest, GroupAttendanceRecord

router = APIRouter()

@router.get("/admin/groups")
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
    
    query = {"is_active": True, "tenant_id": tenant_id}
    
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


@router.post("/admin/groups")
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
        is_active=True,
        enrollment_type=group_data.enrollment_type,
        campus_id=group_data.campus_id,
        category=group_data.category,
    )
    
    await db.groups.insert_one(new_group.model_dump())
    
    logger.info(f"Group created: {new_group.name} for tenant {tenant_id}")
    
    return {
        "message": "Group created successfully",
        "group": new_group.model_dump()
    }


@router.put("/admin/groups/{group_id}")
async def update_group(request: Request, group_id: str, updates: dict):
    """Update a group's details"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": group_id, "tenant_id": tenant_id}
    
    allowed_fields = [
        "name", "description", "group_type", "meeting_day", "meeting_time",
        "location", "capacity", "is_open", "leader_id", "enrollment_type",
        "campus_id", "category", "tags"
    ]
    
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    
    result = await db.groups.update_one(query, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"message": "Group updated successfully"}


@router.delete("/admin/groups/{group_id}")
async def delete_group(request: Request, group_id: str):
    """Delete (deactivate) a group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": group_id, "tenant_id": tenant_id}
    
    # Soft delete - set is_active to False
    result = await db.groups.update_one(query, {"$set": {"is_active": False}})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"message": "Group deleted successfully"}


@router.get("/admin/groups/{group_id}/members")
async def get_group_members(request: Request, group_id: str):
    """Get members of a specific group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify group exists and belongs to tenant
    query = {"id": group_id, "tenant_id": tenant_id}
    
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


@router.post("/admin/groups/{group_id}/members")
async def admin_add_member_to_group(request: Request, group_id: str, member_data: AddMemberToGroupRequest):
    """Admin adds a member to a group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify group exists
    query = {"id": group_id, "tenant_id": tenant_id}
    
    group = await db.groups.find_one(query, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Verify person exists
    person_query = {"id": member_data.person_id, "tenant_id": tenant_id}
    
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


@router.delete("/admin/groups/{group_id}/members/{person_id}")
async def admin_remove_member_from_group(request: Request, group_id: str, person_id: str):
    """Admin removes a member from a group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Verify group exists
    query = {"id": group_id, "tenant_id": tenant_id}
    
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


@router.get("/admin/groups/{group_id}/available-members")
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
    query = {"id": {"$nin": current_member_ids}, "tenant_id": tenant_id}
    
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


@router.post("/admin/groups/{group_id}/attendance")
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


@router.get("/admin/groups/{group_id}/attendance")
async def get_group_attendance_history(request: Request, group_id: str, limit: int = 8):
    """Get attendance history for a group (last 8 sessions)"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    records = await db.group_attendance.find(
        {"group_id": group_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("session_date", -1).limit(limit).to_list(limit)
    
    return {"sessions": records}


@router.get("/admin/groups/{group_id}/at-risk")
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


@router.post("/admin/groups/{group_id}/outreach")
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

# ============== PHASE 4: GROUP JOIN REQUESTS ==============


@router.get("/admin/groups/{group_id}/join-requests")
async def get_group_join_requests(request: Request, group_id: str, status: Optional[str] = None):
    """Get join requests for a group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    query = {"group_id": group_id, "tenant_id": tenant_id}
    if status:
        query["status"] = status
    requests_list = await db.group_join_requests.find(query, {"_id": 0}).sort("requested_at", -1).to_list(100)
    return {"requests": requests_list, "total": len(requests_list)}


@router.get("/admin/groups/join-requests/all")
async def get_all_join_requests(request: Request):
    """Get all pending join requests across all groups"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    requests_list = await db.group_join_requests.find(
        {"tenant_id": tenant_id, "status": "pending"}, {"_id": 0}
    ).sort("requested_at", -1).to_list(200)
    # Enrich with group names
    for req in requests_list:
        group = await db.groups.find_one({"id": req["group_id"]}, {"_id": 0, "name": 1})
        req["group_name"] = group.get("name", "Unknown") if group else "Unknown"
    return {"requests": requests_list, "total": len(requests_list)}


@router.put("/admin/groups/{group_id}/join-requests/{request_id}")
async def handle_join_request(request: Request, group_id: str, request_id: str, payload: dict):
    """Approve or reject a join request"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    action = payload.get("action", "approve")
    
    join_req = await db.group_join_requests.find_one(
        {"id": request_id, "group_id": group_id, "tenant_id": tenant_id}, {"_id": 0}
    )
    if not join_req:
        raise HTTPException(status_code=404, detail="Join request not found")
    
    if action == "approve":
        # Add member to group
        membership = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "group_id": group_id,
            "person_id": join_req["person_id"],
            "role": "member",
            "joined_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "is_active": True,
            "approved_by": user.get("user_id"),
        }
        await db.group_members.insert_one(membership)
        await db.groups.update_one({"id": group_id}, {"$inc": {"member_count": 1}})
        await db.group_join_requests.update_one(
            {"id": request_id},
            {"$set": {"status": "approved", "handled_at": datetime.now(timezone.utc).isoformat(), "handled_by": user.get("user_id")}}
        )
        return {"message": f"Approved {join_req.get('person_name', 'member')}'s request"}
    else:
        await db.group_join_requests.update_one(
            {"id": request_id},
            {"$set": {"status": "rejected", "handled_at": datetime.now(timezone.utc).isoformat(), "handled_by": user.get("user_id"), "rejection_reason": payload.get("reason", "")}}
        )
        return {"message": f"Rejected {join_req.get('person_name', 'member')}'s request"}

# ============== PHASE 4: GROUP EVENTS + RSVP ==============


@router.get("/admin/groups/{group_id}/events")
async def get_group_events(request: Request, group_id: str):
    """Get events for a specific group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    events = await db.group_events.find(
        {"group_id": group_id, "tenant_id": tenant_id}, {"_id": 0}
    ).sort("event_date", -1).to_list(100)
    # Enrich with RSVP counts
    for evt in events:
        rsvps = await db.group_event_rsvps.find({"event_id": evt["id"]}, {"_id": 0}).to_list(200)
        evt["rsvp_counts"] = {
            "attending": len([r for r in rsvps if r.get("response") == "attending"]),
            "maybe": len([r for r in rsvps if r.get("response") == "maybe"]),
            "declined": len([r for r in rsvps if r.get("response") == "declined"]),
        }
        evt["total_rsvps"] = len(rsvps)
    return {"events": events, "total": len(events)}


@router.post("/admin/groups/{group_id}/events")
async def create_group_event(request: Request, group_id: str, payload: dict):
    """Create a group event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    event = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "group_id": group_id,
        "title": payload.get("title", ""),
        "description": payload.get("description", ""),
        "event_date": payload.get("event_date", ""),
        "event_time": payload.get("event_time", ""),
        "location": payload.get("location", ""),
        "created_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.group_events.insert_one(event)
    return {"event": {k: v for k, v in event.items() if k != "_id"}}


@router.put("/admin/groups/{group_id}/events/{event_id}")
async def update_group_event(request: Request, group_id: str, event_id: str, payload: dict):
    """Update a group event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    updates = {}
    for field in ["title", "description", "event_date", "event_time", "location"]:
        if field in payload:
            updates[field] = payload[field]
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.group_events.update_one(
        {"id": event_id, "group_id": group_id, "tenant_id": tenant_id}, {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event updated"}


@router.delete("/admin/groups/{group_id}/events/{event_id}")
async def delete_group_event(request: Request, group_id: str, event_id: str):
    """Delete a group event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    result = await db.group_events.delete_one({"id": event_id, "group_id": group_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.group_event_rsvps.delete_many({"event_id": event_id})
    return {"message": "Event deleted"}


@router.post("/admin/groups/{group_id}/events/{event_id}/rsvp")
async def rsvp_group_event(request: Request, group_id: str, event_id: str, payload: dict):
    """RSVP to a group event (admin on behalf of member)"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    person_id = payload.get("person_id")
    response = payload.get("response", "attending")
    
    existing = await db.group_event_rsvps.find_one({"event_id": event_id, "person_id": person_id})
    if existing:
        await db.group_event_rsvps.update_one(
            {"event_id": event_id, "person_id": person_id},
            {"$set": {"response": response, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        rsvp = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "event_id": event_id,
            "group_id": group_id,
            "person_id": person_id,
            "person_name": payload.get("person_name", ""),
            "response": response,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.group_event_rsvps.insert_one(rsvp)
    return {"message": f"RSVP recorded as {response}"}


@router.get("/admin/groups/{group_id}/events/{event_id}/rsvps")
async def get_event_rsvps(request: Request, group_id: str, event_id: str):
    """Get RSVPs for a group event"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    rsvps = await db.group_event_rsvps.find(
        {"event_id": event_id, "tenant_id": tenant_id}, {"_id": 0}
    ).to_list(200)
    return {"rsvps": rsvps, "total": len(rsvps)}

# ============== PHASE 4: GROUP RESOURCES ==============


@router.get("/admin/groups/{group_id}/resources")
async def get_group_resources(request: Request, group_id: str):
    """Get shared resources for a group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    resources = await db.group_resources.find(
        {"group_id": group_id, "tenant_id": tenant_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return {"resources": resources, "total": len(resources)}


@router.post("/admin/groups/{group_id}/resources")
async def add_group_resource(request: Request, group_id: str, payload: dict):
    """Add a resource to a group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    resource = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "group_id": group_id,
        "title": payload.get("title", ""),
        "description": payload.get("description", ""),
        "resource_type": payload.get("resource_type", "link"),
        "url": payload.get("url", ""),
        "created_by": user.get("user_id"),
        "created_by_name": user.get("name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.group_resources.insert_one(resource)
    return {"resource": {k: v for k, v in resource.items() if k != "_id"}}


@router.delete("/admin/groups/{group_id}/resources/{resource_id}")
async def delete_group_resource(request: Request, group_id: str, resource_id: str):
    """Delete a group resource"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    result = await db.group_resources.delete_one({"id": resource_id, "group_id": group_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"message": "Resource deleted"}

# ============== PHASE 4: GROUP CHAT (Scaffolding) ==============


@router.get("/admin/groups/{group_id}/messages")
async def get_group_messages(request: Request, group_id: str, limit: int = 50, before: Optional[str] = None):
    """Get chat messages for a group"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    query = {"group_id": group_id, "tenant_id": tenant_id}
    if before:
        query["created_at"] = {"$lt": before}
    messages = await db.group_messages.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    messages.reverse()
    return {"messages": messages, "total": len(messages)}


@router.post("/admin/groups/{group_id}/messages")
async def send_group_message(request: Request, group_id: str, payload: dict):
    """Send a message in group chat"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    message = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "group_id": group_id,
        "sender_id": user.get("user_id"),
        "sender_name": user.get("name", "Admin"),
        "content": payload.get("content", ""),
        "message_type": payload.get("message_type", "text"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.group_messages.insert_one(message)
    return {"message": {k: v for k, v in message.items() if k != "_id"}}



# ============== GROUP Q&A (Admin) ==============

@router.get("/admin/groups/{group_id}/questions")
async def admin_get_group_questions(request: Request, group_id: str):
    """Admin/Leader: View all questions for a group."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    questions = await db.group_questions.find(
        {"group_id": group_id, "tenant_id": tenant_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return {"questions": questions}


@router.put("/admin/groups/{group_id}/questions/{question_id}/answer")
async def admin_answer_group_question(request: Request, group_id: str, question_id: str):
    """Admin/Leader: Answer a group question."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    body = await request.json()
    answer = body.get("answer", "").strip()
    if not answer:
        raise HTTPException(status_code=400, detail="Answer cannot be empty")

    result = await db.group_questions.update_one(
        {"id": question_id, "group_id": group_id, "tenant_id": tenant_id},
        {"$set": {
            "answer": answer,
            "answered_by": user.get("name", user.get("email")),
            "answered_at": datetime.now(timezone.utc).isoformat(),
            "status": "answered",
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Answer posted"}


@router.get("/admin/group-notifications")
async def admin_get_group_notifications(request: Request):
    """Admin: See all group notification signups."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    notifications = await db.group_notifications.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return {"notifications": notifications}
