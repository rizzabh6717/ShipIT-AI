import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Star, Truck, Route as RouteIcon, MapPin, Plus, Check, X, PackageCheck, Clock, Upload, Scale, IndianRupee } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { RequireAuth } from "@/components/RequireAuth";
import { CountUp } from "@/components/CountUp";
import { useAuth } from "@/lib/auth";
import { apiClient, mediaUrl } from "@/lib/api-client";
import { LoadingState, EmptyState, ErrorState } from "@/components/LoadingStates";
import type { DriverMatch, DriverStats } from "@/lib/mock-api";

export const Route = createFileRoute("/driver")({
  head: () => ({
    meta: [
      { title: "Driver Dashboard — ShipIT AI" },
      {
        name: "description",
        content: "Go online, review parcel requests on your route and accept the ones that fit.",
      },
      { property: "og:title", content: "Driver Dashboard — ShipIT AI" },
      { property: "og:description", content: "Parcels requesting delivery along routes you already drive." },
    ],
  }),
  component: () => (
    <RequireAuth role="driver">
      <DriverDashboard />
    </RequireAuth>
  ),
});

const emptyStats: DriverStats = {
  totalDeliveries: 0,
  completedDeliveries: 0,
  pendingDeliveries: 0,
  inTransitDeliveries: 0,
  rejectedDeliveries: 0,
  onTimeRate: 1,
  completionRate: 1,
  rating: 5,
  reviewsCount: 0,
  activeRoutes: 0,
};

function RequestCard({ m, onAccept, onReject, busy }: {
  m: DriverMatch;
  onAccept: () => void;
  onReject: () => void;
  busy: boolean;
}) {
  return (
    <div className="glass-card lift p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">{m.from} → {m.to}</p>
          <p className="mt-2 font-display text-lg font-bold">{m.weight} kg parcel</p>
          {m.description && <p className="mt-1 text-sm text-[#6B6B6B]">{m.description}</p>}
        </div>
        <span className="rounded-full border border-[#FBBF24]/40 bg-[#FBBF24]/12 px-3 py-1 text-[10px] font-semibold tracking-widest uppercase text-[#FBBF24]">
          Pending approval
        </span>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="flex items-center gap-3 rounded-xl border border-[#292929] bg-[#101010] px-3 py-2.5">
          <Scale className="h-4 w-4 text-[#4C9EFF]" />
          <div>
            <p className="eyebrow">Pickup</p>
            <p className="text-sm font-medium">{m.from}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-xl border border-[#292929] bg-[#101010] px-3 py-2.5">
          <MapPin className="h-4 w-4 text-[#00D4AA]" />
          <div>
            <p className="eyebrow">Destination</p>
            <p className="text-sm font-medium">{m.to}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-xl border border-[#292929] bg-[#101010] px-3 py-2.5">
          <Scale className="h-4 w-4 text-[#FBBF24]" />
          <div>
            <p className="eyebrow">Weight / Dimensions</p>
            <p className="text-sm font-medium">{m.weight} kg{m.dimensions ? ` · ${m.dimensions}` : ""}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-xl border border-[#292929] bg-[#101010] px-3 py-2.5">
          <IndianRupee className="h-4 w-4 text-[#00D4AA]" />
          <div>
            <p className="eyebrow">Budget</p>
            <p className="text-sm font-medium">₹{m.payout}</p>
          </div>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-xs text-[#6B6B6B]">
        {m.deadline && (
          <span className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" /> Deadline {new Date(m.deadline).toLocaleString()}
          </span>
        )}
      </div>

      <div className="mt-5 flex gap-3">
        <button
          onClick={onAccept}
          disabled={busy}
          className="btn-primary flex-1 items-center justify-center gap-2"
        >
          <Check className="h-4 w-4" /> Accept
        </button>
        <button
          onClick={onReject}
          disabled={busy}
          className="btn-secondary flex-1 items-center justify-center gap-2"
        >
          <X className="h-4 w-4" /> Reject
        </button>
      </div>
    </div>
  );
}

function DeliveryCard({ m, onPickup, onDeliver, busy }: {
  m: DriverMatch;
  onPickup: () => void;
  onDeliver: (file?: File) => void;
  busy: boolean;
}) {
  const [file, setFile] = useState<File | null>(null);

  return (
    <div className="glass-card lift p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="eyebrow">{m.from} → {m.to}</p>
          <p className="mt-2 font-display text-lg font-bold">{m.weight} kg parcel</p>
          {m.description && <p className="mt-1 text-sm text-[#6B6B6B]">{m.description}</p>}
          <p className="mt-1 text-xs text-[#6B6B6B]">
            Budget ₹{m.payout}{m.deadline ? ` · deadline ${new Date(m.deadline).toLocaleString()}` : ""}
          </p>
        </div>
        <span className="rounded-full border border-[#4C9EFF]/40 bg-[#4C9EFF]/12 px-3 py-1 text-[10px] font-semibold tracking-widest uppercase text-[#4C9EFF]">
          {m.requestStatus === "in_transit" ? "In Transit" : m.requestStatus === "delivered" ? "Delivered" : "Matched"}
        </span>
      </div>

      {m.proofImageUrl && m.requestStatus === "delivered" && (
        <a
          href={mediaUrl(m.proofImageUrl)}
          target="_blank"
          rel="noreferrer"
          className="mt-5 block overflow-hidden rounded-xl border border-[#292929]"
        >
          <img
            src={mediaUrl(m.proofImageUrl)}
            alt="Proof of delivery"
            className="h-28 w-44 object-cover"
          />
        </a>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-2">
        {m.requestStatus === "matched" && (
          <button
            onClick={() => onPickup()}
            disabled={busy}
            className="btn-primary !py-2 flex items-center gap-1.5"
          >
            <Check className="h-3.5 w-3.5" /> Confirm Pickup
          </button>
        )}
        {m.requestStatus === "in_transit" && (
          <div className="flex flex-wrap items-center gap-2">
            <label className="btn-secondary !py-2 cursor-pointer flex items-center gap-1.5">
              <Upload className="h-3.5 w-3.5" /> {file ? file.name : "Choose proof photo"}
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <button
              onClick={() => file && onDeliver(file)}
              disabled={busy || !file}
              className="btn-primary !py-2 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PackageCheck className="h-3.5 w-3.5" /> {busy ? "Uploading…" : "Mark Delivered"}
            </button>
            {!file && (
              <span className="flex items-center gap-1.5 text-xs text-[#FBBF24]">
                <Upload className="h-3.5 w-3.5" /> A proof photo is required
              </span>
            )}
          </div>
        )}
        {m.requestStatus === "delivered" && (
          <span className="flex items-center gap-1.5 text-xs text-[#00D4AA]">
            <PackageCheck className="h-3.5 w-3.5" /> Delivered
          </span>
        )}
        <span className="flex items-center gap-1.5 text-xs text-[#6B6B6B]">
          <MapPin className="h-3.5 w-3.5" /> {m.from} → {m.to}
        </span>
      </div>
    </div>
  );
}

function DriverDashboard() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [online, setOnline] = useState(true);
  const [tab, setTab] = useState<"pending" | "active">("pending");

  const stats = useQuery({
    queryKey: ["driver-stats"],
    queryFn: () => apiClient.getDriverStats(),
  });

  const statData: DriverStats = stats.data ?? emptyStats;

  const requests = useQuery({
    queryKey: ["driver-requests"],
    queryFn: () => apiClient.listDriverRequests(),
  });

  const deliveries = useQuery({
    queryKey: ["driver-deliveries"],
    queryFn: () => apiClient.listDriverDeliveries(),
  });

  const toggleAvailability = useMutation({
    mutationFn: (nextOnline: boolean) =>
      apiClient.updateAvailability(nextOnline ? "available" : "offline"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["driver-stats"] });
    },
  });

  const respond = useMutation({
    mutationFn: ({ requestId, accept }: { requestId: string; accept: boolean }) =>
      apiClient.respondToRequest(requestId, accept),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["driver-requests"] });
      qc.invalidateQueries({ queryKey: ["driver-deliveries"] });
      qc.invalidateQueries({ queryKey: ["driver-stats"] });
      toast.success("Request updated");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Update failed"),
  });

  const pickup = useMutation({
    mutationFn: (requestId: string) => apiClient.confirmPickup(requestId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["driver-deliveries"] });
      qc.invalidateQueries({ queryKey: ["driver-requests"] });
      toast.success("Picked up — parcel in transit");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Update failed"),
  });

  const delivered = useMutation({
    mutationFn: async ({ requestId, file }: { requestId: string; file: File }) => {
      const proofUrl = await apiClient.uploadRequestProof(requestId, file);
      await apiClient.markDelivered(requestId, proofUrl);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["driver-deliveries"] });
      qc.invalidateQueries({ queryKey: ["driver-requests"] });
      qc.invalidateQueries({ queryKey: ["driver-stats"] });
      toast.success("Delivered — proof of delivery saved.");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Update failed"),
  });

  const statCards = [
    { icon: RouteIcon, label: "Completed deliveries", value: statData.completedDeliveries, decimals: 0, prefix: "", suffix: "" },
    { icon: PackageCheck, label: "Total requests", value: statData.totalDeliveries, decimals: 0, prefix: "", suffix: "" },
    { icon: Star, label: "Rating", value: statData.rating, decimals: 1, prefix: "", suffix: "" },
    { icon: Star, label: "On-time rate", value: statData.onTimeRate * 100, decimals: 0, prefix: "", suffix: "%" },
  ];

  return (
    <PageShell>
      <section className="container-page section-y">
        <Reveal className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Driver dashboard</p>
            <h1 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">
              On the road, {user?.name}.
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                const next = !online;
                setOnline(next);
                toggleAvailability.mutate(next);
              }}
              className={`flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold tracking-widest uppercase transition ${
                online
                  ? "border-[#00D4AA]/45 bg-[#00D4AA]/12 text-[#00D4AA]"
                  : "border-[#292929] bg-[#101010] text-[#6B6B6B]"
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${online ? "bg-[#00D4AA]" : "bg-[#6B6B6B]"}`} />
              {online ? "Available for routes" : "Offline"}
            </button>
            <Link to="/create-shipment" className="btn-primary flex items-center gap-2">
              <Plus className="h-4 w-4" /> Publish Route
            </Link>
          </div>
        </Reveal>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statCards.map((s, i) => (
            <Reveal key={s.label} delay={i * 0.05}>
              <div className="glass-card lift p-6">
                <s.icon className="h-4 w-4 text-[#00D4AA]" />
                <p className="mt-4 font-display text-3xl font-bold">
                  {s.prefix}<CountUp to={s.value} decimals={s.decimals} suffix={s.suffix} />
                </p>
                <p className="eyebrow mt-2">{s.label}</p>
              </div>
            </Reveal>
          ))}
        </div>

        <div className="mt-10 grid max-w-lg grid-cols-2 gap-1 rounded-xl border border-[#292929] bg-[#101010] p-1">
          {(
            [
              { key: "pending" as const, label: "Requests Awaiting Your Approval" },
              { key: "active" as const, label: "Your Active Deliveries" },
            ]
          ).map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={`rounded-lg py-2 text-xs font-semibold tracking-widest uppercase transition ${
                tab === t.key ? "bg-[#00D4AA] text-[#080808]" : "text-muted-foreground"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {!online && tab === "pending" && (
          <p className="mt-3 text-sm text-[#6B6B6B]">
            You are offline — go available to receive new requests.
          </p>
        )}

        <div className="mt-6 flex flex-col gap-4">
          {tab === "pending" ? (
            requests.isLoading ? (
              <LoadingState message="Loading requests…" size="lg" />
            ) : requests.isError ? (
              <ErrorState
                title="Could not load requests"
                description={requests.error instanceof Error ? requests.error.message : "Unknown error"}
                onRetry={() => requests.refetch()}
              />
            ) : (requests.data ?? []).length === 0 ? (
              <EmptyState
                icon={Truck}
                title="No pending requests"
                description="No parcels have requested your route yet. Publish a route and senders will match with you."
                action={
                  <Link to="/create-shipment" className="btn-primary flex items-center gap-2">
                    <Plus className="h-4 w-4" /> Publish a Route
                  </Link>
                }
              />
            ) : (
              (requests.data ?? []).map((m, i) => (
                <Reveal key={m.id} delay={i * 0.05}>
                  <RequestCard
                    m={m}
                    busy={respond.isPending}
                    onAccept={() => respond.mutate({ requestId: m.requestId!, accept: true })}
                    onReject={() => respond.mutate({ requestId: m.requestId!, accept: false })}
                  />
                </Reveal>
              ))
            )
          ) : deliveries.isLoading ? (
            <LoadingState message="Loading deliveries…" size="lg" />
          ) : deliveries.isError ? (
            <ErrorState
              title="Could not load deliveries"
              description={deliveries.error instanceof Error ? deliveries.error.message : "Unknown error"}
              onRetry={() => deliveries.refetch()}
            />
          ) : (deliveries.data ?? []).length === 0 ? (
            <EmptyState
              icon={PackageCheck}
              title="No active deliveries"
              description="Accepted parcels will appear here so you can confirm pickup and delivery."
            />
          ) : (
            (deliveries.data ?? []).map((m, i) => (
              <Reveal key={m.id} delay={i * 0.05}>
                <DeliveryCard
                  m={m}
                  busy={delivered.isPending || pickup.isPending}
                  onPickup={() => pickup.mutate(m.requestId!)}
                  onDeliver={(file) => file && delivered.mutate({ requestId: m.requestId!, file })}
                />
              </Reveal>
            ))
          )}
        </div>
      </section>
    </PageShell>
  );
}