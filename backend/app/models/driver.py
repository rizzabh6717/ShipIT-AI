from datetime import datetime

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import DriverStatus, VehicleType
from app.models.mixins import TimestampMixin


class Driver(TimestampMixin, Base):
    """Driver profile linked 1:1 to a User with role=driver."""

    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(
            VehicleType,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=VehicleType.CAR,
    )
    capacity_kg: Mapped[float] = mapped_column(Float, default=50.0)
    license_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vehicle_reg_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    on_time_rate: Mapped[float] = mapped_column(Float, default=1.0)
    completion_rate: Mapped[float] = mapped_column(Float, default=1.0)
    reviews_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[DriverStatus] = mapped_column(
        Enum(
            DriverStatus,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=DriverStatus.OFFLINE,
        index=True,
    )
    current_city: Mapped[str | None] = mapped_column(String(120), nullable=True)

    @property
    def name(self) -> str:
        """Display name delegated from the linked User account."""
        return self.user.name if self.user else ""

    @property
    def email(self) -> str:
        """Email delegated from the linked User account."""
        return self.user.email if self.user else ""

    @property
    def phone(self) -> str | None:
        """Phone delegated from the linked User account."""
        return self.user.phone if self.user else None

    # Relationships
    user = relationship("User", back_populates="driver_profile", lazy="selectin")
    routes = relationship("Route", back_populates="driver", cascade="all, delete-orphan", lazy="selectin")
    deliveries = relationship("Delivery", back_populates="driver", lazy="selectin")
    matches = relationship("Match", back_populates="driver", lazy="selectin")
    requests = relationship("DeliveryRequest", back_populates="driver", lazy="selectin")
    feedback = relationship("DriverFeedback", back_populates="driver", lazy="selectin")
