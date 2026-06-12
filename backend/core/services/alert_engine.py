import json
import logging
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from sqlalchemy import select, desc

from config import settings
from db.postgres import AsyncSessionLocal
from db.postgres_models import (
    AIAlert,
    Company,
    StockQuote,
    Fundamental,
    NewsArticle,
    Watchlist,
)

logger = logging.getLogger(__name__)

ALERT_PROMPT = """You are a financial alert analyst for Indian stock market. Given the following data for {symbol}, determine if there's a noteworthy alert.

Stock: {symbol} ({name})
Current Price: ₹{price}
Change: {change_pct}%
Sector: {sector}

Recent Fundamentals:
PE: {pe}, PB: {pb}, ROE: {roe}%, Debt/Equity: {de}

Recent News:
{news}

Analyze and return a JSON object:
{{
    "has_alert": true/false,
    "severity": "critical" | "warning" | "info",
    "alert_type": "price_alert" | "fundamental_alert" | "news_alert" | "technical_alert",
    "title": "Short alert title (max 80 chars)",
    "summary": "2-3 sentence analysis with specific numbers",
    "action": "Suggested action for the investor"
}}

Only generate an alert if something is genuinely noteworthy (unusual price move, significant news, fundamental red flag, etc).
"""


class AlertEngine:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"

    async def check_symbol(self, symbol: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        try:
            async with AsyncSessionLocal() as session:
                company_q = await session.execute(
                    select(Company).where(Company.symbol == symbol.upper())
                )
                company = company_q.scalar_one_or_none()
                if not company:
                    return None

                quote_q = await session.execute(
                    select(StockQuote)
                    .where(StockQuote.company_id == company.id)
                    .order_by(desc(StockQuote.timestamp))
                    .limit(2)
                )
                quotes = quote_q.scalars().all()
                if not quotes:
                    return None

                latest = quotes[0]
                prev = quotes[1] if len(quotes) > 1 else latest
                change_pct = (
                    ((latest.close or 0) - (prev.close or 1))
                    / (prev.close or 1)
                    * 100
                )

                fund_q = await session.execute(
                    select(Fundamental)
                    .where(Fundamental.company_id == company.id)
                    .order_by(desc(Fundamental.id))
                    .limit(1)
                )
                fund = fund_q.scalar_one_or_none()

                news_q = await session.execute(
                    select(NewsArticle)
                    .where(NewsArticle.related_symbols.contains([symbol.upper()]))
                    .order_by(desc(NewsArticle.published_at))
                    .limit(3)
                )
                news = news_q.scalars().all()

                news_text = "\n".join(
                    [f"- {n.headline} [{n.source}]" for n in news]
                ) or "No recent news"

                prompt = ALERT_PROMPT.format(
                    symbol=symbol.upper(),
                    name=company.name or "",
                    price=latest.close or 0,
                    change_pct=round(change_pct, 2),
                    sector=company.sector or "Unknown",
                    pe=fund.pe if fund else "N/A",
                    pb=fund.pb if fund else "N/A",
                    roe=fund.roe if fund else "N/A",
                    de=fund.debt_equity if fund else "N/A",
                    news=news_text,
                )

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a financial alert system. Return only valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=500,
                )

                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]

                alert_data = json.loads(content)

                if not alert_data.get("has_alert"):
                    return None

                alert = AIAlert(
                    user_id=user_id,
                    symbol=symbol.upper(),
                    alert_type=alert_data.get("alert_type", "price_alert"),
                    severity=alert_data.get("severity", "info"),
                    title=alert_data.get("title", f"Alert for {symbol}"),
                    summary=alert_data.get("summary", ""),
                    data={
                        "price": latest.close,
                        "change_pct": change_pct,
                        "action": alert_data.get("action"),
                    },
                )
                session.add(alert)
                await session.flush()

                return {
                    "id": alert.id,
                    "symbol": alert.symbol,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "title": alert.title,
                    "summary": alert.summary,
                    "data": alert.data,
                    "created_at": alert.created_at.isoformat()
                    if alert.created_at
                    else None,
                }

        except Exception as e:
            logger.error(f"Alert engine error for {symbol}: {e}")
            return None

    async def run_for_all_watchlists(self) -> List[Dict[str, Any]]:
        alerts = []
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Watchlist))
                watchlists = result.scalars().all()

                symbols_checked = set()
                for wl in watchlists:
                    for sym in (wl.symbols or []):
                        if sym in symbols_checked:
                            continue
                        symbols_checked.add(sym)

                        alert = await self.check_symbol(sym, user_id=None)
                        if alert:
                            alerts.append(alert)

        except Exception as e:
            logger.error(f"Watchlist alert scan error: {e}")

        return alerts
