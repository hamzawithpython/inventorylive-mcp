"""Read-only inventory endpoints (Phase 1)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services import inventory as svc
from app.schemas import ProjectOut, UnitOut

router = APIRouter(prefix="/api", tags=["inventory"])


@router.get("/projects", response_model=list[ProjectOut])
def get_projects(db: Session = Depends(get_db)):
    return svc.list_projects(db)


@router.get("/units", response_model=list[UnitOut])
def get_units(project_id: int | None = None, status: str | None = None,
              db: Session = Depends(get_db)):
    return svc.list_units(db, project_id=project_id, status=status)


@router.get("/projects/{project_id}/summary")
def get_summary(project_id: int, db: Session = Depends(get_db)):
    return svc.inventory_summary(db, project_id)