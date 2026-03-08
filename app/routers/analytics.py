import math
from collections import defaultdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.models.schemas import DepartmentStat, DepartmentStatsResponse, WarehouseModel

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class HistogramBucket(BaseModel):
    range_min: float
    range_max: float
    count: int


class PricePerM2Response(BaseModel):
    buckets: list[HistogramBucket]
    median: float
    mean: float


class DepartmentStats(BaseModel):
    department: str
    avg_price: float
    avg_surface: float
    avg_price_per_m2: float
    count: int


class ByDepartmentResponse(BaseModel):
    departments: list[DepartmentStats]


class PriceTrendPoint(BaseModel):
    period: str  # "YYYY-MM"
    avg_price: float
    avg_price_per_m2: float
    count: int


class PriceTrendsResponse(BaseModel):
    trends: list[PriceTrendPoint]


class CommuneStats(BaseModel):
    commune: str
    department: str
    avg_price_per_m2: float
    count: int


class TopCommunesResponse(BaseModel):
    most_expensive: list[CommuneStats]
    cheapest: list[CommuneStats]


@router.get("/price-per-m2", response_model=PricePerM2Response)
async def price_per_m2(session: AsyncSession = Depends(get_db_session)):
    """Return price per m2 distribution as histogram buckets."""
    result = await session.execute(
        select(WarehouseModel.price_eur, WarehouseModel.surface_m2)
        .where(
            WarehouseModel.price_eur.isnot(None),
            WarehouseModel.surface_m2.isnot(None),
            WarehouseModel.surface_m2 > 0,
        )
    )

    values = []
    for price, surface in result.all():
        if price and surface and surface > 0:
            values.append(price / surface)

    if not values:
        return PricePerM2Response(buckets=[], median=0, mean=0)

    values.sort()
    mean_val = sum(values) / len(values)
    n = len(values)
    median_val = values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2

    # Build histogram with ~10 buckets
    min_val = values[0]
    max_val = values[-1]
    num_buckets = min(10, n)
    bucket_width = math.ceil((max_val - min_val) / num_buckets) if max_val > min_val else 1

    buckets: list[HistogramBucket] = []
    for i in range(num_buckets):
        lo = min_val + i * bucket_width
        hi = lo + bucket_width
        count = sum(1 for v in values if lo <= v < hi or (i == num_buckets - 1 and v == hi))
        buckets.append(HistogramBucket(range_min=round(lo, 2), range_max=round(hi, 2), count=count))

    return PricePerM2Response(
        buckets=buckets,
        median=round(median_val, 2),
        mean=round(mean_val, 2),
    )


@router.get("/by-department", response_model=ByDepartmentResponse)
async def by_department(session: AsyncSession = Depends(get_db_session)):
    """Return avg price, avg surface, count grouped by department."""
    result = await session.execute(
        select(
            WarehouseModel.department,
            WarehouseModel.price_eur,
            WarehouseModel.surface_m2,
        ).where(WarehouseModel.department.isnot(None))
    )

    groups: dict[str, dict] = defaultdict(lambda: {"prices": [], "surfaces": [], "count": 0})
    for dept, price, surface in result.all():
        if not dept:
            continue
        groups[dept]["count"] += 1
        if price:
            groups[dept]["prices"].append(price)
        if surface:
            groups[dept]["surfaces"].append(surface)

    departments = []
    for dept, g in sorted(groups.items()):
        avg_price = sum(g["prices"]) / len(g["prices"]) if g["prices"] else 0
        avg_surface = sum(g["surfaces"]) / len(g["surfaces"]) if g["surfaces"] else 0
        avg_ppm2 = (avg_price / avg_surface) if avg_surface > 0 else 0
        departments.append(
            DepartmentStats(
                department=dept,
                avg_price=round(avg_price, 2),
                avg_surface=round(avg_surface, 2),
                avg_price_per_m2=round(avg_ppm2, 2),
                count=g["count"],
            )
        )

    return ByDepartmentResponse(departments=departments)


@router.get("/price-trends", response_model=PriceTrendsResponse)
async def price_trends(session: AsyncSession = Depends(get_db_session)):
    """Return avg price by month/year over time."""
    result = await session.execute(
        select(
            WarehouseModel.transaction_date,
            WarehouseModel.price_eur,
            WarehouseModel.surface_m2,
        )
        .where(
            WarehouseModel.transaction_date.isnot(None),
            WarehouseModel.price_eur.isnot(None),
        )
        .order_by(WarehouseModel.transaction_date.asc())
    )

    groups: dict[str, dict] = defaultdict(lambda: {"prices": [], "ppm2": [], "count": 0})
    for txn_date, price, surface in result.all():
        if not txn_date or not price:
            continue
        period = txn_date.strftime("%Y-%m")
        groups[period]["prices"].append(price)
        groups[period]["count"] += 1
        if surface and surface > 0:
            groups[period]["ppm2"].append(price / surface)

    trends = []
    for period in sorted(groups.keys()):
        g = groups[period]
        avg_price = sum(g["prices"]) / len(g["prices"]) if g["prices"] else 0
        avg_ppm2 = sum(g["ppm2"]) / len(g["ppm2"]) if g["ppm2"] else 0
        trends.append(
            PriceTrendPoint(
                period=period,
                avg_price=round(avg_price, 2),
                avg_price_per_m2=round(avg_ppm2, 2),
                count=g["count"],
            )
        )

    return PriceTrendsResponse(trends=trends)


@router.get("/top-communes", response_model=TopCommunesResponse)
async def top_communes(session: AsyncSession = Depends(get_db_session)):
    """Return top 10 most expensive and cheapest communes by avg price per m2."""
    result = await session.execute(
        select(
            WarehouseModel.commune,
            WarehouseModel.department,
            WarehouseModel.price_eur,
            WarehouseModel.surface_m2,
        ).where(
            WarehouseModel.commune.isnot(None),
            WarehouseModel.price_eur.isnot(None),
            WarehouseModel.surface_m2.isnot(None),
            WarehouseModel.surface_m2 > 0,
        )
    )

    groups: dict[str, dict] = defaultdict(lambda: {"department": "", "ppm2_values": []})
    for commune, department, price, surface in result.all():
        if not commune or not price or not surface or surface <= 0:
            continue
        groups[commune]["department"] = department or ""
        groups[commune]["ppm2_values"].append(price / surface)

    commune_stats = []
    for commune, g in groups.items():
        if len(g["ppm2_values"]) == 0:
            continue
        avg_ppm2 = sum(g["ppm2_values"]) / len(g["ppm2_values"])
        commune_stats.append(
            CommuneStats(
                commune=commune,
                department=g["department"],
                avg_price_per_m2=round(avg_ppm2, 2),
                count=len(g["ppm2_values"]),
            )
        )

    commune_stats.sort(key=lambda x: x.avg_price_per_m2, reverse=True)
    most_expensive = commune_stats[:10]
    cheapest = list(reversed(commune_stats[-10:])) if len(commune_stats) >= 10 else list(reversed(commune_stats))

    return TopCommunesResponse(
        most_expensive=most_expensive,
        cheapest=cheapest,
    )


@router.get("/department-stats", response_model=DepartmentStatsResponse)
async def department_stats(session: AsyncSession = Depends(get_db_session)):
    """Return avg price per m2 and warehouse count per department (for heatmap)."""
    result = await session.execute(
        select(
            WarehouseModel.department,
            WarehouseModel.price_eur,
            WarehouseModel.surface_m2,
        ).where(
            WarehouseModel.department.isnot(None),
            WarehouseModel.price_eur.isnot(None),
            WarehouseModel.surface_m2.isnot(None),
            WarehouseModel.surface_m2 > 0,
        )
    )

    dept_map: dict[str, dict] = {}
    for dept, price, surface in result.all():
        if not dept or not price or not surface or surface == 0:
            continue
        if dept not in dept_map:
            dept_map[dept] = {"total_price_per_m2": 0.0, "count": 0}
        dept_map[dept]["total_price_per_m2"] += price / surface
        dept_map[dept]["count"] += 1

    items = [
        DepartmentStat(
            department=dept,
            avg_price_per_m2=round(data["total_price_per_m2"] / data["count"], 2),
            total_count=data["count"],
        )
        for dept, data in sorted(dept_map.items())
    ]

    return DepartmentStatsResponse(items=items)
