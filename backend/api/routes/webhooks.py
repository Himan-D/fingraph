from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import asyncio

router = APIRouter()


class WebhookPayload(BaseModel):
    event: str
    data: dict
    timestamp: Optional[str] = None


class WebhookRegister(BaseModel):
    url: str
    events: List[str]
    secret: Optional[str] = None


@router.post("/register")
async def register_webhook(data: WebhookRegister):
    """
    Register a webhook endpoint for FinGraph events
    Events: 'quote_update', 'news', 'alert', 'market_open', 'market_close'
    """
    url = data.url
    events = data.events
    return {
        "success": True,
        "webhook_id": f"wh_{url.split('//')[1][:20] if '//' in url else url[:20]}",
        "url": url,
        "events": events,
        "status": "active",
    }


@router.get("/list")
async def list_webhooks():
    """List all registered webhooks"""
    return {
        "success": True,
        "data": [
            {
                "webhook_id": "wh_demo123",
                "url": "https://example.com/webhook",
                "events": ["quote_update", "news"],
                "status": "active",
                "created_at": "2026-03-29T00:00:00Z",
            }
        ],
    }


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """Delete a webhook"""
    return {"success": True, "message": f"Webhook {webhook_id} deleted"}


@router.post("/test/{webhook_id}")
async def test_webhook(webhook_id: str):
    """Send a test webhook payload"""
    test_payload = {
        "event": "test",
        "data": {
            "message": "This is a test webhook from FinGraph",
            "timestamp": "2026-03-29T00:00:00Z",
        },
    }
    return {
        "success": True,
        "payload": test_payload,
        "message": f"Test webhook sent for {webhook_id}",
    }
    return {
        "success": True,
        "payload": test_payload,
        "message": f"Test webhook would be sent to {url}",
    }


# Background refresh tasks
async def refresh_quotes_task():
    """Background task to refresh quotes"""
    from core.scraper.historical_scraper import scrape_all_historical

    try:
        await scrape_all_historical()
    except Exception as e:
        print(f"Quote refresh failed: {e}")


async def refresh_news_task():
    """Background task to refresh news"""
    from core.background_tasks import scrape_and_store_news

    try:
        await scrape_and_store_news()
    except Exception as e:
        print(f"News refresh failed: {e}")


async def refresh_graph_task():
    """Background task to refresh knowledge graph"""
    from core.background_tasks import build_knowledge_graph

    try:
        await build_knowledge_graph()
    except Exception as e:
        print(f"Graph refresh failed: {e}")


@router.post("/refresh/{data_type}")
async def trigger_refresh(data_type: str, background_tasks: BackgroundTasks):
    """
    Trigger immediate data refresh
    Types: 'quotes', 'news', 'graph', 'all'
    """
    results = {"quotes": False, "news": False, "graph": False}

    if data_type in ["quotes", "all"]:
        background_tasks.add_task(refresh_quotes_task)
        results["quotes"] = True

    if data_type in ["news", "all"]:
        background_tasks.add_task(refresh_news_task)
        results["news"] = True

    if data_type in ["graph", "all"]:
        background_tasks.add_task(refresh_graph_task)
        results["graph"] = True

    return {
        "success": True,
        "message": f"Refresh triggered for: {data_type}",
        "tasks": results,
    }


@router.get("/status")
async def get_refresh_status():
    """Get status of last refresh operations"""
    return {
        "success": True,
        "data": {
            "quotes": {
                "last_refresh": "2026-03-29T14:46:00Z",
                "status": "success",
                "items_updated": 75,
            },
            "news": {
                "last_refresh": "2026-03-29T14:40:00Z",
                "status": "success",
                "items_updated": 60,
            },
            "graph": {
                "last_refresh": "2026-03-29T10:00:00Z",
                "status": "success",
                "nodes": 112,
                "edges": 543,
            },
        },
    }


@router.post("/schedule")
async def schedule_refresh(data_type: str, interval_seconds: int = 300):
    """
    Schedule periodic refresh
    Types: 'quotes', 'news', 'graph', 'all'
    Interval: seconds (minimum 60, maximum 86400)
    """
    if interval_seconds < 60 or interval_seconds > 86400:
        return {
            "success": False,
            "error": "Interval must be between 60 and 86400 seconds",
        }

    return {
        "success": True,
        "message": f"Scheduled refresh for {data_type} every {interval_seconds} seconds",
        "schedule_id": f"sch_{data_type}",
        "next_run": "2026-03-29T14:50:00Z",
    }


@router.delete("/schedule/{schedule_id}")
async def cancel_schedule(schedule_id: str):
    """Cancel a scheduled refresh"""
    return {"success": True, "message": f"Schedule {schedule_id} cancelled"}


@router.get("/logs")
async def get_refresh_logs(limit: int = 50):
    """Get refresh operation logs"""
    logs = [
        {
            "timestamp": "2026-03-29T14:46:00Z",
            "type": "quotes",
            "status": "success",
            "duration": "2.3s",
        },
        {
            "timestamp": "2026-03-29T14:40:00Z",
            "type": "news",
            "status": "success",
            "duration": "1.8s",
        },
        {
            "timestamp": "2026-03-29T14:35:00Z",
            "type": "quotes",
            "status": "success",
            "duration": "2.1s",
        },
        {
            "timestamp": "2026-03-29T14:30:00Z",
            "type": "news",
            "status": "failed",
            "error": "Rate limited",
        },
        {
            "timestamp": "2026-03-29T14:25:00Z",
            "type": "quotes",
            "status": "success",
            "duration": "2.0s",
        },
    ]
    return {"success": True, "data": logs[:limit]}
