"""Solomon AI — Admin Media Routes"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from core import db, DEFAULT_TENANT_ID, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc, extract_youtube_id
from models.schemas import MediaCategory, MediaVideo, MediaVideoCreate, Tenant, GivingDonateRequest, SermonCreate, SermonUpdate

router = APIRouter()

@router.get("/admin/media/categories")
async def get_media_categories(request: Request):
    """Get all media categories for the church"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    if not tenant_id:
        # Platform admin - get default categories
        categories = await db.media_categories.find({}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    else:
        categories = await db.media_categories.find(
            {"tenant_id": tenant_id}, {"_id": 0}
        ).sort("sort_order", 1).to_list(100)
    
    return {"categories": categories}


@router.post("/admin/media/categories")
async def create_media_category(request: Request, category: dict):
    """Create a new media category"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    new_category = MediaCategory(
        tenant_id=tenant_id,
        name=category.get("name"),
        slug=category.get("slug", category.get("name", "").lower().replace(" ", "-")),
        icon=category.get("icon", "video"),
        sort_order=category.get("sort_order", 0)
    )
    
    await db.media_categories.insert_one(new_category.model_dump())
    return {"message": "Category created", "category": new_category.model_dump()}

# --- Media Videos ---


@router.get("/admin/media/videos")
async def get_admin_media_videos(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    category_id: Optional[str] = None,
    series_id: Optional[str] = None,
    search: Optional[str] = None,
    is_published: Optional[bool] = None
):
    """Get all videos for admin management"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"tenant_id": tenant_id}
    
    if category_id:
        query["category_id"] = category_id
    if series_id:
        query["series_id"] = series_id
    if is_published is not None:
        query["is_published"] = is_published
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"instructor": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    videos = await db.media_videos.find(
        query, {"_id": 0}
    ).sort([("is_featured", -1), ("created_at", -1)]).skip(skip).limit(limit).to_list(limit)
    
    total = await db.media_videos.count_documents(query)
    
    return {
        "videos": videos,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/admin/media/videos")
async def create_media_video(request: Request, video_data: MediaVideoCreate):
    """Create a new video from YouTube URL"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    
    # Extract YouTube ID
    youtube_id = extract_youtube_id(video_data.youtube_url)
    if not youtube_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    # Check for duplicate
    existing = await db.media_videos.find_one({
        "tenant_id": tenant_id,
        "youtube_id": youtube_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="This video already exists in your library")
    
    # Auto-generate thumbnail URL
    thumbnail_url = f"https://i.ytimg.com/vi/{youtube_id}/maxresdefault.jpg"
    
    # Create video record
    new_video = MediaVideo(
        tenant_id=tenant_id,
        title=video_data.title or f"Video {youtube_id}",
        description=video_data.description,
        youtube_id=youtube_id,
        youtube_url=video_data.youtube_url,
        thumbnail_url=thumbnail_url,
        instructor=video_data.instructor,
        category_id=video_data.category_id,
        series_id=video_data.series_id,
        is_featured=video_data.is_featured,
        badge=video_data.badge,
        is_published=True,
        published_at=datetime.now(timezone.utc).isoformat()
    )
    
    await db.media_videos.insert_one(new_video.model_dump())
    
    logger.info(f"Video created: {new_video.title} ({youtube_id}) for tenant {tenant_id}")
    
    return {
        "message": "Video added successfully",
        "video": new_video.model_dump()
    }


@router.put("/admin/media/videos/{video_id}")
async def update_media_video(request: Request, video_id: str, updates: dict):
    """Update a video's metadata"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": video_id, "tenant_id": tenant_id}
    
    # Allowed fields to update
    allowed_fields = [
        "title", "description", "instructor", "category_id", "series_id",
        "is_featured", "is_published", "badge", "sort_order", "duration"
    ]
    
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.media_videos.update_one(query, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {"message": "Video updated successfully"}


@router.delete("/admin/media/videos/{video_id}")
async def delete_media_video(request: Request, video_id: str):
    """Delete a video from the library"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": video_id, "tenant_id": tenant_id}
    
    result = await db.media_videos.delete_one(query)
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {"message": "Video deleted successfully"}


@router.post("/admin/media/videos/{video_id}/feature")
async def toggle_video_featured(request: Request, video_id: str):
    """Toggle featured status of a video"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    
    query = {"id": video_id, "tenant_id": tenant_id}
    
    video = await db.media_videos.find_one(query, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    new_featured = not video.get("is_featured", False)
    await db.media_videos.update_one(query, {"$set": {"is_featured": new_featured}})
    
    return {"message": f"Video {'featured' if new_featured else 'unfeatured'}", "is_featured": new_featured}

# --- Portal Media API (for members) ---


@router.get("/admin/media/sermons")
async def get_admin_media_sermons(request: Request, limit: int = 200):
    """List all sermons for admin management."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    sermons = await db.media_videos.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("published_at", -1).to_list(limit)
    return {"sermons": [serialize_doc(s) for s in sermons]}


@router.post("/admin/media/sermons")
async def create_admin_media_sermon(request: Request, payload: SermonCreate):
    """Publish a new sermon — immediately visible to all members."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    now_iso = datetime.now(timezone.utc).isoformat()
    sermon = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "title": payload.title,
        "description": payload.description,
        "video_url": payload.video_url,
        "thumbnail_url": payload.thumbnail_url,
        "pastor": payload.pastor,
        "series_name": payload.series_name,
        "duration_seconds": payload.duration_seconds,
        "content_type": payload.category,
        "category": payload.category,
        "is_published": payload.published,
        "published": payload.published,
        "published_at": now_iso if payload.published else None,
        "created_by": user.get("user_id"),
        "created_at": now_iso,
    }
    await db.media_videos.insert_one(sermon)
    return {"id": sermon["id"], "title": sermon["title"], "status": "published" if payload.published else "draft"}


@router.put("/admin/media/sermons/{sermon_id}")
async def update_admin_media_sermon(request: Request, sermon_id: str, payload: SermonUpdate):
    """Edit a sermon."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if "published" in update_data and update_data["published"]:
        update_data["published_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.media_videos.update_one(
        {"id": sermon_id, "tenant_id": tenant_id}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sermon not found")
    return {"message": "Sermon updated"}


@router.delete("/admin/media/sermons/{sermon_id}")
async def delete_admin_media_sermon(request: Request, sermon_id: str):
    """Delete a sermon."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    result = await db.media_videos.delete_one({"id": sermon_id, "tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sermon not found")
    return {"message": "Sermon deleted"}

# --- Giving Donate Endpoint ---
class GivingDonateRequest(BaseModel):
    amount: float
    fund: str = "general"
    frequency: str = "one_time"
    payment_method_id: Optional[str] = None
    source: str = "direct"

