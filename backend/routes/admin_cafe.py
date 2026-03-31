"""Solomon AI — Admin Cafe Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc
from core.seed import ensure_demo_cafe_data
from models.schemas import (
    CafeItem, CafeItemCreate, CafeItemUpdate,
    CafeSettingsUpdate, Tenant,
)

router = APIRouter()

@router.get("/admin/cafe/settings")
async def get_admin_cafe_settings(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_cafe_data(tenant_id)
    settings = await db.cafe_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    return {"settings": serialize_doc(settings) if settings else None}


@router.patch("/admin/cafe/settings")
async def update_admin_cafe_settings(request: Request, payload: CafeSettingsUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.cafe_settings.update_one(
            {"tenant_id": tenant_id},
            {"$set": update_data},
            upsert=True
        )

    settings = await db.cafe_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    return {"settings": serialize_doc(settings) if settings else None}


@router.get("/admin/cafe/items")
async def get_admin_cafe_items(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None
):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_cafe_data(tenant_id)

    query = {"tenant_id": tenant_id}
    if category:
        query["category"] = category
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    items = await db.cafe_items.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"items": [serialize_doc(item) for item in items]}


@router.post("/admin/cafe/items")
async def create_admin_cafe_item(request: Request, payload: CafeItemCreate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    item = CafeItem(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        price=payload.price,
        image_url=payload.image_url,
        is_featured=payload.is_featured,
        is_active=payload.is_active
    ).model_dump()

    await db.cafe_items.insert_one(item)
    return {"item": serialize_doc(item)}


@router.put("/admin/cafe/items/{item_id}")
async def update_admin_cafe_item(request: Request, item_id: str, payload: CafeItemUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.cafe_items.update_one({"id": item_id, "tenant_id": tenant_id}, {"$set": update_data})

    item = await db.cafe_items.find_one({"id": item_id, "tenant_id": tenant_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Cafe item not found")

    return {"item": serialize_doc(item)}


@router.delete("/admin/cafe/items/{item_id}")
async def delete_admin_cafe_item(request: Request, item_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await db.cafe_items.delete_one({"id": item_id, "tenant_id": tenant_id})
    return {"message": "Cafe item deleted"}


@router.get("/admin/cafe/orders")
async def get_admin_cafe_orders(request: Request, limit: int = 50):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_cafe_data(tenant_id)

    orders = await db.cafe_orders.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"orders": [serialize_doc(order) for order in orders]}


@router.get("/admin/cafe/summary")
async def get_admin_cafe_summary(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_cafe_data(tenant_id)

    items_total = await db.cafe_items.count_documents({"tenant_id": tenant_id})
    active_items = await db.cafe_items.count_documents({"tenant_id": tenant_id, "is_active": True})
    orders = await db.cafe_orders.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(200)
    revenue = round(sum(order.get("total", 0) for order in orders), 2)
    member_count = await db.people.count_documents({"tenant_id": tenant_id})
    if member_count == 0 or member_count > 5000:
        member_count = 500

    return {
        "items_total": items_total,
        "active_items": active_items,
        "orders_count": len(orders),
        "revenue": revenue,
        "member_count": member_count
    }

