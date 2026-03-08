"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
  Cell,
} from "recharts";
import {
  PricePerM2Response,
  ByDepartmentResponse,
  PriceTrendsResponse,
  TopCommunesResponse,
} from "@/lib/types";
import {
  fetchPricePerM2,
  fetchByDepartment,
  fetchPriceTrends,
  fetchTopCommunes,
} from "@/lib/api";

function ChartCard({
  title,
  children,
  subtitle,
}: {
  title: string;
  children: React.ReactNode;
  subtitle?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-100">{title}</h3>
        {subtitle && (
          <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>
        )}
      </div>
      {children}
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex h-64 items-center justify-center">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-600 border-t-blue-500" />
    </div>
  );
}

function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="flex h-64 items-center justify-center">
      <p className="text-sm text-red-400">{message}</p>
    </div>
  );
}

const tooltipStyle = {
  contentStyle: {
    backgroundColor: "#1e293b",
    border: "1px solid #334155",
    borderRadius: "8px",
    fontSize: "12px",
    color: "#e2e8f0",
  },
  labelStyle: { color: "#94a3b8" },
};

function formatEurCompact(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}k`;
  return value.toFixed(0);
}

export default function AnalyticsDashboard() {
  const [pricePerM2, setPricePerM2] = useState<PricePerM2Response | null>(null);
  const [byDept, setByDept] = useState<ByDepartmentResponse | null>(null);
  const [trends, setTrends] = useState<PriceTrendsResponse | null>(null);
  const [topCommunes, setTopCommunes] = useState<TopCommunesResponse | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const errs: Record<string, string> = {};

    Promise.allSettled([
      fetchPricePerM2().then(setPricePerM2).catch(() => {
        errs.pricePerM2 = "Failed to load price distribution";
      }),
      fetchByDepartment().then(setByDept).catch(() => {
        errs.byDept = "Failed to load department data";
      }),
      fetchPriceTrends().then(setTrends).catch(() => {
        errs.trends = "Failed to load price trends";
      }),
      fetchTopCommunes().then(setTopCommunes).catch(() => {
        errs.topCommunes = "Failed to load commune data";
      }),
    ]).finally(() => {
      setErrors(errs);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-300 border-t-blue-600" />
          <p className="text-sm text-slate-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  // Prepare histogram data
  const histogramData = pricePerM2?.buckets.map((b) => ({
    range: `${Math.round(b.range_min)}-${Math.round(b.range_max)}`,
    count: b.count,
  })) ?? [];

  // Prepare department data (top 15 by count for readability)
  const deptData = byDept?.departments
    .sort((a, b) => b.count - a.count)
    .slice(0, 15)
    .map((d) => ({
      department: d.department,
      avg_price_per_m2: d.avg_price_per_m2,
      avg_price: d.avg_price,
      count: d.count,
    })) ?? [];

  // Prepare trend data
  const trendData = trends?.trends.map((t) => ({
    period: t.period,
    avg_price: t.avg_price,
    avg_price_per_m2: t.avg_price_per_m2,
    count: t.count,
  })) ?? [];

  // Color scale for communes
  const expensiveColors = [
    "#ef4444", "#f87171", "#fb923c", "#fbbf24", "#facc15",
    "#a3e635", "#4ade80", "#34d399", "#2dd4bf", "#22d3ee",
  ];

  return (
    <div className="h-full overflow-y-auto p-6">
      {/* Summary stats row */}
      {pricePerM2 && (
        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-3">
            <p className="text-xs uppercase tracking-wider text-slate-500">Median Price/m2</p>
            <p className="mt-1 text-xl font-bold text-slate-100">
              {pricePerM2.median.toLocaleString("fr-FR")} EUR
            </p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-3">
            <p className="text-xs uppercase tracking-wider text-slate-500">Mean Price/m2</p>
            <p className="mt-1 text-xl font-bold text-slate-100">
              {pricePerM2.mean.toLocaleString("fr-FR")} EUR
            </p>
          </div>
          {byDept && (
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-3">
              <p className="text-xs uppercase tracking-wider text-slate-500">Departments</p>
              <p className="mt-1 text-xl font-bold text-slate-100">
                {byDept.departments.length}
              </p>
            </div>
          )}
          {trends && (
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-3">
              <p className="text-xs uppercase tracking-wider text-slate-500">Time Periods</p>
              <p className="mt-1 text-xl font-bold text-slate-100">
                {trends.trends.length}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Charts grid */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* Price per m2 histogram */}
        <ChartCard
          title="Price per m2 Distribution"
          subtitle={pricePerM2 ? `Median: ${pricePerM2.median.toLocaleString("fr-FR")} EUR/m2` : undefined}
        >
          {errors.pricePerM2 ? (
            <ErrorMessage message={errors.pricePerM2} />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={histogramData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="range"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  angle={-30}
                  textAnchor="end"
                  height={50}
                />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Department comparison */}
        <ChartCard
          title="Average Price per m2 by Department"
          subtitle="Top 15 departments by transaction count"
        >
          {errors.byDept ? (
            <ErrorMessage message={errors.byDept} />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={deptData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="department"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  angle={-30}
                  textAnchor="end"
                  height={50}
                />
                <YAxis
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  tickFormatter={(v) => `${formatEurCompact(v)}`}
                />
                <Tooltip
                  {...tooltipStyle}
                  formatter={(value, name) => {
                    const v = Number(value);
                    if (name === "avg_price_per_m2") return [`${v.toLocaleString("fr-FR")} EUR/m2`, "Avg Price/m2"];
                    return [v.toLocaleString("fr-FR"), String(name)];
                  }}
                />
                <Bar dataKey="avg_price_per_m2" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Price trends over time */}
        <ChartCard
          title="Price Trends Over Time"
          subtitle="Average price and price per m2 by month"
        >
          {errors.trends ? (
            <ErrorMessage message={errors.trends} />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="period"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  angle={-30}
                  textAnchor="end"
                  height={50}
                />
                <YAxis
                  yAxisId="left"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  tickFormatter={(v) => `${formatEurCompact(v)}`}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  tickFormatter={(v) => `${formatEurCompact(v)}`}
                />
                <Tooltip
                  {...tooltipStyle}
                  formatter={(value, name) => {
                    const v = Number(value);
                    if (name === "avg_price") return [`${v.toLocaleString("fr-FR")} EUR`, "Avg Price"];
                    if (name === "avg_price_per_m2") return [`${v.toLocaleString("fr-FR")} EUR/m2`, "Avg Price/m2"];
                    return [v, String(name)];
                  }}
                />
                <Legend
                  wrapperStyle={{ fontSize: "12px", color: "#94a3b8" }}
                  formatter={(value) => {
                    if (value === "avg_price") return "Avg Price";
                    if (value === "avg_price_per_m2") return "Avg Price/m2";
                    return value;
                  }}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="avg_price"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "#3b82f6" }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="avg_price_per_m2"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "#10b981" }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Top communes - horizontal bar chart */}
        <ChartCard
          title="Top Communes by Price per m2"
          subtitle="10 most expensive and 10 cheapest"
        >
          {errors.topCommunes ? (
            <ErrorMessage message={errors.topCommunes} />
          ) : topCommunes ? (
            <div className="space-y-6">
              {/* Most expensive */}
              <div>
                <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-red-400">
                  Most Expensive
                </h4>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart
                    data={topCommunes.most_expensive}
                    layout="vertical"
                    margin={{ left: 10 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                    <XAxis
                      type="number"
                      tick={{ fill: "#94a3b8", fontSize: 10 }}
                      tickFormatter={(v) => `${formatEurCompact(v)}`}
                    />
                    <YAxis
                      type="category"
                      dataKey="commune"
                      tick={{ fill: "#94a3b8", fontSize: 10 }}
                      width={120}
                    />
                    <Tooltip
                      {...tooltipStyle}
                      formatter={(value) => [`${Number(value).toLocaleString("fr-FR")} EUR/m2`, "Avg Price/m2"]}
                    />
                    <Bar dataKey="avg_price_per_m2" radius={[0, 4, 4, 0]}>
                      {topCommunes.most_expensive.map((_, index) => (
                        <Cell key={index} fill={expensiveColors[index] || "#ef4444"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Cheapest */}
              <div>
                <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-green-400">
                  Most Affordable
                </h4>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart
                    data={topCommunes.cheapest}
                    layout="vertical"
                    margin={{ left: 10 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                    <XAxis
                      type="number"
                      tick={{ fill: "#94a3b8", fontSize: 10 }}
                      tickFormatter={(v) => `${formatEurCompact(v)}`}
                    />
                    <YAxis
                      type="category"
                      dataKey="commune"
                      tick={{ fill: "#94a3b8", fontSize: 10 }}
                      width={120}
                    />
                    <Tooltip
                      {...tooltipStyle}
                      formatter={(value) => [`${Number(value).toLocaleString("fr-FR")} EUR/m2`, "Avg Price/m2"]}
                    />
                    <Bar dataKey="avg_price_per_m2" fill="#22c55e" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            <LoadingSpinner />
          )}
        </ChartCard>
      </div>
    </div>
  );
}
