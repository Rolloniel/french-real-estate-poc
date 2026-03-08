import math

from fastapi import APIRouter, Query
from typing import Optional
from app.db import get_db
from app.models.schemas import (
    Warehouse,
    WarehouseListResponse,
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
):
    # Clamp values explicitly (FastAPI Query constraints don't clamp, they reject)
    limit = max(1, min(100, limit))
    offset = max(0, offset)

    db = get_db()
    query = db.table("warehouses").select("*", count="exact")

    # Apply filters
    if department:
        query = query.eq("department", department)
    if min_price is not None:
        query = query.gte("price_eur", min_price)
    if max_price is not None:
        query = query.lte("price_eur", max_price)
    if min_surface is not None:
        query = query.gte("surface_m2", min_surface)
    if max_surface is not None:
        query = query.lte("surface_m2", max_surface)
    if date_from:
        query = query.gte("transaction_date", date_from)
    if date_to:
        query = query.lte("transaction_date", date_to)
    if commune:
        query = query.ilike("commune", f"%{commune}%")

    result = (
        query.order("transaction_date", desc=True, nullsfirst=False)
        .limit(limit)
        .offset(offset)
        .execute()
    )

    items = [Warehouse(**row) for row in result.data]
    total = result.count if result.count is not None else len(items)

    return WarehouseListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/warehouses/nearby", response_model=NearbyWarehouseListResponse)
async def nearby_warehouses(
    lat: float = Query(..., description="Latitude of center point"),
    lng: float = Query(..., description="Longitude of center point"),
    radius_km: float = Query(
        default=50, ge=1, le=500, description="Search radius in km"
    ),
):
    """Return warehouses within radius_km of the given point, sorted by distance."""
    db = get_db()

    # Fetch all warehouses with coordinates (POC-scale dataset)
    result = db.table("warehouses").select("*").execute()

    nearby = []
    for row in result.data:
        w_lat = row.get("latitude")
        w_lng = row.get("longitude")
        if w_lat is None or w_lng is None:
            continue

        dist = haversine(lat, lng, w_lat, w_lng)
        if dist <= radius_km:
            nearby.append(NearbyWarehouse(**row, distance_km=round(dist, 2)))

    # Sort by distance ascending (nearest first)
    nearby.sort(key=lambda w: w.distance_km)

    return NearbyWarehouseListResponse(
        items=nearby,
        total=len(nearby),
        center_lat=lat,
        center_lng=lng,
        radius_km=radius_km,
    )


@router.get("/departments", response_model=list[str])
async def list_departments():
    """Return sorted list of unique department values for filter dropdown."""
    db = get_db()
    result = db.table("warehouses").select("department").execute()
    departments = sorted(
        {r["department"] for r in result.data if r.get("department")}
    )
    return departments


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    db = get_db()

    # Get count
    count_result = db.table("warehouses").select("id", count="exact").execute()
    count = count_result.count or 0

    # Get all data for avg/sum (acceptable for POC with <1000 rows)
    all_data = db.table("warehouses").select("price_eur, surface_m2").execute()

    prices = [r["price_eur"] for r in all_data.data if r.get("price_eur")]
    surfaces = [r["surface_m2"] for r in all_data.data if r.get("surface_m2")]

    avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0
    total_surface = round(sum(surfaces), 2) if surfaces else 0.0

    return StatsResponse(
        count=count,
        avg_price=avg_price,
        total_surface=total_surface,
    )
