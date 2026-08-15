from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.config import settings
from app.database import Base
from app.models.mixins import TimestampMixin


class Route(TimestampMixin, Base):
    """A driver's planned route. `route_text` is embedded into a pgvector column
    to enable semantic similarity search against parcels."""

    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"), index=True
    )
    origin: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(255))
    waypoints: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    route_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    route_embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dimensions), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    planned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    driver = relationship("Driver", back_populates="routes", lazy="selectin")
