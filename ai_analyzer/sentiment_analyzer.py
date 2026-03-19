"""Sentiment analysis using Claude AI."""
import json
import logging
from dataclasses import dataclass

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


@dataclass
class SentimentResult:
    text: str
    sentiment: str          # "positive" | "negative" | "neutral"
    score: float            # -1.0 … +1.0
    confidence: float       # 0.0 … 1.0
    market_impact: str      # "bullish" | "bearish" | "neutral"
    affected_sectors: list[str]
    reasoning: str


_SYSTEM_PROMPT = """\
You are a senior FinTech analyst specializing in event-driven investing.
Given a news headline or social media post, analyze:
1. Overall sentiment (positive / negative / neutral)
2. Sentiment score from -1.0 (very negative) to +1.0 (very positive)
3. Confidence level 0.0–1.0
4. Market impact for investors: bullish | bearish | neutral
5. Affected market sectors (choose from: technology, semiconductor, energy, finance,
   consumer, manufacturing, healthcare, materials, real estate, utilities)
6. Brief reasoning (≤ 2 sentences)

Respond ONLY with valid JSON matching exactly this schema:
{
  "sentiment": "positive|negative|neutral",
  "score": <float>,
  "confidence": <float>,
  "market_impact": "bullish|bearish|neutral",
  "affected_sectors": ["sector1", ...],
  "reasoning": "<string>"
}"""


class SentimentAnalyzer:
    """Analyzes financial text sentiment using Claude."""

    def analyze(self, text: str) -> SentimentResult:
        """Analyze a single piece of text."""
        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=512,
                messages=[
                    {"role": "user", "content": f"Analyze this financial signal:\n\n{text}"}
                ],
                system=_SYSTEM_PROMPT,
            )
            raw = message.content[0].text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            return SentimentResult(
                text=text,
                sentiment=data["sentiment"],
                score=float(data["score"]),
                confidence=float(data["confidence"]),
                market_impact=data["market_impact"],
                affected_sectors=data.get("affected_sectors", []),
                reasoning=data.get("reasoning", ""),
            )
        except Exception as exc:
            logger.error("Sentiment analysis failed: %s", exc)
            # Graceful fallback
            return SentimentResult(
                text=text,
                sentiment="neutral",
                score=0.0,
                confidence=0.0,
                market_impact="neutral",
                affected_sectors=[],
                reasoning=f"Analysis failed: {exc}",
            )

    def analyze_batch(self, texts: list[str]) -> list[SentimentResult]:
        return [self.analyze(t) for t in texts]
