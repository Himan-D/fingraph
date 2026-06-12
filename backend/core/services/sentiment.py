import json
import logging
from typing import Dict, List, Optional

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)

SENTIMENT_PROMPT = """Analyze the sentiment of these financial news headlines for Indian stock market.
For each headline, classify as: positive, negative, or neutral.
Also rate confidence 0-1 and extract any mentioned stock symbols.

Return a JSON array with objects containing:
- headline: the original headline
- sentiment: positive/negative/neutral
- confidence: 0.0 to 1.0
- symbols: array of mentioned stock symbols (NSE format)
- summary: one-line summary of why this sentiment

Headlines:
"""


class SentimentEngine:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
        self.batch_size = 20

    async def analyze_headlines(
        self, headlines: List[Dict[str, str]]
    ) -> List[Dict]:
        if not headlines:
            return []

        results = []
        for i in range(0, len(headlines), self.batch_size):
            batch = headlines[i : i + self.batch_size]
            try:
                batch_results = await self._analyze_batch(batch)
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"Sentiment batch error: {e}")
                for h in batch:
                    results.append(
                        {
                            "headline": h.get("headline", ""),
                            "sentiment": "neutral",
                            "confidence": 0.0,
                            "symbols": [],
                            "summary": "Analysis failed",
                        }
                    )

        return results

    async def _analyze_batch(self, headlines: List[Dict[str, str]]) -> List[Dict]:
        numbered = []
        for i, h in enumerate(headlines, 1):
            text = h.get("headline", "")
            source = h.get("source", "")
            numbered.append(f"{i}. [{source}] {text}")

        prompt = SENTIMENT_PROMPT + "\n".join(numbered)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial news sentiment analyzer. Return only valid JSON arrays.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            logger.warning("Failed to parse sentiment response as JSON")

        return [
            {
                "headline": h.get("headline", ""),
                "sentiment": "neutral",
                "confidence": 0.0,
                "symbols": [],
                "summary": "Parse error",
            }
            for h in headlines
        ]

    async def analyze_single(self, headline: str, source: str = "") -> Dict:
        results = await self.analyze_headlines(
            [{"headline": headline, "source": source}]
        )
        return results[0] if results else {
            "headline": headline,
            "sentiment": "neutral",
            "confidence": 0.0,
            "symbols": [],
            "summary": "No result",
        }
