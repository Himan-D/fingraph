import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db
from core.services.auth import (
    authenticate_user,
    create_user,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from api.deps import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter()


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/signup")
async def signup(req: SignupRequest, db: AsyncSession = Depends(get_db)):
    if len(req.password) < 6:
        raise HTTPException(
            status_code=400, detail="Password must be at least 6 characters"
        )

    result = await create_user(db, req.email, req.password, req.name)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    access = create_access_token({"sub": result["email"], "user_id": result["id"]})
    refresh = create_refresh_token({"sub": result["email"], "user_id": result["id"]})

    return {
        "success": True,
        "data": {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "user": {
                "id": result["id"],
                "email": result["email"],
                "name": result["name"],
                "plan": result["plan"],
            },
        },
    }


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access = create_access_token({"sub": user["email"], "user_id": user["id"]})
    refresh = create_refresh_token({"sub": user["email"], "user_id": user["id"]})

    return {
        "success": True,
        "data": {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "user": user,
        },
    }


@router.post("/refresh")
async def refresh_token(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access = create_access_token(
        {"sub": payload["sub"], "user_id": payload["user_id"]}
    )
    refresh = create_refresh_token(
        {"sub": payload["sub"], "user_id": payload["user_id"]}
    )

    return {
        "success": True,
        "data": {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        },
    }


@router.get("/me")
async def get_me(user: Optional[dict] = Depends(get_current_user_optional)):
    if not user:
        return {
            "success": True,
            "data": {
                "authenticated": False,
                "plan": "FREE",
                "daily_limit": 10,
            },
        }

    limits = {"FREE": 10, "DEVELOPER": 100, "PRO": 1000, "ENTERPRISE": -1}
    return {
        "success": True,
        "data": {
            "authenticated": True,
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "plan": user["plan"],
            "daily_limit": limits.get(user["plan"], 10),
        },
    }
