import {
  WarehouseListResponse,
  NearbyWarehouseListResponse,
  StatsResponse,
  WarehouseFilters,
  DepartmentHeatmapStatsResponse,
  PricePerM2Response,
  ByDepartmentResponse,
  PriceTrendsResponse,
  TopCommunesResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export async function fetchWarehouses(
  limit = 100,
  offset = 0,
  filters?: WarehouseFilters
): Promise<WarehouseListResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));

  if (filters) {
    if (filters.department) params.set("department", filters.department);
    if (filters.min_price) params.set("min_price", filters.min_price);
    if (filters.max_price) params.set("max_price", filters.max_price);
    if (filters.min_surface) params.set("min_surface", filters.min_surface);
    if (filters.max_surface) params.set("max_surface", filters.max_surface);
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    if (filters.commune) params.set("commune", filters.commune);
  }

  const res = await fetch(`${API_BASE}/api/warehouses?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch warehouses: ${res.status}`);
  }
  return res.json();
}

export async function fetchDepartments(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/departments`);
  if (!res.ok) {
    throw new Error(`Failed to fetch departments: ${res.status}`);
  }
  return res.json();
}

export async function fetchNearbyWarehouses(
  lat: number,
  lng: number,
  radius_km: number = 50
): Promise<NearbyWarehouseListResponse> {
  const params = new URLSearchParams({
    lat: String(lat),
    lng: String(lng),
    radius_km: String(radius_km),
  });
  const res = await fetch(`${API_BASE}/api/warehouses/nearby?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch nearby warehouses: ${res.status}`);
  }
  return res.json();
}

export async function fetchStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_BASE}/api/stats`);
  if (!res.ok) {
    throw new Error(`Failed to fetch stats: ${res.status}`);
  }
  return res.json();
}

export async function fetchDepartmentStats(): Promise<DepartmentHeatmapStatsResponse> {
  const res = await fetch(`${API_BASE}/api/analytics/department-stats`);
  if (!res.ok) {
    throw new Error(`Failed to fetch department stats: ${res.status}`);
  }
  return res.json();
}

export async function fetchPricePerM2(): Promise<PricePerM2Response> {
  const res = await fetch(`${API_BASE}/api/analytics/price-per-m2`);
  if (!res.ok) {
    throw new Error(`Failed to fetch price per m2: ${res.status}`);
  }
  return res.json();
}

export async function fetchByDepartment(): Promise<ByDepartmentResponse> {
  const res = await fetch(`${API_BASE}/api/analytics/by-department`);
  if (!res.ok) {
    throw new Error(`Failed to fetch department analytics: ${res.status}`);
  }
  return res.json();
}

export async function fetchPriceTrends(): Promise<PriceTrendsResponse> {
  const res = await fetch(`${API_BASE}/api/analytics/price-trends`);
  if (!res.ok) {
    throw new Error(`Failed to fetch price trends: ${res.status}`);
  }
  return res.json();
}

export async function fetchTopCommunes(): Promise<TopCommunesResponse> {
  const res = await fetch(`${API_BASE}/api/analytics/top-communes`);
  if (!res.ok) {
    throw new Error(`Failed to fetch top communes: ${res.status}`);
  }
  return res.json();
}
