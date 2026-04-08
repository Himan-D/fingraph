import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

COMMODITY_KEYWORDS = {
    "GOLD": [
        "gold",
        "gold rate",
        "gold price",
        "gold trading",
        "gold futures",
        "sovereign gold",
        "gold loan",
        "gold etf",
        "xauusd",
        "xau",
    ],
    "SILVER": [
        "silver",
        "silver rate",
        "silver price",
        "silver trading",
        "silver futures",
        "silver etf",
        "xagusd",
        "xag",
    ],
    "CRUDEOIL": [
        "crude oil",
        "crude",
        "brent crude",
        "wti crude",
        "crude futures",
        "opec",
        "oil price",
        "oil trading",
        "cl=f",
    ],
    "NATURALGAS": [
        "natural gas",
        "lng",
        "natural gas price",
        "gas price",
        "gas futures",
        "ng=f",
    ],
    "COPPER": ["copper", "copper price", "copper futures", "copper trading", "hg=f"],
    "ALUMINIUM": [
        "aluminum",
        "aluminium",
        "aluminum price",
        "aluminium price",
        "ali=f",
    ],
    "ZINC": ["zinc", "zinc price", "zinc futures"],
    "NICKEL": ["nickel", "nickel price", "nickel futures"],
}


class CommodityStockTwitsScraper:
    """Scrape StockTwits for commodity sentiment - LIVE SOURCE"""

    TICKERS = [
        "GLD",
        "SLV",
        "IAU",
        "SGOL",
        "PSLV",
        "USO",
        "UNG",
        "DBO",
        "COPX",
        "JJU",
        "PPLT",
        "GLD",
    ]

    commodity_map = {
        "GLD": "GOLD",
        "SLV": "SILVER",
        "IAU": "GOLD",
        "SGOL": "GOLD",
        "PSLV": "SILVER",
        "USO": "CRUDEOIL",
        "UNG": "NATURALGAS",
        "DBO": "CRUDEOIL",
        "COPX": "COPPER",
        "JJU": "COPPER",
        "PPLT": "PLATINUM",
    }

    async def scrape_ticker(self, ticker: str) -> List[Dict]:
        """Scrape messages for a ticker - REAL API"""
        messages = []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        messages_data = data.get("messages", [])[:30]

                        for msg in messages_data:
                            sentiment = msg.get("entities", {}).get("sentiment", {})

                            messages.append(
                                {
                                    "text": msg.get("body", ""),
                                    "username": msg.get("user", {}).get("username", ""),
                                    "ticker": ticker,
                                    "commodity": self.commodity_map.get(ticker, ticker),
                                    "sentiment": sentiment.get("basic", ""),
                                    "source": "stocktwits",
                                    "timestamp": msg.get("created_at", ""),
                                }
                            )
        except Exception as e:
            logger.debug(f"StockTwits scrape failed for {ticker}: {e}")

        return messages

    async def scrape_all(self) -> List[Dict]:
        """Scrape all commodity tickers"""
        results = await asyncio.gather(
            *[self.scrape_ticker(t) for t in self.TICKERS],
            return_exceptions=True,
        )

        all_messages = []
        for result in results:
            if isinstance(result, list):
                all_messages.extend(result)

        return all_messages


class TradingViewScraper:
    """Scrape TradingView for commodity social sentiment - LIVE"""

    def _get_commodity_id(self, commodity: str) -> str:
        """Get TradingView symbol ID"""
        mapping = {
            "GOLD": "TVC:GOLD",
            "SILVER": "TVC:SILVER",
            "CRUDEOIL": "TVC:CL",
            "NATURALGAS": "TVC:NG",
            "COPPER": "TVC:COPPER",
            "PLATINUM": "TVC:PLATINUM",
        }
        return mapping.get(commodity.upper(), f"TVC:{commodity.upper()}")

    async def get_sentiment(self, commodity: str) -> Dict:
        """Get TradingView sentiment data"""
        symbol = self._get_commodity_id(commodity)

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0"}

                url = f"https://scanner.tradingview.com/scan?symbols={symbol}"
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.debug(f"TradingView scraper: {e}")

        return {}


class FinvizScraper:
    """Scrape Finviz for commodity ETF sentiment"""

    ETF_MAP = {
        "GOLD": ["GLD", "IAU", "SGOL", "GLDM"],
        "SILVER": ["SLV", "PSLV", "SIVR"],
        "CRUDEOIL": ["USO", "UCO", "DBO"],
        "NATURALGAS": ["UNG", "BOIL", "DRG"],
    }

    async def scrape_etf(self, ticker: str) -> Optional[Dict]:
        """Scrape ETF data from Finviz"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0"}

                url = f"https://finviz.com/quote.ashx?t={ticker}"
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()

                        from bs4 import BeautifulSoup

                        soup = BeautifulSoup(html, "html.parser")

                        price_elem = soup.find("td", string="Price")
                        if price_elem:
                            price_val = price_elem.find_next_sibling("td")
                            if price_val:
                                return {
                                    "ticker": ticker,
                                    "price": price_val.get_text(strip=True),
                                }
        except Exception as e:
            logger.debug(f"Finviz scrape failed for {ticker}: {e}")

        return None


class CommodityRedditScraper:
    """Scrape Reddit for commodity discussions - LIVE"""

    SUBREDDITS = [
        "WallStreetBets",
        "CommodityTrading",
        "Gold",
        "Silverbugs",
        "stocks",
        "investing",
        "options",
        "IndianStocks",
        "nifty50",
    ]

    def _extract_commodities(self, text: str) -> List[str]:
        """Extract commodities from text"""
        text_lower = text.lower()
        commodities = []

        for commodity, keywords in COMMODITY_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    commodities.append(commodity)
                    break

        return commodities

    async def scrape_subreddit(self, subreddit: str) -> List[Dict]:
        """Scrape a subreddit"""
        posts = []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }

                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        children = data.get("data", {}).get("children", [])

                        for child in children[:25]:
                            post = child.get("data", {})

                            title = post.get("title", "")
                            text = post.get("selftext", "")
                            full_text = title + " " + text
                            commodities = self._extract_commodities(full_text)

                            if commodities:
                                posts.append(
                                    {
                                        "title": title,
                                        "text": text[:1000],
                                        "author": post.get("author", ""),
                                        "subreddit": subreddit,
                                        "url": f"https://reddit.com{post.get('permalink', '')}",
                                        "score": post.get("score", 0),
                                        "num_comments": post.get("num_comments", 0),
                                        "commodities": commodities,
                                        "source": "reddit",
                                        "timestamp": datetime.fromtimestamp(
                                            post.get("created_utc", 0)
                                        ).isoformat(),
                                    }
                                )
        except Exception as e:
            logger.debug(f"Reddit scrape failed for {subreddit}: {e}")

        return posts

    async def scrape_all_subreddits(self) -> List[Dict]:
        """Scrape all commodity-related subreddits"""
        results = await asyncio.gather(
            *[self.scrape_subreddit(s) for s in self.SUBREDDITS],
            return_exceptions=True,
        )

        all_posts = []
        for result in results:
            if isinstance(result, list):
                all_posts.extend(result)

        return all_posts

    async def search_commodity(self, commodity: str) -> List[Dict]:
        """Search Reddit for a specific commodity"""
        keywords = COMMODITY_KEYWORDS.get(commodity.upper(), [commodity.lower()])

        results = []
        for sub in self.SUBREDDITS[:5]:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"User-Agent": "Mozilla/5.0"}

                    for kw in keywords[:2]:
                        url = f"https://www.reddit.com/r/{sub}/search.json?q={kw}&sort=hot&limit=25"
                        async with session.get(
                            url,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=15),
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                children = data.get("data", {}).get("children", [])

                                for child in children[:10]:
                                    post = child.get("data", {})
                                    results.append(
                                        {
                                            "title": post.get("title", ""),
                                            "text": post.get("selftext", ""),
                                            "author": post.get("author", ""),
                                            "subreddit": sub,
                                            "url": f"https://reddit.com{post.get('permalink', '')}",
                                            "score": post.get("score", 0),
                                            "commodity": commodity.upper(),
                                            "source": "reddit",
                                            "timestamp": datetime.fromtimestamp(
                                                post.get("created_utc", 0)
                                            ).isoformat(),
                                        }
                                    )
            except Exception as e:
                logger.debug(f"Search failed for {commodity} in {sub}: {e}")

        return results


class XTwitterScraper:
    """Try alternative methods to get commodity discussions"""

    async def scrape_tradingview_widget(self) -> List[Dict]:
        """Scrape TradingView social widget"""
        results = []

        commodities = ["GOLD", "SILVER", "CRUDEOIL"]

        for comm in commodities:
            try:
                from bs4 import BeautifulSoup

                async with aiohttp.ClientSession() as session:
                    headers = {"User-Agent": "Mozilla/5.0"}

                    url = f"https://www.tradingview.com/symbols/{comm.upper()}-USD/"
                    async with session.get(
                        url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            soup = BeautifulSoup(html, "html.parser")

                            ideas = soup.find_all(string=re.compile(r"bullish|bearish"))
                            for idea in ideas[:5]:
                                results.append(
                                    {
                                        "text": idea.parent.get_text(strip=True)
                                        if idea.parent
                                        else idea,
                                        "source": "tradingview",
                                        "commodity": comm,
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )
            except Exception as e:
                logger.debug(f"TradingView scrape failed: {e}")

        return results

    async def scrape_finance_yahoo(self, commodity: str) -> List[Dict]:
        """Scrape Yahoo Finance comments"""
        ticker_map = {
            "GOLD": "GC=F",
            "SILVER": "SI=F",
            "CRUDEOIL": "CL=F",
        }

        ticker = ticker_map.get(commodity.upper())
        if not ticker:
            return []

        results = []

        try:
            from bs4 import BeautifulSoup

            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0"}

                url = f"https://finance.yahoo.com/quote/{ticker}/community"
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")

                        comments = soup.find_all(
                            "p", {"class": re.compile(r"comment")}
                        )[:10]
                        for comment in comments:
                            text = comment.get_text(strip=True)
                            if text and len(text) > 20:
                                results.append(
                                    {
                                        "text": text,
                                        "source": "yahoo-finance",
                                        "commodity": commodity.upper(),
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )
        except Exception as e:
            logger.debug(f"Yahoo Finance scrape failed: {e}")

        return results


class CommoditySentimentAnalyzer:
    """Analyze sentiment for commodities from social data"""

    BULLISH_KEYWORDS = [
        "bullish",
        "buy",
        "long",
        "moon",
        "gain",
        "profit",
        "up",
        "call",
        "beat",
        "higher",
        "rise",
        "rally",
        "surge",
        "breakout",
        "accumulate",
        "overweight",
        "outperform",
        "strong",
        "growth",
        "positive",
        "target",
        "hold",
        "cheap",
        " undervalued",
        "moving up",
        "going up",
        "winner",
        "profit",
        "green",
        "calls",
    ]
    BEARISH_KEYWORDS = [
        "bearish",
        "sell",
        "short",
        "dump",
        "loss",
        "down",
        "put",
        "miss",
        "lower",
        "fall",
        "decline",
        "drop",
        "breakdown",
        "distribution",
        "underweight",
        "underperform",
        "weak",
        "negative",
        "red",
        "stop loss",
        "sold",
        "puts",
        "overvalued",
        "crash",
        "plunge",
        "dump",
    ]

    def analyze(self, text: str, commodity: str) -> Dict:
        """Analyze sentiment for a commodity"""
        if not text:
            return {
                "commodity": commodity,
                "sentiment": "neutral",
                "score": 0,
                "bullish_count": 0,
                "bearish_count": 0,
            }

        text_lower = text.lower()

        bullish = sum(1 for kw in self.BULLISH_KEYWORDS if kw in text_lower)
        bearish = sum(1 for kw in self.BEARISH_KEYWORDS if kw in text_lower)

        if bullish > bearish:
            sentiment = "bullish"
            score = (bullish - bearish) / max(bullish + bearish, 1) * 100
        elif bearish > bullish:
            sentiment = "bearish"
            score = -(bearish - bullish) / max(bullish + bearish, 1) * 100
        else:
            sentiment = "neutral"
            score = 0

        return {
            "commodity": commodity,
            "sentiment": sentiment,
            "score": round(score, 2),
            "bullish_count": bullish,
            "bearish_count": bearish,
        }

    def analyze_batch(self, texts: List[str], commodity: str) -> Dict:
        """Analyze batch of texts"""
        results = [self.analyze(t, commodity) for t in texts if t]

        if not results:
            return {
                "commodity": commodity,
                "sentiment": "neutral",
                "score": 0,
                "total_mentions": 0,
                "bullish_mentions": 0,
                "bearish_mentions": 0,
            }

        total_bullish = sum(r["bullish_count"] for r in results)
        total_bearish = sum(r["bearish_count"] for r in results)

        avg_score = sum(r["score"] for r in results) / len(results)

        return {
            "commodity": commodity,
            "sentiment": "bullish"
            if avg_score > 10
            else "bearish"
            if avg_score < -10
            else "neutral",
            "score": round(avg_score, 2),
            "total_mentions": len(results),
            "bullish_mentions": total_bullish,
            "bearish_mentions": total_bearish,
        }


async def scrape_commodity_social():
    """Main social scraping function for commodities - REAL DATA"""

    stocktwits = CommodityStockTwitsScraper()
    stocktwits_messages = await stocktwits.scrape_all()

    reddit = CommodityRedditScraper()
    reddit_posts = await reddit.scrape_all_subreddits()

    tradingview = XTwitterScraper()
    tradingview_data = await tradingview.scrape_tradingview_widget()

    return {
        "twitter": tradingview_data,
        "reddit": reddit_posts,
        "stocktwits": stocktwits_messages,
    }


async def get_commodity_sentiment(commodity: str) -> Dict:
    """Get sentiment for a specific commodity - REAL DATA"""
    reddit = CommodityRedditScraper()
    posts = await reddit.search_commodity(commodity)

    texts = [p.get("title", "") + " " + p.get("text", "") for p in posts]

    stocktwits = CommodityStockTwitsScraper()
    ticker_map = {
        "GOLD": "GLD",
        "SILVER": "SLV",
        "CRUDEOIL": "USO",
        "NATURALGAS": "UNG",
    }
    ticker = ticker_map.get(commodity.upper(), commodity.upper())
    st_messages = await stocktwits.scrape_ticker(ticker)
    st_texts = [m.get("text", "") for m in st_messages]

    all_texts = texts + st_texts

    if not all_texts:
        return {
            "commodity": commodity,
            "sentiment": "neutral",
            "score": 0,
            "total_mentions": 0,
            "bullish_mentions": 0,
            "bearish_mentions": 0,
        }

    analyzer = CommoditySentimentAnalyzer()
    return analyzer.analyze_batch(all_texts, commodity)


if __name__ == "__main__":

    async def main():
        print("=== Testing Commodity Social Scrapers (REAL DATA) ===")

        # Test StockTwits
        print("\n--- StockTwits ---")
        stocktwits = CommodityStockTwitsScraper()
        st_messages = await stocktwits.scrape_all()
        print(f"Got {len(st_messages)} StockTwits messages")

        # Test Reddit
        print("\n--- Reddit ---")
        reddit = CommodityRedditScraper()
        reddit_posts = await reddit.scrape_all_subreddits()
        print(f"Got {len(reddit_posts)} Reddit posts")

        # Test sentiment
        print("\n=== Sentiment Analysis ===")
        for commodity in ["GOLD", "CRUDEOIL", "SILVER"]:
            sentiment = await get_commodity_sentiment(commodity)
            print(f"{commodity}: {sentiment}")

    asyncio.run(main())
