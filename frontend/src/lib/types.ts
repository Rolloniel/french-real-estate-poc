export interface Warehouse {
  id: string;
  address: string | null;
  postal_code: string | null;
  commune: string | null;
  department: string | null;
  surface_m2: number | null;
  price_eur: number | null;
  transaction_date: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface WarehouseListResponse {
  items: Warehouse[];
  total: number;
  limit: number;
  offset: number;
}

export interface StatsResponse {
  count: number;
  avg_price: number;
  total_surface: number;
}
