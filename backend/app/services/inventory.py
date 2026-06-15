"""Inventory read logic, RBAC-scoped. Shared by REST and (later) MCP.

Every query is filtered through the permitted block-id set so an agent
only ever sees units in blocks they are allowed to access.
"""
from sqlalchemy.orm import Session
from app.models import models as m
from app.services.permissions import get_permitted_block_ids, ALL_BLOCKS


def _scoped_unit_query(db: Session, permitted):
    q = db.query(m.Unit).join(m.Block)
    if permitted != ALL_BLOCKS:
        if not permitted:
            # No permissions → no rows.
            return q.filter(m.Unit.id == -1)
        q = q.filter(m.Unit.block_id.in_(permitted))
    return q


def list_projects(db: Session, agent: m.Agent):
    permitted = get_permitted_block_ids(db, agent)
    if permitted == ALL_BLOCKS:
        return db.query(m.Project).all()
    if not permitted:
        return []
    proj_ids = (
        db.query(m.Block.project_id)
        .filter(m.Block.id.in_(permitted))
        .distinct()
    )
    return db.query(m.Project).filter(m.Project.id.in_(proj_ids)).all()


def list_units(db: Session, agent: m.Agent, project_id: int | None = None,
               status: str | None = None):
    permitted = get_permitted_block_ids(db, agent)
    q = _scoped_unit_query(db, permitted)
    if project_id is not None:
        q = q.filter(m.Block.project_id == project_id)
    if status is not None:
        q = q.filter(m.Unit.status == status)
    return q.order_by(m.Unit.id).all()


def inventory_summary(db: Session, agent: m.Agent, project_id: int):
    units = list_units(db, agent, project_id=project_id)
    counts = {"available": 0, "reserved": 0, "sold": 0}
    for u in units:
        counts[u.status] = counts.get(u.status, 0) + 1
    return counts