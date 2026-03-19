"""AI Investment Signals — main orchestration pipeline.

Flow:
  1. Collect news + social signals
  2. Analyse sentiment (Claude AI)
  3. Classify events (Claude AI)
  4. Generate investment strategy (Claude AI)
  5. Run backtesting
  6. Push LINE notification
"""
import logging
import sys
from dataclasses import dataclass

from config import ANTHROPIC_API_KEY
from data_collector import NewsCollector, SocialCollector
from ai_analyzer import SentimentAnalyzer, EventClassifier, StrategyGenerator
from backtester import BacktestEngine
from line_bot import LineBotNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    news_days_back: int = 1
    news_max: int = 30
    social_max: int = 20
    top_signals: int = 3          # how many signals to act on
    run_backtest: bool = True
    send_line: bool = True
    use_mock_social: bool = True  # set False when Twitter token available


def run_pipeline(cfg: PipelineConfig = None) -> None:
    cfg = cfg or PipelineConfig()

    if not ANTHROPIC_API_KEY:
        logger.error(
            "ANTHROPIC_API_KEY is not set. "
            "Please create a .env file with your key."
        )
        sys.exit(1)

    # ── 1. Data Collection ────────────────────────────────────────────
    logger.info("Step 1/5 — Collecting signals...")
    news_collector = NewsCollector()
    social_collector = SocialCollector(use_mock=cfg.use_mock_social)

    news_items = news_collector.collect(days_back=cfg.news_days_back, max_results=cfg.news_max)
    social_posts = social_collector.collect(max_results=cfg.social_max)

    logger.info("Collected %d news items + %d social posts", len(news_items), len(social_posts))

    # Combine text signals
    all_texts = (
        [item.full_text() for item in news_items]
        + [post.text for post in social_posts]
    )
    if not all_texts:
        logger.warning("No signals collected. Exiting.")
        return

    # ── 2. Sentiment Analysis ─────────────────────────────────────────
    logger.info("Step 2/5 — Running sentiment analysis (top %d signals)...", cfg.top_signals)
    sentiment_analyzer = SentimentAnalyzer()
    top_texts = all_texts[: cfg.top_signals]
    sentiments = sentiment_analyzer.analyze_batch(top_texts)

    for i, s in enumerate(sentiments, 1):
        logger.info(
            "  Signal %d: sentiment=%s (%.2f) | impact=%s | sectors=%s",
            i, s.sentiment, s.score, s.market_impact, s.affected_sectors,
        )

    # ── 3. Event Classification ───────────────────────────────────────
    logger.info("Step 3/5 — Classifying events...")
    event_classifier = EventClassifier()
    events = event_classifier.classify_batch(top_texts)

    for i, e in enumerate(events, 1):
        logger.info(
            "  Event %d: type=%s | urgency=%s | horizon=%s",
            i, e.event_type, e.urgency, e.time_horizon,
        )

    # ── 4. Strategy Generation ────────────────────────────────────────
    # Use the highest-urgency / most-bearish signal to drive strategy
    combined = sorted(
        zip(sentiments, events),
        key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}.get(x[1].urgency, 1),
            abs(x[0].score),
        ),
        reverse=True,
    )

    logger.info("Step 4/5 — Generating investment strategy...")
    strategy_gen = StrategyGenerator()
    best_sentiment, best_event = combined[0]
    strategy = strategy_gen.generate(best_sentiment, best_event)

    logger.info(
        "Strategy: stance=%s | risk=%s | expected=%s",
        strategy.overall_stance, strategy.risk_level, strategy.expected_return_range,
    )
    for act in strategy.actions:
        logger.info("  Action: %s %s (%.0f%%) — %s", act.action, act.asset, act.allocation_pct, act.rationale)

    # ── 5. Backtesting ────────────────────────────────────────────────
    performance = None
    if cfg.run_backtest:
        logger.info("Step 5/5 — Running backtest...")
        engine = BacktestEngine()
        result = engine.run(strategy, strategy_name=f"AI Signal: {best_event.event_type}")
        result.print_summary()
        performance = result.performance

    # ── 6. LINE Notification ──────────────────────────────────────────
    if cfg.send_line:
        logger.info("Sending LINE notification...")
        notifier = LineBotNotifier()
        if performance:
            notifier.send_strategy_alert(strategy, performance)
        else:
            notifier.send_text(strategy.to_line_message())

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()
