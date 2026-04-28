"""Seed Abundant East, West, Downtown campuses with 3 years of realistic data."""
import asyncio
import random
import uuid
import hashlib
from datetime import datetime, timezone, timedelta, date
import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ.get('DB_NAME', 'solomonai')]

FIRST_M = ['James','John','Michael','William','David','Marcus','Carlos','Miguel','Jose','Luis','Antonio','Eduardo','Roberto','Jorge','Gabriel']
FIRST_F = ['Jennifer','Ashley','Maria','Sofia','Isabella','Jasmine','Diana','Rosa','Elena','Angela','Claudia','Lucia','Patricia','Sandra','Teresa']
LAST = ['Johnson','Williams','Garcia','Rodriguez','Martinez','Hernandez','Lopez','Gonzalez','Perez','Torres','Flores','Sanchez','Reyes','Cruz','Morales']

CAMPUSES = [
    {'id':'abundant-east-001','name':'Abundant East','members':10000,'annual':2_400_000,'active_pct':0.83},
    {'id':'abundant-west-001','name':'Abundant West','members':10100,'annual':2_850_000,'active_pct':0.80},
    {'id':'abundant-downtown-001','name':'Abundant Downtown','members':10000,'annual':3_350_000,'active_pct':0.78},
]

START=date(2023,4,1); END=date(2026,3,31)

def all_sundays():
    d=START
    while d.weekday()!=6: d+=timedelta(days=1)
    s=[]
    while d<=END: s.append(d); d+=timedelta(days=7)
    return s

SUNDAYS=all_sundays()
DEMO_PW=hashlib.sha256(b'Demo2026!').hexdigest()
FUNDS=[('General Fund',0.72),('Building Fund',0.10),('Missions',0.08),('Youth',0.05),('Benevolence',0.05)]
METHODS=['card']*55+['check']*25+['cash']*10+['ach']*10

async def seed_campus(t):
    tid=t['id']; nm=t['name']; members=t['members']; annual=t['annual']
    await db.tenants.update_one({'id':tid},{'$set':{'id':tid,'name':nm,'subscription_status':'active',
        'city':'El Paso','state':'TX','primary_color':'#1e40af','parent_organization':'Abundant',
        'created_at':datetime.now(timezone.utc).isoformat()}},upsert=True)
    existing=await db.people.count_documents({'tenant_id':tid})
    if existing>100:
        print(f'  {nm}: already seeded ({existing} people)')
        return
    print(f'  Seeding {nm}...')
    people=[]
    for i in range(members):
        g=random.choice(['M','F'])
        fn=random.choice(FIRST_M if g=='M' else FIRST_F)
        ln=random.choice(LAST)
        pid=f'p_{tid[:8]}_{i:05d}'
        people.append({'id':pid,'tenant_id':tid,'first_name':fn,'last_name':ln,'name':f'{fn} {ln}',
            'email':f'{fn.lower()}.{ln.lower()}.{i}@{tid[:8]}.church','gender':g,
            'mobile_phone':f'({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}',
            'membership_status':random.choice(['member']*3+['regular','visitor']),
            'created_at':datetime.now(timezone.utc).isoformat()})
    for i in range(0,len(people),500): await db.people.insert_many(people[i:i+500])
    print(f'  {nm}: {len(people)} people inserted')
    
    fund_docs=[]
    for fname,fpct in FUNDS:
        fid=f'fund_{tid[:6]}_{uuid.uuid4().hex[:8]}'
        fund_docs.append({'id':fid,'tenant_id':tid,'name':fname,'is_active':True,'goal_amount':int(annual*fpct),'current_amount':0,'created_at':datetime.now(timezone.utc).isoformat()})
    await db.funds.insert_many(fund_docs)
    
    givers=random.sample(people,int(len(people)*0.60))
    target=annual*3  # 3 years
    total_per_giver=target/len(givers)
    donations=[]
    for p in givers:
        events_per_yr=random.randint(6,52)
        per_event=total_per_giver/events_per_yr/3
        for year in [2023,2024,2025]:
            yr_sundays=[s for s in SUNDAYS if s.year==year]
            chosen=random.sample(yr_sundays,min(events_per_yr,len(yr_sundays)))
            for d in chosen:
                amt=round(per_event*random.uniform(0.7,1.4)*(1+(year-2023)*0.04),2)
                if amt<5: continue
                fund=random.choices(fund_docs,weights=[f[1] for f in FUNDS])[0]
                method=random.choice(METHODS)
                fee=round(amt*0.019+0.30,2) if method=='card' else round(min(amt*0.008+0.30,5.0),2) if method=='ach' else 0
                donations.append({'id':str(uuid.uuid4()),'tenant_id':tid,'person_id':p['id'],
                    'donor_name':p['name'],'fund_id':fund['id'],'fund_name':fund['name'],
                    'amount':amt,'fee_amount':fee,'net_amount':round(amt-fee,2),
                    'donation_date':d.isoformat(),'payment_method':method,'status':'completed',
                    'source':'solomonpay','created_at':datetime(year,d.month,d.day,10,0,tzinfo=timezone.utc)})
    for i in range(0,len(donations),1000): await db.donations.insert_many(donations[i:i+1000])
    print(f'  {nm}: {len(donations)} donations inserted  (${sum(d["amount"] for d in donations):,.0f})')
    
    active=int(members*t['active_pct'])
    annual_2025=sum(d['amount'] for d in donations if d['donation_date'].startswith('2025'))
    await db.dashboard_stats_cache.update_one({'tenant_id':tid},{'$set':{
        'tenant_id':tid,'total_members':members,'active_members':active,
        'ytd_giving':round(annual_2025,2),'mtd_giving':round(annual_2025/12,2),'mtd_goal':round(annual/12,2),
        'active_groups':12,'last_attendance':int(active*0.55),'recurring_givers':int(len(givers)*0.12),
        'updated_at':datetime.now(timezone.utc).isoformat()}},upsert=True)
    
    domain=nm.lower().replace(' ','').replace("'",'')
    await db.users.update_one({'email':f'admin@{domain}.church'},{'$set':{
        'user_id':f'admin_{tid[:8]}','email':f'admin@{domain}.church','name':f'Admin {nm}',
        'role':'church_admin','tenant_id':tid,'password_hash':DEMO_PW,
        'created_at':datetime.now(timezone.utc).isoformat()}},upsert=True)

async def main():
    for t in CAMPUSES:
        await seed_campus(t)
    print('Abundant campuses done!')
    client.close()

asyncio.run(main())
