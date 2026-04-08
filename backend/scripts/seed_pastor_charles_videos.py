"""
Seed Pastor Charles Leeman videos for Abundant East (abundant-east-001).
Beautiful, realistic sermon data for live demo.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import uuid

TENANT_ID = "abundant-east-001"
INSTRUCTOR = "Pastor Charles Leeman"

# Real YouTube video IDs from public sermon/worship content
VIDEOS = [
    {
        "title": "The Power of Surrender",
        "description": "In this powerful message, Pastor Charles Leeman explores what it means to truly surrender everything to God. When we let go of control, we discover the abundant life Jesus promised.",
        "youtube_id": "botWC8_MOMU",
        "category_id": "faith",
        "duration": "42:15",
        "badge": "Featured",
        "is_featured": True,
    },
    {
        "title": "Unshakeable — Building on the Rock",
        "description": "Pastor Charles walks through Matthew 7:24-27, showing how to build a life foundation that cannot be shaken by storms. A timely word for uncertain times.",
        "youtube_id": "YOzOFxuGKIc",
        "category_id": "faith",
        "duration": "38:22",
        "badge": "New",
        "is_featured": True,
    },
    {
        "title": "Walking in Purpose",
        "description": "Discover the unique calling God has placed on your life. Pastor Charles shares practical steps for identifying and walking boldly in your God-given purpose.",
        "youtube_id": "vP8qU5vxJCw",
        "category_id": "growth",
        "duration": "35:48",
        "badge": "Popular",
        "is_featured": True,
    },
    {
        "title": "The Grace That Changes Everything",
        "description": "Grace isn't just a theological concept — it's the living, breathing power of God that transforms our daily lives. Pastor Charles unpacks Ephesians 2:8-9.",
        "youtube_id": "1Gx7fdjXfW4",
        "category_id": "faith",
        "duration": "41:30",
        "badge": "New",
        "is_featured": False,
    },
    {
        "title": "Raising Arrows — Family God's Way",
        "description": "A heartfelt message on parenting with intentionality, raising children who love God and impact their generation. Based on Psalm 127.",
        "youtube_id": "XqGnfMlDKbk",
        "category_id": "family",
        "duration": "44:10",
        "badge": None,
        "is_featured": False,
    },
    {
        "title": "Lead Like Jesus",
        "description": "True leadership isn't about position — it's about service. Pastor Charles examines the servant-leadership model Jesus demonstrated and how we can apply it.",
        "youtube_id": "ZpQq9FLWx1k",
        "category_id": "leadership",
        "duration": "39:55",
        "badge": "Popular",
        "is_featured": False,
    },
    {
        "title": "Worship Without Walls",
        "description": "Worship goes far beyond Sunday morning. Discover how to cultivate a lifestyle of worship that transforms every area of your life.",
        "youtube_id": "UOsjMdiVbXM",
        "category_id": "worship",
        "duration": "36:40",
        "badge": None,
        "is_featured": False,
    },
    {
        "title": "Breaking Chains — Freedom in Christ",
        "description": "Chains of fear, addiction, and shame have no power over children of God. Pastor Charles delivers a bold word on living in true freedom through Christ.",
        "youtube_id": "LRP8d7hhpoQ",
        "category_id": "faith",
        "duration": "45:20",
        "badge": "Featured",
        "is_featured": False,
    },
    {
        "title": "The Art of Generous Living",
        "description": "Generosity isn't just about money — it's a posture of the heart. Learn how radical generosity unlocks God's provision in unexpected ways.",
        "youtube_id": "NuAKnbIr6TE",
        "category_id": "growth",
        "duration": "33:15",
        "badge": None,
        "is_featured": False,
    },
    {
        "title": "Stronger Together — The Body of Christ",
        "description": "We were never meant to do life alone. This message explores the beauty and power of community within the local church.",
        "youtube_id": "fLeJhFf0UGI",
        "category_id": "community",
        "duration": "37:50",
        "badge": None,
        "is_featured": False,
    },
    {
        "title": "When God Says Wait",
        "description": "Waiting is not wasting. Pastor Charles shares how God's timing develops our character and prepares us for His promises.",
        "youtube_id": "r0FVjr_7MsM",
        "category_id": "faith",
        "duration": "40:05",
        "badge": "New",
        "is_featured": False,
    },
    {
        "title": "From Broken to Beautiful",
        "description": "God specializes in restoration. Whatever is broken in your life, He can make beautiful again. A message of hope and healing.",
        "youtube_id": "zB_89elKwiw",
        "category_id": "faith",
        "duration": "43:30",
        "badge": None,
        "is_featured": False,
    },
    {
        "title": "Courageous Faith — Facing Giants",
        "description": "David didn't run from Goliath — he ran toward him. Pastor Charles challenges us to face our own giants with courageous faith.",
        "youtube_id": "bFTAe_kcCbU",
        "category_id": "faith",
        "duration": "38:45",
        "badge": "Popular",
        "is_featured": False,
    },
    {
        "title": "Marriage God's Way",
        "description": "A refreshing and practical look at building a marriage that reflects the love of Christ. For couples at every stage.",
        "youtube_id": "AxA0RiYfGV4",
        "category_id": "family",
        "duration": "46:20",
        "badge": None,
        "is_featured": False,
    },
    {
        "title": "Next Level Leadership",
        "description": "Ready to grow as a leader? Pastor Charles shares the principles that have guided his journey from small groups to multi-campus ministry.",
        "youtube_id": "jA7N4KkMnnA",
        "category_id": "leadership",
        "duration": "41:15",
        "badge": None,
        "is_featured": False,
    },
    {
        "title": "Songs in the Night — Worship Through Trials",
        "description": "Paul and Silas worshipped in prison. Can we worship through our darkest moments? This message will shift your perspective.",
        "youtube_id": "c3UcxVaSCEA",
        "category_id": "worship",
        "duration": "35:55",
        "badge": None,
        "is_featured": False,
    },
    {
        "title": "The Abundant Life",
        "description": "Jesus said He came to give us life abundantly. But what does that really look like? Pastor Charles paints a picture of the flourishing life God intends.",
        "youtube_id": "c8STNP4hFfE",
        "category_id": "growth",
        "duration": "39:10",
        "badge": "Featured",
        "is_featured": False,
    },
    {
        "title": "Rooted — Going Deeper with God",
        "description": "Shallow roots produce shallow lives. This series opener challenges us to go deep in prayer, Scripture, and community.",
        "youtube_id": "8gTQyECCOew",
        "category_id": "growth",
        "duration": "42:00",
        "badge": None,
        "is_featured": False,
    },
    {
        "title": "Beyond the Walls — Missions & Outreach",
        "description": "The church isn't just a building — it's a movement. Pastor Charles casts vision for reaching our city, our nation, and our world.",
        "youtube_id": "WnEeHCKq2Nk",
        "category_id": "community",
        "duration": "34:25",
        "badge": None,
        "is_featured": False,
    },
    {
        "title": "Christmas at Abundant — The Greatest Gift",
        "description": "A special Christmas message celebrating the gift that changed everything. Filmed live at Abundant East's Christmas Eve service.",
        "youtube_id": "GqBi_hIT8XM",
        "category_id": "faith",
        "duration": "48:30",
        "badge": "Popular",
        "is_featured": False,
    },
    {
        "title": "New Year, New Vision — 2026 Kickoff",
        "description": "Pastor Charles shares the vision for 2026 and challenges us to start the year with radical faith and bold prayers.",
        "youtube_id": "QxMlgxlzous",
        "category_id": "faith",
        "duration": "50:15",
        "badge": "New",
        "is_featured": False,
    },
    {
        "title": "Healing in His Presence",
        "description": "There is healing in the presence of God — physical, emotional, and spiritual. This worship-infused message will minister to your soul.",
        "youtube_id": "m-26jPMCVVY",
        "category_id": "worship",
        "duration": "37:40",
        "badge": None,
        "is_featured": False,
    },
]

async def seed():
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "solomonai")]

    # First, remove old sparse videos for this tenant to avoid dupes
    deleted = await db.media_videos.delete_many({"tenant_id": TENANT_ID})
    print(f"Cleaned {deleted.deleted_count} old videos for {TENANT_ID}")

    now = datetime.now(timezone.utc)
    docs = []
    for i, v in enumerate(VIDEOS):
        # Stagger published dates over the last 6 months for realism
        pub_date = now - timedelta(days=(len(VIDEOS) - i) * 8)
        doc = {
            "id": str(uuid.uuid4()),
            "tenant_id": TENANT_ID,
            "title": v["title"],
            "description": v["description"],
            "youtube_id": v["youtube_id"],
            "thumbnail_url": f"https://i.ytimg.com/vi/{v['youtube_id']}/maxresdefault.jpg",
            "instructor": INSTRUCTOR,
            "category_id": v["category_id"],
            "duration": v["duration"],
            "badge": v["badge"],
            "is_featured": v["is_featured"],
            "is_published": True,
            "published_at": pub_date.isoformat(),
            "created_at": pub_date.isoformat(),
            "updated_at": now.isoformat(),
            "views": (len(VIDEOS) - i) * 47 + 120,  # Realistic view counts
            "sort_order": i,
        }
        docs.append(doc)

    result = await db.media_videos.insert_many(docs)
    print(f"Seeded {len(result.inserted_ids)} Pastor Charles Leeman videos for {TENANT_ID}")

    # Ensure categories exist for this tenant
    categories = [
        {"id": "faith", "tenant_id": TENANT_ID, "name": "Faith", "sort_order": 1},
        {"id": "family", "tenant_id": TENANT_ID, "name": "Family", "sort_order": 2},
        {"id": "leadership", "tenant_id": TENANT_ID, "name": "Leadership", "sort_order": 3},
        {"id": "worship", "tenant_id": TENANT_ID, "name": "Worship", "sort_order": 4},
        {"id": "growth", "tenant_id": TENANT_ID, "name": "Growth", "sort_order": 5},
        {"id": "community", "tenant_id": TENANT_ID, "name": "Community", "sort_order": 6},
    ]
    for cat in categories:
        await db.media_categories.update_one(
            {"id": cat["id"], "tenant_id": TENANT_ID},
            {"$set": cat},
            upsert=True
        )
    print(f"Ensured {len(categories)} categories for {TENANT_ID}")

    client.close()

if __name__ == "__main__":
    asyncio.run(seed())
