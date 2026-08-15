from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ParcelStatus
from app.schemas.driver import DriverRead
from app.schemas.parcel import ParcelRead


class DeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    parcel_id: int
    driver_id: int
    accepted_at: datetime | None
    picked_up_at: datetime | None
    delivered_at: datetime | None
    proof_image_url: str | None
    created_at: datetime
    updated_at: datetime

    parcel: ParcelRead | None = None
    driver: DriverRead | None = None


class DeliveryAcceptResponse(BaseModel):
    success: bool = True
    message: str
    delivery: DeliveryRead


class DeliveryStatusResponse(BaseModel):
    success: bool = True
    message: str
    status: ParcelStatus
    delivery: DeliveryRead
