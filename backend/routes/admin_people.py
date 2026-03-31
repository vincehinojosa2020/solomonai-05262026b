"""Solomon AI — Admin People, Members, Households, Roles Routes"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import csv
import io
import json
import logging

from core import (
    db, DEFAULT_TENANT_ID, PERMISSION_REGISTRY, ROLE_TEMPLATES,
    get_current_admin_user, require_permission, require_tenant,
    get_permissions_for_user, audit_log,
    logger,
)
from core.helpers import serialize_doc
from models.schemas import Household, User

router = APIRouter()

@router.get("/admin/members")
async def get_admin_member_directory(
    request: Request, 
    skip: int = 0, 
    limit: int = 50,
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """Get member directory for church admin or platform admin"""
    user = await get_current_admin_user(request)
    
    # Build query based on role
    query = {"role": "member"}
    
    if user.get("role") in ["church_admin", "admin"]:
        # Church admin only sees their own church members
        query["tenant_id"] = user.get("tenant_id")
    elif user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    # Platform admin sees all members (no tenant filter)
    
    # Add search filter
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}}
        ]
    
    # Add status filter
    if status:
        query["membership_status"] = status
    
    # Sort direction
    sort_dir = -1 if sort_order == "desc" else 1
    
    # Execute query
    members = await db.users.find(
        query,
        {"_id": 0, "password_hash": 0}
    ).sort(sort_by, sort_dir).skip(skip).limit(limit).to_list(limit)
    
    total = await db.users.count_documents(query)
    
    # Enrich with tenant names
    for member in members:
        if member.get("tenant_id"):
            tenant = await db.tenants.find_one({"id": member["tenant_id"]}, {"_id": 0, "name": 1})
            member["church_name"] = tenant["name"] if tenant else "Unknown"
    
    return {
        "members": members,
        "total": total,
        "skip": skip,
        "limit": limit,
        "filters": {
            "search": search,
            "status": status
        }
    }

# ============== RBAC, VOLUNTEER, HEALTH ENDPOINTS ==============

class RoleUpdateRequest(BaseModel):
    role: str = None
    role_template: str = None

class PermissionsUpdateRequest(BaseModel):
    permissions: List[str]

class PermissionGrantRequest(BaseModel):
    permission: str


@router.get("/admin/roles/templates")
async def get_role_templates(request: Request):
    user = await require_permission(request, "admin.users.roles")
    templates = {name: {"title": t["role_title"], "permissions": t["permissions"]}
            for name, t in ROLE_TEMPLATES.items()
            if name != "platform_admin" or user.get("role") == "platform_admin"}
    return {"templates": templates}


@router.get("/admin/roles/users")
async def get_users_by_role(request: Request):
    user = await require_permission(request, "admin.members.view")
    tenant_id = user.get("tenant_id")
    query = {"tenant_id": tenant_id} if tenant_id and user.get("role") != "platform_admin" else {}
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    grouped = {}
    for u in users:
        rt = u.get("role_title") or ROLE_TEMPLATES.get(u.get("role", "member"), {}).get("role_title", "Member")
        grouped.setdefault(rt, []).append({"user_id": u.get("user_id"), "name": u.get("name"), "email": u.get("email"), "role": u.get("role"), "role_title": rt, "permissions": get_permissions_for_user(u)})
    return grouped


# ============== CSV MEMBER IMPORT ==============


@router.post("/admin/members/import/parse")
async def parse_csv_for_import(request: Request, file: UploadFile = File(...)):
    """Parse uploaded CSV and return headers + preview rows for column mapping."""
    user = await get_current_admin_user(request)
    import csv as _csv
    import io as _io

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = _csv.DictReader(_io.StringIO(text))
    headers = reader.fieldnames or []
    if not headers:
        raise HTTPException(status_code=400, detail="CSV file has no headers")

    preview_rows = []
    for i, row in enumerate(reader):
        if i >= 5:
            break
        preview_rows.append(dict(row))

    # Count total rows
    text_reader = _csv.DictReader(_io.StringIO(text))
    total_rows = sum(1 for _ in text_reader)

    return {
        "headers": headers,
        "preview": preview_rows,
        "total_rows": total_rows,
        "system_fields": [
            {"key": "first_name", "label": "First Name", "required": True},
            {"key": "last_name", "label": "Last Name", "required": True},
            {"key": "email", "label": "Email", "required": False},
            {"key": "mobile_phone", "label": "Phone", "required": False},
            {"key": "gender", "label": "Gender", "required": False},
            {"key": "date_of_birth", "label": "Date of Birth", "required": False},
            {"key": "membership_status", "label": "Membership Status", "required": False},
            {"key": "campus", "label": "Campus", "required": False},
            {"key": "notes", "label": "Notes", "required": False},
        ]
    }


@router.post("/admin/members/import/execute")
async def execute_csv_import(request: Request, file: UploadFile = File(...), mapping: str = Form("{}")):
    """Execute CSV import with provided column mapping."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    import csv as _csv
    import io as _io
    import json as _json

    try:
        col_map = _json.loads(mapping)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid mapping JSON")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = _csv.DictReader(_io.StringIO(text))
    imported = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader):
        try:
            first_name = row.get(col_map.get("first_name", ""), "").strip()
            last_name = row.get(col_map.get("last_name", ""), "").strip()
            email = row.get(col_map.get("email", ""), "").strip()

            if not first_name and not last_name:
                skipped += 1
                continue

            # Check duplicate by email if provided
            if email:
                existing = await db.people.find_one({"email": email, "tenant_id": tenant_id})
                if existing:
                    skipped += 1
                    continue

            person_id = str(uuid.uuid4())
            person_doc = {
                "id": person_id,
                "tenant_id": tenant_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email or None,
                "mobile_phone": row.get(col_map.get("mobile_phone", ""), "").strip() or None,
                "gender": row.get(col_map.get("gender", ""), "").strip() or None,
                "date_of_birth": row.get(col_map.get("date_of_birth", ""), "").strip() or None,
                "membership_status": row.get(col_map.get("membership_status", ""), "").strip() or "visitor",
                "campus": row.get(col_map.get("campus", ""), "").strip() or None,
                "notes": row.get(col_map.get("notes", ""), "").strip() or None,
                "engagement_score": 0,
                "ytd_giving": 0.0,
                "lifetime_giving": 0.0,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            await db.people.insert_one(person_doc)
            imported += 1
        except Exception as exc:
            errors.append({"row": i + 2, "error": str(exc)})

    # Log activity
    await db.activity_log.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "action": "csv_import",
        "description": f"CSV Import: {imported} members imported, {skipped} skipped by {user.get('name', 'Admin')}",
        "entity_type": "import",
        "entity_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10],
        "total_processed": imported + skipped + len(errors)
    }

# ============== AGGREGATE CAMPUS DASHBOARD ==============


@router.get("/admin/members/{user_id}/permissions")
async def get_member_permissions(request: Request, user_id: str):
    admin = await require_permission(request, "admin.users.roles")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if admin.get("role") != "platform_admin" and target.get("tenant_id") != admin.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Cannot view users outside your church")
    perms = get_permissions_for_user(target)
    template_match = None
    for tname, tdata in ROLE_TEMPLATES.items():
        if set(tdata["permissions"]) == set(perms):
            template_match = tname
            break
    return {"user_id": user_id, "name": target.get("name"), "email": target.get("email"), "role": target.get("role"), "role_title": target.get("role_title", ""), "permissions": perms, "template_match": template_match, "is_custom": template_match is None}


@router.put("/admin/members/{user_id}/role")
async def update_member_role(request: Request, user_id: str, payload: RoleUpdateRequest):
    admin = await require_permission(request, "admin.users.roles")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if admin.get("role") != "platform_admin" and target.get("tenant_id") != admin.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Cannot modify users outside your church")
    before = {"role": target.get("role"), "role_title": target.get("role_title"), "permissions": get_permissions_for_user(target)}
    template_key = payload.role_template or payload.role
    if not template_key or template_key not in ROLE_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(sorted(ROLE_TEMPLATES.keys()))}")
    tmpl = ROLE_TEMPLATES[template_key]
    role_field = template_key if template_key in ("church_admin", "platform_admin", "member") else ("church_admin" if any(p.startswith("admin.") for p in tmpl["permissions"]) else "member")
    update_fields = {"role": role_field, "role_title": tmpl["role_title"], "permissions": tmpl["permissions"]}
    await db.users.update_one({"user_id": user_id}, {"$set": update_fields})
    after = {"role": update_fields["role"], "role_title": update_fields["role_title"], "permissions": update_fields["permissions"]}
    await audit_log("role_change", "user", user_id, target.get("tenant_id", ""), admin.get("user_id", ""), admin.get("name", ""), before, after, request)
    return {"success": True, "user_id": user_id, "new_role": update_fields["role"], "role_title": update_fields["role_title"], "permissions": update_fields["permissions"], "name": target.get("name")}


@router.put("/admin/members/{user_id}/permissions")
async def update_member_permissions(request: Request, user_id: str, payload: PermissionsUpdateRequest):
    admin = await require_permission(request, "admin.users.roles")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if admin.get("role") != "platform_admin" and target.get("tenant_id") != admin.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Cannot modify users outside your church")
    invalid = [p for p in payload.permissions if p not in PERMISSION_REGISTRY]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown permissions: {', '.join(invalid)}")
    has_admin = any(p.startswith("admin.") for p in payload.permissions)
    role_field = "church_admin" if has_admin else "member"
    if target.get("role") == "platform_admin":
        role_field = "platform_admin"
    await db.users.update_one({"user_id": user_id}, {"$set": {"permissions": payload.permissions, "role": role_field}})
    await audit_log("permissions_change", "user", user_id, target.get("tenant_id", ""), admin.get("user_id", ""), admin.get("name", ""), {"permissions": get_permissions_for_user(target)}, {"permissions": payload.permissions}, request)
    return {"success": True, "user_id": user_id, "permissions": payload.permissions}


@router.post("/admin/members/{user_id}/permissions/grant")
async def grant_permission(request: Request, user_id: str, payload: PermissionGrantRequest):
    admin = await require_permission(request, "admin.users.roles")
    if payload.permission not in PERMISSION_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown permission: {payload.permission}")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    current = get_permissions_for_user(target)
    if payload.permission not in current:
        current.append(payload.permission)
    await db.users.update_one({"user_id": user_id}, {"$set": {"permissions": current}})
    return {"success": True, "user_id": user_id, "permissions": current}


@router.delete("/admin/members/{user_id}/permissions/{perm}")
async def revoke_permission(request: Request, user_id: str, perm: str):
    admin = await require_permission(request, "admin.users.roles")
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    current = [p for p in get_permissions_for_user(target) if p != perm]
    await db.users.update_one({"user_id": user_id}, {"$set": {"permissions": current}})
    return {"success": True, "user_id": user_id, "permissions": current}

# ============== VOLUNTEER TEAM ENDPOINTS ==============


@router.get("/admin/people/duplicates")
async def detect_duplicates(request: Request):
    """Detect potential duplicate members"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    members = await db.users.find(
        {"tenant_id": tenant_id, "role": {"$in": ["member", "visitor"]}},
        {"_id": 0, "user_id": 1, "name": 1, "email": 1, "phone": 1, "membership_status": 1}
    ).to_list(5000)
    duplicates = []
    seen = set()
    for i, a in enumerate(members):
        for b in members[i+1:]:
            pair_key = tuple(sorted([a["user_id"], b["user_id"]]))
            if pair_key in seen:
                continue
            score = 0
            a_name = (a.get("name") or "").lower().strip()
            b_name = (b.get("name") or "").lower().strip()
            if a_name and b_name and a_name == b_name:
                score += 50
            elif a_name and b_name:
                a_parts = set(a_name.split())
                b_parts = set(b_name.split())
                overlap = a_parts & b_parts
                if len(overlap) >= 1 and (len(overlap) / max(len(a_parts), len(b_parts))) >= 0.5:
                    score += 30
            a_email = (a.get("email") or "").lower().strip()
            b_email = (b.get("email") or "").lower().strip()
            if a_email and b_email and a_email == b_email:
                score += 40
            a_phone = (a.get("phone") or "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            b_phone = (b.get("phone") or "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            if a_phone and b_phone and len(a_phone) >= 7 and a_phone[-7:] == b_phone[-7:]:
                score += 30
            if score >= 40:
                seen.add(pair_key)
                duplicates.append({
                    "person_a": a,
                    "person_b": b,
                    "score": min(score, 100),
                    "reasons": []
                })
    duplicates.sort(key=lambda x: x["score"], reverse=True)
    return {"duplicates": duplicates[:50], "total": len(duplicates)}


@router.post("/admin/people/merge")
async def merge_people(request: Request, payload: dict):
    """Merge two duplicate member profiles"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    keep_id = payload.get("keep_id")
    merge_id = payload.get("merge_id")
    if not keep_id or not merge_id:
        raise HTTPException(status_code=400, detail="keep_id and merge_id required")
    keep = await db.users.find_one({"user_id": keep_id, "tenant_id": tenant_id})
    merge = await db.users.find_one({"user_id": merge_id, "tenant_id": tenant_id})
    if not keep or not merge:
        raise HTTPException(status_code=404, detail="One or both profiles not found")
    merge_fields = {}
    for field in ["phone", "address", "city", "state", "zip", "birthday", "gender", "notes"]:
        if not keep.get(field) and merge.get(field):
            merge_fields[field] = merge[field]
    if merge_fields:
        await db.users.update_one({"user_id": keep_id}, {"$set": merge_fields})
    await db.donations.update_many({"person_id": merge_id}, {"$set": {"person_id": keep_id}})
    await db.event_registrations.update_many({"user_id": merge_id}, {"$set": {"user_id": keep_id}})
    await db.group_members.update_many({"person_id": merge_id}, {"$set": {"person_id": keep_id}})
    await db.workflow_enrollments.update_many({"person_id": merge_id}, {"$set": {"person_id": keep_id}})
    await db.users.delete_one({"user_id": merge_id, "tenant_id": tenant_id})
    return {"message": f"Profiles merged. Kept {keep.get('name', keep_id)}.", "kept_id": keep_id}

# ============== PHASE 2: SMART LISTS ==============


@router.get("/admin/households")
async def get_households(request: Request):
    user = await require_permission(request, "admin.members.view")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    households = await db.households.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(500)
    return {"households": households, "total": len(households)}


@router.post("/admin/households")
async def create_household(request: Request, payload: dict):
    user = await require_permission(request, "admin.members.edit")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    household = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "household_name": payload.get("household_name", ""),
        "member_ids": payload.get("member_ids", []),
        "primary_contact_id": payload.get("primary_contact_id"),
        "address": payload.get("address", {}),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.households.insert_one({**household})
    return household


@router.put("/admin/households/{household_id}")
async def update_household(request: Request, household_id: str, payload: dict):
    user = await require_permission(request, "admin.members.edit")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    updates = {k: v for k, v in payload.items() if k in ["household_name", "member_ids", "primary_contact_id", "address"]}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.households.update_one({"id": household_id, "tenant_id": tenant_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Household not found")
    return await db.households.find_one({"id": household_id}, {"_id": 0})


# ============== MEMBER DIRECTORY ==============



# ============== CUSTOM FIELDS ON PEOPLE ==============

@router.put("/admin/people/{person_id}/custom-fields")
async def update_person_custom_fields(request: Request, person_id: str):
    """Update custom_fields dict for a person record."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    custom_fields = body.get("custom_fields", {})

    result = await db.people.update_one(
        {"id": person_id, "tenant_id": tenant_id},
        {"$set": {"custom_fields": custom_fields, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"message": "Custom fields updated", "custom_fields": custom_fields}


@router.get("/admin/people/{person_id}/custom-fields")
async def get_person_custom_fields(request: Request, person_id: str):
    """Get custom_fields for a specific person."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    person = await db.people.find_one(
        {"id": person_id, "tenant_id": tenant_id},
        {"_id": 0, "custom_fields": 1, "id": 1}
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"person_id": person_id, "custom_fields": person.get("custom_fields", {})}
