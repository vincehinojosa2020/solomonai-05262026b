"""Seed realistic 2026 donation data for all churches for demo purposes"""
import pymongo
import os
import random
import uuid
from datetime import datetime, timedelta

client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client[os.environ.get('DB_NAME', 'solomonai')]

# Get real tenants
tenants = list(db.tenants.find(
    {"subscription_status": "active"},
    {"_id": 0, "id": 1, "name": 1}
))
real_tenants = [t for t in tenants if not t["name"].startswith("TEST_")]

# Church giving profiles (monthly giving amounts for Jan-Apr 2026)
PROFILES = {
    "Abundant Downtown": {"monthly_giving": 550000, "donors_per_month": 800, "avg_gift": 688},
    "Abundant West": {"monthly_giving": 480000, "donors_per_month": 700, "avg_gift": 686},
    "Abundant East": {"monthly_giving": 420000, "donors_per_month": 650, "avg_gift": 646},
    "The Potter's House": {"monthly_giving": 1200000, "donors_per_month": 1800, "avg_gift": 667},
    "City Reach Church": {"monthly_giving": 320000, "donors_per_month": 500, "avg_gift": 640},
    "EdenX Ministries": {"monthly_giving": 180000, "donors_per_month": 320, "avg_gift": 563},
    "Hill Country Bible Church": {"monthly_giving": 650000, "donors_per_month": 950, "avg_gift": 684},
    "Cristo Viene Church": {"monthly_giving": 750000, "donors_per_month": 1100, "avg_gift": 682},
}

FUNDS = ["General Fund", "Building Fund", "Missions Fund", "Youth Ministry", "Benevolence", "Worship Arts", "Children's Ministry"]
METHODS = ["card", "card", "card", "ach", "ach", "card", "card", "solomonpay", "solomonpay", "card"]

now = datetime.utcnow()
donations_to_insert = []
total_seeded = 0

for tenant in real_tenants:
    profile = PROFILES.get(tenant["name"], {"monthly_giving": 200000, "donors_per_month": 400, "avg_gift": 500})
    tenant_id = tenant["id"]
    
    # Get some people from this tenant for realistic donor names
    people = list(db.people.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1}
    ).limit(500))
    
    if not people:
        people = [{"id": f"person-{i}", "first_name": f"Member{i}", "last_name": "Donor"} for i in range(100)]
    
    # Get funds for this tenant
    funds = list(db.funds.find({"tenant_id": tenant_id}, {"_id": 0, "id": 1, "name": 1}).limit(10))
    if not funds:
        funds = [{"id": f"fund-general-{tenant_id}", "name": "General Fund"}]
    
    # Seed 4 months of 2026 data (Jan - Apr 8)
    for month in range(1, 5):
        days_in_month = 31 if month in [1, 3] else 30 if month == 4 else 28
        if month == 4:
            days_in_month = min(8, days_in_month)  # Only up to Apr 8
        
        num_donations = profile["donors_per_month"] // (1 if month < 4 else 4)
        
        for _ in range(num_donations):
            person = random.choice(people)
            fund = random.choice(funds)
            method = random.choice(METHODS)
            day = random.randint(1, days_in_month)
            
            # Realistic gift amounts with distribution
            r = random.random()
            if r < 0.3:
                amount = random.uniform(10, 50)      # Small gifts
            elif r < 0.6:
                amount = random.uniform(50, 200)      # Medium gifts
            elif r < 0.85:
                amount = random.uniform(200, 500)     # Large gifts
            elif r < 0.95:
                amount = random.uniform(500, 2000)    # Major gifts
            else:
                amount = random.uniform(2000, 10000)  # Mega gifts
            
            amount = round(amount, 2)
            date_str = f"2026-{month:02d}-{day:02d}"
            
            fee_rate = 0.019 if method in ["card", "solomonpay"] else 0.008
            fee = round(amount * fee_rate + 0.30, 2)
            
            donations_to_insert.append({
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "person_id": person["id"],
                "amount": amount,
                "donation_date": date_str,
                "fund_id": fund["id"],
                "payment_method": method,
                "status": "completed",
                "processor": "solomon_pay",
                "processor_fee": fee,
                "net_amount": round(amount - fee, 2),
                "created_at": datetime(2026, month, day, random.randint(6, 22), random.randint(0, 59)).isoformat(),
            })
    
    total_seeded += len([d for d in donations_to_insert if d["tenant_id"] == tenant_id])
    print(f"  {tenant['name']}: prepared {len([d for d in donations_to_insert if d['tenant_id'] == tenant_id])} donations")

# Insert in batches
if donations_to_insert:
    batch_size = 5000
    for i in range(0, len(donations_to_insert), batch_size):
        batch = donations_to_insert[i:i+batch_size]
        db.donations.insert_many(batch)
        print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} records")

# Create indexes for fast queries
db.donations.create_index([("tenant_id", 1), ("donation_date", -1)])
db.donations.create_index([("tenant_id", 1), ("person_id", 1)])

# Update giving stats
print(f"\nTotal 2026 donations seeded: {len(donations_to_insert)}")

# Verify
for t in real_tenants:
    count = db.donations.count_documents({"tenant_id": t["id"], "donation_date": {"$gte": "2026-01-01"}})
    total_giving = 0
    for d in db.donations.find({"tenant_id": t["id"], "donation_date": {"$gte": "2026-01-01"}}, {"amount": 1, "_id": 0}):
        total_giving += d.get("amount", 0)
    print(f"  {t['name']}: {count} donations in 2026, ${total_giving:,.0f} total")
