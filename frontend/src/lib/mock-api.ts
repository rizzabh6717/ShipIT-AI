// Mock data layer. Mirrors the shape of a REST backend so a real fetch client
// (VITE_API_URL) can be dropped in later without touching UI code.
//
// The mock is fully data-driven: driver routes, parcels and delivery requests
// are persisted in localStorage, and driver matches are computed deterministically
// from those collections — never from hardcoded arrays.

export type Role = "sender" | "driver";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
}

export type ParcelStatus =
  | "pending"
  | "pending_driver_approval"
  | "matched"
  | "in_transit"
  | "delivered";

export interface Shipment {
  id: string;
  from: string;
  to: string;
  weight: number;
  status: ParcelStatus;
  match: number;
  price: number;
  eta: string;
  trackingId: string;
  description?: string;
  dimensions?: string;
  deadline?: string;
  requestId?: string;
  proofImageUrl?: string;
}

export interface Feedback {
  id: string;
  driverId: string;
  requestId: string;
  rating: number;
  comment: string | null;
  createdAt: string;
}

export interface DriverProfile {
  publicId: string;
  name: string;
  phone?: string;
  email?: string;
  vehicleType: string;
  licenseNumber?: string;
  vehicleRegNumber?: string;
  capacityKg: number;
  rating: number;
  onTimeRate: number;
  completionRate: number;
  reviewsCount: number;
  completedDeliveries: number;
  currentCity?: string;
  routes: { from: string; to: string; departureTime?: string; isActive: boolean }[];
}

export interface DriverStats {
  totalDeliveries: number;
  completedDeliveries: number;
  pendingDeliveries: number;
  inTransitDeliveries: number;
  rejectedDeliveries: number;
  onTimeRate: number;
  completionRate: number;
  rating: number;
  reviewsCount: number;
  activeRoutes: number;
}

export interface BudgetRecommendation {
  recommendedBudget: number;
  totalAmount: number;
  currency: string;
  baseRate: number;
  distanceKm: number;
  distanceCharge: number;
  weightCharge: number;
  sizeTier: string;
  sizeCharge: number;
  platformDiscountPct: number;
  explanation: string;
}

export interface Parcel {
  id: string; // public id, e.g. "PA1B2C"
  senderId: string;
  from: string;
  to: string;
  weight: number;
  dimensions: string;
  description: string;
  deadline: string;
  budget: number;
  status: ParcelStatus;
  createdAt: string;
  driverId?: string;
  requestId?: string;
}

export type DeliveryRequestStatus =
  | "pending_driver_approval"
  | "rejected"
  | "matched"
  | "in_transit"
  | "delivered";

export interface DeliveryRequest {
  id: string;
  parcelId: string;
  driverId: string;
  routeId: string;
  status: DeliveryRequestStatus;
  createdAt: string;
  respondedAt?: string;
  proofImageUrl?: string;
}

export interface DriverRoute {
  id: string;
  driverId: string;
  driverName: string;
  vehicleType: string;
  vehicleLabel: string;
  from: string;
  to: string;
  departureTime: string;
  capacityKg: number;
  availableSpaceKg: number;
  pricePerKg: number;
  description: string;
  recurring: boolean;
  recurrenceDays: string[];
  status: "active" | "inactive";
  rating: number;
  onTimeRate: number;
  createdAt: string;
}

export interface DriverMatch {
  id: string;
  driverId: string;
  routeId: string;
  driver: string;
  vehicle: string;
  rating: number;
  match: number;
  overlap: number;
  detour: number;
  eta: string;
  payout: number;
  from: string;
  to: string;
  weight: number;
  distance: number;
  reasons: string[];
  requestId?: string;
  requestStatus?: DeliveryRequestStatus;
  rankedBy?: "ai" | "heuristic";
  description?: string;
  deadline?: string;
  dimensions?: string;
  profile?: DriverProfile;
  proofImageUrl?: string;
}

export interface MarketRoute {
  id: string;
  from: string;
  to: string;
  drivers: number;
  time: string;
  distance: number;
  co2: number;
  price: number;
  match: number;
}

const delay = (ms = 450) => new Promise((r) => setTimeout(r, ms));

// ---------------------------------------------------------------------------
// Storage
// ---------------------------------------------------------------------------

const ROUTES_KEY = "shipit.driverRoutes";
const PARCELS_KEY = "shipit.parcels";
const REQUESTS_KEY = "shipit.deliveryRequests";

function read<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function write<T>(key: string, value: T) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key, JSON.stringify(value));
}

function readRoutes(): DriverRoute[] {
  return read<DriverRoute[]>(ROUTES_KEY, []);
}
function writeRoutes(routes: DriverRoute[]) {
  write(ROUTES_KEY, routes);
}
function readParcels(): Parcel[] {
  return read<Parcel[]>(PARCELS_KEY, []);
}
function writeParcels(parcels: Parcel[]) {
  write(PARCELS_KEY, parcels);
}
function readRequests(): DeliveryRequest[] {
  return read<DeliveryRequest[]>(REQUESTS_KEY, []);
}
function writeRequests(requests: DeliveryRequest[]) {
  write(REQUESTS_KEY, requests);
}

function currentUser(): User | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem("shipit.user");
    if (!raw) return null;
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

function uid(prefix: string): string {
  return `${prefix}${Math.random().toString(36).slice(2, 7).toUpperCase()}`;
}

// ---------------------------------------------------------------------------
// Distance model (approximate km between NCR cities)
// ---------------------------------------------------------------------------

const DIST: Record<string, number> = {
  "Delhi|Noida": 25,
  "Delhi|Gurgaon": 32,
  "Delhi|Ghaziabad": 21,
  "Delhi|Faridabad": 29,
  "Delhi|Greater Noida": 40,
  "Delhi|Manesar": 45,
  "Delhi|Bahadurgarh": 28,
  "Noida|Gurgaon": 45,
  "Noida|Ghaziabad": 30,
  "Noida|Faridabad": 40,
  "Noida|Greater Noida": 15,
  "Noida|Manesar": 55,
  "Noida|Bahadurgarh": 50,
  "Gurgaon|Ghaziabad": 42,
  "Gurgaon|Faridabad": 35,
  "Gurgaon|Greater Noida": 55,
  "Gurgaon|Manesar": 15,
  "Gurgaon|Bahadurgarh": 55,
  "Ghaziabad|Faridabad": 45,
  "Ghaziabad|Greater Noida": 35,
  "Ghaziabad|Manesar": 60,
  "Ghaziabad|Bahadurgarh": 35,
  "Faridabad|Greater Noida": 40,
  "Faridabad|Manesar": 35,
  "Faridabad|Bahadurgarh": 55,
  "Greater Noida|Manesar": 65,
  "Greater Noida|Bahadurgarh": 70,
  "Manesar|Bahadurgarh": 70,
};

function dist(a: string, b: string): number {
  if (!a || !b) return 30;
  if (a === b) return 0;
  const key = [a, b].sort().join("|");
  return DIST[key] ?? 30;
}

// A city is "on the way" from A to B if going through it adds little distance.
function onTheWay(city: string, from: string, to: string): boolean {
  if (city === from || city === to) return true;
  return dist(from, city) + dist(city, to) <= dist(from, to) * 1.15;
}

function estimateEta(departureTime: string, extraKm: number): string {
  if (!departureTime) return "Flexible";
  const totalKm = extraKm + 10;
  const mins = Math.round((totalKm / 40) * 60);
  const d = new Date(departureTime);
  if (Number.isNaN(d.getTime())) return "Flexible";
  d.setMinutes(d.getMinutes() + mins);
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// Matching engine (deterministic, explainable)
// ---------------------------------------------------------------------------

function scoreRoute(parcel: Parcel, route: DriverRoute): DriverMatch | null {
  const from = route.from;
  const to = route.to;

  // 1. Compatibility: pickup and drop must lie on the driver's route.
  const pickupOk = onTheWay(parcel.from, from, to);
  const dropOk = onTheWay(parcel.to, from, to);
  if (!pickupOk || !dropOk) return null;

  // 2. Capacity must fit the parcel.
  if (parcel.weight > route.availableSpaceKg) return null;

  // 3. Departure must not be after the parcel deadline.
  if (parcel.deadline && route.departureTime) {
    const depart = new Date(route.departureTime);
    const deadline = new Date(`${parcel.deadline}T23:59:59`);
    if (!Number.isNaN(depart.getTime()) && !Number.isNaN(deadline.getTime()) && depart > deadline) {
      return null;
    }
  }

  // 4. Direction alignment: how closely the driver travels the parcel's way.
  const direction =
    from === parcel.from && to === parcel.to
      ? 1
      : from === parcel.from
        ? 0.9
        : to === parcel.to
          ? 0.85
          : from === parcel.to || to === parcel.from
            ? 0.5
            : 0.8;

  // 5. Detour: extra km the driver must travel to handle this parcel.
  const extra =
    dist(from, parcel.from) + dist(parcel.from, parcel.to) + dist(parcel.to, to) - dist(from, to);
  const detour = Math.max(0, Math.round(extra * 10) / 10);

  // 6. Route overlap: fraction of the parcel journey the driver covers.
  const totalPath = Math.max(1, dist(from, parcel.from) + dist(parcel.from, parcel.to) + dist(parcel.to, to));
  const overlap = Math.min(100, Math.round((100 * dist(parcel.from, parcel.to)) / totalPath));

  const capacityFit = Math.min(1, route.availableSpaceKg / (route.availableSpaceKg + parcel.weight));
  const reliability = (route.rating / 5) * 0.5 + (route.onTimeRate || 0.9) * 0.5;
  const detourScore = Math.max(0, 1 - detour / 15);

  const score =
    0.4 * (overlap / 100) +
    0.15 * direction +
    0.15 * capacityFit +
    0.2 * reliability +
    0.1 * detourScore;
  const match = Math.max(0, Math.min(100, Math.round(score * 100)));

  const reasons: string[] = [];
  if (from === parcel.from) reasons.push("Route departs from your pickup location");
  else if (pickupOk) reasons.push("Pickup location is on the route");
  if (to === parcel.to) reasons.push("Drops near your destination");
  else if (dropOk) reasons.push("Destination is on the route");
  if (parcel.weight <= route.availableSpaceKg) reasons.push("Capacity available for this load");
  if (route.onTimeRate >= 0.92) reasons.push("High on-time delivery rate");
  if (detour <= 3) reasons.push("Minimal pickup detour");
  if (route.rating >= 4.8) reasons.push("Highly rated driver");

  return {
    id: `dm-${parcel.id}-${route.id}`,
    driverId: route.driverId,
    routeId: route.id,
    driver: route.driverName,
    vehicle: route.vehicleLabel,
    rating: route.rating,
    match,
    overlap,
    detour,
    eta: estimateEta(route.departureTime, detour),
    payout: Math.round(parcel.budget || route.pricePerKg * parcel.weight),
    from: parcel.from,
    to: parcel.to,
    weight: parcel.weight,
    distance: dist(parcel.from, parcel.to),
    reasons,
  };
}

function computeMatchesForParcel(parcel: Parcel): DriverMatch[] {
  const requests = readRequests().filter((r) => r.parcelId === parcel.id);
  const rejectedDriverIds = new Set(
    requests.filter((r) => r.status === "rejected").map((r) => r.driverId),
  );
  const activeByDriver = new Map(
    requests
      .filter((r) => r.status === "pending_driver_approval" || r.status === "matched")
      .map((r) => [r.driverId, r]),
  );

  const matches = readRoutes()
    .filter((r) => r.status === "active" && !rejectedDriverIds.has(r.driverId))
    .map((r) => {
      const scored = scoreRoute(parcel, r);
      if (!scored) return null;
      const activeReq = activeByDriver.get(r.driverId);
      if (activeReq) {
        scored.requestId = activeReq.id;
        scored.requestStatus = activeReq.status;
      }
      return scored;
    })
    .filter((m): m is DriverMatch => m !== null)
    .sort((a, b) => b.match - a.match);

  return matches;
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

export const api = {
  async register(input: { name: string; email: string; password: string; role: Role }) {
    await delay();
    if (!input.email.includes("@")) throw new Error("Enter a valid email address");
    if (input.password.length < 6) throw new Error("Password must be at least 6 characters");
    const user: User = {
      id: `usr_${Math.random().toString(36).slice(2, 9)}`,
      name: input.name,
      email: input.email,
      role: input.role,
    };
    return { user, token: `mock.${user.id}` };
  },

  async login(input: { email: string; password: string }) {
    await delay();
    if (!input.email.includes("@")) throw new Error("Enter a valid email address");
    if (input.password.length < 6) throw new Error("Password must be at least 6 characters");
    const role: Role = input.email.startsWith("driver") ? "driver" : "sender";
    const name = (input.email.split("@")[0] ?? "User")
      .replace(/[._-]/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    const user: User = {
      id: `usr_${Math.random().toString(36).slice(2, 9)}`,
      name,
      email: input.email,
      role,
    };
    return { user, token: `mock.${user.id}` };
  },

  // --- Driver routes -------------------------------------------------------

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
    await delay(600);
    const user = currentUser();
    if (!user) throw new Error("Please sign in to publish a route");
    const route: DriverRoute = {
      id: uid("R"),
      driverId: user.id,
      driverName: user.name,
      vehicleType: input.vehicleType,
      vehicleLabel: input.vehicleLabel,
      from: input.from,
      to: input.to,
      departureTime: input.departureTime,
      capacityKg: input.capacityKg,
      availableSpaceKg: input.availableSpaceKg,
      pricePerKg: input.pricePerKg,
      description: input.description,
      recurring: input.recurring,
      recurrenceDays: input.recurrenceDays,
      status: "active",
      rating: 4.7,
      onTimeRate: 0.93,
      createdAt: new Date().toISOString(),
    };
    writeRoutes([route, ...readRoutes()]);
    return route;
  },

  async listActiveDriverRoutes(): Promise<DriverRoute[]> {
    await delay(300);
    return readRoutes().filter((r) => r.status === "active");
  },

  // --- Parcels --------------------------------------------------------------

  async createShipment(input: {
    from: string;
    to: string;
    weight: number;
    dimensions: string;
    description: string;
    deadline: string;
    budget?: number;
  }): Promise<Shipment> {
    await delay(500);
    const user = currentUser();
    if (!user) throw new Error("Please sign in to send a parcel");
    const parcel: Parcel = {
      id: uid("P"),
      senderId: user.id,
      from: input.from,
      to: input.to,
      weight: input.weight,
      dimensions: input.dimensions,
      description: input.description,
      deadline: input.deadline,
      budget: input.budget ?? 100,
      status: "pending",
      createdAt: new Date().toISOString(),
    };
    writeParcels([parcel, ...readParcels()]);
    return {
      id: parcel.id,
      from: parcel.from,
      to: parcel.to,
      weight: parcel.weight,
      status: parcel.status,
      match: 0,
      price: Math.round(parcel.budget),
      eta: "Pending",
      trackingId: `SHIPIT-${parcel.id.slice(1)}`,
    };
  },

  async listShipments(): Promise<Shipment[]> {
    await delay(300);
    const user = currentUser();
    const parcels = user ? readParcels().filter((p) => p.senderId === user.id) : [];
    return parcels.map((p) => ({
      id: p.id,
      from: p.from,
      to: p.to,
      weight: p.weight,
      status: p.status,
      match: 0,
      price: Math.round(p.budget),
      eta: "Pending",
      trackingId: `SHIPIT-${p.id.slice(1)}`,
    }));
  },

  // --- AI matching -----------------------------------------------------------

  async matchDrivers(shipmentId: string): Promise<DriverMatch[]> {
    await delay(550);
    const parcel = readParcels().find((p) => p.id === shipmentId);
    if (!parcel) return [];
    return computeMatchesForParcel(parcel);
  },

  // --- Delivery requests ------------------------------------------------------

  async selectDriver(parcelId: string, driverId: string, routeId: string): Promise<DeliveryRequest> {
    await delay(400);
    const parcels = readParcels();
    const parcel = parcels.find((p) => p.id === parcelId);
    if (!parcel) throw new Error("Parcel not found");
    const requests = readRequests();
    const active = requests.find(
      (r) =>
        r.parcelId === parcel.id &&
        (r.status === "pending_driver_approval" || r.status === "matched"),
    );
    if (active) {
      throw new Error("This parcel already has an active delivery request");
    }
    const request: DeliveryRequest = {
      id: uid("REQ"),
      parcelId: parcel.id,
      driverId,
      routeId,
      status: "pending_driver_approval",
      createdAt: new Date().toISOString(),
    };
    writeRequests([request, ...requests]);
    parcel.status = "pending_driver_approval";
    parcel.driverId = driverId;
    parcel.requestId = request.id;
    writeParcels(parcels);
    return request;
  },

  async listDriverRequests(): Promise<DriverMatch[]> {
    await delay(300);
    const user = currentUser();
    if (!user) return [];
    const routes = readRoutes().filter((r) => r.driverId === user.id);
    const routeIds = new Set(routes.map((r) => r.id));
    const requests = readRequests().filter(
      (r) => routeIds.has(r.routeId) && r.status === "pending_driver_approval",
    );
    const parcels = readParcels();
    const matches: DriverMatch[] = [];
    for (const req of requests) {
      const parcel = parcels.find((p) => p.id === req.parcelId);
      const route = routes.find((r) => r.id === req.routeId);
      if (!parcel || !route) continue;
      const scored = scoreRoute(parcel, route);
      if (!scored) continue;
      matches.push({ ...scored, id: req.id, requestId: req.id, requestStatus: req.status });
    }
    return matches;
  },

  async respondToRequest(requestId: string, accept: boolean): Promise<void> {
    await delay(400);
    const requests = readRequests();
    const req = requests.find((r) => r.id === requestId);
    if (!req) throw new Error("Request not found");
    req.status = accept ? "matched" : "rejected";
    req.respondedAt = new Date().toISOString();
    writeRequests(requests);

    const routes = readRoutes();
    const route = routes.find((r) => r.id === req.routeId);

    const parcels = readParcels();
    const parcel = parcels.find((p) => p.id === req.parcelId);
    if (parcel) {
      if (accept) {
        parcel.status = "matched";
        if (route) {
          route.availableSpaceKg = Math.max(0, route.availableSpaceKg - parcel.weight);
          writeRoutes(routes);
        }
      } else {
        parcel.status = "pending";
        parcel.driverId = undefined;
        parcel.requestId = undefined;
      }
      writeParcels(parcels);
    }
  },

  async listDriverDeliveries(): Promise<DriverMatch[]> {
    await delay(300);
    const user = currentUser();
    if (!user) return [];
    const routes = readRoutes().filter((r) => r.driverId === user.id);
    const routeIds = new Set(routes.map((r) => r.id));
    const requests = readRequests().filter(
      (r) => routeIds.has(r.routeId) && r.status !== "pending_driver_approval" && r.status !== "rejected",
    );
    const parcels = readParcels();
    const matches: DriverMatch[] = [];
    for (const req of requests) {
      const parcel = parcels.find((p) => p.id === req.parcelId);
      const route = routes.find((r) => r.id === req.routeId);
      if (!parcel || !route) continue;
      const scored = scoreRoute(parcel, route);
      if (!scored) continue;
      matches.push({ ...scored, id: req.id, requestId: req.id, requestStatus: req.status });
    }
    return matches;
  },

  async confirmPickup(requestId: string): Promise<void> {
    await delay(400);
    const requests = readRequests();
    const req = requests.find((r) => r.id === requestId);
    if (!req) throw new Error("Delivery not found");
    req.status = "in_transit";
    writeRequests(requests);
    const parcels = readParcels();
    const parcel = parcels.find((p) => p.id === req.parcelId);
    if (parcel) {
      parcel.status = "in_transit";
      writeParcels(parcels);
    }
  },

  async markDelivered(requestId: string, proofImageUrl?: string): Promise<void> {
    await delay(400);
    if (!proofImageUrl) throw new Error("A proof-of-delivery photo is required");
    const requests = readRequests();
    const req = requests.find((r) => r.id === requestId);
    if (!req) throw new Error("Delivery not found");
    req.status = "delivered";
    req.proofImageUrl = proofImageUrl;
    writeRequests(requests);
    const parcels = readParcels();
    const parcel = parcels.find((p) => p.id === req.parcelId);
    if (parcel) {
      parcel.status = "delivered";
      writeParcels(parcels);
    }
  },

  // --- Tracking --------------------------------------------------------------

  async tracking(parcelPublicId: string) {
    await delay(400);
    const parcel = readParcels().find((p) => p.id === parcelPublicId);
    if (!parcel) throw new Error("Parcel not found");
    const requests = readRequests().filter((r) => r.parcelId === parcel.id);
    const latest = requests[requests.length - 1] ?? null;
    const routes = readRoutes();
    const route = latest ? routes.find((r) => r.id === latest.routeId) ?? null : null;
    const driverName = latest && route ? route.driverName : null;
    // Match data is only surfaced for the driver on an active/accepted request —
    // never recomputed as a background "best match".
    const scored =
      latest && route && latest.status !== "rejected" ? scoreRoute(parcel, route) : null;

    const steps: { label: string; time: string; done: boolean }[] = [
      { label: "Parcel posted", time: new Date(parcel.createdAt).toLocaleString(), done: true },
    ];

    if (parcel.status === "pending_driver_approval" && driverName) {
      steps.push({
        label: `Awaiting ${driverName}'s approval`,
        time: "Request sent",
        done: false,
      });
    } else if (driverName) {
      steps.push({
        label: `AI matched with ${driverName}`,
        time: "Approved",
        done: parcel.status !== "pending_driver_approval",
      });
    }

    if (parcel.status === "matched" || parcel.status === "in_transit" || parcel.status === "delivered") {
      steps.push({ label: "Driver accepted", time: "Approved", done: true });
    }
    if (parcel.status === "in_transit" || parcel.status === "delivered") {
      steps.push({ label: "Picked up", time: "Driver confirmed pickup", done: true });
      steps.push({ label: "In transit", time: "On the way", done: true });
    }
    if (parcel.status === "delivered") {
      steps.push({ label: "Delivered", time: "Proof of delivery uploaded", done: true });
    }

    return {
      trackingId: parcel.id,
      from: parcel.from,
      to: parcel.to,
      driver: driverName || "No driver assigned",
      match: scored?.match ?? 0,
      eta: scored?.eta || parcel.status,
      status: parcel.status,
      steps,
    };
  },

  // --- Marketplace -----------------------------------------------------------

  async listMarketRoutes(): Promise<MarketRoute[]> {
    await delay(300);
    const routes = readRoutes().filter((r) => r.status === "active");
    const byCorridor = new Map<string, DriverRoute[]>();
    for (const r of routes) {
      const key = `${r.from}|${r.to}`;
      const list = byCorridor.get(key) ?? [];
      list.push(r);
      byCorridor.set(key, list);
    }
    return [...byCorridor.entries()].map(([key, group]) => {
      const [from, to] = key.split("|");
      const avgPrice = Math.round(group.reduce((s, r) => s + r.pricePerKg, 0) / group.length);
      const avgCapacity = Math.round(
        group.reduce((s, r) => s + r.availableSpaceKg, 0) / group.length,
      );
      return {
        id: key,
        from,
        to,
        drivers: group.length,
        time: "N/A",
        distance: dist(from, to),
        co2: Math.round((dist(from, to) * 0.11 * group.length) * 10) / 10,
        price: avgPrice,
        match: Math.min(100, Math.round((avgCapacity / 1000) * 100)),
      };
    });
  },

  // --- Production features (mock) --------------------------------------------

  async uploadRequestProof(requestId: string, file: File): Promise<string> {
    await delay(300);
    const url = `/uploads/proofs/${file.name || "mock-proof.jpg"}`;
    const requests = readRequests();
    const req = requests.find((r) => r.id === requestId);
    if (req) {
      req.proofImageUrl = url;
      writeRequests(requests);
    }
    return url;
  },

  async getDriverProfile(driverPublicId: string): Promise<DriverProfile> {
    await delay(250);
    const route = readRoutes().find((r) => r.driverId === driverPublicId) ?? null;
    return {
      publicId: driverPublicId,
      name: route?.driverName || "Driver",
      phone: "+91 90000 00000",
      email: "driver@example.com",
      vehicleType: route?.vehicleType || "car",
      licenseNumber: "DL-01-2025-000001",
      vehicleRegNumber: "MH12AB1234",
      capacityKg: route?.capacityKg || 500,
      rating: route?.rating ?? 4.5,
      onTimeRate: route?.onTimeRate ?? 0.93,
      completionRate: 0.98,
      reviewsCount: 12,
      completedDeliveries: 34,
      ...(route?.from ? { currentCity: route.from } : {}),
      routes: route
        ? [{ from: route.from, to: route.to, departureTime: route.departureTime, isActive: true }]
        : [],
    };
  },

  async getDriverRoutes(_driverPublicId: string): Promise<DriverProfile["routes"]> {
    await delay(200);
    return readRoutes().map((r) => ({
      from: r.from,
      to: r.to,
      departureTime: r.departureTime,
      isActive: r.status === "active",
    }));
  },

  async getDriverStats(): Promise<DriverStats> {
    await delay(250);
    return {
      totalDeliveries: 12,
      completedDeliveries: 11,
      pendingDeliveries: 1,
      inTransitDeliveries: 0,
      rejectedDeliveries: 1,
      onTimeRate: 0.94,
      completionRate: 0.92,
      rating: 4.8,
      reviewsCount: 12,
      activeRoutes: 1,
    };
  },

  async updateAvailability(_status: "available" | "offline"): Promise<void> {
    await delay(250);
  },

  async recommendBudget(input: {
    from: string;
    to: string;
    weight: number;
    dimensions?: string;
  }): Promise<BudgetRecommendation> {
    await delay(350);
    const km = dist(input.from, input.to);
    const w = input.weight;
    const weightCharge = w < 5 ? 0 : w < 10 ? 20 : w < 20 ? 50 : 80;
    const nums = (input.dimensions || "").match(/\d+(\.\d+)?/g)?.map(Number) ?? [];
    const longest = Math.max(...nums, 0);
    const sizeTier = longest > 59 ? "large" : longest > 29 ? "medium" : "small";
    const sizeCharge = sizeTier === "large" ? 40 : sizeTier === "medium" ? 20 : 0;
    const recommended = Math.round((40 + km * 12 + weightCharge + sizeCharge) / 10) * 10;
    const totalAmount = Math.round(recommended * 0.9 * 100) / 100;
    return {
      recommendedBudget: recommended,
      totalAmount,
      currency: "INR",
      baseRate: 40,
      distanceKm: km,
      distanceCharge: km * 12,
      weightCharge,
      sizeTier,
      sizeCharge,
      platformDiscountPct: 10,
      explanation: `Recommended ₹${recommended} = base ₹40 + distance (${km} km × ₹12) + weight tier (₹${weightCharge}) + ${sizeTier} size (₹${sizeCharge}) − 10% platform discount`,
    };
  },

  async submitFeedback(
    requestId: string,
    rating: number,
    comment?: string,
  ): Promise<Feedback> {
    await delay(400);
    return {
      id: uid("FB"),
      driverId: "D1",
      requestId,
      rating,
      comment: comment || null,
      createdAt: new Date().toISOString(),
    };
  },
};
