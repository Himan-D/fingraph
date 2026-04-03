"""
NSE India Data Fetcher - Direct API integration
"""

import httpx
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

NSE_URL = "https://www.nseindia.com"


class NSEDataFetcher:
    """Fetch data directly from NSE India"""

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": NSE_URL,
                "Origin": NSE_URL,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        self.cookies = {}

    async def _get_cookies(self):
        """Get NSE cookies"""
        try:
            # Warm up cookie jar via homepage + a lightweight API endpoint.
            await self.client.get(NSE_URL)
            await self.client.get(f"{NSE_URL}/api/allIndices")
            self.cookies = dict(self.client.cookies)
        except Exception as e:
            logger.warning(f"Failed to get cookies: {e}")

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get live quote for a symbol"""
        await self._get_cookies()

        try:
            # Try equity quote
            url = f"{NSE_URL}/api/quote-equity?symbol={quote_plus(symbol)}"
            response = await self.client.get(url, cookies=self.cookies)

            if response.status_code == 200 and response.text:
                data = response.json()
                return self._parse_quote(data, symbol)
        except Exception as e:
            logger.warning(f"NSE quote failed for {symbol}: {e}")

        # Fallback endpoint
        try:
            url = f"{NSE_URL}/api/quote-advance?symbol={quote_plus(symbol)}"
            response = await self.client.get(url, cookies=self.cookies)
            if response.status_code == 200 and response.text:
                data = response.json()
                return self._parse_quote(data, symbol)
        except Exception as e:
            logger.warning(f"NSE quote fallback failed for {symbol}: {e}")

        return None

    def _parse_quote(self, data: Dict, symbol: str) -> Dict[str, Any]:
        """Parse NSE quote response"""
        try:
            metadata = data.get("metadata", {})
            priceInfo = data.get("priceInfo", {})
            security_info = data.get("securityInfo", {})

            return {
                "symbol": symbol,
                "name": metadata.get("companyName", symbol),
                "price": priceInfo.get("lastPrice", 0),
                "change": priceInfo.get("change", 0),
                "pct_change": priceInfo.get("pChange", 0),
                "open": priceInfo.get("open", 0),
                "high": priceInfo.get("high", 0),
                "low": priceInfo.get("low", 0),
                "volume": priceInfo.get("total traded volume", 0),
                "value": priceInfo.get("total traded value", 0),
                "market_cap": metadata.get("marketCap", 0)
                or security_info.get("issuedCap", 0),
                "sector": metadata.get("industry", "") or security_info.get("sector", ""),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Failed to parse quote: {e}")
            return None

    async def get_indices(self) -> List[Dict[str, Any]]:
        """Get index values"""
        await self._get_cookies()

        try:
            url = f"{NSE_URL}/api/allIndices"
            response = await self.client.get(url, cookies=self.cookies)
            if response.status_code != 200 or not response.text:
                return []

            payload = response.json()
            all_data = payload.get("data", []) if isinstance(payload, dict) else []
            wanted = {
                "NIFTY 50": "NIFTY50",
                "NIFTY BANK": "BANKNIFTY",
                "NIFTY IT": "NIFTYIT",
                "NIFTY AUTO": "NIFTYAUTO",
                "NIFTY PHARMA": "NIFTYPHARMA",
                "NIFTY FMCG": "NIFTYFMCG",
                "NIFTY METAL": "NIFTYMETAL",
            }

            results: List[Dict[str, Any]] = []
            for row in all_data:
                if not isinstance(row, dict):
                    continue
                name = str(row.get("index", "")).upper()
                if name in wanted:
                    results.append(
                        {
                            "symbol": wanted[name],
                            "name": row.get("index", name),
                            "price": row.get("last", 0),
                            "change": row.get("variation", 0),
                            "pct_change": row.get("percentChange", 0),
                        }
                    )
            return results
        except Exception as e:
            logger.warning(f"Indices fetch failed: {e}")
            return []

    async def get_movers(self) -> Dict[str, List]:
        """Get top gainers and losers"""
        await self._get_cookies()

        try:
            # Get market status
            url = f"{NSE_URL}/api/marketStatus"
            response = await self.client.get(url, cookies=self.cookies)

            if response.status_code == 200:
                data = response.json()
                return {
                    "gainers": data.get("gainers", [])[:10],
                    "losers": data.get("losers", [])[:10],
                }
        except Exception as e:
            logger.warning(f"Movers failed: {e}")

        return {"gainers": [], "losers": []}

    async def get_option_chain(self, symbol: str = "NIFTY") -> Dict:
        """Get option chain"""
        await self._get_cookies()

        try:
            symbol_upper = symbol.upper()
            if symbol_upper in {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"}:
                url = f"{NSE_URL}/api/option-chain-indices?symbol={quote_plus(symbol_upper)}"
            else:
                url = f"{NSE_URL}/api/option-chain-equities?symbol={quote_plus(symbol_upper)}"
            response = await self.client.get(url, cookies=self.cookies)

            if response.status_code == 200:
                data = response.json()
                return data
        except Exception as e:
            logger.warning(f"Option chain failed: {e}")

        return {}

    async def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed stock information"""
        await self._get_cookies()

        try:
            url = f"{NSE_URL}/api/quote?symbol={symbol}"
            response = await self.client.get(url, cookies=self.cookies)

            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Stock info failed: {e}")

        return {}

    async def close(self):
        """Close client"""
        await self.client.aclose()


# Singleton instance
_nse_fetcher = None


def get_nse_fetcher() -> NSEDataFetcher:
    global _nse_fetcher
    if _nse_fetcher is None:
        _nse_fetcher = NSEDataFetcher()
    return _nse_fetcher
