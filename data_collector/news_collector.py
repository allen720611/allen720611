"""News data collector using NewsAPI and RSS feeds."""
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

import requests
import feedparser

from config import NEWS_API_KEY, NEWS_API_URL, SIGNAL_KEYWORDS

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    title: str
    description: str
    url: str
    published_at: str
    source: str
    keywords_matched: list[str] = field(default_factory=list)

    def full_text(self) -> str:
        return f"{self.title}. {self.description}"


# Free RSS feeds — no API key needed
RSS_FEEDS = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "BBC Business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "CNBC Finance": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "MarketWatch": "http://feeds.marketwatch.com/marketwatch/topstories/",
}


class NewsCollector:
    """Collects financial news from NewsAPI and public RSS feeds."""

    def __init__(self):
        self.api_key = NEWS_API_KEY

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def collect(self, days_back: int = 1, max_results: int = 50) -> list[NewsItem]:
        """Return news items relevant to investment signals."""
        items: list[NewsItem] = []

        # Try NewsAPI first (requires API key)
        if self.api_key:
            items.extend(self._from_newsapi(days_back, max_results // 2))

        # Always try RSS (free)
        items.extend(self._from_rss(max_results - len(items)))

        # Filter to keyword-relevant items
        relevant = self._filter_by_keywords(items)
        logger.info("Collected %d relevant news items (from %d total)", len(relevant), len(items))
        return relevant

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _from_newsapi(self, days_back: int, max_results: int) -> list[NewsItem]:
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        query = " OR ".join(SIGNAL_KEYWORDS[:5])  # API allows ~500 chars
        try:
            resp = requests.get(
                NEWS_API_URL,
                params={
                    "q": query,
                    "from": from_date,
                    "sortBy": "publishedAt",
                    "pageSize": max_results,
                    "language": "en",
                    "apiKey": self.api_key,
                },
                timeout=10,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            return [
                NewsItem(
                    title=a.get("title", ""),
                    description=a.get("description", "") or "",
                    url=a.get("url", ""),
                    published_at=a.get("publishedAt", ""),
                    source=a.get("source", {}).get("name", "NewsAPI"),
                )
                for a in articles
            ]
        except Exception as exc:
            logger.warning("NewsAPI fetch failed: %s", exc)
            return []

    def _from_rss(self, max_per_feed: int = 10) -> list[NewsItem]:
        items: list[NewsItem] = []
        for source_name, url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:max_per_feed]:
                    items.append(
                        NewsItem(
                            title=entry.get("title", ""),
                            description=entry.get("summary", "") or "",
                            url=entry.get("link", ""),
                            published_at=entry.get("published", str(datetime.utcnow())),
                            source=source_name,
                        )
                    )
                time.sleep(0.3)  # be polite to RSS servers
            except Exception as exc:
                logger.warning("RSS fetch failed for %s: %s", source_name, exc)
        return items

    def _filter_by_keywords(self, items: list[NewsItem]) -> list[NewsItem]:
        relevant = []
        for item in items:
            text = item.full_text().lower()
            matched = [kw for kw in SIGNAL_KEYWORDS if kw.lower() in text]
            if matched:
                item.keywords_matched = matched
                relevant.append(item)
        return relevant
