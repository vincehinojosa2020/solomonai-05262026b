"""
Solomon AI — Seed: Pathways + Meetings
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from core import db, DEFAULT_TENANT_ID
from models.schemas import PastorMeetingSlot, PastorMeeting


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
        "pathway_course_001", "pathway_course_002", "pathway_course_003",
        "pathway_course_004", "pathway_course_005", "pathway_course_006",
        "pathway_course_007", "pathway_course_008"
    ]

    now_iso = datetime.now(timezone.utc).isoformat()

    pathways_courses = [
        {"id": "pathway_course_001", "tenant_id": "abundant-east-001", "title": "Abundant Next Steps", "description": "Your on-ramp to belonging, serving, and growing at Abundant.", "cover_image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80", "category": "New Members Track", "level": "Beginner", "is_published": True, "created_at": now_iso, "updated_at": now_iso},
        {"id": "pathway_course_002", "tenant_id": "abundant-east-001", "title": "Preparing for Baptism", "description": "Understand baptism and get ready to share your story.", "cover_image_url": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80", "category": "Baptism Track", "level": "Beginner", "is_published": True, "created_at": now_iso, "updated_at": now_iso},
        {"id": "pathway_course_003", "tenant_id": "abundant-east-001", "title": "Foundations of Discipleship", "description": "Build daily rhythms of scripture, prayer, and obedience.", "cover_image_url": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?auto=format&fit=crop&w=1200&q=80", "category": "Discipleship Track", "level": "Intermediate", "is_published": True, "created_at": now_iso, "updated_at": now_iso},
        {"id": "pathway_course_004", "tenant_id": "abundant-east-001", "title": "Financial Peace University", "description": "Walk through budgeting, generosity, and debt-free living.", "cover_image_url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80", "category": "Stewardship Track", "level": "Intermediate", "is_published": True, "created_at": now_iso, "updated_at": now_iso},
        {"id": "pathway_course_005", "tenant_id": "abundant-east-001", "title": "Serving with Purpose", "description": "Discover your gifts and find the right team to serve.", "cover_image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80", "category": "Leadership Track", "level": "Beginner", "is_published": True, "created_at": now_iso, "updated_at": now_iso},
        {"id": "pathway_course_006", "tenant_id": "abundant-east-001", "title": "Prayer & Presence", "description": "Deepen your prayer life and sensitivity to God's presence.", "cover_image_url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80", "category": "Spiritual Practices", "level": "Intermediate", "is_published": True, "created_at": now_iso, "updated_at": now_iso},
        {"id": "pathway_course_007", "tenant_id": "abundant-east-001", "title": "Marriage & Family Care", "description": "Strengthen your relationships and build a healthy home.", "cover_image_url": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=1200&q=80", "category": "Family Track", "level": "Beginner", "is_published": True, "created_at": now_iso, "updated_at": now_iso},
        {"id": "pathway_course_008", "tenant_id": "abundant-east-001", "title": "Mission & Outreach", "description": "Live on mission through local and global outreach.", "cover_image_url": "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?auto=format&fit=crop&w=1200&q=80", "category": "Outreach Track", "level": "Beginner", "is_published": True, "created_at": now_iso, "updated_at": now_iso},
    ]

    pathways_lessons = [
        {"id": "pathway_lesson_001", "tenant_id": "abundant-east-001", "course_id": "pathway_course_001", "title": "Welcome to Abundant", "description": "Meet the heart, mission, and values of Abundant Church.", "youtube_id": "FoPI3hMbXvw", "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw", "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg", "duration_label": "15:40", "duration_seconds": 940, "sort_order": 1, "is_published": True, "created_at": now_iso, "updated_at": now_iso},
        {"id": "pathway_lesson_002", "tenant_id": "abundant-east-001", "course_id": "pathway_course_001", "title": "Belonging & Community", "description": "Find your people and take your next step into community.", "youtube_id": "pzpbbibEWPE", "video_url": "https://youtube.com/watch?v=pzpbbibEWPE", "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg", "duration_label": "18:20", "duration_seconds": 1100, "sort_order": 2, "is_published": True, "created_at": now_iso, "updated_at": now_iso},
        {"id": "pathway_lesson_003", "tenant_id": "abundant-east-001", "course_id": "pathway_course_002", "title": "Why Baptism Matters", "description": "Understand the significance of baptism and next steps.", "youtube_id": "Lnj6vMvOLME", "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME", "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg", "duration_label": "16:05", "duration_seconds": 965, "sort_order": 1, "is_published": True, "created_at": now_iso, "updated_at": now_iso},
        {"id": "pathway_lesson_004", "tenant_id": "abundant-east-001", "course_id": "pathway_course_002", "title": "Preparing Your Story", "description": "Craft your testimony and prepare for the baptism service.", "youtube_id": "wCjwUQMhCIY", "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY", "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg", "duration_label": "14:35", "duration_seconds": 875, "sort_order": 2, "is_published": True, "created_at": now_iso, "updated_at": now_iso},
    ]

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
            "assigned_at": now_iso,
            "updated_at": now_iso
        }
        await db.pathways_enrollments.update_one(
            {"id": enrollment["id"]},
            {"$setOnInsert": {**enrollment, "created_at": now_iso}},
            upsert=True
        )
