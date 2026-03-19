"""Investment strategy generator using Claude AI."""
import json
import logging
from dataclasses import dataclass, field

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, SECTOR_TICKERS
from ai_analyzer.sentiment_analyzer import SentimentResult
from ai_analyzer.event_classifier import EventClassification

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


@dataclass
class InvestmentAction:
    action: str          # "BUY" | "SELL" | "HOLD" | "SHORT"
    asset: str           # ticker or sector name
    allocation_pct: float  # % of portfolio
    rationale: str


@dataclass
class InvestmentStrategy:
    event_summary: str
    overall_stance: str          # "bullish" | "bearish" | "neutral" | "defensive"
    actions: list[InvestmentAction]
    risk_level: str              # "low" | "medium" | "high"
    expected_return_range: str   # e.g. "+5% to +15%"
    stop_loss_pct: float
    time_horizon: str
    key_risks: list[str]
    raw: dict = field(default_factory=dict)

    def to_line_message(self) -> str:
        """Format strategy as LINE Bot push message."""
        lines = [
            "⚠️ AI 投資預警",
            f"📌 事件: {self.event_summary}",
            f"📊 整體立場: {self.overall_stance.upper()}",
            f"⚡ 風險等級: {self.risk_level}",
            f"📈 預期報酬: {self.expected_return_range}",
            f"🛑 停損: -{self.stop_loss_pct:.1f}%",
            f"⏱  時間框架: {self.time_horizon}",
            "",
            "🎯 建議操作:",
        ]
        for act in self.actions[:4]:  # LINE has message length limits
            emoji = {"BUY": "🟢", "SELL": "🔴", "SHORT": "🔻", "HOLD": "🟡"}.get(act.action, "⚪")
            lines.append(f"  {emoji} {act.action} {act.asset} ({act.allocation_pct:.0f}%)")
            lines.append(f"     {act.rationale}")
        if self.key_risks:
            lines.append("")
            lines.append(f"⚠️ 主要風險: {', '.join(self.key_risks[:3])}")
        return "\n".join(lines)


_SYSTEM_PROMPT = """\
You are an expert event-driven investment strategist at a quantitative hedge fund.
Given a financial event with its sentiment and classification, generate a concrete
investment strategy.

Consider:
- Event-driven trading principles (how markets typically react to this event type)
- Sector rotation opportunities
- Risk management (stop-loss, position sizing)
- Time horizon appropriate to the event urgency

Respond ONLY with valid JSON:
{
  "overall_stance": "bullish|bearish|neutral|defensive",
  "actions": [
    {
      "action": "BUY|SELL|SHORT|HOLD",
      "asset": "<ticker or sector>",
      "allocation_pct": <0-100>,
      "rationale": "<one sentence>"
    }
  ],
  "risk_level": "low|medium|high",
  "expected_return_range": "<e.g. +5% to +12%>",
  "stop_loss_pct": <float>,
  "time_horizon": "<e.g. 2-4 weeks>",
  "key_risks": ["<risk1>", "<risk2>"]
}
Make sure allocation_pct values sum to ≤ 100."""


class StrategyGenerator:
    """Generates investment strategies from event analysis using Claude."""

    def generate(
        self,
        sentiment: SentimentResult,
        event: EventClassification,
    ) -> InvestmentStrategy:
        # Build context for Claude
        context = {
            "event_summary": event.summary,
            "event_type": event.event_type,
            "urgency": event.urgency,
            "time_horizon": event.time_horizon,
            "geographic_scope": event.geographic_scope,
            "sentiment": sentiment.sentiment,
            "sentiment_score": sentiment.score,
            "market_impact": sentiment.market_impact,
            "affected_sectors": sentiment.affected_sectors,
            "key_entities": event.key_entities,
            "available_tickers": SECTOR_TICKERS,
        }

        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Generate an investment strategy for this event:\n\n"
                            + json.dumps(context, indent=2)
                        ),
                    }
                ],
                system=_SYSTEM_PROMPT,
            )
            raw = message.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)

            actions = [
                InvestmentAction(
                    action=a["action"],
                    asset=a["asset"],
                    allocation_pct=float(a["allocation_pct"]),
                    rationale=a["rationale"],
                )
                for a in data.get("actions", [])
            ]

            return InvestmentStrategy(
                event_summary=event.summary,
                overall_stance=data.get("overall_stance", "neutral"),
                actions=actions,
                risk_level=data.get("risk_level", "medium"),
                expected_return_range=data.get("expected_return_range", "unknown"),
                stop_loss_pct=float(data.get("stop_loss_pct", 5.0)),
                time_horizon=data.get("time_horizon", event.time_horizon),
                key_risks=data.get("key_risks", []),
                raw=data,
            )
        except Exception as exc:
            logger.error("Strategy generation failed: %s", exc)
            return InvestmentStrategy(
                event_summary=event.summary,
                overall_stance="neutral",
                actions=[],
                risk_level="high",
                expected_return_range="unknown",
                stop_loss_pct=5.0,
                time_horizon="unknown",
                key_risks=[str(exc)],
            )
