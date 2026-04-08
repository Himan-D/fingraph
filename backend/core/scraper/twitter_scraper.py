import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


class TwitterFinanceScraper:
    """Scrape Twitter/X finance data and trending topics"""
    
    ACCOUNTS = [
        "@nseindia",
        "@BSEIndia", 
        "@MktProfiler",
        "@ Investors,
        "@saurabh",
        "@ market",
        "@ETMarkets",
        "@moneycontrol",
        "@livemint",
        "@NDTV",
        "@reuters",
    ]
    
    async def _fetch_with_browserless(self, url: str) -> str:
        """Use browserless API to fetch JavaScript-rendered content"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "url": url,
                    "elements": [
                        {"selector": "[data-testid='tweet']"},
                        {"selector": "article"},
                    ]
                }
                async with session.post(
                    "https://chrome.browserless.io/scrape",
                    params={"token": "demo"},
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("data", {})
        except Exception as e:
            logger.debug(f"Browserless failed for {url}: {e}")
        return ""
    
    async def _parse_tweet(self, html: str) -> List[Dict]:
        """Parse tweet HTML and extract data"""
        tweets = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            articles = soup.find_all("article", {"data-testid": "tweet"})
            
            for article in articles:
                try:
                    text_el = article.find("div", {"data-testid": "tweetText"})
                    time_el = article.find("time")
                    user_el = article.find("div", {"data-testid": "User-Name"})
                    
                    text = text_el.get_text(strip=True) if text_el else ""
                    timestamp = time_el.get("datetime") if time_el else datetime.now().isoformat()
                    
                    username = ""
                    if user_el:
                        spans = user_el.find_all("span")
                        if spans:
                            username = spans[0].get_text(strip=True)
                    
                    if text and len(text) > 10:
                        tweets.append({
                            "text": text[:500],
                            "username": username,
                            "timestamp": timestamp,
                            "source": "twitter",
                        })
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Tweet parse error: {e}")
        return tweets
    
    async def scrape_finance_accounts(self) -> List[Dict]:
        """Scrape finance tweets using RSS-to-JSON bridge"""
        tweets = []
        
        rss_urls = [
            "https://nitter.net/rss/nseindia",
            "https://nitter.net/rss/moneycontrol",
            "https://nitter.net/rss/ETMarkets",
        ]
        
        for url in rss_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            xml = await resp.text()
                            soup = BeautifulSoup(xml, "xml")
                            items = soup.find_all("item")
                            
                            for item in items[:20]:
                                title = item.find("title")
                                date = item.find("pubDate")
                                
                                if title:
                                    text = title.get_text(strip=True)
                                    tweets.append({
                                        "text": text[:500],
                                        "username": url.split("/rss/")[-1] if "/rss/" in url else "unknown",
                                        "timestamp": date.get_text(strip=True) if date else datetime.now().isoformat(),
                                        "source": "twitter",
                                    })
            except Exception as e:
                logger.warning(f"RSS scrape failed for {url}: {e}")
        
        return tweets
    
    async def scrape_trending_stocks(self) -> List[Dict]:
        """Scrape trending stock mentions"""
        trending = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0"}
                async with session.get(
                    "https://stocktwits.com/symbols/nifty-50",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")
                        
                        symbols = soup.find_all("a", href=re.compile(r"/symbols/"))
                        for sym in symbols[:20]:
                            text = sym.get_text(strip=True)
                            if text and text.isupper() and len(text) <= 10:
                                trending.append({
                                    "text": f"${text} trending on StockTwits",
                                    "username": "StockTwits",
                                    "timestamp": datetime.now().isoformat(),
                                    "source": "twitter",
                                    "symbol": text,
                                })
        except Exception as e:
            logger.warning(f"StockTwits scrape failed: {e}")
        
        return trending
    
    async def get_all_tweets(self) -> List[Dict]:
        """Get all tweets from finance sources"""
        results = await asyncio.gather(
            self.scrape_finance_accounts(),
            self.scrape_trending_stocks(),
            return_exceptions=True,
        )
        
        all_tweets = []
        for result in results:
            if isinstance(result, list):
                all_tweets.extend(result)
        
        return all_tweets


class StockTwitsScraper:
    """Scrape StockTwits for social sentiment"""
    
    SYMBOLS = ["RELIANCE", "INFY", "TCS", "HDFCBANK", "ICICIBANK", "SBIN", "ADANIGREEN"]
    
    async def scrape_symbol(self, symbol: str) -> List[Dict]:
        """Scrape messages for a symbol"""
        messages = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0"}
                async with session.get(
                    f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for msg in data.get("messages", [])[:50]:
                            messages.append({
                                "text": msg.get("body", ""),
                                "username": msg.get("user", {}).get("username", ""),
                                "timestamp": msg.get("created_at", ""),
                                "source": "stocktwits",
                                "symbol": symbol,
                                "sentiment": msg.get("entities", {}).get("sentiment", {}).get("basic", ""),
                            })
        except Exception as e:
            logger.warning(f"StockTwits scrape failed for {symbol}: {e}")
        
        return messages
    
    async def get_all_messages(self) -> List[Dict]:
        """Get messages for all tracked symbols"""
        results = await asyncio.gather(
            *[self.scrape_symbol(s) for s in self.SYMBOLS],
            return_exceptions=True,
        )
        
        all_messages = []
        for result in results:
            if isinstance(result, list):
                all_messages.extend(result)
        
        return all_messages


async def scrape_twitter_finance():
    """Main Twitter finance scraping function"""
    scraper = TwitterFinanceScraper()
    tweets = await scraper.get_all_tweets()
    return tweets


async def scrape_stocktwits():
    """Main StockTwits scraping function"""
    scraper = StockTwitsScraper()
    messages = await scraper.get_all_messages()
    return messages


if __name__ == "__main__":
    async def main():
        tweets = await scrape_twitter_finance()
        print(f"Found {len(tweets)} tweets")
        
        messages = await scrape_stocktwits()
        print(f"Found {len(messages)} StockTwits messages")
    
    asyncio.run(main())
