"""Solomon AI — Admin Workflows, Forms, Smart Lists Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc
from models.schemas import FormCreate, WorkflowCreate

router = APIRouter()

@router.get("/admin/workflows")
async def get_workflows(request: Request):
    """List all workflows"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    workflows = await db.workflows.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"workflows": workflows}


@router.post("/admin/workflows")
async def create_workflow(request: Request, payload: WorkflowCreate):
    """Create a new workflow"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    wf = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": payload.name,
        "description": payload.description,
        "trigger": payload.trigger,
        "is_active": True,
        "steps": payload.steps or [
            {"id": str(uuid.uuid4()), "order": 1, "type": "task", "title": "Step 1", "description": "", "assignee": None, "due_days": 1},
        ],
        "enrolled_count": 0,
        "completed_count": 0,
        "created_by": user.get("name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.workflows.insert_one(wf)
    return {"workflow": {k: v for k, v in wf.items() if k != "_id"}}


@router.put("/admin/workflows/{workflow_id}")
async def update_workflow(request: Request, workflow_id: str, payload: dict):
    """Update a workflow"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    allowed = ["name", "description", "trigger", "steps", "is_active"]
    updates = {k: v for k, v in payload.items() if k in allowed}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.workflows.update_one(
        {"id": workflow_id, "tenant_id": tenant_id}, {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow updated"}


@router.delete("/admin/workflows/{workflow_id}")
async def delete_workflow(request: Request, workflow_id: str):
    """Delete a workflow"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    result = await db.workflows.delete_one({"id": workflow_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow deleted"}


@router.post("/admin/workflows/{workflow_id}/enroll")
async def enroll_in_workflow(request: Request, workflow_id: str, payload: dict):
    """Enroll people in a workflow"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    person_ids = payload.get("person_ids", [])
    wf = await db.workflows.find_one({"id": workflow_id, "tenant_id": tenant_id}, {"_id": 0})
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    enrolled = 0
    for pid in person_ids:
        existing = await db.workflow_enrollments.find_one({"workflow_id": workflow_id, "person_id": pid, "status": "active"})
        if existing:
            continue
        enrollment = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "workflow_id": workflow_id,
            "workflow_name": wf["name"],
            "person_id": pid,
            "status": "active",
            "current_step": 0,
            "step_statuses": {s["id"]: "pending" for s in wf.get("steps", [])},
            "enrolled_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.workflow_enrollments.insert_one(enrollment)
        enrolled += 1
    await db.workflows.update_one({"id": workflow_id}, {"$inc": {"enrolled_count": enrolled}})
    return {"message": f"{enrolled} people enrolled", "enrolled": enrolled}


@router.get("/admin/workflows/{workflow_id}/enrollments")
async def get_workflow_enrollments(request: Request, workflow_id: str):
    """Get enrollments for a workflow"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    enrollments = await db.workflow_enrollments.find(
        {"workflow_id": workflow_id, "tenant_id": tenant_id}, {"_id": 0}
    ).to_list(500)
    for e in enrollments:
        person = await db.users.find_one({"user_id": e["person_id"]}, {"_id": 0, "name": 1, "email": 1})
        if person:
            e["person_name"] = person.get("name", "")
            e["person_email"] = person.get("email", "")
    return {"enrollments": enrollments}

# ============== PHASE 2: FORM BUILDER ==============


@router.get("/admin/forms")
async def get_forms(request: Request):
    """List all forms"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    forms = await db.custom_forms.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"forms": forms}


@router.post("/admin/forms")
async def create_form(request: Request, payload: FormCreate):
    """Create a new form"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    form = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": payload.name,
        "description": payload.description,
        "fields": payload.fields or [
            {"id": str(uuid.uuid4()), "type": "text", "label": "First Name", "required": True},
            {"id": str(uuid.uuid4()), "type": "text", "label": "Last Name", "required": True},
            {"id": str(uuid.uuid4()), "type": "email", "label": "Email", "required": True},
        ],
        "is_public": payload.is_public,
        "auto_create_profile": payload.auto_create_profile,
        "redirect_url": payload.redirect_url,
        "submission_count": 0,
        "is_active": True,
        "created_by": user.get("name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.custom_forms.insert_one(form)
    return {"form": {k: v for k, v in form.items() if k != "_id"}}


@router.put("/admin/forms/{form_id}")
async def update_form(request: Request, form_id: str, payload: dict):
    """Update a form"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    allowed = ["name", "description", "fields", "is_public", "auto_create_profile", "redirect_url", "is_active"]
    updates = {k: v for k, v in payload.items() if k in allowed}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.custom_forms.update_one({"id": form_id, "tenant_id": tenant_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Form not found")
    return {"message": "Form updated"}


@router.delete("/admin/forms/{form_id}")
async def delete_form(request: Request, form_id: str):
    """Delete a form"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    result = await db.custom_forms.delete_one({"id": form_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Form not found")
    return {"message": "Form deleted"}


@router.get("/admin/forms/{form_id}/submissions")
async def get_form_submissions(request: Request, form_id: str):
    """Get submissions for a form"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    subs = await db.form_submissions.find(
        {"form_id": form_id, "tenant_id": tenant_id}, {"_id": 0}
    ).sort("submitted_at", -1).to_list(500)
    return {"submissions": subs}

# ============== PHASE 2: DUPLICATE DETECTION & MERGE ==============


@router.get("/admin/smart-lists")
async def get_smart_lists(request: Request):
    """Get saved smart lists"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    lists = await db.smart_lists.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"lists": lists}


@router.post("/admin/smart-lists")
async def create_smart_list(request: Request, payload: dict):
    """Create a smart list with filter rules"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    sl = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": payload.get("name", "Untitled List"),
        "description": payload.get("description", ""),
        "rules": payload.get("rules", []),
        "is_smart": True,
        "created_by": user.get("name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.smart_lists.insert_one(sl)
    return {"list": {k: v for k, v in sl.items() if k != "_id"}}


@router.post("/admin/smart-lists/{list_id}/run")
async def run_smart_list(request: Request, list_id: str):
    """Execute a smart list and return matching members"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    sl = await db.smart_lists.find_one({"id": list_id, "tenant_id": tenant_id}, {"_id": 0})
    if not sl:
        raise HTTPException(status_code=404, detail="Smart list not found")
    query = {"tenant_id": tenant_id, "role": {"$in": ["member", "visitor"]}}
    for rule in sl.get("rules", []):
        field = rule.get("field")
        op = rule.get("operator")
        value = rule.get("value")
        if not field or not op:
            continue
        if op == "equals":
            query[field] = value
        elif op == "contains":
            query[field] = {"$regex": value, "$options": "i"}
        elif op == "not_equals":
            query[field] = {"$ne": value}
        elif op == "exists":
            query[field] = {"$exists": True, "$ne": ""}
        elif op == "not_exists":
            query[f"${field}"] = {"$exists": False}
    members = await db.users.find(query, {"_id": 0, "user_id": 1, "name": 1, "email": 1, "phone": 1, "membership_status": 1}).to_list(1000)
    return {"members": members, "count": len(members), "list_name": sl["name"]}

