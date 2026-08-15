import { Loader2, PackageSearch, Truck, AlertCircle, RefreshCw, Search } from "lucide-react";
import { motion } from "motion/react";

export function LoadingState({
  message = "Loading…",
  size = "md",
  className = "",
}: { message?: string; size?: "sm" | "md" | "lg"; className?: string }) {
  const sizes = {
    sm: "h-6 w-6 text-sm",
    md: "h-10 w-10 text-base",
    lg: "h-14 w-14 text-lg",
  };

  return (
    <div className={`flex flex-col items-center justify-center gap-3 py-12 ${className}`}>
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        className={sizes[size]}
      >
        <Loader2 className="h-full w-full text-[#00D4AA]" />
      </motion.div>
      <p className="text-sm text-[#6B6B6B]">{message}</p>
    </div>
  );
}

export function SkeletonCard({ className = "", lines = 3 }: { className?: string; lines?: number }) {
  return (
    <div className={`glass-card rounded-2xl p-6 ${className}`}>
      <div className="h-4 w-3/12 rounded bg-[#1C1C1C] animate-pulse mb-4" />
      <div className="h-8 w-1/2 rounded bg-[#1C1C1C] animate-pulse mb-6" />
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <div key={i} className="h-3 w-full rounded bg-[#1C1C1C] animate-pulse" />
        ))}
      </div>
    </div>
  );
}

export function SkeletonList({ count = 3, className = "" }: { count?: number; className?: string }) {
  return (
    <div className={`space-y-4 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} lines={2} />
      ))}
    </div>
  );
}

export function EmptyState({
  icon: Icon = PackageSearch,
  title = "Nothing here yet",
  description = "Get started by creating your first item.",
  action,
  className = "",
}: {
  icon?: React.ElementType;
  title?: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex flex-col items-center justify-center text-center py-16 px-4 ${className}`}>
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#1C1C1C] text-[#6B6B6B]">
        <Icon className="h-8 w-8" />
      </div>
      <h3 className="mt-5 font-display text-lg font-bold text-foreground">{title}</h3>
      <p className="mt-2 text-sm text-[#6B6B6B] max-w-xs">{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

export function ErrorState({
  icon: Icon = AlertCircle,
  title = "Something went wrong",
  description = "We couldn't load this content. Please try again.",
  onRetry,
  className = "",
}: {
  icon?: React.ElementType;
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div className={`flex flex-col items-center justify-center text-center py-16 px-4 ${className}`}>
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#FBBF24]/12 text-[#FBBF24]">
        <Icon className="h-8 w-8" />
      </div>
      <h3 className="mt-5 font-display text-lg font-bold text-foreground">{title}</h3>
      <p className="mt-2 text-sm text-[#6B6B6B] max-w-xs">{description}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-6 btn-secondary flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" /> Try again
        </button>
      )}
    </div>
  );
}

export function SearchEmptyState({
  query,
  onClear,
  className = "",
}: {
  query?: string;
  onClear?: () => void;
  className?: string;
}) {
  return (
    <div className={`flex flex-col items-center justify-center text-center py-16 px-4 ${className}`}>
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#1C1C1C] text-[#6B6B6B]">
        <Search className="h-8 w-8" />
      </div>
      <h3 className="mt-5 font-display text-lg font-bold text-foreground">
        {query ? `No results for "${query}"` : "No shipments found"}
      </h3>
      <p className="mt-2 text-sm text-[#6B6B6B] max-w-xs">
        {query
          ? "Try adjusting your search or filters."
          : "You don't have any shipments yet."}
      </p>
      {onClear && query && (
        <button onClick={onClear} className="mt-6 btn-secondary flex items-center gap-2">
          <RefreshCw className="h-4 w-4" /> Clear search
        </button>
      )}
    </div>
  );
}

export function PageSkeleton({ sections = 3 }: { sections?: number }) {
  return (
    <div className="container-page section-y">
      <div className="max-w-2xl">
        <div className="h-3 w-2/12 rounded bg-[#1C1C1C] animate-pulse mb-4" />
        <div className="h-8 w-4/5 rounded bg-[#1C1C1C] animate-pulse mb-6" />
        <div className="h-4 w-full rounded bg-[#1C1C1C] animate-pulse" />
      </div>
      <div className="mt-12 grid gap-8 lg:grid-cols-2">
        {Array.from({ length: sections }).map((_, i) => (
          <SkeletonCard key={i} className="h-[300px]" />
        ))}
      </div>
    </div>
  );
}