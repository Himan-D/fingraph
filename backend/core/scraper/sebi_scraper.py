import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import List, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class SebiScraper:
    """Scrape SEBI filings and disclosures using crawl4ai"""

    CRAWL4AI_URL = getattr(settings, "CRAWL4AI_URL", "http://localhost:11202")
    BASE_URL = "https://www.sebi.gov.in"

    async def _crawl_with_crawl4ai(self, url: str) -> str:
        """Use crawl4ai API to crawl page"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "urls": [url],
                    "css_selector": "h1, h2, h3, h4, h5, h6, p, a, li, table",
                    "exclude_selector": "script, style, nav, footer, .ad",
                    "word_count_threshold": 5,
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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
                                href = el.get("href", "")
                                if text and len(text) > 10:
                                    news.append(
                                        {
                                            "title": text,
                                            "url": f"{self.BASE_URL}{href}"
                                            if href.startswith("/")
                                            else href,
                                            "source": "SEBI",
                                            "category": "regulatory",
                                        }
                                    )
        except Exception as e:
            logger.warning(f"BS scrape failed for {url}: {e}")
        return news

    async def get_latest_filings(self, limit: int = 20) -> List[Dict]:
        """Get latest SEBI filings"""
        filings = []

        # Try crawl4ai
        content = await self._crawl_with_crawl4ai(f"{self.BASE_URL}/sebiweb/home/0")
        if content:
            lines = content.split("\n")
            for line in lines:
                text = line.strip()
                if text and len(text) > 20 and len(text) < 200:
                    filings.append(
                        {
                            "title": text,
                            "url": f"{self.BASE_URL}/sebiweb/home/0",
                            "source": "SEBI",
                            "category": "regulatory",
                        }
                    )
            if filings:
                return filings[:limit]

        # Fallback to BS
        return await self._scrape_with_bs(
            f"{self.BASE_URL}/sebiweb/home/0",
            ["h1", "h2", "h3", "a[href*='order']", "a[href*='circular']"],
        )

    async def get_circulars(self, year: int = 2025) -> List[Dict]:
        """Get SEBI circulars for a year"""
        circulars = []

        # Try crawl4ai
        content = await self._crawl_with_crawl4ai(
            f"{self.BASE_URL}/sebiweb/codifiedCirculars.do"
        )
        if content:
            lines = content.split("\n")
            for line in lines:
                text = line.strip()
                if text and len(text) > 20:
                    circulars.append(
                        {
                            "title": f"Circular {year}: {text}",
                            "url": f"{self.BASE_URL}/sebiweb/codifiedCirculars.do",
                            "source": "SEBI",
                            "category": "circular",
                        }
                    )
            if circulars:
                return circulars

        return [{"year": year, "count": 0, "note": "Check SEBI website for circulars"}]

    async def get_orders(self) -> List[Dict]:
        """Get SEBI orders"""
        content = await self._crawl_with_crawl4ai(
            f"{self.BASE_URL}/sebiweb/order/list.do"
        )
        if content:
            lines = content.split("\n")
            return [
                {
                    "title": line.strip(),
                    "url": f"{self.BASE_URL}/sebiweb/order/list.do",
                    "source": "SEBI",
                    "category": "order",
                }
                for line in lines
                if line.strip() and len(line.strip()) > 20
            ]

        return await self._scrape_with_bs(
            f"{self.BASE_URL}/sebiweb/order/list.do", ["h1", "h2", "a"]
        )


async def scrape_sebi():
    """Main SEBI scraping function"""
    scraper = SebiScraper()
    filings = await scraper.get_latest_filings()
    return filings


if __name__ == "__main__":
    asyncio.run(scrape_sebi())
