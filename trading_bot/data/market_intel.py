"""Agrégation intelligence marché — inspiré AI-Trader market_intel.py"""
import time
from dataclasses import dataclass, field
from typing import Dict, List

from trading_bot.data.price_fetcher import LAST_PRICES, get_ohlcv
from trading_bot.analysis.sentiment import get_sentiment
from trading_bot.data.news_fetcher import get_news


@dataclass
class MarketSnapshot:
    timestamp: float
    prices: Dict[str, float]
    sentiment_score: float
    sentiment_label: str
    top_news: List[str]
    activity_level: str    # quiet / calm / active / elevated


def get_market_snapshot() -> MarketSnapshot:
    """Retourne un instantané de l'état du marché."""
    sentiment = get_sentiment()
    news = get_news(5)

    # Niveau d'activité basé sur le nombre de news récentes
    news_count = len(get_news(50))
    if news_count < 5:
        activity = "quiet"
    elif news_count < 15:
        activity = "calm"
    elif news_count < 30:
        activity = "active"
    else:
        activity = "elevated"

    return MarketSnapshot(
        timestamp=time.time(),
        prices=dict(LAST_PRICES),
        sentiment_score=sentiment.score,
        sentiment_label=sentiment.label,
        top_news=[n["title"] for n in news],
        activity_level=activity,
    )
