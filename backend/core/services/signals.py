"""
Signal Generation Service - Professional trading signals for commodities

Generates buy/sell/hold signals based on:
- Price momentum
- Social sentiment
- News impact
- Technical indicators
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import String

from core.services.commodity_pipeline import get_commodity_prices, get_commodity_news
from core.services.commodity_prediction import CommodityPredictionModel

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """Trading signal types"""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class SignalStrength(str, Enum):
    """Signal strength levels"""

    VERY_HIGH = "very_high"  # > 80%
    HIGH = "high"  # 60-80%
    MEDIUM = "medium"  # 40-60%
    LOW = "low"  # < 40%


@dataclass
class TradingSignal:
    """Professional trading signal"""

    commodity: str
    signal: SignalType
    confidence: float
    strength: SignalStrength
    target_price: Optional[float]
    stop_loss: Optional[float]
    rationale: List[str]
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            "commodity": self.commodity,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "strength": self.strength.value,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "rationale": self.rationale,
            "timestamp": self.timestamp.isoformat(),
        }


class SignalGenerator:
    """Professional signal generation engine"""

    COMMODITIES = ["GOLD", "SILVER", "CRUDEOIL", "NATURALGAS"]

    def __init__(self):
        self.prediction_model = CommodityPredictionModel()

    async def generate_signal(self, commodity: str) -> TradingSignal:
        """Generate trading signal for a commodity"""
        logger.info(f"Generating signal for {commodity}")

        prediction = await self.prediction_model.predict(commodity)
        prices = await get_commodity_prices(commodity, days=7)
        news = await get_commodity_news(commodity, limit=10)

        confidence = prediction.get("confidence", 50)
        direction = prediction.get("direction", "neutral")

        current_price = prices[0].get("close", 0) if prices else 0

        if direction == "bullish":
            if confidence > 70:
                signal = SignalType.STRONG_BUY
            else:
                signal = SignalType.BUY
        elif direction == "bearish":
            if confidence > 70:
                signal = SignalType.STRONG_SELL
            else:
                signal = SignalType.SELL
        else:
            signal = SignalType.HOLD

        if confidence > 80:
            strength = SignalStrength.VERY_HIGH
        elif confidence > 60:
            strength = SignalStrength.HIGH
        elif confidence > 40:
            strength = SignalStrength.MEDIUM
        else:
            strength = SignalStrength.LOW

        target_price, stop_loss = self._calculate_targets(
            commodity, current_price, direction
        )

        rationale = self._generate_rationale(
            commodity, prediction, prices, news, confidence
        )

        return TradingSignal(
            commodity=commodity,
            signal=signal,
            confidence=confidence,
            strength=strength,
            target_price=target_price,
            stop_loss=stop_loss,
            rationale=rationale,
            timestamp=datetime.now(),
        )

    def _calculate_targets(
        self, commodity: str, current_price: float, direction: str
    ) -> tuple:
        """Calculate target and stop loss prices"""
        if direction == "bullish":
            target = current_price * 1.03
            stop_loss = current_price * 0.97
        elif direction == "bearish":
            target = current_price * 0.97
            stop_loss = current_price * 1.03
        else:
            return None, None

        return round(target, 2), round(stop_loss, 2)

    def _generate_rationale(
        self,
        commodity: str,
        prediction: Dict,
        prices: List[Dict],
        news: List[Dict],
        confidence: float,
    ) -> List[str]:
        """Generate signal rationale"""
        rationale = []

        prediction_score = prediction.get("score", 50)
        if prediction_score > 60:
            rationale.append(
                f"Prediction model shows bullish bias (score: {prediction_score:.1f})"
            )
        elif prediction_score < 40:
            rationale.append(
                f"Prediction model shows bearish bias (score: {prediction_score:.1f})"
            )

        if prices:
            latest = prices[0]
            change = latest.get("change_pct", 0)
            if change > 2:
                rationale.append(f"Strong upward momentum: {change:.1f}% today")
            elif change < -2:
                rationale.append(f"Downward pressure: {change:.1f}% today")

        if news:
            rationale.append(f"Found {len(news)} recent news articles")

        if confidence > 70:
            rationale.append(f"High confidence level: {confidence:.0f}%")

        return rationale[:4]

    async def generate_all_signals(self) -> List[TradingSignal]:
        """Generate signals for all commodities"""
        signals = []

        for commodity in self.COMMODITIES:
            try:
                signal = await self.generate_signal(commodity)
                signals.append(signal)
            except Exception as e:
                logger.error(f"Failed to generate signal for {commodity}: {e}")

        return signals

    async def get_top_picks(
        self, signal_type: SignalType = SignalType.BUY, limit: int = 3
    ) -> List[TradingSignal]:
        """Get top commodity picks"""
        all_signals = await self.generate_all_signals()

        filtered = [s for s in all_signals if s.signal == signal_type]
        filtered.sort(key=lambda x: x.confidence, reverse=True)

        return filtered[:limit]


class SignalService:
    """Public-facing signal service"""

    def __init__(self):
        self.generator = SignalGenerator()

    async def get_signal(self, commodity: str) -> Dict:
        """Get signal for specific commodity"""
        signal = await self.generator.generate_signal(commodity.upper())
        return signal.to_dict()

    async def get_all_signals(self) -> List[Dict]:
        """Get signals for all commodities"""
        signals = await self.generator.generate_all_signals()
        return [s.to_dict() for s in signals]

    async def get_top_picks(self, direction: str = "buy") -> List[Dict]:
        """Get top picks (buy/sell)"""
        signal_type = SignalType.BUY if direction.lower() == "buy" else SignalType.SELL
        picks = await self.generator.get_top_picks(signal_type)
        return [p.to_dict() for p in picks]

    async def get_market_summary(self) -> Dict:
        """Get market summary with signals"""
        signals = await self.generator.generate_all_signals()

        buy_signals = [
            s for s in signals if s.signal in [SignalType.BUY, SignalType.STRONG_BUY]
        ]
        sell_signals = [
            s for s in signals if s.signal in [SignalType.SELL, SignalType.STRONG_SELL]
        ]

        avg_confidence = (
            sum(s.confidence for s in signals) / len(signals) if signals else 0
        )

        return {
            "market_sentiment": "BULLISH"
            if len(buy_signals) > len(sell_signals)
            else "BEARISH"
            if len(sell_signals) > len(buy_signals)
            else "NEUTRAL",
            "signal_count": {
                "strong_buy": len(
                    [s for s in signals if s.signal == SignalType.STRONG_BUY]
                ),
                "buy": len([s for s in signals if s.signal == SignalType.BUY]),
                "hold": len([s for s in signals if s.signal == SignalType.HOLD]),
                "sell": len([s for s in signals if s.signal == SignalType.SELL]),
                "strong_sell": len(
                    [s for s in signals if s.signal == SignalType.STRONG_SELL]
                ),
            },
            "avg_confidence": round(avg_confidence, 1),
            "top_buy_picks": [s.to_dict() for s in buy_signals[:3]],
            "top_sell_picks": [s.to_dict() for s in sell_signals[:3]],
            "generated_at": datetime.now().isoformat(),
        }


signal_service = SignalService()
