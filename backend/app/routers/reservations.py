"""Reservation endpoint — reserves, then broadcasts the live change."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_agent
from app.services import reservations as svc
from app.services.ws_manager import manager
from app.models import models as m

router = APIRouter(prefix="/api", tags=["reservations"])


@router.post("/units/{unit_id}/reserve")
async def reserve(unit_id: int, db: Session = Depends(get_db),
                  agent: m.Agent = Depends(get_current_agent)):
    try:
        result = svc.reserve_unit(db, agent, unit_id, source="portal")
    except svc.ReservationError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Push the live change to every permitted connection.
    await manager.broadcast_unit_change(result["block_id"], {
        "type": "unit_changed",
        "unit_id": result["unit_id"],
        "status": result["status"],
        "version": result["version"],
        "by": result["reserved_by"],
        "source": result["source"],
    })
    return result