"""Reservation logic with row-level locking. Shared by REST and (later) MCP.

reserve_unit() is the concurrency core: it locks the unit row, verifies
availability, flips status, writes a time-limited hold, and audit-logs the
source (portal|mcp). Two simultaneous reserves cannot both succeed.
"""
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models import models as m
from app.services.permissions import get_permitted_block_ids, is_block_allowed

HOLD_MINUTES = 10


class ReservationError(Exception):
    """Raised when a reservation cannot be granted."""


def reserve_unit(db: Session, agent: m.Agent, unit_id: int,
                 source: str = "portal") -> dict:
    """Place a time-limited hold on a unit. Raises ReservationError on failure.

    source: 'portal' or 'mcp' — recorded in the audit log so we can show
    which door the action came through.
    """
    unit = (
        db.query(m.Unit)
        .filter(m.Unit.id == unit_id)
        .with_for_update()
        .first()
    )
    if unit is None:
        raise ReservationError("Unit not found")

    permitted = get_permitted_block_ids(db, agent)
    if not is_block_allowed(permitted, unit.block_id):
        raise ReservationError("Not permitted to reserve this unit")

    if unit.status != "available":
        raise ReservationError(f"Unit is {unit.status}, not available")

    unit.status = "reserved"
    unit.version += 1
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=HOLD_MINUTES)

    reservation = m.Reservation(
        unit_id=unit.id, agent_id=agent.id, status="active",
        expires_at=expires_at,
    )
    db.add(reservation)
    db.add(m.AuditLog(
        actor_id=agent.id, action="reserve", unit_id=unit.id, source=source,
        detail_json=json.dumps({"expires_at": expires_at.isoformat()}),
    ))
    db.commit()
    db.refresh(unit)

    return {
        "unit_id": unit.id,
        "block_id": unit.block_id,
        "status": unit.status,
        "version": unit.version,
        "reserved_by": agent.id,
        "expires_at": expires_at.isoformat(),
        "source": source,
    }


def release_expired(db: Session) -> list[tuple[int, int, int]]:
    """Flip expired holds back to available.

    Returns list of (unit_id, block_id, version) for broadcasting.
    """
    now = datetime.now(timezone.utc)
    expired = (
        db.query(m.Reservation)
        .filter(m.Reservation.status == "active",
                m.Reservation.expires_at < now)
        .all()
    )
    affected: list[tuple[int, int, int]] = []
    for r in expired:
        unit = (
            db.query(m.Unit).filter(m.Unit.id == r.unit_id)
            .with_for_update().first()
        )
        if unit and unit.status == "reserved":
            unit.status = "available"
            unit.version += 1
            affected.append((unit.id, unit.block_id, unit.version))
        r.status = "expired"
        db.add(m.AuditLog(
            actor_id=None, action="hold_expired", unit_id=r.unit_id,
            source="system", detail_json=None,
        ))
    db.commit()
    return affected