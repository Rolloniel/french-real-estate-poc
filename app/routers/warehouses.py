from fastapi import APIRouter, Query, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.models.schemas import (
    Warehouse,
    WarehouseListResponse,
    WarehouseModel,
    StatsResponse,
)

router = APIRouter(prefix="/api", tags=["warehouses"])


@router.get("/warehouses", response_model=WarehouseListResponse)
async def list_warehouses(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_db_session),
):
    limit = max(1, min(100, limit))
    offset = max(0, offset)

    count_result = await session.execute(
        select(func.count()).select_from(WarehouseModel)
    )
    total = count_result.scalar() or 0

    result = await session.execute(
        select(WarehouseModel)
        .order_by(WarehouseModel.transaction_date.desc().nulls_last())
        .limit(limit)
        .offset(offset)
    )
    rows = result.scalars().all()
    items = [Warehouse.model_validate(row) for row in rows]

    return WarehouseListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


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
