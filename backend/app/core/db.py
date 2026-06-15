"""SQLAlchemy engine, session factory, and declarative base."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# pool_pre_ping handles Neon scale-to-zero: a stale connection is detected
# and replaced instead of erroring on the first query after idle wake-up.
engine = create_engine(settings.sqlalchemy_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()