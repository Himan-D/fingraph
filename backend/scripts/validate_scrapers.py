import asyncio
import json
from core.data_sources.nse import NSEDataFetcher
from core.scraper.rss_scraper import RSSScraper, RSS_FEEDS
from core.scraper.sebi_scraper import SebiScraper


async def validate() -> dict:
    out = {
        "nse": {},
        "rss": {},
        "sebi": {},
        "overall_ok": False,
    }

    # NSE direct API
    nse = NSEDataFetcher()
    try:
        quote = await asyncio.wait_for(nse.get_quote("RELIANCE"), timeout=25)
        indices = await asyncio.wait_for(nse.get_indices(), timeout=35)
        option_chain = await asyncio.wait_for(
            nse.get_option_chain("NIFTY"), timeout=25
        )
    finally:
        await nse.close()

    out["nse"] = {
        "quote_ok": bool(quote and quote.get("symbol") == "RELIANCE"),
        "quote_price": (quote or {}).get("price") if quote else None,
        "indices_count": len(indices or []),
        "option_chain_has_records": bool((option_chain or {}).get("records"))
        if isinstance(option_chain, dict)
        else False,
    }

    # RSS feeds specifically for NSE/BSE
    rss = RSSScraper()

    # Use aiohttp path here because it has explicit network timeout and avoids
    # feedparser blocking behavior in validation runs.
    nse_rss = await asyncio.wait_for(
        rss._fetch_with_aiohttp(
            "NSE Corporate Actions",
            RSS_FEEDS["NSE Corporate Actions"],
        ),
        timeout=20,
    )
    bse_rss = await asyncio.wait_for(
        rss._fetch_with_aiohttp(
            "BSE Announcements",
            RSS_FEEDS["BSE Announcements"],
        ),
        timeout=60,
    )

    out["rss"] = {
        "nse_items": len(nse_rss),
        "bse_items": len(bse_rss),
        "nse_sample": nse_rss[0].get("headline") if nse_rss else None,
        "bse_sample": bse_rss[0].get("headline") if bse_rss else None,
    }

    # SEBI scraper
    sebi = SebiScraper()
    filings = await asyncio.wait_for(sebi.get_latest_filings(limit=5), timeout=30)
    circulars = await asyncio.wait_for(sebi.get_circulars(year=2026), timeout=30)
    orders = await asyncio.wait_for(sebi.get_orders(), timeout=30)

    out["sebi"] = {
        "filings_count": len(filings or []),
        "circulars_count": len(circulars or []),
        "orders_count": len(orders or []),
        "sample_filing": filings[0].get("title") if filings else None,
    }

    out["overall_ok"] = (
        out["nse"]["quote_ok"]
        and out["nse"]["indices_count"] > 0
        and out["rss"]["nse_items"] > 0
        and out["rss"]["bse_items"] > 0
        and out["sebi"]["filings_count"] > 0
    )

    return out


if __name__ == "__main__":
    result = asyncio.run(validate())
    print(json.dumps(result, indent=2, ensure_ascii=False))
