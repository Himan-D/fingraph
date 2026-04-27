"""
NSE Live Data Pipeline - Real-time market data ingestion
Fetches from NSE India API and stores in PostgreSQL
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import select, and_
from db.postgres import AsyncSessionLocal, engine
from db.postgres_models import (
    StockQuote, Company, IndexQuote, 
    OptionChain, StockInventory
)
from core.data_sources.nse import get_nse_fetcher

logger = logging.getLogger(__name__)


class NSELiveDataPipeline:
    """Real-time NSE data pipeline"""
    
    def __init__(self):
        self.nse = get_nse_fetcher()
        self.running = False
        self.interval = 10  # seconds
    
    async def start(self):
        """Start the pipeline"""
        self.running = True
        logger.info("NSE Live Data Pipeline started")
        
        while self.running:
            try:
                await self.fetch_all_quotes()
                await self.fetch_indices()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """Stop the pipeline"""
        self.running = False
        logger.info("NSE Live Data Pipeline stopped")
    
    async def fetch_all_quotes(self):
        """Fetch quotes for tracked symbols"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(StockInventory.symbol).where(StockInventory.is_active == True)
            )
            symbols = [row[0] for row in result.fetchall()]
        
        if not symbols:
            symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", 
                      "SBIN", "KOTAKBANK", "HINDUNILVR", "BHARTIARTL", "ADANIPORTS"]
        
        for symbol in symbols[:50]:
            try:
                quote = await self.nse.get_quote(symbol)
                if quote:
                    await self.store_quote(quote)
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
    
    async def store_quote(self, quote: Dict):
        """Store quote in database"""
        async with AsyncSessionLocal() as session:
            try:
                from sqlalchemy import select
                from db.postgres_models import Company
                
                result = await session.execute(
                    select(Company).where(Company.nse_code == quote.get("symbol"))
                )
                company = result.scalar_one_or_none()
                
                if not company:
                    company = Company(
                        symbol=quote.get("symbol", ""),
                        nse_code=quote.get("symbol"),
                        name=quote.get("name", ""),
                        sector=quote.get("sector", "")
                    )
                    session.add(company)
                    await session.flush()
                
                stock_quote = StockQuote(
                    company_id=company.id,
                    timestamp=datetime.now(),
                    open=quote.get("open", 0),
                    high=quote.get("high", 0),
                    low=quote.get("low", 0),
                    close=quote.get("price", 0),
                    volume=quote.get("volume", 0),
                    value=quote.get("value", 0)
                )
                session.add(stock_quote)
                await session.commit()
                
            except Exception as e:
                logger.warning(f"Failed to store quote: {e}")
    
    async def fetch_indices(self):
        """Fetch and store index values"""
        try:
            indices = await self.nse.get_indices()
            
            async with AsyncSessionLocal() as session:
                for idx in indices:
                    index_quote = IndexQuote(
                        symbol=idx.get("symbol"),
                        name=idx.get("name"),
                        price=idx.get("price", 0),
                        change=idx.get("change", 0),
                        pct_change=idx.get("pct_change", 0),
                        timestamp=datetime.now()
                    )
                    session.add(index_quote)
                
                await session.commit()
                
        except Exception as e:
            logger.warning(f"Index fetch failed: {e}")
    
    async def fetch_option_chain(self, symbol: str = "NIFTY"):
        """Fetch and store option chain"""
        try:
            chain_data = await self.nse.get_option_chain(symbol)
            
            if not chain_data:
                return None
            
            async with AsyncSessionLocal() as session:
                records = chain_data.get("records", [])
                
                for record in records[:100]:
                    strike_price = record.get("strikePrice", 0)
                    
                    ce = record.get("CE", {})
                    pe = record.get("PE", {})
                    
                    option = OptionChain(
                        symbol=symbol,
                        expiry_date=datetime.strptime(
                            record.get("expiryDate", ""), "%d %b %Y"
                        ) if record.get("expiryDate") else None,
                        strike_price=strike_price,
                        option_type="CE",
                        last_price=ce.get("lastPrice", 0),
                        open_interest=ce.get("openInterest", 0),
                        volume=ce.get("totalVolume", 0),
                        iv=ce.get("impliedVolatility", 0),
                        delta=ce.get("delta", 0),
                        gamma=ce.get("gamma", 0),
                        theta=ce.get("theta", 0),
                        vega=ce.get("vega", 0)
                    )
                    session.add(option)
                    
                    option_pe = OptionChain(
                        symbol=symbol,
                        expiry_date=datetime.strptime(
                            record.get("expiryDate", ""), "%d %b %Y"
                        ) if record.get("expiryDate") else None,
                        strike_price=strike_price,
                        option_type="PE",
                        last_price=pe.get("lastPrice", 0),
                        open_interest=pe.get("openInterest", 0),
                        volume=pe.get("totalVolume", 0),
                        iv=pe.get("impliedVolatility", 0),
                        delta=pe.get("delta", 0),
                        gamma=pe.get("gamma", 0),
                        theta=pe.get("theta", 0),
                        vega=pe.get("vega", 0)
                    )
                    session.add(option_pe)
                
                await session.commit()
                
            return chain_data
            
        except Exception as e:
            logger.warning(f"Option chain fetch failed: {e}")
            return None


class MarketDataCache:
    """In-memory cache for fast quote access"""
    
    _cache: Dict[str, Dict] = {}
    _indices: Dict[str, Dict] = {}
    _last_update: Optional[datetime] = None
    
    @classmethod
    async def update_quotes(cls):
        """Update cache from database"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(StockQuote)
                .order_by(StockQuote.timestamp.desc())
                .limit(200)
            )
            quotes = result.scalars().all()
            
            for quote in quotes:
                cls._cache[quote.company.nse_code] = {
                    "price": quote.close,
                    "open": quote.open,
                    "high": quote.high,
                    "low": quote.low,
                    "volume": quote.volume,
                    "change": 0,
                    "pct_change": 0
                }
            
            result = await session.execute(
                select(IndexQuote)
                .order_by(IndexQuote.timestamp.desc())
            )
            indices = result.scalars().all()
            
            cls._indices = {
                idx.symbol: {
                    "price": idx.price,
                    "change": idx.change,
                    "pct_change": idx.pct_change
                }
                for idx in indices
            }
            
            cls._last_update = datetime.now()
    
    @classmethod
    def get_quote(cls, symbol: str) -> Optional[Dict]:
        """Get cached quote"""
        return cls._cache.get(symbol)
    
    @classmethod
    def get_indices(cls) -> Dict[str, Dict]:
        """Get cached indices"""
        return cls._indices


async def start_nse_pipeline():
    """Start NSE data pipeline"""
    pipeline = NSELiveDataPipeline()
    await pipeline.start()


if __name__ == "__main__":
    asyncio.run(start_nse_pipeline())