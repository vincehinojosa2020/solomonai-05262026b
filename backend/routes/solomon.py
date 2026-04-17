"""Solomon AI — Solomon Chat Routes with Agentic Action Execution"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel
import uuid
import re
import json
import logging
import os
import asyncio

from core import (
    db, get_current_portal_user, get_session_token_from_request,
    DEFAULT_TENANT_ID, logger,
)
from core.helpers import (
    serialize_doc, get_church_context, SOLOMON_SYSTEM_PROMPT, COMPETITOR_KNOWLEDGE,
)
from models.schemas import SolomonChatRequest, SolomonChatResponse
from services.solomon_actions import action_executor

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()

solomon_sessions: Dict[str, LlmChat] = {}


class ExecuteActionRequest(BaseModel):
    session_id: str
    action_type: str
    params: Dict[str, Any]


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


def _parse_action_from_response(response_text: str) -> tuple:
    """Extract action block from Solomon's response. Returns (clean_text, action_dict or None)."""
    pattern = r"```action\s*\n?(.*?)\n?```"
    match = re.search(pattern, response_text, re.DOTALL)
    if not match:
        return response_text, None

    try:
        action_json = json.loads(match.group(1).strip())
        clean_text = response_text[:match.start()].rstrip()
        return clean_text, action_json
    except (json.JSONDecodeError, KeyError):
        return response_text, None


@router.post("/solomon/chat")
async def solomon_chat(request: Request, payload: SolomonChatRequest):
    """Chat with Solomon AI analyst — with agentic action detection"""
    try:
        if not payload.message or not payload.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        session_id = payload.session_id or str(uuid.uuid4())

        user = await _get_user_safe(request)
        user_role = user.get("role") if user else None

        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="Solomon AI is not configured")

        # ── Route to platform admin context if needed ──────────────────────
        if user_role == "platform_admin":
            from core.helpers_ai import build_platform_admin_context
            full_system_prompt = await build_platform_admin_context()
        else:
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

        # Parse for action intent
        clean_response, action_data = _parse_action_from_response(response_text)

        # Store conversation
        await db.solomon_conversations.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": payload.message, "timestamp": datetime.now(timezone.utc).isoformat()},
                            {"role": "assistant", "content": clean_response, "timestamp": datetime.now(timezone.utc).isoformat()}
                        ]
                    }
                },
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
                "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}
            },
            upsert=True
        )

        # Build pending_action if detected
        pending_action = None
        if action_data and isinstance(action_data, dict):
            action_type = action_data.get("action_type")
            params = action_data.get("params", {})
            display_summary = action_data.get("display_summary", "")
            if action_type:
                pending_action = {
                    "action_type": action_type,
                    "params": params,
                    "display_summary": display_summary,
                    "confirmation_id": str(uuid.uuid4()),
                }

        # Navigation actions (keep existing logic for non-action messages)
        actions = None
        if not pending_action:
            response_lower = clean_response.lower()
            query_lower = payload.message.lower()
            combined_text = f"{query_lower} {response_lower}"
            is_member = user_role == "member"

            portal_paths = {
                "giving": "/portal/give", "groups": "/portal/groups", "events": "/portal/events",
                "watch": "/portal/library", "media": "/portal/library", "thinkific": "/portal/thinkific",
                "pathways": "/portal/pathways", "discipleship": "/portal/pathways",
                "merch": "/portal/merch", "store": "/portal/merch", "shop": "/portal/merch",
                "cafe": "/portal/cafe", "coffee": "/portal/cafe",
            }
            admin_paths = {
                "giving": "/giving", "groups": "/admin/groups", "events": "/admin/events",
                "watch": "/media", "media": "/media", "thinkific": "/thinkific",
                "pathways": "/abundant-pathways", "discipleship": "/abundant-pathways",
                "merch": "/merch", "store": "/merch", "shop": "/merch",
                "cafe": "/cafe", "coffee": "/cafe",
            }
            path_map = portal_paths if is_member else admin_paths

            action_candidates = [
                ("giving", "Open Giving"), ("groups", "View Groups"), ("events", "View Events"),
                ("thinkific", "Open Thinkific"), ("pathways", "Open Abundant Pathways"),
                ("discipleship", "Open Abundant Pathways"), ("watch", "Open Watch"),
                ("media", "Open Media Library"), ("merch", "Open Merch"),
                ("store", "Open Merch"), ("shop", "Open Merch"),
                ("cafe", "Open Cafe"), ("coffee", "Open Cafe"),
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

        return SolomonChatResponse(
            response=clean_response,
            session_id=session_id,
            data=None,
            actions=actions,
            pending_action=pending_action
        )
    except Exception as e:
        logger.error(f"Solomon AI error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Solomon AI error: {str(e)}")


@router.post("/solomon/chat/stream")
async def solomon_chat_stream(request: Request):
    """Streaming chat with Solomon AI — returns Server-Sent Events for real-time typing effect."""
    body = await request.json()
    message = (body.get("message") or "").strip()
    session_id = body.get("session_id") or str(uuid.uuid4())

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user = await _get_user_safe(request)
    user_role = user.get("role") if user else None

    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Solomon AI is not configured")

    if user_role == "platform_admin":
        from core.helpers_ai import build_platform_admin_context
        full_system_prompt = await build_platform_admin_context()
    else:
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

    async def generate_sse():
        try:
            user_message = UserMessage(text=message)
            response_text = await chat.send_message(user_message)

            # Stream word-by-word for typing effect
            words = response_text.split(' ')
            accumulated = ""
            for i, word in enumerate(words):
                accumulated += (" " if i > 0 else "") + word
                chunk = json.dumps({"type": "chunk", "content": word + (" " if i < len(words) - 1 else ""), "session_id": session_id})
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.02)  # ~50 words/sec typing speed

            # Parse actions from full response
            clean_response, action_data = _parse_action_from_response(response_text)

            # Store conversation
            await db.solomon_conversations.update_one(
                {"session_id": session_id},
                {
                    "$push": {"messages": {"$each": [
                        {"role": "user", "content": message, "timestamp": datetime.now(timezone.utc).isoformat()},
                        {"role": "assistant", "content": clean_response, "timestamp": datetime.now(timezone.utc).isoformat()}
                    ]}},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}
                },
                upsert=True
            )

            done = json.dumps({"type": "done", "session_id": session_id, "full_response": clean_response})
            yield f"data: {done}\n\n"
        except Exception as e:
            error = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error}\n\n"

    return StreamingResponse(generate_sse(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    })


@router.post("/solomon/tts")
async def solomon_text_to_speech(request: Request):
    """Text-to-Speech scaffold — returns audio URL or signals client to use Web Speech API."""
    body = await request.json()
    text = (body.get("text") or "").strip()
    voice = body.get("voice", "en-GB")  # Default: UK English

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Scaffold: Signal client to use Web Speech API with UK English
    # When ElevenLabs or OpenAI TTS is integrated, this will return an audio URL
    return {
        "method": "web_speech_api",
        "voice": voice,
        "text": text,
        "message": "TTS via browser Web Speech API. Server-side TTS (ElevenLabs) coming soon."
    }




@router.post("/solomon/execute-action")
async def execute_solomon_action(request: Request, payload: ExecuteActionRequest):
    """Execute a confirmed action from Solomon AI conversation."""
    user = await _get_user_safe(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to execute actions")

    user_id = user.get("user_id")
    tenant_id = user.get("tenant_id", DEFAULT_TENANT_ID)

    result = await action_executor.execute_action(
        action_type=payload.action_type,
        params=payload.params,
        user_id=user_id,
        tenant_id=tenant_id,
    )

    # Log the action in conversation
    await db.solomon_conversations.update_one(
        {"session_id": payload.session_id},
        {
            "$push": {
                "messages": {
                    "role": "system",
                    "content": f"Action executed: {payload.action_type} — {result.get('message', '')}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            }
        },
    )

    return result


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


@router.post("/solomon/voice-transcribe")
async def voice_transcribe(request: Request):
    """Transcribe voice audio using OpenAI Whisper for long-form recordings (5-15 min)"""
    from fastapi import UploadFile
    import tempfile
    from pathlib import Path

    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Voice transcription not configured")

    form = await request.form()
    audio_file = form.get("audio")
    if not audio_file:
        raise HTTPException(status_code=400, detail="No audio file provided")

    # Save to temp file
    suffix = ".webm"
    content_type = getattr(audio_file, 'content_type', '')
    if 'wav' in content_type:
        suffix = ".wav"
    elif 'mp3' in content_type or 'mpeg' in content_type:
        suffix = ".mp3"
    elif 'mp4' in content_type or 'm4a' in content_type:
        suffix = ".m4a"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await audio_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from emergentintegrations.llm.openai import OpenAISpeechToText
        stt = OpenAISpeechToText(api_key=api_key)
        with open(tmp_path, 'rb') as f:
            response = await stt.transcribe(
                file=f,
                model="whisper-1",
                response_format="json",
                language="en",
                prompt="This is a business discussion about church management, SaaS metrics, fundraising, and platform strategy."
            )
        transcript = response.text if hasattr(response, 'text') else str(response)
        return {"transcript": transcript, "duration_seconds": len(content) / 16000}
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        import os as _os
        _os.unlink(tmp_path)


@router.post("/solomon/generate-report")
async def generate_report(request: Request):
    """Generate a downloadable report (PDF/Excel) from Solomon AI"""
    user = await _get_user_safe(request)
    if not user or user.get("role") != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform admin access required")

    body = await request.json()
    report_type = body.get("report_type", "investor_summary")
    fmt = body.get("format", "pdf")
    title = body.get("title", "Solomon AI Report")

    # Build report data from cache/DB
    cached = await db.platform_stats_cache.find_one({"id": "global"}, {"_id": 0})
    if not cached:
        cached = await db.platform_stats_cache.find_one({}, {"_id": 0})

    campuses = cached.get("campus_breakdown", []) if cached else []
    giving = cached.get("giving", {}) if cached else {}
    fees = cached.get("fees", {}) if cached else {}
    platform = cached.get("platform", {}) if cached else {}
    txns = cached.get("transactions", {}) if cached else {}
    donors_data = cached.get("donors", {}) if cached else {}

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    if fmt == "csv":
        # Generate CSV
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == "church_performance":
            writer.writerow(["Church", "All-Time Giving", "Fees Earned", "Members", "Active Donors", "Active %", "Health"])
            for c in campuses:
                active_pct = (c.get("active_donors", 0) / max(c.get("members", 1), 1)) * 100
                writer.writerow([c.get("name"), f"${c.get('giving', 0):,.2f}", f"${c.get('fees', 0):,.2f}",
                                c.get("members", 0), c.get("active_donors", 0), f"{active_pct:.1f}%", c.get("health", "N/A")])
        elif report_type == "donor_analysis":
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Donors", donors_data.get("total", 0)])
            writer.writerow(["Active (90d)", donors_data.get("active_90d", 0)])
            writer.writerow(["Recurring", donors_data.get("recurring", 0)])
            writer.writerow(["Avg Gift", f"${donors_data.get('avg_gift', 0):,.2f}"])
            writer.writerow(["Platform GMV", f"${giving.get('all_time', 0):,.2f}"])
        else:
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Platform GMV (All-Time)", f"${giving.get('all_time', 0):,.2f}"])
            writer.writerow(["Total Revenue (Fees)", f"${fees.get('all_time', 0):,.2f}"])
            writer.writerow(["Processing MRR", f"${platform.get('processing_mrr', 0):,.2f}"])
            writer.writerow(["Total ARR", f"${platform.get('arr', 0):,.2f}"])
            writer.writerow(["Churches", len(campuses)])
            writer.writerow(["Total Members", platform.get("total_members", 0)])
            writer.writerow(["Total Transactions", txns.get("total", 0)])
            writer.writerow(["Avg Transaction", f"${txns.get('avg_amount', 0):,.2f}"])
            writer.writerow([])
            writer.writerow(["Church Portfolio Breakdown"])
            writer.writerow(["Church", "All-Time Giving", "Fees", "Members", "Active Donors"])
            for c in campuses:
                writer.writerow([c.get("name"), f"${c.get('giving', 0):,.2f}", f"${c.get('fees', 0):,.2f}",
                                c.get("members", 0), c.get("active_donors", 0)])

        csv_content = output.getvalue()
        report_id = str(uuid.uuid4())[:8]
        filename = f"solomon_{report_type}_{now.strftime('%Y%m%d')}_{report_id}.csv"

        # Store in DB for download
        await db.generated_reports.insert_one({
            "id": report_id,
            "filename": filename,
            "content": csv_content,
            "content_type": "text/csv",
            "report_type": report_type,
            "generated_at": now.isoformat(),
            "generated_by": user.get("user_id"),
        })

        return {
            "success": True,
            "download_url": f"/solomon/download-report/{report_id}",
            "filename": filename,
            "report_type": report_type,
            "format": "csv"
        }

    # Default: generate markdown report (can be rendered as PDF client-side)
    report_md = f"# {title}\n\n"
    report_md += f"**Generated:** {now.strftime('%B %d, %Y at %I:%M %p UTC')}\n"
    report_md += f"**Prepared by:** Solomon AI Platform Analytics\n\n"

    if report_type == "investor_summary":
        report_md += "## Executive Summary\n\n"
        report_md += f"Solomon AI is a next-generation church management and payment processing platform "
        report_md += f"serving **{len(campuses)} churches** with **{platform.get('total_members', 0):,} members** "
        report_md += f"and **${giving.get('all_time', 0):,.0f} in all-time GMV**.\n\n"
        report_md += "## Key Metrics\n\n"
        report_md += f"| Metric | Value |\n|---|---|\n"
        report_md += f"| Platform GMV | ${giving.get('all_time', 0):,.0f} |\n"
        report_md += f"| Total Revenue | ${fees.get('all_time', 0):,.0f} |\n"
        report_md += f"| Processing MRR | ${platform.get('processing_mrr', 0):,.0f} |\n"
        report_md += f"| ARR | ${platform.get('arr', 0):,.0f} |\n"
        report_md += f"| Churches | {len(campuses)} |\n"
        report_md += f"| Total Members | {platform.get('total_members', 0):,} |\n"
        report_md += f"| Total Transactions | {txns.get('total', 0):,} |\n"
        report_md += f"| Avg Transaction | ${txns.get('avg_amount', 0):,.2f} |\n\n"
        report_md += "## Church Portfolio\n\n"
        report_md += "| Church | All-Time Giving | Fees | Members | Active Donors |\n"
        report_md += "|---|---|---|---|---|\n"
        for c in campuses:
            report_md += f"| {c.get('name', '')} | ${c.get('giving', 0):,.0f} | ${c.get('fees', 0):,.0f} | {c.get('members', 0):,} | {c.get('active_donors', 0):,} |\n"
    else:
        report_md += f"## {report_type.replace('_', ' ').title()}\n\n"
        report_md += f"Platform GMV: ${giving.get('all_time', 0):,.0f}\n"
        report_md += f"Revenue: ${fees.get('all_time', 0):,.0f}\n"

    report_id = str(uuid.uuid4())[:8]
    filename = f"solomon_{report_type}_{now.strftime('%Y%m%d')}_{report_id}.md"
    await db.generated_reports.insert_one({
        "id": report_id,
        "filename": filename,
        "content": report_md,
        "content_type": "text/markdown",
        "report_type": report_type,
        "generated_at": now.isoformat(),
        "generated_by": user.get("user_id"),
    })

    return {
        "success": True,
        "download_url": f"/solomon/download-report/{report_id}",
        "filename": filename,
        "report_type": report_type,
        "format": "markdown",
        "content_preview": report_md[:500]
    }


@router.get("/solomon/download-report/{report_id}")
async def download_report(report_id: str):
    """Download a generated report"""
    from fastapi.responses import Response
    report = await db.generated_reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    content_type = report.get("content_type", "text/plain")
    filename = report.get("filename", f"report_{report_id}")
    content = report.get("content", "")

    return Response(
        content=content.encode("utf-8"),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/solomon/generate-deliverable")
async def generate_deliverable(request: Request):
    """Generate PPTX/DOCX/PDF deliverables — scaffold with honest status.
    Per the Honesty Pact: if we can generate it, we do. If not, we say so."""
    user = await _get_user_safe(request)
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")

    body = await request.json()
    deliverable_type = body.get("type", "pdf")  # pdf, pptx, docx, xlsx
    title = body.get("title", "Solomon AI Report")
    content = body.get("content", "")

    if deliverable_type == "pdf":
        # PDF generation is supported via reportlab (already in requirements)
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            import io as _io

            buf = _io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = [
                Paragraph(title, styles["Title"]),
                Spacer(1, 12),
                Paragraph(content.replace("\n", "<br/>"), styles["Normal"]),
            ]
            doc.build(elements)

            report_id = str(uuid.uuid4())[:8]
            filename = f"solomon_{report_id}.pdf"
            pdf_bytes = buf.getvalue()

            await db.generated_reports.insert_one({
                "id": report_id,
                "filename": filename,
                "content_bytes": pdf_bytes,
                "content_type": "application/pdf",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generated_by": user.get("user_id"),
            })

            from fastapi.responses import Response
            return Response(content=pdf_bytes, media_type="application/pdf",
                           headers={"Content-Disposition": f'attachment; filename="{filename}"'})
        except ImportError:
            return {"status": "coming_soon", "type": "pdf",
                    "message": "PDF generation requires reportlab. Install with: pip install reportlab"}

    elif deliverable_type in ("pptx", "docx", "xlsx"):
        # Honest scaffold — these require python-pptx, python-docx, openpyxl
        lib_map = {"pptx": "python-pptx", "docx": "python-docx", "xlsx": "openpyxl"}
        return {
            "status": "coming_soon",
            "type": deliverable_type,
            "message": f"{deliverable_type.upper()} generation is scaffolded. Requires {lib_map[deliverable_type]} microservice.",
            "workaround": "Use CSV export (available now) and convert to the desired format, or request PDF format which is fully supported."
        }

    return {"status": "unsupported", "message": f"Format '{deliverable_type}' is not supported. Use: pdf, csv, pptx, docx, xlsx"}
