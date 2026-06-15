"""Inventory endpoints — now auth-protected and RBAC-scoped."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_agent
from app.services import inventory as svc
from app.schemas import ProjectOut, UnitOut
from app.models import models as m

router = APIRouter(prefix="/api", tags=["inventory"])


@router.get("/projects", response_model=list[ProjectOut])
def get_projects(db: Session = Depends(get_db),
                 agent: m.Agent = Depends(get_current_agent)):
    return svc.list_projects(db, agent)


@router.get("/units", response_model=list[UnitOut])
def get_units(project_id: int | None = None, status: str | None = None,
              db: Session = Depends(get_db),
              agent: m.Agent = Depends(get_current_agent)):
    return svc.list_units(db, agent, project_id=project_id, status=status)


@router.get("/projects/{project_id}/summary")
def get_summary(project_id: int, db: Session = Depends(get_db),
                agent: m.Agent = Depends(get_current_agent)):
    return svc.inventory_summary(db, agent, project_id)