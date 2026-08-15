"""Lightweight geo utilities for route/pickup overlap estimates.

The AI matching pipeline needs rough distance estimates without a full
geocoding dependency. Locations are free-text ("Mumbai, Maharashtra"), so we
normalize tokens and estimate overlap. When GPS coordinates are available
(waypoints with lat/lng) we use a haversine distance.
"""

from __future__ import annotations

import math
import re
from difflib import SequenceMatcher

_STOPWORDS = {
    "the", "and", "near", "around", "in", "at", "on", "road", "rd", "street",
    "st", "area", "district", "dist", "city", "town", "zone", "via",
}


def normalize_location(text: str) -> str:
    """Normalize a free-text location for token comparison."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    tokens = [t for t in text.split() if t not in _STOPWORDS]
    return " ".join(sorted(tokens)).strip()


def location_overlap(loc_a: str, loc_b: str) -> float:
    """Return a 0..1 similarity between two free-text locations."""
    a, b = normalize_location(loc_a), normalize_location(loc_b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def route_points(route: object) -> list[str]:
    """Named points along a driver route: origin, destination, waypoints."""
    points = [getattr(route, "origin", ""), getattr(route, "destination", "")]
    for wp in getattr(route, "waypoints", None) or []:
        if isinstance(wp, dict):
            label = wp.get("label") or wp.get("city") or wp.get("address")
            if label:
                points.append(label)
    return [p for p in points if p]


def geographic_route_overlap(parcel: object, route: object) -> float:
    """Geographic route overlap (0..1): how well the parcel's pickup and drop
    points lie on the driver's route (origin/destination/waypoints).

    Uses token-overlap on the free-text locations. This is the true route
    overlap metric — distinct from embedding cosine similarity, which is used
    only for candidate recall.
    """
    points = route_points(route)
    if not points:
        return 0.0
    pickup = max(
        location_overlap(p, getattr(parcel, "pickup_location", "")) for p in points
    )
    drop = max(
        location_overlap(p, getattr(parcel, "drop_location", "")) for p in points
    )
    return round((pickup + drop) / 2.0, 3)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two coordinates in kilometers."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# Pickup is considered "on the route" when it matches a route point this
# closely (or is within this many km of a GPS waypoint on the route).
DETOUR_ZERO_OVERLAP = 0.85
PICKUP_ON_ROUTE_KM = 0.3
# Max additional km used by the free-text fallback; matches the proximity
# scale in the match score (proximity = 1 - detour / 10).
DETOUR_MAX_KM = 10.0


def _point_coords(point: object) -> tuple[float, float] | None:
    if isinstance(point, dict):
        lat, lon = point.get("lat"), point.get("lng")
        if lat is not None and lon is not None:
            return float(lat), float(lon)
    return None


def _route_point_coords(route: object) -> list[tuple[float, float]]:
    coords: list[tuple[float, float]] = []
    for wp in getattr(route, "waypoints", None) or []:
        c = _point_coords(wp)
        if c:
            coords.append(c)
    return coords


def _pickup_coords(parcel: object) -> tuple[float, float] | None:
    pickup = getattr(parcel, "pickup_location", "")
    if isinstance(pickup, dict):
        c = _point_coords(pickup)
        if c:
            return c
    for wp in getattr(parcel, "waypoints", None) or []:
        c = _point_coords(wp)
        if c:
            return c
    return None


def estimate_pickup_detour_km(parcel: object, driver_route: object) -> float:
    """Additional distance the driver must travel off their published route
    (origin, destination, or any waypoint) to reach the sender's pickup.

    - If the pickup lies directly on the driver's route, detour = 0 km.
    - Otherwise return the actual additional distance (GPS when available,
      deterministic token-overlap estimate otherwise).

    The returned value is the exact same ``pickup_detour_km`` used by the AI
    match score (proximity = 1 - detour / 10) and by the ETA estimate, so the
    number shown on the UI is always consistent with the score.
    """
    pickup = getattr(parcel, "pickup_location", "") or ""
    points = route_points(driver_route)
    if not points:
        return 0.0

    # Free-text check against every named point on the route (not just origin).
    best_overlap = max(location_overlap(pickup, p) for p in points)
    if best_overlap >= DETOUR_ZERO_OVERLAP:
        return 0.0

    # GPS check: distance from the pickup to the nearest route waypoint.
    pickup_coords = _pickup_coords(parcel)
    route_coords = _route_point_coords(driver_route)
    if pickup_coords and route_coords:
        nearest = min(
            haversine_km(*pickup_coords, *rc) for rc in route_coords
        )
        return round(0.0 if nearest <= PICKUP_ON_ROUTE_KM else nearest, 2)

    # Deterministic estimate: how far off the route the pickup sits, 0-10 km.
    return round((1.0 - best_overlap) * DETOUR_MAX_KM, 2)
