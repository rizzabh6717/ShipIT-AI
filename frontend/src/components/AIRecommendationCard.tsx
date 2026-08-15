import { MapPin, Truck, Star, Zap, ShieldCheck, Clock, ArrowRight, Sparkles, Cpu } from "lucide-react";
import { ProgressBar } from "./ProgressBar";
import { CountUp } from "./CountUp";
import type { DriverMatch } from "@/lib/mock-api";

export interface AIRecommendationCardProps {
  match: DriverMatch;
  variant?: "default" | "compact" | "detailed";
  showActions?: boolean;
  onAccept?: () => void;
  onViewDetails?: () => void;
  isAccepted?: boolean;
  isBest?: boolean;
  className?: string;
}

function FactorIcon({ icon, color = "#4C9EFF" }: { icon: React.ElementType; color?: string }) {
  const Icon = icon;
  return (
    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-opacity-12">
      <Icon className="h-4 w-4" style={{ color }} strokeWidth={2} />
    </span>
  );
}

function BestMatchBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-[#00D4AA]/40 bg-[#00D4AA]/12 px-3 py-1 text-[10px] font-bold tracking-widest uppercase text-[#00D4AA]">
      <Sparkles className="h-3 w-3" /> Best Match
    </span>
  );
}

function RankingBadge({ rankedBy }: { rankedBy: "ai" | "heuristic" | undefined }) {
  const isAi = rankedBy !== "heuristic";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[10px] font-bold tracking-widest uppercase ${
        isAi
          ? "border-[#4C9EFF]/40 bg-[#4C9EFF]/12 text-[#4C9EFF]"
          : "border-[#FBBF24]/40 bg-[#FBBF24]/12 text-[#FBBF24]"
      }`}
      title={isAi ? "Ordered by the AI explainer's semantic scoring" : "Ordered by the deterministic heuristic scorer"}
    >
      {isAi ? <Cpu className="h-3 w-3" /> : <Zap className="h-3 w-3" />}
      {isAi ? "AI-ranked" : "Heuristic-ranked"}
    </span>
  );
}

function ReasonsList({ reasons }: { reasons?: string[] }) {
  if (!reasons || reasons.length === 0) return null;
  return (
    <div className="mt-5 rounded-xl border border-[#292929] bg-[#101010] p-4">
      <p className="eyebrow flex items-center gap-1.5">
        <Zap className="h-3.5 w-3.5 text-[#00D4AA]" /> Why this driver
      </p>
      <ul className="mt-3 flex flex-col gap-2">
        {reasons.map((r, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-[#6B6B6B]">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#00D4AA]" />
            {r}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function AIRecommendationCard({
  match,
  variant = "default",
  showActions = true,
  onAccept,
  onViewDetails,
  isAccepted = false,
  isBest = false,
  className = "",
}: AIRecommendationCardProps) {
  const matchPercent = match.match;
  const overlapPercent = match.overlap ?? matchPercent;
  const detourKm = match.detour;
  const eta = match.eta;
  const rating = match.rating;

  const factors = [
    { icon: MapPin, label: "Route overlap", value: `${overlapPercent}%`, color: "#4C9EFF" },
    { icon: Truck, label: "Pickup detour", value: `+${detourKm} km`, color: "#FBBF24" },
    { icon: Clock, label: "ETA", value: eta, color: "#00D4AA" },
    { icon: Star, label: "Reliability", value: `${rating}/5.0`, color: "#FBBF24" },
  ];

  if (variant === "compact") {
    return (
      <div className={`glass-card lift p-4 ${className}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#00D4AA]/12 text-[#00D4AA]">
              <Truck className="h-5 w-5" />
            </div>
            <div>
              <p className="font-display text-base font-bold">{match.driver}</p>
              <p className="text-xs text-[#6B6B6B]">{match.vehicle}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="font-display text-xl font-bold text-[#00D4AA]">
              <CountUp to={matchPercent} suffix="%" />
            </p>
            <p className="eyebrow">AI Match</p>
          </div>
        </div>

        {isBest && <div className="mt-3"><BestMatchBadge /></div>}
        <div className="mt-3"><RankingBadge rankedBy={match.rankedBy} /></div>

        <div className="mt-4">
          <ProgressBar value={matchPercent} color="#4C9EFF" label="Match confidence" />
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-[#6B6B6B]">
          <span className="flex items-center gap-1.5"><MapPin className="h-3.5 w-3.5" /> {overlapPercent}% overlap</span>
          <span className="flex items-center gap-1.5"><Clock className="h-3.5 w-3.5" /> {eta}</span>
        </div>

        {showActions && (
          <div className="mt-4 flex gap-2">
            <button
              onClick={onAccept}
              disabled={isAccepted}
              className={`btn-primary flex-1 ${isAccepted ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {isAccepted ? "Accepted" : "Accept"}
            </button>
            <button onClick={onViewDetails} className="btn-secondary">
              Details
            </button>
          </div>
        )}
      </div>
    );
  }

  if (variant === "detailed") {
    return (
      <div className={`glass-card lift p-6 ${className}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#00D4AA]/12 text-[#00D4AA]">
              <Truck className="h-6 w-6" />
            </div>
            <div>
              <p className="font-display text-lg font-bold">{match.driver}</p>
              <p className="text-sm text-[#6B6B6B]">{match.vehicle} · {match.weight} kg</p>
            </div>
          </div>
          <div className="text-right">
            {isBest && <div className="mb-1 flex justify-end"><BestMatchBadge /></div>}
            <div className="mb-1 flex justify-end"><RankingBadge rankedBy={match.rankedBy} /></div>
            <p className="font-display text-2xl font-bold text-[#00D4AA]">
              <CountUp to={matchPercent} suffix="%" />
            </p>
            <p className="eyebrow">AI Match Confidence</p>
          </div>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {factors.map((f, i) => (
            <div key={f.label} className="rounded-xl border border-[#292929] bg-[#101010] p-4">
              <div className="flex items-center gap-2">
                <FactorIcon icon={f.icon} color={f.color} />
                <span className="eyebrow">{f.label}</span>
              </div>
              <p className="mt-2 font-display text-xl font-bold" style={{ color: f.color }}>
                {f.value}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-6">
          <ProgressBar value={matchPercent} color="#4C9EFF" label="Overall confidence" valueLabel={`${matchPercent}%`} />
        </div>

        <ReasonsList reasons={match.reasons} />

        {showActions && (
          <div className="mt-6 flex gap-3">
            <button
              onClick={onAccept}
              disabled={isAccepted}
              className={`btn-primary flex-1 ${isAccepted ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {isAccepted ? "Accepted" : "Accept this match"}
            </button>
            <button onClick={onViewDetails} className="btn-secondary">
              <ArrowRight className="h-4 w-4" /> View details
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`glass-card lift p-6 ${className}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#00D4AA]/12 text-[#00D4AA]">
            <Truck className="h-6 w-6" />
          </div>
          <div>
            <p className="font-display text-lg font-bold">{match.driver}</p>
            <p className="text-sm text-[#6B6B6B]">{match.vehicle}</p>
          </div>
        </div>
        <div className="text-right">
          {isBest && <div className="mb-1 flex justify-end"><BestMatchBadge /></div>}
          <div className="mb-1 flex justify-end"><RankingBadge rankedBy={match.rankedBy} /></div>
          <p className="font-display text-3xl font-bold text-[#00D4AA]">
            <CountUp to={matchPercent} suffix="%" />
          </p>
          <p className="eyebrow">Match Score</p>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-[#6B6B6B]">
        <span className="flex items-center gap-1.5"><MapPin className="h-4 w-4" /> {match.from} → {match.to}</span>
        <span className="flex items-center gap-1.5"><Clock className="h-4 w-4" /> {eta}</span>
        <span className="flex items-center gap-1.5"><Star className="h-4 w-4" /> {rating}/5.0</span>
      </div>

      <div className="mt-5">
        <ProgressBar value={matchPercent} color="#4C9EFF" label="AI confidence" valueLabel={`${matchPercent}%`} />
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {factors.slice(0, 4).map((f) => (
          <div key={f.label} className="flex items-center gap-3 rounded-xl border border-[#292929] bg-[#101010] px-3 py-2.5">
            <FactorIcon icon={f.icon} color={f.color} />
            <div>
              <p className="eyebrow">{f.label}</p>
              <p className="font-medium text-sm" style={{ color: f.color }}>{f.value}</p>
            </div>
          </div>
        ))}
      </div>

      <ReasonsList reasons={match.reasons} />

      {showActions && (
        <div className="mt-6 flex gap-3">
          <button
            onClick={onAccept}
            disabled={isAccepted}
            className={`btn-primary flex-1 ${isAccepted ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            {isAccepted ? "Accepted" : "Accept Match"}
          </button>
          <button onClick={onViewDetails} className="btn-secondary">
            <ArrowRight className="h-4 w-4" /> Details
          </button>
        </div>
      )}
    </div>
  );
}