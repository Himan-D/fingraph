from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    filters: Optional[dict] = None


@router.post("/query")
async def natural_query(request: QueryRequest):
    """Natural language query"""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

        # Build context for the query
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
                "result": response.choices[0].message.content,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summarize/{symbol}")
async def summarize_company(symbol: str):
    """AI summary of company financials"""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

        # Get company fundamentals (placeholder)
        # In production, fetch from database

        prompt = f"""Summarize the following company financials for {symbol.upper()}:
        - This is a placeholder for actual financial data
        
        Provide:
        1. Business overview
        2. Key highlights
        3. Risk factors
        4. Investment thesis
        """

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "summary": response.choices[0].message.content,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news-sentiment/{symbol}")
async def news_sentiment(symbol: str):
    """News sentiment analysis"""
    try:
        return {
            "success": True,
            "data": {"symbol": symbol.upper(), "sentiment": "neutral", "articles": []},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_ai_alerts():
    """Get AI-generated alerts"""
    return {"success": True, "data": []}


@router.post("/analyze-pattern")
async def analyze_pattern(symbol: str, period: str = "1y"):
    """AI chart pattern recognition"""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

        prompt = f"""Analyze the price chart for {symbol.upper()} over {period} period.
        Identify:
        - Support and resistance levels
        - Chart patterns (if any)
        - Trend direction
        - Key price levels
        """

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "analysis": response.choices[0].message.content,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
