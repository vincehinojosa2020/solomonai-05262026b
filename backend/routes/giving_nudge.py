"""
Giving nudge route for Solomon AI — contextual giving prompts.
"""
from fastapi import APIRouter, Request
from database import db, DEFAULT_TENANT_ID
from auth import get_current_member_user

router = APIRouter()


@router.get("/portal/giving/nudge")
async def get_giving_nudge(request: Request, context: str = "general"):
    user = await get_current_member_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    nudges = {
        "cafe": {
            "title": "Give While You Sip",
            "message": "Enjoying your coffee? Your generosity fuels our mission. Consider a quick gift today!",
            "suggested_amounts": [5, 10, 25],
            "cta": "Give Now"
        },
        "merch": {
            "title": "Give While You Shop",
            "message": "Love the merch? Your giving helps us reach more people in our community.",
            "suggested_amounts": [10, 25, 50],
            "cta": "Give Now"
        },
        "general": {
            "title": "Give While You're Here",
            "message": "Your generosity makes everything we do possible. Every gift, big or small, makes an impact.",
            "suggested_amounts": [10, 25, 50, 100],
            "cta": "Give Now"
        }
    }

    nudge = nudges.get(context, nudges["general"])

    ytd = await db.donations.find(
        {"tenant_id": tenant_id, "person_id": user.get("user_id")},
        {"_id": 0, "amount": 1}
    ).to_list(500)
    ytd_total = sum(d.get("amount", 0) for d in ytd)

    nudge["ytd_giving"] = round(ytd_total, 2)
    nudge["giving_url"] = "/portal/giving"
    return {"nudge": nudge}
