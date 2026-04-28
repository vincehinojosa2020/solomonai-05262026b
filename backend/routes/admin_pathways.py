"""Solomon AI — Admin Pathways & Next Steps Routes"""
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import (
    serialize_doc, duration_to_seconds, extract_youtube_id,
    evaluate_member_next_steps_membership,
)
from core.seed import ensure_abundant_pathways_data
from models.schemas import (
    ThinkificUpdate, NextStepsApprovalRequest,
    PathwaysCourse, PathwaysCourseCreate, PathwaysCourseUpdate,
    PathwaysLesson, PathwaysLessonCreate, PathwaysLessonUpdate,
    PathwaysEnrollment, PathwaysEnrollmentRequest,
    Tenant,
)

router = APIRouter()

@router.get("/admin/thinkific")
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


@router.patch("/admin/thinkific")
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


@router.get("/admin/next-steps/approvals")
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


@router.post("/admin/next-steps/approvals/{user_id}")
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


@router.get("/admin/pathways/courses")
async def get_admin_pathways_courses(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    # Ensure demo data exists for Abundant Church
    await ensure_abundant_pathways_data(tenant_id)
    
    query = {"tenant_id": tenant_id}

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


@router.post("/admin/pathways/courses")
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


@router.put("/admin/pathways/courses/{course_id}")
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


@router.delete("/admin/pathways/courses/{course_id}")
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


@router.get("/admin/pathways/courses/{course_id}/lessons")
async def get_pathways_lessons(request: Request, course_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    lessons = await db.pathways_lessons.find(
        {"course_id": course_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("sort_order", 1).to_list(200)

    return {"lessons": [serialize_doc(lsn) for lsn in lessons]}


@router.post("/admin/pathways/courses/{course_id}/lessons")
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


@router.put("/admin/pathways/lessons/{lesson_id}")
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


@router.delete("/admin/pathways/lessons/{lesson_id}")
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


@router.get("/admin/pathways/courses/{course_id}/assignments")
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


@router.get("/admin/pathways/available-members")
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


@router.post("/admin/pathways/courses/{course_id}/assignments")
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


@router.delete("/admin/pathways/courses/{course_id}/assignments/{member_id}")
async def remove_pathways_member(request: Request, course_id: str, member_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await db.pathways_enrollments.delete_one({"course_id": course_id, "tenant_id": tenant_id, "user_id": member_id})
    await db.pathways_progress.delete_many({"course_id": course_id, "tenant_id": tenant_id, "user_id": member_id})
    return {"message": "Member removed"}

