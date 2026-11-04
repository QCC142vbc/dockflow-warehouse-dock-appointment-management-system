from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_service_access_token() -> str:
    secret = settings.SERVICE_AUTH_SECRET
    if not secret:
        raise RuntimeError(
            "SERVICE_AUTH_SECRET must be configured before dispatching integration events."
        )

    now = datetime.now(timezone.utc)
    payload = {
        "sub": settings.SERVICE_AUTH_ISSUER,
        "scope": "integration:write",
        "iat": now,
        "exp": now + timedelta(seconds=settings.SERVICE_AUTH_TOKEN_EXPIRE_SECONDS),
        "iss": settings.SERVICE_AUTH_ISSUER,
        "aud": settings.SERVICE_AUTH_AUDIENCE,
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )
    except JWTError:
        return None