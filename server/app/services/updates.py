import asyncio
import json
import time
from collections import defaultdict

from fastapi import WebSocket


class UpdatesManager:
    """Manages real-time update delivery to connected clients via WebSocket."""

    def __init__(self) -> None:
        # user_id -> list of active websocket connections
        self._connections: dict[int, list[WebSocket]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[user_id].append(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(user_id, [])
            if websocket in conns:
                conns.remove(websocket)
            if not conns:
                self._connections.pop(user_id, None)

    async def send_update(self, user_id: int, update: dict) -> None:
        update.setdefault("date", int(time.time()))
        async with self._lock:
            conns = list(self._connections.get(user_id, []))
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(update))
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    conns = self._connections.get(user_id, [])
                    if ws in conns:
                        conns.remove(ws)

    async def broadcast_to_chat_members(
        self, member_ids: list[int], update: dict
    ) -> None:
        for uid in member_ids:
            await self.send_update(uid, update)

    def is_online(self, user_id: int) -> bool:
        return bool(self._connections.get(user_id))


updates_manager = UpdatesManager()
