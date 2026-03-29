"""
RSS Feed Scraper for Indian Financial News
"""

import feedparser
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# Major Indian Financial RSS Feeds
RSS_FEEDS = {
    # News
    "Money Control": "https://www.moneycontrol.com/rss/mc_topnews.xml",
    "Economic Times": "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
    "Business Standard": "https://www.business-standard.com/rss/rssfeed.xml",
    "Financial Express": "https://www.financialexpress.com/feed/",
    "Live Mint": "https://www.livemint.com/rss/news",
    "NDTV Profit": "https://feeds.feedburner.com/ndtvprofit-topstories",
    "CNBC TV18": "https://www.cnbctv18.com/rssfeed.xml",
    "Zee Business": "https://www.zeebiz.com/rssfeed.xml",
    "Screener.in": "https://www.screener.in/rss/",
    "Investing.com India": "https://in.investing.com/rss/news.rss",
    "Yahoo Finance India": "https://finance.yahoo.com/news/rssindex",
    "Bloomberg Quint": "https://www.bloombergquint.com/rssfeed",
    "Google Finance": "https://news.google.com/rss/search?q=Indian+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
    # Corporate Actions & Announcements
    "NSE Corporate Actions": "https://www.nseindia.com/corporate/corpinfo_ann.xml",
    "BSE Announcements": "https://api.bseindia.com/RssBSEPressRelease.aspx?Topic=2",
    # Economy & Markets
    "ET Markets": "https://economictimes.indiatimes.com/markets/rssfeed.cms",
    "ET Economy": "https://economictimes.indiatimes.com/economy/rssfeed.cms",
    # International
    "Reuters Business": "https://www.reutersagency.com/feed/?best-topics=business-finance",
    "WSJ Markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "FT Markets": "https://www.ft.com/rss/home",
}


class RSSScraper:
    """Scrape financial news from RSS feeds"""

    async def _fetch_feed(self, name: str, url: str) -> List[Dict]:
        """Fetch a single RSS feed"""
        news = []
        try:
            # Use feedparser for RSS
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)

            if feed.entries:
                for entry in feed.entries:  # No limit - fetch all
                    news.append(
                        {
                            "headline": entry.get("title", ""),  # No limit
                            "summary": entry.get("summary", ""),  # No limit
                            "source": name,
                            "url": entry.get("link", ""),
                            "published_at": entry.get(
                                "published", datetime.now().isoformat()
                            ),
                        }
                    )
        except Exception as e:
            logger.debug(f"RSS feed {name} failed: {e}")

        return news

    async def _fetch_with_aiohttp(self, name: str, url: str) -> List[Dict]:
        """Fallback: Fetch RSS with aiohttp"""
        news = []
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/rss+xml, application/xml, text/xml",
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "xml")

                        items = soup.find_all("item")  # No limit - fetch all
                        for item in items:
                            title = item.find("title")
                            link = item.find("link")
                            desc = item.find("description")
                            pub_date = item.find("pubDate")

                            if title:
                                news.append(
                                    {
                                        "headline": title.get_text(
                                            strip=True
                                        ),  # No limit
                                        "summary": desc.get_text(strip=True)
                                        if desc
                                        else "",  # No limit
                                        "source": name,
                                        "url": link.get_text(strip=True)
                                        if link
                                        else "",
                                        "published_at": pub_date.get_text(strip=True)
                                        if pub_date
                                        else datetime.now().isoformat(),
                                    }
                                )
        except Exception as e:
            logger.debug(f"Aiohttp fetch {name} failed: {e}")

        return news

    async def get_all_rss_news(self) -> List[Dict]:
        """Fetch news from all RSS feeds"""
        tasks = []
        for name, url in RSS_FEEDS.items():
            tasks.append(self._fetch_feed(name, url))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_news = []
        seen = set()

        for result in results:
            if isinstance(result, list):
                for item in result:
                    headline = item.get("headline", "")[:100]
                    if headline and headline not in seen:
                        seen.add(headline)
                        all_news.append(item)

        return all_news  # No limit - return all


# Additional market research sources
MARKET_RESEARCH_SOURCES = {
    # NSE/BSE Announcements
    "NSE Corporate Actions": "https://www.nseindia.com/corporate/corpinfo_announcements.jsp?symbol=RELIANCE",
    "BSE Corporate Actions": "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active",
    # Market Data
    "NSE Live": "https://www.nseindia.com/",
    "BSE Live": "https://www.bseindia.com/",
    # Stock Screens
    "Screener.in": "https://www.screener.in/",
    "Trendlyne": "https://trendlyne.com/",
    "StockEdge": "https://www.stockedge.com/",
    # Financial Data
    "Tickertape": "https://www.tickertape.in/",
    "Morningstar India": "https://www.morningstar.in/",
    # Brokerage Reports
    "Motilal Oswal": "https://www.motilaloswal.com/",
    "ICICI Direct": "https://www.icicidirect.com/",
    "HDFC Securities": "https://www.hdfcsec.com/",
    # Global Markets
    "Reuters India": "https://www.reuters.com/place/india",
    "Bloomberg India": "https://www.bloomberg.com/india",
}


async def get_market_news():
    """Get comprehensive market news"""
    rss_scraper = RSSScraper()
    news = await rss_scraper.get_all_rss_news()
    return news


if __name__ == "__main__":
    import json

    news = asyncio.run(get_market_news())
    print(f"Found {len(news)} news items")
    for item in news[:5]:
        print(f"- {item['headline'][:60]}... ({item['source']})")
