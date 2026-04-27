"""
Monitoring and Metrics Service

Professional observability for:
- API health checks
- System metrics
- Business metrics
- Alerting
"""

import logging
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque

# Ensure backend root is in path before kimi project
_backend_root = str(Path(__file__).parent.parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from sqlalchemy import select, func, and_
from db.postgres import AsyncSessionLocal
from db.redis_client import get_redis

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Service health status"""

    service: str
    status: str  # healthy, degraded, down
    latency_ms: Optional[float] = None
    error: Optional[str] = None


@dataclass
class ApiMetrics:
    """API metrics snapshot"""

    timestamp: datetime
    requests_total: int
    requests_success: int
    requests_error: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float


class MetricsCollector:
    """In-memory metrics collector with rolling window"""

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self._response_times = deque(maxlen=window_size)
        self._request_count = 0
        self._error_count = 0
        self._start_time = time.time()
        self._lock = None

    def record_request(self, response_time_ms: float, is_error: bool = False):
        """Record a request"""
        self._response_times.append(response_time_ms)
        self._request_count += 1
        if is_error:
            self._error_count += 1

    def get_metrics(self) -> ApiMetrics:
        """Get current metrics"""
        times = list(self._response_times)

        if not times:
            return ApiMetrics(
                timestamp=datetime.now(),
                requests_total=0,
                requests_success=0,
                requests_error=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
            )

        times_sorted = sorted(times)
        n = len(times_sorted)

        return ApiMetrics(
            timestamp=datetime.now(),
            requests_total=self._request_count,
            requests_success=self._request_count - self._error_count,
            requests_error=self._error_count,
            avg_response_time_ms=sum(times) / n,
            p95_response_time_ms=times_sorted[int(n * 0.95)],
            p99_response_time_ms=times_sorted[int(n * 0.99)],
        )


@dataclass
class SystemMetrics:
    """System-level metrics"""

    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: float
    active_connections: int


class MonitoringService:
    """Professional monitoring service"""

    def __init__(self):
        self._metrics = MetricsCollector()

    async def check_database_health(self) -> HealthStatus:
        """Check PostgreSQL health"""
        start = time.time()
        try:
            from sqlalchemy import text
            from db.postgres import engine

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            latency = (time.time() - start) * 1000
            return HealthStatus(
                service="postgresql",
                status="healthy",
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            return HealthStatus(
                service="postgresql",
                status="down",
                error=str(e),
            )

    async def check_redis_health(self) -> HealthStatus:
        """Check Redis health"""
        start = time.time()
        try:
            redis = await get_redis()
            await redis.ping()

            latency = (time.time() - start) * 1000
            return HealthStatus(
                service="redis",
                status="healthy",
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            return HealthStatus(
                service="redis",
                status="down",
                error=str(e),
            )

    async def check_neo4j_health(self) -> HealthStatus:
        """Check Neo4j health"""
        start = time.time()
        try:
            from db.neo4j_client import get_neo4j

            driver = get_neo4j()
            if driver:
                async with driver.session() as session:
                    await session.run("RETURN 1")

                latency = (time.time() - start) * 1000
                return HealthStatus(
                    service="neo4j",
                    status="healthy",
                    latency_ms=round(latency, 2),
                )
            else:
                return HealthStatus(
                    service="neo4j",
                    status="degraded",
                    error="Not configured",
                )
        except Exception as e:
            return HealthStatus(
                service="neo4j",
                status="down",
                error=str(e),
            )

    async def get_all_health(self) -> Dict:
        """Get health status for all services"""
        services = await self._check_all_services()

        overall = "healthy"
        if any(s.status == "down" for s in services):
            overall = "degraded"
        if any(s.status == "down" for s in services):
            overall = "down"

        return {
            "status": overall,
            "timestamp": datetime.now().isoformat(),
            "services": [s.__dict__ for s in services],
        }

    async def _check_all_services(self) -> List[HealthStatus]:
        """Check all services in parallel"""
        import asyncio

        return await asyncio.gather(
            self.check_database_health(),
            self.check_redis_health(),
            self.check_neo4j_health(),
            return_exceptions=True,
        )

    async def get_api_metrics(self) -> Dict:
        """Get API metrics"""
        metrics = self._metrics.get_metrics()

        return {
            "timestamp": metrics.timestamp.isoformat(),
            "requests": {
                "total": metrics.requests_total,
                "success": metrics.requests_success,
                "errors": metrics.requests_error,
                "error_rate": round(
                    metrics.requests_error / metrics.requests_total * 100, 2
                )
                if metrics.requests_total > 0
                else 0,
            },
            "response_time": {
                "avg_ms": round(metrics.avg_response_time_ms, 2),
                "p95_ms": round(metrics.p95_response_time_ms, 2),
                "p99_ms": round(metrics.p99_response_time_ms, 2),
            },
        }

    async def get_business_metrics(self) -> Dict:
        """Get business metrics"""
        from models.billing import UsageDaily, ApiKey, Subscription, Plan

        metrics = {
            "api_keys": {"total": 0, "active": 0},
            "subscriptions": {"total": 0, "active": 0},
            "usage": {"today_calls": 0},
        }

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(ApiKey.id)))
            metrics["api_keys"]["total"] = result.scalar() or 0

            result = await session.execute(
                select(func.count(ApiKey.id)).where(ApiKey.is_active == True)
            )
            metrics["api_keys"]["active"] = result.scalar() or 0

            result = await session.execute(select(func.count(Subscription.id)))
            metrics["subscriptions"]["total"] = result.scalar() or 0

            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            result = await session.execute(
                select(func.sum(UsageDaily.total_calls)).where(UsageDaily.date >= today)
            )
            metrics["usage"]["today_calls"] = result.scalar() or 0

        return metrics

    async def get_dashboard(self) -> Dict:
        """Get complete dashboard data"""
        health = await self.get_all_health()
        api_metrics = await self.get_api_metrics()
        business = await self.get_business_metrics()

        return {
            "generated_at": datetime.now().isoformat(),
            "health": health,
            "api_metrics": api_metrics,
            "business": business,
        }


monitoring_service = MonitoringService()
