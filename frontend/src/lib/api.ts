import { WarehouseListResponse, StatsResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export async function fetchWarehouses(
  limit = 100,
  offset = 0
): Promise<WarehouseListResponse> {
  const res = await fetch(
    `${API_BASE}/api/warehouses?limit=${limit}&offset=${offset}`
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch warehouses: ${res.status}`);
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
