"""
Push notification routes for Solomon AI PWA.
"""
from fastapi import APIRouter, Request, HTTPException
from pywebpush import webpush, WebPushException
from datetime import datetime, timezone
import json
import os

from database import db
from auth import get_current_user

router = APIRouter(prefix="/push", tags=["push"])

VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "mailto:admin@solomon.ai")


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    return {"public_key": VAPID_PUBLIC_KEY}


@router.post("/subscribe")
async def push_subscribe(request: Request):
    """Store a push subscription for the authenticated user."""
    user = await get_current_portal_user(request)
    body = await request.json()
    subscription = body.get("subscription")
    if not subscription or not subscription.get("endpoint"):
        raise HTTPException(status_code=400, detail="Invalid subscription")

    await db.push_subscriptions.update_one(
        {"endpoint": subscription["endpoint"]},
        {"$set": {
            "subscription": subscription,
            "user_id": user.get("id", ""),
            "tenant_id": user.get("tenant_id", ""),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    return {"status": "subscribed"}


@router.delete("/subscribe")
async def push_unsubscribe(request: Request):
    """Remove a push subscription."""
    user = await get_current_portal_user(request)
    body = await request.json()
    endpoint = body.get("endpoint", "")
    if endpoint:
        await db.push_subscriptions.delete_one({"endpoint": endpoint})
    return {"status": "unsubscribed"}


async def send_push_notification(user_id: str, tenant_id: str, title: str, body: str, url: str = "/portal"):
    """Send push notification to all subscriptions for a user."""
    if not VAPID_PRIVATE_KEY:
        return

    subs = await db.push_subscriptions.find(
        {"user_id": user_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(50)

    payload = json.dumps({"title": title, "body": body, "url": url})

    for sub in subs:
        try:
            webpush(
                subscription_info=sub["subscription"],
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIMS_EMAIL}
            )
        except WebPushException:
            await db.push_subscriptions.delete_one({"endpoint": sub["subscription"]["endpoint"]})
        except Exception:
            pass
