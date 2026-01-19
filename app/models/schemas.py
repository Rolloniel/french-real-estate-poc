from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID


class Warehouse(BaseModel):
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


class WarehouseListResponse(BaseModel):
    items: list[Warehouse]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    count: int
    avg_price: float
    total_surface: float
