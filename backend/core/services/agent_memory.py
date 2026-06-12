import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc

from db.postgres import AsyncSessionLocal

logger = logging.getLogger(__name__)

DEFAULT_PREFERENCES = {
    "risk_tolerance": "moderate",
    "investment_horizon": "long_term",
    "preferred_sectors": [],
    "preferred_stocks": [],
    "max_allocation_per_stock": 10,
}


class AgentMemory:
    async def get_preferences(self, user_id: Optional[int]) -> Dict[str, Any]:
        if not user_id:
            return DEFAULT_PREFERENCES.copy()
        try:
            from db.postgres_models import AgentMemory

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AgentMemory)
                    .where(
                        AgentMemory.user_id == user_id,
                        AgentMemory.memory_type == "preference",
                    )
                    .order_by(desc(AgentMemory.id))
                    .limit(1)
                )
                record = result.scalar_one_or_none()
                if record and record.data:
                    return {**DEFAULT_PREFERENCES, **record.data}
        except Exception as e:
            logger.debug(f"Get preferences error: {e}")
        return DEFAULT_PREFERENCES.copy()

    async def set_preference(
        self, user_id: int, key: str, value: Any
    ) -> None:
        try:
            from db.postgres_models import AgentMemory

            prefs = await self.get_preferences(user_id)
            prefs[key] = value
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AgentMemory)
                    .where(
                        AgentMemory.user_id == user_id,
                        AgentMemory.memory_type == "preference",
                    )
                    .order_by(desc(AgentMemory.id))
                    .limit(1)
                )
                record = result.scalar_one_or_none()
                if record:
                    record.data = prefs
                else:
                    record = AgentMemory(
                        user_id=user_id,
                        memory_type="preference",
                        key="user_preferences",
                        data=prefs,
                    )
                    session.add(record)
                await session.commit()
        except Exception as e:
            logger.error(f"Set preference error: {e}")

    async def get_insight(self, symbol: str) -> Optional[str]:
        try:
            from db.postgres_models import AgentMemory

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AgentMemory)
                    .where(
                        AgentMemory.memory_type == "insight",
                        AgentMemory.key == symbol.upper(),
                    )
                    .order_by(desc(AgentMemory.id))
                    .limit(1)
                )
                record = result.scalar_one_or_none()
                if record:
                    return record.data.get("insight") if record.data else None
        except Exception as e:
            logger.debug(f"Get insight error: {e}")
        return None

    async def store_insight(
        self, symbol: str, insight: str, user_id: Optional[int] = None
    ) -> None:
        try:
            from db.postgres_models import AgentMemory

            async with AsyncSessionLocal() as session:
                record = AgentMemory(
                    user_id=user_id,
                    memory_type="insight",
                    key=symbol.upper(),
                    data={"insight": insight, "symbol": symbol.upper()},
                )
                session.add(record)
                await session.commit()
        except Exception as e:
            logger.error(f"Store insight error: {e}")

    async def get_market_context(self) -> Dict[str, Any]:
        context = {}
        try:
            from core.services.market_cache import market_cache

            indices = await market_cache.get_all_indices()
            if indices:
                for idx in indices:
                    context[idx.get("symbol", "")] = idx

            nifty = context.get("NIFTY50")
            if nifty:
                context["nifty_level"] = nifty.get("price")
                context["nifty_change"] = nifty.get("pct_change")
        except Exception as e:
            logger.debug(f"Market context error: {e}")

        try:
            from sqlalchemy import text
            from db.postgres import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                vix = await session.execute(
                    text("SELECT close FROM stock_quotes ORDER BY timestamp DESC LIMIT 1")
                )
                row = vix.scalar_one_or_none()
                if row:
                    context["vix"] = row
        except Exception:
            pass

        return context

    async def build_system_context(
        self, user_id: Optional[int] = None, symbol: Optional[str] = None
    ) -> str:
        parts = []
        prefs = await self.get_preferences(user_id)
        if prefs != DEFAULT_PREFERENCES:
            parts.append(f"User preferences: risk_tolerance={prefs.get('risk_tolerance')}, investment_horizon={prefs.get('investment_horizon')}")
            if prefs.get("preferred_sectors"):
                parts.append(f"Preferred sectors: {', '.join(prefs['preferred_sectors'])}")

        market_ctx = await self.get_market_context()
        if market_ctx.get("nifty_level"):
            parts.append(f"Current Nifty: {market_ctx['nifty_level']} ({market_ctx.get('nifty_change', 0):.2f}%)")

        if symbol:
            insight = await self.get_insight(symbol)
            if insight:
                parts.append(f"Previous insight for {symbol}: {insight[:200]}")

        return "\n".join(parts) if parts else ""


agent_memory = AgentMemory()
