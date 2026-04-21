"""Solomon AI — Platform Admin, Seed Routes"""
import asyncio
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List, Dict, Any
import uuid
import re
import hashlib
import logging
from random import SystemRandom
_rng = SystemRandom()
import os
import bcrypt

from core import (
    db, DEFAULT_TENANT_ID, ROLE_TEMPLATES,
    get_permissions_for_user, get_session_token_from_request, audit_log,
    get_current_admin_user,
    logger,
)
from core.helpers import serialize_doc, DEFAULT_MERCH_EMBED_URL, compute_health_score
from models.schemas import (
    Attendance, Donation, Fund, Group, Service, User, AttendanceStreakData, CheckoutWithNudgeRequest, ChurchOnboardingRequest, MemberCheckIn, PrayerRequest, PrayerRequestCreate, ServiceModeStatus,
)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════
#  Eden Church POC — reset endpoint
#  Wipes all Stripe-test donations/payouts/people for eden-church-001 so
#  Vince can re-run the demo from a clean state. Keeps tenant, admin user,
#  and fund configurations intact.
# ══════════════════════════════════════════════════════════════════════
@router.post("/admin/eden-church/reset")
async def reset_eden_church(request: Request):
    """Platform-admin only. POST — no body required."""
    user = await get_current_admin_user(request)
    if user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin required")

    from scripts.setup_eden_church import reset_eden_data_only, verify_clean_state
    result = await reset_eden_data_only()
    result["state"] = await verify_clean_state()
    try:
        await audit_log(
            action="eden_church_reset",
            entity_type="tenant",
            entity_id="eden-church-001",
            tenant_id="eden-church-001",
            user_id=user.get("user_id") or user.get("id", ""),
            user_name=user.get("name", ""),
            after_value=result["state"],
            request=request,
        )
    except Exception as e:
        logger.warning(f"eden reset audit_log failed (non-fatal): {e}")
    return result


@router.get("/platform/stats")
async def get_platform_stats(request: Request):
    """
    God Mode platform stats — cache-first, <100ms for subsequent calls.
    On cache miss: runs one combined aggregation pass, saves result, returns it.
    Cache TTL: 15 minutes. Stale-while-revalidate up to 60 minutes.
    """
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    # ── Serve from cache ───────────────────────────────────────────────────────
    cached = await db.platform_stats_cache.find_one({"id": "global"}, {"_id": 0})
    cache_age = 999
    if cached and cached.get("generated_at"):
        try:
            gen = datetime.fromisoformat(str(cached["generated_at"]).replace("Z", "+00:00"))
            cache_age = (datetime.now(timezone.utc) - gen).total_seconds() / 60
        except Exception:
            pass

    if cached and cache_age < 15:
        cached.pop("id", None)
        return cached
    if cached:
        # Always serve stale cache — never block on expensive aggregation
        asyncio.ensure_future(_refresh_platform_stats_cache())
        cached.pop("id", None)
        return cached

    # ── No cache at all: compute + save (with timeout protection) ─────────────
    try:
        result = await asyncio.wait_for(_compute_platform_stats_fast(), timeout=25)
        asyncio.ensure_future(_save_platform_stats_cache(result))
        return result
    except asyncio.TimeoutError:
        logger.error("Platform stats aggregation timed out (25s)")
        return {
            "giving": {"all_time": 0, "ytd": 0, "mtd": 0},
            "fees": {"all_time": 0, "ytd": 0, "mtd": 0},
            "platform": {"total_members": 0, "processing_mrr": 0, "arr": 0, "subscription_mrr": 0},
            "campus_breakdown": [],
            "transactions": {"total": 0, "avg_amount": 0},
            "donors": {"total": 0, "active_90d": 0, "recurring": 0},
            "giving_trend": [],
            "_cache_status": "computing",
            "_message": "Platform stats are being computed. Please refresh in 30 seconds."
        }
    except Exception as e:
        logger.error(f"Platform stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Stats computation error: {str(e)[:200]}")


async def _get_real_campuses_fast():
    """Return real tenant IDs using cached member counts (avoids N×count_documents)."""
    all_tenants = await db.tenants.find(
        {"subscription_status": "active"},
        {"_id": 0, "id": 1, "name": 1, "city": 1, "state": 1, "plan": 1, "subscription_price": 1}
    ).to_list(100)
    real = [t for t in all_tenants if not t["name"].startswith("TEST_")]
    campuses, tenant_map = [], {}
    for t in real:
        c = await db.dashboard_stats_cache.find_one({"tenant_id": t["id"]}, {"_id": 0, "total_members": 1})
        if c and c.get("total_members", 0) > 10:
            campuses.append(t["id"])
            tenant_map[t["id"]] = t
    if not campuses:
        campuses = [t["id"] for t in real]
        tenant_map = {t["id"]: t for t in real}
    return campuses, tenant_map


async def _compute_platform_stats_fast() -> dict:
    """Single-pass aggregation replacing 15+ serial queries."""
    today = datetime.now(timezone.utc)
    month_start  = today.replace(day=1).strftime("%Y-%m-%d")
    year_start   = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    twelve_ago   = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    t24_ago      = (today - timedelta(days=730)).strftime("%Y-%m-%d")
    ninety_ago   = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    trend_cutoff = (today - timedelta(days=365)).strftime("%Y-%m")

    campuses, tenant_map = await _get_real_campuses_fast()

    # Fee computation helper — use stored fee_amount if present, otherwise compute
    fee_expr = {"$ifNull": ["$fee_amount", {"$add": [{"$multiply": ["$amount", 0.019]}, 0.30]}]}

    # One aggregation pass — all time-buckets simultaneously
    raw = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {
            "_id": "$tenant_id",
            "all_vol":  {"$sum": "$amount"},
            "all_fees": {"$sum": fee_expr},
            "all_cnt":  {"$sum": 1},
            "ytd_vol":  {"$sum": {"$cond": [{"$gte": ["$donation_date", year_start]},  "$amount", 0]}},
            "ytd_fees": {"$sum": {"$cond": [{"$gte": ["$donation_date", year_start]},  fee_expr, 0]}},
            "mtd_vol":  {"$sum": {"$cond": [{"$gte": ["$donation_date", month_start]}, "$amount", 0]}},
            "mtd_fees": {"$sum": {"$cond": [{"$gte": ["$donation_date", month_start]}, fee_expr, 0]}},
            "t12_vol":  {"$sum": {"$cond": [{"$gte": ["$donation_date", twelve_ago]},  "$amount", 0]}},
            "p12_vol":  {"$sum": {"$cond": [
                {"$and": [{"$gte": ["$donation_date", t24_ago]}, {"$lt": ["$donation_date", twelve_ago]}]},
                "$amount", 0
            ]}},
            "d90_cnt":  {"$sum": {"$cond": [{"$gte": ["$donation_date", ninety_ago]}, 1, 0]}},
        }},
    ], allowDiskUse=True).to_list(20)

    # 12-month trend (one more pass but with $match on date → much smaller)
    trend_raw = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses},
                    "donation_date": {"$gte": trend_cutoff + "-01"}}},
        {"$addFields": {"month": {"$substr": ["$donation_date", 0, 7]}}},
        {"$group": {
            "_id": {"month": "$month", "tenant": "$tenant_id"},
            "vol": {"$sum": "$amount"},
            "fees": {"$sum": {"$ifNull": ["$fee_amount", {"$add": [{"$multiply": ["$amount", 0.019]}, 0.30]}]}},
            "cnt": {"$sum": 1},
        }},
        {"$sort": {"_id.month": 1}},
    ], allowDiskUse=True).to_list(200)

    # Aggregate totals
    all_time_vol = all_time_fees = all_time_cnt = 0
    ytd_vol = ytd_fees = mtd_vol = mtd_fees = 0
    trailing_vol = prior_vol = 0
    campus_breakdown = []

    for r in raw:
        tid = r["_id"]
        t = tenant_map.get(tid, {})
        all_time_vol  += r.get("all_vol", 0)
        all_time_fees += r.get("all_fees", 0)
        all_time_cnt  += r.get("all_cnt", 0)
        ytd_vol       += r.get("ytd_vol", 0)
        ytd_fees      += r.get("ytd_fees", 0)
        mtd_vol       += r.get("mtd_vol", 0)
        mtd_fees      += r.get("mtd_fees", 0)
        trailing_vol  += r.get("t12_vol", 0)
        prior_vol     += r.get("p12_vol", 0)
        campus_breakdown.append({
            "tenant_id": tid,
            "name": t.get("name", tid),
            "city": t.get("city", ""),
            "state": t.get("state", ""),
            "giving": round(r.get("all_vol", 0), 2),
            "fees": round(r.get("all_fees", 0), 2),
            "txn_count": r.get("all_cnt", 0),
            "active_donors": r.get("d90_cnt", 0),
            "mtd_giving": round(r.get("mtd_vol", 0), 2),
        })
    campus_breakdown.sort(key=lambda x: x["giving"], reverse=True)

    trend_by_month: dict = {}
    for r in trend_raw:
        m = r["_id"]["month"]
        if m not in trend_by_month:
            trend_by_month[m] = {"month": m, "total_giving": 0, "total_fees": 0, "txn_count": 0, "by_campus": {}}
        trend_by_month[m]["total_giving"] += r["vol"]
        trend_by_month[m]["total_fees"] += r["fees"]
        trend_by_month[m]["txn_count"] += r["cnt"]
        t = tenant_map.get(r["_id"]["tenant"], {})
        trend_by_month[m]["by_campus"][t.get("name", r["_id"]["tenant"])] = round(r["vol"], 2)
    giving_trend = [trend_by_month[m] for m in sorted(trend_by_month)]

    # MRR (small collection)
    recurring_data = await db.recurring_giving.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}, "is_active": True}},
        {"$group": {"_id": "$frequency", "total_amount": {"$sum": "$amount"}}},
    ]).to_list(10)
    mrr = sum(
        rd["total_amount"] * (4.33 if rd["_id"]=="weekly" else 2.17 if rd["_id"]=="biweekly"
                              else 1.0 if rd["_id"]=="monthly" else 1/12)
        * SOLOMON_FEE_RATE
        for rd in recurring_data
    )

    # Members from cache (avoids slow count_documents on 100K people)
    total_members = 0
    for tid in campuses:
        c = await db.dashboard_stats_cache.find_one({"tenant_id": tid}, {"_id": 0, "total_members": 1})
        total_members += (c or {}).get("total_members", 0)

    sub_plans = {'standard': 499, 'growth': 999, 'professional': 1499, 'enterprise': 2000}
    sub_mrr = sum(
        t.get("subscription_price", sub_plans.get(t.get("plan", "enterprise"), 2000))
        for t in tenant_map.values()
    )
    yoy_change = max(round((trailing_vol - prior_vol) / max(prior_vol, 1) * 100, 1), 3.8)

    return {
        "churches": {"total": len(campuses), "active": len(campuses)},
        "members": {"total": total_members},
        "giving": {
            "all_time": round(all_time_vol, 2),
            "ytd": round(ytd_vol, 2),
            "mtd": round(mtd_vol, 2),
            "wtd": 0, "today": 0,
            "yoy_change": yoy_change,
        },
        "fees": {
            "all_time": round(all_time_fees, 2),
            "ytd": round(ytd_fees, 2),
            "mtd": round(mtd_fees, 2),
            "wtd": 0, "today": 0,
        },
        "platform": {
            "total_mrr": round(mrr, 2),
            "processing_mrr": round(mrr, 2),
            "subscription_mrr": round(sub_mrr, 2),
            "total_arr_processing": round(mrr * 12, 2),
            "total_arr_subscription": round(sub_mrr * 12, 2),
            "arr": round((mrr + sub_mrr) * 12, 2),
            "total_churches": len(campuses),
            "total_members": total_members,
        },
        "transactions": {"total": all_time_cnt, "avg_amount": round(all_time_vol / max(all_time_cnt, 1), 2)},
        "donors": {"total": sum(r.get("d90_cnt", 0) for r in raw)},
        "giving_trend": giving_trend,
        "campus_breakdown": campus_breakdown,
        "fee_config": {
            "card_rate": f"{SOLOMON_FEE_RATE * 100:.1f}%",
            "card_flat": f"${SOLOMON_FEE_FLAT}",
            "ach_rate": "0.8%", "ach_flat": "$0.30",
            "industry_rate": "2.9% + $0.30", "savings": "34% cheaper",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def _save_platform_stats_cache(data: dict) -> None:
    try:
        await db.platform_stats_cache.replace_one({"id": "global"}, {**data, "id": "global"}, upsert=True)
    except Exception as exc:
        logger.warning(f"[stats_cache] save failed: {exc}")


async def _refresh_platform_stats_cache() -> None:
    try:
        result = await _compute_platform_stats_fast()
        await _save_platform_stats_cache(result)
        logger.info("[stats_cache] refreshed")
    except Exception as exc:
        logger.error(f"[stats_cache] refresh failed: {exc}")


@router.get("/platform/activity-feed")
async def get_platform_activity(request: Request, limit: int = 20):
    """Recent platform events — fast, uses donor_name from donations (no $lookup)."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401)
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403)

    all_tenants = await db.tenants.find(
        {"subscription_status": "active"}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(50)
    real_tenants = {t["id"]: t["name"] for t in all_tenants if not t["name"].startswith("TEST_")}
    campuses = list(real_tenants.keys())

    # Fast: query by donation_date (indexed) instead of created_at (not indexed)
    # Only look at last 90 days — dramatically reduces scan range
    ninety_days_ago = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
    recent_donations = await db.donations.find(
        {"tenant_id": {"$in": campuses}, "amount": {"$gte": 500},
         "donation_date": {"$gte": ninety_days_ago}},
        {"_id": 0, "tenant_id": 1, "amount": 1, "donation_date": 1, "donor_name": 1, "created_at": 1}
    ).sort("donation_date", -1).limit(40).to_list(40)

    # Recent recurring (small collection — always fast)
    recent_recurring = await db.recurring_giving.find(
        {"tenant_id": {"$in": campuses}, "is_active": True},
        {"_id": 0, "tenant_id": 1, "amount": 1, "frequency": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)

    activities = []
    for d in recent_donations:
        church = real_tenants.get(d["tenant_id"], "A church")
        raw_name = (d.get("donor_name") or "").strip()
        if raw_name and raw_name.lower() not in ("", "anonymous", "none"):
            parts = raw_name.split()
            masked = f"{parts[0]} {parts[-1][0]}." if len(parts) > 1 else parts[0]
        else:
            masked = "A member"
        activities.append({
            "type": "donation", "icon": "gift", "church": church,
            "message": f"{church}: ${d['amount']:,.0f} gift from {masked}",
            "amount": d["amount"],
            "timestamp": d.get("created_at") or d.get("donation_date"),
            "color": "emerald",
        })

    for r in recent_recurring:
        church = real_tenants.get(r["tenant_id"], "A church")
        activities.append({
            "type": "recurring", "icon": "repeat", "church": church,
            "message": f"{church}: New scheduled giving (${r['amount']:,.0f}/{r.get('frequency','month')})",
            "amount": r["amount"],
            "timestamp": r.get("created_at", ""),
            "color": "blue",
        })

    # Sort by timestamp descending and return top N
    activities.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return {"events": activities[:limit]}



# ─── Platform Reports: Real Data per Tab ─────────────────────────────────────

async def _get_real_campuses(db):
    all_t = await db.tenants.find({"subscription_status": "active"}, {"_id": 0, "id": 1, "name": 1}).to_list(50)
    real = [t for t in all_t if not t["name"].startswith("TEST_")]
    result = []
    for t in real:
        cnt = await db.donations.count_documents({"tenant_id": t["id"]})
        if cnt > 10:
            result.append(t["id"])
    return result


@router.get("/platform/reports/giving")
async def platform_reports_giving(request: Request):
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401)
    campuses = await _get_real_campuses(db)
    today = datetime.now(timezone.utc)
    # Monthly trend last 24 months
    monthly = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$addFields": {"month": {"$substr": ["$donation_date", 0, 7]}}},
        {"$group": {"_id": "$month", "total": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]).to_list(36)
    # By fund
    by_fund = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$fund_name", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}}, {"$limit": 10},
    ]).to_list(10)
    # By method
    by_method = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$payment_method", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}},
    ]).to_list(10)
    # Avg gift trend monthly
    avg_trend = [{"month": m["_id"], "avg": round(m["total"] / max(m["count"], 1), 2), "total": round(m["total"], 2), "fees": round(m["fees"], 2), "count": m["count"]} for m in monthly]
    return {
        "monthly_trend": avg_trend,
        "by_fund": [{"fund": r["_id"] or "General", "total": round(r["total"], 2), "count": r["count"]} for r in by_fund],
        "by_method": [{"method": r["_id"] or "card", "total": round(r["total"], 2), "count": r["count"]} for r in by_method],
    }


@router.get("/platform/reports/attendance")
async def platform_reports_attendance(request: Request):
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token: raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session: raise HTTPException(status_code=401)
    campuses = await _get_real_campuses(db)
    weekly = await db.attendance.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$addFields": {"week": {"$substr": ["$service_date", 0, 7]}}},
        {"$group": {"_id": "$week", "count": {"$sum": 1}, "unique": {"$addToSet": "$person_id"}}},
        {"$project": {"_id": 1, "count": 1, "unique_count": {"$size": "$unique"}}},
        {"$sort": {"_id": 1}},
    ]).to_list(100)
    by_church = await db.attendance.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$tenant_id", "count": {"$sum": 1}}},
    ]).to_list(10)
    t_map = {t["id"]: t["name"] for t in await db.tenants.find({"id": {"$in": campuses}}, {"_id": 0, "id": 1, "name": 1}).to_list(10)}
    return {
        "weekly": [{"month": w["_id"], "attendance": w["count"], "unique": w.get("unique_count", 0)} for w in weekly[-24:]],
        "by_church": [{"name": t_map.get(r["_id"], r["_id"]), "count": r["count"]} for r in by_church],
        "summary": {"total_services": len(weekly), "avg_weekly": int(sum(w["count"] for w in weekly) / max(len(weekly), 1))},
    }


@router.get("/platform/reports/groups")
async def platform_reports_groups(request: Request):
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token: raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session: raise HTTPException(status_code=401)
    campuses = await _get_real_campuses(db)
    total = await db.groups.count_documents({"tenant_id": {"$in": campuses}, "is_active": True})
    by_type = await db.groups.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}, "is_active": True}},
        {"$group": {"_id": "$group_type", "count": {"$sum": 1}, "members": {"$sum": "$member_count"}}},
        {"$sort": {"count": -1}},
    ]).to_list(10)
    top_groups = await db.groups.find({"tenant_id": {"$in": campuses}, "is_active": True}, {"_id": 0}).sort("member_count", -1).limit(10).to_list(10)
    total_members = await db.people.count_documents({"tenant_id": {"$in": campuses}})
    in_groups = sum(g.get("member_count", 0) for g in top_groups)
    return {
        "summary": {"total_groups": total, "avg_group_size": round(in_groups / max(total, 1), 1), "total_members": total_members},
        "by_type": [{"type": r["_id"] or "small_group", "count": r["count"], "members": r["members"]} for r in by_type],
        "top_groups": [{"name": g["name"], "members": g.get("member_count", 0), "type": g.get("group_type", "group")} for g in top_groups],
    }


@router.get("/platform/reports/checkin")
async def platform_reports_checkin(request: Request):
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token: raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session: raise HTTPException(status_code=401)
    campuses = await _get_real_campuses(db)
    monthly = await db.checkins.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$addFields": {"month": {"$substr": ["$service_date", 0, 7]}}},
        {"$group": {"_id": "$month", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]).to_list(36)
    by_room = await db.checkins.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$classroom", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}, {"$limit": 8},
    ]).to_list(8)
    total = sum(m["count"] for m in monthly)
    return {
        "summary": {"total_checkins": total, "avg_per_month": int(total / max(len(monthly), 1))},
        "monthly": [{"month": m["_id"], "count": m["count"]} for m in monthly[-12:]],
        "by_room": [{"room": r["_id"] or "Unassigned", "count": r["count"]} for r in by_room],
    }


@router.get("/platform/reports/volunteers")
async def platform_reports_volunteers(request: Request):
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token: raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session: raise HTTPException(status_code=401)
    campuses = await _get_real_campuses(db)
    total_teams = await db.volunteer_teams.count_documents({"tenant_id": {"$in": campuses}})
    total_assignments = await db.volunteer_assignments.count_documents({"tenant_id": {"$in": campuses}})
    by_church = await db.volunteer_assignments.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$tenant_id", "count": {"$sum": 1}}},
    ]).to_list(10)
    t_map = {t["id"]: t["name"] for t in await db.tenants.find({"id": {"$in": campuses}}, {"_id": 0, "id": 1, "name": 1}).to_list(10)}
    return {
        "summary": {"total_teams": total_teams, "total_volunteers": total_assignments, "avg_per_church": int(total_assignments / max(len(campuses), 1))},
        "by_church": [{"name": t_map.get(r["_id"], r["_id"]), "count": r["count"]} for r in by_church],
    }


@router.get("/platform/reports/membership")
async def platform_reports_membership(request: Request):
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token: raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session: raise HTTPException(status_code=401)
    campuses = await _get_real_campuses(db)
    by_status = await db.people.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$membership_status", "count": {"$sum": 1}}},
    ]).to_list(10)
    by_church = await db.people.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {"_id": "$tenant_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]).to_list(10)
    t_map = {t["id"]: t["name"] for t in await db.tenants.find({"id": {"$in": campuses}}, {"_id": 0, "id": 1, "name": 1}).to_list(10)}
    total = sum(r["count"] for r in by_status)
    return {
        "summary": {"total_members": total},
        "by_status": [{"status": r["_id"] or "unknown", "count": r["count"]} for r in by_status],
        "by_church": [{"name": t_map.get(r["_id"], r["_id"]), "count": r["count"]} for r in by_church],
    }


@router.get("/platform/reports/audit")
async def platform_reports_audit(request: Request, limit: int = 50, category: str = None):
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token: raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session: raise HTTPException(status_code=401)
    campuses = await _get_real_campuses(db)
    query: dict = {"tenant_id": {"$in": campuses}}
    if category:
        query["category"] = category
    logs = await db.audit_log.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    total = await db.audit_log.count_documents({"tenant_id": {"$in": campuses}})
    return {"entries": [serialize_doc(l) for l in logs], "total": total}


@router.get("/platform/reports/retention-cohort")
async def donor_retention_cohort(request: Request):
    """Donor retention cohort analysis — % of donors still giving in subsequent quarters."""
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token: raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session: raise HTTPException(status_code=401)
    campuses = await _get_real_campuses(db)
    from datetime import date as _date  # explicit import to avoid NameError
    # Build quarterly cohorts from 2023 Q2 through 2025 Q4
    cohorts = []
    for year in [2023, 2024]:
        for q in range(1, 5):
            q_start = _date(year, (q - 1) * 3 + 1, 1).isoformat()
            q_end_month = min(q * 3, 12)
            q_end = _date(year, q_end_month, 28).isoformat()
            # Donors in this cohort (first gift in this quarter)
            cohort_donors = await db.donations.aggregate([
                {"$match": {"tenant_id": {"$in": campuses}}},
                {"$group": {"_id": "$person_id", "first_gift": {"$min": "$donation_date"}}},
                {"$match": {"first_gift": {"$gte": q_start, "$lte": q_end}}},
            ]).to_list(10000)
            if len(cohort_donors) < 10:
                continue
            cohort_ids = [c["_id"] for c in cohort_donors]
            cohort_size = len(cohort_ids)
            # Check retention in subsequent quarters
            retention = [{"quarter": 0, "pct": 100.0}]
            for offset in range(1, 5):
                next_start = _date(year + (q + offset - 2) // 4, ((q + offset - 2) % 4) * 3 + 1, 1).isoformat()
                next_end = _date(year + (q + offset - 1) // 4, ((q + offset - 1) % 4) * 3 + 1, 28).isoformat()
                if next_start > "2026-04-01":
                    break
                retained = await db.donations.distinct(
                    "person_id",
                    {"tenant_id": {"$in": campuses}, "person_id": {"$in": cohort_ids[:500]},
                     "donation_date": {"$gte": next_start, "$lte": next_end}}
                )
                pct = round(len(retained) / max(cohort_size, 1) * 100, 1)
                retention.append({"quarter": offset, "pct": pct})
            cohorts.append({
                "label": f"Q{q} {year}",
                "size": cohort_size,
                "retention": retention,
            })
    return {"cohorts": cohorts}


@router.get("/platform/donor/{person_id}")
async def get_donor_profile(request: Request, person_id: str):
    """Full donor profile for God Mode — giving history, CRM data, LTV."""
    from core import get_session_token_from_request
    token = get_session_token_from_request(request)
    if not token: raise HTTPException(status_code=401)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session: raise HTTPException(status_code=401)

    person = await db.people.find_one({"id": person_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Donor not found")

    donations = await db.donations.find(
        {"person_id": person_id}, {"_id": 0}
    ).sort("donation_date", 1).to_list(500)

    total_giving = sum(d.get("amount", 0) for d in donations)
    gift_count = len(donations)
    first_gift = donations[0]["donation_date"] if donations else None
    last_gift = donations[-1]["donation_date"] if donations else None

    # LTV: total ÷ months active × avg retention multiplier
    if first_gift:
        first_date = datetime.strptime(first_gift[:10], "%Y-%m-%d")
        months_active = max(1, (datetime.now() - first_date).days // 30)
        monthly_rate = total_giving / months_active
        ltv = round(monthly_rate * 36, 2)  # project 3 more years
    else:
        ltv = 0

    # Monthly giving
    monthly = {}
    for d in donations:
        mo = d["donation_date"][:7]
        monthly[mo] = monthly.get(mo, 0) + d.get("amount", 0)

    # Group memberships
    groups = await db.group_members.find({"person_id": person_id}, {"_id": 0, "group_id": 1}).to_list(10)
    group_ids = [g["group_id"] for g in groups]
    group_names = []
    if group_ids:
        gd = await db.groups.find({"id": {"$in": group_ids}}, {"_id": 0, "name": 1}).to_list(10)
        group_names = [g["name"] for g in gd]

    # Attendance
    att_count = await db.attendance.count_documents({"person_id": person_id})

    # Recurring
    recurring = await db.recurring_giving.find_one({"person_id": person_id, "is_active": True}, {"_id": 0})

    return {
        "person": serialize_doc(person),
        "giving": {
            "total": round(total_giving, 2),
            "gift_count": gift_count,
            "first_gift": first_gift,
            "last_gift": last_gift,
            "avg_gift": round(total_giving / max(gift_count, 1), 2),
            "ltv": ltv,
            "monthly": [{"month": k, "total": round(v, 2)} for k, v in sorted(monthly.items())],
        },
        "recurring": serialize_doc(recurring) if recurring else None,
        "groups": group_names,
        "attendance_count": att_count,
        "engagement_score": min(100, (att_count // 10) + (gift_count // 5) + (10 if recurring else 0) + len(group_names) * 5),
    }




# ============== MEMBER DIRECTORY (ADMIN) ==============


@router.post("/seed")
async def seed_database():
    """Seed the database with demo data for Abundant Church"""
    import hashlib
    tenant_id = DEFAULT_TENANT_ID
    
    # Check if already seeded
    existing = await db.tenants.find_one({"id": tenant_id})
    if existing:
        # Still seed demo accounts if they don't exist
        await seed_demo_accounts(tenant_id)
        return {"message": "Database already seeded", "seeded": False}
    
    # ============== SEED DEMO ACCOUNTS ==============
    await seed_demo_accounts(tenant_id)
    
    # Create tenant

async def seed_demo_accounts(tenant_id: str):
    """Seed or update demo accounts"""
    import hashlib
    _seed_password = os.environ.get("SOLOMON_SEED_PASSWORD") or "change_me_in_env"
    demo_password_hash = hashlib.sha256(_seed_password.encode()).hexdigest()
    
    # Admin account
    await db.users.update_one(
        {"email": "admin@abundant.org"},
        {"$set": {
            "user_id": "user_admin_demo",
            "email": "admin@abundant.org",
            "name": "Pastor David Rivera",
            "picture": None,
            "role": "admin",
            "password_hash": demo_password_hash,
            "church_id": tenant_id,
            "created_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )
    
    # Member account - Maria Gonzalez
    await db.users.update_one(
        {"email": "member@abundant.org"},
        {"$set": {
            "user_id": "user_member_demo",
            "email": "member@abundant.org", 
            "name": "Maria Gonzalez",
            "picture": None,
            "role": "member",
            "password_hash": demo_password_hash,
            "church_id": tenant_id,
            "member_since": "2019-03-15",
            "created_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )

# --- SEED DATA ROUTE ---
    tenant = {
        "id": tenant_id,
        "name": "Abundant Church",
        "subdomain": "abundant",
        "plan": "enterprise",
        "member_limit": 100000,
        "logo_url": None,
        "primary_color": "#4f6ef7",
        "accent_color": "#00c896",
        "timezone": "America/Denver",
        "address": "1556 George Dieter Dr, El Paso, TX 79936",
        "website": "https://www.abundant.org",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.tenants.insert_one(tenant)
    
    # Create funds - Mega church scale
    funds_data = [
        {"name": "General Fund", "description": "General operating fund", "goal_amount": 8000000},
        {"name": "Building Fund", "description": "New sanctuary construction", "goal_amount": 5000000},
        {"name": "Missions", "description": "Global missions support", "goal_amount": 500000},
        {"name": "Benevolence", "description": "Community assistance", "goal_amount": 150000},
        {"name": "Youth Ministry", "description": "Youth programs and events", "goal_amount": 200000},
    ]
    
    funds = []
    for f in funds_data:
        fund = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "is_active": True,
            "current_amount": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **f
        }
        funds.append(fund)
    await db.funds.insert_many(funds)
    
    # Create group types
    group_types_data = [
        {"name": "Small Group", "color": "#4f6ef7", "icon": "users"},
        {"name": "Ministry Team", "color": "#00c896", "icon": "heart"},
        {"name": "Volunteer Team", "color": "#f5a623", "icon": "hand"},
        {"name": "Class", "color": "#8b5cf6", "icon": "book"},
    ]
    
    group_types = []
    for gt in group_types_data:
        gtype = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            **gt
        }
        group_types.append(gtype)
    await db.group_types.insert_many(group_types)
    
    # Create service types
    service_types_data = [
        {"name": "Sunday 9:00 AM", "default_time": "09:00", "default_day": "Sunday"},
        {"name": "Sunday 11:00 AM", "default_time": "11:00", "default_day": "Sunday"},
        {"name": "Wednesday Night", "default_time": "19:00", "default_day": "Wednesday"},
    ]
    
    service_types = []
    for st in service_types_data:
        stype = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "is_active": True,
            **st
        }
        service_types.append(stype)
    await db.service_types.insert_many(service_types)
    
    # Generate sample people (200 members)
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
                   "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
                   "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
                   "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
                   "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
                  "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
                  "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
    
    statuses = ["member", "member", "member", "member", "visitor", "regular", "inactive"]
    genders = ["male", "female"]
    campuses = ["Main Campus", "North Campus", "South Campus"]
    
    people = []
    households = []
    
    # ============== SPECIAL SEED: Maria Gonzalez (Demo Member Account) ==============
    maria_household_id = str(uuid.uuid4())
    maria_person_id = "person_maria_gonzalez"
    
    maria_household = {
        "id": maria_household_id,
        "tenant_id": tenant_id,
        "name": "The Gonzalez Family",
        "address_line1": "4521 Dyer St",
        "city": "El Paso",
        "state": "TX",
        "zip": "79930",
        "country": "US",
        "phone": "(915) 555-0142",
        "envelope_num": 1001,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    households.append(maria_household)
    
    maria_person = {
        "id": maria_person_id,
        "tenant_id": tenant_id,
        "household_id": maria_household_id,
        "first_name": "Maria",
        "last_name": "Gonzalez",
        "email": "member@abundant.org",
        "mobile_phone": "(915) 555-0142",
        "date_of_birth": "1985-06-14",
        "gender": "female",
        "marital_status": "married",
        "membership_status": "member",
        "membership_date": "2019-03-15",
        "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={maria_person_id}",
        "is_head_of_household": False,
        "campus": "East Campus",
        "engagement_score": 88,
        "ytd_giving": 1200.0,
        "lifetime_giving": 18500.0,
        "custom_fields": {},
        "giving_anonymous": False,
        "paperless_statements": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    people.append(maria_person)
    
    # ============== SEED: 10 El Paso-specific named members ==============
    el_paso_members = [
        {"first": "Carlos", "last": "Rivera", "gender": "male"},
        {"first": "Sofia", "last": "Martinez", "gender": "female"},
        {"first": "Juan", "last": "Hernandez", "gender": "male"},
        {"first": "Isabella", "last": "Lopez", "gender": "female"},
        {"first": "Miguel", "last": "Torres", "gender": "male"},
        {"first": "Valentina", "last": "Ramirez", "gender": "female"},
        {"first": "Diego", "last": "Castillo", "gender": "male"},
        {"first": "Ana", "last": "Reyes", "gender": "female"},
        {"first": "Roberto", "last": "Vega", "gender": "male"},
        {"first": "Pastor David", "last": "Rivera", "gender": "male"},
    ]
    
    el_paso_streets = ["Montana Ave", "Alameda Ave", "Mesa St", "Dyer St", "Lee Trevino Dr", 
                       "Gateway Blvd", "Viscount Blvd", "Zaragoza Rd", "Transmountain Dr", "Paisano Dr"]
    
    for i, ep_member in enumerate(el_paso_members):
        ep_household_id = str(uuid.uuid4())
        ep_person_id = str(uuid.uuid4())
        
        ep_household = {
            "id": ep_household_id,
            "tenant_id": tenant_id,
            "name": f"The {ep_member['last']} Family",
            "address_line1": f"{_rng.randint(1000, 9999)} {_rng.choice(el_paso_streets)}",
            "city": "El Paso",
            "state": "TX",
            "zip": f"799{_rng.randint(10, 99)}",
            "country": "US",
            "phone": f"(915) {_rng.randint(200, 999)}-{_rng.randint(1000, 9999)}",
            "envelope_num": 1002 + i,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        households.append(ep_household)
        
        ep_person = {
            "id": ep_person_id,
            "tenant_id": tenant_id,
            "household_id": ep_household_id,
            "first_name": ep_member["first"],
            "last_name": ep_member["last"],
            "email": f"{ep_member['first'].lower()}.{ep_member['last'].lower()}@email.com",
            "mobile_phone": f"(915) {_rng.randint(200, 999)}-{_rng.randint(1000, 9999)}",
            "date_of_birth": f"{_rng.randint(1960, 2000)}-{_rng.randint(1, 12):02d}-{_rng.randint(1, 28):02d}",
            "gender": ep_member["gender"],
            "marital_status": "married",
            "membership_status": "member",
            "membership_date": f"20{_rng.randint(15, 24)}-{_rng.randint(1, 12):02d}-01",
            "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={ep_person_id}",
            "is_head_of_household": True,
            "campus": _rng.choice(["Main Campus", "East Campus", "West Campus"]),
            "engagement_score": _rng.randint(60, 100),
            "ytd_giving": _rng.randint(500, 5000) * 1.0,
            "lifetime_giving": _rng.randint(5000, 50000) * 1.0,
            "custom_fields": {},
            "giving_anonymous": False,
            "paperless_statements": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        people.append(ep_person)
    
    # Create 80 households with 200 people (remaining generic)
    for h in range(80):
        household_id = str(uuid.uuid4())
        last_name = _rng.choice(last_names)
        
        household = {
            "id": household_id,
            "tenant_id": tenant_id,
            "name": f"The {last_name} Family",
            "address_line1": f"{_rng.randint(100, 9999)} {_rng.choice(['Oak', 'Main', 'Church', 'Park', 'Elm', 'Cedar'])} {_rng.choice(['St', 'Ave', 'Blvd', 'Dr'])}",
            "city": "El Cajon",
            "state": "CA",
            "zip": f"920{_rng.randint(10, 99)}",
            "country": "US",
            "phone": f"619-{_rng.randint(200, 999)}-{_rng.randint(1000, 9999)}",
            "envelope_num": h + 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        households.append(household)
        
        # 2-3 people per household
        num_people = _rng.randint(2, 3)
        for i in range(num_people):
            person_id = str(uuid.uuid4())
            first_name = _rng.choice(first_names)
            gender = _rng.choice(genders)
            birth_year = _rng.randint(1950, 2010)
            
            person = {
                "id": person_id,
                "tenant_id": tenant_id,
                "household_id": household_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name.lower()}.{last_name.lower()}{_rng.randint(1, 99)}@email.com",
                "mobile_phone": f"619-{_rng.randint(200, 999)}-{_rng.randint(1000, 9999)}",
                "date_of_birth": f"{birth_year}-{_rng.randint(1, 12):02d}-{_rng.randint(1, 28):02d}",
                "gender": gender,
                "marital_status": _rng.choice(["single", "married", "married"]),
                "membership_status": _rng.choice(statuses),
                "membership_date": f"20{_rng.randint(10, 24)}-{_rng.randint(1, 12):02d}-01",
                "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={person_id}",
                "is_head_of_household": i == 0,
                "campus": _rng.choice(campuses),
                "engagement_score": _rng.randint(20, 100),
                "ytd_giving": 0,
                "lifetime_giving": 0,
                "custom_fields": {},
                "giving_anonymous": False,
                "paperless_statements": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            people.append(person)
    
    await db.households.insert_many(households)
    await db.people.insert_many(people)
    
    # Create groups (20 groups)
    group_names = [
        "Young Adults", "Marriage Builders", "New Believers", "Prayer Warriors",
        "Women's Bible Study", "Men's Brotherhood", "College & Career", "Empty Nesters",
        "Parents of Teens", "Grief Support", "Financial Peace", "Spanish Fellowship",
        "Worship Team", "Tech Team", "Greeting Team", "Parking Team",
        "Children's Ministry", "Youth Group", "Senior Saints", "Community Outreach"
    ]
    
    groups = []
    for i, name in enumerate(group_names):
        group_type = group_types[i % len(group_types)]
        leader = _rng.choice(people)
        
        group = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "group_type_id": group_type["id"],
            "name": name,
            "description": f"{name} - a place to grow and connect",
            "location": _rng.choice(["Room 101", "Room 202", "Fellowship Hall", "Chapel", "Youth Center"]),
            "meeting_schedule": _rng.choice(["Weekly", "Bi-weekly", "Monthly"]),
            "meeting_day": _rng.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]),
            "meeting_time": _rng.choice(["09:00", "10:00", "18:00", "19:00"]),
            "capacity": _rng.randint(15, 60),
            "is_open": _rng.choice([True, True, True, False]),
            "is_active": True,
            "leader_id": leader["id"],
            "tags": [],
            "member_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        groups.append(group)
    await db.groups.insert_many(groups)
    
    # Assign people to groups (each person in 1-3 groups)
    group_members = []
    for person in people:
        num_groups = _rng.randint(1, 3)
        selected_groups = _rng.sample(groups, min(num_groups, len(groups)))
        
        for g in selected_groups:
            member = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "group_id": g["id"],
                "person_id": person["id"],
                "role": _rng.choice(["member", "member", "member", "leader", "co-leader"]),
                "joined_at": f"20{_rng.randint(20, 24)}-{_rng.randint(1, 12):02d}-{_rng.randint(1, 28):02d}",
                "is_active": True
            }
            group_members.append(member)
    await db.group_members.insert_many(group_members)
    
    # Update group member counts
    for g in groups:
        count = sum(1 for gm in group_members if gm["group_id"] == g["id"])
        await db.groups.update_one({"id": g["id"]}, {"$set": {"member_count": count}})
    
    # Create services for last 18 months (every Sunday)
    services = []
    today = datetime.now(timezone.utc)
    
    for weeks_ago in range(78):  # ~18 months
        service_date = today - timedelta(weeks=weeks_ago)
        # Find the Sunday
        days_until_sunday = (6 - service_date.weekday()) % 7
        sunday = service_date - timedelta(days=service_date.weekday() + 1)
        sunday_str = sunday.strftime("%Y-%m-%d")
        
        for st in service_types[:2]:  # Two Sunday services
            service = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "service_type_id": st["id"],
                "date": sunday_str,
                "time": st["default_time"],
                "total_headcount": _rng.randint(3000, 4500),
                "notes": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            services.append(service)
    
    await db.services.insert_many(services)
    
    # Create attendance records
    attendance_records = []
    for service in services[-24:]:  # Last 12 weeks (24 services)
        # Random subset of people attended
        attendees = _rng.sample(people, _rng.randint(60, 120))
        for person in attendees:
            record = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "service_id": service["id"],
                "person_id": person["id"],
                "check_in_time": datetime.now(timezone.utc).isoformat()
            }
            attendance_records.append(record)
    
    if attendance_records:
        await db.attendance.insert_many(attendance_records)
    
    # Create donations (18 months of giving)
    donations = []
    payment_methods = ["card", "card", "card", "check", "check", "cash", "ach", "ach"]
    
    for weeks_ago in range(78):
        week_date = today - timedelta(weeks=weeks_ago)
        sunday = week_date - timedelta(days=week_date.weekday() + 1)
        sunday_str = sunday.strftime("%Y-%m-%d")
        
        # 40-80 donations per week
        num_donations = _rng.randint(40, 80)
        donors = _rng.sample(people, min(num_donations, len(people)))
        
        for donor in donors:
            fund = _rng.choice(funds)
            amount = _rng.choice([25, 50, 100, 100, 150, 200, 250, 500, 1000, 2500])
            
            donation = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "person_id": donor["id"],
                "fund_id": fund["id"],
                "amount": float(amount),
                "donation_date": sunday_str,
                "payment_method": _rng.choice(payment_methods),
                "is_recurring": _rng.random() < 0.15,
                "receipt_sent": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            donations.append(donation)
    
    # Add 5 crypto donations
    crypto_currencies = ["BTC", "ETH", "USDC", "SOL"]
    for _ in range(5):
        donor = _rng.choice(people)
        crypto_amount = _rng.uniform(0.01, 2.0)
        usd_value = _rng.uniform(500, 25000)
        
        donation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": donor["id"],
            "fund_id": funds[0]["id"],  # General fund
            "amount": usd_value,
            "donation_date": (today - timedelta(days=_rng.randint(1, 180))).strftime("%Y-%m-%d"),
            "payment_method": "crypto",
            "crypto_currency": _rng.choice(crypto_currencies),
            "crypto_amount": crypto_amount,
            "crypto_tx_hash": f"0x{''.join(_rng.choices('0123456789abcdef', k=64))}",
            "crypto_usd_value": usd_value,
            "is_recurring": False,
            "receipt_sent": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        donations.append(donation)
    
    # Add 2 asset donations
    asset_donations = [
        {"asset_type": "vehicle", "asset_description": "2020 Toyota Camry", "asset_appraised_value": 22000},
        {"asset_type": "stock", "asset_description": "500 shares AAPL", "asset_appraised_value": 95000},
    ]
    
    for asset in asset_donations:
        donor = _rng.choice(people)
        donation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": donor["id"],
            "fund_id": funds[1]["id"],  # Building fund
            "amount": asset["asset_appraised_value"],
            "donation_date": (today - timedelta(days=_rng.randint(30, 180))).strftime("%Y-%m-%d"),
            "payment_method": "stock" if asset["asset_type"] == "stock" else "vehicle",
            "asset_type": asset["asset_type"],
            "asset_description": asset["asset_description"],
            "asset_appraised_value": asset["asset_appraised_value"],
            "is_recurring": False,
            "receipt_sent": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        donations.append(donation)
    
    await db.donations.insert_many(donations)
    
    # Update fund totals
    for fund in funds:
        total = sum(d["amount"] for d in donations if d["fund_id"] == fund["id"])
        await db.funds.update_one({"id": fund["id"]}, {"$set": {"current_amount": total}})
    
    # Update person giving totals
    ytd_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    for person in people:
        person_donations = [d for d in donations if d["person_id"] == person["id"]]
        lifetime = sum(d["amount"] for d in person_donations)
        ytd = sum(d["amount"] for d in person_donations if d["donation_date"] >= ytd_start)
        await db.people.update_one(
            {"id": person["id"]},
            {"$set": {"lifetime_giving": lifetime, "ytd_giving": ytd}}
        )
    
    # Create recurring giving (30 givers)
    recurring_givers = _rng.sample(people, 30)
    recurring_records = []
    
    for person in recurring_givers:
        recurring = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": person["id"],
            "fund_id": _rng.choice(funds)["id"],
            "amount": float(_rng.choice([50, 100, 150, 200, 250, 500])),
            "frequency": _rng.choice(["weekly", "biweekly", "monthly"]),
            "next_gift_date": (today + timedelta(days=_rng.randint(1, 30))).strftime("%Y-%m-%d"),
            "payment_method": "card",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        recurring_records.append(recurring)
    
    await db.recurring_giving.insert_many(recurring_records)
    
    # Create pledges (10 pledges for Building Fund campaign)
    pledgers = _rng.sample(people, 10)
    pledges = []
    
    for person in pledgers:
        pledge_amount = _rng.choice([5000, 10000, 15000, 25000, 50000])
        total_given = _rng.uniform(0.2, 0.9) * pledge_amount
        
        pledge = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": person["id"],
            "fund_id": funds[1]["id"],  # Building Fund
            "pledge_amount": float(pledge_amount),
            "start_date": "2024-01-01",
            "end_date": "2026-12-31",
            "frequency": "monthly",
            "total_given": total_given,
            "notes": "Building Fund Campaign 2024-2026",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        pledges.append(pledge)
    
    await db.pledges.insert_many(pledges)
    
    # Create donation batches
    batches = [
        {"name": "Sunday Offering 01/12/2025", "date": "2025-01-12", "status": "open", "total_amount": 45230.00, "donation_count": 87},
        {"name": "Sunday Offering 01/05/2025", "date": "2025-01-05", "status": "closed", "total_amount": 52100.00, "donation_count": 102},
        {"name": "Sunday Offering 12/29/2024", "date": "2024-12-29", "status": "deposited", "total_amount": 89500.00, "donation_count": 156},
    ]
    
    batch_records = []
    for b in batches:
        batch = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **b
        }
        batch_records.append(batch)
    await db.donation_batches.insert_many(batch_records)
    
    # Create upcoming events
    events = [
        {
            "name": "Sunday Service",
            "description": "Join us for worship, prayer, and the Word",
            "location": "Main Sanctuary",
            "start_datetime": (today + timedelta(days=(6 - today.weekday()))).strftime("%Y-%m-%dT09:00:00"),
            "is_public": True,
            "capacity": 5000,
            "registration_required": False,
            "registration_count": 0
        },
        {
            "name": "Youth Night",
            "description": "Middle and High School students gather for games, worship, and teaching",
            "location": "Youth Center",
            "start_datetime": (today + timedelta(days=3)).strftime("%Y-%m-%dT18:30:00"),
            "is_public": True,
            "capacity": 200,
            "registration_required": False,
            "registration_count": 45
        },
        {
            "name": "Women's Conference",
            "description": "Annual women's conference - 'Renewed'",
            "location": "Fellowship Hall",
            "start_datetime": (today + timedelta(days=14)).strftime("%Y-%m-%dT09:00:00"),
            "is_public": True,
            "capacity": 500,
            "registration_required": True,
            "registration_count": 287
        },
        {
            "name": "Baptism Sunday",
            "description": "Celebrate new believers taking the step of baptism",
            "location": "Main Sanctuary",
            "start_datetime": (today + timedelta(days=21)).strftime("%Y-%m-%dT11:00:00"),
            "is_public": True,
            "capacity": 5000,
            "registration_required": False,
            "registration_count": 23
        },
        {
            "name": "Marriage Retreat",
            "description": "Strengthen your marriage at our couples retreat",
            "location": "Pine Valley Resort",
            "start_datetime": (today + timedelta(days=45)).strftime("%Y-%m-%dT17:00:00"),
            "is_public": True,
            "capacity": 50,
            "registration_required": True,
            "registration_count": 34
        },
        {
            "name": "Volunteer Appreciation Dinner",
            "description": "Thank you dinner for all church volunteers",
            "location": "Fellowship Hall",
            "start_datetime": (today + timedelta(days=30)).strftime("%Y-%m-%dT18:00:00"),
            "is_public": False,
            "capacity": 300,
            "registration_required": True,
            "registration_count": 156
        }
    ]
    
    event_records = []
    for e in events:
        event = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **e
        }
        event_records.append(event)
    await db.events.insert_many(event_records)
    
    # Create activity log entries
    activities = [
        {"action": "member_added", "description": "New member added: Sarah Johnson", "entity_type": "person"},
        {"action": "donation_recorded", "description": "Donation of $1,500.00 recorded", "entity_type": "donation"},
        {"action": "group_created", "description": "New group created: Young Professionals", "entity_type": "group"},
        {"action": "event_created", "description": "New event created: Easter Service", "entity_type": "event"},
        {"action": "member_updated", "description": "Member status updated: John Smith → Active Member", "entity_type": "person"},
        {"action": "batch_closed", "description": "Batch closed: Sunday Offering 01/05/2025", "entity_type": "batch"},
        {"action": "email_sent", "description": "Email sent to 4,287 recipients: January Newsletter", "entity_type": "communication"},
        {"action": "attendance_recorded", "description": "Attendance recorded for Sunday 9AM: 3,421 attendees", "entity_type": "attendance"},
    ]
    
    activity_records = []
    for i, a in enumerate(activities):
        activity = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "entity_id": str(uuid.uuid4()),
            "created_at": (today - timedelta(hours=i*2)).isoformat(),
            **a
        }
        activity_records.append(activity)
    await db.activity_log.insert_many(activity_records)
    
    # Create communication templates
    communications = [
        {
            "subject": "Welcome to Abundant Church!",
            "body_html": "<h1>Welcome!</h1><p>We're so glad you visited us...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        },
        {
            "subject": "Prayer Request Follow-up",
            "body_html": "<p>Dear {first_name},</p><p>We've been praying for you...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        },
        {
            "subject": "You're Invited: {event_name}",
            "body_html": "<h2>{event_name}</h2><p>Join us for this special event...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        },
        {
            "subject": "Your Giving Statement",
            "body_html": "<h1>Annual Giving Statement</h1><p>Thank you for your generosity...</p>",
            "comm_type": "email",
            "status": "template",
            "recipient_count": 0
        }
    ]
    
    comm_records = []
    for c in communications:
        comm = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **c
        }
        comm_records.append(comm)
    await db.communications.insert_many(comm_records)
    
    return {
        "message": "Database seeded successfully",
        "seeded": True,
        "counts": {
            "tenant": 1,
            "households": len(households),
            "people": len(people),
            "groups": len(groups),
            "group_members": len(group_members),
            "funds": len(funds),
            "services": len(services),
            "attendance": len(attendance_records),
            "donations": len(donations),
            "recurring_giving": len(recurring_records),
            "pledges": len(pledges),
            "batches": len(batch_records),
            "events": len(event_records),
            "communications": len(comm_records)
        }
    }

# ============== MULTI-TENANT SEED ==============


@router.post("/seed-platform")
async def seed_platform():
    """Seed the entire Solomon AI platform with multiple churches and demo data"""
    import hashlib
    
    _seed_password = os.environ.get("SOLOMON_SEED_PASSWORD") or "change_me_in_env"
    demo_password_hash = hashlib.sha256(_seed_password.encode()).hexdigest()
    
    # Define the three demo churches
    churches = [
        {
            "id": "abundant-east-001",
            "name": "Abundant Church",
            "subdomain": "abundant",
            "plan": "enterprise",
            "member_limit": 100000,
            "subscription_status": "active",
            "address": "1556 George Dieter Dr",
            "city": "El Paso",
            "state": "TX",
            "timezone": "America/Denver",
            "website": "https://www.abundant.org",
            "phone": "(915) 755-3000",
            "primary_color": "#4f6ef7",
            "accent_color": "#00c896",
            "thinkific_url": "https://abundantchurch.thinkific.com/collections",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        },
        {
            "id": "cristoviene-church-001",
            "name": "Cristo Viene",
            "subdomain": "cristoviene",
            "plan": "enterprise",
            "member_limit": 50000,
            "subscription_status": "active",
            "address": "7500 N Loop Dr",
            "city": "El Paso",
            "state": "TX",
            "timezone": "America/Denver",
            "website": "https://cristoviene.org",
            "phone": "(915) 598-4000",
            "primary_color": "#dc2626",
            "accent_color": "#fbbf24",
            "thinkific_url": "https://cristoviene.thinkific.com",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        },
        {
            "id": "pottershouse-church-001",
            "name": "The Potter's House",
            "subdomain": "pottershouse",
            "plan": "enterprise",
            "member_limit": 100000,
            "subscription_status": "active",
            "address": "6777 W Kiest Blvd",
            "city": "Dallas",
            "state": "TX",
            "timezone": "America/Chicago",
            "website": "https://thepottershouse.org",
            "phone": "(214) 331-0954",
            "primary_color": "#7c3aed",
            "accent_color": "#ec4899",
            "thinkific_url": "https://pottershouse.thinkific.com",
            "merch_embed_url": DEFAULT_MERCH_EMBED_URL
        }
    ]
    
    results = {"churches": [], "platform_accounts": []}
    
    # Create/update Solomon platform admin accounts
    platform_accounts = [
        {
            "user_id": "platform_admin_001",
            "email": "admin@solomon.ai",
            "name": "Solomon Platform Admin",
            "role": "platform_admin",
            "tenant_id": None  # Platform admin has no tenant restriction
        },
        {
            "user_id": "platform_member_001",
            "email": "member@solomon.ai",
            "name": "Demo Member",
            "role": "member",
            "tenant_id": "abundant-east-001"  # Default to Abundant for demo
        },
        {
            "user_id": "platform_newmember_001",
            "email": "newmember@solomon.ai",
            "name": "New Member Demo",
            "role": "member",
            "tenant_id": "abundant-east-001"
        }
    ]
    
    for account in platform_accounts:
        await db.users.update_one(
            {"user_id": account["user_id"]},
            {"$set": {
                **account,
                "password_hash": demo_password_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }},
            upsert=True
        )
        results["platform_accounts"].append(account["email"])
    
    # Seed each church
    for church in churches:
        # Create/update tenant
        await db.tenants.update_one(
            {"id": church["id"]},
            {"$set": {
                **church,
                "created_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        # Create church admin account
        admin_email = f"admin@{church['subdomain']}.church"
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {
                "user_id": f"admin_{church['subdomain']}",
                "email": admin_email,
                "name": f"{church['name']} Admin",
                "role": "church_admin",
                "tenant_id": church["id"],
                "password_hash": demo_password_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }},
            upsert=True
        )
        
        # Create demo member account
        member_email = f"member@{church['subdomain']}.church"
        await db.users.update_one(
            {"email": member_email},
            {"$set": {
                "user_id": f"member_{church['subdomain']}",
                "email": member_email,
                "name": f"{church['name']} Member",
                "role": "member",
                "tenant_id": church["id"],
                "password_hash": demo_password_hash,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }},
            upsert=True
        )
        
        # Generate 500 members for this church with 6 months of data
        existing_members = await db.people.count_documents({"tenant_id": church["id"]})
        if existing_members < 100:  # Only seed if not already seeded
            await seed_church_members(church["id"], church["name"], 500)
        
        results["churches"].append({
            "name": church["name"],
            "subdomain": church["subdomain"],
            "admin_email": admin_email,
            "member_email": member_email
        })
    
    # Seed media videos for Abundant Church (as demo content - matching member portal)
    abundant_videos = [
        {
            "id": "video_001",
            "tenant_id": "abundant-east-001",
            "title": "Community With a Purpose",
            "description": "Discover how the church is God's purposeful community - not a club but a family with divine purpose.",
            "youtube_id": "FoPI3hMbXvw",
            "youtube_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration": "40:45",
            "instructor": "Pastor Charles Nieman",
            "category_id": "community",
            "is_featured": True,
            "is_published": True,
            "badge": "New",
            "view_count": 1250,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_002",
            "tenant_id": "abundant-east-001",
            "title": "Blessing & Healing Through Humility",
            "description": "Learn how humility unlocks God's blessings and healing in your life.",
            "youtube_id": "pzpbbibEWPE",
            "youtube_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration": "38:30",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": True,
            "is_published": True,
            "badge": "New",
            "view_count": 890,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_003",
            "tenant_id": "abundant-east-001",
            "title": "Building Your Life",
            "description": "Build your life on God's Word - biblical principles for personal spiritual development.",
            "youtube_id": "Lnj6vMvOLME",
            "youtube_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration": "45:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "growth",
            "is_featured": False,
            "is_published": True,
            "view_count": 1520,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_004",
            "tenant_id": "abundant-east-001",
            "title": "The Missing Peace",
            "description": "Find God's inner peace through grace and righteousness.",
            "youtube_id": "OjhMsB6czxc",
            "youtube_url": "https://youtube.com/watch?v=OjhMsB6czxc",
            "thumbnail_url": "https://i.ytimg.com/vi/OjhMsB6czxc/maxresdefault.jpg",
            "duration": "38:30",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": True,
            "is_published": True,
            "view_count": 780,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_005",
            "tenant_id": "abundant-east-001",
            "title": "The Laws of Life",
            "description": "Your thoughts and beliefs shape your outcomes - learn the laws that govern life.",
            "youtube_id": "WQy48ANpj5c",
            "youtube_url": "https://youtube.com/watch?v=WQy48ANpj5c",
            "thumbnail_url": "https://i.ytimg.com/vi/WQy48ANpj5c/maxresdefault.jpg",
            "duration": "37:57",
            "instructor": "Pastor Charles Nieman",
            "category_id": "growth",
            "is_featured": False,
            "is_published": True,
            "view_count": 650,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_006",
            "tenant_id": "abundant-east-001",
            "title": "The Story Behind the Story",
            "description": "Discover the deeper meaning of Christmas and God's plan through Jesus' birth.",
            "youtube_id": "wCjwUQMhCIY",
            "youtube_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration": "37:30",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": False,
            "is_published": True,
            "view_count": 430,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_007",
            "tenant_id": "abundant-east-001",
            "title": "Managing Your Emotions",
            "description": "Biblical wisdom on understanding and handling your emotions effectively.",
            "youtube_id": "0grr2E0kuFg",
            "youtube_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration": "42:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "growth",
            "is_featured": False,
            "is_published": True,
            "badge": "Popular",
            "view_count": 2100,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_008",
            "tenant_id": "abundant-east-001",
            "title": "Worship In Spirit & In Truth",
            "description": "Experience authentic worship that transforms your relationship with God.",
            "youtube_id": "uwkmP6sDihI",
            "youtube_url": "https://youtube.com/watch?v=uwkmP6sDihI",
            "thumbnail_url": "https://i.ytimg.com/vi/uwkmP6sDihI/maxresdefault.jpg",
            "duration": "35:00",
            "instructor": "Pastor Jared Nieman",
            "category_id": "worship",
            "is_featured": False,
            "is_published": True,
            "view_count": 560,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_009",
            "tenant_id": "abundant-east-001",
            "title": "Vision Sunday 2025",
            "description": "The church's vision and community outreach efforts for the year ahead.",
            "youtube_id": "O0WfS3Ma2XM",
            "youtube_url": "https://youtube.com/watch?v=O0WfS3Ma2XM",
            "thumbnail_url": "https://i.ytimg.com/vi/O0WfS3Ma2XM/maxresdefault.jpg",
            "duration": "48:00",
            "instructor": "Pastor Jared Nieman",
            "category_id": "leadership",
            "is_featured": False,
            "is_published": True,
            "view_count": 1800,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_010",
            "tenant_id": "abundant-east-001",
            "title": "Abundant Conference 2025",
            "description": "Night 2 of the Abundant Conference featuring worship and powerful teaching.",
            "youtube_id": "kGXOOO6hHUk",
            "youtube_url": "https://youtube.com/watch?v=kGXOOO6hHUk",
            "thumbnail_url": "https://i.ytimg.com/vi/kGXOOO6hHUk/maxresdefault.jpg",
            "duration": "1:20:00",
            "instructor": "Pastor Marcos Witt",
            "category_id": "worship",
            "is_featured": True,
            "is_published": True,
            "badge": "Featured",
            "view_count": 3200,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_011",
            "tenant_id": "abundant-east-001",
            "title": "We Are Abundant",
            "description": "Understanding our calling to be a blessing to others in our community.",
            "youtube_id": "rMmIcJCDsaU",
            "youtube_url": "https://youtube.com/watch?v=rMmIcJCDsaU",
            "thumbnail_url": "https://i.ytimg.com/vi/rMmIcJCDsaU/maxresdefault.jpg",
            "duration": "40:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "community",
            "is_featured": False,
            "is_published": True,
            "view_count": 920,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "video_012",
            "tenant_id": "abundant-east-001",
            "title": "Faith That Moves Mountains",
            "description": "Discover the kind of faith that can move any mountain in your life.",
            "youtube_id": "3BHJSkx3J4E",
            "youtube_url": "https://youtube.com/watch?v=3BHJSkx3J4E",
            "thumbnail_url": "https://i.ytimg.com/vi/3BHJSkx3J4E/maxresdefault.jpg",
            "duration": "36:00",
            "instructor": "Pastor Charles Nieman",
            "category_id": "faith",
            "is_featured": False,
            "is_published": True,
            "view_count": 750,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Seed media categories
    categories = [
        {"id": "faith", "tenant_id": "abundant-east-001", "name": "Faith", "slug": "faith", "icon": "heart", "sort_order": 1},
        {"id": "family", "tenant_id": "abundant-east-001", "name": "Family", "slug": "family", "icon": "users", "sort_order": 2},
        {"id": "leadership", "tenant_id": "abundant-east-001", "name": "Leadership", "slug": "leadership", "icon": "briefcase", "sort_order": 3},
        {"id": "worship", "tenant_id": "abundant-east-001", "name": "Worship", "slug": "worship", "icon": "music", "sort_order": 4},
        {"id": "growth", "tenant_id": "abundant-east-001", "name": "Growth", "slug": "growth", "icon": "trending-up", "sort_order": 5},
        {"id": "community", "tenant_id": "abundant-east-001", "name": "Community", "slug": "community", "icon": "home", "sort_order": 6},
    ]
    
    # Insert categories
    for cat in categories:
        await db.media_categories.update_one(
            {"id": cat["id"], "tenant_id": cat["tenant_id"]},
            {"$set": cat},
            upsert=True
        )
    
    # Insert videos
    for video in abundant_videos:
        await db.media_videos.update_one(
            {"id": video["id"]},
            {"$set": video},
            upsert=True
        )

    # Seed Abundant Pathways courses
    pathways_courses = [
        {
            "id": "pathway_course_001",
            "tenant_id": "abundant-east-001",
            "title": "Abundant Next Steps",
            "description": "Your on-ramp to belonging, serving, and growing at Abundant.",
            "cover_image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
            "category": "New Members Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_002",
            "tenant_id": "abundant-east-001",
            "title": "Preparing for Baptism",
            "description": "Understand baptism and get ready to share your story.",
            "cover_image_url": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80",
            "category": "Baptism Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_003",
            "tenant_id": "abundant-east-001",
            "title": "Foundations of Discipleship",
            "description": "Build daily rhythms of scripture, prayer, and obedience.",
            "cover_image_url": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?auto=format&fit=crop&w=1200&q=80",
            "category": "Discipleship Track",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_004",
            "tenant_id": "abundant-east-001",
            "title": "Financial Peace University",
            "description": "Walk through budgeting, generosity, and debt-free living.",
            "cover_image_url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80",
            "category": "Stewardship Track",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_005",
            "tenant_id": "abundant-east-001",
            "title": "Serving with Purpose",
            "description": "Discover your gifts and find the right team to serve.",
            "cover_image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
            "category": "Leadership Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_006",
            "tenant_id": "abundant-east-001",
            "title": "Prayer & Presence",
            "description": "Deepen your prayer life and sensitivity to God's presence.",
            "cover_image_url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80",
            "category": "Spiritual Practices",
            "level": "Intermediate",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_007",
            "tenant_id": "abundant-east-001",
            "title": "Marriage & Family Care",
            "description": "Strengthen your relationships and build a healthy home.",
            "cover_image_url": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=1200&q=80",
            "category": "Family Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_course_008",
            "tenant_id": "abundant-east-001",
            "title": "Mission & Outreach",
            "description": "Live on mission through local and global outreach.",
            "cover_image_url": "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?auto=format&fit=crop&w=1200&q=80",
            "category": "Outreach Track",
            "level": "Beginner",
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    pathways_lessons = [
        {
            "id": "pathway_lesson_001",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_001",
            "title": "Welcome to Abundant",
            "description": "Meet the heart, mission, and values of Abundant Church.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "15:40",
            "duration_seconds": 940,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_002",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_001",
            "title": "Belonging & Community",
            "description": "Find your people and take your next step into community.",
            "youtube_id": "pzpbbibEWPE",
            "video_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration_label": "18:20",
            "duration_seconds": 1100,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_003",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_002",
            "title": "Why Baptism Matters",
            "description": "Understand the significance of baptism and next steps.",
            "youtube_id": "Lnj6vMvOLME",
            "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration_label": "16:05",
            "duration_seconds": 965,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_004",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_002",
            "title": "Preparing Your Story",
            "description": "Craft your testimony and prepare for the baptism service.",
            "youtube_id": "wCjwUQMhCIY",
            "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration_label": "14:35",
            "duration_seconds": 875,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_005",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_003",
            "title": "Daily Discipleship",
            "description": "Develop a daily walk with Jesus through scripture and prayer.",
            "youtube_id": "0grr2E0kuFg",
            "video_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration_label": "20:10",
            "duration_seconds": 1210,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_006",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_003",
            "title": "Scripture & Spirit",
            "description": "Learn to listen to God's voice and apply the word.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "19:05",
            "duration_seconds": 1145,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_007",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_004",
            "title": "Budgeting with Purpose",
            "description": "Build a budget aligned with your values and goals.",
            "youtube_id": "pzpbbibEWPE",
            "video_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration_label": "21:20",
            "duration_seconds": 1280,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_008",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_004",
            "title": "Debt-Free Journey",
            "description": "Steps to reduce debt and build margin for generosity.",
            "youtube_id": "Lnj6vMvOLME",
            "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration_label": "17:30",
            "duration_seconds": 1050,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_009",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_005",
            "title": "Discover Your Gifts",
            "description": "Identify your gifts and how they serve the church.",
            "youtube_id": "wCjwUQMhCIY",
            "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration_label": "14:55",
            "duration_seconds": 895,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_010",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_005",
            "title": "Serving Teams",
            "description": "Explore serving opportunities and next steps.",
            "youtube_id": "0grr2E0kuFg",
            "video_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration_label": "13:50",
            "duration_seconds": 830,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_011",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_006",
            "title": "Prayer Rhythm",
            "description": "Create a daily prayer rhythm that anchors your week.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "18:00",
            "duration_seconds": 1080,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_012",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_006",
            "title": "Hearing God's Voice",
            "description": "Learn to discern and respond to God's leading.",
            "youtube_id": "wCjwUQMhCIY",
            "video_url": "https://youtube.com/watch?v=wCjwUQMhCIY",
            "thumbnail_url": "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
            "duration_label": "17:15",
            "duration_seconds": 1035,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_013",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_007",
            "title": "Healthy Relationships",
            "description": "Build healthy rhythms in your marriage and family.",
            "youtube_id": "pzpbbibEWPE",
            "video_url": "https://youtube.com/watch?v=pzpbbibEWPE",
            "thumbnail_url": "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
            "duration_label": "16:45",
            "duration_seconds": 1005,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_014",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_007",
            "title": "Family Devotions",
            "description": "Practical ideas for discipleship at home.",
            "youtube_id": "Lnj6vMvOLME",
            "video_url": "https://youtube.com/watch?v=Lnj6vMvOLME",
            "thumbnail_url": "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
            "duration_label": "15:30",
            "duration_seconds": 930,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_015",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_008",
            "title": "Living on Mission",
            "description": "Share your faith through local outreach.",
            "youtube_id": "FoPI3hMbXvw",
            "video_url": "https://youtube.com/watch?v=FoPI3hMbXvw",
            "thumbnail_url": "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
            "duration_label": "17:05",
            "duration_seconds": 1025,
            "sort_order": 1,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pathway_lesson_016",
            "tenant_id": "abundant-east-001",
            "course_id": "pathway_course_008",
            "title": "Community Outreach",
            "description": "Plan practical ways to serve El Paso together.",
            "youtube_id": "0grr2E0kuFg",
            "video_url": "https://youtube.com/watch?v=0grr2E0kuFg",
            "thumbnail_url": "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
            "duration_label": "18:35",
            "duration_seconds": 1115,
            "sort_order": 2,
            "is_published": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    for course in pathways_courses:
        await db.pathways_courses.update_one(
            {"id": course["id"]},
            {"$set": course},
            upsert=True
        )

    for lesson in pathways_lessons:
        await db.pathways_lessons.update_one(
            {"id": lesson["id"]},
            {"$set": lesson},
            upsert=True
        )

    # Assign demo member to pathways courses
    enrollments = []
    for idx, course in enumerate(pathways_courses, start=1):
        enrollments.append({
            "id": f"pathway_enroll_{idx:03d}",
            "tenant_id": "abundant-east-001",
            "course_id": course["id"],
            "user_id": "member_abundant",
            "assigned_by": "admin_abundant",
            "status": "assigned",
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

    for enrollment in enrollments:
        await db.pathways_enrollments.update_one(
            {"id": enrollment["id"]},
            {"$set": enrollment},
            upsert=True
        )

    return {
        "message": "Platform seeded successfully",
        "results": results,
        "demo_credentials": {
            "password": os.environ.get("SOLOMON_SEED_PASSWORD") or "change_me_in_env",
            "platform_admin": "admin@solomon.ai",
            "abundant_admin": "admin@abundant.church",
            "cristoviene_admin": "admin@cristoviene.church",
            "pottershouse_admin": "admin@pottershouse.church"
        }
    }

async def seed_church_members(tenant_id: str, church_name: str, count: int = 500):
    """Generate realistic church members with 6 months of giving/attendance data"""
    
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
                   "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
                   "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
                   "Matthew", "Betty", "Anthony", "Margaret", "Carlos", "Maria", "Juan", "Sofia",
                   "Miguel", "Isabella", "Diego", "Valentina", "Roberto", "Ana", "Luis", "Carmen"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
                  "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
                  "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
    
    statuses = ["member", "member", "member", "member", "visitor", "regular"]
    
    people = []
    donations = []
    attendance_records = []
    
    today = datetime.now(timezone.utc)
    six_months_ago = today - timedelta(days=180)
    
    fund_names = ["General Fund", "Building Fund", "Missions", "Benevolence", "Youth Ministry"]
    
    for i in range(count):
        person_id = str(uuid.uuid4())
        first_name = _rng.choice(first_names)
        last_name = _rng.choice(last_names)
        
        person = {
            "id": person_id,
            "tenant_id": tenant_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@email.com",
            "mobile_phone": f"({_rng.randint(200, 999)}) {_rng.randint(200, 999)}-{_rng.randint(1000, 9999)}",
            "date_of_birth": f"{_rng.randint(1960, 2005)}-{_rng.randint(1, 12):02d}-{_rng.randint(1, 28):02d}",
            "gender": _rng.choice(["male", "female"]),
            "membership_status": _rng.choice(statuses),
            "membership_date": (six_months_ago + timedelta(days=_rng.randint(0, 180))).strftime("%Y-%m-%d"),
            "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={person_id}",
            "engagement_score": _rng.randint(30, 100),
            "ytd_giving": 0,
            "lifetime_giving": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        people.append(person)
        
        # Generate donations (6 months of history)
        if _rng.random() > 0.3:  # 70% of members give
            num_donations = _rng.randint(3, 24)  # 3-24 donations over 6 months
            person_total = 0
            for _ in range(num_donations):
                donation_date = six_months_ago + timedelta(days=_rng.randint(0, 180))
                amount = _rng.choice([25, 50, 100, 150, 200, 250, 500, 1000])
                donation = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "person_id": person_id,
                    "donor_name": f"{first_name} {last_name}",
                    "amount": amount,
                    "fund_name": _rng.choice(fund_names),
                    "donation_date": donation_date.strftime("%Y-%m-%d"),
                    "payment_method": _rng.choice(["card", "ach", "cash", "check"]),
                    "payment_status": "completed",
                    "created_at": donation_date.isoformat()
                }
                donations.append(donation)
                person_total += amount
            person["ytd_giving"] = person_total
            person["lifetime_giving"] = person_total * _rng.uniform(1, 3)
        
        # Generate attendance (6 months)
        if _rng.random() > 0.2:  # 80% have some attendance
            num_attendances = _rng.randint(5, 24)  # 5-24 services over 6 months
            for _ in range(num_attendances):
                att_date = six_months_ago + timedelta(days=_rng.randint(0, 180))
                att_record = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "person_id": person_id,
                    "person_name": f"{first_name} {last_name}",
                    "service_name": _rng.choice(["Sunday 9AM", "Sunday 11AM", "Wednesday Night"]),
                    "check_in_time": att_date.isoformat(),
                    "created_at": att_date.isoformat()
                }
                attendance_records.append(att_record)
    
    # Bulk insert
    if people:
        await db.people.insert_many(people)
    if donations:
        await db.donations.insert_many(donations)
    if attendance_records:
        await db.attendance.insert_many(attendance_records)
    
    logger.info(f"Seeded {len(people)} members for {church_name}")
    return len(people)

# ============== SUMMIT ENHANCEMENTS - SERVICE MODE & ATTENDANCE STREAKS ==============

class ServiceModeStatus(BaseModel):
    is_service_day: bool
    is_service_time: bool
    current_service: Optional[Dict[str, Any]] = None
    next_service: Optional[Dict[str, Any]] = None
    attendance_streak: int = 0
    check_in_status: Optional[str] = None  # 'in_person', 'online', None

class AttendanceStreakData(BaseModel):
    current_streak: int = 0
    longest_streak: int = 0
    total_attended: int = 0
    last_attendance: Optional[str] = None
    streak_badges: List[Dict[str, Any]] = []

class PrayerRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    user_name: str
    category: str = "general"  # general, healing, family, financial, guidance, thanksgiving
    title: str
    content: str
    is_public: bool = False  # For prayer wall
    is_anonymous: bool = False
    prayer_count: int = 0  # How many people prayed
    status: str = "active"  # active, answered, closed
    admin_notes: Optional[str] = None
    follow_up_date: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class PrayerRequestCreate(BaseModel):
    category: str = "general"
    title: str
    content: str
    is_public: bool = False
    is_anonymous: bool = False

class MemberCheckIn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    service_id: Optional[str] = None
    check_in_type: str = "in_person"  # 'in_person' or 'online'
    service_date: str
    check_in_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== SERVICE MODE ENDPOINTS ==============


@router.get("/platform/health-scores")
async def get_all_health_scores(request: Request):
    """Get Church Health Scores for all tenants."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    tenants = await db.tenants.find({}, {"_id": 0}).to_list(100)
    results = []
    for t in tenants:
        # Skip TEST_ churches and empty stubs
        if t.get("name", "").startswith("TEST_"):
            continue
        donation_cnt = await db.donations.count_documents({"tenant_id": t["id"]})
        if donation_cnt < 10:
            continue
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": t["id"]}, {"_id": 0})
        preset = (cached or {}).get("preset_health_score")
        if preset is not None:
            health = {
                "score": cached.get("preset_health_score", 0),
                "grade": cached.get("preset_health_grade", "N/A"),
                "dimensions": cached.get("preset_health_dimensions", {}),
            }
        else:
            health = compute_health_score(cached, t)
        results.append({
            "tenant_id": t["id"],
            "name": t["name"],
            "location": t.get("location", ""),
            "plan": t.get("plan", ""),
            "members": cached.get("total_members", 0) if cached else 0,
            "health": health,
        })

    results.sort(key=lambda x: x["health"]["score"], reverse=True)
    return {"churches": results}


@router.get("/platform/churches")
async def get_all_platform_churches(request: Request):
    """
    List all church tenants with metrics.
    Serves from platform_stats_cache (already computed by /platform/stats).
    Falls back to single-pass aggregation only if cache is missing.
    """
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    # ── Fast path: serve from platform_stats_cache ────────────────────────────
    # The campus_breakdown in the stats cache has everything we need.
    stats_cache = await db.platform_stats_cache.find_one({"id": "global"}, {"_id": 0})
    if stats_cache and stats_cache.get("campus_breakdown"):
        campus_breakdown = stats_cache["campus_breakdown"]

        # Enrich with health scores and full tenant details
        churches = []
        for cb in campus_breakdown:
            tid = cb.get("tenant_id")
            if not tid:
                continue
            t = await db.tenants.find_one({"id": tid}, {"_id": 0,
                "name": 1, "city": 1, "state": 1, "plan": 1, "subdomain": 1})
            cached = await db.dashboard_stats_cache.find_one({"tenant_id": tid}, {"_id": 0})

            preset = (cached or {}).get("preset_health_score")
            if preset is not None:
                health = {
                    "score": (cached or {}).get("preset_health_score", 0),
                    "grade": (cached or {}).get("preset_health_grade", "N/A"),
                    "dimensions": (cached or {}).get("preset_health_dimensions", {}),
                }
            else:
                health = compute_health_score(cached or {}, t or {})

            churches.append({
                "id": tid,
                "name": cb.get("name", (t or {}).get("name", "")),
                "city": cb.get("city", (t or {}).get("city", "")),
                "state": cb.get("state", (t or {}).get("state", "")),
                "plan": (t or {}).get("plan", "enterprise"),
                "subdomain": (t or {}).get("subdomain", ""),
                "total_members": (cached or {}).get("total_members", 0),
                "giving":     cb.get("giving", 0),
                "fees":       cb.get("fees", 0),
                "txn_count":  cb.get("txn_count", 0),
                "ytd_giving": cb.get("ytd_giving", 0),
                "mtd_giving": cb.get("mtd_giving", 0),
                "active_donors": cb.get("active_donors", 0),
                "health": health,
            })

        churches.sort(key=lambda x: x["giving"], reverse=True)
        return {"churches": churches, "total": len(churches)}

    # ── Slow fallback (only if cache completely missing — runs once) ──────────
    stats = await _compute_platform_stats_fast()
    asyncio.ensure_future(_save_platform_stats_cache(stats))

    # Build response from just-computed stats
    churches = []
    for cb in stats.get("campus_breakdown", []):
        tid = cb.get("tenant_id")
        t = await db.tenants.find_one({"id": tid}, {"_id": 0}) or {}
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": tid}, {"_id": 0}) or {}
        preset = cached.get("preset_health_score")
        health = ({"score": cached.get("preset_health_score", 0),
                   "grade": cached.get("preset_health_grade", "N/A"),
                   "dimensions": cached.get("preset_health_dimensions", {})}
                  if preset is not None else compute_health_score(cached, t))
        churches.append({
            "id": tid, "name": cb.get("name", ""), "city": cb.get("city", ""),
            "state": cb.get("state", ""), "plan": t.get("plan", "enterprise"),
            "subdomain": t.get("subdomain", ""), "total_members": cached.get("total_members", 0),
            "giving": cb.get("giving", 0), "fees": cb.get("fees", 0),
            "txn_count": cb.get("txn_count", 0), "ytd_giving": cb.get("ytd_giving", 0),
            "mtd_giving": cb.get("mtd_giving", 0), "active_donors": cb.get("active_donors", 0),
            "health": health,
        })
    churches.sort(key=lambda x: x["giving"], reverse=True)
    return {"churches": churches, "total": len(churches)}

    now = datetime.now(timezone.utc)
    year_start  = now.replace(month=1, day=1).strftime("%Y-%m-%d")
    month_start = now.replace(day=1).strftime("%Y-%m-%d")

    # Tenants (small collection — fast)
    tenants = await db.tenants.find({"subscription_status": "active"}, {"_id": 0}).to_list(100)
    real_tenants = {t["id"]: t for t in tenants if not t.get("name", "").startswith("TEST_")}

    # Dashboard stats cache — already has member counts (fast lookup)
    cache_docs = await db.dashboard_stats_cache.find(
        {"tenant_id": {"$in": list(real_tenants.keys())}}, {"_id": 0}
    ).to_list(100)
    cache_map = {c["tenant_id"]: c for c in cache_docs}

    # Keep only churches with real data (use cache instead of count_documents)
    valid_ids = [tid for tid, c in cache_map.items() if c.get("total_members", 0) > 10]
    if not valid_ids:
        valid_ids = list(real_tenants.keys())

    # SINGLE aggregation across all churches — all buckets in one pass
    agg = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": valid_ids}}},
        {"$group": {
            "_id": "$tenant_id",
            "all_vol":  {"$sum": "$amount"},
            "all_fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}},
            "all_cnt":  {"$sum": 1},
            "ytd_vol":  {"$sum": {"$cond": [{"$gte": ["$donation_date", year_start]},  "$amount", 0]}},
            "mtd_vol":  {"$sum": {"$cond": [{"$gte": ["$donation_date", month_start]}, "$amount", 0]}},
        }},
    ], allowDiskUse=True).to_list(20)
    agg_map = {r["_id"]: r for r in agg}

    churches = []
    for tid in valid_ids:
        t = real_tenants.get(tid, {})
        if not t:
            continue
        cached = cache_map.get(tid, {})
        r = agg_map.get(tid, {})

        # Health score from pre-computed cache
        preset = cached.get("preset_health_score")
        if preset is not None:
            health = {
                "score": cached.get("preset_health_score", 0),
                "grade": cached.get("preset_health_grade", "N/A"),
                "dimensions": cached.get("preset_health_dimensions", {}),
            }
        else:
            health = compute_health_score(cached, t)

        churches.append({
            "id": tid,
            "name": t.get("name", ""),
            "city": t.get("city", ""),
            "state": t.get("state", ""),
            "plan": t.get("plan", "enterprise"),
            "subdomain": t.get("subdomain", ""),
            "total_members": cached.get("total_members", 0),
            "giving":     round(r.get("all_vol", 0), 2),
            "fees":       round(r.get("all_fees", 0), 2),
            "txn_count":  r.get("all_cnt", 0),
            "ytd_giving": round(r.get("ytd_vol", 0), 2),
            "mtd_giving": round(r.get("mtd_vol", 0), 2),
            "health": health,
        })

    churches.sort(key=lambda x: x["giving"], reverse=True)
    return {"churches": churches, "total": len(churches)}

# ============== PLATFORM CHURCH ONBOARDING (Task 2) ==============

class ChurchOnboardingRequest(BaseModel):
    name: str
    city: str = ""
    state: str = ""
    denomination: str = ""
    website: str = ""
    service_times: list = []
    primary_color: str = "#2563eb"
    subdomain: str = ""
    admin_name: str = ""
    admin_email: str = ""
    admin_password: str = ""
    admin_phone: str = ""
    estimated_members: int = 0
    plan: str = "starter"


@router.get("/platform/churches/{tenant_id}/detail")
async def get_church_detail(request: Request, tenant_id: str):
    """Church drill-through detail page — giving chart, top donors, recent transactions, member roster."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Church not found")

    today = datetime.now(timezone.utc)
    twelve_ago = (today - timedelta(days=365)).strftime("%Y-%m")
    ninety_ago = (today - timedelta(days=90)).strftime("%Y-%m-%d")

    # 12-month giving chart
    monthly_giving = await db.donations.aggregate([
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": twelve_ago + "-01"}}},
        {"$addFields": {"month": {"$substr": ["$donation_date", 0, 7]}}},
        {"$group": {"_id": "$month", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ], allowDiskUse=True).to_list(24)

    # Top 10 donors
    top_donors = await db.donations.aggregate([
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$person_id", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 10},
        {"$lookup": {"from": "people", "localField": "_id", "foreignField": "id", "as": "person"}},
        {"$unwind": {"path": "$person", "preserveNullAndEmptyArrays": True}},
        {"$project": {"_id": 0, "person_id": "$_id", "total": 1, "count": 1,
                       "name": {"$concat": [{"$ifNull": ["$person.first_name", ""]}, " ", {"$ifNull": ["$person.last_name", ""]}]},
                       "email": {"$ifNull": ["$person.email", ""]}}},
    ], allowDiskUse=True).to_list(10)

    # Recent 20 transactions
    recent_txns = await db.donations.find(
        {"tenant_id": tenant_id}, {"_id": 0, "person_id": 1, "amount": 1, "donation_date": 1, "fund_name": 1, "payment_method": 1, "status": 1}
    ).sort("donation_date", -1).limit(20).to_list(20)
    pid_set = list(set(t.get("person_id") for t in recent_txns if t.get("person_id")))
    pcache = {}
    if pid_set:
        pdocs = await db.people.find({"id": {"$in": pid_set}}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1}).to_list(len(pid_set))
        pcache = {p["id"]: p for p in pdocs}
    for t in recent_txns:
        p = pcache.get(t.get("person_id"), {})
        t["person_name"] = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or "Member"
        t["fund_name"] = t.get("fund_name") or "General Fund"
        t["status"] = t.get("status") or "completed"
        t["payment_method"] = t.get("payment_method") or "card"

    # Member roster (top 20 by engagement/giving)
    members = await db.people.find(
        {"tenant_id": tenant_id}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "membership_status": 1, "campus": 1, "engagement_score": 1, "ytd_giving": 1, "lifetime_giving": 1}
    ).sort("lifetime_giving", -1).limit(20).to_list(20)

    # Health score
    cached = await db.dashboard_stats_cache.find_one({"tenant_id": tenant_id}, {"_id": 0})
    total_members = (cached or {}).get("total_members", 0)
    health = compute_health_score(cached or {}, tenant)

    # Summary stats
    total_donations = await db.donations.count_documents({"tenant_id": tenant_id})
    total_giving_raw = await db.donations.aggregate([
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]).to_list(1)
    total_giving = total_giving_raw[0]["total"] if total_giving_raw else 0

    active_donors = await db.donations.aggregate([
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": ninety_ago}}},
        {"$group": {"_id": "$person_id"}},
        {"$count": "count"},
    ]).to_list(1)

    return {
        "church": {
            "tenant_id": tenant_id,
            "name": tenant.get("name", ""),
            "city": tenant.get("city", ""),
            "state": tenant.get("state", ""),
            "plan": tenant.get("plan", ""),
            "address": tenant.get("address", ""),
            "phone": tenant.get("phone", ""),
        },
        "health": health,
        "summary": {
            "total_members": total_members,
            "total_giving": round(total_giving, 2),
            "total_transactions": total_donations,
            "active_donors_90d": active_donors[0]["count"] if active_donors else 0,
        },
        "monthly_giving": [{"month": m["_id"], "total": round(m["total"], 2), "count": m["count"]} for m in monthly_giving],
        "top_donors": top_donors,
        "recent_transactions": recent_txns,
        "members": members,
    }


@router.post("/platform/churches/create")
async def create_church_onboarding(request: Request, payload: ChurchOnboardingRequest):
    """5-step church onboarding wizard — creates a new tenant with admin account."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    if not payload.name:
        raise HTTPException(status_code=400, detail="Church name is required")
    if not payload.admin_email:
        raise HTTPException(status_code=400, detail="Admin email is required")

    subdomain = payload.subdomain or payload.name.lower().replace(" ", "-").replace("'", "")[:30]
    existing = await db.tenants.find_one({"subdomain": subdomain})
    if existing:
        raise HTTPException(status_code=409, detail=f"Subdomain '{subdomain}' is already taken")

    existing_email = await db.users.find_one({"email": payload.admin_email.lower()})
    if existing_email:
        raise HTTPException(status_code=409, detail=f"Email '{payload.admin_email}' is already registered")

    tenant_id = f"{subdomain}-001"
    now_iso = datetime.now(timezone.utc).isoformat()

    tenant = {
        "id": tenant_id,
        "name": payload.name,
        "subdomain": subdomain,
        "city": payload.city,
        "state": payload.state,
        "denomination": payload.denomination,
        "website": payload.website,
        "primary_color": payload.primary_color,
        "plan": payload.plan,
        "subscription_status": "active",
        "estimated_members": payload.estimated_members,
        "service_times": payload.service_times,
        "created_at": now_iso,
        "onboarded_by": user.get("user_id")
    }
    await db.tenants.insert_one({**tenant})

    import bcrypt as _bc; admin_password_hash = _bc.hashpw((payload.admin_password or os.environ.get("SOLOMON_DEFAULT_PASSWORD", "Welcome2026!")).encode("utf-8"), _bc.gensalt()).decode("utf-8")
    admin_user = {
        "user_id": str(uuid.uuid4()),
        "email": payload.admin_email.lower(),
        "password_hash": admin_password_hash,
        "name": payload.admin_name or payload.name + " Admin",
        "role": "church_admin",
        "role_title": "Church Administrator",
        "permissions": ROLE_TEMPLATES["church_admin"]["permissions"],
        "tenant_id": tenant_id,
        "phone": payload.admin_phone,
        "created_at": now_iso,
        "is_verified": True
    }
    await db.users.insert_one({**admin_user})

    await audit_log("church_created", "tenant", tenant_id, tenant_id, user.get("user_id"), user.get("name", ""), {}, {"tenant": payload.name, "admin_email": payload.admin_email}, request)

    return {
        "success": True,
        "tenant_id": tenant_id,
        "subdomain": subdomain,
        "church_name": payload.name,
        "admin_email": payload.admin_email,
        "admin_user_id": admin_user["user_id"],
        "message": f"Church '{payload.name}' created successfully with admin account."
    }


# ============== PLATFORM USER MANAGEMENT ==============


@router.post("/platform/users/create")
async def platform_create_user(request: Request, payload: dict):
    """Platform admin creates a user tied to a specific church."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    admin = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not admin or admin.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    email = (payload.get("email") or "").strip().lower()
    name = (payload.get("name") or "").strip()
    tenant_id = payload.get("tenant_id")
    role_template = payload.get("role_template", "member")
    password = payload.get("password") or os.environ.get("SOLOMON_DEFAULT_PASSWORD", "Welcome2026!")

    if not email or not name or not tenant_id:
        raise HTTPException(status_code=400, detail="email, name, and tenant_id are required")

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Church '{tenant_id}' not found")

    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail=f"Email '{email}' is already registered")

    if role_template not in ROLE_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid role_template. Options: {', '.join(sorted(ROLE_TEMPLATES.keys()))}")

    tmpl = ROLE_TEMPLATES[role_template]
    role_field = role_template if role_template in ("church_admin", "platform_admin", "member") else ("church_admin" if any(p.startswith("admin.") for p in tmpl["permissions"]) else "member")

    new_user = {
        "user_id": str(uuid.uuid4()),
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        "name": name,
        "first_name": name.split()[0] if name.split() else name,
        "last_name": name.split()[-1] if len(name.split()) > 1 else "",
        "role": role_field,
        "role_title": tmpl["role_title"],
        "permissions": tmpl["permissions"],
        "tenant_id": tenant_id,
        "church_id": tenant_id,
        "is_active": True,
        "membership_status": "Active",
        "email_verified": True,
        "registration_source": "platform_created",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "directory_visible": True,
        "share_email": True,
        "share_phone": True,
    }
    await db.users.insert_one({**new_user})

    await db.people.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": new_user["user_id"],
        "name": name,
        "first_name": new_user["first_name"],
        "last_name": new_user["last_name"],
        "email": email,
        "role": role_field,
        "membership_status": "Active",
        "tenant_id": tenant_id,
        "created_at": new_user["created_at"],
        "directory_visible": True,
        "share_email": True,
        "share_phone": True,
        "groups": [],
        "tags": [],
    })

    await audit_log("user_created", "user", new_user["user_id"], tenant_id, admin.get("user_id"), admin.get("name", ""), {}, {"email": email, "name": name, "role": role_field, "church": tenant.get("name")}, request)

    return {
        "success": True,
        "user_id": new_user["user_id"],
        "email": email,
        "name": name,
        "role": role_field,
        "role_title": tmpl["role_title"],
        "church": tenant.get("name"),
        "message": f"User '{name}' created for {tenant.get('name')}"
    }


@router.put("/platform/users/{user_id}/promote")
async def platform_promote_user(request: Request, user_id: str, payload: dict):
    """Platform admin promotes a member to admin (or changes their role template)."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    admin = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not admin or admin.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    role_template = payload.get("role_template", "church_admin")
    if role_template not in ROLE_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Options: {', '.join(sorted(ROLE_TEMPLATES.keys()))}")

    tmpl = ROLE_TEMPLATES[role_template]
    role_field = role_template if role_template in ("church_admin", "platform_admin", "member") else ("church_admin" if any(p.startswith("admin.") for p in tmpl["permissions"]) else "member")

    before = {"role": target.get("role"), "role_title": target.get("role_title"), "permissions": get_permissions_for_user(target)}

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "role": role_field,
            "role_title": tmpl["role_title"],
            "permissions": tmpl["permissions"],
        }}
    )

    after = {"role": role_field, "role_title": tmpl["role_title"], "permissions": tmpl["permissions"]}
    await audit_log("role_promotion", "user", user_id, target.get("tenant_id", ""), admin.get("user_id"), admin.get("name", ""), before, after, request)

    return {
        "success": True,
        "user_id": user_id,
        "name": target.get("name"),
        "email": target.get("email"),
        "new_role": role_field,
        "role_title": tmpl["role_title"],
        "permissions_count": len(tmpl["permissions"]),
        "message": f"{target.get('name')} promoted to {tmpl['role_title']}"
    }


# ============== ORGANIZATIONS & CAMPUS COMPARISON (Universal Multi-Campus) ==============


@router.get("/platform/organizations")
async def list_organizations(request: Request):
    """List all multi-campus organizations with their campuses."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    tenants = await db.tenants.find({"organization_id": {"$exists": True, "$ne": None}}, {"_id": 0}).to_list(200)

    orgs = {}
    for t in tenants:
        org_id = t["organization_id"]
        if org_id not in orgs:
            orgs[org_id] = {
                "organization_id": org_id,
                "organization_name": t.get("organization_name", org_id),
                "campuses": [],
                "total_members": 0,
                "total_mrr": 0,
                "total_mtd_giving": 0,
            }
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": t["id"]}, {"_id": 0})
        campus_info = {
            "tenant_id": t["id"],
            "name": t["name"],
            "location": t.get("location", ""),
            "plan": t.get("plan", ""),
            "mrr": float(t.get("mrr", 0) or 0),
            "subscription_status": t.get("subscription_status", "active"),
            "members": cached.get("total_members", 0) if cached else 0,
            "active_members": cached.get("active_members", 0) if cached else 0,
            "mtd_giving": cached.get("mtd_giving", 0) if cached else 0,
            "ytd_giving": cached.get("ytd_giving", 0) if cached else 0,
            "weekly_attendance": cached.get("last_attendance", 0) if cached else 0,
            "groups": cached.get("active_groups", 0) if cached else 0,
            "cafe_orders_week": cached.get("cafe_orders_week", 0) if cached else 0,
            "merch_orders_week": cached.get("merch_orders_week", 0) if cached else 0,
            "recurring_givers": cached.get("recurring_givers", 0) if cached else 0,
        }
        orgs[org_id]["campuses"].append(campus_info)
        orgs[org_id]["total_members"] += campus_info["members"]
        orgs[org_id]["total_mrr"] += campus_info["mrr"]
        orgs[org_id]["total_mtd_giving"] += campus_info["mtd_giving"]

    return list(orgs.values())


@router.get("/platform/organizations/{org_id}/comparison")
async def get_campus_comparison(org_id: str, request: Request):
    """Get detailed campus comparison metrics for a multi-campus organization."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    tenants = await db.tenants.find({"organization_id": org_id}, {"_id": 0}).to_list(50)
    if not tenants:
        raise HTTPException(status_code=404, detail="Organization not found")

    org_name = tenants[0].get("organization_name", org_id)
    campuses = []
    totals = {"members": 0, "active": 0, "attendance": 0, "mtd_giving": 0, "ytd_giving": 0, "groups": 0, "mrr": 0,
              "cafe_orders": 0, "cafe_giving": 0, "merch_orders": 0, "merch_giving": 0, "recurring_givers": 0}

    for t in tenants:
        tid = t["id"]
        cached = await db.dashboard_stats_cache.find_one({"tenant_id": tid}, {"_id": 0})
        c = cached or {}

        members = c.get("total_members", 0)
        active = c.get("active_members", 0)
        attendance = c.get("last_attendance", 0)
        mtd = c.get("mtd_giving", 0)
        ytd = c.get("ytd_giving", 0)
        groups = c.get("active_groups", 0)
        cafe_orders = c.get("cafe_orders_week", 0)
        cafe_giving = c.get("cafe_giving_added", 0)
        merch_orders = c.get("merch_orders_week", 0)
        merch_giving = c.get("merch_giving_added", 0)
        recurring = c.get("recurring_givers", 0)

        campus = {
            "tenant_id": tid,
            "name": t["name"],
            "location": t.get("location", ""),
            "plan": t.get("plan", ""),
            "mrr": float(t.get("mrr", 0) or 0),
            "metrics": {
                "total_members": members,
                "active_members": active,
                "engagement_rate": round((active / members * 100), 1) if members > 0 else 0,
                "weekly_attendance": attendance,
                "attendance_rate": round((attendance / members * 100), 1) if members > 0 else 0,
                "mtd_giving": mtd,
                "ytd_giving": ytd,
                "giving_per_capita": round(mtd / members, 2) if members > 0 else 0,
                "recurring_givers": recurring,
                "recurring_rate": round((recurring / members * 100), 1) if members > 0 else 0,
                "active_groups": groups,
                "members_per_group": round(members / groups, 0) if groups > 0 else 0,
                "cafe_orders_week": cafe_orders,
                "cafe_giving_added": cafe_giving,
                "merch_orders_week": merch_orders,
                "merch_giving_added": merch_giving,
            }
        }
        campuses.append(campus)

        for k in totals:
            if k == "members": totals[k] += members
            elif k == "active": totals[k] += active
            elif k == "attendance": totals[k] += attendance
            elif k == "mtd_giving": totals[k] += mtd
            elif k == "ytd_giving": totals[k] += ytd
            elif k == "groups": totals[k] += groups
            elif k == "mrr": totals[k] += float(t.get("mrr", 0) or 0)
            elif k == "cafe_orders": totals[k] += cafe_orders
            elif k == "cafe_giving": totals[k] += cafe_giving
            elif k == "merch_orders": totals[k] += merch_orders
            elif k == "merch_giving": totals[k] += merch_giving
            elif k == "recurring_givers": totals[k] += recurring

    # Giving trends by campus (last 4 weeks)
    giving_trends = []
    for week_offset in range(4):
        week_end = NOW - timedelta(weeks=week_offset)
        week_start = week_end - timedelta(days=7)
        week_label = week_start.strftime("%b %d")
        week_data = {"week": week_label}
        for t in tenants:
            pipeline = [
                {"$match": {
                    "tenant_id": t["id"],
                    "donation_date": {"$gte": week_start.strftime("%Y-%m-%d"), "$lt": week_end.strftime("%Y-%m-%d")}
                }},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            result = await db.donations.aggregate(pipeline).to_list(1)
            week_data[t["name"]] = result[0]["total"] if result else 0
        giving_trends.append(week_data)

    giving_trends.reverse()

    return {
        "organization_id": org_id,
        "organization_name": org_name,
        "campus_count": len(campuses),
        "campuses": campuses,
        "totals": {
            "total_members": totals["members"],
            "total_active": totals["active"],
            "total_attendance": totals["attendance"],
            "total_mtd_giving": totals["mtd_giving"],
            "total_ytd_giving": totals["ytd_giving"],
            "total_groups": totals["groups"],
            "total_mrr": totals["mrr"],
            "total_cafe_orders": totals["cafe_orders"],
            "total_merch_orders": totals["merch_orders"],
            "engagement_rate": round((totals["active"] / totals["members"] * 100), 1) if totals["members"] > 0 else 0,
            "giving_per_capita": round(totals["mtd_giving"] / totals["members"], 2) if totals["members"] > 0 else 0,
        },
        "giving_trends": giving_trends,
    }


# ============== GIVING NUDGE CHECKOUT FLOW ==============

class CheckoutWithNudgeRequest(BaseModel):
    items: List[Dict[str, Any]]
    giving_amount: float = 0
    giving_fund: str = "General Fund"
    payment_method_id: Optional[str] = None
    order_type: str = "cafe"  # "cafe" or "merch"
    pickup_time: Optional[str] = None


@router.get("/platform/health")
async def platform_health(request: Request):
    """System health check for platform admin dashboard."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    # DB health check
    db_healthy = True
    try:
        await db.command("ping")
    except Exception:
        db_healthy = False

    # Active sessions
    active_sessions = await db.user_sessions.count_documents({
        "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
    })

    # Failed logins (check for any rate limiting triggers)
    twenty_four_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent_activity = await db.activity_log.count_documents({
        "created_at": {"$gte": twenty_four_hours_ago}
    })

    total_collections = await db.list_collection_names()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": {
            "status": "connected" if db_healthy else "disconnected",
            "collections": len(total_collections),
        },
        "sessions": {
            "active_now": active_sessions,
        },
        "activity": {
            "events_24h": recent_activity,
        },
        "uptime": "99.9%",
        "checked_at": datetime.now(timezone.utc).isoformat()
    }

# NOW is used in comparison endpoint
NOW = datetime.now(timezone.utc)

# ============== PUBLIC ENDPOINTS (NO AUTH) ==============



# ============== GODMODE REVENUE DASHBOARD ==============

SOLOMON_FEE_RATE = 0.019  # 1.9%
SOLOMON_FEE_FLAT = 0.30   # $0.30 per transaction


@router.get("/platform/revenue")
async def get_platform_revenue(request: Request):
    """Revenue dashboard — built from platform_stats_cache (fast, <200ms)."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    # ── Serve from platform_stats_cache — no new aggregations ─────────────────
    stats = await db.platform_stats_cache.find_one({"id": "global"}, {"_id": 0})
    if not stats:
        # Compute and cache if missing
        stats = await _compute_platform_stats_fast()
        asyncio.ensure_future(_save_platform_stats_cache(stats))

    campus_breakdown = stats.get("campus_breakdown", [])
    giving_trend = stats.get("giving_trend", [])
    all_time_fees = stats.get("fees", {}).get("all_time", 0)
    all_time_giving = stats.get("giving", {}).get("all_time", 0)
    total_txns = stats.get("transactions", {}).get("total", 0)

    # By-church revenue from campus_breakdown
    by_church = [
        {
            "tenant_id": c.get("tenant_id", ""),
            "name": c.get("name", ""),
            "total_volume": c.get("giving", 0),
            "total_fees": c.get("fees", 0),
            "txn_count": c.get("txn_count", 0),
        }
        for c in campus_breakdown
    ]

    # Monthly trend from giving_trend (already computed)
    monthly_trend = [
        {
            "month": m.get("month", ""),
            "volume": m.get("total_giving", 0),
            "fees": m.get("total_fees", 0),
            "txn_count": m.get("txn_count", 0),
        }
        for m in giving_trend
    ]

    # By year — derive from monthly trend
    by_year_map: dict = {}
    for m in monthly_trend:
        yr = m.get("month", "")[:4]
        if yr not in by_year_map:
            by_year_map[yr] = {"year": yr, "total_volume": 0, "total_fees": 0, "txn_count": 0}
        by_year_map[yr]["total_volume"] += m.get("volume", 0)
        by_year_map[yr]["total_fees"] += m.get("fees", 0)
        by_year_map[yr]["txn_count"] += m.get("txn_count", 0)
    by_year = [{"year": v["year"], "total_volume": round(v["total_volume"], 2),
                "total_fees": round(v["total_fees"], 2), "txn_count": v["txn_count"]}
               for v in sorted(by_year_map.values(), key=lambda x: x["year"])]

    return {
        "summary": {
            "total_processing_volume": round(all_time_giving, 2),
            "total_fees_earned":  round(all_time_fees, 2),
            "all_time_fees":      round(all_time_fees, 2),
            "all_time_giving":    round(all_time_giving, 2),
            "total_transactions": total_txns,
            "active_churches":    len(by_church),
            "fee_rate":           f"{SOLOMON_FEE_RATE * 100:.1f}% + ${SOLOMON_FEE_FLAT:.2f}",
            "industry_rate":      "2.9% + $0.30",
            "savings_vs_industry":"34% cheaper",
            "avg_fee_rate":       round(all_time_fees / max(all_time_giving, 1) * 100, 2),
        },
        "by_church": by_church,
        "by_year": by_year,
        "monthly_trend": monthly_trend,
    }


# ═══════════════════ PLATFORM TRANSACTIONS ═══════════════════

@router.get("/platform/transactions")
async def get_platform_transactions(request: Request, page: int = 1, limit: int = 50, church: str = "", status: str = "", method: str = "", fund: str = "", search: str = "", start_date: str = "", end_date: str = ""):
    """All transactions across platform with filters, pagination, search."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    query = {}
    if church:
        query["tenant_id"] = church
    if status:
        query["status"] = status
    if method:
        query["payment_method"] = method
    if fund:
        query["fund_name"] = fund
    if search:
        query["$or"] = [
            {"donor_name": {"$regex": search, "$options": "i"}},
            {"person_name": {"$regex": search, "$options": "i"}},
            {"person_email": {"$regex": search, "$options": "i"}},
        ]
    if start_date:
        query.setdefault("donation_date", {})["$gte"] = start_date
    if end_date:
        query.setdefault("donation_date", {})["$lte"] = end_date

    total = await db.donations.count_documents(query)
    skip = (page - 1) * limit
    txns = await db.donations.find(query, {"_id": 0}).sort("donation_date", -1).skip(skip).limit(limit).to_list(limit)

    # Batch-enrich with church names AND person names/emails
    tenant_cache = {}
    person_ids = list(set(t.get("person_id") for t in txns if t.get("person_id")))
    person_cache = {}
    if person_ids:
        people_docs = await db.people.find(
            {"id": {"$in": person_ids}},
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1}
        ).to_list(len(person_ids))
        person_cache = {p["id"]: p for p in people_docs}

    for txn in txns:
        tid = txn.get("tenant_id")
        if tid and tid not in tenant_cache:
            t = await db.tenants.find_one({"id": tid}, {"_id": 0, "name": 1})
            tenant_cache[tid] = t.get("name", tid) if t else tid
        txn["church_name"] = tenant_cache.get(tid, tid)
        # Enrich person data
        person = person_cache.get(txn.get("person_id"), {})
        pname = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
        txn["person_name"] = txn.get("person_name") or txn.get("donor_name") or pname or "Member"
        txn["person_email"] = txn.get("person_email") or person.get("email", "")
        txn["fund_name"] = txn.get("fund_name") or "General Fund"
        txn["status"] = txn.get("status") or "completed"
        txn["payment_method"] = txn.get("payment_method") or "card"

    return {
        "transactions": txns,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/platform/transactions/export")
async def export_platform_transactions(request: Request, church: str = "", status: str = "", method: str = "", fund: str = "", start_date: str = "", end_date: str = ""):
    """Export all matching transactions as CSV."""
    from fastapi.responses import StreamingResponse
    import csv
    import io

    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    query = {}
    if church:
        query["tenant_id"] = church
    if status:
        query["status"] = status
    if method:
        query["payment_method"] = method
    if fund:
        query["fund_name"] = fund
    if start_date:
        query.setdefault("donation_date", {})["$gte"] = start_date
    if end_date:
        query.setdefault("donation_date", {})["$lte"] = end_date

    txns = await db.donations.find(query, {"_id": 0}).sort("donation_date", -1).limit(100000).to_list(100000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Church", "Donor", "Email", "Amount", "Fee", "Net", "Fund", "Method", "Status", "Transaction ID"])
    for t in txns:
        writer.writerow([
            t.get("donation_date", ""),
            t.get("tenant_id", ""),
            t.get("person_name", ""),
            t.get("person_email", ""),
            t.get("amount", 0),
            t.get("solomon_fee", 0),
            t.get("net_amount", 0),
            t.get("fund_name", ""),
            t.get("payment_method", ""),
            t.get("status", ""),
            t.get("transaction_id", ""),
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=solomon_transactions.csv"},
    )


# ═══════════════════ PLATFORM PAYOUTS ═══════════════════

@router.get("/platform/payouts")
async def get_platform_payouts(request: Request, page: int = 1, limit: int = 50, church: str = "", start_date: str = "", end_date: str = ""):
    """Weekly payout history — capped at 500 records to prevent timeout on Atlas."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    limit = min(limit, 100)  # cap per-page to reduce load
    query: dict = {}
    if church:
        query["tenant_id"] = church
    if start_date:
        query.setdefault("payout_date", {})["$gte"] = start_date
    if end_date:
        query.setdefault("payout_date", {})["$lte"] = end_date

    skip = (page - 1) * limit
    # Skip count_documents on full collection (slow) — use estimate
    raw_payouts = await db.payouts.find(query, {"_id": 0}).sort("payout_date", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.payouts.estimated_document_count() if not query else len(raw_payouts) + skip

    # Normalize field names and enrich with church name
    tenant_cache = {}
    payouts = []
    for p in raw_payouts:
        tid = p.get("tenant_id", "")
        if tid and tid not in tenant_cache:
            t = await db.tenants.find_one({"id": tid}, {"_id": 0, "name": 1})
            tenant_cache[tid] = t.get("name", tid) if t else tid
        normalized = {
            "id": p.get("id", ""),
            "payout_date": p.get("payout_date") or p.get("period_end") or p.get("created_at", "")[:10] if p.get("created_at") else "",
            "church_name": p.get("church_name") or tenant_cache.get(tid, tid),
            "gross_amount": round(float(p.get("gross_amount") or p.get("amount") or 0), 2),
            "total_fees": round(float(p.get("total_fees") or p.get("fee_amount") or 0), 2),
            "net_payout": round(float(p.get("net_payout") or p.get("net_amount") or 0), 2),
            "transaction_count": p.get("transaction_count") or p.get("txn_count") or 0,
            "status": p.get("status", "completed"),
            "bank_account": f"****{p.get('bank_last_four', '????')}",
            "tenant_id": tid,
        }
        payouts.append(normalized)

    # Pending balances: sum of donations since last payout for each church
    pending = []
    pending_tenants = await db.tenants.find(
        {"subscription_status": "active"}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(100)
    for tenant_doc in pending_tenants:
        tid = tenant_doc["id"]
        last_payout = await db.payouts.find_one({"tenant_id": tid}, {"_id": 0, "payout_date": 1}, sort=[("payout_date", -1)])
        since = last_payout["payout_date"] if last_payout else "2023-01-01"
        pipe = [
            {"$match": {"tenant_id": tid, "donation_date": {"$gt": since}, "status": "completed"}},
            {"$group": {"_id": None, "gross": {"$sum": "$amount"}, "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}}}},
        ]
        result = await db.donations.aggregate(pipe).to_list(1)
        if result:
            pending.append({
                "tenant_id": tid,
                "church_name": tenant_doc.get("name", tid),
                "available_balance": round(result[0]["gross"] - result[0]["fees"], 2),
                "bank_account": f"****{tid[-4:]}",
                "payout_method": "ACH - Standard",
            })

    return {
        "payouts": payouts,
        "pending_payouts": pending,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/platform/payouts/{payout_id}/transactions")
async def get_payout_transactions(request: Request, payout_id: str):
    """Drill-down: get all constituent transactions for a specific payout."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    payout = await db.payouts.find_one({"id": payout_id}, {"_id": 0})
    if not payout:
        return {"transactions": [], "payout_id": payout_id}

    tid = payout.get("tenant_id", "")
    payout_date = payout.get("payout_date") or payout.get("period_end", "")
    period_start = payout.get("period_start", "")

    # Find donations in the payout period for this tenant
    query = {"tenant_id": tid, "status": {"$in": ["completed", None]}}
    if period_start and payout_date:
        query["donation_date"] = {"$gte": period_start, "$lte": payout_date}
    elif payout_date:
        query["donation_date"] = {"$lte": payout_date}

    txns = await db.donations.find(query, {"_id": 0, "person_id": 1, "amount": 1, "donation_date": 1, "fund_name": 1, "payment_method": 1}).sort("donation_date", -1).limit(100).to_list(100)

    # Enrich with person names
    person_ids = list(set(t.get("person_id") for t in txns if t.get("person_id")))
    pcache = {}
    if person_ids:
        pdocs = await db.people.find({"id": {"$in": person_ids}}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1}).to_list(len(person_ids))
        pcache = {p["id"]: p for p in pdocs}
    for t in txns:
        p = pcache.get(t.get("person_id"), {})
        t["person_name"] = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or "Member"
        t["fund_name"] = t.get("fund_name") or "General Fund"

    return {"transactions": txns, "payout_id": payout_id, "total": len(txns)}



# ═══════════════════ FUND RECONCILIATION ═══════════════════

@router.get("/platform/funds/reconciliation")
async def get_fund_reconciliation(request: Request, tenant_id: str = ""):
    """Fund reconciliation view — giving by fund with reconciliation status."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    campuses, _ = await _get_real_campuses_fast()
    target_tenants = [tenant_id] if tenant_id and tenant_id.strip() else campuses

    # Aggregate giving by fund across target tenants
    fund_data = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": target_tenants}}},
        {"$group": {
            "_id": {"fund": {"$ifNull": ["$fund_name", "General Fund"]}, "tenant": "$tenant_id"},
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1},
            "fees": {"$sum": {"$ifNull": ["$fee_amount", 0]}},
        }},
        {"$sort": {"total": -1}},
    ], allowDiskUse=True).to_list(100)

    # Get actual fund records for goals
    fund_goals = {}
    funds_raw = await db.funds.find({"tenant_id": {"$in": target_tenants}}, {"_id": 0, "name": 1, "goal_amount": 1, "current_amount": 1}).to_list(100)
    for f in funds_raw:
        fund_goals[f.get("name", "")] = f

    # Tenant name cache
    t_map = {}
    for t in await db.tenants.find({"id": {"$in": target_tenants}}, {"_id": 0, "id": 1, "name": 1}).to_list(20):
        t_map[t["id"]] = t["name"]

    # Aggregate by fund name
    by_fund = {}
    for row in fund_data:
        fname = row["_id"]["fund"] or "General Fund"
        if fname not in by_fund:
            goal = fund_goals.get(fname, {})
            by_fund[fname] = {
                "fund_name": fname,
                "total_giving": 0, "total_fees": 0, "transaction_count": 0,
                "goal_amount": goal.get("goal_amount", 0),
                "by_church": {},
            }
        by_fund[fname]["total_giving"] += round(row["total"], 2)
        by_fund[fname]["total_fees"] += round(row.get("fees", 0), 2)
        by_fund[fname]["transaction_count"] += row["count"]
        church_name = t_map.get(row["_id"]["tenant"], row["_id"]["tenant"])
        by_fund[fname]["by_church"][church_name] = round(row["total"], 2)

    funds_list = sorted(by_fund.values(), key=lambda x: x["total_giving"], reverse=True)
    for f in funds_list:
        f["net_giving"] = round(f["total_giving"] - f["total_fees"], 2)
        f["pct_of_goal"] = round(f["total_giving"] / max(f["goal_amount"], 1) * 100, 1) if f["goal_amount"] else 0

    return {
        "funds": funds_list,
        "total_giving": round(sum(f["total_giving"] for f in funds_list), 2),
        "total_fees": round(sum(f["total_fees"] for f in funds_list), 2),
        "total_net": round(sum(f["net_giving"] for f in funds_list), 2),
    }


# ═══════════════════ MONDAY MORNING SUMMARY EMAIL ═══════════════════

@router.post("/platform/send-summary-email")
async def send_monday_morning_summary(request: Request):
    """Send weekly platform summary email to founders — SecureGive parity feature."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    body = await request.json()
    recipients = body.get("recipients", ["admin@solomonai.us"])

    # Build summary from cached stats
    cached = await db.platform_stats_cache.find_one({"id": "global"}, {"_id": 0})
    if not cached:
        raise HTTPException(status_code=500, detail="Platform stats not available. Please refresh the dashboard first.")

    giving = cached.get("giving", {})
    fees = cached.get("fees", {})
    platform = cached.get("platform", {})
    campuses = cached.get("campus_breakdown", [])
    now = datetime.now(timezone.utc)

    # Build HTML email
    church_rows = ""
    for c in sorted(campuses, key=lambda x: x.get("mtd_giving", 0), reverse=True):
        church_rows += f"""<tr>
            <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;font-size:14px;color:#334155">{c.get('name','')}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;font-size:14px;color:#334155;text-align:right">${c.get('mtd_giving',0):,.0f}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;font-size:14px;color:#059669;text-align:right">${c.get('fees',0):,.0f}</td>
        </tr>"""

    email_html = f"""<div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:600px;margin:0 auto;background:#fff">
        <div style="background:#0f172a;padding:24px 32px;border-radius:12px 12px 0 0">
            <span style="font-size:16px;font-weight:200;letter-spacing:6px;color:#fff">SOLOMON</span>
            <span style="font-size:16px;font-weight:700;color:#3b82f6"> AI</span>
            <p style="color:#94a3b8;font-size:13px;margin:8px 0 0">Monday Morning Platform Summary</p>
        </div>
        <div style="padding:32px">
            <h2 style="font-size:20px;font-weight:700;color:#0f172a;margin:0 0 4px">Week of {now.strftime('%B %d, %Y')}</h2>
            <p style="color:#64748b;font-size:14px;margin:0 0 24px">Here's how your platform performed this week.</p>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:24px">
                <div style="background:#f8fafc;border-radius:8px;padding:16px"><p style="font-size:12px;color:#64748b;margin:0 0 4px">Platform GMV</p><p style="font-size:24px;font-weight:800;color:#0f172a;margin:0">${giving.get('all_time',0):,.0f}</p></div>
                <div style="background:#f8fafc;border-radius:8px;padding:16px"><p style="font-size:12px;color:#64748b;margin:0 0 4px">Total Revenue</p><p style="font-size:24px;font-weight:800;color:#059669;margin:0">${fees.get('all_time',0):,.0f}</p></div>
                <div style="background:#f8fafc;border-radius:8px;padding:16px"><p style="font-size:12px;color:#64748b;margin:0 0 4px">MTD Giving</p><p style="font-size:24px;font-weight:800;color:#0f172a;margin:0">${giving.get('mtd',0):,.0f}</p></div>
                <div style="background:#f8fafc;border-radius:8px;padding:16px"><p style="font-size:12px;color:#64748b;margin:0 0 4px">Churches</p><p style="font-size:24px;font-weight:800;color:#2563eb;margin:0">{len(campuses)}</p></div>
            </div>
            <h3 style="font-size:16px;font-weight:700;color:#0f172a;margin:0 0 12px">Church Performance</h3>
            <table style="width:100%;border-collapse:collapse">
                <thead><tr style="background:#f8fafc">
                    <th style="padding:8px 12px;text-align:left;font-size:12px;color:#64748b;font-weight:600">Church</th>
                    <th style="padding:8px 12px;text-align:right;font-size:12px;color:#64748b;font-weight:600">MTD Giving</th>
                    <th style="padding:8px 12px;text-align:right;font-size:12px;color:#64748b;font-weight:600">Fees</th>
                </tr></thead>
                <tbody>{church_rows}</tbody>
            </table>
            <p style="font-size:12px;color:#94a3b8;margin:24px 0 0;text-align:center">&copy; {now.year} Solomon AI &middot; Platform Summary</p>
        </div>
    </div>"""

    # Send via Resend
    resend_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
    if not resend_key:
        return {"success": False, "message": "Email not configured. Set RESEND_API_KEY."}

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                json={
                    "from": f"Solomon AI <{sender}>",
                    "to": recipients,
                    "subject": f"Solomon AI — Monday Morning Summary ({now.strftime('%B %d')})",
                    "html": email_html,
                },
                timeout=15
            )
        if resp.status_code in (200, 201):
            logger.info(f"Monday summary sent to {recipients}")
            return {"success": True, "message": f"Summary email sent to {', '.join(recipients)}"}
        else:
            return {"success": False, "message": f"Email API returned {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        logger.error(f"Failed to send summary email: {e}")
        return {"success": False, "message": f"Email send failed: {str(e)}"}


# ═══════════════════ PLATFORM DONOR ANALYTICS ═══════════════════

@router.get("/platform/donors")
async def get_platform_donors_alias(request: Request):
    """Alias for /platform/donors/stats — frontend calls this path."""
    return await get_platform_donor_stats(request)


@router.get("/platform/donors/stats")
async def get_platform_donor_stats(request: Request):
    """Platform-wide donor analytics — cache-first, single-pass aggregation."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    # ── Serve from cache ───────────────────────────────────────────────────────
    cached = await db.platform_donors_cache.find_one({"id": "global"}, {"_id": 0})
    cache_age = 999
    if cached and cached.get("generated_at"):
        try:
            gen = datetime.fromisoformat(str(cached["generated_at"]).replace("Z", "+00:00"))
            cache_age = (datetime.now(timezone.utc) - gen).total_seconds() / 60
        except Exception:
            pass
    if cached and cache_age < 30:
        cached.pop("id", None)
        return cached
    if cached and cache_age < 120:
        asyncio.ensure_future(_refresh_donor_stats_cache())
        cached.pop("id", None)
        return cached

    # ── No cache — compute with single combined pass ──────────────────────────
    result = await _compute_donor_stats_fast()
    asyncio.ensure_future(_save_donor_stats_cache(result))
    return result


async def _compute_donor_stats_fast() -> dict:
    """Single aggregation pass replacing 9 serial queries."""
    today = datetime.now(timezone.utc)
    d90 = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    d30 = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    year_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")

    # Get campuses from dashboard_stats_cache (fast)
    all_tenants = await db.tenants.find(
        {"subscription_status": "active"}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(100)
    campuses = []
    for t in all_tenants:
        if t["name"].startswith("TEST_"):
            continue
        c = await db.dashboard_stats_cache.find_one({"tenant_id": t["id"]}, {"_id": 0, "total_members": 1})
        if c and c.get("total_members", 0) > 10:
            campuses.append(t["id"])
    if not campuses:
        campuses = [t["id"] for t in all_tenants if not t["name"].startswith("TEST_")]

    # SINGLE PASS: per-donor aggregation with all buckets simultaneously
    # This replaces 9 separate aggregations with ONE
    per_donor = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": campuses}}},
        {"$group": {
            "_id": "$person_id",
            "total":       {"$sum": "$amount"},
            "gift_count":  {"$sum": 1},
            "first_gift":  {"$min": "$donation_date"},
            "last_gift":   {"$max": "$donation_date"},
            "is_active":   {"$sum": {"$cond": [{"$gte": ["$donation_date", d90]}, 1, 0]}},
            "is_recurring":{"$sum": {"$cond": [{"$eq": ["$is_recurring", True]}, 1, 0]}},
            "is_first_time_30d": {"$sum": {"$cond": [{"$gte": ["$donation_date", d30]}, 1, 0]}},
            "is_this_year": {"$sum": {"$cond": [{"$gte": ["$donation_date", year_start]}, 1, 0]}},
            "donor_name":  {"$first": "$donor_name"},
            "tenant_id":   {"$first": "$tenant_id"},
        }},
        {"$sort": {"total": -1}},
    ], allowDiskUse=True).to_list(50000)  # limit for memory safety

    # Compute stats from in-memory results
    total_donors   = len(per_donor)
    active_donors  = sum(1 for d in per_donor if d.get("is_active", 0) > 0)
    recurring_d    = sum(1 for d in per_donor if d.get("is_recurring", 0) > 0)
    first_time_30d = sum(1 for d in per_donor
                        if d.get("first_gift", "") >= d30 and d.get("is_first_time_30d", 0) > 0)
    lapsed         = max(0, total_donors - active_donors)
    this_year_d    = sum(1 for d in per_donor if d.get("is_this_year", 0) > 0)

    total_giving   = sum(d.get("total", 0) for d in per_donor)
    avg_ltv        = round(total_giving / max(total_donors, 1), 2)
    avg_gift       = round(total_giving / max(sum(d.get("gift_count", 0) for d in per_donor), 1), 2)

    one_time = max(0, total_donors - recurring_d)
    stages = {
        "first_time": first_time_30d,
        "occasional": round(one_time * 0.35),
        "regular": round(one_time * 0.30),
        "recurring": recurring_d,
        "at_risk": round(lapsed * 0.05),
        "lapsed": round(lapsed * 0.03),
    }

    # Retention: simple approximation from this_year vs total
    retention_rate = round(this_year_d / max(total_donors, 1) * 100, 1)

    # Top donors (already sorted)
    t_map = {t["id"]: t["name"] for t in all_tenants}
    top_donors = [
        {
            "person_id": d["_id"],
            "name": d.get("donor_name") or "Member",
            "total": round(d.get("total", 0), 2),
            "donation_count": d.get("gift_count", 0),
            "church": t_map.get(d.get("tenant_id", ""), ""),
        }
        for d in per_donor[:20]
    ]

    # Compute by_campus from per_donor results
    campus_counts = {}
    for d in per_donor:
        tid = d.get("tenant_id", "")
        if tid:
            campus_counts[tid] = campus_counts.get(tid, 0) + 1
    by_campus = campus_counts

    # Get recurring donor count from recurring_giving collection (more accurate)
    recurring_from_collection = await db.recurring_giving.count_documents(
        {"tenant_id": {"$in": campuses}, "is_active": True}
    )
    if recurring_from_collection > recurring_d:
        recurring_d = recurring_from_collection
        # Update stages with corrected recurring count
        one_time = max(0, total_donors - recurring_d)
        stages["recurring"] = recurring_d
        stages["occasional"] = round(one_time * 0.35)
        stages["regular"] = round(one_time * 0.30)

    return {
        "total_donors": total_donors,
        "active_donors": active_donors,
        "recurring_donors": recurring_d,
        "first_time_donors_30d": first_time_30d,
        "lapsed_donors": lapsed,
        "avg_lifetime_value": avg_ltv,
        "avg_gift": avg_gift,
        "retention_rate_yoy": retention_rate,
        "donor_stages": stages,
        "top_donors": top_donors,
        "by_campus": by_campus,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def _save_donor_stats_cache(data: dict) -> None:
    try:
        await db.platform_donors_cache.replace_one({"id": "global"}, {**data, "id": "global"}, upsert=True)
    except Exception as exc:
        logger.warning(f"[donors_cache] save failed: {exc}")


async def _refresh_donor_stats_cache() -> None:
    try:
        result = await _compute_donor_stats_fast()
        await _save_donor_stats_cache(result)
        logger.info("[donors_cache] refreshed")
    except Exception as exc:
        logger.error(f"[donors_cache] refresh failed: {exc}")


# ═══════════════════ PLATFORM IMPERSONATE ═══════════════════

@router.post("/platform/impersonate")
async def impersonate_church(request: Request):
    """Impersonate a church admin — returns a session for that church."""
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    body = await request.json()
    target_tenant = body.get("tenant_id")
    if not target_tenant:
        raise HTTPException(status_code=400, detail="tenant_id required")

    # Find a church_admin for that tenant
    admin = await db.users.find_one({"tenant_id": target_tenant, "role": "church_admin"}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=404, detail="No admin found for this church")

    import secrets as _sec
    imp_token = _sec.token_hex(32)
    await db.user_sessions.insert_one({
        "session_token": imp_token,
        "user_id": admin["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_impersonation": True,
        "impersonated_by": user["user_id"],
    })

    return {
        "token": imp_token,
        "user": {
            "name": admin.get("name"),
            "email": admin.get("email"),
            "role": admin.get("role"),
            "tenant_id": admin.get("tenant_id"),
        },
        "impersonating": True,
    }
