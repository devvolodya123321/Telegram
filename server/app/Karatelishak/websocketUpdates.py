import time

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.updates import updates_manager
from app.utils.security import decode_access_token

router = APIRouter(tags=["updates"])


@router.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("user_id")
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    await updates_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        await updates_manager.disconnect(user_id, websocket)
