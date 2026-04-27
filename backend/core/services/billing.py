"""
Billing Service - Professional subscription and API key management

Handles:
- Plan management
- API key generation and validation
- Usage tracking and rate limiting
- Subscription lifecycle
"""

import hashlib
import secrets
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure backend root is in path before kimi project
_backend_root = str(Path(__file__).parent.parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from models.billing import (
    Plan,
    Subscription,
    ApiKey,
    UsageRecord,
    UsageDaily,
    PlanTier,
    BillingPeriod,
    SubscriptionStatus,
    DEFAULT_PLANS,
)
from db.postgres import AsyncSessionLocal

logger = logging.getLogger(__name__)


class BillingService:
    """Professional billing and subscription service"""

    def __init__(self):
        self._plans_cache: Optional[List[Plan]] = None

    async def initialize_plans(self):
        """Initialize default plans in database"""
        async with AsyncSessionLocal() as session:
            for plan_data in DEFAULT_PLANS:
                result = await session.execute(
                    select(Plan).where(Plan.tier == plan_data["tier"])
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    plan = Plan(**plan_data)
                    session.add(plan)

            await session.commit()
            logger.info("Default plans initialized")

    async def get_plan(self, tier: PlanTier) -> Optional[Plan]:
        """Get plan by tier"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Plan).where(Plan.tier == tier, Plan.is_active == True)
            )
            return result.scalar_one_or_none()

    async def get_all_plans(self) -> List[Plan]:
        """Get all active plans"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Plan).where(Plan.is_active == True).order_by(Plan.price_monthly)
            )
            return list(result.scalars().all())

    async def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription)
                .where(
                    Subscription.user_id == user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                )
                .order_by(Subscription.created_at.desc())
            )
            return result.scalar_one_or_none()

    async def get_subscription_plan(self, user_id: str) -> Optional[Plan]:
        """Get user's subscription plan"""
        subscription = await self.get_user_subscription(user_id)
        if not subscription:
            return await self.get_plan(PlanTier.FREE)

        return await self.get_plan_by_id(subscription.plan_id)

    async def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        """Get plan by ID"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Plan).where(Plan.id == plan_id))
            return result.scalar_one_or_none()

    async def create_api_key(
        self,
        user_id: str,
        name: str,
        plan_id: Optional[int] = None,
        expires_in_days: Optional[int] = None,
    ) -> Dict[str, str]:
        """Create new API key"""
        if not plan_id:
            user_plan = await self.get_subscription_plan(user_id)
            plan_id = user_plan.id if user_plan else 1

        key_raw = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key_raw.encode()).hexdigest()
        key_prefix = f"fg_{key_raw[:8]}"

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        async with AsyncSessionLocal() as session:
            api_key = ApiKey(
                user_id=user_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=name,
                plan_id=plan_id,
                expires_at=expires_at,
            )
            session.add(api_key)
            await session.commit()

        return {
            "id": api_key.id,
            "key": f"{key_prefix}_{key_raw}",
            "name": name,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

    async def validate_api_key(self, key: str) -> Optional[Dict]:
        """Validate API key and return associated data"""
        if not key or "_" not in key:
            return None

        parts = key.split("_")
        if len(parts) < 2:
            return None

        key_prefix = parts[0] + "_" + parts[1]
        key_raw = "_".join(parts[2:])
        key_hash = hashlib.sha256(key_raw.encode()).hexdigest()

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ApiKey).where(
                    ApiKey.key_prefix == key_prefix, ApiKey.is_active == True
                )
            )
            api_key = result.scalar_one_or_none()

            if not api_key:
                return None

            if api_key.expires_at and api_key.expires_at < datetime.now():
                return None

            if api_key.key_hash != key_hash:
                return None

            api_key.last_used_at = datetime.now()
            await session.commit()

            plan = await self.get_plan_by_id(api_key.plan_id)

            return {
                "id": api_key.id,
                "user_id": api_key.user_id,
                "plan_id": api_key.plan_id,
                "plan_tier": plan.tier.value if plan else "free",
                "api_calls_per_day": plan.api_calls_per_day if plan else 100,
            }

    async def check_rate_limit(self, api_key_id: int) -> Dict:
        """Check if API key has exceeded rate limit"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UsageDaily).where(
                    UsageDaily.api_key_id == api_key_id,
                    UsageDaily.date
                    >= datetime.now().replace(hour=0, minute=0, second=0),
                )
            )
            usage = result.scalar_one_or_none()

            result = await session.execute(
                select(ApiKey).where(ApiKey.id == api_key_id)
            )
            api_key = result.scalar_one_or_none()

            if not api_key:
                return {"allowed": False, "reason": "API key not found"}

            plan = await self.get_plan_by_id(api_key.plan_id)
            daily_limit = plan.api_calls_per_day if plan else 100

            current_usage = usage.total_calls if usage else 0

            return {
                "allowed": current_usage < daily_limit,
                "current_usage": current_usage,
                "daily_limit": daily_limit,
                "remaining": max(0, daily_limit - current_usage),
            }

    async def record_usage(
        self,
        api_key_id: int,
        endpoint: str,
        method: str = "GET",
        status_code: int = 200,
        response_time_ms: int = 0,
        ip_address: str = None,
    ):
        """Record API usage"""
        async with AsyncSessionLocal() as session:
            record = UsageRecord(
                api_key_id=api_key_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                ip_address=ip_address,
            )
            session.add(record)

            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            result = await session.execute(
                select(UsageDaily).where(
                    UsageDaily.api_key_id == api_key_id, UsageDaily.date == today
                )
            )
            daily = result.scalar_one_or_none()

            if daily:
                daily.total_calls += 1
                daily.total_response_time += response_time_ms
                daily.avg_response_time = daily.total_response_time / daily.total_calls
                if status_code >= 400:
                    daily.error_count += 1
            else:
                daily = UsageDaily(
                    api_key_id=api_key_id,
                    date=today,
                    total_calls=1,
                    total_response_time=response_time_ms,
                    avg_response_time=response_time_ms,
                    error_count=1 if status_code >= 400 else 0,
                )
                session.add(daily)

            await session.commit()

    async def get_usage_stats(self, api_key_id: int) -> Dict:
        """Get usage statistics for API key"""
        async with AsyncSessionLocal() as session:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            result = await session.execute(
                select(UsageDaily).where(
                    UsageDaily.api_key_id == api_key_id, UsageDaily.date >= today
                )
            )
            daily = result.scalar_one_or_none()

            result = await session.execute(
                select(ApiKey).where(ApiKey.id == api_key_id)
            )
            api_key = result.scalar_one_or_none()

            plan = await self.get_plan_by_id(api_key.plan_id) if api_key else None

            total_calls = daily.total_calls if daily else 0
            daily_limit = plan.api_calls_per_day if plan else 100

            return {
                "total_calls_today": total_calls,
                "calls_remaining": max(0, daily_limit - total_calls),
                "daily_limit": daily_limit,
                "avg_response_time": daily.avg_response_time if daily else 0,
                "error_count": daily.error_count if daily else 0,
                "error_rate": (daily.error_count / total_calls * 100)
                if total_calls > 0
                else 0,
            }

    async def list_user_api_keys(self, user_id: str) -> List[ApiKey]:
        """List all API keys for user"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ApiKey)
                .where(ApiKey.user_id == user_id)
                .order_by(ApiKey.created_at.desc())
            )
            return list(result.scalars().all())

    async def revoke_api_key(self, key_id: int, user_id: str) -> bool:
        """Revoke an API key"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
            )
            api_key = result.scalar_one_or_none()

            if api_key:
                api_key.is_active = False
                await session.commit()
                return True

            return False


# Singleton instance
billing_service = BillingService()
