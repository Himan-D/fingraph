"""
Comprehensive Financial Data Scraper - All sources
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import feedparser
import json

logger = logging.getLogger(__name__)


class ComprehensiveScraper:
    """Scrape data from all financial sources"""

    def __init__(self):
        self.session = None

    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/html, application/xml",
                }
            )
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()

    # ==================== YAHOO FINANCE ====================
    async def scrape_yahoo_quote(self, symbol: str) -> Dict:
        """Get quote from Yahoo Finance"""
        try:
            session = await self.get_session()
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range=5d"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data.get("chart", {}).get("result", [])
                    if result:
                        meta = result[0].get("meta", {})
                        return {
                            "source": "Yahoo Finance",
                            "symbol": symbol,
                            "price": meta.get("regularMarketPrice"),
                            "change": meta.get("regularMarketChange"),
                            "pct_change": meta.get("regularMarketChangePercent"),
                            "volume": meta.get("regularMarketVolume"),
                            "market_cap": meta.get("marketCap"),
                        }
        except Exception as e:
            logger.debug(f"Yahoo quote failed for {symbol}: {e}")
        return {}

    async def scrape_yahoo_historical(self, symbol: str, days: int = 365) -> List[Dict]:
        """Get historical data from Yahoo"""
        try:
            session = await self.get_session()
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?interval=1d&range={days}d"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data.get("chart", {}).get("result", [])
                    if result:
                        result = result[0]
                        timestamps = result.get("timestamp", [])
                        quote = result.get("indicators", {}).get("quote", [{}])[0]
                        return [
                            {
                                "symbol": symbol,
                                "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
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
                            for i, ts in enumerate(timestamps)
                        ]
        except Exception as e:
            logger.debug(f"Yahoo historical failed: {e}")
        return []

    async def scrape_yahoo_options(self, symbol: str) -> Dict:
        """Get options data"""
        try:
            session = await self.get_session()
            url = f"https://query1.finance.yahoo.com/v7/finance/options/{symbol}.NS"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "Yahoo Finance",
                        "symbol": symbol,
                        "options": data.get("optionChain", {}).get("result", []),
                    }
        except Exception as e:
            logger.debug(f"Yahoo options failed: {e}")
        return {}

    # ==================== SCREENER.IN ====================
    async def scrape_screener(self, symbol: str) -> Dict:
        """Scrape Screener.in for financials"""
        try:
            session = await self.get_session()
            url = f"https://www.screener.in/company/{symbol}/"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Extract key metrics
                    price = soup.select_one(".price")
                    mcap = soup.select_one(".market-cap")
                    pe = soup.select_one(".pe-ratio")

                    return {
                        "source": "Screener.in",
                        "symbol": symbol,
                        "price": price.get_text(strip=True) if price else "",
                        "market_cap": mcap.get_text(strip=True) if mcap else "",
                        "pe_ratio": pe.get_text(strip=True) if pe else "",
                    }
        except Exception as e:
            logger.debug(f"Screener failed: {e}")
        return {}

    # ==================== MONEY CONTROL ====================
    async def scrape_moneycontrol(self, symbol: str) -> Dict:
        """Scrape MoneyControl"""
        try:
            session = await self.get_session()
            url = f"https://www.moneycontrol.com/stocks/cprice.php?sccode={symbol}"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")

                    price_elem = soup.select_one(".price")
                    return {
                        "source": "MoneyControl",
                        "symbol": symbol,
                        "price": price_elem.get_text(strip=True) if price_elem else "",
                    }
        except Exception as e:
            logger.debug(f"MoneyControl failed: {e}")
        return {}

    # ==================== NSE DIRECT ====================
    async def scrape_nse_quote(self, symbol: str) -> Dict:
        """Get quote from NSE"""
        try:
            session = await self.get_session()
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "source": "NSE",
                        "symbol": symbol,
                        "data": data,
                    }
        except Exception as e:
            logger.debug(f"NSE quote failed: {e}")
        return {}

    async def scrape_nse_fno(self, symbol: str) -> Dict:
        """Get F&O data"""
        try:
            session = await self.get_session()
            url = f"https://www.nseindia.com/api/fiidiQuote?symbol={symbol}"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"source": "NSE F&O", "symbol": symbol, "data": data}
        except Exception as e:
            logger.debug(f"NSE F&O failed: {e}")
        return {}

    # ==================== MARKET DATA ====================
    async def scrape_market_status(self) -> Dict:
        """Get market status"""
        try:
            session = await self.get_session()
            url = "https://www.nseindia.com/api/marketStatus"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"source": "NSE", "market_status": data}
        except Exception as e:
            logger.debug(f"Market status failed: {e}")
        return {}

    async def scrape_fii_dii_data(self) -> Dict:
        """Get FII/DII data"""
        try:
            session = await self.get_session()
            url = "https://www.nseindia.com/api/fiiAndDiiMarketActivity"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"source": "NSE", "fii_dii": data}
        except Exception as e:
            logger.debug(f"FII/DII failed: {e}")
        return {}

    async def scrape_bulk_block_deals(self) -> List[Dict]:
        """Get bulk and block deals"""
        deals = []
        try:
            session = await self.get_session()
            url = "https://www.nseindia.com/api/bulk-deals"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    deals.extend(data)
        except Exception as e:
            logger.debug(f"Bulk deals failed: {e}")
        return deals

    # ==================== CORPORATE ACTIONS ====================
    async def scrape_corporate_actions(self, symbol: str) -> List[Dict]:
        """Get corporate actions"""
        try:
            session = await self.get_session()
            url = f"https://www.nseindia.com/api/corporates-historical?symbol={symbol}&segment=Equity"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data if isinstance(data, list) else []
        except Exception as e:
            logger.debug(f"Corporate actions failed: {e}")
        return []

    async def scrape_dividends(self, symbol: str) -> List[Dict]:
        """Get dividend history"""
        try:
            session = await self.get_session()
            url = f"https://www.nseindia.com/api/dividend-announcement?symbol={symbol}"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data if isinstance(data, list) else []
        except Exception as e:
            logger.debug(f"Dividends failed: {e}")
        return []

    # ==================== SHORT SELLING ====================
    async def scrape_short_interest(self) -> List[Dict]:
        """Get short selling data"""
        try:
            session = await self.get_session()
            url = "https://www.nseindia.com/api/short-selling"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data if isinstance(data, list) else []
        except Exception as e:
            logger.debug(f"Short interest failed: {e}")
        return []

    # ==================== OPTIONS DATA ====================
    async def scrape_option_chain(self, symbol: str = "NIFTY") -> Dict:
        """Get option chain"""
        try:
            session = await self.get_session()
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"source": "NSE", "symbol": symbol, "data": data}
        except Exception as e:
            logger.debug(f"Option chain failed: {e}")
        return {}

    async def scrape_pcr(self, symbol: str = "NIFTY") -> Dict:
        """Get put-call ratio"""
        try:
            session = await self.get_session()
            url = f"https://www.nseindia.com/api/put-call-ratio?symbol={symbol}"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"source": "NSE", "pcr": data}
        except Exception as e:
            logger.debug(f"PCR failed: {e}")
        return {}

    # ==================== INSIDER TRADING ====================
    async def scrape_insider_trading(self, symbol: str) -> List[Dict]:
        """Get insider trading data"""
        try:
            session = await self.get_session()
            url = f"https://www.nseindia.com/api/insider-trading?symbol={symbol}"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data if isinstance(data, list) else []
        except Exception as e:
            logger.debug(f"Insider trading failed: {e}")
        return []

    # ==================== PROMOTER HOLDING ====================
    async def scrape_promoter_holding(self, symbol: str) -> Dict:
        """Get promoter holding"""
        try:
            session = await self.get_session()
            url = f"https://www.nseindia.com/api/promoter-holding?symbol={symbol}"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"source": "NSE", "promoter_holding": data}
        except Exception as e:
            logger.debug(f"Promoter holding failed: {e}")
        return {}

    # ==================== NEWS ====================
    async def scrape_news_sources(self) -> List[Dict]:
        """Scrape all news sources"""
        news = []

        rss_feeds = [
            (
                "Economic Times",
                "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
            ),
            ("MoneyControl", "https://www.moneycontrol.com/rss/mc_topnews.xml"),
            ("Business Standard", "https://www.business-standard.com/rss/rssfeed.xml"),
            ("Live Mint", "https://www.livemint.com/rss/news"),
            ("CNBC TV18", "https://www.cnbctv18.com/rssfeed.xml"),
            ("NDTV Profit", "https://feeds.feedburner.com/ndtvprofit-topstories"),
            ("Zee Business", "https://www.zeebiz.com/rssfeed.xml"),
            ("Investing.com", "https://in.investing.com/rss/news.rss"),
            ("Screener.in", "https://www.screener.in/rss/"),
        ]

        for name, url in rss_feeds:
            try:
                session = await self.get_session()
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        feed = feedparser.parse(text)
                        for entry in feed.entries[:20]:
                            news.append(
                                {
                                    "headline": entry.get("title", ""),
                                    "summary": entry.get("summary", ""),
                                    "source": name,
                                    "url": entry.get("link", ""),
                                    "published": entry.get("published", ""),
                                }
                            )
            except Exception as e:
                logger.debug(f"News feed {name} failed: {e}")

        return news

    # ==================== COMPREHENSIVE SCRAPE ====================
    async def scrape_all_for_symbol(self, symbol: str) -> Dict:
        """Scrape all data for a symbol"""
        results = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "sources": {},
        }

        # Yahoo
        results["sources"]["yahoo_quote"] = await self.scrape_yahoo_quote(symbol)
        results["sources"]["yahoo_historical"] = await self.scrape_yahoo_historical(
            symbol, 30
        )

        # NSE
        results["sources"]["nse_quote"] = await self.scrape_nse_quote(symbol)
        results["sources"]["nse_fno"] = await self.scrape_nse_fno(symbol)

        # Corporate
        results["sources"]["corporate_actions"] = await self.scrape_corporate_actions(
            symbol
        )
        results["sources"]["dividends"] = await self.scrape_dividends(symbol)

        # Holdings
        results["sources"]["promoter_holding"] = await self.scrape_promoter_holding(
            symbol
        )
        results["sources"]["insider_trading"] = await self.scrape_insider_trading(
            symbol
        )

        return results


async def scrape_all_companies():
    """Scrape data for all companies in DB"""
    from db.postgres import AsyncSessionLocal
    from db.postgres_models import Company
    from sqlalchemy import select

    scraper = ComprehensiveScraper()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company).limit(100))
        companies = result.scalars().all()

        all_data = []
        for company in companies:
            print(f"Scraping {company.symbol}...")
            data = await scraper.scrape_all_for_symbol(company.symbol)
            all_data.append(data)
            await asyncio.sleep(0.5)  # Rate limiting

        print(f"Scraped {len(all_data)} companies")

    await scraper.close()
    return all_data


async def scrape_market_overview():
    """Scrape all market overview data"""
    scraper = ComprehensiveScraper()

    data = {
        "market_status": await scraper.scrape_market_status(),
        "fii_dii": await scraper.scrape_fii_dii_data(),
        "bulk_deals": await scraper.scrape_bulk_block_deals(),
        "short_interest": await scraper.scrape_short_interest(),
        "option_chain": await scraper.scrape_option_chain("NIFTY"),
        "news": await scraper.scrape_news_sources(),
    }

    await scraper.close()
    return data


if __name__ == "__main__":
    import json

    data = asyncio.run(scrape_market_overview())
    print(json.dumps(data, indent=2))
