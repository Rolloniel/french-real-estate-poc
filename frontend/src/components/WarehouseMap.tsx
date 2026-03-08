"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import { Warehouse } from "@/lib/types";
import { fetchWarehouses } from "@/lib/api";
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

// France center coordinates
const FRANCE_CENTER: [number, number] = [46.6, 2.3];
const FRANCE_ZOOM = 6;

export default function WarehouseMap() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWarehouses(100)
      .then((data) => {
        setWarehouses(data.items);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
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
      {mappable.map((w) => (
        <Marker
          key={w.id}
          position={[w.latitude!, w.longitude!]}
        >
          <Popup>
            <div className="min-w-[200px] font-sans">
              <p className="text-lg font-bold text-blue-700">
                {formatEur(w.price_eur)}
              </p>
              <hr className="my-1.5 border-slate-200" />
              <table className="w-full text-sm">
                <tbody>
                  <tr>
                    <td className="pr-3 text-slate-500">Surface</td>
                    <td className="font-medium">{formatSurface(w.surface_m2)}</td>
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
  );
}
