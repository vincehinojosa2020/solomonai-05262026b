"""
Solomon AI — Seed: Commerce (Merch + Cafe)
"""
from datetime import datetime, timezone
from typing import Optional
import uuid
import random

from core import db, DEFAULT_TENANT_ID
from core.helpers import DEFAULT_MERCH_EMBED_URL
from models.schemas import MerchProduct, CafeSettings, CafeItem


async def ensure_demo_merch_data(tenant_id: Optional[str]):
    if not tenant_id:
        return

    product_count = await db.merch_products.count_documents({"tenant_id": tenant_id})
    if product_count == 0:
        demo_products = [
            {
                "name": "SO BE IT - Vinyl",
                "description": "Limited edition worship vinyl for collectors.",
                "image_url": "https://images.unsplash.com/photo-1539375665275-f9de415ef9ac?auto=format&fit=crop&w=600&q=80",
                "price": 40.00,
                "category": "Music",
                "is_featured": True,
                "inventory": 120
            },
            {
                "name": "SO BE IT Hoodie",
                "description": "Soft fleece hoodie inspired by the SO BE IT collection.",
                "image_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=600&q=80",
                "price": 60.00,
                "category": "Apparel",
                "is_featured": True,
                "inventory": 80
            },
            {
                "name": "SO BE IT Album T-Shirt",
                "description": "Classic tee with album artwork. Perfect for Sundays and beyond.",
                "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=600&q=80",
                "price": 30.00,
                "category": "Apparel",
                "inventory": 150
            },
            {
                "name": "SO BE IT Crest Camo Hat",
                "description": "Structured camo hat with embroidered crest.",
                "image_url": "https://images.unsplash.com/photo-1588850561407-ed78c334e67a?auto=format&fit=crop&w=600&q=80",
                "price": 35.00,
                "category": "Accessories",
                "inventory": 90
            },
            {
                "name": "SO BE IT Tote",
                "description": "Canvas tote for carrying all the essentials.",
                "image_url": "https://images.unsplash.com/photo-1622260614153-03223fb72052?auto=format&fit=crop&w=600&q=80",
                "price": 20.00,
                "category": "Accessories",
                "inventory": 140
            },
            {
                "name": "Abundant Ceramic Mug",
                "description": "Signature mug for morning devotionals and coffee.",
                "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1200&q=80",
                "price": 18.00,
                "category": "Drinkware",
                "inventory": 110
            },
            {
                "name": "Abundant YETI Tumbler",
                "description": "Insulated tumbler with laser-etched logo.",
                "image_url": "https://images.unsplash.com/photo-1527169402691-feff5539e52c?auto=format&fit=crop&w=1200&q=80",
                "price": 42.00,
                "category": "Drinkware",
                "inventory": 70
            }
        ]

        for idx, product in enumerate(demo_products, start=1):
            merch = MerchProduct(
                tenant_id=tenant_id,
                name=product["name"],
                description=product.get("description"),
                image_url=product.get("image_url"),
                price=product["price"],
                category=product.get("category"),
                is_featured=product.get("is_featured", False),
                is_active=True,
                inventory=product.get("inventory", 0)
            ).model_dump()
            merch["id"] = f"merch_{tenant_id}_{idx}"
            await db.merch_products.update_one({"id": merch["id"]}, {"$set": merch}, upsert=True)

    order_count = await db.merch_orders.count_documents({"tenant_id": tenant_id})
    if order_count == 0:
        member = await db.users.find_one({"tenant_id": tenant_id, "role": "member"}, {"_id": 0})
        if member:
            products = await db.merch_products.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(10)
            if products:
                for i in range(6):
                    item = random.choice(products)
                    quantity = random.randint(1, 3)
                    total = round(item["price"] * quantity, 2)
                    order = {
                        "id": str(uuid.uuid4()),
                        "tenant_id": tenant_id,
                        "user_id": member["user_id"],
                        "items": [{
                            "product_id": item["id"],
                            "name": item["name"],
                            "price": item["price"],
                            "quantity": quantity,
                            "image_url": item.get("image_url")
                        }],
                        "subtotal": total,
                        "total": total,
                        "status": "placed",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.merch_orders.update_one({"id": order["id"]}, {"$set": order}, upsert=True)

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "merch_embed_url": 1})
    if tenant is not None and not tenant.get("merch_embed_url"):
        await db.tenants.update_one({"id": tenant_id}, {"$set": {"merch_embed_url": DEFAULT_MERCH_EMBED_URL}})


async def ensure_demo_cafe_data(tenant_id: Optional[str]):
    if not tenant_id:
        return

    settings = await db.cafe_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not settings:
        settings_doc = CafeSettings(
            tenant_id=tenant_id,
            pickup_start="07:30 AM",
            pickup_end="10:30 AM",
            pickup_interval_minutes=15,
            location="Lobby pickup counter"
        ).model_dump()
        await db.cafe_settings.insert_one(settings_doc)

    item_count = await db.cafe_items.count_documents({"tenant_id": tenant_id})
    if item_count == 0:
        demo_items = [
            {
                "name": "House Latte",
                "description": "Espresso with steamed milk and vanilla.",
                "category": "Coffee",
                "price": 4.5,
                "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1200&q=80",
                "is_featured": True
            },
            {
                "name": "Cold Brew",
                "description": "Slow-steeped cold brew over ice.",
                "category": "Coffee",
                "price": 4.0,
                "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "name": "Cappuccino",
                "description": "Rich espresso topped with velvety foam.",
                "category": "Coffee",
                "price": 4.75,
                "image_url": "https://images.unsplash.com/photo-1504753793650-d4a2b783c15e?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "name": "Chai Latte",
                "description": "Spiced chai with steamed oat milk.",
                "category": "Tea",
                "price": 4.25,
                "image_url": "https://images.unsplash.com/photo-1507133750040-4a8f57021571?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "name": "Iced Matcha",
                "description": "Creamy matcha latte served cold.",
                "category": "Tea",
                "price": 4.5,
                "image_url": "https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "name": "Blueberry Muffin",
                "description": "Fresh-baked muffin with blueberries.",
                "category": "Pastry",
                "price": 3.0,
                "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=1200&q=80"
            },
            {
                "name": "Butter Croissant",
                "description": "Flaky croissant with butter layers.",
                "category": "Pastry",
                "price": 3.25,
                "image_url": "https://images.unsplash.com/photo-1509365465985-25d11c17e812?auto=format&fit=crop&w=1200&q=80"
            }
        ]

        for idx, item in enumerate(demo_items, start=1):
            cafe_item = CafeItem(
                tenant_id=tenant_id,
                name=item["name"],
                description=item.get("description"),
                category=item.get("category"),
                price=item["price"],
                image_url=item.get("image_url"),
                is_featured=item.get("is_featured", False),
                is_active=True
            ).model_dump()
            cafe_item["id"] = f"cafe_{tenant_id}_{idx}"
            await db.cafe_items.update_one({"id": cafe_item["id"]}, {"$set": cafe_item}, upsert=True)

    order_count = await db.cafe_orders.count_documents({"tenant_id": tenant_id})
    if order_count == 0:
        member = await db.users.find_one({"tenant_id": tenant_id, "role": "member"}, {"_id": 0})
        if member:
            items = await db.cafe_items.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(10)
            if items:
                for i in range(4):
                    item = random.choice(items)
                    quantity = random.randint(1, 2)
                    total = round(item["price"] * quantity, 2)
                    order = {
                        "id": str(uuid.uuid4()),
                        "tenant_id": tenant_id,
                        "user_id": member.get("user_id"),
                        "items": [{
                            "item_id": item["id"],
                            "name": item["name"],
                            "price": item["price"],
                            "quantity": quantity,
                            "image_url": item.get("image_url")
                        }],
                        "pickup_time": "Sunday 9:15 AM",
                        "notes": "",
                        "total": total,
                        "status": "placed",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.cafe_orders.update_one({"id": order["id"]}, {"$set": order}, upsert=True)
