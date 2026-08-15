import { useState } from "react";
import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import { Truck, Menu, X, LogOut, LayoutDashboard, PackageSearch, Route, Plus } from "lucide-react";
import { useAuth } from "@/lib/auth";

interface NavLink {
  to: string;
  label: string;
  icon?: React.ElementType;
}

const PUBLIC_LINKS: NavLink[] = [
  { to: "/how-it-works", label: "How It Works" },
  { to: "/sustainability", label: "Sustainability" },
];

const SENDER_LINKS: NavLink[] = [
  { to: "/sender", label: "Dashboard", icon: LayoutDashboard },
  { to: "/create-parcel", label: "Send Parcel", icon: Plus },
  { to: "/tracking", label: "Track Shipment", icon: PackageSearch },
];

const DRIVER_LINKS: NavLink[] = [
  { to: "/driver", label: "Dashboard", icon: LayoutDashboard },
  { to: "/create-shipment", label: "Publish Route", icon: Plus },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const { user, logout, loading } = useAuth();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  const handleSignOut = () => {
    logout();
    setOpen(false);
    navigate({ to: "/", replace: true });
  };

  const getLinks = (): NavLink[] => {
    if (loading) return PUBLIC_LINKS;
    if (!user) return PUBLIC_LINKS;
    return user.role === "driver" ? DRIVER_LINKS : SENDER_LINKS;
  };

  const links = getLinks();

  const renderNavLinks = (mobile = false) => (
    links.map((l) => {
      const active = pathname === l.to;
      const Icon = l.icon;
      return (
        <Link
          key={l.to}
          to={l.to}
          onClick={() => setOpen(false)}
          className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
            mobile
              ? "text-muted-foreground hover:bg-[#161616] hover:text-foreground"
              : "text-muted-foreground hover:text-foreground"
          } ${active ? "text-foreground bg-[#1C1C1C]" : ""}`}
        >
          {Icon && <Icon className="h-4 w-4" />}
          <span>{l.label}</span>
          {active && !mobile && (
            <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-[#00D4AA]" />
          )}
        </Link>
      );
    })
  );

  if (loading) {
    return (
      <header className="fixed inset-x-0 top-0 z-50 h-16 border-b border-[#292929] bg-[#080808]/85 backdrop-blur-xl">
        <div className="container-page grid h-16 grid-cols-[auto_1fr_auto] items-center gap-4">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00D4AA]">
              <Truck className="h-4.5 w-4.5 text-[#080808]" strokeWidth={2.4} />
            </span>
            <span className="font-display text-base font-bold tracking-tight text-foreground">
              ShipIT <span className="text-[#00D4AA]">AI</span>
            </span>
          </Link>
          <nav className="hidden items-center justify-center gap-8 lg:flex">
            {PUBLIC_LINKS.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className="relative py-5 text-sm text-muted-foreground animate-pulse"
              >
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
    );
  }

  return (
    <header className="fixed inset-x-0 top-0 z-50 h-16 border-b border-[#292929] bg-[#080808]/85 backdrop-blur-xl">
      <div className="container-page grid h-16 grid-cols-[auto_1fr_auto] items-center gap-4">
        <Link to="/" className="flex items-center gap-2.5" onClick={() => setOpen(false)}>
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00D4AA]">
            <Truck className="h-4.5 w-4.5 text-[#080808]" strokeWidth={2.4} />
          </span>
          <span className="font-display text-base font-bold tracking-tight text-foreground">
            ShipIT <span className="text-[#00D4AA]">AI</span>
          </span>
        </Link>

        <nav className="hidden items-center justify-center gap-2 lg:flex" role="navigation" aria-label="Main navigation">
          {renderNavLinks(false)}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          {user ? (
            <>
              <Link
                to={user.role === "driver" ? "/driver" : "/sender"}
                className="flex items-center gap-2.5 rounded-lg border border-[#292929] bg-[#101010] px-3 py-1.5 hover:bg-[#1C1C1C] transition-colors"
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[#00D4AA] text-xs font-bold text-[#080808]">
                  {user.name.charAt(0).toUpperCase()}
                </span>
                <span className="leading-tight hidden sm:block">
                  <span className="block text-xs font-medium text-foreground">{user.name}</span>
                  <span className="block text-[10px] text-[#6B6B6B] capitalize">{user.role}</span>
                </span>
              </Link>
              <button onClick={handleSignOut} className="btn-secondary !px-3 !py-2 flex items-center gap-1.5">
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Sign out</span>
              </button>
            </>
          ) : (
            <>
              <Link to="/auth" className="px-3 text-sm text-muted-foreground transition-colors hover:text-foreground">
                Sign in
              </Link>
            </>
          )}
        </div>

        <button
          className="justify-self-end rounded-md border border-[#292929] bg-[#101010] p-2 lg:hidden"
          onClick={() => setOpen((prev: boolean) => !prev)}
          aria-label="Toggle menu"
          aria-expanded={open}
        >
          {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>

      {open && (
        <div className="border-b border-[#292929] bg-[#0B0B0B] lg:hidden" role="navigation" aria-label="Mobile navigation">
          <div className="container-page flex flex-col gap-1 py-4">
            {renderNavLinks(true)}
            <div className="mt-3 flex flex-col gap-2 border-t border-[#292929] pt-3">
              {user ? (
                <>
                  <Link
                    to={user.role === "driver" ? "/driver" : "/sender"}
                    onClick={() => setOpen(false)}
                    className="btn-secondary flex items-center gap-2"
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    {user.name} · Dashboard
                  </Link>
                  <button onClick={handleSignOut} className="btn-secondary flex items-center gap-2">
                    <LogOut className="h-3.5 w-3.5" /> Sign out
                  </button>
                </>
              ) : (
                <>
                  <Link to="/auth" onClick={() => setOpen(false)} className="btn-secondary flex items-center gap-2">
                    <Truck className="h-4 w-4" /> Sign in
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}