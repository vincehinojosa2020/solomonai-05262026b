"""Solomon AI — Admin Giving Routes"""
from fastapi import APIRouter, HTTPException, Request, Response, Header
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import csv
import io
import logging

from core import (
    db, DEFAULT_TENANT_ID,
    get_current_admin_user, require_permission, require_tenant,
    logger,
)
from core.helpers import serialize_doc, get_tenant_giving_metrics
from models.schemas import Fund, Group, Person, Tenant

router = APIRouter()

@router.get("/admin/giving/summary")
async def get_admin_giving_summary(request: Request):
    """Tenant-scoped giving summary endpoint for admin dashboard."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    return await get_tenant_giving_metrics(tenant_id)

# --- PEOPLE ROUTES ---
@router.get("/people")

@router.get("/admin/giving/report")
async def get_giving_report(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fund_id: Optional[str] = None,
    group_by: str = "day"  # day, week, month, fund, donor
):
    """Get giving report with aggregated statistics"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    
    query = {"tenant_id": tenant_id, "status": "completed"}
    
    if start_date:
        query["donation_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("donation_date", {})["$lte"] = end_date
    if fund_id:
        query["fund_id"] = fund_id
    
    # Basic statistics
    total_donations = await db.donations.count_documents(query)
    
    # Sum total amount
    sum_pipeline = [
        {"$match": query},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    sum_result = await db.donations.aggregate(sum_pipeline).to_list(1)
    total_amount = sum_result[0]["total"] if sum_result else 0
    
    # Group by specified field
    if group_by == "fund":
        group_pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$fund_id",
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"}
            }},
            {"$lookup": {
                "from": "funds",
                "localField": "_id",
                "foreignField": "id",
                "as": "fund"
            }},
            {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "_id": 0,
                "label": {"$ifNull": ["$fund.name", "$_id"]},
                "count": 1,
                "total": 1
            }},
            {"$sort": {"total": -1}}
        ]
    elif group_by == "donor":
        group_pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$person_id",
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"}
            }},
            {"$lookup": {
                "from": "people",
                "localField": "_id",
                "foreignField": "id",
                "as": "donor"
            }},
            {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "_id": 0,
                "label": {"$concat": [{"$ifNull": ["$donor.first_name", ""]}, " ", {"$ifNull": ["$donor.last_name", "Anonymous"]}]},
                "count": 1,
                "total": 1
            }},
            {"$sort": {"total": -1}},
            {"$limit": 20}
        ]
    elif group_by == "month":
        group_pipeline = [
            {"$match": query},
            {"$group": {
                "_id": {"$substr": ["$donation_date", 0, 7]},  # YYYY-MM
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"}
            }},
            {"$project": {
                "_id": 0,
                "label": "$_id",
                "count": 1,
                "total": 1
            }},
            {"$sort": {"label": -1}}
        ]
    else:  # day
        group_pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$donation_date",
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"}
            }},
            {"$project": {
                "_id": 0,
                "label": "$_id",
                "count": 1,
                "total": 1
            }},
            {"$sort": {"label": -1}},
            {"$limit": 30}
        ]
    
    breakdown = await db.donations.aggregate(group_pipeline).to_list(100)
    
    # Get recent donations
    recent_pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "people",
            "localField": "person_id",
            "foreignField": "id",
            "as": "donor"
        }},
        {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "funds",
            "localField": "fund_id",
            "foreignField": "id",
            "as": "fund"
        }},
        {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "amount": 1,
            "donation_date": 1,
            "payment_method": 1,
            "donor_name": {"$concat": [{"$ifNull": ["$donor.first_name", ""]}, " ", {"$ifNull": ["$donor.last_name", "Anonymous"]}]},
            "donor_email": "$donor.email",
            "fund_name": "$fund.name"
        }},
        {"$sort": {"donation_date": -1}},
        {"$limit": 50}
    ]
    recent = await db.donations.aggregate(recent_pipeline).to_list(50)
    
    return {
        "summary": {
            "total_donations": total_donations,
            "total_amount": total_amount,
            "average_donation": total_amount / total_donations if total_donations > 0 else 0,
            "date_range": {"start": start_date, "end": end_date}
        },
        "breakdown": breakdown,
        "recent_donations": recent
    }


@router.get("/admin/giving/export")
async def export_giving_csv(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fund_id: Optional[str] = None
):
    """Export giving data as CSV"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    
    query = {"tenant_id": tenant_id, "status": "completed"}
    
    if start_date:
        query["donation_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("donation_date", {})["$lte"] = end_date
    if fund_id:
        query["fund_id"] = fund_id
    
    # Get all donations with donor and fund info
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "people",
            "localField": "person_id",
            "foreignField": "id",
            "as": "donor"
        }},
        {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "funds",
            "localField": "fund_id",
            "foreignField": "id",
            "as": "fund"
        }},
        {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "donation_date": 1,
            "amount": 1,
            "payment_method": 1,
            "check_number": 1,
            "donor_first_name": "$donor.first_name",
            "donor_last_name": "$donor.last_name",
            "donor_email": "$donor.email",
            "donor_phone": "$donor.phone",
            "donor_address": "$donor.address",
            "fund_name": "$fund.name",
            "notes": 1,
            "transaction_id": 1
        }},
        {"$sort": {"donation_date": -1}}
    ]
    
    donations = await db.donations.aggregate(pipeline).to_list(10000)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Date", "Amount", "Payment Method", "Check #",
        "First Name", "Last Name", "Email", "Phone", "Address",
        "Fund", "Notes", "Transaction ID"
    ])
    
    # Data rows
    for d in donations:
        writer.writerow([
            d.get("donation_date", ""),
            f"${d.get('amount', 0):.2f}",
            d.get("payment_method", ""),
            d.get("check_number", ""),
            d.get("donor_first_name", ""),
            d.get("donor_last_name", ""),
            d.get("donor_email", ""),
            d.get("donor_phone", ""),
            d.get("donor_address", ""),
            d.get("fund_name", ""),
            d.get("notes", ""),
            d.get("transaction_id", "")
        ])
    
    output.seek(0)
    
    # Generate filename
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"giving_report_{date_str}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/admin/giving/year-end-statement/{person_id}")
async def get_year_end_statement(request: Request, person_id: str, year: int = 2025):
    """Generate year-end giving statement data for a specific person"""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    
    # Get person info
    person = await db.people.find_one({"id": person_id, "tenant_id": tenant_id}, {"_id": 0})
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Get all donations for this person in the specified year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    pipeline = [
        {"$match": {
            "tenant_id": tenant_id,
            "person_id": person_id,
            "status": "completed",
            "donation_date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$lookup": {
            "from": "funds",
            "localField": "fund_id",
            "foreignField": "id",
            "as": "fund"
        }},
        {"$unwind": {"path": "$fund", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "donation_date": 1,
            "amount": 1,
            "payment_method": 1,
            "check_number": 1,
            "fund_name": "$fund.name"
        }},
        {"$sort": {"donation_date": 1}}
    ]
    
    donations = await db.donations.aggregate(pipeline).to_list(1000)
    
    # Calculate totals by fund
    fund_totals = {}
    for d in donations:
        fund = d.get("fund_name", "General")
        fund_totals[fund] = fund_totals.get(fund, 0) + d.get("amount", 0)
    
    total_amount = sum(d.get("amount", 0) for d in donations)
    
    # Get church/tenant info
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    
    return {
        "statement": {
            "year": year,
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
            "church": {
                "name": tenant.get("name", "Church") if tenant else "Church",
                "address": tenant.get("address", "") if tenant else "",
                "city": tenant.get("city", "") if tenant else "",
                "state": tenant.get("state", "") if tenant else "",
                "ein": tenant.get("ein", "XX-XXXXXXX") if tenant else "XX-XXXXXXX"
            },
            "donor": {
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "address": person.get("address", ""),
                "city": person.get("city", ""),
                "state": person.get("state", ""),
                "zip": person.get("zip", "")
            },
            "donations": donations,
            "fund_totals": [{"fund": k, "total": v} for k, v in fund_totals.items()],
            "total_amount": total_amount,
            "donation_count": len(donations),
            "disclaimer": "No goods or services were provided in exchange for these contributions except intangible religious benefits."
        }
    }


@router.get("/admin/giving/processor-settings")
async def get_processor_settings(request: Request):
    """Get configured payment processor for this tenant."""
    user = await require_permission(request, "admin.giving")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    settings = await db.payment_processor_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not settings:
        settings = {"tenant_id": tenant_id, "active_processor": "manual", "processors": {"manual": {"enabled": True, "status": "connected"}}}
    return settings


@router.get("/admin/giving/settings")
async def get_giving_settings_alias(request: Request):
    """Alias for processor-settings."""
    return await get_processor_settings(request)


@router.post("/admin/giving/processor-settings")
async def update_processor_settings(request: Request, payload: dict):
    """Configure payment processor for this tenant."""
    user = await require_permission(request, "admin.giving")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    processor_id = payload.get("processor_id")
    action = payload.get("action", "connect")

    if processor_id not in PAYMENT_PROCESSORS:
        raise HTTPException(status_code=400, detail=f"Unknown processor: {processor_id}")

    settings = await db.payment_processor_settings.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not settings:
        settings = {"tenant_id": tenant_id, "active_processor": "manual", "processors": {"manual": {"enabled": True, "status": "connected"}}}

    if action == "connect":
        settings["processors"][processor_id] = {
            "enabled": True,
            "status": "connected",
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "config": payload.get("config", {}),
        }
        settings["active_processor"] = processor_id
    elif action == "disconnect":
        if processor_id in settings.get("processors", {}):
            settings["processors"][processor_id]["enabled"] = False
            settings["processors"][processor_id]["status"] = "disconnected"
        if settings.get("active_processor") == processor_id:
            settings["active_processor"] = "manual"
    elif action == "set_active":
        if processor_id in settings.get("processors", {}) and settings["processors"][processor_id].get("enabled"):
            settings["active_processor"] = processor_id
        else:
            raise HTTPException(status_code=400, detail=f"Processor {processor_id} is not connected")

    settings["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.payment_processor_settings.update_one({"tenant_id": tenant_id}, {"$set": settings}, upsert=True)

    return {"success": True, "active_processor": settings["active_processor"], "processors": settings["processors"]}


@router.post("/admin/giving/settings")
async def update_giving_settings_alias(request: Request, payload: dict):
    """Alias for processor-settings POST."""
    return await update_processor_settings(request, payload)


@router.get("/admin/giving/integrations")
async def get_giving_integrations(request: Request):
    """Get giving processor integration status for current church."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    config = await db.giving_integrations.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not config:
        config = {
            "tenant_id": tenant_id,
            "active_processor": None,
            "processors": {
                "solomon_pay": {"enabled": False, "status": "not_connected", "label": "Solomon Pay", "description": "Native giving powered by Solomon AI. Lowest fees, seamless integration."},
                "pushpay": {"enabled": False, "status": "not_connected", "label": "Pushpay", "description": "Connect your existing Pushpay account for seamless giving sync."},
                "securegive": {"enabled": False, "status": "not_connected", "label": "SecureGive", "description": "Integrate with SecureGive for church giving management."},
            },
        }
    return config


@router.post("/admin/giving/integrations/connect")
async def connect_giving_processor(request: Request):
    """Connect a giving processor (mocked for demo)."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    processor = body.get("processor")
    if processor not in ("solomon_pay", "pushpay", "securegive"):
        raise HTTPException(status_code=400, detail="Invalid processor. Choose: solomon_pay, pushpay, securegive")

    now_iso = datetime.now(timezone.utc).isoformat()
    # Mark the selected processor as active, deactivate others
    update_set = {
        "tenant_id": tenant_id,
        "active_processor": processor,
        f"processors.{processor}.enabled": True,
        f"processors.{processor}.status": "active",
        f"processors.{processor}.connected_at": now_iso,
        f"processors.{processor}.connected_by": user.get("name", ""),
        "updated_at": now_iso,
    }
    # Deactivate other processors
    for p in ("solomon_pay", "pushpay", "securegive"):
        if p != processor:
            update_set[f"processors.{p}.enabled"] = False
            update_set[f"processors.{p}.status"] = "not_connected"

    await db.giving_integrations.update_one(
        {"tenant_id": tenant_id},
        {"$set": update_set, "$setOnInsert": {"created_at": now_iso}},
        upsert=True
    )
    return {"success": True, "active_processor": processor, "message": f"{processor.replace('_', ' ').title()} connected successfully"}


@router.post("/admin/giving/integrations/disconnect")
async def disconnect_giving_processor(request: Request):
    """Disconnect the active giving processor."""
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    processor = body.get("processor")
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.giving_integrations.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            f"processors.{processor}.enabled": False,
            f"processors.{processor}.status": "not_connected",
            "active_processor": None,
            "updated_at": now_iso,
        }}
    )
    return {"success": True, "message": f"{processor.replace('_', ' ').title()} disconnected"}


# ============== DEMO QUALITY DATA SEED ==============

