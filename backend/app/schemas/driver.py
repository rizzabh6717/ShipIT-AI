from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DriverStatus, VehicleType


class DriverBase(BaseModel):
    vehicle_type: VehicleType = VehicleType.CAR
    capacity_kg: float = Field(gt=0, le=20000)
    license_number: str | None = Field(default=None, max_length=64)
    vehicle_reg_number: str | None = Field(default=None, max_length=32)
    current_city: str | None = Field(default=None, max_length=120)


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    vehicle_type: VehicleType | None = None
    capacity_kg: float | None = Field(default=None, gt=0, le=20000)
    license_number: str | None = None
    vehicle_reg_number: str | None = None
    current_city: str | None = None
    status: DriverStatus | None = None


class DriverRead(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    user_id: int
    rating: float
    on_time_rate: float
    completion_rate: float
    reviews_count: int
    status: DriverStatus
    created_at: datetime
    updated_at: datetime
    name: str
    email: str
    phone: str | None = None
    completed_deliveries: int = 0


class DriverStats(BaseModel):
    total_deliveries: int
    completed_deliveries: int
    pending_deliveries: int
    in_transit_deliveries: int
    rejected_deliveries: int
    on_time_rate: float
    completion_rate: float
    rating: float
    reviews_count: int
    active_routes: int


class DriverAvailabilityUpdate(BaseModel):
    status: DriverStatus
    current_city: str | None = Field(default=None, max_length=120)
