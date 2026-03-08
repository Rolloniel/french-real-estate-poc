"use client";

import { useEffect, useState, useCallback } from "react";
import { WarehouseFilters } from "@/lib/types";
import { fetchDepartments } from "@/lib/api";

interface FilterPanelProps {
  filters: WarehouseFilters;
  onChange: (filters: WarehouseFilters) => void;
  resultCount: number;
}

const emptyFilters: WarehouseFilters = {
  department: "",
  min_price: "",
  max_price: "",
  min_surface: "",
  max_surface: "",
  date_from: "",
  date_to: "",
  commune: "",
};

export default function FilterPanel({
  filters,
  onChange,
  resultCount,
}: FilterPanelProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [departments, setDepartments] = useState<string[]>([]);

  useEffect(() => {
    fetchDepartments()
      .then(setDepartments)
      .catch(() => {
        /* non-critical */
      });
  }, []);

  const update = useCallback(
    (key: keyof WarehouseFilters, value: string) => {
      onChange({ ...filters, [key]: value });
    },
    [filters, onChange]
  );

  const clearAll = useCallback(() => {
    onChange({ ...emptyFilters });
  }, [onChange]);

  const hasActiveFilters = Object.values(filters).some((v) => v && v !== "");

  return (
    <div
      className={`flex flex-col border-r border-slate-800 bg-slate-900 transition-all duration-200 ${
        collapsed ? "w-10" : "w-72"
      }`}
    >
      {/* Toggle button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex h-10 items-center justify-center border-b border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
        title={collapsed ? "Show filters" : "Hide filters"}
      >
        {collapsed ? (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        )}
      </button>

      {!collapsed && (
        <div className="flex flex-1 flex-col overflow-y-auto px-3 py-3">
          {/* Header row */}
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Filters
            </h2>
            {hasActiveFilters && (
              <button
                onClick={clearAll}
                className="rounded px-2 py-0.5 text-xs text-blue-400 hover:bg-slate-800 hover:text-blue-300"
              >
                Clear All
              </button>
            )}
          </div>

          {/* Result count */}
          <div className="mb-4 rounded-md bg-slate-800/60 px-3 py-2 text-center">
            <span className="text-lg font-bold text-slate-100">
              {resultCount.toLocaleString("fr-FR")}
            </span>
            <span className="ml-1.5 text-xs text-slate-400">results</span>
          </div>

          {/* Department */}
          <label className="mb-1 text-xs font-medium text-slate-500">
            Department
          </label>
          <select
            value={filters.department || ""}
            onChange={(e) => update("department", e.target.value)}
            className="mb-3 rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
          >
            <option value="">All departments</option>
            {departments.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          {/* Commune search */}
          <label className="mb-1 text-xs font-medium text-slate-500">
            Commune
          </label>
          <input
            type="text"
            placeholder="Search commune..."
            value={filters.commune || ""}
            onChange={(e) => update("commune", e.target.value)}
            className="mb-3 rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
          />

          {/* Price range */}
          <label className="mb-1 text-xs font-medium text-slate-500">
            Price (EUR)
          </label>
          <div className="mb-3 flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.min_price || ""}
              onChange={(e) => update("min_price", e.target.value)}
              className="w-1/2 rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
            <input
              type="number"
              placeholder="Max"
              value={filters.max_price || ""}
              onChange={(e) => update("max_price", e.target.value)}
              className="w-1/2 rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Surface range */}
          <label className="mb-1 text-xs font-medium text-slate-500">
            Surface (m2)
          </label>
          <div className="mb-3 flex gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.min_surface || ""}
              onChange={(e) => update("min_surface", e.target.value)}
              className="w-1/2 rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
            <input
              type="number"
              placeholder="Max"
              value={filters.max_surface || ""}
              onChange={(e) => update("max_surface", e.target.value)}
              className="w-1/2 rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Date range */}
          <label className="mb-1 text-xs font-medium text-slate-500">
            Transaction Date
          </label>
          <div className="mb-3 flex flex-col gap-2">
            <input
              type="date"
              value={filters.date_from || ""}
              onChange={(e) => update("date_from", e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
            />
            <input
              type="date"
              value={filters.date_to || ""}
              onChange={(e) => update("date_to", e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
      )}
    </div>
  );
}
