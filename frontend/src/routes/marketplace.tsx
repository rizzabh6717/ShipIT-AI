import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { MapPin, ArrowRight, Truck, Clock, Leaf } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { RouteMap, ROUTES, createMarketplacePaths } from "@/components/RouteMap";
import { ProgressBar } from "@/components/ProgressBar";
import { LoadingState, EmptyState, ErrorState } from "@/components/LoadingStates";
import { apiClient } from "@/lib/api-client";

export const Route = createFileRoute("/marketplace")({
  head: () => ({
    meta: [
      { title: "Route Marketplace — ShipIT AI" },
      {
        name: "description",
        content:
          "Browse live Delhi-NCR corridors, driver availability, pricing, CO₂ saved and AI match strength for every route.",
      },
      { property: "og:title", content: "Route Marketplace — ShipIT AI" },
      {
        property: "og:description",
        content: "Live routes across Delhi-NCR with driver counts, pricing and AI match scores.",
      },
    ],
  }),
  component: Marketplace,
});

const MARKET_ROUTE_IDS = ["delhiNoida", "noidaGurgaon", "delhiGhaziabad", "gurgaonDelhi"] as const;

function Marketplace() {
  const { data: routes = [], isLoading, isError, error, refetch } = useQuery({
    queryKey: ["market-routes"],
    queryFn: () => apiClient.listMarketRoutes(),
  });
  const [selected, setSelected] = useState<string>("");
  const active = routes.find((r) => r.id === selected) ?? routes[0];

  const routePaths = createMarketplacePaths(
    selected || MARKET_ROUTE_IDS[0],
    ROUTES,
    MARKET_ROUTE_IDS,
  );

  return (
    <PageShell>
      <section className="container-page section-y">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">Route marketplace</p>
          <h1 className="mt-4 font-display text-4xl font-bold tracking-tight sm:text-5xl">
            Live corridors, priced by overlap.
          </h1>
          <p className="mt-4 text-muted-foreground">
            Corridors aggregated from routes drivers have actually published.
          </p>
        </Reveal>

        <div className="mt-12 grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="flex max-h-[720px] flex-col gap-4 overflow-y-auto pr-1">
            {isLoading ? (
              <LoadingState message="Loading live routes…" />
            ) : isError ? (
              <ErrorState
                title="Could not load routes"
                description={error instanceof Error ? error.message : "Unknown error"}
                onRetry={() => refetch()}
              />
            ) : routes.length === 0 ? (
              <EmptyState
                icon={Truck}
                title="No routes published yet"
                description="Drivers publish their planned routes and they appear here. Check back soon."
              />
            ) : (
              routes.map((r) => {
                const isActive = r.id === active?.id;
                return (
                  <button
                    key={r.id}
                    onClick={() => setSelected(r.id)}
                    className={`lift rounded-2xl border bg-[#1C1C1C] p-5 text-left transition ${
                      isActive
                        ? "border-[#4C9EFF] shadow-[0_0_0_1px_#4C9EFF,0_18px_44px_-26px_rgba(76,158,255,0.9)]"
                        : "border-[#292929]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4 text-[#00D4AA]" />
                        <span className="font-display text-base font-bold">{r.from}</span>
                        <ArrowRight className="h-3.5 w-3.5 text-[#6B6B6B]" />
                        <span className="font-display text-base font-bold">{r.to}</span>
                      </div>
                      <span className="font-display text-lg font-bold text-[#00D4AA]">₹{r.price}/kg</span>
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-[#6B6B6B]">
                      <span className="flex items-center gap-1.5">
                        <Truck className="h-3.5 w-3.5" /> {r.drivers} driver{r.drivers === 1 ? "" : "s"}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <MapPin className="h-3.5 w-3.5" /> {r.distance} km
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Leaf className="h-3.5 w-3.5" /> {r.co2} kg CO₂
                      </span>
                    </div>

                    <div className="mt-4">
                      <ProgressBar
                        value={r.match}
                        color="#4C9EFF"
                        label="Capacity available"
                        valueLabel={`${r.match}%`}
                      />
                    </div>
                  </button>
                );
              })
            )}
          </div>

          <div className="lg:sticky lg:top-24">
            <RouteMap
              className="h-[420px]"
              paths={routePaths}
              stops={[
                { x: 48, y: 208, label: active?.from ?? "Delhi", kind: "origin" },
                { x: 348, y: 54, label: active?.to ?? "Noida", kind: "dest", anchor: "end", dy: -10 },
                { x: 60, y: 96, label: "Gurgaon", kind: "driver" },
                { x: 340, y: 168, label: "Ghaziabad", kind: "parcel", anchor: "end" },
              ]}
            />

            <div className="glass-card mt-6 p-6">
              <p className="eyebrow">Selected route</p>
              <h2 className="mt-3 font-display text-2xl font-bold">
                {active?.from ?? "—"} → {active?.to ?? "—"}
              </h2>
              <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div>
                  <p className="eyebrow">Avg price</p>
                  <p className="mt-1.5 font-display text-lg font-bold text-[#00D4AA]">
                    ₹{active?.price ?? 0}/kg
                  </p>
                </div>
                <div>
                  <p className="eyebrow">Drivers</p>
                  <p className="mt-1.5 font-display text-lg font-bold">{active?.drivers ?? 0}</p>
                </div>
                <div>
                  <p className="eyebrow">Distance</p>
                  <p className="mt-1.5 font-display text-lg font-bold">{active?.distance ?? 0} km</p>
                </div>
                <div>
                  <p className="eyebrow">CO₂ saved</p>
                  <p className="mt-1.5 font-display text-lg font-bold text-[#00D4AA]">
                    {active?.co2 ?? 0} kg
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </PageShell>
  );
}
