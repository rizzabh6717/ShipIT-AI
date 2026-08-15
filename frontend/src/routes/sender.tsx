import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Package, Sparkles, CheckCircle2, Plus, Search, Star, X } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { RequireAuth } from "@/components/RequireAuth";
import { CountUp } from "@/components/CountUp";
import { useAuth } from "@/lib/auth";
import { apiClient, mediaUrl } from "@/lib/api-client";
import { LoadingState, EmptyState, ErrorState } from "@/components/LoadingStates";
import type { Shipment } from "@/lib/mock-api";

export const Route = createFileRoute("/sender")({
  head: () => ({
    meta: [
      { title: "Sender Dashboard — ShipIT AI" },
      { name: "description", content: "Track your parcels and find drivers for pending shipments." },
      { property: "og:title", content: "Sender Dashboard — ShipIT AI" },
      { property: "og:description", content: "Your shipments, matching and delivery status in one view." },
    ],
  }),
  component: () => (
    <RequireAuth role="sender">
      <SenderDashboard />
    </RequireAuth>
  ),
});

const STATUS_LABEL: Record<Shipment["status"] | string, string> = {
  pending: "Pending",
  pending_driver_approval: "Pending Driver Approval",
  accepted: "Driver Assigned",
  matched: "Matched",
  in_transit: "In Transit",
  delivered: "Delivered",
};

const STATUS_STYLE: Record<Shipment["status"] | string, string> = {
  matched: "border-[#4C9EFF]/40 bg-[#4C9EFF]/12 text-[#4C9EFF]",
  pending_driver_approval: "border-[#A78BFA]/40 bg-[#A78BFA]/12 text-[#A78BFA]",
  accepted: "border-[#A78BFA]/40 bg-[#A78BFA]/12 text-[#A78BFA]",
  pending: "border-[#FBBF24]/40 bg-[#FBBF24]/12 text-[#FBBF24]",
  in_transit: "border-[#00D4AA]/40 bg-[#00D4AA]/12 text-[#00D4AA]",
  delivered: "border-[#00D4AA]/40 bg-[#00D4AA]/12 text-[#00D4AA]",
};

function SenderDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [finding, setFinding] = useState<string | null>(null);
  const [noMatch, setNoMatch] = useState<string | null>(null);
  const [tab, setTab] = useState<"current" | "delivered">("current");
  const [feedbackFor, setFeedbackFor] = useState<Shipment | null>(null);
  const [proofFor, setProofFor] = useState<Shipment | null>(null);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

  const { data: shipments = [], isLoading, isError, error, refetch } = useQuery({
    queryKey: ["shipments"],
    queryFn: () => apiClient.listShipments(),
  });

  const submitFeedback = useMutation({
    mutationFn: ({ requestId, rating, comment }: { requestId: string; rating: number; comment: string }) =>
      apiClient.submitFeedback(requestId, rating, comment),
    onSuccess: () => {
      toast.success("Feedback recorded — thanks for rating your driver.");
      setFeedbackFor(null);
      setRating(5);
      setComment("");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Could not submit feedback"),
  });

  const current = shipments.filter((s) => s.status !== "delivered");
  const delivered = shipments.filter((s) => s.status === "delivered");

  const stats = [
    { icon: Package, label: "Active parcels", value: current.length, suffix: "" },
    { icon: Sparkles, label: "Matched", value: shipments.filter((s) => s.status === "matched").length, suffix: "" },
    { icon: CheckCircle2, label: "Delivered", value: delivered.length, suffix: "" },
    { icon: Star, label: "Feedback sent", value: shipments.filter((s) => s.status === "delivered").length, suffix: "" },
  ];

  // AI matching runs only here — when the sender explicitly clicks Find Drivers.
  const findDrivers = async (s: Shipment) => {
    if (finding) return;
    setFinding(s.id);
    setNoMatch(null);
    try {
      const matches = await apiClient.matchDrivers(s.id);
      if (matches.length > 0) {
        navigate({ to: "/driver-matching", search: { shipmentId: s.id } });
      } else {
        setNoMatch(s.id);
      }
    } catch {
      setNoMatch(s.id);
    } finally {
      setFinding(null);
    }
  };

  if (isLoading) {
    return (
      <PageShell>
        <section className="container-page section-y">
          <LoadingState message="Loading your dashboard…" size="lg" />
        </section>
      </PageShell>
    );
  }

  if (isError) {
    return (
      <PageShell>
        <section className="container-page section-y">
          <ErrorState
            title="Could not load shipments"
            description={error instanceof Error ? error.message : "Unknown error"}
            onRetry={() => refetch()}
          />
        </section>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <section className="container-page section-y">
        <Reveal className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Sender dashboard</p>
            <h1 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">
              Welcome back, {user?.name}.
            </h1>
          </div>
          <Link to="/create-parcel" className="btn-primary">
            <Plus className="h-4 w-4" /> New parcel
          </Link>
        </Reveal>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((s, i) => (
            <Reveal key={s.label} delay={i * 0.05}>
              <div className="glass-card lift p-6">
                <s.icon className="h-4 w-4 text-[#00D4AA]" />
                <p className="mt-4 font-display text-3xl font-bold">
                  <CountUp to={s.value} decimals={s.suffix ? 1 : 0} suffix={s.suffix} />
                </p>
                <p className="eyebrow mt-2">{s.label}</p>
              </div>
            </Reveal>
          ))}
        </div>

        <div className="mt-10 grid max-w-md grid-cols-2 gap-1 rounded-xl border border-[#292929] bg-[#101010] p-1">
          {(
            [
              { key: "current" as const, label: "Current Parcels" },
              { key: "delivered" as const, label: "Delivered Parcels" },
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

        <div className="mt-6 flex flex-col gap-4">
          {(tab === "current" ? current : delivered).length === 0 ? (
            <EmptyState
              icon={Package}
              title={tab === "current" ? "No active parcels" : "No delivered parcels yet"}
              description={
                tab === "current"
                  ? "Create your first parcel to get started."
                  : "Delivered parcels and their proof photos will appear here."
              }
              action={
                tab === "current" ? (
                  <Link to="/create-parcel" className="btn-primary"><Plus className="h-4 w-4" /> Send a Parcel</Link>
                ) : undefined
              }
            />
          ) : (
            (tab === "current" ? current : delivered).map((s, i) => (
              <Reveal key={s.id} delay={i * 0.04}>
                <div className="glass-card lift p-6">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="eyebrow">{s.id}</p>
                      <p className="mt-2 font-display text-lg font-bold">
                        {s.from} → {s.to}
                      </p>
                      <p className="mt-1 text-xs text-[#6B6B6B]">
                        {s.weight} kg{s.dimensions ? ` · ${s.dimensions}` : ""} · {s.eta} · ₹{s.price}
                      </p>
                      {s.description && (
                        <p className="mt-1 text-xs text-[#6B6B6B]">{s.description}</p>
                      )}
                    </div>
                    <span
                      className={`rounded-full border px-3 py-1 text-[10px] font-semibold tracking-widest uppercase ${STATUS_STYLE[s.status]}`}
                    >
                      {STATUS_LABEL[s.status]}
                    </span>
                  </div>

                  {tab === "delivered" && (
                    <div className="mt-5 flex flex-wrap items-center gap-4">
                      {s.proofImageUrl ? (
                        <>
                          <a
                            href={mediaUrl(s.proofImageUrl)}
                            target="_blank"
                            rel="noreferrer"
                            className="group block overflow-hidden rounded-xl border border-[#292929]"
                          >
                            <img
                              src={mediaUrl(s.proofImageUrl)}
                              alt="Proof of delivery"
                              className="h-32 w-48 object-cover transition group-hover:opacity-80"
                            />
                          </a>
                          <button
                            onClick={() => setProofFor(s)}
                            className="btn-secondary !py-2 flex items-center gap-1.5"
                          >
                            <Package className="h-3.5 w-3.5" /> View Proof
                          </button>
                        </>
                      ) : (
                        <span className="flex items-center gap-1.5 text-xs text-[#6B6B6B]">
                          <Package className="h-3.5 w-3.5" /> No proof photo attached yet
                        </span>
                      )}

                      {s.requestId ? (
                        <button
                          onClick={() => setFeedbackFor(s)}
                          className="btn-primary !py-2 flex items-center gap-1.5"
                        >
                          <Star className="h-3.5 w-3.5" /> Rate Driver
                        </button>
                      ) : null}
                    </div>
                  )}

                  <div className="mt-5 flex flex-wrap gap-2">
                    <Link
                      to="/tracking"
                      search={{ shipmentId: s.id }}
                      className="btn-secondary !py-2 flex items-center gap-1.5"
                    >
                      <Search className="h-3.5 w-3.5" /> Track
                    </Link>

                    {s.status === "pending" && (
                      <button
                        onClick={() => findDrivers(s)}
                        disabled={finding === s.id}
                        className="btn-primary !py-2 flex items-center gap-1.5 disabled:opacity-60"
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                        {finding === s.id ? "Matching…" : "Find Drivers"}
                      </button>
                    )}

                    {s.status === "pending_driver_approval" && (
                      <span className="flex items-center gap-1.5 text-xs text-[#A78BFA]">
                        <Sparkles className="h-3.5 w-3.5" /> Awaiting driver approval
                      </span>
                    )}

                    {(s.status === "matched" || s.status === "in_transit") && (
                      <span className="flex items-center gap-1.5 text-xs text-[#6B6B6B]">
                        <Sparkles className="h-3.5 w-3.5" /> Delivery request active
                      </span>
                    )}
                  </div>

                  {noMatch === s.id && (
                    <div className="mt-5 rounded-xl border border-[#FBBF24]/30 bg-[#FBBF24]/8 p-5">
                      <p className="text-sm font-medium text-foreground">
                        No drivers currently available for this route.
                      </p>
                      <p className="mt-1 text-xs text-[#6B6B6B]">
                        No compatible driver route exists yet. Try again later or adjust the parcel.
                      </p>
                    </div>
                  )}
                </div>
              </Reveal>
            ))
          )}
        </div>

        {proofFor && proofFor.proofImageUrl && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
            onClick={() => setProofFor(null)}
          >
            <div
              className="glass-card w-full max-w-2xl rounded-3xl p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="eyebrow">Proof of delivery</p>
                  <h2 className="mt-2 font-display text-xl font-bold">
                    {proofFor.from} → {proofFor.to}
                  </h2>
                </div>
                <button
                  onClick={() => setProofFor(null)}
                  className="btn-secondary !px-3 !py-2"
                  aria-label="Close proof"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <img
                src={mediaUrl(proofFor.proofImageUrl)}
                alt="Proof of delivery"
                className="mt-5 w-full rounded-2xl border border-[#292929] object-contain"
              />
              <a
                href={mediaUrl(proofFor.proofImageUrl)}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary mt-4 w-full flex items-center justify-center gap-2"
              >
                Open in new tab
              </a>
            </div>
          </div>
        )}

        {feedbackFor && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setFeedbackFor(null)}>
            <div className="glass-card w-full max-w-md rounded-3xl p-8" onClick={(e) => e.stopPropagation()}>
              <p className="eyebrow">Rate your driver</p>
              <h2 className="mt-2 font-display text-xl font-bold">{feedbackFor.from} → {feedbackFor.to}</h2>
              <div className="mt-5 flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setRating(v)}
                    className={`text-3xl transition ${v <= rating ? "text-[#FBBF24]" : "text-[#292929]"}`}
                  >
                    ★
                  </button>
                ))}
              </div>
              <textarea
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="How was the delivery? (optional)"
                className="mt-5 w-full rounded-lg px-3 py-2.5 text-sm"
              />
              <div className="mt-5 flex gap-3">
                <button
                  onClick={() => setFeedbackFor(null)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={() =>
                    feedbackFor.requestId &&
                    submitFeedback.mutate({ requestId: feedbackFor.requestId, rating, comment })
                  }
                  disabled={submitFeedback.isPending}
                  className="btn-primary flex-1 disabled:opacity-60"
                >
                  {submitFeedback.isPending ? "Submitting…" : "Submit rating"}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </PageShell>
  );
}