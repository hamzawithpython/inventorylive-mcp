"""Reservation endpoint — auth-protected, RBAC-enforced in the service."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_agent
from app.services import reservations as svc
from app.models import models as m

router = APIRouter(prefix="/api", tags=["reservations"])


@router.post("/units/{unit_id}/reserve")
def reserve(unit_id: int, db: Session = Depends(get_db),
            agent: m.Agent = Depends(get_current_agent)):
    try:
        return svc.reserve_unit(db, agent, unit_id, source="portal")
    except svc.ReservationError as e:
        raise HTTPException(status_code=409, detail=str(e))