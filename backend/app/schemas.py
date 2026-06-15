"""API response schemas (Pydantic v2)."""
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    unit_number: str
    size_marla: Decimal
    floor: int
    price_pkr: Decimal
    status: str
    version: int


class BlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    city: str