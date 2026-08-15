from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ParcelStatus
from app.models.parcel import Parcel
from app.models.user import User
from app.schemas.parcel import ParcelCreate, ParcelUpdate
from app.utils.public_ids import new_public_id


class ParcelService:
    """Parcel (shipment request) management."""

    @staticmethod
    async def create(session: AsyncSession, sender: User, data: ParcelCreate) -> Parcel:
        parcel = Parcel(
            public_id=new_public_id("parcel"),
            sender_id=sender.id,
            pickup_location=data.pickup_location,
            drop_location=data.drop_location,
            item_description=data.item_description,
            item_value=data.item_value,
            weight=data.weight,
            dimensions=data.dimensions,
            size_tier=data.size_tier,
            budget=data.budget,
            deadline=data.deadline,
            special_instructions=data.special_instructions,
            sender_photo_url=data.sender_photo_url,
            status=ParcelStatus.PENDING,
        )
        session.add(parcel)
        await session.flush()
        return parcel

    @staticmethod
    async def get(session: AsyncSession, parcel_id: int) -> Parcel | None:
        return await session.get(Parcel, parcel_id)

    @staticmethod
    async def get_by_public_id(session: AsyncSession, public_id: str) -> Parcel | None:
        return await session.scalar(select(Parcel).where(Parcel.public_id == public_id))

    @staticmethod
    async def list_for_sender(session: AsyncSession, sender_id: int) -> list[Parcel]:
        query = (
            select(Parcel)
            .where(Parcel.sender_id == sender_id)
            .order_by(Parcel.created_at.desc())
        )
        return list((await session.scalars(query)).all())

    @staticmethod
    async def list_available(
        session: AsyncSession,
        statuses: list[ParcelStatus] | None = None,
        limit: int = 100,
    ) -> list[Parcel]:
        statuses = statuses or [ParcelStatus.PENDING, ParcelStatus.MATCHED]
        query = select(Parcel).where(Parcel.status.in_(statuses)).order_by(Parcel.created_at.asc())
        if limit:
            query = query.limit(limit)
        return list((await session.scalars(query)).all())

    @staticmethod
    async def update(session: AsyncSession, parcel: Parcel, data: ParcelUpdate) -> Parcel:
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(parcel, field, value)
        await session.flush()
        return parcel

    @staticmethod
    async def set_status(session: AsyncSession, parcel: Parcel, status: ParcelStatus) -> Parcel:
        parcel.status = status
        await session.flush()
        return parcel
