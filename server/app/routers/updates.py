"""
WebSocket endpoint for real-time updates (push notifications).

Client connects to:  ws://<host>:<port>/api/updates/ws?token=<auth_token>

The server pushes JSON updates for:
  - updateNewMessage
  - updateEditMessage
  - updateDeleteMessages
  - updateReadHistoryOutbox
  - updateUserStatus
  - updateChatParticipantAdd
"""

import time

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import async_session
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.security import decode_access_token

router = APIRouter(prefix="/api/updates", tags=["updates"])


@router.websocket("/ws")
async def websocket_updates(websocket: WebSocket, token: str = Query(...)):
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("user_id")
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    await updates_manager.connect(user_id, websocket)

    # Mark user online
    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_online = True
            await db.commit()

    try:
        while True:
            # Keep connection alive; client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        await updates_manager.disconnect(user_id, websocket)
        # Mark user offline
        async with async_session() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.is_online = False
                user.last_seen = int(time.time())
                await db.commit()
