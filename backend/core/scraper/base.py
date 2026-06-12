"""
Base scraper with shared HTTP client, retry logic, and exponential backoff.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseScraper:
    BASE_URL: str = ""
    MAX_RETRIES: int = 3
    TIMEOUT: float = 30.0

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.TIMEOUT,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
            )
        return self._client

    async def fetch(
        self, path: str, retries: Optional[int] = None
    ) -> Optional[httpx.Response]:
        client = await self._get_client()
        url = f"{self.BASE_URL}{path}"
        max_retries = retries if retries is not None else self.MAX_RETRIES

        for attempt in range(max_retries):
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return response
                if response.status_code in (403, 404, 429):
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt * (attempt + 1)
                        logger.debug(
                            f"HTTP {response.status_code} for {url}, retrying in {wait}s"
                        )
                        await asyncio.sleep(wait)
                        continue
                    return response
                return response
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt * (attempt + 1)
                    logger.debug(f"Request error for {url}, retrying in {wait}s: {e}")
                    await asyncio.sleep(wait)
                    continue
                logger.warning(f"Request failed for {url} after {max_retries} attempts: {e}")
                return None

        return None

    def parse_html(self, response: httpx.Response) -> Optional[BeautifulSoup]:
        try:
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            logger.warning(f"HTML parse error: {e}")
            return None

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
