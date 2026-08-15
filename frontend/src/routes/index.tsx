import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { Sparkles, Truck, PackageCheck } from "lucide-react";
import { PageShell, Reveal, fadeUp } from "@/components/PageShell";
import { RouteMap, ROUTES } from "@/components/RouteMap";
import { useAuth } from "@/lib/auth";
import { apiClient } from "@/lib/api-client";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ShipIT AI — Your package already has a route" },
      {
        name: "description",
        content:
          "Semantic route matching and explainable AI connect your parcel with drivers already travelling your way across Delhi-NCR.",
      },
      { property: "og:title", content: "ShipIT AI — Your package already has a route" },
      {
        property: "og:description",
        content: "Match parcels with drivers already on the road. No dedicated trip, no wasted fuel.",
      },
    ],
  }),
  component: Landing,
});

const STEPS = [
  {
    icon: PackageCheck,
    tag: "POST",
    body: "Post your parcel in seconds — origin, destination, weight and deadline. No quotes, no phone calls, no waiting rooms.",
    to: "/create-parcel" as const,
  },
  {
    icon: Sparkles,
    tag: "AI MATCH",
    body: "Semantic embeddings score every live route for overlap, detour, capacity and driver reliability — then explain the pick.",
    to: "/ai-matching" as const,
  },
  {
    icon: Truck,
    tag: "DELIVER",
    body: "Follow the parcel down the road with real-time tracking, live ETA updates and proof of delivery at the door.",
    to: "/tracking" as const,
  },
];

function Landing() {
  const { user, loading } = useAuth();

  useEffect(() => {
    if (loading || !user) return;
  }, [user, loading]);

  const { data: routes = [] } = useQuery({
    queryKey: ["landing-routes"],
    queryFn: () => apiClient.listActiveDriverRoutes(),
  });

  const corridors = useMemo(() => {
    const map = new Map<string, { drivers: number; capacity: number }>();
    for (const r of routes) {
      const key = `${r.from} → ${r.to}`;
      const cur = map.get(key) ?? { drivers: 0, capacity: 0 };
      cur.drivers += 1;
      cur.capacity += r.availableSpaceKg;
      map.set(key, cur);
    }
    return [...map.entries()]
      .map(([label, v]) => ({ label, ...v }))
      .sort((a, b) => b.drivers - a.drivers);
  }, [routes]);

  const totalDrivers = routes.length;
  const top = routes[0] ?? null;
  const topCorridor = corridors[0] ?? null;

  return (
    <PageShell>
        {/* HERO */}
      <section className="container-page grid items-start gap-10 pt-16 pb-12 lg:grid-cols-[1fr_440px] lg:pt-24">
        <motion.div variants={fadeUp}>
          <p className="eyebrow">Semantic route matching · pgvector · explainable AI</p>
          <h1 className="mt-5 font-display text-5xl leading-[0.95] font-bold tracking-tight sm:text-6xl lg:text-7xl">
            YOUR PACKAGE.
            <br />
            <span className="text-[#00D4AA]">ALREADY HAS A ROUTE.</span>
          </h1>
          <p className="mt-6 max-w-xl text-base text-muted-foreground sm:text-lg">
            ShipIT AI uses semantic route matching and explainable AI to connect your parcel with
            drivers already travelling your way.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/create-parcel" className="btn-primary">
              <Sparkles className="h-4 w-4" /> Send a Parcel
            </Link>
            <Link to="/auth" className="btn-secondary">
              <Truck className="h-4 w-4" /> Become a Driver
            </Link>
          </div>
          <p className="mt-6 text-xs text-[#6B6B6B]">
            {totalDrivers > 0
              ? `${totalDrivers} driver${totalDrivers === 1 ? "" : "s"} on ${corridors.length} live corridor${corridors.length === 1 ? "" : "s"} across Delhi-NCR`
              : "No driver routes published yet — be the first on the road"}
          </p>
        </motion.div>

        <motion.div variants={fadeUp} className="relative">
          <RouteMap
            className="h-[300px] sm:h-[360px] lg:h-[400px]"
            paths={[{ d: ROUTES.full, trucks: totalDrivers > 0 ? 2 : 0 }]}
            stops={[
              { x: 48, y: 208, label: top?.from ?? "Delhi", kind: "origin" },
              { x: 158, y: 152, label: "Parcel", kind: "parcel" },
              { x: 292, y: 92, label: top?.driverName ?? "Driver", kind: "driver", anchor: "end" },
              { x: 348, y: 54, label: top?.to ?? "Noida", kind: "dest", anchor: "end", dy: -10 },
            ]}
          />
          <div className="absolute top-4 left-4 rounded-xl border border-[#292929] bg-[#101010]/85 px-3 py-2 backdrop-blur">
            <div className="flex items-center gap-2 text-[10px] tracking-widest text-[#6B6B6B] uppercase">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#00D4AA] opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#00D4AA]" />
              </span>
              {totalDrivers > 0 ? "Live routes" : "Awaiting routes"}
            </div>
            <p className="mt-1 text-xs font-semibold text-foreground">
              {topCorridor ? `${topCorridor.label}` : "No drivers available yet"}
            </p>
          </div>
          <div className="absolute top-4 right-4 rounded-full border border-[#292929] bg-[#101010]/85 px-3 py-1.5 text-[11px] text-muted-foreground backdrop-blur">
            {top ? `${top.driverName} · ${top.vehicleLabel}` : "Publish a route to appear here"}
          </div>
          <div className="absolute bottom-4 left-4 rounded-full border border-[#292929] bg-[#101010]/85 px-3 py-1.5 text-[11px] text-muted-foreground backdrop-blur">
            {top ? `${top.from} → ${top.to} · ${Math.round(top.availableSpaceKg)} kg free` : "Delhi-NCR coverage"}
          </div>
        </motion.div>
      </section>

      {/* HOW IT WORKS */}
      <section className="container-page section-y">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="eyebrow">How ShipIT AI works</p>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Intelligent matching for every shipment.
          </h2>
        </Reveal>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <Reveal key={s.tag} delay={i * 0.08}>
              <div className="glass-card lift flex h-full min-h-[220px] flex-col p-6">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#00D4AA]/12 text-[#00D4AA]">
                  <s.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-5 font-display text-lg font-bold tracking-wide">{s.tag}</h3>
                <p className="mt-3 text-sm text-muted-foreground">{s.body}</p>
                <Link
                  to={s.to}
                  className="mt-auto pt-5 text-sm font-medium text-[#00D4AA] hover:underline"
                >
                  Explore →
                </Link>
              </div>
            </Reveal>
          ))}
        </div>
      </section>
    </PageShell>
  );
}
