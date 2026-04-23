"""Solomon AI — Competitive Intel Module (God Mode).

Lets the platform CEO pin up to 5 target churches from a curated list of
200+ top US churches and see a Claude-generated "what changed" digest next
to live performance data pulled from Solomon Pay.

Endpoints (all require platform_admin):

    POST   /api/admin/competitive/seed            — (re)seed the catalog from the shipped JSON list
    GET    /api/admin/competitive/top-churches    — search/filter the catalog
    GET    /api/admin/competitive/pins            — current pinned competitors
    POST   /api/admin/competitive/pins            — pin a church (max 5)
    DELETE /api/admin/competitive/pins/{rank}     — unpin
    POST   /api/admin/competitive/digest          — generate a Claude digest for a specific church
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db, get_session_token_from_request
from data.top_churches_seed import TOP_CHURCHES

logger = logging.getLogger("solomon.competitive_intel")
router = APIRouter()

MAX_PINS = 5


# ─── Auth helper ────────────────────────────────────────────────────────────
async def _require_platform_admin(request: Request) -> dict:
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")
    return user


# ─── Models ─────────────────────────────────────────────────────────────────
class PinRequest(BaseModel):
    rank: int = Field(..., description="Rank / ID of the church in the top-churches catalog")


class DigestRequest(BaseModel):
    rank: int
    notes: Optional[str] = Field(None, description="Extra context or URL the CEO wants Claude to factor in")


# ─── Seed ───────────────────────────────────────────────────────────────────
@router.post("/admin/competitive/seed")
async def seed_catalog(request: Request):
    """Upsert the shipped top-churches list into `competitor_churches`.
    Safe to call repeatedly — each rank is the stable key."""
    await _require_platform_admin(request)
    for entry in TOP_CHURCHES:
        await db.competitor_churches.update_one(
            {"rank": entry["rank"]},
            {"$set": {**entry, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    total = await db.competitor_churches.count_documents({})
    return {"seeded": len(TOP_CHURCHES), "total_in_catalog": total}


# ─── Search catalog ─────────────────────────────────────────────────────────
@router.get("/admin/competitive/top-churches")
async def list_top_churches(
    request: Request,
    q: Optional[str] = None,
    vendor: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    await _require_platform_admin(request)
    query: dict = {}
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"city": {"$regex": q, "$options": "i"}},
            {"state": {"$regex": q, "$options": "i"}},
        ]
    if vendor:
        query["vendor"] = vendor
    total = await db.competitor_churches.count_documents(query)
    rows = await db.competitor_churches.find(query, {"_id": 0}).sort("rank", 1).skip(skip).limit(min(limit, 200)).to_list(limit)

    # Vendor breakdown for the filter sidebar
    vendor_pipe = [{"$group": {"_id": "$vendor", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    vendors = await db.competitor_churches.aggregate(vendor_pipe).to_list(None)
    return {
        "total": total,
        "churches": rows,
        "vendors": [{"name": v["_id"] or "Unknown", "count": v["count"]} for v in vendors],
    }


# ─── Pins ───────────────────────────────────────────────────────────────────
async def _load_pins(user_id: str) -> list:
    rows = await db.competitor_pins.find({"user_id": user_id}, {"_id": 0}).sort("pinned_at", 1).to_list(MAX_PINS)
    # Attach the catalog entry for each pin
    ranks = [r["rank"] for r in rows]
    catalog = await db.competitor_churches.find({"rank": {"$in": ranks}}, {"_id": 0}).to_list(None)
    by_rank = {c["rank"]: c for c in catalog}
    for r in rows:
        r["church"] = by_rank.get(r["rank"])
    return rows


@router.get("/admin/competitive/pins")
async def list_pins(request: Request):
    user = await _require_platform_admin(request)
    pins = await _load_pins(user["user_id"])
    return {"pins": pins, "max": MAX_PINS}


@router.post("/admin/competitive/pins")
async def pin_church(request: Request, body: PinRequest):
    user = await _require_platform_admin(request)
    count = await db.competitor_pins.count_documents({"user_id": user["user_id"]})
    already = await db.competitor_pins.find_one({"user_id": user["user_id"], "rank": body.rank})
    if already:
        raise HTTPException(409, "Already pinned")
    if count >= MAX_PINS:
        raise HTTPException(400, f"Pin limit reached ({MAX_PINS}). Unpin one first.")
    church = await db.competitor_churches.find_one({"rank": body.rank}, {"_id": 0})
    if not church:
        raise HTTPException(404, "Church not found in catalog")
    pin = {
        "id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        "rank": body.rank,
        "pinned_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.competitor_pins.insert_one(pin)
    return {"pin": {k: v for k, v in pin.items() if k != "_id"}, "church": church}


@router.delete("/admin/competitive/pins/{rank}")
async def unpin_church(request: Request, rank: int):
    user = await _require_platform_admin(request)
    res = await db.competitor_pins.delete_one({"user_id": user["user_id"], "rank": rank})
    if res.deleted_count == 0:
        raise HTTPException(404, "Pin not found")
    return {"unpinned": rank}


# ─── Claude digest ─────────────────────────────────────────────────────────
@router.post("/admin/competitive/digest")
async def generate_digest(request: Request, body: DigestRequest):
    """Ask Claude Sonnet 4.5 for a 'what changed' strategic digest on a
    specific pinned competitor. The digest is cached on the pin so it
    survives refresh and doesn't re-bill the LLM on every page load."""
    user = await _require_platform_admin(request)
    church = await db.competitor_churches.find_one({"rank": body.rank}, {"_id": 0})
    if not church:
        raise HTTPException(404, "Church not found in catalog")

    from emergentintegrations.llm.chat import LlmChat, UserMessage
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(500, "Claude is not configured (EMERGENT_LLM_KEY missing)")

    chat = LlmChat(
        api_key=api_key,
        session_id=f"comp-intel-{body.rank}-{uuid.uuid4().hex[:8]}",
        system_message=(
            "You are Solomon AI's competitive-intel analyst for a church-tech SaaS platform. "
            "Your role is to help the CEO understand each pinned church as an acquisition target. "
            "Be terse, high-signal, and strategic. Use markdown headings. No fluff. "
            "Each answer ends with '**Recommended next action**' — one concrete sales play."
        ),
    )
    chat.with_model("anthropic", "claude-sonnet-4-5-20250929")

    prompt = f"""Target church profile:

- Name: {church.get('name')}
- Location: {church.get('city')}, {church.get('state')}, {church.get('country')}
- Denomination: {church.get('denomination') or 'Non-denominational'}
- Est. weekly attendance: {church.get('attendance')}
- Current giving platform: {church.get('vendor') or 'Unknown'}
- Seed note: {church.get('notes') or 'N/A'}

Additional context from the CEO (optional):
{body.notes or '(none)'}

Generate a strategic one-pager with these sections:

### 1. Why this church matters
One sentence — the money case.

### 2. Current-vendor weak spots
Three bullets tailored to their current platform ({church.get('vendor') or 'Unknown'}). Focus on pain the pastor feels.

### 3. Solomon's differentiated pitch
Three bullets. Lean on: 0.35% platform fee, AI pastoral workflows, modern embedded Stripe Elements, instant payouts.

### 4. Likely decision makers
Name roles (not people), phrased as who to meet.

### 5. Best time to reach out
One sentence — based on church calendar rhythm (giving cycle, year-end, Easter, etc.)

**Recommended next action**
One concrete 48-hour play."""

    try:
        digest = await chat.send_message(UserMessage(text=prompt))
    except Exception as e:
        logger.error("Claude digest failed for rank=%s: %s", body.rank, e)
        raise HTTPException(502, f"Claude digest failed: {e}")

    saved_at = datetime.now(timezone.utc).isoformat()
    await db.competitor_pins.update_one(
        {"user_id": user["user_id"], "rank": body.rank},
        {"$set": {"last_digest": digest, "last_digest_at": saved_at, "last_digest_notes": body.notes}},
        upsert=False,
    )
    return {"rank": body.rank, "digest": digest, "generated_at": saved_at}
