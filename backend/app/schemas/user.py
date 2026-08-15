from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class SenderRegister(UserCreate):
    role: UserRole = UserRole.SENDER


class DriverRegister(UserCreate):
    role: UserRole = UserRole.DRIVER
    vehicle_type: str = Field(default="car")
    capacity_kg: float = Field(gt=0, le=20000)
    phone: str = Field(min_length=7, max_length=20)
    license_number: str = Field(min_length=4, max_length=64)
    vehicle_reg_number: str = Field(min_length=4, max_length=32)
    current_city: str | None = Field(default=None, max_length=120)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
