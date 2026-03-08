"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import { Warehouse, NearbyWarehouse, WarehouseFilters } from "@/lib/types";
import { fetchWarehouses, fetchNearbyWarehouses } from "@/lib/api";
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

interface WarehouseMapProps {
  filters: WarehouseFilters;
  onResultCount: (count: number) => void;
}

/** Helper to check if a warehouse-like object has a distance_km field */
function isNearbyWarehouse(w: Warehouse | NearbyWarehouse): w is NearbyWarehouse {
  return "distance_km" in w;
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

export default function WarehouseMap({
  filters,
  onResultCount,
}: WarehouseMapProps) {
  const [warehouses, setWarehouses] = useState<(Warehouse | NearbyWarehouse)[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Proximity search state
  const [proximityMode, setProximityMode] = useState(false);
  const [centerPoint, setCenterPoint] = useState<[number, number] | null>(null);
  const [radiusKm, setRadiusKm] = useState(50);

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
                  Center: {centerPoint[0].toFixed(4)}, {centerPoint[1].toFixed(4)}
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
                  {mappable.length} warehouse{mappable.length !== 1 ? "s" : ""} found
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

        {/* Warehouse markers */}
        {mappable.map((w) => (
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
                      <td className="font-medium">{w.commune || "N/A"}</td>
                    </tr>
                    <tr>
                      <td className="pr-3 text-slate-500">Department</td>
                      <td className="font-medium">{w.department || "N/A"}</td>
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
    </div>
  );
}
