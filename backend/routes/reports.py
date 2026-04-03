"""Solomon AI — Reports Routes"""
from fastapi import APIRouter, HTTPException, Request, Response, Header
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import csv
import io
import logging

from core import (
    db, DEFAULT_TENANT_ID,
    require_permission, audit_log,
    logger,
)
from core.helpers import serialize_doc
from models.schemas import Attendance, Child, Fund, Group, Person, Service, User

router = APIRouter()

@router.get("/reports/giving-by-fund")
async def report_giving_by_fund(start_date: str, end_date: str):
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {
            "tenant_id": tenant_id,
            "donation_date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$lookup": {
            "from": "funds",
            "localField": "fund_id",
            "foreignField": "id",
            "as": "fund"
        }},
        {"$unwind": "$fund"},
        {"$group": {
            "_id": {"fund_id": "$fund_id", "fund_name": "$fund.name"},
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "fund_id": "$_id.fund_id",
            "fund_name": "$_id.fund_name",
            "total": 1,
            "count": 1
        }}
    ]
    
    results = await db.donations.aggregate(pipeline).to_list(20)
    return results


@router.get("/reports/giving-by-method")
async def report_giving_by_method(start_date: str, end_date: str):
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {
            "tenant_id": tenant_id,
            "donation_date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$group": {
            "_id": "$payment_method",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "method": "$_id",
            "total": 1,
            "count": 1
        }}
    ]
    
    results = await db.donations.aggregate(pipeline).to_list(20)
    return results


@router.get("/reports/top-donors")
async def report_top_donors(start_date: str, end_date: str, limit: int = 20):
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {
            "tenant_id": tenant_id,
            "donation_date": {"$gte": start_date, "$lte": end_date},
            "person_id": {"$ne": None}
        }},
        {"$group": {
            "_id": "$person_id",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from": "people",
            "localField": "_id",
            "foreignField": "id",
            "as": "person"
        }},
        {"$unwind": "$person"},
        {"$project": {
            "_id": 0,
            "person_id": "$_id",
            "name": {"$concat": ["$person.first_name", " ", "$person.last_name"]},
            "total": 1,
            "count": 1
        }}
    ]
    
    results = await db.donations.aggregate(pipeline).to_list(limit)
    return results


@router.get("/reports/membership")
async def report_membership():
    tenant_id = DEFAULT_TENANT_ID
    
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": "$membership_status",
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "status": "$_id",
            "count": 1
        }}
    ]
    
    results = await db.people.aggregate(pipeline).to_list(10)
    total = sum(r["count"] for r in results)
    
    return {
        "by_status": results,
        "total": total
    }

# ============== EXTENDED REPORT ENDPOINTS (Task 6) ==============


@router.get("/reports/kids-history")
async def report_kids_history(start_date: str = None, end_date: str = None):
    """Kids check-in/check-out history report."""
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if start_date:
        query["checked_in_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("checked_in_at", {})["$lte"] = end_date + "T23:59:59"

    records = await db.kids_checkins.find(query, {"_id": 0}).sort("checked_in_at", -1).to_list(500)
    total_checkins = len(records)
    unique_kids = len(set(r.get("child_id", "") for r in records))
    checked_out = sum(1 for r in records if r.get("checked_out_at"))
    return {
        "records": records,
        "summary": {"total_checkins": total_checkins, "unique_kids": unique_kids, "checked_out": checked_out, "still_checked_in": total_checkins - checked_out}
    }


@router.get("/reports/attendance")
async def report_attendance(start_date: str = None, end_date: str = None):
    """Attendance report with weekly breakdown."""
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if start_date:
        query["service_date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("service_date", {})["$lte"] = end_date

    checkins = await db.member_checkins.find(query, {"_id": 0}).sort("service_date", -1).to_list(2000)
    by_date = {}
    for c in checkins:
        d = c.get("service_date", "unknown")
        by_date.setdefault(d, {"date": d, "in_person": 0, "online": 0, "total": 0})
        t = c.get("check_in_type", "in_person")
        by_date[d][t if t in ("in_person", "online") else "in_person"] += 1
        by_date[d]["total"] += 1
    weekly = sorted(by_date.values(), key=lambda x: x["date"], reverse=True)
    return {
        "weekly": weekly,
        "summary": {"total_services": len(weekly), "total_checkins": len(checkins), "avg_per_service": round(len(checkins) / max(len(weekly), 1), 1)}
    }


@router.get("/reports/cafe")
async def report_cafe(start_date: str = None, end_date: str = None):
    """Cafe orders report."""
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date + "T23:59:59"

    orders = await db.cafe_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    total_revenue = sum(o.get("total", 0) for o in orders)
    item_counts = {}
    for o in orders:
        for item in o.get("items", []):
            name = item.get("name", "Unknown")
            item_counts[name] = item_counts.get(name, 0) + item.get("quantity", 1)
    top_items = sorted([{"name": k, "quantity": v} for k, v in item_counts.items()], key=lambda x: x["quantity"], reverse=True)[:10]
    return {
        "orders": orders[:100],
        "summary": {"total_orders": len(orders), "total_revenue": round(total_revenue, 2), "avg_order": round(total_revenue / max(len(orders), 1), 2)},
        "top_items": top_items
    }


@router.get("/reports/merch")
async def report_merch(start_date: str = None, end_date: str = None):
    """Merch orders report."""
    tenant_id = DEFAULT_TENANT_ID
    query = {"tenant_id": tenant_id}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date + "T23:59:59"

    orders = await db.merch_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    total_revenue = sum(o.get("total", 0) for o in orders)
    return {
        "orders": orders[:100],
        "summary": {"total_orders": len(orders), "total_revenue": round(total_revenue, 2)}
    }


@router.get("/reports/groups")
async def report_groups():
    """Groups and small group report."""
    tenant_id = DEFAULT_TENANT_ID
    groups = await db.groups.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(200)
    total_members = 0
    group_data = []
    for g in groups:
        member_count = len(g.get("members", []))
        total_members += member_count
        group_data.append({"id": g.get("id"), "name": g.get("name"), "type": g.get("group_type", "small_group"), "members": member_count, "leader": g.get("leader_name", ""), "status": g.get("status", "active")})
    return {
        "groups": group_data,
        "summary": {"total_groups": len(groups), "total_members_in_groups": total_members, "avg_group_size": round(total_members / max(len(groups), 1), 1)}
    }


@router.get("/reports/next-steps")
async def report_next_steps():
    """Next Steps / Membership Pathway completion report."""
    tenant_id = DEFAULT_TENANT_ID
    journeys = await db.next_steps_journeys.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(500)
    memberships = await db.next_steps_memberships.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(500)
    completed = sum(1 for m in memberships if m.get("completed"))
    in_progress = len(journeys)
    return {
        "journeys": journeys[:100],
        "memberships": memberships[:100],
        "summary": {"total_enrolled": in_progress, "completed_membership": completed, "completion_rate": round(completed / max(in_progress, 1) * 100, 1)}
    }


@router.get("/reports/executive-summary")
async def report_executive_summary():
    """Executive summary combining all key metrics."""
    tenant_id = DEFAULT_TENANT_ID
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    members_total = await db.people.count_documents({"tenant_id": tenant_id})
    members_active = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "active"})
    new_this_month = await db.people.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": month_start}})

    donations = await db.donations.find({"tenant_id": tenant_id, "created_at": {"$gte": month_start}}, {"_id": 0, "amount": 1}).to_list(5000)
    giving_this_month = sum(d.get("amount", 0) for d in donations)

    attendance_checkins = await db.member_checkins.find({"tenant_id": tenant_id, "service_date": {"$gte": now.strftime("%Y-%m-01")}}, {"_id": 0}).to_list(5000)
    unique_attendees = len(set(c.get("user_id", "") for c in attendance_checkins))

    kids_checkins = await db.kids_checkins.count_documents({"tenant_id": tenant_id, "checked_in_at": {"$gte": month_start}})
    groups_count = await db.groups.count_documents({"tenant_id": tenant_id, "status": "active"})
    cafe_orders = await db.cafe_orders.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": month_start}})
    merch_orders = await db.merch_orders.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": month_start}})

    return {
        "period": {"month": now.strftime("%B %Y"), "start": month_start[:10], "end": now.strftime("%Y-%m-%d")},
        "membership": {"total": members_total, "active": members_active, "new_this_month": new_this_month},
        "giving": {"total_this_month": round(giving_this_month, 2), "donation_count": len(donations), "avg_gift": round(giving_this_month / max(len(donations), 1), 2)},
        "attendance": {"total_checkins": len(attendance_checkins), "unique_attendees": unique_attendees},
        "kids": {"checkins_this_month": kids_checkins},
        "groups": {"active_groups": groups_count},
        "cafe": {"orders_this_month": cafe_orders},
        "merch": {"orders_this_month": merch_orders}
    }


@router.get("/reports/{report_type}/export")
async def export_report_csv(report_type: str, format: str = "csv", start_date: str = None, end_date: str = None):
    """Export any report as CSV."""
    import io, csv
    if format != "csv":
        raise HTTPException(status_code=400, detail="Only CSV export is currently supported")

    tenant_id = DEFAULT_TENANT_ID
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "kids-history":
        writer.writerow(["Child Name", "Parent", "Service Type", "Check-in Time", "Check-out Time", "Pickup Code"])
        records = await db.kids_checkins.find({"tenant_id": tenant_id}, {"_id": 0}).sort("checked_in_at", -1).to_list(2000)
        for r in records:
            writer.writerow([r.get("child_name", ""), r.get("parent_name", ""), r.get("service_type", ""), r.get("checked_in_at", ""), r.get("checked_out_at", ""), r.get("pickup_code", "")])
    elif report_type == "attendance":
        writer.writerow(["Date", "User", "Check-in Type", "Service"])
        records = await db.member_checkins.find({"tenant_id": tenant_id}, {"_id": 0}).sort("service_date", -1).to_list(2000)
        for r in records:
            writer.writerow([r.get("service_date", ""), r.get("user_id", ""), r.get("check_in_type", ""), r.get("service_name", "")])
    elif report_type == "giving-fund":
        data = await report_giving_by_fund(start_date or "2020-01-01", end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        writer.writerow(["Fund", "Total", "Count"])
        for item in data:
            writer.writerow([item.get("fund_name", ""), item.get("total", 0), item.get("count", 0)])
    elif report_type == "top-donors":
        data = await report_top_donors(start_date or "2020-01-01", end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        writer.writerow(["Rank", "Name", "Total", "Count"])
        for idx, d in enumerate(data):
            writer.writerow([idx + 1, d.get("name", ""), d.get("total", 0), d.get("count", 0)])
    elif report_type == "cafe":
        writer.writerow(["Order ID", "Customer", "Total", "Status", "Created"])
        records = await db.cafe_orders.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(2000)
        for r in records:
            writer.writerow([r.get("id", ""), r.get("customer_name", ""), r.get("total", 0), r.get("status", ""), r.get("created_at", "")])
    elif report_type == "groups":
        groups = await db.groups.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(200)
        writer.writerow(["Group Name", "Type", "Members", "Leader", "Status"])
        for g in groups:
            writer.writerow([g.get("name", ""), g.get("group_type", ""), len(g.get("members", [])), g.get("leader_name", ""), g.get("status", "")])
    elif report_type == "executive-summary":
        summary = await report_executive_summary()
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Period", summary["period"]["month"]])
        writer.writerow(["Total Members", summary["membership"]["total"]])
        writer.writerow(["Active Members", summary["membership"]["active"]])
        writer.writerow(["New This Month", summary["membership"]["new_this_month"]])
        writer.writerow(["Giving This Month", summary["giving"]["total_this_month"]])
        writer.writerow(["Avg Gift", summary["giving"]["avg_gift"]])
        writer.writerow(["Attendance Checkins", summary["attendance"]["total_checkins"]])
        writer.writerow(["Kids Checkins", summary["kids"]["checkins_this_month"]])
        writer.writerow(["Active Groups", summary["groups"]["active_groups"]])
        writer.writerow(["Cafe Orders", summary["cafe"]["orders_this_month"]])
        writer.writerow(["Merch Orders", summary["merch"]["orders_this_month"]])
    else:
        raise HTTPException(status_code=404, detail=f"Unknown report type: {report_type}")

    csv_content = output.getvalue()
    from fastapi.responses import Response
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"})


# ============== WAR ROOM LIVE DATA ==============


@router.get("/admin/reports/kids/history")
async def admin_report_kids_history(request: Request, start_date: str = None, end_date: str = None):
    user = await require_permission(request, "admin.reports.view")
    return await report_kids_history(start_date, end_date)


@router.get("/admin/reports/giving/summary")
async def admin_report_giving_summary(request: Request, start_date: str = None, end_date: str = None):
    user = await require_permission(request, "admin.reports.view")
    if not start_date: start_date = "2020-01-01"
    if not end_date: end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    funds = await report_giving_by_fund(start_date, end_date)
    methods = await report_giving_by_method(start_date, end_date)
    donors = await report_top_donors(start_date, end_date, 10)
    return {"by_fund": funds, "by_method": methods, "top_donors": donors, "period": {"start": start_date, "end": end_date}}


@router.get("/admin/reports/attendance/summary")
async def admin_report_attendance_summary(request: Request, start_date: str = None, end_date: str = None):
    user = await require_permission(request, "admin.reports.view")
    return await report_attendance(start_date, end_date)


@router.get("/admin/reports/executive-summary")
async def admin_report_executive_summary(request: Request):
    user = await require_permission(request, "admin.reports.view")
    return await report_executive_summary()


@router.post("/admin/reports/export")
async def admin_export_report(request: Request, payload: dict):
    """Export any report as CSV or PDF."""
    user = await require_permission(request, "admin.reports.view")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)
    report_type = payload.get("report_type", "executive")
    fmt = payload.get("format", "csv")
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")

    tenant_doc = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "name": 1})
    church_name = (tenant_doc or {}).get("name", "Church")

    # Gather report data
    if report_type == "kids":
        data = await report_kids_history(start_date, end_date)
        title = "Kids Check-In History"
    elif report_type == "giving":
        s = start_date or "2020-01-01"
        e = end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        funds = await report_giving_by_fund(s, e)
        data = {"by_fund": funds, "summary": {"total_funds": len(funds), "total": sum(f.get("total", 0) for f in funds)}}
        title = "Giving Summary"
    elif report_type == "attendance":
        data = await report_attendance(start_date, end_date)
        title = "Attendance Summary"
    elif report_type == "executive":
        data = await report_executive_summary()
        title = "Executive Summary"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown report_type: {report_type}")

    # Audit the export
    await audit_log("export_report", "report", report_type, tenant_id, user.get("user_id"), user.get("name", ""),
                     {}, {"report_type": report_type, "format": fmt, "start_date": start_date, "end_date": end_date}, request)

    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_church = church_name.lower().replace(" ", "-")[:20]
    filename = f"solomon-{report_type}-{safe_church}-{now_str}"

    if fmt == "csv":
        import io as _io, csv as _csv
        output = _io.StringIO()
        writer = _csv.writer(output)

        if report_type == "kids":
            writer.writerow(["Child Name", "Parent", "Service Type", "Check-in Time", "Check-out Time", "Pickup Code"])
            for r in data.get("records", []):
                writer.writerow([r.get("child_name", ""), r.get("parent_name", ""), r.get("service_type", ""), r.get("checked_in_at", ""), r.get("checked_out_at", ""), r.get("pickup_code", "")])
        elif report_type == "giving":
            writer.writerow(["Fund", "Total", "Count"])
            for f in data.get("by_fund", []):
                writer.writerow([f.get("fund_name", ""), f.get("total", 0), f.get("count", 0)])
        elif report_type == "attendance":
            writer.writerow(["Date", "In Person", "Online", "Total"])
            for w in data.get("weekly", []):
                writer.writerow([w.get("date", ""), w.get("in_person", 0), w.get("online", 0), w.get("total", 0)])
        elif report_type == "executive":
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Period", data.get("period", {}).get("month", "")])
            for section, metrics in [("membership", data.get("membership", {})), ("giving", data.get("giving", {})), ("attendance", data.get("attendance", {})), ("kids", data.get("kids", {})), ("groups", data.get("groups", {}))]:
                for k, v in metrics.items():
                    writer.writerow([f"{section}.{k}", v])

        from fastapi.responses import Response
        return Response(content=output.getvalue(), media_type="text/csv",
                       headers={"Content-Disposition": f"attachment; filename={filename}.csv"})

    elif fmt == "pdf":
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import io as _io

        buf = _io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()

        header_style = ParagraphStyle("Header", parent=styles["Heading1"], fontSize=16, textColor=colors.HexColor("#1e293b"), spaceAfter=4)
        sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#64748b"), spaceAfter=12)
        section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#334155"), spaceAfter=6, spaceBefore=16)
        footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#94a3b8"))

        elements = []
        elements.append(Paragraph(f"SOLOMON AI — {title.upper()} — CONFIDENTIAL", ParagraphStyle("Brand", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#4f6ef7"), spaceAfter=2)))
        elements.append(Paragraph(title, header_style))
        elements.append(Paragraph(f"{church_name} | {start_date or 'All time'} to {end_date or 'Present'} | Generated by {user.get('name', 'Admin')} on {datetime.now(timezone.utc).strftime('%B %d, %Y at %I:%M %p UTC')}", sub_style))
        elements.append(Spacer(1, 8))

        table_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])

        if report_type == "kids":
            s = data.get("summary", {})
            elements.append(Paragraph("Summary", section_style))
            sum_data = [["Total Check-Ins", "Unique Kids", "Checked Out", "Still In"],
                        [str(s.get("total_checkins", 0)), str(s.get("unique_kids", 0)), str(s.get("checked_out", 0)), str(s.get("still_checked_in", 0))]]
            elements.append(Table(sum_data, colWidths=[1.5*inch]*4, style=table_style))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Check-In Records", section_style))
            rows = [["Child", "Service", "Check-In", "Pickup Code", "Status"]]
            for r in data.get("records", [])[:100]:
                rows.append([r.get("child_name", ""), r.get("service_type", ""), r.get("checked_in_at", "")[:16], r.get("pickup_code", ""), "Out" if r.get("checked_out_at") else "In"])
            elements.append(Table(rows, colWidths=[1.4*inch, 1.2*inch, 1.4*inch, 1*inch, 0.6*inch], style=table_style))
            elements.append(Spacer(1, 16))
            elements.append(Paragraph("Records retained 7 years. Encrypted at rest.", footer_style))

        elif report_type == "giving":
            elements.append(Paragraph("Giving by Fund", section_style))
            rows = [["Fund", "Total", "Donations"]]
            for f in data.get("by_fund", []):
                rows.append([f.get("fund_name", ""), f"${f.get('total', 0):,.2f}", str(f.get("count", 0))])
            if len(rows) > 1:
                elements.append(Table(rows, colWidths=[2.5*inch, 1.5*inch, 1.5*inch], style=table_style))

        elif report_type == "attendance":
            s = data.get("summary", {})
            elements.append(Paragraph("Summary", section_style))
            sum_data = [["Total Services", "Total Check-Ins", "Avg per Service"],
                        [str(s.get("total_services", 0)), str(s.get("total_checkins", 0)), str(s.get("avg_per_service", 0))]]
            elements.append(Table(sum_data, colWidths=[2*inch]*3, style=table_style))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Weekly Breakdown", section_style))
            rows = [["Date", "In Person", "Online", "Total"]]
            for w in data.get("weekly", [])[:52]:
                rows.append([w.get("date", ""), str(w.get("in_person", 0)), str(w.get("online", 0)), str(w.get("total", 0))])
            if len(rows) > 1:
                elements.append(Table(rows, colWidths=[1.5*inch]*4, style=table_style))

        elif report_type == "executive":
            for section_name, section_key in [("Membership", "membership"), ("Giving", "giving"), ("Attendance", "attendance"), ("Kids", "kids"), ("Groups", "groups"), ("Cafe", "cafe"), ("Merch", "merch")]:
                section_data = data.get(section_key, {})
                if section_data:
                    elements.append(Paragraph(section_name, section_style))
                    rows = [["Metric", "Value"]]
                    for k, v in section_data.items():
                        display_val = f"${v:,.2f}" if "giving" in section_key and isinstance(v, (int, float)) and "count" not in k else str(v)
                        rows.append([k.replace("_", " ").title(), display_val])
                    elements.append(Table(rows, colWidths=[3*inch, 2.5*inch], style=table_style))

        doc.build(elements)
        pdf_bytes = buf.getvalue()

        from fastapi.responses import Response
        return Response(content=pdf_bytes, media_type="application/pdf",
                       headers={"Content-Disposition": f"attachment; filename={filename}.pdf"})

    else:
        raise HTTPException(status_code=400, detail="format must be 'csv' or 'pdf'")


# ============== SERVICES / WORSHIP PLANNING ==============


# ─── Custom Report Builder ────────────────────────────────────────────────────

ALLOWED_COLLECTIONS = {
    "people": "people",
    "donations": "donations",
    "attendance": "attendance",
    "groups": "groups",
    "checkins": "checkins",
}

ALLOWED_FIELDS = {
    "people": ["first_name", "last_name", "email", "mobile_phone", "membership_status", "campus", "membership_date", "created_at"],
    "donations": ["donor_name", "amount", "fund_name", "donation_date", "payment_method", "status", "is_recurring"],
    "attendance": ["person_id", "service_date", "service_type", "check_in_time"],
    "groups": ["name", "group_type", "meeting_day", "meeting_time", "member_count", "is_open"],
    "checkins": ["child_name", "classroom", "service_date", "pickup_code", "status", "checked_in_at"],
}


@router.get("/admin/reports/custom")
async def list_custom_reports(request: Request):
    """List saved custom reports."""
    from core import get_current_admin_user
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    reports = await db.custom_reports.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"reports": [serialize_doc(r) for r in reports]}


@router.post("/admin/reports/custom")
async def save_custom_report(request: Request):
    """Save a custom report configuration."""
    from core import get_current_admin_user
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()
    report = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": body.get("name", "Untitled Report"),
        "source": body.get("source"),
        "fields": body.get("fields", []),
        "filters": body.get("filters", []),
        "group_by": body.get("group_by"),
        "aggregation": body.get("aggregation", "count"),
        "created_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.custom_reports.insert_one(report)
    return {"message": "Report saved", "report": {k: v for k, v in report.items() if k != "_id"}}


@router.post("/admin/reports/custom/preview")
async def preview_custom_report(request: Request):
    """Execute a custom report query and return preview rows."""
    from core import get_current_admin_user
    user = await get_current_admin_user(request)
    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    body = await request.json()

    source = body.get("source", "people")
    if source not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail="Invalid data source")

    collection_name = ALLOWED_COLLECTIONS[source]
    raw_fields = body.get("fields", [])
    allowed = ALLOWED_FIELDS.get(source, [])
    fields = [f for f in raw_fields if f in allowed]
    if not fields:
        fields = allowed[:4]

    limit = min(int(body.get("limit", 50)), 500)
    filters_raw = body.get("filters", [])

    # Build query
    query = {"tenant_id": tenant_id}
    for f in filters_raw:
        field = f.get("field")
        op = f.get("op", "=")
        value = f.get("value", "")
        if field and field in allowed and value:
            if op == "=": query[field] = value
            elif op == "!=": query[field] = {"$ne": value}
            elif op == "contains": query[field] = {"$regex": value, "$options": "i"}
            elif op == ">": query[field] = {"$gt": value}
            elif op == "<": query[field] = {"$lt": value}

    projection = {"_id": 0, **{f: 1 for f in fields}}
    coll = getattr(db, collection_name)
    total = await coll.count_documents(query)
    docs = await coll.find(query, projection).limit(limit).to_list(limit)

    rows = [{f: str(doc.get(f, "")) for f in fields} for doc in docs]
    return {"columns": fields, "rows": rows, "total_count": total, "returned": len(rows)}


@router.post("/admin/reports/custom/export")
async def export_custom_report(request: Request):
    """Export a custom report as CSV."""
    import io
    from fastapi.responses import StreamingResponse
    from core import get_current_admin_user
    user = await get_current_admin_user(request)
    body = await request.json()

    source = body.get("source", "people")
    if source not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=400, detail="Invalid source")
    collection_name = ALLOWED_COLLECTIONS[source]
    allowed = ALLOWED_FIELDS.get(source, [])
    fields = [f for f in body.get("fields", allowed) if f in allowed]

    tenant_id = user.get("tenant_id") or DEFAULT_TENANT_ID
    coll = getattr(db, collection_name)
    docs = await coll.find({"tenant_id": tenant_id}, {"_id": 0}).limit(500).to_list(500)

    buf = io.StringIO()
    buf.write(",".join(fields) + "\n")
    for doc in docs:
        row = ",".join(f'"{str(doc.get(f,""))}"' for f in fields)
        buf.write(row + "\n")

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=custom_report.csv"}
    )

