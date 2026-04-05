"""
Seed Hill Country Bible Church + add subscription records for all 7 churches.
Calibrates existing churches to match the correct financial model:
  - 70% active donors per church
  - $220-$900/year per active donor  
  - 4-5% YoY growth (2023 < 2024 < 2025)
  - Tier distribution: Tithers 5%, Committed 15%, Engaged 25%, Regular 25%, Occasional 30%
"""
import asyncio, random, uuid, hashlib, os
from datetime import datetime, timezone, timedelta, date
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ.get('DB_NAME', 'solomonai')]

DEMO_PW = hashlib.sha256(b'Demo2026!').hexdigest()

# ── Giving tiers ────────────────────────────────────────────────────────────
TIERS = [
    {'name': 'Tither',    'pct': 0.05, 'min': 3000, 'max': 9000,  'freq_range': (26, 52)},  # weekly/biweekly
    {'name': 'Committed', 'pct': 0.15, 'min': 900,  'max': 3000,  'freq_range': (12, 24)},  # monthly+
    {'name': 'Engaged',   'pct': 0.25, 'min': 400,  'max': 900,   'freq_range': (8, 18)},
    {'name': 'Regular',   'pct': 0.25, 'min': 220,  'max': 400,   'freq_range': (4, 12)},
    {'name': 'Occasional','pct': 0.30, 'min': 220,  'max': 300,   'freq_range': (2, 8)},
]

GROWTH = {2023: 1.00, 2024: 1.04, 2025: 1.084}   # ~4% YoY, then ~4.2%

METHODS = ['card']*55 + ['check']*25 + ['cash']*10 + ['ach']*10
FUNDS = [('General Fund',0.72),('Building Fund',0.10),('Missions',0.08),
         ('Youth Ministry',0.05),('Benevolence',0.05)]

FIRST_M = ['James','John','Michael','William','David','Robert','Joseph','Charles','Thomas','Daniel',
           'Mark','Paul','Timothy','Joshua','Nathan','Carlos','Luis','Miguel','Juan','Antonio']
FIRST_F = ['Mary','Jennifer','Ashley','Jennifer','Patricia','Linda','Barbara','Susan','Jessica',
           'Sarah','Karen','Margaret','Sandra','Dorothy','Helen','Maria','Rosa','Sofia','Elena']
LAST = ['Johnson','Williams','Brown','Davis','Miller','Wilson','Moore','Taylor','Anderson',
        'Thomas','Jackson','White','Harris','Martin','Thompson','Robinson','Clark','Lewis',
        'Garcia','Rodriguez','Martinez','Hernandez','Lopez','Gonzalez','Perez','Torres']

# New church config
HILL_COUNTRY = {
    'id': 'hillcountry-001',
    'name': 'Hill Country Bible Church',
    'city': 'Cedar Park', 'state': 'TX',
    'address': '3115 Bagdad Rd, Cedar Park, TX 78613',
    'subdomain': 'hillcountry',
    'plan': 'growth',
    'members': 10000,
    'annual_giving_per_donor': 550,
    'active_pct': 0.70,
    'admin_email': 'admin@hillcountrybible.church',
    'admin_name': 'Pastor David Thompson',
}

START = date(2023, 4, 1)
END = date(2026, 3, 31)

def all_sundays():
    d = START
    while d.weekday() != 6: d += timedelta(days=1)
    s = []
    while d <= END: s.append(d); d += timedelta(days=7)
    return s

SUNDAYS = all_sundays()

def rand_person(tid, idx):
    g = random.choice(['M','F'])
    fn = random.choice(FIRST_M if g=='M' else FIRST_F)
    ln = random.choice(LAST)
    return {
        'id': f'p_{tid[:8]}_{idx:05d}',
        'tenant_id': tid,
        'first_name': fn, 'last_name': ln,
        'name': f'{fn} {ln}', 'gender': g,
        'email': f'{fn.lower()}.{ln.lower()}.{idx}@{tid[:6]}.church',
        'mobile_phone': f'({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}',
        'membership_status': random.choice(['member']*4 + ['regular', 'visitor']),
        'created_at': datetime.now(timezone.utc).isoformat(),
    }

def assign_tier(i, total_active):
    """Assign donor tier by index."""
    cumulative = 0
    for tier in TIERS:
        cumulative += tier['pct']
        if i < total_active * cumulative:
            return tier
    return TIERS[-1]

async def seed_church(cfg):
    tid = cfg['id']
    members = cfg['members']
    active_count = int(members * cfg['active_pct'])
    
    # Check if already seeded
    existing = await db.people.count_documents({'tenant_id': tid})
    if existing > 100:
        print(f'  {cfg["name"]}: already seeded ({existing} people) — skipping people')
    else:
        print(f'  Seeding {cfg["name"]} — {members} members...')
        people = [rand_person(tid, i) for i in range(members)]
        for i in range(0, len(people), 500):
            await db.people.insert_many(people[i:i+500])
        print(f'    {len(people)} people inserted')

    # Check donations
    don_count = await db.donations.count_documents({'tenant_id': tid})
    if don_count > 1000:
        print(f'  {cfg["name"]}: already has {don_count:,} donations — skipping donations')
    else:
        print(f'  Generating donations for {cfg["name"]}...')
        # Get people
        people_list = await db.people.find({'tenant_id': tid}, {'_id': 0, 'id': 1, 'name': 1}).to_list(members + 100)
        active_people = people_list[:active_count]
        
        # Funds
        fund_docs = await db.funds.find({'tenant_id': tid}, {'_id': 0}).to_list(10)
        if not fund_docs:
            fund_docs = []
            for fname, fpct in FUNDS:
                fid = f'fund_{tid[:6]}_{uuid.uuid4().hex[:8]}'
                fdoc = {'id': fid, 'tenant_id': tid, 'name': fname, 'is_active': True,
                        'goal_amount': int(cfg['annual_giving_per_donor'] * active_count * fpct),
                        'current_amount': 0, 'created_at': datetime.now(timezone.utc).isoformat()}
                fund_docs.append(fdoc)
            await db.funds.insert_many(fund_docs)

        donations = []
        for i, person in enumerate(active_people):
            tier = assign_tier(i, active_count)
            for year in [2023, 2024, 2025]:
                growth = GROWTH[year]
                annual_target = random.uniform(tier['min'], tier['max']) * growth
                events_per_year = random.randint(*tier['freq_range'])
                per_event = annual_target / events_per_year
                yr_sundays = [s for s in SUNDAYS if s.year == year]
                chosen = random.sample(yr_sundays, min(events_per_year, len(yr_sundays)))
                for d in chosen:
                    amt = round(per_event * random.uniform(0.8, 1.2), 2)
                    if amt < 5: continue
                    fund = random.choices(fund_docs, weights=[f[1] for f in FUNDS])[0]
                    method = random.choice(METHODS)
                    fee = round(amt * 0.019 + 0.30, 2) if method == 'card' else \
                          round(min(amt * 0.008 + 0.30, 5.0), 2) if method == 'ach' else 0
                    donations.append({
                        'id': str(uuid.uuid4()),
                        'tenant_id': tid,
                        'person_id': person['id'],
                        'donor_name': person['name'],
                        'fund_id': fund['id'],
                        'fund_name': fund['name'],
                        'amount': amt, 'fee_amount': fee, 'net_amount': round(amt - fee, 2),
                        'donation_date': d.isoformat(),
                        'payment_method': method, 'status': 'completed',
                        'source': 'solomonpay',
                        'created_at': datetime(year, d.month, d.day, 9, 0, tzinfo=timezone.utc),
                    })
        for i in range(0, len(donations), 1000):
            await db.donations.insert_many(donations[i:i+1000])
        print(f'    {len(donations):,} donations inserted — ${sum(d["amount"] for d in donations):,.0f}')

    # Subscription records (monthly, 36 months)
    plan = cfg.get('plan', 'growth')
    sub_amount = {'standard': 299, 'growth': 499, 'enterprise': 799}.get(plan, 499)
    existing_subs = await db.subscriptions.count_documents({'tenant_id': tid})
    if existing_subs < 10:
        subs = []
        for mo in range(36):
            dt = date(2023, 4, 1) + timedelta(days=30 * mo)
            subs.append({'id': str(uuid.uuid4()), 'tenant_id': tid, 'plan': plan,
                         'amount': sub_amount, 'status': 'paid',
                         'billing_date': dt.isoformat(),
                         'period_month': dt.strftime('%Y-%m'),
                         'created_at': datetime.now(timezone.utc).isoformat()})
        await db.subscriptions.insert_many(subs)
        print(f'    {len(subs)} subscription records inserted (${sub_amount}/mo)')

    # Stats cache
    people_list2 = await db.people.find({'tenant_id': tid}, {'_id': 0, 'id': 1}).to_list(members + 100)
    active_ids = [p['id'] for p in people_list2[:active_count]]
    ytd = await db.donations.aggregate([
        {'$match': {'tenant_id': tid, 'donation_date': {'$gte': '2025-01-01'}}},
        {'$group': {'_id': None, 'vol': {'$sum': '$amount'}}}
    ]).to_list(1)
    ytd_vol = ytd[0]['vol'] if ytd else 0
    await db.dashboard_stats_cache.update_one(
        {'tenant_id': tid},
        {'$set': {
            'tenant_id': tid,
            'total_members': members,
            'active_members': active_count,
            'ytd_giving': round(ytd_vol, 2),
            'mtd_giving': round(ytd_vol / 12, 2),
            'mtd_goal': round(cfg['annual_giving_per_donor'] * active_count / 12, 2),
            'active_groups': 14, 'last_attendance': int(active_count * 0.55),
            'recurring_givers': int(active_count * 0.40),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True
    )

    # Tenant record
    await db.tenants.update_one(
        {'id': tid},
        {'$set': {'id': tid, 'name': cfg['name'], 'subscription_status': 'active',
                  'plan': plan, 'city': cfg['city'], 'state': cfg['state'],
                  'address': cfg.get('address', ''), 'subdomain': cfg['subdomain'],
                  'primary_color': '#1a5276',
                  'created_at': datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )

    # Admin user
    await db.users.update_one(
        {'email': cfg['admin_email']},
        {'$set': {'user_id': f'admin_{tid[:8]}', 'email': cfg['admin_email'],
                  'name': cfg['admin_name'], 'role': 'church_admin',
                  'tenant_id': tid, 'password_hash': DEMO_PW,
                  'created_at': datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    print(f'  {cfg["name"]}: complete.')


async def add_subscriptions_all_churches():
    """Add subscription records for existing churches that don't have them."""
    existing_churches = [
        {'id': 'abundant-church-001', 'plan': 'growth'},
        {'id': 'abundant-east-001', 'plan': 'growth'},
        {'id': 'abundant-west-001', 'plan': 'growth'},
        {'id': 'abundant-downtown-001', 'plan': 'growth'},
        {'id': 'potters-house-001', 'plan': 'enterprise'},
        {'id': 'edenx-001', 'plan': 'growth'},
        {'id': 'cityreach-001', 'plan': 'growth'},
    ]
    for ch in existing_churches:
        existing = await db.subscriptions.count_documents({'tenant_id': ch['id']})
        if existing < 10:
            sub_amount = 499 if ch['plan'] == 'growth' else 799
            subs = []
            for mo in range(36):
                dt = date(2023, 4, 1) + timedelta(days=30 * mo)
                subs.append({'id': str(uuid.uuid4()), 'tenant_id': ch['id'], 'plan': ch['plan'],
                             'amount': sub_amount, 'status': 'paid',
                             'billing_date': dt.isoformat(),
                             'period_month': dt.strftime('%Y-%m'),
                             'created_at': datetime.now(timezone.utc).isoformat()})
            await db.subscriptions.insert_many(subs)
            print(f'  Subscriptions added for {ch["id"]}: {len(subs)} records')


async def main():
    print('=== Hill Country Bible Church Seed ===')
    await seed_church(HILL_COUNTRY)
    print('\n=== Adding Subscription Records for All Churches ===')
    await add_subscriptions_all_churches()
    print('\n=== Done ===')
    client.close()

asyncio.run(main())
