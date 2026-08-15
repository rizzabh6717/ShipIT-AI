"""Porter-inspired price recommendation for a parcel.

Recommended Price = Base Fare + Distance Charge + Weight Charge + Size Charge

  - Base Fare            : ₹40
  - Distance Charge      : ₹12 × distance_km
  - Weight Charge        : 0–5 kg ₹0 · 5–10 kg ₹20 · 10–20 kg ₹50 · 20+ kg ₹80
  - Size Charge          : Small ₹0 · Medium ₹20 · Large ₹40

A 10% platform discount is then applied, and the discounted Total Amount is the
price shown to the sender. The sender may still adjust the final budget before
publishing the parcel.
"""

from __future__ import annotations

from app.models.enums import ParcelSizeTier
from app.schemas.ai import BudgetRecommend
from app.utils.geo import location_overlap

BASE_RATE = 40.0          # INR base fare per shipment
PER_KM = 12.0             # INR per km
WEIGHT_CHARGES = [        # (min_kg, max_kg_exclusive, charge)
    (0.0, 5.0, 0.0),
    (5.0, 10.0, 20.0),
    (10.0, 20.0, 50.0),
    (20.0, float("inf"), 80.0),
]
SIZE_CHARGES = {
    ParcelSizeTier.SMALL: 0.0,
    ParcelSizeTier.MEDIUM: 20.0,
    ParcelSizeTier.LARGE: 40.0,
}
PLATFORM_DISCOUNT_PCT = 10.0

# Largest dimension that still counts as the next smaller size tier.
SMALL_MAX_CM = 29.0
MEDIUM_MAX_CM = 59.0


def estimate_distance_km(pickup: str, drop: str) -> float:
    """Estimate route distance from location similarity.

    Same city/region => short hop; unrelated locations => long haul.
    """
    overlap = location_overlap(pickup, drop)
    if overlap >= 0.8:
        return 12.0
    if overlap >= 0.4:
        return 80.0
    return 350.0


def compute_weight_charge(weight: float) -> float:
    for low, high, charge in WEIGHT_CHARGES:
        if weight >= low and weight < high:
            return charge
    return WEIGHT_CHARGES[-1][2]


def size_tier_for(dimensions: dict | None) -> ParcelSizeTier:
    """Derive a size tier from the largest dimension of the parcel."""
    if not dimensions:
        return ParcelSizeTier.MEDIUM
    longest = max(
        (float(dimensions.get(k) or 0) for k in ("length", "width", "height")),
        default=0.0,
    )
    if longest > MEDIUM_MAX_CM:
        return ParcelSizeTier.LARGE
    if longest > SMALL_MAX_CM:
        return ParcelSizeTier.MEDIUM
    return ParcelSizeTier.SMALL


def recommend(
    pickup_location: str,
    drop_location: str,
    weight: float,
    dimensions: dict | None,
    size_tier: ParcelSizeTier | None = None,
) -> BudgetRecommend:
    distance_km = estimate_distance_km(pickup_location, drop_location)
    tier = size_tier or size_tier_for(dimensions)

    distance_charge = distance_km * PER_KM
    weight_charge = compute_weight_charge(weight)
    size_charge = SIZE_CHARGES[tier]

    recommended = BASE_RATE + distance_charge + weight_charge + size_charge
    recommended = round(recommended / 10.0) * 10.0  # round to nearest 10 INR
    total = recommended * (1.0 - PLATFORM_DISCOUNT_PCT / 100.0)

    explanation = (
        f"₹{recommended:.0f} = base ₹{BASE_RATE:.0f} + distance ({distance_km:.0f} km × ₹{PER_KM:.0f}) "
        f"+ weight tier (₹{weight_charge:.0f}) + {tier.value} size (₹{size_charge:.0f}) "
        f"− {PLATFORM_DISCOUNT_PCT:.0f}% platform discount"
    )
    return BudgetRecommend(
        recommended_budget=recommended,
        total_amount=round(total, 2),
        base_rate=BASE_RATE,
        distance_km=round(distance_km, 1),
        distance_charge=round(distance_charge, 2),
        weight_charge=round(weight_charge, 2),
        size_tier=tier.value,
        size_charge=round(size_charge, 2),
        platform_discount_pct=PLATFORM_DISCOUNT_PCT,
        explanation=explanation,
    )