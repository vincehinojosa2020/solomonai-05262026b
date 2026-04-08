"""
Solomon AI — Seed: Accounts + Demo Content + Go-Live Portal
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import hashlib
import logging
import os

from core import (
    db, DEFAULT_TENANT_ID, PERMISSION_REGISTRY,
    get_permissions_for_user, logger,
)
from core.helpers import DEFAULT_NEXT_STEPS_URL


async def ensure_mobile_demo_accounts():
    """Ensure required demo users exist for mobile QA and onboarding."""
    now_iso = datetime.now(timezone.utc).isoformat()
    demo_password_hash = hashlib.sha256("Demo2026!".encode()).hexdigest()

    tenant_defaults = [
        {"id": "abundant-east-001", "name": "Abundant East", "subdomain": "abundant-east", "subscription_status": "active", "created_at": now_iso, "organization_id": "abundant-org-001", "organization_name": "Abundant Church", "city": "El Paso", "state": "TX", "plan": "enterprise", "monthly_rate": 2999, "senior_pastor": "Pastor David Martinez"},
        {"id": "abundant-downtown-001", "name": "Abundant Downtown", "subdomain": "abundant-downtown", "subscription_status": "active", "created_at": now_iso, "organization_id": "abundant-org-001", "organization_name": "Abundant Church", "city": "El Paso", "state": "TX", "plan": "enterprise", "monthly_rate": 2999, "senior_pastor": "Pastor David Martinez"},
        {"id": "abundant-west-001", "name": "Abundant West", "subdomain": "abundant-west", "subscription_status": "active", "created_at": now_iso, "organization_id": "abundant-org-001", "organization_name": "Abundant Church", "city": "El Paso", "state": "TX", "plan": "enterprise", "monthly_rate": 2999, "senior_pastor": "Pastor David Martinez"},
    ]

    for tenant in tenant_defaults:
        await db.tenants.update_one({"id": tenant["id"]}, {"$set": tenant}, upsert=True)

    old_admin = await db.users.find_one({"email": "admin@solomon.ai"})
    if old_admin:
        try:
            await db.users.update_one(
                {"email": "admin@solomon.ai"},
                {"$set": {"email": "admin@solomonai.us", "password_hash": demo_password_hash}}
            )
            logging.info("Migrated admin@solomon.ai -> admin@solomonai.us")
        except Exception as e:
            logging.warning(f"Admin email migration warning: {e}")

    required_accounts = [
        {"email": "shannonnieman1030@gmail.com", "user_id": "shannon_nieman_001", "name": "Shannon Nieman", "first_name": "Shannon", "last_name": "Nieman", "role": "church_admin", "role_title": "Lead Pastor", "tenant_id": "abundant-east-001", "accessible_tenant_ids": ["abundant-east-001", "abundant-downtown-001", "abundant-west-001"], "organization_id": "abundant-org-001", "organization_name": "Abundant Church"},
        {"email": "jacobpacheco@abundanteast.com", "user_id": "jacob_pacheco_001", "name": "Jacob Pacheco", "first_name": "Jacob", "last_name": "Pacheco", "role": "church_admin", "role_title": "Pastoral Staff", "tenant_id": "abundant-east-001", "accessible_tenant_ids": ["abundant-east-001", "abundant-downtown-001", "abundant-west-001"], "organization_id": "abundant-org-001", "organization_name": "Abundant Church"},
        {"email": "avopham@gmail.com", "user_id": "f1d0f1d8-de66-4fc0-a8c7-8f81f679ce22", "name": "Aivy Vopham", "first_name": "Aivy", "last_name": "Vopham", "role": "church_admin", "role_title": "Church Administrator", "tenant_id": "abundant-east-001", "accessible_tenant_ids": ["abundant-east-001", "abundant-downtown-001", "abundant-west-001"], "organization_id": "abundant-org-001", "organization_name": "Abundant Church"},
        {"email": "vince@charlottesoftwareengineering.com", "user_id": "cc7a823c-4d38-45d9-bb09-1df8caffe258", "name": "Vince Hinojosa", "first_name": "Vince", "last_name": "Hinojosa", "role": "member", "tenant_id": "abundant-east-001"},
        {"email": "admin@solomonai.us", "user_id": "platform_admin_001", "name": "Solomon Platform Admin", "first_name": "Solomon", "last_name": "Admin", "role": "platform_admin", "tenant_id": None},
        {"email": "member@abundant.church", "user_id": "member_abundant", "name": "Maria Garcia", "first_name": "Maria", "last_name": "Garcia", "role": "member", "tenant_id": "abundant-east-001"},
        {"email": "admin@abundant.church", "user_id": "admin_abundant", "name": "Pastor David Martinez", "first_name": "David", "last_name": "Martinez", "role": "church_admin", "tenant_id": "abundant-east-001"},
    ]

    god_mode_emails = {"shannonnieman1030@gmail.com", "jacobpacheco@abundanteast.com"}
    seed_success = []
    seed_fail = []
    for account in required_accounts:
        pw = demo_password_hash
        if account["email"] in god_mode_emails:
            permissions = PERMISSION_REGISTRY[:]
        else:
            permissions = get_permissions_for_user(account)
        update_doc = {**account, "password_hash": pw, "permissions": permissions, "is_active": True, "updated_at": now_iso}
        try:
            result = await db.users.update_one(
                {"email": account["email"]},
                {"$set": update_doc, "$setOnInsert": {"created_at": now_iso}},
                upsert=True
            )
            seed_success.append(f"{account['email']} (matched={result.matched_count}, modified={result.modified_count}, upserted={result.upserted_id is not None})")
        except Exception:
            try:
                result = await db.users.update_one({"user_id": account["user_id"]}, {"$set": update_doc})
                seed_success.append(f"{account['email']} via user_id fallback (modified={result.modified_count})")
            except Exception:
                try:
                    await db.users.delete_one({"user_id": account["user_id"]})
                    await db.users.insert_one({**update_doc, "created_at": now_iso})
                    seed_success.append(f"{account['email']} via delete+insert")
                except Exception as e3:
                    seed_fail.append(f"{account['email']}: {e3}")

    logging.info(f"[SEED] Success: {len(seed_success)} accounts - {', '.join(seed_success)}")
    if seed_fail:
        logging.error(f"[SEED] FAILED: {seed_fail}")

    await ensure_abundant_mobile_demo_content(now_iso)
    await ensure_abundant_go_live_portal_content(now_iso)

    health_stats = {
        "abundant-east-001": {"total_members": 22000, "active_members": 15400, "mtd_giving": 220000, "ytd_giving": 2420000, "last_attendance": 5280, "active_groups": 264, "recurring_givers": 2860, "new_members_this_month": 87, "first_time_visitors": 134, "average_attendance": 5100, "total_giving": 2420000},
        "abundant-downtown-001": {"total_members": 18500, "active_members": 12950, "mtd_giving": 185000, "ytd_giving": 2035000, "last_attendance": 4440, "active_groups": 222, "recurring_givers": 2405, "new_members_this_month": 72, "first_time_visitors": 113, "average_attendance": 4300, "total_giving": 2035000},
        "abundant-west-001": {"total_members": 14000, "active_members": 9800, "mtd_giving": 140000, "ytd_giving": 1540000, "last_attendance": 3360, "active_groups": 168, "recurring_givers": 1820, "new_members_this_month": 54, "first_time_visitors": 86, "average_attendance": 3250, "total_giving": 1540000},
        "cristoviene-church-001": {"total_members": 1200, "active_members": 240, "mtd_giving": 2400, "ytd_giving": 26400, "last_attendance": 96, "active_groups": 3, "recurring_givers": 36, "new_members_this_month": 2, "first_time_visitors": 5, "average_attendance": 90, "total_giving": 26400},
        "pottershouse-church-001": {"total_members": 8500, "active_members": 1700, "mtd_giving": 17000, "ytd_giving": 187000, "last_attendance": 680, "active_groups": 17, "recurring_givers": 255, "new_members_this_month": 8, "first_time_visitors": 15, "average_attendance": 650, "total_giving": 187000},
    }
    for tid, stats in health_stats.items():
        stats["tenant_id"] = tid
        stats["updated_at"] = now_iso
        await db.dashboard_stats_cache.update_one({"tenant_id": tid}, {"$set": stats}, upsert=True)


async def ensure_abundant_mobile_demo_content(now_iso: Optional[str] = None):
    """Seed deterministic demo content expected by mobile + web QA checks."""
    tenant_id = DEFAULT_TENANT_ID
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()

    await db.tenants.update_one({"id": tenant_id}, {"$set": {"next_steps_url": DEFAULT_NEXT_STEPS_URL, "updated_at": now_iso}})

    member_user = await db.users.find_one({"email": "member@abundant.church"}, {"_id": 0})
    if not member_user:
        return

    person_doc = {"id": "person_member_abundant", "tenant_id": tenant_id, "first_name": "Maria", "last_name": "Garcia", "email": "member@abundant.church", "mobile_phone": "915-555-0101", "membership_status": "member", "membership_date": "2019-03-15", "ytd_giving": 500, "lifetime_giving": 3500, "updated_at": now_iso, "created_at": now_iso}
    await db.people.update_one({"email": "member@abundant.church", "tenant_id": tenant_id}, {"$set": person_doc}, upsert=True)

    funds = [
        {"id": "fund_general_mobile", "name": "General Fund", "goal_amount": 1500000},
        {"id": "fund_building_mobile", "name": "Building Fund", "goal_amount": 750000}
    ]
    for fund in funds:
        await db.funds.update_one(
            {"id": fund["id"], "tenant_id": tenant_id},
            {"$set": {"tenant_id": tenant_id, "is_active": True, "current_amount": 0, "updated_at": now_iso, **fund}, "$setOnInsert": {"created_at": now_iso}},
            upsert=True
        )

    merch_products = [
        {"id": "merch_mobile_001", "name": "SO BE IT Vinyl", "price": 40, "category": "Music", "is_featured": True, "description": "Limited edition SO BE IT worship vinyl.", "image_url": "https://images.unsplash.com/photo-1461360370896-922624d12aa1?auto=format&fit=crop&w=1200&q=80"},
        {"id": "merch_mobile_002", "name": "SO BE IT Hoodie", "price": 60, "category": "Apparel", "is_featured": True, "description": "Premium hoodie from the SO BE IT collection.", "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=1200&q=80"},
        {"id": "merch_mobile_003", "name": "Abundant YETI Tumbler", "price": 42, "category": "Drinkware", "is_featured": True, "description": "Insulated tumbler with engraved Abundant logo.", "image_url": "https://images.unsplash.com/photo-1527169402691-feff5539e52c?auto=format&fit=crop&w=1200&q=80"},
        {"id": "merch_mobile_004", "name": "SO BE IT T-Shirt", "price": 35, "category": "Apparel", "is_featured": False, "description": "Soft cotton tee featuring SO BE IT art.", "image_url": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=1200&q=80"},
        {"id": "merch_mobile_005", "name": "Church Tote Bag", "price": 28, "category": "Accessories", "is_featured": False, "description": "Canvas tote bag for Sunday essentials.", "image_url": "https://images.unsplash.com/photo-1594223274512-ad4803739b7c?auto=format&fit=crop&w=1200&q=80"},
    ]
    merch_ids = [item["id"] for item in merch_products]
    for product in merch_products:
        await db.merch_products.update_one(
            {"id": product["id"], "tenant_id": tenant_id},
            {"$set": {"tenant_id": tenant_id, "is_active": True, "inventory": 120, "updated_at": now_iso, **product}, "$setOnInsert": {"created_at": now_iso}},
            upsert=True
        )
    await db.merch_products.update_many({"tenant_id": tenant_id, "id": {"$nin": merch_ids}}, {"$set": {"is_active": False, "updated_at": now_iso}})

    cafe_items = [
        {"id": "cafe_mobile_001", "name": "Latte", "price": 5, "category": "Coffee", "is_featured": True, "description": "Espresso with silky steamed milk."},
        {"id": "cafe_mobile_002", "name": "Cold Brew", "price": 5, "category": "Coffee", "is_featured": False, "description": "Slow-steeped cold brew over ice."},
        {"id": "cafe_mobile_003", "name": "Croissant", "price": 3, "category": "Pastry", "is_featured": True, "description": "Buttery flaky croissant baked fresh."},
        {"id": "cafe_mobile_004", "name": "Blueberry Muffin", "price": 3, "category": "Pastry", "is_featured": False, "description": "Classic blueberry muffin."},
        {"id": "cafe_mobile_005", "name": "Chai Tea", "price": 4, "category": "Tea", "is_featured": False, "description": "Warm spiced chai tea."},
    ]
    cafe_ids = [item["id"] for item in cafe_items]
    for item in cafe_items:
        await db.cafe_items.update_one(
            {"id": item["id"], "tenant_id": tenant_id},
            {"$set": {"tenant_id": tenant_id, "is_active": True, "updated_at": now_iso, **item}, "$setOnInsert": {"created_at": now_iso}},
            upsert=True
        )
    await db.cafe_items.update_many({"tenant_id": tenant_id, "id": {"$nin": cafe_ids}}, {"$set": {"is_active": False, "updated_at": now_iso}})

    sermons = [
        {"id": "sermon_mobile_001", "title": "SO BE IT", "instructor": "Pastor James", "published_at": "2026-03-09", "duration": "42:00", "duration_seconds": 2520, "youtube_id": "FoPI3hMbXvw", "youtube_url": "https://youtube.com/watch?v=FoPI3hMbXvw"},
        {"id": "sermon_mobile_002", "title": "Unshakeable Faith", "instructor": "Pastor James", "published_at": "2026-03-02", "duration": "38:00", "duration_seconds": 2280, "youtube_id": "pzpbbibEWPE", "youtube_url": "https://youtube.com/watch?v=pzpbbibEWPE"},
        {"id": "sermon_mobile_003", "title": "New Beginnings", "instructor": "Pastor Sarah", "published_at": "2026-02-23", "duration": "45:00", "duration_seconds": 2700, "youtube_id": "Lnj6vMvOLME", "youtube_url": "https://youtube.com/watch?v=Lnj6vMvOLME"},
    ]
    sermon_ids = [s["id"] for s in sermons]
    for sermon in sermons:
        await db.media_videos.update_one(
            {"id": sermon["id"], "tenant_id": tenant_id},
            {"$set": {"tenant_id": tenant_id, "description": sermon["title"], "thumbnail_url": f"https://i.ytimg.com/vi/{sermon['youtube_id']}/maxresdefault.jpg", "is_featured": sermon["id"] == "sermon_mobile_001", "is_published": True, "content_type": "sermon", "updated_at": now_iso, **sermon}, "$setOnInsert": {"created_at": now_iso}},
            upsert=True
        )
    await db.media_videos.update_many({"tenant_id": tenant_id, "content_type": "sermon", "id": {"$nin": sermon_ids}}, {"$set": {"is_published": False, "updated_at": now_iso}})

    donation_seed = [
        {"id": "don_mobile_001", "amount": 150, "fund_id": "fund_general_mobile", "donation_date": "2026-01-05"},
        {"id": "don_mobile_002", "amount": 150, "fund_id": "fund_general_mobile", "donation_date": "2026-02-02"},
        {"id": "don_mobile_003", "amount": 150, "fund_id": "fund_general_mobile", "donation_date": "2026-03-02"},
        {"id": "don_mobile_004", "amount": 50, "fund_id": "fund_building_mobile", "donation_date": "2026-02-14"},
    ]
    donation_ids = [d["id"] for d in donation_seed]
    for donation in donation_seed:
        await db.donations.update_one(
            {"id": donation["id"], "tenant_id": tenant_id},
            {"$set": {"tenant_id": tenant_id, "person_id": person_doc["id"], "fund_name": "General Fund" if donation["fund_id"] == "fund_general_mobile" else "Building Fund", "payment_method": "card", "status": "completed", "created_at": now_iso, **donation}},
            upsert=True
        )
    await db.donations.delete_many({"tenant_id": tenant_id, "person_id": person_doc["id"], "id": {"$nin": donation_ids}})

    child_doc = {"id": "child_emma_johnson", "tenant_id": tenant_id, "parent_user_id": member_user["user_id"], "name": "Emma Johnson", "birthdate": "2019-08-15", "allergies": "None", "special_needs": "", "emergency_contact": "Maria Garcia", "emergency_phone": "915-555-0101", "updated_at": now_iso, "created_at": now_iso}
    await db.children.update_one({"id": child_doc["id"], "tenant_id": tenant_id}, {"$set": child_doc}, upsert=True)

    ethan_doc = {"id": "child_ethan_johnson", "tenant_id": tenant_id, "name": "Ethan Johnson", "age": 7, "birthday": "2019-05-10", "classroom": "Elementary", "allergies": "None", "emergency_contact": "Maria Garcia", "emergency_phone": "915-555-0101", "parent_name": "Maria Garcia", "parent_phone": "915-555-0101", "parent_user_id": member_user["user_id"], "updated_at": now_iso, "created_at": now_iso}
    await db.children.update_one({"id": ethan_doc["id"], "tenant_id": tenant_id}, {"$set": ethan_doc}, upsert=True)

    baby_hinojosa_doc = {"id": "80f242e5-de94-4d96-9f21-1a3aff0ba40d", "tenant_id": tenant_id, "parent_user_id": "cc7a823c-4d38-45d9-bb09-1df8caffe258", "name": "Baby Hinojosa", "first_name": "Baby", "last_name": "Hinojosa", "birthdate": "2023-03-15", "grade": "PreK", "classroom": "Sunday School Adventures", "allergies": "", "special_needs": "", "emergency_contact": "Vince Hinojosa", "emergency_phone": "", "updated_at": now_iso, "created_at": now_iso}
    await db.children.update_one({"id": baby_hinojosa_doc["id"], "tenant_id": tenant_id}, {"$set": baby_hinojosa_doc}, upsert=True)

    checkins = [
        {"id": "chk_mobile_001", "service_date": "2026-03-09"},
        {"id": "chk_mobile_002", "service_date": "2026-02-23"},
        {"id": "chk_mobile_003", "service_date": "2026-02-16"},
        {"id": "chk_mobile_004", "service_date": "2026-02-09"},
    ]
    checkin_ids = [item["id"] for item in checkins]
    for entry in checkins:
        await db.member_checkins.update_one(
            {"id": entry["id"], "tenant_id": tenant_id},
            {"$set": {"tenant_id": tenant_id, "user_id": member_user["user_id"], "service_id": None, "check_in_type": "in_person", "check_in_time": f"{entry['service_date']}T09:00:00+00:00", **entry}},
            upsert=True
        )
    await db.member_checkins.delete_many({"tenant_id": tenant_id, "user_id": member_user["user_id"], "id": {"$nin": checkin_ids}})

    next_steps_course_ids = ["pathway_course_001", "pathway_course_002", "pathway_course_003"]
    await db.tenants.update_one({"id": tenant_id}, {"$set": {"next_steps_course_ids": next_steps_course_ids, "updated_at": now_iso}})

    for course_id in next_steps_course_ids:
        await db.pathways_enrollments.update_one(
            {"tenant_id": tenant_id, "user_id": member_user["user_id"], "course_id": course_id},
            {"$set": {"id": f"path_enroll_{member_user['user_id']}_{course_id}", "tenant_id": tenant_id, "user_id": member_user["user_id"], "course_id": course_id, "assigned_by": "admin_abundant", "assigned_at": now_iso, "status": "completed", "updated_at": now_iso}, "$setOnInsert": {"created_at": now_iso}},
            upsert=True
        )


async def ensure_abundant_go_live_portal_content(now_iso: Optional[str] = None):
    """Seed go-live API data expected by web + mobile clients for Abundant demo account."""
    tenant_id = DEFAULT_TENANT_ID
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()

    member_user = await db.users.find_one({"email": "member@abundant.church"}, {"_id": 0, "user_id": 1, "name": 1, "tenant_id": 1})
    if not member_user:
        return

    events_count = await db.events.count_documents({"tenant_id": tenant_id})
    if events_count < 50:
        today = datetime.now(timezone.utc).date()
        for idx in range(1, 51):
            event_date = (today + timedelta(days=idx)).isoformat()
            event_doc = {"id": f"event_abundant_{idx:03d}", "tenant_id": tenant_id, "name": f"Abundant Event {idx}", "description": "Church gathering and discipleship opportunity.", "location": "Abundant Main Campus", "event_date": event_date, "start_datetime": f"{event_date}T18:00:00", "is_public": True, "capacity": 350, "registration_required": idx % 2 == 0, "registration_count": min(idx * 2, 120), "created_at": now_iso}
            await db.events.update_one({"id": event_doc["id"], "tenant_id": tenant_id}, {"$set": event_doc}, upsert=True)

    active_groups_count = await db.groups.count_documents({"tenant_id": tenant_id, "is_active": True})
    if active_groups_count < 100:
        for idx in range(1, 101):
            group_doc = {"id": f"group_abundant_{idx:03d}", "tenant_id": tenant_id, "name": f"Life Group {idx}", "description": "Weekly small group for growth and community.", "category": "Small Groups", "meeting_day": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"][idx % 5], "meeting_time": "7:00 PM", "location": "Campus + Homes", "is_active": True, "max_members": 25, "created_at": now_iso}
            await db.groups.update_one({"id": group_doc["id"], "tenant_id": tenant_id}, {"$set": group_doc}, upsert=True)

    today = datetime.now(timezone.utc).date()
    recent_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    recent_checkin = {"id": "chk_mobile_recent", "tenant_id": tenant_id, "user_id": member_user["user_id"], "service_id": None, "check_in_type": "in_person", "service_date": recent_sunday.isoformat(), "check_in_time": f"{recent_sunday.isoformat()}T09:00:00+00:00"}
    await db.member_checkins.update_one({"id": recent_checkin["id"], "tenant_id": tenant_id}, {"$set": recent_checkin}, upsert=True)

    next_steps_doc = {"id": f"next_steps_{member_user['user_id']}", "tenant_id": tenant_id, "user_id": member_user["user_id"], "current_step": "Baptism", "steps": [{"id": 1, "title": "Salvation", "completed": True}, {"id": 2, "title": "Baptism", "completed": True}, {"id": 3, "title": "Membership Class", "completed": True}, {"id": 4, "title": "Small Group", "completed": False}, {"id": 5, "title": "Serve", "completed": False}], "percentage_complete": 60, "status": "in_progress", "thinkific_url": "https://abundant.thinkific.com/courses", "updated_at": now_iso}
    await db.next_steps_journeys.update_one({"tenant_id": tenant_id, "user_id": member_user["user_id"]}, {"$set": next_steps_doc}, upsert=True)

    course_docs = [
        {"id": "course_mobile_001", "tenant_id": tenant_id, "user_id": member_user["user_id"], "title": "Abundant Foundations", "description": "Core beliefs and foundations of faith", "progress": 100, "completed": True, "thinkific_url": "https://abundant.thinkific.com/courses/foundations", "thumbnail": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?auto=format&fit=crop&w=900&q=80", "updated_at": now_iso},
        {"id": "course_mobile_002", "tenant_id": tenant_id, "user_id": member_user["user_id"], "title": "Discovering Your Purpose", "description": "Find your calling and ministry gifting", "progress": 45, "completed": False, "thinkific_url": "https://abundant.thinkific.com/courses/discovering-your-purpose", "thumbnail": "https://images.unsplash.com/photo-1516534775068-ba3e7458af70?auto=format&fit=crop&w=900&q=80", "updated_at": now_iso},
    ]
    for course in course_docs:
        await db.member_courses.update_one({"id": course["id"], "tenant_id": tenant_id, "user_id": member_user["user_id"]}, {"$set": course, "$setOnInsert": {"created_at": now_iso}}, upsert=True)
    await db.member_courses.delete_many({"tenant_id": tenant_id, "user_id": member_user["user_id"], "id": {"$nin": ["course_mobile_001", "course_mobile_002"]}})

    prayer_seed = [
        {"id": "prayer_mobile_001", "tenant_id": tenant_id, "user_id": member_user["user_id"], "user_name": member_user.get("name", "Maria Garcia"), "category": "healing", "title": "Healing for my mother", "content": "Please pray for full healing and strength for my mother this month.", "is_public": False, "is_anonymous": False, "prayer_count": 0, "status": "active", "created_at": datetime.now(timezone.utc) - timedelta(days=6)},
        {"id": "prayer_mobile_002", "tenant_id": tenant_id, "user_id": member_user["user_id"], "user_name": member_user.get("name", "Maria Garcia"), "category": "guidance", "title": "New job opportunity", "content": "Praying for wisdom, favor, and peace in this interview process.", "is_public": True, "is_anonymous": False, "prayer_count": 3, "status": "active", "created_at": datetime.now(timezone.utc) - timedelta(days=2)},
    ]
    prayer_ids = [item["id"] for item in prayer_seed]
    for item in prayer_seed:
        await db.prayer_requests.update_one({"id": item["id"], "tenant_id": tenant_id}, {"$set": item, "$setOnInsert": {"updated_at": now_iso}}, upsert=True)
    await db.prayer_requests.delete_many({"tenant_id": tenant_id, "user_id": member_user["user_id"], "id": {"$nin": prayer_ids}})

    opportunities = [
        {"id": "vol_001", "title": "Worship Team", "description": "Serve through music and worship.", "schedule": "Sundays 8:00 AM", "location": "Main Sanctuary", "spots_available": 4, "ministry_area": "Worship"},
        {"id": "vol_002", "title": "Hospitality", "description": "Welcome guests and help with connections.", "schedule": "Sundays 8:30 AM", "location": "Main Lobby", "spots_available": 6, "ministry_area": "Guest Experience"},
        {"id": "vol_003", "title": "Kids Ministry", "description": "Support Sunday classes and safe check-in.", "schedule": "Sundays 10:30 AM", "location": "Kids Wing", "spots_available": 5, "ministry_area": "Kids"},
        {"id": "vol_004", "title": "Parking Team", "description": "Guide traffic and assist families arriving on campus.", "schedule": "Sundays 8:15 AM", "location": "Parking Lot", "spots_available": 8, "ministry_area": "Operations"},
        {"id": "vol_005", "title": "Tech Team", "description": "Help with audio, video, and live stream.", "schedule": "Sundays 8:00 AM", "location": "Production Booth", "spots_available": 3, "ministry_area": "Production"},
        {"id": "vol_006", "title": "Food Pantry", "description": "Serve local families through weekend pantry outreach.", "schedule": "Saturday 9:00 AM", "location": "Community Center", "spots_available": 10, "ministry_area": "Outreach"},
    ]
    for op in opportunities:
        await db.volunteer_opportunities.update_one(
            {"id": op["id"], "tenant_id": tenant_id},
            {"$set": {**op, "tenant_id": tenant_id, "is_active": True, "updated_at": now_iso}, "$setOnInsert": {"created_at": now_iso}},
            upsert=True
        )

    announcements = [
        {"id": "ann_001", "title": "Easter Sunday — April 20th — All 3 services!", "body": "Celebrate Easter with us at 8:30AM, 10:30AM, and 12:30PM.", "priority": "high", "expires_at": "2026-04-21T00:00:00+00:00"},
        {"id": "ann_002", "title": "Marriage Retreat registration now open", "body": "Reserve your spot for the spring marriage retreat.", "priority": "medium", "expires_at": "2026-05-30T00:00:00+00:00"},
        {"id": "ann_003", "title": "Food Pantry needs volunteers this Saturday", "body": "Join the outreach team and help serve local families.", "priority": "high", "expires_at": "2026-03-31T00:00:00+00:00"},
    ]
    for ann in announcements:
        await db.announcements.update_one(
            {"id": ann["id"], "tenant_id": tenant_id},
            {"$set": {**ann, "tenant_id": tenant_id, "created_at": now_iso, "updated_at": now_iso}},
            upsert=True
        )
