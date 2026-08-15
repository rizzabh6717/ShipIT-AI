from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DeliveryRequestStatus
from app.schemas.driver import DriverRead
from app.schemas.parcel import ParcelRead


class DeliveryRequestCreate(BaseModel):
    parcel_id: str = Field(description="Public parcel identifier, e.g. 'P123'")
    driver_id: str = Field(description="Public driver identifier, e.g. 'D17'")
    route_id: str | None = Field(default=None, description="Public route id, if known")


class DeliveryRequestRespond(BaseModel):
    accept: bool


class DeliveryRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    parcel_id: int
    driver_id: int
    route_id: int | None
    status: DeliveryRequestStatus
    responded_at: datetime | None
    proof_image_url: str | None = None
    created_at: datetime
    updated_at: datetime

    parcel: ParcelRead | None = None
    driver: DriverRead | None = None


class DeliveryRequestResponse(BaseModel):
    success: bool = True
    message: str
    request: DeliveryRequestRead


class DeliveryProofRequest(BaseModel):
    proof_image_url: str = Field(min_length=1)


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    driver_id: int
    sender_id: int
    request_id: int
    rating: int
    comment: str | None
    created_at: datetime


class FeedbackResponse(BaseModel):
    success: bool = True
    message: str
    feedback: FeedbackRead