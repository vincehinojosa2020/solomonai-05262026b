"""Rename Abundant Northeast to Abundant Downtown"""
import pymongo
import os
import re

client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client[os.environ.get('DB_NAME', 'solomonai')]

# Rename in tenants
result = db.tenants.update_many(
    {'name': re.compile('Abundant Northeast', re.IGNORECASE)},
    {'$set': {'name': 'Abundant Downtown'}}
)
print(f'Tenants renamed: {result.modified_count}')

# Update in platform_stats_cache
cache = db.platform_stats_cache.find_one({'cache_key': 'platform_stats'})
if cache and 'data' in cache:
    data = cache['data']
    if 'campus_breakdown' in data:
        for c in data['campus_breakdown']:
            if 'northeast' in c.get('name', '').lower():
                c['name'] = 'Abundant Downtown'
                print(f'Updated campus_breakdown entry to: Abundant Downtown')
        db.platform_stats_cache.update_one(
            {'cache_key': 'platform_stats'},
            {'$set': {'data': data}}
        )
        print('Cache updated')

# Update in dashboard_stats_cache
for doc in db.dashboard_stats_cache.find({'tenant_name': re.compile('northeast', re.IGNORECASE)}):
    db.dashboard_stats_cache.update_one(
        {'_id': doc['_id']},
        {'$set': {'tenant_name': 'Abundant Downtown'}}
    )
    print(f'Updated dashboard_stats_cache for tenant')

# Also update health scores cache
for doc in db.platform_stats_cache.find({'cache_key': 'health_scores'}):
    if 'data' in doc:
        for hs in doc['data']:
            if 'northeast' in hs.get('name', '').lower():
                hs['name'] = 'Abundant Downtown'
        db.platform_stats_cache.update_one(
            {'_id': doc['_id']},
            {'$set': {'data': doc['data']}}
        )
        print('Updated health scores cache')

# Verify
print('\nAll tenants:')
for t in db.tenants.find({}, {'name': 1, '_id': 0}):
    print(f'  - {t["name"]}')
