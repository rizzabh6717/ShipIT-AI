from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.config import settings
from app.dependencies import get_current_user, get_session
from app.models.enums import UserRole, VehicleType
from app.models.user import User
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _token_response(user: User) -> dict:
    token = AuthService.issue_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": user,
    }


@router.post(
    "/register/sender",
    response_model=schemas.RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_sender(
    data: schemas.SenderRegister,
    session: AsyncSession = Depends(get_session),
):
    """Register a sender account (name, email, password)."""
    try:
        user = await AuthService.register_sender(session, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    payload = _token_response(user)
    return {"success": True, "message": "Sender registered", **payload}


@router.post(
    "/register/driver",
    response_model=schemas.RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_driver(
    data: schemas.DriverRegister,
    session: AsyncSession = Depends(get_session),
):
    """Register a driver account plus its Driver profile in one request."""
    try:
        vehicle_type = VehicleType(data.vehicle_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid vehicle_type; choose from "
            f"{[v.value for v in VehicleType]}",
        ) from None
    try:
        user = await AuthService.register_driver(
            session,
            name=data.name,
            email=data.email,
            password=data.password,
            phone=data.phone,
            vehicle_type=vehicle_type,
            capacity_kg=data.capacity_kg,
            license_number=data.license_number,
            vehicle_reg_number=data.vehicle_reg_number,
            current_city=data.current_city,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    payload = _token_response(user)
    return {"success": True, "message": "Driver registered", **payload}


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    data: schemas.LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """Login with email + password; returns a JWT bearer token."""
    user = await AuthService.authenticate(session, data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return _token_response(user)


@router.get("/me", response_model=schemas.UserRead)
async def me(user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return user


@router.get("/user/{public_id}", response_model=schemas.UserExistsResponse)
async def user_exists(
    public_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Frontend compatibility check: does this public id (or email) exist?

    Used by the auth flow to decide between "register" and "log in".
    """
    user = await AuthService.get_by_public_id(session, public_id)
    if user is None:
        user = await AuthService.get_by_email(session, public_id)
    if user is None:
        return {"success": True, "userExists": False}
    return {
        "success": True,
        "userExists": True,
        "role": user.role.value,
        "user": user,
    }
