"""WebSocket endpoint. Auth via ?token= query param (WS can''t use headers easily).

Connect:  ws://host/ws?token=<JWT>
Server pushes {type: "unit_changed", ...} events for permitted blocks only.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import decode_token
from app.services.ws_manager import manager
from app.services.permissions import get_permitted_block_ids
from app.models import models as m

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, token: str = "",
                      db: Session = Depends(get_db)):
    payload = decode_token(token)
    if payload is None or "sub" not in payload:
        await websocket.close(code=4401)  # custom: unauthorized
        return
    agent = db.query(m.Agent).filter(m.Agent.id == int(payload["sub"])).first()
    if agent is None:
        await websocket.close(code=4401)
        return

    permitted = get_permitted_block_ids(db, agent)
    await manager.connect(websocket, agent, permitted)
    try:
        # We don''t expect client messages; just keep the socket open.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)