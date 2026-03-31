"""Solomon AI — Admin Merch Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc, DEFAULT_MERCH_EMBED_URL
from core.seed import ensure_demo_merch_data
from models.schemas import (
    MerchProduct, MerchProductCreate, MerchProductUpdate,
    MerchSettingsUpdate, Tenant,
)

router = APIRouter()

@router.get("/admin/merch/settings")
async def get_merch_settings(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_merch_data(tenant_id)
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "merch_embed_url": 1})
    return {"merch_embed_url": tenant.get("merch_embed_url", DEFAULT_MERCH_EMBED_URL) if tenant else DEFAULT_MERCH_EMBED_URL}


@router.patch("/admin/merch/settings")
async def update_merch_settings(request: Request, payload: MerchSettingsUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {"merch_embed_url": payload.merch_embed_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Merch settings updated", "merch_embed_url": payload.merch_embed_url}


@router.get("/admin/merch/products")
async def get_admin_merch_products(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None
):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_merch_data(tenant_id)

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

    products = await db.merch_products.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"products": [serialize_doc(p) for p in products]}


@router.post("/admin/merch/products")
async def create_merch_product(request: Request, payload: MerchProductCreate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    product = MerchProduct(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        image_url=payload.image_url,
        price=payload.price,
        category=payload.category,
        is_featured=payload.is_featured,
        is_active=payload.is_active,
        inventory=payload.inventory
    ).model_dump()

    await db.merch_products.insert_one(product)
    return {"product": serialize_doc(product)}


@router.put("/admin/merch/products/{product_id}")
async def update_merch_product(request: Request, product_id: str, payload: MerchProductUpdate):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.merch_products.update_one(
            {"id": product_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )

    product = await db.merch_products.find_one({"id": product_id, "tenant_id": tenant_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"product": serialize_doc(product)}


@router.delete("/admin/merch/products/{product_id}")
async def delete_merch_product(request: Request, product_id: str):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await db.merch_products.delete_one({"id": product_id, "tenant_id": tenant_id})
    return {"message": "Product deleted"}


@router.get("/admin/merch/orders")
async def get_merch_orders(request: Request, limit: int = 50):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_merch_data(tenant_id)

    orders = await db.merch_orders.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return {"orders": [serialize_doc(o) for o in orders]}


@router.get("/admin/merch/summary")
async def get_merch_summary(request: Request):
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")

    await ensure_demo_merch_data(tenant_id)

    products_total = await db.merch_products.count_documents({"tenant_id": tenant_id})
    active_products = await db.merch_products.count_documents({"tenant_id": tenant_id, "is_active": True})
    featured_products = await db.merch_products.count_documents({"tenant_id": tenant_id, "is_featured": True})
    orders = await db.merch_orders.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(200)
    revenue = round(sum(order.get("total", 0) for order in orders), 2)
    member_count = await db.people.count_documents({"tenant_id": tenant_id})
    if member_count == 0 or member_count > 5000:
        member_count = 500

    return {
        "products_total": products_total,
        "active_products": active_products,
        "featured_products": featured_products,
        "orders_count": len(orders),
        "revenue": revenue,
        "member_count": member_count
    }

