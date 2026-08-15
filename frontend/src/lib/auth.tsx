import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { apiClient, isRealBackend } from "./api-client";
import type { Role, User } from "./mock-api";

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (
    name: string,
    email: string,
    password: string,
    role: Role,
    driver?: { phone: string; vehicleRegNumber: string; licenseNumber: string },
  ) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);
const TOKEN_KEY = "shipit.token";
const USER_KEY = "shipit.user";

// Default context for SSR/edge cases where provider hasn't mounted yet
const defaultAuthState: AuthState = {
  user: null,
  token: null,
  loading: true,
  login: async () => { throw new Error("Auth not ready"); },
  register: async () => { throw new Error("Auth not ready"); },
  logout: () => {},
  refreshUser: async () => {},
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);
    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser) as User);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
      }
    }
    setLoading(false);
  }, []);

  const persist = useCallback((next: { user: User; token: string }) => {
    localStorage.setItem(TOKEN_KEY, next.token);
    localStorage.setItem(USER_KEY, JSON.stringify(next.user));
    setToken(next.token);
    setUser(next.user);
  }, []);

  const clearSession = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await apiClient.login({ email, password });
      persist(res);
      return res.user;
    },
    [persist],
  );

  const register = useCallback(
    async (
      name: string,
      email: string,
      password: string,
      role: Role,
      driver?: { phone: string; vehicleRegNumber: string; licenseNumber: string },
    ) => {
      const res = await apiClient.register({ name, email, password, role, ...driver });
      persist(res);
      return res.user;
    },
    [persist],
  );

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const refreshUser = useCallback(async () => {
    if (!isRealBackend() || !token) return;
    try {
      const freshUser = await apiClient.me();
      localStorage.setItem(USER_KEY, JSON.stringify(freshUser));
      setUser(freshUser);
    } catch {
      clearSession();
    }
  }, [token, clearSession]);

  const value = useMemo(
    () => ({ user, token, loading, login, register, logout, refreshUser }),
    [user, token, loading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  // Return default state instead of throwing during SSR or if provider missing
  if (!ctx) {
    if (typeof window === "undefined") {
      return defaultAuthState; // SSR
    }
    console.warn("useAuth called outside AuthProvider - returning default state");
    return defaultAuthState;
  }
  return ctx;
}