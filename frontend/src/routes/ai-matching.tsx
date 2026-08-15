import { createFileRoute } from "@tanstack/react-router";
import { MapPin, Sparkles, ShieldCheck, Truck, Star, Zap, Clock } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { RouteMap, ROUTES } from "@/components/RouteMap";

export const Route = createFileRoute("/ai-matching")({
  head: () => ({
    meta: [
      { title: "AI Matching — ShipIT AI" },
      {
        name: "description",
        content:
          "Explainable AI scores route overlap, detour, capacity and driver reliability to pick the best match for your parcel.",
      },
      { property: "og:title", content: "AI Matching — ShipIT AI" },
      {
        property: "og:description",
        content: "See how a driver match is scored and explained, factor by factor.",
      },
    ],
  }),
  component: AiMatching,
});

const FACTORS = [
  { icon: MapPin, text: "Route overlap — does the driver's route cover pickup and drop?" },
  { icon: Truck, text: "Pickup detour — how far off the planned route is the pickup?" },
  { icon: Zap, text: "Capacity — can the vehicle still carry this parcel?" },
  { icon: Star, text: "Reliability — rating and on-time delivery history" },
  { icon: Clock, text: "Deadline — can the driver still meet the delivery deadline?" },
  { icon: ShieldCheck, text: "Availability — is the driver online and accepting parcels?" },
];

function AiMatching() {
  return (
    <PageShell>
      <section className="container-page section-y">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">Explainable matching</p>
          <h1 className="mt-4 font-display text-4xl font-bold tracking-tight sm:text-5xl">
            Every match comes with its reasons.
          </h1>
          <p className="mt-4 text-muted-foreground">
            When you post a parcel, ShipIT AI compares your route against every active driver route
            and scores each driver across the factors below. Only compatible drivers are recommended —
            and every score comes with a plain-English explanation.
          </p>
        </Reveal>

        <div className="mt-12 grid items-start gap-8 lg:grid-cols-2">
          <Reveal>
            <RouteMap
              className="h-[440px]"
              paths={[{ d: ROUTES.full, trucks: 2 }]}
              stops={[
                { x: 48, y: 208, label: "Delhi", kind: "origin" },
                { x: 158, y: 152, label: "Pickup", kind: "parcel" },
                { x: 292, y: 92, label: "Driver", kind: "driver", anchor: "end" },
                { x: 348, y: 54, label: "Noida", kind: "dest", anchor: "end", dy: -10 },
              ]}
            />
            <p className="mt-4 text-xs text-[#6B6B6B]">
              Route overlap · detour · capacity · reliability · deadline — scored per driver, explained
              for every recommendation
            </p>
          </Reveal>

          <Reveal delay={0.08}>
            <div className="glass-card rounded-3xl p-6">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-[#4C9EFF]" />
                <span className="eyebrow">How matches are scored</span>
              </div>
              <ul className="mt-4 space-y-3">
                {FACTORS.map((f) => (
                  <li key={f.text} className="flex items-start gap-3">
                    <f.icon className="mt-0.5 h-4 w-4 shrink-0 text-[#4C9EFF]" />
                    <span className="text-sm text-muted-foreground">{f.text}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="glass-card mt-6 rounded-3xl p-6">
              <p className="eyebrow">No fake scores</p>
              <p className="mt-3 text-sm text-[#6B6B6B]">
                Driver recommendations are only generated from routes drivers have actually published.
                If no compatible driver exists for your route, you'll be told so — with no phantom
                matches.
              </p>
            </div>
          </Reveal>
        </div>
      </section>
    </PageShell>
  );
}