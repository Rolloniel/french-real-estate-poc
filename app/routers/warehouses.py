import math

from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.models.schemas import (
    Warehouse,
    WarehouseListResponse,
    WarehouseModel,
    NearbyWarehouse,
    NearbyWarehouseListResponse,
    StatsResponse,
)

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bounding_box(lat: float, lng: float, radius_km: float) -> tuple[float, float, float, float]:
    """Return (lat_min, lat_max, lng_min, lng_max) for a bounding box around the point."""
    delta_lat = radius_km / 111.0
    delta_lng = radius_km / (111.0 * max(math.cos(math.radians(lat)), 1e-10))
    return (
        lat - delta_lat,
        lat + delta_lat,
        lng - delta_lng,
        lng + delta_lng,
    )


router = APIRouter(prefix="/api", tags=["warehouses"])


@router.get("/warehouses", response_model=WarehouseListResponse)
async def list_warehouses(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    department: Optional[str] = Query(default=None),
    min_price: Optional[float] = Query(default=None),
    max_price: Optional[float] = Query(default=None),
    min_surface: Optional[float] = Query(default=None),
    max_surface: Optional[float] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    commune: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    limit = max(1, min(100, limit))
    offset = max(0, offset)

    base_query = select(WarehouseModel)
    count_query = select(func.count()).select_from(WarehouseModel)

    # Apply filters
    if department:
        base_query = base_query.where(WarehouseModel.department == department)
        count_query = count_query.where(WarehouseModel.department == department)
    if min_price is not None:
        base_query = base_query.where(WarehouseModel.price_eur >= min_price)
        count_query = count_query.where(WarehouseModel.price_eur >= min_price)
    if max_price is not None:
        base_query = base_query.where(WarehouseModel.price_eur <= max_price)
        count_query = count_query.where(WarehouseModel.price_eur <= max_price)
    if min_surface is not None:
        base_query = base_query.where(WarehouseModel.surface_m2 >= min_surface)
        count_query = count_query.where(WarehouseModel.surface_m2 >= min_surface)
    if max_surface is not None:
        base_query = base_query.where(WarehouseModel.surface_m2 <= max_surface)
        count_query = count_query.where(WarehouseModel.surface_m2 <= max_surface)
    if date_from:
        base_query = base_query.where(WarehouseModel.transaction_date >= date_from)
        count_query = count_query.where(WarehouseModel.transaction_date >= date_from)
    if date_to:
        base_query = base_query.where(WarehouseModel.transaction_date <= date_to)
        count_query = count_query.where(WarehouseModel.transaction_date <= date_to)
    if commune:
        base_query = base_query.where(WarehouseModel.commune.ilike(f"%{commune}%"))
        count_query = count_query.where(WarehouseModel.commune.ilike(f"%{commune}%"))

    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    result = await session.execute(
        base_query
        .order_by(WarehouseModel.transaction_date.desc().nulls_last())
        .limit(limit)
        .offset(offset)
    )
    rows = result.scalars().all()
    items = [Warehouse.model_validate(row) for row in rows]

    return WarehouseListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get("/warehouses/nearby", response_model=NearbyWarehouseListResponse)
async def nearby_warehouses(
    lat: float = Query(..., description="Latitude of center point"),
    lng: float = Query(..., description="Longitude of center point"),
    radius_km: float = Query(
        default=50, ge=1, le=500, description="Search radius in km"
    ),
    session: AsyncSession = Depends(get_db_session),
):
    """Return warehouses within radius_km of the given point, sorted by distance."""
    lat_min, lat_max, lng_min, lng_max = bounding_box(lat, lng, radius_km)

    result = await session.execute(
        select(WarehouseModel)
        .where(
            WarehouseModel.latitude.isnot(None),
            WarehouseModel.longitude.isnot(None),
            WarehouseModel.latitude >= lat_min,
            WarehouseModel.latitude <= lat_max,
            WarehouseModel.longitude >= lng_min,
            WarehouseModel.longitude <= lng_max,
        )
    )
    candidates = result.scalars().all()

    nearby = []
    for row in candidates:
        dist = haversine(lat, lng, row.latitude, row.longitude)
        if dist <= radius_km:
            wh = Warehouse.model_validate(row)
            nearby.append(NearbyWarehouse(**wh.model_dump(), distance_km=round(dist, 2)))

    nearby.sort(key=lambda w: w.distance_km)

    return NearbyWarehouseListResponse(
        items=nearby,
        total=len(nearby),
        center_lat=lat,
        center_lng=lng,
        radius_km=radius_km,
    )


@router.get("/departments", response_model=list[str])
async def list_departments(
    session: AsyncSession = Depends(get_db_session),
):
    """Return sorted list of unique department values for filter dropdown."""
    result = await session.execute(
        select(WarehouseModel.department)
        .where(WarehouseModel.department.isnot(None))
        .distinct()
    )
    departments = sorted(row[0] for row in result.all())
    return departments


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(
            func.count(WarehouseModel.id),
            func.avg(WarehouseModel.price_eur),
            func.sum(WarehouseModel.surface_m2),
        )
    )
    count, avg_price, total_surface = result.one()

    return StatsResponse(
        count=count or 0,
        avg_price=round(float(avg_price), 2) if avg_price else 0.0,
        total_surface=round(float(total_surface), 2) if total_surface else 0.0,
    )
