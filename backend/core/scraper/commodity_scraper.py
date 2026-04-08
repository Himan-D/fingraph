import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class YahooFinanceCommodityScraper:
    """Scrape real commodity prices from Yahoo Finance"""

    TICKERS = {
        "GOLD": "GC=F",
        "SILVER": "SI=F",
        "CRUDEOIL": "CL=F",
        "NATURALGAS": "NG=F",
        "COPPER": "HG=F",
        "PLATINUM": "PL=F",
        "PALLADIUM": "PA=F",
        "COTTON": "CT=F",
        "SUGAR": "SB=F",
        "COFFEE": "KC=F",
        "CORN": "ZC=F",
        "WHEAT": "ZW=F",
        "SOYBEANS": "ZS=F",
        "RICE": "ZR=F",
        "OATS": "ZO=F",
        "ALUMINIUM": "ALI=F",
    }

    async def _fetch_yahoo(self, ticker: str) -> Optional[Dict]:
        """Fetch from Yahoo Finance API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }

                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = data.get("chart", {}).get("result", [])

                        if result:
                            meta = result[0].get("meta", {})
                            quote = (
                                result[0].get("indicators", {}).get("quote", [{}])[0]
                            )

                            prev_close = meta.get("previousClose", 0)
                            last_close = meta.get("regularMarketPrice", 0)
                            change = last_close - prev_close
                            change_pct = (
                                (change / prev_close * 100) if prev_close else 0
                            )

                            return {
                                "symbol": ticker.replace("=F", "").replace("-", ""),
                                "exchange": "COMEX/NYMEX",
                                "close": last_close,
                                "open": quote.get("open", [0])[-1]
                                if quote.get("open")
                                else last_close,
                                "high": quote.get("high", [0])[-1]
                                if quote.get("high")
                                else last_close,
                                "low": quote.get("low", [0])[-1]
                                if quote.get("low")
                                else last_close,
                                "previous_close": prev_close,
                                "change": change,
                                "change_pct": change_pct,
                                "volume": quote.get("volume", [0])[-1]
                                if quote.get("volume")
                                else 0,
                                "timestamp": datetime.now().isoformat(),
                            }
        except Exception as e:
            logger.debug(f"Yahoo fetch failed for {ticker}: {e}")

        return None

    async def scrape_all(self) -> List[Dict]:
        """Scrape all commodities from Yahoo"""
        results = await asyncio.gather(
            *[self._fetch_yahoo(t) for t in self.TICKERS.values()],
            return_exceptions=True,
        )

        valid = [r for r in results if r and r.get("close", 0) > 0]

        symbol_map = {
            v.replace("=F", "").replace("-", ""): k for k, v in self.TICKERS.items()
        }
        for r in valid:
            original = symbol_map.get(r.get("symbol", ""), r.get("symbol", ""))
            r["symbol"] = original

        return valid


class MCXIndiaScraper:
    """Scrape real MCX India commodity prices"""

    BASE_URL = "https://api.mcxindia.com"

    async def _fetch_mcx_realtime(self, symbol: str) -> Optional[Dict]:
        """Fetch from MCX realtime API"""
        mcx_symbols = {
            "GOLD": "GOLD",
            "SILVER": "SILVER",
            "CRUDEOIL": "CRUDEOIL",
            "NATURALGAS": "NATURALGAS",
            "COPPER": "COPPER",
            "ZINC": "ZINC",
            "NICKEL": "NICKEL",
            "LEAD": "LEAD",
            "ALUMINIUM": "ALUMINIUM",
        }

        mcx_code = mcx_symbols.get(symbol.upper())
        if not mcx_code:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://www.mcxindia.com/ajaxcalls/get_market_data.php?symbol={mcx_code}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                    "Referer": "https://www.mcxindia.com/market-data/real-time-data",
                }

                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        text = await resp.text()

                        if text and text.strip():
                            try:
                                data = text.strip()
                                parts = data.split(",")

                                if len(parts) >= 6:
                                    close = float(parts[0].strip() or 0)
                                    change = float(parts[1].strip() or 0)

                                    return {
                                        "symbol": symbol.upper(),
                                        "exchange": "MCX",
                                        "close": close,
                                        "change": change,
                                        "change_pct": (change / (close - change) * 100)
                                        if close > change
                                        else 0,
                                        "timestamp": datetime.now().isoformat(),
                                    }
                            except:
                                pass
        except Exception as e:
            logger.debug(f"MCX fetch failed for {symbol}: {e}")

        return None

    async def scrape_screener_in(self, symbol: str) -> Optional[Dict]:
        """Fallback: Scrape from Screener.in"""
        screener_map = {
            "GOLD": "gold",
            "SILVER": "silver",
            "CRUDEOIL": "crude-oil",
            "NATURALGAS": "natural-gas",
        }

        scrip = screener_map.get(symbol.upper())
        if not scrip:
            return None

        try:
            from bs4 import BeautifulSoup

            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0"}

                url = f"https://www.screener.in/commodities/{scrip}/"
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")

                        price_elem = soup.find(string=re.compile(r"(₹|Rs|Rs\.)"))

                        if price_elem:
                            parent = price_elem.parent
                            if parent:
                                text = parent.get_text()
                                numbers = re.findall(r"[\d,]+\.?\d*", text)
                                if numbers:
                                    close = float(numbers[0].replace(",", ""))

                                    return {
                                        "symbol": symbol.upper(),
                                        "exchange": "MCX",
                                        "close": close,
                                        "timestamp": datetime.now().isoformat(),
                                    }
        except Exception as e:
            logger.debug(f"Screener scrape failed for {symbol}: {e}")

        return None

    async def scrape_all(self) -> List[Dict]:
        """Scrape all MCX commodities"""
        symbols = ["GOLD", "SILVER", "CRUDEOIL", "NATURALGAS"]

        results = []
        for symbol in symbols:
            data = await self._fetch_mcx_realtime(symbol)
            if not data:
                data = await self.scrape_screener_in(symbol)
            if data:
                results.append(data)

        return results


class InvestingComScraper:
    """Scrape from Investing.com"""

    COMMODITY_IDS = {
        "GOLD": 8830,
        "SILVER": 8831,
        "CRUDEOIL": 8849,
        "NATURALGAS": 8874,
        "COPPER": 8970,
    }

    async def _fetch_investing(self, commodity_id: int) -> Optional[Dict]:
        """Fetch from Investing.com API"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                }

                url = f"https://api.investing.com/api/marketdata/v1/{commodity_id}"
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        return {
                            "symbol": data.get("symbol", ""),
                            "close": data.get("last", 0),
                            "change": data.get("change", 0),
                            "change_pct": data.get("change_percent", 0),
                            "high": data.get("high", 0),
                            "low": data.get("low", 0),
                            "timestamp": datetime.now().isoformat(),
                        }
        except Exception as e:
            logger.debug(f"Investing fetch failed for {commodity_id}: {e}")

        return None

    async def scrape_all(self) -> List[Dict]:
        """Scrape all investing.com commodities"""
        results = await asyncio.gather(
            *[self._fetch_investing(cid) for cid in self.COMMODITY_IDS.values()],
            return_exceptions=True,
        )

        return [r for r in results if r]


class MetalsPriceAPI:
    """Use metals.price API for precious metals"""

    async def fetch_gold_silver(self) -> List[Dict]:
        """Fetch gold and silver spot prices"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.metals.live/api/v1/spot"
                headers = {"User-Agent": "Mozilla/5.0"}

                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        results = []
                        for item in data:
                            metal = item.get("metal", "").upper()
                            if metal in ["XAU", "GOLD"]:
                                results.append(
                                    {
                                        "symbol": "GOLD",
                                        "exchange": "SPOT",
                                        "close": item.get("price", 0),
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )
                            elif metal in ["XAG", "SILVER"]:
                                results.append(
                                    {
                                        "symbol": "SILVER",
                                        "exchange": "SPOT",
                                        "close": item.get("price", 0),
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )

                        return results
        except Exception as e:
            logger.debug(f"Metals API failed: {e}")

        return []


class IBKRCommodityScraper:
    """Scrape via Indian Bank rates for conversion"""

    async def get_inr_conversion(self) -> float:
        """Get USD to INR conversion rate"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.exchangerate.host/latest?base=USD&symbols=INR"
                headers = {"User-Agent": "Mozilla/5.0"}

                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("rates", {}).get("INR", 83.0)
        except Exception as e:
            logger.debug(f"INR conversion failed: {e}")

        return 83.0


class UnifiedCommodityScraper:
    """Unified scraper that combines multiple sources"""

    async def scrape_all_commodities(self) -> List[Dict]:
        """Scrape from all available sources"""
        all_prices = []

        yahoo = YahooFinanceCommodityScraper()
        yahoo_prices = await yahoo.scrape_all()
        all_prices.extend(yahoo_prices)

        mcx = MCXIndiaScraper()
        mcx_prices = await mcx.scrape_all()
        all_prices.extend(mcx_prices)

        metals = MetalsPriceAPI()
        metal_prices = await metals.fetch_gold_silver()
        all_prices.extend(metal_prices)

        dedup = {}
        for p in all_prices:
            sym = p.get("symbol", "")
            if sym and sym not in dedup:
                dedup[sym] = p
            elif sym in dedup:
                if p.get("close") and not dedup[sym].get("close"):
                    dedup[sym] = p

        return list(dedup.values())

    async def scrape_gold(self) -> Dict:
        """Get gold prices from all sources"""
        result = {
            "symbol": "GOLD",
            "sources": [],
            "timestamp": datetime.now().isoformat(),
        }

        yahoo = YahooFinanceCommodityScraper()
        ydata = await yahoo._fetch_yahoo("GC=F")
        if ydata:
            result["sources"].append({"source": "yahoo", "data": ydata})
            result["close_usd"] = ydata.get("close")

        metals = MetalsPriceAPI()
        metals_data = await metals.fetch_gold_silver()
        for m in metals_data:
            if m["symbol"] == "GOLD":
                result["sources"].append({"source": "metals.live", "data": m})
                if not result.get("close_usd"):
                    result["close_usd"] = m.get("close")

        ibkr = IBKRCommodityScraper()
        inr = await ibkr.get_inr_conversion()
        result["inr_conversion"] = inr

        if result.get("close_usd"):
            result["close_inr"] = result["close_usd"] * inr
            result["close"] = result["close_usd"] * 10
            result["unit"] = "10 gm"

        return result

    async def scrape_silver(self) -> Dict:
        """Get silver prices"""
        result = {
            "symbol": "SILVER",
            "sources": [],
            "timestamp": datetime.now().isoformat(),
        }

        yahoo = YahooFinanceCommodityScraper()
        ydata = await yahoo._fetch_yahoo("SI=F")
        if ydata:
            result["sources"].append({"source": "yahoo", "data": ydata})
            result["close_usd"] = ydata.get("close")

        metals = MetalsPriceAPI()
        metals_data = await metals.fetch_gold_silver()
        for m in metals_data:
            if m["symbol"] == "SILVER":
                result["sources"].append({"source": "metals.live", "data": m})
                if not result.get("close_usd"):
                    result["close_usd"] = m.get("close")

        ibkr = IBKRCommodityScraper()
        inr = await ibkr.get_inr_conversion()
        result["inr_conversion"] = inr

        if result.get("close_usd"):
            result["close_inr"] = result["close_usd"] * inr * 1000
            result["close"] = result["close_usd"] * 1000
            result["unit"] = "1 kg"

        return result

    async def scrape_crude(self) -> Dict:
        """Get crude oil prices"""
        result = {
            "symbol": "CRUDEOIL",
            "sources": [],
            "timestamp": datetime.now().isoformat(),
        }

        yahoo = YahooFinanceCommodityScraper()
        ydata = await yahoo._fetch_yahoo("CL=F")
        if ydata:
            result["sources"].append({"source": "yahoo", "data": ydata})
            result["close_usd"] = ydata.get("close")

        mcx = MCXIndiaScraper()
        mcx_data = await mcx._fetch_mcx_realtime("CRUDEOIL")
        if mcx_data:
            result["sources"].append({"source": "mcx", "data": mcx_data})

        ibkr = IBKRCommodityScraper()
        inr = await ibkr.get_inr_conversion()
        result["inr_conversion"] = inr

        if result.get("close_usd"):
            result["close_inr"] = result["close_usd"] * inr * 100
            result["close"] = result["close_usd"] * 100
            result["unit"] = "100 bbl"

        return result


async def scrape_all_commodities():
    """Main function to scrape all commodities"""
    scraper = UnifiedCommodityScraper()
    return await scraper.scrape_all_commodities()


async def scrape_gold_prices():
    """Scrape gold specifically"""
    scraper = UnifiedCommodityScraper()
    return await scraper.scrape_gold()


async def scrape_silver_prices():
    """Scrape silver specifically"""
    scraper = UnifiedCommodityScraper()
    return await scraper.scrape_silver()


async def scrape_crude_prices():
    """Scrape crude oil specifically"""
    scraper = UnifiedCommodityScraper()
    return await scraper.scrape_crude()


if __name__ == "__main__":

    async def main():
        print("Scraping commodities...")
        prices = await scrape_all_commodities()
        print(f"Found {len(prices)} commodity prices")

        for p in prices:
            print(f"  {p['symbol']}: ${p.get('close', 'N/A')}")

        gold = await scrape_gold_prices()
        print(f"\nGold: ${gold.get('close_usd')} = ₹{gold.get('close_inr')}")

    asyncio.run(main())
