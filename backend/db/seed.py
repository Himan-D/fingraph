import asyncio
from datetime import datetime, timedelta
import random
from db.postgres import AsyncSessionLocal, init_db
from db.postgres_models import (
    Company,
    StockQuote,
    Fundamental,
    Shareholding,
    NewsArticle,
    Watchlist,
)


async def seed_data():
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if data exists
        from sqlalchemy import select

        result = await session.execute(select(Company).limit(1))
        if result.scalars().first():
            print("Data already exists, skipping seed...")
            return

        # Seed Companies
        companies = [
            {
                "symbol": "RELIANCE",
                "nse_code": "RELIANCE",
                "name": "Reliance Industries Ltd",
                "sector": "Energy",
                "industry": "Oil & Gas",
                "market_cap": 2012500000000,
            },
            {
                "symbol": "TCS",
                "nse_code": "TCS",
                "name": "Tata Consultancy Services Ltd",
                "sector": "Technology",
                "industry": "IT Services",
                "market_cap": 1520000000000,
            },
            {
                "symbol": "HDFCBANK",
                "nse_code": "HDFCBANK",
                "name": "HDFC Bank Ltd",
                "sector": "Financial Services",
                "industry": "Banking",
                "market_cap": 1250000000000,
            },
            {
                "symbol": "INFY",
                "nse_code": "INFY",
                "name": "Infosys Ltd",
                "sector": "Technology",
                "industry": "IT Services",
                "market_cap": 780000000000,
            },
            {
                "symbol": "ICICIBANK",
                "nse_code": "ICICIBANK",
                "name": "ICICI Bank Ltd",
                "sector": "Financial Services",
                "industry": "Banking",
                "market_cap": 685000000000,
            },
            {
                "symbol": "SBIN",
                "nse_code": "SBIN",
                "name": "State Bank of India",
                "sector": "Financial Services",
                "industry": "Banking",
                "market_cap": 650000000000,
            },
            {
                "symbol": "WIPRO",
                "nse_code": "WIPRO",
                "name": "Wipro Ltd",
                "sector": "Technology",
                "industry": "IT Services",
                "market_cap": 285000000000,
            },
            {
                "symbol": "LT",
                "nse_code": "LT",
                "name": "Larsen & Toubro Ltd",
                "sector": "Capital Goods",
                "industry": "Construction",
                "market_cap": 450000000000,
            },
            {
                "symbol": "HINDUNILVR",
                "nse_code": "HINDUNILVR",
                "name": "Hindustan Unilever Ltd",
                "sector": "FMCG",
                "industry": "Consumer Goods",
                "market_cap": 565000000000,
            },
            {
                "symbol": "KOTAKBANK",
                "nse_code": "KOTAKBANK",
                "name": "Kotak Mahindra Bank Ltd",
                "sector": "Financial Services",
                "industry": "Banking",
                "market_cap": 355000000000,
            },
            {
                "symbol": "BHARTIARTL",
                "nse_code": "BHARTIARTL",
                "name": "Bharti Airtel Ltd",
                "sector": "Telecommunication",
                "industry": "Telecom Services",
                "market_cap": 920000000000,
            },
            {
                "symbol": "HCLTECH",
                "nse_code": "HCLTECH",
                "name": "HCL Technologies Ltd",
                "sector": "Technology",
                "industry": "IT Services",
                "market_cap": 495000000000,
            },
            {
                "symbol": "MARUTI",
                "nse_code": "MARUTI",
                "name": "Maruti Suzuki India Ltd",
                "sector": "Automobile",
                "industry": "Automobiles",
                "market_cap": 385000000000,
            },
            {
                "symbol": "TITAN",
                "nse_code": "TITAN",
                "name": "Titan Company Ltd",
                "sector": "Consumer Goods",
                "industry": "Jewelry",
                "market_cap": 340000000000,
            },
            {
                "symbol": "BAJFINANCE",
                "nse_code": "BAJFINANCE",
                "name": "Bajaj Finance Ltd",
                "sector": "Financial Services",
                "industry": "NBFC",
                "market_cap": 485000000000,
            },
            {
                "symbol": "TATASTEEL",
                "nse_code": "TATASTEEL",
                "name": "Tata Steel Ltd",
                "sector": "Metals",
                "industry": "Steel",
                "market_cap": 185000000000,
            },
            {
                "symbol": "AXISBANK",
                "nse_code": "AXISBANK",
                "name": "Axis Bank Ltd",
                "sector": "Financial Services",
                "industry": "Banking",
                "market_cap": 380000000000,
            },
            {
                "symbol": "SUNPHARMA",
                "nse_code": "SUNPHARMA",
                "name": "Sun Pharmaceutical Industries Ltd",
                "sector": "Healthcare",
                "industry": "Pharmaceuticals",
                "market_cap": 445000000000,
            },
            {
                "symbol": "NESTLEIND",
                "nse_code": "NESTLEIND",
                "name": "Nestle India Ltd",
                "sector": "FMCG",
                "industry": "Food Products",
                "market_cap": 235000000000,
            },
            {
                "symbol": "M&M",
                "nse_code": "M&M",
                "name": "Mahindra & Mahindra Ltd",
                "sector": "Automobile",
                "industry": "Automobiles",
                "market_cap": 385000000000,
            },
            {
                "symbol": "TATAMOTORS",
                "nse_code": "TATAMOTORS",
                "name": "Tata Motors Ltd",
                "sector": "Automobile",
                "industry": "Automobiles",
                "market_cap": 195000000000,
            },
            {
                "symbol": "ADANIPORTS",
                "nse_code": "ADANIPORTS",
                "name": "Adani Ports and SEZ Ltd",
                "sector": "Services",
                "industry": "Ports & Shipping",
                "market_cap": 295000000000,
            },
            {
                "symbol": "ULTRACEMCO",
                "nse_code": "ULTRACEMCO",
                "name": "UltraTech Cement Ltd",
                "sector": "Materials",
                "industry": "Cement",
                "market_cap": 285000000000,
            },
            {
                "symbol": "INDUSINDBK",
                "nse_code": "INDUSINDBK",
                "name": "IndusInd Bank Ltd",
                "sector": "Financial Services",
                "industry": "Banking",
                "market_cap": 225000000000,
            },
            {
                "symbol": "JSWSTEEL",
                "nse_code": "JSWSTEEL",
                "name": "JSW Steel Ltd",
                "sector": "Metals",
                "industry": "Steel",
                "market_cap": 195000000000,
            },
            {
                "symbol": "TECHM",
                "nse_code": "TECHM",
                "name": "Tech Mahindra Ltd",
                "sector": "Technology",
                "industry": "IT Services",
                "market_cap": 145000000000,
            },
            {
                "symbol": "HINDALCO",
                "nse_code": "HINDALCO",
                "name": "Hindalco Industries Ltd",
                "sector": "Metals",
                "industry": "Aluminum",
                "market_cap": 175000000000,
            },
            {
                "symbol": "CIPLA",
                "nse_code": "CIPLA",
                "name": "Cipla Ltd",
                "sector": "Healthcare",
                "industry": "Pharmaceuticals",
                "market_cap": 115000000000,
            },
            {
                "symbol": "DRREDDY",
                "nse_code": "DRREDDY",
                "name": "Dr. Reddy's Laboratories Ltd",
                "sector": "Healthcare",
                "industry": "Pharmaceuticals",
                "market_cap": 115000000000,
            },
            {
                "symbol": "ADANIENSOL",
                "nse_code": "ADANIENSOL",
                "name": "Adani Energy Solutions Ltd",
                "sector": "Energy",
                "industry": "Power",
                "market_cap": 265000000000,
            },
        ]

        company_objs = []
        for c in companies:
            company = Company(**c)
            company_objs.append(company)
        session.add_all(company_objs)
        await session.flush()

        # Seed Stock Quotes (latest)
        base_prices = {
            "RELIANCE": 2965,
            "TCS": 4125,
            "HDFCBANK": 1685,
            "INFY": 1845,
            "ICICIBANK": 985,
            "SBIN": 725,
            "WIPRO": 485,
            "LT": 3256,
            "HINDUNILVR": 2685,
            "KOTAKBANK": 1785,
            "BHARTIARTL": 1580,
            "HCLTECH": 1850,
            "MARUTI": 12500,
            "TITAN": 3850,
            "BAJFINANCE": 7250,
            "TATASTEEL": 145,
            "AXISBANK": 985,
            "SUNPHARMA": 1850,
            "NESTLEIND": 2450,
            "M&M": 3250,
            "TATAMOTORS": 985,
            "ADANIPORTS": 1450,
            "ULTRACEMCO": 9850,
            "INDUSINDBK": 1450,
            "JSWSTEEL": 825,
            "TECHM": 1680,
            "HINDALCO": 485,
            "CIPLA": 1420,
            "DRREDDY": 6850,
            "ADANIENSOL": 1285,
        }

        now = datetime.now()
        for c in company_objs:
            base = base_prices.get(c.symbol, 1000)
            variation = random.uniform(-0.02, 0.02)
            price = base * (1 + variation)
            change = price - base
            pct_change = (change / base) * 100

            quote = StockQuote(
                company_id=c.id,
                timestamp=now,
                open=base * (1 + random.uniform(-0.01, 0.01)),
                high=base * (1 + random.uniform(0, 0.025)),
                low=base * (1 + random.uniform(-0.025, 0)),
                close=price,
                volume=random.randint(500000, 5000000),
            )
            session.add(quote)

        # Seed News
        news_items = [
            {
                "headline": "RBI keeps repo rate unchanged at 6.5%",
                "source": "ET Markets",
                "sentiment": "neutral",
            },
            {
                "headline": "IT stocks rally on strong Q3 results",
                "source": "MoneyControl",
                "sentiment": "positive",
            },
            {
                "headline": "FII buying continues in banking sector",
                "source": "Business Standard",
                "sentiment": "positive",
            },
            {
                "headline": "RIL announces new renewable energy venture",
                "source": "Reuters",
                "sentiment": "positive",
            },
            {
                "headline": "TCS wins $500M deal from European client",
                "source": "Economic Times",
                "sentiment": "positive",
            },
            {
                "headline": "Oil prices surge amid geopolitical tensions",
                "source": "Bloomberg",
                "sentiment": "negative",
            },
            {
                "headline": "Auto sales report shows strong growth in March",
                "source": "MoneyControl",
                "sentiment": "positive",
            },
            {
                "headline": "Bank Nifty hits all-time high",
                "source": "CNBC TV18",
                "sentiment": "positive",
            },
            {
                "headline": "Govt announces new infrastructure spending",
                "source": "The Hindu",
                "sentiment": "positive",
            },
            {
                "headline": "Pharma sector faces headwinds from US pricing",
                "source": "Business Line",
                "sentiment": "negative",
            },
        ]

        for i, n in enumerate(news_items):
            news = NewsArticle(
                headline=n["headline"],
                summary="",
                source=n["source"],
                url="",
                published_at=now - timedelta(minutes=i * 10),
                sentiment=n["sentiment"],
                related_symbols=[],
            )
            session.add(news)

        # Seed Watchlists
        watchlists = [
            {
                "user_id": "default",
                "name": "Favorites",
                "symbols": ["RELIANCE", "TCS", "INFY"],
            },
            {
                "user_id": "default",
                "name": "IT Stocks",
                "symbols": ["WIPRO", "HCLTECH", "TECHM"],
            },
            {
                "user_id": "default",
                "name": "Bank Nifty",
                "symbols": ["HDFCBANK", "ICICIBANK", "SBIN"],
            },
        ]

        for w in watchlists:
            wl = Watchlist(**w)
            session.add(wl)

        await session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
