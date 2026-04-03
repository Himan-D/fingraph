"""
RSS Feed Scraper for Indian Financial News
"""

import feedparser
import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
NSE_STATIC_RSS_INDEX_URL = "https://www.nseindia.com/static/rss-feed"


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
    "NSE Corporate Actions": "https://www.nseindia.com/api/corporate-announcements?index=equities",
    "BSE Announcements": "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active",
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

    def __init__(self):
        self._nse_static_feed_cache: Dict[str, str] = {}

    async def _discover_nse_static_rss_feeds(self) -> Dict[str, str]:
        """Discover RSS/XML feed URLs listed on the NSE static RSS index page."""
        if self._nse_static_feed_cache:
            return dict(self._nse_static_feed_cache)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.nseindia.com/",
        }

        discovered: Dict[str, str] = {}
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    await session.get("https://www.nseindia.com", headers=headers)
                except Exception:
                    pass

                async with session.get(
                    NSE_STATIC_RSS_INDEX_URL,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=35),
                ) as resp:
                    if resp.status != 200:
                        return {}

                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")

                    for a in soup.find_all("a", href=True):
                        absolute_url = urljoin(NSE_STATIC_RSS_INDEX_URL, a.get("href", "").strip())
                        lowered = absolute_url.lower()
                        if "/content/rss/" not in lowered or not lowered.endswith(".xml"):
                            continue

                        feed_slug = absolute_url.rsplit("/", 1)[-1].replace(".xml", "")
                        feed_name = f"NSE RSS {feed_slug.replace('_', ' ').title()}"
                        discovered[feed_name] = absolute_url
        except Exception as e:
            logger.debug(f"Unable to discover NSE static RSS feeds: {e}")
            return {}

        self._nse_static_feed_cache = discovered
        return dict(discovered)

    def _entry_to_item(self, entry: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Normalize feedparser entry to internal news shape."""
        return {
            "headline": entry.get("title", "") or "",
            "summary": entry.get("summary", "") or entry.get("description", "") or "",
            "source": source,
            "url": entry.get("link", "") or "",
            "published_at": entry.get("published", datetime.now().isoformat()),
        }

    async def _fetch_feed(self, name: str, url: str) -> List[Dict]:
        """Fetch a single RSS feed"""
        news = []
        try:
            # Use feedparser for RSS
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(
                None,
                lambda: feedparser.parse(
                    url,
                    request_headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/rss+xml, application/xml, text/xml",
                        "Referer": "https://www.google.com/",
                    },
                ),
            )

            if feed.entries:
                for entry in feed.entries:  # No limit - fetch all
                    news.append(self._entry_to_item(entry, name))
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
                "Referer": "https://www.google.com/",
            }

            # JSON API sources need API-friendly headers.
            if "/api/" in url:
                headers["Accept"] = "application/json, text/plain, */*"
                headers["X-Requested-With"] = "XMLHttpRequest"

            if "bseindia.com" in url:
                headers["Referer"] = "https://www.bseindia.com/"

            if "nseindia.com" in url:
                headers["Referer"] = "https://www.nseindia.com/"
                headers["Origin"] = "https://www.nseindia.com"

            async with aiohttp.ClientSession() as session:
                # NSE endpoints require cookie warm-up.
                if "nseindia.com" in url:
                    try:
                        await session.get("https://www.nseindia.com", headers=headers)
                        await session.get("https://www.nseindia.com/api/allIndices", headers=headers)
                    except Exception:
                        pass

                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=35)
                ) as resp:
                    if resp.status == 200:
                        content_type = (resp.headers.get("Content-Type") or "").lower()

                        # JSON mode (e.g., NSE corporate announcements API)
                        if "application/json" in content_type or "/api/" in url:
                            try:
                                body_json = await resp.text()
                                payload = json.loads(body_json)

                                if isinstance(payload, list):
                                    rows = payload
                                elif isinstance(payload, dict):
                                    rows = (
                                        payload.get("data")
                                        or payload.get("Data")
                                        or payload.get("Table")
                                        or payload.get("items")
                                        or []
                                    )
                                else:
                                    rows = []

                                for row in rows[:500]:
                                    if not isinstance(row, dict):
                                        continue
                                    title = (
                                        row.get("desc")
                                        or row.get("subject")
                                        or row.get("headline")
                                        or row.get("Scrip_Name")
                                        or row.get("Issuer_Name")
                                        or row.get("symbol")
                                        or ""
                                    )
                                    if title:
                                        news.append(
                                            {
                                                "headline": str(title).strip(),
                                                "summary": str(
                                                    row.get("details")
                                                    or row.get("attchmntText")
                                                    or row.get("INDUSTRY")
                                                    or row.get("Status")
                                                    or ""
                                                ).strip(),
                                                "source": name,
                                                "url": row.get("attchmntFile")
                                                or row.get("url")
                                                or row.get("NSURL")
                                                or url,
                                                "published_at": row.get("an_dt")
                                                or row.get("date")
                                                or datetime.now().isoformat(),
                                            }
                                        )
                                if news:
                                    return news
                            except Exception as e:
                                logger.debug(f"JSON parse fallback failed for {name}: {e}")

                        body = await resp.text()

                        # Try XML/RSS first
                        soup = BeautifulSoup(body, "xml")
                        items = soup.find_all("item")
                        if items:
                            for item in items:
                                title = item.find("title")
                                link = item.find("link")
                                desc = item.find("description")
                                pub_date = item.find("pubDate")

                                if title:
                                    news.append(
                                        {
                                            "headline": title.get_text(strip=True),
                                            "summary": desc.get_text(strip=True)
                                            if desc
                                            else "",
                                            "source": name,
                                            "url": link.get_text(strip=True)
                                            if link
                                            else "",
                                            "published_at": pub_date.get_text(strip=True)
                                            if pub_date
                                            else datetime.now().isoformat(),
                                        }
                                    )
                            return news

                        # HTML fallback (BSE endpoint returns HTML in current behavior)
                        html_soup = BeautifulSoup(body, "html.parser")
                        for a in html_soup.find_all("a", href=True):
                            text = a.get_text(strip=True)
                            href = a.get("href", "")
                            if text and len(text) > 12:
                                news.append(
                                    {
                                        "headline": text,
                                        "summary": "",
                                        "source": name,
                                        "url": href,
                                        "published_at": datetime.now().isoformat(),
                                    }
                                )
                        if news:
                            return news[:200]
        except Exception as e:
            logger.debug(f"Aiohttp fetch {name} failed: {e}")

        return news

    async def get_all_rss_news(self) -> List[Dict]:
        """Fetch news from all RSS feeds"""
        feed_map = dict(RSS_FEEDS)

        # Dynamically add all NSE RSS feeds listed on the static RSS index page.
        feed_map.update(await self._discover_nse_static_rss_feeds())

        tasks = []
        for name, url in feed_map.items():
            tasks.append(self._fetch_feed(name, url))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_news = []
        seen = set()

        for (name, url), result in zip(feed_map.items(), results):
            items: List[Dict[str, Any]] = []
            if isinstance(result, list):
                items = result

            # Automatic fallback path for feeds blocked by feedparser/NSE bot checks.
            if not items:
                try:
                    items = await self._fetch_with_aiohttp(name, url)
                except Exception:
                    items = []

            for item in items:
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
