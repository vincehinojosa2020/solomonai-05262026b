"""Solomon AI — SMS Routes (Text-to-Give + Admin SMS Management)"""
from fastapi import APIRouter, HTTPException, Request, Form
from datetime import datetime, timezone
from core import db, DEFAULT_TENANT_ID, logger
from core.helpers import serialize_doc
from services.sms_service import send_sms, send_bulk_sms, handle_incoming_sms

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
    if not user or user.get("role") not in ("church_admin", "admin", "platform_admin", "senior_pastor", "finance"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.post("/sms/incoming")
async def incoming_sms(request: Request):
    """Twilio webhook for incoming SMS (text-to-give)."""
    try:
        form = await request.form()
        from_number = form.get("From", "")
        body = form.get("Body", "")
        tenant_id = DEFAULT_TENANT_ID

        result = await handle_incoming_sms(from_number, body, tenant_id)
        # Return TwiML response
        reply = result.get("reply", "")
        return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply}</Message></Response>'
    except Exception as e:
        logger.error(f"Incoming SMS error: {e}")
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'


@router.post("/admin/sms/send")
async def admin_send_sms(request: Request):
    """Admin sends SMS to a member."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    to = body.get("to", "")
    message = body.get("message", "")
    if not to or not message:
        raise HTTPException(status_code=400, detail="Phone and message required")
    result = await send_sms(to, message, tenant_id, "admin_send")
    return result


@router.post("/admin/sms/bulk")
async def admin_bulk_sms(request: Request):
    """Admin sends bulk SMS."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    recipients = body.get("recipients", [])
    message = body.get("message", "")
    if not recipients or not message:
        raise HTTPException(status_code=400, detail="Recipients and message required")
    result = await send_bulk_sms(recipients, message, tenant_id, "admin_bulk")
    return result


@router.get("/admin/sms/logs")
async def get_sms_logs(request: Request, page: int = 1, per_page: int = 50):
    """Get SMS send history."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    total = await db.sms_logs.count_documents(query)
    logs = await db.sms_logs.find(query, {"_id": 0}).sort("created_at", -1).skip((page-1)*per_page).limit(per_page).to_list(per_page)
    return {"logs": [serialize_doc(l) for l in logs], "total": total}


@router.get("/admin/sms/text-to-give/config")
async def get_ttg_config(request: Request):
    """Get text-to-give configuration."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    config = await db.text_to_give_config.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not config:
        config = {
            "tenant_id": tenant_id,
            "enabled": False,
            "phone_number": "",
            "keywords": ["GIVE"],
            "default_fund": "General Fund",
            "welcome_message": "Welcome to Solomon AI Giving! Text 'GIVE 50' to give $50.",
            "confirmation_template": "Thank you, {name}! Your ${amount} gift to {fund} has been received.",
        }
    return config


@router.put("/admin/sms/text-to-give/config")
async def update_ttg_config(request: Request):
    """Update text-to-give configuration."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    body["tenant_id"] = tenant_id
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.text_to_give_config.update_one({"tenant_id": tenant_id}, {"$set": body}, upsert=True)
    return {"message": "Configuration updated"}
