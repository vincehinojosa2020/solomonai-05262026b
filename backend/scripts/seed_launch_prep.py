"""
Seed Cristo Viene + fix all 7 church caches to match launch spec:
- 10,000+ members each
- 80%+ active donors (8,000+)
- Health scores: Abundant = A+, others = B-
- Subscription tier: Enterprise ($2,000/mo) for all 10K+ churches
"""
import asyncio, random, uuid, hashlib, os
from datetime import datetime, timezone, timedelta, date
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ.get('DB_NAME', 'solomonai')]

DEMO_PW = hashlib.sha256(b'Demo2026!').hexdigest()
START = date(2023, 4, 1); END = date(2026, 3, 31)

FIRST_M = ['Carlos','Juan','Miguel','Jose','Luis','Antonio','Roberto','Eduardo','Francisco','Manuel','Pedro','Rafael','Jorge','Alejandro','Diego']
FIRST_F = ['Maria','Ana','Sofia','Isabella','Carmen','Rosa','Elena','Patricia','Diana','Angela','Gloria','Lucia','Sandra','Teresa','Monica']
LAST = ['Garcia','Rodriguez','Martinez','Hernandez','Lopez','Gonzalez','Perez','Torres','Flores','Sanchez','Reyes','Cruz','Morales','Jimenez','Ortiz']

TIERS = [
    {'name':'Tither',   'pct':0.05,'min':3000,'max':9000,'freq':(26,52)},
    {'name':'Committed','pct':0.15,'min':900, 'max':3000,'freq':(12,24)},
    {'name':'Engaged',  'pct':0.25,'min':400, 'max':900, 'freq':(8,18)},
    {'name':'Regular',  'pct':0.25,'min':220, 'max':400, 'freq':(4,12)},
    {'name':'Occasional','pct':0.30,'min':100,'max':300, 'freq':(2,8)},
]
GROWTH = {2023:1.00, 2024:1.04, 2025:1.084}
METHODS = ['card']*55+['check']*25+['cash']*10+['ach']*10
FUNDS = [('General Fund',0.72),('Building Fund',0.10),('Missions',0.08),('Youth Ministry',0.05),('Benevolence',0.05)]

def all_sundays():
    d = START
    while d.weekday() != 6: d += timedelta(days=1)
    s = []
    while d <= END: s.append(d); d += timedelta(days=7)
    return s
SUNDAYS = all_sundays()

def assign_tier(i, total):
    c = 0
    for t in TIERS:
        c += t['pct']
        if i < total * c: return t
    return TIERS[-1]

async def seed_cristo_viene():
    tid = 'cristoviene-001'
    existing = await db.people.count_documents({'tenant_id': tid})
    
    await db.tenants.update_one({'id': tid}, {'$set': {
        'id': tid, 'name': 'Cristo Viene Church', 'subscription_status': 'active',
        'plan': 'enterprise', 'city': 'El Paso', 'state': 'TX',
        'address': '4500 Transmountain Dr, El Paso, TX 79924',
        'subdomain': 'cristoviene', 'primary_color': '#dc2626',
        'parent_organization': None, 'created_at': datetime.now(timezone.utc).isoformat(),
    }}, upsert=True)

    await db.users.update_one({'email': 'admin@cristoviene.church'}, {'$set': {
        'user_id': f'admin_cristoviene', 'email': 'admin@cristoviene.church',
        'name': 'Pastor Carlos Mendoza', 'role': 'church_admin',
        'tenant_id': tid, 'password_hash': DEMO_PW,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }}, upsert=True)

    if existing > 100:
        print(f'  Cristo Viene: already has {existing} people')
    else:
        members = 10200
        print(f'  Seeding Cristo Viene ({members} members)...')
        people = []
        for i in range(members):
            g = random.choice(['M','F'])
            fn = random.choice(FIRST_M if g=='M' else FIRST_F)
            ln = random.choice(LAST)
            people.append({'id': f'p_crv_{i:05d}', 'tenant_id': tid,
                'first_name': fn, 'last_name': ln, 'name': f'{fn} {ln}', 'gender': g,
                'email': f'{fn.lower()}.{ln.lower()}.{i}@cristoviene.church',
                'membership_status': random.choice(['member']*4+['regular','visitor']),
                'created_at': datetime.now(timezone.utc).isoformat()})
        for i in range(0, len(people), 500):
            await db.people.insert_many(people[i:i+500])

        # Funds
        fund_docs = []
        for fname, fpct in FUNDS:
            fid = f'fund_crv_{uuid.uuid4().hex[:8]}'
            fund_docs.append({'id': fid, 'tenant_id': tid, 'name': fname, 'is_active': True,
                'goal_amount': int(3500000 * fpct), 'current_amount': 0,
                'created_at': datetime.now(timezone.utc).isoformat()})
        await db.funds.insert_many(fund_docs)

        # Donations
        active_count = int(members * 0.82)
        givers = people[:active_count]
        donations = []
        for i, person in enumerate(givers):
            tier = assign_tier(i, active_count)
            for year in [2023, 2024, 2025]:
                g2 = GROWTH[year]
                annual = random.uniform(tier['min'], tier['max']) * g2
                events = random.randint(*tier['freq'])
                per_event = annual / events
                yr_sundays = [s for s in SUNDAYS if s.year == year]
                chosen = random.sample(yr_sundays, min(events, len(yr_sundays)))
                for d in chosen:
                    amt = round(per_event * random.uniform(0.8, 1.2), 2)
                    if amt < 5: continue
                    fund = random.choices(fund_docs, weights=[f[1] for f in FUNDS])[0]
                    method = random.choice(METHODS)
                    fee = round(amt*0.019+0.30,2) if method=='card' else round(min(amt*0.008+0.30,5.0),2) if method=='ach' else 0
                    donations.append({'id': str(uuid.uuid4()), 'tenant_id': tid,
                        'person_id': person['id'], 'donor_name': person['name'],
                        'fund_id': fund['id'], 'fund_name': fund['name'],
                        'amount': amt, 'fee_amount': fee, 'net_amount': round(amt-fee,2),
                        'donation_date': d.isoformat(), 'payment_method': method,
                        'status': 'completed', 'source': 'solomonpay',
                        'created_at': datetime(year, d.month, d.day, 9, 0, tzinfo=timezone.utc)})
        for i in range(0, len(donations), 1000):
            await db.donations.insert_many(donations[i:i+1000])
        total_giving = sum(d['amount'] for d in donations)
        print(f'  Cristo Viene: {len(donations):,} donations, ${total_giving:,.0f}')

    # Stats cache
    ytd = await db.donations.aggregate([
        {'$match': {'tenant_id': tid, 'donation_date': {'$gte': '2025-01-01'}}},
        {'$group': {'_id': None, 'vol': {'$sum': '$amount'}}}
    ]).to_list(1)
    ytd_vol = ytd[0]['vol'] if ytd else 0
    members_count = await db.people.count_documents({'tenant_id': tid})
    active_count = int(members_count * 0.82)
    
    await db.dashboard_stats_cache.update_one({'tenant_id': tid}, {'$set': {
        'tenant_id': tid, 'total_members': members_count, 'active_members': active_count,
        'ytd_giving': round(ytd_vol, 2), 'mtd_giving': round(ytd_vol/12, 2),
        'mtd_goal': round(ytd_vol/12, 2), 'active_groups': 18,
        'last_attendance': int(active_count*0.55), 'recurring_givers': int(active_count*0.42),
        'preset_health_score': 74, 'preset_health_grade': 'B-',
        'preset_health_dimensions': {
            'engagement': {'score':72,'value':82,'label':'Engagement Rate','unit':'%'},
            'giving': {'score':73,'value':8.5,'label':'Giving / Member','unit':'$/mo'},
            'community': {'score':71,'value':1.0,'label':'Groups/100 Members','unit':''},
            'attendance': {'score':72,'value':48,'label':'Attendance Rate','unit':'%'},
            'growth': {'score':73,'value':34,'label':'Recurring Donors','unit':'%'},
        },
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }}, upsert=True)
    print('  Cristo Viene: cache set')


async def fix_all_church_caches():
    """Fix all 7 churches to match launch spec: 10K+ members, 80%+ active donors."""
    
    # Final 7 church health config per directive
    # Abundant (East/West/Downtown): A+ | All others: B-
    CHURCHES = [
        {'id':'abundant-east-001',     'name':'Abundant East',     'members':10200, 'active_pct':0.83, 'grade':'A+', 'score':96},
        {'id':'abundant-west-001',     'name':'Abundant West',     'members':10100, 'active_pct':0.81, 'grade':'A+', 'score':93},
        {'id':'abundant-downtown-001', 'name':'Abundant Downtown', 'members':10000, 'active_pct':0.80, 'grade':'A+', 'score':89},
        {'id':'hillcountry-001',       'name':'Hill Country Bible Church', 'members':10000, 'active_pct':0.80, 'grade':'B-', 'score':68},
        {'id':'cityreach-001',         'name':'City Reach Church', 'members':10400, 'active_pct':0.82, 'grade':'B-', 'score':66},
        {'id':'edenx-001',             'name':'EdenX Ministries',  'members':10300, 'active_pct':0.81, 'grade':'B-', 'score':67},
        {'id':'cristoviene-001',       'name':'Cristo Viene Church','members':10200,'active_pct':0.82,'grade':'B-', 'score':65},
    ]
    
    B_MINUS_DIMS = lambda: {
        'engagement': {'score':68,'value':80,'label':'Engagement Rate','unit':'%'},
        'giving':     {'score':66,'value':7.8,'label':'Giving / Member','unit':'$/mo'},
        'community':  {'score':65,'value':0.9,'label':'Groups/100 Members','unit':''},
        'attendance': {'score':64,'value':46,'label':'Attendance Rate','unit':'%'},
        'growth':     {'score':65,'value':32,'label':'Recurring Donors','unit':'%'},
    }
    A_PLUS_DIMS = {
        'abundant-east-001':     {'engagement':{'score':95,'value':83,'label':'Engagement Rate','unit':'%'},'giving':{'score':98,'value':13.2,'label':'Giving / Member','unit':'$/mo'},'community':{'score':95,'value':1.5,'label':'Groups/100 Members','unit':''},'attendance':{'score':96,'value':58,'label':'Attendance Rate','unit':'%'},'growth':{'score':94,'value':44,'label':'Recurring Donors','unit':'%'}},
        'abundant-west-001':     {'engagement':{'score':92,'value':81,'label':'Engagement Rate','unit':'%'},'giving':{'score':94,'value':12.1,'label':'Giving / Member','unit':'$/mo'},'community':{'score':90,'value':1.4,'label':'Groups/100 Members','unit':''},'attendance':{'score':91,'value':55,'label':'Attendance Rate','unit':'%'},'growth':{'score':90,'value':42,'label':'Recurring Donors','unit':'%'}},
        'abundant-downtown-001': {'engagement':{'score':88,'value':80,'label':'Engagement Rate','unit':'%'},'giving':{'score':89,'value':11.0,'label':'Giving / Member','unit':'$/mo'},'community':{'score':85,'value':1.3,'label':'Groups/100 Members','unit':''},'attendance':{'score':87,'value':52,'label':'Attendance Rate','unit':'%'},'growth':{'score':85,'value':40,'label':'Recurring Donors','unit':'%'}},
    }

    for ch in CHURCHES:
        tid = ch['id']
        members = ch['members']
        active = int(members * ch['active_pct'])
        
        ytd = await db.donations.aggregate([
            {'$match': {'tenant_id': tid, 'donation_date': {'$gte': '2025-01-01'}}},
            {'$group': {'_id': None, 'vol': {'$sum': '$amount'}}}
        ]).to_list(1)
        ytd_vol = ytd[0]['vol'] if ytd else members * 550

        dims = A_PLUS_DIMS.get(tid, B_MINUS_DIMS())
        
        await db.dashboard_stats_cache.update_one({'tenant_id': tid}, {'$set': {
            'tenant_id': tid,
            'total_members': members,
            'active_members': active,
            'ytd_giving': round(ytd_vol, 2),
            'mtd_giving': round(ytd_vol/12, 2),
            'mtd_goal': round(members * 450 / 12, 2),
            'active_groups': random.randint(14, 22),
            'last_attendance': int(active * 0.55),
            'recurring_givers': int(active * 0.42),
            'preset_health_score': ch['score'],
            'preset_health_grade': ch['grade'],
            'preset_health_dimensions': dims,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }}, upsert=True)
        print(f'  {ch["name"]}: {members:,} members, {active:,} active ({int(ch["active_pct"]*100)}%), health={ch["grade"]}({ch["score"]})')
    
    # Also fix tenant names
    await db.tenants.update_one({'id':'abundant-downtown-001'},{'$set':{'name':'Abundant Downtown'}})


async def add_subscription_tiers():
    """Update all churches to Enterprise tier ($2,000/mo) — all have 10K+ members."""
    tier_config = {'enterprise_10k': {'name': 'Enterprise', 'price': 2000, 'min_members': 10000}}
    churches = ['abundant-east-001','abundant-west-001','abundant-downtown-001',
                'hillcountry-001','cityreach-001','edenx-001','cristoviene-001',
                'potters-house-001','abundant-church-001']
    for tid in churches:
        await db.tenants.update_one({'id': tid}, {'$set': {'plan': 'enterprise', 'subscription_price': 2000}})
    print(f'  Updated {len(churches)} churches to Enterprise ($2,000/mo)')


async def main():
    print('=== Seeding Cristo Viene ===')
    await seed_cristo_viene()
    print('\n=== Fixing all church caches ===')
    await fix_all_church_caches()
    print('\n=== Updating subscription tiers ===')
    await add_subscription_tiers()
    print('\nDone!')
    client.close()

asyncio.run(main())
