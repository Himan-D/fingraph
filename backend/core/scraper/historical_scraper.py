"""
Historical Data Scraper - Stock prices, index data using Yahoo Finance API
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import json

logger = logging.getLogger(__name__)


class HistoricalDataScraper:
    """Scrape historical stock data from Yahoo Finance"""

    async def get_yahoo_historical(self, symbol: str, days: int = 365) -> List[Dict]:
        """Get historical data from Yahoo Finance Chart API"""
        data = []
        try:
            # Use .NS suffix for NSE stocks
            if not symbol.endswith(".NS") and not symbol.startswith("^"):
                yahoo_symbol = f"{symbol}.NS"
            else:
                yahoo_symbol = symbol

            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval=1d&range={days}d"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        json_data = await resp.json()
                        result = json_data.get("chart", {}).get("result", [])

                        if result:
                            result = result[0]
                            timestamps = result.get("timestamp", [])
                            quote = result.get("indicators", {}).get("quote", [{}])[0]

                            for i, ts in enumerate(timestamps):
                                data.append(
                                    {
                                        "symbol": symbol,
                                        "date": datetime.fromtimestamp(ts).strftime(
                                            "%Y-%m-%d"
                                        ),
                                        "open": quote.get("open", [0])[i]
                                        if quote.get("open")
                                        else 0,
                                        "high": quote.get("high", [0])[i]
                                        if quote.get("high")
                                        else 0,
                                        "low": quote.get("low", [0])[i]
                                        if quote.get("low")
                                        else 0,
                                        "close": quote.get("close", [0])[i]
                                        if quote.get("close")
                                        else 0,
                                        "volume": quote.get("volume", [0])[i]
                                        if quote.get("volume")
                                        else 0,
                                    }
                                )
        except Exception as e:
            logger.warning(f"Yahoo historical failed for {symbol}: {e}")

        return data

    async def get_current_quote(self, symbol: str) -> Dict:
        """Get current quote for a symbol"""
        try:
            if not symbol.endswith(".NS") and not symbol.startswith("^"):
                yahoo_symbol = f"{symbol}.NS"
            else:
                yahoo_symbol = symbol

            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval=1d&range=1d"

            headers = {"User-Agent": "Mozilla/5.0"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        json_data = await resp.json()
                        result = json_data.get("chart", {}).get("result", [])

                        if result:
                            result = result[0]
                            meta = result.get("meta", {})
                            quote = result.get("indicators", {}).get("quote", [{}])[0]

                            return {
                                "symbol": symbol,
                                "price": meta.get("regularMarketPrice", 0),
                                "change": meta.get("regularMarketChange", 0),
                                "pct_change": meta.get("regularMarketChangePercent", 0),
                                "open": quote.get("open", [0])[0]
                                if quote.get("open")
                                else 0,
                                "high": quote.get("high", [0])[0]
                                if quote.get("high")
                                else 0,
                                "low": quote.get("low", [0])[0]
                                if quote.get("low")
                                else 0,
                                "volume": quote.get("volume", [0])[0]
                                if quote.get("volume")
                                else 0,
                            }
        except Exception as e:
            logger.debug(f"Quote failed for {symbol}: {e}")

        return None

    async def get_index_data(self, index: str = "NIFTY 50") -> Dict:
        """Get index data"""
        index_map = {
            "NIFTY 50": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "NIFTY IT": "^CNXIT",
            "NIFTY AUTO": "^CNXAUTO",
            "NIFTY METAL": "^CNXMETAL",
            "NIFTY PHARMA": "^CNXPHARMA",
            "NIFTY FMCG": "^CNXFMCG",
            "NIFTY ENERGY": "^CNXENERGY",
            "BSE SENSEX": "^BSESN",
        }

        yahoo_symbol = index_map.get(index, "^NSEI")

        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval=1d&range=5d"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        json_data = await resp.json()
                        result = json_data.get("chart", {}).get("result", [])

                        if result:
                            result = result[0]
                            meta = result.get("meta", {})
                            return {
                                "name": index,
                                "price": meta.get("regularMarketPrice", 0),
                                "change": meta.get("regularMarketChange", 0),
                                "pct_change": meta.get("regularMarketChangePercent", 0),
                            }
        except Exception as e:
            logger.warning(f"Index data failed for {index}: {e}")

        return None


async def scrape_all_historical():
    """Scrape historical data for all companies"""
    from db.postgres import AsyncSessionLocal
    from db.postgres_models import Company, StockQuote
    from sqlalchemy import select

    scraper = HistoricalDataScraper()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company).limit(50))
        companies = result.scalars().all()

        total_scraped = 0
        for company in companies:
            try:
                historical = await scraper.get_yahoo_historical(
                    company.symbol, days=365
                )

                for h in historical:
                    try:
                        quote = StockQuote(
                            company_id=company.id,
                            timestamp=datetime.strptime(h["date"], "%Y-%m-%d"),
                            open=h.get("open", 0),
                            high=h.get("high", 0),
                            low=h.get("low", 0),
                            close=h.get("close", 0),
                            volume=h.get("volume", 0),
                        )
                        session.add(quote)
                    except Exception as e:
                        pass

                total_scraped += len(historical)
                logger.info(f"Scraped {len(historical)} days for {company.symbol}")

            except Exception as e:
                logger.warning(f"Failed {company.symbol}: {e}")

        await session.commit()
        logger.info(f"Total historical data scraped: {total_scraped} records")


async def scrape_all_quotes():
    """Scrape current quotes for all companies"""
    from db.postgres import AsyncSessionLocal
    from db.postgres_models import Company, StockQuote
    from sqlalchemy import select

    scraper = HistoricalDataScraper()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company).limit(50))
        companies = result.scalars().all()

        for company in companies:
            try:
                quote_data = await scraper.get_current_quote(company.symbol)
                if quote_data:
                    quote = StockQuote(
                        company_id=company.id,
                        timestamp=datetime.now(),
                        open=quote_data.get("open", 0),
                        high=quote_data.get("high", 0),
                        low=quote_data.get("low", 0),
                        close=quote_data.get("price", 0),
                        volume=quote_data.get("volume", 0),
                    )
                    session.add(quote)
            except Exception as e:
                logger.debug(f"Quote failed for {company.symbol}: {e}")

        await session.commit()
        logger.info("Updated current quotes")


if __name__ == "__main__":
    asyncio.run(scrape_all_quotes())
