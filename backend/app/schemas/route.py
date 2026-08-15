from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import VehicleType


class RouteBase(BaseModel):
    origin: str = Field(min_length=2, max_length=255)
    destination: str = Field(min_length=2, max_length=255)
    waypoints: list[dict] | None = None
    planned_at: datetime | None = None


class RouteCreate(RouteBase):
    pass


class RouteRead(RouteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    driver_id: int
    route_text: str | None
    is_active: bool
    has_embedding: bool = False
    created_at: datetime
    updated_at: datetime


class RouteList(BaseModel):
    routes: list[RouteRead]
    total: int


class RouteEmbedResponse(BaseModel):
    route_id: int
    status: str = "embedded"
    dimensions: int
    route_text: str
