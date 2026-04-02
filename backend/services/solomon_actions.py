"""Solomon AI — Action Executor Service
Handles execution of real system actions triggered by conversational AI intent.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid
import logging

from core import db, DEFAULT_TENANT_ID

logger = logging.getLogger(__name__)

SUPPORTED_ACTIONS = {
    "cafe_order": {
        "label": "Cafe Order",
        "description": "Order items from Abundant Cafe",
        "required_params": ["items"],
        "optional_params": ["pickup_time", "notes"],
    },
    "merch_order": {
        "label": "Merch Order",
        "description": "Order merchandise from the church store",
        "required_params": ["items"],
        "optional_params": ["notes"],
    },
    "donation": {
        "label": "Donation",
        "description": "Make a one-time gift",
        "required_params": ["amount"],
        "optional_params": ["fund", "note"],
    },
    "recurring_giving": {
        "label": "Recurring Giving",
        "description": "Set up recurring donations",
        "required_params": ["amount", "frequency"],
        "optional_params": ["fund"],
    },
    "event_registration": {
        "label": "Event Registration",
        "description": "Register for a church event",
        "required_params": ["event_name"],
        "optional_params": [],
    },
    "group_join": {
        "label": "Join Group",
        "description": "Join a church group or ministry",
        "required_params": ["group_name"],
        "optional_params": [],
    },
    "checkin": {
        "label": "Kids Check-In",
        "description": "Check in children for service",
        "required_params": ["child_name"],
        "optional_params": ["classroom"],
    },
}


class SolomonActionExecutor:
    """Executes system actions parsed from Solomon AI conversations."""

    async def execute_action(
        self,
        action_type: str,
        params: Dict[str, Any],
        user_id: str,
        tenant_id: str,
    ) -> Dict[str, Any]:
        handlers = {
            "cafe_order": self._create_cafe_order,
            "merch_order": self._create_merch_order,
            "donation": self._create_donation,
            "recurring_giving": self._create_recurring,
            "event_registration": self._register_event,
            "group_join": self._join_group,
            "checkin": self._checkin_child,
        }
        handler = handlers.get(action_type)
        if not handler:
            return {"success": False, "message": f"Unknown action: {action_type}"}
        try:
            return await handler(params, user_id, tenant_id)
        except Exception as e:
            logger.error(f"Action execution error ({action_type}): {e}")
            return {"success": False, "message": str(e)}

    async def _create_cafe_order(
        self, params: Dict, user_id: str, tenant_id: str
    ) -> Dict:
        items_raw = params.get("items", [])
        if isinstance(items_raw, str):
            items_raw = [{"name": items_raw, "quantity": 1, "price": 5.00}]

        items = []
        total = 0
        for item in items_raw:
            name = item.get("name", "Coffee")
            qty = int(item.get("quantity", 1))
            price = float(item.get("price", 5.00))
            items.append({"name": name, "quantity": qty, "price": price})
            total += price * qty

        order = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": user_id,
            "items": items,
            "pickup_time": params.get("pickup_time", "ASAP"),
            "notes": params.get("notes", "Ordered via Solomon AI"),
            "total": round(total, 2),
            "status": "placed",
            "source": "solomon_ai",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.cafe_orders.insert_one(order)
        item_names = ", ".join(f"{i['quantity']}x {i['name']}" for i in items)
        return {
            "success": True,
            "message": f"Cafe order placed! {item_names} — Total: ${order['total']:.2f}. Pickup: {order['pickup_time']}",
            "order_id": order["id"],
            "navigate": "/portal/cafe",
        }

    async def _create_merch_order(
        self, params: Dict, user_id: str, tenant_id: str
    ) -> Dict:
        items_raw = params.get("items", [])
        if isinstance(items_raw, str):
            items_raw = [{"name": items_raw, "quantity": 1, "price": 25.00}]

        items = []
        total = 0
        for item in items_raw:
            name = item.get("name", "T-Shirt")
            qty = int(item.get("quantity", 1))
            price = float(item.get("price", 25.00))
            size = item.get("size", "M")
            items.append({"name": name, "quantity": qty, "price": price, "size": size})
            total += price * qty

        order = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": user_id,
            "items": items,
            "subtotal": round(total, 2),
            "total": round(total, 2),
            "status": "placed",
            "source": "solomon_ai",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.merch_orders.insert_one(order)
        item_names = ", ".join(f"{i['quantity']}x {i['name']}" for i in items)
        return {
            "success": True,
            "message": f"Merch order placed! {item_names} — Total: ${order['total']:.2f}",
            "order_id": order["id"],
            "navigate": "/portal/merch",
        }

    async def _create_donation(
        self, params: Dict, user_id: str, tenant_id: str
    ) -> Dict:
        amount = float(params.get("amount", 0))
        if amount <= 0:
            return {"success": False, "message": "Donation amount must be positive"}

        fund = params.get("fund", "General Fund")
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        person_name = user.get("name", "") if user else ""
        person_email = user.get("email", "") if user else ""

        donation = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "person_id": user_id,
            "person_name": person_name,
            "person_email": person_email,
            "amount": round(amount, 2),
            "base_amount": round(amount, 2),
            "processing_fee": 0,
            "fees_covered_by_donor": False,
            "fund": fund,
            "fund_name": fund,
            "fund_id": "general",
            "frequency": "one_time",
            "donation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "payment_method": "solomonpay",
            "transaction_id": f"sol_txn_{uuid.uuid4().hex[:12]}",
            "source": "solomon_ai",
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.donations.insert_one(donation)
        return {
            "success": True,
            "message": f"Thank you for your ${amount:.2f} gift to {fund}! Your generosity makes a difference.",
            "donation_id": donation["id"],
            "navigate": "/portal/give",
        }

    async def _create_recurring(
        self, params: Dict, user_id: str, tenant_id: str
    ) -> Dict:
        amount = float(params.get("amount", 0))
        if amount <= 0:
            return {"success": False, "message": "Amount must be positive"}

        frequency = params.get("frequency", "weekly")
        fund = params.get("fund", "General Fund")
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        person_name = user.get("name", "") if user else ""
        person_email = user.get("email", "") if user else ""

        schedule = {
            "id": f"rec_{uuid.uuid4().hex[:12]}",
            "tenant_id": tenant_id,
            "person_id": user_id,
            "person_name": person_name,
            "person_email": person_email,
            "amount": round(amount, 2),
            "fund_id": "general",
            "fund_name": fund,
            "frequency": frequency,
            "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "next_charge_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "payment_method_id": None,
            "card_last_four": None,
            "card_brand": None,
            "status": "active",
            "is_active": True,
            "source": "solomon_ai",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_at": None,
        }
        await db.recurring_giving.insert_one(schedule)
        return {
            "success": True,
            "message": f"Recurring {frequency} gift of ${amount:.2f} to {fund} has been set up!",
            "schedule_id": schedule["id"],
            "navigate": "/portal/give",
        }

    async def _register_event(
        self, params: Dict, user_id: str, tenant_id: str
    ) -> Dict:
        event_name = params.get("event_name", "")
        if not event_name:
            return {"success": False, "message": "Event name is required"}

        event = await db.events.find_one(
            {
                "tenant_id": tenant_id,
                "$or": [
                    {"name": {"$regex": event_name, "$options": "i"}},
                    {"title": {"$regex": event_name, "$options": "i"}},
                ],
            },
            {"_id": 0},
        )
        if not event:
            available = await db.events.find(
                {"tenant_id": tenant_id}, {"_id": 0, "name": 1, "title": 1}
            ).to_list(10)
            names = ", ".join(e.get("name") or e.get("title", "?") for e in available) if available else "none"
            return {
                "success": False,
                "message": f"Could not find an event matching '{event_name}'. Available events: {names}",
            }

        event_display_name = event.get("name") or event.get("title", "Event")

        existing = await db.event_registrations.find_one(
            {"event_id": event["id"], "user_id": user_id}
        )
        if existing:
            return {
                "success": True,
                "message": f"You're already registered for {event_display_name}!",
                "navigate": "/portal/events",
            }

        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        registration = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "event_id": event["id"],
            "user_id": user_id,
            "user_name": user.get("name", "") if user else "",
            "user_email": user.get("email", "") if user else "",
            "source": "solomon_ai",
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.event_registrations.insert_one(registration)
        await db.events.update_one(
            {"id": event["id"]}, {"$inc": {"registration_count": 1}}
        )
        return {
            "success": True,
            "message": f"You're registered for {event_display_name}! See you there.",
            "navigate": "/portal/events",
        }

    async def _join_group(
        self, params: Dict, user_id: str, tenant_id: str
    ) -> Dict:
        group_name = params.get("group_name", "")
        if not group_name:
            return {"success": False, "message": "Group name is required"}

        group = await db.groups.find_one(
            {
                "tenant_id": tenant_id,
                "is_active": True,
                "name": {"$regex": group_name, "$options": "i"},
            },
            {"_id": 0},
        )
        if not group:
            available = await db.groups.find(
                {"tenant_id": tenant_id, "is_active": True},
                {"_id": 0, "name": 1},
            ).to_list(10)
            names = ", ".join(g["name"] for g in available) if available else "none"
            return {
                "success": False,
                "message": f"Could not find a group matching '{group_name}'. Available groups: {names}",
            }

        person = await db.people.find_one(
            {"tenant_id": tenant_id, "user_id": user_id}, {"_id": 0}
        )
        if not person:
            person = await db.people.find_one(
                {"tenant_id": tenant_id}, {"_id": 0}
            )
        person_id = person.get("id", user_id) if person else user_id

        existing = await db.group_members.find_one(
            {"group_id": group["id"], "person_id": person_id, "is_active": True}
        )
        if existing:
            return {
                "success": True,
                "message": f"You're already a member of {group['name']}!",
                "navigate": "/portal/groups",
            }

        membership = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "group_id": group["id"],
            "person_id": person_id,
            "role": "member",
            "is_active": True,
            "source": "solomon_ai",
            "joined_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.group_members.insert_one(membership)
        await db.groups.update_one(
            {"id": group["id"]}, {"$inc": {"member_count": 1}}
        )
        return {
            "success": True,
            "message": f"Welcome to {group['name']}! You've been added as a member.",
            "navigate": "/portal/groups",
        }

    async def _checkin_child(
        self, params: Dict, user_id: str, tenant_id: str
    ) -> Dict:
        child_name = params.get("child_name", "")
        if not child_name:
            return {"success": False, "message": "Child name is required"}

        child = await db.children.find_one(
            {
                "tenant_id": tenant_id,
                "parent_user_id": user_id,
                "name": {"$regex": child_name, "$options": "i"},
            },
            {"_id": 0},
        )
        if not child:
            children = await db.children.find(
                {"tenant_id": tenant_id, "parent_user_id": user_id},
                {"_id": 0, "name": 1},
            ).to_list(10)
            if children:
                names = ", ".join(c["name"] for c in children)
                return {
                    "success": False,
                    "message": f"Could not find '{child_name}'. Your children: {names}",
                }
            return {
                "success": False,
                "message": "No children found on your account. Please add them in the Kids section first.",
            }

        existing = await db.checkins.find_one(
            {"child_id": child["id"], "status": "checked_in"}, {"_id": 0}
        )
        if existing:
            return {
                "success": True,
                "message": f"{child['name']} is already checked in! Pickup code: {existing.get('pickup_code', 'N/A')}",
                "navigate": "/portal/kids",
            }

        import secrets
        import string
        pickup_code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        classroom = params.get("classroom", "Sunday School")

        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        checkin = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "child_id": child["id"],
            "child_name": child.get("name", child_name),
            "parent_user_id": user_id,
            "parent_name": user.get("name", "Parent") if user else "Parent",
            "parent_phone": user.get("phone", "") if user else "",
            "pickup_code": pickup_code,
            "classroom": classroom,
            "status": "checked_in",
            "source": "solomon_ai",
            "checked_in_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.checkins.insert_one(checkin)
        return {
            "success": True,
            "message": f"{child['name']} is checked in to {classroom}! Pickup code: {pickup_code}",
            "pickup_code": pickup_code,
            "navigate": "/portal/kids",
        }


# Singleton
action_executor = SolomonActionExecutor()
