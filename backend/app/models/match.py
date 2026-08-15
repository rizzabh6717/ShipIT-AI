from datetime import datetime

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class Match(TimestampMixin, Base):
    """A persisted, explainable AI match between a parcel and a driver."""

    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("parcel_id", "driver_id", name="uq_match_parcel_driver"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    parcel_id: Mapped[int] = mapped_column(
        ForeignKey("parcels.id", ondelete="CASCADE"), index=True
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"), index=True
    )
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    eta: Mapped[str | None] = mapped_column(String(64), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    parcel = relationship("Parcel", back_populates="matches", lazy="selectin")
    driver = relationship("Driver", back_populates="matches", lazy="selectin")
