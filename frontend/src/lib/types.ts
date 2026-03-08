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

export interface NearbyWarehouse extends Warehouse {
  distance_km: number;
}

export interface NearbyWarehouseListResponse {
  items: NearbyWarehouse[];
  total: number;
  center_lat: number;
  center_lng: number;
  radius_km: number;
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

export interface WarehouseFilters {
  department?: string;
  min_price?: string;
  max_price?: string;
  min_surface?: string;
  max_surface?: string;
  date_from?: string;
  date_to?: string;
  commune?: string;
}

// Analytics types

export interface HistogramBucket {
  range_min: number;
  range_max: number;
  count: number;
}

export interface PricePerM2Response {
  buckets: HistogramBucket[];
  median: number;
  mean: number;
}

export interface DepartmentStats {
  department: string;
  avg_price: number;
  avg_surface: number;
  avg_price_per_m2: number;
  count: number;
}

export interface ByDepartmentResponse {
  departments: DepartmentStats[];
}

export interface PriceTrendPoint {
  period: string;
  avg_price: number;
  avg_price_per_m2: number;
  count: number;
}

export interface PriceTrendsResponse {
  trends: PriceTrendPoint[];
}

export interface CommuneStats {
  commune: string;
  department: string;
  avg_price_per_m2: number;
  count: number;
}

export interface TopCommunesResponse {
  most_expensive: CommuneStats[];
  cheapest: CommuneStats[];
}

export interface DepartmentHeatmapStat {
  department: string;
  avg_price_per_m2: number;
  total_count: number;
}

export interface DepartmentHeatmapStatsResponse {
  items: DepartmentHeatmapStat[];
}
