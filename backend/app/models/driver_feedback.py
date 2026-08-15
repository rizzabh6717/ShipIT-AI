from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class DriverFeedback(TimestampMixin, Base):
    """A sender's rating + optional comment for a completed delivery.

    One feedback row per delivery request (enforced by a unique constraint on
    request_id). Aggregated into the driver's reliability score.
    """

    __tablename__ = "driver_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"), index=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    request_id: Mapped[int] = mapped_column(
        ForeignKey("delivery_requests.id", ondelete="CASCADE"), unique=True
    )
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    driver = relationship("Driver", back_populates="feedback", lazy="selectin")
    sender = relationship("User", lazy="selectin")
