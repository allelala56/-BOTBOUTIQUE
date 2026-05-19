"""
Market intelligence aggregator.
Combines macro signals, news sentiment, and orderbook health.
Inspired by HKUDS/AI-Trader market_intel.py structure.
"""
import logging
from dataclasses import dataclass
from typing import Dict

from trading_bot.data.news_fetcher import get_recent_news
from trading_bot.data.price_fetcher import get_candles, get_orderbook

log = logging.getLogger(__name__)


@dataclass
class MarketIntel:
    sentiment_score: float       # -1 (bearish) to +1 (bullish)
    sentiment_label: str
    news_activity: str           # quiet / calm / active / elevated
    top_bullish_symbols: list
    top_bearish_symbols: list
    market_summary: str


def build_market_intel(sentiment_score: float, sentiment_label: str) -> MarketIntel:
    """
    Aggregate news + prices into a MarketIntel snapshot.
    sentiment_score comes from SentimentAnalyzer.
    """
    news = get_recent_news(20)
    count = len(news)

    if count < 5:
        activity = "quiet"
    elif count < 10:
        activity = "calm"
    elif count < 18:
        activity = "active"
    else:
        activity = "elevated"

    # Parse Alpha Vantage ticker sentiment if available
    bullish: Dict[str, float] = {}
    bearish: Dict[str, float] = {}
    for article in news:
        score = article.get("av_sentiment_score", 0.0)
        symbol = article.get("source", "")
        if score > 0.15:
            bullish[symbol] = bullish.get(symbol, 0) + score
        elif score < -0.15:
            bearish[symbol] = bearish.get(symbol, 0) + abs(score)

    top_bullish = sorted(bullish, key=bullish.get, reverse=True)[:3]
    top_bearish = sorted(bearish, key=bearish.get, reverse=True)[:3]

    trend = "neutre"
    if sentiment_score > 0.3:
        trend = "haussier"
    elif sentiment_score < -0.3:
        trend = "baissier"

    summary = (
        f"Marché {trend} | Activité: {activity} | "
        f"{count} news récentes | Score sentiment: {sentiment_score:+.2f}"
    )

    return MarketIntel(
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label,
        news_activity=activity,
        top_bullish_symbols=top_bullish,
        top_bearish_symbols=top_bearish,
        market_summary=summary,
    )
