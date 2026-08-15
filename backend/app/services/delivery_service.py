from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import Delivery
from app.models.enums import DriverStatus, ParcelStatus
from app.models.driver import Driver
from app.models.parcel import Parcel
from app.utils.public_ids import new_public_id


class DeliveryService:
    """Delivery workflow: accept, pickup, deliver, proof upload."""

    @staticmethod
    async def get(session: AsyncSession, delivery_id: int) -> Delivery | None:
        return await session.get(Delivery, delivery_id)

    @staticmethod
    async def get_by_public_id(session: AsyncSession, public_id: str) -> Delivery | None:
        return await session.scalar(select(Delivery).where(Delivery.public_id == public_id))

    @staticmethod
    async def get_active_for_parcel(session: AsyncSession, parcel_id: int) -> Delivery | None:
        return await session.scalar(
            select(Delivery).where(Delivery.parcel_id == parcel_id)
        )

    @staticmethod
    async def accept(session: AsyncSession, parcel: Parcel, driver: Driver) -> Delivery:
        """Driver accepts a parcel, creating the Delivery record."""
        delivery = Delivery(
            public_id=new_public_id("delivery"),
            parcel_id=parcel.id,
            driver_id=driver.id,
            accepted_at=datetime.now(timezone.utc),
        )
        session.add(delivery)
        parcel.status = ParcelStatus.ACCEPTED
        driver.status = DriverStatus.BUSY
        await session.flush()
        # Refresh to load relationships for response serialization
        await session.refresh(delivery, ["parcel", "driver"])
        return delivery

    @staticmethod
    async def confirm_pickup(session: AsyncSession, delivery: Delivery) -> Delivery:
        delivery.picked_up_at = datetime.now(timezone.utc)
        delivery.parcel.status = ParcelStatus.PICKED_UP
        await session.flush()
        return delivery

    @staticmethod
    async def mark_delivered(
        session: AsyncSession, delivery: Delivery, proof_url: str
    ) -> Delivery:
        if not proof_url or not proof_url.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A proof-of-delivery photo is required to mark this delivery complete",
            )
        delivery.delivered_at = datetime.now(timezone.utc)
        delivery.proof_image_url = proof_url
        delivery.parcel.status = ParcelStatus.DELIVERED
        delivery.driver.status = DriverStatus.AVAILABLE
        await session.flush()
        return delivery

    @staticmethod
    async def set_proof(session: AsyncSession, delivery: Delivery, url: str) -> Delivery:
        delivery.proof_image_url = url
        await session.flush()
        return delivery

    @staticmethod
    async def list_for_driver(session: AsyncSession, driver_id: int) -> list[Delivery]:
        query = (
            select(Delivery)
            .where(Delivery.driver_id == driver_id)
            .order_by(Delivery.created_at.desc())
        )
        return list((await session.scalars(query)).all())
