import { createFileRoute } from "@tanstack/react-router";
import { Leaf } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { RouteMap, ROUTES } from "@/components/RouteMap";
import { CountUp } from "@/components/CountUp";

export const Route = createFileRoute("/sustainability")({
  head: () => ({
    meta: [
      { title: "Sustainability — ShipIT AI" },
      {
        name: "description",
        content:
          "Shared routes avoid 14.4 km of dedicated driving and 2.8 kg of CO₂ per parcel. Every journey can carry something.",
      },
      { property: "og:title", content: "Sustainability — ShipIT AI" },
      {
        property: "og:description",
        content: "Traditional delivery vs ShipIT AI: 18.6 km against 4.2 km.",
      },
    ],
  }),
  component: Sustainability,
});

function Sustainability() {
  return (
    <PageShell>
      <section className="container-page section-y">
        <Reveal className="max-w-3xl">
          <p className="eyebrow">Sustainability</p>
          <h1 className="mt-4 font-display text-4xl leading-[1.02] font-bold tracking-tight sm:text-6xl">
            YOUR DELIVERY DIDN'T NEED ANOTHER TRIP.
          </h1>
        </Reveal>

        <div className="mt-14 grid gap-6 lg:grid-cols-2">
          <Reveal>
            <div className="glass-card h-full p-8">
              <p className="eyebrow">Traditional delivery</p>
              <p className="mt-4 font-display text-4xl font-bold text-foreground">
                <CountUp to={18.6} decimals={1} suffix=" km" />
              </p>
              <p className="mt-2 text-sm text-[#6B6B6B]">a dedicated trip just for you</p>
              <div className="mt-8">
                <RouteMap
                  className="h-52"
                  paths={[{ d: ROUTES.straight, active: false, dashed: true }]}
                  stops={[
                    { x: 40, y: 130, label: "Depot", kind: "dest" },
                    { x: 360, y: 130, label: "You", kind: "dest", anchor: "end" },
                  ]}
                />
              </div>
            </div>
          </Reveal>

          <Reveal delay={0.08}>
            <div className="h-full rounded-2xl border border-[#00D4AA]/45 bg-[#1C1C1C] p-8">
              <div className="flex items-center gap-2">
                <Leaf className="h-4 w-4 text-[#00D4AA]" />
                <p className="eyebrow">ShipIT AI</p>
              </div>
              <p className="mt-4 font-display text-4xl font-bold text-[#00D4AA]">
                <CountUp to={4.2} decimals={1} suffix=" km" />
              </p>
              <p className="mt-2 text-sm text-[#6B6B6B]">added to a journey already happening</p>
              <div className="mt-8">
                <RouteMap
                  className="h-52"
                  paths={[{ d: ROUTES.efficient, trucks: 1 }]}
                  stops={[
                    { x: 40, y: 168, label: "Driver", kind: "driver" },
                    { x: 220, y: 104, label: "Pickup", kind: "parcel" },
                    { x: 360, y: 96, label: "You", kind: "origin", anchor: "end" },
                  ]}
                />
              </div>
            </div>
          </Reveal>
        </div>

        <div className="mt-6 grid gap-6 sm:grid-cols-2">
          <Reveal>
            <div className="glass-card p-8">
              <p className="eyebrow">Km avoided</p>
              <p className="mt-3 font-display text-3xl font-bold text-foreground">
                <CountUp to={14.4} decimals={1} suffix=" km" />
              </p>
            </div>
          </Reveal>
          <Reveal delay={0.06}>
            <div className="glass-card p-8">
              <p className="eyebrow">CO₂ saved</p>
              <p className="mt-3 font-display text-3xl font-bold text-[#00D4AA]">
                <CountUp to={2.8} decimals={1} suffix=" kg" />
              </p>
            </div>
          </Reveal>
        </div>

        <p className="mt-12 text-center text-sm text-[#6B6B6B]">
          Every journey can carry something.
        </p>
      </section>
    </PageShell>
  );
}
