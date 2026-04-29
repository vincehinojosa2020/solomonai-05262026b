"""Solomon AI — Auth Routes"""
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import hashlib
import logging
import os
import re
import httpx
import bcrypt

from core import (
    db, DEFAULT_TENANT_ID, ROLE_TEMPLATES, check_rate_limit_v2,
    get_permissions_for_user, get_session_token_from_request,
    get_current_admin_user, get_current_portal_user,
    logger,
)
from core.helpers import send_welcome_email, serialize_doc, check_rate_limit
from models.schemas import (
    SessionRequest, EmailLoginRequest, UserRegistrationRequest, User,
)

router = APIRouter()

@router.post("/auth/session")
async def exchange_session(request: SessionRequest, response: Response):
    """Exchange session_id from Emergent Auth for user data and set cookie"""
    try:
        # Call Emergent Auth to get session data
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": request.session_id}
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            auth_data = auth_response.json()
        
        # Extract user info
        email = auth_data.get("email")
        name = auth_data.get("name")
        picture = auth_data.get("picture")
        session_token = auth_data.get("session_token")
        
        if not email or not session_token:
            raise HTTPException(status_code=401, detail="Invalid auth response")
        
        # Check if user exists, create if not
        existing_user = await db.users.find_one({"email": email}, {"_id": 0})
        
        if existing_user:
            user_id = existing_user["user_id"]
            # Update user info if changed
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"name": name, "picture": picture}}
            )
        else:
            # Create new user
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            new_user = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": datetime.now(timezone.utc)
            }
            await db.users.insert_one(new_user)
        
        # Store session
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.user_sessions.delete_many({"user_id": user_id})  # Remove old sessions
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "role": existing_user.get("role", "member") if existing_user else "member",
            "session_token": session_token,
        }
        
    except httpx.RequestError as e:
        logger.error("auth_request_failed", extra={"exc_type": type(e).__name__})
        raise HTTPException(status_code=500, detail="Auth service unavailable")


# get_session_token_from_request: imported from core
    session_token = request.cookies.get("session_token")
    if session_token:
        return session_token

    return None


@router.get("/auth/me")
async def get_current_user(request: Request):
    """Get current user from session cookie or Authorization header"""
    session_token = get_session_token_from_request(request)
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]},
        {"_id": 0}
    )
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    result = serialize_doc(user_doc)
    # Ensure role and permissions are included
    result["role"] = user_doc.get("role", "admin")  # Default to admin for Google OAuth users
    result["permissions"] = get_permissions_for_user(user_doc)
    result["role_title"] = user_doc.get("role_title") or ROLE_TEMPLATES.get(user_doc.get("role", "member"), {}).get("role_title", "Member")
    
    # Multi-campus support: include accessible tenants
    accessible = user_doc.get("accessible_tenant_ids", [])
    if accessible and len(accessible) > 1:
        campus_list = []
        for tid in accessible:
            t = await db.tenants.find_one({"id": tid}, {"_id": 0, "id": 1, "name": 1, "city": 1, "state": 1})
            if t:
                campus_list.append(t)
        result["accessible_campuses"] = campus_list
        result["organization_id"] = user_doc.get("organization_id")
        result["organization_name"] = user_doc.get("organization_name")
    
    # Check if user has an active campus override in their session
    active_campus = session_doc.get("active_tenant_id")
    if active_campus and active_campus in accessible:
        result["active_tenant_id"] = active_campus
        active_tenant = await db.tenants.find_one({"id": active_campus}, {"_id": 0, "name": 1})
        result["active_tenant_name"] = active_tenant.get("name") if active_tenant else None
    
    return result


@router.post("/auth/switch-campus")
async def switch_campus(request: Request, payload: dict):
    """Switch the active campus for multi-campus admin users."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    target_tenant_id = payload.get("tenant_id")
    if not target_tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id required")
    
    accessible = user_doc.get("accessible_tenant_ids", [])
    if target_tenant_id not in accessible:
        raise HTTPException(status_code=403, detail="You do not have access to this campus")
    
    # Update the session with the active tenant override
    await db.user_sessions.update_one(
        {"session_token": session_token},
        {"$set": {"active_tenant_id": target_tenant_id}}
    )
    
    # Also update the user's current tenant_id for data queries
    await db.users.update_one(
        {"user_id": user_doc["user_id"]},
        {"$set": {"tenant_id": target_tenant_id}}
    )
    
    tenant = await db.tenants.find_one({"id": target_tenant_id}, {"_id": 0, "name": 1})
    tenant_name = tenant.get("name") if tenant else target_tenant_id
    
    return {
        "message": f"Switched to {tenant_name}",
        "active_tenant_id": target_tenant_id,
        "active_tenant_name": tenant_name,
    }


@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Clear session and cookie"""
    session_token = get_session_token_from_request(request)
    
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=True,
        samesite="none"
    )
    
    return {"message": "Logged out"}


def _refuse_in_production():
    """BLOCKER #5 from production audit — debug endpoints below leak password
    hash prefixes, similar-email lookups, and accept arbitrary email/password
    pairs to echo back diagnostic data. They are dev-only."""
    if os.environ.get("ENVIRONMENT", "").lower() == "production":
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/auth/debug/verify-accounts")
async def debug_verify_accounts():
    """Temporary diagnostic endpoint to verify seed accounts exist and have correct password hashes."""
    _refuse_in_production()
    import hashlib
    seed_password = os.environ.get("SOLOMON_SEED_PASSWORD")
    if not seed_password:
        # Fail-closed: never compare against a hardcoded default like "change_me"
        # which lets anyone who reads the source guess the expected hash.
        raise HTTPException(status_code=503, detail="SOLOMON_SEED_PASSWORD not configured")
    expected_hash = hashlib.sha256(seed_password.encode()).hexdigest()

    accounts_to_check = [
        "admin@solomonai.us",
        "admin@solomon.ai",
        "shannonnieman1030@gmail.com",
        "jacobpacheco@abundanteast.com",
    ]

    results = []
    for email in accounts_to_check:
        user = await db.users.find_one({"email": email}, {"_id": 0, "email": 1, "name": 1, "role": 1, "password_hash": 1, "user_id": 1, "is_active": 1})
        if user:
            stored = user.get("password_hash", "")
            results.append({
                "email": email,
                "exists": True,
                "name": user.get("name"),
                "role": user.get("role"),
                "user_id": user.get("user_id"),
                "is_active": user.get("is_active"),
                "has_password_hash": bool(stored),
                "hash_starts_with": stored[:12] if stored else None,
                "expected_hash_starts_with": expected_hash[:12],
                "password_matches_Demo2026": stored == expected_hash,
            })
        else:
            results.append({"email": email, "exists": False})

    total_users = await db.users.count_documents({})
    return {
        "total_users_in_db": total_users,
        "expected_hash_for_Demo2026": expected_hash[:16] + "...",
        "accounts": results,
    }


@router.post("/auth/debug/test-login")
async def debug_test_login(request: Request, payload: EmailLoginRequest):
    """Temporary diagnostic endpoint - simulates login flow and reports each step."""
    _refuse_in_production()
    import hashlib
    
    steps = []
    login_email = payload.email.strip().lower()
    steps.append({"step": "1_email_normalized", "value": login_email})
    steps.append({"step": "2_password_length", "value": len(payload.password)})
    steps.append({"step": "3_password_first_3_chars", "value": payload.password[:3] + "***"})
    
    input_hash = hashlib.sha256(payload.password.encode()).hexdigest()
    steps.append({"step": "4_input_hash", "value": input_hash[:16] + "..."})
    
    user_doc = await db.users.find_one({"email": login_email}, {"_id": 0})
    steps.append({"step": "5_user_found", "value": user_doc is not None})
    
    if user_doc:
        steps.append({"step": "6_user_name", "value": user_doc.get("name")})
        steps.append({"step": "7_user_role", "value": user_doc.get("role")})
        stored_hash = user_doc.get("password_hash", "")
        steps.append({"step": "8_stored_hash_field", "value": "password_hash"})
        steps.append({"step": "9_stored_hash", "value": stored_hash[:16] + "..." if stored_hash else "EMPTY"})
        steps.append({"step": "10_hashes_match", "value": input_hash == stored_hash})
        
        # Also check if password is stored in other fields
        for field in ["password", "pwd", "pass", "hashed_password"]:
            val = user_doc.get(field)
            if val:
                steps.append({"step": f"11_alt_field_{field}", "value": str(val)[:16] + "..."})
    else:
        # Check case-insensitive
        all_emails = await db.users.distinct("email")
        similar = [e for e in all_emails if login_email in e.lower() or e.lower() in login_email]
        steps.append({"step": "6_similar_emails", "value": similar[:5]})
    
    return {"email": login_email, "steps": steps}


@router.post("/auth/login")
async def email_password_login(request: Request, payload: EmailLoginRequest, response: Response):
    """Login with email and password — supports bcrypt + SHA256 legacy with auto-migration"""
    import hashlib
    import bcrypt
    
    # Normalize email
    login_email = payload.email.strip().lower()
    
    # Rate limiting disabled for demo
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.headers.get("x-real-ip", "") or request.client.host or "unknown"
    
    user_doc = await db.users.find_one({"email": login_email}, {"_id": 0})
    if not user_doc:
        logging.warning("auth_login_failed", extra={"reason": "user_not_found"})
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    stored_hash = user_doc.get("password_hash")
    if not stored_hash:
        logging.warning("auth_login_failed", extra={"reason": "no_password_hash", "user_id": user_doc.get("user_id")})
        raise HTTPException(status_code=401, detail="Password login not enabled for this account")
    
    # Verify password — support both bcrypt and legacy SHA256
    password_valid = False
    needs_rehash = False
    
    if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
        # bcrypt hash — verify with bcrypt
        password_valid = bcrypt.checkpw(payload.password.encode("utf-8"), stored_hash.encode("utf-8"))
    else:
        # Legacy SHA256 hash — verify and flag for migration
        input_hash = hashlib.sha256(payload.password.encode()).hexdigest()
        password_valid = (input_hash == stored_hash)
        needs_rehash = password_valid  # Migrate on successful login
    
    if not password_valid:
        logging.warning("auth_login_failed", extra={"reason": "password_mismatch", "user_id": user_doc.get("user_id")})
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Auto-migrate from SHA256 to bcrypt on successful login
    if needs_rehash:
        new_hash = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        await db.users.update_one(
            {"user_id": user_doc["user_id"]},
            {"$set": {"password_hash": new_hash}}
        )
        logging.info("auth_password_migrated", extra={"user_id": user_doc.get("user_id")})
    
    # Session management: limit to 5 concurrent sessions
    existing = await db.user_sessions.count_documents({"user_id": user_doc["user_id"]})
    if existing >= 5:
        # Delete oldest session
        oldest = await db.user_sessions.find({"user_id": user_doc["user_id"]}).sort("created_at", 1).limit(1).to_list(1)
        if oldest:
            await db.user_sessions.delete_one({"session_token": oldest[0].get("session_token")})
    
    session_token = f"sess_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    await db.user_sessions.insert_one({
        "user_id": user_doc["user_id"],
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc),
        "ip_address": client_ip,
        "device_hint": "mobile" if "Mobile" in request.headers.get("user-agent", "") else "desktop",
    })
    
    response.set_cookie(
        key="session_token", value=session_token,
        httponly=True, secure=True, samesite="none",
        path="/", max_age=24 * 60 * 60
    )
    
    # Resolve permissions
    permissions = get_permissions_for_user(user_doc)
    role = user_doc.get("role", "member")
    role_title = user_doc.get("role_title") or ROLE_TEMPLATES.get(role, {}).get("role_title", "Member")
    
    tenant_id = user_doc.get("tenant_id")
    tenant_name = None
    if tenant_id:
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "name": 1})
        tenant_name = tenant.get("name") if tenant else None
    
    login_response = {
        "user_id": user_doc["user_id"],
        "email": user_doc["email"],
        "name": user_doc["name"],
        "picture": user_doc.get("picture"),
        "role": role,
        "role_title": role_title,
        "permissions": permissions,
        "tenant_id": tenant_id,
        "tenant_name": tenant_name,
        "session_token": session_token,
        "token": session_token,
        "access_token": session_token,
    }
    
    # Multi-campus support
    accessible = user_doc.get("accessible_tenant_ids", [])
    if accessible and len(accessible) > 1:
        campus_list = []
        for tid in accessible:
            t = await db.tenants.find_one({"id": tid}, {"_id": 0, "id": 1, "name": 1})
            if t:
                campus_list.append(t)
        login_response["accessible_campuses"] = campus_list
        login_response["organization_id"] = user_doc.get("organization_id")
        login_response["organization_name"] = user_doc.get("organization_name")
    
    return login_response

# ============== USER REGISTRATION ==============

import re

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        return False, "Password must contain at least one special character (!@#$%^&*)"
    
    return True, "Password meets requirements"


@router.post("/auth/register")
async def register_user(request: UserRegistrationRequest, response: Response):
    """Register a new member account with email and password"""
    
    # Validate passwords match
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Validate password strength
    is_valid, message = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": request.email.lower()}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    
    # Create user
    user_id = str(uuid.uuid4())
    import bcrypt as _bc; password_hash = _bc.hashpw(request.password.encode("utf-8"), _bc.gensalt()).decode("utf-8")
    
    # Use provided tenant_id or default
    tenant_id = request.tenant_id if request.tenant_id else DEFAULT_TENANT_ID
    church_name = "your church"  # Default
    
    # Validate tenant exists and is active
    if tenant_id:
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
        if not tenant:
            raise HTTPException(status_code=400, detail="Selected church not found")
        if tenant.get("subscription_status") != "active":
            raise HTTPException(status_code=400, detail="Selected church is not accepting registrations")
        church_name = tenant.get("name", "your church")
    
    new_user = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "email": request.email.lower(),
        "password_hash": password_hash,
        "name": f"{request.first_name} {request.last_name}",
        "first_name": request.first_name,
        "last_name": request.last_name,
        "phone": request.phone,
        "role": "member",
        "church_id": tenant_id,
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
        "membership_status": "Active",
        "profile_photo": None,
        "email_verified": False,
        "registration_source": "web_signup"
    }
    
    await db.users.insert_one(new_user)
    
    # Create session and auto-login
    session_token = f"sess_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    logger.info("user_registered", extra={"tenant_id": tenant_id, "user_id": user_id})
    
    # Send welcome email from Solomon AI (non-blocking)
    asyncio.create_task(send_welcome_email(request.email, request.first_name, church_name))
    
    return {
        "message": "Account created successfully",
        "user_id": user_id,
        "email": new_user["email"],
        "name": new_user["name"],
        "role": "member",
        "session_token": session_token,
        "token": session_token,
        "access_token": session_token
    }


@router.post("/auth/check-email")
async def check_email_availability(data: dict):
    """Check if an email is available for registration"""
    email = data.get("email", "").lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    return {"available": existing is None}

# ============== MEMBER PORTAL ROUTES ==============


@router.post("/auth/register-church")
async def register_church(payload: dict):
    """Self-service church registration (signup flow)."""
    church_name = payload.get("church_name", "").strip()
    email = payload.get("email", "").strip()
    password = payload.get("password", "").strip()
    first_name = payload.get("first_name", "").strip()
    last_name = payload.get("last_name", "").strip()
    if not all([church_name, email, password, first_name]):
        raise HTTPException(status_code=400, detail="Church name, email, password, and first name are required")
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    tenant_id = church_name.lower().replace(" ", "-").replace("'", "") + "-" + str(uuid.uuid4())[:8]
    await db.tenants.insert_one({
        "id": tenant_id, "name": church_name, "city": payload.get("city", ""), "state": payload.get("state", ""),
        "denomination": payload.get("denomination", ""), "member_count_range": payload.get("member_count", ""),
        "plan": "growth", "trial_start": datetime.now(timezone.utc).isoformat(),
        "trial_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "status": "trial", "created_at": datetime.now(timezone.utc).isoformat()
    })
    user_id = str(uuid.uuid4())
    await db.users.insert_one({
        "user_id": user_id, "email": email, "password_hash": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        "name": f"{first_name} {last_name}".strip(), "first_name": first_name, "last_name": last_name,
        "role": "church_admin", "role_title": payload.get("role_title", "Lead Pastor"),
        "tenant_id": tenant_id, "is_first_login": True, "created_at": datetime.now(timezone.utc).isoformat()
    })
    session_token = f"sess_{uuid.uuid4().hex}"
    await db.user_sessions.insert_one({
        "session_token": session_token, "user_id": user_id, "email": email, "role": "church_admin",
        "tenant_id": tenant_id, "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    })
    return {"success": True, "token": session_token, "user_id": user_id, "name": f"{first_name} {last_name}".strip(),
            "role": "church_admin", "tenant_id": tenant_id, "church_name": church_name, "is_first_login": True}


# ============== GIVING INTEGRATIONS (Scaffolding for Pushpay / SecureGive / Solomon Pay) ==============



@router.post("/auth/forgot-password")
async def forgot_password(request: Request):
    """Send password reset email. Always returns 200 to prevent email enumeration."""
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    if not email:
        return {"message": "If an account exists, reset instructions have been sent."}

    user = await db.users.find_one({"email": email}, {"_id": 0, "user_id": 1, "name": 1, "email": 1})
    if user:
        # Generate reset token
        reset_token = str(uuid.uuid4())
        await db.password_resets.update_one(
            {"email": email},
            {"$set": {
                "email": email,
                "token": reset_token,
                "user_id": user["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                "used": False,
            }},
            upsert=True
        )
        # Send email via Resend if configured
        try:
            resend_key = os.environ.get("RESEND_API_KEY")
            sender = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
            if resend_key:
                import httpx as _httpx
                await _httpx.AsyncClient().post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                    json={
                        "from": f"Solomon AI <{sender}>",
                        "to": [email],
                        "subject": "Reset Your Solomon AI Password",
                        "html": f"""<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px">
                            <h2 style="color:#0f172a">Password Reset</h2>
                            <p>Hi {user.get('name', 'there')},</p>
                            <p>We received a request to reset your Solomon AI password. Your reset code is:</p>
                            <div style="background:#f1f5f9;border-radius:8px;padding:16px;text-align:center;margin:16px 0">
                                <code style="font-size:24px;font-weight:bold;color:#3b82f6;letter-spacing:2px">{reset_token[:8].upper()}</code>
                            </div>
                            <p style="color:#64748b;font-size:14px">This code expires in 1 hour. If you didn't request this, ignore this email.</p>
                            <p style="color:#94a3b8;font-size:12px;margin-top:24px">&copy; {datetime.now().year} Solomon AI</p>
                        </div>"""
                    },
                    timeout=10
                )
                logger.info("password_reset_email_sent", extra={"user_id": user.get("user_id")})
        except Exception as e:
            logger.error("password_reset_email_failed", extra={"exc_type": type(e).__name__, "user_id": user.get("user_id")})

    return {"message": "If an account exists, reset instructions have been sent."}
