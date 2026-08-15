from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.dependencies import get_current_user, get_session
from app.models.enums import ParcelStatus, UserRole
from app.models.user import User
from app.services.parcel_service import ParcelService

router = APIRouter(prefix="/parcels", tags=["Parcels"])


@router.post("", response_model=schemas.ParcelRead, status_code=status.HTTP_201_CREATED)
async def create_parcel(
    data: schemas.ParcelCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a parcel request. Returns a public id like 'P123'."""
    return await ParcelService.create(session, user, data)


@router.get("", response_model=list[schemas.ParcelRead])
async def list_my_parcels(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return the current user's own parcels."""
    return await ParcelService.list_for_sender(session, user.id)


@router.get("/available", response_model=list[schemas.ParcelRead])
async def available_parcels(
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """Parcels that still need a driver (pending/matched)."""
    return await ParcelService.list_available(session, limit=limit)


@router.get("/{public_id}", response_model=schemas.ParcelWithMatches)
async def get_parcel(
    public_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Parcel detail including its persisted AI matches."""
    parcel = await ParcelService.get_by_public_id(session, public_id)
    if parcel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found"
        )

    matches = []
    best_driver = None
    for m in sorted(parcel.matches, key=lambda x: x.match_score, reverse=True):
        matches.append(
            {
                "driver_id": m.driver.public_id if m.driver else None,
                "score": m.match_score,
                "eta": m.eta,
                "explanation": (m.explanation or "").split("\n"),
            }
        )
        if best_driver is None and m.driver is not None:
            best_driver = m.driver

    result = schemas.ParcelRead.model_validate(parcel)
    result_dict = result.model_dump()
    result_dict["matches"] = matches
    if best_driver is not None:
        from app.schemas.driver import DriverRead

        result_dict["best_driver"] = DriverRead.model_validate(best_driver)
    return schemas.ParcelWithMatches(**result_dict)


@router.patch("/{public_id}", response_model=schemas.ParcelRead)
async def update_parcel(
    public_id: str,
    data: schemas.ParcelUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    parcel = await ParcelService.get_by_public_id(session, public_id)
    if parcel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found"
        )
    if parcel.sender_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your parcel"
        )
    return await ParcelService.update(session, parcel, data)


@router.post("/{public_id}/cancel", response_model=schemas.ParcelRead)
async def cancel_parcel(
    public_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    parcel = await ParcelService.get_by_public_id(session, public_id)
    if parcel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found"
        )
    if parcel.sender_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your parcel"
        )
    return await ParcelService.set_status(session, parcel, ParcelStatus.CANCELLED)
