import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings

logger = logging.getLogger(__name__)

JWT_SECRET = getattr(settings, "JWT_SECRET", "") or "dev-only-insecure-key"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _get_jwt_secret() -> str:
    return JWT_SECRET


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, _get_jwt_secret(), algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, _get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def authenticate_user(
    session: AsyncSession, email: str, password: str
) -> Optional[dict]:
    from db.postgres_models import User

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "plan": user.plan,
    }


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    name: str,
    plan: str = "FREE",
) -> dict:
    from db.postgres_models import User

    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return {"error": "Email already registered"}

    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
        plan=plan,
    )
    session.add(user)
    await session.flush()

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "plan": user.plan,
    }
