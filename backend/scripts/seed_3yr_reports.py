"""Seed 3-year historical data for Reports: membership, volunteers, check-in, groups across all campuses"""
import pymongo
import os
import random
from datetime import datetime, timedelta

client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client[os.environ.get('DB_NAME', 'solomonai')]

# Get real tenant IDs
tenants = list(db.tenants.find(
    {"subscription_status": "active"},
    {"_id": 0, "id": 1, "name": 1}
))
real_tenants = [t for t in tenants if not t["name"].startswith("TEST_")]
print(f"Found {len(real_tenants)} real tenants")

# Church size profiles
PROFILES = {
    "Abundant Downtown": {"base_members": 4200, "groups": 42, "avg_attendance": 1800, "volunteers": 380},
    "Abundant West": {"base_members": 3800, "groups": 38, "avg_attendance": 1600, "volunteers": 340},
    "Abundant East": {"base_members": 3200, "groups": 32, "avg_attendance": 1400, "volunteers": 290},
    "The Potter's House": {"base_members": 8500, "groups": 85, "avg_attendance": 4200, "volunteers": 720},
    "City Reach Church": {"base_members": 2800, "groups": 28, "avg_attendance": 1200, "volunteers": 240},
    "EdenX Ministries": {"base_members": 1800, "groups": 18, "avg_attendance": 800, "volunteers": 160},
    "Hill Country Bible Church": {"base_members": 5200, "groups": 52, "avg_attendance": 2400, "volunteers": 450},
    "Cristo Viene Church": {"base_members": 6500, "groups": 55, "avg_attendance": 3000, "volunteers": 520},
}

now = datetime.utcnow()
three_years_ago = now - timedelta(days=365 * 3)

# Seed monthly reports data
monthly_reports = []
for tenant in real_tenants:
    profile = PROFILES.get(tenant["name"], {"base_members": 2000, "groups": 20, "avg_attendance": 900, "volunteers": 180})
    
    for month_offset in range(36):  # 36 months = 3 years
        date = three_years_ago + timedelta(days=month_offset * 30)
        month_str = date.strftime("%Y-%m")
        
        # Growth factor (gradual growth over 3 years)
        growth = 1.0 + (month_offset / 36) * 0.25  # 25% growth over 3 years
        seasonal = 1.0 + 0.08 * (1 if date.month in [3, 4, 9, 10, 11, 12] else -0.05)
        
        members = int(profile["base_members"] * growth * random.uniform(0.97, 1.03))
        new_members = int(members * random.uniform(0.015, 0.035))
        active_members = int(members * random.uniform(0.62, 0.82))
        visitors = int(members * random.uniform(0.04, 0.08))
        
        avg_attendance = int(profile["avg_attendance"] * growth * seasonal * random.uniform(0.92, 1.08))
        peak_attendance = int(avg_attendance * random.uniform(1.15, 1.35))
        services = random.randint(8, 12)
        
        active_groups = int(profile["groups"] * growth * random.uniform(0.88, 1.05))
        group_members = int(active_groups * random.uniform(10, 18))
        group_attendance_rate = random.uniform(0.65, 0.85)
        
        total_checkins = int(avg_attendance * 0.22 * 4.3 * random.uniform(0.85, 1.15))
        unique_children = int(total_checkins * random.uniform(0.35, 0.55))
        first_timers = int(unique_children * random.uniform(0.04, 0.10))
        
        active_volunteers = int(profile["volunteers"] * growth * random.uniform(0.90, 1.10))
        volunteer_hours = int(active_volunteers * random.uniform(8, 16))
        new_volunteers = int(active_volunteers * random.uniform(0.03, 0.08))
        
        monthly_reports.append({
            "tenant_id": tenant["id"],
            "tenant_name": tenant["name"],
            "month": month_str,
            "date": date.strftime("%Y-%m-%d"),
            "membership": {
                "total_members": members,
                "active_members": active_members,
                "new_members": new_members,
                "visitors": visitors,
                "inactive": members - active_members,
                "growth_rate": round((new_members / max(members, 1)) * 100, 1),
            },
            "attendance": {
                "avg_sunday": avg_attendance,
                "peak": peak_attendance,
                "total_services": services,
                "total_attendance": avg_attendance * services,
                "yoy_growth": round(random.uniform(2.0, 8.5), 1),
            },
            "groups": {
                "active_groups": active_groups,
                "total_group_members": group_members,
                "avg_group_size": round(group_members / max(active_groups, 1), 1),
                "attendance_rate": round(group_attendance_rate * 100, 1),
                "pct_members_connected": round((group_members / max(members, 1)) * 100, 1),
            },
            "checkin": {
                "total_checkins": total_checkins,
                "unique_children": unique_children,
                "first_timers": first_timers,
                "avg_per_service": round(total_checkins / max(services * 4.3, 1), 0),
            },
            "volunteers": {
                "active_volunteers": active_volunteers,
                "total_hours": volunteer_hours,
                "new_volunteers": new_volunteers,
                "avg_hours_per_volunteer": round(volunteer_hours / max(active_volunteers, 1), 1),
                "volunteer_rate": round((active_volunteers / max(members, 1)) * 100, 1),
            },
            "created_at": now.isoformat(),
        })

# Drop old data and insert
db.monthly_reports.delete_many({})
if monthly_reports:
    db.monthly_reports.insert_many(monthly_reports)
    print(f"Inserted {len(monthly_reports)} monthly report records")

# Create indexes
db.monthly_reports.create_index([("tenant_id", 1), ("month", -1)])
db.monthly_reports.create_index([("month", -1)])

# Summary
for t in real_tenants:
    count = db.monthly_reports.count_documents({"tenant_id": t["id"]})
    print(f"  {t['name']}: {count} monthly reports")

print("\nDone! 3-year historical data seeded for all campuses.")
