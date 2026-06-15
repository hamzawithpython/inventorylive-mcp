"""Login endpoint — issues JWT for valid credentials."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import verify_password, create_access_token
from app.models import models as m

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    agent = db.query(m.Agent).filter(m.Agent.email == form.username).first()
    if not agent or not verify_password(form.password, agent.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(agent.id, agent.role)
    return {"access_token": token, "token_type": "bearer", "role": agent.role}