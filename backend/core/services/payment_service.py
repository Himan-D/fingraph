"""
Stripe Payment Integration
Subscriptions, API keys, webhooks
"""

import logging
from typing import Dict, List, Optional
import stripe
from datetime import datetime, timedelta
from config import settings
from db.postgres import AsyncSessionLocal
from db.postgres_models import Subscription, APIKey
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class StripePaymentService:
    """Stripe payment processing"""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else None
    
    async def create_customer(
        self,
        email: str,
        name: str = None,
        metadata: Dict = None
    ) -> Optional[str]:
        """Create Stripe customer"""
        if not stripe.api_key:
            logger.warning("Stripe not configured")
            return None
        
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return customer.id
        except Exception as e:
            logger.error(f"Customer creation failed: {e}")
            return None
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Dict = None
    ) -> Optional[Dict]:
        """Create subscription"""
        if not stripe.api_key:
            return self._create_mock_subscription(customer_id, price_id)
        
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                metadata=metadata or {},
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )
            
            return {
                "id": subscription.id,
                "status": subscription.status,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None
            }
        except Exception as e:
            logger.error(f"Subscription creation failed: {e}")
            return None
    
    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str
    ) -> Optional[str]:
        """Create checkout session"""
        if not stripe.api_key:
            return None
        
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{"price": price_id, "quantity": 1}],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url
            )
            return session.url
        except Exception as e:
            logger.error(f"Checkout session failed: {e}")
            return None
    
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel subscription"""
        if not stripe.api_key:
            return True
        
        try:
            stripe.Subscription.cancel(subscription_id)
            return True
        except Exception as e:
            logger.error(f"Cancellation failed: {e}")
            return False
    
    async def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        """Get subscription details"""
        if not stripe.api_key:
            return {"status": "active", "mock": True}
        
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": sub.id,
                "status": sub.status,
                "current_period_end": datetime.fromtimestamp(sub.current_period_end),
                "plan": sub.items.data[0].price.id
            }
        except Exception as e:
            logger.error(f"Get subscription failed: {e}")
            return None
    
    def _create_mock_subscription(self, customer_id: str, price_id: str) -> Dict:
        """Create mock subscription for testing"""
        return {
            "id": f"mock_{datetime.now().timestamp()}",
            "status": "active",
            "plan": price_id,
            "mock": True
        }
    
    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Optional[Dict]:
        """Handle Stripe webhook"""
        if not stripe.api_key:
            return {"received": True, "mock": True}
        
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET if hasattr(settings, 'STRIPE_WEBHOOK_SECRET') else None
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            
            if event['type'] == 'checkout.session.completed':
                return await self._handle_checkout_complete(event['data'])
            elif event['type'] == 'customer.subscription.updated':
                return await self._handle_subscription_update(event['data'])
            elif event['type'] == 'customer.subscription.deleted':
                return await self._handle_subscription_cancelled(event['data'])
            elif event['type'] == 'invoice.payment_failed':
                return await self._handle_payment_failed(event['data'])
            
            return {"received": True, "type": event['type']}
            
        except Exception as e:
            logger.error(f"Webhook handling failed: {e}")
            return None
    
    async def _handle_checkout_complete(self, data: Dict) -> Dict:
        """Handle successful checkout"""
        session = data['object']
        
        async with AsyncSessionLocal() as session_db:
            result = await session_db.execute(
                select(Subscription).where(Subscription.stripe_customer_id == session.get('customer'))
            )
            sub = result.scalar_one_or_none()
            
            if sub:
                sub.status = 'active'
                sub.stripe_subscription_id = session.get('subscription')
                sub.current_period_end = datetime.fromtimestamp(
                    session.get('expires_at', datetime.now().timestamp() + 30*24*3600)
                )
                await session_db.commit()
        
        return {"processed": True, "event": "checkout_complete"}
    
    async def _handle_subscription_update(self, data: Dict) -> Dict:
        """Handle subscription update"""
        sub = data['object']
        
        async with AsyncSessionLocal() as session_db:
            result = await session_db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == sub['id'])
            )
            subscription = result.scalar_one_or_none()
            
            if subscription:
                subscription.status = sub['status']
                subscription.current_period_end = datetime.fromtimestamp(sub['current_period_end'])
                await session_db.commit()
        
        return {"processed": True, "event": "subscription_updated"}
    
    async def _handle_subscription_cancelled(self, data: Dict) -> Dict:
        """Handle subscription cancellation"""
        sub = data['object']
        
        async with AsyncSessionLocal() as session_db:
            result = await session_db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == sub['id'])
            )
            subscription = result.scalar_one_or_none()
            
            if subscription:
                subscription.status = 'cancelled'
                await session_db.commit()
        
        return {"processed": True, "event": "subscription_cancelled"}
    
    async def _handle_payment_failed(self, data: Dict) -> Dict:
        """Handle payment failure"""
        invoice = data['object']
        
        async with AsyncSessionLocal() as session_db:
            result = await session_db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == invoice.get('subscription'))
            )
            subscription = result.scalar_one_or_none()
            
            if subscription:
                subscription.status = 'past_due'
                await session_db.commit()
        
        return {"processed": True, "event": "payment_failed"}


class SubscriptionManager:
    """Manage user subscriptions"""
    
    PLANS = {
        "free": {
            "name": "Free",
            "price": 0,
            "price_id": None,
            "features": [
                "Delayed quotes",
                "Basic graph",
                "5 AI queries/day",
                "1 watchlist"
            ],
            "limits": {
                "api_calls_per_day": 100,
                "ai_queries_per_day": 5,
                "watchlists": 1
            }
        },
        "pro": {
            "name": "Pro",
            "price": 199,
            "price_id": "price_pro_monthly",
            "features": [
                "Real-time quotes",
                "Full graph analytics",
                "Unlimited AI queries",
                "10 watchlists",
                "API access"
            ],
            "limits": {
                "api_calls_per_day": 10000,
                "ai_queries_per_day": 999999,
                "watchlists": 10
            }
        },
        "pro_plus": {
            "name": "Pro+",
            "price": 499,
            "price_id": "price_pro_plus_monthly",
            "features": [
                "Real-time quotes",
                "Advanced GDS",
                "Unlimited AI queries",
                "Unlimited watchlists",
                "Full API access",
                "Priority support"
            ],
            "limits": {
                "api_calls_per_day": 100000,
                "ai_queries_per_day": 999999,
                "watchlists": 999999
            }
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 1999,
            "price_id": "price_enterprise_monthly",
            "features": [
                "Everything in Pro+",
                "Custom integrations",
                "Dedicated support",
                "White-label",
                "SLA guarantee"
            ],
            "limits": {
                "api_calls_per_day": 999999999,
                "ai_queries_per_day": 999999999,
                "watchlists": 999999
            }
        }
    }
    
    async def get_user_subscription(self, user_id: int) -> Dict:
        """Get user's current subscription"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            sub = result.scalar_one_or_none()
        
        if not sub:
            return self.PLANS["free"]
        
        plan_name = sub.plan_tier
        return self.PLANS.get(plan_name, self.PLANS["free"])
    
    async def check_feature_access(
        self,
        user_id: int,
        feature: str
    ) -> bool:
        """Check if user has access to feature"""
        sub = await self.get_user_subscription(user_id)
        
        features = sub.get("features", [])
        
        feature_map = {
            "realtime_quotes": ["Real-time quotes"],
            "full_graph": ["Full graph analytics", "Advanced GDS"],
            "unlimited_ai": ["Unlimited AI queries"],
            "api_access": ["API access", "Full API access"],
            "priority_support": ["Priority support"],
            "white_label": ["White-label"]
        }
        
        required = feature_map.get(feature, [])
        return any(f in features for f in required)
    
    async def check_rate_limit(
        self,
        user_id: int,
        limit_type: str
    ) -> bool:
        """Check if user is within rate limits"""
        sub = await self.get_user_subscription(user_id)
        limits = sub.get("limits", {})
        
        max_calls = limits.get(f"{limit_type}_per_day", 100)
        
        from db.redis_client import get_redis
        redis = get_redis()
        
        if redis:
            key = f"rate_limit:{user_id}:{limit_type}"
            current = await redis.get(key)
            
            if current and int(current) >= max_calls:
                return False
            
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, 86400)
            await pipe.execute()
        
        return True


async def get_payment_service() -> StripePaymentService:
    """Get payment service"""
    return StripePaymentService()


if __name__ == "__main__":
    import asyncio
    
    async def main():
        manager = SubscriptionManager()
        sub = await manager.get_user_subscription(1)
        print(f"User subscription: {sub}")
    
    asyncio.run(main())