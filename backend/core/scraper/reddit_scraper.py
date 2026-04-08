import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


class RedditScraper:
    """Scrape Reddit finance subreddits for market sentiment"""

    SUBREDDITS = [
        "wallstreetbets",
        "IndianStreetBets",
        "stocks",
        "investing",
        "options",
        "cryptocurrency",
        "nifty50",
        "IndianStocks",
    ]

    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text"""
        symbols = []
        patterns = [
            r"\b([A-Z]{2,5})\b",
            r"\$([A-Z]{2,5})\b",
            r"NS:(\w+)",
            r"NSE:(\w+)",
            r"BSE:(\w+)",
        ]

        excluded = {
            "A",
            "I",
            "VS",
            "ON",
            "UP",
            "IT",
            "ALL",
            "ONE",
            "YES",
            "NOW",
            "CEO",
            "CFO",
            "CTO",
            "IPO",
            "ETF",
            "USA",
            "UK",
            "INR",
            "USD",
            "EUR",
            "GBP",
            "GDP",
            "NIFTY",
            "SENSEX",
            "BSE",
            "NSE",
            "SEBI",
            "FII",
            "FDI",
            "IPO",
            "API",
            "AI",
            "LLM",
            "GPT",
            "USA",
            "UK",
            "EU",
            "UN",
            "WHO",
        }

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in excluded and len(match) <= 5 and not match.isdigit():
                    symbols.append(match)

        return list(set(symbols))

    async def _fetch_reddit_json(self, url: str) -> List[Dict]:
        """Fetch Reddit JSON API"""
        posts = []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                }
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        children = data.get("data", {}).get("children", [])

                        for child in children:
                            post = child.get("data", {})
                            posts.append(
                                {
                                    "title": post.get("title", ""),
                                    "text": post.get("selftext", ""),
                                    "author": post.get("author", ""),
                                    "subreddit": post.get("subreddit", ""),
                                    "score": post.get("score", 0),
                                    "num_comments": post.get("num_comments", 0),
                                    "url": f"https://reddit.com{post.get('permalink', '')}",
                                    "created_utc": post.get("created_utc", 0),
                                    "timestamp": datetime.fromtimestamp(
                                        post.get("created_utc", 0)
                                    ).isoformat(),
                                }
                            )
        except Exception as e:
            logger.warning(f"Reddit API fetch failed for {url}: {e}")

        return posts

    async def _fetch_rss(self, subreddit: str) -> List[Dict]:
        """Fetch subreddit via RSS"""
        posts = []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0"}
                url = f"https://www.reddit.com/r/{subreddit}/new/.rss"
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        xml = await resp.text()

                        try:
                            from bs4 import BeautifulSoup

                            soup = BeautifulSoup(xml, "xml")
                            items = soup.find_all("item")

                            for item in items[:25]:
                                title = item.find("title")
                                desc = item.find("description")
                                author = item.find("dc:creator")
                                link = item.find("link")

                                post_text = title.get_text(strip=True) if title else ""
                                if desc:
                                    post_text += " " + desc.get_text(strip=True)

                                posts.append(
                                    {
                                        "title": title.get_text(strip=True)
                                        if title
                                        else "",
                                        "text": post_text[:1000],
                                        "author": author.get_text(strip=True)
                                        if author
                                        else "anonymous",
                                        "subreddit": subreddit,
                                        "score": 0,
                                        "num_comments": 0,
                                        "url": link.get_text(strip=True)
                                        if link
                                        else "",
                                        "created_utc": 0,
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )
                        except Exception as e:
                            logger.warning(f"RSS parse error for {subreddit}: {e}")
        except Exception as e:
            logger.warning(f"RSS fetch failed for {subreddit}: {e}")

        return posts

    async def scrape_subreddit(self, subreddit: str, limit: int = 50) -> List[Dict]:
        """Scrape a single subreddit"""
        posts = await self._fetch_reddit_json(
            f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
        )

        if not posts:
            posts = await self._fetch_rss(subreddit)

        for post in posts:
            post["source"] = "reddit"
            post["symbols"] = self._extract_symbols(
                post.get("title", "") + " " + post.get("text", "")
            )

        return posts

    async def scrape_all_subreddits(self) -> List[Dict]:
        """Scrape all finance subreddits"""
        results = await asyncio.gather(
            *[self.scrape_subreddit(s, 50) for s in self.SUBREDDITS],
            return_exceptions=True,
        )

        all_posts = []
        for result in results:
            if isinstance(result, list):
                all_posts.extend(result)

        return all_posts

    async def scrape_hot_posts(self, subreddit: str = "wallstreetbets") -> List[Dict]:
        """Scrape hot posts"""
        return await self._fetch_reddit_json(
            f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
        )


class RedditSearchScraper:
    """Search Reddit for specific stocks/keywords"""

    async def search(self, query: str, subreddits: List[str] = None) -> List[Dict]:
        """Search Reddit for a query"""
        if subreddits is None:
            subreddits = RedditScraper.SUBREDDITS

        results = []

        for sub in subreddits:
            try:
                url = f"https://www.reddit.com/r/{sub}/search.json?q={query}&sort=hot&limit=50"
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    }
                    async with session.get(
                        url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            children = data.get("data", {}).get("children", [])

                            for child in children:
                                post = child.get("data", {})
                                results.append(
                                    {
                                        "title": post.get("title", ""),
                                        "text": post.get("selftext", ""),
                                        "author": post.get("author", ""),
                                        "subreddit": post.get("subreddit", ""),
                                        "score": post.get("score", 0),
                                        "url": f"https://reddit.com{post.get('permalink', '')}",
                                        "timestamp": datetime.fromtimestamp(
                                            post.get("created_utc", 0)
                                        ).isoformat(),
                                        "source": "reddit",
                                        "symbols": RedditScraper()._extract_symbols(
                                            post.get("title", "")
                                            + " "
                                            + post.get("selftext", "")
                                        ),
                                    }
                                )
            except Exception as e:
                logger.warning(f"Search failed for {sub}: {e}")

        return results


async def scrape_reddit():
    """Main Reddit scraping function"""
    scraper = RedditScraper()
    posts = await scraper.scrape_all_subreddits()
    return posts


async def search_reddit(query: str):
    """Search Reddit for a query"""
    scraper = RedditSearchScraper()
    results = await scraper.search(query)
    return results


if __name__ == "__main__":

    async def main():
        posts = await scrape_reddit()
        print(f"Found {len(posts)} Reddit posts")

        for post in posts[:3]:
            print(f"- r/{post['subreddit']}: {post['title'][:80]}")

    asyncio.run(main())
