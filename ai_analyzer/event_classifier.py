"""Event classifier — categorises signals into actionable event types."""
import json
import logging
from dataclasses import dataclass

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Canonical event types used throughout the system
EVENT_TYPES = [
    "TARIFF_POLICY",
    "INTEREST_RATE",
    "TRADE_AGREEMENT",
    "EXPORT_CONTROL",
    "GOVERNMENT_SUBSIDY",
    "AI_REGULATION",
    "SUPPLY_CHAIN_DISRUPTION",
    "EARNINGS_SURPRISE",
    "GEOPOLITICAL_TENSION",
    "COMMODITY_SHOCK",
    "OTHER",
]

_SYSTEM_PROMPT = f"""\
You are a financial event classification expert.
Classify the provided financial signal text into exactly ONE event type from this list:
{', '.join(EVENT_TYPES)}

Also provide:
- urgency: "high" | "medium" | "low"
- geographic_scope: list of affected regions/countries (e.g. ["US", "China", "Global"])
- time_horizon: "short_term" (days–weeks) | "medium_term" (weeks–months) | "long_term" (months–years)
- key_entities: important companies, agencies, or individuals mentioned

Respond ONLY with valid JSON:
{{
  "event_type": "<EVENT_TYPE>",
  "urgency": "high|medium|low",
  "geographic_scope": ["..."],
  "time_horizon": "short_term|medium_term|long_term",
  "key_entities": ["..."],
  "summary": "<one sentence summary>"
}}"""


@dataclass
class EventClassification:
    text: str
    event_type: str
    urgency: str
    geographic_scope: list[str]
    time_horizon: str
    key_entities: list[str]
    summary: str


class EventClassifier:
    """Classifies financial news/social signals into structured event types."""

    def classify(self, text: str) -> EventClassification:
        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=512,
                messages=[
                    {"role": "user", "content": f"Classify this financial event:\n\n{text}"}
                ],
                system=_SYSTEM_PROMPT,
            )
            raw = message.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            return EventClassification(
                text=text,
                event_type=data.get("event_type", "OTHER"),
                urgency=data.get("urgency", "low"),
                geographic_scope=data.get("geographic_scope", []),
                time_horizon=data.get("time_horizon", "medium_term"),
                key_entities=data.get("key_entities", []),
                summary=data.get("summary", ""),
            )
        except Exception as exc:
            logger.error("Event classification failed: %s", exc)
            return EventClassification(
                text=text,
                event_type="OTHER",
                urgency="low",
                geographic_scope=[],
                time_horizon="medium_term",
                key_entities=[],
                summary=f"Classification failed: {exc}",
            )

    def classify_batch(self, texts: list[str]) -> list[EventClassification]:
        return [self.classify(t) for t in texts]
