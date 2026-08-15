from collections.abc import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.user import User
from app.utils.security import decode_access_token

# HTTPBearer(auto_error=False) so we can raise our own 401s consistently.
_bearer = HTTPBearer(auto_error=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async session dependency (commit on success, rollback on error)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_credentials(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def get_current_user(
    token: str = Depends(get_credentials),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Resolve the authenticated User from a verified Bearer JWT."""
    try:
        payload = decode_access_token(token)
        public_id = payload.get("sub")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        ) from exc

    if not public_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = await session.scalar(select(User).where(User.public_id == public_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_roles(*roles: UserRole):
    """Dependency factory enforcing role-based access control."""

    async def _role_guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {[r.value for r in roles]}",
            )
        return user

    return _role_guard


CurrentUser = Depends(get_current_user)
RequireSender = Depends(require_roles(UserRole.SENDER))
RequireDriver = Depends(require_roles(UserRole.DRIVER))
RequireAdmin = Depends(require_roles(UserRole.ADMIN))
