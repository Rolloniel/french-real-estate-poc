import logging
import math
from collections import defaultdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_db
from app.models.schemas import DepartmentStat, DepartmentStatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Safety cap: prevents loading unbounded data into Python memory.
# GROUP BY operations require Python-side aggregation because the Supabase
# REST API does not expose raw SQL GROUP BY.  This cap bounds the worst case.
MAX_ROWS = 50_000


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
async def price_per_m2():
    """Return price per m2 distribution as histogram buckets.

    Fetches only the two required columns with a row cap to prevent memory blowout.
    Histogram + median/mean are computed in Python since Supabase REST does not
    expose percentile or histogram aggregation.
    """
    try:
        db = get_db()
        data = (
            db.table("warehouses")
            .select("price_eur, surface_m2")
            .not_.is_("price_eur", "null")
            .not_.is_("surface_m2", "null")
            .gt("surface_m2", 0)
            .limit(MAX_ROWS)
            .execute()
        )

        values = []
        for r in data.data:
            price = r.get("price_eur")
            surface = r.get("surface_m2")
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
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error computing price-per-m2 analytics")
        raise HTTPException(status_code=500, detail=f"Failed to compute price-per-m2 analytics: {e}")


@router.get("/by-department", response_model=ByDepartmentResponse)
async def by_department():
    """Return avg price, avg surface, count grouped by department.

    Supabase REST does not support GROUP BY, so we fetch the three required
    columns with a row cap and aggregate in Python.
    """
    try:
        db = get_db()
        data = (
            db.table("warehouses")
            .select("department, price_eur, surface_m2")
            .not_.is_("department", "null")
            .limit(MAX_ROWS)
            .execute()
        )

        groups: dict[str, dict] = defaultdict(lambda: {"prices": [], "surfaces": [], "count": 0})
        for r in data.data:
            dept = r.get("department")
            if not dept:
                continue
            groups[dept]["count"] += 1
            if r.get("price_eur"):
                groups[dept]["prices"].append(r["price_eur"])
            if r.get("surface_m2"):
                groups[dept]["surfaces"].append(r["surface_m2"])

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
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error computing by-department analytics")
        raise HTTPException(status_code=500, detail=f"Failed to compute by-department analytics: {e}")


@router.get("/price-trends", response_model=PriceTrendsResponse)
async def price_trends():
    """Return avg price by month/year over time.

    Fetches only the columns needed, ordered by date, with a row cap.
    """
    try:
        db = get_db()
        data = (
            db.table("warehouses")
            .select("transaction_date, price_eur, surface_m2")
            .not_.is_("transaction_date", "null")
            .not_.is_("price_eur", "null")
            .order("transaction_date", desc=False)
            .limit(MAX_ROWS)
            .execute()
        )

        groups: dict[str, dict] = defaultdict(lambda: {"prices": [], "ppm2": [], "count": 0})
        for r in data.data:
            date_str = r.get("transaction_date")
            price = r.get("price_eur")
            surface = r.get("surface_m2")
            if not date_str or not price:
                continue
            # Extract YYYY-MM
            period = date_str[:7]
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
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error computing price-trends analytics")
        raise HTTPException(status_code=500, detail=f"Failed to compute price-trends analytics: {e}")


@router.get("/top-communes", response_model=TopCommunesResponse)
async def top_communes():
    """Return top 10 most expensive and cheapest communes by avg price per m2.

    Fetches only rows with valid price, surface, and commune, with a row cap.
    """
    try:
        db = get_db()
        data = (
            db.table("warehouses")
            .select("commune, department, price_eur, surface_m2")
            .not_.is_("commune", "null")
            .not_.is_("price_eur", "null")
            .not_.is_("surface_m2", "null")
            .gt("surface_m2", 0)
            .limit(MAX_ROWS)
            .execute()
        )

        groups: dict[str, dict] = defaultdict(lambda: {"department": "", "ppm2_values": []})
        for r in data.data:
            commune = r.get("commune")
            price = r.get("price_eur")
            surface = r.get("surface_m2")
            if not commune or not price or not surface or surface <= 0:
                continue
            groups[commune]["department"] = r.get("department", "")
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
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error computing top-communes analytics")
        raise HTTPException(status_code=500, detail=f"Failed to compute top-communes analytics: {e}")


@router.get("/department-stats", response_model=DepartmentStatsResponse)
async def department_stats():
    """Return avg price per m2 and warehouse count per department (for heatmap).

    Fetches only rows with valid department, price, and surface, with a row cap.
    """
    try:
        db = get_db()

        result = (
            db.table("warehouses")
            .select("department, price_eur, surface_m2")
            .not_.is_("department", "null")
            .not_.is_("price_eur", "null")
            .not_.is_("surface_m2", "null")
            .gt("surface_m2", 0)
            .limit(MAX_ROWS)
            .execute()
        )

        dept_map: dict[str, dict] = {}
        for row in result.data:
            dept = row.get("department")
            price = row.get("price_eur")
            surface = row.get("surface_m2")
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
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error computing department-stats analytics")
        raise HTTPException(status_code=500, detail=f"Failed to compute department-stats analytics: {e}")
