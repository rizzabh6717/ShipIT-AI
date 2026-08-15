import { useId, useRef, useEffect, useState } from "react";
import { motion, animate } from "motion/react";

export interface Stop {
  x: number;
  y: number;
  label: string;
  kind: "origin" | "dest" | "parcel" | "driver";
  anchor?: "start" | "middle" | "end";
  dy?: number;
}

export interface RoutePath {
  d: string;
  color?: string;
  active?: boolean;
  dashed?: boolean;
  trucks?: number;
  truckColor?: string;
  highlight?: boolean;
  pulse?: boolean;
}

const KIND_COLOR: Record<Stop["kind"], string> = {
  origin: "#00D4AA",
  dest: "#F5F5F5",
  parcel: "#FBBF24",
  driver: "#4C9EFF",
};

interface TruckMarkerProps {
  path: string;
  color?: string;
  delay?: number;
  duration?: number;
  size?: number;
}

function TruckMarker({
  path,
  color = "#F5F5F5",
  delay = 0,
  duration = 8000,
  size = 14,
}: TruckMarkerProps) {
  const [progress, setProgress] = useState(0);
  const pathRef = useRef<SVGPathElement>(null);

  useEffect(() => {
    let cancelled = false;
    const startTime = Date.now() + delay;

    const tick = () => {
      if (cancelled) return;
      const elapsed = Date.now() - startTime;
      if (elapsed < 0) {
        requestAnimationFrame(tick);
        return;
      }
      const p = (elapsed % duration) / duration;
      setProgress(p);
      requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
    return () => {
      cancelled = true;
    };
  }, [delay, duration]);

  const pointAt = (t: number) => {
    if (!pathRef.current) return { x: 0, y: 0, angle: 0 };
    const len = pathRef.current.getTotalLength();
    const pt = pathRef.current.getPointAtLength(t * len);
    const ptNext = pathRef.current.getPointAtLength(Math.min(1, t + 0.01) * len);
    const angle = Math.atan2(ptNext.y - pt.y, ptNext.x - pt.x) * (180 / Math.PI);
    return { x: pt.x, y: pt.y, angle };
  };

  const { x, y, angle } = pointAt(progress);

  return (
    <g transform={`translate(${x - size / 2}, ${y - size / 2}) rotate(${angle}, ${size / 2}, ${size / 2})`}>
      <motion.rect
        x={0}
        y={0}
        width={size}
        height={size * 0.6}
        rx={size * 0.1}
        fill={color}
        opacity={0.95}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 0.95 }}
        transition={{ duration: 0.5, delay }}
      />
      <motion.path
        d={`M${size} ${size * 0.16}h${size * 0.33}l${size * 0.22} ${size * 0.33}V${size * 0.6}H${size}z`}
        fill={color}
        opacity={0.7}
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.5, delay }}
      />
      <motion.circle
        cx={size * 0.21}
        cy={size * 0.66}
        r={size * 0.11}
        fill="#080808"
        stroke={color}
        strokeWidth={size * 0.05}
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.5, delay }}
      />
      <motion.circle
        cx={size * 0.81}
        cy={size * 0.66}
        r={size * 0.11}
        fill="#080808"
        stroke={color}
        strokeWidth={size * 0.05}
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.5, delay }}
      />
    </g>
  );
}

function PulsingDot({ x, y, color, size = 12 }: { x: number; y: number; color: string; size?: number }) {
  return (
    <g>
      <circle
        cx={x}
        cy={y}
        r={size}
        fill={color}
        opacity={0.15}
        className="pulse-ring"
        style={{ "--pulse-size": `${size}px` } as React.CSSProperties}
      />
      <motion.circle
        cx={x}
        cy={y}
        r={size * 0.4}
        fill={color}
        stroke="#080808"
        strokeWidth={1}
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
      />
    </g>
  );
}

export function RouteMap({
  paths,
  stops = [],
  className = "h-64",
  animate = true,
  showGrid = true,
}: {
  paths: RoutePath[];
  stops?: Stop[];
  className?: string;
  animate?: boolean;
  showGrid?: boolean;
}) {
  const uid = useId().replace(/:/g, "");

  return (
    <div
      className={`relative w-full overflow-hidden rounded-2xl border border-[#292929] bg-[#0B0B0B] ${className}`}
      role="img"
      aria-label="Route map visualization"
    >
      <svg viewBox="0 0 400 260" className="h-full w-full" preserveAspectRatio="none">
        <defs>
          {showGrid && (
            <pattern id={`grid-${uid}`} width="26" height="26" patternUnits="userSpaceOnUse">
              <path d="M26 0H0V26" fill="none" stroke="#1C1C1C" strokeWidth="1" />
            </pattern>
          )}
          <filter id={`glow-${uid}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeIn in="coloredBlur" />
              <feMergeIn in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id={`glow-strong-${uid}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="coloredBlur" />
            <feMerge>
              <feMergeIn in="coloredBlur" />
              <feMergeIn in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {showGrid && <rect width="400" height="260" fill={`url(#grid-${uid})`} />}

        {paths.map((p, i) => {
          const baseColor = p.color ?? (p.active === false ? "#3A3A3A" : "#00D4AA");
          const isHighlighted = p.highlight === true;
          const truckColor = p.truckColor ?? baseColor;
          const strokeWidth = isHighlighted ? 3.2 : p.active === false ? 1.6 : 2.4;
          const opacity = isHighlighted ? 1 : p.active === false ? 0.45 : 1;
          const filter = isHighlighted ? `url(#glow-strong-${uid})` : p.pulse ? `url(#glow-${uid})` : undefined;

          return (
            <g key={i}>
              <motion.path
                ref={(el) => {
                  if (el && p.trucks && p.trucks > 0) {
                    (el as SVGPathElement).id = `path-${uid}-${i}`;
                  }
                }}
                d={p.d}
                fill="none"
                stroke={baseColor}
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray={p.dashed ? "6 8" : undefined}
                opacity={opacity}
                filter={filter}
                initial={{ pathLength: animate ? 0 : 1 }}
                whileInView={{ pathLength: 1 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ duration: isHighlighted ? 2.8 : 2.4, ease: "easeOut" }}
                style={{ willChange: "stroke-dashoffset" }}
              />
              {p.trucks && p.trucks > 0 && p.active !== false && (
                <>
                  <defs>
                    <path id={`path-${uid}-${i}`} d={p.d} />
                  </defs>
                  {Array.from({ length: p.trucks } as const).map((_, t) => (
                    <TruckMarker
                      key={t}
                      path={p.d}
                      color={truckColor}
                      delay={t * 2000}
                      duration={isHighlighted ? 10000 : 8000}
                      size={isHighlighted ? 16 : 14}
                    />
                  ))}
                </>
              )}
            </g>
          );
        })}

        {stops.map((s, i) => {
          const color = KIND_COLOR[s.kind];
          const isParcel = s.kind === "parcel";
          const pulseColors: Record<Stop["kind"], string> = {
            origin: "#00D4AA",
            dest: "#F5F5F5",
            parcel: "#FBBF24",
            driver: "#4C9EFF",
          };

          return (
            <g key={i}>
              <PulsingDot x={s.x} y={s.y} color={pulseColors[s.kind]} size={isParcel ? 10 : 8} />
              {isParcel ? (
                <rect
                  x={s.x - 5}
                  y={s.y - 5}
                  width="10"
                  height="10"
                  rx="1.8"
                  fill={color}
                  stroke="#080808"
                  strokeWidth="1.5"
                />
              ) : (
                <circle cx={s.x} cy={s.y} r={5} fill={color} stroke="#080808" strokeWidth="1.5" />
              )}
              <text
                x={s.x + (s.anchor === "end" ? -14 : s.anchor === "middle" ? 0 : 14)}
                y={s.y + (s.dy ?? 6)}
                textAnchor={s.anchor ?? "start"}
                fontSize="10.5"
                letterSpacing="0.06em"
                fill="#A1A1A1"
                fontFamily="Inter, sans-serif"
                fontWeight={500}
              >
                {s.label.toUpperCase()}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// Shared route geometries used across pages.
export const ROUTES = {
  simple: "M 48 208 C 140 190, 200 120, 348 54",
  viaDriver: "M 48 208 C 120 200, 170 150, 224 132 C 280 112, 300 80, 348 54",
  full: "M 48 208 C 96 186, 122 156, 158 152 C 214 146, 246 118, 292 92 C 316 78, 330 66, 348 54",
  straight: "M 40 130 L 360 130",
  efficient: "M 40 168 C 120 168, 150 110, 220 104 C 290 98, 320 118, 360 96",
  // Additional marketplace routes
  delhiNoida: "M 48 208 C 96 186, 122 156, 158 152 C 214 146, 246 118, 292 92 C 316 78, 330 66, 348 54",
  noidaGurgaon: "M 348 54 C 300 110, 200 150, 60 96",
  delhiGhaziabad: "M 48 208 C 120 220, 240 196, 340 168",
  gurgaonDelhi: "M 60 96 C 120 60, 240 70, 340 120",
} as const;

export function createMarketplacePaths(
  selectedId: string,
  routes: typeof ROUTES,
  routeIds: string[]
): RoutePath[] {
  return routeIds.map((id) => ({
    d: routes[id as keyof typeof routes] ?? routes.simple,
    color: id === selectedId ? "#00D4AA" : "#3A3A3A",
    active: id === selectedId,
    highlight: id === selectedId,
    pulse: id === selectedId,
    trucks: id === selectedId ? 2 : 0,
    truckColor: "#00D4AA",
  }));
}