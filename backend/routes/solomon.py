"""Solomon AI — Solomon Chat Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging
import os

from core import (
    db, get_current_portal_user, get_session_token_from_request,
    DEFAULT_TENANT_ID, logger,
)
from core.helpers import (
    serialize_doc, get_church_context, SOLOMON_SYSTEM_PROMPT, COMPETITOR_KNOWLEDGE,
)
from models.schemas import SolomonChatRequest, SolomonChatResponse

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()

solomon_sessions: Dict[str, LlmChat] = {}


async def _get_user_safe(request: Request):
    """Safely get user from session, returns None on failure."""
    try:
        token = get_session_token_from_request(request)
        if not token:
            return None
        session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
        if not session:
            return None
        user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
        return user
    except Exception:
        return None


@router.post("/solomon/chat")
async def solomon_chat(request: Request, payload: SolomonChatRequest):
    """Chat with Solomon AI analyst"""
    try:
        if not payload.message or not payload.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        session_id = payload.session_id or str(uuid.uuid4())

        user = await _get_user_safe(request)
        user_role = user.get("role") if user else None

        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="Solomon AI is not configured")

        church_context = await get_church_context(user)
        competitor_context = f"\n\n{COMPETITOR_KNOWLEDGE}" if COMPETITOR_KNOWLEDGE else ""
        full_system_prompt = f"{SOLOMON_SYSTEM_PROMPT}{competitor_context}\n\n{church_context}"

        if session_id not in solomon_sessions:
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id,
                system_message=full_system_prompt
            )
            chat.with_model("anthropic", "claude-sonnet-4-5-20250929")
            solomon_sessions[session_id] = chat
        else:
            chat = solomon_sessions[session_id]

        user_message = UserMessage(text=payload.message)
        response_text = await chat.send_message(user_message)

        await db.solomon_conversations.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": payload.message, "timestamp": datetime.now(timezone.utc).isoformat()},
                            {"role": "assistant", "content": response_text, "timestamp": datetime.now(timezone.utc).isoformat()}
                        ]
                    }
                },
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
                "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}
            },
            upsert=True
        )

        actions = None
        data = None
        response_lower = response_text.lower()
        query_lower = payload.message.lower()
        combined_text = f"{query_lower} {response_lower}"
        is_member = user_role == "member"

        portal_paths = {
            "giving": "/portal/give", "groups": "/portal/groups", "events": "/portal/events",
            "watch": "/portal/library", "media": "/portal/library", "thinkific": "/portal/thinkific",
            "pathways": "/portal/pathways", "discipleship": "/portal/pathways",
            "merch": "/portal/merch", "store": "/portal/merch", "shop": "/portal/merch",
            "cafe": "/portal/cafe", "coffee": "/portal/cafe",
            "meet": "/portal/meetings", "meeting": "/portal/meetings", "pastor": "/portal/meetings"
        }
        admin_paths = {
            "giving": "/giving", "groups": "/admin/groups", "events": "/admin/events",
            "watch": "/media", "media": "/media", "thinkific": "/thinkific",
            "pathways": "/abundant-pathways", "discipleship": "/abundant-pathways",
            "merch": "/merch", "store": "/merch", "shop": "/merch",
            "notes": "/notes", "leadership": "/notes",
            "cafe": "/cafe", "coffee": "/cafe",
            "meet": "/meetings", "meeting": "/meetings", "pastor": "/meetings"
        }
        path_map = portal_paths if is_member else admin_paths

        action_candidates = [
            ("giving", "Open Giving"), ("groups", "View Groups"), ("events", "View Events"),
            ("thinkific", "Open Thinkific"), ("pathways", "Open Abundant Pathways"),
            ("discipleship", "Open Abundant Pathways"), ("watch", "Open Watch"),
            ("media", "Open Media Library"), ("merch", "Open Merch"),
            ("store", "Open Merch"), ("shop", "Open Merch"),
            ("cafe", "Open Cafe"), ("coffee", "Open Cafe"),
            ("meet", "Open Meetings"), ("meeting", "Open Meetings"),
            ("pastor", "Open Meetings"), ("notes", "View Notes"), ("leadership", "View Notes")
        ]
        for keyword, label in action_candidates:
            if keyword in combined_text:
                actions = [{"label": label, "action": "navigate", "path": path_map.get(keyword, "/")}]
                break

        if actions is None:
            if "giving" in combined_text or "donation" in combined_text:
                actions = [
                    {"label": "View Giving Dashboard", "action": "navigate", "path": path_map.get("giving", "/giving")},
                    {"label": "Generate Report", "action": "navigate", "path": "/reports"}
                ]
            elif "group" in combined_text or "ministry" in combined_text:
                actions = [{"label": "View Groups", "action": "navigate", "path": path_map.get("groups", "/admin/groups")}]
            elif "event" in combined_text:
                actions = [{"label": "View Events", "action": "navigate", "path": path_map.get("events", "/admin/events")}]

        return SolomonChatResponse(response=response_text, session_id=session_id, data=data, actions=actions)
    except Exception as e:
        logger.error(f"Solomon AI error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Solomon AI error: {str(e)}")


@router.get("/solomon/history/{session_id}")
async def get_solomon_history(session_id: str):
    """Get conversation history for a session"""
    conversation = await db.solomon_conversations.find_one({"session_id": session_id}, {"_id": 0})
    if not conversation:
        return {"messages": [], "session_id": session_id}
    return serialize_doc(conversation)


@router.delete("/solomon/session/{session_id}")
async def clear_solomon_session(session_id: str):
    """Clear a Solomon chat session"""
    if session_id in solomon_sessions:
        del solomon_sessions[session_id]
    await db.solomon_conversations.delete_one({"session_id": session_id})
    return {"message": "Session cleared", "session_id": session_id}
