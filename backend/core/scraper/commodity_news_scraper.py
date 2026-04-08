import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


class RealCommodityNewsScraper:
    """Scrape real commodity news from actual sources"""

    def _extract_commodities(self, text: str) -> List[str]:
        """Extract commodity names from text"""
        text_lower = text.lower()
        commodities = []

        patterns = {
            "GOLD": [
                r"\bgold\b",
                r"\bgold futures\b",
                r"\bgold etf\b",
                r"\bspot gold\b",
                r"\bxau\b",
                r"\bsgold\b",
            ],
            "SILVER": [
                r"\bsilver\b",
                r"\bsilver futures\b",
                r"\bsilver etf\b",
                r"\bxag\b",
            ],
            "CRUDEOIL": [
                r"\bcrude oil\b",
                r"\bbrent\b",
                r"\bwti\b",
                r"\bopec\b",
                r"\bcrude\b",
                r"\b石油\b",
            ],
            "NATURALGAS": [r"\bnatural gas\b", r"\blng\b", r"\bgas\b", r"\b天然气\b"],
            "COPPER": [r"\bcopper\b", r"\bcopper futures\b", r"\b铜\b"],
            "ALUMINIUM": [r"\baluminum\b", r"\baluminium\b", r"\b铝\b"],
            "PLATINUM": [r"\bplatinum\b", r"\bxpt\b"],
            "PALLADIUM": [r"\bpalladium\b", r"\bxpd\b"],
        }

        for commodity, regex_patterns in patterns.items():
            for pattern in regex_patterns:
                if re.search(pattern, text_lower):
                    commodities.append(commodity)
                    break

        return list(set(commodities))

    async def _scrape_moneycontrol(self) -> List[Dict]:
        """Scrape MoneyControl commodity news"""
        news = []

        try:
            from bs4 import BeautifulSoup

            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                async with session.get(
                    "https://www.moneycontrol.com/news/business/commodities/",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")

                        # Find all links and extract titles
                        links = soup.find_all("a", href=re.compile(r"/news/"))

                        for link in links[:30]:
                            title = link.get_text(strip=True)
                            if title and len(title) > 30 and len(title) < 300:
                                commodities = self._extract_commodities(title)

                                if commodities:
                                    href = link.get("href", "")
                                    full_url = (
                                        f"https://www.moneycontrol.com{href}"
                                        if href.startswith("/")
                                        else href
                                    )

                                    news.append(
                                        {
                                            "headline": title,
                                            "summary": title,
                                            "source": "MoneyControl",
                                            "url": full_url,
                                            "commodities": commodities,
                                            "published_at": datetime.now().isoformat(),
                                            "tags": commodities,
                                        }
                                    )
        except Exception as e:
            logger.warning(f"MoneyControl scrape failed: {e}")

        return news

    async def _scrape_etnow(self) -> List[Dict]:
        """Scrape ET Now commodity news"""
        news = []

        try:
            from bs4 import BeautifulSoup

            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0"}

                async with session.get(
                    "https://www.etnow.in/markets/commodities",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")

                        links = soup.find_all("a", href=re.compile(r"commodit"))

                        for link in links[:20]:
                            title = link.get_text(strip=True)
                            if title and len(title) > 20:
                                commodities = self._extract_commodities(title)

                                news.append(
                                    {
                                        "headline": title,
                                        "summary": title,
                                        "source": "ET Now",
                                        "url": "https://www.etnow.in/markets/commodities",
                                        "commodities": commodities,
                                        "published_at": datetime.now().isoformat(),
                                        "tags": commodities,
                                    }
                                )
        except Exception as e:
            logger.warning(f"ET Now scrape failed: {e}")

        return news

    async def _scrape_livemint(self) -> List[Dict]:
        """Scrape Livemint commodity news"""
        news = []

        try:
            from bs4 import BeautifulSoup

            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0"}

                async with session.get(
                    "https://www.livemint.com/market/commodities",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")

                        articles = soup.find_all(
                            ["h2", "h3"], string=re.compile(r".{20,}")
                        )

                        for article in articles[:20]:
                            title = article.get_text(strip=True)
                            if title and len(title) > 20:
                                commodities = self._extract_commodities(title)

                                link = article.find_parent("a")
                                url = link.get("href", "") if link else ""

                                news.append(
                                    {
                                        "headline": title,
                                        "summary": title,
                                        "source": "LiveMint",
                                        "url": url,
                                        "commodities": commodities,
                                        "published_at": datetime.now().isoformat(),
                                        "tags": commodities,
                                    }
                                )
        except Exception as e:
            logger.warning(f"LiveMint scrape failed: {e}")

        return news

    async def _scrape_investing(self) -> List[Dict]:
        """Scrape Investing.com commodity news"""
        news = []

        commodity_urls = {
            "GOLD": "https://in.investing.com/commodities/gold-news",
            "SILVER": "https://in.investing.com/commodities/silver-news",
            "CRUDEOIL": "https://in.investing.com/commodities/crude-oil-news",
        }

        for commodity, url in commodity_urls.items():
            try:
                from bs4 import BeautifulSoup

                async with aiohttp.ClientSession() as session:
                    headers = {
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://in.investing.com/",
                    }

                    async with session.get(
                        url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            soup = BeautifulSoup(html, "html.parser")

                            articles = soup.find_all("article")[:15]

                            for article in articles:
                                title_elem = article.find("a")
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                                    if title and len(title) > 20:
                                        href = title_elem.get("href", "")
                                        full_url = (
                                            href
                                            if href.startswith("http")
                                            else f"https://in.investing.com{href}"
                                        )

                                        news.append(
                                            {
                                                "headline": title,
                                                "summary": title,
                                                "source": "Investing.com",
                                                "url": full_url,
                                                "commodities": [commodity],
                                                "published_at": datetime.now().isoformat(),
                                                "tags": [commodity],
                                            }
                                        )
            except Exception as e:
                logger.warning(f"Investing scrape failed for {commodity}: {e}")

        return news

    async def get_all_news(self) -> List[Dict]:
        """Get all commodity news"""
        results = await asyncio.gather(
            self._scrape_moneycontrol(),
            self._scrape_etnow(),
            self._scrape_livemint(),
            self._scrape_investing(),
            return_exceptions=True,
        )

        all_news = []
        seen = set()

        for result in results:
            if isinstance(result, list):
                for item in result:
                    headline = item.get("headline", "")[:100]
                    if headline and headline not in seen:
                        seen.add(headline)
                        all_news.append(item)

        return all_news

    async def get_news_by_commodity(self, commodity: str) -> List[Dict]:
        """Get news for specific commodity"""
        all_news = await self.get_all_news()

        return [n for n in all_news if commodity.upper() in n.get("commodities", [])]


async def scrape_commodity_news():
    """Main commodity news scraping function"""
    scraper = RealCommodityNewsScraper()
    return await scraper.get_all_news()


async def get_commodity_news(commodity: str):
    """Get news for specific commodity"""
    scraper = RealCommodityNewsScraper()
    return await scraper.get_news_by_commodity(commodity)


if __name__ == "__main__":

    async def main():
        print("=== Scraping Commodity News ===")

        scraper = RealCommodityNewsScraper()
        news = await scraper.get_all_news()

        print(f"Found {len(news)} news articles")

        for n in news[:10]:
            print(f"\n- {n['headline'][:80]}")
            print(f"  Source: {n['source']}")
            print(f"  Commodities: {n.get('commodities', [])}")

    asyncio.run(main())
