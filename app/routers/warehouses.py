from fastapi import APIRouter, Query
from app.db import get_db
from app.models.schemas import Warehouse, WarehouseListResponse, StatsResponse

router = APIRouter(prefix="/api", tags=["warehouses"])


@router.get("/warehouses", response_model=WarehouseListResponse)
async def list_warehouses(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
):
    # Clamp values explicitly (FastAPI Query constraints don't clamp, they reject)
    limit = max(1, min(100, limit))
    offset = max(0, offset)

    db = get_db()
    result = (
        db.table("warehouses")
        .select("*", count="exact")
        .order("transaction_date", desc=True, nullsfirst=False)
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
