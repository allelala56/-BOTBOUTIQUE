"""
News sentiment analysis via Claude Haiku (claude-haiku-4-5-20251001).
Caches results for SENTIMENT_INTERVAL seconds to minimize API calls.
"""
import json
import logging
import time
from typing import Optional, Tuple

import anthropic

from trading_bot.config import config
from trading_bot.data.news_fetcher import get_recent_news

log = logging.getLogger(__name__)

_cached_score: float = 0.0
_cached_label: str = "Neutral"
_cached_at: float = 0.0

_client: Optional[anthropic.AsyncAnthropic] = None


def _get_client() -> Optional[anthropic.AsyncAnthropic]:
    global _client
    if not config.anthropic_api_key:
        return None
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
    return _client


def _score_from_av_news(news: list) -> float:
    """Fallback: average Alpha Vantage sentiment scores directly."""
    scores = [n.get("av_sentiment_score", 0.0) for n in news if "av_sentiment_score" in n]
    return sum(scores) / len(scores) if scores else 0.0


async def analyze_sentiment() -> Tuple[float, str]:
    """
    Returns (score, label) where score is -1 (bearish) to +1 (bullish).
    Uses cached result if still fresh.
    """
    global _cached_score, _cached_label, _cached_at

    now = time.time()
    if now - _cached_at < config.sentiment_interval:
        return _cached_score, _cached_label

    news = get_recent_news(20)
    if not news:
        return 0.0, "Neutral"

    client = _get_client()
    if client is None:
        # Fallback: use Alpha Vantage scores directly
        score = _score_from_av_news(news)
        label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
        _cached_score, _cached_label, _cached_at = score, label, now
        log.info("[SENTIMENT] fallback AV score=%.3f label=%s", score, label)
        return score, label

    # Build news digest for Claude
    headlines = "\n".join(
        f"- [{n['source']}] {n['title']}" for n in news[:15]
    )
    prompt = (
        "Tu es un analyste financier spécialisé en crypto. "
        "Analyse les titres d'actualité suivants et évalue le sentiment global du marché crypto.\n\n"
        f"ACTUALITÉS:\n{headlines}\n\n"
        "Réponds UNIQUEMENT avec un JSON valide sur une seule ligne:\n"
        '{"score": <float entre -1 et +1>, "label": "<Bullish|Neutral|Bearish>", "reason": "<max 50 chars>"}'
    )

    try:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)
        score = float(max(-1.0, min(1.0, data.get("score", 0.0))))
        label = data.get("label", "Neutral")
        reason = data.get("reason", "")
        _cached_score, _cached_label, _cached_at = score, label, now
        log.info("[SENTIMENT] Claude: score=%+.2f label=%s | %s", score, label, reason)
        return score, label
    except Exception as exc:
        log.warning("[SENTIMENT] Claude analysis failed: %s", exc)
        score = _score_from_av_news(news)
        label = "Bullish" if score > 0.15 else "Bearish" if score < -0.15 else "Neutral"
        _cached_score, _cached_label, _cached_at = score, label, now
        return score, label


def get_cached_sentiment() -> Tuple[float, str]:
    return _cached_score, _cached_label
