from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.dependencies import get_current_user, get_session, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=schemas.UserRead)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=schemas.UserRead)
async def update_me(
    data: schemas.UserUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(user, field, value)
    await session.flush()
    return user


@router.get("/{public_id}", response_model=schemas.UserRead)
async def get_user(
    public_id: str,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = await AuthService.get_by_public_id(session, public_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
