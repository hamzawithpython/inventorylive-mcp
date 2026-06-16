"""Natural-language query endpoint, powered by Groq + the shared service layer."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_agent
from app.services import ask as ask_svc
from app.models import models as m

router = APIRouter(prefix="/api", tags=["ai"])


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask_ai(body: AskRequest, db: Session = Depends(get_db),
           agent: m.Agent = Depends(get_current_agent)):
    return ask_svc.ask(db, agent, body.question)