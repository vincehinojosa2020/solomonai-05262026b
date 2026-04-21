"""Solomon AI — SolomonPay Admin Dashboard Routes"""
from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional
from datetime import datetime, timezone, timedelta
from core import db, DEFAULT_TENANT_ID, logger
from core.helpers import serialize_doc
import uuid

router = APIRouter()


async def _get_admin(request, required_perm=None):
    """Quick admin auth helper with optional permission check."""
    from core import get_session_token_from_request, get_permissions_for_user
    token = get_session_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user or user.get("role") not in ("church_admin", "admin", "platform_admin", "senior_pastor", "executive_pastor", "finance", "staff"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if required_perm:
        perms = get_permissions_for_user(user)
        if required_perm not in perms:
            raise HTTPException(status_code=403, detail=f"Missing permission: {required_perm}")
    return user


@router.get("/admin/solomonpay/dashboard")
async def solomonpay_dashboard(request: Request, source: Optional[str] = None):
    """SolomonPay admin dashboard — aggregate stats.
    `source` query param filters by payment_source:
      * "stripe" → only real Stripe PaymentIntents (test or live)
      * "demo"   → only seeded/fake data (payment_source != stripe)
      * None     → all donations (default)
    """
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    ytd_start = now.replace(month=1, day=1).strftime("%Y-%m-%d")

    def _source_filter():
        if source == "stripe":
            return {"payment_source": "stripe"}
        if source == "demo":
            return {"$or": [{"payment_source": {"$ne": "stripe"}}, {"payment_source": {"$exists": False}}]}
        return {}

    src = _source_filter()

    async def _sum(match):
        pipeline = [{"$match": {**match, **src, "tenant_id": tenant_id}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}]
        r = await db.donations.aggregate(pipeline).to_list(1)
        return {"total": round(r[0]["total"], 2) if r else 0, "count": r[0]["count"] if r else 0}

    today = await _sum({"donation_date": today_str})
    week = await _sum({"donation_date": {"$gte": week_ago}})
    month = await _sum({"donation_date": {"$gte": month_start}})
    ytd = await _sum({"donation_date": {"$gte": ytd_start}})

    # Active recurring count (not source-filtered — recurring lives separately)
    recurring_count = await db.recurring_giving.count_documents({"tenant_id": tenant_id, "is_active": True})

    # Average gift
    avg_pipeline = [{"$match": {**src, "tenant_id": tenant_id, "donation_date": {"$gte": ytd_start}}}, {"$group": {"_id": None, "avg": {"$avg": "$amount"}}}]
    avg_r = await db.donations.aggregate(avg_pipeline).to_list(1)
    avg_gift = round(avg_r[0]["avg"], 2) if avg_r else 0

    # Top fund
    fund_pipeline = [{"$match": {**src, "tenant_id": tenant_id, "donation_date": {"$gte": ytd_start}}}, {"$group": {"_id": "$fund_name", "total": {"$sum": "$amount"}}}, {"$sort": {"total": -1}}, {"$limit": 1}]
    top_fund_r = await db.donations.aggregate(fund_pipeline).to_list(1)
    top_fund = top_fund_r[0]["_id"] if top_fund_r else "General Fund"

    # 12-month trend
    trend = []
    for i in range(11, -1, -1):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        ms = f"{y}-{m:02d}"
        mp = [{"$match": {**src, "tenant_id": tenant_id, "donation_date": {"$regex": f"^{ms}"}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}]
        mr = await db.donations.aggregate(mp).to_list(1)
        trend.append({"month": ms, "total": round(mr[0]["total"], 2) if mr else 0, "count": mr[0]["count"] if mr else 0})

    # Recent 20 transactions
    recent = await db.donations.find({**src, "tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)

    # Counts by source (for the UI toggle badge)
    stripe_count = await db.donations.count_documents({"tenant_id": tenant_id, "payment_source": "stripe"})
    demo_count = await db.donations.count_documents({"tenant_id": tenant_id, "$or": [{"payment_source": {"$ne": "stripe"}}, {"payment_source": {"$exists": False}}]})

    return {
        "today": today, "week": week, "month": month, "ytd": ytd,
        "active_recurring": recurring_count, "avg_gift": avg_gift, "top_fund": top_fund,
        "trend": trend, "recent_transactions": [serialize_doc(d) for d in recent],
        "source_filter": source or "all",
        "source_counts": {"stripe": stripe_count, "demo": demo_count, "total": stripe_count + demo_count},
    }


@router.get("/admin/solomonpay/transactions")
async def solomonpay_transactions(
    request: Request,
    page: int = 1, per_page: int = 50,
    fund: Optional[str] = None, donor: Optional[str] = None,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    amount_min: Optional[float] = None, amount_max: Optional[float] = None,
    payment_method: Optional[str] = None, sort_by: str = "donation_date", sort_dir: str = "desc",
    search: Optional[str] = None, source: Optional[str] = None,
):
    """Full transaction list with filtering. `source` filters by payment_source
    (stripe | demo | None for all)."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if source == "stripe":
        query["payment_source"] = "stripe"
    elif source == "demo":
        query["$or"] = [{"payment_source": {"$ne": "stripe"}}, {"payment_source": {"$exists": False}}]
    if fund:
        query["fund_name"] = fund
    if donor:
        query["$or"] = [{"person_name": {"$regex": donor, "$options": "i"}}, {"person_id": donor}]
    if date_from:
        query.setdefault("donation_date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("donation_date", {})["$lte"] = date_to
    if amount_min is not None:
        query.setdefault("amount", {})["$gte"] = amount_min
    if amount_max is not None:
        query.setdefault("amount", {})["$lte"] = amount_max
    if payment_method:
        query["payment_method"] = payment_method
    if search:
        query["$or"] = [{"person_name": {"$regex": search, "$options": "i"}}, {"transaction_id": {"$regex": search, "$options": "i"}}]

    sort_dir_val = -1 if sort_dir == "desc" else 1
    total = await db.donations.count_documents(query)
    skip = (page - 1) * per_page
    docs = await db.donations.find(query, {"_id": 0}).sort(sort_by, sort_dir_val).skip(skip).limit(per_page).to_list(per_page)

    return {"data": [serialize_doc(d) for d in docs], "total": total, "page": page, "per_page": per_page}


@router.get("/admin/solomonpay/transactions/export")
async def export_transactions_csv(request: Request, date_from: Optional[str] = None, date_to: Optional[str] = None):
    """Export transactions as CSV."""
    from fastapi.responses import StreamingResponse
    import io, csv
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if date_from:
        query.setdefault("donation_date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("donation_date", {})["$lte"] = date_to
    docs = await db.donations.find(query, {"_id": 0}).sort("donation_date", -1).to_list(10000)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Date", "Donor", "Fund", "Amount", "Method", "Status", "Transaction ID"])
    for d in docs:
        w.writerow([d.get("donation_date"), d.get("person_name", "Anonymous"), d.get("fund_name", "General"), d.get("amount", 0), d.get("payment_method", ""), d.get("status", ""), d.get("transaction_id", "")])
    buf.seek(0)
    return StreamingResponse(io.BytesIO(buf.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=solomonpay_transactions.csv"})


@router.get("/admin/solomonpay/payouts")
async def get_payouts(request: Request):
    """Get payout history and balance."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    # Calculate available balance (sum of completed donations minus past payouts)
    donation_total_r = await db.donations.aggregate([{"$match": {"tenant_id": tenant_id}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]).to_list(1)
    donation_total = donation_total_r[0]["total"] if donation_total_r else 0
    payout_total_r = await db.payouts.aggregate([{"$match": {"tenant_id": tenant_id, "status": {"$in": ["completed", "processing"]}}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]).to_list(1)
    payout_total = payout_total_r[0]["total"] if payout_total_r else 0
    available = round(donation_total - payout_total, 2)

    payouts = await db.payouts.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"available_balance": max(0, available), "payouts": [serialize_doc(p) for p in payouts]}


@router.post("/admin/solomonpay/payouts/request")
async def request_payout(request: Request):
    """Request a payout (instant or standard)."""
    user = await _get_admin(request, "admin.giving.payouts")
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    payout_type = body.get("type", "standard")  # "instant" or "standard"
    amount = body.get("amount", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    fee = round(amount * 0.015, 2) if payout_type == "instant" else 0
    net = round(amount - fee, 2)

    arrival_delta = timedelta(minutes=30) if payout_type == "instant" else timedelta(days=3)
    payout = {
        "id": f"po_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "amount": amount,
        "fee": fee,
        "net_amount": net,
        "type": payout_type,
        "status": "processing" if payout_type == "instant" else "pending",
        "estimated_arrival": (datetime.now(timezone.utc) + arrival_delta).isoformat(),
        "requested_by": user.get("name", user.get("email")),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.payouts.insert_one(payout)
    return {"message": f"Payout of ${net:.2f} requested", "payout": {k: v for k, v in payout.items() if k != "_id"}}


@router.get("/admin/solomonpay/donors")
async def get_donors(request: Request, search: Optional[str] = None, page: int = 1, per_page: int = 50):
    """List all donors with lifetime stats."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    # Aggregate donors from donations
    match = {"tenant_id": tenant_id}
    if search:
        match["person_name"] = {"$regex": search, "$options": "i"}
    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": "$person_id",
            "name": {"$first": "$person_name"},
            "email": {"$first": "$person_email"},
            "lifetime_total": {"$sum": "$amount"},
            "donation_count": {"$sum": 1},
            "first_gift": {"$min": "$donation_date"},
            "last_gift": {"$max": "$donation_date"},
        }},
        {"$sort": {"lifetime_total": -1}},
        {"$skip": (page - 1) * per_page},
        {"$limit": per_page},
    ]
    donors = await db.donations.aggregate(pipeline).to_list(per_page)
    # Count total unique donors
    count_pipeline = [{"$match": match}, {"$group": {"_id": "$person_id"}}, {"$count": "total"}]
    count_r = await db.donations.aggregate(count_pipeline).to_list(1)
    total = count_r[0]["total"] if count_r else 0

    for d in donors:
        d["person_id"] = d.pop("_id")
        d["lifetime_total"] = round(d["lifetime_total"], 2)
        # Check for active recurring
        rec = await db.recurring_giving.find_one({"person_id": d["person_id"], "is_active": True, "tenant_id": tenant_id}, {"_id": 0, "amount": 1, "frequency": 1})
        d["recurring"] = rec

    return {"donors": donors, "total": total}


@router.get("/admin/solomonpay/donors/{person_id}")
async def get_donor_detail(request: Request, person_id: str):
    """Get a donor's full giving profile."""
    user = await _get_admin(request, "admin.giving.donors")
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    person = await db.people.find_one({"id": person_id, "tenant_id": tenant_id}, {"_id": 0})
    donations = await db.donations.find({"person_id": person_id, "tenant_id": tenant_id}, {"_id": 0}).sort("donation_date", -1).to_list(500)
    lifetime = sum(d.get("amount", 0) for d in donations)

    # By year
    by_year = {}
    for d in donations:
        yr = d.get("donation_date", "")[:4]
        by_year.setdefault(yr, 0)
        by_year[yr] = round(by_year[yr] + d.get("amount", 0), 2)

    # By fund
    by_fund = {}
    for d in donations:
        fn = d.get("fund_name", "General Fund")
        by_fund.setdefault(fn, 0)
        by_fund[fn] = round(by_fund[fn] + d.get("amount", 0), 2)

    recurring = await db.recurring_giving.find({"person_id": person_id, "tenant_id": tenant_id}, {"_id": 0}).to_list(10)

    return {
        "person": serialize_doc(person) if person else {"id": person_id, "first_name": "Unknown", "last_name": ""},
        "donations": [serialize_doc(d) for d in donations[:100]],
        "lifetime_total": round(lifetime, 2),
        "donation_count": len(donations),
        "by_year": [{"year": k, "total": v} for k, v in sorted(by_year.items(), reverse=True)],
        "by_fund": [{"fund": k, "total": v} for k, v in sorted(by_fund.items(), key=lambda x: -x[1])],
        "recurring": [serialize_doc(r) for r in recurring],
    }


@router.post("/admin/solomonpay/statements/bulk")
async def bulk_generate_statements(request: Request):
    """Bulk generate year-end statements for all donors."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    year = body.get("year", datetime.now(timezone.utc).year - 1)

    # Get all unique donors for the year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    pipeline = [
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": "$person_id", "name": {"$first": "$person_name"}, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}},
    ]
    donors = await db.donations.aggregate(pipeline).to_list(10000)
    total_donors = len(donors)
    total_amount = round(sum(d["total"] for d in donors), 2)

    # Record the bulk job
    job = {
        "id": f"stmt_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "year": year,
        "donor_count": total_donors,
        "total_amount": total_amount,
        "status": "completed",
        "requested_by": user.get("name", user.get("email")),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.statement_jobs.insert_one(job)
    return {"message": f"Generated {total_donors} statements for {year}", "job": {k: v for k, v in job.items() if k != "_id"}, "donors": [{"person_id": d["_id"], "name": d["name"], "total": round(d["total"], 2), "count": d["count"]} for d in donors[:100]]}


@router.get("/admin/solomonpay/settings")
async def get_solomonpay_settings(request: Request):
    """Get SolomonPay configuration."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    settings = await db.solomonpay_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not settings:
        settings = {
            "tenant_id": tenant_id,
            "payout_schedule": "weekly",
            "bank_connected": False,
            "bank_last_four": None,
            "bank_name": None,
            "show_processing_fees": True,
            "receipt_email_enabled": True,
            "receipt_email_template": "default",
        }
    return settings


@router.put("/admin/solomonpay/settings")
async def update_solomonpay_settings(request: Request):
    """Update SolomonPay configuration."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    body["tenant_id"] = tenant_id
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.solomonpay_settings.update_one({"tenant_id": tenant_id}, {"$set": body}, upsert=True)
    return {"message": "Settings updated"}


# Fund management (CRUD)
@router.get("/admin/solomonpay/funds")
async def get_funds(request: Request):
    """Get all funds with giving totals."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    funds = await db.funds.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(100)
    # Enrich with totals
    for f in funds:
        pipeline = [{"$match": {"tenant_id": tenant_id, "fund_id": f["id"]}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}]
        r = await db.donations.aggregate(pipeline).to_list(1)
        f["total_received"] = round(r[0]["total"], 2) if r else 0
        f["donation_count"] = r[0]["count"] if r else 0
    return {"funds": [serialize_doc(f) for f in funds]}


@router.post("/admin/solomonpay/funds")
async def create_fund(request: Request):
    """Create a new fund."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    fund = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": body.get("name", "New Fund"),
        "description": body.get("description", ""),
        "goal_amount": body.get("goal_amount"),
        "current_amount": 0,
        "is_active": True,
        "is_archived": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.funds.insert_one(fund)
    return {"message": "Fund created", "fund": {k: v for k, v in fund.items() if k != "_id"}}


@router.put("/admin/solomonpay/funds/{fund_id}")
async def update_fund(request: Request, fund_id: str):
    """Update a fund."""
    user = await _get_admin(request)
    body = await request.json()
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    body.pop("id", None)
    body.pop("_id", None)
    await db.funds.update_one({"id": fund_id}, {"$set": body})
    return {"message": "Fund updated"}


@router.delete("/admin/solomonpay/funds/{fund_id}")
async def archive_fund(request: Request, fund_id: str):
    """Archive (soft-delete) a fund."""
    user = await _get_admin(request)
    await db.funds.update_one({"id": fund_id}, {"$set": {"is_archived": True, "is_active": False}})
    return {"message": "Fund archived"}


# ═══════════════════ GAP CLOSURE: DonorIQ Engagement Stages ═══════════════════

def _classify_donor_stage(donation_count, last_gift_date, has_recurring):
    """Classify donor into SecureGive-style engagement stages."""
    if has_recurring:
        return "recurring"
    if not last_gift_date:
        return "lapsed"
    try:
        last = datetime.fromisoformat(last_gift_date) if isinstance(last_gift_date, str) else last_gift_date
    except Exception:
        return "lapsed"
    days_since = (datetime.now(timezone.utc) - last.replace(tzinfo=timezone.utc if last.tzinfo is None else last.tzinfo)).days
    if days_since > 180:
        return "lapsed"
    if days_since > 90:
        return "at_risk"
    if donation_count == 1:
        return "once"
    if donation_count <= 3:
        return "occasional"
    return "regular"


@router.get("/admin/solomonpay/donor-insights")
async def donor_insights(request: Request):
    """DonorIQ-style engagement breakdown."""
    user = await _get_admin(request, "admin.giving.view")
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": "$person_id",
            "name": {"$first": "$person_name"},
            "count": {"$sum": 1},
            "total": {"$sum": "$amount"},
            "last_gift": {"$max": "$donation_date"},
        }},
    ]
    donors = await db.donations.aggregate(pipeline).to_list(10000)

    # Check recurring status for each donor
    recurring_ids = set()
    recs = await db.recurring_giving.find({"tenant_id": tenant_id, "is_active": True}, {"_id": 0, "person_id": 1}).to_list(10000)
    for r in recs:
        recurring_ids.add(r.get("person_id"))

    stages = {"once": 0, "occasional": 0, "regular": 0, "recurring": 0, "at_risk": 0, "lapsed": 0}
    stage_donors = {"once": [], "occasional": [], "regular": [], "recurring": [], "at_risk": [], "lapsed": []}

    for d in donors:
        stage = _classify_donor_stage(d["count"], d["last_gift"], d["_id"] in recurring_ids)
        stages[stage] = stages.get(stage, 0) + 1
        if len(stage_donors[stage]) < 10:
            stage_donors[stage].append({"person_id": d["_id"], "name": d["name"], "total": round(d["total"], 2), "count": d["count"], "last_gift": d["last_gift"]})

    return {
        "total_donors": len(donors),
        "stages": stages,
        "stage_donors": stage_donors,
    }


# ═══════════════════ GAP CLOSURE: Virtual Terminal ═══════════════════

@router.post("/admin/solomonpay/virtual-terminal")
async def virtual_terminal(request: Request):
    """Process a donation on behalf of a donor (phone/in-person)."""
    user = await _get_admin(request, "admin.giving.edit")
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()

    person_id = body.get("person_id")
    person_name = body.get("person_name", "Walk-in Donor")
    amount = body.get("amount", 0)
    fund_name = body.get("fund_name", "General Fund")
    fund_id = body.get("fund_id", "general")
    payment_method = body.get("payment_method", "cash")
    note = body.get("note", "")
    cover_fees = body.get("cover_fees", False)

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    processing_fee = round(amount * 0.025 + 0.30, 2) if cover_fees else 0
    total = round(amount + processing_fee, 2)

    donation = {
        "id": f"don_{uuid.uuid4().hex[:12]}",
        "transaction_id": f"vt_{uuid.uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "person_id": person_id or f"walk-in-{uuid.uuid4().hex[:6]}",
        "person_name": person_name,
        "person_email": body.get("person_email", ""),
        "amount": total,
        "base_amount": amount,
        "processing_fee": processing_fee,
        "fees_covered_by_donor": cover_fees,
        "fund_id": fund_id,
        "fund_name": fund_name,
        "payment_method": payment_method,
        "source": "virtual_terminal",
        "status": "completed",
        "note": note,
        "processed_by": user.get("name", user.get("email")),
        "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.donations.insert_one(donation)
    return {"message": f"${amount:.2f} donation processed for {person_name}", "donation": {k: v for k, v in donation.items() if k != "_id"}}


# ═══════════════════ GAP CLOSURE: Refund ═══════════════════

@router.post("/admin/solomonpay/refund/{donation_id}")
async def refund_donation(request: Request, donation_id: str):
    """Refund a donation."""
    user = await _get_admin(request, "admin.giving.edit")
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    donation = await db.donations.find_one({"id": donation_id, "tenant_id": tenant_id}, {"_id": 0})
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    if donation.get("status") == "refunded":
        raise HTTPException(status_code=400, detail="Already refunded")

    await db.donations.update_one({"id": donation_id}, {"$set": {
        "status": "refunded",
        "refunded_at": datetime.now(timezone.utc).isoformat(),
        "refunded_by": user.get("name", user.get("email")),
    }})

    # Record refund as negative donation
    refund = {
        "id": f"ref_{uuid.uuid4().hex[:12]}",
        "transaction_id": f"ref_{donation.get('transaction_id', '')}",
        "tenant_id": tenant_id,
        "person_id": donation.get("person_id"),
        "person_name": donation.get("person_name"),
        "amount": -donation.get("amount", 0),
        "fund_id": donation.get("fund_id"),
        "fund_name": donation.get("fund_name"),
        "payment_method": donation.get("payment_method"),
        "source": "refund",
        "status": "completed",
        "original_donation_id": donation_id,
        "processed_by": user.get("name", user.get("email")),
        "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.donations.insert_one(refund)
    return {"message": f"Refund of ${abs(donation.get('amount', 0)):.2f} processed", "refund": {k: v for k, v in refund.items() if k != "_id"}}


# ═══════════════════ GAP CLOSURE: QR Code Giving ═══════════════════

@router.get("/admin/solomonpay/qr-codes")
async def generate_qr_codes(request: Request):
    """Generate QR codes for giving links."""
    user = await _get_admin(request, "admin.giving.view")
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID

    # Get active funds
    funds = await db.funds.find({"tenant_id": tenant_id, "is_active": True, "is_archived": {"$ne": True}}, {"_id": 0, "id": 1, "name": 1}).to_list(50)

    org = await db.organizations.find_one({"id": tenant_id}, {"_id": 0, "website": 1, "name": 1})
    base_url = org.get("website", "") if org else ""

    qr_codes = [
        {"label": "General Giving", "url": f"{base_url}/portal/give", "fund": "general"},
    ]
    for f in funds:
        qr_codes.append({"label": f"Give to {f['name']}", "url": f"{base_url}/portal/give?fund={f['id']}", "fund": f["id"]})

    return {"qr_codes": qr_codes, "note": "Use any QR code generator to create scannable codes from these URLs."}



# ═══ Recurring Giving Scheduler Admin ═══

@router.get("/admin/solomonpay/scheduler/status")
async def get_scheduler_status(request: Request):
    """Get recurring giving scheduler status, stats, and recent runs."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Active schedules
    active_count = await db.recurring_giving.count_documents(
        {"tenant_id": tenant_id, "is_active": True}
    )
    paused_count = await db.recurring_giving.count_documents(
        {"tenant_id": tenant_id, "is_active": False, "paused_reason": {"$exists": True}}
    )
    # Due today
    due_today = await db.recurring_giving.count_documents(
        {"tenant_id": tenant_id, "is_active": True, "next_charge_date": {"$lte": today_str}}
    )
    # Failed queue
    failed_queue = await db.recurring_giving.find(
        {"tenant_id": tenant_id, "is_active": True, "consecutive_failures": {"$gt": 0}},
        {"_id": 0, "id": 1, "person_id": 1, "amount": 1, "frequency": 1,
         "consecutive_failures": 1, "last_failure_reason": 1, "next_charge_date": 1}
    ).limit(20).to_list(20)
    # Auto-paused
    auto_paused = await db.recurring_giving.find(
        {"tenant_id": tenant_id, "paused_reason": "auto_paused_3_failures"},
        {"_id": 0, "id": 1, "person_id": 1, "amount": 1, "last_failure_reason": 1}
    ).limit(20).to_list(20)

    # Recent runs (platform-wide — runs are not tenant-scoped)
    recent_runs = await db.recurring_giving_runs.find(
        {}, {"_id": 0}
    ).sort("started_at", -1).limit(10).to_list(10)

    # Next scheduled run estimate (30s after startup + interval)
    from services.recurring_scheduler import SCHEDULER_INTERVAL_SECONDS
    next_run_approx = (datetime.now(timezone.utc) + timedelta(seconds=SCHEDULER_INTERVAL_SECONDS)).isoformat()

    return {
        "scheduler": {
            "active": True,
            "interval_seconds": SCHEDULER_INTERVAL_SECONDS,
            "next_run_estimate": next_run_approx,
        },
        "stats": {
            "active_schedules": active_count,
            "paused_schedules": paused_count,
            "due_today": due_today,
            "failed_retry_queue": len(failed_queue),
            "auto_paused_count": len(auto_paused),
        },
        "failed_queue": [serialize_doc(r) for r in failed_queue],
        "auto_paused": [serialize_doc(r) for r in auto_paused],
        "recent_runs": [serialize_doc(r) for r in recent_runs],
    }


@router.post("/admin/solomonpay/scheduler/run-now")
async def trigger_scheduler_run(request: Request):
    """Manually trigger a scheduler batch run immediately."""
    user = await _get_admin(request)
    from services.recurring_scheduler import run_recurring_batch
    result = await run_recurring_batch(db)
    return {
        "message": "Batch run completed",
        "run_id": result["id"],
        "successful": result["successful"],
        "failed": result["failed"],
        "skipped": result["skipped"],
        "total_scheduled": result["total_scheduled"],
        "duration_ms": result["duration_ms"],
    }


@router.post("/admin/solomonpay/scheduler/resume/{schedule_id}")
async def admin_resume_schedule(request: Request, schedule_id: str):
    """Resume an auto-paused recurring giving schedule."""
    user = await _get_admin(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    schedule = await db.recurring_giving.find_one(
        {"id": schedule_id, "tenant_id": tenant_id}, {"_id": 0}
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    from routes.portal import _calculate_next_charge_date
    next_date = _calculate_next_charge_date(schedule.get("frequency", "monthly"))
    await db.recurring_giving.update_one(
        {"id": schedule_id},
        {"$set": {
            "is_active": True,
            "consecutive_failures": 0,
            "paused_reason": None,
            "last_failure_reason": None,
            "next_charge_date": next_date,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    return {"message": "Schedule resumed", "next_charge_date": next_date}
