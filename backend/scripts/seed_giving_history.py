"""
Solomon AI — 3-Year Giving History Seed Script
Seeds realistic donation data for all churches on the platform.
Processing fee: 2.2% + $0.22 per transaction (25% cheaper than industry 2.9% + $0.30)
"""
import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

# Solomon Pay processing fee (25% cheaper than industry 2.9% + $0.30)
PROCESSING_RATE = 0.022  # 2.2%
PROCESSING_FLAT = 0.22   # $0.22

FUNDS = ["General Fund", "Missions", "Building Fund", "Youth Ministry", "Benevolence", "Worship & Arts", "Community Outreach"]

# Church giving targets (annual)
CHURCHES = {
    "abundant-east-001": {
        "name": "Abundant East",
        "annual_target": 5_000_000,
        "avg_donation": 185,
        "donor_pool": 800,
        "fund_weights": [0.45, 0.15, 0.12, 0.10, 0.08, 0.05, 0.05],
    },
    "abundant-downtown-001": {
        "name": "Abundant Downtown",
        "annual_target": 4_000_000,
        "avg_donation": 210,
        "donor_pool": 600,
        "fund_weights": [0.50, 0.12, 0.15, 0.08, 0.07, 0.04, 0.04],
    },
    "abundant-west-001": {
        "name": "Abundant West",
        "annual_target": 3_000_000,
        "avg_donation": 165,
        "donor_pool": 500,
        "fund_weights": [0.48, 0.14, 0.10, 0.12, 0.08, 0.04, 0.04],
    },
    "pottershouse-church-001": {
        "name": "The Potter's House",
        "annual_target": 8_000_000,
        "avg_donation": 145,
        "donor_pool": 2000,
        "fund_weights": [0.40, 0.18, 0.15, 0.10, 0.07, 0.05, 0.05],
    },
    "cristoviene-church-001": {
        "name": "Cristo Viene",
        "annual_target": 2_000_000,
        "avg_donation": 120,
        "donor_pool": 400,
        "fund_weights": [0.50, 0.20, 0.08, 0.10, 0.06, 0.03, 0.03],
    },
    "eden-x-001": {
        "name": "Eden X Church",
        "annual_target": 1_500_000,
        "avg_donation": 155,
        "donor_pool": 300,
        "fund_weights": [0.52, 0.15, 0.10, 0.08, 0.07, 0.04, 0.04],
    },
    "cityreach-church-001": {
        "name": "CityReach Church",
        "annual_target": 3_000_000,
        "avg_donation": 175,
        "donor_pool": 550,
        "fund_weights": [0.45, 0.16, 0.12, 0.10, 0.08, 0.05, 0.04],
    },
    "grace-community-church-001": {
        "name": "Grace Community Church",
        "annual_target": 1_500_000,
        "avg_donation": 130,
        "donor_pool": 350,
        "fund_weights": [0.55, 0.12, 0.10, 0.08, 0.07, 0.04, 0.04],
    },
}

# Monthly seasonality multipliers (Jan=0, Dec=11)
SEASONALITY = [0.85, 0.80, 0.90, 1.05, 0.95, 0.90, 0.85, 0.88, 0.95, 1.00, 1.05, 1.50]

PAYMENT_METHODS = ["solomonpay", "solomonpay", "solomonpay", "cash", "check"]
DONOR_FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Dorothy", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Emily", "Andrew", "Donna", "Paul", "Michelle", "Joshua", "Carol",
    "Kenneth", "Amanda", "Kevin", "Melissa", "Brian", "Deborah", "George", "Stephanie",
    "Timothy", "Rebecca", "Ronald", "Sharon", "Edward", "Laura", "Jason", "Cynthia",
    "Jeffrey", "Kathleen", "Ryan", "Amy", "Jacob", "Angela", "Gary", "Shirley",
    "Nicholas", "Brenda", "Eric", "Emma", "Jonathan", "Anna", "Stephen", "Pamela",
    "Larry", "Nicole", "Justin", "Samantha", "Scott", "Katherine", "Brandon", "Christine",
    "Benjamin", "Debra", "Samuel", "Rachel", "Raymond", "Carolyn", "Gregory", "Janet",
    "Frank", "Catherine", "Alexander", "Maria", "Patrick", "Heather", "Jack", "Diane",
]
DONOR_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson", "Watson",
]


def generate_donor_pool(tenant_id, count):
    """Pre-generate a fixed pool of donors for a church."""
    donors = []
    for i in range(count):
        first = random.choice(DONOR_FIRST_NAMES)
        last = random.choice(DONOR_LAST_NAMES)
        donors.append({
            "person_id": f"donor_{tenant_id}_{i:04d}",
            "person_name": f"{first} {last}",
            "person_email": f"{first.lower()}.{last.lower()}{i}@email.com",
        })
    return donors


def pick_fund(fund_weights):
    """Weighted random fund selection."""
    return random.choices(FUNDS[:len(fund_weights)], weights=fund_weights, k=1)[0]


def generate_amount(avg, is_recurring=False):
    """Generate a realistic donation amount."""
    if is_recurring:
        # Recurring tends to be round numbers
        options = [25, 50, 75, 100, 150, 200, 250, 300, 500, 750, 1000]
        weights = [15, 25, 10, 20, 8, 8, 5, 3, 3, 2, 1]
        return random.choices(options, weights=weights, k=1)[0]
    else:
        # One-time varies more
        base = random.gauss(avg, avg * 0.6)
        base = max(10, min(base, avg * 10))
        # Round to nearest $5 for amounts over $50, or $1 otherwise
        if base > 50:
            return round(base / 5) * 5
        return round(base)


async def seed_church_giving(db, tenant_id, config):
    """Seed 3 years of giving data for a single church."""
    print(f"\n  Seeding {config['name']} ({tenant_id})...")
    donors = generate_donor_pool(tenant_id, config["donor_pool"])
    annual_target = config["annual_target"]
    avg_donation = config["avg_donation"]
    fund_weights = config["fund_weights"]

    all_donations = []
    yearly_totals = {2023: 0, 2024: 0, 2025: 0}

    for year in [2023, 2024, 2025]:
        # Slight year-over-year growth (5-10%)
        growth = 1.0 + (year - 2023) * random.uniform(0.04, 0.08)
        year_target = annual_target * growth

        for month in range(1, 13):
            # Skip future months in 2025 (we're in early 2026, so all of 2025 is valid)
            month_target = (year_target / 12) * SEASONALITY[month - 1]
            month_total = 0
            month_donations = []

            # Generate donations for this month
            while month_total < month_target * 0.95:
                donor = random.choice(donors)
                is_recurring = random.random() < 0.35  # 35% recurring
                amount = generate_amount(avg_donation, is_recurring)

                if month_total + amount > month_target * 1.08:
                    break

                # Pick a random day in the month (weighted toward Sundays)
                day = random.randint(1, 28)
                # Bias toward Sundays (days 1,8,15,22 roughly)
                if random.random() < 0.65:
                    day = random.choice([1, 7, 8, 14, 15, 21, 22, 28])

                donation_date = datetime(year, month, min(day, 28), 
                                        random.randint(7, 20), 
                                        random.randint(0, 59), 
                                        tzinfo=timezone.utc)

                fund = pick_fund(fund_weights)
                payment = random.choice(PAYMENT_METHODS)
                processing_fee = round(amount * PROCESSING_RATE + PROCESSING_FLAT, 2) if payment == "solomonpay" else 0

                donation = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "person_id": donor["person_id"],
                    "person_name": donor["person_name"],
                    "person_email": donor["person_email"],
                    "amount": round(amount, 2),
                    "base_amount": round(amount, 2),
                    "processing_fee": processing_fee,
                    "solomon_fee": processing_fee,
                    "fees_covered_by_donor": random.random() < 0.3,
                    "fund": fund,
                    "fund_name": fund,
                    "fund_id": fund.lower().replace(" ", "_").replace("&", "and"),
                    "frequency": "recurring" if is_recurring else "one_time",
                    "donation_date": donation_date.strftime("%Y-%m-%d"),
                    "payment_method": payment,
                    "transaction_id": f"sol_txn_{uuid.uuid4().hex[:12]}",
                    "source": "solomonpay",
                    "status": "completed",
                    "created_at": donation_date.isoformat(),
                }

                month_donations.append(donation)
                month_total += amount

            yearly_totals[year] += month_total
            all_donations.extend(month_donations)

            if month % 4 == 0:
                print(f"    {year}-{month:02d}: {len(month_donations)} txns, ${month_total:,.0f}")

    # Batch insert
    if all_donations:
        BATCH_SIZE = 5000
        for i in range(0, len(all_donations), BATCH_SIZE):
            batch = all_donations[i:i + BATCH_SIZE]
            await db.donations.insert_many(batch)
            print(f"    Inserted batch {i // BATCH_SIZE + 1} ({len(batch)} records)")

    total = sum(yearly_totals.values())
    print(f"  {config['name']}: {len(all_donations)} donations seeded")
    print(f"    2023: ${yearly_totals[2023]:,.0f}")
    print(f"    2024: ${yearly_totals[2024]:,.0f}")
    print(f"    2025: ${yearly_totals[2025]:,.0f}")
    print(f"    Total: ${total:,.0f}")
    return len(all_donations), total


async def ensure_tenants(db):
    """Ensure all churches have tenant records."""
    missing_tenants = {
        "eden-x-001": {
            "id": "eden-x-001",
            "name": "Eden X Church",
            "church_name": "Eden X Church",
            "slug": "eden-x",
            "status": "active",
            "plan": "pro",
            "contact_email": "admin@edenx.church",
            "phone": "(555) 444-3333",
            "address": "789 Innovation Blvd, Austin, TX 78701",
            "city": "Austin",
            "state": "TX",
            "timezone": "America/Chicago",
            "created_at": "2023-01-15T00:00:00+00:00",
        },
        "cityreach-church-001": {
            "id": "cityreach-church-001",
            "name": "CityReach Church",
            "church_name": "CityReach Church",
            "slug": "cityreach",
            "status": "active",
            "plan": "pro",
            "contact_email": "admin@cityreach.church",
            "phone": "(555) 555-4444",
            "address": "456 Urban Way, Miami, FL 33101",
            "city": "Miami",
            "state": "FL",
            "timezone": "America/New_York",
            "created_at": "2023-03-01T00:00:00+00:00",
        },
    }
    for tid, data in missing_tenants.items():
        existing = await db.tenants.find_one({"id": tid})
        if not existing:
            await db.tenants.insert_one(data)
            print(f"  Created tenant: {data['name']}")
        else:
            print(f"  Tenant exists: {tid}")


async def cleanup_junk_data(db):
    """Remove test/junk donation data."""
    # Remove the 2.8M junk records from abundant-church-001
    result = await db.donations.delete_many({"tenant_id": "abundant-church-001"})
    print(f"  Cleaned abundant-church-001: {result.deleted_count} junk records removed")

    # Remove old donations for churches we're re-seeding
    for tid in CHURCHES:
        result = await db.donations.delete_many({"tenant_id": tid})
        print(f"  Cleaned {tid}: {result.deleted_count} old records removed")

    # Clean orphaned donations
    result = await db.donations.delete_many({"tenant_id": None})
    print(f"  Cleaned null tenant donations: {result.deleted_count}")


async def main():
    print("=" * 60)
    print("Solomon AI — 3-Year Giving History Seed")
    print("Processing fee: 2.2% + $0.22 (25% below industry)")
    print("=" * 60)

    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print("\n[1/4] Ensuring tenant records...")
    await ensure_tenants(db)

    print("\n[2/4] Cleaning up junk data...")
    await cleanup_junk_data(db)

    print("\n[3/4] Seeding 3-year giving data...")
    grand_total_records = 0
    grand_total_amount = 0
    for tenant_id, config in CHURCHES.items():
        records, amount = await seed_church_giving(db, tenant_id, config)
        grand_total_records += records
        grand_total_amount += amount

    print(f"\n[4/4] Summary")
    print(f"  Total records: {grand_total_records:,}")
    print(f"  Total amount: ${grand_total_amount:,.0f}")

    # Calculate platform fees
    fee_pipeline = [
        {"$match": {"source": "solomonpay", "payment_method": "solomonpay"}},
        {"$group": {
            "_id": None,
            "total_volume": {"$sum": "$amount"},
            "total_fees": {"$sum": "$solomon_fee"},
            "txn_count": {"$sum": 1},
        }}
    ]
    fee_result = await db.donations.aggregate(fee_pipeline).to_list(1)
    if fee_result:
        r = fee_result[0]
        print(f"  SolomonPay volume: ${r['total_volume']:,.0f}")
        print(f"  Processing fees earned: ${r['total_fees']:,.0f}")
        print(f"  SolomonPay transactions: {r['txn_count']:,}")

    print("\n" + "=" * 60)
    print("SEED COMPLETE!")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
