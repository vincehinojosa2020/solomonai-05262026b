"""
Solomon AI — Master Seed Script
Generates realistic demo data for Abundant Church (3 campuses, 25K members)
El Paso, TX demographics, Pareto giving distribution, 3-year history
"""
import asyncio
import os
import random
import uuid
from datetime import datetime, timezone, timedelta, date
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import bcrypt
import logging

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger('seed')

MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ.get('DB_NAME', 'solomonai')

# ═══════ CONSTANTS ═══════
TENANT_ID = "abundant-church-001"
CAMPUSES = [
    {"id": "abundant-east-001", "name": "Abundant East", "subdomain": "abundant-east", "members_target": 12000,
     "city": "El Paso", "state": "TX", "address": "4100 E. Paisano Dr", "zip": "79905"},
    {"id": "abundant-west-001", "name": "Abundant West", "subdomain": "abundant-west", "members_target": 8000,
     "city": "El Paso", "state": "TX", "address": "7800 N. Mesa St", "zip": "79932"},
    {"id": "abundant-downtown-001", "name": "Abundant Downtown", "subdomain": "abundant-downtown", "members_target": 5000,
     "city": "El Paso", "state": "TX", "address": "11500 Pebble Hills Blvd", "zip": "79936"},
]
TOTAL_MEMBERS = 25000
ANNUAL_GIVING = 13_000_000  # $13M per year
START_DATE = date(2023, 4, 1)
END_DATE = date(2026, 3, 31)

FUNDS = [
    {"name": "General Fund", "pct": 0.75},
    {"name": "Building Fund", "pct": 0.10},
    {"name": "Missions", "pct": 0.08},
    {"name": "Youth Ministry", "pct": 0.04},
    {"name": "Benevolence", "pct": 0.03},
]

# El Paso Hispanic/Latino name pools
HISPANIC_FIRST_MALE = ["José", "Carlos", "Miguel", "Luis", "Juan", "Francisco", "Alejandro", "Daniel", "David", "Ricardo", "Andrés", "Eduardo", "Gabriel", "Fernando", "Roberto", "Diego", "Sergio", "Antonio", "Rafael", "Manuel", "Arturo", "Enrique", "Raúl", "Javier", "Marcos", "Adrián", "Óscar", "Héctor", "Pedro", "Iván", "Gustavo", "César", "Salvador", "Ramón", "Lorenzo"]
HISPANIC_FIRST_FEMALE = ["María", "Ana", "Laura", "Sofía", "Carmen", "Rosa", "Guadalupe", "Patricia", "Elena", "Lucía", "Isabella", "Valentina", "Camila", "Gabriela", "Alejandra", "Daniela", "Fernanda", "Marisol", "Teresa", "Angela", "Victoria", "Adriana", "Monica", "Diana", "Sandra", "Claudia", "Silvia", "Veronica", "Mariana", "Natalia", "Catalina", "Lorena", "Paloma", "Susana", "Esmeralda"]
ENGLISH_FIRST_MALE = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Christopher", "Matthew", "Anthony", "Mark", "Steven", "Andrew", "Joshua", "Brian", "Kevin", "Timothy", "Ronald", "Jason", "Brandon", "Eric", "Nathan", "Scott"]
ENGLISH_FIRST_FEMALE = ["Jennifer", "Jessica", "Sarah", "Ashley", "Amanda", "Stephanie", "Nicole", "Elizabeth", "Rachel", "Megan", "Lauren", "Heather", "Emily", "Michelle", "Samantha", "Rebecca", "Katherine", "Christina", "Hannah", "Brittany", "Lisa", "Kimberly", "Melissa", "Angela", "Cynthia"]
HISPANIC_LAST = ["García", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Perez", "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Cruz", "Morales", "Reyes", "Gutierrez", "Ortiz", "Ruiz", "Vargas", "Castillo", "Mendoza", "Jimenez", "Romero", "Salazar", "Aguilar", "Espinoza", "Vega", "Medina", "Delgado", "Contreras", "Rios", "Navarro", "Fuentes", "Soto", "Acosta", "Herrera", "Nunez", "Cervantes", "Pena", "Trujillo", "Silva", "Valdez", "Molina"]
ENGLISH_LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Robinson", "Clark", "Lewis"]

EL_PASO_ZIPS = ["79901", "79902", "79903", "79904", "79905", "79906", "79907", "79908", "79911", "79912", "79915", "79920", "79922", "79924", "79925", "79927", "79928", "79930", "79932", "79934", "79935", "79936", "79938"]
STREETS = ["Mesa St", "Montana Ave", "Paisano Dr", "Alameda Ave", "Dyer St", "Lee Trevino Dr", "Zaragoza Rd", "Gateway Blvd", "Transmountain Rd", "Doniphan Dr", "Rim Rd", "Resler Dr", "Shadow Mountain Dr", "Kenworthy St", "Yarbrough Dr", "Joe Battle Blvd", "Edgemere Blvd", "McRae Blvd", "Trawood Dr", "Viscount Blvd"]

GROUP_TYPES_DATA = [
    {"name": "Bible Study", "color": "#2563eb", "icon": "book-open"},
    {"name": "Life Groups", "color": "#7c3aed", "icon": "users"},
    {"name": "Men's Ministry", "color": "#0891b2", "icon": "shield"},
    {"name": "Women's Ministry", "color": "#ec4899", "icon": "heart"},
    {"name": "Youth", "color": "#f59e0b", "icon": "star"},
    {"name": "Young Adults", "color": "#10b981", "icon": "coffee"},
    {"name": "Recovery", "color": "#6366f1", "icon": "refresh-cw"},
    {"name": "Serve Teams", "color": "#ef4444", "icon": "hand-heart"},
    {"name": "Leadership", "color": "#0f172a", "icon": "award"},
]

SERMON_SERIES = [
    ("Unshakeable Faith", 6), ("Kingdom Come", 8), ("The Good Life", 5),
    ("Love Does", 4), ("All In", 7), ("Wild At Heart", 6),
    ("Fearless", 5), ("Better Together", 4), ("Breakthrough", 6),
    ("Hope Rising", 5), ("Made New", 4), ("Generous Life", 6),
    ("Rooted", 8), ("Psalms of Summer", 5), ("Born For This", 4),
    ("Family Matters", 6), ("ReNew", 5), ("The Way Forward", 4),
    ("Advent: Light of the World", 4), ("Easter: Risen", 3),
    ("Fresh Start", 5), ("Beyond Limits", 6), ("Sacred Rhythms", 4),
    ("Building Bridges", 5), ("Grace Abounds", 4), ("Identity", 6),
]

CAFE_ITEMS = [
    ("Drip Coffee", "Beverages", 2.50), ("Latte", "Beverages", 4.50),
    ("Cappuccino", "Beverages", 4.00), ("Iced Coffee", "Beverages", 3.50),
    ("Hot Chocolate", "Beverages", 3.00), ("Smoothie", "Beverages", 5.50),
    ("Croissant", "Pastries", 3.00), ("Muffin", "Pastries", 2.75),
    ("Scone", "Pastries", 3.25), ("Cinnamon Roll", "Pastries", 4.00),
    ("Breakfast Burrito", "Food", 6.50), ("Turkey Wrap", "Food", 7.00),
    ("Caesar Salad", "Food", 6.00), ("Grilled Chicken Sandwich", "Food", 7.50),
    ("Kids Meal", "Food", 4.00),
]

def uid():
    return str(uuid.uuid4())

def rand_date_between(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def seasonal_multiplier(d):
    """Returns a multiplier for giving based on month (seasonality)"""
    m = d.month
    if m == 12: return 1.35  # Christmas
    if m == 4: return 1.20   # Easter
    if m in (9, 10): return 1.10  # Stewardship campaign
    if m in (6, 7, 8): return 0.85  # Summer dip
    return 1.0

def yoy_growth(year):
    """3-5% year-over-year growth"""
    base = 2023
    return 1.0 + 0.04 * (year - base)

# ═══════ MAIN SEED FUNCTION ═══════
async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # ── STEP 0: Drop data collections (preserve system collections) ──
    log.info("Dropping data collections...")
    data_collections = [
        "people", "households", "donations", "recurring_giving", "funds",
        "attendance", "services", "service_types", "service_types_config",
        "groups", "group_members", "group_types", "group_events", "group_messages",
        "group_questions", "group_resources", "group_attendance", "group_outreach_logs",
        "events", "event_registrations", "registration_configs",
        "children", "checkins", "payouts", "platform_donors",
        "cafe_items", "cafe_orders", "cafe_settings",
        "merch_products", "merch_orders",
        "prayer_requests", "prayer_logs",
        "media_videos", "media_categories", "media",
        "volunteer_opportunities", "volunteer_signups",
        "communications", "notifications", "announcements",
        "donation_batches", "pledges",
        "songs", "service_plans", "plan_templates", "service_templates",
        "solomonpay_transactions", "payment_transactions", "payment_processor_settings",
        "solomon_conversations",
        "activity_log", "audit_log",
        "dashboard_stats_cache",
        "tenant_branding",
        "leads", "smart_lists",
        "custom_forms", "form_submissions", "custom_field_definitions",
        "courses", "course_lessons", "course_modules",
        "pathways_courses", "pathways_lessons", "pathways_enrollments",
        "next_steps", "next_steps_journeys",
        "video_notes", "watch_progress",
        "attendance_streaks", "attendance_checkins", "member_checkins",
        "workflows", "workflow_enrollments",
        "giving_goals", "giving_integrations",
        "pastor_meetings", "pastor_meeting_slots",
        "geofence_config", "checkin_locations", "checkin_stations", "checkin_labels",
    ]
    for c in data_collections:
        try:
            await db.drop_collection(c)
        except Exception:
            pass
    log.info(f"Dropped {len(data_collections)} data collections")
    
    # ── STEP 1: Create Tenants ──
    log.info("Creating tenants...")
    main_tenant = {
        "id": TENANT_ID, "name": "Abundant Church", "subdomain": "abundant",
        "plan": "enterprise", "member_limit": 50000,
        "primary_color": "#2563eb", "accent_color": "#00c896",
        "timezone": "America/Denver", "subscription_status": "active",
        "address": "4100 E. Paisano Dr", "city": "El Paso", "state": "TX",
        "website": "https://abundant.org", "phone": "(915) 555-0100",
        "created_at": datetime(2023, 1, 15, tzinfo=timezone.utc),
    }
    campus_tenants = []
    for c in CAMPUSES:
        t = {
            "id": c["id"], "name": c["name"], "subdomain": c["subdomain"],
            "plan": "enterprise", "member_limit": 50000,
            "primary_color": "#2563eb", "accent_color": "#00c896",
            "timezone": "America/Denver", "subscription_status": "active",
            "parent_tenant_id": TENANT_ID,
            "address": c["address"], "city": c["city"], "state": c["state"],
            "phone": f"(915) 555-{random.randint(1000,9999)}",
            "created_at": datetime(2023, 1, 15, tzinfo=timezone.utc),
        }
        campus_tenants.append(t)
    
    await db.tenants.insert_many([main_tenant] + campus_tenants)
    
    # Branding
    await db.tenant_branding.insert_one({
        "id": uid(), "tenant_id": TENANT_ID,
        "logo_url": "", "primary_color": "#2563eb", "accent_color": "#00c896",
        "church_name": "Abundant Church", "tagline": "Love God. Love People. Make Disciples.",
        "created_at": datetime.now(timezone.utc),
    })
    
    # ── STEP 2: Create Admin Users ──
    log.info("Creating admin users...")
    admin_pw = bcrypt.hashpw("Demo2026!".encode(), bcrypt.gensalt()).decode()
    member_pw = bcrypt.hashpw("Demo2026!".encode(), bcrypt.gensalt()).decode()
    
    users_to_insert = [
        {"user_id": uid(), "email": "admin@solomonai.us", "name": "Solomon Admin",
         "password_hash": admin_pw, "role": "platform_admin", "tenant_id": TENANT_ID,
         "permissions": [], "created_at": datetime(2023, 1, 15, tzinfo=timezone.utc)},
        {"user_id": uid(), "email": "pastor@abundant.org", "name": "Pastor David Martinez",
         "password_hash": admin_pw, "role": "admin", "role_template": "senior_pastor",
         "tenant_id": TENANT_ID, "campus_id": "campus-east",
         "permissions": [], "created_at": datetime(2023, 1, 15, tzinfo=timezone.utc)},
        {"user_id": uid(), "email": "admin@abundant.org", "name": "Shannon Nieman",
         "password_hash": admin_pw, "role": "admin", "role_template": "church_admin",
         "tenant_id": TENANT_ID, "campus_id": "campus-east",
         "permissions": [], "created_at": datetime(2023, 2, 1, tzinfo=timezone.utc)},
        {"user_id": uid(), "email": "member@abundant.org", "name": "Maria Garcia",
         "password_hash": member_pw, "role": "member",
         "tenant_id": TENANT_ID, "campus_id": "campus-east",
         "permissions": [], "created_at": datetime(2023, 3, 1, tzinfo=timezone.utc)},
    ]
    await db.users.insert_many(users_to_insert)
    
    # ── STEP 3: Create Funds ──
    log.info("Creating funds...")
    fund_ids = {}
    funds_docs = []
    for f in FUNDS:
        fid = uid()
        fund_ids[f["name"]] = fid
        funds_docs.append({
            "id": fid, "tenant_id": TENANT_ID, "name": f["name"],
            "description": f"Fund for {f['name']}", "is_active": True,
            "goal_amount": ANNUAL_GIVING * f["pct"] * 3 if f["name"] != "General Fund" else None,
            "current_amount": 0.0,
            "created_at": datetime(2023, 1, 20, tzinfo=timezone.utc),
        })
    await db.funds.insert_many(funds_docs)
    
    # ── STEP 4: Generate People & Households ──
    log.info("Generating 25,000 people and ~7,100 households...")
    
    all_people = []
    all_households = []
    household_map = {}  # hh_id -> [person_ids]
    person_campus = {}  # person_id -> campus_id
    
    campus_weights = [c["members_target"] / TOTAL_MEMBERS for c in CAMPUSES]
    
    # Age distribution
    AGE_BRACKETS = [
        (0, 4, 0.05), (5, 12, 0.10), (13, 17, 0.12), (18, 29, 0.15),
        (30, 44, 0.25), (45, 59, 0.20), (60, 85, 0.13),
    ]
    
    # Membership status distribution
    STATUS_WEIGHTS = {"active": 0.70, "inactive": 0.12, "visitor": 0.10, "new_member": 0.08}
    
    def random_age():
        r = random.random()
        cum = 0
        for lo, hi, pct in AGE_BRACKETS:
            cum += pct
            if r <= cum:
                return random.randint(lo, hi)
        return random.randint(30, 44)
    
    def random_name(gender, ethnicity):
        if ethnicity == "hispanic":
            fn = random.choice(HISPANIC_FIRST_MALE if gender == "M" else HISPANIC_FIRST_FEMALE)
            ln = random.choice(HISPANIC_LAST)
        else:
            fn = random.choice(ENGLISH_FIRST_MALE if gender == "M" else ENGLISH_FIRST_FEMALE)
            ln = random.choice(ENGLISH_LAST)
        return fn, ln
    
    def random_status():
        r = random.random()
        cum = 0
        for s, w in STATUS_WEIGHTS.items():
            cum += w
            if r <= cum:
                return s
        return "active"
    
    def random_address():
        return f"{random.randint(100, 12000)} {random.choice(STREETS)}"
    
    # Generate households first, then people
    num_households = 8500  # Higher to hit 25K people (avg hh size ~3.0 after clamping)
    people_generated = 0
    
    for hh_idx in range(num_households):
        hh_id = uid()
        campus = random.choices(CAMPUSES, weights=campus_weights)[0]
        campus_id = campus["id"]
        
        # Ethnicity: 82% Hispanic, 12% White, 6% Other
        eth = random.choices(["hispanic", "english"], weights=[0.82, 0.18])[0]
        
        hh_size = max(1, min(8, int(random.gauss(3.5, 1.2))))
        if people_generated + hh_size > TOTAL_MEMBERS:
            hh_size = TOTAL_MEMBERS - people_generated
        if hh_size <= 0:
            break
        
        _, hh_last = random_name("M", eth)
        zip_code = random.choice(EL_PASO_ZIPS)
        
        hh_doc = {
            "id": hh_id, "tenant_id": TENANT_ID, "name": f"The {hh_last} Family",
            "address_line1": random_address(), "city": "El Paso", "state": "TX",
            "zip": zip_code, "country": "US",
            "phone": f"(915) {random.randint(200,999)}-{random.randint(1000,9999)}",
            "created_at": datetime(2023, random.randint(1, 12), random.randint(1, 28), tzinfo=timezone.utc),
        }
        all_households.append(hh_doc)
        household_map[hh_id] = []
        
        for member_idx in range(hh_size):
            pid = uid()
            if member_idx == 0:
                gender = "M"
                age = random.randint(28, 65)
                is_head = True
            elif member_idx == 1:
                gender = "F"
                age = random.randint(26, 63)
                is_head = False
            else:
                gender = random.choice(["M", "F"])
                age = random.randint(1, 22)
                is_head = False
            
            fn, ln = random_name(gender, eth)
            if member_idx > 0:
                ln = hh_last  # Same last name
            
            birth_year = 2026 - age
            dob = f"{birth_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            
            status = random_status() if age >= 13 else "active"
            join_date = rand_date_between(START_DATE, END_DATE)
            if status == "new_member":
                join_date = rand_date_between(date(2025, 10, 1), END_DATE)
            
            email = None
            if age >= 16:
                email_base = f"{fn.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}.{ln.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}"
                email = f"{email_base}{random.randint(1,999)}@{'gmail.com' if random.random() < 0.6 else 'yahoo.com' if random.random() < 0.5 else 'outlook.com'}"
            
            phone = None
            if age >= 16:
                phone = f"(915) {random.randint(200,999)}-{random.randint(1000,9999)}"
            
            person = {
                "id": pid, "tenant_id": TENANT_ID,
                "first_name": fn, "last_name": ln,
                "email": email, "mobile_phone": phone,
                "date_of_birth": dob, "gender": gender,
                "membership_status": status,
                "membership_date": join_date.isoformat() if status in ("active", "new_member") else None,
                "household_id": hh_id, "campus": campus_id,
                "is_head_of_household": is_head,
                "engagement_score": 0,  # Calculated later
                "ytd_giving": 0.0, "lifetime_giving": 0.0,
                "custom_fields": {},
                "giving_anonymous": random.random() < 0.02,
                "paperless_statements": random.random() < 0.7,
                "created_at": datetime.combine(join_date, datetime.min.time()).replace(tzinfo=timezone.utc),
            }
            all_people.append(person)
            household_map[hh_id].append(pid)
            person_campus[pid] = campus_id
            people_generated += 1
        
        if people_generated >= TOTAL_MEMBERS:
            break
    
    log.info(f"Generated {len(all_people)} people in {len(all_households)} households")
    
    # Bulk insert
    for i in range(0, len(all_households), 5000):
        await db.households.insert_many(all_households[i:i+5000])
    for i in range(0, len(all_people), 5000):
        await db.people.insert_many(all_people[i:i+5000])
    log.info("People + Households inserted")
    
    # ── STEP 5: Assign Donor Tiers (Pareto) ──
    log.info("Assigning donor tiers (Pareto distribution)...")
    adults = [p for p in all_people if p.get("date_of_birth") and int(p["date_of_birth"][:4]) <= 2008]
    random.shuffle(adults)
    
    # Tier assignments
    n = len(adults)
    tier1 = adults[:int(n * 0.02)]         # Top 2% — Anchor ($5K-$25K/yr)
    tier2 = adults[int(n*0.02):int(n*0.20)] # Next 18% — Committed ($1.2K-$5K/yr)
    tier3 = adults[int(n*0.20):int(n*0.50)] # Next 30% — Regular ($200-$1.2K/yr)
    tier4 = adults[int(n*0.50):int(n*0.75)] # Next 25% — Occasional ($15-$120/yr)
    tier5 = adults[int(n*0.75):]            # Remaining 25% — Rare ($0-$30/yr)
    
    donor_annual_budget = {}  # person_id -> annual budget
    for p in tier1:
        donor_annual_budget[p["id"]] = random.uniform(5000, 25000)
    for p in tier2:
        donor_annual_budget[p["id"]] = random.uniform(1200, 5000)
    for p in tier3:
        donor_annual_budget[p["id"]] = random.uniform(200, 1200)
    for p in tier4:
        donor_annual_budget[p["id"]] = random.uniform(15, 120)
    for p in tier5:
        donor_annual_budget[p["id"]] = random.uniform(0, 30)
    
    # ── STEP 6: Generate Donations (3 years) ──
    log.info("Generating 3 years of donations...")
    all_donations = []
    all_recurring = []
    person_giving_total = {}
    person_ytd = {}
    person_donation_count = {}
    
    fund_names = [f["name"] for f in FUNDS]
    fund_weights = [f["pct"] for f in FUNDS]
    
    # Create recurring giving schedules for tier1 and tier2
    recurring_map = {}  # person_id -> recurring schedule
    recurring_docs = []
    
    for p in tier1 + tier2:
        if random.random() < 0.85:  # 85% of top tiers are recurring
            freq = random.choices(["monthly", "biweekly", "weekly", "annually"], weights=[0.50, 0.25, 0.15, 0.10])[0]
            fund = random.choices(fund_names, weights=fund_weights)[0]
            annual = donor_annual_budget[p["id"]]
            
            if freq == "weekly": amt = round(annual / 52, 2)
            elif freq == "biweekly": amt = round(annual / 26, 2)
            elif freq == "monthly": amt = round(annual / 12, 2)
            else: amt = round(annual, 2)
            
            start = rand_date_between(START_DATE, date(2025, 6, 1))
            is_paused = random.random() < 0.05
            is_cancelled = random.random() < 0.10
            
            rec_id = uid()
            status = "active"
            if is_cancelled: status = "cancelled"
            elif is_paused: status = "paused"
            
            rec_doc = {
                "id": rec_id, "tenant_id": TENANT_ID,
                "person_id": p["id"], "fund_id": fund_ids.get(fund, fund_ids["General Fund"]),
                "fund_name": fund, "amount": amt, "frequency": freq,
                "payment_method": random.choice(["card", "card", "card", "ach"]),
                "next_gift_date": None,
                "is_active": status == "active",
                "status": status,
                "card_last_four": f"{random.randint(1000,9999)}",
                "card_brand": random.choice(["Visa", "Mastercard", "Amex"]),
                "created_at": datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc),
            }
            recurring_docs.append(rec_doc)
            recurring_map[p["id"]] = {"id": rec_id, "freq": freq, "amt": amt, "fund": fund, "start": start, "method": rec_doc["payment_method"]}
    
    # Also add tier3 recurring (more aggressive to hit 8K target)
    for p in tier3:
        if random.random() < 0.55:
            fund = "General Fund"
            annual = donor_annual_budget[p["id"]]
            amt = round(annual / 12, 2)
            if amt < 5:
                continue
            start = rand_date_between(date(2024, 1, 1), date(2025, 12, 1))
            rec_id = uid()
            rec_doc = {
                "id": rec_id, "tenant_id": TENANT_ID,
                "person_id": p["id"], "fund_id": fund_ids["General Fund"],
                "fund_name": fund, "amount": amt, "frequency": "monthly",
                "payment_method": "card", "next_gift_date": None,
                "is_active": True, "status": "active",
                "card_last_four": f"{random.randint(1000,9999)}",
                "card_brand": random.choice(["Visa", "Mastercard"]),
                "created_at": datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc),
            }
            recurring_docs.append(rec_doc)
            recurring_map[p["id"]] = {"id": rec_id, "freq": "monthly", "amt": amt, "fund": fund, "start": start, "method": "card"}
    
    log.info(f"Created {len(recurring_docs)} recurring giving schedules")
    
    # Generate actual donation transactions
    current = START_DATE
    donation_count = 0
    
    while current <= END_DATE:
        year = current.year
        month = current.month
        growth = yoy_growth(year)
        season = seasonal_multiplier(current)
        
        # Process recurring donations for this week
        for pid, rec in recurring_map.items():
            if rec["start"] > current:
                continue
            
            should_give = False
            if rec["freq"] == "weekly":
                should_give = current.weekday() == 6  # Sundays
            elif rec["freq"] == "biweekly":
                week_num = (current - rec["start"]).days // 7
                should_give = current.weekday() == 6 and week_num % 2 == 0
            elif rec["freq"] == "monthly":
                should_give = current.day <= 7 and current.weekday() == 6
            elif rec["freq"] == "annually":
                should_give = current.month == rec["start"].month and current.day <= 7
            
            if should_give:
                amt = round(rec["amt"] * growth * season * random.uniform(0.95, 1.05), 2)
                fund = rec["fund"]
                method = rec["method"]
                
                fee = round(amt * 0.019 + 0.30, 2) if method == "card" else round(amt * 0.008 + 0.30, 2)
                cover_fee = random.random() < 0.15
                if cover_fee:
                    amt = round(amt + fee, 2)
                
                donation = {
                    "id": uid(), "tenant_id": TENANT_ID,
                    "person_id": pid, "fund_id": fund_ids.get(fund, fund_ids["General Fund"]),
                    "fund_name": fund, "amount": amt,
                    "donation_date": current.isoformat(),
                    "payment_method": method,
                    "is_recurring": True, "recurring_id": rec["id"],
                    "status": "completed", "source": "solomonpay",
                    "fee_amount": fee, "net_amount": round(amt - fee, 2),
                    "cover_fees": cover_fee,
                    "created_at": datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc, hour=random.randint(7, 12)),
                }
                all_donations.append(donation)
                person_giving_total[pid] = person_giving_total.get(pid, 0) + amt
                if current.year == 2026:
                    person_ytd[pid] = person_ytd.get(pid, 0) + amt
                person_donation_count[pid] = person_donation_count.get(pid, 0) + 1
                donation_count += 1
        
        # Non-recurring (occasional) donations on Sundays
        if current.weekday() == 6:
            # Tier3 occasional giving
            for p in tier3:
                if p["id"] in recurring_map:
                    continue
                if random.random() < 0.015 * season:  # ~1.5% chance per Sunday
                    budget = donor_annual_budget[p["id"]]
                    amt = round(random.uniform(budget * 0.1, budget * 0.4) * growth, 2)
                    if amt < 5:
                        continue
                    fund = random.choices(fund_names, weights=fund_weights)[0]
                    method = random.choices(["card", "ach", "cash", "check"], weights=[0.65, 0.15, 0.10, 0.10])[0]
                    fee = 0
                    if method == "card":
                        fee = round(amt * 0.019 + 0.30, 2)
                    elif method == "ach":
                        fee = round(amt * 0.008 + 0.30, 2)
                    
                    donation = {
                        "id": uid(), "tenant_id": TENANT_ID,
                        "person_id": p["id"], "fund_id": fund_ids.get(fund, fund_ids["General Fund"]),
                        "fund_name": fund, "amount": amt,
                        "donation_date": current.isoformat(),
                        "payment_method": method,
                        "is_recurring": False, "status": "completed", "source": "solomonpay",
                        "fee_amount": fee, "net_amount": round(amt - fee, 2),
                        "created_at": datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc, hour=random.randint(8, 14)),
                    }
                    all_donations.append(donation)
                    person_giving_total[p["id"]] = person_giving_total.get(p["id"], 0) + amt
                    if current.year == 2026:
                        person_ytd[p["id"]] = person_ytd.get(p["id"], 0) + amt
                    person_donation_count[p["id"]] = person_donation_count.get(p["id"], 0) + 1
                    donation_count += 1
            
            # Tier4 occasional
            for p in tier4:
                if random.random() < 0.004 * season:
                    amt = round(random.uniform(15, 50) * growth, 2)
                    fund = random.choices(fund_names, weights=fund_weights)[0]
                    method = random.choices(["card", "cash", "check"], weights=[0.6, 0.25, 0.15])[0]
                    fee = round(amt * 0.019 + 0.30, 2) if method == "card" else 0
                    
                    donation = {
                        "id": uid(), "tenant_id": TENANT_ID,
                        "person_id": p["id"], "fund_id": fund_ids.get(fund, fund_ids["General Fund"]),
                        "fund_name": fund, "amount": amt,
                        "donation_date": current.isoformat(),
                        "payment_method": method,
                        "is_recurring": False, "status": "completed", "source": "solomonpay",
                        "fee_amount": fee, "net_amount": round(amt - fee, 2),
                        "created_at": datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc, hour=random.randint(8, 14)),
                    }
                    all_donations.append(donation)
                    person_giving_total[p["id"]] = person_giving_total.get(p["id"], 0) + amt
                    if current.year == 2026:
                        person_ytd[p["id"]] = person_ytd.get(p["id"], 0) + amt
                    person_donation_count[p["id"]] = person_donation_count.get(p["id"], 0) + 1
                    donation_count += 1
            
            # Tier5 rare
            for p in tier5:
                if random.random() < 0.001 * season:
                    amt = round(random.uniform(10, 30) * growth, 2)
                    method = random.choices(["card", "cash"], weights=[0.5, 0.5])[0]
                    fee = round(amt * 0.019 + 0.30, 2) if method == "card" else 0
                    
                    donation = {
                        "id": uid(), "tenant_id": TENANT_ID,
                        "person_id": p["id"], "fund_id": fund_ids["General Fund"],
                        "fund_name": "General Fund", "amount": amt,
                        "donation_date": current.isoformat(),
                        "payment_method": method,
                        "is_recurring": False, "status": "completed", "source": "solomonpay",
                        "fee_amount": fee, "net_amount": round(amt - fee, 2),
                        "created_at": datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc, hour=random.randint(8, 14)),
                    }
                    all_donations.append(donation)
                    person_giving_total[p["id"]] = person_giving_total.get(p["id"], 0) + amt
                    if current.year == 2026:
                        person_ytd[p["id"]] = person_ytd.get(p["id"], 0) + amt
                    person_donation_count[p["id"]] = person_donation_count.get(p["id"], 0) + 1
                    donation_count += 1
        
        # Batch insert every 50K donations
        if len(all_donations) >= 50000:
            await db.donations.insert_many(all_donations)
            log.info(f"  Inserted batch: {donation_count:,} total donations so far")
            all_donations = []
        
        current += timedelta(days=1)
    
    # Final insert
    if all_donations:
        await db.donations.insert_many(all_donations)
    log.info(f"Total donations: {donation_count:,}")
    
    # Insert recurring giving
    if recurring_docs:
        for i in range(0, len(recurring_docs), 5000):
            await db.recurring_giving.insert_many(recurring_docs[i:i+5000])
    
    # Update people with giving totals and engagement scores
    log.info("Updating people with giving totals and engagement scores...")
    bulk_ops = []
    from pymongo import UpdateOne
    for p in all_people:
        pid = p["id"]
        lifetime = round(person_giving_total.get(pid, 0), 2)
        ytd = round(person_ytd.get(pid, 0), 2)
        count = person_donation_count.get(pid, 0)
        
        # Engagement score: 0-100 based on giving + will add attendance later
        score = min(50, int(count * 2))  # Giving component (max 50)
        
        if lifetime > 0 or score > 0:
            bulk_ops.append(UpdateOne(
                {"id": pid},
                {"$set": {"lifetime_giving": lifetime, "ytd_giving": ytd, "engagement_score": score}}
            ))
        
        if len(bulk_ops) >= 5000:
            await db.people.bulk_write(bulk_ops)
            bulk_ops = []
    if bulk_ops:
        await db.people.bulk_write(bulk_ops)
    
    # ── STEP 7: Generate Service Types & Attendance ──
    log.info("Generating service types and attendance...")
    
    service_type_ids = {}
    st_docs = []
    for campus in CAMPUSES:
        for svc_name, svc_time in [("Sunday 9:00 AM", "09:00"), ("Sunday 11:00 AM", "11:00")]:
            stid = uid()
            service_type_ids[f"{campus['id']}_{svc_time}"] = stid
            st_docs.append({
                "id": stid, "tenant_id": TENANT_ID, "name": f"{campus['name']} {svc_name}",
                "default_time": svc_time, "default_day": "Sunday", "is_active": True,
                "campus_id": campus["id"],
                "created_at": datetime(2023, 1, 15, tzinfo=timezone.utc),
            })
    # Flagship evening service
    stid = uid()
    service_type_ids["campus-east_18:00"] = stid
    st_docs.append({
        "id": stid, "tenant_id": TENANT_ID, "name": "Abundant East Sunday 6:00 PM",
        "default_time": "18:00", "default_day": "Sunday", "is_active": True,
        "campus_id": "campus-east",
        "created_at": datetime(2023, 1, 15, tzinfo=timezone.utc),
    })
    await db.service_types.insert_many(st_docs)
    
    # Generate weekly services and attendance
    all_services = []
    all_attendance = []
    person_attendance_count = {}
    
    current = START_DATE
    # Find first Sunday
    while current.weekday() != 6:
        current += timedelta(days=1)
    
    campus_people = {}
    for c in CAMPUSES:
        campus_people[c["id"]] = [p for p in all_people if p["campus"] == c["id"] and int(p["date_of_birth"][:4]) <= 2013]
    
    while current <= END_DATE:
        season = seasonal_multiplier(current)
        growth = yoy_growth(current.year)
        
        for campus in CAMPUSES:
            cid = campus["id"]
            cp = campus_people[cid]
            base_attendance_rate = 0.55 * season * min(growth, 1.1)
            
            for svc_time in ["09:00", "11:00"]:
                key = f"{cid}_{svc_time}"
                if key not in service_type_ids:
                    continue
                
                svc_id = uid()
                headcount = int(len(cp) * base_attendance_rate * 0.5 * random.uniform(0.9, 1.1))
                
                all_services.append({
                    "id": svc_id, "tenant_id": TENANT_ID,
                    "service_type_id": service_type_ids[key],
                    "date": current.isoformat(), "time": svc_time,
                    "total_headcount": headcount,
                    "created_at": datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc),
                })
                
                # Sample attendees
                attendees = random.sample(cp, min(headcount, len(cp)))
                for person in attendees:
                    all_attendance.append({
                        "id": uid(), "tenant_id": TENANT_ID,
                        "service_id": svc_id, "person_id": person["id"],
                        "check_in_time": datetime.combine(current, datetime.min.time()).replace(
                            tzinfo=timezone.utc, hour=int(svc_time[:2]), minute=random.randint(0, 30)),
                    })
                    person_attendance_count[person["id"]] = person_attendance_count.get(person["id"], 0) + 1
            
            # Evening service for East only
            if cid == "campus-east":
                key = "campus-east_18:00"
                svc_id = uid()
                headcount = int(len(cp) * base_attendance_rate * 0.2 * random.uniform(0.85, 1.15))
                all_services.append({
                    "id": svc_id, "tenant_id": TENANT_ID,
                    "service_type_id": service_type_ids[key],
                    "date": current.isoformat(), "time": "18:00",
                    "total_headcount": headcount,
                    "created_at": datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc),
                })
                attendees = random.sample(cp, min(headcount, len(cp)))
                for person in attendees:
                    all_attendance.append({
                        "id": uid(), "tenant_id": TENANT_ID,
                        "service_id": svc_id, "person_id": person["id"],
                        "check_in_time": datetime.combine(current, datetime.min.time()).replace(
                            tzinfo=timezone.utc, hour=18, minute=random.randint(0, 20)),
                    })
                    person_attendance_count[person["id"]] = person_attendance_count.get(person["id"], 0) + 1
        
        # Batch insert
        if len(all_attendance) >= 50000:
            await db.attendance.insert_many(all_attendance)
            await db.services.insert_many(all_services)
            log.info(f"  Attendance batch: {sum(person_attendance_count.values()):,} records")
            all_attendance = []
            all_services = []
        
        current += timedelta(days=7)
    
    if all_attendance:
        await db.attendance.insert_many(all_attendance)
    if all_services:
        await db.services.insert_many(all_services)
    total_att = sum(person_attendance_count.values())
    log.info(f"Total attendance records: {total_att:,}")
    
    # Update engagement scores with attendance component
    log.info("Updating engagement scores with attendance...")
    bulk_ops = []
    for pid, att_count in person_attendance_count.items():
        att_score = min(50, int(att_count * 0.3))  # Attendance component (max 50)
        bulk_ops.append(UpdateOne(
            {"id": pid},
            {"$inc": {"engagement_score": att_score}, "$set": {"last_attended_at": END_DATE.isoformat()}}
        ))
        if len(bulk_ops) >= 5000:
            await db.people.bulk_write(bulk_ops)
            bulk_ops = []
    if bulk_ops:
        await db.people.bulk_write(bulk_ops)
    
    # ── STEP 8: Generate Groups ──
    log.info("Generating groups...")
    
    group_type_ids = {}
    gt_docs = []
    for gt in GROUP_TYPES_DATA:
        gtid = uid()
        group_type_ids[gt["name"]] = gtid
        gt_docs.append({
            "id": gtid, "tenant_id": TENANT_ID, "name": gt["name"],
            "color": gt["color"], "icon": gt["icon"],
        })
    await db.group_types.insert_many(gt_docs)
    
    all_groups = []
    all_group_members = []
    
    for campus in CAMPUSES:
        cid = campus["id"]
        cp = [p for p in all_people if p["campus"] == cid and int(p["date_of_birth"][:4]) <= 2008]
        
        num_groups = int(len(cp) / 70)  # ~1 group per 70 adults
        for _ in range(num_groups):
            gt_name = random.choice(list(group_type_ids.keys()))
            gid = uid()
            leader = random.choice(cp)
            size = random.randint(8, 25)
            members = random.sample(cp, min(size, len(cp)))
            
            group = {
                "id": gid, "tenant_id": TENANT_ID,
                "name": f"{campus['name'].split()[-1]} {gt_name} {random.randint(1,50)}",
                "description": f"A {gt_name.lower()} group at {campus['name']}",
                "group_type_id": group_type_ids[gt_name],
                "leader_id": leader["id"],
                "meeting_day": random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
                "meeting_time": random.choice(["6:30 PM", "7:00 PM", "7:30 PM"]),
                "location": random.choice(["Campus Room A", "Campus Room B", "Host Home", "Fellowship Hall", "Youth Room"]),
                "capacity": size + 5,
                "member_count": len(members),
                "is_open": random.random() < 0.8,
                "is_active": True,
                "campus_id": cid,
                "enrollment_type": "open",
                "created_at": datetime.combine(rand_date_between(START_DATE, date(2025, 6, 1)), datetime.min.time()).replace(tzinfo=timezone.utc),
            }
            all_groups.append(group)
            
            for m in members:
                all_group_members.append({
                    "id": uid(), "tenant_id": TENANT_ID,
                    "group_id": gid, "person_id": m["id"],
                    "role": "leader" if m["id"] == leader["id"] else "member",
                    "joined_at": rand_date_between(START_DATE, END_DATE).isoformat(),
                    "is_active": True,
                })
    
    log.info(f"Generated {len(all_groups)} groups with {len(all_group_members)} memberships")
    for i in range(0, len(all_groups), 5000):
        await db.groups.insert_many(all_groups[i:i+5000])
    for i in range(0, len(all_group_members), 5000):
        await db.group_members.insert_many(all_group_members[i:i+5000])
    
    # ── STEP 9: Generate Events ──
    log.info("Generating events...")
    event_docs = []
    reg_docs = []
    
    event_templates = [
        ("Abundant Conference", 2000, True), ("VBS: Ocean Adventures", 500, True),
        ("Women's Retreat", 200, True), ("Men's Breakfast", 150, True),
        ("Youth Lock-In", 100, True), ("Baptism Sunday", None, False),
        ("Easter Egg Hunt", 300, True), ("Fall Festival", 1000, True),
        ("Christmas Eve Service", None, False), ("New Year's Prayer Night", 500, False),
        ("Marriage Retreat", 100, True), ("Volunteer Appreciation Night", 200, False),
        ("Outreach: Feed El Paso", 300, True), ("Leadership Summit", 80, True),
        ("Worship Night", None, False), ("Back to School Bash", 400, True),
    ]
    
    for year in [2023, 2024, 2025, 2026]:
        for template in event_templates:
            name, cap, has_reg = template
            if year == 2026 and random.random() > 0.4:
                continue
            
            month = random.randint(1, 12) if year < 2026 else random.randint(4, 6)
            day = random.randint(1, 28)
            campus = random.choice(CAMPUSES)
            eid = uid()
            
            evt = {
                "id": eid, "tenant_id": TENANT_ID,
                "name": f"{name} {year}", "description": f"Annual {name} event at {campus['name']}",
                "location": f"{campus['name']} - Main Auditorium",
                "start_datetime": f"{year}-{month:02d}-{day:02d}T09:00:00",
                "end_datetime": f"{year}-{month:02d}-{day:02d}T17:00:00",
                "is_public": True, "capacity": cap,
                "registration_required": has_reg,
                "registration_count": 0, "campus_id": campus["id"],
                "created_at": datetime(year, max(1, month-1), 15, tzinfo=timezone.utc),
            }
            
            if has_reg and cap:
                reg_count = random.randint(int(cap * 0.3), int(cap * 0.9))
                evt["registration_count"] = reg_count
                cp = [p for p in all_people if p["campus"] == campus["id"]]
                for registrant in random.sample(cp, min(reg_count, len(cp))):
                    reg_docs.append({
                        "id": uid(), "tenant_id": TENANT_ID,
                        "event_id": eid, "person_id": registrant["id"],
                        "name": f"{registrant['first_name']} {registrant['last_name']}",
                        "email": registrant.get("email", ""),
                        "status": "confirmed",
                        "registered_at": datetime(year, month, random.randint(1, day), tzinfo=timezone.utc),
                    })
            
            event_docs.append(evt)
    
    await db.events.insert_many(event_docs)
    if reg_docs:
        for i in range(0, len(reg_docs), 5000):
            await db.event_registrations.insert_many(reg_docs[i:i+5000])
    log.info(f"Generated {len(event_docs)} events, {len(reg_docs)} registrations")
    
    # ── STEP 10: Generate Children & Check-ins ──
    log.info("Generating children and check-in records...")
    children_docs = []
    checkin_docs = []
    
    families_with_kids = [(hh_id, members) for hh_id, members in household_map.items() if len(members) > 2]
    selected_families = random.sample(families_with_kids, min(500, len(families_with_kids)))
    
    classrooms = ["Nursery (0-2)", "Toddlers (2-3)", "Pre-K (4-5)", "Kindergarten", "1st-2nd Grade", "3rd-4th Grade", "5th-6th Grade"]
    
    for hh_id, member_ids in selected_families:
        parent_person = next((p for p in all_people if p["id"] == member_ids[0]), None)
        if not parent_person:
            continue
        
        num_kids = random.randint(1, 3)
        for _ in range(num_kids):
            age = random.randint(0, 12)
            child_id = uid()
            child = {
                "id": child_id, "tenant_id": TENANT_ID,
                "parent_user_id": member_ids[0],
                "name": random.choice(HISPANIC_FIRST_MALE + HISPANIC_FIRST_FEMALE + ENGLISH_FIRST_MALE + ENGLISH_FIRST_FEMALE) + " " + parent_person["last_name"],
                "first_name": random.choice(HISPANIC_FIRST_MALE + ENGLISH_FIRST_MALE if random.random() < 0.5 else HISPANIC_FIRST_FEMALE + ENGLISH_FIRST_FEMALE),
                "last_name": parent_person["last_name"],
                "birthdate": f"{2026-age}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "allergies": random.choice([None, None, None, "Peanuts", "Dairy", "Gluten"]),
                "special_needs": None,
                "grade": classrooms[min(age // 2, len(classrooms)-1)] if age >= 2 else "Nursery (0-2)",
                "classroom": classrooms[min(age // 2, len(classrooms)-1)] if age >= 2 else "Nursery (0-2)",
                "campus_id": parent_person.get("campus", "campus-east"),
                "created_at": datetime.combine(rand_date_between(START_DATE, END_DATE), datetime.min.time()).replace(tzinfo=timezone.utc),
            }
            children_docs.append(child)
            
            # Generate check-in records for past year
            num_checkins = random.randint(10, 45)
            for _ in range(num_checkins):
                ci_date = rand_date_between(date(2025, 4, 1), END_DATE)
                if ci_date.weekday() != 6:
                    continue
                pickup_code = f"{random.randint(1000, 9999)}"
                checkin_docs.append({
                    "id": uid(), "tenant_id": TENANT_ID,
                    "child_id": child_id, "child_name": child["name"],
                    "parent_user_id": member_ids[0],
                    "parent_name": f"{parent_person['first_name']} {parent_person['last_name']}",
                    "pickup_code": pickup_code,
                    "classroom": child["classroom"],
                    "status": "checked_out",
                    "checked_in_at": datetime.combine(ci_date, datetime.min.time()).replace(tzinfo=timezone.utc, hour=9, minute=random.randint(0, 30)),
                    "checked_out_at": datetime.combine(ci_date, datetime.min.time()).replace(tzinfo=timezone.utc, hour=12, minute=random.randint(0, 30)),
                })
    
    await db.children.insert_many(children_docs)
    if checkin_docs:
        for i in range(0, len(checkin_docs), 5000):
            await db.checkins.insert_many(checkin_docs[i:i+5000])
    log.info(f"Generated {len(children_docs)} children, {len(checkin_docs)} check-ins")
    
    # ── STEP 11: Generate Payouts ──
    log.info("Generating weekly payouts...")
    payout_docs = []
    current = START_DATE
    while current.weekday() != 4:  # First Friday
        current += timedelta(days=1)
    
    while current <= END_DATE:
        period_end = current
        period_start = current - timedelta(days=7)
        
        for campus in CAMPUSES:
            cid = campus["id"]
            # Sum donations for this campus in this period
            campus_pids = set(p["id"] for p in all_people if p["campus"] == cid)
            # Estimate based on proportional campus size
            total_fraction = campus["members_target"] / TOTAL_MEMBERS
            weekly_giving = ANNUAL_GIVING / 52 * total_fraction * yoy_growth(current.year) * seasonal_multiplier(current)
            gross = round(weekly_giving * random.uniform(0.9, 1.1), 2)
            fees = round(gross * 0.019, 2)
            net = round(gross - fees, 2)
            
            payout_docs.append({
                "id": uid(), "tenant_id": TENANT_ID, "campus_id": cid,
                "amount": gross, "fee_amount": fees, "net_amount": net,
                "status": "completed" if current < date(2026, 3, 28) else "pending",
                "bank_last_four": f"{random.randint(1000,9999)}",
                "bank_name": f"{campus['name']} Operating Account",
                "transaction_count": random.randint(80, 400),
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "created_at": datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc),
            })
        
        current += timedelta(days=7)
    
    await db.payouts.insert_many(payout_docs)
    log.info(f"Generated {len(payout_docs)} payouts")
    
    # ── STEP 12: Cafe, Merch, Prayer, Sermons, Courses, Volunteers, Communications ──
    log.info("Generating cafe items and orders...")
    cafe_item_docs = []
    for name, cat, price in CAFE_ITEMS:
        cafe_item_docs.append({
            "id": uid(), "tenant_id": TENANT_ID, "name": name,
            "category": cat, "price": price, "is_active": True,
            "is_featured": random.random() < 0.2,
            "created_at": datetime(2023, 3, 1, tzinfo=timezone.utc),
        })
    await db.cafe_items.insert_many(cafe_item_docs)
    
    cafe_order_docs = []
    # Generate exactly on Sundays for the past year
    cafe_sunday = START_DATE
    while cafe_sunday.weekday() != 6:
        cafe_sunday += timedelta(days=1)
    cafe_sundays = []
    while cafe_sunday <= END_DATE:
        if cafe_sunday >= date(2025, 4, 1):
            cafe_sundays.append(cafe_sunday)
        cafe_sunday += timedelta(days=7)
    
    for d in cafe_sundays:
        num_orders = random.randint(30, 50)
        for _ in range(num_orders):
            pass  # Generate below
    
    # Flatten: generate ~2000 cafe orders on Sundays
    for _ in range(2000):
        d = random.choice(cafe_sundays) if cafe_sundays else END_DATE
        person = random.choice(adults)
        items = random.sample(cafe_item_docs, random.randint(1, 3))
        order_items = [{"item_id": it["id"], "name": it["name"], "price": it["price"], "quantity": 1} for it in items]
        total = sum(i["price"] for i in order_items)
        cafe_order_docs.append({
            "id": uid(), "tenant_id": TENANT_ID, "user_id": person["id"],
            "items": order_items, "total": round(total, 2),
            "pickup_time": f"{random.choice(['9:30', '10:00', '10:30', '11:30', '12:00'])} AM",
            "status": "completed",
            "created_at": datetime.combine(d, datetime.min.time()).replace(tzinfo=timezone.utc, hour=random.randint(8, 12)),
        })
    if cafe_order_docs:
        await db.cafe_orders.insert_many(cafe_order_docs)
    log.info(f"Generated {len(cafe_order_docs)} cafe orders")
    
    log.info("Generating merch products and orders...")
    merch_items = [
        ("Abundant Church T-Shirt", "Apparel", 25.00), ("Abundant Hoodie", "Apparel", 45.00),
        ("Abundant Hat", "Accessories", 18.00), ("Faith Over Fear Tee", "Apparel", 22.00),
        ("Daily Devotional Journal", "Books", 15.00), ("Abundant Coffee Mug", "Accessories", 12.00),
        ("Kids Bible Story Book", "Books", 10.00), ("Worship Night Poster", "Art", 8.00),
        ("Abundant Water Bottle", "Accessories", 16.00), ("Sunday School Kit", "Resources", 20.00),
    ]
    merch_docs = []
    for name, cat, price in merch_items:
        merch_docs.append({
            "id": uid(), "tenant_id": TENANT_ID, "name": name,
            "category": cat, "price": price, "is_active": True,
            "is_featured": random.random() < 0.3, "inventory": random.randint(20, 200),
            "created_at": datetime(2023, 6, 1, tzinfo=timezone.utc),
        })
    await db.merch_products.insert_many(merch_docs)
    
    merch_order_docs = []
    for _ in range(500):
        d = rand_date_between(date(2025, 1, 1), END_DATE)
        person = random.choice(adults)
        items = random.sample(merch_docs, random.randint(1, 2))
        order_items = [{"product_id": it["id"], "name": it["name"], "price": it["price"], "quantity": 1} for it in items]
        total = sum(i["price"] for i in order_items)
        merch_order_docs.append({
            "id": uid(), "tenant_id": TENANT_ID, "user_id": person["id"],
            "items": order_items, "total": round(total, 2), "status": "completed",
            "created_at": datetime.combine(d, datetime.min.time()).replace(tzinfo=timezone.utc),
        })
    await db.merch_orders.insert_many(merch_order_docs)
    log.info(f"Generated {len(merch_order_docs)} merch orders")
    
    log.info("Generating prayer requests...")
    prayer_categories = ["healing", "family", "financial", "guidance", "thanksgiving", "general"]
    prayer_titles = ["Healing for my mother", "Job transition", "Family restoration", "Financial breakthrough",
                     "Guidance for career", "Thanksgiving for answered prayer", "Peace in difficult season",
                     "Strength for loved one", "Protection for family", "Wisdom for decisions"]
    prayer_docs = []
    for _ in range(200):
        person = random.choice(adults)
        prayer_docs.append({
            "id": uid(), "tenant_id": TENANT_ID, "user_id": person["id"],
            "user_name": f"{person['first_name']} {person['last_name']}",
            "category": random.choice(prayer_categories),
            "title": random.choice(prayer_titles),
            "content": "Please keep my family in your prayers during this season.",
            "is_public": random.random() < 0.6, "is_anonymous": random.random() < 0.15,
            "prayer_count": random.randint(0, 50), "status": "active",
            "created_at": datetime.combine(rand_date_between(date(2025, 1, 1), END_DATE), datetime.min.time()).replace(tzinfo=timezone.utc),
        })
    await db.prayer_requests.insert_many(prayer_docs)
    
    log.info("Generating sermon library...")
    sermon_docs = []
    cat_docs = [
        {"id": uid(), "tenant_id": TENANT_ID, "name": "Faith", "slug": "faith", "icon": "book-open", "sort_order": 0, "is_active": True, "created_at": datetime.now(timezone.utc)},
        {"id": uid(), "tenant_id": TENANT_ID, "name": "Family", "slug": "family", "icon": "home", "sort_order": 1, "is_active": True, "created_at": datetime.now(timezone.utc)},
        {"id": uid(), "tenant_id": TENANT_ID, "name": "Leadership", "slug": "leadership", "icon": "award", "sort_order": 2, "is_active": True, "created_at": datetime.now(timezone.utc)},
    ]
    await db.media_categories.insert_many(cat_docs)
    
    sermon_idx = 0
    current = START_DATE
    while current.weekday() != 6:
        current += timedelta(days=1)
    
    series_idx = 0
    weeks_in_series = 0
    current_series = SERMON_SERIES[0]
    
    while current <= END_DATE and sermon_idx < 156:
        if weeks_in_series >= current_series[1]:
            series_idx = (series_idx + 1) % len(SERMON_SERIES)
            current_series = SERMON_SERIES[series_idx]
            weeks_in_series = 0
        
        sermon_docs.append({
            "id": uid(), "tenant_id": TENANT_ID,
            "title": f"{current_series[0]} — Part {weeks_in_series + 1}",
            "description": f"Week {weeks_in_series + 1} of the {current_series[0]} series",
            "youtube_id": f"placeholder_{sermon_idx:03d}",
            "thumbnail_url": "",
            "duration": f"{random.randint(35, 55)}:00",
            "instructor": random.choice(["Pastor David Martinez", "Pastor Sarah Johnson", "Pastor Miguel Torres"]),
            "category_id": random.choice(cat_docs)["id"],
            "series_name": current_series[0],
            "is_featured": sermon_idx < 4,
            "is_published": True,
            "view_count": random.randint(50, 2000),
            "published_at": current.isoformat(),
            "created_at": datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc),
        })
        
        sermon_idx += 1
        weeks_in_series += 1
        current += timedelta(days=7)
    
    await db.media_videos.insert_many(sermon_docs)
    log.info(f"Generated {len(sermon_docs)} sermons")
    
    log.info("Generating volunteer opportunities and signups...")
    vol_opps = [
        "Sunday Greeter", "Parking Team", "Kids Ministry", "Youth Leader",
        "Worship Team", "Sound & Media", "Cafe Team", "Hospitality",
        "Security Team", "Prayer Team", "Outreach", "Altar Ministry",
    ]
    vol_opp_docs = []
    for opp_name in vol_opps:
        vol_opp_docs.append({
            "id": uid(), "tenant_id": TENANT_ID, "title": opp_name,
            "description": f"Serve on the {opp_name} team",
            "category": "Serve Teams", "is_active": True,
            "campus_id": random.choice([c["id"] for c in CAMPUSES]),
            "created_at": datetime(2023, 2, 1, tzinfo=timezone.utc),
        })
    await db.volunteer_opportunities.insert_many(vol_opp_docs)
    
    vol_signup_docs = []
    for _ in range(800):
        person = random.choice(adults)
        opp = random.choice(vol_opp_docs)
        vol_signup_docs.append({
            "id": uid(), "tenant_id": TENANT_ID,
            "user_id": person["id"], "opportunity_id": opp["id"],
            "person_name": f"{person['first_name']} {person['last_name']}",
            "status": "active",
            "created_at": datetime.combine(rand_date_between(START_DATE, END_DATE), datetime.min.time()).replace(tzinfo=timezone.utc),
        })
    await db.volunteer_signups.insert_many(vol_signup_docs)
    log.info(f"Generated {len(vol_signup_docs)} volunteer signups")
    
    log.info("Generating communications...")
    comm_docs = []
    subjects = [
        "This Week at Abundant", "Sunday Recap: What You Missed", "Upcoming Events This Month",
        "Volunteer Opportunities", "Year-End Giving Reminder", "VBS Registration Open!",
        "Easter Service Times", "Christmas Eve Schedule", "New Series Starting Sunday",
        "Annual Report: What God Did This Year", "Baptism Sunday Sign-Up",
    ]
    for _ in range(100):
        d = rand_date_between(START_DATE, END_DATE)
        comm_docs.append({
            "id": uid(), "tenant_id": TENANT_ID,
            "subject": random.choice(subjects), "body_html": "<p>Dear Church Family,</p><p>We're excited to share...</p>",
            "comm_type": "email", "status": "sent",
            "sent_at": d.isoformat(), "sent_by": "admin@abundant.org",
            "recipient_count": random.randint(5000, 20000),
            "created_at": datetime.combine(d, datetime.min.time()).replace(tzinfo=timezone.utc),
        })
    await db.communications.insert_many(comm_docs)
    
    # ── STEP 13: Generate platform_donors for God Mode ──
    log.info("Generating platform_donors...")
    pd_docs = []
    for pid, total in person_giving_total.items():
        if total <= 0:
            continue
        person = next((p for p in all_people if p["id"] == pid), None)
        if not person:
            continue
        count = person_donation_count.get(pid, 0)
        
        # Determine stage
        if count >= 20:
            stage = "champion"
        elif count >= 10:
            stage = "consistent"
        elif count >= 4:
            stage = "growing"
        elif count >= 1:
            stage = "new"
        else:
            stage = "lapsed"
        
        pd_docs.append({
            "id": uid(), "tenant_id": TENANT_ID,
            "person_id": pid,
            "name": f"{person['first_name']} {person['last_name']}",
            "email": person.get("email", ""),
            "campus": person.get("campus", ""),
            "total_given": round(total, 2),
            "donation_count": count,
            "avg_gift": round(total / count, 2) if count > 0 else 0,
            "first_gift_date": START_DATE.isoformat(),
            "last_gift_date": END_DATE.isoformat(),
            "giving_frequency": "recurring" if pid in recurring_map else "occasional",
            "stage": stage,
        })
    
    for i in range(0, len(pd_docs), 5000):
        await db.platform_donors.insert_many(pd_docs[i:i+5000])
    log.info(f"Generated {len(pd_docs)} platform donor records")
    
    # ── STEP 14: Recreate indexes ──
    log.info("Recreating indexes...")
    index_pairs = [
        ("donations", [("tenant_id", 1), ("donation_date", -1)]),
        ("donations", [("tenant_id", 1), ("person_id", 1), ("donation_date", -1)]),
        ("donations", [("tenant_id", 1), ("fund_id", 1), ("donation_date", -1)]),
        ("donations", [("tenant_id", 1), ("status", 1)]),
        ("attendance", [("tenant_id", 1), ("check_in_time", -1)]),
        ("attendance", [("tenant_id", 1), ("service_id", 1)]),
        ("attendance", [("tenant_id", 1), ("person_id", 1), ("check_in_time", -1)]),
        ("people", [("tenant_id", 1), ("last_name", 1), ("first_name", 1)]),
        ("people", [("tenant_id", 1), ("email", 1)]),
        ("people", [("tenant_id", 1), ("campus", 1)]),
        ("people", [("tenant_id", 1), ("engagement_score", -1)]),
        ("group_members", [("tenant_id", 1), ("group_id", 1), ("is_active", 1)]),
        ("group_members", [("tenant_id", 1), ("person_id", 1)]),
        ("services", [("tenant_id", 1), ("date", -1)]),
        ("recurring_giving", [("tenant_id", 1), ("is_active", 1), ("next_gift_date", 1)]),
        ("payouts", [("tenant_id", 1), ("created_at", -1)]),
        ("funds", [("tenant_id", 1), ("is_active", 1)]),
        ("users", [("email", 1)]),
        ("user_sessions", [("session_token", 1)]),
        ("platform_donors", [("tenant_id", 1), ("total_given", -1)]),
        ("events", [("tenant_id", 1), ("start_datetime", -1)]),
        ("checkins", [("tenant_id", 1), ("status", 1)]),
        ("children", [("tenant_id", 1), ("parent_user_id", 1)]),
    ]
    for coll, keys in index_pairs:
        await db[coll].create_index(keys, background=True)
    # TTL index
    await db.user_sessions.create_index([("expires_at", 1)], expireAfterSeconds=0)
    log.info("Indexes recreated")
    
    # ── FINAL VALIDATION ──
    log.info("=" * 60)
    log.info("SEED COMPLETE — VALIDATION")
    log.info("=" * 60)
    
    colls_to_check = ["tenants", "users", "people", "households", "funds", "donations",
                       "recurring_giving", "attendance", "services", "service_types",
                       "groups", "group_members", "group_types", "events", "event_registrations",
                       "children", "checkins", "payouts", "platform_donors",
                       "cafe_items", "cafe_orders", "merch_products", "merch_orders",
                       "prayer_requests", "media_videos", "media_categories",
                       "volunteer_opportunities", "volunteer_signups", "communications",
                       "tenant_branding"]
    
    for c in colls_to_check:
        count = await db[c].estimated_document_count()
        log.info(f"  {c}: {count:,}")
    
    # Giving totals
    total_giving = sum(person_giving_total.values())
    log.info(f"\n  Total Giving: ${total_giving:,.2f}")
    log.info(f"  Unique Donors: {len(person_giving_total):,}")
    log.info(f"  Total Donations: {donation_count:,}")
    log.info(f"  Recurring Schedules: {len(recurring_docs):,}")
    
    # Pareto check
    sorted_donors = sorted(person_giving_total.values(), reverse=True)
    top_20_pct = int(len(sorted_donors) * 0.20)
    top_20_total = sum(sorted_donors[:top_20_pct])
    pareto_ratio = top_20_total / total_giving * 100
    log.info(f"  Pareto Check: Top 20% of donors = {pareto_ratio:.1f}% of giving {'PASS' if pareto_ratio > 70 else 'NEEDS REVIEW'}")
    
    # Fund distribution check
    fund_totals = {}
    sample_donations = await db.donations.aggregate([
        {"$group": {"_id": "$fund_name", "total": {"$sum": "$amount"}}}
    ]).to_list(10)
    for fd in sample_donations:
        if fd["_id"]:
            fund_totals[fd["_id"]] = fd["total"]
    total_fund = sum(fund_totals.values())
    log.info("\n  Fund Distribution:")
    for fn, ft in sorted(fund_totals.items(), key=lambda x: -x[1]):
        pct = ft / total_fund * 100
        log.info(f"    {fn}: ${ft:,.0f} ({pct:.1f}%)")
    
    log.info("\nSEED COMPLETE!")
    client.close()


if __name__ == "__main__":
    if os.environ.get("ENVIRONMENT", "").lower() == "production":
        # BLOCKER #6 from production audit — never plant 28.5M synthetic
        # giving rows in a production database. Require explicit override.
        if os.environ.get("I_KNOW_WHAT_IM_DOING") != "yes":
            raise SystemExit(
                "Refusing to run seed_master.py against ENVIRONMENT=production. "
                "This script seeds 28.5M synthetic donations and demo accounts. "
                "Set I_KNOW_WHAT_IM_DOING=yes only if you have a written reason."
            )
    asyncio.run(seed())
