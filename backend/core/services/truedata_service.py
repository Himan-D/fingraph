import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Callable, Optional
import websockets
from websockets.exceptions import ConnectionClosed
from config import settings
from db.redis_client import get_redis

logger = logging.getLogger(__name__)


class TrueDataService:
    def __init__(self):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.subscribed_symbols: set = set()
        self.reconnect_delay = 5
        self.is_connected = False
        self.callbacks: Dict[str, Callable] = {}

    async def connect(self):
        """Connect to TrueData WebSocket"""
        try:
            url = f"{settings.TRUEDATA_URL}?username={settings.TRUEDATA_USERNAME}&password={settings.TRUEDATA_PASSWORD}"
            self.ws = await websockets.connect(url, ping_interval=30)
            self.is_connected = True
            self.reconnect_delay = 5
            logger.info("Connected to TrueData")

            # Start listening in background
            asyncio.create_task(self._listen())
            return True
        except Exception as e:
            logger.error(f"Failed to connect to TrueData: {e}")
            self.is_connected = False
            return False

    async def _listen(self):
        """Listen for incoming messages"""
        while self.is_connected and self.ws:
            try:
                message = await self.ws.recv()
                await self._handle_message(message)
            except ConnectionClosed:
                logger.warning("TrueData connection closed, reconnecting...")
                await self.reconnect()
                break
            except Exception as e:
                logger.error(f"Error listening: {e}")
                break

    async def _handle_message(self, message: str):
        """Process incoming message"""
        try:
            data = json.loads(message)

            # Handle different message types
            msg_type = data.get("t")

            if msg_type == "quote":
                symbol = data.get("symbol")
                quote_data = {
                    "symbol": symbol,
                    "last": data.get("last"),
                    "open": data.get("open"),
                    "high": data.get("high"),
                    "low": data.get("low"),
                    "volume": data.get("volume"),
                    "turnover": data.get("turnover"),
                    "bid": data.get("bid"),
                    "ask": data.get("ask"),
                    "timestamp": datetime.now().isoformat(),
                }

                # Cache in Redis
                redis = get_redis()
                if redis:
                    await redis.hset(f"quote:{symbol}", mapping=quote_data)
                    await redis.expire(f"quote:{symbol}", 60)  # 1 minute TTL

                # Call registered callbacks
                if symbol in self.callbacks:
                    await self.callbacks[symbol](quote_data)

            elif msg_type == "index":
                # Handle index data
                pass

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def subscribe(self, symbols: List[str]):
        """Subscribe to symbols"""
        if not self.ws or not self.is_connected:
            logger.warning("Not connected to TrueData")
            return False

        try:
            for symbol in symbols:
                if symbol not in self.subscribed_symbols:
                    await self.ws.send(json.dumps({"t": "subscribe", "symbol": symbol}))
                    self.subscribed_symbols.add(symbol)
            return True
        except Exception as e:
            logger.error(f"Error subscribing: {e}")
            return False

    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from symbols"""
        if not self.ws or not self.is_connected:
            return False

        try:
            for symbol in symbols:
                if symbol in self.subscribed_symbols:
                    await self.ws.send(
                        json.dumps({"t": "unsubscribe", "symbol": symbol})
                    )
                    self.subscribed_symbols.discard(symbol)
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
            return False

    def register_callback(self, symbol: str, callback: Callable):
        """Register callback for symbol updates"""
        self.callbacks[symbol] = callback

    async def get_quote(self, symbol: str) -> Optional[dict]:
        """Get cached quote for symbol"""
        redis = get_redis()
        if redis:
            return await redis.hgetall(f"quote:{symbol}")
        return None

    async def reconnect(self):
        """Reconnect to TrueData"""
        await asyncio.sleep(self.reconnect_delay)
        self.reconnect_delay = min(self.reconnect_delay * 2, 60)
        await self.connect()

        # Resubscribe to symbols
        if self.subscribed_symbols:
            await self.subscribe(list(self.subscribed_symbols))

    async def disconnect(self):
        """Disconnect from TrueData"""
        self.is_connected = False
        if self.ws:
            await self.ws.close()
        logger.info("Disconnected from TrueData")
