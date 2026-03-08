"use client";

import dynamic from "next/dynamic";

const WarehouseMap = dynamic(() => import("@/components/WarehouseMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-300 border-t-blue-600" />
    </div>
  ),
});

export default function MapLoader() {
  return <WarehouseMap />;
}
