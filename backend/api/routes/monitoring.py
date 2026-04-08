"""
Monitoring API Routes

Professional health checks and metrics.
"""

from fastapi import APIRouter, Query
from typing import Optional

from core.services.monitoring import monitoring_service

router = APIRouter()


@router.get("/health")
async def health_check():
    """Get health status of all services"""
    return await monitoring_service.get_all_health()


@router.get("/health/{service}")
async def service_health(service: str):
    """Get health of specific service"""
    if service == "postgres" or service == "postgresql":
        return await monitoring_service.check_database_health()
    elif service == "redis":
        return await monitoring_service.check_redis_health()
    elif service == "neo4j":
        return await monitoring_service.check_neo4j_health()
    else:
        return {"error": f"Unknown service: {service}"}


@router.get("/metrics")
async def get_api_metrics():
    """Get API metrics"""
    return await monitoring_service.get_api_metrics()


@router.get("/metrics/business")
async def get_business_metrics():
    """Get business metrics"""
    return await monitoring_service.get_business_metrics()


@router.get("/dashboard")
async def get_dashboard():
    """Get complete dashboard"""
    return await monitoring_service.get_dashboard()


@router.get("/status")
async def get_status():
    """Quick status check"""
    health = await monitoring_service.get_all_health()
    return {
        "status": health["status"],
        "version": "1.0.0",
        "timestamp": health["timestamp"],
    }
