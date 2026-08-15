"""Explainable AI: turns raw match signals into human-readable reasons."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.driver import Driver
from app.models.parcel import Parcel
from app.models.route import Route


@dataclass
class ScoreBreakdown:
    route_overlap: float
    pickup_proximity: float
    deadline_score: float
    reliability_score: float
    capacity_score: float
    pickup_detour_km: float
    weights: dict[str, float]

    @property
    def total(self) -> float:
        w = self.weights
        return (
            w["route_overlap"] * self.route_overlap
            + w["pickup_proximity"] * self.pickup_proximity
            + w["deadline"] * self.deadline_score
            + w["reliability"] * self.reliability_score
            + w["capacity"] * self.capacity_score
        )


DEFAULT_WEIGHTS = {
    "route_overlap": 0.35,
    "pickup_proximity": 0.15,
    "deadline": 0.15,
    "reliability": 0.20,
    "capacity": 0.15,
}


def hours_until(deadline: datetime | None) -> float | None:
    if deadline is None:
        return None
    return (deadline - datetime.now(timezone.utc)).total_seconds() / 3600.0


def estimate_eta(detour_km: float) -> str:
    """Rough ETA string based on pickup detour distance."""
    minutes = max(15, round((detour_km / 40.0) * 60.0))
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def breakdown(parcel: Parcel, driver: Driver, route: Route | None, route_overlap: float, pickup_detour_km: float) -> ScoreBreakdown:
    """Compute the component scores for a parcel-driver pair."""
    # 1. Route overlap (semantic similarity between parcel route and driver route)
    overlap = max(0.0, min(1.0, route_overlap))

    # 2. Pickup proximity (1 = at origin, 0 = >=10km away)
    proximity = max(0.0, 1.0 - pickup_detour_km / 10.0)

    # 3. Deadline feasibility
    hours = hours_until(parcel.deadline)
    if hours is None:
        deadline_score = 0.7  # flexible window
    else:
        deadline_score = min(1.0, max(0.0, hours / 48.0))

    # 4. Reliability (rating + on-time rate + completion rate)
    reliability_score = (
        (driver.rating / 5.0) * 0.5
        + (driver.on_time_rate or 0.0) * 0.3
        + (driver.completion_rate or 1.0) * 0.2
    )

    # 5. Capacity (full credit if it fits, scaled penalty otherwise)
    if driver.capacity_kg >= parcel.weight:
        capacity_score = 1.0
    else:
        capacity_score = max(0.0, (driver.capacity_kg / parcel.weight) * 0.5)

    return ScoreBreakdown(
        route_overlap=overlap,
        pickup_proximity=proximity,
        deadline_score=deadline_score,
        reliability_score=reliability_score,
        capacity_score=capacity_score,
        pickup_detour_km=pickup_detour_km,
        weights=DEFAULT_WEIGHTS,
    )


def reasons(bd: ScoreBreakdown, parcel: Parcel, driver: Driver) -> list[str]:
    """Turn a breakdown into the bullet list shown to the user."""
    bullets = [
        f"Route overlap: {bd.route_overlap * 100:.0f}%",
        f"Pickup detour: {bd.pickup_detour_km:.1f} km",
    ]

    hours = hours_until(parcel.deadline)
    if hours is None:
        bullets.append("Delivery window: flexible")
    else:
        bullets.append(f"Delivery deadline: {hours:.1f}h away")

    if driver.capacity_kg >= parcel.weight:
        bullets.append(f"Vehicle capacity sufficient ({parcel.weight}kg of {driver.capacity_kg:.0f}kg)")
    else:
        bullets.append(f"Capacity shortfall: parcel {parcel.weight}kg > {driver.capacity_kg:.0f}kg")

    bullets.append(f"Driver reliability: {driver.rating:.1f}/5")
    bullets.append(f"On-time rate: {driver.on_time_rate * 100:.0f}%")
    bullets.append(f"Completion rate: {driver.completion_rate * 100:.0f}%")
    return bullets
