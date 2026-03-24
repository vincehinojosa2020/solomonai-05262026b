"""Solomon Academy — Course / LMS routes."""

from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timezone
import uuid

router = APIRouter()

# ---- helpers (imported at bottom to avoid circular) ----
_db = None
_require_permission = None
_get_current_member_user = None
_DEFAULT_TENANT_ID = None


def _init(db, require_permission, get_current_member_user, default_tenant_id):
    global _db, _require_permission, _get_current_member_user, _DEFAULT_TENANT_ID
    _db = db
    _require_permission = require_permission
    _get_current_member_user = get_current_member_user
    _DEFAULT_TENANT_ID = default_tenant_id


def _now():
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════
#  ADMIN  —  COURSES
# ═══════════════════════════════════════════════════════

@router.get("/admin/courses")
async def list_courses(request: Request):
    user = await _require_permission(request, "admin.courses.view")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    courses = await _db.courses.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(500)
    # attach counts
    for c in courses:
        c["enrolled_count"] = await _db.course_enrollments.count_documents({"course_id": c["id"], "tenant_id": tenant_id})
        total_lessons = await _db.course_lessons.count_documents({"course_id": c["id"], "tenant_id": tenant_id})
        c["lesson_count"] = total_lessons
        if c["enrolled_count"] > 0 and total_lessons > 0:
            pipeline = [
                {"$match": {"course_id": c["id"], "tenant_id": tenant_id, "completed_at": {"$ne": None}}},
                {"$group": {"_id": "$user_id"}},
                {"$count": "completed"}
            ]
            agg = await _db.course_enrollments.aggregate(pipeline).to_list(1)
            completed = agg[0]["completed"] if agg else 0
            c["completion_rate"] = round(completed / c["enrolled_count"] * 100)
        else:
            c["completion_rate"] = 0
    return {"courses": courses}


@router.post("/admin/courses")
async def create_course(request: Request):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    data = await request.json()
    course = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "title": data.get("title", "Untitled Course"),
        "description": data.get("description", ""),
        "thumbnail_url": data.get("thumbnail_url", ""),
        "instructor_name": data.get("instructor_name", ""),
        "category": data.get("category", "general"),
        "status": data.get("status", "draft"),
        "enrollment_type": data.get("enrollment_type", "open"),
        "certificate_enabled": False,
        "created_at": _now(),
        "updated_at": _now(),
    }
    await _db.courses.insert_one({**course})
    return course


@router.get("/admin/courses/{course_id}")
async def get_course_admin(request: Request, course_id: str):
    user = await _require_permission(request, "admin.courses.view")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    course = await _db.courses.find_one({"id": course_id, "tenant_id": tenant_id}, {"_id": 0})
    if not course:
        raise HTTPException(404, "Course not found")
    modules = await _db.course_modules.find({"course_id": course_id, "tenant_id": tenant_id}, {"_id": 0}).sort("order", 1).to_list(100)
    lessons = await _db.course_lessons.find({"course_id": course_id, "tenant_id": tenant_id}, {"_id": 0}).sort("order", 1).to_list(500)
    # group lessons under modules
    for m in modules:
        m["lessons"] = [l for l in lessons if l["module_id"] == m["id"]]
    course["modules"] = modules
    course["enrolled_count"] = await _db.course_enrollments.count_documents({"course_id": course_id, "tenant_id": tenant_id})
    course["lesson_count"] = len(lessons)
    return course


@router.put("/admin/courses/{course_id}")
async def update_course(request: Request, course_id: str):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    data = await request.json()
    allowed = ["title", "description", "thumbnail_url", "instructor_name", "category", "status", "enrollment_type"]
    updates = {k: v for k, v in data.items() if k in allowed}
    updates["updated_at"] = _now()
    result = await _db.courses.update_one({"id": course_id, "tenant_id": tenant_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(404, "Course not found")
    return {"success": True, **updates}


@router.delete("/admin/courses/{course_id}")
async def delete_course(request: Request, course_id: str):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    await _db.courses.delete_one({"id": course_id, "tenant_id": tenant_id})
    await _db.course_modules.delete_many({"course_id": course_id, "tenant_id": tenant_id})
    await _db.course_lessons.delete_many({"course_id": course_id, "tenant_id": tenant_id})
    await _db.course_enrollments.delete_many({"course_id": course_id, "tenant_id": tenant_id})
    await _db.course_lesson_progress.delete_many({"course_id": course_id, "tenant_id": tenant_id})
    return {"success": True}


# ═══════════════════════════════════════════════════════
#  ADMIN  —  MODULES
# ═══════════════════════════════════════════════════════

@router.post("/admin/courses/{course_id}/modules")
async def create_module(request: Request, course_id: str):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    data = await request.json()
    max_order = await _db.course_modules.find_one({"course_id": course_id, "tenant_id": tenant_id}, {"_id": 0}, sort=[("order", -1)])
    next_order = (max_order["order"] + 1) if max_order else 1
    module = {
        "id": str(uuid.uuid4()),
        "course_id": course_id,
        "tenant_id": tenant_id,
        "title": data.get("title", "New Module"),
        "order": next_order,
        "created_at": _now(),
    }
    await _db.course_modules.insert_one({**module})
    return module


@router.put("/admin/courses/{course_id}/modules/{module_id}")
async def update_module(request: Request, course_id: str, module_id: str):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    data = await request.json()
    updates = {}
    if "title" in data:
        updates["title"] = data["title"]
    if updates:
        await _db.course_modules.update_one({"id": module_id, "course_id": course_id, "tenant_id": tenant_id}, {"$set": updates})
    return {"success": True}


@router.delete("/admin/courses/{course_id}/modules/{module_id}")
async def delete_module(request: Request, course_id: str, module_id: str):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    await _db.course_modules.delete_one({"id": module_id, "course_id": course_id, "tenant_id": tenant_id})
    await _db.course_lessons.delete_many({"module_id": module_id, "course_id": course_id, "tenant_id": tenant_id})
    return {"success": True}


@router.post("/admin/courses/{course_id}/modules/{module_id}/move")
async def move_module(request: Request, course_id: str, module_id: str):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    data = await request.json()
    direction = data.get("direction", "down")
    modules = await _db.course_modules.find({"course_id": course_id, "tenant_id": tenant_id}, {"_id": 0}).sort("order", 1).to_list(100)
    idx = next((i for i, m in enumerate(modules) if m["id"] == module_id), None)
    if idx is None:
        raise HTTPException(404, "Module not found")
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if swap_idx < 0 or swap_idx >= len(modules):
        return {"success": True, "message": "Already at boundary"}
    # swap orders
    await _db.course_modules.update_one({"id": modules[idx]["id"], "tenant_id": tenant_id}, {"$set": {"order": modules[swap_idx]["order"]}})
    await _db.course_modules.update_one({"id": modules[swap_idx]["id"], "tenant_id": tenant_id}, {"$set": {"order": modules[idx]["order"]}})
    return {"success": True}


# ═══════════════════════════════════════════════════════
#  ADMIN  —  LESSONS
# ═══════════════════════════════════════════════════════

@router.post("/admin/courses/{course_id}/modules/{module_id}/lessons")
async def create_lesson(request: Request, course_id: str, module_id: str):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    data = await request.json()
    max_order = await _db.course_lessons.find_one({"module_id": module_id, "course_id": course_id, "tenant_id": tenant_id}, {"_id": 0}, sort=[("order", -1)])
    next_order = (max_order["order"] + 1) if max_order else 1
    lesson = {
        "id": str(uuid.uuid4()),
        "module_id": module_id,
        "course_id": course_id,
        "tenant_id": tenant_id,
        "title": data.get("title", "New Lesson"),
        "type": data.get("type", "text"),
        "content": data.get("content", {}),
        "duration_minutes": data.get("duration_minutes", 5),
        "is_required": data.get("is_required", True),
        "order": next_order,
        "created_at": _now(),
    }
    await _db.course_lessons.insert_one({**lesson})
    return lesson


@router.put("/admin/courses/{course_id}/lessons/{lesson_id}")
async def update_lesson(request: Request, course_id: str, lesson_id: str):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    data = await request.json()
    allowed = ["title", "type", "content", "duration_minutes", "is_required"]
    updates = {k: v for k, v in data.items() if k in allowed}
    if updates:
        await _db.course_lessons.update_one({"id": lesson_id, "course_id": course_id, "tenant_id": tenant_id}, {"$set": updates})
    return {"success": True}


@router.delete("/admin/courses/{course_id}/lessons/{lesson_id}")
async def delete_lesson(request: Request, course_id: str, lesson_id: str):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    await _db.course_lessons.delete_one({"id": lesson_id, "course_id": course_id, "tenant_id": tenant_id})
    return {"success": True}


@router.post("/admin/courses/{course_id}/lessons/{lesson_id}/move")
async def move_lesson(request: Request, course_id: str, lesson_id: str):
    user = await _require_permission(request, "admin.courses.edit")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    data = await request.json()
    direction = data.get("direction", "down")
    lesson = await _db.course_lessons.find_one({"id": lesson_id, "course_id": course_id, "tenant_id": tenant_id}, {"_id": 0})
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    siblings = await _db.course_lessons.find({"module_id": lesson["module_id"], "course_id": course_id, "tenant_id": tenant_id}, {"_id": 0}).sort("order", 1).to_list(100)
    idx = next((i for i, s in enumerate(siblings) if s["id"] == lesson_id), None)
    if idx is None:
        raise HTTPException(404, "Lesson not in list")
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if swap_idx < 0 or swap_idx >= len(siblings):
        return {"success": True, "message": "Already at boundary"}
    await _db.course_lessons.update_one({"id": siblings[idx]["id"], "tenant_id": tenant_id}, {"$set": {"order": siblings[swap_idx]["order"]}})
    await _db.course_lessons.update_one({"id": siblings[swap_idx]["id"], "tenant_id": tenant_id}, {"$set": {"order": siblings[idx]["order"]}})
    return {"success": True}


# ═══════════════════════════════════════════════════════
#  ADMIN  —  ENROLLMENTS
# ═══════════════════════════════════════════════════════

@router.get("/admin/courses/{course_id}/enrollments")
async def get_enrollments(request: Request, course_id: str):
    user = await _require_permission(request, "admin.courses.view")
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    enrollments = await _db.course_enrollments.find({"course_id": course_id, "tenant_id": tenant_id}, {"_id": 0}).to_list(500)
    total_lessons = await _db.course_lessons.count_documents({"course_id": course_id, "tenant_id": tenant_id, "is_required": True})
    for e in enrollments:
        # get user info
        u = await _db.users.find_one({"user_id": e["user_id"]}, {"_id": 0, "name": 1, "email": 1, "picture": 1})
        e["user"] = u or {"name": "Unknown", "email": ""}
        completed_count = await _db.course_lesson_progress.count_documents({"user_id": e["user_id"], "course_id": course_id, "tenant_id": tenant_id, "status": "completed"})
        e["progress"] = round(completed_count / total_lessons * 100) if total_lessons > 0 else 0
        e["completed_lessons"] = completed_count
        e["total_lessons"] = total_lessons
    return {"enrollments": enrollments, "total": len(enrollments)}


# ═══════════════════════════════════════════════════════
#  PORTAL  —  COURSES (Member-facing)
# ═══════════════════════════════════════════════════════

@router.get("/portal/courses")
async def portal_list_courses(request: Request):
    user = await _get_current_member_user(request)
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    courses = await _db.courses.find({"tenant_id": tenant_id, "status": "published"}, {"_id": 0}).sort("created_at", -1).to_list(200)
    my_enrollments = await _db.course_enrollments.find({"user_id": user["user_id"], "tenant_id": tenant_id}, {"_id": 0}).to_list(200)
    enrollment_map = {e["course_id"]: e for e in my_enrollments}
    for c in courses:
        total_lessons = await _db.course_lessons.count_documents({"course_id": c["id"], "tenant_id": tenant_id, "is_required": True})
        c["lesson_count"] = total_lessons
        enrollment = enrollment_map.get(c["id"])
        if enrollment:
            c["enrolled"] = True
            c["enrolled_at"] = enrollment.get("enrolled_at")
            c["completed_at"] = enrollment.get("completed_at")
            completed_count = await _db.course_lesson_progress.count_documents({"user_id": user["user_id"], "course_id": c["id"], "tenant_id": tenant_id, "status": "completed"})
            c["progress"] = round(completed_count / total_lessons * 100) if total_lessons > 0 else 0
        else:
            c["enrolled"] = False
            c["progress"] = 0
        # estimate total duration
        lessons = await _db.course_lessons.find({"course_id": c["id"], "tenant_id": tenant_id}, {"_id": 0, "duration_minutes": 1}).to_list(500)
        c["total_duration_minutes"] = sum(l.get("duration_minutes", 0) for l in lessons)
    return {"courses": courses}


@router.get("/portal/courses/my")
async def portal_my_courses(request: Request):
    user = await _get_current_member_user(request)
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    enrollments = await _db.course_enrollments.find({"user_id": user["user_id"], "tenant_id": tenant_id}, {"_id": 0}).to_list(200)
    courses = []
    for e in enrollments:
        course = await _db.courses.find_one({"id": e["course_id"], "tenant_id": tenant_id}, {"_id": 0})
        if course:
            total_lessons = await _db.course_lessons.count_documents({"course_id": course["id"], "tenant_id": tenant_id, "is_required": True})
            completed_count = await _db.course_lesson_progress.count_documents({"user_id": user["user_id"], "course_id": course["id"], "tenant_id": tenant_id, "status": "completed"})
            course["lesson_count"] = total_lessons
            course["progress"] = round(completed_count / total_lessons * 100) if total_lessons > 0 else 0
            course["enrolled"] = True
            course["enrolled_at"] = e.get("enrolled_at")
            course["completed_at"] = e.get("completed_at")
            lessons_all = await _db.course_lessons.find({"course_id": course["id"], "tenant_id": tenant_id}, {"_id": 0, "duration_minutes": 1}).to_list(500)
            course["total_duration_minutes"] = sum(l.get("duration_minutes", 0) for l in lessons_all)
            courses.append(course)
    return {"courses": courses}


@router.get("/portal/courses/{course_id}")
async def portal_course_detail(request: Request, course_id: str):
    user = await _get_current_member_user(request)
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    course = await _db.courses.find_one({"id": course_id, "tenant_id": tenant_id, "status": "published"}, {"_id": 0})
    if not course:
        raise HTTPException(404, "Course not found")
    modules = await _db.course_modules.find({"course_id": course_id, "tenant_id": tenant_id}, {"_id": 0}).sort("order", 1).to_list(100)
    lessons = await _db.course_lessons.find({"course_id": course_id, "tenant_id": tenant_id}, {"_id": 0}).sort("order", 1).to_list(500)
    # check enrollment
    enrollment = await _db.course_enrollments.find_one({"user_id": user["user_id"], "course_id": course_id, "tenant_id": tenant_id}, {"_id": 0})
    # get progress
    progress_docs = await _db.course_lesson_progress.find({"user_id": user["user_id"], "course_id": course_id, "tenant_id": tenant_id}, {"_id": 0}).to_list(500)
    progress_map = {p["lesson_id"]: p for p in progress_docs}
    for l in lessons:
        prog = progress_map.get(l["id"])
        l["completed"] = prog["status"] == "completed" if prog else False
        if l["type"] == "quiz" and prog:
            l["quiz_score"] = prog.get("quiz_score")
            l["quiz_passed"] = prog.get("quiz_passed")
    for m in modules:
        m["lessons"] = [l for l in lessons if l["module_id"] == m["id"]]
    total_lessons = sum(1 for l in lessons if l.get("is_required", True))
    completed_count = sum(1 for l in lessons if l.get("completed") and l.get("is_required", True))
    course["modules"] = modules
    course["enrolled"] = enrollment is not None
    course["enrolled_at"] = enrollment.get("enrolled_at") if enrollment else None
    course["completed_at"] = enrollment.get("completed_at") if enrollment else None
    course["progress"] = round(completed_count / total_lessons * 100) if total_lessons > 0 else 0
    course["lesson_count"] = total_lessons
    course["completed_lessons"] = completed_count
    course["total_duration_minutes"] = sum(l.get("duration_minutes", 0) for l in lessons)
    return course


@router.post("/portal/courses/{course_id}/enroll")
async def portal_enroll(request: Request, course_id: str):
    user = await _get_current_member_user(request)
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    # check course exists and is published
    course = await _db.courses.find_one({"id": course_id, "tenant_id": tenant_id, "status": "published"}, {"_id": 0})
    if not course:
        raise HTTPException(404, "Course not found")
    # check not already enrolled
    existing = await _db.course_enrollments.find_one({"user_id": user["user_id"], "course_id": course_id, "tenant_id": tenant_id})
    if existing:
        return {"success": True, "message": "Already enrolled"}
    enrollment = {
        "id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        "course_id": course_id,
        "tenant_id": tenant_id,
        "enrolled_at": _now(),
        "completed_at": None,
        "certificate_issued": False,
    }
    await _db.course_enrollments.insert_one({**enrollment})
    return {"success": True, "enrollment": {k: v for k, v in enrollment.items() if k != "_id"}}


@router.get("/portal/courses/{course_id}/lessons/{lesson_id}")
async def portal_get_lesson(request: Request, course_id: str, lesson_id: str):
    user = await _get_current_member_user(request)
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    # check enrollment
    enrollment = await _db.course_enrollments.find_one({"user_id": user["user_id"], "course_id": course_id, "tenant_id": tenant_id})
    if not enrollment:
        raise HTTPException(403, "You must enroll in this course first")
    lesson = await _db.course_lessons.find_one({"id": lesson_id, "course_id": course_id, "tenant_id": tenant_id}, {"_id": 0})
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    # get progress
    prog = await _db.course_lesson_progress.find_one({"user_id": user["user_id"], "lesson_id": lesson_id, "tenant_id": tenant_id}, {"_id": 0})
    lesson["completed"] = prog["status"] == "completed" if prog else False
    if lesson["type"] == "quiz" and prog:
        lesson["quiz_score"] = prog.get("quiz_score")
        lesson["quiz_passed"] = prog.get("quiz_passed")
    # get prev/next lesson info
    all_lessons = await _db.course_lessons.find({"course_id": course_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1, "module_id": 1, "order": 1}).to_list(500)
    # sort by module order then lesson order
    all_modules = await _db.course_modules.find({"course_id": course_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1, "order": 1}).sort("order", 1).to_list(100)
    mod_order = {m["id"]: m["order"] for m in all_modules}
    sorted_lessons = sorted(all_lessons, key=lambda x: (mod_order.get(x["module_id"], 0), x.get("order", 0)))
    lesson_ids = [l["id"] for l in sorted_lessons]
    current_idx = lesson_ids.index(lesson_id) if lesson_id in lesson_ids else -1
    lesson["prev_lesson_id"] = lesson_ids[current_idx - 1] if current_idx > 0 else None
    lesson["next_lesson_id"] = lesson_ids[current_idx + 1] if current_idx < len(lesson_ids) - 1 else None
    return lesson


@router.post("/portal/courses/{course_id}/lessons/{lesson_id}/complete")
async def portal_complete_lesson(request: Request, course_id: str, lesson_id: str):
    user = await _get_current_member_user(request)
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    enrollment = await _db.course_enrollments.find_one({"user_id": user["user_id"], "course_id": course_id, "tenant_id": tenant_id})
    if not enrollment:
        raise HTTPException(403, "Not enrolled")
    await _db.course_lesson_progress.update_one(
        {"user_id": user["user_id"], "lesson_id": lesson_id, "course_id": course_id, "tenant_id": tenant_id},
        {"$set": {"id": str(uuid.uuid4()), "user_id": user["user_id"], "lesson_id": lesson_id, "course_id": course_id, "tenant_id": tenant_id, "status": "completed", "completed_at": _now()}},
        upsert=True
    )
    # check if all required lessons complete → mark course complete
    total_required = await _db.course_lessons.count_documents({"course_id": course_id, "tenant_id": tenant_id, "is_required": True})
    completed_count = await _db.course_lesson_progress.count_documents({"user_id": user["user_id"], "course_id": course_id, "tenant_id": tenant_id, "status": "completed"})
    course_completed = completed_count >= total_required and total_required > 0
    if course_completed:
        await _db.course_enrollments.update_one(
            {"user_id": user["user_id"], "course_id": course_id, "tenant_id": tenant_id},
            {"$set": {"completed_at": _now()}}
        )
    return {"success": True, "course_completed": course_completed, "progress": round(completed_count / total_required * 100) if total_required > 0 else 100}


@router.post("/portal/courses/{course_id}/lessons/{lesson_id}/quiz")
async def portal_submit_quiz(request: Request, course_id: str, lesson_id: str):
    user = await _get_current_member_user(request)
    tenant_id = user.get("tenant_id", _DEFAULT_TENANT_ID)
    enrollment = await _db.course_enrollments.find_one({"user_id": user["user_id"], "course_id": course_id, "tenant_id": tenant_id})
    if not enrollment:
        raise HTTPException(403, "Not enrolled")
    lesson = await _db.course_lessons.find_one({"id": lesson_id, "course_id": course_id, "tenant_id": tenant_id}, {"_id": 0})
    if not lesson or lesson["type"] != "quiz":
        raise HTTPException(400, "Not a quiz lesson")
    data = await request.json()
    answers = data.get("answers", [])
    questions = lesson.get("content", {}).get("questions", [])
    passing_score = lesson.get("content", {}).get("passing_score", 70)
    correct = 0
    for i, q in enumerate(questions):
        if i < len(answers) and answers[i] == q.get("correct"):
            correct += 1
    total = len(questions)
    score = round(correct / total * 100) if total > 0 else 0
    passed = score >= passing_score
    # save progress
    await _db.course_lesson_progress.update_one(
        {"user_id": user["user_id"], "lesson_id": lesson_id, "course_id": course_id, "tenant_id": tenant_id},
        {"$set": {
            "id": str(uuid.uuid4()), "user_id": user["user_id"], "lesson_id": lesson_id,
            "course_id": course_id, "tenant_id": tenant_id,
            "status": "completed" if passed else "in_progress",
            "completed_at": _now() if passed else None,
            "quiz_score": score, "quiz_passed": passed,
        }},
        upsert=True
    )
    # check course completion
    if passed:
        total_required = await _db.course_lessons.count_documents({"course_id": course_id, "tenant_id": tenant_id, "is_required": True})
        completed_count = await _db.course_lesson_progress.count_documents({"user_id": user["user_id"], "course_id": course_id, "tenant_id": tenant_id, "status": "completed"})
        if completed_count >= total_required and total_required > 0:
            await _db.course_enrollments.update_one(
                {"user_id": user["user_id"], "course_id": course_id, "tenant_id": tenant_id},
                {"$set": {"completed_at": _now()}}
            )
    return {"score": score, "correct": correct, "total": total, "passed": passed, "passing_score": passing_score}


# ═══════════════════════════════════════════════════════
#  SEED — Abundant Next Steps
# ═══════════════════════════════════════════════════════

async def seed_academy_course():
    """Seed the Abundant Next Steps demo course if it doesn't exist."""
    existing = await _db.courses.find_one({"id": "abundant-next-steps"})
    if existing:
        return
    tenant_id = "abundant-east-001"
    now = _now()
    course = {
        "id": "abundant-next-steps",
        "tenant_id": tenant_id,
        "title": "Abundant Next Steps",
        "description": "At Abundant Church, our heart and vision is to teach you how to enjoy the abundant life that Jesus came for you to have. The Abundant Life is one that is always moving forward and taking Next Steps.\n\nAbundant Next Steps will help you learn about our vision & values, and connect with our church family.",
        "thumbnail_url": "",
        "instructor_name": "Pastor Charles Nieman",
        "category": "new_members",
        "status": "published",
        "enrollment_type": "open",
        "certificate_enabled": False,
        "created_at": now,
        "updated_at": now,
    }
    modules = [
        {"id": "mod-1", "course_id": "abundant-next-steps", "tenant_id": tenant_id, "title": "Introduction", "order": 1, "created_at": now},
        {"id": "mod-2", "course_id": "abundant-next-steps", "tenant_id": tenant_id, "title": "Chapter 1: Welcome", "order": 2, "created_at": now},
        {"id": "mod-3", "course_id": "abundant-next-steps", "tenant_id": tenant_id, "title": "Chapter 2: Vision & Values", "order": 3, "created_at": now},
        {"id": "mod-4", "course_id": "abundant-next-steps", "tenant_id": tenant_id, "title": "Chapter 3: Belonging", "order": 4, "created_at": now},
        {"id": "mod-5", "course_id": "abundant-next-steps", "tenant_id": tenant_id, "title": "Chapter 4: What's Next?", "order": 5, "created_at": now},
    ]
    lessons = [
        {
            "id": "les-1", "module_id": "mod-1", "course_id": "abundant-next-steps", "tenant_id": tenant_id,
            "title": "Introduction: A Word from Pastor Charles Nieman", "type": "video",
            "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            "duration_minutes": 5, "is_required": True, "order": 1, "created_at": now,
        },
        {
            "id": "les-2", "module_id": "mod-2", "course_id": "abundant-next-steps", "tenant_id": tenant_id,
            "title": "Welcome to Abundant Next Steps", "type": "text",
            "content": {"body": "# Welcome!\n\nWe're so excited to have you here at Abundant Church!\n\nOur heart and vision is to teach you how to enjoy the **abundant life** that Jesus came for you to have.\n\n## What You'll Learn\n\n- What we believe as a church\n- Our vision and values\n- Why belonging to a church matters\n- Your next steps to get connected\n\nLet's get started!"},
            "duration_minutes": 3, "is_required": True, "order": 1, "created_at": now,
        },
        {
            "id": "les-3", "module_id": "mod-2", "course_id": "abundant-next-steps", "tenant_id": tenant_id,
            "title": "What We Believe at Abundant", "type": "text",
            "content": {"body": "# Our Core Beliefs\n\nAt Abundant Church, we believe:\n\n## The Bible\nThe Bible is God's Word, inspired and without error, and is our guide for faith and life.\n\n## Salvation\nSalvation is a gift from God through faith in Jesus Christ \u2014 not by our own works.\n\n## The Church\nThe church is the body of Christ, called to love God and love people.\n\n## The Holy Spirit\nThe Holy Spirit empowers us to live out our faith and serve others."},
            "duration_minutes": 5, "is_required": True, "order": 2, "created_at": now,
        },
        {
            "id": "les-4", "module_id": "mod-3", "course_id": "abundant-next-steps", "tenant_id": tenant_id,
            "title": "Our Vision and Our Values", "type": "video",
            "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            "duration_minutes": 8, "is_required": True, "order": 1, "created_at": now,
        },
        {
            "id": "les-5", "module_id": "mod-4", "course_id": "abundant-next-steps", "tenant_id": tenant_id,
            "title": "Why Does Belonging to a Church Matter?", "type": "text",
            "content": {"body": "# The Importance of Community\n\nGod designed us to live in relationship with others.\n\n> *\"And let us consider how we may spur one another on toward love and good deeds, not giving up meeting together...\"* \u2014 Hebrews 10:24-25\n\n## Benefits of Church Community\n\n1. **Spiritual Growth** \u2014 We grow faster together than alone\n2. **Support System** \u2014 Life's challenges are easier with others\n3. **Accountability** \u2014 We help each other stay on track\n4. **Purpose** \u2014 We can make a bigger impact together\n5. **Belonging** \u2014 We all need a place to call home"},
            "duration_minutes": 5, "is_required": True, "order": 1, "created_at": now,
        },
        {
            "id": "les-6", "module_id": "mod-5", "course_id": "abundant-next-steps", "tenant_id": tenant_id,
            "title": "What's Next?", "type": "text",
            "content": {"body": "# Your Next Steps\n\nCongratulations on completing this course! Here's what to do next:\n\n## 1. Schedule a One-on-One\nMeet with a member of our team to get connected personally.\n\n## 2. Join a Small Group\nFind community with others in a group that fits your life stage.\n\n## 3. Find a Place to Serve\nDiscover your gifts and make a difference in our church family.\n\n## 4. Make Abundant Your Home\nComplete your membership and officially join our family!\n\n---\n\n*We can't wait to take next steps with you!*"},
            "duration_minutes": 3, "is_required": True, "order": 1, "created_at": now,
        },
        {
            "id": "les-7", "module_id": "mod-5", "course_id": "abundant-next-steps", "tenant_id": tenant_id,
            "title": "Quiz: Next Steps Review", "type": "quiz",
            "content": {
                "questions": [
                    {"question": "What is Abundant Church's heart and vision?", "options": ["Building the biggest church", "Teaching you to enjoy abundant life", "Growing numbers", "Building buildings"], "correct": 1},
                    {"question": "According to the course, why is belonging to a church important?", "options": ["It's required for salvation", "Community helps us grow and support each other", "To look good", "Tradition"], "correct": 1},
                    {"question": "What are the suggested next steps after this course?", "options": ["Wait and do nothing", "Schedule a one-on-one, join a group, find a place to serve", "Just attend Sundays", "Send a donation"], "correct": 1},
                ],
                "passing_score": 70,
            },
            "duration_minutes": 5, "is_required": True, "order": 2, "created_at": now,
        },
    ]
    await _db.courses.insert_one({**course})
    for m in modules:
        await _db.course_modules.insert_one({**m})
    for l in lessons:
        await _db.course_lessons.insert_one({**l})
    print("Seeded 'Abundant Next Steps' course with 5 modules and 7 lessons")
