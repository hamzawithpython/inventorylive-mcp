"""WebSocket connection hub with permission-aware fan-out.

Each connection caches the agent and their permitted block-id set (resolved
once at connect). Events are only delivered to connections allowed to see the
affected unit''s block — the same RBAC rule used by REST and reservations.
"""
import asyncio
from dataclasses import dataclass, field
from fastapi import WebSocket
from app.models import models as m
from app.services.permissions import is_block_allowed, ALL_BLOCKS


@dataclass
class Connection:
    websocket: WebSocket
    agent_id: int
    permitted: object  # set[int] or ALL_BLOCKS sentinel


@dataclass
class ConnectionManager:
    connections: list[Connection] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def connect(self, websocket: WebSocket, agent: m.Agent, permitted):
        await websocket.accept()
        async with self._lock:
            self.connections.append(
                Connection(websocket=websocket, agent_id=agent.id,
                           permitted=permitted)
            )

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self.connections = [
                c for c in self.connections if c.websocket is not websocket
            ]

    async def broadcast_unit_change(self, block_id: int, payload: dict):
        """Send payload only to connections permitted to see this block."""
        async with self._lock:
            targets = [
                c for c in self.connections
                if is_block_allowed(c.permitted, block_id)
            ]
        dead = []
        for c in targets:
            try:
                await c.websocket.send_json(payload)
            except Exception:  # noqa: BLE001 — connection dropped
                dead.append(c.websocket)
        for ws in dead:
            await self.disconnect(ws)


# Single shared instance.
manager = ConnectionManager()