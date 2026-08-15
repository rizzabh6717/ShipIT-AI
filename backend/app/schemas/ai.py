from pydantic import BaseModel, Field

from app.models.enums import ParcelSizeTier
from app.schemas.driver import DriverRead


class MatchRequest(BaseModel):
    parcel_id: str = Field(description="Public parcel identifier, e.g. 'P123'")


class MatchResult(BaseModel):
    driver_id: str
    score: float = Field(ge=0, le=1)
    overlap: float = Field(default=0.0, ge=0, le=1, description="Raw route-overlap similarity, 0..1")
    eta: str
    reason: list[str]
    detour_km: float = 0.0
    driver: DriverRead | None = None


class MatchResponse(BaseModel):
    parcel_id: str
    matches: list[MatchResult] = Field(default_factory=list)
    model: str | None = None
    provider: str | None = None
    ranked_by: str = "ai"


class RouteEmbedRequest(BaseModel):
    route_id: int | None = None
    origin: str
    destination: str
    waypoints: list[dict] | None = None


class BudgetRecommendRequest(BaseModel):
    pickup_location: str
    drop_location: str
    weight: float = Field(gt=0)
    dimensions: dict | None = None
    size_tier: ParcelSizeTier | None = None


class BudgetRecommend(BaseModel):
    """Porter-inspired price breakdown.

    recommended_budget is the pre-discount Recommended Price; total_amount is
    the price shown to the sender after the 10% platform discount.
    """

    recommended_budget: float
    total_amount: float
    currency: str = "INR"
    base_rate: float
    distance_km: float
    distance_charge: float
    weight_charge: float
    size_tier: str
    size_charge: float
    platform_discount_pct: float
    explanation: str
