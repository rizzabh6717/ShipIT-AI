import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Sparkles, ShieldCheck, Wand2 } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { RequireAuth } from "@/components/RequireAuth";
import { RouteMap, ROUTES } from "@/components/RouteMap";
import { apiClient } from "@/lib/api-client";
import type { Shipment, BudgetRecommendation } from "@/lib/mock-api";

export const Route = createFileRoute("/create-parcel")({
  head: () => ({
    meta: [
      { title: "Create a Parcel — ShipIT AI" },
      {
        name: "description",
        content: "Post a parcel with origin, destination, weight and deadline, and get matched instantly.",
      },
      { property: "og:title", content: "Create a Parcel — ShipIT AI" },
      { property: "og:description", content: "Post a parcel and let AI find a driver already going." },
    ],
  }),
  component: () => (
    <RequireAuth role="sender">
      <CreateParcel />
    </RequireAuth>
  ),
});

const CITIES = ["Delhi", "Noida", "Gurgaon", "Ghaziabad", "Faridabad"];

function CreateParcel() {
  const [form, setForm] = useState({
    from: "Delhi",
    to: "Noida",
    weight: "2.4",
    dimensions: "30 × 20 × 15 cm",
    description: "",
    deadline: "",
    budget: "100",
  });
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Shipment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recs, setRecs] = useState<BudgetRecommendation | null>(null);
  const [recommending, setRecommending] = useState(false);

  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const recommend = async () => {
    if (form.from === form.to) {
      toast.error("Origin and destination must differ");
      return;
    }
    setRecommending(true);
    try {
      const rec = await apiClient.recommendBudget({
        from: form.from,
        to: form.to,
        weight: Number(form.weight) || 1,
        dimensions: form.dimensions,
      });
      setRecs(rec);
      setForm((f) => ({ ...f, budget: String(rec.totalAmount) }));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not recommend a budget");
    } finally {
      setRecommending(false);
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.from === form.to) {
      toast.error("Origin and destination must differ");
      return;
    }
    if (!form.deadline) {
      toast.error("A delivery deadline is required");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const shipment = await apiClient.createShipment({
        from: form.from,
        to: form.to,
        weight: Number(form.weight) || 1,
        dimensions: form.dimensions,
        description: form.description,
        deadline: form.deadline,
        budget: Number(form.budget) || 100,
      });
      setResult(shipment);
      toast.success("Parcel posted. Find drivers from your dashboard.");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Could not create the shipment";
      setError(msg);
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  };

  const field = "mt-2 w-full rounded-lg px-3 py-2.5 text-sm";

  return (
    <PageShell>
      <section className="container-page section-y">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">New shipment</p>
          <h1 className="mt-4 font-display text-4xl font-bold tracking-tight">Post a parcel.</h1>
          <p className="mt-4 text-muted-foreground">
            Tell us the essentials — the matching engine handles the rest.
          </p>
        </Reveal>

        <div className="mt-12 grid items-start gap-8 lg:grid-cols-2">
          <Reveal>
            <form onSubmit={submit} className="glass-card rounded-3xl p-8">
              {error && (
                <div className="mb-5 p-3 rounded-lg border border-[#FBBF24]/40 bg-[#FBBF24]/10 text-[#FBBF24] text-sm">
                  {error}
                </div>
              )}
              <div className="grid gap-5 sm:grid-cols-2">
                <div>
                  <label className="eyebrow" htmlFor="from">
                    Origin city
                  </label>
                  <select
                    id="from"
                    value={form.from}
                    onChange={(e) => set("from", e.target.value)}
                    className={field}
                  >
                    {CITIES.map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="eyebrow" htmlFor="to">
                    Destination city
                  </label>
                  <select
                    id="to"
                    value={form.to}
                    onChange={(e) => set("to", e.target.value)}
                    className={field}
                  >
                    {CITIES.map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="eyebrow" htmlFor="weight">
                    Weight (kg)
                  </label>
                  <input
                    id="weight"
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={form.weight}
                    onChange={(e) => set("weight", e.target.value)}
                    className={field}
                  />
                </div>
                <div>
                  <label className="eyebrow" htmlFor="budget">
                    Budget (₹)
                  </label>
                  <div className="flex gap-2">
                    <input
                      id="budget"
                      type="number"
                      step="1"
                      min="0"
                      value={form.budget}
                      onChange={(e) => set("budget", e.target.value)}
                      className={`${field} mt-0 flex-1`}
                    />
                    <button
                      type="button"
                      onClick={recommend}
                      disabled={recommending}
                      className="btn-secondary !py-2 flex items-center gap-1.5 whitespace-nowrap"
                    >
                      <Wand2 className="h-3.5 w-3.5" />
                      {recommending ? "Estimating…" : "Auto"}
                    </button>
                  </div>
                  {recs && (
                    <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
                      <span className="rounded-full border border-[#4C9EFF]/40 bg-[#4C9EFF]/12 px-2.5 py-1 text-[#4C9EFF]">
                        Recommended ₹{recs.recommendedBudget}
                      </span>
                      <span className="rounded-full border border-[#00D4AA]/40 bg-[#00D4AA]/12 px-2.5 py-1 text-[#00D4AA]">
                        Total ₹{recs.totalAmount}
                      </span>
                    </div>
                  )}
                  {recs && (
                    <p className="mt-2 text-[11px] text-[#6B6B6B]">{recs.explanation}</p>
                  )}
                  <p className="mt-1 text-[11px] text-[#6B6B6B]">
                    You can still adjust the budget before posting.
                  </p>
                </div>
                <div>
                  <label className="eyebrow" htmlFor="dimensions">
                    Dimensions
                  </label>
                  <input
                    id="dimensions"
                    value={form.dimensions}
                    onChange={(e) => set("dimensions", e.target.value)}
                    className={field}
                  />
                </div>
              </div>

              <div className="mt-5">
                <label className="eyebrow" htmlFor="description">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={3}
                  value={form.description}
                  onChange={(e) => set("description", e.target.value)}
                  placeholder="Two laptops, fragile, handle upright"
                  className={field}
                />
              </div>

              <div className="mt-5">
                <label className="eyebrow" htmlFor="deadline">
                  Delivery deadline <span className="text-[#FBBF24]">*</span>
                </label>
                <input
                  id="deadline"
                  type="date"
                  required
                  value={form.deadline}
                  onChange={(e) => set("deadline", e.target.value)}
                  className={field}
                />
                <p className="mt-1 text-[11px] text-[#6B6B6B]">
                  Required — matching and on-time scoring depend on it.
                </p>
              </div>

              <button type="submit" disabled={busy} className="btn-primary mt-8 w-full disabled:opacity-60">
                <Sparkles className="h-4 w-4" />
                {busy ? "Posting parcel…" : "Post Parcel"}
              </button>
            </form>
          </Reveal>

          <Reveal delay={0.08}>
            <RouteMap
              className="h-[300px]"
              paths={[{ d: ROUTES.viaDriver, trucks: 1 }]}
              stops={[
                { x: 48, y: 208, label: form.from, kind: "origin" },
                { x: 224, y: 132, label: "Your parcel", kind: "parcel" },
                { x: 348, y: 54, label: form.to, kind: "dest", anchor: "end", dy: -10 },
              ]}
            />

            {result && (
              <div className="glass-card mt-6 p-6">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-[#00D4AA]" />
                  <p className="eyebrow">Parcel posted · {result.id}</p>
                </div>
                <p className="mt-2 text-sm text-[#6B6B6B]">
                  {result.from} → {result.to} · {result.weight} kg · ₹{result.price}
                </p>
                <p className="mt-4 text-sm text-muted-foreground">
                  Matching is not automatic. Open your dashboard and use{" "}
                  <span className="font-medium text-[#00D4AA]">Find Drivers</span> to compute and
                  review ranked driver matches for this parcel.
                </p>
                <div className="mt-5 flex flex-col gap-2">
                  <Link to="/sender" className="btn-primary w-full flex items-center justify-center gap-2">
                    <Sparkles className="h-4 w-4" /> Go to dashboard
                  </Link>
                </div>
              </div>
            )}
          </Reveal>
        </div>
      </section>
    </PageShell>
  );
}