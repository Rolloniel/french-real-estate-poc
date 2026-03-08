import MapLoader from "@/components/MapLoader";
import NavTabs from "@/components/NavTabs";
import StatsBar from "@/components/StatsBar";

export default function Home() {
  return (
    <div className="flex h-screen flex-col bg-slate-950">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-800 px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-600 text-sm font-bold text-white">
            W
          </div>
          <h1 className="text-lg font-semibold text-slate-100">
            Warehouse Map
          </h1>
          <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs text-slate-400">
            France DVF
          </span>
          <NavTabs />
        </div>
        <StatsBar />
      </header>

      {/* Map fills remaining space */}
      <main className="flex-1">
        <MapLoader />
      </main>
    </div>
  );
}
