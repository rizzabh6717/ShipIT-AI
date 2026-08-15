from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.dependencies import get_current_user, get_session
from app.models.driver import Driver
from app.models.user import User
from app.services.driver_service import DriverService

router = APIRouter(prefix="/drivers", tags=["Drivers"])


def _to_read(driver: Driver, completed: int) -> schemas.DriverRead:
    item = schemas.DriverRead.model_validate(driver)
    item.completed_deliveries = completed
    return item


@router.get("/me", response_model=schemas.DriverRead)
async def get_my_profile(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return the authenticated user's driver profile."""
    driver = await DriverService.ensure_profile(session, user)
    completed = await DriverService.completed_deliveries(session, driver.id)
    return _to_read(driver, completed)


@router.patch("/me", response_model=schemas.DriverRead)
async def update_my_profile(
    data: schemas.DriverUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    driver = await DriverService.ensure_profile(session, user)
    updated = await DriverService.update(session, driver, data)
    completed = await DriverService.completed_deliveries(session, updated.id)
    return _to_read(updated, completed)


@router.patch("/me/availability", response_model=schemas.DriverRead)
async def set_availability(
    data: schemas.DriverAvailabilityUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    driver = await DriverService.ensure_profile(session, user)
    updated = await DriverService.set_availability(
        session, driver, data.status, data.current_city
    )
    completed = await DriverService.completed_deliveries(session, updated.id)
    return _to_read(updated, completed)


@router.get("/me/stats", response_model=schemas.DriverStats)
async def my_stats(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Real delivery statistics for the authenticated driver."""
    driver = await DriverService.ensure_profile(session, user)
    stats = await DriverService.compute_stats(session, driver)
    return schemas.DriverStats(**stats)


@router.get("", response_model=list[schemas.DriverRead])
async def list_drivers(
    city: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """List available drivers (optionally filtered by current city)."""
    drivers = await DriverService.list_available(session, city=city, limit=limit)
    return [
        _to_read(d, await DriverService.completed_deliveries(session, d.id))
        for d in drivers
    ]


@router.get("/{public_id}", response_model=schemas.DriverRead)
async def get_driver(
    public_id: str,
    session: AsyncSession = Depends(get_session),
):
    driver = await DriverService.get_by_public_id(session, public_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found"
        )
    completed = await DriverService.completed_deliveries(session, driver.id)
    return _to_read(driver, completed)
