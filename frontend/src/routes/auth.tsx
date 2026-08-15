import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Truck, User as UserIcon, Car, Phone, FileText, CreditCard } from "lucide-react";
import { PageShell, Reveal } from "@/components/PageShell";
import { useAuth } from "@/lib/auth";
import type { Role } from "@/lib/mock-api";

export const Route = createFileRoute("/auth")({
  head: () => ({
    meta: [
      { title: "Sign in — ShipIT AI" },
      {
        name: "description",
        content: "Log in or create a ShipIT AI account as a sender or a driver.",
      },
      { property: "og:title", content: "Sign in — ShipIT AI" },
      { property: "og:description", content: "Access your ShipIT AI sender or driver dashboard." },
    ],
  }),
  component: AuthPage,
});

function AuthPage() {
  const { user, loading, login, register } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [role, setRole] = useState<Role>("sender");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [vehicleReg, setVehicleReg] = useState("");
  const [license, setLicense] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (loading || !user) return;
    navigate({ to: user.role === "driver" ? "/driver" : "/sender", replace: true });
  }, [user, loading, navigate]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (tab === "register" && role === "driver") {
      if (!phone.trim()) {
        toast.error("Phone number is required for drivers");
        return;
      }
      if (!vehicleReg.trim()) {
        toast.error("Vehicle registration number is required");
        return;
      }
      if (!license.trim()) {
        toast.error("Driver licence number is required");
        return;
      }
    }
    setBusy(true);
    try {
      const next =
        tab === "login"
          ? await login(email, password)
          : await register(
              name.trim() || "New User",
              email,
              password,
              role,
              tab === "register" && role === "driver"
                ? { phone: phone.trim(), vehicleRegNumber: vehicleReg.trim(), licenseNumber: license.trim() }
                : undefined,
            );
      toast.success(tab === "login" ? "Welcome back" : "Account created");
      navigate({ to: next.role === "driver" ? "/driver" : "/sender", replace: true });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  const field = "mt-2 w-full rounded-lg px-3 py-2.5 text-sm";

  return (
    <PageShell>
      <section className="container-page flex min-h-[calc(100vh-4rem)] items-center justify-center py-16">
        <Reveal className="w-full max-w-md">
          <div className="glass-card rounded-3xl p-8 backdrop-blur">
            <p className="eyebrow">ShipIT AI account</p>
            <h1 className="mt-3 font-display text-2xl font-bold">
              {tab === "login" ? "Welcome back." : "Join the network."}
            </h1>

            <div className="mt-6 grid grid-cols-2 gap-1 rounded-xl border border-[#292929] bg-[#101010] p-1">
              {(["login", "register"] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setTab(t)}
                  className={`rounded-lg py-2 text-xs font-semibold tracking-widest uppercase transition ${
                    tab === t ? "bg-[#00D4AA] text-[#080808]" : "text-muted-foreground"
                  }`}
                >
                  {t === "login" ? "Login" : "Register"}
                </button>
              ))}
            </div>

            <form onSubmit={submit} className="mt-6 flex flex-col gap-4">
              {tab === "register" && (
                <>
                  <div>
                    <label className="eyebrow">I am a</label>
                    <div className="mt-2 flex gap-2">
                      {(
                        [
                          { key: "sender" as const, label: "Sender", icon: UserIcon },
                          { key: "driver" as const, label: "Driver", icon: Truck },
                        ] satisfies { key: Role; label: string; icon: typeof Truck }[]
                      ).map((r) => (
                        <button
                          key={r.key}
                          type="button"
                          onClick={() => setRole(r.key)}
                          className={`flex flex-1 items-center justify-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold tracking-wider uppercase transition ${
                            role === r.key
                              ? "border-[#00D4AA] bg-[#00D4AA]/12 text-[#00D4AA]"
                              : "border-[#292929] bg-[#101010] text-muted-foreground"
                          }`}
                        >
                          <r.icon className="h-3.5 w-3.5" /> {r.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="eyebrow" htmlFor="name">
                      Name
                    </label>
                    <input
                      id="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Aarav Sharma"
                      className={field}
                    />
                  </div>

                  {role === "driver" && (
                    <>
                      <div>
                        <label className="eyebrow" htmlFor="phone">
                          <Phone className="mr-1 inline h-3 w-3" /> Phone number <span className="text-[#FBBF24]">*</span>
                        </label>
                        <input
                          id="phone"
                          type="tel"
                          required
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          placeholder="+91 98765 43210"
                          className={field}
                        />
                      </div>
                      <div>
                        <label className="eyebrow" htmlFor="vehicleReg">
                          <Car className="mr-1 inline h-3 w-3" /> Vehicle registration number <span className="text-[#FBBF24]">*</span>
                        </label>
                        <input
                          id="vehicleReg"
                          required
                          value={vehicleReg}
                          onChange={(e) => setVehicleReg(e.target.value)}
                          placeholder="MH12AB1234"
                          className={field}
                        />
                      </div>
                      <div>
                        <label className="eyebrow" htmlFor="license">
                          <FileText className="mr-1 inline h-3 w-3" /> Driver licence number <span className="text-[#FBBF24]">*</span>
                        </label>
                        <input
                          id="license"
                          required
                          value={license}
                          onChange={(e) => setLicense(e.target.value)}
                          placeholder="DL-01-2025-000001"
                          className={field}
                        />
                      </div>
                    </>
                  )}
                </>
              )}

              <div>
                <label className="eyebrow" htmlFor="email">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className={field}
                />
              </div>

              <div>
                <label className="eyebrow" htmlFor="password">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className={field}
                />
                <p className="mt-1 text-[11px] text-[#6B6B6B]">At least 8 characters</p>
              </div>

              <button type="submit" disabled={busy} className="btn-primary mt-2 w-full disabled:opacity-60">
                {busy ? "Please wait…" : tab === "login" ? "Sign In" : "Create Account"}
              </button>
            </form>

            {tab === "register" && role === "driver" && (
              <div className="mt-4 rounded-xl border border-[#FBBF24]/30 bg-[#FBBF24]/8 p-3">
                <p className="flex items-center gap-1.5 text-[11px] text-[#FBBF24]">
                  <CreditCard className="h-3 w-3" /> Your documents are stored on your driver profile
                  and shown to senders when they review your details.
                </p>
              </div>
            )}

            <p className="mt-5 text-center text-[11px] text-[#6B6B6B]">
              Demo mode · any email works. Use an email starting with "driver" to log in as a
              driver. Password must be 8+ characters.
            </p>
          </div>
        </Reveal>
      </section>
    </PageShell>
  );
}
