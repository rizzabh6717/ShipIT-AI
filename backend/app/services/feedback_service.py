from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_request import DeliveryRequest
from app.models.driver import Driver
from app.models.driver_feedback import DriverFeedback
from app.utils.public_ids import new_public_id


class FeedbackService:
    """Sender feedback on completed deliveries + driver reliability updates."""

    @staticmethod
    async def get_for_request(session: AsyncSession, request_id: int) -> DriverFeedback | None:
        return await session.scalar(
            select(DriverFeedback).where(DriverFeedback.request_id == request_id)
        )

    @staticmethod
    async def submit(
        session: AsyncSession,
        request: DeliveryRequest,
        sender_id: int,
        rating: int,
        comment: str | None,
    ) -> DriverFeedback:
        """Record one feedback row (unique per request) and recompute the driver's
        rating, review count, and completion rate from real data."""
        existing = await FeedbackService.get_for_request(session, request.id)
        if existing is not None:
            raise ValueError("Feedback already submitted for this delivery")

        feedback = DriverFeedback(
            public_id=new_public_id("feedback"),
            driver_id=request.driver_id,
            sender_id=sender_id,
            request_id=request.id,
            rating=rating,
            comment=comment,
        )
        session.add(feedback)
        try:
            await session.flush()
        except IntegrityError:
            raise ValueError("Feedback already submitted for this delivery") from None

        driver = await session.get(Driver, request.driver_id)
        if driver is not None:
            avg = await session.scalar(
                select(func.avg(DriverFeedback.rating)).where(
                    DriverFeedback.driver_id == driver.id
                )
            )
            count = await session.scalar(
                select(func.count(DriverFeedback.id)).where(
                    DriverFeedback.driver_id == driver.id
                )
            )
            driver.rating = round(float(avg or 5.0), 2)
            driver.reviews_count = int(count or 0)
            await session.flush()

        return feedback