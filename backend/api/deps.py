from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from db.postgres import get_db
from db.postgres_models import User
from core.services.auth import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[dict]:
    state_user = getattr(request.state, "user", None)
    if state_user:
        return state_user
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None
    user_id = payload.get("user_id")
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "plan": user.plan,
    }


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    state_user = getattr(request.state, "user", None)
    if state_user:
        return state_user
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "plan": user.plan,
    }


async def require_plan(*allowed_plans: str):
    async def _check(user: dict = Depends(get_current_user)) -> dict:
        if user["plan"] not in allowed_plans and user["plan"] != "ENTERPRISE":
            raise HTTPException(
                status_code=403,
                detail=f"Plan '{user['plan']}' not allowed. Required: {allowed_plans}",
            )
        return user
    return _check
