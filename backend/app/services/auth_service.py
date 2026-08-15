from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DriverStatus, UserRole, VehicleType
from app.models.user import User
from app.schemas.user import SenderRegister
from app.utils.public_ids import new_public_id
from app.utils.security import create_access_token, hash_password, verify_password


class AuthService:
    """Registration, login, and token issuance."""

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        return await session.scalar(select(User).where(User.email == email.lower()))

    @staticmethod
    async def get_by_public_id(session: AsyncSession, public_id: str) -> User | None:
        return await session.scalar(select(User).where(User.public_id == public_id))

    @staticmethod
    async def register_sender(session: AsyncSession, data: SenderRegister) -> User:
        existing = await AuthService.get_by_email(session, data.email)
        if existing:
            raise ValueError("Email already registered")
        user = User(
            public_id=new_public_id("user"),
            name=data.name,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            role=UserRole.SENDER,
            phone=data.phone,
        )
        session.add(user)
        try:
            await session.flush()
        except IntegrityError:
            raise ValueError("Email already registered") from None
        return user

    @staticmethod
    async def register_driver(
        session: AsyncSession,
        name: str,
        email: str,
        password: str,
        phone: str | None,
        vehicle_type: VehicleType,
        capacity_kg: float,
        license_number: str | None,
        vehicle_reg_number: str | None,
        current_city: str | None,
    ) -> User:
        """Create a User (role=driver) plus its Driver profile in one transaction."""
        from app.models.driver import Driver

        existing = await AuthService.get_by_email(session, email)
        if existing:
            raise ValueError("Email already registered")

        user = User(
            public_id=new_public_id("user"),
            name=name,
            email=email.lower(),
            password_hash=hash_password(password),
            role=UserRole.DRIVER,
            phone=phone,
        )
        session.add(user)
        await session.flush()

        driver = Driver(
            public_id=new_public_id("driver"),
            user_id=user.id,
            vehicle_type=vehicle_type,
            capacity_kg=capacity_kg,
            license_number=license_number,
            vehicle_reg_number=vehicle_reg_number,
            current_city=current_city,
            status=DriverStatus.OFFLINE,
            rating=5.0,
            on_time_rate=1.0,
            completion_rate=1.0,
        )
        session.add(driver)
        try:
            await session.flush()
        except IntegrityError:
            raise ValueError("Email already registered") from None
        return user

    @staticmethod
    async def authenticate(session: AsyncSession, email: str, password: str) -> User | None:
        user = await AuthService.get_by_email(session, email)
        if user is None or not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def issue_token(user: User) -> str:
        return create_access_token(subject=user.public_id, role=user.role.value)
