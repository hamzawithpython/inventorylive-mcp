"""Inventory read logic. Shared by REST (now) and MCP (Phase 7).

Phase 1 is read-only and unscoped; RBAC filtering arrives in Phase 2.
"""
from sqlalchemy.orm import Session
from app.models import models as m


def list_projects(db: Session):
    return db.query(m.Project).all()


def list_units(db: Session, project_id: int | None = None,
               status: str | None = None):
    q = db.query(m.Unit).join(m.Block)
    if project_id is not None:
        q = q.filter(m.Block.project_id == project_id)
    if status is not None:
        q = q.filter(m.Unit.status == status)
    return q.order_by(m.Unit.id).all()


def inventory_summary(db: Session, project_id: int):
    units = list_units(db, project_id=project_id)
    counts = {"available": 0, "reserved": 0, "sold": 0}
    for u in units:
        counts[u.status] = counts.get(u.status, 0) + 1
    return counts