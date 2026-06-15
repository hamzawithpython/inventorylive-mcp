"""FastAPI dependencies for authentication."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import decode_token
from app.models import models as m

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_agent(token: str = Depends(oauth2_scheme),
                      db: Session = Depends(get_db)) -> m.Agent:
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None or "sub" not in payload:
        raise creds_exc
    agent = db.query(m.Agent).filter(m.Agent.id == int(payload["sub"])).first()
    if agent is None:
        raise creds_exc
    return agent


def require_admin(agent: m.Agent = Depends(get_current_agent)) -> m.Agent:
    if agent.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return agent