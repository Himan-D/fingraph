import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import List, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class NewsScraper:
    """Scrape financial news from various sources using crawl4ai API"""

    CRAWL4AI_URL = getattr(settings, "CRAWL4AI_URL", "http://localhost:11202")

    async def _crawl_with_crawl4ai(self, url: str) -> str:
        """Use crawl4ai API to crawl page"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "urls": [url],
                    "css_selector": "h1, h2, h3, h4, h5, h6, p, article, .headline, .title, .news-title, .story-title",
                    "exclude_selector": "script, style, nav, footer, .ad, .advertisement",
                    "word_count_threshold": 10,
                }
                async with session.post(
                    f"{self.CRAWL4AI_URL}/crawl",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("results"):
                            return data["results"][0].get("markdown", "")
        except Exception as e:
            logger.debug(f"Crawl4AI failed for {url}: {e}")
        return ""

    async def _scrape_with_bs(self, url: str, selectors: List[str]) -> List[Dict]:
        """Fallback: Scrape with BeautifulSoup"""
        news = []
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")

                        for selector in selectors:
                            elements = soup.select(selector)
                            for el in elements:
                                text = el.get_text(strip=True)
                                if text and len(text) > 20 and len(text) < 300:
                                    news.append(
                                        {
                                            "headline": text,
                                            "source": url.split("/")[2].replace(
                                                "www.", ""
                                            ),
                                            "url": url,
                                            "published_at": datetime.now().isoformat(),
                                        }
                                    )
        except Exception as e:
            logger.warning(f"BS scrape failed for {url}: {e}")
        return news

    async def scrape_moneycontrol(self) -> List[Dict]:
        """Scrape MoneyControl - Top business news"""
        # Try crawl4ai first
        content = await self._crawl_with_crawl4ai("https://www.moneycontrol.com/")
        if content:
            # Parse headlines from crawled content
            lines = content.split("\n")
            return [
                {
                    "headline": line.strip(),  # No limit
                    "source": "MoneyControl",
                    "url": "https://www.moneycontrol.com/",
                    "published_at": datetime.now().isoformat(),
                }
                for line in lines
                if line.strip() and len(line.strip()) > 20
            ]  # No limit

        # Fallback to BS
        return await self._scrape_with_bs(
            "https://www.moneycontrol.com/",
            ["h2.headline", "h3.headline", ".news_title", ".story_title"],
        )

    async def scrape_ndtv(self) -> List[Dict]:
        """Scrape NDTV Business"""
        content = await self._crawl_with_crawl4ai("https://www.ndtv.com/business")
        if content:
            lines = content.split("\n")
            return [
                {
                    "headline": line.strip(),
                    "source": "NDTV",
                    "url": "https://www.ndtv.com/business",
                    "published_at": datetime.now().isoformat(),
                }
                for line in lines
                if line.strip() and len(line.strip()) > 20
            ]

        return await self._scrape_with_bs(
            "https://www.ndtv.com/business", ["h2.sp-ttl", ".news_itm-ttl", ".newsHdng"]
        )

    async def scrape_screener(self) -> List[Dict]:
        """Scrape Screener.in"""
        content = await self._crawl_with_crawl4ai("https://www.screener.in/")
        if content:
            lines = content.split("\n")
            return [
                {
                    "headline": line.strip(),
                    "source": "Screener.in",
                    "url": "https://www.screener.in/",
                    "published_at": datetime.now().isoformat(),
                }
                for line in lines
                if line.strip() and len(line.strip()) > 20
            ]

        return await self._scrape_with_bs(
            "https://www.screener.in/", ["h1", "h2", ".company-name", ".stock-price"]
        )

    async def scrape_et_now(self) -> List[Dict]:
        """Scrape ET Now"""
        content = await self._crawl_with_crawl4ai("https://www.etnow.in/")
        if content:
            lines = content.split("\n")
            return [
                {
                    "headline": line.strip(),
                    "source": "ET Now",
                    "url": "https://www.etnow.in/",
                    "published_at": datetime.now().isoformat(),
                }
                for line in lines
                if line.strip() and len(line.strip()) > 20
            ]

        return await self._scrape_with_bs(
            "https://www.etnow.in/", ["h1", "h2", ".story-title", ".headline"]
        )

    async def scrape_businesstoday(self) -> List[Dict]:
        """Scrape Business Today"""
        content = await self._crawl_with_crawl4ai("https://www.businesstoday.in/")
        if content:
            lines = content.split("\n")
            return [
                {
                    "headline": line.strip(),
                    "source": "Business Today",
                    "url": "https://www.businesstoday.in/",
                    "published_at": datetime.now().isoformat(),
                }
                for line in lines
                if line.strip() and len(line.strip()) > 20
            ]

        return await self._scrape_with_bs(
            "https://www.businesstoday.in/", ["h1", "h2", ".story-title", ".headline"]
        )

    async def scrape_livemint(self) -> List[Dict]:
        """Scrape Live Mint"""
        content = await self._crawl_with_crawl4ai("https://www.livemint.com/")
        if content:
            lines = content.split("\n")
            return [
                {
                    "headline": line.strip(),
                    "source": "Live Mint",
                    "url": "https://www.livemint.com/",
                    "published_at": datetime.now().isoformat(),
                }
                for line in lines
                if line.strip() and len(line.strip()) > 20
            ]

        return await self._scrape_with_bs(
            "https://www.livemint.com/", ["h1", "h2", ".headline", ".story-title"]
        )

    async def scrape_bloomberg_quint(self) -> List[Dict]:
        """Scrape Bloomberg Quint"""
        content = await self._crawl_with_crawl4ai("https://www.bloombergquint.com/")
        if content:
            lines = content.split("\n")
            return [
                {
                    "headline": line.strip(),
                    "source": "Bloomberg Quint",
                    "url": "https://www.bloombergquint.com/",
                    "published_at": datetime.now().isoformat(),
                }
                for line in lines
                if line.strip() and len(line.strip()) > 20
            ]

        return await self._scrape_with_bs(
            "https://www.bloombergquint.com/", ["h1", "h2", ".headline", ".story-title"]
        )

    async def scrape_cnbc(self) -> List[Dict]:
        """Scrape CNBC India"""
        content = await self._crawl_with_crawl4ai("https://www.cnbctv18.com/")
        if content:
            lines = content.split("\n")
            return [
                {
                    "headline": line.strip(),
                    "source": "CNBC TV18",
                    "url": "https://www.cnbctv18.com/",
                    "published_at": datetime.now().isoformat(),
                }
                for line in lines
                if line.strip() and len(line.strip()) > 20
            ]

        return await self._scrape_with_bs(
            "https://www.cnbctv18.com/", ["h1", "h2", ".story-title", ".headline"]
        )

    async def scrape_investingcom(self) -> List[Dict]:
        """Scrape Investing.com India"""
        content = await self._crawl_with_crawl4ai("https://in.investing.com/")
        if content:
            lines = content.split("\n")
            return [
                {
                    "headline": line.strip(),
                    "source": "Investing.com",
                    "url": "https://in.investing.com/",
                    "published_at": datetime.now().isoformat(),
                }
                for line in lines
                if line.strip() and len(line.strip()) > 20
            ]

        return await self._scrape_with_bs(
            "https://in.investing.com/", ["h1", "h2", ".article-title", ".headline"]
        )

    async def get_all_news(self) -> List[Dict]:
        """Get news from all Indian financial sources"""
        scrapers = [
            self.scrape_moneycontrol(),
            self.scrape_ndtv(),
            self.scrape_screener(),
            self.scrape_et_now(),
            self.scrape_businesstoday(),
            self.scrape_livemint(),
            self.scrape_bloomberg_quint(),
            self.scrape_cnbc(),
            self.scrape_investingcom(),
        ]

        results = await asyncio.gather(*scrapers, return_exceptions=True)

        all_news = []
        seen = set()

        for result in results:
            if isinstance(result, list):
                for item in result:
                    # Deduplicate
                    headline = item.get("headline", "")[:100]
                    if headline and headline not in seen:
                        seen.add(headline)
                        all_news.append(item)

        return all_news  # No limit - return all


async def scrape_news():
    """Main news scraping function"""
    scraper = NewsScraper()
    news = await scraper.get_all_news()
    return news


if __name__ == "__main__":
    asyncio.run(scrape_news())
