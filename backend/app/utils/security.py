import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

# ---------------------------------------------------------------------------
# Password hashing (bcrypt directly — avoids passlib/bcrypt version issues)
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------


def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    """Create a signed JWT access token.

    Claims:
      - sub: user public_id
      - role: user role
      - iat / exp: issued-at / expiry timestamps
    """
    now = datetime.now(timezone.utc)
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def generate_secret_key() -> str:
    """Utility to generate a strong secret for .env (for documentation)."""
    return secrets.token_urlsafe(64)
