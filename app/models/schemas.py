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
