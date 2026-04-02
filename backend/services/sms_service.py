"""Solomon AI — SMS Service (Twilio with Graceful Degradation)
If Twilio keys are present, sends real SMS. Otherwise, logs to sms_logs collection.
"""
import os
import re
import logging
from datetime import datetime, timezone
from typing import Optional
from core import db, logger

TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.environ.get("TWILIO_PHONE_NUMBER")

_twilio_client = None

def _get_twilio():
    global _twilio_client
    if _twilio_client:
        return _twilio_client
    if TWILIO_SID and TWILIO_TOKEN:
        try:
            from twilio.rest import Client
            _twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
            logger.info("Twilio client initialized")
            return _twilio_client
        except ImportError:
            logger.warning("twilio package not installed — SMS will be logged only")
        except Exception as e:
            logger.warning(f"Twilio init failed: {e}")
    return None


async def send_sms(to: str, message: str, tenant_id: str = "", context: str = "general") -> dict:
    """Send SMS. If Twilio keys present, send real SMS. Otherwise log to DB."""
    log_entry = {
        "to": to,
        "message": message,
        "tenant_id": tenant_id,
        "context": context,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    client = _get_twilio()
    if client and TWILIO_PHONE:
        try:
            msg = client.messages.create(body=message, from_=TWILIO_PHONE, to=to)
            log_entry["status"] = "sent"
            log_entry["sid"] = msg.sid
            log_entry["provider"] = "twilio"
            logger.info(f"SMS sent to {to}: {message[:50]}...")
        except Exception as e:
            log_entry["status"] = "failed"
            log_entry["error"] = str(e)
            log_entry["provider"] = "twilio"
            logger.error(f"SMS send failed to {to}: {e}")
    else:
        log_entry["status"] = "logged"
        log_entry["provider"] = "none"
        logger.info(f"SMS logged (no Twilio keys): to={to}, msg={message[:50]}...")

    await db.sms_logs.insert_one(log_entry)
    return {"status": log_entry["status"], "to": to}


async def send_bulk_sms(recipients: list, message: str, tenant_id: str = "", context: str = "bulk") -> dict:
    """Send SMS to multiple recipients."""
    results = {"sent": 0, "logged": 0, "failed": 0}
    for phone in recipients:
        r = await send_sms(phone, message, tenant_id, context)
        results[r["status"]] = results.get(r["status"], 0) + 1
    return results


def parse_text_to_give(body: str) -> dict:
    """Parse text-to-give message. Formats: 'GIVE 50', 'GIVE 100 MISSIONS', '$25', '50'."""
    body = body.strip().upper()
    result = {"amount": None, "fund": "General Fund", "valid": False}

    patterns = [
        r"^GIVE\s+\$?(\d+(?:\.\d{2})?)\s*(.*)?$",
        r"^\$(\d+(?:\.\d{2})?)$",
        r"^(\d+(?:\.\d{2})?)$",
    ]
    for p in patterns:
        m = re.match(p, body)
        if m:
            result["amount"] = float(m.group(1))
            fund = m.group(2).strip() if m.lastindex >= 2 and m.group(2) else ""
            if fund:
                fund_map = {
                    "GENERAL": "General Fund", "BUILDING": "Building Fund",
                    "MISSIONS": "Missions", "YOUTH": "Youth Ministry",
                    "BENEVOLENCE": "Benevolence", "KIDS": "Kids Ministry",
                }
                result["fund"] = fund_map.get(fund, fund.title() + " Fund")
            result["valid"] = result["amount"] > 0
            break
    return result


async def handle_incoming_sms(from_number: str, body: str, tenant_id: str = "") -> dict:
    """Process incoming SMS (text-to-give flow)."""
    import uuid

    # Log the incoming message
    await db.sms_logs.insert_one({
        "direction": "incoming",
        "from": from_number,
        "body": body,
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    parsed = parse_text_to_give(body)

    if body.strip().upper() in ("HELP", "INFO", "?"):
        reply = "Solomon AI Giving: Text 'GIVE 50' to give $50 to General Fund. Text 'GIVE 100 MISSIONS' for a specific fund. Text 'STOP' to unsubscribe."
        await send_sms(from_number, reply, tenant_id, "text-to-give-help")
        return {"action": "help", "reply": reply}

    if body.strip().upper() == "STOP":
        await send_sms(from_number, "You have been unsubscribed from Solomon AI text notifications.", tenant_id, "unsubscribe")
        return {"action": "unsubscribe"}

    if not parsed["valid"]:
        reply = "Sorry, I didn't understand. Text 'GIVE 50' to donate $50, or 'HELP' for instructions."
        await send_sms(from_number, reply, tenant_id, "text-to-give-error")
        return {"action": "parse_error", "reply": reply}

    # Look up member by phone
    clean_phone = re.sub(r"\D", "", from_number)[-10:]
    person = await db.people.find_one(
        {"$or": [
            {"mobile_phone": {"$regex": clean_phone}},
            {"phone": {"$regex": clean_phone}},
        ], "tenant_id": tenant_id},
        {"_id": 0}
    )

    if not person:
        reply = f"We couldn't find your account. Please register at our website first, then try again."
        await send_sms(from_number, reply, tenant_id, "text-to-give-no-member")
        return {"action": "no_member", "reply": reply}

    # Check for saved payment method
    payment = await db.payment_methods.find_one(
        {"person_id": person.get("id"), "is_default": True},
        {"_id": 0}
    )

    if not payment:
        reply = f"Hi {person.get('first_name', 'there')}! You don't have a saved payment method. Please add one at our website first."
        await send_sms(from_number, reply, tenant_id, "text-to-give-no-payment")
        return {"action": "no_payment", "reply": reply, "person_id": person.get("id")}

    # Create donation
    donation = {
        "id": str(uuid.uuid4()),
        "transaction_id": f"txt_{uuid.uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "person_id": person.get("id"),
        "person_name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
        "person_email": person.get("email", ""),
        "amount": parsed["amount"],
        "fund_name": parsed["fund"],
        "payment_method": f"{payment.get('card_brand', 'Card')} ****{payment.get('card_last_four', '****')}",
        "source": "text_to_give",
        "status": "pending",
        "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.donations.insert_one(donation)

    reply = f"Thank you, {person.get('first_name', '')}! Your ${parsed['amount']:.2f} gift to {parsed['fund']} has been received. God bless!"
    await send_sms(from_number, reply, tenant_id, "text-to-give-confirmation")

    return {
        "action": "donation_created",
        "donation_id": donation["id"],
        "amount": parsed["amount"],
        "fund": parsed["fund"],
        "person_id": person.get("id"),
        "reply": reply,
    }
