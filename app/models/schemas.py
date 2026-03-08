import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date
from uuid import UUID

from sqlalchemy import Column, String, Float, Date, Uuid
from sqlalchemy.orm import DeclarativeBase


# --- SQLAlchemy ORM ---

class Base(DeclarativeBase):
    pass


class WarehouseModel(Base):
    __tablename__ = "warehouses"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    dvf_mutation_id = Column(String, unique=True, nullable=False)
    address = Column(String)
    postal_code = Column(String)
    commune = Column(String)
    department = Column(String)
    surface_m2 = Column(Float)
    price_eur = Column(Float)
    transaction_date = Column(Date)
    latitude = Column(Float)
    longitude = Column(Float)
    property_type = Column(String)


# --- Pydantic response schemas ---

class Warehouse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    address: Optional[str] = None
    postal_code: Optional[str] = None
    commune: Optional[str] = None
    department: Optional[str] = None
    surface_m2: Optional[float] = None
    price_eur: Optional[float] = None
    transaction_date: Optional[date] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class NearbyWarehouse(Warehouse):
    distance_km: float


class WarehouseListResponse(BaseModel):
    items: list[Warehouse]
    total: int
    limit: int
    offset: int


class NearbyWarehouseListResponse(BaseModel):
    items: list[NearbyWarehouse]
    total: int
    center_lat: float
    center_lng: float
    radius_km: float


class StatsResponse(BaseModel):
    count: int
    avg_price: float
    total_surface: float


class DepartmentStat(BaseModel):
    department: str
    avg_price_per_m2: float
    total_count: int


class DepartmentStatsResponse(BaseModel):
    items: list[DepartmentStat]
