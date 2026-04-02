"""Solomon AI — Printer Management Routes"""
from fastapi import APIRouter, HTTPException, Request
from core import db, DEFAULT_TENANT_ID
from core.helpers import serialize_doc
from services.print_service import get_available_printers, add_printer, print_label, test_print, generate_label_preview

router = APIRouter()


async def _get_admin(request):
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") not in ("church_admin", "admin", "platform_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/admin/printers")
async def list_printers(request: Request):
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    printers = await get_available_printers(tenant_id)
    return {"printers": [serialize_doc(p) for p in printers]}


@router.post("/admin/printers")
async def create_printer(request: Request):
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    printer = await add_printer(tenant_id, body)
    return {"message": "Printer added", "printer": printer}


@router.delete("/admin/printers/{printer_id}")
async def remove_printer(request: Request, printer_id: str):
    user = await _get_admin(request)
    await db.printers.delete_one({"id": printer_id})
    return {"message": "Printer removed"}


@router.post("/admin/printers/{printer_id}/test")
async def test_printer(request: Request, printer_id: str):
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    result = await test_print(printer_id, tenant_id)
    return result


@router.post("/admin/printers/print")
async def print_checkin_label(request: Request):
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    label_data = body.get("label_data", {})
    printer_id = body.get("printer_id")
    result = await print_label(label_data, printer_id, tenant_id)
    return result


@router.post("/admin/printers/preview")
async def preview_label(request: Request):
    user = await _get_admin(request)
    body = await request.json()
    preview = generate_label_preview(body.get("label_data", {}), body.get("template", "child_checkin"))
    return {"preview": preview}
