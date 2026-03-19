"""Configuration for AI Investment Signals system."""
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic / Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"

# News API (https://newsapi.org — free tier)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_URL = "https://newsapi.org/v2/everything"

# LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")  # target user/group to push

# Backtesting defaults
BACKTEST_YEARS = 3
INITIAL_CAPITAL = 1_000_000  # TWD

# Watched keywords for policy / social signals
SIGNAL_KEYWORDS = [
    "tariff", "trade war", "Fed rate", "interest rate",
    "semiconductor", "AI regulation", "subsidy",
    "sanctions", "export ban", "supply chain",
]

# Sector → representative ETF/stock tickers (Yahoo Finance)
SECTOR_TICKERS = {
    "technology": ["AAPL", "MSFT", "NVDA", "TSM"],
    "semiconductor": ["NVDA", "AMD", "INTC", "TSM", "ASML"],
    "energy": ["XOM", "CVX", "COP"],
    "finance": ["JPM", "BAC", "GS"],
    "consumer": ["AMZN", "WMT", "MCD"],
    "manufacturing": ["CAT", "DE", "MMM"],
    "healthcare": ["JNJ", "PFE", "UNH"],
}
