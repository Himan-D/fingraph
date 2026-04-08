"""
Billing API Routes

Professional subscription and API key management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime

from core.services.billing import billing_service
from models.billing import (
    PlanResponse,
    ApiKeyResponse,
    SubscriptionResponse,
    UsageStats,
)

router = APIRouter()


@router.get("/plans", response_model=List[PlanResponse])
async def list_plans():
    """List all available subscription plans"""
    plans = await billing_service.get_all_plans()
    return [PlanResponse.model_validate(p) for p in plans]


@router.get("/plans/{tier}")
async def get_plan(tier: str):
    """Get plan details by tier"""
    from models.billing import PlanTier

    try:
        plan = await billing_service.get_plan(PlanTier(tier))
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return PlanResponse.model_validate(plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tier")


@router.get("/subscription")
async def get_my_subscription(user_id: str = Query(...)):
    """Get current user's subscription"""
    subscription = await billing_service.get_user_subscription(user_id)
    if not subscription:
        return {"status": "free", "plan": None}

    plan = await billing_service.get_plan_by_id(subscription.plan_id)
    return {
        "subscription": SubscriptionResponse.model_validate(subscription),
        "plan": PlanResponse.model_validate(plan) if plan else None,
    }


@router.post("/api-keys")
async def create_api_key(
    user_id: str = Query(...),
    name: str = Query(...),
    plan_id: Optional[int] = None,
    expires_in_days: Optional[int] = None,
):
    """Create new API key"""
    result = await billing_service.create_api_key(
        user_id=user_id,
        name=name,
        plan_id=plan_id,
        expires_in_days=expires_in_days,
    )

    return {
        "success": True,
        "api_key": result["key"],
        "warning": "Store this key securely - it cannot be retrieved again!",
        "details": {
            "id": result["id"],
            "name": result["name"],
            "expires_at": result["expires_at"],
        },
    }


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(user_id: str = Query(...)):
    """List all API keys for user"""
    keys = await billing_service.list_user_api_keys(user_id)
    return [ApiKeyResponse.model_validate(k) for k in keys]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: int, user_id: str = Query(...)):
    """Revoke an API key"""
    success = await billing_service.revoke_api_key(key_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"success": True, "message": "API key revoked"}


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    api_key_id: int = Query(...),
):
    """Get usage statistics for API key"""
    stats = await billing_service.get_usage_stats(api_key_id)
    return UsageStats(**stats)


@router.get("/rate-limit")
async def check_rate_limit(api_key_id: int = Query(...)):
    """Check rate limit status"""
    limit = await billing_service.check_rate_limit(api_key_id)
    return limit


@router.post("/usage/record")
async def record_usage(
    api_key_id: int = Query(...),
    endpoint: str = Query(...),
    method: str = "GET",
    status_code: int = 200,
    response_time_ms: int = 0,
    ip_address: Optional[str] = None,
):
    """Record API usage (internal)"""
    await billing_service.record_usage(
        api_key_id=api_key_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        ip_address=ip_address,
    )
    return {"success": True}
