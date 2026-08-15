from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class UserExistsResponse(BaseModel):
    success: bool = True
    userExists: bool
    role: str | None = None
    user: UserRead | None = None


class RegisterResponse(BaseModel):
    success: bool = True
    message: str
    user: UserRead
    access_token: str | None = None
    token_type: str = "bearer"
