from datetime import datetime

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import UserRole
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    """Registered account. Every driver is also a User with role=driver."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        default=UserRole.SENDER,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    driver_profile = relationship("Driver", back_populates="user", uselist=False, lazy="selectin")
    parcels = relationship("Parcel", back_populates="sender", lazy="selectin")
