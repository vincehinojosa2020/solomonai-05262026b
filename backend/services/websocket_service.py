"""Solomon AI — WebSocket Real-Time Service
Replaces polling with push-based real-time updates.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("solomon.websocket")


class ConnectionManager:
    """Manages WebSocket connections by tenant and user."""

    def __init__(self):
        self.active: Dict[str, Dict[str, WebSocket]] = {}  # {tenant_id: {user_id: ws}}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, tenant_id: str, user_id: str):
        await websocket.accept()
        async with self._lock:
            if tenant_id not in self.active:
                self.active[tenant_id] = {}
            # Close old connection if exists
            old = self.active[tenant_id].get(user_id)
            if old:
                try:
                    await old.close()
                except Exception:
                    pass
            self.active[tenant_id][user_id] = websocket
        logger.info(f"WS connected: {tenant_id}/{user_id} (total: {self.count()})")

    async def disconnect(self, tenant_id: str, user_id: str):
        async with self._lock:
            if tenant_id in self.active:
                self.active[tenant_id].pop(user_id, None)
                if not self.active[tenant_id]:
                    del self.active[tenant_id]
        logger.info(f"WS disconnected: {tenant_id}/{user_id} (total: {self.count()})")

    def count(self) -> int:
        return sum(len(users) for users in self.active.values())

    async def send_to_user(self, tenant_id: str, user_id: str, event: str, data: dict):
        ws = self.active.get(tenant_id, {}).get(user_id)
        if ws:
            try:
                await ws.send_json({"event": event, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()})
            except Exception:
                await self.disconnect(tenant_id, user_id)

    async def broadcast_to_tenant(self, tenant_id: str, event: str, data: dict):
        users = self.active.get(tenant_id, {})
        msg = json.dumps({"event": event, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()})
        disconnected = []
        for uid, ws in users.items():
            try:
                await ws.send_text(msg)
            except Exception:
                disconnected.append(uid)
        for uid in disconnected:
            await self.disconnect(tenant_id, uid)

    async def broadcast_to_admins(self, tenant_id: str, event: str, data: dict, admin_ids: set = None):
        """Broadcast only to admin users of a tenant."""
        users = self.active.get(tenant_id, {})
        msg = json.dumps({"event": event, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()})
        disconnected = []
        for uid, ws in users.items():
            if admin_ids is None or uid in admin_ids:
                try:
                    await ws.send_text(msg)
                except Exception:
                    disconnected.append(uid)
        for uid in disconnected:
            await self.disconnect(tenant_id, uid)


# Singleton
ws_manager = ConnectionManager()


# Event emitters for use in other routes
async def emit_new_donation(tenant_id: str, donation_data: dict):
    await ws_manager.broadcast_to_tenant(tenant_id, "new_donation", donation_data)

async def emit_new_order(tenant_id: str, order_data: dict):
    await ws_manager.broadcast_to_tenant(tenant_id, "new_order", order_data)

async def emit_new_registration(tenant_id: str, reg_data: dict):
    await ws_manager.broadcast_to_tenant(tenant_id, "new_registration", reg_data)

async def emit_group_update(tenant_id: str, group_data: dict):
    await ws_manager.broadcast_to_tenant(tenant_id, "group_update", group_data)

async def emit_content_update(tenant_id: str, content_data: dict):
    await ws_manager.broadcast_to_tenant(tenant_id, "content_update", content_data)

async def emit_checkin(tenant_id: str, checkin_data: dict):
    await ws_manager.broadcast_to_tenant(tenant_id, "new_checkin", checkin_data)
