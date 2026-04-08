from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, date, timedelta
import asyncio

logger = logging.getLogger(__name__)


class PredictionModel:
    """Stock market prediction using social sentiment and graph analytics"""

    TRACKED_SYMBOLS = [
        "RELIANCE",
        "INFY",
        "TCS",
        "HDFCBANK",
        "ICICIBANK",
        "SBIN",
        "ADANIGREEN",
        "TATAMOTORS",
        "WIPRO",
        "HCLTECH",
        "TECHM",
        "LT",
        "ULTRACEMCO",
        "HINDUNILVR",
        "ITC",
        "KOTAKBANK",
    ]

    async def get_features(self, symbol: str, days: int = 7) -> Dict:
        """Extract features for prediction"""
        from sqlalchemy import select, func
        from sqlalchemy.ext.asyncio import AsyncSession
        from db.postgres import AsyncSessionLocal
        from db.postgres_models import (
            SocialSentiment,
            StockQuote,
            NewsArticle,
            RedditPost,
            TwitterPost,
        )

        features = {
            "symbol": symbol,
            "sentiment_history": [],
            "mention_trend": 0,
            "sentiment_trend": 0,
            "news_count": 0,
            "social_volume": 0,
        }

        async with AsyncSessionLocal() as session:
            query = (
                select(SocialSentiment)
                .where(
                    SocialSentiment.symbol == symbol,
                    SocialSentiment.date >= date.today() - timedelta(days=days),
                )
                .order_by(SocialSentiment.date)
            )

            result = await session.execute(query)
            sentiments = result.scalars().all()

            if sentiments:
                features["sentiment_history"] = [
                    {
                        "date": s.date.isoformat(),
                        "score": s.sentiment_score,
                        "mentions": s.mention_count,
                    }
                    for s in sentiments
                ]

                if len(sentiments) >= 2:
                    features["mention_trend"] = (
                        sentiments[-1].mention_count - sentiments[0].mention_count
                    )
                    features["sentiment_trend"] = (
                        sentiments[-1].sentiment_score - sentiments[0].sentiment_score
                    )

            mention_query = select(func.sum(SocialSentiment.mention_count)).where(
                SocialSentiment.symbol == symbol,
                SocialSentiment.date >= date.today() - timedelta(days=days),
            )
            result = await session.execute(mention_query)
            features["social_volume"] = result.scalar() or 0

            news_query = select(func.count(NewsArticle.id)).where(
                NewsArticle.related_symbols.contains([symbol]),
                NewsArticle.published_at >= datetime.now() - timedelta(days=days),
            )
            result = await session.execute(news_query)
            features["news_count"] = result.scalar() or 0

        return features

    async def calculate_prediction_score(self, features: Dict) -> float:
        """Calculate prediction score based on features"""
        score = 50.0

        sentiment = features.get("sentiment_trend", 0)
        score += sentiment * 0.3

        mentions = features.get("mention_trend", 0)
        if mentions > 0:
            score += min(mentions * 0.5, 10)
        elif mentions < 0:
            score += max(mentions * 0.3, -10)

        volume = features.get("social_volume", 0)
        if volume > 100:
            score += 5
        elif volume > 500:
            score += 10

        news = features.get("news_count", 0)
        if news > 10:
            score += 5
        elif news > 50:
            score += 10

        return max(0, min(100, score))

    async def predict(self, symbol: str, days_ahead: int = 1) -> Dict:
        """Predict stock movement"""
        features = await self.get_features(symbol, days=7)

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

        return {
            "symbol": symbol,
            "direction": direction,
            "confidence": round(confidence, 2),
            "score": round(score, 2),
            "prediction": f"{direction.upper()} ({confidence:.0f}% confidence)",
            "features": features,
            "generated_at": datetime.now().isoformat(),
        }

    async def predict_batch(self, symbols: List[str] = None) -> List[Dict]:
        """Predict multiple stocks"""
        if symbols is None:
            symbols = self.TRACKED_SYMBOLS

        predictions = []
        for symbol in symbols:
            try:
                pred = await self.predict(symbol)
                predictions.append(pred)
            except Exception as e:
                logger.warning(f"Prediction failed for {symbol}: {e}")

        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        return predictions

    async def get_top_picks(
        self, direction: str = "bullish", limit: int = 10
    ) -> List[Dict]:
        """Get top stock picks"""
        predictions = await self.predict_batch()

        filtered = [p for p in predictions if p["direction"] == direction]
        return filtered[:limit]

    async def get_recommendations(self) -> Dict:
        """Get overall market recommendations"""
        predictions = await self.predict_batch()

        bullish = [p for p in predictions if p["direction"] == "bullish"]
        bearish = [p for p in predictions if p["direction"] == "bearish"]
        neutral = [p for p in predictions if p["direction"] == "neutral"]

        avg_confidence = (
            sum(p["confidence"] for p in predictions) / len(predictions)
            if predictions
            else 0
        )

        if len(bullish) > len(bearish):
            market_sentiment = "BULLISH"
        elif len(bearish) > len(bullish):
            market_sentiment = "BEARISH"
        else:
            market_sentiment = "NEUTRAL"

        return {
            "market_sentiment": market_sentiment,
            "avg_confidence": round(avg_confidence, 2),
            "bullish_count": len(bullish),
            "bearish_count": len(bearish),
            "neutral_count": len(neutral),
            "top_bullish": [p["symbol"] for p in bullish[:5]],
            "top_bearish": [p["symbol"] for p in bearish[:5]],
            "generated_at": datetime.now().isoformat(),
        }


class GraphEnhancedPrediction(PredictionModel):
    """Enhanced prediction using GDS analytics"""

    async def get_graph_features(self, symbol: str) -> Dict:
        """Get graph-based features for prediction"""
        from db.neo4j_client import get_neo4j

        driver = get_neo4j()
        if not driver:
            return {}

        features = {}

        queries = {
            "pagerank": """
                MATCH (s:Stock {symbol: $symbol})
                RETURN s.pagerank as score
            """,
            "community_size": """
                MATCH (s:Stock {symbol: $symbol})-[:AFFECTS|RELEVANT_TO]-(other)
                WHERE s.community = other.community
                RETURN count(other) as community_size
            """,
            "influence_score": """
                MATCH (s:Stock {symbol: $symbol})
                OPTIONAL MATCH (s)<-[:AFFECTS]-(e:Event)
                RETURN coalesce(s.pagerank, 0) * coalesce(s.betweenness, 0) as influence_score,
                       count(e) as event_count
            """,
        }

        async with driver.session() as session:
            for key, query in queries.items():
                try:
                    result = await session.run(query, symbol=symbol)
                    data = await result.data()
                    if data:
                        features[key] = data[0]
                except Exception as e:
                    logger.debug(f"Graph feature error for {key}: {e}")

        return features

    async def predict_with_graph(self, symbol: str) -> Dict:
        """Enhanced prediction using both social and graph data"""
        base_prediction = await self.predict(symbol)

        graph_features = await self.get_graph_features(symbol)

        score = base_prediction["score"]

        if graph_features:
            influence = graph_features.get("influence_score", {})
            if influence:
                score += influence.get("influence_score", 0) * 0.1

        if score > 60:
            direction = "bullish"
            confidence = min((score - 60) / 40 * 100, 95)
        elif score < 40:
            direction = "bearish"
            confidence = min((40 - score) / 40 * 100, 95)
        else:
            direction = "neutral"
            confidence = 100 - abs(score - 50) * 2

        return {
            "symbol": symbol,
            "direction": direction,
            "confidence": round(confidence, 2),
            "score": round(score, 2),
            "prediction": f"{direction.upper()} ({confidence:.0f}% confidence)",
            "graph_features": graph_features,
            "features": base_prediction["features"],
            "generated_at": datetime.now().isoformat(),
        }

    async def event_driven_predictions(self, event_name: str) -> List[Dict]:
        """Predict stocks affected by a specific event"""
        from db.neo4j_client import get_neo4j

        driver = get_neo4j()
        if not driver:
            return []

        query = """
            MATCH (e:Event {name: $event})-[:AFFECTS]->(s:Stock)
            RETURN s.symbol as symbol, e.sentiment as sentiment
        """

        async with driver.session() as session:
            result = await session.run(query, event=event_name)
            affected = await result.data()

        predictions = []
        for stock in affected:
            pred = await self.predict(stock["symbol"])
            if stock.get("sentiment") == "positive":
                pred["score"] = min(pred["score"] + 10, 100)
            elif stock.get("sentiment") == "negative":
                pred["score"] = max(pred["score"] - 10, 0)
            pred["event"] = event_name
            predictions.append(pred)

        return predictions


async def get_predictions() -> List[Dict]:
    """Get predictions for all tracked stocks"""
    model = PredictionModel()
    return await model.predict_batch()


async def get_recommendations() -> Dict:
    """Get market recommendations"""
    model = PredictionModel()
    return await model.get_recommendations()


async def get_graph_predictions() -> List[Dict]:
    """Get graph-enhanced predictions"""
    model = GraphEnhancedPrediction()
    return await model.predict_batch()


if __name__ == "__main__":
    import asyncio

    async def main():
        model = PredictionModel()

        recs = await model.get_recommendations()
        print(f"Market: {recs['market_sentiment']}")
        print(f"Top Bullish: {recs['top_bullish']}")
        print(f"Top Bearish: {recs['top_bearish']}")

    asyncio.run(main())
