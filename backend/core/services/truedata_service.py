import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Dict, List, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from config import settings
from core.services.market_cache import market_cache

logger = logging.getLogger(__name__)

NIFTY50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
    "ITC", "SBIN", "BHARTIARTL", "LT", "KOTAKBANK", "AXISBANK",
    "ASIANPAINT", "BAJFINANCE", "MARUTI", "SUNPHARMA", "TATAMOTORS",
    "WIPRO", "HCLTECH", "ULTRACEMCO", "TITAN", "NESTLEIND", "NESTLEIND",
    "ADANIENT", "ONGC", "NTPC", "POWERGRID", "TATASTEEL", "HDFC LIFE",
    "BAJAJFINSV", "COALINDIA", "TECHM", "DRREDDY", "JSWSTEEL",
    "HINDALCO", "CIPLA", "BPCL", "TATACONSUM", "EICHERMOT", "GRASIM",
    "HEROMOTOCO", "INDUSINDBK", "DIVISLAB", "BRITANNIA", "APOLLOHOSP",
    "M_M", "SHRIRAMFIN", "SBILIFE", "TRENT", "HDFCAMC",
]

INDEX_SYMBOLS = ["NIFTY50", "BANKNIFTY", "NIFTYMIDCAP", "NIFTYIT"]


class TrueDataService:
    def __init__(self):
        self.ws = None
        self.subscribed_symbols: set = set()
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
        self.is_connected = False
        self.callbacks: Dict[str, Callable] = {}
        self._listen_task: Optional[asyncio.Task] = None
        self._running = False

    async def connect(self) -> bool:
        if not settings.TRUEDATA_USERNAME or not settings.TRUEDATA_PASSWORD:
            logger.info("TrueData credentials not configured, skipping")
            return False

        try:
            url = (
                f"{settings.TRUEDATA_URL}"
                f"?username={settings.TRUEDATA_USERNAME}"
                f"&password={settings.TRUEDATA_PASSWORD}"
            )
            self.ws = await websockets.connect(
                url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )
            self.is_connected = True
            self.reconnect_delay = 1
            self._running = True
            logger.info("Connected to TrueData WebSocket")

            if self._listen_task and not self._listen_task.done():
                self._listen_task.cancel()
            self._listen_task = asyncio.create_task(self._listen_loop())

            await self.subscribe_default()
            return True
        except Exception as e:
            logger.warning(f"TrueData connection failed: {e}")
            self.is_connected = False
            if self._running:
                asyncio.create_task(self._reconnect())
            return False

    async def _listen_loop(self):
        while self._running and self.is_connected:
            try:
                message = await self.ws.recv()
                await self._handle_message(message)
            except ConnectionClosed:
                logger.warning("TrueData WebSocket closed")
                self.is_connected = False
                if self._running:
                    await self._reconnect()
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"TrueData listen error: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, message: str):
        try:
            data = json.loads(message)
            msg_type = data.get("t")

            if msg_type == "quote":
                symbol = data.get("symbol", "")
                quote_data = {
                    "symbol": symbol,
                    "price": data.get("last"),
                    "open": data.get("open"),
                    "high": data.get("high"),
                    "low": data.get("low"),
                    "close": data.get("last"),
                    "volume": data.get("volume"),
                    "turnover": data.get("turnover"),
                    "bid": data.get("bid"),
                    "ask": data.get("ask"),
                    "timestamp": datetime.now().isoformat(),
                }
                await market_cache.set_quote(symbol, quote_data)
                await market_cache.set_tick(
                    symbol, quote_data["price"], quote_data["timestamp"]
                )

                if symbol in self.callbacks:
                    try:
                        await self.callbacks[symbol](quote_data)
                    except Exception as e:
                        logger.debug(f"Callback error for {symbol}: {e}")

            elif msg_type == "index":
                symbol = data.get("symbol", "")
                index_data = {
                    "symbol": symbol,
                    "name": data.get("name", symbol),
                    "price": data.get("last"),
                    "change": data.get("change"),
                    "pct_change": data.get("pct_change"),
                    "high": data.get("high"),
                    "low": data.get("low"),
                    "timestamp": datetime.now().isoformat(),
                }
                await market_cache.set_index(symbol, index_data)

        except json.JSONDecodeError:
            logger.debug(f"Non-JSON message from TrueData: {message[:100]}")
        except Exception as e:
            logger.error(f"TrueData message handling error: {e}")

    async def subscribe_default(self):
        await self.subscribe(NIFTY50_SYMBOLS + INDEX_SYMBOLS)

    async def subscribe(self, symbols: List[str]) -> bool:
        if not self.ws or not self.is_connected:
            return False
        try:
            for symbol in symbols:
                if symbol not in self.subscribed_symbols:
                    await self.ws.send(
                        json.dumps({"t": "subscribe", "symbol": symbol})
                    )
                    self.subscribed_symbols.add(symbol)
            logger.info(f"Subscribed to {len(symbols)} symbols ({len(self.subscribed_symbols)} total)")
            return True
        except Exception as e:
            logger.error(f"Subscribe error: {e}")
            return False

    async def unsubscribe(self, symbols: List[str]) -> bool:
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
            logger.error(f"Unsubscribe error: {e}")
            return False

    def register_callback(self, symbol: str, callback: Callable):
        self.callbacks[symbol] = callback

    async def get_quote(self, symbol: str) -> Optional[dict]:
        cached = await market_cache.get_quote(symbol)
        if cached:
            return cached
        return None

    async def _reconnect(self):
        if not self._running:
            return
        logger.info(f"Reconnecting in {self.reconnect_delay}s...")
        await asyncio.sleep(self.reconnect_delay)
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        await self.connect()

    async def disconnect(self):
        self._running = False
        self.is_connected = False
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
        logger.info("Disconnected from TrueData")
