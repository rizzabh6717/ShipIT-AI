from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class Delivery(TimestampMixin, Base):
    """Tracks the execution of a parcel by a specific driver."""

    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    parcel_id: Mapped[int] = mapped_column(
        ForeignKey("parcels.id", ondelete="CASCADE"), unique=True, index=True
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"), index=True
    )

    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    proof_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    parcel = relationship("Parcel", back_populates="delivery", lazy="joined")
    driver = relationship("Driver", back_populates="deliveries", lazy="joined")
