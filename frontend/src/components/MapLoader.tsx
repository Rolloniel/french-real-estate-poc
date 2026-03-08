"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { WarehouseFilters } from "@/lib/types";
import FilterPanel from "@/components/FilterPanel";

const WarehouseMap = dynamic(() => import("@/components/WarehouseMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-300 border-t-blue-600" />
    </div>
  ),
});

const initialFilters: WarehouseFilters = {
  department: "",
  min_price: "",
  max_price: "",
  min_surface: "",
  max_surface: "",
  date_from: "",
  date_to: "",
  commune: "",
};

export default function MapLoader() {
  const [filters, setFilters] = useState<WarehouseFilters>(initialFilters);
  const [resultCount, setResultCount] = useState(0);

  const handleResultCount = useCallback((count: number) => {
    setResultCount(count);
  }, []);

  return (
    <div className="flex h-full">
      <FilterPanel
        filters={filters}
        onChange={setFilters}
        resultCount={resultCount}
      />
      <div className="flex-1">
        <WarehouseMap filters={filters} onResultCount={handleResultCount} />
      </div>
    </div>
  );
}
