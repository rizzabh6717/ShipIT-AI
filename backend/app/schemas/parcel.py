from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ParcelSizeTier, ParcelStatus
from app.schemas.driver import DriverRead


class ParcelBase(BaseModel):
    pickup_location: str = Field(min_length=2, max_length=255)
    drop_location: str = Field(min_length=2, max_length=255)
    item_description: str = Field(min_length=2, max_length=500)
    item_value: float = Field(default=0.0, ge=0)
    weight: float = Field(default=1.0, gt=0, le=20000)
    dimensions: dict | None = None
    size_tier: ParcelSizeTier = ParcelSizeTier.MEDIUM
    budget: float = Field(default=0.0, ge=0)
    deadline: datetime | None = None
    special_instructions: str | None = None
    sender_photo_url: str | None = None


class ParcelCreate(ParcelBase):
    pass


class ParcelUpdate(BaseModel):
    pickup_location: str | None = None
    drop_location: str | None = None
    item_description: str | None = None
    item_value: float | None = Field(default=None, ge=0)
    weight: float | None = Field(default=None, gt=0)
    budget: float | None = Field(default=None, ge=0)
    deadline: datetime | None = None
    special_instructions: str | None = None


class ParcelStatusUpdate(BaseModel):
    status: ParcelStatus


class ParcelRead(ParcelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    sender_id: int
    status: ParcelStatus
    created_at: datetime
    updated_at: datetime


class ParcelWithMatches(ParcelRead):
    """Parcel plus a ranked list of explainable AI driver matches."""

    matches: list[dict] = Field(default_factory=list)
    best_driver: DriverRead | None = None
