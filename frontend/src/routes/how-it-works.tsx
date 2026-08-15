import { createFileRoute, Link } from "@tanstack/react-router";
import { PackageCheck, Sparkles, Truck } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { RouteMap, ROUTES, type Stop } from "@/components/RouteMap";

export const Route = createFileRoute("/how-it-works")({
  head: () => ({
    meta: [
      { title: "How It Works — ShipIT AI" },
      {
        name: "description",
        content:
          "Post a parcel, let semantic AI match it to a driver already on the route, then track it to the door.",
      },
      { property: "og:title", content: "How It Works — ShipIT AI" },
      {
        property: "og:description",
        content: "Three steps: post, AI match, deliver — explained end to end.",
      },
    ],
  }),
  component: HowItWorks,
});

const ROWS = [
  {
    icon: PackageCheck,
    title: "POST",
    body: "Describe the parcel once: pickup, drop, weight, dimensions and the deadline that actually matters. ShipIT AI turns it into a route embedding immediately — no quotes, no back and forth.",
    cta: "Post a parcel",
    to: "/create-parcel" as const,
    path: ROUTES.simple,
    stops: [
      { x: 48, y: 208, label: "Delhi", kind: "origin" },
      { x: 348, y: 54, label: "Noida", kind: "dest", anchor: "end", dy: -10 },
    ] as Stop[],
  },
  {
    icon: Sparkles,
    title: "AI MATCH",
    body: "Every live driver route is scored against your parcel for semantic overlap, added detour, remaining capacity and reliability. The winning match arrives with the reasons attached.",
    cta: "See the match engine",
    to: "/ai-matching" as const,
    path: ROUTES.viaDriver,
    stops: [
      { x: 48, y: 208, label: "Delhi", kind: "origin" },
      { x: 224, y: 132, label: "Driver en route", kind: "driver" },
      { x: 348, y: 54, label: "Noida", kind: "dest", anchor: "end", dy: -10 },
    ] as Stop[],
  },
  {
    icon: Truck,
    title: "DELIVER",
    body: "The driver collects on the way past, and you follow the parcel in real time with a live ETA that updates against traffic — right through to proof of delivery.",
    cta: "Track a shipment",
    to: "/tracking" as const,
    path: ROUTES.full,
    stops: [
      { x: 48, y: 208, label: "Delhi", kind: "origin" },
      { x: 158, y: 152, label: "Pickup Rohini", kind: "parcel" },
      { x: 348, y: 54, label: "Noida", kind: "dest", anchor: "end", dy: -10 },
    ] as Stop[],
  },
];

function HowItWorks() {
  return (
    <PageShell>
      <section className="container-page section-y">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">How it works</p>
          <h1 className="mt-4 font-display text-4xl font-bold tracking-tight sm:text-5xl">
            Three steps from doorstep to doorstep.
          </h1>
          <p className="mt-5 text-muted-foreground">
            No dedicated trip is created. Your parcel joins a journey that was already happening.
          </p>
        </Reveal>

        <div className="mt-14 flex flex-col gap-8">
          {ROWS.map((row, i) => (
            <Reveal key={row.title} delay={i * 0.06}>
              <div className="rounded-3xl border border-[#292929] bg-[#101010] p-8">
                <div
                  className="grid items-center gap-8 lg:grid-cols-2"
                  style={{ direction: i % 2 === 1 ? "rtl" : "ltr" }}
                >
                  <div style={{ direction: "ltr" }}>
                    <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#00D4AA]/12 text-[#00D4AA]">
                      <row.icon className="h-5 w-5" />
                    </span>
                    <h2 className="mt-5 font-display text-3xl font-bold tracking-wide">
                      {row.title}
                    </h2>
                    <p className="mt-4 max-w-lg text-[#6B6B6B]">{row.body}</p>
                    <Link to={row.to} className="btn-secondary mt-7">
                      {row.cta}
                    </Link>
                  </div>
                  <div style={{ direction: "ltr" }}>
                    <RouteMap className="h-64" paths={[{ d: row.path, trucks: 1 }]} stops={row.stops} />
                  </div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>
    </PageShell>
  );
}
