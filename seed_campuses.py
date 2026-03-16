"""
Solomon AI - Multi-Campus Seed Script
Seeds 3 Abundant Church campuses with realistic demo data
Run once: python3 seed_campuses.py
"""
import asyncio
import hashlib
import random
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / 'backend' / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

DEMO_PASSWORD_HASH = hashlib.sha256("Demo2026!".encode()).hexdigest()
NOW = datetime.now(timezone.utc)
NOW_ISO = NOW.isoformat()
TODAY = NOW.strftime("%Y-%m-%d")

# ============================================================
# CAMPUS DEFINITIONS
# ============================================================
CAMPUSES = [
    {
        "tenant_id": "abundant-east-001",
        "name": "Abundant East",
        "subdomain": "abundant-east",
        "location": "El Paso East, TX",
        "address": "1556 George Dieter Dr, El Paso, TX 79936",
        "city": "El Paso", "state": "TX",
        "plan": "enterprise",
        "member_limit": 100000,
        "subscription_tier": "enterprise",
        "mrr": 2500.00,
        "member_target": 20000,
        "active_pct": 0.62,
        "weekly_attendance": 3800,
        "groups_count": 142,
        "cafe_weekly": 200,
        "merch_weekly": 55,
        "monthly_giving": 125000,
        "ytd_giving": 1425000,
        "latitude": 31.7619,
        "longitude": -106.4850,
        "admin_email": "admin@abundant.church",
        "admin_user_id": "admin_abundant",
        "admin_name": "Pastor David Rivera",
        "member_email": "member@abundant.church",
        "member_user_id": "member_abundant",
        "member_name": "Maria Garcia",
        "member_first": "Maria",
        "member_last": "Garcia",
    },
    {
        "tenant_id": "abundant-downtown-001",
        "name": "Abundant Downtown",
        "subdomain": "abundant-downtown",
        "location": "Downtown El Paso, TX",
        "address": "210 E San Antonio Ave, El Paso, TX 79901",
        "city": "El Paso", "state": "TX",
        "plan": "enterprise",
        "member_limit": 50000,
        "subscription_tier": "enterprise",
        "mrr": 2000.00,
        "member_target": 18000,
        "active_pct": 0.58,
        "weekly_attendance": 3200,
        "groups_count": 124,
        "cafe_weekly": 180,
        "merch_weekly": 45,
        "monthly_giving": 110000,
        "ytd_giving": 1230000,
        "latitude": 31.7587,
        "longitude": -106.4452,
        "admin_email": "admin@abundant-downtown.church",
        "admin_user_id": "admin_abundant_downtown",
        "admin_name": "Pastor Sarah Chen",
        "member_email": "member@abundant-downtown.church",
        "member_user_id": "member_abundant_downtown",
        "member_name": "Isabella Torres",
        "member_first": "Isabella",
        "member_last": "Torres",
    },
    {
        "tenant_id": "abundant-west-001",
        "name": "Abundant West",
        "subdomain": "abundant-west",
        "location": "West El Paso, TX",
        "address": "6500 N Mesa St, El Paso, TX 79912",
        "city": "El Paso", "state": "TX",
        "plan": "growth",
        "member_limit": 25000,
        "subscription_tier": "growth",
        "mrr": 1500.00,
        "member_target": 12000,
        "active_pct": 0.55,
        "weekly_attendance": 2100,
        "groups_count": 86,
        "cafe_weekly": 120,
        "merch_weekly": 30,
        "monthly_giving": 75000,
        "ytd_giving": 810000,
        "latitude": 31.8200,
        "longitude": -106.5800,
        "admin_email": "admin@abundant-west.church",
        "admin_user_id": "admin_abundant_west",
        "admin_name": "Pastor Michael Reyes",
        "member_email": "member@abundant-west.church",
        "member_user_id": "member_abundant_west",
        "member_name": "Sofia Martinez",
        "member_first": "Sofia",
        "member_last": "Martinez",
    }
]

# Name pools for people generation
FIRST_NAMES_M = ["James","John","Robert","Michael","William","David","Richard","Joseph","Thomas","Charles",
    "Christopher","Daniel","Matthew","Anthony","Mark","Donald","Steven","Paul","Andrew","Joshua",
    "Carlos","Miguel","Diego","Juan","Roberto","Fernando","Eduardo","Alejandro","Luis","Santiago"]
FIRST_NAMES_F = ["Mary","Patricia","Jennifer","Linda","Elizabeth","Barbara","Susan","Jessica","Sarah","Karen",
    "Maria","Sofia","Isabella","Valentina","Ana","Gabriela","Camila","Elena","Rosa","Carmen",
    "Emily","Ashley","Kimberly","Michelle","Donna","Lisa","Betty","Margaret","Sandra","Nancy"]
LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
    "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
    "Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson",
    "Torres","Rivera","Reyes","Castillo","Morales","Gutierrez","Ortiz","Ramos","Delgado","Mendoza"]

EL_PASO_STREETS = ["Montana Ave","Alameda Ave","Mesa St","Dyer St","Lee Trevino Dr",
    "Gateway Blvd","Viscount Blvd","Zaragoza Rd","Transmountain Dr","Paisano Dr",
    "George Dieter Dr","Joe Battle Blvd","Doniphan Dr","Resler Dr","Executive Center Blvd"]

GROUP_NAMES = [
    "Young Adults","Marriage Builders","New Believers","Prayer Warriors",
    "Women's Bible Study","Men's Brotherhood","College & Career","Empty Nesters",
    "Parents of Teens","Grief Support","Financial Peace","Spanish Fellowship",
    "Worship Team","Tech Team","Greeting Team","Parking Team",
    "Children's Ministry","Youth Group","Senior Saints","Community Outreach",
    "Faith & Family","Single Parents","Nuevo Comienzo","Leadership Development",
    "Monday Night Football","Tuesday Night Worship","Wednesday Bible Study",
    "Thursday Moms Group","Friday Young Professionals","Saturday Service Team",
    "Home Group - North","Home Group - South","Home Group - East","Home Group - West",
    "Home Group - Central","Home Group - Mesa Hills","Home Group - Westside",
    "Home Group - Eastlake","Home Group - Northeast","Home Group - Montana",
]

EVENT_TEMPLATES = [
    {"title": "Sunday Worship Service", "category": "worship", "recurring": True},
    {"title": "Women's Conference 2026", "category": "women", "recurring": False},
    {"title": "Men's Retreat: Iron Sharpens Iron", "category": "men", "recurring": False},
    {"title": "Youth Night: Ignite", "category": "youth", "recurring": True},
    {"title": "Community Easter Egg Hunt", "category": "community", "recurring": False},
    {"title": "Financial Peace University", "category": "community", "recurring": True},
    {"title": "Baptism Sunday", "category": "worship", "recurring": False},
    {"title": "Vacation Bible School", "category": "youth", "recurring": False},
    {"title": "Marriage Enrichment Workshop", "category": "community", "recurring": False},
    {"title": "Worship Night: Altar", "category": "worship", "recurring": False},
    {"title": "New Members Lunch", "category": "community", "recurring": True},
    {"title": "Missions Trip Info Night", "category": "community", "recurring": False},
]

CAFE_ITEMS = [
    {"name": "House Drip Coffee", "price": 3.50, "category": "coffee"},
    {"name": "Caramel Latte", "price": 5.50, "category": "coffee"},
    {"name": "Cold Brew", "price": 5.00, "category": "coffee"},
    {"name": "Vanilla Chai Latte", "price": 5.50, "category": "tea"},
    {"name": "Matcha Latte", "price": 6.00, "category": "tea"},
    {"name": "Blueberry Muffin", "price": 3.50, "category": "pastry"},
    {"name": "Croissant", "price": 4.00, "category": "pastry"},
    {"name": "Banana Bread", "price": 3.50, "category": "pastry"},
    {"name": "Hot Chocolate", "price": 4.50, "category": "coffee"},
    {"name": "Iced Americano", "price": 4.50, "category": "coffee"},
]

MERCH_ITEMS = [
    {"name": "Abundant Worship Tee", "price": 25.00, "category": "apparel"},
    {"name": "Faith Over Fear Hoodie", "price": 45.00, "category": "apparel"},
    {"name": "Abundant Church Cap", "price": 20.00, "category": "apparel"},
    {"name": "Worship Album - 'Altar'", "price": 15.00, "category": "music"},
    {"name": "Abundant Tumbler 20oz", "price": 22.00, "category": "drinkware"},
    {"name": "Scripture Journal", "price": 18.00, "category": "accessories"},
    {"name": "Abundant Sticker Pack", "price": 8.00, "category": "accessories"},
    {"name": "Kids Ministry Tee", "price": 15.00, "category": "apparel"},
]

FUND_NAMES = ["General Fund", "Building Fund", "Missions", "Benevolence", "Youth Ministry"]

KIDS_FIRST_NAMES = ["Emma","Liam","Olivia","Noah","Ava","Ethan","Sophia","Mason","Isabella","Lucas",
    "Mia","Logan","Charlotte","Aiden","Amelia","Jackson","Harper","Sebastian","Evelyn","Mateo"]

async def seed_campus(campus):
    tid = campus["tenant_id"]
    print(f"\n{'='*60}")
    print(f"Seeding: {campus['name']} ({tid})")
    print(f"{'='*60}")

    # 1. TENANT RECORD
    tenant_doc = {
        "id": tid,
        "name": campus["name"],
        "subdomain": campus["subdomain"],
        "plan": campus["plan"],
        "member_limit": campus["member_limit"],
        "subscription_status": "active",
        "subscription_tier": campus["subscription_tier"],
        "mrr": campus["mrr"],
        "primary_color": "#4f6ef7",
        "accent_color": "#00c896",
        "timezone": "America/Denver",
        "address": campus["address"],
        "city": campus["city"],
        "state": campus["state"],
        "website": "https://www.abundant.org",
        "location": campus["location"],
        "onboarded_date": "2026-01-15",
        "mobile_app_status": "approved",
        "created_at": (NOW - timedelta(days=60)).isoformat()
    }
    await db.tenants.update_one({"id": tid}, {"$set": tenant_doc}, upsert=True)
    print(f"  Tenant record created")

    # 2. ADMIN + MEMBER USER ACCOUNTS
    await db.users.update_one(
        {"email": campus["admin_email"]},
        {"$set": {
            "user_id": campus["admin_user_id"],
            "email": campus["admin_email"],
            "name": campus["admin_name"],
            "role": "church_admin",
            "tenant_id": tid,
            "password_hash": DEMO_PASSWORD_HASH,
            "is_active": True,
            "created_at": NOW_ISO
        }}, upsert=True
    )
    await db.users.update_one(
        {"email": campus["member_email"]},
        {"$set": {
            "user_id": campus["member_user_id"],
            "email": campus["member_email"],
            "name": campus["member_name"],
            "first_name": campus["member_first"],
            "last_name": campus["member_last"],
            "role": "member",
            "tenant_id": tid,
            "password_hash": DEMO_PASSWORD_HASH,
            "is_active": True,
            "member_since": "2024-03-15",
            "created_at": NOW_ISO
        }}, upsert=True
    )
    print(f"  Admin + Member accounts created")

    # 3. GENERATE PEOPLE (200 per campus for browsable directory)
    people = []
    person_ids = []
    member_person_id = f"person_{campus['member_user_id']}"
    
    # Create person record for the demo member
    member_person = {
        "id": member_person_id,
        "tenant_id": tid,
        "first_name": campus["member_first"],
        "last_name": campus["member_last"],
        "email": campus["member_email"],
        "mobile_phone": f"(915) {random.randint(200,999)}-{random.randint(1000,9999)}",
        "gender": "female",
        "membership_status": "member",
        "membership_date": "2024-03-15",
        "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={member_person_id}",
        "campus": campus["name"],
        "engagement_score": 92,
        "ytd_giving": 1850.0,
        "lifetime_giving": 12400.0,
        "created_at": NOW_ISO
    }
    people.append(member_person)
    person_ids.append(member_person_id)

    for i in range(199):
        pid = str(uuid.uuid4())
        is_male = random.random() < 0.5
        fn = random.choice(FIRST_NAMES_M if is_male else FIRST_NAMES_F)
        ln = random.choice(LAST_NAMES)
        person_ids.append(pid)
        people.append({
            "id": pid,
            "tenant_id": tid,
            "first_name": fn,
            "last_name": ln,
            "email": f"{fn.lower()}.{ln.lower()}{random.randint(1,999)}@email.com",
            "mobile_phone": f"(915) {random.randint(200,999)}-{random.randint(1000,9999)}",
            "gender": "male" if is_male else "female",
            "membership_status": random.choice(["member"]*8 + ["visitor", "regular"]),
            "membership_date": f"20{random.randint(18,25)}-{random.randint(1,12):02d}-01",
            "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={pid}",
            "campus": campus["name"],
            "engagement_score": random.randint(30, 100),
            "ytd_giving": round(random.uniform(0, 5000), 2),
            "lifetime_giving": round(random.uniform(500, 50000), 2),
            "created_at": (NOW - timedelta(days=random.randint(1, 365))).isoformat()
        })

    # Delete old people for this tenant and insert fresh
    await db.people.delete_many({"tenant_id": tid})
    await db.people.insert_many(people)
    print(f"  200 people created")

    # Also create bulk member USER records (for count queries to show big numbers)
    bulk_members = []
    for i in range(300):
        bulk_members.append({
            "user_id": f"bulk_{tid}_{i}",
            "email": f"member{i}@{campus['subdomain']}.church",
            "name": f"{random.choice(FIRST_NAMES_M + FIRST_NAMES_F)} {random.choice(LAST_NAMES)}",
            "role": "member",
            "tenant_id": tid,
            "is_active": random.random() < campus["active_pct"],
            "created_at": (NOW - timedelta(days=random.randint(1, 365))).isoformat()
        })
    # Remove old bulk members
    await db.users.delete_many({"tenant_id": tid, "user_id": {"$regex": f"^bulk_{tid}_"}})
    await db.users.insert_many(bulk_members)
    print(f"  300 member user records created")

    # 4. GROUPS (use campus group count, but seed ~40 actual records)
    groups = []
    group_ids = []
    available_names = list(GROUP_NAMES)
    random.shuffle(available_names)
    for i, gname in enumerate(available_names[:40]):
        gid = str(uuid.uuid4())
        group_ids.append(gid)
        leader = random.choice(person_ids[1:20])  # Pick from first 20 people as leaders
        groups.append({
            "id": gid,
            "tenant_id": tid,
            "name": gname,
            "description": f"Join us for {gname} at {campus['name']}!",
            "type": random.choice(["small_group", "ministry", "class", "volunteer"]),
            "leader_id": leader,
            "leader_name": next((p["first_name"] + " " + p["last_name"] for p in people if p["id"] == leader), "TBD"),
            "meeting_day": random.choice(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]),
            "meeting_time": f"{random.randint(6,20):02d}:00",
            "location": f"Room {random.randint(100,400)}, {campus['name']}",
            "capacity": random.randint(10, 30),
            "member_count": random.randint(5, 25),
            "is_active": True,
            "category": random.choice(["faith","family","leadership","worship","growth","community"]),
            "created_at": (NOW - timedelta(days=random.randint(30, 365))).isoformat()
        })

    await db.groups.delete_many({"tenant_id": tid})
    await db.groups.insert_many(groups)
    print(f"  {len(groups)} groups created")

    # 5. GROUP MEMBERSHIPS (for demo member to have groups)
    memberships = []
    member_groups = random.sample(group_ids[:10], min(3, len(group_ids)))
    for gid in member_groups:
        memberships.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "group_id": gid,
            "person_id": member_person_id,
            "user_id": campus["member_user_id"],
            "role": "member",
            "is_active": True,
            "joined_at": (NOW - timedelta(days=random.randint(30, 180))).isoformat()
        })
    # Add some other members to groups
    for gid in group_ids:
        for pid in random.sample(person_ids[1:], min(8, len(person_ids)-1)):
            memberships.append({
                "id": str(uuid.uuid4()),
                "tenant_id": tid,
                "group_id": gid,
                "person_id": pid,
                "role": "member",
                "is_active": True,
                "joined_at": (NOW - timedelta(days=random.randint(1, 200))).isoformat()
            })
    
    await db.group_members.delete_many({"tenant_id": tid})
    await db.group_members.insert_many(memberships)
    print(f"  {len(memberships)} group memberships created")

    # 6. DONATIONS (last 60 days of giving data)
    donations = []
    fund_weights = [0.55, 0.20, 0.12, 0.08, 0.05]  # General, Building, Missions, Benevolence, Youth
    monthly_target = campus["monthly_giving"]
    
    for day_offset in range(60):
        day = NOW - timedelta(days=day_offset)
        day_str = day.strftime("%Y-%m-%d")
        is_sunday = day.weekday() == 6
        
        # More donations on Sundays
        num_donations = random.randint(15, 30) if is_sunday else random.randint(2, 8)
        for _ in range(num_donations):
            fund_idx = random.choices(range(5), weights=fund_weights, k=1)[0]
            amt = round(random.choice([25, 50, 75, 100, 150, 200, 250, 500, 1000, 2500]) * random.uniform(0.8, 1.2), 2)
            donor = random.choice(person_ids)
            donor_person = next((p for p in people if p["id"] == donor), None)
            donations.append({
                "id": str(uuid.uuid4()),
                "tenant_id": tid,
                "person_id": donor,
                "person_name": f"{donor_person['first_name']} {donor_person['last_name']}" if donor_person else "Anonymous",
                "amount": amt,
                "fund_id": f"fund_{FUND_NAMES[fund_idx].lower().replace(' ', '_')}",
                "fund_name": FUND_NAMES[fund_idx],
                "fund": FUND_NAMES[fund_idx],
                "payment_method": random.choice(["card", "ach", "check", "online"]),
                "frequency": random.choice(["one_time", "one_time", "one_time", "weekly", "monthly"]),
                "status": "completed",
                "donation_date": day_str,
                "created_at": day.isoformat()
            })

    await db.donations.delete_many({"tenant_id": tid})
    await db.donations.insert_many(donations)
    total_donated = sum(d["amount"] for d in donations)
    print(f"  {len(donations)} donations created (${total_donated:,.0f} total)")

    # 7. CAFE ITEMS + ORDERS
    cafe_items = []
    for item in CAFE_ITEMS:
        cid = str(uuid.uuid4())
        cafe_items.append({
            "id": cid,
            "tenant_id": tid,
            "name": item["name"],
            "price": item["price"],
            "category": item["category"],
            "description": f"Fresh {item['name']}",
            "image_url": "",
            "is_available": True,
            "created_at": NOW_ISO
        })
    await db.cafe_items.delete_many({"tenant_id": tid})
    await db.cafe_items.insert_many(cafe_items)

    cafe_orders = []
    for day_offset in range(30):
        day = NOW - timedelta(days=day_offset)
        is_sunday = day.weekday() == 6
        num_orders = random.randint(25, 50) if is_sunday else random.randint(0, 5)
        for _ in range(num_orders):
            items_ordered = random.sample(cafe_items, random.randint(1, 3))
            order_total = sum(i["price"] for i in items_ordered)
            # Giving nudge: ~30% add a gift
            gift = round(random.choice([5, 10, 20, 0, 0, 0, 0]), 2)
            cafe_orders.append({
                "id": str(uuid.uuid4()),
                "tenant_id": tid,
                "user_id": random.choice(person_ids),
                "items": [{"name": i["name"], "price": i["price"], "quantity": 1} for i in items_ordered],
                "subtotal": order_total,
                "giving_addition": gift,
                "total": round(order_total + gift, 2),
                "status": "completed",
                "pickup_time": f"{random.randint(7,10)}:{random.choice(['00','15','30','45'])} AM",
                "created_at": day.isoformat()
            })
    
    await db.cafe_orders.delete_many({"tenant_id": tid})
    if cafe_orders:
        await db.cafe_orders.insert_many(cafe_orders)
    cafe_total = sum(o["total"] for o in cafe_orders)
    cafe_giving = sum(o["giving_addition"] for o in cafe_orders)
    print(f"  {len(cafe_orders)} cafe orders (${cafe_total:,.0f}, giving nudge ${cafe_giving:,.0f})")

    # 8. MERCH PRODUCTS + ORDERS
    merch_products = []
    for item in MERCH_ITEMS:
        mid = str(uuid.uuid4())
        merch_products.append({
            "id": mid,
            "tenant_id": tid,
            "name": item["name"],
            "price": item["price"],
            "category": item["category"],
            "description": f"Represent your faith with {item['name']}",
            "image_url": "",
            "sizes": ["S","M","L","XL"] if item["category"] == "apparel" else [],
            "in_stock": True,
            "created_at": NOW_ISO
        })
    await db.merch_products.delete_many({"tenant_id": tid})
    await db.merch_products.insert_many(merch_products)

    merch_orders = []
    for day_offset in range(30):
        day = NOW - timedelta(days=day_offset)
        is_sunday = day.weekday() == 6
        num_orders = random.randint(5, 15) if is_sunday else random.randint(0, 3)
        for _ in range(num_orders):
            items_ordered = random.sample(merch_products, random.randint(1, 2))
            order_total = sum(i["price"] for i in items_ordered)
            gift = round(random.choice([10, 20, 0, 0, 0]), 2)
            merch_orders.append({
                "id": str(uuid.uuid4()),
                "tenant_id": tid,
                "user_id": random.choice(person_ids),
                "items": [{"name": i["name"], "price": i["price"], "quantity": 1, "size": random.choice(["M","L","XL"])} for i in items_ordered],
                "subtotal": order_total,
                "giving_addition": gift,
                "total": round(order_total + gift, 2),
                "status": random.choice(["completed", "processing", "shipped"]),
                "created_at": day.isoformat()
            })

    await db.merch_orders.delete_many({"tenant_id": tid})
    if merch_orders:
        await db.merch_orders.insert_many(merch_orders)
    merch_total = sum(o["total"] for o in merch_orders)
    print(f"  {len(merch_orders)} merch orders (${merch_total:,.0f})")

    # 9. EVENTS
    events = []
    for i, tmpl in enumerate(EVENT_TEMPLATES):
        eid = str(uuid.uuid4())
        start_day = NOW + timedelta(days=random.randint(1, 60))
        events.append({
            "id": eid,
            "tenant_id": tid,
            "title": tmpl["title"],
            "description": f"Join us for {tmpl['title']} at {campus['name']}!",
            "category": tmpl["category"],
            "start_datetime": start_day.strftime("%Y-%m-%d"),
            "event_date": start_day.strftime("%Y-%m-%d"),
            "start_time": f"{random.choice(['09:00','10:00','18:00','19:00'])}",
            "end_time": f"{random.choice(['11:00','12:00','20:00','21:00'])}",
            "location": campus["name"],
            "capacity": random.randint(50, 500),
            "registered_count": random.randint(10, 200),
            "is_featured": i == 0,
            "image_url": "",
            "created_at": NOW_ISO
        })
    
    await db.events.delete_many({"tenant_id": tid})
    await db.events.insert_many(events)
    print(f"  {len(events)} events created")

    # 10. KIDS + CHECK-INS (for today)
    children = []
    checkins = []
    child_names = random.sample(KIDS_FIRST_NAMES, 10)
    parent_ids = random.sample(person_ids[1:50], 10)
    
    for i, cname in enumerate(child_names):
        child_id = str(uuid.uuid4())
        parent = next((p for p in people if p["id"] == parent_ids[i]), people[1])
        age = random.randint(2, 12)
        children.append({
            "id": child_id,
            "tenant_id": tid,
            "parent_id": parent_ids[i],
            "parent_name": f"{parent['first_name']} {parent['last_name']}",
            "parent_phone": parent.get("mobile_phone", ""),
            "first_name": cname,
            "last_name": parent["last_name"],
            "name": f"{cname} {parent['last_name']}",
            "date_of_birth": f"{NOW.year - age}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "age": age,
            "grade": max(0, age - 5),
            "curriculum": random.choice(["Toddlers","Pre-K","Elementary","Pre-Teen"]),
            "allergies": random.choice(["", "", "", "Peanuts", "Dairy", "Gluten"]),
            "emergency_contact": f"{parent['first_name']} {parent['last_name']}",
            "created_at": NOW_ISO
        })
        
        # Check in half the kids for today
        if i < 5:
            pickup_code = str(random.randint(100, 999))
            checkins.append({
                "id": str(uuid.uuid4()),
                "tenant_id": tid,
                "child_id": child_id,
                "child_name": f"{cname} {parent['last_name']}",
                "parent_name": f"{parent['first_name']} {parent['last_name']}",
                "parent_phone": parent.get("mobile_phone", ""),
                "pickup_code": pickup_code,
                "status": "checked_in",
                "checked_in_at": NOW.isoformat(),
                "checked_out_at": None,
                "created_at": NOW_ISO
            })

    # Also create children for the demo member
    demo_child_id = str(uuid.uuid4())
    children.append({
        "id": demo_child_id,
        "tenant_id": tid,
        "parent_id": member_person_id,
        "parent_name": campus["member_name"],
        "parent_phone": "(915) 555-0142",
        "first_name": "Emma",
        "last_name": campus["member_last"],
        "name": f"Emma {campus['member_last']}",
        "date_of_birth": f"{NOW.year - 7}-03-15",
        "age": 7,
        "grade": 2,
        "curriculum": "Elementary",
        "allergies": "",
        "emergency_contact": campus["member_name"],
        "created_at": NOW_ISO
    })

    await db.children.delete_many({"tenant_id": tid})
    await db.children.insert_many(children)
    await db.checkins.delete_many({"tenant_id": tid})
    if checkins:
        await db.checkins.insert_many(checkins)
    print(f"  {len(children)} children, {len(checkins)} checked in today")

    # 11. ATTENDANCE CHECK-INS (for member streak)
    attendance_records = []
    # Create 4 weeks of Sunday attendance for the demo member
    for week in range(4):
        sunday = NOW - timedelta(days=(NOW.weekday() + 1) % 7 + week * 7)
        attendance_records.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "user_id": campus["member_user_id"],
            "user_name": campus["member_name"],
            "check_in_type": "in_person",
            "date": sunday.strftime("%Y-%m-%d"),
            "service_date": sunday.strftime("%Y-%m-%d"),
            "checked_in_at": sunday.isoformat()
        })
    # Add today's check-in for some members
    for pid in random.sample(person_ids[:50], 20):
        attendance_records.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "user_id": pid,
            "check_in_type": "in_person",
            "date": TODAY,
            "service_date": TODAY,
            "checked_in_at": NOW.isoformat()
        })

    await db.attendance_checkins.delete_many({"tenant_id": tid})
    await db.member_checkins.delete_many({"tenant_id": tid})
    await db.attendance_checkins.insert_many(attendance_records)
    # Also insert into member_checkins for the last_sunday_attendance query
    await db.member_checkins.insert_many(attendance_records)
    print(f"  {len(attendance_records)} attendance records")

    # 12. GEOFENCE CONFIG
    await db.geofence_config.update_one(
        {"tenant_id": tid},
        {"$set": {
            "tenant_id": tid,
            "zones": [{
                "id": "zone_main",
                "name": campus["name"],
                "latitude": campus["latitude"],
                "longitude": campus["longitude"],
                "radius_meters": 150,
                "is_enabled": True
            }],
            "auto_checkin_enabled": True,
            "active_days": ["Sunday"],
            "active_start": "07:00",
            "active_end": "13:00",
            "nudge_cafe": True,
            "nudge_giving": True,
            "nudge_giving_amounts": [25, 50, 100, 250],
            "updated_at": NOW_ISO
        }},
        upsert=True
    )
    print(f"  Geofence config seeded")

    # 13. ANNOUNCEMENTS
    announcements = [
        {"title": "Welcome to Solomon AI!", "body": f"We're excited to launch our new church management platform at {campus['name']}!", "priority": "high"},
        {"title": "Easter Sunday Service", "body": "Join us for a special Easter celebration. Invite your friends and family!", "priority": "normal"},
        {"title": "VBS Registration Open", "body": "Vacation Bible School registration is now open for ages 4-12.", "priority": "normal"},
    ]
    ann_docs = []
    for ann in announcements:
        ann_docs.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "title": ann["title"],
            "body": ann["body"],
            "priority": ann["priority"],
            "is_active": True,
            "created_by": campus["admin_user_id"],
            "created_at": (NOW - timedelta(days=random.randint(0, 14))).isoformat()
        })
    await db.announcements.delete_many({"tenant_id": tid})
    await db.announcements.insert_many(ann_docs)
    print(f"  {len(ann_docs)} announcements created")

    # 14. FUNDS
    funds = []
    for fname in FUND_NAMES:
        funds.append({
            "id": f"fund_{fname.lower().replace(' ', '_')}_{tid}",
            "tenant_id": tid,
            "name": fname,
            "description": f"{fname} for {campus['name']}",
            "is_active": True,
            "goal_amount": random.randint(100000, 5000000),
            "current_amount": random.randint(50000, 2000000),
            "created_at": NOW_ISO
        })
    await db.funds.delete_many({"tenant_id": tid})
    await db.funds.insert_many(funds)
    print(f"  {len(funds)} funds created")

    # 15. CAFE SETTINGS
    await db.cafe_settings.update_one(
        {"tenant_id": tid},
        {"$set": {
            "tenant_id": tid,
            "is_open": True,
            "open_time": "07:30",
            "close_time": "10:30",
            "pickup_location": "Lobby pickup counter",
            "accepting_orders": True,
            "updated_at": NOW_ISO
        }},
        upsert=True
    )

    # 16. MEDIA / SERMONS
    sermons = [
        {"title": "The Power of Faith", "pastor": "Pastor David Rivera", "series": "Faith Foundations", "duration": 2520, "category": "faith"},
        {"title": "Building Strong Families", "pastor": "Pastor Sarah Chen", "series": "Family First", "duration": 2340, "category": "family"},
        {"title": "Leading with Purpose", "pastor": "Pastor Michael Reyes", "series": "Leadership", "duration": 2760, "category": "leadership"},
        {"title": "Worship as a Lifestyle", "pastor": "Pastor David Rivera", "series": "Worship", "duration": 1980, "category": "worship"},
        {"title": "Growing Through Adversity", "pastor": "Pastor Sarah Chen", "series": "Growth", "duration": 2640, "category": "growth"},
        {"title": "Serving Your Community", "pastor": "Pastor Michael Reyes", "series": "Community", "duration": 2100, "category": "community"},
    ]
    sermon_docs = []
    for i, s in enumerate(sermons):
        sermon_docs.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "title": s["title"],
            "description": f"A powerful message on {s['title'].lower()} from {s['pastor']}.",
            "video_url": f"https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "thumbnail_url": "",
            "pastor": s["pastor"],
            "series_name": s["series"],
            "duration_seconds": s["duration"],
            "category": s["category"],
            "published": True,
            "is_featured": i == 0,
            "views": random.randint(100, 5000),
            "created_at": (NOW - timedelta(days=i * 7)).isoformat()
        })
    await db.media.delete_many({"tenant_id": tid})
    await db.media.insert_many(sermon_docs)
    print(f"  {len(sermon_docs)} sermons created")

    # 17. NEXT STEPS / PATHWAYS for demo member
    steps = ["salvation", "baptism", "membership_class", "small_group", "serve"]
    step_docs = []
    for i, step in enumerate(steps):
        step_docs.append({
            "id": f"nextstep_{campus['member_user_id']}_{step}",
            "tenant_id": tid,
            "user_id": campus["member_user_id"],
            "step": step,
            "completed": i < 3,  # First 3 completed
            "completed_at": (NOW - timedelta(days=90 - i * 20)).isoformat() if i < 3 else None,
            "created_at": NOW_ISO
        })
    await db.next_steps.delete_many({"tenant_id": tid, "user_id": campus["member_user_id"]})
    await db.next_steps.insert_many(step_docs)

    # 18. PRAYER REQUESTS
    prayers = [
        {"title": "Healing for my mother", "description": "Please pray for my mom's recovery from surgery.", "is_public": True},
        {"title": "Job interview tomorrow", "description": "I have a big interview. Praying for peace and favor.", "is_public": True},
        {"title": "Family unity", "description": "Pray for restoration in our family.", "is_public": False},
    ]
    prayer_docs = []
    for pr in prayers:
        prayer_docs.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "user_id": campus["member_user_id"],
            "user_name": campus["member_name"],
            "title": pr["title"],
            "description": pr["description"],
            "is_public": pr["is_public"],
            "prayer_count": random.randint(2, 30),
            "status": "active",
            "created_at": (NOW - timedelta(days=random.randint(0, 14))).isoformat()
        })
    await db.prayer_requests.delete_many({"tenant_id": tid})
    await db.prayer_requests.insert_many(prayer_docs)
    print(f"  Prayer requests, next steps created")

    # 19. ACTIVITY LOG (recent activity for dashboard)
    activities = []
    activity_templates = [
        "New member registered: {name}",
        "{name} donated ${amount} to General Fund",
        "{name} joined {group} group",
        "{name} checked in for Sunday service",
        "{name} signed up for {event}",
        "New cafe order: {name} - ${amount}",
        "{name} submitted a prayer request",
    ]
    for i in range(20):
        person = random.choice(people)
        template = random.choice(activity_templates)
        name = f"{person['first_name']} {person['last_name']}"
        activities.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "type": random.choice(["registration","donation","group_join","checkin","event_signup","cafe_order","prayer"]),
            "message": template.format(
                name=name,
                amount=random.randint(25, 500),
                group=random.choice(GROUP_NAMES[:10]),
                event=random.choice(EVENT_TEMPLATES)["title"]
            ),
            "user_name": name,
            "created_at": (NOW - timedelta(hours=random.randint(0, 72))).isoformat()
        })
    await db.activity_log.delete_many({"tenant_id": tid})
    await db.activity_log.insert_many(activities)
    print(f"  {len(activities)} activity log entries")

    # 20. ATTENDANCE STREAK for demo member
    await db.attendance_streaks.update_one(
        {"tenant_id": tid, "user_id": campus["member_user_id"]},
        {"$set": {
            "tenant_id": tid,
            "user_id": campus["member_user_id"],
            "current_streak": 4,
            "best_streak": 8,
            "total_checkins": 24,
            "last_checkin_date": TODAY,
            "updated_at": NOW_ISO
        }},
        upsert=True
    )

    print(f"  COMPLETE: {campus['name']} seeded successfully!")


async def seed_dashboard_stats():
    """Seed per-tenant dashboard stats cache for impressive demo numbers"""
    print(f"\n{'='*60}")
    print("Seeding dashboard stats cache")
    print(f"{'='*60}")
    
    for campus in CAMPUSES:
        tid = campus["tenant_id"]
        target = campus["member_target"]
        active = int(target * campus["active_pct"])
        
        stats = {
            "tenant_id": tid,
            "total_members": target,
            "active_members": active,
            "visitors": random.randint(100, 400),
            "active_groups": campus["groups_count"],
            "open_groups": int(campus["groups_count"] * 0.3),
            "mtd_giving": campus["monthly_giving"],
            "ytd_giving": campus["ytd_giving"],
            "mtd_goal": int(campus["monthly_giving"] * 1.35),
            "last_attendance": campus["weekly_attendance"],
            "last_attendance_change": random.randint(50, 300),
            "new_this_week": random.randint(20, 100),
            "recurring_givers": int(target * 0.085),
            "cafe_orders_week": campus["cafe_weekly"],
            "cafe_giving_added": int(campus["cafe_weekly"] * 8.5),
            "merch_orders_week": campus["merch_weekly"],
            "merch_giving_added": int(campus["merch_weekly"] * 11.3),
            "event_registrations_month": random.randint(400, 1500),
            "at_risk_members": int(target * 0.003),
            "kids_checked_in_today": random.randint(40, 150),
            "updated_at": NOW_ISO
        }
        await db.dashboard_stats_cache.update_one(
            {"tenant_id": tid},
            {"$set": stats},
            upsert=True
        )
        print(f"  {campus['name']}: {target:,} members, ${campus['monthly_giving']:,.0f}/mo giving")

    # Also create an aggregate stat for the old abundant-church-001 ID (backwards compat)
    total_members = sum(c["member_target"] for c in CAMPUSES)
    total_giving = sum(c["monthly_giving"] for c in CAMPUSES)
    total_ytd = sum(c["ytd_giving"] for c in CAMPUSES)
    total_attendance = sum(c["weekly_attendance"] for c in CAMPUSES)
    
    await db.dashboard_stats_cache.update_one(
        {"tenant_id": "abundant-church-001"},
        {"$set": {
            "tenant_id": "abundant-church-001",
            "total_members": total_members,
            "active_members": int(total_members * 0.59),
            "visitors": 500,
            "active_groups": sum(c["groups_count"] for c in CAMPUSES),
            "open_groups": 75,
            "mtd_giving": total_giving,
            "ytd_giving": total_ytd,
            "mtd_goal": int(total_giving * 1.35),
            "last_attendance": total_attendance,
            "last_attendance_change": 650,
            "new_this_week": 150,
            "recurring_givers": int(total_members * 0.085),
            "cafe_orders_week": sum(c["cafe_weekly"] for c in CAMPUSES),
            "cafe_giving_added": 4250,
            "merch_orders_week": sum(c["merch_weekly"] for c in CAMPUSES),
            "merch_giving_added": 1470,
            "event_registrations_month": 2800,
            "at_risk_members": int(total_members * 0.003),
            "kids_checked_in_today": 280,
            "updated_at": NOW_ISO
        }},
        upsert=True
    )
    print(f"\n  AGGREGATE: {total_members:,} total members across all Abundant campuses")


async def main():
    print("=" * 60)
    print("SOLOMON AI - Multi-Campus Seed Script")
    print(f"Seeding 3 Abundant Church campuses with realistic demo data")
    print("=" * 60)

    # Seed each campus
    for campus in CAMPUSES:
        await seed_campus(campus)

    # Seed dashboard stats cache
    await seed_dashboard_stats()

    # Ensure platform admin and other demo accounts still exist
    print(f"\n{'='*60}")
    print("Ensuring platform admin and other church accounts")
    print(f"{'='*60}")
    
    # Platform admin
    await db.users.update_one(
        {"email": "admin@solomon.ai"},
        {"$set": {
            "user_id": "platform_admin_001",
            "email": "admin@solomon.ai",
            "name": "Solomon Platform Admin",
            "role": "platform_admin",
            "tenant_id": None,
            "password_hash": DEMO_PASSWORD_HASH,
            "is_active": True,
            "created_at": NOW_ISO
        }}, upsert=True
    )

    # Cristo Viene
    await db.tenants.update_one(
        {"id": "cristoviene-church-001"},
        {"$set": {
            "id": "cristoviene-church-001",
            "name": "Cristo Viene",
            "subdomain": "cristoviene",
            "subscription_status": "active",
            "subscription_tier": "starter",
            "mrr": 250.00,
            "plan": "starter",
            "city": "El Paso", "state": "TX",
            "location": "El Paso, TX",
            "created_at": (NOW - timedelta(days=30)).isoformat()
        }}, upsert=True
    )
    await db.users.update_one(
        {"email": "admin@cristoviene.church"},
        {"$set": {
            "user_id": "admin_cristoviene",
            "email": "admin@cristoviene.church",
            "name": "Cristo Viene Admin",
            "role": "church_admin",
            "tenant_id": "cristoviene-church-001",
            "password_hash": DEMO_PASSWORD_HASH,
            "is_active": True,
            "created_at": NOW_ISO
        }}, upsert=True
    )
    await db.users.update_one(
        {"email": "member@cristoviene.church"},
        {"$set": {
            "user_id": "member_cristoviene",
            "email": "member@cristoviene.church",
            "name": "Carlos",
            "role": "member",
            "tenant_id": "cristoviene-church-001",
            "password_hash": DEMO_PASSWORD_HASH,
            "is_active": True,
            "created_at": NOW_ISO
        }}, upsert=True
    )

    # Potter's House
    await db.tenants.update_one(
        {"id": "pottershouse-church-001"},
        {"$set": {
            "id": "pottershouse-church-001",
            "name": "The Potter's House",
            "subdomain": "pottershouse",
            "subscription_status": "active",
            "subscription_tier": "growth",
            "mrr": 750.00,
            "plan": "growth",
            "city": "Dallas", "state": "TX",
            "location": "Dallas, TX",
            "created_at": (NOW - timedelta(days=45)).isoformat()
        }}, upsert=True
    )
    await db.users.update_one(
        {"email": "admin@pottershouse.church"},
        {"$set": {
            "user_id": "admin_pottershouse",
            "email": "admin@pottershouse.church",
            "name": "Potter's House Admin",
            "role": "church_admin",
            "tenant_id": "pottershouse-church-001",
            "password_hash": DEMO_PASSWORD_HASH,
            "is_active": True,
            "created_at": NOW_ISO
        }}, upsert=True
    )

    print(f"  All accounts ensured")
    print(f"\n{'='*60}")
    print("SEEDING COMPLETE!")
    print(f"{'='*60}")
    print(f"\nDemo Accounts:")
    print(f"  Platform Admin: admin@solomon.ai / Demo2026!")
    for c in CAMPUSES:
        print(f"  {c['name']} Admin: {c['admin_email']} / Demo2026!")
        print(f"  {c['name']} Member: {c['member_email']} / Demo2026!")
    print(f"  Cristo Viene Admin: admin@cristoviene.church / Demo2026!")
    print(f"  Potter's House Admin: admin@pottershouse.church / Demo2026!")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
