import json
import logging
from typing import Any, Dict, List, Optional

from db.redis_client import get_redis

logger = logging.getLogger(__name__)

CACHE_PREFIX = "fingraph:quote:"
INDEX_PREFIX = "fingraph:index:"
TICK_PREFIX = "fingraph:tick:"


class MarketCache:
    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if not self._redis:
            self._redis = await get_redis()
        return self._redis

    async def set_quote(self, symbol: str, data: Dict[str, Any]) -> None:
        try:
            r = await self._get_redis()
            key = f"{CACHE_PREFIX}{symbol.upper()}"
            await r.set(key, json.dumps(data, default=str), ex=300)
        except Exception as e:
            logger.debug(f"Cache set failed for {symbol}: {e}")

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            r = await self._get_redis()
            key = f"{CACHE_PREFIX}{symbol.upper()}"
            data = await r.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"Cache get failed for {symbol}: {e}")
        return None

    async def set_index(self, symbol: str, data: Dict[str, Any]) -> None:
        try:
            r = await self._get_redis()
            key = f"{INDEX_PREFIX}{symbol.upper()}"
            await r.set(key, json.dumps(data, default=str), ex=300)
        except Exception as e:
            logger.debug(f"Index cache set failed for {symbol}: {e}")

    async def get_index(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            r = await self._get_redis()
            key = f"{INDEX_PREFIX}{symbol.upper()}"
            data = await r.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"Index cache get failed for {symbol}: {e}")
        return None

    async def get_all_indices(self) -> List[Dict[str, Any]]:
        try:
            r = await self._get_redis()
            keys = []
            async for key in r.scan_iter(f"{INDEX_PREFIX}*"):
                keys.append(key)
            if not keys:
                return []
            values = await r.mget(keys)
            results = []
            for v in values:
                if v:
                    results.append(json.loads(v))
            return results
        except Exception as e:
            logger.debug(f"Get all indices failed: {e}")
            return []

    async def set_tick(self, symbol: str, price: float, timestamp: str) -> None:
        try:
            r = await self._get_redis()
            key = f"{TICK_PREFIX}{symbol.upper()}"
            await r.set(key, json.dumps({"price": price, "timestamp": timestamp}), ex=60)
        except Exception as e:
            logger.debug(f"Tick cache failed for {symbol}: {e}")

    async def bulk_set_quotes(self, quotes: Dict[str, Dict[str, Any]]) -> None:
        if not quotes:
            return
        try:
            r = await self._get_redis()
            pipe = r.pipeline()
            for symbol, data in quotes.items():
                key = f"{CACHE_PREFIX}{symbol.upper()}"
                pipe.set(key, json.dumps(data, default=str), ex=300)
            await pipe.execute()
        except Exception as e:
            logger.debug(f"Bulk cache set failed: {e}")

    async def mget_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        if not symbols:
            return {}
        try:
            r = await self._get_redis()
            keys = [f"{CACHE_PREFIX}{s.upper()}" for s in symbols]
            values = await r.mget(keys)
            results = {}
            for sym, val in zip(symbols, values):
                if val:
                    results[sym] = json.loads(val)
            return results
        except Exception as e:
            logger.debug(f"Batch cache get failed: {e}")
            return {}


market_cache = MarketCache()
