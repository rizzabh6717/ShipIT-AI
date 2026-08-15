from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_request import DeliveryRequest
from app.models.driver import Driver
from app.models.enums import DeliveryRequestStatus, DriverStatus, ParcelStatus
from app.models.parcel import Parcel
from app.services.driver_service import DriverService
from app.utils.public_ids import new_public_id


ACTIVE_REQUEST_STATUSES = (
    DeliveryRequestStatus.PENDING_DRIVER_APPROVAL,
    DeliveryRequestStatus.MATCHED,
)


class DeliveryRequestService:
    """Sender-initiated delivery requests awaiting driver approval."""

    @staticmethod
    async def get_by_public_id(session: AsyncSession, public_id: str) -> DeliveryRequest | None:
        return await session.scalar(
            select(DeliveryRequest).where(DeliveryRequest.public_id == public_id)
        )

    @staticmethod
    async def get_active_for_parcel(session: AsyncSession, parcel_id: int) -> DeliveryRequest | None:
        return await session.scalar(
            select(DeliveryRequest).where(
                DeliveryRequest.parcel_id == parcel_id,
                DeliveryRequest.status.in_(ACTIVE_REQUEST_STATUSES),
            )
        )

    @staticmethod
    async def create(
        session: AsyncSession,
        parcel: Parcel,
        driver: Driver,
        route_id: int | None = None,
    ) -> DeliveryRequest:
        """Create a pending request and park the parcel awaiting driver approval."""
        request = DeliveryRequest(
            public_id=new_public_id("request"),
            parcel_id=parcel.id,
            driver_id=driver.id,
            route_id=route_id,
            status=DeliveryRequestStatus.PENDING_DRIVER_APPROVAL,
        )
        session.add(request)
        parcel.status = ParcelStatus.PENDING_DRIVER_APPROVAL
        await session.flush()
        await session.refresh(request, ["parcel", "driver"])
        return request

    @staticmethod
    async def list_for_driver(
        session: AsyncSession,
        driver_id: int,
        scope: str = "pending",
    ) -> list[DeliveryRequest]:
        statuses = (
            [DeliveryRequestStatus.PENDING_DRIVER_APPROVAL]
            if scope == "pending"
            else [
                DeliveryRequestStatus.MATCHED,
                DeliveryRequestStatus.IN_TRANSIT,
                DeliveryRequestStatus.DELIVERED,
            ]
        )
        query = (
            select(DeliveryRequest)
            .where(DeliveryRequest.driver_id == driver_id)
            .where(DeliveryRequest.status.in_(statuses))
            .order_by(DeliveryRequest.created_at.desc())
        )
        return list((await session.scalars(query)).all())

    @staticmethod
    async def list_for_sender(
        session: AsyncSession,
        sender_id: int,
    ) -> list[DeliveryRequest]:
        query = (
            select(DeliveryRequest)
            .join(DeliveryRequest.parcel)
            .where(Parcel.sender_id == sender_id)
            .order_by(DeliveryRequest.created_at.desc())
        )
        return list((await session.scalars(query)).all())

    @staticmethod
    async def respond(session: AsyncSession, request: DeliveryRequest, accept: bool) -> DeliveryRequest:
        request.responded_at = datetime.now(timezone.utc)
        if accept:
            request.status = DeliveryRequestStatus.MATCHED
            request.parcel.status = ParcelStatus.MATCHED
        else:
            request.status = DeliveryRequestStatus.REJECTED
            request.parcel.status = ParcelStatus.PENDING
        await session.flush()
        await session.refresh(request, ["parcel", "driver"])
        return request

    @staticmethod
    async def confirm_pickup(session: AsyncSession, request: DeliveryRequest) -> DeliveryRequest:
        request.status = DeliveryRequestStatus.IN_TRANSIT
        request.parcel.status = ParcelStatus.IN_TRANSIT
        await session.flush()
        await session.refresh(request, ["parcel", "driver"])
        return request

    @staticmethod
    async def mark_delivered(
        session: AsyncSession,
        request: DeliveryRequest,
        proof_image_url: str,
    ) -> DeliveryRequest:
        """Mark a request delivered. A proof-of-delivery photo is mandatory."""
        if not proof_image_url or not proof_image_url.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A proof-of-delivery photo is required to mark this delivery complete",
            )
        request.status = DeliveryRequestStatus.DELIVERED
        request.parcel.status = ParcelStatus.DELIVERED
        request.driver.status = DriverStatus.AVAILABLE
        request.proof_image_url = proof_image_url
        await session.flush()
        # Update the driver's on-time / completion rates from real records so
        # the reliability used in future AI matching reflects this delivery.
        await DriverService.persist_reliability(session, request.driver)
        await session.refresh(request, ["parcel", "driver"])
        return request