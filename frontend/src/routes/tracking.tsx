import { createFileRoute, useSearch, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, CheckCircle2, Circle, RefreshCw, Sparkles } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { RouteMap, ROUTES } from "@/components/RouteMap";
import { ProgressBar } from "@/components/ProgressBar";
import { apiClient } from "@/lib/api-client";
import { LoadingState, ErrorState, EmptyState } from "@/components/LoadingStates";
import { AIRecommendationCard } from "@/components/AIRecommendationCard";
import { toast } from "sonner";
import type { DriverMatch } from "@/lib/mock-api";

export const Route = createFileRoute("/tracking")({
  validateSearch: (search: Record<string, unknown>) => ({
    shipmentId: typeof search.shipmentId === "string" ? search.shipmentId : "",
  }),
  head: () => ({
    meta: [
      { title: "Track a Shipment — ShipIT AI" },
      {
        name: "description",
        content: "Follow your parcel in real time with live ETA updates from pickup to doorstep.",
      },
      { property: "og:title", content: "Track a Shipment — ShipIT AI" },
      { property: "og:description", content: "Live parcel tracking with route map and timeline." },
    ],
  }),
  component: Tracking,
});

function Tracking() {
  const { shipmentId } = useSearch({ from: "/tracking" });
  const navigate = useNavigate();
  const parcelPublicId = shipmentId; // Actual parcel public_id like "PA1B2C"

  const [input, setInput] = useState(parcelPublicId || "");
  const [trackingId, setTrackingId] = useState(parcelPublicId || "");

  const { data, isFetching, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["tracking", trackingId],
    queryFn: () => apiClient.tracking(trackingId),
    enabled: !!trackingId,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const newId = input.trim().toUpperCase();
    setTrackingId(newId);
    navigate({ to: "/tracking", search: { shipmentId: newId } });
  };

  const handleViewMatches = () => {
    if (trackingId) {
      navigate({ to: "/driver-matching", search: { shipmentId: trackingId } });
    }
  };

  if (!trackingId) {
    return (
      <PageShell>
        <section className="container-page section-y">
          <Reveal className="max-w-2xl">
            <p className="eyebrow">Live tracking</p>
            <h1 className="mt-4 font-display text-4xl font-bold tracking-tight sm:text-5xl">
              Where is it right now?
            </h1>
            <form onSubmit={handleSearch} className="mt-8 flex gap-3">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="SHIPIT-4821"
                className="flex-1 rounded-lg px-3 py-2.5 text-sm"
              />
              <button type="submit" className="btn-primary">
                <Search className="h-4 w-4" /> Track
              </button>
            </form>
          </Reveal>
        </section>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <section className="container-page section-y">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">Live tracking</p>
          <h1 className="mt-4 font-display text-4xl font-bold tracking-tight sm:text-5xl">
            Where is it right now?
          </h1>
          <form onSubmit={handleSearch} className="mt-8 flex gap-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="SHIPIT-4821"
              className="flex-1 rounded-lg px-3 py-2.5 text-sm"
            />
            <button type="submit" className="btn-primary">
              <Search className="h-4 w-4" /> Track
            </button>
          </form>
        </Reveal>

        <div className="mt-12 grid items-start gap-8 lg:grid-cols-2">
          <Reveal>
            {isLoading ? (
              <LoadingState message="Loading tracking data…" size="lg" className="h-[360px]" />
            ) : isError ? (
              <ErrorState
                title="Could not load tracking"
                description={error instanceof Error ? error.message : "Unknown error"}
                onRetry={() => refetch()}
                className="h-[360px]"
              />
            ) : !data ? (
              <EmptyState
                icon={Search}
                title="No tracking data found"
                description={`No information available for ${trackingId}`}
                className="h-[360px]"
              />
            ) : (
              <>
                <RouteMap
                  className="h-[360px]"
                  paths={[{ d: ROUTES.full, trucks: 2 }]}
                  stops={[
                    { x: 48, y: 208, label: data?.from ?? "Delhi", kind: "origin" },
                    { x: 158, y: 152, label: "Rohini", kind: "parcel" },
                    { x: 292, y: 92, label: data?.driver ?? "Driver", kind: "driver", anchor: "end" },
                    { x: 348, y: 54, label: data?.to ?? "Noida", kind: "dest", anchor: "end", dy: -10 },
                  ]}
                />
                <div className="glass-card mt-6 p-6">
                  <p className="eyebrow">{trackingId}</p>
                  <p className="mt-3 font-display text-xl font-bold">
                    {data?.from} → {data?.to}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Driver {data?.driver} · ETA {data?.eta}
                  </p>
                  <div className="mt-5">
                    <ProgressBar
                      value={data?.match ?? 0}
                      color="#4C9EFF"
                      label="AI match"
                      valueLabel={`${data?.match ?? 0}%`}
                    />
                  </div>
                  {trackingId && (
                    <button
                      onClick={handleViewMatches}
                      className="btn-secondary mt-4 w-full flex items-center justify-center gap-2"
                    >
                      <Sparkles className="h-4 w-4" /> View Driver Matches
                    </button>
                  )}
                </div>
              </>
            )}
          </Reveal>

          <Reveal delay={0.08}>
            <div className="glass-card rounded-3xl p-8">
              <div className="flex items-center justify-between">
                <p className="eyebrow">{isFetching ? "Refreshing…" : "Journey timeline"}</p>
                <button
                  onClick={() => refetch()}
                  disabled={isFetching}
                  className="btn-secondary !px-3 !py-1.5 text-xs flex items-center gap-1.5"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
                  Refresh
                </button>
              </div>
              {isLoading ? (
                <LoadingState message="Loading timeline…" className="mt-6" />
              ) : !data ? (
                <EmptyState
                  icon={Search}
                  title="No timeline data"
                  description="Tracking information not available"
                />
              ) : (
                <ol className="mt-6 flex flex-col gap-5">
                  {data?.steps.map((s) => (
                    <li key={s.label} className="flex items-start gap-3">
                      {s.done ? (
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#00D4AA]" />
                      ) : (
                        <Circle className="mt-0.5 h-4 w-4 shrink-0 text-[#6B6B6B]" />
                      )}
                      <div>
                        <p
                          className={`text-sm ${s.done ? "text-foreground" : "text-[#6B6B6B]"}`}
                        >
                          {s.label}
                        </p>
                        <p className="mt-0.5 text-xs text-[#6B6B6B]">{s.time}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </Reveal>
        </div>
      </section>
    </PageShell>
  );
}