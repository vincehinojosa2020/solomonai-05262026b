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


async def seed_academy_courses_v2():
    """Seed all 6 Solomon Academy demo courses."""
    tenant_id = "abundant-east-001"
    now = _now()

    COURSES = [
        {
            "id": "becoming-a-member",
            "title": "Becoming a Member",
            "description": "Discover what it means to be a member of Abundant Church. Learn about our beliefs, values, and what membership commitment looks like.",
            "instructor_name": "Pastor Charles Nieman",
            "category": "new_members",
            "thumbnail_url": "https://images.unsplash.com/photo-1529070538774-1db5681a4e3e?w=600",
            "lessons": [
                {"title": "Welcome to Abundant", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "Pastor Charles welcomes you and shares the heart behind Abundant Church."}, "duration_minutes": 8},
                {"title": "Our Beliefs and Values", "type": "text", "content": {"body": "# Our Beliefs and Values\n\n## What We Believe\n\nAt Abundant Church, we believe in:\n\n- **The Bible** — God's inspired, inerrant Word\n- **One God** — Father, Son, and Holy Spirit\n- **Salvation** — Through faith in Jesus Christ alone\n- **The Church** — The body of believers, called to love God and love people\n- **The Great Commission** — Go and make disciples of all nations\n\n## Our Core Values\n\n1. **Faith** — We trust God in all things\n2. **Family** — We are better together\n3. **Generosity** — We give because God first gave to us\n4. **Excellence** — We honor God by giving our best\n5. **Growth** — We are always taking next steps\n\n## Download Resources\n\nYou can download our full beliefs statement from the church office or ask your small group leader."}, "duration_minutes": 10},
                {"title": "What Membership Means", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "Understand the privileges and responsibilities of church membership."}, "duration_minutes": 12},
                {"title": "Next Steps After This Course", "type": "text", "content": {"body": "# Your Next Steps\n\nCongratulations on completing this course!\n\n## What's Next?\n\n1. **Schedule a meeting** with a pastor or staff member\n2. **Join a Small Group** to build authentic relationships\n3. **Find a place to serve** — discover your gifts\n4. **Set up recurring giving** — invest in God's kingdom\n\n## Membership Commitment\n\nMembership at Abundant is not just joining an organization — it's joining a family."}, "duration_minutes": 5},
                {"title": "Membership Commitment", "type": "quiz", "content": {"questions": [{"question": "What is the primary purpose of church membership?", "options": ["Status", "Joining a family and committing to growth", "Getting benefits", "Tradition"], "correct": 1}, {"question": "Which is NOT one of Abundant's core values?", "options": ["Faith", "Generosity", "Competition", "Growth"], "correct": 2}], "passing_score": 70, "description": "Complete this to confirm your membership commitment."}, "duration_minutes": 5},
            ],
        },
        {
            "id": "why-we-give",
            "title": "Why We Give",
            "description": "Explore the biblical foundation of generosity and understand how your giving makes an eternal impact at Abundant Church.",
            "instructor_name": "Shannon Nieman",
            "category": "stewardship",
            "thumbnail_url": "https://images.unsplash.com/photo-1532629345422-7515f3d16bb6?w=600",
            "lessons": [
                {"title": "The Heart of Generosity", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "Shannon Nieman shares her personal testimony of how generosity transformed their family."}, "duration_minutes": 10},
                {"title": "Biblical Foundation", "type": "text", "content": {"body": "# Biblical Foundation for Giving\n\n## Key Scriptures\n\n### Malachi 3:10\n> *\"Bring the whole tithe into the storehouse, that there may be food in my house. Test me in this,\" says the LORD Almighty, \"and see if I will not throw open the floodgates of heaven and pour out so much blessing that there will not be room enough to store it.\"*\n\n### 2 Corinthians 9:7\n> *\"Each of you should give what you have decided in your heart to give, not reluctantly or under compulsion, for God loves a cheerful giver.\"*\n\n### Proverbs 3:9-10\n> *\"Honor the LORD with your wealth, with the firstfruits of all your crops; then your barns will be filled to overflowing.\"*\n\n## Principles of Biblical Giving\n\n1. **Tithing** — The first 10% belongs to God\n2. **Offerings** — Above and beyond the tithe\n3. **Cheerful** — Give with a willing heart\n4. **Faithful** — Consistent, not sporadic\n5. **Trusting** — God honors our obedience"}, "duration_minutes": 8},
                {"title": "How Your Giving Makes an Impact", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "See the real-world impact of giving: missions, food pantry, kids programs, and community outreach."}, "duration_minutes": 12},
                {"title": "Setting Up Recurring Giving", "type": "text", "content": {"body": "# Setting Up Recurring Giving\n\nThe easiest way to honor God with your finances is to automate your generosity.\n\n## How to Set Up Recurring Giving\n\n1. Go to the **Give** page in your member portal\n2. Enter your desired **amount**\n3. Select your **fund** (General, Missions, Building, etc.)\n4. Choose your **frequency** (Weekly, Bi-weekly, Monthly)\n5. Enter your payment information\n6. Click **Start Recurring**\n\n## Why Automate?\n\n- **Consistency** — Never miss a giving opportunity\n- **Discipline** — Prioritize giving before spending\n- **Impact** — The church can plan and budget effectively\n- **Convenience** — Set it and forget it\n\nIf you need help, visit the church office or contact us at giving@abundant.church."}, "duration_minutes": 5},
            ],
        },
        {
            "id": "what-is-baptism",
            "title": "What is Baptism",
            "description": "Learn about the meaning, significance, and practice of water baptism. Prepare for your baptism day at Abundant Church.",
            "instructor_name": "Pastor Charles Nieman",
            "category": "spiritual_growth",
            "thumbnail_url": "https://images.unsplash.com/photo-1507692049790-de58290a4334?w=600",
            "lessons": [
                {"title": "The Meaning of Baptism", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "Pastor Charles explains the spiritual significance of water baptism."}, "duration_minutes": 10},
                {"title": "Baptism in Scripture", "type": "text", "content": {"body": "# Baptism in Scripture\n\n## What the Bible Says\n\n### Matthew 28:19\n> *\"Go and make disciples of all nations, baptizing them in the name of the Father and of the Son and of the Holy Spirit.\"*\n\n### Romans 6:3-4\n> *\"Don't you know that all of us who were baptized into Christ Jesus were baptized into his death? We were therefore buried with him through baptism into death in order that, just as Christ was raised from the dead through the glory of the Father, we too may live a new life.\"*\n\n### Acts 2:38\n> *\"Repent and be baptized, every one of you, in the name of Jesus Christ for the forgiveness of your sins. And you will receive the gift of the Holy Spirit.\"*\n\n## What Baptism Represents\n\n1. **Death** — to our old life of sin\n2. **Burial** — going under the water\n3. **Resurrection** — rising to new life in Christ"}, "duration_minutes": 8},
                {"title": "What to Expect on Baptism Day", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "A walkthrough of what happens on your baptism day — what to wear, bring, and expect."}, "duration_minutes": 6},
                {"title": "Schedule Your Baptism", "type": "text", "content": {"body": "# Schedule Your Baptism\n\nWe're so excited that you've decided to be baptized!\n\n## Next Steps\n\n1. **Contact our office** at baptism@abundant.church\n2. **Choose a date** — We do baptisms on the first Sunday of each month\n3. **Invite friends & family** — This is a celebration!\n4. **Prepare your testimony** — You'll have the option to share briefly\n\n## What to Bring\n\n- Change of clothes\n- Towel\n- A heart ready to celebrate!\n\nWe provide baptism robes and will have someone assist you in the water.\n\n*If you have questions, reach out to your small group leader or a pastor.*"}, "duration_minutes": 5},
            ],
        },
        {
            "id": "premarital-counseling",
            "title": "Premarital Counseling",
            "description": "A comprehensive 6-session course for engaged couples covering communication, finances, conflict resolution, and spiritual foundations.",
            "instructor_name": "Pastor Charles & Shannon Nieman",
            "category": "marriage",
            "thumbnail_url": "https://images.unsplash.com/photo-1519741497674-611481863552?w=600",
            "lessons": [
                {"title": "Introduction to the Journey", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "Pastor Charles and Shannon welcome couples and share their own marriage journey."}, "duration_minutes": 15},
                {"title": "Communication Foundations", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "Learn healthy communication patterns, active listening, and how to express needs.", "worksheet_note": "Download the Communication Worksheet from your group leader."}, "duration_minutes": 20},
                {"title": "Financial Unity", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "Discuss budgeting, tithing, debt management, and financial goals as a couple.", "worksheet_note": "Download the Financial Unity Worksheet."}, "duration_minutes": 18},
                {"title": "Conflict Resolution", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "Understand healthy conflict, forgiveness, and repair in marriage.", "worksheet_note": "Download the Conflict Resolution Worksheet."}, "duration_minutes": 20},
                {"title": "Spiritual Foundations", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "Build your marriage on the rock — prayer, devotions, and church involvement as a couple."}, "duration_minutes": 15},
                {"title": "Planning Your Ceremony", "type": "text", "content": {"body": "# Planning Your Ceremony\n\nCongratulations! Here's a checklist for your wedding planning:\n\n## Ceremony Checklist\n\n- [ ] Set a date with the church office\n- [ ] Choose your wedding party\n- [ ] Schedule a rehearsal\n- [ ] Select music and readings\n- [ ] Arrange premarital counseling completion certificate\n- [ ] Submit marriage license to church office\n\n## Resources\n\n- Wedding coordinator contact: weddings@abundant.church\n- Venue booking: Contact the church office\n- Photography: Ask for our recommended vendors list\n\n*We're honored to be part of your special day!*"}, "duration_minutes": 10},
            ],
        },
        {
            "id": "volunteer-food-pantry",
            "title": "Volunteer Training: Food Pantry",
            "description": "Everything you need to know to serve effectively in Abundant's Food Pantry ministry. Safety, procedures, and scheduling.",
            "instructor_name": "Community Outreach Team",
            "category": "volunteer",
            "thumbnail_url": "https://images.unsplash.com/photo-1593113646773-028c64a8f1b8?w=600",
            "lessons": [
                {"title": "Welcome to the Food Pantry Team", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "Meet the food pantry team and learn about our mission to serve the community."}, "duration_minutes": 8},
                {"title": "Safety and Procedures", "type": "text", "content": {"body": "# Safety and Procedures\n\n## Food Safety Guidelines\n\n1. **Wash hands** before handling any food\n2. **Wear gloves** when sorting and distributing\n3. **Check expiration dates** — discard expired items\n4. **Temperature control** — Keep cold items cold, hot items hot\n5. **Allergen awareness** — Label packages containing common allergens\n\n## Operating Procedures\n\n### Before Opening\n- Set up distribution tables\n- Sort incoming donations by category\n- Prepare family packs\n\n### During Distribution\n- Greet every person with warmth and dignity\n- Follow the distribution list for each family\n- Log all distributions in the tracking sheet\n\n### After Closing\n- Clean and sanitize all surfaces\n- Inventory remaining stock\n- Report any issues to the team lead\n\n## Emergency Procedures\n\n- First aid kit location: Kitchen counter\n- Emergency contacts posted by the door\n- Report any incidents immediately"}, "duration_minutes": 12},
                {"title": "Serving with Compassion", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "How to serve with dignity, compassion, and without judgment."}, "duration_minutes": 10},
                {"title": "Scheduling Your Shifts", "type": "text", "content": {"body": "# Scheduling Your Shifts\n\n## How to Sign Up\n\n1. Go to the **Volunteer** page in your member portal\n2. Select **Food Pantry** team\n3. Choose available shifts\n4. Confirm your commitment\n\n## Regular Schedule\n\n- **Tuesday**: 9 AM - 12 PM (Sorting & prep)\n- **Wednesday**: 10 AM - 2 PM (Distribution day)\n- **Saturday**: 9 AM - 1 PM (Community distribution)\n\n## Expectations\n\n- Commit to at least 2 shifts per month\n- Notify the team lead 24 hours in advance if you can't make it\n- Wear closed-toe shoes and comfortable clothes\n\nQuestions? Email foodpantry@abundant.church"}, "duration_minutes": 5},
            ],
        },
        {
            "id": "first-time-volunteers",
            "title": "First-Time Volunteers",
            "description": "New to volunteering at Abundant Church? Start here! Learn about our volunteer culture, find your fit, and take your first step.",
            "instructor_name": "Volunteer Team",
            "category": "volunteer",
            "thumbnail_url": "https://images.unsplash.com/photo-1559027615-cd4628902d4a?w=600",
            "lessons": [
                {"title": "Welcome to the Team", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "A warm welcome from our volunteer coordinators."}, "duration_minutes": 6},
                {"title": "Our Volunteer Culture", "type": "text", "content": {"body": "# Our Volunteer Culture\n\nAt Abundant Church, we believe everyone has a gift and a role to play.\n\n## Our Volunteer Values\n\n1. **Serve with Excellence** — Whatever you do, do it as unto the Lord\n2. **Be Faithful** — Show up on time, prepared, and with a great attitude\n3. **Be Teachable** — We're all learning and growing\n4. **Love People** — Every person matters to God\n5. **Have Fun** — Ministry should be life-giving!\n\n## What to Expect\n\n- A welcoming team that values you\n- Training and resources for your role\n- Opportunities to grow and lead\n- A community of like-minded servants\n\n## Volunteer Covenant\n\nAs a volunteer, you agree to:\n- Uphold the values of Abundant Church\n- Be reliable and communicative\n- Maintain appropriate conduct\n- Participate in required training"}, "duration_minutes": 8},
                {"title": "Serving with Excellence", "type": "video", "content": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "description": "What does excellence look like in church volunteering? Real stories from our teams."}, "duration_minutes": 10},
                {"title": "Finding Your Fit", "type": "text", "content": {"body": "# Finding Your Fit\n\nNot sure where to serve? Here's a quick guide:\n\n## Ministry Teams\n\n### Worship & Production\n- Worship team, sound, lights, cameras\n- *Best for:* Creative, technical, musical people\n\n### Kids Ministry\n- Sunday school, nursery, VBS\n- *Best for:* Patient, fun, child-loving people\n\n### Guest Services\n- Greeters, ushers, parking team, info desk\n- *Best for:* Friendly, outgoing, organized people\n\n### Food Pantry & Outreach\n- Community events, food distribution\n- *Best for:* Compassionate, service-oriented people\n\n### Small Group Leaders\n- Facilitate weekly small groups\n- *Best for:* Relational, mature believers\n\n### Administrative\n- Office support, data entry, communications\n- *Best for:* Detail-oriented, organized people\n\n## Self-Assessment Questions\n\n1. What are you passionate about?\n2. What skills do you have?\n3. Where do you feel God leading you?\n4. What energizes you?"}, "duration_minutes": 10},
                {"title": "Next Steps", "type": "quiz", "content": {"questions": [{"question": "Which is a core volunteer value at Abundant?", "options": ["Work alone", "Serve with excellence", "Only attend Sundays", "Avoid leadership"], "correct": 1}, {"question": "What should you do if you can't make your shift?", "options": ["Just don't show up", "Notify team lead 24 hours in advance", "Wait until next week", "Send someone random"], "correct": 1}], "passing_score": 70, "description": "Quick review before you get started!"}, "duration_minutes": 5},
            ],
        },
    ]

    seeded = 0
    for course_data in COURSES:
        existing = await _db.courses.find_one({"id": course_data["id"]})
        if existing:
            continue

        lessons_data = course_data.pop("lessons")
        course = {
            **course_data,
            "tenant_id": tenant_id,
            "status": "published",
            "enrollment_type": "open",
            "certificate_enabled": course_data["id"] in ("becoming-a-member", "premarital-counseling"),
            "created_at": now,
            "updated_at": now,
        }
        await _db.courses.insert_one({**course})

        # Create a single module per course
        module_id = f"mod-{course_data['id']}"
        await _db.course_modules.insert_one({
            "id": module_id,
            "course_id": course_data["id"],
            "tenant_id": tenant_id,
            "title": course_data["title"],
            "order": 1,
            "created_at": now,
        })

        for idx, lesson in enumerate(lessons_data):
            lesson_doc = {
                "id": f"les-{course_data['id']}-{idx+1}",
                "module_id": module_id,
                "course_id": course_data["id"],
                "tenant_id": tenant_id,
                "title": lesson["title"],
                "type": lesson["type"],
                "content": lesson["content"],
                "duration_minutes": lesson["duration_minutes"],
                "is_required": True,
                "order": idx + 1,
                "created_at": now,
            }
            await _db.course_lessons.insert_one({**lesson_doc})

        seeded += 1
        print(f"  Seeded course: {course_data['title']} ({len(lessons_data)} lessons)")

    if seeded > 0:
        print(f"Seeded {seeded} Solomon Academy courses")
    return seeded
