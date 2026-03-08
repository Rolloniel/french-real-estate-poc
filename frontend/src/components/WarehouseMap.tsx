"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  GeoJSON,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import {
  Warehouse,
  NearbyWarehouse,
  WarehouseFilters,
  DepartmentHeatmapStat,
} from "@/lib/types";
import {
  fetchWarehouses,
  fetchNearbyWarehouses,
  fetchDepartmentStats,
} from "@/lib/api";
import { formatEur, formatSurface, formatDate } from "@/lib/format";
import "leaflet/dist/leaflet.css";

// Fix default marker icons for webpack/next.js bundling
const DefaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

// Distinct icon for the proximity search center point
const CenterIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [30, 49],
  iconAnchor: [15, 49],
  popupAnchor: [1, -40],
  shadowSize: [49, 49],
  className: "proximity-center-marker",
});

// France center coordinates
const FRANCE_CENTER: [number, number] = [46.6, 2.3];
const FRANCE_ZOOM = 6;

const GEOJSON_URL =
  "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson";

interface WarehouseMapProps {
  filters: WarehouseFilters;
  onResultCount: (count: number) => void;
}

/** Helper to check if a warehouse-like object has a distance_km field */
function isNearbyWarehouse(
  w: Warehouse | NearbyWarehouse
): w is NearbyWarehouse {
  return "distance_km" in w;
}

// ---------------------------------------------------------------------------
// Heatmap helpers
// ---------------------------------------------------------------------------

/** Color scale: green (cheap) -> yellow -> red (expensive) */
function priceToColor(value: number, min: number, max: number): string {
  if (max === min) return "#22c55e";
  const t = Math.min(1, Math.max(0, (value - min) / (max - min)));
  let r: number, g: number, b: number;
  if (t < 0.5) {
    const s = t * 2;
    r = Math.round(34 + (234 - 34) * s);
    g = Math.round(197 + (179 - 197) * s);
    b = Math.round(94 + (8 - 94) * s);
  } else {
    const s = (t - 0.5) * 2;
    r = Math.round(234 + (239 - 234) * s);
    g = Math.round(179 + (68 - 179) * s);
    b = Math.round(8 + (68 - 8) * s);
  }
  return `rgb(${r},${g},${b})`;
}

function formatPricePerM2(value: number): string {
  return (
    new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(value) + "/m\u00B2"
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Floating legend for the heatmap */
function HeatmapLegend({ min, max }: { min: number; max: number }) {
  const steps = 6;
  const labels: { color: string; label: string }[] = [];
  for (let i = 0; i <= steps; i++) {
    const value = min + (max - min) * (i / steps);
    labels.push({
      color: priceToColor(value, min, max),
      label: formatPricePerM2(Math.round(value)),
    });
  }

  return (
    <div
      style={{
        position: "absolute",
        bottom: 30,
        right: 10,
        zIndex: 1000,
        background: "rgba(15,23,42,0.9)",
        borderRadius: 8,
        padding: "10px 14px",
        color: "#e2e8f0",
        fontSize: 12,
        lineHeight: "18px",
        pointerEvents: "auto",
        border: "1px solid rgba(148,163,184,0.2)",
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 6 }}>
        Avg. Price / m&sup2;
      </div>
      {labels.map((l, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span
            style={{
              display: "inline-block",
              width: 16,
              height: 12,
              backgroundColor: l.color,
              borderRadius: 2,
              flexShrink: 0,
            }}
          />
          <span>{l.label}</span>
        </div>
      ))}
    </div>
  );
}

/** Toggle button: Pins vs Heatmap */
function ViewToggle({
  mode,
  onToggle,
}: {
  mode: "pins" | "heatmap";
  onToggle: () => void;
}) {
  return (
    <div
      style={{
        position: "absolute",
        top: 10,
        left: 60,
        zIndex: 1000,
        pointerEvents: "auto",
      }}
    >
      <button
        onClick={onToggle}
        style={{
          background: "rgba(15,23,42,0.9)",
          color: "#e2e8f0",
          border: "1px solid rgba(148,163,184,0.3)",
          borderRadius: 6,
          padding: "6px 14px",
          fontSize: 13,
          fontWeight: 500,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}
      >
        <span
          style={{
            display: "inline-block",
            width: 8,
            height: 8,
            borderRadius: mode === "pins" ? "50%" : 2,
            backgroundColor: mode === "pins" ? "#3b82f6" : "#ef4444",
          }}
        />
        {mode === "pins" ? "Pins" : "Heatmap"}
        <span style={{ opacity: 0.5, marginLeft: 2 }}>
          {mode === "pins" ? "| Switch to Heatmap" : "| Switch to Pins"}
        </span>
      </button>
    </div>
  );
}

/** Choropleth GeoJSON layer coloured by department avg price per m2 */
function ChoroplethLayer({
  geojson,
  deptStatsMap,
  minPrice,
  maxPrice,
}: {
  geojson: FeatureCollection;
  deptStatsMap: Map<string, DepartmentHeatmapStat>;
  minPrice: number;
  maxPrice: number;
}) {
  const geoJsonRef = useRef<L.GeoJSON | null>(null);

  const style = useCallback(
    (feature: Feature<Geometry> | undefined) => {
      if (!feature || !feature.properties) {
        return {
          fillColor: "#334155",
          weight: 1,
          color: "#475569",
          fillOpacity: 0.3,
        };
      }
      const code = feature.properties.code as string;
      const stat = deptStatsMap.get(code);
      if (!stat) {
        return {
          fillColor: "#334155",
          weight: 1,
          color: "#475569",
          fillOpacity: 0.3,
        };
      }
      return {
        fillColor: priceToColor(stat.avg_price_per_m2, minPrice, maxPrice),
        weight: 1,
        color: "#94a3b8",
        fillOpacity: 0.7,
      };
    },
    [deptStatsMap, minPrice, maxPrice]
  );

  const onEachFeature = useCallback(
    (feature: Feature<Geometry>, layer: L.Layer) => {
      const code = feature.properties?.code as string;
      const name = feature.properties?.nom as string;
      const stat = deptStatsMap.get(code);

      layer.on({
        mouseover: (e: L.LeafletMouseEvent) => {
          const target = e.target as L.Path;
          target.setStyle({ weight: 3, color: "#fff", fillOpacity: 0.85 });
          target.bringToFront();
        },
        mouseout: () => {
          if (geoJsonRef.current) {
            geoJsonRef.current.resetStyle();
          }
        },
      });

      const tooltipContent = stat
        ? `<div style="font-size:13px;line-height:1.5">
            <strong>${name} (${code})</strong><br/>
            Avg: ${formatPricePerM2(stat.avg_price_per_m2)}<br/>
            Warehouses: ${stat.total_count}
          </div>`
        : `<div style="font-size:13px"><strong>${name} (${code})</strong><br/>No data</div>`;

      layer.bindTooltip(tooltipContent, { sticky: true, direction: "top" });
    },
    [deptStatsMap]
  );

  return (
    <GeoJSON
      ref={(ref) => {
        geoJsonRef.current = ref;
      }}
      data={geojson}
      style={style}
      onEachFeature={onEachFeature}
    />
  );
}

/** Inner component to handle map click events */
function MapClickHandler({
  enabled,
  onMapClick,
}: {
  enabled: boolean;
  onMapClick: (lat: number, lng: number) => void;
}) {
  useMapEvents({
    click(e) {
      if (enabled) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    },
  });
  return null;
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function WarehouseMap({
  filters,
  onResultCount,
}: WarehouseMapProps) {
  const [warehouses, setWarehouses] = useState<
    (Warehouse | NearbyWarehouse)[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Proximity search state
  const [proximityMode, setProximityMode] = useState(false);
  const [centerPoint, setCenterPoint] = useState<[number, number] | null>(
    null
  );
  const [radiusKm, setRadiusKm] = useState(50);

  // Heatmap state
  const [viewMode, setViewMode] = useState<"pins" | "heatmap">("pins");
  const [deptStats, setDeptStats] = useState<DepartmentHeatmapStat[]>([]);
  const [geojson, setGeojson] = useState<FeatureCollection | null>(null);
  const [heatmapLoaded, setHeatmapLoaded] = useState(false);

  // Load heatmap data once (lazy — only when first switching to heatmap)
  useEffect(() => {
    if (viewMode !== "heatmap" || heatmapLoaded) return;

    Promise.all([
      fetchDepartmentStats().then((data) => data.items),
      fetch(GEOJSON_URL).then((res) => {
        if (!res.ok) throw new Error("Failed to load department boundaries");
        return res.json() as Promise<FeatureCollection>;
      }),
    ])
      .then(([stats, geo]) => {
        setDeptStats(stats);
        setGeojson(geo);
        setHeatmapLoaded(true);
      })
      .catch((err) => {
        console.error("Heatmap data error:", err);
      });
  }, [viewMode, heatmapLoaded]);

  const loadData = useCallback(
    (f: WarehouseFilters) => {
      setLoading(true);
      fetchWarehouses(100, 0, f)
        .then((data) => {
          setWarehouses(data.items);
          onResultCount(data.total);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    },
    [onResultCount]
  );

  const loadNearby = useCallback(
    (lat: number, lng: number, radius: number) => {
      setLoading(true);
      fetchNearbyWarehouses(lat, lng, radius)
        .then((data) => {
          setWarehouses(data.items);
          onResultCount(data.total);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    },
    [onResultCount]
  );

  // Load regular warehouse data with debounce
  useEffect(() => {
    if (proximityMode) return;

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      loadData(filters);
    }, 400);
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [filters, loadData, proximityMode]);

  // Load proximity data when center/radius changes
  useEffect(() => {
    if (!proximityMode || !centerPoint) return;

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      loadNearby(centerPoint[0], centerPoint[1], radiusKm);
    }, 300);
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [proximityMode, centerPoint, radiusKm, loadNearby]);

  // When toggling off proximity mode, reload regular data
  useEffect(() => {
    if (!proximityMode) {
      setCenterPoint(null);
      loadData(filters);
    }
  }, [proximityMode]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleMapClick = useCallback(
    (lat: number, lng: number) => {
      if (proximityMode) {
        setCenterPoint([lat, lng]);
      }
    },
    [proximityMode]
  );

  if (loading && warehouses.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-300 border-t-blue-600" />
          <p className="text-sm text-slate-400">Loading warehouses...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="rounded-lg border border-red-800 bg-red-950/50 px-6 py-4 text-red-300">
          <p className="font-medium">Failed to load data</p>
          <p className="mt-1 text-sm opacity-75">{error}</p>
        </div>
      </div>
    );
  }

  const mappable = warehouses.filter(
    (w) => w.latitude !== null && w.longitude !== null
  );

  // Pre-compute heatmap derived values
  const deptStatsMap = new Map(deptStats.map((d) => [d.department, d]));
  const prices = deptStats.map((d) => d.avg_price_per_m2);
  const minPrice = prices.length ? Math.min(...prices) : 0;
  const maxPrice = prices.length ? Math.max(...prices) : 1;

  const showPins = viewMode === "pins";
  const showHeatmap = viewMode === "heatmap" && geojson !== null;

  return (
    <div className="relative h-full w-full">
      {/* Proximity search controls */}
      <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-2">
        <button
          onClick={() => setProximityMode(!proximityMode)}
          className={`rounded-lg px-4 py-2 text-sm font-medium shadow-lg transition-colors ${
            proximityMode
              ? "bg-blue-600 text-white"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700"
          }`}
        >
          {proximityMode ? "Exit Proximity Search" : "Proximity Search"}
        </button>

        {proximityMode && (
          <div className="rounded-lg bg-slate-800/95 p-3 shadow-lg backdrop-blur-sm">
            {!centerPoint && (
              <p className="text-xs text-slate-400">
                Click on the map to set a center point
              </p>
            )}
            {centerPoint && (
              <>
                <div className="mb-2 text-xs text-slate-400">
                  Center: {centerPoint[0].toFixed(4)},{" "}
                  {centerPoint[1].toFixed(4)}
                </div>
                <label className="mb-1 block text-xs text-slate-400">
                  Radius: {radiusKm} km
                </label>
                <input
                  type="range"
                  min={10}
                  max={200}
                  step={5}
                  value={radiusKm}
                  onChange={(e) => setRadiusKm(Number(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <div className="mt-1 flex justify-between text-[10px] text-slate-500">
                  <span>10 km</span>
                  <span>200 km</span>
                </div>
                <div className="mt-2 text-xs text-slate-300">
                  {mappable.length} warehouse{mappable.length !== 1 ? "s" : ""}{" "}
                  found
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <MapContainer
        center={FRANCE_CENTER}
        zoom={FRANCE_ZOOM}
        className="h-full w-full"
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        <MapClickHandler enabled={proximityMode} onMapClick={handleMapClick} />

        {/* Heatmap choropleth layer */}
        {showHeatmap && (
          <ChoroplethLayer
            geojson={geojson!}
            deptStatsMap={deptStatsMap}
            minPrice={minPrice}
            maxPrice={maxPrice}
          />
        )}

        {/* Proximity circle overlay */}
        {proximityMode && centerPoint && (
          <Circle
            center={centerPoint}
            radius={radiusKm * 1000}
            pathOptions={{
              color: "#3b82f6",
              fillColor: "#3b82f6",
              fillOpacity: 0.08,
              weight: 2,
              dashArray: "6 4",
            }}
          />
        )}

        {/* Center marker */}
        {proximityMode && centerPoint && (
          <Marker position={centerPoint} icon={CenterIcon}>
            <Popup>
              <div className="font-sans text-sm">
                <p className="font-bold text-blue-700">Search Center</p>
                <p className="text-slate-500">
                  {centerPoint[0].toFixed(4)}, {centerPoint[1].toFixed(4)}
                </p>
                <p className="text-slate-500">Radius: {radiusKm} km</p>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Warehouse pin markers — hidden in heatmap mode */}
        {showPins &&
          mappable.map((w) => (
            <Marker key={w.id} position={[w.latitude!, w.longitude!]}>
              <Popup>
                <div className="min-w-[200px] font-sans">
                  <p className="text-lg font-bold text-blue-700">
                    {formatEur(w.price_eur)}
                  </p>
                  <hr className="my-1.5 border-slate-200" />
                  <table className="w-full text-sm">
                    <tbody>
                      {isNearbyWarehouse(w) && (
                        <tr>
                          <td className="pr-3 text-slate-500">Distance</td>
                          <td className="font-medium text-blue-600">
                            {w.distance_km.toFixed(1)} km
                          </td>
                        </tr>
                      )}
                      <tr>
                        <td className="pr-3 text-slate-500">Surface</td>
                        <td className="font-medium">
                          {formatSurface(w.surface_m2)}
                        </td>
                      </tr>
                      <tr>
                        <td className="pr-3 text-slate-500">Commune</td>
                        <td className="font-medium">
                          {w.commune || "N/A"}
                        </td>
                      </tr>
                      <tr>
                        <td className="pr-3 text-slate-500">Department</td>
                        <td className="font-medium">
                          {w.department || "N/A"}
                        </td>
                      </tr>
                      <tr>
                        <td className="pr-3 text-slate-500">Date</td>
                        <td className="font-medium">
                          {formatDate(w.transaction_date)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </Popup>
            </Marker>
          ))}
      </MapContainer>

      {/* View toggle (Pins / Heatmap) */}
      <ViewToggle
        mode={viewMode}
        onToggle={() =>
          setViewMode(viewMode === "pins" ? "heatmap" : "pins")
        }
      />

      {/* Heatmap legend */}
      {showHeatmap && <HeatmapLegend min={minPrice} max={maxPrice} />}
    </div>
  );
}
