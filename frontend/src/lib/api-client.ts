import type {
  Role,
  User,
  Shipment,
  DriverMatch,
  MarketRoute,
  DriverRoute,
  DeliveryRequest,
  DriverProfile,
  DriverStats,
  BudgetRecommendation,
  Feedback,
} from "./mock-api";

const API_URL = import.meta.env.VITE_API_URL ?? "";

function isRealBackend(): boolean {
  return Boolean(API_URL);
}

export function mediaUrl(path?: string | null): string {
  if (!path) return "";
  if (/^https?:\/\//i.test(path) || path.startsWith("//") || path.startsWith("data:")) return path;
  const base = API_URL.replace(/\/api\/?$/, "");
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_URL}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("shipit.token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function formatDimensions(d: any): string {
  const l = d?.length, w = d?.width, h = d?.height;
  if (l && w && h) return `${l} × ${w} × ${h} cm`;
  if (l && w) return `${l} × ${w} cm`;
  return JSON.stringify(d);
}

function parseDimensions(dims: string): { length: number; width: number; height: number } | undefined {
  const nums = (dims || "").match(/\d+(\.\d+)?/g)?.map(Number) ?? [];
  if (nums.length >= 3) {
    return { length: nums[0]!, width: nums[1]!, height: nums[2]! };
  }
  if (nums.length >= 2) {
    return { length: nums[0]!, width: nums[1]!, height: nums[1]! };
  }
  return undefined;
}

function mapDriverRequest(r: any, i: number): DriverMatch {
  const p = r.parcel || {};
  const d = r.driver || {};
  return {
    id: r.public_id || `req-${i}`,
    driverId: d?.public_id || String(r.driver_id ?? ""),
    routeId: r.route_id ? String(r.route_id) : "",
    driver: d?.name || "Driver",
    vehicle: d?.vehicle_type || "Your Route",
    rating: d?.rating ?? 0,
    match: 0,
    overlap: 0,
    detour: 0,
    eta: p?.deadline || "N/A",
    payout: Math.round(p?.budget || 0),
    from: p?.pickup_location || "",
    to: p?.drop_location || "",
    weight: p?.weight || 0,
    distance: 0,
    reasons: [],
    requestId: r.public_id || `req-${i}`,
    requestStatus: r.status,
    description: p?.item_description,
    deadline: p?.deadline,
    ...(p?.dimensions ? { dimensions: formatDimensions(p.dimensions) } : {}),
    ...(r.proof_image_url ? { proofImageUrl: r.proof_image_url } : {}),
  };
}

function normalizeUser(user: any): User {
    return {
      ...user,
      role: user.role?.toLowerCase() === "driver" ? "driver" : "sender",
    };
  }

  export interface RegisterInput {
    name: string;
    email: string;
    password: string;
    role: Role;
    phone?: string;
    vehicleType?: string;
    capacityKg?: number;
    licenseNumber?: string;
    vehicleRegNumber?: string;
    currentCity?: string;
  }

  export const apiClient = {
  async register(input: RegisterInput) {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.register(input);
    }
    const endpoint = input.role === "driver" ? "/auth/register/driver" : "/auth/register/sender";
    const body = input.role === "driver"
      ? {
          name: input.name,
          email: input.email,
          password: input.password,
          phone: input.phone ?? "",
          vehicle_type: input.vehicleType ?? "van",
          capacity_kg: input.capacityKg ?? 1000,
          license_number: input.licenseNumber ?? "TEMP-LICENCE",
          vehicle_reg_number: input.vehicleRegNumber ?? "TEMP-REG",
          current_city: input.currentCity ?? "Delhi",
        }
      : { name: input.name, email: input.email, password: input.password };
    const data = await fetchJson<{ access_token: string; user: any }>(endpoint, {
      method: "POST",
      body: JSON.stringify(body),
    });
    localStorage.setItem("shipit.token", data.access_token);
    return { user: normalizeUser(data.user), token: data.access_token };
  },

  async login(input: { email: string; password: string }) {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.login(input);
    }
    const data = await fetchJson<{ access_token: string; user: any }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    });
    localStorage.setItem("shipit.token", data.access_token);
    return { user: normalizeUser(data.user), token: data.access_token };
  },

  async me() {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.login({ email: "demo@sender.com", password: "password" });
    }
    const user = await fetchJson<any>("/auth/me", { headers: getAuthHeaders() });
    return normalizeUser(user);
  },

  async listShipments(): Promise<Shipment[]> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.listShipments();
    }
    const parcels = await fetchJson<any[]>("/parcels", { headers: getAuthHeaders() });
    const requests = await fetchJson<any[]>("/deliveries/requests/sender", {
      headers: getAuthHeaders(),
    }).catch(() => []);
    const reqByParcel = new Map(
      requests.map((r) => [r.parcel?.public_id, r]),
    );
    return parcels.map((p) => {
      const req = reqByParcel.get(p.public_id);
      return {
        id: p.public_id,
        from: p.pickup_location,
        to: p.drop_location,
        weight: p.weight,
        status: p.status,
        // No pre-computed best match — scores appear only after the sender
        // explicitly runs matching from the dashboard.
        match: 0,
        price: Math.round(p.budget || 100),
        eta: p.deadline ? new Date(p.deadline).toLocaleString() : "Pending",
        trackingId: `SHIPIT-${p.public_id.slice(1)}`,
        description: p.item_description,
        deadline: p.deadline,
        requestId: req?.public_id,
        proofImageUrl: req?.proof_image_url,
        ...(p.dimensions ? { dimensions: formatDimensions(p.dimensions) } : {}),
      };
    });
  },

  async createShipment(input: {
    from: string;
    to: string;
    weight: number;
    dimensions: string;
    description: string;
    deadline: string;
    budget?: number;
  }): Promise<Shipment> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.createShipment(input);
    }
    const parcel = await fetchJson<any>("/parcels", {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        pickup_location: input.from,
        drop_location: input.to,
        weight: input.weight,
        item_description: input.description || "Parcel",
        budget: input.budget ?? 100,
        deadline: input.deadline ? new Date(input.deadline).toISOString() : undefined,
        dimensions: parseDimensions(input.dimensions),
      }),
    });
    return {
      id: parcel.public_id,
      from: parcel.pickup_location,
      to: parcel.drop_location,
      weight: parcel.weight,
      status: parcel.status,
      match: 0,
      price: Math.round(parcel.budget || 100),
      eta: "Pending",
      trackingId: `SHIPIT-${parcel.public_id.slice(1)}`,
    };
  },

  async matchDrivers(shipmentId: string): Promise<DriverMatch[]> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.matchDrivers(shipmentId);
    }
    const res = await fetchJson<any>(`/ai/match`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ parcel_id: shipmentId }),
    });
    return (res.matches || []).map((m: any, i: number) => {
      const matchPct = Math.round((m.score || 0) * 100);
      const overlapPct = Math.round((m.overlap ?? 0) * 100);
      const d = m.driver;
      return {
        id: m.driver_id || `${shipmentId}-m${i}`,
        driverId: m.driver_id || "",
        routeId: m.route_id ? String(m.route_id) : "",
        driver: d?.name || `Driver ${m.driver_id}`,
        vehicle: d?.vehicle_type || "Vehicle",
        rating: d?.rating ?? 4.5,
        match: matchPct,
        overlap: overlapPct,
        detour: m.detour_km ?? 0,
        eta: m.eta || "Unknown",
        payout: 0,
        from: "",
        to: "",
        weight: d?.capacity_kg || 0,
        distance: 0,
        reasons: Array.isArray(m.reason) ? m.reason : [],
        rankedBy: res.ranked_by === "heuristic" ? "heuristic" : "ai",
        profile: d
          ? {
              publicId: d.public_id || m.driver_id,
              name: d.name,
              phone: d.phone,
              email: d.email,
              vehicleType: d.vehicle_type,
              licenseNumber: d.license_number,
              vehicleRegNumber: d.vehicle_reg_number,
              capacityKg: d.capacity_kg || 0,
              rating: d.rating ?? 4.5,
              onTimeRate: d.on_time_rate ?? 1,
              completionRate: d.completion_rate ?? 1,
              reviewsCount: d.reviews_count ?? 0,
              completedDeliveries: d.completed_deliveries ?? 0,
              currentCity: d.current_city,
              routes: [],
            }
          : undefined,
      };
    });
  },

  async tracking(parcelPublicId: string) {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.tracking(parcelPublicId);
    }
    const p = await fetchJson<any>(`/parcels/${parcelPublicId}`, { headers: getAuthHeaders() });
    const matches: { driver_id?: string; score?: number; eta?: string }[] = Array.isArray(p?.matches)
      ? p.matches
      : [];
    const best = matches[0];
    const status: string = p?.status ?? "pending";
    const fmt = (iso?: string) => {
      if (!iso) return "—";
      const d = new Date(iso);
      return isNaN(d.getTime()) ? iso : d.toLocaleString();
    };
    const steps: { label: string; time: string; done: boolean }[] = [
      { label: "Parcel posted", time: fmt(p?.created_at), done: true },
      {
        label: "Driver found",
        time: best ? "Assigned" : "Searching the network",
        done: !!best || ["matched", "in_transit", "delivered"].includes(status),
      },
      {
        label: "Picked up",
        time: "Driver confirmed pickup",
        done: ["in_transit", "delivered"].includes(status),
      },
      {
        label: "In transit",
        time: "On the way",
        done: ["in_transit", "delivered"].includes(status),
      },
      {
        label: "Delivered",
        time: "Proof of delivery uploaded",
        done: status === "delivered",
      },
    ];
    return {
      from: p?.pickup_location,
      to: p?.drop_location,
      driver: p?.best_driver?.name ?? best?.driver_id ?? "—",
      eta: best?.eta ?? (p?.deadline ? new Date(p.deadline).toLocaleString() : "—"),
      match: best?.score ?? 0,
      status,
      steps,
    };
  },

  async listMarketRoutes(): Promise<MarketRoute[]> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.listMarketRoutes();
    }
    const routes = await fetchJson<any[]>("/routes", { headers: getAuthHeaders() });
    return routes.map((r, i) => ({
      id: r.public_id || `r${i}`,
      from: r.origin,
      to: r.destination,
      drivers: r.drivers?.length || 0,
      time: r.eta || "N/A",
      distance: r.distance_km || 0,
      co2: r.co2_saved_kg || 0,
      price: r.price || 0,
      match: 0,
    }));
  },

  async createDriverRoute(input: {
    from: string;
    to: string;
    departureTime: string;
    vehicleType: string;
    vehicleLabel: string;
    capacityKg: number;
    availableSpaceKg: number;
    pricePerKg: number;
    description: string;
    recurring: boolean;
    recurrenceDays: string[];
  }): Promise<DriverRoute> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.createDriverRoute(input);
    }
    return fetchJson<any>("/routes", {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        origin: input.from,
        destination: input.to,
        waypoints: [],
        planned_at: input.departureTime ? new Date(input.departureTime).toISOString() : undefined,
      }),
    });
  },

  async listActiveDriverRoutes(): Promise<DriverRoute[]> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.listActiveDriverRoutes();
    }
    const res = await fetchJson<any[]>("/routes", { headers: getAuthHeaders() });
    return res.map((r, i) => ({
      id: r.public_id || `r${i}`,
      driverId: String(r.driver_id ?? i),
      driverName: r.driver?.name || `Driver ${r.driver_id ?? i}`,
      vehicleType: r.driver?.vehicle_type || "van",
      vehicleLabel: r.driver?.vehicle_type || "Vehicle",
      from: r.origin,
      to: r.destination,
      departureTime: r.planned_at || "",
      capacityKg: r.driver?.capacity_kg || 1000,
      availableSpaceKg: r.driver?.capacity_kg || 1000,
      pricePerKg: r.price || 15,
      description: r.route_text || "",
      recurring: false,
      recurrenceDays: [],
      status: "active",
      rating: r.driver?.rating ?? 4.5,
      onTimeRate: r.driver?.on_time_rate ?? 0.9,
      createdAt: r.created_at || "",
    }));
  },

  async listDriverRequests(): Promise<DriverMatch[]> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.listDriverRequests();
    }
    // Only the driver's own pending requests are ever surfaced.
    const requests = await fetchJson<any[]>("/deliveries/requests/me?scope=pending", {
      headers: getAuthHeaders(),
    });
    return requests.map((r, i) => mapDriverRequest(r, i));
  },

  async listDriverDeliveries(): Promise<DriverMatch[]> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.listDriverDeliveries();
    }
    const requests = await fetchJson<any[]>("/deliveries/requests/me?scope=active", {
      headers: getAuthHeaders(),
    });
    return requests.map((r, i) => mapDriverRequest(r, i));
  },

  async selectDriver(parcelId: string, driverId: string, routeId: string): Promise<DeliveryRequest> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.selectDriver(parcelId, driverId, routeId);
    }
    const res = await fetchJson<any>("/deliveries/request", {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        parcel_id: parcelId,
        driver_id: driverId,
        route_id: routeId || undefined,
      }),
    });
    const r = res.request || {};
    return {
      id: r.public_id || "",
      parcelId,
      driverId,
      routeId: routeId || "",
      status: r.status || "pending_driver_approval",
      createdAt: r.created_at || new Date().toISOString(),
      respondedAt: r.responded_at || undefined,
    };
  },

  async respondToRequest(requestId: string, accept: boolean): Promise<void> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.respondToRequest(requestId, accept);
    }
    return fetchJson<any>(`/deliveries/requests/${encodeURIComponent(requestId)}/respond`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ accept }),
    });
  },

  async confirmPickup(requestId: string): Promise<void> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.confirmPickup(requestId);
    }
    return fetchJson<any>(`/deliveries/requests/${encodeURIComponent(requestId)}/pickup`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
  },

  async markDelivered(requestId: string, proofImageUrl: string): Promise<void> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.markDelivered(requestId, proofImageUrl);
    }
    return fetchJson<any>(`/deliveries/requests/${encodeURIComponent(requestId)}/delivered`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ proof_image_url: proofImageUrl }),
    });
  },

  async uploadRequestProof(requestId: string, file: File): Promise<string> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.uploadRequestProof(requestId, file);
    }
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_URL}/photos/delivery-request-proof?request_id=${encodeURIComponent(requestId)}`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: form,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`${res.status}: ${text}`);
    }
    const data = await res.json();
    return data.proofImageUrl || "";
  },

  async getDriverProfile(driverPublicId: string): Promise<DriverProfile> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.getDriverProfile(driverPublicId);
    }
    const d = await fetchJson<any>(`/drivers/${encodeURIComponent(driverPublicId)}`, {
      headers: getAuthHeaders(),
    });
    return {
      publicId: d.public_id,
      name: d.name,
      phone: d.phone,
      email: d.email,
      vehicleType: d.vehicle_type,
      licenseNumber: d.license_number,
      vehicleRegNumber: d.vehicle_reg_number,
      capacityKg: d.capacity_kg || 0,
      rating: d.rating ?? 4.5,
      onTimeRate: d.on_time_rate ?? 1,
      completionRate: d.completion_rate ?? 1,
      reviewsCount: d.reviews_count ?? 0,
      completedDeliveries: d.completed_deliveries ?? 0,
      currentCity: d.current_city,
      routes: [],
    };
  },

  async getDriverRoutes(driverPublicId: string): Promise<DriverProfile["routes"]> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.getDriverRoutes(driverPublicId);
    }
    const routes = await fetchJson<any[]>("/routes", { headers: getAuthHeaders() });
    const driverRoutes = routes.filter(
      (r) => r.driver?.public_id === driverPublicId || String(r.driver_id) === driverPublicId,
    );
    return driverRoutes.map((r) => ({
      from: r.origin,
      to: r.destination,
      departureTime: r.planned_at,
      isActive: r.is_active !== false,
    }));
  },

  async getDriverStats(): Promise<DriverStats> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.getDriverStats();
    }
    const s = await fetchJson<any>("/drivers/me/stats", { headers: getAuthHeaders() });
    return {
      totalDeliveries: s.total_deliveries || 0,
      completedDeliveries: s.completed_deliveries || 0,
      pendingDeliveries: s.pending_deliveries || 0,
      inTransitDeliveries: s.in_transit_deliveries || 0,
      rejectedDeliveries: s.rejected_deliveries || 0,
      onTimeRate: s.on_time_rate || 1,
      completionRate: s.completion_rate || 1,
      rating: s.rating || 5,
      reviewsCount: s.reviews_count || 0,
      activeRoutes: s.active_routes || 0,
    };
  },

  async updateAvailability(status: "available" | "offline"): Promise<void> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.updateAvailability(status);
    }
    return fetchJson<any>("/drivers/me/availability", {
      method: "PATCH",
      headers: getAuthHeaders(),
      body: JSON.stringify({ status }),
    });
  },

  async recommendBudget(input: {
    from: string;
    to: string;
    weight: number;
    dimensions?: string;
  }): Promise<BudgetRecommendation> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.recommendBudget(input);
    }
    const res = await fetchJson<any>("/ai/budget-recommend", {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        pickup_location: input.from,
        drop_location: input.to,
        weight: input.weight,
        dimensions: parseDimensions(input.dimensions || ""),
      }),
    });
    return {
      recommendedBudget: res.recommended_budget,
      totalAmount: res.total_amount,
      currency: res.currency,
      baseRate: res.base_rate,
      distanceKm: res.distance_km,
      distanceCharge: res.distance_charge,
      weightCharge: res.weight_charge,
      sizeTier: res.size_tier,
      sizeCharge: res.size_charge,
      platformDiscountPct: res.platform_discount_pct,
      explanation: res.explanation,
    };
  },

  async submitFeedback(
    requestId: string,
    rating: number,
    comment?: string,
  ): Promise<Feedback> {
    if (!isRealBackend()) {
      const { api } = await import("./mock-api");
      return api.submitFeedback(requestId, rating, comment);
    }
    const res = await fetchJson<any>(`/deliveries/requests/${encodeURIComponent(requestId)}/feedback`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ rating, comment: comment || "" }),
    });
    const f = res.feedback || {};
    return {
      id: f.public_id,
      driverId: String(f.driver_id),
      requestId: String(f.request_id),
      rating: f.rating,
      comment: f.comment ?? null,
      createdAt: f.created_at,
    };
  },

  async listDriverMatches(): Promise<DriverMatch[]> {
    return this.listDriverRequests();
  },
};

export { isRealBackend };