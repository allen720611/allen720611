"""Social signal collector.

For demo purposes this module provides:
1. A mock generator that produces realistic-looking policy tweets.
2. A stub for real Twitter/X API v2 (requires Bearer token).

Switch between them via USE_MOCK_DATA in .env / config.
"""
import os
import random
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# Key accounts whose posts may move markets
WATCHED_ACCOUNTS = [
    "realDonaldTrump",
    "potus",
    "federalreserve",
    "SecYellen",
    "USTR",
]

# Mock templates: realistic policy-related tweet content
_MOCK_TEMPLATES = [
    "We will impose {pct}% tariffs on all {product} imports from {country}. America First!",
    "The Fed raised interest rates by {bps} bps today. Markets brace for impact.",
    "New export controls on advanced {chip} chips announced. National security concerns cited.",
    "Trade deal with {country} reached. Great news for American {sector} industry!",
    "BREAKING: {country} retaliates with {pct}% tariffs on US {product}.",
    "AI regulation bill passes committee. Tech sector faces new compliance requirements.",
    "Semiconductor subsidies of ${bn}B approved to boost domestic chip manufacturing.",
    "Supply chain disruption alert: {product} shortages expected in {country} factories.",
]


@dataclass
class SocialPost:
    text: str
    author: str
    platform: str
    posted_at: str
    url: str = ""
    keywords_matched: list[str] = field(default_factory=list)


class SocialCollector:
    """Collects social-media signals relevant to investment decisions."""

    def __init__(self, use_mock: bool = None):
        if use_mock is None:
            use_mock = not bool(TWITTER_BEARER_TOKEN)
        self.use_mock = use_mock

    def collect(self, max_results: int = 20) -> list[SocialPost]:
        if self.use_mock:
            logger.info("Using mock social data (no Twitter Bearer token found).")
            return self._generate_mock_posts(max_results)
        return self._fetch_twitter(max_results)

    # ------------------------------------------------------------------

    def _generate_mock_posts(self, n: int) -> list[SocialPost]:
        products = ["steel", "semiconductor", "EV", "solar panel", "pharmaceutical"]
        countries = ["China", "Mexico", "EU", "Japan", "South Korea"]
        sectors = ["manufacturing", "technology", "energy", "agriculture"]
        posts = []
        for i in range(n):
            template = random.choice(_MOCK_TEMPLATES)
            text = template.format(
                pct=random.choice([10, 25, 50]),
                product=random.choice(products),
                country=random.choice(countries),
                bps=random.choice([25, 50, 75]),
                chip=random.choice(["AI", "advanced", "military-grade"]),
                sector=random.choice(sectors),
                bn=random.choice([5, 10, 52]),
            )
            days_ago = random.randint(0, 2)
            posted_at = (datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))).isoformat()
            posts.append(
                SocialPost(
                    text=text,
                    author=random.choice(WATCHED_ACCOUNTS),
                    platform="Twitter/X (mock)",
                    posted_at=posted_at,
                )
            )
        return posts

    def _fetch_twitter(self, max_results: int) -> list[SocialPost]:
        """Real Twitter API v2 fetch (requires Bearer token)."""
        try:
            import requests

            headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
            query = " OR ".join(["tariff", "trade war", "Fed rate", "semiconductor", "sanctions"])
            params = {
                "query": f"({query}) lang:en -is:retweet",
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,author_id,text",
                "expansions": "author_id",
            }
            resp = requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers=headers,
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            posts = []
            for tweet in data.get("data", []):
                posts.append(
                    SocialPost(
                        text=tweet["text"],
                        author=tweet.get("author_id", "unknown"),
                        platform="Twitter/X",
                        posted_at=tweet.get("created_at", ""),
                        url=f"https://twitter.com/i/web/status/{tweet['id']}",
                    )
                )
            return posts
        except Exception as exc:
            logger.warning("Twitter API fetch failed: %s. Falling back to mock.", exc)
            return self._generate_mock_posts(max_results)
