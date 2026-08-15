from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.dependencies import get_current_user, get_session
from app.models.enums import DeliveryRequestStatus, ParcelStatus, UserRole
from app.models.user import User
from app.services.delivery_request_service import DeliveryRequestService
from app.services.delivery_service import DeliveryService
from app.services.driver_service import DriverService
from app.services.feedback_service import FeedbackService
from app.services.parcel_service import ParcelService

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


@router.post("/request", response_model=schemas.DeliveryRequestResponse)
async def create_request(
    data: schemas.DeliveryRequestCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Sender requests a driver for a parcel, parking it pending driver approval."""
    if user.role != UserRole.SENDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Senders only"
        )
    parcel = await ParcelService.get_by_public_id(session, data.parcel_id)
    if parcel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found"
        )
    if parcel.sender_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your parcel"
        )
    if parcel.status != ParcelStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Parcel cannot be requested in status '{parcel.status.value}'",
        )
    existing = await DeliveryRequestService.get_active_for_parcel(session, parcel.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This parcel already has an active delivery request",
        )
    driver = await DriverService.get_by_public_id(session, data.driver_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found"
        )
    route_id = None
    if data.route_id:
        try:
            route_id = int(data.route_id)
        except (TypeError, ValueError):
            route_id = None
    request = await DeliveryRequestService.create(session, parcel, driver, route_id)
    return {"success": True, "message": "Request sent", "request": request}


@router.get("/requests/sender", response_model=list[schemas.DeliveryRequestRead])
async def sender_requests(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return delivery requests for the sender's own parcels."""
    if user.role != UserRole.SENDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Senders only"
        )
    return await DeliveryRequestService.list_for_sender(session, user.id)


@router.get("/requests/me", response_model=list[schemas.DeliveryRequestRead])
async def my_requests(
    scope: str = Query("pending", pattern="^(pending|active)$"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return the authenticated driver's delivery requests."""
    if user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Drivers only"
        )
    driver = await DriverService.ensure_profile(session, user)
    return await DeliveryRequestService.list_for_driver(session, driver.id, scope)


async def _get_owned_request(public_id: str, user: User, session: AsyncSession):
    request = await DeliveryRequestService.get_by_public_id(session, public_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    if request.driver.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your request"
        )
    return request


@router.post("/requests/{public_id}/respond", response_model=schemas.DeliveryRequestResponse)
async def respond_request(
    public_id: str,
    data: schemas.DeliveryRequestRespond,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    request = await _get_owned_request(public_id, user, session)
    if request.status != DeliveryRequestStatus.PENDING_DRIVER_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Request already responded with status '{request.status.value}'",
        )
    request = await DeliveryRequestService.respond(session, request, data.accept)
    action = "accepted" if data.accept else "rejected"
    return {"success": True, "message": f"Request {action}", "request": request}


@router.post("/requests/{public_id}/pickup", response_model=schemas.DeliveryRequestResponse)
async def request_confirm_pickup(
    public_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    request = await _get_owned_request(public_id, user, session)
    if request.status != DeliveryRequestStatus.MATCHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Request cannot be picked up in status '{request.status.value}'",
        )
    request = await DeliveryRequestService.confirm_pickup(session, request)
    return {"success": True, "message": "Picked up", "request": request}


@router.post("/requests/{public_id}/delivered", response_model=schemas.DeliveryRequestResponse)
async def request_mark_delivered(
    public_id: str,
    data: schemas.DeliveryProofRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    request = await _get_owned_request(public_id, user, session)
    if request.status not in (DeliveryRequestStatus.MATCHED, DeliveryRequestStatus.IN_TRANSIT):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Request cannot be delivered in status '{request.status.value}'",
        )
    request = await DeliveryRequestService.mark_delivered(
        session, request, data.proof_image_url
    )
    return {"success": True, "message": "Delivered", "request": request}


@router.post("/requests/{public_id}/feedback", response_model=schemas.FeedbackResponse)
async def request_feedback(
    public_id: str,
    data: schemas.FeedbackCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Sender rates a completed delivery request (1-5 stars + optional comment)."""
    request = await DeliveryRequestService.get_by_public_id(session, public_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    if request.parcel.sender_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your delivery"
        )
    if request.status != DeliveryRequestStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only completed deliveries can be reviewed",
        )
    try:
        feedback = await FeedbackService.submit(
            session, request, user.id, data.rating, data.comment
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return {
        "success": True,
        "message": "Feedback recorded",
        "feedback": feedback,
    }


@router.post("/accept", response_model=schemas.DeliveryAcceptResponse)
async def accept_parcel(
    parcel_id: str = Query(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Driver accepts a parcel, creating the delivery record."""
    if user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Drivers only"
        )
    driver = await DriverService.ensure_profile(session, user)
    parcel = await ParcelService.get_by_public_id(session, parcel_id)
    if parcel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found"
        )
    if parcel.status not in (ParcelStatus.PENDING, ParcelStatus.MATCHED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Parcel cannot be accepted in status '{parcel.status.value}'",
        )
    existing = await DeliveryService.get_active_for_parcel(session, parcel.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Parcel already accepted"
        )
    delivery = await DeliveryService.accept(session, parcel, driver)
    return {"success": True, "message": "Delivery accepted", "delivery": delivery}


async def _get_owned_delivery(public_id: str, user: User, session: AsyncSession):
    delivery = await DeliveryService.get_by_public_id(session, public_id)
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found"
        )
    if delivery.driver.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your delivery"
        )
    return delivery


@router.post("/{public_id}/pickup", response_model=schemas.DeliveryStatusResponse)
async def confirm_pickup(
    public_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    delivery = await _get_owned_delivery(public_id, user, session)
    delivery = await DeliveryService.confirm_pickup(session, delivery)
    return {
        "success": True,
        "message": "Picked up",
        "status": delivery.parcel.status,
        "delivery": delivery,
    }


@router.post("/{public_id}/delivered", response_model=schemas.DeliveryStatusResponse)
async def mark_delivered(
    public_id: str,
    data: schemas.DeliveryProofRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    delivery = await _get_owned_delivery(public_id, user, session)
    delivery = await DeliveryService.mark_delivered(session, delivery, data.proof_image_url)
    return {
        "success": True,
        "message": "Delivered",
        "status": delivery.parcel.status,
        "delivery": delivery,
    }


@router.get("/driver/me", response_model=list[schemas.DeliveryRead])
async def my_deliveries(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return the authenticated driver's deliveries."""
    if user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Drivers only"
        )
    driver = await DriverService.ensure_profile(session, user)
    return await DeliveryService.list_for_driver(session, driver.id)


@router.get("/{public_id}", response_model=schemas.DeliveryRead)
async def get_delivery(
    public_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _get_owned_delivery(public_id, user, session)
