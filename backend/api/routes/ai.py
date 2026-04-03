from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    query: str
    filters: Optional[dict] = None


async def _fetch_company_context(symbol: str) -> dict:
    """Fetch real company + fundamentals context from DB / sample data for AI prompts."""
    ctx: dict = {"symbol": symbol}
    try:
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import Company, Fundamental, StockQuote
        from sqlalchemy import select, desc

        async with AsyncSessionLocal() as session:
            # Company row
            co_result = await session.execute(
                select(Company).where(Company.symbol == symbol)
            )
            company = co_result.scalars().first()
            if company:
                ctx.update({
                    "name": company.name,
                    "sector": company.sector,
                    "industry": company.industry,
                    "market_cap": company.market_cap,
                    "description": company.description,
                })

            # Latest fundamental row
            fund_result = await session.execute(
                select(Fundamental)
                .where(Fundamental.company_id == company.id if company else False)
                .limit(1)
            )
            fund = fund_result.scalars().first()
            if fund:
                ctx.update({
                    "pe_ratio": fund.pe_ratio,
                    "pb_ratio": fund.pb_ratio,
                    "roe": fund.roe,
                    "roce": fund.roce,
                    "debt_to_equity": fund.debt_to_equity,
                    "dividend_yield": fund.dividend_yield,
                    "eps": fund.eps,
                })

            # Latest price
            quote_result = await session.execute(
                select(StockQuote)
                .where(StockQuote.company_id == company.id if company else False)
                .order_by(desc(StockQuote.timestamp))
                .limit(1)
            )
            quote = quote_result.scalars().first()
            if quote:
                ctx.update({
                    "current_price": quote.close,
                    "volume": quote.volume,
                    "high_52w": quote.high,
                    "low_52w": quote.low,
                })
    except Exception as e:
        logger.debug(f"DB context fetch for {symbol} failed: {e}")

    # If DB gave nothing, try SAMPLE_FUNDAMENTALS
    if len(ctx) == 1:
        try:
            from api.routes.fundamentals import SAMPLE_FUNDAMENTALS
            sample = SAMPLE_FUNDAMENTALS.get(symbol, {})
            ctx.update(sample)
        except Exception:
            pass

    return ctx


@router.post("/query")
async def natural_query(request: QueryRequest):
    """Natural language query"""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

        system_prompt = """You are a financial data assistant for Indian stock market.
        You help users find stocks based on their criteria.
        
        Available filters:
        - market_cap (min, max in crores)
        - pe (min, max)
        - roe (min)
        - roce (min)
        - net_margin (min)
        - dividend_yield (min)
        - debt_equity (max)
        - sector
        
        Return stocks in JSON format:
        {"stocks": [{"symbol": "RELIANCE", "reason": "..."}]}
        """

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query},
            ],
            temperature=0.3,
        )

        return {
            "success": True,
            "data": {
                "query": request.query,
                "response": response.choices[0].message.content,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summarize/{symbol}")
async def summarize_company(symbol: str):
    """AI summary of company financials, injecting real DB data into the prompt."""
    symbol = symbol.upper()
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        ctx = await _fetch_company_context(symbol)

        data_lines = "\n".join(
            f"  - {k.replace('_', ' ').title()}: {v}"
            for k, v in ctx.items()
            if k != "symbol" and v is not None
        )
        if not data_lines:
            data_lines = "  - No financial data available"

        prompt = f"""Analyze the following real financial data for {ctx.get('name', symbol)} ({symbol}):

{data_lines}

Provide a concise analysis covering:
1. Business overview (2-3 sentences)
2. Key financial highlights
3. Risk factors
4. Investment thesis
Keep the response professional and factual. Where data is missing, state it clearly."""

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )

        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "summary": response.choices[0].message.content,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news-sentiment/{symbol}")
async def news_sentiment(symbol: str):
    """News sentiment analysis"""
    return {
        "success": True,
        "data": {"symbol": symbol.upper(), "sentiment": "neutral", "articles": []},
    }


@router.get("/alerts")
async def get_ai_alerts():
    """Get AI-generated alerts"""
    return {"success": True, "data": []}


@router.post("/analyze-pattern")
async def analyze_pattern(symbol: str, period: str = "1y"):
    """AI chart pattern recognition — includes recent price data from DB."""
    symbol = symbol.upper()
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

        # Fetch recent prices from DB for richer prompt
        price_summary = ""
        try:
            from db.postgres import AsyncSessionLocal
            from db.postgres_models import Company, StockQuote
            from sqlalchemy import select, desc

            async with AsyncSessionLocal() as session:
                co_result = await session.execute(
                    select(Company).where(Company.symbol == symbol)
                )
                company = co_result.scalars().first()
                if company:
                    quotes_result = await session.execute(
                        select(StockQuote)
                        .where(StockQuote.company_id == company.id)
                        .order_by(desc(StockQuote.timestamp))
                        .limit(20)
                    )
                    quotes = quotes_result.scalars().all()
                    if quotes:
                        price_lines = [
                            f"  {q.timestamp.date()} O:{q.open} H:{q.high} L:{q.low} C:{q.close} V:{q.volume}"
                            for q in reversed(quotes)
                        ]
                        price_summary = "\nRecent OHLCV data:\n" + "\n".join(price_lines)
        except Exception:
            pass

        prompt = f"""Analyze the price chart for {symbol} over {period} period.{price_summary}

Identify:
- Current trend direction
- Key support and resistance levels
- Notable chart patterns (if any)
- Momentum indicators interpretation"""

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "analysis": response.choices[0].message.content,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

