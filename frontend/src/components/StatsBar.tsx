"use client";

import { useEffect, useState } from "react";
import { StatsResponse } from "@/lib/types";
import { fetchStats } from "@/lib/api";
import { formatEur, formatSurface } from "@/lib/format";

export default function StatsBar() {
  const [stats, setStats] = useState<StatsResponse | null>(null);

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch(() => {
        /* stats are non-critical, silently fail */
      });
  }, []);

  if (!stats) return null;

  const items = [
    { label: "Warehouses", value: stats.count.toLocaleString("fr-FR") },
    { label: "Avg. Price", value: formatEur(stats.avg_price) },
    { label: "Total Surface", value: formatSurface(stats.total_surface) },
  ];

  return (
    <div className="flex items-center gap-6">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-2">
          <span className="text-xs uppercase tracking-wider text-slate-500">
            {item.label}
          </span>
          <span className="text-sm font-semibold text-slate-200">
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
}
