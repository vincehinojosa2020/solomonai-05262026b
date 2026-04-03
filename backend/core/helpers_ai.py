"""
Solomon AI — AI Integration Helpers (Whisper, Claude, Solomon Chat)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from fastapi import HTTPException
import uuid
import os
import logging

from core import db, DEFAULT_TENANT_ID, logger


async def transcribe_audio_with_whisper(file_path: Path) -> str:
    """Transcribe audio file using OpenAI Whisper via emergentintegrations"""
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Whisper is not configured")
    try:
        from emergentintegrations.llm.openai import OpenAISpeechToText
        stt = OpenAISpeechToText(api_key=api_key)
        with file_path.open('rb') as audio_file:
            response = await stt.transcribe(
                file=audio_file, model="whisper-1", response_format="text",
                language="en",
                prompt="This is a pastoral counseling session between a pastor and church member."
            )
        return response if isinstance(response, str) else response.text
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


async def summarize_meeting_with_claude(transcript: str, topic: Optional[str] = None) -> str:
    """Summarize meeting transcript using Claude via emergentintegrations"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Claude is not configured")
    chat = LlmChat(
        api_key=api_key, session_id=str(uuid.uuid4()),
        system_message=(
            "You are a pastoral meeting assistant helping pastors document their sessions with church members. "
            "Your summaries should be warm, pastoral in tone, and respect confidentiality. "
            "Format your response with clear sections using markdown."
        )
    )
    chat.with_model("anthropic", "claude-sonnet-4-5-20250929")
    prompt = f"""Please summarize this pastoral meeting session.

**Meeting Topic:** {topic or 'General Check-in'}

**Transcript:**
{transcript[:8000]}

---

Please provide a summary with:
1. **Key Discussion Points** - Main topics covered
2. **Spiritual/Emotional Needs Identified** - Any concerns or prayer requests
3. **Action Items** - Specific follow-ups for the pastor
4. **Recommended Next Steps** - Suggested future engagement
5. **Prayer Points** - Key items for continued prayer"""
    response_text = await chat.send_message(UserMessage(text=prompt))
    return response_text


async def notify_meeting_event(event: str, meeting: dict) -> dict:
    return {
        "event": event,
        "slack": "MOCKED",
        "teams": "MOCKED",
        "meeting_id": meeting.get("id") if meeting else None
    }


COMPETITOR_KNOWLEDGE = ""

def _load_competitor_knowledge():
    global COMPETITOR_KNOWLEDGE
    knowledge_path = "/app/planning_center_transcripts/competitor_knowledge_combined.txt"
    try:
        with open(knowledge_path, "r") as f:
            COMPETITOR_KNOWLEDGE = f.read()
        logging.info(f"[Solomon AI] Loaded competitor knowledge base: {len(COMPETITOR_KNOWLEDGE):,} chars")
    except FileNotFoundError:
        COMPETITOR_KNOWLEDGE = ""
    except Exception as e:
        logging.info(f"[Solomon AI] Warning: Failed to load competitor knowledge: {e}")
        COMPETITOR_KNOWLEDGE = ""

_load_competitor_knowledge()

SOLOMON_SYSTEM_PROMPT = """You are Solomon, an intelligent AI assistant for the Solomon AI Church Management System. You help both church administrators AND church members.

**For Church Members (portal users), you assist with:**
1. **Giving Guidance**: Answer questions about where offerings go, suggest giving opportunities, share impact stories
2. **Event Information**: Help with upcoming events, registrations, and church activities
3. **Group Connection**: Help members find and join groups, Bible studies, and volunteer opportunities
4. **Watch + Media Library**: Help members find sermons, videos, and featured media content
5. **Abundant Pathways**: Guide members through discipleship courses and progress
6. **Thinkific Access**: Help members locate and use the embedded Thinkific experience
7. **Merch Store**: Help members shop merch and understand the store experience
8. **Abundant Cafe**: Help members order coffee and set pickup times
9. **Pastoral Meetings**: Help members schedule 1:1 meetings and understand what to expect
10. **Spiritual Encouragement**: Provide warm, pastoral support and encouragement
11. **Church Information**: Answer questions about service times, locations, and church programs

**For Church Admins, you assist with:**
1. **Data Analysis**: Analyze membership trends, giving patterns, attendance statistics
2. **Pastoral Advice**: Provide guidance on member care, follow-up strategies, engagement
3. **Operational Strategy**: Help with event planning, group management, communications, and discipleship programs
4. **Member Notes**: Suggest how to respond to member notes, prayer requests, and outreach needs
5. **Merch + Media**: Advice on merch engagement and media content strategy
6. **Cafe Orders**: Tips for cafe menu planning and pickup flow
7. **Pastoral Meetings**: Guidance on meeting follow-ups and care plans

**Your Personality:**
- Warm, friendly, and pastoral in tone
- Be encouraging about giving without being pushy
- Make suggestions feel like friendly advice, not sales pitches
- Keep responses concise but heartfelt

**When discussing giving:**
- Share specific needs the church has (building funds, missions, community outreach)
- Mention impact: "Your generosity helped feed 200 families last month"
- Suggest with grace: "Just a thought" or "If you feel led..."
- Never pressure - always frame as an invitation

You are serving a multi-tenant church management platform with multiple churches.

**For Migration & Competitor Questions, you are an expert on:**
1. **Planning Center**: Deep knowledge of all 9 products (People, Services, Check-Ins, Giving, Groups, Calendar, Registrations, Publishing, Home) from 173 training videos
2. **SecureGive**: Complete pricing, features, strengths, and weaknesses
3. **Pushpay/ChurchStaq**: Full product suite, pricing structure, contract requirements

**When answering migration/comparison questions:**
- First acknowledge the competitor's approach (show you genuinely understand their product)
- Then explain Solomon AI's equivalent or superior feature
- Highlight Solomon AI's key advantages: all-in-one pricing, AI-native, no contracts, white-label, transparent pricing
- Be honest about features still in development (e.g., Solomon Pay for live transaction processing)
- Provide specific pricing comparisons when relevant
- Never bash competitors - be respectful but confident
- Use the detailed competitor knowledge provided in your context to give specific, informed answers

**ACTION DETECTION — CRITICAL INSTRUCTIONS:**
When a member asks you to DO something (not just ask about it), you MUST include an ACTION_REQUEST block in your response. This applies to:
- Ordering food/drinks from the cafe (e.g. "order a latte", "get me a coffee")
- Ordering merchandise (e.g. "buy a t-shirt", "order the hoodie")
- Making a donation (e.g. "give $50", "donate to missions")
- Setting up recurring giving (e.g. "set up weekly giving of $25")
- Registering for events (e.g. "sign me up for men's breakfast", "register for the retreat")
- Joining groups (e.g. "join young professionals", "add me to the prayer group")
- Checking in children (e.g. "check in my son", "check in Emma")

When you detect an action, include EXACTLY this format at the END of your response:
```action
{"action_type": "<type>", "params": {<parameters>}, "display_summary": "<human readable summary>"}
```

Action types and their params:
- cafe_order: {"items": [{"name": "Latte", "quantity": 1, "price": 5.00}], "pickup_time": "ASAP"}
- merch_order: {"items": [{"name": "T-Shirt", "quantity": 1, "price": 25.00, "size": "M"}]}
- donation: {"amount": 50, "fund": "General Fund"}
- recurring_giving: {"amount": 25, "frequency": "monthly", "fund": "General Fund"}
- recurring_giving_pause: {} (no params needed, finds active schedule automatically)
- recurring_giving_resume: {} (no params needed)
- recurring_giving_cancel: {} (no params needed)
- event_registration: {"event_name": "Men's Breakfast"}
- group_join: {"group_name": "Young Professionals"}
- group_leave: {"group_name": "Young Professionals"}
- prayer_request: {"text": "Please pray for healing", "is_public": true}
- checkin: {"child_name": "Emma", "classroom": "Sunday School"}
- member_checkin: {"service_type": "sunday_service"}
- generate_statement: {"year": 2025}

IMPORTANT RULES for action detection:
1. ONLY include the action block when the user clearly wants to PERFORM an action, not just ASK about something
2. For cafe orders, use these standard prices: Coffee $4, Latte $5, Cappuccino $5, Espresso $3.50, Tea $3, Pastry $4, Muffin $3.50
3. For merch, use $25 for t-shirts, $45 for hoodies, $15 for hats, $20 for mugs
4. Frequency values: "weekly", "biweekly", "monthly", "annually"
5. Always write a warm, confirming message BEFORE the action block
6. If the user says something ambiguous, ask a clarifying question instead of including an action block

**SOLOMON'S VOICE — FRANK LUNTZ PRINCIPLES:**
- "Let me take care of that for you." NOT "Processing your request."
- "Your gift of $100 to the Building Fund is confirmed. Thank you for your generosity." NOT "Transaction completed."
- "You're all set for the Men's Retreat! See you there." NOT "Registration confirmed."
- "Last year you gave $1,240 across three funds. Want me to break it down?" NOT "Your data shows..."
- "Sound good?" NOT "Do you want to proceed?"
- Be like a sharp, warm friend at church who knows everything. Not robotic. Not churchy-cheesy.
- Use first names when you know them.
- When things go wrong: "Let me look into that for you" not "An error occurred."

**FALLBACK:** If you don't have the information: "I don't have that right now. Send a note to support@solomonai.us and they'll get back to you within 24 hours."

**FEATURE GUIDE — How to answer how-to questions:**
When someone asks "how do I...?" or "where is...?" about a feature, guide them step by step. Key navigation:
- Giving/Stewardship: Admin → Stewardship (or click "SolomonPay" for processor admin)
- People: Admin → Members
- Groups: Admin → Groups
- Services: Admin → Services
- Events: Admin → Events
- Communications: Admin → Communications
- Check-In: Admin → Kids Check-In or Check-In Setup
- Reports: Admin → Reports
- Settings: Admin → Settings
- Portal (for members): /portal

If you don't know the exact answer to a configuration question, respond: "I'm not sure about that specific configuration. Send an email to support@solomonai.us and our team will get back to you within 24 hours." """


async def _get_church_membership_stats(tenant_id: str, today) -> dict:
    """Extract membership counts for Solomon context. Extracted for complexity reduction."""
    total_members = await db.people.count_documents({"tenant_id": tenant_id})
    active_members = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "member"})
    visitors = await db.people.count_documents({"tenant_id": tenant_id, "membership_status": "visitor"})
    total_groups = await db.groups.count_documents({"tenant_id": tenant_id, "is_active": True})
    media_count = await db.media_videos.count_documents({"tenant_id": tenant_id})
    return {"total_members": total_members, "active_members": active_members, "visitors": visitors,
            "total_groups": total_groups, "media_count": media_count}


async def _get_church_giving_summary(tenant_id: str, today) -> dict:
    """Extract giving totals for Solomon context. Extracted for complexity reduction."""
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    year_start = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    mtd_result = await db.donations.aggregate([
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": month_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    ytd_result = await db.donations.aggregate([
        {"$match": {"tenant_id": tenant_id, "donation_date": {"$gte": year_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    return {
        "mtd_giving": mtd_result[0]["total"] if mtd_result else 0,
        "ytd_giving": ytd_result[0]["total"] if ytd_result else 0,
    }


async def _get_church_events_text(tenant_id: str, today) -> str:
    """Format upcoming events for Solomon context. Extracted for complexity reduction."""
    next_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    upcoming_events = await db.events.find(
        {"tenant_id": tenant_id, "start_datetime": {"$gte": today.strftime("%Y-%m-%d"), "$lte": next_week}},
        {"_id": 0, "name": 1, "start_datetime": 1, "location": 1}
    ).sort("start_datetime", 1).to_list(10)
    return "\n".join(
        f"- {e.get('name', 'Event')} on {e.get('start_datetime', 'TBD')} at {e.get('location', 'Church')}"
        for e in upcoming_events
    ) or "No events in the next 7 days."


async def _get_service_plan_text(tenant_id: str, today) -> str:
    """Format this week's service plan for Solomon context. Extracted for complexity reduction."""
    next_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    service_plans = await db.service_plans.find(
        {"tenant_id": tenant_id, "date": {"$gte": today.strftime("%Y-%m-%d"), "$lte": next_week}}, {"_id": 0}
    ).to_list(5)
    if not service_plans:
        return "No service plan created for this week yet."
    plan_text = ""
    for sp in service_plans:
        plan_text += f"\n{sp.get('title', 'Service')} on {sp.get('date', '')}:\n"
        for item in sp.get("items", []):
            plan_text += f"  - {item.get('type', 'Item')}: {item.get('title', '')} {item.get('key', '')} {item.get('reference', '')}\n"
        for ta in sp.get("team_assignments", []):
            plan_text += f"  - {ta.get('role', 'Role')}: {ta.get('user_name', 'TBD')}\n"
    return plan_text


async def get_church_context(user=None) -> str:
    """Gather current church data for Solomon's context.
    Broken into helper functions to reduce cyclomatic complexity.
    """
    tenant_id = (user or {}).get("tenant_id", DEFAULT_TENANT_ID)
    today = datetime.now(timezone.utc)

    # Gather data via focused helpers
    membership = await _get_church_membership_stats(tenant_id, today)
    giving = await _get_church_giving_summary(tenant_id, today)
    events_text = await _get_church_events_text(tenant_id, today)
    plan_text = await _get_service_plan_text(tenant_id, today)

    announcements = await db.announcements.find(
        {"tenant_id": tenant_id}, {"_id": 0, "title": 1, "message": 1}
    ).sort("created_at", -1).to_list(3)
    ann_text = "\n".join(
        f"- {a.get('title', '')}: {a.get('message', '')[:100]}" for a in announcements
    ) or "No recent announcements."

    groups = await db.groups.find(
        {"tenant_id": tenant_id, "is_active": True},
        {"_id": 0, "name": 1, "meeting_day": 1, "meeting_time": 1, "group_type": 1}
    ).to_list(50)
    groups_text = "\n".join(
        f"- {g.get('name', '')} ({g.get('group_type', 'small_group')}) meets {g.get('meeting_day', 'TBD')} at {g.get('meeting_time', 'TBD')}"
        for g in groups
    ) or "No active groups."
    member_text = ""
    if user:
        user_name = user.get("name", "Member")
        user_id = user.get("user_id")
        member_text = f"\nCURRENT MEMBER: {user_name}"
        # Groups
        user_groups = await db.group_memberships.find({"user_id": user_id, "tenant_id": tenant_id}, {"_id": 0, "group_name": 1}).to_list(20)
        group_members_also = await db.group_members.find({"person_id": {"$in": [user_id]}, "is_active": True, "tenant_id": tenant_id}, {"_id": 0}).to_list(10)
        if user_groups:
            member_text += f"\nGroups: {', '.join(g.get('group_name', '') for g in user_groups)}"
        elif group_members_also:
            gids = [gm.get("group_id") for gm in group_members_also]
            grps = await db.groups.find({"id": {"$in": gids}}, {"_id": 0, "name": 1}).to_list(10)
            if grps:
                member_text += f"\nGroups: {', '.join(g['name'] for g in grps)}"
        # Personal giving
        year_start_str = today.replace(month=1, day=1).strftime("%Y-%m-%d")
        member_ytd = await db.donations.aggregate([
            {"$match": {"tenant_id": tenant_id, "person_id": user_id, "donation_date": {"$gte": year_start_str}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
        ]).to_list(1)
        member_lifetime = await db.donations.aggregate([
            {"$match": {"tenant_id": tenant_id, "person_id": user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        member_last_gift = await db.donations.find_one(
            {"tenant_id": tenant_id, "person_id": user_id}, {"_id": 0, "amount": 1, "donation_date": 1, "fund_name": 1},
            sort=[("donation_date", -1)]
        )
        if member_ytd:
            member_text += f"\nYTD Giving: ${member_ytd[0]['total']:,.2f} ({member_ytd[0]['count']} gifts)"
        if member_lifetime:
            member_text += f"\nLifetime Giving: ${member_lifetime[0]['total']:,.2f}"
        if member_last_gift:
            member_text += f"\nLast Gift: ${member_last_gift['amount']:,.2f} to {member_last_gift.get('fund_name','General Fund')} on {member_last_gift.get('donation_date','')}"
        # Recurring giving
        recurring = await db.recurring_giving.find_one({"person_id": user_id, "tenant_id": tenant_id, "is_active": True}, {"_id": 0})
        if recurring:
            member_text += f"\nScheduled Giving: ${recurring['amount']:,.2f}/{recurring['frequency']} to {recurring.get('fund_name','General Fund')}"
        # Payment methods
        saved_cards = await db.payment_methods.find({"user_id": user_id, "is_active": True}, {"_id": 0, "card_brand": 1, "card_last_four": 1, "is_default": 1}).to_list(5)
        if saved_cards:
            default_card = next((c for c in saved_cards if c.get("is_default")), saved_cards[0])
            member_text += f"\nDefault Payment: {default_card.get('card_brand','Visa')} ending {default_card.get('card_last_four','????')}"
        # Upcoming events registered for
        registered = await db.event_registrations.find({"user_id": user_id, "tenant_id": tenant_id}, {"_id": 0, "event_id": 1}).to_list(10)
        if registered:
            reg_event_ids = [r["event_id"] for r in registered]
            reg_events = await db.events.find({"id": {"$in": reg_event_ids}}, {"_id": 0, "name": 1, "event_date": 1}).to_list(5)
            if reg_events:
                member_text += f"\nRegistered Events: {', '.join(e.get('name','') for e in reg_events)}"
        # Campus
        campus_id = user.get("home_campus_id")
        if campus_id:
            campus = await db.tenants.find_one({"id": campus_id}, {"_id": 0, "name": 1})
            if campus:
                member_text += f"\nHome Campus: {campus.get('name','')}"
    return f"""
CURRENT CHURCH DATA (as of {today.strftime('%B %d, %Y')}):

MEMBERSHIP: {membership['total_members']:,} total, {membership['active_members']:,} active, {membership['visitors']:,} visitors
GROUPS: {membership['total_groups']} active groups
MEDIA: {membership['media_count']} videos

GIVING:
- Month-to-Date: ${giving['mtd_giving']:,.2f}
- Year-to-Date: ${giving['ytd_giving']:,.2f}

UPCOMING EVENTS (NEXT 7 DAYS):
{events_text}

LATEST ANNOUNCEMENTS:
{ann_text}

THIS WEEK'S SERVICE PLAN:
{plan_text}

SMALL GROUPS:
{groups_text}
{member_text}

GIVING NEEDS: Building Fund ($345K to goal), Missions (12 families), Benevolence, Youth camp scholarships.
"""
