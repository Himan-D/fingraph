from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, date, timedelta
from sqlalchemy import String, select, func

from db.postgres import AsyncSessionLocal
from db.postgres_models import (
    Commodity,
    CommodityPrice,
    CommodityNews,
    CommoditySentiment,
)


class CommodityPredictionModel:
    """Stock market prediction using social sentiment and graph analytics"""

    COMMODITIES = [
        "GOLD",
        "SILVER",
        "CRUDEOIL",
        "NATURALGAS",
        "COPPER",
        "ALUMINIUM",
        "ZINC",
        "NICKEL",
    ]

    async def get_features(self, commodity: str, days: int = 7) -> Dict:
        """Extract features for prediction"""
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import CommodityPrice, CommodityNews, CommoditySentiment
        from sqlalchemy import select, func

        features = {
            "commodity": commodity,
            "price_history": [],
            "price_change": 0,
            "price_change_pct": 0,
            "volume_trend": 0,
            "news_count": 0,
            "sentiment_score": 0,
            "mention_count": 0,
        }

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Commodity).where(Commodity.symbol == commodity.upper())
            )
            commodity_obj = result.scalar_one_or_none()

            if not commodity_obj:
                return {"commodity": commodity, "error": "Commodity not found"}

            query = (
                select(CommodityPrice)
                .where(
                    CommodityPrice.commodity_id == commodity_obj.id,
                    CommodityPrice.timestamp >= datetime.now() - timedelta(days=days),
                )
                .order_by(CommodityPrice.timestamp.desc())
            )

            result = await session.execute(query)
            prices = result.scalars().all()

            if prices:
                features["price_history"] = [
                    {
                        "timestamp": p.timestamp.isoformat(),
                        "close": p.close,
                        "change": p.change,
                        "change_pct": p.change_pct,
                    }
                    for p in prices[:7]
                ]

                if len(prices) >= 2:
                    features["price_change"] = prices[0].change or 0
                    features["price_change_pct"] = prices[0].change_pct or 0

                    if len(prices) >= 7:
                        avg_volume = sum(p.volume or 0 for p in prices[1:7]) / 6
                        features["volume_trend"] = (prices[0].volume or 0) - avg_volume

            news_query = select(func.count(CommodityNews.id)).where(
                CommodityNews.commodities.cast(String).like(f"%{commodity.upper()}%"),
                CommodityNews.published_at >= datetime.now() - timedelta(days=days),
            )
            result = await session.execute(news_query)
            features["news_count"] = result.scalar() or 0

            sent_query = (
                select(CommoditySentiment)
                .where(
                    CommoditySentiment.commodity_symbol == commodity.upper(),
                    CommoditySentiment.date >= date.today() - timedelta(days=days),
                )
                .order_by(CommoditySentiment.date.desc())
            )
            result = await session.execute(sent_query)
            sentiments = result.scalars().all()

            if sentiments:
                features["sentiment_score"] = sum(
                    s.sentiment_score for s in sentiments
                ) / len(sentiments)
                features["mention_count"] = sum(s.mention_count for s in sentiments)

        return features

    async def calculate_prediction_score(self, features: Dict) -> float:
        """Calculate prediction score based on features"""
        score = 50.0

        price_change = features.get("price_change_pct", 0)
        if price_change > 0:
            score += min(price_change * 0.5, 15)
        elif price_change < 0:
            score += max(price_change * 0.5, -15)

        sentiment = features.get("sentiment_score", 0)
        score += sentiment * 0.3

        mentions = features.get("mention_count", 0)
        if mentions > 20:
            score += 5
        elif mentions > 50:
            score += 10

        news = features.get("news_count", 0)
        if news > 10:
            score += 3
        elif news > 30:
            score += 7

        volume_trend = features.get("volume_trend", 0)
        if volume_trend > 0:
            score += 3

        return max(0, min(100, score))

    async def predict(self, commodity: str) -> Dict:
        """Predict commodity movement"""
        features = await self.get_features(commodity)

        score = await self.calculate_prediction_score(features)

        if score > 60:
            direction = "bullish"
            confidence = (score - 60) / 40 * 100
        elif score < 40:
            direction = "bearish"
            confidence = (40 - score) / 40 * 100
        else:
            direction = "neutral"
            confidence = 100 - abs(score - 50) * 2

        price_targets = self._calculate_price_targets(features, direction)

        return {
            "commodity": commodity,
            "direction": direction,
            "confidence": round(confidence, 2),
            "score": round(score, 2),
            "prediction": f"{direction.upper()} ({confidence:.0f}% confidence)",
            "price_targets": price_targets,
            "features": features,
            "generated_at": datetime.now().isoformat(),
        }

    def _calculate_price_targets(self, features: Dict, direction: str) -> Dict:
        """Calculate price targets"""
        history = features.get("price_history", [])
        if not history:
            return {}

        current_price = history[0].get("close", 0)

        if direction == "bullish":
            target_high = current_price * 1.02
            target_low = current_price * 1.005
            stop_loss = current_price * 0.98
        elif direction == "bearish":
            target_high = current_price * 0.995
            target_low = current_price * 0.98
            stop_loss = current_price * 1.02
        else:
            return {"current": current_price}

        return {
            "current": current_price,
            "target_high": round(target_high, 2),
            "target_low": round(target_low, 2),
            "stop_loss": round(stop_loss, 2),
        }

    async def predict_batch(self, commodities: List[str] = None) -> List[Dict]:
        """Predict multiple commodities"""
        if commodities is None:
            commodities = self.COMMODITIES

        predictions = []
        for commodity in commodities:
            try:
                pred = await self.predict(commodity)
                predictions.append(pred)
            except Exception as e:
                logger.warning(f"Prediction failed for {commodity}: {e}")

        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        return predictions

    async def get_top_picks(
        self, direction: str = "bullish", limit: int = 5
    ) -> List[Dict]:
        """Get top commodity picks"""
        predictions = await self.predict_batch()

        filtered = [p for p in predictions if p["direction"] == direction]
        return filtered[:limit]

    async def get_market_summary(self) -> Dict:
        """Get commodity market summary"""
        predictions = await self.predict_batch()

        bullish = [p for p in predictions if p["direction"] == "bullish"]
        bearish = [p for p in predictions if p["direction"] == "bearish"]
        neutral = [p for p in predictions if p["direction"] == "neutral"]

        avg_score = (
            sum(p["score"] for p in predictions) / len(predictions)
            if predictions
            else 50
        )

        if len(bullish) > len(bearish):
            sentiment = "BULLISH"
        elif len(bearish) > len(bullish):
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"

        return {
            "market_sentiment": sentiment,
            "avg_score": round(avg_score, 2),
            "bullish_count": len(bullish),
            "bearish_count": len(bearish),
            "neutral_count": len(neutral),
            "top_bullish": [p["commodity"] for p in bullish[:3]],
            "top_bearish": [p["commodity"] for p in bearish[:3]],
            "predictions": predictions,
            "generated_at": datetime.now().isoformat(),
        }


class CommodityMLPrediction(CommodityPredictionModel):
    """ML-enhanced commodity prediction"""

    async def predict_with_technicals(self, commodity: str) -> Dict:
        """Predict with technical indicators"""
        base = await self.predict(commodity)

        features = await self.get_features(commodity, days=30)

        sma_5, sma_20 = self._calculate_sma(features.get("price_history", []))

        rsi = self._calculate_rsi(features.get("price_history", []))

        technical_signal = "neutral"
        if sma_5 > sma_20:
            technical_signal = "bullish"
        elif sma_5 < sma_20:
            technical_signal = "bearish"

        if rsi > 70:
            technical_signal = "bearish"
        elif rsi < 30:
            technical_signal = "bullish"

        score = base["score"]

        if technical_signal == "bullish":
            score += 5
        elif technical_signal == "bearish":
            score -= 5

        if score > 60:
            direction = "bullish"
        elif score < 40:
            direction = "bearish"
        else:
            direction = "neutral"

        base["technical_signal"] = technical_signal
        base["rsi"] = round(rsi, 2)
        base["sma_5"] = round(sma_5, 2) if sma_5 else None
        base["sma_20"] = round(sma_20, 2) if sma_20 else None
        base["direction"] = direction
        base["score"] = round(score, 2)

        return base

    def _calculate_sma(self, price_history: List[Dict]) -> tuple:
        """Calculate SMA 5 and SMA 20"""
        if len(price_history) < 5:
            return None, None

        closes = [p.get("close", 0) for p in price_history]

        sma_5 = sum(closes[:5]) / 5 if len(closes) >= 5 else None

        sma_20 = sum(closes[:20]) / 20 if len(closes) >= 20 else sma_5

        return sma_5, sma_20

    def _calculate_rsi(self, price_history: List[Dict], period: int = 14) -> float:
        """Calculate RSI"""
        if len(price_history) < period + 1:
            return 50

        closes = [p.get("close", 0) for p in price_history[: period + 1]]

        gains = []
        losses = []

        for i in range(1, len(closes)):
            change = closes[i] - closes[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    async def predict_with_correlation(self, commodity: str) -> Dict:
        """Predict considering correlated commodities"""
        base = await self.predict(commodity)

        correlations = {
            "GOLD": ["SILVER", "CRUDEOIL"],
            "SILVER": ["GOLD", "COPPER"],
            "CRUDEOIL": ["NATURALGAS", "GOLD"],
            "NATURALGAS": ["CRUDEOIL"],
            "COPPER": ["ALUMINIUM", "SILVER"],
            "ALUMINIUM": ["COPPER", "ZINC"],
        }

        correlated = correlations.get(commodity.upper(), [])

        correlated_predictions = []
        for corr in correlated:
            try:
                pred = await self.predict(corr)
                correlated_predictions.append(pred)
            except:
                pass

        base["correlated_commodities"] = correlated_predictions

        if correlated_predictions:
            avg_score = sum(p["score"] for p in correlated_predictions) / len(
                correlated_predictions
            )
            base["score"] = round((base["score"] + avg_score) / 2, 2)

        return base


class CommodityEventPrediction:
    """Predict based on events"""

    async def predict_event_impact(self, event_type: str) -> Dict:
        """Predict impact of event type"""
        event_impacts = {
            "OPEC_MEETING": {
                "CRUDEOIL": {"direction": "high_volatility", "impact": "positive"},
                "NATURALGAS": {"direction": "neutral", "impact": "neutral"},
            },
            "FED_RATE": {
                "GOLD": {"direction": "bullish", "impact": "positive"},
                "SILVER": {"direction": "bullish", "impact": "positive"},
                "CRUDEOIL": {"direction": "bearish", "impact": "negative"},
            },
            "INFLATION": {
                "GOLD": {"direction": "bullish", "impact": "positive"},
                "SILVER": {"direction": "bullish", "impact": "positive"},
                "CRUDEOIL": {"direction": "bullish", "impact": "positive"},
            },
            "USD_MOVEMENT": {
                "GOLD": {"direction": "inverse", "impact": "negative"},
                "SILVER": {"direction": "inverse", "impact": "negative"},
            },
        }

        return event_impacts.get(event_type, {})

    async def get_upcoming_events(self) -> List[Dict]:
        """Get upcoming events that may impact commodities"""
        events = [
            {
                "type": "OPEC_MEETING",
                "date": "2024-04-15",
                "commodities": ["CRUDEOIL", "NATURALGAS"],
            },
            {
                "type": "FED_RATE",
                "date": "2024-05-01",
                "commodities": ["GOLD", "SILVER"],
            },
            {
                "type": "US_NFP",
                "date": "2024-04-05",
                "commodities": ["GOLD", "SILVER", "CRUDEOIL"],
            },
        ]

        return events


async def get_predictions() -> List[Dict]:
    """Get predictions for all commodities"""
    model = CommodityPredictionModel()
    return await model.predict_batch()


async def get_market_summary() -> Dict:
    """Get market summary"""
    model = CommodityPredictionModel()
    return await model.get_market_summary()


async def get_technical_prediction(commodity: str) -> Dict:
    """Get technical analysis prediction"""
    model = CommodityMLPrediction()
    return await model.predict_with_technicals(commodity)


async def get_correlation_prediction(commodity: str) -> Dict:
    """Get correlation-based prediction"""
    model = CommodityMLPrediction()
    return await model.predict_with_correlation(commodity)


if __name__ == "__main__":
    import asyncio

    async def main():
        model = CommodityPredictionModel()
        summary = await model.get_market_summary()
        print(f"Market: {summary['market_sentiment']}")
        print(f"Bullish: {summary['top_bullish']}")
        print(f"Bearish: {summary['top_bearish']}")

    asyncio.run(main())
