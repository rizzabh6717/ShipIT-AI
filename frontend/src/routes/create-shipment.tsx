import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Plus, MapPin, Truck, Clock, Leaf, Sparkles, ArrowRight } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { RequireAuth } from "@/components/RequireAuth";
import { RouteMap, ROUTES } from "@/components/RouteMap";
import { ProgressBar } from "@/components/ProgressBar";
import { apiClient } from "@/lib/api-client";
import { LoadingState, EmptyState, ErrorState } from "@/components/LoadingStates";

export const Route = createFileRoute("/create-shipment")({
  head: () => ({
    meta: [
      { title: "Publish Route — ShipIT AI" },
      {
        name: "description",
        content: "Drivers can publish their planned routes to receive parcel matches and earn extra income.",
      },
      { property: "og:title", content: "Publish Route — ShipIT AI" },
    ],
  }),
  component: () => (
    <RequireAuth role="driver">
      <CreateShipmentPage />
    </RequireAuth>
  ),
});

const CITIES = [
  "Delhi",
  "Noida",
  "Gurgaon",
  "Ghaziabad",
  "Faridabad",
  "Greater Noida",
  "Manesar",
  "Bahadurgarh",
];

const VEHICLE_TYPES = [
  { value: "bike", label: "Bike / Scooter", capacity: 50 },
  { value: "van", label: "Van (Tata Ace)", capacity: 750 },
  { value: "pickup", label: "Pickup (Bolero)", capacity: 1200 },
  { value: "truck_small", label: "Small Truck (Eicher 10ft)", capacity: 2000 },
  { value: "truck_large", label: "Large Truck (16ft+)", capacity: 5000 },
];

function CreateShipmentPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    from: "Delhi",
    to: "Noida",
    departureTime: "",
    vehicleType: "van",
    capacityKg: "750",
    availableSpaceKg: "500",
    pricePerKg: "15",
    description: "",
    recurring: false,
    recurrenceDays: [] as string[],
  });
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ routeId: string; matches: number } | null>(null);

  const set = (k: keyof typeof form, v: string | boolean | string[]) =>
    setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.from === form.to) {
      toast.error("Origin and destination must differ");
      return;
    }
    if (!form.departureTime) {
      toast.error("Please select a departure time");
      return;
    }
    setBusy(true);
    try {
      const vehicle = VEHICLE_TYPES.find((v) => v.value === form.vehicleType);
      const res = await apiClient.createDriverRoute({
        from: form.from,
        to: form.to,
        departureTime: form.departureTime,
        vehicleType: form.vehicleType,
        vehicleLabel: vehicle?.label ?? form.vehicleType,
        capacityKg: Number(form.capacityKg) || 1,
        availableSpaceKg: Number(form.availableSpaceKg) || 1,
        pricePerKg: Number(form.pricePerKg) || 15,
        description: form.description,
        recurring: form.recurring,
        recurrenceDays: form.recurrenceDays as string[],
      });
      setResult({ routeId: res.id, matches: 0 });
      toast.success(`Route published! Your route ID: ${res.id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not publish route");
    } finally {
      setBusy(false);
    }
  };

  const estimatedEarnings = Math.round(
    (Number(form.availableSpaceKg) || 0) * (Number(form.pricePerKg) || 0)
  );
  const co2Saved = (Number(form.availableSpaceKg) || 0) * 0.02;

  const field = "mt-2 w-full rounded-lg px-3 py-2.5 text-sm";

  return (
    <PageShell>
      <section className="container-page section-y">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">Publish a route</p>
          <h1 className="mt-4 font-display text-4xl font-bold tracking-tight">Monetize your journey.</h1>
          <p className="mt-4 text-muted-foreground">
            Tell us where you're headed and when. We'll match parcels along your way — extra income, zero detour.
          </p>
        </Reveal>

        <div className="mt-12 grid items-start gap-8 lg:grid-cols-2">
          <Reveal>
            <form onSubmit={submit} className="glass-card rounded-3xl p-8">
              <div className="grid gap-5 sm:grid-cols-2">
                <div>
                  <label className="eyebrow" htmlFor="from">Origin city</label>
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
                  <label className="eyebrow" htmlFor="to">Destination city</label>
                  <select
                    id="to"
                    value={form.to}
                    onChange={(e) => set("to", e.target.value)}
                    className={field}
                  >
                    {CITIES.filter((c) => c !== form.from).map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="eyebrow" htmlFor="departureTime">Departure date & time</label>
                  <input
                    id="departureTime"
                    type="datetime-local"
                    value={form.departureTime}
                    onChange={(e) => set("departureTime", e.target.value)}
                    className={field}
                  />
                </div>
                <div>
                  <label className="eyebrow" htmlFor="vehicleType">Vehicle type</label>
                  <select
                    id="vehicleType"
                    value={form.vehicleType}
                    onChange={(e) => {
                      set("vehicleType", e.target.value);
                      const vt = VEHICLE_TYPES.find((v) => v.value === e.target.value);
                      if (vt) set("capacityKg", String(vt.capacity));
                    }}
                    className={field}
                  >
                    {VEHICLE_TYPES.map((v) => (
                      <option key={v.value} value={v.value}>
                        {v.label} ({v.capacity} kg)
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-5 grid gap-5 sm:grid-cols-2">
                <div>
                  <label className="eyebrow" htmlFor="capacityKg">Total capacity (kg)</label>
                  <input
                    id="capacityKg"
                    type="number"
                    min="1"
                    value={form.capacityKg}
                    onChange={(e) => set("capacityKg", e.target.value)}
                    className={field}
                  />
                </div>
                <div>
                  <label className="eyebrow" htmlFor="availableSpaceKg">Available space (kg)</label>
                  <input
                    id="availableSpaceKg"
                    type="number"
                    min="1"
                    max={Number(form.capacityKg) || 9999}
                    value={form.availableSpaceKg}
                    onChange={(e) => set("availableSpaceKg", e.target.value)}
                    className={field}
                  />
                </div>
                <div>
                  <label className="eyebrow" htmlFor="pricePerKg">Price per kg (₹)</label>
                  <input
                    id="pricePerKg"
                    type="number"
                    step="0.5"
                    min="1"
                    value={form.pricePerKg}
                    onChange={(e) => set("pricePerKg", e.target.value)}
                    className={field}
                  />
                </div>
              </div>

              <div className="mt-5">
                <label className="eyebrow" htmlFor="description">Description (optional)</label>
                <textarea
                  id="description"
                  rows={3}
                  value={form.description}
                  onChange={(e) => set("description", e.target.value)}
                  placeholder="e.g., Daily Delhi-Noida run, leave 9 AM, return 6 PM. Cold chain available."
                  className={field}
                />
              </div>

              <div className="mt-5 flex items-center gap-3">
                <input
                  type="checkbox"
                  id="recurring"
                  checked={form.recurring}
                  onChange={(e) => set("recurring", e.target.checked)}
                  className="rounded border-[#292929] bg-[#101010] text-[#00D4AA] focus:ring-[#00D4AA]"
                />
                <label htmlFor="recurring" className="text-sm text-muted-foreground">
                  Recurring route (same schedule daily)
                </label>
              </div>

              {form.recurring && (
                <div className="mt-3">
                  <label className="eyebrow">Recurrence days</label>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => (
                      <button
                        key={day}
                        type="button"
                        onClick={() =>
                          set(
                            "recurrenceDays",
                            (form.recurrenceDays as string[]).includes(day)
                              ? (form.recurrenceDays as string[]).filter((d) => d !== day)
                              : [...(form.recurrenceDays as string[]), day]
                          )
                        }
                        className={`rounded-full border px-3 py-1 text-xs font-semibold tracking-wider uppercase transition ${
                          (form.recurrenceDays as string[]).includes(day)
                            ? "border-[#00D4AA] bg-[#00D4AA]/12 text-[#00D4AA]"
                            : "border-[#292929] bg-[#101010] text-muted-foreground"
                        }`}
                      >
                        {day}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <button type="submit" disabled={busy} className="btn-primary mt-8 w-full disabled:opacity-60">
                <Sparkles className="h-4 w-4" />
                {busy ? "Publishing route…" : "Publish Route"}
              </button>
            </form>
          </Reveal>

          <Reveal delay={0.08}>
            <RouteMap
              className="h-[300px]"
              paths={[{ d: ROUTES.viaDriver, trucks: 1 }]}
              stops={[
                { x: 48, y: 208, label: form.from, kind: "origin" },
                { x: 224, y: 132, label: "Your route", kind: "driver" },
                { x: 348, y: 54, label: form.to, kind: "dest", anchor: "end", dy: -10 },
              ]}
            />

            <div className="glass-card mt-6 p-6">
              <p className="eyebrow">Route preview</p>
              <h2 className="mt-3 font-display text-xl font-bold">
                {form.from} → {form.to}
              </h2>
              <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div>
                  <p className="eyebrow">Est. earnings</p>
                  <p className="mt-1.5 font-display text-lg font-bold text-[#00D4AA]">
                    ₹{estimatedEarnings.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="eyebrow">Available space</p>
                  <p className="mt-1.5 font-display text-lg font-bold">{form.availableSpaceKg} kg</p>
                </div>
                <div>
                  <p className="eyebrow">CO₂ saved</p>
                  <p className="mt-1.5 font-display text-lg font-bold text-[#00D4AA]">
                    {co2Saved.toFixed(1)} kg
                  </p>
                </div>
                <div>
                  <p className="eyebrow">Price/kg</p>
                  <p className="mt-1.5 font-display text-lg font-bold">₹{form.pricePerKg}</p>
                </div>
              </div>

              <div className="mt-5">
                <ProgressBar
                  value={Math.min(100, Math.round((Number(form.availableSpaceKg) || 0) / (Number(form.capacityKg) || 1) * 100))}
                  color="#4C9EFF"
                  label="Capacity utilization"
                  valueLabel={`${Math.round((Number(form.availableSpaceKg) || 0) / (Number(form.capacityKg) || 1) * 100)}%`}
                />
              </div>

              {result && (
                <div className="mt-6 p-4 rounded-xl border border-[#00D4AA]/40 bg-[#00D4AA]/10">
                  <div className="flex items-center gap-2 text-[#00D4AA]">
                    <Sparkles className="h-4 w-4" />
                    <p className="eyebrow">Route published!</p>
                  </div>
                  <p className="mt-2 font-display text-lg font-bold">Route ID: {result.routeId}</p>
                  <p className="mt-1 text-sm text-[#6B6B6B]">
                    Waiting for parcel matches… Refresh the driver dashboard to see new matches.
                  </p>
                  <button
                    onClick={() => navigate({ to: "/driver" })}
                    className="btn-secondary mt-4 w-full"
                  >
                    Go to Dashboard
                  </button>
                </div>
              )}
            </div>
          </Reveal>
        </div>
      </section>
    </PageShell>
  );
}