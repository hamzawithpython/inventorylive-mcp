"""ORM models — the single source of truth schema.

status fields use plain strings (checked in the service layer) rather than
DB enums, so we can evolve states without migrations during early build.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Numeric, func
)
from sqlalchemy.orm import relationship
from app.core.db import Base


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    blocks = relationship("Block", back_populates="project")


class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g. "Block C"
    project = relationship("Project", back_populates="blocks")
    units = relationship("Unit", back_populates="block")


class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True)
    block_id = Column(Integer, ForeignKey("blocks.id"), nullable=False)
    unit_number = Column(String, nullable=False)
    size_marla = Column(Numeric(5, 1), nullable=False)  # 5, 10, 20 (1 kanal)
    floor = Column(Integer, default=0)
    price_pkr = Column(Numeric(14, 2), nullable=False)   # store raw PKR
    status = Column(String, default="available")          # available|reserved|sold
    version = Column(Integer, default=0)                  # optimistic-lock counter
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    block = relationship("Block", back_populates="units")


class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="agent")                # admin|agent
    api_key = Column(String, unique=True, nullable=False) # MCP auth
    created_at = Column(DateTime, server_default=func.now())


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    block_id = Column(Integer, ForeignKey("blocks.id"), nullable=True)  # null = whole project


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    status = Column(String, default="active")             # active|expired|completed
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    unit_id = Column(Integer, nullable=True)
    source = Column(String, nullable=False)               # portal|mcp
    detail_json = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())