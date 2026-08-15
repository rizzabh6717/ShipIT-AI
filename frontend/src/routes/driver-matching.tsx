import { createFileRoute, useSearch, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { MapPin, Truck, Star, Clock, ShieldCheck, ArrowRight, Sparkles, Phone, Car, Gauge, Route as RouteIcon, X } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { RequireAuth } from "@/components/RequireAuth";
import { RouteMap, ROUTES, createMarketplacePaths } from "@/components/RouteMap";
import { ProgressBar } from "@/components/ProgressBar";
import { AIRecommendationCard } from "@/components/AIRecommendationCard";
import { LoadingState, EmptyState, ErrorState } from "@/components/LoadingStates";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import type { DriverMatch, DriverProfile } from "@/lib/mock-api";

export const Route = createFileRoute("/driver-matching")({
  validateSearch: (search: Record<string, unknown>) => ({
    shipmentId: typeof search.shipmentId === "string" ? search.shipmentId : "",
    ...(typeof search.detail === "string" ? { detail: search.detail } : {}),
  }),
  head: () => ({
    meta: [
      { title: "Driver Matches — ShipIT AI" },
      {
        name: "description",
        content: "View AI-ranked driver matches for your shipment with confidence scores, route overlap, detour, ETA, and explanations.",
      },
      { property: "og:title", content: "Driver Matches — ShipIT AI" },
    ],
  }),
  component: () => (
    <RequireAuth>
      <DriverMatchingPage />
    </RequireAuth>
  ),
});

function DriverDetailsPanel({ profile, onClose }: { profile: DriverProfile; onClose: () => void }) {
  const rating = Math.round(profile.rating * 10) / 10;
  const onTime = Math.round(profile.onTimeRate * 100);
  const completion = Math.round(profile.completionRate * 100);
  return (
    <div className="glass-card lift p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Driver profile</p>
          <h3 className="mt-1 font-display text-lg font-bold">{profile.name}</h3>
          <p className="mt-1 text-sm text-[#6B6B6B]">{profile.vehicleType} · {profile.capacityKg} kg capacity</p>
        </div>
        <button onClick={onClose} className="btn-secondary !px-3 !py-2" aria-label="Close details">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="mt-5 grid gap-2 text-sm">
        {profile.phone && (
          <p className="flex items-center gap-2 text-[#6B6B6B]">
            <Phone className="h-4 w-4 text-[#00D4AA]" /> {profile.phone}
          </p>
        )}
        {profile.vehicleRegNumber && (
          <p className="flex items-center gap-2 text-[#6B6B6B]">
            <Car className="h-4 w-4 text-[#FBBF24]" /> {profile.vehicleRegNumber}
          </p>
        )}
        {profile.licenseNumber && (
          <p className="flex items-center gap-2 text-[#6B6B6B]">
            <ShieldCheck className="h-4 w-4 text-[#4C9EFF]" /> {profile.licenseNumber}
          </p>
        )}
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-[#292929] bg-[#101010] p-3">
          <p className="eyebrow flex items-center gap-1"><Star className="h-3 w-3 text-[#FBBF24]" /> Rating</p>
          <p className="mt-1 font-display text-lg font-bold">{rating}/5</p>
        </div>
        <div className="rounded-xl border border-[#292929] bg-[#101010] p-3">
          <p className="eyebrow flex items-center gap-1"><Clock className="h-3 w-3 text-[#4C9EFF]" /> On-time</p>
          <p className="mt-1 font-display text-lg font-bold">{onTime}%</p>
        </div>
        <div className="rounded-xl border border-[#292929] bg-[#101010] p-3">
          <p className="eyebrow flex items-center gap-1"><Gauge className="h-3 w-3 text-[#00D4AA]" /> Completion</p>
          <p className="mt-1 font-display text-lg font-bold">{completion}%</p>
        </div>
        <div className="rounded-xl border border-[#292929] bg-[#101010] p-3">
          <p className="eyebrow flex items-center gap-1"><Truck className="h-3 w-3 text-[#FBBF24]" /> Deliveries</p>
          <p className="mt-1 font-display text-lg font-bold">{profile.completedDeliveries}</p>
        </div>
      </div>

      {profile.routes && profile.routes.length > 0 && (
        <div className="mt-5 rounded-xl border border-[#292929] bg-[#101010] p-4">
          <p className="eyebrow flex items-center gap-1.5"><RouteIcon className="h-3.5 w-3.5 text-[#00D4AA]" /> Active routes</p>
          <ul className="mt-3 flex flex-col gap-2">
            {profile.routes
              .filter((r) => r.isActive)
              .map((r, i) => (
                <li key={i} className="flex items-center justify-between gap-2 text-sm">
                  <span className="flex items-center gap-2 text-[#6B6B6B]">
                    <MapPin className="h-3.5 w-3.5" /> {r.from} → {r.to}
                  </span>
                  {r.departureTime && (
                    <span className="text-xs text-[#00D4AA]">{r.departureTime}</span>
                  )}
                </li>
              ))}
          </ul>
        </div>
      )}

      <p className="mt-5 text-[11px] text-[#6B6B6B]">
        {profile.reviewsCount} verified review{profile.reviewsCount === 1 ? "" : "s"} · reliability is
        computed from rating, on-time and completion history.
      </p>
    </div>
  );
}

function DriverMatchingPage() {
  const { shipmentId, detail } = useSearch({ from: "/driver-matching" });
  const navigate = useNavigate();

  const { data: matches, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["driver-matches", shipmentId],
    queryFn: () => apiClient.matchDrivers(shipmentId || ""),
    enabled: !!shipmentId,
  });

  const [acceptedIds, setAcceptedIds] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const handleAccept = async (match: DriverMatch) => {
    if (!shipmentId) return;
    setSubmitting(true);
    try {
      await apiClient.selectDriver(shipmentId, match.driverId, match.routeId);
      setAcceptedIds((prev) => [...prev, match.id]);
      toast.success("Request sent — waiting for driver approval.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not send request");
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewDetails = (match: DriverMatch) => {
    if (!match.profile) {
      toast.info("Full driver profile is not available for this match.");
      return;
    }
    navigate({
      to: "/driver-matching",
      search: detail === match.id ? { shipmentId } : { shipmentId, detail: match.id },
    });
  };

  const selectedMatch = matches?.find((m) => m.id === detail) ?? null;

  if (!shipmentId) {
    return (
      <PageShell>
        <section className="container-page section-y">
          <Reveal className="max-w-2xl">
            <p className="eyebrow">Driver Matching</p>
            <h1 className="mt-4 font-display text-4xl font-bold tracking-tight sm:text-5xl">
              Select a shipment to view matches
            </h1>
            <p className="mt-4 text-muted-foreground">
              Navigate from your sender dashboard or tracking page to see AI-ranked driver matches.
            </p>
          </Reveal>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            <Reveal delay={0.05}>
              <div className="glass-card lift p-6 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#00D4AA]/12 text-[#00D4AA] mx-auto">
                  <Sparkles className="h-6 w-6" />
                </div>
                <h3 className="mt-4 font-display text-lg font-bold">No Shipment Selected</h3>
                <p className="mt-2 text-sm text-[#6B6B6B]">Please select a shipment from your dashboard to view driver matches.</p>
              </div>
            </Reveal>
          </div>
        </section>
      </PageShell>
    );
  }

  const routePaths = createMarketplacePaths(
    "delhiNoida",
    ROUTES,
    ["delhiNoida", "noidaGurgaon", "delhiGhaziabad", "gurgaonDelhi"]
  );

  return (
    <PageShell>
      <section className="container-page section-y">
        <Reveal className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">AI Driver Matching</p>
            <h1 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">
              Matches for <span className="text-[#00D4AA]">{shipmentId}</span>
            </h1>
            <p className="mt-2 text-sm text-[#6B6B6B]">
              Ranked by route overlap, pickup detour, ETA, reliability & deadline fit
            </p>
          </div>
        </Reveal>

        <div className="mt-12 grid items-start gap-8 lg:grid-cols-[1fr_480px]">
          <div className="flex flex-col gap-4">
            {selectedMatch?.profile ? (
              <DriverDetailsPanel
                profile={selectedMatch.profile}
                onClose={() =>
                  navigate({ to: "/driver-matching", search: { shipmentId } })
                }
              />
            ) : null}

            {isLoading ? (
              <LoadingState message="Finding the best drivers…" size="lg" />
            ) : isError ? (
              <ErrorState
                title="Could not load matches"
                description={error instanceof Error ? error.message : "Unknown error"}
                onRetry={() => refetch()}
              />
            ) : matches && matches.length === 0 ? (
              <EmptyState
                icon={Truck}
                title="No drivers currently available for this route."
                description="No compatible driver routes exist for this shipment. Try again later or adjust the shipment."
              />
            ) : (
              (matches ?? []).map((match, i) => (
                <Reveal key={match.id} delay={i * 0.05}>
                  <AIRecommendationCard
                    match={match}
                    variant="detailed"
                    isBest={i === 0}
                    showActions={true}
                    onAccept={() => handleAccept(match)}
                    onViewDetails={() => handleViewDetails(match)}
                    isAccepted={acceptedIds.includes(match.id)}
                  />
                </Reveal>
              ))
            )}
          </div>

          <div className="lg:sticky lg:top-24">
            <Reveal delay={0.08}>
              <RouteMap
                className="h-[420px]"
                paths={routePaths}
                stops={[
                  { x: 48, y: 208, label: "Delhi", kind: "origin" },
                  { x: 348, y: 54, label: "Noida", kind: "dest", anchor: "end", dy: -10 },
                  { x: 60, y: 96, label: "Gurgaon", kind: "driver" },
                  { x: 340, y: 168, label: "Ghaziabad", kind: "parcel", anchor: "end" },
                ]}
              />

              <div className="glass-card mt-6 p-6">
                <p className="eyebrow">How matching works</p>
                <ul className="mt-4 space-y-3 text-sm text-[#6B6B6B]">
                  <li className="flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-[#00D4AA]" />
                    <span>Semantic route embedding scores overlap</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-[#FBBF24]" />
                    <span>Detour penalty for pickup deviation</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-[#4C9EFF]" />
                    <span>ETA feasibility vs deadline</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Star className="h-4 w-4 text-[#FBBF24]" />
                    <span>Driver reliability & rating history</span>
                  </li>
                </ul>
              </div>
            </Reveal>
          </div>
        </div>
      </section>
    </PageShell>
  );
}