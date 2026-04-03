import pytest

from core.data_sources.nse import NSEDataFetcher
from core.scraper.rss_scraper import RSSScraper
from core.scraper.sebi_scraper import SebiScraper


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text="ok"):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_nse_get_indices_parses_allindices(monkeypatch):
    fetcher = NSEDataFetcher()

    async def fake_get_cookies():
        return None

    async def fake_get(url, cookies=None):
        if "allIndices" in url:
            return DummyResponse(
                200,
                {
                    "data": [
                        {
                            "index": "NIFTY 50",
                            "last": 22815.26,
                            "variation": 365.26,
                            "percentChange": 1.63,
                        },
                        {
                            "index": "NIFTY BANK",
                            "last": 48520.50,
                            "variation": 420.80,
                            "percentChange": 0.87,
                        },
                    ]
                },
            )
        return DummyResponse(404, {}, "")

    monkeypatch.setattr(fetcher, "_get_cookies", fake_get_cookies)
    monkeypatch.setattr(fetcher.client, "get", fake_get)

    rows = await fetcher.get_indices()
    await fetcher.close()

    assert any(r["symbol"] == "NIFTY50" for r in rows)
    assert any(r["symbol"] == "BANKNIFTY" for r in rows)


@pytest.mark.asyncio
async def test_rss_get_all_news_uses_fallback_when_primary_empty(monkeypatch):
    scraper = RSSScraper()

    async def fake_fetch_feed(name, url):
        return []

    async def fake_fetch_with_aiohttp(name, url):
        return [
            {
                "headline": f"{name} headline",
                "summary": "summary",
                "source": name,
                "url": url,
                "published_at": "2026-03-30",
            }
        ]

    async def fake_discover_nse_feeds():
        return {
            "NSE RSS Financial Results": "https://nsearchives.nseindia.com/content/RSS/Financial_Results.xml"
        }

    monkeypatch.setattr(scraper, "_fetch_feed", fake_fetch_feed)
    monkeypatch.setattr(scraper, "_fetch_with_aiohttp", fake_fetch_with_aiohttp)
    monkeypatch.setattr(scraper, "_discover_nse_static_rss_feeds", fake_discover_nse_feeds)

    data = await scraper.get_all_rss_news()

    assert len(data) > 0
    assert all("headline" in item for item in data)


@pytest.mark.asyncio
async def test_rss_get_all_news_includes_discovered_nse_feeds(monkeypatch):
    scraper = RSSScraper()

    discovered_name = "NSE RSS Financial Results"
    discovered_url = "https://nsearchives.nseindia.com/content/RSS/Financial_Results.xml"

    async def fake_discover_nse_feeds():
        return {discovered_name: discovered_url}

    async def fake_fetch_feed(name, url):
        return [
            {
                "headline": f"{name} headline",
                "summary": "summary",
                "source": name,
                "url": url,
                "published_at": "2026-03-30",
            }
        ]

    monkeypatch.setattr(scraper, "_discover_nse_static_rss_feeds", fake_discover_nse_feeds)
    monkeypatch.setattr(scraper, "_fetch_feed", fake_fetch_feed)

    data = await scraper.get_all_rss_news()

    assert any(item.get("source") == discovered_name for item in data)
    assert any(item.get("url") == discovered_url for item in data)


@pytest.mark.asyncio
async def test_sebi_latest_filings_prefers_rss(monkeypatch):
    scraper = SebiScraper()

    async def fake_rss(limit=20):
        return [
            {
                "title": "SEBI order sample",
                "url": "https://www.sebi.gov.in/sample",
                "source": "SEBI",
                "category": "regulatory",
            }
        ]

    monkeypatch.setattr(scraper, "_fetch_sebi_rss", fake_rss)

    items = await scraper.get_latest_filings(limit=5)
    assert len(items) == 1
    assert items[0]["source"] == "SEBI"
