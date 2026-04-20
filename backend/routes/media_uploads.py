"""
Media upload routes for Solomon AI — Admin file upload and management.
Secured: Path traversal protection via safe_path + secure_filename.
"""
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime, timezone
from database import db, serialize_doc, DEFAULT_TENANT_ID
from auth import get_current_admin_user
import uuid
import os
import re

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "audio/mpeg", "audio/wav", "audio/ogg",
    "video/mp4", "video/webm",
    "application/pdf"
}


def _secure_filename(filename: str) -> str:
    """Sanitize filename — strip path separators, null bytes, and dangerous chars."""
    if not filename:
        return "file"
    # Remove path separators and null bytes
    filename = filename.replace("/", "").replace("\\", "").replace("\x00", "")
    # Keep only safe chars
    filename = re.sub(r'[^\w\s\-.]', '', filename).strip()
    # Prevent hidden files
    filename = filename.lstrip('.')
    return filename or "file"


def _safe_path(base_dir: Path, *parts: str) -> Path:
    """Resolve path and verify it stays within base_dir. Raises ValueError on traversal."""
    resolved = (base_dir / os.path.join(*parts)).resolve()
    base_resolved = base_dir.resolve()
    if not str(resolved).startswith(str(base_resolved)):
        raise ValueError("Path traversal attempt blocked")
    return resolved


@router.post("/admin/media/upload")
async def upload_media_file(request: Request, file: UploadFile = File(...)):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    # Sanitize tenant_id for filesystem use
    safe_tenant = _secure_filename(tenant_id)
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="File type not allowed")
    max_size = 50 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    file_id = str(uuid.uuid4())
    safe_name = _secure_filename(file.filename or "file")
    ext = Path(safe_name).suffix or ".bin"
    # Only allow safe extensions
    if ext.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.mp3', '.wav', '.ogg', '.mp4', '.webm', '.pdf'}:
        ext = ".bin"
    stored_name = f"{file_id}{ext}"
    try:
        tenant_dir = _safe_path(UPLOAD_DIR, safe_tenant)
        tenant_dir.mkdir(exist_ok=True)
        file_path = _safe_path(UPLOAD_DIR, safe_tenant, stored_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")
    with open(file_path, "wb") as f:
        f.write(contents)
    record = {
        "id": file_id,
        "tenant_id": tenant_id,
        "filename": safe_name,
        "stored_name": stored_name,
        "content_type": file.content_type or "application/octet-stream",
        "size_bytes": len(contents),
        "uploaded_by": user.get("user_id"),
        "url": f"/api/admin/media/uploads/{file_id}/file",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.media_uploads.insert_one(record)
    return {"message": "File uploaded", "upload": serialize_doc(record)}


@router.get("/admin/media/uploads")
async def list_media_uploads(request: Request, limit: int = 100):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    uploads = await db.media_uploads.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    return {"uploads": [serialize_doc(u) for u in uploads]}


@router.get("/admin/media/uploads/{upload_id}/file")
async def serve_uploaded_file(request: Request, upload_id: str):
    record = await db.media_uploads.find_one({"id": upload_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        safe_tenant = _secure_filename(record["tenant_id"])
        safe_stored = _secure_filename(record["stored_name"])
        file_path = _safe_path(UPLOAD_DIR, safe_tenant, safe_stored)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File missing from storage")
    return FileResponse(
        path=str(file_path),
        media_type=record.get("content_type", "application/octet-stream"),
        filename=_secure_filename(record.get("filename", "download"))
    )


@router.delete("/admin/media/uploads/{upload_id}")
async def delete_media_upload(request: Request, upload_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    record = await db.media_uploads.find_one(
        {"id": upload_id, "tenant_id": tenant_id}, {"_id": 0}
    )
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found")
    try:
        safe_tenant = _secure_filename(tenant_id)
        safe_stored = _secure_filename(record["stored_name"])
        file_path = _safe_path(UPLOAD_DIR, safe_tenant, safe_stored)
        if file_path.exists():
            file_path.unlink()
    except ValueError:
        pass  # File path invalid, skip deletion
    await db.media_uploads.delete_one({"id": upload_id, "tenant_id": tenant_id})
    return {"message": "Upload deleted"}
