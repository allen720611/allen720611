"""Demo script — runs the full pipeline with sample hard-coded signals.

This allows grading the system WITHOUT real API keys for news / social.
Only ANTHROPIC_API_KEY is required to run the AI analysis stages.

Usage:
    cd <project-root>
    python demo/demo_run.py
"""
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import logging
from config import ANTHROPIC_API_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Hard-coded demo signals ───────────────────────────────────────────────────
DEMO_SIGNALS = [
    (
        "US announces 25% tariffs on all Chinese semiconductor imports effective immediately. "
        "Markets expected to react sharply as supply chain disruptions loom."
    ),
    (
        "Federal Reserve raises interest rates by 50 bps, citing persistent inflation. "
        "Tech stocks slide as growth expectations are revised downward."
    ),
    (
        "New $52B CHIPS Act subsidy approved for domestic semiconductor manufacturing. "
        "Intel and TSMC announce new US fabs, boosting domestic supply chain."
    ),
]


def main():
    print("\n" + "="*70)
    print("  AI 投資訊號預警系統 — Demo Run")
    print("  AI Investment Signals System — Demo")
    print("="*70 + "\n")

    if not ANTHROPIC_API_KEY:
        print("⚠️  ANTHROPIC_API_KEY not set in .env\n")
        print("   Running in OFFLINE DEMO mode (showing mock outputs).")
        _offline_demo()
        return

    from ai_analyzer import SentimentAnalyzer, EventClassifier, StrategyGenerator
    from backtester import BacktestEngine
    from line_bot import LineBotNotifier

    sentiment_analyzer = SentimentAnalyzer()
    event_classifier = EventClassifier()
    strategy_gen = StrategyGenerator()
    engine = BacktestEngine()
    notifier = LineBotNotifier()

    results = []

    for i, signal_text in enumerate(DEMO_SIGNALS, 1):
        print(f"{'─'*60}")
        print(f"訊號 {i}: {signal_text[:80]}...\n" if len(signal_text) > 80 else f"訊號 {i}: {signal_text}\n")

        # Sentiment
        sentiment = sentiment_analyzer.analyze(signal_text)
        print(f"  情緒分析  : {sentiment.sentiment} ({sentiment.score:+.2f})")
        print(f"  市場影響  : {sentiment.market_impact}")
        print(f"  受影響產業: {', '.join(sentiment.affected_sectors)}")
        print(f"  推理      : {sentiment.reasoning}\n")

        # Event classification
        event = event_classifier.classify(signal_text)
        print(f"  事件類型  : {event.event_type}")
        print(f"  緊急程度  : {event.urgency}")
        print(f"  時間框架  : {event.time_horizon}")
        print(f"  摘要      : {event.summary}\n")

        # Strategy
        strategy = strategy_gen.generate(sentiment, event)
        print(f"  策略立場  : {strategy.overall_stance.upper()}")
        print(f"  風險等級  : {strategy.risk_level}")
        print(f"  預期報酬  : {strategy.expected_return_range}")
        print(f"  停損設定  : -{strategy.stop_loss_pct:.1f}%")
        print("  建議操作  :")
        for act in strategy.actions:
            print(f"    {act.action:5s} {act.asset:6s} {act.allocation_pct:.0f}% — {act.rationale}")

        # Backtest
        print("\n  ▶ 執行回測...")
        bt_result = engine.run(strategy, strategy_name=f"Signal {i}: {event.event_type}")
        p = bt_result.performance
        print(f"    年化報酬  : {p.annualized_return_pct:+.2f}%")
        print(f"    最大回撤  : {p.max_drawdown_pct:.2f}%")
        print(f"    夏普比率  : {p.sharpe_ratio:.3f}")
        print(f"    勝率      : {p.win_rate_pct:.1f}%")
        print(f"    Alpha     : {p.alpha_pct:+.2f}%")

        # LINE push (simulated if no credentials)
        notifier.send_strategy_alert(strategy, p)
        results.append((strategy, p))
        print()

    print("="*70)
    print("Demo 完成！所有訊號已分析並生成投資策略。")
    print("="*70 + "\n")


def _offline_demo():
    """Print pre-computed mock outputs when no API key is available."""
    print("""
─────────────────────────────────────────────────────────
訊號 1: US announces 25% tariffs on all Chinese semiconductor imports...

  情緒分析  : negative (-0.82)
  市場影響  : bearish
  受影響產業: semiconductor, technology, manufacturing
  推理      : 關稅措施將推高供應鏈成本，壓縮科技企業利潤空間。

  事件類型  : TARIFF_POLICY
  緊急程度  : high
  時間框架  : short_term
  摘要      : 美國對中國半導體加徵25%關稅，衝擊全球供應鏈。

  策略立場  : BEARISH
  風險等級  : high
  預期報酬  : -5% to +8%
  停損設定  : -8.0%
  建議操作  :
    SELL  NVDA   25% — 減持曝險於中國供應鏈的半導體股
    BUY   INTC   20% — 增持受益於本土製造補貼的企業
    HOLD  AAPL   15% — 觀察蘋果供應鏈調整進度

  ▶ 執行回測...
    年化報酬  : +14.23%
    最大回撤  : -9.87%
    夏普比率  : 0.912
    勝率      : 63.6%
    Alpha     : +5.41%

══════════════════════════════════════════════════════════════════════
Demo 完成！所有訊號已分析並生成投資策略。
══════════════════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    main()
