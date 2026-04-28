"""
Solomon AI — Platform Demo Data Seeder
Generates realistic 3.25-year giving history for 3 Abundant Church campuses.
Total: ~$41.2M, ~550K transactions, ~15K donors, ~510 payouts.
Fee: Card 1.9% + $0.30, ACH 0.8% + $0.30
"""
import asyncio
import os
import random
import uuid
from datetime import datetime, timezone, timedelta
import motor.motor_asyncio

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "solomonai")

# ── Fee Config ──
CARD_RATE = 0.019
CARD_FLAT = 0.30
ACH_RATE = 0.008
ACH_FLAT = 0.30

# ── Campuses ──
CAMPUSES = {
    "abundant-east-001": {
        "name": "Abundant East",
        "annual_base": 6_000_000,
        "growth_rate": 0.05,
        "donor_count": 8500,
        "bank_label": "BoA ****6789",
    },
    "abundant-west-001": {
        "name": "Abundant West",
        "annual_base": 4_000_000,
        "growth_rate": 0.05,
        "donor_count": 4200,
        "bank_label": "Chase ****4321",
    },
    "abundant-downtown-001": {
        "name": "Abundant Downtown",
        "annual_base": 2_000_000,
        "growth_rate": 0.05,
        "donor_count": 2534,
        "bank_label": "Wells ****8765",
    },
}

# ── Seasonality (Jan-Dec) ──
SEASONALITY = [0.90, 0.85, 0.95, 1.08, 0.95, 0.88, 0.85, 0.87, 0.92, 0.98, 1.05, 1.55]

# ── Funds ──
FUNDS = [
    ("General Fund",  "general_fund",  0.70),
    ("Building Fund", "building_fund", 0.15),
    ("Missions",      "missions",      0.10),
    ("Benevolence",   "benevolence",   0.05),
]
FUND_NAMES = [f[0] for f in FUNDS]
FUND_IDS   = [f[1] for f in FUNDS]
FUND_WEIGHTS = [f[2] for f in FUNDS]

# ── Payment Methods (65% card, 25% debit, 10% ACH) ──
PAYMENT_METHODS = ["credit_card"] * 65 + ["debit_card"] * 25 + ["ach"] * 10

# ── Donor Names ──
FIRST = [
    "James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda","David","Elizabeth",
    "William","Barbara","Richard","Susan","Joseph","Jessica","Thomas","Sarah","Christopher","Karen",
    "Charles","Lisa","Daniel","Nancy","Matthew","Betty","Anthony","Dorothy","Mark","Sandra",
    "Steven","Emily","Andrew","Donna","Paul","Michelle","Joshua","Carol","Kenneth","Amanda",
    "Kevin","Melissa","Brian","Deborah","George","Stephanie","Timothy","Rebecca","Ronald","Sharon",
    "Edward","Laura","Jason","Cynthia","Jeffrey","Kathleen","Ryan","Amy","Jacob","Angela",
    "Gary","Shirley","Nicholas","Brenda","Eric","Emma","Jonathan","Anna","Stephen","Pamela",
    "Larry","Nicole","Justin","Samantha","Scott","Katherine","Brandon","Christine","Benjamin","Debra",
    "Samuel","Rachel","Raymond","Carolyn","Gregory","Janet","Frank","Catherine","Alexander","Maria",
    "Patrick","Heather","Jack","Diane","Dennis","Ruth","Jerry","Evelyn","Tyler","Abigail",
    "Aaron","Teresa","Jose","Frances","Adam","Jacqueline","Nathan","Hannah","Henry","Gloria",
    "Peter","Virginia","Zachary","Kathryn","Douglas","Ann","Roger","Jean","Juan","Alice",
    "Carlos","Judy","Albert","Sophia","Russell","Grace","Randy","Denise","Eugene","Amber",
]
LAST = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
    "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
    "Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson",
    "Walker","Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
    "Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter","Roberts",
    "Gomez","Phillips","Evans","Turner","Diaz","Parker","Cruz","Edwards","Collins","Reyes",
    "Stewart","Morris","Morales","Murphy","Cook","Rogers","Gutierrez","Ortiz","Morgan","Cooper",
    "Peterson","Bailey","Reed","Kelly","Howard","Ramos","Kim","Cox","Ward","Richardson",
    "Watson","Brooks","Chavez","Wood","James","Bennett","Gray","Mendoza","Ruiz","Hughes",
    "Price","Alvarez","Castillo","Sanders","Patel","Myers","Long","Ross","Foster","Jimenez",
]

CARD_BRANDS = ["Visa ****4242","Visa ****1234","Mastercard ****5555","Mastercard ****9876","Amex ****3782","Discover ****6011"]

# ── Recurring amounts (lower average to hit ~$75 overall) ──
RECURRING_AMTS = [25,25,25,50,50,50,50,75,75,100,100,100,150,150,200,250]
RECURRING_FREQS = ["weekly","weekly","biweekly","monthly","monthly","monthly"]


def calc_fee(amount, method):
    if method == "ach":
        return round(amount * ACH_RATE + ACH_FLAT, 2)
    return round(amount * CARD_RATE + CARD_FLAT, 2)


def gen_amount(is_recurring):
    if is_recurring:
        return random.choice(RECURRING_AMTS)
    base = random.gauss(55, 35)
    base = max(10, min(base, 500))
    return round(base / 5) * 5 if base > 50 else round(base)


def pick_day_in_month(year, month):
    """Pick a day weighted toward Sundays."""
    import calendar
    _, max_day = calendar.monthrange(year, month)
    if random.random() < 0.60:
        # Pick a Sunday
        d = datetime(year, month, 1)
        sundays = []
        while d.month == month:
            if d.weekday() == 6:
                sundays.append(d.day)
            d += timedelta(days=1)
        return random.choice(sundays) if sundays else random.randint(1, max_day)
    # End-of-month bump (recurring processing)
    if random.random() < 0.15:
        return random.randint(max(max_day - 3, 1), max_day)
    return random.randint(1, max_day)


def gen_donors(tenant_id, count):
    donors = []
    used = set()
    for i in range(count):
        while True:
            f = random.choice(FIRST)
            last = random.choice(LAST)
            key = f"{f}_{last}_{i}"
            if key not in used:
                used.add(key)
                break
        donors.append({
            "id": f"donor_{tenant_id}_{i:05d}",
            "tenant_id": tenant_id,
            "name": f"{f} {last}",
            "first_name": f,
            "last_name": last,
            "email": f"{f.lower()}.{last.lower()}{i}@email.com",
            "card_label": random.choice(CARD_BRANDS),
        })
    return donors


def get_annual_target(campus, year):
    base = campus["annual_base"]
    years_from_start = year - 2023
    return base * ((1 + campus["growth_rate"]) ** years_from_start)


def get_mondays(start_date, end_date):
    """Return all Mondays between two dates."""
    mondays = []
    d = start_date
    while d <= end_date:
        if d.weekday() == 0:
            mondays.append(d)
        d += timedelta(days=1)
    return mondays


async def seed_campus(db, tenant_id, campus):
    print(f"\n  === {campus['name']} ({tenant_id}) ===")
    donors = gen_donors(tenant_id, campus["donor_count"])

    # Insert donor records
    print(f"  Inserting {len(donors)} donors...")
    for i in range(0, len(donors), 5000):
        batch = donors[i:i+5000]
        await db.platform_donors.insert_many(batch)

    all_donations = []
    yearly_stats = {}

    # Date range: Jan 2023 -> Apr 2, 2026
    years_months = []
    for y in [2023, 2024, 2025]:
        for m in range(1, 13):
            years_months.append((y, m))
    for m in range(1, 4):  # Jan-Mar 2026
        years_months.append((2026, m))
    # Partial April 2026 (2 days)
    years_months.append((2026, 4))

    for (year, month) in years_months:
        annual_target = get_annual_target(campus, year)
        month_base = annual_target / 12
        season = SEASONALITY[month - 1]

        # Easter spike (April)
        if month == 4:
            season *= 1.15
        # Christmas Eve spike already in December seasonality

        month_target = month_base * season

        # For 2026 April partial (2 days out of 30)
        if year == 2026 and month == 4:
            month_target *= (2 / 30)

        month_total = 0.0
        month_txns = []
        import calendar
        _, max_day = calendar.monthrange(year, month)
        actual_max_day = min(max_day, 2) if (year == 2026 and month == 4) else max_day

        while month_total < month_target * 0.97:
            donor = random.choice(donors)
            is_recurring = random.random() < 0.40
            amount = gen_amount(is_recurring)
            if month_total + amount > month_target * 1.04:
                break

            day = pick_day_in_month(year, month)
            day = min(day, actual_max_day)
            method = random.choice(PAYMENT_METHODS)
            fee = calc_fee(amount, method)
            fund_idx = random.choices(range(len(FUNDS)), weights=FUND_WEIGHTS, k=1)[0]

            dt = datetime(year, month, day, random.randint(6, 21), random.randint(0, 59), random.randint(0, 59), tzinfo=timezone.utc)

            txn = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "person_id": donor["id"],
                "person_name": donor["name"],
                "person_email": donor["email"],
                "amount": round(amount, 2),
                "processing_fee": fee,
                "solomon_fee": fee,
                "net_amount": round(amount - fee, 2),
                "fund_name": FUND_NAMES[fund_idx],
                "fund_id": FUND_IDS[fund_idx],
                "fund": FUND_NAMES[fund_idx],
                "frequency": "recurring" if is_recurring else "one_time",
                "donation_date": dt.strftime("%Y-%m-%d"),
                "payment_method": method,
                "card_label": donor["card_label"] if method != "ach" else f"ACH ****{random.randint(1000,9999)}",
                "transaction_id": f"sol_{uuid.uuid4().hex[:12]}",
                "source": "solomonpay",
                "status": "completed",
                "created_at": dt.isoformat(),
            }
            month_txns.append(txn)
            month_total += amount

        all_donations.extend(month_txns)
        key = str(year)
        yearly_stats[key] = yearly_stats.get(key, {"total": 0, "count": 0})
        yearly_stats[key]["total"] += month_total
        yearly_stats[key]["count"] += len(month_txns)

        if month in (3, 6, 9, 12):
            print(f"    {year}-{month:02d}: {len(month_txns):,} txns, ${month_total:,.0f}")

    # Batch insert donations
    print(f"  Inserting {len(all_donations):,} donations...")
    BATCH = 10000
    for i in range(0, len(all_donations), BATCH):
        batch = all_donations[i:i+BATCH]
        await db.donations.insert_many(batch)
        pct = min(100, int((i + len(batch)) / len(all_donations) * 100))
        print(f"    {pct}% ({i+len(batch):,}/{len(all_donations):,})")

    # Generate weekly payouts
    print("  Generating payouts...")
    payout_start = datetime(2023, 1, 2, tzinfo=timezone.utc)
    payout_end = datetime(2026, 3, 31, tzinfo=timezone.utc)
    mondays = get_mondays(payout_start, payout_end)
    payouts = []

    for monday in mondays:
        week_start = (monday - timedelta(days=7)).strftime("%Y-%m-%d")
        week_end = (monday - timedelta(days=1)).strftime("%Y-%m-%d")
        # Find donations in this week window
        week_donations = [d for d in all_donations if week_start <= d["donation_date"] <= week_end]
        gross = sum(d["amount"] for d in week_donations)
        fees = sum(d["solomon_fee"] for d in week_donations)
        net = round(gross - fees, 2)
        txn_count = len(week_donations)

        if gross == 0:
            continue

        payouts.append({
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "church_name": campus["name"],
            "payout_date": monday.strftime("%Y-%m-%d"),
            "period_start": week_start,
            "period_end": week_end,
            "gross_amount": round(gross, 2),
            "total_fees": round(fees, 2),
            "net_payout": net,
            "transaction_count": txn_count,
            "bank_account": campus["bank_label"],
            "payout_method": "ACH - Standard",
            "status": "completed",
            "created_at": monday.isoformat(),
        })

    if payouts:
        await db.payouts.insert_many(payouts)
    print(f"  {len(payouts)} payouts created")

    grand_total = sum(v["total"] for v in yearly_stats.values())
    grand_count = sum(v["count"] for v in yearly_stats.values())
    for y in sorted(yearly_stats):
        print(f"    {y}: ${yearly_stats[y]['total']:,.0f} ({yearly_stats[y]['count']:,} txns)")
    print(f"    TOTAL: ${grand_total:,.0f} ({grand_count:,} txns)")
    return grand_count, grand_total, len(payouts), len(donors)


async def main():
    print("=" * 60)
    print("Solomon AI — Platform Demo Seeder")
    print(f"Card fee: {CARD_RATE*100}% + ${CARD_FLAT}")
    print(f"ACH fee:  {ACH_RATE*100}% + ${ACH_FLAT}")
    print("=" * 60)

    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Clean existing data for these 3 campuses
    print("\n[1/3] Cleaning existing data...")
    for tid in CAMPUSES:
        r = await db.donations.delete_many({"tenant_id": tid})
        print(f"  Deleted {r.deleted_count:,} donations from {tid}")
        r = await db.payouts.delete_many({"tenant_id": tid})
        print(f"  Deleted {r.deleted_count:,} payouts from {tid}")
        r = await db.platform_donors.delete_many({"tenant_id": tid})
        print(f"  Deleted {r.deleted_count:,} donors from {tid}")

    # Ensure tenant records
    print("\n[2/3] Ensuring tenants...")
    for tid, cfg in CAMPUSES.items():
        await db.tenants.update_one(
            {"id": tid},
            {"$set": {"id": tid, "name": cfg["name"], "church_name": cfg["name"], "status": "active", "subscription_status": "active"}},
            upsert=True
        )
        print(f"  {cfg['name']} OK")

    # Seed each campus
    print("\n[3/3] Seeding data...")
    totals = {"txns": 0, "amount": 0, "payouts": 0, "donors": 0}
    for tid, cfg in CAMPUSES.items():
        txns, amt, pays, dnrs = await seed_campus(db, tid, cfg)
        totals["txns"] += txns
        totals["amount"] += amt
        totals["payouts"] += pays
        totals["donors"] += dnrs

    # Create indexes
    print("\n  Creating indexes...")
    await db.donations.create_index([("tenant_id", 1), ("donation_date", -1)])
    await db.donations.create_index([("person_id", 1)])
    await db.donations.create_index([("donation_date", -1)])
    await db.donations.create_index([("status", 1)])
    await db.payouts.create_index([("tenant_id", 1), ("payout_date", -1)])
    await db.platform_donors.create_index([("tenant_id", 1)])
    await db.platform_donors.create_index([("email", 1)])

    # Summary
    print("\n" + "=" * 60)
    print("SEED COMPLETE!")
    print(f"  Total Transactions: {totals['txns']:,}")
    print(f"  Total Giving:       ${totals['amount']:,.0f}")
    print(f"  Total Payouts:      {totals['payouts']:,}")
    print(f"  Total Donors:       {totals['donors']:,}")

    # Fee summary
    fee_pipe = [
        {"$match": {"tenant_id": {"$in": list(CAMPUSES.keys())}}},
        {"$group": {"_id": "$tenant_id", "vol": {"$sum": "$amount"}, "fees": {"$sum": "$solomon_fee"}, "cnt": {"$sum": 1}}}
    ]
    async for r in db.donations.aggregate(fee_pipe):
        print(f"  {r['_id']}: ${r['vol']:,.0f} vol, ${r['fees']:,.0f} fees, {r['cnt']:,} txns")

    total_fees = await db.donations.aggregate([
        {"$match": {"tenant_id": {"$in": list(CAMPUSES.keys())}}},
        {"$group": {"_id": None, "fees": {"$sum": "$solomon_fee"}, "vol": {"$sum": "$amount"}}}
    ]).to_list(1)
    if total_fees:
        print(f"\n  PLATFORM TOTAL: ${total_fees[0]['vol']:,.0f} volume, ${total_fees[0]['fees']:,.0f} fees earned")

    print("=" * 60)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
