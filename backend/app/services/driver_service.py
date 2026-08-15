from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_request import DeliveryRequest
from app.models.driver import Driver
from app.models.enums import DeliveryRequestStatus, DriverStatus
from app.models.parcel import Parcel
from app.models.route import Route
from app.models.user import User
from app.schemas.driver import DriverUpdate
from app.utils.public_ids import new_public_id


class DriverService:
    """Driver profile management."""

    @staticmethod
    async def get_profile(session: AsyncSession, user: User) -> Driver | None:
        return await session.scalar(select(Driver).where(Driver.user_id == user.id))

    @staticmethod
    async def get_driver(session: AsyncSession, driver_id: int) -> Driver | None:
        return await session.get(Driver, driver_id)

    @staticmethod
    async def ensure_profile(session: AsyncSession, user: User) -> Driver:
        """Create a Driver profile for a driver user if one does not exist."""
        profile = await DriverService.get_profile(session, user)
        if profile is not None:
            return profile
        profile = Driver(
            public_id=new_public_id("driver"),
            user_id=user.id,
            capacity_kg=50.0,
            status=DriverStatus.OFFLINE,
        )
        session.add(profile)
        await session.flush()
        return profile

    @staticmethod
    async def get_by_public_id(session: AsyncSession, public_id: str) -> Driver | None:
        return await session.scalar(select(Driver).where(Driver.public_id == public_id))

    @staticmethod
    async def list_available(
        session: AsyncSession,
        city: str | None = None,
        limit: int = 50,
    ) -> list[Driver]:
        query = select(Driver).where(Driver.status == DriverStatus.AVAILABLE)
        if city:
            query = query.where(Driver.current_city.ilike(f"%{city}%"))
        query = query.order_by(Driver.rating.desc()).limit(limit)
        return list((await session.scalars(query)).all())

    @staticmethod
    async def update(session: AsyncSession, driver: Driver, data: DriverUpdate) -> Driver:
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(driver, field, value)
        await session.flush()
        return driver

    @staticmethod
    async def set_availability(
        session: AsyncSession, driver: Driver, status: DriverStatus, city: str | None
    ) -> Driver:
        driver.status = status
        if city is not None:
            driver.current_city = city
        await session.flush()
        return driver

    @staticmethod
    async def completed_deliveries(session: AsyncSession, driver_id: int) -> int:
        """Count delivered delivery requests for a driver."""
        return await session.scalar(
            select(func.count(DeliveryRequest.id)).where(
                DeliveryRequest.driver_id == driver_id,
                DeliveryRequest.status == DeliveryRequestStatus.DELIVERED,
            )
        ) or 0

    @staticmethod
    async def reliability_rates(session: AsyncSession, driver_id: int) -> tuple[float, float]:
        """Compute (on_time_rate, completion_rate) from real delivery records.

        on_time_rate      = on_time_deliveries / total_completed_deliveries
        completion_rate   = completed_deliveries / accepted_deliveries

        accepted = requests the driver accepted (matched / in_transit / delivered).
        A delivery is on time when it was delivered before the parcel deadline.
        """
        counts = dict(
            (await session.execute(
                select(DeliveryRequest.status, func.count(DeliveryRequest.id))
                .where(DeliveryRequest.driver_id == driver_id)
                .group_by(DeliveryRequest.status)
            )).all()
        )
        delivered = counts.get(DeliveryRequestStatus.DELIVERED, 0)
        accepted = (
            counts.get(DeliveryRequestStatus.MATCHED, 0)
            + counts.get(DeliveryRequestStatus.IN_TRANSIT, 0)
            + delivered
        )

        if delivered:
            now = datetime.now(timezone.utc)
            on_time = await session.scalar(
                select(func.count(DeliveryRequest.id))
                .join(DeliveryRequest.parcel)
                .where(
                    DeliveryRequest.driver_id == driver_id,
                    DeliveryRequest.status == DeliveryRequestStatus.DELIVERED,
                    func.coalesce(Parcel.deadline, now) >= DeliveryRequest.updated_at,
                )
            ) or 0
            on_time_rate = on_time / delivered
        else:
            on_time_rate = 1.0

        completion_rate = (delivered / accepted) if accepted else 1.0
        return round(on_time_rate, 3), round(completion_rate, 3)

    @staticmethod
    async def persist_reliability(session: AsyncSession, driver: Driver) -> None:
        """Recompute and store on_time_rate / completion_rate on the driver.

        Called after every completed delivery so the values used by the AI
        matcher (and shown on the driver profile) always reflect real history.
        """
        on_time_rate, completion_rate = await DriverService.reliability_rates(
            session, driver.id
        )
        driver.on_time_rate = on_time_rate
        driver.completion_rate = completion_rate
        await session.flush()

    @staticmethod
    async def compute_stats(session: AsyncSession, driver: Driver) -> dict:
        """Compute real delivery statistics for a driver from DB records."""
        counts = dict(
            (await session.execute(
                select(DeliveryRequest.status, func.count(DeliveryRequest.id))
                .where(DeliveryRequest.driver_id == driver.id)
                .group_by(DeliveryRequest.status)
            )).all()
        )
        total = sum(counts.values())
        delivered = counts.get(DeliveryRequestStatus.DELIVERED, 0)
        in_transit = counts.get(DeliveryRequestStatus.IN_TRANSIT, 0)
        rejected = counts.get(DeliveryRequestStatus.REJECTED, 0)
        pending = counts.get(DeliveryRequestStatus.PENDING_DRIVER_APPROVAL, 0)

        on_time_rate, completion_rate = await DriverService.reliability_rates(
            session, driver.id
        )

        active_routes = await session.scalar(
            select(func.count(Route.id)).where(
                Route.driver_id == driver.id, Route.is_active.is_(True)
            )
        ) or 0

        return {
            "total_deliveries": total,
            "completed_deliveries": delivered,
            "pending_deliveries": pending,
            "in_transit_deliveries": in_transit,
            "rejected_deliveries": rejected,
            "on_time_rate": on_time_rate,
            "completion_rate": completion_rate,
            "rating": driver.rating or 5.0,
            "reviews_count": driver.reviews_count or 0,
            "active_routes": active_routes,
        }
