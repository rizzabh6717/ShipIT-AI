from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ParcelSizeTier, ParcelStatus
from app.models.mixins import TimestampMixin


class Parcel(TimestampMixin, Base):
    """A shipment request created by a sender."""

    __tablename__ = "parcels"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    pickup_location: Mapped[str] = mapped_column(String(255))
    drop_location: Mapped[str] = mapped_column(String(255))
    item_description: Mapped[str] = mapped_column(String(500))
    item_value: Mapped[float] = mapped_column(Float, default=0.0)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    dimensions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    size_tier: Mapped[ParcelSizeTier] = mapped_column(
        Enum(
            ParcelSizeTier,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ParcelSizeTier.MEDIUM,
    )
    budget: Mapped[float] = mapped_column(Float, default=0.0)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    special_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[ParcelStatus] = mapped_column(
        Enum(
            ParcelStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ParcelStatus.PENDING,
        index=True,
    )

    # Relationships
    sender = relationship("User", back_populates="parcels", lazy="selectin")
    delivery = relationship(
        "Delivery",
        back_populates="parcel",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )
    matches = relationship("Match", back_populates="parcel", cascade="all, delete-orphan", lazy="selectin")
    requests = relationship("DeliveryRequest", back_populates="parcel", cascade="all, delete-orphan", lazy="selectin")
