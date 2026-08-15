import { useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { useAuth } from "@/lib/auth";
import type { Role } from "@/lib/mock-api";

export function RequireAuth({ role, children }: { role?: Role; children: ReactNode }) {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      navigate({ to: "/auth", replace: true });
      return;
    }
    if (role && user.role !== role) {
      navigate({ to: user.role === "driver" ? "/driver" : "/sender", replace: true });
    }
  }, [user, loading, role, navigate]);

  if (loading || !user || (role && user.role !== role)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span className="eyebrow animate-pulse">Loading…</span>
      </div>
    );
  }

  return <>{children}</>;
}
