"""
Media upload routes for Solomon AI — Admin file upload and management.
"""
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime, timezone
from database import db, serialize_doc, DEFAULT_TENANT_ID
from auth import get_current_admin_user
import uuid

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "audio/mpeg", "audio/wav", "audio/ogg",
    "video/mp4", "video/webm",
    "application/pdf"
}


@router.post("/admin/media/upload")
async def upload_media_file(request: Request, file: UploadFile = File(...)):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")
    max_size = 50 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    file_id = str(uuid.uuid4())
    ext = Path(file.filename or "file").suffix or ".bin"
    stored_name = f"{file_id}{ext}"
    tenant_dir = UPLOAD_DIR / tenant_id
    tenant_dir.mkdir(exist_ok=True)
    file_path = tenant_dir / stored_name
    with open(file_path, "wb") as f:
        f.write(contents)
    record = {
        "id": file_id,
        "tenant_id": tenant_id,
        "filename": file.filename,
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
    file_path = UPLOAD_DIR / record["tenant_id"] / record["stored_name"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File missing from storage")
    return FileResponse(
        path=str(file_path),
        media_type=record.get("content_type", "application/octet-stream"),
        filename=record.get("filename", "download")
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
    file_path = UPLOAD_DIR / tenant_id / record["stored_name"]
    if file_path.exists():
        file_path.unlink()
    await db.media_uploads.delete_one({"id": upload_id, "tenant_id": tenant_id})
    return {"message": "Upload deleted"}
