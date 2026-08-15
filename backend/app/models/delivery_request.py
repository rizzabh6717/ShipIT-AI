from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import DeliveryRequestStatus
from app.models.mixins import TimestampMixin


class DeliveryRequest(TimestampMixin, Base):
    """A sender-initiated delivery request awaiting driver approval.

    Mirrors the mock's two-phase flow: the sender requests a driver, the driver
    accepts/rejects, and the request tracks pickup/delivery afterwards.
    """

    __tablename__ = "delivery_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    parcel_id: Mapped[int] = mapped_column(
        ForeignKey("parcels.id", ondelete="CASCADE"), index=True
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"), index=True
    )
    route_id: Mapped[int | None] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    status: Mapped[DeliveryRequestStatus] = mapped_column(
        Enum(
            DeliveryRequestStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=DeliveryRequestStatus.PENDING_DRIVER_APPROVAL,
        index=True,
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    proof_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    parcel = relationship("Parcel", back_populates="requests", lazy="selectin")
    driver = relationship("Driver", back_populates="requests", lazy="selectin")
    route = relationship("Route", lazy="selectin")