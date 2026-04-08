"""
Subscription and Billing Models

Professional subscription management with tiers, usage tracking, and billing.
"""

from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Text,
)
from sqlalchemy.sql import func

from db.postgres import Base


class PlanTier(str, Enum):
    """Subscription plan tiers"""

    FREE = "free"
    DEVELOPER = "developer"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingPeriod(str, Enum):
    """Billing period options"""

    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    """Subscription status"""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    TRIALING = "trialing"


class Plan(Base):
    """Subscription plans"""

    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    tier = Column(SQLEnum(PlanTier), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price_monthly = Column(Float, default=0)
    price_yearly = Column(Float, default=0)
    api_calls_per_day = Column(Integer, default=0)
    concurrent_requests = Column(Integer, default=1)
    historical_data_days = Column(Integer, default=1)
    real_time_quotes = Column(Boolean, default=False)
    ai_queries = Column(Integer, default=0)
    knowledge_graph = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    custom_integrations = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Subscription(Base):
    """User subscriptions"""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    plan_id = Column(Integer, nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIALING)
    billing_period = Column(SQLEnum(BillingPeriod), default=BillingPeriod.MONTHLY)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    stripe_customer_id = Column(String(100))
    stripe_subscription_id = Column(String(100))
    razorpay_subscription_id = Column(String(100))
    trial_end = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ApiKey(Base):
    """API keys for programmatic access"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)
    name = Column(String(100))
    plan_id = Column(Integer)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UsageRecord(Base):
    """API usage tracking"""

    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, index=True, nullable=False)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10))
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())


class UsageDaily(Base):
    """Daily usage aggregation"""

    __tablename__ = "usage_daily"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, index=True, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    total_calls = Column(Integer, default=0)
    total_response_time = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0)
    error_count = Column(Integer, default=0)


# Pydantic schemas for API
class PlanResponse(BaseModel):
    """Plan response schema"""

    id: int
    tier: PlanTier
    name: str
    description: Optional[str]
    price_monthly: float
    price_yearly: float
    api_calls_per_day: int
    concurrent_requests: int
    historical_data_days: int
    real_time_quotes: bool
    ai_queries: int
    knowledge_graph: bool
    priority_support: bool
    custom_integrations: bool

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Subscription response schema"""

    id: int
    user_id: str
    plan_id: int
    status: SubscriptionStatus
    billing_period: BillingPeriod
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool

    class Config:
        from_attributes = True


class CreateApiKeyRequest(BaseModel):
    """Create API key request"""

    name: str = Field(..., min_length=1, max_length=100)
    plan_id: Optional[int] = None
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)


class ApiKeyResponse(BaseModel):
    """API key response (with masked key)"""

    id: int
    user_id: str
    key_prefix: str
    name: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class UsageStats(BaseModel):
    """Usage statistics"""

    total_calls_today: int
    calls_remaining: int
    avg_response_time: float
    error_rate: float


# Plan definitions
DEFAULT_PLANS = [
    {
        "tier": PlanTier.FREE,
        "name": "Free",
        "description": "For learning and testing",
        "price_monthly": 0,
        "price_yearly": 0,
        "api_calls_per_day": 100,
        "concurrent_requests": 1,
        "historical_data_days": 1,
        "real_time_quotes": False,
        "ai_queries": 10,
        "knowledge_graph": False,
        "priority_support": False,
        "custom_integrations": False,
    },
    {
        "tier": PlanTier.DEVELOPER,
        "name": "Developer",
        "description": "For developers and testing",
        "price_monthly": 999,
        "price_yearly": 9990,
        "api_calls_per_day": 5000,
        "concurrent_requests": 5,
        "historical_data_days": 30,
        "real_time_quotes": True,
        "ai_queries": 100,
        "knowledge_graph": True,
        "priority_support": False,
        "custom_integrations": False,
    },
    {
        "tier": PlanTier.PRO,
        "name": "Pro",
        "description": "For professional traders",
        "price_monthly": 4999,
        "price_yearly": 49990,
        "api_calls_per_day": 50000,
        "concurrent_requests": 20,
        "historical_data_days": 365,
        "real_time_quotes": True,
        "ai_queries": 1000,
        "knowledge_graph": True,
        "priority_support": True,
        "custom_integrations": False,
    },
    {
        "tier": PlanTier.ENTERPRISE,
        "name": "Enterprise",
        "description": "For institutions",
        "price_monthly": 24999,
        "price_yearly": 249990,
        "api_calls_per_day": 1000000,
        "concurrent_requests": 100,
        "historical_data_days": 1825,
        "real_time_quotes": True,
        "ai_queries": 10000,
        "knowledge_graph": True,
        "priority_support": True,
        "custom_integrations": True,
    },
]
