"""Solomon AI — Disputes & Fraud Risk Scaffold (Stripe Parity)"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
import uuid
import logging

from core import db, get_session_token_from_request, logger

router = APIRouter()


def _auth_platform_admin(session_token, session, user):
    """Validate platform admin auth chain."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")


@router.get("/platform/disputes")
async def get_disputes(request: Request, page: int = 1, limit: int = 20, status: str = ""):
    """List payment disputes/chargebacks — scaffold with seeded demo data."""
    session_token = get_session_token_from_request(request)
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0}) if session_token else None
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0}) if session else None
    _auth_platform_admin(session_token, session, user)

    query = {}
    if status:
        query["status"] = status

    total = await db.disputes.count_documents(query)
    skip = (page - 1) * limit
    disputes = await db.disputes.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    if not disputes and total == 0:
        # Return demo scaffold data
        return {
            "disputes": [],
            "total": 0,
            "page": page,
            "pages": 0,
            "summary": {
                "open": 0,
                "won": 0,
                "lost": 0,
                "total_amount_disputed": 0,
                "win_rate": 100.0,
            },
            "message": "No disputes recorded. This is expected for a new platform."
        }

    summary_pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total": {"$sum": "$amount"},
        }}
    ]
    summary_raw = await db.disputes.aggregate(summary_pipeline).to_list(10)
    summary_map = {s["_id"]: s for s in summary_raw}

    return {
        "disputes": disputes,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "summary": {
            "open": summary_map.get("open", {}).get("count", 0),
            "won": summary_map.get("won", {}).get("count", 0),
            "lost": summary_map.get("lost", {}).get("count", 0),
            "total_amount_disputed": round(sum(s.get("total", 0) for s in summary_raw), 2),
            "win_rate": round(
                summary_map.get("won", {}).get("count", 0) /
                max(sum(s.get("count", 0) for s in summary_raw), 1) * 100, 1
            ),
        }
    }


@router.get("/platform/fraud/risk-scores")
async def get_fraud_risk_scores(request: Request):
    """Fraud risk scoring scaffold — returns risk categorization of recent transactions."""
    session_token = get_session_token_from_request(request)
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0}) if session_token else None
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0}) if session else None
    _auth_platform_admin(session_token, session, user)

    # Scaffold: compute basic risk indicators from donation patterns
    now = datetime.now(timezone.utc)
    thirty_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    # High-value transactions in last 30 days (>$5000)
    high_value = await db.donations.count_documents({
        "amount": {"$gte": 5000},
        "donation_date": {"$gte": thirty_ago}
    })

    # Rapid-fire: more than 5 donations from same person in one day
    rapid_fire_pipeline = [
        {"$match": {"donation_date": {"$gte": thirty_ago}}},
        {"$group": {
            "_id": {"person": "$person_id", "date": "$donation_date"},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gte": 5}}},
        {"$count": "flagged"}
    ]
    rapid_result = await db.donations.aggregate(rapid_fire_pipeline).to_list(1)
    rapid_fire = rapid_result[0]["flagged"] if rapid_result else 0

    return {
        "risk_summary": {
            "overall_risk": "low",
            "high_value_transactions_30d": high_value,
            "rapid_fire_alerts": rapid_fire,
            "flagged_accounts": 0,
            "chargeback_rate": "0.00%",
        },
        "risk_rules": [
            {"rule": "High-value transaction (>$5,000)", "triggers_30d": high_value, "severity": "medium"},
            {"rule": "Rapid-fire donations (5+ same day)", "triggers_30d": rapid_fire, "severity": "high"},
            {"rule": "New card + large donation", "triggers_30d": 0, "severity": "high"},
            {"rule": "International card usage", "triggers_30d": 0, "severity": "low"},
        ],
        "message": "Fraud risk scoring is scaffold-level. Full Stripe Radar integration coming with production payment processing."
    }


@router.post("/platform/disputes/{dispute_id}/respond")
async def respond_to_dispute(request: Request, dispute_id: str):
    """Respond to a dispute (scaffold — would submit evidence to Stripe in production)."""
    session_token = get_session_token_from_request(request)
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0}) if session_token else None
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0}) if session else None
    _auth_platform_admin(session_token, session, user)

    body = await request.json()
    evidence = body.get("evidence", "")

    dispute = await db.disputes.find_one({"id": dispute_id}, {"_id": 0})
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    await db.disputes.update_one(
        {"id": dispute_id},
        {"$set": {
            "status": "under_review",
            "evidence_submitted": evidence,
            "responded_at": datetime.now(timezone.utc).isoformat(),
            "responded_by": user.get("user_id"),
        }}
    )

    return {"success": True, "message": "Evidence submitted. In production, this would be forwarded to Stripe for review."}
